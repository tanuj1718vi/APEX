"""
Safe simulated tools for the APEX MVP.

None of these touch the real filesystem, network, or shell. They are
deterministic Python functions that mutate an execution-scoped
`context` dict, which is exactly what the spec calls for:

    "For the hackathon MVP, use safe simulated tools.
     No arbitrary command execution."

`repair_service` is deliberately designed to fail on its first call
and succeed on a subsequent call *if* the dependency has been reset
in between (`simulate_failure` / the recovery retry resets it). This
gives APEX a real, reproducible failure -> recovery -> success cycle
instead of a scripted/faked one.
"""

import re
from typing import Any, Dict

from apex.backend.governance.governance import RiskLevel
from apex.backend.tools.registry import ToolDefinition, ToolRegistry


def _system_status(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    service_state = context.get("service_state", "healthy")
    return {
        "status": "completed",
        "system_status": "nominal" if service_state != "broken" else "degraded",
        "services": {
            "api": "healthy",
            "database": "healthy",
            "queue": "healthy" if service_state != "broken" else "failed",
        },
    }


def _get_metrics(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    service_state = context.get("service_state", "healthy")
    return {
        "status": "completed",
        "cpu_percent": 71 if service_state == "broken" else 34,
        "memory_percent": 66 if service_state == "broken" else 41,
        "requests_per_minute": 340 if service_state == "broken" else 1180,
    }


def _analyze_data(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "completed",
        "summary": f"Analysis complete for: {task.description}",
        "findings": [
            "No anomalies detected in the sampled window."
            if context.get("service_state", "healthy") != "broken"
            else "Elevated error rate correlated with queue service.",
        ],
    }


_NUMBER_RE = re.compile(r"-?\d+(\.\d+)?")


def _calculate(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    # Use finditer (not findall) because the pattern has a capture
    # group, which would make findall return partial-match tuples.
    numbers = [float(m.group()) for m in _NUMBER_RE.finditer(task.description)]

    if not numbers:
        return {
            "status": "failed",
            "detail": "No numeric operands found in task description.",
        }

    total = sum(numbers)
    return {
        "status": "completed",
        "operands": numbers,
        "result": total,
        "detail": f"Summed {len(numbers)} operand(s) from the task description.",
    }


def _simulate_failure(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    context["service_state"] = "broken"
    context["repair_attempts"] = 0
    return {
        "status": "completed",
        "service_status": "broken",
        "detail": "Failure condition injected for the recovery demonstration.",
    }


def _repair_service(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    attempt = context.get("repair_attempts", 0)
    context["repair_attempts"] = attempt + 1

    if attempt == 0:
        # Intentional, controlled first-attempt failure: the
        # dependency has not been reset yet.
        context["service_state"] = "failed"
        return {
            "status": "failed",
            "service_status": "failed",
            "attempt": attempt + 1,
            "detail": (
                "Repair attempt failed: dependency is in a broken "
                "state and must be reset before the service can "
                "restart cleanly."
            ),
        }

    # On any subsequent attempt the dependency has been reset
    # (by recovery re-running this tool), so the repair succeeds.
    context["service_state"] = "healthy"
    return {
        "status": "completed",
        "service_status": "healthy",
        "attempt": attempt + 1,
        "detail": "Dependency reset; service restarted cleanly.",
    }


def _verify_system(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    expected = "healthy"
    observed = context.get("service_state", "healthy")
    return {
        "status": "completed",
        "expected_state": expected,
        "observed_state": observed,
        "match": expected == observed,
    }


def _generate_report(task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    service_state = context.get("service_state", "healthy")
    repair_attempts = context.get("repair_attempts", 0)
    lines = [
        f"Final service state: {service_state}",
        f"Repair attempts made: {repair_attempts}",
    ]
    return {
        "status": "completed",
        "report": "\n".join(lines),
    }


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="system_status",
            description="Report overall system and service health.",
            input_schema={"type": "object", "properties": {}},
            output_schema={
                "type": "object",
                "properties": {
                    "system_status": {"type": "string"},
                    "services": {"type": "object"},
                },
            },
            risk_level=RiskLevel.LOW,
            handler=_system_status,
        )
    )

    registry.register(
        ToolDefinition(
            name="get_metrics",
            description="Fetch current CPU, memory, and throughput metrics.",
            input_schema={"type": "object", "properties": {}},
            output_schema={
                "type": "object",
                "properties": {
                    "cpu_percent": {"type": "number"},
                    "memory_percent": {"type": "number"},
                    "requests_per_minute": {"type": "number"},
                },
            },
            risk_level=RiskLevel.LOW,
            handler=_get_metrics,
        )
    )

    registry.register(
        ToolDefinition(
            name="analyze_data",
            description="Analyze the current system state for anomalies.",
            input_schema={
                "type": "object",
                "properties": {"description": {"type": "string"}},
            },
            output_schema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "findings": {"type": "array"},
                },
            },
            risk_level=RiskLevel.LOW,
            handler=_analyze_data,
        )
    )

    registry.register(
        ToolDefinition(
            name="calculate",
            description=(
                "Extract numeric operands from the task description "
                "and sum them."
            ),
            input_schema={
                "type": "object",
                "properties": {"description": {"type": "string"}},
            },
            output_schema={
                "type": "object",
                "properties": {"result": {"type": "number"}},
            },
            risk_level=RiskLevel.LOW,
            handler=_calculate,
        )
    )

    registry.register(
        ToolDefinition(
            name="simulate_failure",
            description=(
                "Deliberately inject a failure condition into the "
                "simulated service, for demonstration purposes."
            ),
            input_schema={"type": "object", "properties": {}},
            output_schema={
                "type": "object",
                "properties": {"service_status": {"type": "string"}},
            },
            risk_level=RiskLevel.MEDIUM,
            handler=_simulate_failure,
        )
    )

    registry.register(
        ToolDefinition(
            name="repair_service",
            description=(
                "Attempt to repair the simulated service. Fails if "
                "the underlying dependency has not been reset."
            ),
            input_schema={"type": "object", "properties": {}},
            output_schema={
                "type": "object",
                "properties": {"service_status": {"type": "string"}},
            },
            risk_level=RiskLevel.HIGH,
            handler=_repair_service,
        )
    )

    registry.register(
        ToolDefinition(
            name="verify_system",
            description=(
                "Compare the expected service state against the "
                "actual observed state."
            ),
            input_schema={"type": "object", "properties": {}},
            output_schema={
                "type": "object",
                "properties": {
                    "expected_state": {"type": "string"},
                    "observed_state": {"type": "string"},
                    "match": {"type": "boolean"},
                },
            },
            risk_level=RiskLevel.LOW,
            handler=_verify_system,
        )
    )

    registry.register(
        ToolDefinition(
            name="generate_report",
            description="Generate a final human-readable execution report.",
            input_schema={"type": "object", "properties": {}},
            output_schema={
                "type": "object",
                "properties": {"report": {"type": "string"}},
            },
            risk_level=RiskLevel.LOW,
            handler=_generate_report,
        )
    )

    return registry
