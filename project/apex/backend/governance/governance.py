"""
APEX Risk Governance.

Every tool-backed action carries a risk level. This module decides,
before a task is allowed to execute, whether it can run automatically
or must wait for a human to approve it.

Policy:

    LOW      -> always executes automatically.
    MEDIUM   -> executes automatically, but is flagged in the audit
                trail so it's visible after the fact.
    HIGH     -> requires approval UNLESS the execution was created
                with auto_approve_high=True.
    CRITICAL -> NEVER executes automatically, regardless of
                auto_approve_high. Must always be approved per
                execution.

This module is deliberately independent of AEGIS Runtime and of
FastAPI so it can be unit tested in isolation.
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def highest_risk(levels):
    """Return the most severe RiskLevel in an iterable, or LOW if empty."""

    levels = list(levels)
    if not levels:
        return RiskLevel.LOW
    return max(levels, key=lambda lvl: _ORDER[lvl])


class GovernanceOutcome(str, Enum):
    ALLOW = "allow"
    ALLOW_WITH_AUDIT = "allow_with_audit"
    REQUIRES_APPROVAL = "requires_approval"
    BLOCKED = "blocked"


@dataclass
class GovernanceDecision:
    outcome: GovernanceOutcome
    risk_level: RiskLevel
    reason: str

    @property
    def can_execute(self) -> bool:
        return self.outcome in (
            GovernanceOutcome.ALLOW,
            GovernanceOutcome.ALLOW_WITH_AUDIT,
        )


class GovernanceBlockedError(Exception):
    """
    Raised by the executor when a task's tool requires approval or is
    blocked and the execution was not pre-approved for it. Surfaces
    to RuntimeEngine as a normal task failure, which flows into
    AEGIS's existing recovery/abort machinery rather than silently
    bypassing governance.
    """

    def __init__(self, decision: "GovernanceDecision", tool_name: str):
        self.decision = decision
        self.tool_name = tool_name
        super().__init__(
            f"Tool '{tool_name}' blocked by governance "
            f"({decision.outcome.value}): {decision.reason}"
        )


class GovernanceGate:
    """
    Stateless policy evaluator. Approval state (has a human already
    approved this execution?) is tracked by the caller (the DB-backed
    Execution record) and passed in as `approved`.
    """

    def evaluate(
        self,
        risk_level: RiskLevel,
        auto_approve_high: bool = False,
        approved: bool = False,
    ) -> GovernanceDecision:

        if risk_level == RiskLevel.LOW:
            return GovernanceDecision(
                outcome=GovernanceOutcome.ALLOW,
                risk_level=risk_level,
                reason="Low-risk actions execute automatically.",
            )

        if risk_level == RiskLevel.MEDIUM:
            return GovernanceDecision(
                outcome=GovernanceOutcome.ALLOW_WITH_AUDIT,
                risk_level=risk_level,
                reason=(
                    "Medium-risk actions execute automatically "
                    "and are recorded in the audit trail."
                ),
            )

        if risk_level == RiskLevel.HIGH:
            if approved or auto_approve_high:
                return GovernanceDecision(
                    outcome=GovernanceOutcome.ALLOW_WITH_AUDIT,
                    risk_level=risk_level,
                    reason="High-risk action was approved.",
                )
            return GovernanceDecision(
                outcome=GovernanceOutcome.REQUIRES_APPROVAL,
                risk_level=risk_level,
                reason="High-risk actions require explicit approval.",
            )

        if risk_level == RiskLevel.CRITICAL:
            if approved:
                return GovernanceDecision(
                    outcome=GovernanceOutcome.ALLOW_WITH_AUDIT,
                    risk_level=risk_level,
                    reason=(
                        "Critical action was explicitly approved "
                        "for this execution."
                    ),
                )
            return GovernanceDecision(
                outcome=GovernanceOutcome.BLOCKED,
                risk_level=risk_level,
                reason=(
                    "Critical actions can never execute "
                    "automatically, even with auto_approve_high. "
                    "They must be approved explicitly."
                ),
            )

        raise ValueError(f"Unknown risk level: {risk_level}")
