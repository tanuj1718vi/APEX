import { useState } from "react";
import { Dashboard } from "./pages/Dashboard";
import { NewGoal } from "./pages/NewGoal";
import { ExecutionView } from "./pages/ExecutionView";
import { TaskGraph } from "./pages/TaskGraph";
import { ExecutionHistory } from "./pages/ExecutionHistory";
import { useBackendHealth } from "./hooks/useBackendHealth";

type Screen = "dashboard" | "new-goal" | "execution" | "task-graph" | "history";

const NAV_ITEMS: { key: Screen; label: string }[] = [
  { key: "dashboard", label: "Dashboard" },
  { key: "new-goal", label: "New Goal" },
  { key: "execution", label: "Execution View" },
  { key: "task-graph", label: "Task Graph" },
  { key: "history", label: "Execution History" },
];

export default function App() {
  const [screen, setScreen] = useState<Screen>("dashboard");
  const [activeExecutionId, setActiveExecutionId] = useState<string | null>(null);
  const health = useBackendHealth();

  function openExecution(id: string) {
    setActiveExecutionId(id);
    setScreen("execution");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span
            className={`brand-heartbeat ${health === "ok" ? "ok" : health === "unreachable" ? "down" : ""}`}
            title={`Backend: ${health}`}
          />
          <div className="brand-text">
            <p className="brand-title">APEX</p>
            <p className="brand-subtitle">Autonomous Predictive Execution</p>
          </div>
        </div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              className={`nav-item ${screen === item.key ? "active" : ""}`}
              onClick={() => setScreen(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main">
        {screen === "dashboard" && <Dashboard onOpenExecution={openExecution} />}
        {screen === "new-goal" && (
          <NewGoal onExecutionStarted={openExecution} />
        )}
        {screen === "execution" &&
          (activeExecutionId ? (
            <ExecutionView executionId={activeExecutionId} />
          ) : (
            <div className="empty-state">
              No execution selected. Start one from "New Goal" or pick one
              from "Execution History".
            </div>
          ))}
        {screen === "task-graph" && <TaskGraph />}
        {screen === "history" && (
          <ExecutionHistory onOpenExecution={openExecution} />
        )}
      </main>
    </div>
  );
}
