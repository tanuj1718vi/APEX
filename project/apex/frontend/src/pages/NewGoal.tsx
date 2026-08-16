import { useState } from "react";
import { api } from "../api/client";
import type { SubmitGoalResponse } from "../api/types";
import { Badge } from "../components/Badge";

export function NewGoal({
  onExecutionStarted,
}: {
  onExecutionStarted: (executionId: string) => void;
}) {
  const [goalText, setGoalText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SubmitGoalResponse | null>(null);
  const [autoApproveHigh, setAutoApproveHigh] = useState(false);

  async function handleSubmit() {
    if (!goalText.trim()) return;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.submitGoal(goalText.trim());
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRunDemo() {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.submitRecoveryDemoGoal();
      setGoalText(response.structured_goal.objective);
      setResult(response);
      setAutoApproveHigh(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStartExecution() {
    if (!result) return;
    setStarting(true);
    setError(null);
    try {
      const execution = await api.createExecution(
        result.goal_id,
        autoApproveHigh
      );
      onExecutionStarted(execution.execution_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStarting(false);
    }
  }

  return (
    <div>
      <p className="page-eyebrow">submit / analyze / plan</p>
      <h1 className="page-title">New Goal</h1>
      <p className="page-subtitle">
        Describe a goal in plain language. Gemini will analyze it and
        generate a task graph for AEGIS Runtime to execute.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <div className="card-title">Goal</div>
        <textarea
          rows={4}
          placeholder="e.g. Check system health and generate a status report"
          value={goalText}
          onChange={(e) => setGoalText(e.target.value)}
        />
        <div className="btn-row">
          <button className="btn" onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Analyzing..." : "Analyze Goal"}
          </button>
          <button className="demo-btn" onClick={handleRunDemo} disabled={submitting}>
            ⚡ Run Recovery Demo
          </button>
        </div>
        <p className="risk-note">
          "Run Recovery Demo" loads a deterministic scenario: check
          state → analyze → repair (intentionally fails once) →
          verify, so you can see real failure → recovery → success.
        </p>
      </div>

      {result && (
        <div className="card">
          <div className="card-title">Generated Plan</div>
          <p style={{ marginTop: 0 }}>
            <Badge kind={result.max_risk} /> highest risk in this plan
          </p>

          {result.plan.tasks.map((task) => (
            <div className="task-node" key={task.id}>
              <div className="task-node-header">
                <span className="task-node-id">{task.id}</span>
                <span>
                  {task.required_capabilities.map((c) => (
                    <Badge key={c} kind="running" label={c} />
                  ))}
                </span>
              </div>
              <div className="task-node-desc">{task.description}</div>
              {task.dependencies.length > 0 && (
                <div className="task-node-deps">
                  depends on: {task.dependencies.join(", ")}
                </div>
              )}
            </div>
          ))}

          <div className="checkbox-row">
            <input
              type="checkbox"
              checked={autoApproveHigh}
              onChange={(e) => setAutoApproveHigh(e.target.checked)}
              id="auto-approve"
            />
            <label htmlFor="auto-approve">
              Auto-approve HIGH risk actions (CRITICAL actions always
              require manual approval, regardless of this setting)
            </label>
          </div>

          <div className="btn-row">
            <button
              className="btn"
              onClick={handleStartExecution}
              disabled={starting}
            >
              {starting ? "Starting..." : "Start Execution"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
