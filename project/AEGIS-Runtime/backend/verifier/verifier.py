from typing import Any

from backend.config.config import get_gemini_client, generate_content_with_retry
from backend.models.schemas import TaskNode, VerificationResult


class VerificationEngine:
    """
    Independently evaluates whether a task result
    satisfies the requirements of the task.
    """

    def __init__(self, client=None):
        self.client = client or get_gemini_client()

    def verify(
        self,
        task: TaskNode,
        result: Any,
    ) -> VerificationResult:

        prompt = f"""
You are the Verification Engine of AEGIS Runtime.

Your job is to independently check whether the result
of a task actually satisfies the task requirements.

TASK:
{task.description}

REQUIRED CAPABILITIES:
{task.required_capabilities}

RESULT:
{result}

Evaluate the result carefully.

Rules:

1. Do not assume the result is correct simply because
   the worker reported success.
2. Check whether the task was actually addressed.
3. Identify missing information or obvious problems.
4. Give a score from 0.0 to 1.0.
5. Set passed=true only when the result is sufficiently valid.
"""

        response = generate_content_with_retry(
            self.client,
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": VerificationResult,
            },
        )

        return VerificationResult.model_validate_json(
            response.text
        )
