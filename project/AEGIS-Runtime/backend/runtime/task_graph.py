from typing import Dict, List

from backend.models.schemas import (
    ExecutionPlan,
    TaskNode,
    TaskStatus,
)


class TaskGraph:
    """
    Represents and manages the executable task graph of AEGIS.
    """

    def __init__(self, plan: ExecutionPlan):
        self.tasks: Dict[str, TaskNode] = {}

        for task in plan.tasks:
            self.tasks[task.id] = TaskNode(
                id=task.id,
                description=task.description,
                dependencies=task.dependencies,
                required_capabilities=task.required_capabilities,
            )

        self._update_ready_tasks()

    def _update_ready_tasks(self) -> None:
        """Mark tasks as READY when all dependencies are completed."""

        for task in self.tasks.values():

            if task.status != TaskStatus.PENDING:
                continue

            dependencies_completed = all(
                self.tasks[dependency].status == TaskStatus.COMPLETED
                for dependency in task.dependencies
                if dependency in self.tasks
            )

            if dependencies_completed:
                task.status = TaskStatus.READY

    def get_ready_tasks(self) -> List[TaskNode]:
        """Return tasks that are ready for execution."""

        self._update_ready_tasks()

        return [
            task
            for task in self.tasks.values()
            if task.status == TaskStatus.READY
        ]

    def mark_running(self, task_id: str) -> None:
        """Mark a task as currently running."""

        self._require_task(task_id)
        self.tasks[task_id].status = TaskStatus.RUNNING

    def mark_completed(self, task_id: str) -> None:
        """Mark a task as successfully completed."""

        self._require_task(task_id)
        self.tasks[task_id].status = TaskStatus.COMPLETED
        self._update_ready_tasks()

    def mark_failed(self, task_id: str) -> None:
        """Mark a task as failed."""

        self._require_task(task_id)
        self.tasks[task_id].status = TaskStatus.FAILED
    def reset_for_retry(self, task_id: str) -> None:
        """
        Reset a failed task so the Runtime can execute it again.
        """

        self._require_task(task_id)

        if self.tasks[task_id].status != TaskStatus.FAILED:
            raise ValueError(
            f"Task '{task_id}' is not failed and cannot be retried."
        )

        self.tasks[task_id].status = TaskStatus.READY

    def get_task(self, task_id: str) -> TaskNode:
        """Return a specific task."""

        self._require_task(task_id)
        return self.tasks[task_id]

    def is_complete(self) -> bool:
        """Return True when every task has completed successfully."""

        return all(
            task.status == TaskStatus.COMPLETED
            for task in self.tasks.values()
        )

    def _require_task(self, task_id: str) -> None:
        if task_id not in self.tasks:
            raise ValueError(f"Unknown task ID: {task_id}")
