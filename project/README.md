# APEX on AEGIS Runtime

```
                    AEGIS RUNTIME
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
       AEGIS-FRAUDGUARD           APEX
       (untouched)          Autonomous Predictive
                                  Execution
```

`AEGIS-Runtime/` is the reusable execution engine (unchanged in
purpose, only extended with additive, backward-compatible hooks --
see "What changed in AEGIS Runtime" below). `apex/` is a separate
application built on top of it. Nothing in `AEGIS-Runtime/`'s public
behavior changed for existing callers; every original test still
passes.

## Project layout

```
AEGIS-Runtime/            # reusable core (unchanged behavior)
  backend/
    runtime/               # RuntimeEngine, TaskGraph
    orchestrator/           # AEGISOrchestrator facade
    agents/                  # GoalAnalyzer, Planner (via factory), AgentFactory
    planner/ verifier/ recovery/ models/ config/
  tests/                     # 26 tests, all passing

apex/
  backend/
    goal_manager.py          # the ONLY file that talks to AEGIS Runtime
    governance/               # risk levels + approval gate
    tools/                     # tool registry + 8 safe simulated tools
    execution/                 # executor_factory: tasks -> tools -> governance
    events/                     # thread-safe event bus for the WebSocket
    db/                          # SQLite persistence (goals/executions/events)
    demo/                         # deterministic "Run Recovery Demo" scenario
    api/main.py                    # FastAPI app: REST + WebSocket
  frontend/                        # React + TypeScript dashboard (Vite)
  tests/                           # 41 tests, all passing
```

## Running it

### Backend

```bash
cd AEGIS-Runtime && pip install -r requirements.txt --break-system-packages
cd ../apex/backend && pip install -r requirements.txt --break-system-packages

# GEMINI_API_KEY must be set (in AEGIS-Runtime/.env or the environment)
# for real goal analysis/planning/verification/recovery reasoning.

cd ../..
PYTHONPATH=.:AEGIS-Runtime uvicorn apex.backend.api.main:app --reload --port 8000
```

### Frontend

```bash
cd apex/frontend
npm install
cp .env.example .env   # VITE_API_BASE=http://localhost:8000
npm run dev
```

### Tests (no network / no Gemini key required -- all AI components are
### injected as fakes, exactly like AEGIS's own test suite does)

```bash
cd AEGIS-Runtime && python3 -m pytest tests/ -q      # 26 passed
cd ..
PYTHONPATH=.:AEGIS-Runtime python3 -m pytest apex/tests/ -q   # 41 passed
```

## What changed in AEGIS Runtime (and why)

Two additive, backward-compatible fixes were made directly to
`AEGIS-Runtime/backend/runtime/runtime.py` and `orchestrator.py`,
because APEX genuinely needed them and they were missing:

1. **REASSIGN was a no-op.** `RecoveryAction.REASSIGN` existed and
   `AgentFactory.create_worker()` already accepted an
   `excluded_workers` list, but `RuntimeEngine` never passed it, so
   "reassign" silently retried the *same* worker. `RuntimeEngine` now
   tracks which worker handled each task and excludes it on
   reassignment. Covered by
   `AEGIS-Runtime/tests/test_runtime_agentfactory_reassignment.py`.

2. **No observability.** `RuntimeEngine`/`AEGISOrchestrator` only
   `print()`ed. Added optional `on_event(event_type, payload)` and
   `should_cancel()` hooks (both default to `None`/no-op, so every
   existing caller and test is unaffected) so APEX's API layer can
   stream real runtime events over a WebSocket and support
   cooperative cancellation. Covered by
   `AEGIS-Runtime/tests/test_runtime_events.py`.

3. **`.env` was never found when run from the project root.**
   `config.py` called `load_dotenv()` with no arguments, which only
   searches *upward* from the process's working directory — never
   into subfolders. Since APEX must be started from `project/` (one
   level above `AEGIS-Runtime/`) for its imports to resolve, this
   meant `GEMINI_API_KEY` could never be found, no matter how
   correctly it was set. Fixed by loading `AEGIS-Runtime/.env`
   explicitly, relative to `config.py`'s own location. Covered by
   `AEGIS-Runtime/tests/test_config_env_loading.py`.

4. **No retry on transient Gemini failures.** Every Gemini call
   (`GoalAnalyzer`, `Planner`, `VerificationEngine`, `RecoveryEngine`,
   the `AgentFactory` AI worker) called `generate_content` directly,
   so a single `429 RESOURCE_EXHAUSTED` (free-tier rate limit — 5
   requests/minute on `gemini-2.5-flash`) or transient `5xx` hard-failed
   the whole execution. Added `generate_content_with_retry()` in
   `config.py`: retries on 429/5xx only (a genuinely bad request or
   invalid key still fails immediately, not silently masked), honors
   Gemini's own suggested `retryDelay` when present, exponential
   backoff otherwise. All 5 call sites now go through it. Covered by
   `AEGIS-Runtime/tests/test_gemini_retry.py`.

Nothing else in AEGIS Runtime was modified. FraudGuard was not
touched (its integration was an empty stub to begin with).

## How APEX uses AEGIS Runtime

`apex/backend/goal_manager.py` is the single interface: it builds a
`StructuredGoal`/`ExecutionPlan` (via Gemini, or deterministically for
the demo), wraps AEGIS's `TaskGraph` + `RuntimeEngine`, and supplies:

- an **executor** (`apex/backend/execution/executor_factory.py`) that
  routes each task to a registered tool through the **governance
  gate**, or falls back to AEGIS's own Gemini `AgentFactory` for
  tasks that don't match a known tool;
- **verifier/recovery** — AEGIS's real Gemini-backed
  `VerificationEngine`/`RecoveryEngine`, unmodified;
- an **on_event** callback that persists every event to SQLite and
  publishes it to the WebSocket bus.

## Governance

| Risk level | Behavior |
|---|---|
| LOW | executes automatically |
| MEDIUM | executes automatically, logged to the audit trail |
| HIGH | requires approval, unless the execution set `auto_approve_high=True` |
| CRITICAL | **never** executes automatically, even with `auto_approve_high` -- always requires an explicit `POST /executions/{id}/approve` |

A pre-flight check runs when an execution is created (blocking start
if the plan's highest-risk tool needs approval); a per-task check
also runs at execution time as a safety net (e.g. if a replan
introduces a new high-risk task mid-run).

## API

```
GET  /api/health
GET  /api/tools
POST /api/goals                          { goal: string }
POST /api/goals/demo-recovery            (deterministic demo plan)
GET  /api/goals/{goal_id}
POST /api/executions                     { goal_id, auto_approve_high }
GET  /api/executions
GET  /api/executions/{id}
POST /api/executions/{id}/approve
POST /api/executions/{id}/cancel
WS   /api/executions/{id}/stream
```

## The "Run Recovery Demo" scenario

`apex/backend/demo/recovery_demo.py` builds a fixed 4-task plan
(check state → analyze → repair → verify) in plain Python, so the
demo is reproducible without depending on what Gemini happens to plan
that day. Everything *downstream* of the plan is real:
`repair_service` (see `apex/backend/tools/simulated_tools.py`)
genuinely fails on its first call and genuinely succeeds on a second
call against the same execution-scoped state; `VerificationEngine`
and `RecoveryEngine` (both real Gemini calls, unless fakes are
injected for tests) genuinely decide pass/fail and genuinely decide
to retry. See `apex/tests/test_recovery_demo.py` for the event trail
this produces: `task_failed` → `recovery_decided` → `task_retrying` →
a second `verification_completed` that passes → `run_completed`.

## Known MVP limitations

- Approval is a single execution-level flag, not per-task. A HIGH/
  CRITICAL task introduced mid-run by a replan is safety-netted (it
  fails with a clear governance reason instead of silently
  executing) rather than pausing the run for approval, since
  `RuntimeEngine.run()` is a synchronous blocking loop with no
  pause/resume primitive. Extending it to a real pause/resume state
  machine is the natural next step if per-task mid-run approval is
  needed.
- SQLite only, as specified for the MVP.
- The frontend's Task Graph view infers per-task status by replaying
  events client-side rather than the backend exposing a dedicated
  "current graph state" endpoint -- fine at MVP scale, worth
  revisiting if task counts grow large.
