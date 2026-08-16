import type { ExecutionEvent } from "../api/types";

type Tone = "signal" | "cognition" | "alert" | "critical";

interface DisplayEvent {
  icon: string;
  label: string;
  detail?: string;
}

/**
 * Maps an event's icon to a semantic tone, consistent across the
 * app: signal = execution happening, cognition = Gemini reasoning,
 * alert = warning/retry, critical = failure/abort. This is what
 * colors the timeline's left-border glow.
 */
function toneForIcon(icon: string): Tone {
  switch (icon) {
    case "🧠":
      return "cognition";
    case "⚠":
    case "↻":
      return "alert";
    case "✖":
      return "critical";
    default:
      return "signal";
  }
}

function describeEvent(event: ExecutionEvent): DisplayEvent {
  const p = event.payload || {};

  switch (event.event_type) {
    case "run_started":
      return { icon: "▶", label: "Execution started" };
    case "goal_analysis_started":
      return { icon: "🧠", label: "Analyzing goal" };
    case "goal_analyzed":
      return { icon: "✓", label: "Goal analyzed" };
    case "planning_started":
      return { icon: "🧠", label: "Generating plan" };
    case "plan_generated":
      return {
        icon: "✓",
        label: "Plan generated",
        detail: p.plan?.tasks ? `${p.plan.tasks.length} task(s)` : undefined,
      };
    case "task_graph_created":
      return { icon: "✓", label: "Task graph created" };
    case "task_started":
      return {
        icon: "▶",
        label: `Task started: ${p.task_id}`,
        detail: p.description,
      };
    case "governance_evaluated":
      return {
        icon: p.outcome === "requires_approval" || p.outcome === "blocked" ? "⚠" : "✓",
        label: `Governance: ${p.tool} (${p.risk_level}) — ${p.outcome}`,
        detail: p.reason,
      };
    case "task_executed":
      return {
        icon: "✓",
        label: `Task executed: ${p.task_id}`,
        detail: p.worker ? `worker: ${p.worker}` : undefined,
      };
    case "verification_completed":
      return {
        icon: p.passed ? "✓" : "⚠",
        label: p.passed
          ? `Verification passed: ${p.task_id}`
          : `Verification failed: ${p.task_id}`,
        detail: p.reasoning,
      };
    case "task_completed":
      return { icon: "✓", label: `Task completed: ${p.task_id}` };
    case "task_failed":
      return {
        icon: "⚠",
        label: `Task failed: ${p.task_id}`,
        detail: p.reasoning,
      };
    case "recovery_decided":
      return {
        icon: "🧠",
        label: `Recovery planned (${String(p.action).toUpperCase()}): ${p.task_id}`,
        detail: p.reason,
      };
    case "task_retrying":
      return { icon: "↻", label: `Retrying task: ${p.task_id}` };
    case "task_reassigning":
      return {
        icon: "↻",
        label: `Reassigning task: ${p.task_id}`,
        detail: p.excluded_workers?.length
          ? `excluding: ${p.excluded_workers.join(", ")}`
          : undefined,
      };
    case "replanning_started":
      return { icon: "↻", label: `Replanning workflow (task ${p.task_id})` };
    case "replanning_completed":
      return {
        icon: "✓",
        label: "Replanning completed",
        detail: p.task_count ? `${p.task_count} task(s) in new plan` : undefined,
      };
    case "task_aborted":
      return { icon: "✖", label: `Task aborted: ${p.task_id}`, detail: p.reason };
    case "execution_created":
      return {
        icon: "▶",
        label: "Execution created",
        detail: p.governance_reason,
      };
    case "execution_approved":
      return { icon: "✓", label: "Execution approved" };
    case "cancel_requested":
      return { icon: "✖", label: "Cancellation requested" };
    case "run_completed":
      return { icon: "✓", label: "GOAL COMPLETED" };
    case "run_failed":
      return { icon: "✖", label: "Execution failed", detail: p.error };
    case "run_cancelled":
      return { icon: "✖", label: "Execution cancelled" };
    default:
      return { icon: "•", label: event.event_type };
  }
}

export function EventTimeline({ events }: { events: ExecutionEvent[] }) {
  if (events.length === 0) {
    return <div className="empty-state">No events yet.</div>;
  }

  return (
    <div className="timeline">
      {events.map((event, index) => {
        const display = describeEvent(event);
        const tone = toneForIcon(display.icon);
        return (
          <div
            className={`timeline-item tone-${tone}`}
            key={event.id}
            style={{ animationDelay: `${Math.min(index, 20) * 15}ms` }}
          >
            <div className="timeline-icon">{display.icon}</div>
            <div className="timeline-body">
              <div className="timeline-label">{display.label}</div>
              {display.detail && (
                <div className="timeline-detail">{String(display.detail)}</div>
              )}
            </div>
            <div className="timeline-time">
              {new Date(event.created_at * 1000).toLocaleTimeString()}
            </div>
          </div>
        );
      })}
    </div>
  );
}
