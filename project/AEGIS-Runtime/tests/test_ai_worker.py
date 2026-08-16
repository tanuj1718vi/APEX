from backend.agents.agent_factory import AgentFactory
from backend.models.schemas import TaskNode


def test_ai_worker():

    factory = AgentFactory()

    task = TaskNode(
        id="task_1",
        description="Explain what machine learning is",
        required_capabilities=["machine_learning"],
    )

    worker = factory.create_worker(task)

    assert worker.name == "ai_machine_learning_worker"
    assert "machine_learning" in worker.capabilities
    assert callable(worker.executor)

    print("\nAI worker creation test passed!")


if __name__ == "__main__":
    test_ai_worker()
