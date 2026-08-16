from backend.memory.memory_manager import MemoryManager


def test_memory_manager():

    memory = MemoryManager()

    # Add execution memory
    memory.add_memory(
        memory_type="execution",
        content={
            "status": "completed",
            "output": "Data prepared successfully",
        },
        task_id="task_1",
    )

    # Add verification memory
    memory.add_memory(
        memory_type="verification",
        content={
            "passed": True,
            "score": 1.0,
        },
        task_id="task_1",
    )

    memories = memory.get_memories()

    # We should have two memories
    assert len(memories) == 2

    # Check first memory
    assert memories[0]["type"] == "execution"
    assert memories[0]["task_id"] == "task_1"

    # Check second memory
    assert memories[1]["type"] == "verification"
    assert memories[1]["task_id"] == "task_1"

    # Test clear
    memory.clear()

    assert len(memory.get_memories()) == 0

    print("\nMemory Manager test passed!")


if __name__ == "__main__":
    test_memory_manager()
