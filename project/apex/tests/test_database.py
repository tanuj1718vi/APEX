import tempfile
import os

from apex.backend.db.database import Database


def _fresh_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # let sqlite create it fresh
    return Database(db_path=path)


def test_goal_roundtrip():
    db = _fresh_db()
    goal_id = db.insert_goal(
        user_goal="Run the recovery demo",
        structured_goal={"objective": "Run the recovery demo"},
        plan={"objective": "Run the recovery demo", "tasks": []},
        max_risk="high",
    )
    goal = db.get_goal(goal_id)
    assert goal["user_goal"] == "Run the recovery demo"
    assert goal["structured_goal"]["objective"] == "Run the recovery demo"
    assert goal["max_risk"] == "high"


def test_execution_lifecycle():
    db = _fresh_db()
    goal_id = db.insert_goal(user_goal="Test goal")
    execution_id = db.insert_execution(
        goal_id=goal_id, status="running", auto_approve_high=True
    )

    execution = db.get_execution(execution_id)
    assert execution["status"] == "running"
    assert execution["auto_approve_high"] is True
    assert execution["approved"] is False

    db.update_execution(
        execution_id, status="completed", result={"ok": True}
    )
    updated = db.get_execution(execution_id)
    assert updated["status"] == "completed"
    assert updated["result"] == {"ok": True}


def test_execution_approval_flag():
    db = _fresh_db()
    goal_id = db.insert_goal(user_goal="Test goal")
    execution_id = db.insert_execution(goal_id=goal_id, status="pending_approval")

    db.update_execution(execution_id, approved=True, status="running")
    execution = db.get_execution(execution_id)
    assert execution["approved"] is True
    assert execution["status"] == "running"


def test_events_are_ordered_and_typed():
    db = _fresh_db()
    goal_id = db.insert_goal(user_goal="Test goal")
    execution_id = db.insert_execution(goal_id=goal_id, status="running")

    db.insert_event(execution_id, "run_started", {})
    db.insert_event(execution_id, "task_started", {"task_id": "task_1"})
    db.insert_event(execution_id, "run_completed", {"results": {}})

    events = db.list_events(execution_id)
    assert [e["event_type"] for e in events] == [
        "run_started",
        "task_started",
        "run_completed",
    ]
    assert events[1]["payload"]["task_id"] == "task_1"


def test_list_executions_orders_newest_first():
    db = _fresh_db()
    goal_id = db.insert_goal(user_goal="Test goal")
    first = db.insert_execution(goal_id=goal_id, status="completed")
    second = db.insert_execution(goal_id=goal_id, status="running")

    executions = db.list_executions()
    ids = [e["id"] for e in executions]
    assert ids.index(second) < ids.index(first)


if __name__ == "__main__":
    test_goal_roundtrip()
    test_execution_lifecycle()
    test_execution_approval_flag()
    test_events_are_ordered_and_typed()
    test_list_executions_orders_newest_first()
    print("All database tests passed!")
