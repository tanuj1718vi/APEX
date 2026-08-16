import os
import tempfile

from apex.backend.db.database import Database
from apex.backend.goal_manager import GoalManager

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "AEGIS-Runtime"))

from backend.models.schemas import VerificationResult, RecoveryDecision, RecoveryAction


def _fresh_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    return Database(db_path=path)


class StateAwareVerifier:
    """
    Stands in for the real Gemini VerificationEngine. Compares the
    tool's reported `status` against expectations -- this is exactly
    the "expected vs actual" comparison the spec requires, just
    without a live Gemini call so the test is network-independent.
    """

    def __init__(self):
        self.calls = []

    def verify(self, task, result):
        self.calls.append((task.id, result.get("status")))
        passed = result.get("status") == "completed"
        return VerificationResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            reasoning=(
                "Tool reported completed status."
                if passed
                else "Tool reported a failed status."
            ),
            issues=[] if passed else [result.get("detail", "unknown failure")],
        )


class RetryOnceRecovery:
    """Stands in for the real Gemini RecoveryEngine: retry on failure."""

    def decide(self, task, verification, attempts=0):
        return RecoveryDecision(
            action=RecoveryAction.RETRY,
            reason="Retrying after inspecting the failure.",
            attempts=attempts,
        )


def test_recovery_demo_end_to_end():
    db = _fresh_db()
    manager = GoalManager(
        db=db,
        verifier=StateAwareVerifier(),
        recovery=RetryOnceRecovery(),
    )

    goal = manager.create_recovery_demo_goal()
    assert goal["max_risk"] == "high"  # repair_service is HIGH risk

    execution = manager.create_execution(goal["goal_id"], auto_approve_high=True)
    assert execution["status"] == "running"

    outcome = manager.run_execution(execution["execution_id"])

    assert outcome["status"] == "completed"

    results = outcome["results"]
    assert results["check_system_state"]["verification"]["passed"] is True
    assert results["analyze_system"]["verification"]["passed"] is True
    assert results["repair_service"]["verification"]["passed"] is True
    assert results["verify_service_health"]["verification"]["passed"] is True

    # verify_system must have observed a *healthy* state -- proof the
    # repair genuinely changed the simulated system state, not just
    # that the task was marked complete.
    verify_result = results["verify_service_health"]["execution"]
    assert verify_result["observed_state"] == "healthy"
    assert verify_result["match"] is True

    # Confirm the real failure -> recovery -> success trail happened.
    events = db.list_events(execution["execution_id"])
    event_types = [e["event_type"] for e in events]

    assert "task_failed" in event_types
    assert "recovery_decided" in event_types
    assert "task_retrying" in event_types
    assert "run_completed" in event_types

    # The repair task specifically must show one failure then one
    # success -- not a fabricated timeline.
    repair_task_events = [
        e for e in events if e.get("payload", {}).get("task_id") == "repair_service"
    ]
    verification_events = [
        e for e in repair_task_events if e["event_type"] == "verification_completed"
    ]
    assert [e["payload"]["passed"] for e in verification_events] == [False, True]


if __name__ == "__main__":
    test_recovery_demo_end_to_end()
    print("Recovery demo end-to-end test passed!")
