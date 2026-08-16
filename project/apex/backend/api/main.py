"""
APEX API layer.

Thin FastAPI shell over GoalManager. No business logic lives here --
every route just validates input, calls GoalManager (which is the
only thing that talks to AEGIS Runtime), and returns/streams the
result. RuntimeEngine.run() is synchronous and can involve real
Gemini calls, so it always runs inside asyncio.to_thread(); the
WebSocket route reads from the EventBus queue that GoalManager's
on_event callback publishes into from that background thread.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from apex.backend.db.database import Database
from apex.backend.goal_manager import GoalManager
from apex.backend.events.bus import event_bus


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_bus.bind_loop(asyncio.get_running_loop())
    yield


app = FastAPI(
    title="APEX",
    description="Autonomous Predictive Execution, built on AEGIS Runtime.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP: tighten before any real deployment.
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
goal_manager = GoalManager(db=db)


# ------------------------------------------------------------------
# Request/response models
# ------------------------------------------------------------------


class SubmitGoalRequest(BaseModel):
    goal: str


class CreateExecutionRequest(BaseModel):
    goal_id: str
    auto_approve_high: bool = False


# ------------------------------------------------------------------
# Background execution runner
# ------------------------------------------------------------------


async def _run_execution_in_background(execution_id: str) -> None:
    try:
        await asyncio.to_thread(goal_manager.run_execution, execution_id)
    except Exception as error:
        # GoalManager.run_execution has already persisted the
        # failure/cancellation status and an event describing it, so
        # there's nothing further to *do* here -- but printing it
        # means this is diagnosable from the terminal instead of
        # disappearing silently.
        print(
            f"[APEX] execution {execution_id} ended with an error: "
            f"{error!r}"
        )


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "apex"}


# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------


@app.get("/api/tools")
async def list_tools():
    return {"tools": goal_manager.tool_registry.list_tools()}


# ------------------------------------------------------------------
# Goals
# ------------------------------------------------------------------


@app.post("/api/goals")
async def submit_goal(payload: SubmitGoalRequest):
    if not payload.goal or not payload.goal.strip():
        raise HTTPException(status_code=400, detail="goal cannot be empty.")

    try:
        result = await asyncio.to_thread(goal_manager.submit_goal, payload.goal)
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error))

    return result


@app.post("/api/goals/demo-recovery")
async def submit_recovery_demo_goal():
    """
    Not part of the original required API list, but needed to back
    the "Run Recovery Demo" button: builds the deterministic 4-task
    demo plan (see apex/backend/demo/recovery_demo.py) without
    calling Gemini for goal analysis/planning, so the demo is
    reproducible on stage.
    """
    result = await asyncio.to_thread(goal_manager.create_recovery_demo_goal)
    return result


@app.get("/api/goals/{goal_id}")
async def get_goal(goal_id: str):
    goal = goal_manager.db.get_goal(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return goal


# ------------------------------------------------------------------
# Executions
# ------------------------------------------------------------------


@app.post("/api/executions")
async def create_execution(payload: CreateExecutionRequest):
    try:
        execution = goal_manager.create_execution(
            goal_id=payload.goal_id,
            auto_approve_high=payload.auto_approve_high,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    # Create the event queue before anything can run, so no early
    # events are lost to a WebSocket client that connects a moment
    # later.
    event_bus.create_queue(execution["execution_id"])

    if execution["status"] == "running":
        asyncio.create_task(
            _run_execution_in_background(execution["execution_id"])
        )

    return execution


@app.get("/api/executions")
async def list_executions():
    return {"executions": goal_manager.db.list_executions()}


@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str):
    execution = goal_manager.db.get_execution(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found.")

    events = goal_manager.db.list_events(execution_id)
    return {"execution": execution, "events": events}


@app.post("/api/executions/{execution_id}/approve")
async def approve_execution(execution_id: str):
    try:
        execution = goal_manager.approve_execution(execution_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    if event_bus.get_queue(execution_id) is None:
        event_bus.create_queue(execution_id)

    asyncio.create_task(_run_execution_in_background(execution_id))

    return execution


@app.post("/api/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    try:
        execution = goal_manager.cancel_execution(execution_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    return execution


# ------------------------------------------------------------------
# Real-time execution stream
# ------------------------------------------------------------------


@app.websocket("/api/executions/{execution_id}/stream")
async def execution_stream(websocket: WebSocket, execution_id: str):
    await websocket.accept()

    execution = goal_manager.db.get_execution(execution_id)
    if execution is None:
        await websocket.send_json(
            {"event_type": "error", "payload": {"detail": "Execution not found."}}
        )
        await websocket.close()
        return

    queue: Optional[asyncio.Queue] = event_bus.get_queue(execution_id)
    if queue is None:
        queue = event_bus.create_queue(execution_id)

    # Replay everything already persisted so a client connecting
    # after the run started still sees the full timeline, not just
    # whatever happens next.
    for event in goal_manager.db.list_events(execution_id):
        await websocket.send_json(
            {"event_type": event["event_type"], "payload": event["payload"]}
        )

    try:
        while True:
            message = await queue.get()
            await websocket.send_json(message)
    except WebSocketDisconnect:
        pass
