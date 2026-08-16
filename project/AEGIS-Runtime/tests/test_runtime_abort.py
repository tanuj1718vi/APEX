from backend.runtime.runtime import RuntimeEngine
from backend.runtime.task_graph import TaskGraph
from backend.models.schemas import (
    ExecutionPlan,
    PlanTask,
    VerificationResult,
    RecoveryDecision,
    RecoveryAction,
)


class FakeVerifier:
    """
    Always fails verification so that
    the recovery engine gets called.
    """

    def verify(self, task, result):
        return VerificationResult(
            passed=False,
            score=0.0,
            reasoning="Task cannot be verified successfully.",
            issues=["Unrecoverable task failure"],
        )


class FakeRecovery:
    """
    Always chooses ABORT.
    """

    def decide(
        self,
        task,
        verification,
        attempts=0,
    ):
        return RecoveryDecision(
            action=RecoveryAction.ABORT,
            reason="The task cannot be safely recovered.",
            attempts=attempts,
        )


def test_runtime_abort():

    # ---------------------------------------------------------
    # 1. Create test plan
    # ---------------------------------------------------------

    plan = ExecutionPlan(
        objective="Test runtime abort",
        tasks=[
            PlanTask(
                id="task_1",
                description="Perform an unrecoverable task",
                dependencies=[],
                required_capabilities=[
                    "general"
                ],
            )
        ],
    )

    # ---------------------------------------------------------
    # 2. Create task graph
    # ---------------------------------------------------------

    graph = TaskGraph(plan)

    # ---------------------------------------------------------
    # 3. Executor
    # ---------------------------------------------------------

    execution_log = []

    def execute_task(task):

        execution_log.append(task.id)

        return {
            "task_id": task.id,
            "status": "completed",
            "output": "Task executed.",
        }

    # ---------------------------------------------------------
    # 4. Create RuntimeEngine
    # ---------------------------------------------------------

    runtime = RuntimeEngine(
        graph=graph,
        executor=execute_task,
        verifier=FakeVerifier(),
        recovery=FakeRecovery(),
    )

    # ---------------------------------------------------------
    # 5. Runtime should abort
    # ---------------------------------------------------------

    try:

        runtime.run()

        # If runtime.run() does not raise an error,
        # the ABORT path is broken.

        assert False, (
            "Runtime should have raised RuntimeError "
            "for ABORT action."
        )

    except RuntimeError as error:

        error_message = str(error)

        assert "task_1" in error_message
        assert "aborted" in error_message
        assert (
            "cannot be safely recovered"
            in error_message
        )

    # ---------------------------------------------------------
    # 6. Verify task was actually executed
    # ---------------------------------------------------------

    assert execution_log == [
        "task_1"
    ]

    print("\nRuntime abort test passed!")


if __name__ == "__main__":
    test_runtime_abort()
