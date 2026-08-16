from backend.runtime.runtime import RuntimeEngine
from backend.runtime.task_graph import TaskGraph
from backend.models.schemas import (
    ExecutionPlan,
    PlanTask,
    StructuredGoal,
    VerificationResult,
    RecoveryDecision,
    RecoveryAction,
)


class FakeVerifier:
    def __init__(self):
        self.calls = 0

    def verify(self, task, result):
        self.calls += 1

        # First attempt fails.
        if self.calls == 1:
            return VerificationResult(
                passed=False,
                score=0.0,
                reasoning="Task output was insufficient.",
                issues=["Incomplete result"],
            )

        # Replanned workflow succeeds.
        return VerificationResult(
            passed=True,
            score=1.0,
            reasoning="Replanned task completed successfully.",
            issues=[],
        )


class FakeRecovery:

    def decide(
        self,
        task,
        verification,
        attempts=0,
    ):

        return RecoveryDecision(
            action=RecoveryAction.REPLAN,
            reason="The workflow needs to be replanned.",
            attempts=attempts,
        )


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

        return ExecutionPlan(
            objective=goal.objective,
            tasks=[
                PlanTask(
                    id="replanned_task",
                    description="Complete the task using a better approach.",
                    dependencies=[],
                    required_capabilities=[
                        "general"
                    ],
                )
            ],
        )


def test_runtime_replan():

    plan = ExecutionPlan(
        objective="Test workflow replanning",
        tasks=[
            PlanTask(
                id="task_1",
                description="Perform the original task.",
                dependencies=[],
                required_capabilities=[
                    "general"
                ],
            )
        ],
    )

    graph = TaskGraph(plan)

    goal = StructuredGoal(
        objective="Complete the test workflow",
        domain="testing",
        inputs=[],
        requirements=[],
        constraints=[],
        success_criteria=[
            "Workflow completes successfully"
        ],
        ambiguities=[],
    )

    execution_log = []

    def execute_task(task):

        execution_log.append(task.id)

        return {
            "task_id": task.id,
            "status": "completed",
            "output": "Task executed successfully.",
        }

    planner = FakePlanner()

    runtime = RuntimeEngine(
        graph=graph,
        executor=execute_task,
        verifier=FakeVerifier(),
        recovery=FakeRecovery(),
        planner=planner,
        goal=goal,
    )

    results = runtime.run()

    # Planner must have been called.
    assert planner.calls == 1

    # Original task executed first.
    assert execution_log[0] == "task_1"

    # Replanned task executed afterwards.
    assert "replanned_task" in execution_log

    # Final task must succeed.
    assert "replanned_task" in results

    assert (
        results["replanned_task"]["verification"]["passed"]
        is True
    )

    print("\nRuntime replan test passed!")


if __name__ == "__main__":
    test_runtime_replan()
