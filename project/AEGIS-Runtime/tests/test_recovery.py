from backend.models.schemas import (
    TaskNode,
    VerificationResult,
)
from backend.recovery.recovery_engine import RecoveryEngine


def test_recovery():

    task = TaskNode(
        id="task_1",
        description="Build a student performance prediction model.",
        required_capabilities=[
            "machine_learning"
        ],
    )

    verification = VerificationResult(
        passed=False,
        score=0.35,
        reasoning="The model evaluation is incomplete.",
        issues=[
            "Missing evaluation metrics"
        ],
    )

    recovery = RecoveryEngine()

    decision = recovery.decide(
        task=task,
        verification=verification,
        attempts=0,
    )

    print("\n=== RECOVERY DECISION ===")
    print(
        decision.model_dump_json(indent=2)
    )

    assert decision.action
    assert decision.reason

    print("\nRecovery test passed!")


if __name__ == "__main__":
    test_recovery()
