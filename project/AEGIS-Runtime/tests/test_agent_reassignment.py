from backend.agents.agent_factory import AgentFactory
from backend.models.schemas import TaskNode


def test_agent_reassignment():

    factory = AgentFactory()

    # First worker
    def worker_one(task):
        return "Worker 1 executed"

    # Second worker
    def worker_two(task):
        return "Worker 2 executed"

    factory.register_capability(
        capability="data_analysis",
        executor=worker_one,
        worker_name="data_worker_1",
    )

    factory.register_capability(
        capability="data_analysis",
        executor=worker_two,
        worker_name="data_worker_2",
    )

    task = TaskNode(
        id="task_1",
        description="Analyze dataset",
        required_capabilities=[
            "data_analysis"
        ],
    )

    # First assignment
    worker_1 = factory.create_worker(task)

    assert worker_1.name == "data_worker_1"

    # Reassignment
    worker_2 = factory.create_worker(
        task,
        excluded_workers=[worker_1.name],
    )

    assert worker_2.name == "data_worker_2"

    assert worker_1.name != worker_2.name

    print("\nAgent reassignment test passed!")


if __name__ == "__main__":
    test_agent_reassignment()
