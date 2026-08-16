"""
APEX Goal Manager.

This is the ONLY place APEX talks to AEGIS Runtime. Everything
APEX-specific (governance, tools, persistence, event streaming) lives
here or in modules this file composes; AEGIS Runtime itself
(GoalAnalyzer, Planner, TaskGraph, RuntimeEngine, VerificationEngine,
RecoveryEngine, AgentFactory) is used unmodified aside from the
additive on_event/should_cancel hooks added to RuntimeEngine.

    APEX API layer
         |
         v
    GoalManager   <-- this file
         |
         v
    AEGIS Runtime (GoalAnalyzer / Planner / TaskGraph / RuntimeEngine)

Two-phase flow (matches the required API surface):

    submit_goal()      -> Gemini analyzes + plans, no execution yet.
    create_execution()  -> starts (or queues for approval) a run of
                            that plan.
    run_execution()      -> the actual blocking RuntimeEngine.run()
                             call. The API layer runs this inside a
                             background thread.
"""

from typing import Any, Callable, Dict, Optional

from apex.backend.db.database import Database
from apex.backend.events.bus import event_bus
from apex.backend.execution.executor_factory import build_executor
from apex.backend.governance.governance import GovernanceGate, RiskLevel, highest_risk
from apex.backend.tools.registry import ToolRegistry
from apex.backend.tools.simulated_tools import build_default_tool_registry


class GoalManager:
    def __init__(
        self,
        db: Database,
        tool_registry: Optional[ToolRegistry] = None,
        governance_gate: Optional[GovernanceGate] = None,
        goal_analyzer: Optional[Any] = None,
        planner: Optional[Any] = None,
        verifier: Optional[Any] = None,
        recovery: Optional[Any] = None,
        agent_factory: Optional[Any] = None,
    ):
        self.db = db
        self.tool_registry = tool_registry or build_default_tool_registry()
        self.governance_gate = governance_gate or GovernanceGate()

        # These may be injected (e.g. fakes in tests) to avoid ever
        # calling Gemini during automated tests, exactly like AEGIS's
        # own AEGISOrchestrator/RuntimeEngine do.
        self._goal_analyzer = goal_analyzer
        self._planner = planner
        self._verifier = verifier
        self._recovery = recovery
        self._agent_factory = agent_factory

    # ------------------------------------------------------------
    # Lazy AEGIS component construction (real Gemini components,
    # only built if nothing was injected).
    # ------------------------------------------------------------

    def _get_goal_analyzer(self):
        if self._goal_analyzer is None:
            from backend.agents.goal_analyzer import GoalAnalyzer

            self._goal_analyzer = GoalAnalyzer()
        return self._goal_analyzer

    def _get_planner(self):
        if self._planner is None:
            from backend.planner.planner import Planner

            self._planner = Planner()
        return self._planner

    def _get_verifier(self):
        if self._verifier is None:
            from backend.verifier.verifier import VerificationEngine

            self._verifier = VerificationEngine()
        return self._verifier

    def _get_recovery(self):
        if self._recovery is None:
            from backend.recovery.recovery_engine import RecoveryEngine

            self._recovery = RecoveryEngine()
        return self._recovery

    def _get_agent_factory(self):
        if self._agent_factory is None:
            from backend.agents.agent_factory import AgentFactory

            self._agent_factory = AgentFactory()
        return self._agent_factory

    # ------------------------------------------------------------
    # Risk assessment
    # ------------------------------------------------------------

    def _compute_max_risk(self, plan) -> RiskLevel:
        levels = []
        for task in plan.tasks:
            capabilities = task.required_capabilities or []
            tool_name = capabilities[0] if capabilities else None
            if tool_name and self.tool_registry.has(tool_name):
                levels.append(self.tool_registry.get(tool_name).risk_level)
        return highest_risk(levels)

    # ------------------------------------------------------------
    # Phase 1: POST /api/goals
    # ------------------------------------------------------------

    def submit_goal(self, user_goal: str) -> Dict[str, Any]:
        from backend.runtime.task_graph import TaskGraph  # validates plan shape early

        structured_goal = self._get_goal_analyzer().analyze(user_goal)
        plan = self._get_planner().create_plan(structured_goal)

        # Fail fast if the plan is structurally broken (e.g. a cycle)
        # before we ever persist it or offer it for execution.
        TaskGraph(plan)

        max_risk = self._compute_max_risk(plan)

        goal_id = self.db.insert_goal(
            user_goal=user_goal,
            structured_goal=structured_goal.model_dump(),
            plan=plan.model_dump(),
            max_risk=max_risk.value,
        )

        return {
            "goal_id": goal_id,
            "structured_goal": structured_goal.model_dump(),
            "plan": plan.model_dump(),
            "max_risk": max_risk.value,
        }

    # ------------------------------------------------------------
    # Deterministic demo scenario ("Run Recovery Demo")
    # ------------------------------------------------------------

    def create_recovery_demo_goal(self) -> Dict[str, Any]:
        """
        Like submit_goal(), but the StructuredGoal and ExecutionPlan
        are built deterministically in Python instead of by Gemini,
        so the demo is reproducible. Verification and recovery
        REASONING downstream of this are still real Gemini calls.
        """
        from apex.backend.demo.recovery_demo import (
            build_recovery_demo_goal,
            build_recovery_demo_plan,
        )
        from backend.runtime.task_graph import TaskGraph

        structured_goal = build_recovery_demo_goal()
        plan = build_recovery_demo_plan()

        TaskGraph(plan)  # validate shape early

        max_risk = self._compute_max_risk(plan)

        goal_id = self.db.insert_goal(
            user_goal=structured_goal.objective,
            structured_goal=structured_goal.model_dump(),
            plan=plan.model_dump(),
            max_risk=max_risk.value,
        )

        return {
            "goal_id": goal_id,
            "structured_goal": structured_goal.model_dump(),
            "plan": plan.model_dump(),
            "max_risk": max_risk.value,
        }

    # ------------------------------------------------------------
    # Phase 2: POST /api/executions
    # ------------------------------------------------------------

    def create_execution(
        self,
        goal_id: str,
        auto_approve_high: bool = False,
    ) -> Dict[str, Any]:
        goal = self.db.get_goal(goal_id)
        if goal is None:
            raise ValueError(f"Goal '{goal_id}' does not exist.")

        max_risk = RiskLevel(goal["max_risk"]) if goal["max_risk"] else RiskLevel.LOW

        preflight = self.governance_gate.evaluate(
            risk_level=max_risk,
            auto_approve_high=auto_approve_high,
            approved=False,
        )

        status = "running" if preflight.can_execute else "pending_approval"

        execution_id = self.db.insert_execution(
            goal_id=goal_id,
            status=status,
            auto_approve_high=auto_approve_high,
        )

        self.db.insert_event(
            execution_id,
            "execution_created",
            {
                "goal_id": goal_id,
                "max_risk": max_risk.value,
                "status": status,
                "governance_reason": preflight.reason,
            },
        )

        return {"execution_id": execution_id, "status": status}

    # ------------------------------------------------------------
    # POST /api/executions/{id}/approve
    # ------------------------------------------------------------

    def approve_execution(self, execution_id: str) -> Dict[str, Any]:
        execution = self.db.get_execution(execution_id)
        if execution is None:
            raise ValueError(f"Execution '{execution_id}' does not exist.")

        self.db.update_execution(execution_id, approved=True, status="running")
        self.db.insert_event(execution_id, "execution_approved", {})
        event_bus.publish(execution_id, "execution_approved", {})

        return self.db.get_execution(execution_id)

    # ------------------------------------------------------------
    # POST /api/executions/{id}/cancel
    # ------------------------------------------------------------

    def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        execution = self.db.get_execution(execution_id)
        if execution is None:
            raise ValueError(f"Execution '{execution_id}' does not exist.")

        if execution["status"] not in ("running", "pending_approval"):
            return execution

        self.db.update_execution(execution_id, status="cancel_requested")
        self.db.insert_event(execution_id, "cancel_requested", {})
        return self.db.get_execution(execution_id)

    # ------------------------------------------------------------
    # The actual blocking run. Call via asyncio.to_thread from the
    # API layer so the event loop stays free for the WebSocket.
    # ------------------------------------------------------------

    def run_execution(self, execution_id: str) -> Dict[str, Any]:
        from backend.models.schemas import ExecutionPlan, StructuredGoal
        from backend.runtime.task_graph import TaskGraph
        from backend.runtime.runtime import RuntimeEngine

        execution = self.db.get_execution(execution_id)
        if execution is None:
            raise ValueError(f"Execution '{execution_id}' does not exist.")

        try:
            goal = self.db.get_goal(execution["goal_id"])
            plan = ExecutionPlan(**goal["plan"])
            structured_goal = StructuredGoal(**goal["structured_goal"])
            graph = TaskGraph(plan)

            # Execution-scoped mutable state shared by simulated tools
            # (e.g. simulate_failure / repair_service coordinate
            # through this instead of any global/shared variable).
            context: Dict[str, Any] = {}

            def is_approved() -> bool:
                live = self.db.get_execution(execution_id)
                return bool(live and live["approved"])

            def should_cancel() -> bool:
                live = self.db.get_execution(execution_id)
                return bool(live and live["status"] == "cancel_requested")

            def on_event(event_type: str, payload: Dict[str, Any]) -> None:
                self.db.insert_event(execution_id, event_type, payload)
                event_bus.publish(execution_id, event_type, payload)

            executor = build_executor(
                tool_registry=self.tool_registry,
                governance_gate=self.governance_gate,
                context=context,
                auto_approve_high=execution["auto_approve_high"],
                is_approved=is_approved,
                on_governance_event=on_event,
                get_agent_factory=self._get_agent_factory,
            )

            # Constructing these can fail (e.g. a missing/invalid
            # GEMINI_API_KEY) -- that must be caught below, not left
            # to propagate silently and leave the execution stuck at
            # "running" forever.
            runtime = RuntimeEngine(
                graph=graph,
                executor=executor,
                verifier=self._get_verifier(),
                recovery=self._get_recovery(),
                planner=self._get_planner(),
                goal=structured_goal,
                on_event=on_event,
                should_cancel=should_cancel,
            )

            results = runtime.run()
            self.db.update_execution(execution_id, status="completed", result=results)
            return {"status": "completed", "results": results}
        except Exception as error:
            final_status = (
                "cancelled"
                if "cancelled" in str(error).lower()
                else "failed"
            )
            self.db.update_execution(
                execution_id, status=final_status, error=str(error)
            )
            raise
