"""
APEX persistence layer.

Uses plain sqlite3 (stdlib) rather than an ORM to keep the MVP's
dependency footprint small, as instructed. A fresh connection is
opened per call (SQLite handles this cheaply) with WAL journaling so
the API thread and the background execution thread can both read and
write without stepping on each other.

Schema:

    goals       - one row per submitted natural-language goal
    executions  - one row per execution attempt of a goal's plan
    events      - an append-only, event-sourced audit log. Every
                  RuntimeEngine/orchestrator on_event callback and
                  every governance/tool decision becomes one row
                  here. This single table doubles as: observations,
                  actions, failures, recovery attempts, verification
                  results, and audit events -- all discriminated by
                  `event_type`, and all queryable per execution.
"""

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_DB_PATH = Path(__file__).parent / "apex.db"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    user_goal TEXT NOT NULL,
                    structured_goal_json TEXT,
                    plan_json TEXT,
                    max_risk TEXT,
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS executions (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    auto_approve_high INTEGER NOT NULL DEFAULT 0,
                    approved INTEGER NOT NULL DEFAULT 0,
                    result_json TEXT,
                    error TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY(goal_id) REFERENCES goals(id)
                );

                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY(execution_id) REFERENCES executions(id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_execution
                    ON events(execution_id);
                """
            )

    # ------------------------------------------------------------
    # Goals
    # ------------------------------------------------------------

    def insert_goal(
        self,
        user_goal: str,
        structured_goal: Optional[Dict[str, Any]] = None,
        plan: Optional[Dict[str, Any]] = None,
        max_risk: Optional[str] = None,
    ) -> str:
        goal_id = new_id("goal")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO goals
                    (id, user_goal, structured_goal_json, plan_json,
                     max_risk, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    goal_id,
                    user_goal,
                    json.dumps(structured_goal) if structured_goal else None,
                    json.dumps(plan) if plan else None,
                    max_risk,
                    time.time(),
                ),
            )
        return goal_id

    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM goals WHERE id = ?", (goal_id,)
            ).fetchone()
        return self._goal_row_to_dict(row) if row else None

    @staticmethod
    def _goal_row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "user_goal": row["user_goal"],
            "structured_goal": (
                json.loads(row["structured_goal_json"])
                if row["structured_goal_json"]
                else None
            ),
            "plan": (
                json.loads(row["plan_json"]) if row["plan_json"] else None
            ),
            "max_risk": row["max_risk"],
            "created_at": row["created_at"],
        }

    # ------------------------------------------------------------
    # Executions
    # ------------------------------------------------------------

    def insert_execution(
        self,
        goal_id: str,
        status: str,
        auto_approve_high: bool = False,
    ) -> str:
        execution_id = new_id("exec")
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO executions
                    (id, goal_id, status, auto_approve_high, approved,
                     result_json, error, created_at, updated_at)
                VALUES (?, ?, ?, ?, 0, NULL, NULL, ?, ?)
                """,
                (
                    execution_id,
                    goal_id,
                    status,
                    1 if auto_approve_high else 0,
                    now,
                    now,
                ),
            )
        return execution_id

    def update_execution(
        self,
        execution_id: str,
        status: Optional[str] = None,
        approved: Optional[bool] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        fields = []
        values: List[Any] = []

        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if approved is not None:
            fields.append("approved = ?")
            values.append(1 if approved else 0)
        if result is not None:
            fields.append("result_json = ?")
            values.append(json.dumps(result))
        if error is not None:
            fields.append("error = ?")
            values.append(error)

        fields.append("updated_at = ?")
        values.append(time.time())
        values.append(execution_id)

        with self._connect() as conn:
            conn.execute(
                f"UPDATE executions SET {', '.join(fields)} WHERE id = ?",
                values,
            )

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM executions WHERE id = ?", (execution_id,)
            ).fetchone()
        return self._execution_row_to_dict(row) if row else None

    def list_executions(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM executions ORDER BY created_at DESC"
            ).fetchall()
        return [self._execution_row_to_dict(r) for r in rows]

    @staticmethod
    def _execution_row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "goal_id": row["goal_id"],
            "status": row["status"],
            "auto_approve_high": bool(row["auto_approve_high"]),
            "approved": bool(row["approved"]),
            "result": (
                json.loads(row["result_json"]) if row["result_json"] else None
            ),
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    # ------------------------------------------------------------
    # Events (observations / actions / failures / recovery /
    # verification / audit -- all discriminated by event_type)
    # ------------------------------------------------------------

    def insert_event(
        self,
        execution_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> str:
        event_id = new_id("evt")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events
                    (id, execution_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    execution_id,
                    event_type,
                    json.dumps(payload, default=str),
                    time.time(),
                ),
            )
        return event_id

    def list_events(self, execution_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM events
                WHERE execution_id = ?
                ORDER BY created_at ASC
                """,
                (execution_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "execution_id": row["execution_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
