1. Architecture Overview

AEGIS Runtime is an adaptive AI execution platform designed to transform a high-level user goal into a dynamically generated, executable, verified, and recoverable workflow.

Unlike a fixed multi-agent pipeline, AEGIS treats the Runtime Engine and adaptive workflow as the central system.

The system follows this high-level lifecycle:
User Goal
    ↓
Goal Analyzer
    ↓
Planner
    ↓
Agent Factory
    ↓
Adaptive Task Graph
    ↓
Runtime Engine
    ↓
Tools + Memory
    ↓
Verification
    ↓
Recovery / Replanning
    ↓
Final Evaluation
    ↓
Experience Memory
2. Core Architecture Principle

The central design principle of AEGIS is:

The system should adapt its execution strategy according to the current state of the task.

Agents are not permanently fixed.

Instead, AEGIS determines:

What tasks are required
What capabilities are required
Which workers should be created
Which tasks can run in parallel
Which results require verification
When execution has failed
How the workflow should recover
What experience should be remembered

Therefore:

The innovation is adaptive execution, not simply multi-agent collaboration.

3. Main Components

AEGIS consists of the following major components:

3.1 Goal Analyzer

Converts the user's natural-language goal into a structured representation.

3.2 Planner

Determines what needs to be done and produces an initial execution strategy.

3.3 Agent Factory

Creates specialist workers based on the capabilities required by the current task.

3.4 Adaptive Task Graph

Represents tasks, dependencies, states, and execution relationships.

3.5 Runtime Engine

Controls and monitors execution of the workflow.

3.6 Tool Manager

Provides controlled access to tools such as Python execution, files, APIs, databases, and data analysis.

3.7 Memory System

Stores relevant execution state and previous experience.

3.8 Verification Engine

Independently checks important outputs and claims.

3.9 Recovery Engine

Detects failures and determines whether to retry, repair, replace a worker, or replan the workflow.

3.10 Final Evaluator

Determines whether the overall goal was successfully achieved.

3.11 Experience Memory

Stores useful information about previous executions so future workflows can use better strategies.
4. High-Level Data Flow
                    ┌─────────────────┐
                    │    USER GOAL    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  GOAL ANALYZER  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │     PLANNER     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  AGENT FACTORY  │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │  TASK GRAPH     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ RUNTIME ENGINE  │
                    └───────┬─┬───────┘
                            ↓ │
                ┌───────────┘ └───────────┐
                ↓                         ↓
        ┌───────────────┐         ┌───────────────┐
        │     TOOLS     │         │    MEMORY     │
        └───────┬───────┘         └───────┬───────┘
                │                         │
                └───────────┬─────────────┘
                            ↓
                    ┌─────────────────┐
                    │   VERIFICATION  │
                    └────────┬────────┘
                             ↓
                       ┌────────────┐
                       │   PASS?    │
                       └─────┬──────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                 YES                    NO
                  │                     │
                  ↓                     ↓
          ┌──────────────┐      ┌──────────────┐
          │ FINAL RESULT │      │   RECOVERY   │
          └──────┬───────┘      └──────┬───────┘
                 │                     │
                 ↓                     ↓
          ┌──────────────┐      REPLAN / RETRY
          │  EXPERIENCE  │             │
          │    MEMORY    │←────────────┘
          └──────────────┘
# 5. Goal Analyzer

## Purpose

The Goal Analyzer is the first intelligent component of AEGIS Runtime.

Its responsibility is to transform a natural-language user goal into a structured Goal Specification that can be understood by downstream components.

The Goal Analyzer does not determine the complete execution workflow. Workflow generation is handled by the Planner.

## Input

The Goal Analyzer receives:

- Natural-language user goal
- Optional files or datasets
- Optional constraints
- Optional user preferences

Example:

"Build a machine learning system that predicts customer churn."

## Output

The Goal Analyzer produces a structured Goal Specification containing:

- Objective
- Domain
- Expected outputs
- Required capabilities
- Constraints
- Success criteria

Example:

{
    "objective": "Build a customer churn prediction system",
    "domain": "machine_learning",
    "expected_outputs": [
        "trained model",
        "evaluation metrics",
        "prediction results",
        "report"
    ],
    "required_capabilities": [
        "data_analysis",
        "feature_engineering",
        "machine_learning",
        "model_evaluation",
        "report_generation"
    ],
    "constraints": [],
    "success_criteria": []
}

## Responsibilities

The Goal Analyzer should:

1. Understand the user's intent.
2. Identify the primary objective.
3. Identify the problem domain.
4. Determine expected outputs.
5. Identify required capabilities.
6. Extract constraints.
7. Identify explicit success criteria.
8. Detect ambiguity when the goal is unclear.

## Non-Responsibilities

The Goal Analyzer does not:

- Create the complete task graph.
- Execute tasks.
- Create workers.
- Select specific tools.
- Train models.
- Verify final results.

These responsibilities belong to downstream components.

## Key Principle

The Goal Analyzer answers:

"What does the user want?"

The Planner answers:

"How should AEGIS accomplish it?"
# 6. Planner

## Purpose

The Planner converts the structured Goal Specification produced by the Goal Analyzer into an executable strategy.

The Planner determines what tasks are required, how those tasks depend on each other, and what capabilities are required to execute them.

The Planner creates tasks rather than permanently assigning specific agents.

## Input

The Planner receives:

- Structured Goal Specification
- Available capabilities
- Available tools
- Relevant memory or previous experiences

## Output

The Planner produces an Execution Plan containing:

- Plan ID
- Tasks
- Task dependencies
- Required capabilities
- Expected outputs
- Success conditions

Example:

{
    "plan_id": "plan_001",
    "tasks": [
        {
            "id": "task_1",
            "name": "Inspect dataset",
            "depends_on": [],
            "required_capabilities": ["data_analysis"]
        },
        {
            "id": "task_2",
            "name": "Clean dataset",
            "depends_on": ["task_1"],
            "required_capabilities": ["data_cleaning"]
        },
        {
            "id": "task_3",
            "name": "Train ML model",
            "depends_on": ["task_2"],
            "required_capabilities": ["machine_learning"]
        },
        {
            "id": "task_4",
            "name": "Evaluate model",
            "depends_on": ["task_3"],
            "required_capabilities": ["model_evaluation"]
        }
    ]
}

## Responsibilities

The Planner should:

1. Analyze the structured goal.
2. Determine the required tasks.
3. Determine task dependencies.
4. Identify required capabilities.
5. Identify tasks that can run in parallel.
6. Define expected outputs.
7. Define task-level success conditions.
8. Use relevant previous experience when available.
9. Produce an executable plan.

## Adaptive Replanning

The Planner can be invoked again when execution results indicate that the current plan is insufficient.

Example:

Initial plan:

Dataset
↓
EDA
↓
Training
↓
Evaluation

If evaluation fails:

Evaluation
↓
Failure
↓
Planner
↓
Add Feature Engineering
↓
Retraining
↓
Evaluation

This allows AEGIS to modify its workflow instead of blindly restarting the entire process.

## Non-Responsibilities

The Planner does not:

- Execute tasks.
- Directly run tools.
- Permanently create agents.
- Verify final results.
- Repair execution errors itself.

These responsibilities belong to the Runtime Engine, Agent Factory, Verification Engine, and Recovery Engine.

## Key Principle

The Planner answers:

"What should be done, and in what dependency order?"

It does not answer:

"Who should execute it?"

Worker creation is handled by the Agent Factory.
# 7. Agent Factory

## Purpose

The Agent Factory dynamically creates or configures specialist workers based on the capabilities required by tasks in the execution plan.

Workers are created according to task requirements rather than maintaining a permanently fixed team of agents.

## Input

The Agent Factory receives:

- Task specification
- Required capabilities
- Available tools
- Worker templates or capabilities
- Relevant context

## Output

The Agent Factory produces a configured worker capable of executing the assigned task.

Example:

Task:
"Perform exploratory data analysis"

Required capability:
"data_analysis"

Generated worker:

- Role: Data Analysis Worker
- Tools: Python, Pandas, Matplotlib
- Expected output: EDA results

## Responsibilities

The Agent Factory should:

1. Identify the capabilities required by a task.
2. Match required capabilities with available worker capabilities.
3. Create or configure a suitable worker.
4. Provide the worker with required tools.
5. Provide relevant task context.
6. Assign the worker to the task.
7. Track the worker's execution state.

## Dynamic Worker Creation

AEGIS does not require a permanent fixed team of workers.

For example:

Goal:
"Build a customer churn prediction model."

The Planner may create tasks requiring:

- Data analysis
- Data cleaning
- Feature engineering
- Machine learning
- Model evaluation

The Agent Factory can create workers for these capabilities.

A different goal may require a completely different set of workers.

## Non-Responsibilities

The Agent Factory does not:

- Determine the overall project goal.
- Create the complete execution plan.
- Execute the workflow itself.
- Decide whether the final result is correct.
- Perform recovery.

These responsibilities belong to the Goal Analyzer, Planner, Runtime Engine, Verification Engine, and Recovery Engine.

## Key Principle

The Agent Factory answers:

"What type of worker is required for this task?"

It does not answer:

"What should the entire system do?"
# 8. Adaptive Task Graph

## Purpose

The Adaptive Task Graph represents the tasks, dependencies, states, and execution relationships of the current workflow.

It provides the Runtime Engine with a structured representation of what can be executed and what must wait.

## Task Representation

Each task should contain information such as:

- Task ID
- Description
- Required capabilities
- Dependencies
- Current state
- Input references
- Expected output
- Success criteria
- Retry information

## Task States

A task may move through states such as:

PENDING
↓
READY
↓
RUNNING
↓
COMPLETED

or:

RUNNING
↓
FAILED
↓
RECOVERY
↓
RETRY / REPLAN

## Dependencies

A task can depend on one or more previous tasks.

Example:

Load Dataset
↓
Clean Dataset
↓
Train Model

Training cannot begin until the required dataset preparation tasks are complete.

## Parallel Execution

Tasks without dependency relationships may execute in parallel when resources allow.

Example:

Clean Dataset
    ├──→ EDA
    └──→ Data Quality Analysis

Both tasks may execute independently before their results are combined.

## Adaptive Modification

The task graph can be modified during execution when new information becomes available.

Possible modifications include:

- Adding a task
- Removing an unnecessary task
- Replacing a failed task
- Changing dependencies
- Creating a recovery path
- Triggering replanning

## Key Principle

The Task Graph is not a static workflow diagram.

It is a live representation of the current execution state and can evolve during runtime.
# 9. Runtime Engine

## Purpose

The Runtime Engine is the central execution component of AEGIS Runtime.

It is responsible for executing the adaptive task graph, monitoring task execution, updating workflow state, handling execution events, and coordinating with tools, workers, memory, verification, and recovery components.

The Planner determines what should be done.

The Runtime Engine determines when and how the planned tasks are executed.

## Input

The Runtime Engine receives:

- Execution Plan
- Adaptive Task Graph
- Worker capabilities
- Available tools
- Relevant execution context

## Responsibilities

The Runtime Engine should:

1. Load the execution plan.
2. Validate the task graph.
3. Identify tasks that are ready for execution.
4. Assign suitable workers to tasks.
5. Execute tasks through controlled tools.
6. Monitor execution state.
7. Capture task outputs.
8. Record errors and execution events.
9. Update task states.
10. Trigger verification when required.
11. Communicate failures to the Recovery Engine.
12. Apply updated plans or graph changes.
13. Determine when the overall workflow is complete.

## Task Lifecycle

A task may move through the following lifecycle:

PENDING
↓
READY
↓
RUNNING
↓
COMPLETED

If execution fails:

RUNNING
↓
FAILED
↓
RECOVERY
↓
RETRY / REPLAN
↓
READY

## Execution State

The Runtime maintains execution state including:

- Execution ID
- Current workflow status
- Task states
- Active workers
- Task outputs
- Errors
- Execution timestamps
- Verification results
- Recovery events

Example:

{
    "execution_id": "exec_001",
    "status": "RUNNING",
    "tasks_completed": 3,
    "tasks_failed": 1,
    "active_tasks": 2
}

## Adaptive Execution

The Runtime Engine does not assume that the original workflow will always remain valid.

During execution, new information may require the workflow to change.

Examples include:

- A task failure
- Invalid tool output
- Missing data
- Verification failure
- Poor model performance
- New task requirements

When such events occur, the Runtime coordinates with the Recovery Engine and Planner to update the workflow.

## Parallel Execution

When multiple tasks have their dependencies satisfied and do not depend on each other, the Runtime may execute them concurrently when resources permit.

Example:

Task A
↓
Task B ──→
           Task D
Task C ──→

Tasks B and C can execute independently before Task D.

## Failure Handling

The Runtime Engine should not blindly retry every failure.

Instead:

Execution Failure
↓
Failure Classification
↓
Recovery Engine
↓
Retry / Repair / Replace / Replan
↓
Updated Task Graph
↓
Continue Execution

## Completion

The Runtime considers an execution complete when:

- All required tasks have completed successfully.
- Required outputs have been produced.
- Required verification has passed.
- No unresolved critical failures remain.

## Non-Responsibilities

The Runtime Engine does not:

- Determine the user's original goal.
- Design the initial workflow strategy.
- Permanently define worker roles.
- Independently approve unverified results.
- Decide long-term workflow improvements.

These responsibilities belong to the Goal Analyzer, Planner, Agent Factory, Verification Engine, and Experience/Optimization components.

## Key Principle

The Runtime Engine is the execution coordinator of AEGIS.

It transforms the planned workflow into observable, controlled, adaptive execution.
# 10. Tool Manager

## Purpose

The Tool Manager provides controlled access to the tools required by AEGIS workers.

Instead of allowing workers to directly access arbitrary system capabilities, the Tool Manager provides a centralized interface through which tools can be discovered, authorized, executed, and monitored.

## Tool Categories

Potential tool categories include:

- Python execution
- File operations
- Data analysis
- Database access
- External APIs
- Search
- Mathematical computation
- Other specialized capabilities

The initial MVP will implement only the tools required for the selected demonstration scenarios.

## Input

The Tool Manager receives tool requests from workers or the Runtime Engine.

A request may contain:

- Tool name
- Operation
- Input parameters
- Task ID
- Worker ID
- Execution context

## Output

The Tool Manager returns:

- Tool result
- Execution status
- Error information when applicable
- Execution metadata

Example:

{
    "tool": "python",
    "status": "SUCCESS",
    "result": "...",
    "task_id": "task_003"
}

## Responsibilities

The Tool Manager should:

1. Register available tools.
2. Maintain tool metadata.
3. Describe tool capabilities.
4. Validate tool requests.
5. Check whether a worker is allowed to use a requested tool.
6. Execute tools through controlled interfaces.
7. Capture tool outputs.
8. Capture tool errors.
9. Record tool usage.
10. Return results to the requesting worker or Runtime Engine.

## Capability-Based Access

Workers should receive only the capabilities required for their assigned tasks.

Example:

EDA Worker:

- Python
- File Reader
- Pandas/Data Analysis

Database Worker:

- Database Query
- Data Processing

This reduces unnecessary access and makes tool usage easier to monitor.

## Tool Execution Flow

Worker
↓
Tool Request
↓
Tool Manager
↓
Permission / Capability Check
↓
Tool Execution
↓
Result Capture
↓
Worker / Runtime

If the request is not permitted:

Worker
↓
Tool Request
↓
Tool Manager
↓
Permission Check
↓
Request Rejected
↓
Event Recorded

## Error Handling

Tool failures should not automatically terminate the entire workflow.

The Tool Manager should return structured error information to the Runtime Engine.

Example:

{
    "tool": "python",
    "status": "FAILED",
    "error": "ModuleNotFoundError",
    "task_id": "task_003"
}

The Runtime can then forward the failure to the Recovery Engine when appropriate.

## Tool Registry

AEGIS should maintain a registry describing available tools.

Example:

{
    "name": "python",
    "description": "Execute controlled Python operations",
    "capabilities": [
        "computation",
        "data_analysis"
    ]
}

The registry allows workers and the Planner to understand which capabilities are available.

## Non-Responsibilities

The Tool Manager does not:

- Decide the overall workflow.
- Determine task dependencies.
- Decide whether the final goal was achieved.
- Perform long-term memory management.
- Independently perform recovery.

These responsibilities belong to the Planner, Task Graph, Verification Engine, Memory System, and Recovery Engine.

## Key Principle

The Tool Manager acts as the controlled capability layer between AEGIS workers and external or computational resources.
# 11. Memory System

## Purpose

The Memory System provides AEGIS with access to information required during execution and useful knowledge from previous executions.

Memory is divided according to the lifetime and purpose of the information rather than being treated as a single storage mechanism.

## Memory Types

### 11.1 Working Memory

Working Memory stores information required during the current execution.

Examples include:

- Current goal
- Current plan
- Active tasks
- Active workers
- Intermediate results
- Current errors
- Current execution context

Working Memory answers:

"What is happening right now?"

### 11.2 Execution Memory

Execution Memory stores the history and state of a particular workflow execution.

Examples include:

- Execution ID
- Task execution history
- Tool calls
- Worker outputs
- Failures
- Retries
- Verification results
- Recovery events
- Execution timestamps

Execution Memory answers:

"What happened during this execution?"

### 11.3 Experience Memory

Experience Memory stores useful information extracted from completed or partially completed executions that may help future workflows.

Examples include:

- Successful strategies
- Failed strategies
- Recovery patterns
- Useful tool selections
- Task execution patterns
- Performance observations

Experience Memory answers:

"What can we learn from previous executions?"

## Memory Flow

Runtime
↓
Working Memory
↓
Execution Memory
↓
Execution Result
↓
Experience Extraction
↓
Experience Memory
↓
Future Planner

## Responsibilities

The Memory System should:

1. Store current execution context.
2. Store execution history.
3. Store relevant task results.
4. Store failures and recovery events.
5. Retrieve relevant previous experiences.
6. Provide context to the Planner and Runtime.
7. Preserve useful execution knowledge.
8. Avoid storing unnecessary information.

## Memory Retrieval

Memory should be retrieved based on relevance to the current task.

Example:

Current goal:

"Build a customer churn prediction system."

Relevant previous experience:

"Class imbalance was handled successfully using class-weighted models."

Irrelevant experiences should not be injected into the current workflow.

## Experience Feedback Loop

AEGIS can use previous execution experience to improve future planning.

Example:

Previous execution
↓
Successful strategy identified
↓
Stored in Experience Memory
↓
New similar goal
↓
Planner retrieves relevant experience
↓
Planner considers previous strategy
↓
New execution

## Memory and Decision Making

Memory provides context but does not independently determine actions.

The Planner, Runtime Engine, Verification Engine, and Recovery Engine remain responsible for decisions.

## Non-Responsibilities

The Memory System does not:

- Create execution plans.
- Execute tasks.
- Create workers.
- Independently verify results.
- Independently perform recovery.

## Key Principle

Memory allows AEGIS to maintain execution context and learn from previous experiences without turning memory itself into the decision-making component.
# 12. Verification Engine

## Purpose

The Verification Engine independently evaluates task outputs and determines whether they satisfy the expected requirements and success criteria.

AEGIS does not assume that successful execution automatically means a correct result.

## Input

The Verification Engine receives:

- Task specification
- Expected output
- Actual output
- Success criteria
- Relevant execution context
- Relevant previous results when required

## Verification Levels

### 12.1 Structural Verification

Checks whether the output has the expected structure or type.

Examples:

- Expected JSON but received invalid data.
- Expected file but no file was produced.
- Expected numeric result but received text.

### 12.2 Task Verification

Checks whether the output satisfies the task requirements.

Example:

Task:
"Calculate average sales."

The verifier checks whether a valid average was actually calculated.

### 12.3 Quality Verification

Checks whether the result satisfies defined quality criteria.

Example:

Required F1 score:
> 0.75

Actual F1 score:
> 0.61

Result:
VERIFICATION FAILED

### 12.4 Consistency Verification

Checks whether the result is consistent with relevant inputs, previous results, or other constraints.

## Verification Result

The Verification Engine produces a structured result.

Example:

{
    "task_id": "task_004",
    "status": "FAILED",
    "checks": {
        "structure": "PASS",
        "task_requirement": "PASS",
        "quality": "FAIL",
        "consistency": "PASS"
    },
    "reason": "F1 score is below the required threshold."
}

## Responsibilities

The Verification Engine should:

1. Receive task outputs.
2. Compare outputs against expected requirements.
3. Validate output structure.
4. Evaluate task-level success criteria.
5. Perform quality checks when applicable.
6. Perform consistency checks when required.
7. Produce a structured verification result.
8. Report failures to the Runtime Engine.
9. Provide useful failure information to the Recovery Engine.

## Verification Flow

Worker
↓
Task Output
↓
Verification Engine
↓
Structural Check
↓
Task Check
↓
Quality Check
↓
Consistency Check
↓
Verification Result
↓
PASS / FAIL

## Failure Handling

The Verification Engine does not perform recovery itself.

If verification fails:

Verification Engine
↓
Failure Report
↓
Runtime Engine
↓
Recovery Engine

## Non-Responsibilities

The Verification Engine does not:

- Create execution plans.
- Execute tasks.
- Create workers.
- Directly repair failed tasks.
- Modify the workflow independently.

These responsibilities belong to the Planner, Runtime Engine, Agent Factory, and Recovery Engine.

## Key Principle

Execution success and result correctness are separate concepts.

A task can execute successfully while still producing an incorrect or unacceptable result.
# 13. Recovery Engine

## Purpose

The Recovery Engine enables AEGIS to respond to execution and verification failures without unnecessarily terminating the entire workflow.

It determines an appropriate recovery strategy based on the type and severity of the failure.

## Input

The Recovery Engine receives:

- Failed task
- Failure information
- Error details
- Verification results
- Execution history
- Current task graph
- Relevant memory

## Recovery Strategies

### 13.1 Retry

Retries the failed task using the same strategy.

Useful for temporary or transient failures.

Example:

Task
↓
Temporary failure
↓
Retry
↓
Success

### 13.2 Repair

Attempts to correct a known problem before retrying.

Example:

Missing parameter
↓
Repair configuration
↓
Retry task

### 13.3 Replace

Replaces the current worker, tool, or execution approach.

Example:

Worker A
↓
Failure
↓
Worker B
↓
Retry

### 13.4 Replan

Requests a new execution strategy from the Planner when the current approach is no longer suitable.

Example:

Current strategy
↓
Repeated failure
↓
Planner
↓
New strategy
↓
Updated Task Graph

## Failure Classification

The Recovery Engine should classify failures before selecting a recovery strategy.

Potential categories include:

- Transient execution failure
- Tool failure
- Invalid input
- Worker failure
- Verification failure
- Resource failure
- Strategy failure

## Recovery Decision Flow

Failure
↓
Classify Failure
↓
Evaluate Recovery Options
↓
Retry / Repair / Replace / Replan
↓
Update Task Graph
↓
Resume Execution

## Recovery Limits

Recovery should not continue indefinitely.

The system should maintain limits such as:

- Maximum retries
- Maximum recovery attempts
- Maximum replanning attempts
- Failure history

If recovery limits are exceeded, the workflow should be marked as failed and provide a structured failure explanation.

## Responsibilities

The Recovery Engine should:

1. Receive failure information.
2. Classify the failure.
3. Determine an appropriate recovery strategy.
4. Coordinate with the Runtime Engine.
5. Request replanning when necessary.
6. Update recovery state.
7. Record recovery events.
8. Prevent infinite retry loops.
9. Return the workflow to execution when recovery succeeds.

## Non-Responsibilities

The Recovery Engine does not:

- Define the original user goal.
- Independently create the initial execution plan.
- Execute arbitrary tasks.
- Independently approve final results.

These responsibilities belong to the Goal Analyzer, Planner, Runtime Engine, and Verification Engine.

## Key Principle

Failure is treated as an execution state that can trigger adaptation rather than automatically terminating the entire workflow.
# 14. Final Evaluator

## Purpose

The Final Evaluator determines whether the complete execution successfully achieved the original user goal.

While the Verification Engine evaluates individual task outputs, the Final Evaluator evaluates the overall outcome of the workflow.

## Input

The Final Evaluator receives:

- Original Goal Specification
- Execution results
- Verified task outputs
- Success criteria
- Execution status
- Relevant workflow context

## Responsibilities

The Final Evaluator should:

1. Compare the final outcome with the original goal.
2. Check whether required outputs were produced.
3. Check whether required success criteria were satisfied.
4. Consider verification results.
5. Identify unresolved failures.
6. Determine overall execution status.
7. Produce a structured final evaluation.

## Evaluation Result

Example:

{
    "execution_id": "exec_001",
    "status": "SUCCESS",
    "goal_achieved": true,
    "criteria_met": true,
    "unresolved_failures": [],
    "summary": "The requested churn prediction system was successfully produced and verified."
}

Possible overall statuses include:

- SUCCESS
- PARTIAL_SUCCESS
- FAILED

## Final Evaluation Flow

Completed Workflow
↓
Collect Verified Results
↓
Compare With Goal
↓
Evaluate Success Criteria
↓
Check Unresolved Failures
↓
Final Evaluation
↓
SUCCESS / PARTIAL_SUCCESS / FAILED

## Non-Responsibilities

The Final Evaluator does not:

- Create the execution plan.
- Execute tasks.
- Create workers.
- Perform task-level recovery.
- Modify the workflow directly.

These responsibilities belong to the Planner, Runtime Engine, Agent Factory, Verification Engine, and Recovery Engine.

## Key Principle

Task-level correctness does not automatically guarantee goal-level success.

The Final Evaluator determines whether the complete workflow accomplished what the user requested.
# 15. Experience Memory

## Purpose

Experience Memory stores reusable knowledge extracted from previous executions.

It allows AEGIS to use relevant past execution experiences when planning or adapting future workflows.

Experience Memory is a specialized component of the broader Memory System.

## Experience Representation

An experience may contain:

- Experience ID
- Goal or task category
- Context
- Strategy used
- Tools used
- Outcome
- Failures encountered
- Recovery actions
- Successful actions
- Performance observations

Example:

{
    "experience_id": "exp_001",
    "task_type": "customer_churn_prediction",
    "context": "imbalanced classification dataset",
    "strategy": [
        "feature_engineering",
        "class_weighting",
        "random_forest"
    ],
    "outcome": "SUCCESS",
    "performance": {
        "f1_score": 0.79
    }
}

## Experience Creation

Experience can be extracted after an execution completes.

Execution
↓
Results
↓
Verification
↓
Final Evaluation
↓
Experience Extraction
↓
Experience Memory

## Experience Retrieval

When a new goal is received:

New Goal
↓
Goal Analyzer
↓
Planner
↓
Retrieve Relevant Experience
↓
Consider Previous Strategies
↓
Create Execution Plan

Only experiences relevant to the current goal should be retrieved.

## Types of Experience

Experience Memory may store:

### Successful Experiences

Strategies that produced acceptable results.

### Failed Experiences

Strategies that failed and should potentially be avoided.

### Recovery Experiences

Useful patterns for recovering from particular failures.

### Tool Experiences

Information about which tools were effective for specific tasks.

## Experience and Adaptation

Experience Memory does not directly control execution.

Instead, it provides evidence that the Planner and Recovery Engine can consider.

For example:

Previous experience:
"Strategy A failed repeatedly for similar data."

The Planner may choose an alternative strategy.

## Non-Responsibilities

Experience Memory does not:

- Create plans.
- Execute tasks.
- Create workers.
- Independently determine actions.
- Replace the Planner or Runtime Engine.

## Key Principle

Experience Memory transforms previous execution history into reusable knowledge that can improve future planning and recovery.