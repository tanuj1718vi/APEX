from backend.runtime.runtime import RuntimeEngine
from backend.runtime.task_graph import TaskGraph
from backend.models.schemas import (
    ExecutionPlan,
    PlanTask,
    VerificationResult,
    RecoveryDecision,
    RecoveryAction,
)
from backend.agents.agent_factory import AgentFactory


class FakeVerifier:
    def __init__(self):
        self.calls = 0

    def verify(self, task, result):
        self.calls += 1

        # First execution fails.
        if self.calls == 1:
            return VerificationResult(
                passed=False,
                score=0.0,
                reasoning="First worker failed.",
                issues=["Worker failed"],
            )

        # Second execution passes.
        return VerificationResult(
            passed=True,
            score=1.0,
            reasoning="Second worker succeeded.",
            issues=[],
        )


class FakeRecovery:
    def decide(self, task, verification, attempts=0):

        return RecoveryDecision(
            action=RecoveryAction.REASSIGN,
            reason="Assign the task to another worker.",
            attempts=attempts,
        )


def test_runtime_reassignment():

    factory = AgentFactory()

    execution_log = []

    def worker_one(task):
        execution_log.append("worker_1")
        return {
            "worker": "worker_1",
            "status": "failed",
        }

    def worker_two(task):
        execution_log.append("worker_2")
        return {
            "worker": "worker_2",
            "status": "completed",
        }

    factory.register_capability(
        capability="data_analysis",
        executor=worker_one,
        worker_name="worker_1",
    )

    factory.register_capability(
        capability="data_analysis",
        executor=worker_two,
        worker_name="worker_2",
    )

    plan = ExecutionPlan(
        objective="Test reassignment",
        tasks=[
            PlanTask(
                id="task_1",
                description="Analyze data",
                dependencies=[],
                required_capabilities=[
                    "data_analysis"
                ],
            )
        ],
    )

    graph = TaskGraph(plan)

    failed_workers = set()

    def execute_task(task):

        worker = factory.create_worker(
            task,
            excluded_workers=list(failed_workers),
        )

        result = worker.execute(task)

        # If this worker fails, exclude it.
        if result["status"] == "failed":
            failed_workers.add(worker.name)

        print(
            f"Worker selected: {worker.name}"
        )

        return result

    runtime = RuntimeEngine(
        graph=graph,
        executor=execute_task,
        verifier=FakeVerifier(),
        recovery=FakeRecovery(),
    )

    results = runtime.run()

    assert execution_log == [
        "worker_1",
        "worker_2",
    ]

    assert "task_1" in results

    assert results["task_1"]["verification"]["passed"] is True

    print("\nRuntime reassignment test passed!")


if __name__ == "__main__":
    test_runtime_reassignment()
