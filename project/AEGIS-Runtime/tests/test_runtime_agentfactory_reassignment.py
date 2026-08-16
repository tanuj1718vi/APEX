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
    """Fails the first execution, passes the second."""

    def __init__(self):
        self.calls = 0

    def verify(self, task, result):
        self.calls += 1

        if self.calls == 1:
            return VerificationResult(
                passed=False,
                score=0.0,
                reasoning="First worker's output was invalid.",
                issues=["Worker failed"],
            )

        return VerificationResult(
            passed=True,
            score=1.0,
            reasoning="Second worker's output was valid.",
            issues=[],
        )


class FakeRecovery:
    """Always asks the runtime to reassign the task."""

    def decide(self, task, verification, attempts=0):
        return RecoveryDecision(
            action=RecoveryAction.REASSIGN,
            reason="Assign the task to another worker.",
            attempts=attempts,
        )


def test_runtime_agentfactory_reassignment_excludes_failed_worker():
    """
    This is the native path: RuntimeEngine is driven purely by
    AgentFactory (no injected `executor` callable doing the
    worker-exclusion bookkeeping itself, unlike
    test_runtime_reassignment.py). The runtime itself must track
    which worker failed and exclude it on the next attempt.
    """

    factory = AgentFactory()

    execution_log = []

    def worker_one(task):
        execution_log.append("worker_1")
        return {"worker": "worker_1", "status": "failed"}

    def worker_two(task):
        execution_log.append("worker_2")
        return {"worker": "worker_2", "status": "completed"}

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
        objective="Test native agent-factory reassignment",
        tasks=[
            PlanTask(
                id="task_1",
                description="Analyze data",
                dependencies=[],
                required_capabilities=["data_analysis"],
            )
        ],
    )

    graph = TaskGraph(plan)

    runtime = RuntimeEngine(
        graph=graph,
        executor=None,
        agent_factory=factory,
        verifier=FakeVerifier(),
        recovery=FakeRecovery(),
    )

    results = runtime.run()

    # worker_1 must be tried first, fail, then be excluded so
    # worker_2 is the one that gets reassigned the task.
    assert execution_log == ["worker_1", "worker_2"]

    assert "task_1" in results
    assert results["task_1"]["verification"]["passed"] is True

    # The runtime must have recorded worker_1 as excluded.
    assert runtime.excluded_workers["task_1"] == ["worker_1"]

    print("\nNative AgentFactory reassignment test passed!")


if __name__ == "__main__":
    test_runtime_agentfactory_reassignment_excludes_failed_worker()
