import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Execution } from "../api/types";
import { Badge } from "../components/Badge";

export function ExecutionHistory({
  onOpenExecution,
}: {
  onOpenExecution: (id: string) => void;
}) {
  const [executions, setExecutions] = useState<Execution[]>([]);

  useEffect(() => {
    function load() {
      api.listExecutions().then((r) => setExecutions(r.executions));
    }
    load();
    const interval = window.setInterval(load, 3000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <div>
      <p className="page-eyebrow">archive</p>
      <h1 className="page-title">Execution History</h1>
      <p className="page-subtitle">All executions, most recent first.</p>

      <div className="card">
        {executions.length === 0 ? (
          <div className="empty-state">No executions yet.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Execution</th>
                <th>Goal</th>
                <th>Status</th>
                <th>Approved</th>
                <th>Created</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((execution) => (
                <tr
                  key={execution.id}
                  onClick={() => onOpenExecution(execution.id)}
                >
                  <td>{execution.id}</td>
                  <td>{execution.goal_id}</td>
                  <td>
                    <Badge kind={execution.status} />
                  </td>
                  <td>{execution.approved ? "yes" : "no"}</td>
                  <td>{new Date(execution.created_at * 1000).toLocaleString()}</td>
                  <td>{new Date(execution.updated_at * 1000).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
