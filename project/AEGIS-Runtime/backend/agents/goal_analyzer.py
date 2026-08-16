from backend.models.schemas import StructuredGoal
from backend.config.config import get_gemini_client, generate_content_with_retry


class GoalAnalyzer:
    """
    Converts a natural-language user goal
    into a validated StructuredGoal using Gemini.
    """

    def __init__(self, client=None):
        self.client = client or get_gemini_client()

    def analyze(self, goal: str) -> StructuredGoal:

        if not goal or not goal.strip():
            raise ValueError("User goal cannot be empty.")

        prompt = f"""
You are the Goal Analyzer of AEGIS Runtime.

Your job is to convert a user's natural-language goal into
a structured StructuredGoal.

IMPORTANT RULES:

1. Identify the main objective.
2. Identify the domain.
3. Extract inputs explicitly mentioned by the user.
4. Extract explicit requirements.
5. Extract constraints and limitations.
6. Extract success criteria.
7. Identify important ambiguities.
8. Do not invent information that the user did not provide.

CONSTRAINT RULE:

If the user specifies any condition that limits or constrains
how the goal should be achieved, include that condition in
the "constraints" field.

This includes:

- measurable limitations
- thresholds
- minimum values
- maximum values
- required performance levels
- technology restrictions
- resource restrictions
- time restrictions
- budget restrictions
- accuracy requirements
- quality requirements
- other explicit conditions

IMPORTANT:

Do NOT leave "constraints" empty when the user's goal clearly
contains a limiting condition.

For example, if the user says:

"The model should achieve at least 80% accuracy."

Then "constraints" MUST contain something similar to:

"Model accuracy must be at least 80%."

It may ALSO appear in "success_criteria" because achieving
80% accuracy can define successful completion.

DISTINCTION:

- requirements = what the user explicitly wants to build/use/do
- constraints = conditions or limits that restrict how it should
  be achieved
- success_criteria = measurable or explicit conditions that
  determine whether the goal is successfully completed
- ambiguities = important information that is missing or unclear

Do not invent constraints, requirements, inputs, or success
criteria that are not supported by the user's goal.

USER GOAL:

{goal}
"""

        response = generate_content_with_retry(
            self.client,
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": StructuredGoal,
            },
        )

        return StructuredGoal.model_validate_json(response.text)
