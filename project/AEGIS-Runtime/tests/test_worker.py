from backend.models.schemas import TaskNode

from backend.worker.worker import Worker
from backend.worker.capability_registry import (
    CapabilityRegistry,
)


def test_worker_executes_capability():

    registry = CapabilityRegistry()

    def data_analysis_handler(task):

        return {
            "status": "completed",
            "task_id": task.id,
            "output": "Dataset analyzed successfully.",
        }

    registry.register(
        "data_analysis",
        data_analysis_handler,
    )

    worker = Worker(
        registry=registry
    )

    task = TaskNode(
        id="task_1",
        description="Analyze the dataset.",
        dependencies=[],
        required_capabilities=[
            "data_analysis"
        ],
    )

    result = worker.execute(task)

    assert result is not None

    assert result["status"] == "completed"

    assert result["task_id"] == "task_1"

    assert (
        result["output"]
        == "Dataset analyzed successfully."
    )

    print(
        "\n=== WORKER CAPABILITY TEST PASSED ==="
    )


if __name__ == "__main__":
    test_worker_executes_capability()
