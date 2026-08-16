from backend.models.schemas import (
    StructuredGoal,
    ExecutionPlan,
    PlanTask,
    VerificationResult,
    RecoveryDecision,
    RecoveryAction,
)

from backend.runtime.task_graph import TaskGraph
from backend.runtime.runtime import RuntimeEngine

class FakePlanner:

    def __init__(self):
        self.calls = 0

    def create_plan(
        self,
        goal,
        failed_task=None,
        verification=None,
        recovery_reason=None,
    ):
        self.calls += 1

        print(
            f"[FakePlanner] Replanning #{self.calls}"
        )

        # Return a new executable plan.
        return ExecutionPlan(
            objective=goal.objective,
            tasks=[
                PlanTask(
                    id="task_2",
                    description="Prepare data with a more specific executable process",
                    dependencies=[],
                    required_capabilities=[
                        "data_analysis"
                    ],
                )
            ],
        )

class FakeVerifier:
    """
    Deterministic verifier.

    First execution fails.
    Replanned execution succeeds.
    """

    def __init__(self):
        self.calls = 0

    def verify(self, task, result):

        self.calls += 1

        print(
            f"[FakeVerifier] Verification #{self.calls}"
        )

        if task.id == "task_1":

            return VerificationResult(
                passed=False,
                score=0.2,
                reasoning=(
                    "Output lacks verifiable "
                    "evidence."
                ),
                issues=[
                    "Missing specific output"
                ],
            )

        return VerificationResult(
            passed=True,
            score=1.0,
            reasoning=(
                "Replanned task produced "
                "specific verifiable output."
            ),
            issues=[],
        )


class FakeRecovery:
    """
    Deterministic recovery engine.

    First failure -> REPLAN.
    """

    def __init__(self):
        self.calls = 0

    def decide(
        self,
        task,
        verification,
        attempts=0,
    ):

        self.calls += 1

        print(
            f"[FakeRecovery] "
            f"Recovery decision #{self.calls}"
        )

        return RecoveryDecision(
            action=RecoveryAction.REPLAN,
            reason=(
                "The task needs a more "
                "specific executable plan."
            ),
            attempts=attempts,
        )


def fake_executor(task):

    print(
        f"[FakeExecutor] Executing "
        f"{task.id}"
    )

    if task.id == "task_1":

        return {
            "status": "completed",
            "output": "Generic output",
        }

    return {
        "status": "completed",
        "output": (
            "Prepared data with "
            "documented preparation steps."
        ),
    }

def test_replanning():

    print("\n=== AEGIS REPLANNING TEST ===")

    # --------------------------------------------------
    # Original goal
    # --------------------------------------------------

    goal = StructuredGoal(
        objective="Prepare and analyze a dataset",
        domain="data_analysis",
        requirements=[
            "Prepare the data"
        ],
        success_criteria=[
            "Produce verifiable prepared data"
        ],
    )

    # --------------------------------------------------
    # Initial plan
    # --------------------------------------------------

    initial_plan = ExecutionPlan(
        objective=goal.objective,
        tasks=[
            PlanTask(
                id="task_1",
                description="Prepare data",
                dependencies=[],
                required_capabilities=[
                    "data_analysis"
                ],
            )
        ],
    )

    graph = TaskGraph(initial_plan)

    # --------------------------------------------------
    # Fake components
    # --------------------------------------------------

    planner = FakePlanner()
    verifier = FakeVerifier()
    recovery = FakeRecovery()

    # --------------------------------------------------
    # Runtime
    # --------------------------------------------------

    runtime = RuntimeEngine(
        graph=graph,
        executor=fake_executor,
        verifier=verifier,
        recovery=recovery,
        planner=planner,
        goal=goal,
    )

    # --------------------------------------------------
    # Execute
    # --------------------------------------------------

    results = runtime.run()

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    assert planner.calls == 1

    assert verifier.calls == 2

    assert recovery.calls == 1

    assert "task_2" in results

    assert (
        results["task_2"]
        ["verification"]["passed"]
        is True
    )

    print(
        "\nReplanning test passed!"
    )


if __name__ == "__main__":
    test_replanning()
