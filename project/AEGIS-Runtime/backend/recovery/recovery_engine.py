from backend.config.config import get_gemini_client, generate_content_with_retry
from backend.models.schemas import (
    TaskNode,
    VerificationResult,
    RecoveryAction,
    RecoveryDecision,
)


class RecoveryEngine:
    """
    Determines how AEGIS should recover from a failed task.
    """

    def __init__(self):
        self.client = get_gemini_client()

    def decide(
        self,
        task: TaskNode,
        verification: VerificationResult,
        attempts: int = 0,
    ) -> RecoveryDecision:

        # Prevent infinite retries.
        if attempts >= 2:
            return RecoveryDecision(
                action=RecoveryAction.REPLAN,
                reason=(
                    "The task has failed multiple times. "
                    "The workflow should be replanned."
                ),
                attempts=attempts,
            )

        prompt = f"""
You are the Recovery Engine of AEGIS Runtime.

A task failed verification.

TASK:
{task.description}

REQUIRED CAPABILITIES:
{task.required_capabilities}

VERIFICATION:
{verification.model_dump_json(indent=2)}

PREVIOUS ATTEMPTS:
{attempts}

Choose the best recovery strategy:

RETRY:
Use when the same worker can reasonably try again.

REASSIGN:
Use when another capability or worker should handle the task.

REPLAN:
Use when the task itself or its dependencies need to change.

ABORT:
Use only when continuing is not reasonable.

Return a single recovery decision.
"""

        try:
            response = generate_content_with_retry(
                self.client,
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": RecoveryDecision,
                },
            )

            return RecoveryDecision.model_validate_json(
                response.text
            )

        except Exception as error:

            print(
                f"[Recovery] Gemini unavailable: {error}"
            )

            # Safe deterministic fallback.
            if attempts < 1:
                return RecoveryDecision(
                    action=RecoveryAction.RETRY,
                    reason=(
                        "Recovery model was temporarily unavailable. "
                        "Retrying the task using the existing worker."
                    ),
                    attempts=attempts + 1,
                )

            return RecoveryDecision(
                action=RecoveryAction.REPLAN,
                reason=(
                    "Recovery model remained unavailable after retry. "
                    "Workflow should be replanned."
                ),
                attempts=attempts,
            )
