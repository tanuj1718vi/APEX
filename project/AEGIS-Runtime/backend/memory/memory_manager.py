from typing import List, Dict, Any, Optional


class MemoryManager:

    def __init__(self):
        self.memories: List[Dict[str, Any]] = []

    def add_memory(
        self,
        memory_type: str,
        content: Any,
        task_id: Optional[str] = None,
    ):
        """
        Store a memory.

        A memory can optionally be associated
        with a specific task.
        """

        self.memories.append(
            {
                "type": memory_type,
                "content": content,
                "task_id": task_id,
            }
        )

    def get_memories(self) -> List[Dict]:
        """
        Return all stored memories.
        """

        return self.memories

    def get_by_type(
        self,
        memory_type: str,
    ) -> List[Dict]:
        """
        Return memories of a specific type.
        """

        return [
            memory
            for memory in self.memories
            if memory.get("type") == memory_type
        ]

    def get_by_task(
        self,
        task_id: str,
    ) -> List[Dict]:
        """
        Return memories associated with a specific task.
        """

        return [
            memory
            for memory in self.memories
            if memory.get("task_id") == task_id
        ]

    def get_task_memories(
        self,
        task_id: str,
    ) -> List[Dict]:
        """
        Alias for task-based memory retrieval.
        """

        return self.get_by_task(task_id)

    def get_last_memory(self) -> Optional[Dict]:
        """
        Return the most recently stored memory.
        """

        if not self.memories:
            return None

        return self.memories[-1]

    def clear(self):
        """
        Remove all memories.
        """

        self.memories.clear()
    def search(
        self,
        query: str,
    ) -> List[Dict]:
        """
        Retrieve memories whose textual content
        is relevant to the query.
        """

        if not query or not query.strip():
            return []

        query_words = set(
            query.lower().split()
        )

        matches = []

        for memory in self.memories:

            content = str(
                memory.get("content", "")
            ).lower()

            score = sum(
                1
                for word in query_words
                if word in content
            )

            if score > 0:
                matches.append(
                    (score, memory)
                )

        matches.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            memory
            for _, memory in matches
        ]
