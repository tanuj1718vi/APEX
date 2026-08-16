# APEX Frontend

React + TypeScript dashboard for APEX (Autonomous Predictive Execution),
built on AEGIS Runtime. See the top-level `project/README.md` for the
full architecture and how the backend and frontend fit together.

## Screens

- **Dashboard** – backend health, tool registry, recent executions.
- **New Goal** – submit a free-form goal (analyzed and planned by
  Gemini via AEGIS Runtime), or click "Run Recovery Demo" for the
  deterministic failure → recovery → success scenario.
- **Execution View** – the live execution timeline: status, current
  task, recovery attempts, approve/cancel controls, and the full
  runtime event stream.
- **Task Graph** – the plan's dependency graph, colored by live task
  status for the selected execution.
- **Execution History** – all past executions.

## Running locally

```bash
npm install
cp .env.example .env   # point VITE_API_BASE at your APEX backend
npm run dev
```

The dev server proxies nothing automatically — `VITE_API_BASE` must
point at a running APEX backend (default `http://localhost:8000`).
WebSocket streaming derives its URL from the same base.

## Build

```bash
npm run build
```

Type-checks with `tsc -b` and produces a static bundle in `dist/`.

## How real-time updates work

`useExecutionStream` opens a WebSocket to
`/api/executions/{id}/stream` as a low-latency "something happened"
signal, but always re-fetches `GET /api/executions/{id}` (deduped by
event id) as the source of truth for event content and ordering. If
the socket never connects, REST polling alone keeps the view live —
there's no code path that fabricates state client-side.
