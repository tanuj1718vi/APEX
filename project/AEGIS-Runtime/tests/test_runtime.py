def test_runtime_memory():
    from backend.models.schemas import (
    ExecutionPlan,
    PlanTask,
    VerificationResult,
)
    from backend.memory.memory_manager import MemoryManager
    from backend.runtime.task_graph import TaskGraph
    from backend.runtime.runtime import RuntimeEngine

    class MemoryTestVerifier:
        def verify(self, task, result):
            return VerificationResult(
                passed=True,
                score=1.0,
                reasoning="Test result accepted.",
                issues=[],
            )

    memory = MemoryManager()

    plan = ExecutionPlan(
        objective="Test runtime memory",
        tasks=[
            PlanTask(
                id="task_1",
                description="Prepare data",
                dependencies=[],
                required_capabilities=["data_analysis"],
            ),
        ],
    )

    graph = TaskGraph(plan)

    execution_order = []

    def fake_executor(task):
        execution_order.append(task.id)

        return {
            "status": "completed",
            "output": "Data prepared successfully",
        }

    runtime = RuntimeEngine(
        graph=graph,
        executor=fake_executor,
        verifier=MemoryTestVerifier(),
        memory=memory,
    )

    results = runtime.run()

    assert "task_1" in results

    memories = memory.get_memories()

    assert len(memories) >= 2

    memory_types = [
        item["type"]
        for item in memories
    ]

    assert "execution" in memory_types
    assert "verification" in memory_types

    for item in memories:
        assert item["task_id"] == "task_1"

    print("\nRuntime memory test passed!")


if __name__ == "__main__":
    test_runtime_memory()
