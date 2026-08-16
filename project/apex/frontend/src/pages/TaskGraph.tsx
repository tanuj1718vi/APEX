import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Execution, ExecutionEvent, PlanTask } from "../api/types";
import { Badge } from "../components/Badge";

type TaskStatus = "pending" | "running" | "completed" | "failed";

function computeTaskStatuses(events: ExecutionEvent[]): Record<string, TaskStatus> {
  const statuses: Record<string, TaskStatus> = {};

  for (const event of events) {
    const taskId = event.payload?.task_id;
    if (!taskId) continue;

    if (event.event_type === "task_started") {
      statuses[taskId] = "running";
    } else if (event.event_type === "task_completed") {
      statuses[taskId] = "completed";
    } else if (
      event.event_type === "task_failed" ||
      event.event_type === "task_aborted"
    ) {
      // Only mark failed if it hasn't since completed (a retry might
      // still succeed later in the event stream).
      if (statuses[taskId] !== "completed") {
        statuses[taskId] = "failed";
      }
    } else if (
      event.event_type === "task_retrying" ||
      event.event_type === "task_reassigning"
    ) {
      statuses[taskId] = "running";
    }
  }

  return statuses;
}

const STATUS_BADGE: Record<TaskStatus, string> = {
  pending: "medium",
  running: "running",
  completed: "completed",
  failed: "failed",
};

export function TaskGraph() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [tasks, setTasks] = useState<PlanTask[]>([]);
  const [statuses, setStatuses] = useState<Record<string, TaskStatus>>({});
  const [objective, setObjective] = useState<string>("");

  useEffect(() => {
    api.listExecutions().then((r) => {
      setExecutions(r.executions);
      if (r.executions.length > 0 && !selectedId) {
        setSelectedId(r.executions[0].id);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedId) return;

    let cancelled = false;

    async function load() {
      const detail = await api.getExecution(selectedId);
      if (cancelled) return;
      setStatuses(computeTaskStatuses(detail.events));

      const goal = await api.getGoal(detail.execution.goal_id);
      if (cancelled) return;
      setTasks(goal.plan?.tasks ?? []);
      setObjective(goal.plan?.objective ?? goal.user_goal);
    }

    load();
    const interval = window.setInterval(load, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [selectedId]);

  return (
    <div>
      <p className="page-eyebrow">plan / dependency graph</p>
      <h1 className="page-title">Task Graph</h1>
      <p className="page-subtitle">
        Dependency graph for a selected execution, colored by live status.
      </p>

      <div className="card">
        <div className="card-title">Execution</div>
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          style={{
            background: "var(--void)",
            color: "var(--text)",
            border: "1px solid var(--line)",
            borderRadius: 8,
            padding: "10px 12px",
            width: "100%",
            fontFamily: "var(--mono)",
            fontSize: 13,
          }}
        >
          {executions.length === 0 && <option value="">No executions yet</option>}
          {executions.map((execution) => (
            <option key={execution.id} value={execution.id}>
              {execution.id} — {execution.status}
            </option>
          ))}
        </select>
      </div>

      {tasks.length > 0 && (
        <div className="card">
          <div className="card-title">{objective}</div>
          {tasks.map((task) => {
            const status = statuses[task.id] ?? "pending";
            return (
              <div className="task-node" key={task.id}>
                <div className="task-node-header">
                  <span className="task-node-id">{task.id}</span>
                  <Badge kind={STATUS_BADGE[status]} label={status} />
                </div>
                <div className="task-node-desc">{task.description}</div>
                <div className="task-node-deps">
                  capabilities: {task.required_capabilities.join(", ")}
                  {task.dependencies.length > 0 &&
                    ` · depends on: ${task.dependencies.join(", ")}`}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {tasks.length === 0 && selectedId && (
        <div className="empty-state">Loading task graph...</div>
      )}
    </div>
  );
}
