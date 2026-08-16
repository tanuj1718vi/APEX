from typing import Any, Dict

from backend.agents.goal_analyzer import GoalAnalyzer
from backend.planner.planner import Planner
from backend.runtime.task_graph import TaskGraph
from backend.runtime.runtime import RuntimeEngine
from backend.agents.agent_factory import AgentFactory


class AEGISOrchestrator:
    """
    Main orchestration layer of AEGIS Runtime.

    Converts a natural-language goal into an executable,
    verified, recoverable workflow.
    """

    def __init__(
        self,
        goal_analyzer=None,
        planner=None,
        agent_factory=None,
        verifier=None,
        recovery=None,
        memory=None,
    ):
        self.goal_analyzer = (
            goal_analyzer
            or GoalAnalyzer()
        )

        self.planner = (
            planner
            or Planner()
        )

        self.agent_factory = (
            agent_factory
            or AgentFactory()
        )

        self.verifier = verifier
        self.recovery = recovery
        self.memory = memory

    def run(
        self,
        user_goal: str,
        on_event=None,
        should_cancel=None,
    ) -> Dict[str, Any]:
        """
        Execute a complete AEGIS workflow.

        Pipeline:

        User Goal
            ↓
        Goal Analyzer
            ↓
        Structured Goal
            ↓
        Planner
            ↓
        Execution Plan
            ↓
        Task Graph
            ↓
        Runtime Engine
            ↓
        Verified Result
        """

        if not user_goal or not user_goal.strip():
            raise ValueError(
                "User goal cannot be empty."
            )

        def emit(event_type, **payload):
            if on_event is not None:
                try:
                    on_event(event_type, payload)
                except Exception as error:
                    print(
                        f"[Orchestrator] on_event listener "
                        f"raised {error!r}; continuing."
                    )

        print("\n====================================")
        print("        AEGIS RUNTIME START")
        print("====================================")

        # ==================================================
        # 1. ANALYZE GOAL
        # ==================================================

        print("\n[Goal Analyzer] Analyzing user goal...")
        emit("goal_analysis_started", goal=user_goal)

        structured_goal = (
            self.goal_analyzer.analyze(
                user_goal
            )
        )

        print(
            "[Goal Analyzer] "
            "Structured goal created."
        )
        emit(
            "goal_analyzed",
            structured_goal=structured_goal.model_dump(),
        )

        # ==================================================
        # 2. CREATE PLAN
        # ==================================================

        print("\n[Planner] Creating execution plan...")
        emit("planning_started")

        execution_plan = (
            self.planner.create_plan(
                structured_goal
            )
        )

        print(
            "[Planner] "
            f"Created plan with "
            f"{len(execution_plan.tasks)} tasks."
        )
        emit(
            "plan_generated",
            plan=execution_plan.model_dump(),
        )

        # ==================================================
        # 3. CREATE TASK GRAPH
        # ==================================================

        print("\n[TaskGraph] Building task graph...")

        graph = TaskGraph(
            execution_plan
        )

        print(
            "[TaskGraph] "
            "Task graph ready."
        )
        emit(
            "task_graph_created",
            task_ids=[t.id for t in execution_plan.tasks],
        )

        # ==================================================
        # 4. CREATE RUNTIME
        # ==================================================

        print("\n[Runtime] Starting execution...")

        runtime = RuntimeEngine(
            graph=graph,
            executor=None,
            verifier=self.verifier,
            recovery=self.recovery,
            planner=self.planner,
            goal=structured_goal,
            memory=self.memory,
            agent_factory=self.agent_factory,
            on_event=on_event,
            should_cancel=should_cancel,
        )

        # ==================================================
        # 5. EXECUTE WORKFLOW
        # ==================================================

        results = runtime.run()

        # ==================================================
        # 6. FINAL RESULT
        # ==================================================

        print("\n====================================")
        print("       AEGIS RUNTIME COMPLETE")
        print("====================================")

        return {
            "goal": structured_goal.model_dump(),
            "plan": execution_plan.model_dump(),
            "results": results,
        }
