from typing import Any

from backend.models.schemas import TaskNode
from backend.worker.capability_registry import CapabilityRegistry


class Worker:
    """
    Executes tasks using registered capabilities.
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
    ):
        self.registry = registry

    def execute(
        self,
        task: TaskNode,
    ) -> Any:
        """
        Execute a task using one of its required capabilities.
        """

        if not task.required_capabilities:
            raise ValueError(
                f"Task '{task.id}' has no required capabilities."
            )

        # Find the first capability that can execute the task.
        for capability in task.required_capabilities:

            if self.registry.has(capability):

                handler = self.registry.get(
                    capability
                )

                return handler(task)

        raise RuntimeError(
            f"No registered capability can execute "
            f"task '{task.id}'. "
            f"Required capabilities: "
            f"{task.required_capabilities}"
        )
