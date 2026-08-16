from backend.planner.planner import Planner
from backend.models.schemas import StructuredGoal


class FakeResponse:
    """
    Fake Gemini response used for Planner testing.
    """

    text = """
    {
        "objective": "Build a Python machine learning system to predict student performance",
        "tasks": [
            {
                "id": "task_1",
                "description": "Load and inspect students.csv",
                "dependencies": [],
                "required_capabilities": [
                    "data_analysis"
                ]
            },
            {
                "id": "task_2",
                "description": "Prepare the student data for machine learning",
                "dependencies": [
                    "task_1"
                ],
                "required_capabilities": [
                    "data_preprocessing"
                ]
            },
            {
                "id": "task_3",
                "description": "Train a machine learning model",
                "dependencies": [
                    "task_2"
                ],
                "required_capabilities": [
                    "machine_learning"
                ]
            },
            {
                "id": "task_4",
                "description": "Evaluate the model and verify that accuracy reaches at least 80%",
                "dependencies": [
                    "task_3"
                ],
                "required_capabilities": [
                    "model_evaluation"
                ]
            }
        ]
    }
    """


class FakeModels:

    def generate_content(self, **kwargs):
        return FakeResponse()


class FakeClient:

    def __init__(self):
        self.models = FakeModels()


def test_planner():

    # ---------------------------------------------
    # CREATE STRUCTURED GOAL
    # ---------------------------------------------

    goal = StructuredGoal(
        objective=(
            "Build a Python machine learning system "
            "to predict student performance"
        ),
        domain="Machine Learning",
        inputs=[
            "students.csv"
        ],
        requirements=[
            "Python machine learning system"
        ],
        constraints=[
            "Model accuracy must be at least 80%."
        ],
        success_criteria=[
            "Model should achieve at least 80% accuracy"
        ],
        ambiguities=[]
    )

    # ---------------------------------------------
    # CREATE PLANNER
    # ---------------------------------------------

    planner = Planner(
        client=FakeClient()
    )

    # ---------------------------------------------
    # CREATE EXECUTION PLAN
    # ---------------------------------------------

    plan = planner.create_plan(goal)

    # ---------------------------------------------
    # ASSERTIONS
    # ---------------------------------------------

    assert plan is not None

    assert plan.objective

    assert plan.tasks

    assert len(plan.tasks) >= 1

    # ---------------------------------------------
    # VERIFY TASKS
    # ---------------------------------------------

    for task in plan.tasks:

        assert task.id

        assert task.description

        assert task.required_capabilities is not None

    # ---------------------------------------------
    # OUTPUT
    # ---------------------------------------------

    print("\n=== AEGIS PLANNER TEST PASSED ===")

    print(
        plan.model_dump_json(
            indent=2
        )
    )
