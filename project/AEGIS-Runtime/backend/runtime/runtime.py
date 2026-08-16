from typing import Callable, Dict, Any, List

from backend.runtime.task_graph import TaskGraph
from backend.models.schemas import (
    TaskNode,
    TaskStatus,
    RecoveryAction,
)
from backend.verifier.verifier import VerificationEngine
from backend.recovery.recovery_engine import RecoveryEngine
from backend.memory.memory_manager import MemoryManager

class RuntimeEngine:
    """
    Executes tasks from the AEGIS Task Graph.

    Execution lifecycle:

    Execute
       ↓
    Verify
       ↓
    PASS ─────────→ Complete
       │
       NO
       ↓
    Recovery
       ↓
    Retry / Reassign / Replan / Abort
    """

    def __init__(
        self,
        graph: TaskGraph,
        executor: Callable[[TaskNode], Any],
        verifier=None,
        recovery=None,
        planner=None,
        goal=None,
        memory=None,
        agent_factory=None,
        on_event=None,
        should_cancel=None,
    ):
        self.graph = graph
        self.executor = executor
        self.agent_factory = agent_factory

        # Optional observability/control hooks. Both are additive
        # and default to no-ops so existing callers (and tests)
        # are completely unaffected.
        #
        # on_event(event_type: str, payload: dict) is invoked at
        # every meaningful lifecycle transition so a caller (e.g.
        # APEX's API layer) can stream real runtime state over a
        # WebSocket instead of only seeing print() output.
        #
        # should_cancel() -> bool lets a caller request cooperative
        # cancellation between task iterations.
        self.on_event = on_event
        self.should_cancel = should_cancel
        # These can be injected for testing.
        # This is important because our tests should
        # not consume Gemini API quota.
        self.verifier = verifier
        self.recovery = recovery
        self.planner = planner

        self.goal = goal
        self.memory = memory or MemoryManager()

        # Number of attempts for each task.
        self.attempts: Dict[str, int] = {}

        # Number of workflow replans.
        self.replan_count = 0

        # Safety limit to prevent infinite replanning.
        self.max_replans = 3

        # Which workers have already failed a given task.
        # Used so REASSIGN actually picks a *different*
        # worker instead of silently re-running the same one.
        self.excluded_workers: Dict[str, List[str]] = {}

        # The worker that most recently executed a given task.
        # Populated only when using the AgentFactory path.
        self.last_worker: Dict[str, str] = {}

    def _emit(self, event_type: str, **payload) -> None:
        """
        Fire an observability event if a listener was provided.
        Never lets a broken listener take down execution.
        """

        if self.on_event is None:
            return

        try:
            self.on_event(event_type, payload)
        except Exception as error:
            print(
                f"[Runtime] on_event listener raised "
                f"{error!r}; continuing execution."
            )

    def _execute_task(self, task: TaskNode) -> Any:
        """
        Execute a task using the legacy executor or
        the AgentFactory.

        Priority:
        1. Explicit executor
        2. AgentFactory

        This keeps backward compatibility with
        the existing RuntimeEngine tests.
        """

        # --------------------------------------------------
        # Legacy executor
        # --------------------------------------------------

        if self.executor is not None:
            return self.executor(task)

        # --------------------------------------------------
        # Agent Factory
        # --------------------------------------------------

        if self.agent_factory is not None:

            worker = self.agent_factory.create_worker(
                task,
                excluded_workers=self.excluded_workers.get(
                    task.id, []
                ),
            )

            # Remember which worker handled this task so
            # that a later REASSIGN decision knows who to
            # exclude on the next attempt.
            self.last_worker[task.id] = worker.name

            print(
                f"[AgentFactory] "
                f"Assigned worker '{worker.name}' "
                f"to task '{task.id}'."
            )

            return worker.execute(task)

        # --------------------------------------------------
        # Nothing available
        # --------------------------------------------------

        raise RuntimeError(
            "RuntimeEngine has no executor or agent_factory."
        )

    def run(self) -> Dict[str, Any]:
        """
        Execute the workflow with verification and recovery.
        """

        # Create real Gemini components only when they
        # have not been injected.
        if self.verifier is None:
            self.verifier = VerificationEngine()

        if self.recovery is None:
            self.recovery = RecoveryEngine()

        results: Dict[str, Any] = {}

        self._emit("run_started")

        while not self.graph.is_complete():

            if self.should_cancel is not None and self.should_cancel():
                self._emit("run_cancelled")
                raise RuntimeError(
                    "Execution cancelled by request."
                )

            ready_tasks = self.graph.get_ready_tasks()

            if not ready_tasks:
                raise RuntimeError(
                    "Execution stopped: no ready tasks remain."
                )

            for task in ready_tasks:

                task_id = task.id

                # Track attempts.
                attempt = self.attempts.get(
                    task_id,
                    0,
                )

                print(
                    f"\n[Runtime] Executing task: {task_id}"
                )

                self.graph.mark_running(task_id)

                self._emit(
                    "task_started",
                    task_id=task_id,
                    description=task.description,
                    attempt=attempt,
                )

                try:

                    # ==================================================
                    # 1. EXECUTE
                    # ==================================================

                    result = self._execute_task(task)

                    self.memory.add_memory(
                        memory_type="execution",
                        content=result,
                        task_id=task_id,
                    )

                    print(
                        f"[Runtime] Task {task_id} executed."
                    )

                    self._emit(
                        "task_executed",
                        task_id=task_id,
                        result=result,
                        worker=self.last_worker.get(task_id),
                    )

                    # ==================================================
                    # 2. VERIFY
                    # ==================================================

                    print(
                        f"[Verifier] Checking task {task_id}..."
                    )

                    verification = self.verifier.verify(
                        task,
                        result,
                    )
                    self.memory.add_memory(
                        memory_type="verification",
                        content=verification.model_dump(),
                        task_id=task_id,
                    )

                    print(
                        f"[Verifier] "
                        f"passed={verification.passed} "
                        f"score={verification.score}"
                    )

                    self._emit(
                        "verification_completed",
                        task_id=task_id,
                        passed=verification.passed,
                        score=verification.score,
                        reasoning=verification.reasoning,
                        issues=verification.issues,
                    )

                    # ==================================================
                    # 3. SUCCESS
                    # ==================================================

                    if verification.passed:

                        results[task_id] = {
                            "execution": result,
                            "verification": (
                                verification.model_dump()
                            ),
                        }

                        self.graph.mark_completed(
                            task_id
                        )

                        self.memory.add_memory(
                            memory_type="successful_execution",
                            content={
                                "task_id": task_id,
                                "description": task.description,
                                "result": result,
                                "verification_score": verification.score,
                            },
                            task_id=task_id,
                        )
                        print(
                            f"[Runtime] "
                            f"Task {task_id} "
                            f"completed successfully."
                        )

                        self._emit(
                            "task_completed",
                            task_id=task_id,
                        )

                        continue

                    # ==================================================
                    # 4. VERIFICATION FAILURE
                    # ==================================================

                    print(
                        f"[Verifier] "
                        f"Task {task_id} "
                        f"failed verification."
                    )

                    self.graph.mark_failed(
                        task_id
                    )

                    self._emit(
                        "task_failed",
                        task_id=task_id,
                        reasoning=verification.reasoning,
                        issues=verification.issues,
                    )

                    # ==================================================
                    # 5. RECOVERY
                    # ==================================================

                    recovery_decision = self.recovery.decide(
                        task=task,
                        verification=verification,
                        attempts=attempt,
                    )
                    self.memory.add_memory(
                        memory_type="recovery",
                        content=recovery_decision.model_dump(),
                        task_id=task_id,
                    )
                    print(
                        f"[Recovery] "
                        f"action={recovery_decision.action}"
                    )

                    print(
                        f"[Recovery] "
                        f"{recovery_decision.reason}"
                    )

                    self._emit(
                        "recovery_decided",
                        task_id=task_id,
                        action=recovery_decision.action.value,
                        reason=recovery_decision.reason,
                        attempts=recovery_decision.attempts,
                    )

                    # ==================================================
                    # 6. RETRY
                    # ==================================================

                    if (
                        recovery_decision.action
                        == RecoveryAction.RETRY
                    ):

                        self.attempts[task_id] = (
                            attempt + 1
                        )

                        self.graph.reset_for_retry(
                            task_id
                        )

                        print(
                            f"[Recovery] "
                            f"Retrying {task_id}..."
                        )

                        self._emit(
                            "task_retrying",
                            task_id=task_id,
                            attempt=self.attempts[task_id],
                        )

                        continue

                    # ==================================================
                    # 7. REASSIGN
                    # ==================================================

                    if (
                        recovery_decision.action
                        == RecoveryAction.REASSIGN
                    ):

                        self.attempts[task_id] = (
                            attempt + 1
                        )

                        # Exclude the worker that just failed
                        # this task so the AgentFactory is
                        # forced to pick a different one on
                        # the next attempt. (Only meaningful
                        # when using the AgentFactory path;
                        # a legacy injected executor manages
                        # its own worker selection.)
                        failed_worker = self.last_worker.get(
                            task_id
                        )

                        if failed_worker is not None:

                            excluded = self.excluded_workers.setdefault(
                                task_id, []
                            )

                            if failed_worker not in excluded:
                                excluded.append(failed_worker)

                        self.graph.reset_for_retry(
                            task_id
                        )

                        print(
                            f"[Recovery] "
                            f"Reassigning {task_id} "
                            f"(excluding {self.excluded_workers.get(task_id, [])})..."
                        )

                        self._emit(
                            "task_reassigning",
                            task_id=task_id,
                            excluded_workers=self.excluded_workers.get(
                                task_id, []
                            ),
                        )

                        continue

                    # ==================================================
                    # 8. REPLAN
                    # ==================================================

                    if (
                        recovery_decision.action
                        == RecoveryAction.REPLAN
                    ):

                        # Original goal is required.
                        if self.goal is None:
                            raise RuntimeError(
                                f"Task '{task_id}' "
                                "requires replanning, "
                                "but no original goal "
                                "was provided."
                            )

                        # Planner is required.
                        if self.planner is None:
                            raise RuntimeError(
                                f"Task '{task_id}' "
                                "requires replanning, "
                                "but no planner was provided."
                            )

                        # Prevent infinite replanning.
                        if (
                            self.replan_count
                            >= self.max_replans
                        ):
                            raise RuntimeError(
                                "Maximum workflow "
                                "replan limit reached."
                            )

                        self.replan_count += 1

                        print(
                            f"[Recovery] "
                            f"Replanning workflow "
                            f"for task {task_id}..."
                        )

                        self._emit(
                            "replanning_started",
                            task_id=task_id,
                            replan_count=self.replan_count,
                        )

                        print(
                            f"[Recovery] "
                            f"Replan attempt "
                            f"{self.replan_count}/"
                            f"{self.max_replans}"
                        )

                        # --------------------------------------------------
                        # Generate a new plan.
                        #
                        # NOTE:
                        # The current Planner accepts StructuredGoal.
                        # Therefore we currently regenerate the plan
                        # from the original goal.
                        # --------------------------------------------------

                        new_plan = self.planner.create_plan(
                            goal=self.goal,
                            failed_task=task,
                            verification=verification,
                            recovery_reason=recovery_decision.reason,
                        )
                        print(
                            f"[Planner] "
                            f"New plan generated "
                            f"with "
                            f"{len(new_plan.tasks)} "
                            f"tasks."
                        )

                        # --------------------------------------------------
                        # Replace the current graph.
                        # --------------------------------------------------

                        self.graph = TaskGraph(
                            new_plan
                        )

                        # Reset task attempts and worker
                        # tracking because this is a new
                        # workflow with a new task graph.
                        self.attempts = {}
                        self.excluded_workers = {}
                        self.last_worker = {}

                        print(
                            "[Runtime] "
                            "New task graph loaded."
                        )

                        print(
                            "[Runtime] "
                            "Continuing execution "
                            "with replanned workflow."
                        )

                        self._emit(
                            "replanning_completed",
                            task_count=len(new_plan.tasks),
                        )

                        continue

                    # ==================================================
                    # 9. ABORT
                    # ==================================================

                    if (
                        recovery_decision.action
                        == RecoveryAction.ABORT
                    ):
                        self._emit(
                            "task_aborted",
                            task_id=task_id,
                            reason=recovery_decision.reason,
                        )
                        raise RuntimeError(
                            f"Task '{task_id}' aborted: "
                            f"{recovery_decision.reason}"
                        )

                    # Unknown recovery action.
                    raise RuntimeError(
                        f"Unknown recovery action: "
                        f"{recovery_decision.action}"
                    )

                except Exception as error:

                    # If the task itself has not already
                    # been marked failed, mark it failed.
                    #
                    # Important:
                    # After REPLAN, self.graph may point
                    # to a NEW graph, so we first check
                    # whether the task still exists.

                    try:

                        current_task = self.graph.get_task(
                            task_id
                        )

                        if (
                            current_task.status
                            != TaskStatus.FAILED
                        ):
                            self.graph.mark_failed(
                                task_id
                            )

                    except ValueError:
                        # The old task no longer exists
                        # because the workflow was replaced
                        # during replanning.
                        pass

                    self._emit(
                        "run_failed",
                        task_id=task_id,
                        error=str(error),
                    )

                    raise RuntimeError(
                        f"Task '{task_id}' failed: "
                        f"{error}"
                    ) from error

        self._emit("run_completed", results=results)

        return results

