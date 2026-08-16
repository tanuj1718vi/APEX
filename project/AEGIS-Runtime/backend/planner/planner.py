from typing import Optional

from backend.models.schemas import (
    StructuredGoal,
    ExecutionPlan,
    TaskNode,
    VerificationResult,
)

from backend.config.config import get_gemini_client, generate_content_with_retry


class Planner:
    """
    Converts a StructuredGoal into an executable ExecutionPlan.

    Supports:

    1. Initial planning
       goal -> execution plan

    2. Failure-aware replanning
       goal + failed task + verification
       -> improved execution plan
    """

    def __init__(self, client=None):
        """
        Initialize Planner.

        A client can be injected for testing.
        If no client is provided, the real Gemini client is used.
        """
        self.client = client or get_gemini_client()

    def create_plan(
        self,
        goal: StructuredGoal,
        failed_task: Optional[TaskNode] = None,
        verification: Optional[VerificationResult] = None,
        recovery_reason: Optional[str] = None,
    ) -> ExecutionPlan:
        """
        Create an execution plan.

        If failed_task is provided, create a revised plan
        that addresses the failure.
        """

        # ==================================================
        # INITIAL PLANNING
        # ==================================================

        if failed_task is None:

            prompt = f"""
You are the Planner of AEGIS Runtime.

Your job is to convert a structured user goal into
a practical execution plan.

IMPORTANT RULES:

1. Break the goal into clear, actionable tasks.
2. Tasks must represent work that can actually be executed.
3. Identify dependencies between tasks.
4. Identify capabilities required for each task.
5. Do not execute any task.
6. Do not invent requirements that are not present in the goal.
7. Keep the plan as simple as possible while still accomplishing the goal.
8. The final tasks should collectively satisfy the success criteria.
9. Every task must have a clear and verifiable deliverable.
10. Avoid vague tasks such as "do the work" or "complete the task".
11. Respect all constraints from the structured goal.
12. Do not remove measurable requirements or performance thresholds.

STRUCTURED GOAL:

{goal.model_dump_json(indent=2)}

Create the execution plan as structured JSON.
"""

        # ==================================================
        # FAILURE-AWARE REPLANNING
        # ==================================================

        else:

            verification_json = (
                verification.model_dump_json(indent=2)
                if verification is not None
                else "No verification result provided."
            )

            prompt = f"""
You are the Replanning Engine of AEGIS Runtime.

The original execution plan failed verification.

Your job is to create a NEW execution plan that
still accomplishes the original goal while addressing
the failure.

IMPORTANT RULES:

1. Preserve the original user objective.
2. Analyze why the previous task failed.
3. Address every important verification issue.
4. Create concrete and executable tasks.
5. Every task must have a clear deliverable.
6. Tasks must produce outputs that can be independently verified.
7. Add missing steps when necessary.
8. Remove or modify ineffective steps when necessary.
9. Identify dependencies between tasks.
10. Identify required capabilities.
11. Do not execute any task.
12. Do not invent requirements unrelated to the goal.
13. Keep the revised plan as simple as possible.
14. The new plan must be meaningfully improved because
    the previous plan failed verification.
15. Preserve all important constraints from the original goal.
16. Do not weaken or remove measurable performance requirements.

ORIGINAL STRUCTURED GOAL:

{goal.model_dump_json(indent=2)}

FAILED TASK:

{failed_task.model_dump_json(indent=2)}

VERIFICATION RESULT:

{verification_json}

RECOVERY REASON:

{recovery_reason or "No recovery reason provided."}

Create a revised execution plan as structured JSON.
"""

        # ==================================================
        # GENERATE PLAN
        # ==================================================

        response = generate_content_with_retry(
            self.client,
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ExecutionPlan,
            },
        )

        # ==================================================
        # VALIDATE RESPONSE
        # ==================================================

        return ExecutionPlan.model_validate_json(response.text)
