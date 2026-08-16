from typing import Any, Callable, Dict, List, Optional

from backend.models.schemas import TaskNode


class Worker:
    """
    Represents an executable worker in AEGIS.

    A worker has:
    - a name
    - one or more capabilities
    - an executor function
    """

    def __init__(
        self,
        name: str,
        capabilities: List[str],
        executor: Callable[[TaskNode], Any],
    ):
        self.name = name
        self.capabilities = capabilities
        self.executor = executor

    def execute(self, task: TaskNode) -> Any:
        """
        Execute the task using this worker.
        """

        if task is None:
            raise ValueError(
                "Task cannot be None."
            )

        return self.executor(task)


class AgentFactory:
    """
    Creates and assigns workers to AEGIS tasks.

    The factory maintains a pool of workers grouped by
    their capabilities.

    Example:

        data_analysis
            ├── data_worker_1
            └── data_worker_2

    The factory can also exclude workers during
    reassignment.
    """

    def __init__(self):
        # capability -> list of workers
        self._workers: Dict[str, List[Worker]] = {}

    # ==================================================
    # REGISTER CAPABILITY
    # ==================================================

    def register_capability(
        self,
        capability: str,
        executor: Callable[[TaskNode], Any],
        worker_name: str,
    ) -> None:
        """
        Register a worker capable of performing a capability.
        """

        if not capability or not capability.strip():
            raise ValueError(
                "Capability cannot be empty."
            )

        if not worker_name or not worker_name.strip():
            raise ValueError(
                "Worker name cannot be empty."
            )

        if not callable(executor):
            raise TypeError(
                "Executor must be callable."
            )

        worker = Worker(
            name=worker_name,
            capabilities=[capability],
            executor=executor,
        )

        if capability not in self._workers:
            self._workers[capability] = []

        self._workers[capability].append(worker)

    # ==================================================
    # CREATE WORKER
    # ==================================================

    def create_worker(
        self,
        task: TaskNode,
        excluded_workers: Optional[List[str]] = None,
    ) -> Worker:
        """
        Select a worker capable of executing the task.

        Workers listed in excluded_workers are ignored.

        The factory selects the first available worker
        matching one of the task's required capabilities.
        """

        if task is None:
            raise ValueError(
                "Task cannot be None."
            )

        if not task.required_capabilities:
            raise ValueError(
                f"Task '{task.id}' has no "
                "required capabilities."
            )

        excluded_workers = excluded_workers or []

        # ----------------------------------------------
        # Search capabilities in task order
        # ----------------------------------------------

        for capability in task.required_capabilities:

            workers = self._workers.get(
                capability,
                [],
            )

            # ------------------------------------------
            # Find first available worker
            # ------------------------------------------

            for worker in workers:

                if worker.name in excluded_workers:
                    continue

                return worker

        # ----------------------------------------------
        # No worker found
        # ----------------------------------------------

        raise RuntimeError(
            f"No available worker can execute "
            f"task '{task.id}'. "
            f"Required capabilities: "
            f"{task.required_capabilities}. "
            f"Excluded workers: "
            f"{excluded_workers}"
        )

    # ==================================================
    # LIST WORKERS
    # ==================================================

    def list_workers(self) -> List[Worker]:
        """
        Return all registered workers.
        """

        workers = []

        for capability_workers in self._workers.values():
            workers.extend(capability_workers)

        return workers

    # ==================================================
    # LIST CAPABILITIES
    # ==================================================

    def list_capabilities(self) -> List[str]:
        """
        Return all registered capabilities.
        """

        return list(self._workers.keys())
