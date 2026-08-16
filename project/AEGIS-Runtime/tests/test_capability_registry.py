from backend.worker.capability_registry import (
    CapabilityRegistry,
)


def test_capability_registry():

    registry = CapabilityRegistry()

    def fake_handler(task):
        return {
            "status": "completed",
            "task": task,
        }

    registry.register(
        "data_analysis",
        fake_handler,
    )

    assert registry.has("data_analysis")

    handler = registry.get(
        "data_analysis"
    )

    assert handler is fake_handler

    assert (
        "data_analysis"
        in registry.list_capabilities()
    )

    result = handler("task_1")

    assert result["status"] == "completed"

    print(
        "\n=== CAPABILITY REGISTRY TEST PASSED ==="
    )


if __name__ == "__main__":
    test_capability_registry()
