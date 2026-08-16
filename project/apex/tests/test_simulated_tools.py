from types import SimpleNamespace

from apex.backend.tools.simulated_tools import build_default_tool_registry
from apex.backend.tools.registry import ToolNotFoundError


def _task(description="test task"):
    return SimpleNamespace(id="task_1", description=description)


def test_registry_lists_all_eight_tools():
    registry = build_default_tool_registry()
    names = {t["name"] for t in registry.list_tools()}
    assert names == {
        "system_status",
        "get_metrics",
        "analyze_data",
        "calculate",
        "simulate_failure",
        "repair_service",
        "verify_system",
        "generate_report",
    }


def test_unknown_tool_raises():
    registry = build_default_tool_registry()
    try:
        registry.execute("does_not_exist", _task())
        assert False, "expected ToolNotFoundError"
    except ToolNotFoundError:
        pass


def test_system_status_reflects_context():
    registry = build_default_tool_registry()
    healthy = registry.execute("system_status", _task(), {"service_state": "healthy"})
    assert healthy["system_status"] == "nominal"

    broken = registry.execute("system_status", _task(), {"service_state": "broken"})
    assert broken["system_status"] == "degraded"


def test_calculate_sums_numbers_in_description():
    registry = build_default_tool_registry()
    result = registry.execute(
        "calculate", _task("Add 12 and 30 together"), {}
    )
    assert result["status"] == "completed"
    assert result["result"] == 42.0


def test_calculate_fails_without_numbers():
    registry = build_default_tool_registry()
    result = registry.execute("calculate", _task("Do some math"), {})
    assert result["status"] == "failed"


def test_repair_service_fails_first_then_succeeds():
    """
    This is the core of the recovery demo: repair_service must fail
    on the first attempt and succeed once the dependency has been
    reset (i.e. on a second call against the same context).
    """
    registry = build_default_tool_registry()
    context = {}

    registry.execute("simulate_failure", _task(), context)
    assert context["service_state"] == "broken"

    first = registry.execute("repair_service", _task(), context)
    assert first["status"] == "failed"
    assert context["service_state"] == "failed"

    second = registry.execute("repair_service", _task(), context)
    assert second["status"] == "completed"
    assert context["service_state"] == "healthy"


def test_verify_system_matches_after_successful_repair():
    registry = build_default_tool_registry()
    context = {}
    registry.execute("simulate_failure", _task(), context)
    registry.execute("repair_service", _task(), context)  # fails (attempt 1)
    registry.execute("repair_service", _task(), context)  # succeeds (attempt 2)

    verification = registry.execute("verify_system", _task(), context)
    assert verification["match"] is True
    assert verification["observed_state"] == "healthy"


if __name__ == "__main__":
    test_registry_lists_all_eight_tools()
    test_unknown_tool_raises()
    test_system_status_reflects_context()
    test_calculate_sums_numbers_in_description()
    test_calculate_fails_without_numbers()
    test_repair_service_fails_first_then_succeeds()
    test_verify_system_matches_after_successful_repair()
    print("All simulated tool tests passed!")
