from backend.agents.goal_analyzer import GoalAnalyzer


class FakeResponse:

    text = """
    {
        "objective": "Build a Python machine learning system to predict student performance",
        "domain": "Machine Learning",
        "inputs": [
            "students.csv"
        ],
        "requirements": [
            "Python machine learning system"
        ],
        "constraints": [
            "Model accuracy must be at least 80%."
        ],
        "success_criteria": [
            "Model should achieve at least 80% accuracy"
        ],
        "ambiguities": []
    }
    """


class FakeModels:

    def generate_content(self, **kwargs):
        return FakeResponse()


class FakeClient:

    def __init__(self):
        self.models = FakeModels()


def test_goal_analyzer():

    # ---------------------------------------------
    # Create Goal Analyzer with fake Gemini client
    # ---------------------------------------------

    analyzer = GoalAnalyzer(
        client=FakeClient()
    )

    # ---------------------------------------------
    # Analyze goal
    # ---------------------------------------------

    result = analyzer.analyze(
        """
        Build a Python machine learning system using students.csv
        to predict student performance.
        The model should achieve at least 80% accuracy.
        """
    )

    # ---------------------------------------------
    # Assertions
    # ---------------------------------------------

    assert result.objective

    assert result.domain

    assert "students.csv" in result.inputs

    assert result.requirements

    assert result.constraints

    assert any(
        "80%" in constraint
        for constraint in result.constraints
    )

    assert result.success_criteria

    # ---------------------------------------------
    # Display result
    # ---------------------------------------------

    print("\n=== AEGIS GOAL ANALYZER TEST PASSED ===")

    print(
        result.model_dump_json(
            indent=2
        )
    )
