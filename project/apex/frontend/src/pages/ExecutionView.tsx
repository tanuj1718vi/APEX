import { useState } from "react";
import { api } from "../api/client";
import { useExecutionStream } from "../hooks/useExecutionStream";
import { EventTimeline } from "../components/EventTimeline";
import { Badge } from "../components/Badge";
import { PulseWaveform, type PulseTone } from "../components/PulseWaveform";

function pulseToneForStatus(status: string | undefined): PulseTone {
  switch (status) {
    case "running":
      return "live";
    case "completed":
      return "success";
    case "failed":
    case "cancelled":
      return "critical";
    default:
      return "idle";
  }
}

export function ExecutionView({ executionId }: { executionId: string }) {
  const { execution, events, connected } = useExecutionStream(executionId);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function handleApprove() {
    setBusy(true);
    setActionError(null);
    try {
      await api.approveExecution(executionId);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleCancel() {
    setBusy(true);
    setActionError(null);
    try {
      await api.cancelExecution(executionId);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const lastTaskStarted = [...events]
    .reverse()
    .find((e) => e.event_type === "task_started");

  const recoveryAttempts = events.filter(
    (e) => e.event_type === "recovery_decided"
  ).length;

  const failedVerifications = events.filter(
    (e) => e.event_type === "verification_completed" && !e.payload.passed
  ).length;

  return (
    <div>
      <p className="page-eyebrow">execution / {executionId}</p>
      <h1 className="page-title">Execution View</h1>
      <div style={{ marginBottom: 22 }}>
        <PulseWaveform
          tone={pulseToneForStatus(execution?.status)}
          label={connected ? "stream connected" : "polling"}
        />
      </div>

      {actionError && <div className="error-banner">{actionError}</div>}

      <div className="grid grid-3">
        <div className="card">
          <div className="card-title">Status</div>
          <div className="stat-value">
            {execution ? <Badge kind={execution.status} /> : "loading..."}
          </div>
          {execution?.status === "pending_approval" && (
            <div className="btn-row">
              <button className="btn" onClick={handleApprove} disabled={busy}>
                Approve
              </button>
              <button className="btn-danger" onClick={handleCancel} disabled={busy}>
                Cancel
              </button>
            </div>
          )}
          {execution?.status === "running" && (
            <div className="btn-row">
              <button className="btn-danger" onClick={handleCancel} disabled={busy}>
                Cancel Execution
              </button>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">Current Task</div>
          <div className="stat-value" style={{ fontSize: 16 }}>
            {lastTaskStarted ? lastTaskStarted.payload.task_id : "—"}
          </div>
          <div className="stat-label">
            {lastTaskStarted?.payload.description ?? "no task started yet"}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Recovery Attempts</div>
          <div className="stat-value">{recoveryAttempts}</div>
          <div className="stat-label">
            {failedVerifications} verification failure(s) observed
          </div>
        </div>
      </div>

      {execution?.error && (
        <div className="error-banner">Error: {execution.error}</div>
      )}

      {execution?.result && (
        <div className="card">
          <div className="card-title">Final Result</div>
          <pre style={{ margin: 0, fontSize: 12, whiteSpace: "pre-wrap" }}>
            {JSON.stringify(execution.result, null, 2)}
          </pre>
        </div>
      )}

      <div className="card">
        <div className="card-title">Runtime Events</div>
        <EventTimeline events={events} />
      </div>
    </div>
  );
}
