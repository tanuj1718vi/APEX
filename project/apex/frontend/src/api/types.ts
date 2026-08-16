export interface ToolDefinition {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  risk_level: "low" | "medium" | "high" | "critical";
}

export interface PlanTask {
  id: string;
  description: string;
  dependencies: string[];
  required_capabilities: string[];
}

export interface ExecutionPlan {
  objective: string;
  tasks: PlanTask[];
}

export interface StructuredGoal {
  objective: string;
  domain?: string;
  inputs: string[];
  requirements: string[];
  constraints: string[];
  success_criteria: string[];
  ambiguities: string[];
}

export interface SubmitGoalResponse {
  goal_id: string;
  structured_goal: StructuredGoal;
  plan: ExecutionPlan;
  max_risk: "low" | "medium" | "high" | "critical";
}

export type ExecutionStatus =
  | "running"
  | "pending_approval"
  | "completed"
  | "failed"
  | "cancel_requested"
  | "cancelled";

export interface Execution {
  id: string;
  goal_id: string;
  status: ExecutionStatus;
  auto_approve_high: boolean;
  approved: boolean;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: number;
  updated_at: number;
}

export interface ExecutionEvent {
  id: string;
  execution_id: string;
  event_type: string;
  payload: Record<string, any>;
  created_at: number;
}

export interface ExecutionDetail {
  execution: Execution;
  events: ExecutionEvent[];
}
