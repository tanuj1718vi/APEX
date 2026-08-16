from apex.backend.governance.governance import (
    GovernanceGate,
    GovernanceOutcome,
    RiskLevel,
    highest_risk,
)


def test_low_risk_always_allows():
    gate = GovernanceGate()
    decision = gate.evaluate(RiskLevel.LOW)
    assert decision.outcome == GovernanceOutcome.ALLOW
    assert decision.can_execute is True


def test_medium_risk_allows_with_audit():
    gate = GovernanceGate()
    decision = gate.evaluate(RiskLevel.MEDIUM)
    assert decision.outcome == GovernanceOutcome.ALLOW_WITH_AUDIT
    assert decision.can_execute is True


def test_high_risk_requires_approval_by_default():
    gate = GovernanceGate()
    decision = gate.evaluate(RiskLevel.HIGH)
    assert decision.outcome == GovernanceOutcome.REQUIRES_APPROVAL
    assert decision.can_execute is False


def test_high_risk_allowed_with_auto_approve_flag():
    gate = GovernanceGate()
    decision = gate.evaluate(RiskLevel.HIGH, auto_approve_high=True)
    assert decision.can_execute is True


def test_high_risk_allowed_when_approved():
    gate = GovernanceGate()
    decision = gate.evaluate(RiskLevel.HIGH, approved=True)
    assert decision.can_execute is True


def test_critical_risk_never_auto_approves():
    gate = GovernanceGate()
    # Even with auto_approve_high=True, CRITICAL must stay blocked.
    decision = gate.evaluate(RiskLevel.CRITICAL, auto_approve_high=True)
    assert decision.outcome == GovernanceOutcome.BLOCKED
    assert decision.can_execute is False


def test_critical_risk_allowed_only_with_explicit_approval():
    gate = GovernanceGate()
    decision = gate.evaluate(RiskLevel.CRITICAL, approved=True)
    assert decision.can_execute is True


def test_highest_risk_picks_most_severe():
    assert highest_risk([]) == RiskLevel.LOW
    assert highest_risk([RiskLevel.LOW, RiskLevel.MEDIUM]) == RiskLevel.MEDIUM
    assert (
        highest_risk([RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.LOW])
        == RiskLevel.CRITICAL
    )


if __name__ == "__main__":
    test_low_risk_always_allows()
    test_medium_risk_allows_with_audit()
    test_high_risk_requires_approval_by_default()
    test_high_risk_allowed_with_auto_approve_flag()
    test_high_risk_allowed_when_approved()
    test_critical_risk_never_auto_approves()
    test_critical_risk_allowed_only_with_explicit_approval()
    test_highest_risk_picks_most_severe()
    print("All governance tests passed!")
