"""
Builds the `executor` callable that RuntimeEngine.run() drives.

Routing rule: a task's FIRST required_capability is treated as the
tool name. If that name is registered in the ToolRegistry, the task
is a deterministic, safe, simulated tool call. Governance is
evaluated first: LOW/MEDIUM auto-execute, HIGH/CRITICAL are checked
against the execution's approval state and raise
GovernanceBlockedError otherwise, which RuntimeEngine will treat as a
normal task failure (and route into AEGIS's existing recovery logic).

If the required capability does NOT match a registered tool, the
task falls back to AEGIS's own Gemini-backed AgentFactory AI worker,
so free-form goals (not just the fixed demo) still produce a real
result -- Gemini reasons about the task instead of an unknown tool
silently failing.
"""

from typing import Any, Callable, Dict, Optional

from apex.backend.governance.governance import (
    GovernanceGate,
    GovernanceBlockedError,
)
from apex.backend.tools.registry import ToolRegistry


def build_executor(
    tool_registry: ToolRegistry,
    governance_gate: GovernanceGate,
    context: Dict[str, Any],
    auto_approve_high: bool,
    is_approved: Callable[[], bool],
    on_governance_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    get_agent_factory: Optional[Callable[[], Any]] = None,
) -> Callable[[Any], Dict[str, Any]]:
    """
    Returns a callable(task) -> dict suitable for
    RuntimeEngine(executor=...).

    `is_approved` is a callable rather than a plain bool so that an
    approval granted mid-run (via POST /executions/{id}/approve,
    checked between task iterations) is picked up immediately without
    having to reconstruct the executor.

    `get_agent_factory` is a callable (not an instance) so the real,
    Gemini-backed AgentFactory is only constructed the moment a task
    actually falls back to it -- plans that only use registered
    simulated tools never touch Gemini or need an API key at all.
    """

    def emit_governance(event_type: str, **payload) -> None:
        if on_governance_event is not None:
            on_governance_event(event_type, payload)

    def executor(task: Any) -> Dict[str, Any]:
        capabilities = task.required_capabilities or []
        tool_name = capabilities[0] if capabilities else None

        if tool_name is not None and tool_registry.has(tool_name):
            tool = tool_registry.get(tool_name)

            decision = governance_gate.evaluate(
                risk_level=tool.risk_level,
                auto_approve_high=auto_approve_high,
                approved=is_approved(),
            )

            emit_governance(
                "governance_evaluated",
                task_id=task.id,
                tool=tool_name,
                risk_level=tool.risk_level.value,
                outcome=decision.outcome.value,
                reason=decision.reason,
            )

            if not decision.can_execute:
                raise GovernanceBlockedError(decision, tool_name)

            result = tool_registry.execute(tool_name, task, context)
            result.setdefault("tool", tool_name)
            return result

        # ------------------------------------------------------
        # Fallback: no matching simulated tool. Let AEGIS's own
        # Gemini-backed AgentFactory reason about the task instead
        # of failing outright, so arbitrary (non-demo) goals still
        # produce a real result.
        # ------------------------------------------------------

        if get_agent_factory is not None:
            agent_factory = get_agent_factory()
            worker = agent_factory.create_worker(task)
            return worker.execute(task)

        return {
            "status": "failed",
            "detail": (
                f"No tool registered for capability "
                f"'{tool_name}' and no fallback agent_factory "
                f"was configured."
            ),
        }

    return executor
