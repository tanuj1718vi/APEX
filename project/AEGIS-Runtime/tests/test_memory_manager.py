from backend.memory.memory_manager import MemoryManager


def test_memory_manager():

    memory = MemoryManager()

    # Add goal memory
    memory.add_memory(
        memory_type="goal",
        content="Analyze students.csv",
    )

    # Add execution memory
    memory.add_memory(
        memory_type="execution",
        content={
            "status": "completed",
            "rows": 100,
        },
        task_id="task_1",
    )

    # Add verification memory
    memory.add_memory(
        memory_type="verification",
        content={
            "passed": True,
            "score": 0.95,
        },
        task_id="task_1",
    )

    # ---------------------------------------------------------
    # Test all memories
    # ---------------------------------------------------------

    memories = memory.get_memories()

    assert len(memories) == 3

    # ---------------------------------------------------------
    # Test type filtering
    # ---------------------------------------------------------

    execution_memories = memory.get_by_type(
        "execution"
    )

    assert len(execution_memories) == 1

    # ---------------------------------------------------------
    # Test task filtering
    # ---------------------------------------------------------

    task_memories = memory.get_by_task(
        "task_1"
    )

    assert len(task_memories) == 2

    # ---------------------------------------------------------
    # Test last memory
    # ---------------------------------------------------------

    last_memory = memory.get_last_memory()

    assert last_memory is not None
    assert last_memory["type"] == "verification"

    # ---------------------------------------------------------
    # Test clear
    # ---------------------------------------------------------

    memory.clear()

    assert len(memory.get_memories()) == 0

    print("\nMemory Manager test passed!")


if __name__ == "__main__":
    test_memory_manager()
