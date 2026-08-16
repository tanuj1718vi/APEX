from backend.runtime.runtime import RuntimeEngine
from backend.runtime.task_graph import TaskGraph
from backend.models.schemas import (
    ExecutionPlan,
    PlanTask,
    VerificationResult,
    RecoveryDecision,
    RecoveryAction,
)


class PassingVerifier:
    def verify(self, task, result):
        return VerificationResult(
            passed=True,
            score=1.0,
            reasoning="ok",
            issues=[],
        )


class FailThenPassVerifier:
    def __init__(self):
        self.calls = 0

    def verify(self, task, result):
        self.calls += 1
        if self.calls == 1:
            return VerificationResult(
                passed=False,
                score=0.0,
                reasoning="failed once",
                issues=["broken"],
            )
        return VerificationResult(
            passed=True,
            score=1.0,
            reasoning="ok now",
            issues=[],
        )


class RetryOnceRecovery:
    def decide(self, task, verification, attempts=0):
        return RecoveryDecision(
            action=RecoveryAction.RETRY,
            reason="try again",
            attempts=attempts,
        )


def _simple_graph():
    plan = ExecutionPlan(
        objective="Emit events",
        tasks=[
            PlanTask(
                id="task_1",
                description="Do a thing",
                dependencies=[],
                required_capabilities=["general"],
            )
        ],
    )
    return TaskGraph(plan)


def test_runtime_emits_success_events_in_order():
    events = []

    def on_event(event_type, payload):
        events.append(event_type)

    runtime = RuntimeEngine(
        graph=_simple_graph(),
        executor=lambda task: {"status": "completed"},
        verifier=PassingVerifier(),
        recovery=None,
        on_event=on_event,
    )

    runtime.run()

    assert events == [
        "run_started",
        "task_started",
        "task_executed",
        "verification_completed",
        "task_completed",
        "run_completed",
    ]


def test_runtime_emits_failure_and_retry_events():
    events = []

    def on_event(event_type, payload):
        events.append(event_type)

    runtime = RuntimeEngine(
        graph=_simple_graph(),
        executor=lambda task: {"status": "completed"},
        verifier=FailThenPassVerifier(),
        recovery=RetryOnceRecovery(),
        on_event=on_event,
    )

    runtime.run()

    assert events == [
        "run_started",
        "task_started",
        "task_executed",
        "verification_completed",
        "task_failed",
        "recovery_decided",
        "task_retrying",
        "task_started",
        "task_executed",
        "verification_completed",
        "task_completed",
        "run_completed",
    ]


def test_runtime_respects_should_cancel():
    def always_cancel():
        return True

    runtime = RuntimeEngine(
        graph=_simple_graph(),
        executor=lambda task: {"status": "completed"},
        verifier=PassingVerifier(),
        recovery=None,
        should_cancel=always_cancel,
    )

    try:
        runtime.run()
        assert False, "expected cancellation to raise"
    except RuntimeError as error:
        assert "cancelled" in str(error).lower()


def test_broken_on_event_listener_does_not_crash_execution():
    def broken_listener(event_type, payload):
        raise ValueError("listener bug")

    runtime = RuntimeEngine(
        graph=_simple_graph(),
        executor=lambda task: {"status": "completed"},
        verifier=PassingVerifier(),
        recovery=None,
        on_event=broken_listener,
    )

    results = runtime.run()

    assert "task_1" in results
    assert results["task_1"]["verification"]["passed"] is True


if __name__ == "__main__":
    test_runtime_emits_success_events_in_order()
    test_runtime_emits_failure_and_retry_events()
    test_runtime_respects_should_cancel()
    test_broken_on_event_listener_does_not_crash_execution()
