import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "AEGIS-Runtime"))

from fastapi.testclient import TestClient

from backend.models.schemas import (
    StructuredGoal,
    ExecutionPlan,
    PlanTask,
    VerificationResult,
    RecoveryDecision,
    RecoveryAction,
)

from apex.backend.db.database import Database
from apex.backend.goal_manager import GoalManager
import apex.backend.api.main as api_main


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


class AlwaysPassVerifier:
    def verify(self, task, result):
        return VerificationResult(passed=True, score=1.0, reasoning="ok", issues=[])


class AlwaysAbortRecovery:
    def decide(self, task, verification, attempts=0):
        return RecoveryDecision(
            action=RecoveryAction.ABORT, reason="n/a", attempts=attempts
        )


def _fresh_client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)

    test_db = Database(db_path=path)
    test_manager = GoalManager(
        db=test_db,
        goal_analyzer=FakeGoalAnalyzer(),
        planner=LowRiskPlanner(),
        verifier=AlwaysPassVerifier(),
        recovery=AlwaysAbortRecovery(),
    )

    # Swap the module-level singletons the routes close over.
    api_main.db = test_db
    api_main.goal_manager = test_manager

    return TestClient(api_main.app), test_manager


def test_health_endpoint():
    client, _ = _fresh_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tools_endpoint_lists_all_tools():
    client, _ = _fresh_client()
    response = client.get("/api/tools")
    assert response.status_code == 200
    names = {t["name"] for t in response.json()["tools"]}
    assert "repair_service" in names
    assert "system_status" in names


def test_submit_goal_endpoint():
    client, _ = _fresh_client()
    response = client.post("/api/goals", json={"goal": "Check on the system"})
    assert response.status_code == 200
    body = response.json()
    assert "goal_id" in body
    assert body["max_risk"] == "low"


def test_submit_goal_rejects_empty_goal():
    client, _ = _fresh_client()
    response = client.post("/api/goals", json={"goal": "   "})
    assert response.status_code == 400


def test_create_and_get_execution_flow():
    client, _ = _fresh_client()
    goal_response = client.post("/api/goals", json={"goal": "Check on the system"})
    goal_id = goal_response.json()["goal_id"]

    exec_response = client.post("/api/executions", json={"goal_id": goal_id})
    assert exec_response.status_code == 200
    execution_id = exec_response.json()["execution_id"]
    assert exec_response.json()["status"] == "running"

    detail = client.get(f"/api/executions/{execution_id}")
    assert detail.status_code == 200
    assert detail.json()["execution"]["id"] == execution_id

    listing = client.get("/api/executions")
    assert listing.status_code == 200
    assert any(e["id"] == execution_id for e in listing.json()["executions"])


def test_get_nonexistent_execution_returns_404():
    client, _ = _fresh_client()
    response = client.get("/api/executions/does_not_exist")
    assert response.status_code == 404


def test_create_execution_for_nonexistent_goal_returns_404():
    client, _ = _fresh_client()
    response = client.post("/api/executions", json={"goal_id": "does_not_exist"})
    assert response.status_code == 404


def test_demo_recovery_goal_endpoint():
    client, _ = _fresh_client()
    response = client.post("/api/goals/demo-recovery")
    assert response.status_code == 200
    body = response.json()
    assert body["max_risk"] == "high"
    assert len(body["plan"]["tasks"]) == 4


def test_websocket_stream_replays_persisted_events():
    client, manager = _fresh_client()

    goal_response = client.post("/api/goals", json={"goal": "Check on the system"})
    goal_id = goal_response.json()["goal_id"]

    exec_response = client.post("/api/executions", json={"goal_id": goal_id})
    execution_id = exec_response.json()["execution_id"]

    # The background asyncio task kicked off by the route may not
    # have completed yet when we open the socket; poll briefly via
    # the DB (the route itself already ran this synchronously enough
    # for TestClient's sync-over-async bridge in practice, but we
    # guard anyway).
    import time

    for _ in range(50):
        execution = manager.db.get_execution(execution_id)
        if execution["status"] == "completed":
            break
        time.sleep(0.05)

    with client.websocket_connect(
        f"/api/executions/{execution_id}/stream"
    ) as websocket:
        first_message = websocket.receive_json()
        assert "event_type" in first_message


def test_get_goal_endpoint():
    client, _ = _fresh_client()
    goal_response = client.post("/api/goals", json={"goal": "Check on the system"})
    goal_id = goal_response.json()["goal_id"]

    response = client.get(f"/api/goals/{goal_id}")
    assert response.status_code == 200
    assert response.json()["user_goal"] == "Check on the system"
    assert response.json()["plan"]["tasks"][0]["id"] == "task_1"


def test_get_nonexistent_goal_returns_404():
    client, _ = _fresh_client()
    response = client.get("/api/goals/does_not_exist")
    assert response.status_code == 404
