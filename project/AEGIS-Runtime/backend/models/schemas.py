from pydantic import BaseModel, Field
from typing import List

from enum import Enum

class StructuredGoal(BaseModel):
    """
    Structured representation of a user's goal.
    """

    objective: str = Field(
        ...,
        description="Primary objective the user wants to accomplish"
    )

    domain: str = Field(
        default="unknown",
        description="General domain of the task"
    )

    inputs: List[str] = Field(
        default_factory=list,
        description="Inputs explicitly mentioned by the user"
    )

    requirements: List[str] = Field(
        default_factory=list,
        description="Explicit requirements from the user"
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Restrictions or limitations specified by the user"
    )

    success_criteria: List[str] = Field(
        default_factory=list,
        description="Conditions that define success"
    )

    ambiguities: List[str] = Field(
        default_factory=list,
        description="Important missing or unclear information"
    )
class PlanTask(BaseModel):
    """A single executable task in an AEGIS plan."""

    id: str = Field(
        ...,
        description="Unique identifier for the task"
    )

    description: str = Field(
        ...,
        description="What this task needs to accomplish"
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="IDs of tasks that must finish first"
    )

    required_capabilities: List[str] = Field(
        default_factory=list,
        description="Capabilities required to execute the task"
    )


class ExecutionPlan(BaseModel):
    """Execution plan generated from a StructuredGoal."""

    objective: str = Field(
        ...,
        description="Objective the plan is designed to achieve"
    )

    tasks: List[PlanTask] = Field(
        default_factory=list,
        description="Ordered or dependency-aware execution tasks"
    )
class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskNode(BaseModel):
    id: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
class VerificationResult(BaseModel):
    """Result produced by the AEGIS verification engine."""

    passed: bool = Field(
        ...,
        description="Whether the task result is valid"
    )

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )

    reasoning: str = Field(
        ...,
        description="Why the result passed or failed"
    )

    issues: List[str] = Field(
        default_factory=list,
        description="Problems found in the result"
    )
class RecoveryAction(str, Enum):
    RETRY = "retry"
    REASSIGN = "reassign"
    REPLAN = "replan"
    ABORT = "abort"


class RecoveryDecision(BaseModel):
    """Decision made after a task failure."""

    action: RecoveryAction

    reason: str

    attempts: int = 0
