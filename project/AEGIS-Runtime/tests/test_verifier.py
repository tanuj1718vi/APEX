from backend.verifier.verifier import VerificationEngine
from backend.models.schemas import TaskNode


class FakeResponse:

    text = """
    {
        "passed": true,
        "score": 0.95,
        "reasoning": "The result addresses the task requirements."
    }
    """


class FakeModels:

    def generate_content(self, **kwargs):
        return FakeResponse()


class FakeClient:

    def __init__(self):
        self.models = FakeModels()


def test_verifier():

    # ---------------------------------------------
    # Create task
    # ---------------------------------------------

    task = TaskNode(
        id="task_1",
        description=(
            "Identify the main requirements for "
            "an AI student prediction system."
        ),
        dependencies=[],
        required_capabilities=[
            "requirements_gathering"
        ],
    )

    # ---------------------------------------------
    # Task result
    # ---------------------------------------------

    result = """
    The system should collect student academic data,
    preprocess the data, train a prediction model,
    evaluate the model, and provide predictions.
    """

    # ---------------------------------------------
    # Create verifier with fake Gemini client
    # ---------------------------------------------

    verifier = VerificationEngine(
        client=FakeClient()
    )

    # ---------------------------------------------
    # Verify result
    # ---------------------------------------------

    verification = verifier.verify(
        task,
        result,
    )

    # ---------------------------------------------
    # Assertions
    # ---------------------------------------------

    assert verification is not None

    assert verification.passed is True

    assert verification.score >= 0.8

    assert verification.reasoning

    # ---------------------------------------------
    # Output
    # ---------------------------------------------

    print("\n=== AEGIS VERIFIER TEST PASSED ===")

    print(
        verification.model_dump_json(
            indent=2
        )
    )
