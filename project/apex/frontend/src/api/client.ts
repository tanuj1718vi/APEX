import type {
  ToolDefinition,
  SubmitGoalResponse,
  Execution,
  ExecutionDetail,
} from "./types";

export const API_BASE =
  (import.meta as any).env?.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore, fall back to statusText
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; service: string }>("/api/health"),

  listTools: () => request<{ tools: ToolDefinition[] }>("/api/tools"),

  submitGoal: (goal: string) =>
    request<SubmitGoalResponse>("/api/goals", {
      method: "POST",
      body: JSON.stringify({ goal }),
    }),

  submitRecoveryDemoGoal: () =>
    request<SubmitGoalResponse>("/api/goals/demo-recovery", {
      method: "POST",
    }),

  createExecution: (goalId: string, autoApproveHigh: boolean) =>
    request<{ execution_id: string; status: string }>("/api/executions", {
      method: "POST",
      body: JSON.stringify({
        goal_id: goalId,
        auto_approve_high: autoApproveHigh,
      }),
    }),

  listExecutions: () =>
    request<{ executions: Execution[] }>("/api/executions"),

  getExecution: (executionId: string) =>
    request<ExecutionDetail>(`/api/executions/${executionId}`),

  getGoal: (goalId: string) =>
    request<{
      id: string;
      user_goal: string;
      structured_goal: any;
      plan: { objective: string; tasks: any[] } | null;
      max_risk: string;
      created_at: number;
    }>(`/api/goals/${goalId}`),

  approveExecution: (executionId: string) =>
    request<Execution>(`/api/executions/${executionId}/approve`, {
      method: "POST",
    }),

  cancelExecution: (executionId: string) =>
    request<Execution>(`/api/executions/${executionId}/cancel`, {
      method: "POST",
    }),

  streamUrl: (executionId: string) => {
    const wsBase = API_BASE.replace(/^http/, "ws");
    return `${wsBase}/api/executions/${executionId}/stream`;
  },
};
