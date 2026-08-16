import os
import tempfile

from apex.backend.db.database import Database
from apex.backend.goal_manager import GoalManager

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "AEGIS-Runtime"))

from backend.models.schemas import (
    StructuredGoal,
    ExecutionPlan,
    PlanTask,
    VerificationResult,
    RecoveryDecision,
    RecoveryAction,
)


def _fresh_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    return Database(db_path=path)


class FakeGoalAnalyzer:
    def analyze(self, goal):
        return StructuredGoal(
            objective=goal,
            domain="ops",
            inputs=[],
            requirements=[],
            constraints=[],
            success_criteria=[],
            ambiguities=[],
        )


class LowRiskPlanner:
    """Plans that only touch LOW-risk simulated tools."""

    def create_plan(self, goal, **kwargs):
        return ExecutionPlan(
            objective=goal.objective,
            tasks=[
                PlanTask(
                    id="task_1",
                    description="Check system state",
                    dependencies=[],
                    required_capabilities=["system_status"],
                )
            ],
        )


class HighRiskPlanner:
    """Plans that touch a HIGH-risk simulated tool (repair_service)."""

    def create_plan(self, goal, **kwargs):
        return ExecutionPlan(
            objective=goal.objective,
            tasks=[
                PlanTask(
                    id="task_1",
                    description="Repair the service",
                    dependencies=[],
                    required_capabilities=["repair_service"],
                )
            ],
        )


class AlwaysPassVerifier:
    def verify(self, task, result):
        return VerificationResult(
            passed=True, score=1.0, reasoning="ok", issues=[]
        )


class AlwaysAbortRecovery:
    def decide(self, task, verification, attempts=0):
        return RecoveryDecision(
            action=RecoveryAction.ABORT,
            reason="Not retrying in this test.",
            attempts=attempts,
        )


def _manager(db, planner, verifier=None, recovery=None):
    return GoalManager(
        db=db,
        goal_analyzer=FakeGoalAnalyzer(),
        planner=planner,
        verifier=verifier or AlwaysPassVerifier(),
        recovery=recovery or AlwaysAbortRecovery(),
    )


def test_submit_goal_computes_low_risk():
    db = _fresh_db()
    manager = _manager(db, LowRiskPlanner())

    result = manager.submit_goal("Check on the system")

    assert result["max_risk"] == "low"
    assert result["plan"]["tasks"][0]["required_capabilities"] == [
        "system_status"
    ]


def test_submit_goal_computes_high_risk():
    db = _fresh_db()
    manager = _manager(db, HighRiskPlanner())

    result = manager.submit_goal("Fix the broken service")

    assert result["max_risk"] == "high"


def test_create_execution_starts_immediately_for_low_risk():
    db = _fresh_db()
    manager = _manager(db, LowRiskPlanner())
    goal = manager.submit_goal("Check on the system")

    execution = manager.create_execution(goal["goal_id"])

    assert execution["status"] == "running"


def test_create_execution_requires_approval_for_high_risk():
    db = _fresh_db()
    manager = _manager(db, HighRiskPlanner())
    goal = manager.submit_goal("Fix the broken service")

    execution = manager.create_execution(goal["goal_id"], auto_approve_high=False)

    assert execution["status"] == "pending_approval"


def test_create_execution_auto_approves_high_risk_when_flagged():
    db = _fresh_db()
    manager = _manager(db, HighRiskPlanner())
    goal = manager.submit_goal("Fix the broken service")

    execution = manager.create_execution(goal["goal_id"], auto_approve_high=True)

    assert execution["status"] == "running"


def test_run_execution_happy_path_low_risk():
    db = _fresh_db()
    manager = _manager(db, LowRiskPlanner())
    goal = manager.submit_goal("Check on the system")
    execution = manager.create_execution(goal["goal_id"])

    outcome = manager.run_execution(execution["execution_id"])

    assert outcome["status"] == "completed"
    assert "task_1" in outcome["results"]

    stored = db.get_execution(execution["execution_id"])
    assert stored["status"] == "completed"

    events = db.list_events(execution["execution_id"])
    event_types = [e["event_type"] for e in events]
    assert "run_started" in event_types
    assert "governance_evaluated" in event_types
    assert "run_completed" in event_types


def test_run_execution_blocked_by_governance_when_not_approved():
    db = _fresh_db()
    manager = _manager(db, HighRiskPlanner())
    goal = manager.submit_goal("Fix the broken service")
    execution = manager.create_execution(goal["goal_id"], auto_approve_high=False)

    assert execution["status"] == "pending_approval"

    try:
        manager.run_execution(execution["execution_id"])
        assert False, "expected the run to fail due to governance block"
    except RuntimeError:
        pass

    stored = db.get_execution(execution["execution_id"])
    assert stored["status"] == "failed"

    events = db.list_events(execution["execution_id"])
    governance_events = [
        e for e in events if e["event_type"] == "governance_evaluated"
    ]
    assert governance_events[0]["payload"]["outcome"] == "requires_approval"


def test_approve_execution_then_run_succeeds():
    db = _fresh_db()
    manager = _manager(db, HighRiskPlanner())
    goal = manager.submit_goal("Fix the broken service")
    execution = manager.create_execution(goal["goal_id"], auto_approve_high=False)

    manager.approve_execution(execution["execution_id"])

    outcome = manager.run_execution(execution["execution_id"])
    assert outcome["status"] == "completed"


def test_cancel_requested_stops_run_execution():
    db = _fresh_db()
    manager = _manager(db, LowRiskPlanner())
    goal = manager.submit_goal("Check on the system")
    execution = manager.create_execution(goal["goal_id"])

    db.update_execution(execution["execution_id"], status="cancel_requested")

    try:
        manager.run_execution(execution["execution_id"])
        assert False, "expected cancellation to raise"
    except RuntimeError:
        pass

    stored = db.get_execution(execution["execution_id"])
    assert stored["status"] == "cancelled"


def test_failure_constructing_gemini_components_is_caught_not_swallowed():
    """
    Regression test for a real bug: _get_verifier()/_get_recovery()/
    _get_planner() (which construct the real Gemini-backed AEGIS
    components) used to be called OUTSIDE run_execution's try/except.
    If construction failed (e.g. a missing/invalid GEMINI_API_KEY),
    the exception propagated straight out of run_execution, past the
    API layer's background task (which silently swallowed it), and
    the execution was left stuck at status="running" forever with no
    error recorded anywhere.

    This test simulates exactly that failure point -- construction
    itself raising, not something going wrong during a call -- and
    asserts the status flips to "failed" with the error persisted,
    not a silent, permanent hang.
    """
    db = _fresh_db()
    manager = _manager(db, LowRiskPlanner())

    def exploding_get_verifier():
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    manager._get_verifier = exploding_get_verifier

    goal = manager.submit_goal("Check on the system")
    execution = manager.create_execution(goal["goal_id"])

    try:
        manager.run_execution(execution["execution_id"])
        assert False, "expected the construction failure to propagate"
    except RuntimeError:
        pass

    stored = db.get_execution(execution["execution_id"])
    assert stored["status"] == "failed"
    assert stored["error"] is not None
    assert "GEMINI_API_KEY" in stored["error"]


if __name__ == "__main__":
    test_submit_goal_computes_low_risk()
    test_submit_goal_computes_high_risk()
    test_create_execution_starts_immediately_for_low_risk()
    test_create_execution_requires_approval_for_high_risk()
    test_create_execution_auto_approves_high_risk_when_flagged()
    test_run_execution_happy_path_low_risk()
    test_run_execution_blocked_by_governance_when_not_approved()
    test_approve_execution_then_run_succeeds()
    test_cancel_requested_stops_run_execution()
    print("All goal manager tests passed!")
