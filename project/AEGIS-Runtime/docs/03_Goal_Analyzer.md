# Goal Analyzer

## 1. Purpose

The Goal Analyzer is the entry point for converting a user's natural-language goal into a structured representation that can be processed by the AEGIS Planner.

Users may express goals in ambiguous or high-level language. The Goal Analyzer identifies the important aspects of the request and transforms them into structured information.

Example:

User Goal:

"Build a machine learning model to predict customer churn."

The Goal Analyzer produces a structured goal that can be passed to the Planner.

The Goal Analyzer acts as the boundary between natural-language user intent and the structured execution system.

## Core Principle

The Goal Analyzer should answer:

"What does the user want to accomplish?"

It should not determine the complete execution strategy.

The Planner is responsible for deciding how the goal should be accomplished.

## Processing Flow

Natural-Language Goal
↓
Goal Analyzer
↓
Structured Goal
↓
Planner
## 2. Input

The Goal Analyzer receives a natural-language user goal as its primary input.

Additional context and constraints may optionally be provided to improve goal understanding.

### 2.1 Required Input

#### User Goal

The user goal is the natural-language description of what the user wants to accomplish.

Example:

"Build a system that analyzes student performance and predicts whether a student is at risk of failing."

The Goal Analyzer should process the goal without requiring the user to express it in a predefined format.

### 2.2 Optional Input

#### Context

Additional information that may help interpret the goal.

Examples:

- Project context
- Available files
- Existing system information
- Previous execution context
- Relevant domain information

Example:

Project:
Customer analytics

Available data:
customers.csv

#### Constraints

Restrictions or requirements explicitly provided by the user.

Examples:

- Required programming language
- Available tools
- Budget limitations
- Time limitations
- Technology requirements
- Output format requirements

Example:

"Use Python and do not use paid APIs."

### 2.3 Input Representation

The internal input to the Goal Analyzer may be represented as:

{
    "goal": "Build a customer churn prediction system",
    "context": {},
    "constraints": []
}

The Goal Analyzer should treat the user goal as the primary source of intent while using optional context and constraints to improve interpretation.

### 2.4 Input Principle

The Goal Analyzer should accept natural-language requests rather than requiring users to understand the internal AEGIS architecture.

Users describe what they want.

AEGIS determines how that goal should later be represented and executed.
## 3. Output

The Goal Analyzer produces a structured representation of the user's goal that can be consumed by the Planner.

The output should contain the user's intended objective, relevant inputs, requirements, constraints, and measurable success criteria when they are available.

### 3.1 Structured Goal

The initial AEGIS structured goal contains:

- Objective
- Domain
- Inputs
- Requirements
- Constraints
- Success criteria
- Ambiguities

Example:

User Goal:

"Build a machine learning system that predicts customer churn using our customer data. It should achieve at least 80% accuracy."

Structured Goal:

{
    "objective": "Build a customer churn prediction system",
    "domain": "machine_learning",
    "inputs": [
        "customer data"
    ],
    "requirements": [
        "predict customer churn",
        "achieve at least 80% accuracy"
    ],
    "constraints": [],
    "success_criteria": [
        "accuracy >= 0.80"
    ]
}

### 3.2 Output Requirements

The output should:

1. Preserve the user's intended objective.
2. Extract important requirements.
3. Identify relevant inputs when provided.
4. Extract explicit constraints.
5. Identify measurable success criteria when available.
6. Avoid inventing requirements that the user did not provide.
7. Avoid creating execution tasks or implementation strategies.

### 3.3 Output Contract

The Structured Goal acts as the interface between the Goal Analyzer and the Planner.

Natural-Language Goal
↓
Goal Analyzer
↓
Structured Goal
↓
Planner

The Planner should be able to consume the Structured Goal without needing to interpret the original user request again.

### 3.4 Handling Missing Information

Not every user goal will contain all possible fields.

For example:

{
    "objective": "Analyze customer sales data",
    "domain": "data_analysis",
    "inputs": [],
    "requirements": [],
    "constraints": [],
    "success_criteria": []
    "ambiguities": []
}

Missing information should not be fabricated.

If important information is missing and cannot be safely inferred, the Goal Analyzer may mark it as unknown or allow the Planner to determine whether clarification is required.
## 4. Responsibilities

The Goal Analyzer is responsible for understanding and structuring user intent before execution planning begins.

### 4.1 Core Responsibilities

The Goal Analyzer should:

1. Interpret the user's natural-language objective.
2. Identify the primary objective the user wants to accomplish.
3. Extract explicit requirements from the request.
4. Identify inputs mentioned by the user.
5. Identify explicit constraints.
6. Identify measurable or explicit success criteria.
7. Determine the general domain when it can be reasonably inferred.
8. Detect ambiguity or missing critical information.
9. Produce a structured goal representation.
10. Pass the structured goal to the Planner.

### 4.2 Ambiguity Detection

The Goal Analyzer should identify cases where the user's request is unclear or contains insufficient information.

Example:

User:

"Build a prediction system."

Possible issue:

The requested prediction target is not specified.

The Goal Analyzer should represent the missing information rather than inventing an objective.

The Planner or user-interaction layer may later determine whether clarification is required.

### 4.3 Requirement Extraction

The Goal Analyzer should distinguish explicit user requirements from inferred implementation details.

Example:

User:

"Build a churn prediction model with at least 80% accuracy."

Extracted requirements:

- Build a churn prediction model.
- Achieve at least 80% accuracy.

The Goal Analyzer should not automatically add:

- Random Forest
- Logistic Regression
- Feature engineering
- Specific libraries

unless the user explicitly requests them.

### 4.4 Domain Identification

The Goal Analyzer may identify a general domain when the request provides sufficient evidence.

Examples:

- Machine Learning
- Data Analysis
- Software Development
- Data Engineering
- Automation

Domain identification should support planning but should not determine the implementation strategy.

### 4.5 Structured Output Generation

After analyzing the request, the Goal Analyzer produces the Structured Goal defined in Section 3.

Natural-Language Goal
↓
Interpretation
↓
Requirement Extraction
↓
Constraint Extraction
↓
Success Criteria Extraction
↓
Ambiguity Detection
↓
Structured Goal
↓
Planner

### 4.6 Principle

The Goal Analyzer is responsible for answering:

"What does the user want?"

It is not responsible for answering:

"How should AEGIS accomplish it?"

The second question belongs to the Planner.
## 5. Goal Representation

The Goal Analyzer represents user intent using a Structured Goal.

The Structured Goal provides a stable interface between the Goal Analyzer and the Planner.

### 5.1 Structured Goal Schema

The initial AEGIS Structured Goal contains the following fields:

| Field | Description |
|---|---|
| `objective` | The primary outcome the user wants to achieve |
| `domain` | The general domain of the requested task |
| `inputs` | Relevant inputs explicitly mentioned by the user |
| `requirements` | Explicit requirements that the result should satisfy |
| `constraints` | Restrictions or limitations specified by the user |
| | `success_criteria` | Conditions that can be used to determine whether the goal was achieved |
| `ambiguities` | Important missing, unclear, or contradictory information detected during goal analysis |

### 5.2 Example

User Goal:

"Build a machine learning system that predicts customer churn using our customer data. It should achieve at least 80% accuracy."

Structured Goal:

{
    "objective": "Build a customer churn prediction system",
    "domain": "machine_learning",
    "inputs": [
        "customer data"
    ],
    "requirements": [
        "predict customer churn"
    ],
    "constraints": [],
    "success_criteria": [
        "accuracy >= 0.80"
    ]
}

### 5.3 Field Principles

#### Objective

Represents the primary outcome requested by the user.

It should describe what the user wants to accomplish without prescribing an implementation strategy.

#### Domain

Represents the broad area associated with the goal.

Examples:

- machine_learning
- data_analysis
- software_development
- automation
- data_engineering

The domain should only be specified when it can be reasonably inferred from the user's request.

#### Inputs

Contains relevant data, files, resources, or information explicitly mentioned by the user.

The Goal Analyzer should not invent inputs that were not provided.

#### Requirements

Contains explicit conditions or capabilities requested by the user.

Implementation details should not be added unless explicitly requested.

#### Constraints

Contains restrictions imposed by the user.

Examples:

- Required technology
- Budget limitations
- Time limitations
- Tool restrictions
- Output format requirements

#### Success Criteria

Contains explicit or measurable conditions that determine whether the goal has been achieved.

If the user does not provide measurable success criteria, the field may remain empty.
#### Ambiguities

Contains important information that is unclear, missing, or contradictory in the user's request.

Example:

User:

"Build a prediction system."

Ambiguity:

"Prediction target is not specified."

The Goal Analyzer should record important ambiguities rather than silently inventing missing information.

### 5.4 Representation Principles

The Structured Goal should:

1. Preserve the user's intent.
2. Use predictable fields.
3. Avoid unnecessary implementation details.
4. Avoid inventing missing information.
5. Be easy for the Planner to consume.
6. Remain independent from execution-specific details.

### 5.5 Future Implementation

The Structured Goal is expected to become a typed data model during implementation.

A future implementation may use a validation framework such as Pydantic to ensure that Goal Analyzer outputs follow the expected schema.

The exact implementation is intentionally deferred until the design phase is complete.
## 6. Processing Flow

The Goal Analyzer converts a natural-language user request into a validated Structured Goal through a sequence of interpretation and extraction steps.

### 6.1 High-Level Flow

User Goal
↓
Receive Input
↓
Understand Intent
↓
Extract Requirements
↓
Identify Inputs
↓
Identify Constraints
↓
Identify Success Criteria
↓
Detect Ambiguity
↓
Build Structured Goal
↓
Validate Structured Goal
↓
Send to Planner

### 6.2 Step 1 — Receive User Goal

The Goal Analyzer receives the user's natural-language request together with any available optional context.

Example:

"Build a Python system that predicts student performance using students.csv. The model should achieve at least 80% accuracy."

### 6.3 Step 2 — Understand Intent

The analyzer identifies the primary objective expressed by the user.

Example:

"Build a Python system that predicts student performance."

The resulting objective should describe the intended outcome without introducing an execution strategy.

### 6.4 Step 3 — Extract Requirements

The analyzer identifies explicit requirements contained in the request.

Example:

"Predict student performance."

The analyzer should preserve explicit requirements while avoiding unsupported assumptions.

### 6.5 Step 4 — Identify Inputs

The analyzer identifies data, files, resources, or other inputs explicitly mentioned by the user.

Example:

"students.csv"

### 6.6 Step 5 — Identify Constraints

The analyzer identifies restrictions or requirements that limit how the goal may be achieved.

Example:

"Use Python."

This becomes a constraint in the Structured Goal.

### 6.7 Step 6 — Identify Success Criteria

The analyzer extracts explicit measurable or qualitative conditions that define success.

Example:

"The model should achieve at least 80% accuracy."

This becomes:

"accuracy >= 0.80"

### 6.8 Step 7 — Detect Ambiguity

The analyzer checks whether important information is missing, contradictory, or unclear.

Example:

"Build a prediction system."

If the prediction target is not specified, the analyzer should not invent one.

The ambiguity should be represented so that the Planner or user-interaction layer can determine whether clarification is required.

### 6.9 Step 8 — Build Structured Goal

The extracted information is combined into the Structured Goal defined in Section 5.

Example:

{
    "objective": "Build a student performance prediction system",
    "domain": "machine_learning",
    "inputs": [
        "students.csv"
    ],
    "requirements": [
        "predict student performance"
    ],
    "constraints": [
        "use Python"
    ],
    "success_criteria": [
        "accuracy >= 0.80"
    ]
}

### 6.10 Step 9 — Validate Structured Goal

Before passing the result to the Planner, the Goal Analyzer should verify that the generated structure follows the expected schema.

Validation should check:

- Required fields are present.
- Field types are valid.
- No unexpected execution instructions have been introduced.
- User requirements have not been silently changed.
- Missing information is represented appropriately.

### 6.11 Step 10 — Send to Planner

After validation, the Structured Goal is passed to the Planner.

The Planner then determines the execution strategy.

The final boundary is:

Natural-Language Goal
↓
Goal Analyzer
↓
Validated Structured Goal
↓
Planner
## 7. Success Criteria

Success criteria describe the conditions that can be used to determine whether the user's goal has been achieved.

The Goal Analyzer extracts success criteria explicitly provided by the user and represents them in the Structured Goal.

### 7.1 Explicit Success Criteria

When the user provides a measurable or clearly defined success condition, the Goal Analyzer should extract it.

Example:

User:

"Build a churn prediction model with at least 80% accuracy."

Structured Goal:

"success_criteria": [
    "accuracy >= 0.80"
]

### 7.2 Qualitative Success Criteria

Success criteria do not always have to be numerical.

Example:

User:

"Create a report that contains the key findings from the dataset."

Possible success criterion:

"report contains key findings"

The Goal Analyzer should preserve the meaning of the user's requirement rather than unnecessarily converting it into an arbitrary numerical target.

### 7.3 Missing Success Criteria

If the user does not explicitly provide a success criterion, the Goal Analyzer should not invent one.

Example:

User:

"Analyze this sales dataset."

Structured Goal:

"success_criteria": []

The absence of an explicit success criterion should be represented honestly.

The Planner or later evaluation stage may determine whether additional criteria are necessary for successful execution.

### 7.4 Success Criteria and Planning

The Goal Analyzer extracts what the user considers successful.

It does not determine the complete method for achieving those criteria.

Example:

User:

"Achieve at least 80% accuracy."

Goal Analyzer:

"accuracy >= 0.80"

Planner:

Determines which tasks, models, experiments, and evaluation steps should be used to attempt to achieve the target.

### 7.5 Success Criteria and Final Evaluation

Success criteria are eventually used by the Final Evaluator to determine whether the overall goal was achieved.

The flow is:

User Goal
↓
Goal Analyzer
↓
Success Criteria
↓
Planner
↓
Execution
↓
Verification
↓
Final Evaluator
↓
Evaluate Success Criteria

### 7.6 Principle

The Goal Analyzer should preserve user-defined success conditions without inventing unsupported targets.

Explicit criteria should be extracted.

Missing criteria should remain unspecified until a later component determines whether clarification or additional evaluation criteria are required.
## 8. Constraints

Constraints represent restrictions, limitations, or specific conditions that the user wants AEGIS to respect while accomplishing the goal.

The Goal Analyzer extracts constraints explicitly stated by the user and includes them in the Structured Goal.

### 8.1 Types of Constraints

Constraints may include:

- Technology requirements
- Tool restrictions
- Budget limitations
- Time limitations
- Resource limitations
- Output format requirements
- Environment requirements
- Platform requirements

### 8.2 Examples

User:

"Build the application using Python."

Constraint:

"use Python"

User:

"Do not use paid APIs."

Constraint:

"do not use paid APIs"

User:

"Create the final report as a PDF."

Constraint:

"output format: PDF"

### 8.3 Explicit Constraints

The Goal Analyzer should extract constraints that are directly stated by the user.

Example:

"Build a data analysis system using Python and Pandas."

Structured Goal:

{
    "constraints": [
        "use Python",
        "use Pandas"
    ]
}

### 8.4 Missing Constraints

If the user does not specify any constraints, the constraints field should remain empty.

Example:

{
    "constraints": []
}

The Goal Analyzer should not invent restrictions that the user did not provide.

### 8.5 Constraint Interpretation

The Goal Analyzer identifies and represents constraints but does not determine whether they are technically feasible.

For example:

User:

"Build the entire system in one minute."

The Goal Analyzer should record the time constraint.

It should not decide whether the request is feasible.

Feasibility and execution planning belong to later components.

### 8.6 Constraints and Planning

The Planner uses the constraints provided by the Goal Analyzer when developing the execution strategy.

The relationship is:

User
↓
Explicit Constraints
↓
Goal Analyzer
↓
Structured Goal
↓
Planner
↓
Constraint-aware Execution Plan

### 8.7 Constraint Preservation

Constraints should be preserved accurately.

The Goal Analyzer should:

1. Extract explicit constraints.
2. Preserve their intended meaning.
3. Avoid weakening or changing them.
4. Avoid inventing additional restrictions.
5. Pass them to the Planner.

### 8.8 Principle

The Goal Analyzer answers:

"What restrictions did the user specify?"

The Planner answers:

"How can the goal be achieved while respecting those restrictions?"
## 9. Non-Responsibilities

The Goal Analyzer is intentionally limited to understanding and structuring user intent.

It should not perform responsibilities that belong to downstream AEGIS components.

### 9.1 Planning

The Goal Analyzer does not create the execution plan.

It should not determine:

- Which tasks must be performed.
- The order of execution.
- Task dependencies.
- Parallel execution opportunities.
- Execution strategies.

These responsibilities belong to the Planner and Adaptive Task Graph.

### 9.2 Agent Selection

The Goal Analyzer does not select or create agents or workers.

It should not determine:

- Which worker should perform a task.
- Which capabilities are required for execution.
- Which specialist should be created.

These responsibilities belong to the Agent Factory and Planner.

### 9.3 Tool Execution

The Goal Analyzer does not execute tools.

It should not:

- Run Python code.
- Access external APIs.
- Modify files.
- Query databases.
- Execute shell commands.
- Perform data analysis.

These responsibilities belong to the Runtime Engine, Workers, and Tool Manager.

### 9.4 Task Execution

The Goal Analyzer does not execute tasks or control workflow execution.

The Runtime Engine is responsible for executing the workflow represented by the Adaptive Task Graph.

### 9.5 Verification

The Goal Analyzer does not determine whether an executed task produced a correct result.

Task-level verification belongs to the Verification Engine.

### 9.6 Recovery

The Goal Analyzer does not determine how execution failures should be handled.

Retry, repair, replacement, and replanning decisions belong to the Recovery Engine.

### 9.7 Final Evaluation

The Goal Analyzer does not determine whether the complete user goal was successfully achieved.

Overall goal evaluation belongs to the Final Evaluator.

### 9.8 Experience Storage

The Goal Analyzer does not manage long-term execution experience.

Reusable execution experiences are handled by the Memory System and Experience Memory.

### 9.9 Implementation Strategy

The Goal Analyzer should not unnecessarily prescribe implementation technologies or methods.

For example, if the user requests:

"Build a customer churn prediction system."

The Goal Analyzer should not automatically decide:

- Use Random Forest.
- Use XGBoost.
- Use pandas.
- Use scikit-learn.
- Deploy with FastAPI.

These decisions belong to the Planner and later execution components.

### 9.10 Core Boundary

The Goal Analyzer answers:

"What does the user want?"

The Planner answers:

"How should the goal be accomplished?"

The Runtime Engine answers:

"How should the planned workflow be executed?"

The Verification Engine answers:

"Is the task result correct?"

The Recovery Engine answers:

"What should happen when execution fails?"

The Final Evaluator answers:

"Was the overall goal achieved?"

This separation keeps the AEGIS architecture modular, testable, and easier to evolve.
