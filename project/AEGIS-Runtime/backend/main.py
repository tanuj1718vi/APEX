from backend.agents.goal_analyzer import GoalAnalyzer
from backend.planner.planner import Planner
from backend.runtime.task_graph import TaskGraph
from backend.runtime.runtime import RuntimeEngine
from backend.agents.agent_factory import AgentFactory


def run_aegis(user_goal: str):

    print("\n=== AEGIS RUNTIME ===")
    print(f"\nUser Goal:\n{user_goal}")

    # --------------------------------------------------
    # 1. Analyze the goal
    # --------------------------------------------------

    analyzer = GoalAnalyzer()

    structured_goal = analyzer.analyze(user_goal)

    print("\n[1] Structured Goal")
    print(structured_goal.model_dump_json(indent=2))

    # --------------------------------------------------
    # 2. Create execution plan
    # --------------------------------------------------

    planner = Planner()

    execution_plan = planner.create_plan(
        structured_goal
    )

    print("\n[2] Execution Plan")
    print(
        execution_plan.model_dump_json(
            indent=2
        )
    )

    # --------------------------------------------------
    # 3. Build task graph
    # --------------------------------------------------

    graph = TaskGraph(execution_plan)

    print("\n[3] Task Graph")

    for task in graph.tasks.values():

        print(
            f"{task.id}: "
            f"{task.description} "
            f"[{task.status.value}]"
        )

    # --------------------------------------------------
    # 4. Create workers
    # --------------------------------------------------

    factory = AgentFactory()

    def generic_worker(task):

        print(
            f"\nExecuting: "
            f"{task.description}"
        )

        return {
            "task_id": task.id,
            "status": "completed",
            "description": task.description,
            "output": (
                f"Task '{task.description}' "
                f"was executed successfully."
            ),
        }

    # Register a generic capability
    # for MVP execution.

    factory.register_capability(
        "general",
        generic_worker,
    )

    # Give tasks without a capability
    # a generic capability.

    for task in graph.tasks.values():

        if not task.required_capabilities:

            task.required_capabilities = [
                "general"
            ]

    # --------------------------------------------------
    # 5. Runtime executor
    # --------------------------------------------------

    def execute_task(task):

        worker = factory.create_worker(task)

        print(
            f"Worker selected: "
            f"{worker.name}"
        )

        return worker.execute(task)

    # --------------------------------------------------
    # 6. Create Runtime Engine
    # --------------------------------------------------

    runtime = RuntimeEngine(
        graph=graph,
        executor=execute_task,
        planner=planner,
        goal=structured_goal,
    )

    # --------------------------------------------------
    # 7. Execute workflow
    # --------------------------------------------------

    results = runtime.run()

    # --------------------------------------------------
    # 8. Final Results
    # --------------------------------------------------

    print("\n[4] Final Results")

    for task_id, result in results.items():

        print(
            f"{task_id}: {result}"
        )

    print(
        "\n=== AEGIS EXECUTION COMPLETE ==="
    )

    return results


# ------------------------------------------------------
# Program Entry Point
# ------------------------------------------------------

if __name__ == "__main__":

    goal = input(
        "\nEnter your goal for AEGIS: "
    )

    run_aegis(goal)
