import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Execution, ToolDefinition } from "../api/types";
import { Badge } from "../components/Badge";

export function Dashboard({
  onOpenExecution,
}: {
  onOpenExecution: (id: string) => void;
}) {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [health, setHealth] = useState<string>("checking...");

  useEffect(() => {
    api.health().then((r) => setHealth(r.status)).catch(() => setHealth("unreachable"));
    api.listTools().then((r) => setTools(r.tools)).catch(() => {});
    api.listExecutions().then((r) => setExecutions(r.executions)).catch(() => {});
  }, []);

  const running = executions.filter((e) => e.status === "running").length;
  const completed = executions.filter((e) => e.status === "completed").length;
  const failed = executions.filter((e) => e.status === "failed").length;

  return (
    <div>
      <p className="page-eyebrow">system overview</p>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">
        APEX — Autonomous Predictive Execution, built on AEGIS Runtime.
      </p>

      <div className="grid grid-3">
        <div className="card">
          <div className="card-title">Backend</div>
          <div className="stat-value">
            <Badge kind={health === "ok" ? "completed" : "failed"} label={health} />
          </div>
          <div className="stat-label">API health</div>
        </div>
        <div className="card">
          <div className="card-title">Running Executions</div>
          <div className="stat-value">{running}</div>
          <div className="stat-label">of {executions.length} total</div>
        </div>
        <div className="card">
          <div className="card-title">Completed / Failed</div>
          <div className="stat-value">
            {completed} / {failed}
          </div>
          <div className="stat-label">all-time</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Registered Tools ({tools.length})</div>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {tools.map((tool) => (
              <tr key={tool.name}>
                <td>{tool.name}</td>
                <td>{tool.description}</td>
                <td>
                  <Badge kind={tool.risk_level} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-title">Recent Executions</div>
        {executions.length === 0 ? (
          <div className="empty-state">
            No executions yet. Start one from "New Goal".
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Execution</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {executions.slice(0, 8).map((execution) => (
                <tr
                  key={execution.id}
                  onClick={() => onOpenExecution(execution.id)}
                >
                  <td>{execution.id}</td>
                  <td>
                    <Badge kind={execution.status} />
                  </td>
                  <td>
                    {new Date(execution.created_at * 1000).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
