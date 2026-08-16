from backend.agents.agent_factory import AgentFactory
from backend.models.schemas import TaskNode


def test_agent_factory():

    factory = AgentFactory()

    # ---------------------------------------------------------
    # Worker 1
    # ---------------------------------------------------------

    def data_analysis_worker_1(task):
        return (
            f"Analyzed by worker 1: "
            f"{task.description}"
        )

    factory.register_capability(
        capability="data_analysis",
        executor=data_analysis_worker_1,
        worker_name="data_worker_1",
    )

    # ---------------------------------------------------------
    # Worker 2
    # ---------------------------------------------------------

    def data_analysis_worker_2(task):
        return (
            f"Analyzed by worker 2: "
            f"{task.description}"
        )

    factory.register_capability(
        capability="data_analysis",
        executor=data_analysis_worker_2,
        worker_name="data_worker_2",
    )

    # ---------------------------------------------------------
    # Create task
    # ---------------------------------------------------------

    task = TaskNode(
        id="task_1",
        description="Analyze students.csv",
        dependencies=[],
        required_capabilities=[
            "data_analysis"
        ],
    )

    # ---------------------------------------------------------
    # First assignment
    # ---------------------------------------------------------

    worker = factory.create_worker(task)

    print(
        f"\nFirst worker: {worker.name}"
    )

    result = worker.execute(task)

    assert worker.name == "data_worker_1"

    assert (
        "data_analysis"
        in worker.capabilities
    )

    assert result == (
        "Analyzed by worker 1: "
        "Analyze students.csv"
    )

    # ---------------------------------------------------------
    # Reassignment
    # ---------------------------------------------------------

    reassigned_worker = factory.create_worker(
        task,
        excluded_workers=[
            worker.name
        ],
    )

    print(
        f"Reassigned worker: "
        f"{reassigned_worker.name}"
    )

    reassigned_result = (
        reassigned_worker.execute(task)
    )

    # The new worker must be different.
    assert (
        reassigned_worker.name
        != worker.name
    )

    # It must still have the required capability.
    assert (
        "data_analysis"
        in reassigned_worker.capabilities
    )

    assert (
        reassigned_worker.name
        == "data_worker_2"
    )

    assert reassigned_result == (
        "Analyzed by worker 2: "
        "Analyze students.csv"
    )

    print(
        "\nAgent Factory test passed!"
    )


if __name__ == "__main__":
    test_agent_factory()
