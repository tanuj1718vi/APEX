"""
The "Run Recovery Demo" scenario described in the spec:

    Task 1: Check system state   -> SUCCESS
    Task 2: Analyze system       -> SUCCESS
    Task 3: Repair simulated svc -> INTENTIONAL FAILURE
    Task 4: Verify system health -> SUCCESS (after recovery)

The plan itself is deterministic and network-independent (built here
in Python, not by Gemini) so the demo is 100% reproducible on stage.
What is NOT faked is everything downstream of the plan: verification
(VerificationEngine, Gemini) and recovery reasoning (RecoveryEngine,
Gemini) genuinely inspect the real tool output and genuinely decide
what to do. `repair_service`'s first-call-fails/second-call-succeeds
behavior (see apex/backend/tools/simulated_tools.py) is what makes
"failure -> recovery -> verify -> success" a real event trail instead
of a scripted animation.
"""

from backend.models.schemas import StructuredGoal, ExecutionPlan, PlanTask


DEMO_GOAL_TEXT = "Run the system recovery demonstration."


def build_recovery_demo_goal() -> StructuredGoal:
    return StructuredGoal(
        objective=DEMO_GOAL_TEXT,
        domain="operations",
        inputs=[],
        requirements=[
            "Check current system state.",
            "Analyze the system before attempting repair.",
            "Repair the simulated service.",
            "Verify the service is healthy after repair.",
        ],
        constraints=[
            "Only registered, simulated tools may be used.",
            "No arbitrary code or shell execution.",
        ],
        success_criteria=[
            "The simulated service ends in a healthy state.",
            "Verification confirms expected state matches observed state.",
        ],
        ambiguities=[],
    )


def build_recovery_demo_plan() -> ExecutionPlan:
    return ExecutionPlan(
        objective=DEMO_GOAL_TEXT,
        tasks=[
            PlanTask(
                id="check_system_state",
                description="Check current system state.",
                dependencies=[],
                required_capabilities=["system_status"],
            ),
            PlanTask(
                id="analyze_system",
                description="Analyze the system before attempting repair.",
                dependencies=["check_system_state"],
                required_capabilities=["analyze_data"],
            ),
            PlanTask(
                id="repair_service",
                description="Repair the simulated service.",
                dependencies=["analyze_system"],
                required_capabilities=["repair_service"],
            ),
            PlanTask(
                id="verify_service_health",
                description="Verify the service is healthy after repair.",
                dependencies=["repair_service"],
                required_capabilities=["verify_system"],
            ),
        ],
    )
