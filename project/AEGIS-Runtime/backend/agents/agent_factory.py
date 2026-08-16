from typing import Callable, Dict, Any, List, Optional

from backend.models.schemas import TaskNode
from backend.config.config import get_gemini_client, generate_content_with_retry
from backend.memory.memory_manager import MemoryManager


class Worker:
    """
    AI worker dynamically created for an AEGIS task.
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
        return self.executor(task)


class AgentFactory:
    """
    Dynamically creates AI workers based on task requirements.

    Supports:
    - capability-based worker selection
    - multiple workers for the same capability
    - worker exclusion for reassignment
    - Gemini fallback workers
    - shared AEGIS memory
    """

    def __init__(
        self,
        memory: Optional[MemoryManager] = None,
    ):
        self.worker_registry: Dict[
            str, List[Dict[str, Any]]
        ] = {}

        self.client = get_gemini_client()

        # Use the shared MemoryManager when provided.
        # This allows RuntimeEngine and AgentFactory
        # to work with the same memory.
        self.memory = memory or MemoryManager()

    # ---------------------------------------------------------
    # REGISTER WORKER
    # ---------------------------------------------------------

    def register_capability(
        self,
        capability: str,
        executor: Callable[[TaskNode], Any],
        worker_name: Optional[str] = None,
    ) -> None:
        """
        Register a worker for a capability.
        """

        if not capability:
            raise ValueError(
                "Capability cannot be empty."
            )

        if not callable(executor):
            raise TypeError(
                "Executor must be callable."
            )

        if worker_name is None:
            worker_name = f"{capability}_worker"

        worker_definition = {
            "name": worker_name,
            "executor": executor,
        }

        self.worker_registry.setdefault(
            capability,
            []
        ).append(worker_definition)

    # ---------------------------------------------------------
    # CREATE WORKER
    # ---------------------------------------------------------

    def create_worker(
        self,
        task: TaskNode,
        excluded_workers: Optional[List[str]] = None,
    ) -> Worker:
        """
        Create the best available worker for a task.

        excluded_workers is used by REASSIGN so that
        a previously failed worker is not selected again.
        """

        excluded_workers = excluded_workers or []

        # -----------------------------------------------------
        # 1. Find registered specialist
        # -----------------------------------------------------

        for capability in task.required_capabilities:

            workers = self.worker_registry.get(
                capability,
                []
            )

            for worker_definition in workers:

                worker_name = worker_definition["name"]

                if worker_name in excluded_workers:
                    continue

                return Worker(
                    name=worker_name,
                    capabilities=task.required_capabilities,
                    executor=worker_definition["executor"],
                )

        # -----------------------------------------------------
        # 2. No registered specialist available
        # -----------------------------------------------------

        return self._create_ai_worker(
            task,
            excluded_workers,
        )

    # ---------------------------------------------------------
    # GEMINI AI WORKER
    # ---------------------------------------------------------

    def _create_ai_worker(
        self,
        task: TaskNode,
        excluded_workers: Optional[List[str]] = None,
    ) -> Worker:

        excluded_workers = excluded_workers or []

        capabilities = task.required_capabilities

        base_name = (
            f"ai_{capabilities[0]}_worker"
            if capabilities
            else "ai_general_worker"
        )

        worker_name = base_name

        # Make sure reassignment produces a different
        # worker identity.
        counter = 2

        while worker_name in excluded_workers:
            worker_name = f"{base_name}_{counter}"
            counter += 1

        def ai_executor(
            current_task: TaskNode,
        ):

            # -------------------------------------------------
            # Retrieve previous memories for this task.
            # -------------------------------------------------

            previous_memories = (
                self.memory.get_task_memories(
                    current_task.id
                )
            )

            # -------------------------------------------------
            # Build prompt.
            # -------------------------------------------------

            prompt = f"""
You are an execution worker inside AEGIS Runtime.

Your assigned capabilities are:

{capabilities}

Your task is:

{current_task.description}

Previous memories for this task:

{previous_memories}

Use previous memories when they are relevant.

IMPORTANT:

- Previous memories may be incomplete or incorrect.
- Do not blindly trust previous results.
- Improve upon previous attempts when possible.
- Do not claim that you performed physical actions.
- Do not claim that you accessed external systems unless
  access was actually provided.
- Do not invent data.
- Clearly state assumptions.
- Clearly state limitations.
- Provide concrete evidence or output whenever possible.

Execute the task intellectually and provide a useful,
clear and verifiable result.

Return:

1. What you did
2. Your result
3. Evidence supporting the result
4. Important assumptions
5. Any limitations
"""

            # -------------------------------------------------
            # Call Gemini.
            # -------------------------------------------------

            response = generate_content_with_retry(
                self.client,
                model="gemini-2.5-flash",
                contents=prompt,
            )

            # -------------------------------------------------
            # Return structured worker result.
            # -------------------------------------------------

            return {
                "task_id": current_task.id,
                "worker": worker_name,
                "capabilities": capabilities,
                "status": "completed",
                "previous_memories": previous_memories,
                "output": response.text,
            }

        return Worker(
            name=worker_name,
            capabilities=capabilities,
            executor=ai_executor,
        )
