from backend.tools.tool_manager import ToolManager


def test_tool_manager():

    manager = ToolManager()

    def add_numbers(a, b):
        return a + b

    manager.register(
        name="add_numbers",
        tool=add_numbers,
    )

    result = manager.execute(
        "add_numbers",
        10,
        20,
    )

    assert result == 30
    assert "add_numbers" in manager.list_tools()

    print("\nTool Manager test passed!")


if __name__ == "__main__":
    test_tool_manager()
