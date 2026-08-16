from backend.orchestrator.orchestrator import AEGISOrchestrator

from backend.models.schemas import (
    StructuredGoal,
    ExecutionPlan,
    PlanTask,
    VerificationResult,
)

from backend.runtime.runtime import RuntimeEngine


# ============================================================
# Fake Goal Analyzer
# ============================================================

class FakeGoalAnalyzer:

    def __init__(self):
        self.calls = 0

    def analyze(self, goal):

        self.calls += 1

        return StructuredGoal(
            objective=goal,
            domain="data_analysis",
            inputs=[
                "students.csv"
            ],
            requirements=[
                "Prepare the student data",
                "Analyze the prepared data",
            ],
            constraints=[],
            success_criteria=[
                "Produce verifiable analysis"
            ],
            ambiguities=[],
        )


# ============================================================
# Fake Planner
# ============================================================

class FakePlanner:

    def __init__(self):
        self.calls = 0

    def create_plan(self, goal, **kwargs):

        self.calls += 1

        return ExecutionPlan(
            objective=goal.objective,
            tasks=[
                PlanTask(
                    id="task_1",
                    description=(
                        "Prepare and analyze students.csv"
                    ),
                    dependencies=[],
                    required_capabilities=[
                        "data_analysis"
                    ],
                )
            ],
        )


# ============================================================
# Fake Agent Worker
# ============================================================

class FakeWorker:

    def __init__(self):

        self.name = "data_worker"

        self.capabilities = [
            "data_analysis"
        ]

    def execute(self, task):

        print(
            f"[FakeWorker] Executing {task.id}"
        )

        return {
            "status": "completed",
            "output": (
                "Student dataset prepared "
                "and analyzed successfully."
            ),
        }


# ============================================================
# Fake Agent Factory
# ============================================================

class FakeAgentFactory:

    def __init__(self):

        self.calls = 0

    def create_worker(
        self,
        task,
        excluded_workers=None,
    ):

        self.calls += 1

        return FakeWorker()


# ============================================================
# Fake Verifier
# ============================================================

class FakeVerifier:

    def __init__(self):

        self.calls = 0

    def verify(self, task, result):

        self.calls += 1

        return VerificationResult(
            passed=True,
            score=1.0,
            reasoning=(
                "The task produced a valid "
                "and verifiable result."
            ),
            issues=[],
        )


# ============================================================
# Test
# ============================================================

def test_orchestrator():

    print(
        "\n=== AEGIS ORCHESTRATOR TEST ==="
    )

    # --------------------------------------------------------
    # Create fake components
    # --------------------------------------------------------

    goal_analyzer = FakeGoalAnalyzer()

    planner = FakePlanner()

    agent_factory = FakeAgentFactory()

    verifier = FakeVerifier()

    # --------------------------------------------------------
    # Create orchestrator
    # --------------------------------------------------------

    orchestrator = AEGISOrchestrator(
        goal_analyzer=goal_analyzer,
        planner=planner,
        agent_factory=agent_factory,
        verifier=verifier,
    )

    # --------------------------------------------------------
    # Run complete workflow
    # --------------------------------------------------------

    result = orchestrator.run(
        """
        Build a Python system to analyze
        student performance using students.csv.
        """
    )

    # --------------------------------------------------------
    # Assertions
    # --------------------------------------------------------

    assert result is not None

    assert "goal" in result

    assert "plan" in result

    assert "results" in result

    # Goal Analyzer called once.
    assert goal_analyzer.calls == 1

    # Planner called once.
    assert planner.calls == 1

    # AgentFactory assigned one worker.
    assert agent_factory.calls == 1

    # Verifier checked one task.
    assert verifier.calls == 1

    # Task completed successfully.
    assert "task_1" in result["results"]

    assert (
        result["results"]["task_1"]
        ["verification"]["passed"]
        is True
    )

    print(
        "\n=== AEGIS ORCHESTRATOR TEST PASSED ==="
    )

    print(
        "\nFinal Result:"
    )

    print(result)


if __name__ == "__main__":
    test_orchestrator()
