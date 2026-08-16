from backend.memory.memory_manager import MemoryManager


def test_memory_retrieval():

    memory = MemoryManager()

    memory.add_memory(
        memory_type="execution",
        content="Data preparation completed.",
        task_id="task_1",
    )

    memory.add_memory(
        memory_type="verification",
        content="Verification passed.",
        task_id="task_1",
    )

    memory.add_memory(
        memory_type="execution",
        content="Model training completed.",
        task_id="task_2",
    )

    task_1_memories = memory.get_task_memories("task_1")

    assert len(task_1_memories) == 2

    assert task_1_memories[0]["type"] == "execution"
    assert task_1_memories[1]["type"] == "verification"

    task_2_memories = memory.get_task_memories("task_2")

    assert len(task_2_memories) == 1
    assert task_2_memories[0]["type"] == "execution"

    unknown_memories = memory.get_task_memories("task_999")

    assert unknown_memories == []

    print("\nMemory retrieval test passed!")


if __name__ == "__main__":
    test_memory_retrieval()
def test_memory_search():

    memory = MemoryManager()

    memory.add_memory(
        memory_type="execution",
        content="Prepared students.csv successfully.",
        task_id="task_1",
    )

    memory.add_memory(
        memory_type="execution",
        content="Trained random forest model.",
        task_id="task_2",
    )

    memory.add_memory(
        memory_type="verification",
        content="Student data preparation passed verification.",
        task_id="task_1",
    )

    results = memory.search(
        "students data preparation"
    )

    assert results

    assert any(
        "students.csv"
        in str(memory_item["content"])
        for memory_item in results
    )

    print("\nMemory search test passed!")
