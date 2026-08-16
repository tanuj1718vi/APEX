from backend.models.schemas import ExecutionPlan, PlanTask, TaskStatus
from backend.runtime.task_graph import TaskGraph


def test_task_graph():

    plan = ExecutionPlan(
        objective="Test execution graph",
        tasks=[
            PlanTask(
                id="task_1",
                description="Prepare data",
                dependencies=[],
                required_capabilities=["data_analysis"],
            ),
            PlanTask(
                id="task_2",
                description="Train model",
                dependencies=["task_1"],
                required_capabilities=["machine_learning"],
            ),
            PlanTask(
                id="task_3",
                description="Evaluate model",
                dependencies=["task_2"],
                required_capabilities=["evaluation"],
            ),
        ],
    )

    graph = TaskGraph(plan)

    # Initially only task_1 should be ready.
    ready = graph.get_ready_tasks()

    assert len(ready) == 1
    assert ready[0].id == "task_1"
    assert ready[0].status == TaskStatus.READY

    # Complete task_1.
    graph.mark_running("task_1")
    graph.mark_completed("task_1")

    ready = graph.get_ready_tasks()

    assert len(ready) == 1
    assert ready[0].id == "task_2"

    # Complete task_2.
    graph.mark_running("task_2")
    graph.mark_completed("task_2")

    ready = graph.get_ready_tasks()

    assert len(ready) == 1
    assert ready[0].id == "task_3"

    # Complete task_3.
    graph.mark_running("task_3")
    graph.mark_completed("task_3")

    assert graph.is_complete()

    print("\nTask Graph test passed!")


if __name__ == "__main__":
    test_task_graph()
