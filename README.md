## Task 1 — Implement the Reflection Contract

### Objective

This task implements the basic reflection contract used in the Reflect, Refine, Repeat workflow.

The implementation converts a structured failed run into a traceable lesson while ensuring that successful runs or failures without a valid cause do not create lessons.

### Files

- `models.py` — Defines the `RunOutcome` and `Lesson` data structures.
- `reflection.py` — Implements the reflection logic and saves the reflection event.
- `tests/test_reflection.py` — Contains automated tests for the reflection behavior.
- `outputs/reflection_event.json` — Stores the generated reflection event.
- `outputs/reflection.txt` — Stores the main execution output.
- `outputs/test_reflection.txt` — Stores the pytest results.

### Implementation

`RunOutcome` represents the result of an execution and contains:

- run ID
- task
- status
- output
- failure cause
- supporting evidence

`Lesson` represents the learning extracted from a failed run and contains:

- deterministic lesson ID
- failure condition
- refinement
- source evidence
- source run
- confidence
- lesson status

The `reflect()` function only creates a lesson when:

1. The run status is `failure`.
2. A non-empty failure cause is available.

A successful run returns `None`, and a failure without a cause is rejected.

A SHA256 hash of the normalized condition and refinement is used to generate a deterministic lesson ID. This ensures that the same type of failure produces the same lesson identity.

The lesson also preserves the source run and execution evidence so that its origin can be traced.

### Run the Implementation

```bash
python reflection.py
```

### Run Automated Tests

```bash
pytest tests/test_reflection.py -v
```

### Automated Tests

The tests verify:

- A failed run creates a lesson.
- A successful run does not create a lesson.
- A failed run without a cause is rejected.
- The same failure condition generates the same deterministic lesson ID.

### Evidence

Running the implementation creates:

```text
outputs/reflection_event.json
```

The reflection event records:

- run ID
- failure cause
- supporting evidence
- lesson confidence
- generated lesson

This provides traceable evidence showing how the lesson was created from the original failed run.

### Guardrails

- **Validation:** Reflection only accepts failed outcomes with a non-empty cause.
- **Provenance:** Every generated lesson preserves the source run ID and supporting evidence.
- **Feedback-loop prevention:** The generated lesson is treated as derived feedback and not as independent execution evidence.
- **Secret hygiene:** No credentials or sensitive configuration values are stored in the lesson or reflection trace.

Timeout, retry, and step-limit controls are not required in this deterministic reflection function and are implemented later in the bounded repeat/execution stage where they are operationally relevant.

---

## Task 2 — Implement Lesson Validation and Provenance

### Objective

This task validates reflected lessons before they are allowed to move further into the reflective-memory workflow.

The validation checks that each lesson contains the required information and remains traceable to the run and evidence that produced it.

### Files

- `validation.py` — Implements lesson validation and saves validation traces.
- `tests/test_validation.py` — Contains automated tests for validation and provenance checks.
- `outputs/validation_trace.json` — Stores the latest validation decision and reason.
- `outputs/validation.txt` — Stores the main execution output.
- `outputs/test_validation.txt` — Stores the pytest results.

### Implementation

The `validate()` function checks the following fields:

- condition
- refinement
- source run
- evidence
- confidence

A lesson is rejected when any required field is missing.

Confidence must remain within the valid range:

```text
0.0 <= confidence <= 1.0
```

This task only validates the confidence value itself. The minimum confidence required to store a lesson is handled later by the memory-write policy.

### Provenance

Each lesson must contain a `source_run` and supporting `evidence`.

This allows the lesson to be traced back to the execution that produced it.

A generated lesson is not treated as independent proof of itself. The lesson is derived feedback, while the evidence must come from the original execution, validator, tool, or another independent source.

### Validation Trace

Every validation decision creates:

```text
outputs/validation_trace.json
```


### Run the Implementation

```bash
python validation.py
```

### Run Automated Tests

```bash
pytest tests/test_validation.py -v
```

The tests verify:

- a complete valid lesson is accepted
- an incomplete lesson is rejected
- confidence outside the 0–1 range is rejected
- a lesson without evidence is rejected
- a lesson without a source run is rejected

### Guardrails

The following guardrails are implemented in this task:

- **Validation:** Required lesson fields and confidence range are checked before further use.
- **Provenance:** Every valid lesson must reference a source run and supporting evidence.
- **Feedback-loop prevention:** Generated lesson content is kept separate from independent execution evidence.
- **Secret hygiene:** No credentials or sensitive values are stored in validation traces.

Timeout, retry, and step-limit controls are not applied to this deterministic validation function and are handled later in the execution loop where they are relevant.

---

## Task 3 — Implement the Memory-Write Policy

### Objective

This task controls whether a validated lesson is allowed to enter reflective memory.

The memory-write policy checks confidence, prevents duplicate writes, applies review requirements, and records the final lesson status.

### Files

- `memory.py` — Implements the reflective-memory store and write policy.
- `tests/test_memory.py` — Contains automated tests for memory-write behavior.
- `outputs/memory_events.json` — Stores structured memory-write events.
- `outputs/memory_quality.json` — Stores memory-quality counts.
- `outputs/memory.txt` — Stores the main Task 3 execution output.
- `outputs/test_memory.txt` — Stores the pytest results.

### Implementation

The `ReflectiveMemory` class maintains:

- stored lessons
- memory-write events
- memory-quality metrics
- confidence thresholds

The default policy uses:

```text
confidence_floor = 0.70
durable_review_floor = 0.85
```

### Validation Before Write

Before storing a lesson, `write()` reuses the `validate()` function from Task 2.

An invalid lesson returns:

```text
rejected_invalid
```

This prevents incomplete or invalid lessons from entering memory.

### Confidence Policy

A structurally valid lesson must also meet the minimum confidence threshold.

If:

```text
confidence < 0.70
```

the lesson is rejected with:

```text
rejected_low_confidence
```

This separates structural validation from the decision to store the lesson.

### Duplicate Detection

Before writing a lesson, the memory checks whether its deterministic `lesson_id` is already stored.

If the lesson already exists, the write returns:

```text
duplicate_ignored
```

The existing lesson is not silently overwritten.

### Review and Activation

Lessons below the durable review threshold but above the confidence floor become:

```text
active
```

A high-confidence lesson where:

```text
confidence >= 0.85
```

is placed into:

```text
pending_review
```

unless approval is explicitly provided.

If the same type of high-confidence lesson is written with:

```python
approved=True
```

its stored status becomes:

```text
active
```

This prevents important lessons from automatically changing future behavior without passing the required policy boundary.

### Status Persistence

When a lesson is accepted, a stored copy is created with its final status.

The lesson keeps its original:

- lesson ID
- condition
- refinement
- evidence
- source run
- confidence

while its status changes from `candidate` to either `active` or `pending_review`.

### Memory Events

Each write decision is recorded in:

```text
outputs/memory_events.json
```

The events record information such as:

- lesson ID
- write result
- source run
- confidence
- final status

This makes memory decisions traceable.

### Memory Quality Metrics

The implementation tracks:

```text
active_lessons
pending_review
rejected_writes
duplicate_writes
```

These counts are stored in:

```text
outputs/memory_quality.json
```

### Run the Implementation

```bash
python memory.py
```

### Run Automated Tests

```bash
pytest tests/test_memory.py -v
```

### Automated Tests

The tests verify:

- low-confidence lessons are rejected
- duplicate lessons are ignored
- high-confidence lessons require review
- approved high-confidence lessons become active
- stored lesson status and provenance remain available after the write

### Guardrails

The following guardrails are implemented in this task:

- **Validation:** Lessons are validated before memory writes.
- **Confidence threshold:** Low-confidence lessons are rejected.
- **Deduplication:** Existing lessons are not silently overwritten.
- **Review boundary:** High-confidence durable lessons require approval before activation.
- **Provenance:** Stored lessons retain their source run and supporting evidence.
- **Feedback-loop prevention:** A lesson cannot become active solely because it was generated; validation and memory policy are applied before activation.
- **Secret hygiene:** No credentials or secrets are stored in memory events.

Timeout, retry, and step limits are not required for this local memory-write function and are handled in the bounded execution loop.

---

## Task 4 — Implement Refine and Repeat

### Objective

This task implements the Refine and Repeat phases of the reflective-memory workflow.

A failed execution can produce a validated lesson, an active lesson can influence the next plan, and execution is repeated under a hard attempt limit.

### Files

- `loop.py` — Implements `refine()`, `repeat()`, the deterministic demo executor, and loop tracing.
- `tests/test_loop.py` — Contains automated tests for bounded execution and refinement behavior.
- `outputs/loop_trace.json` — Stores attempt-level execution evidence.
- `outputs/loop.txt` — Stores the main Task 4 execution output.
- `outputs/test_loop.txt` — Stores the pytest results.

### Refine Implementation

The `refine()` function checks reflective memory for lessons whose status is:

```text
active
```

Only active lessons can modify the next execution plan.

Lessons that are still:

```text
candidate
```

or:

```text
pending_review
```

do not influence future execution.

When no active lessons exist, the original task is returned unchanged.

When active lessons exist, their refinements are appended to the original task.

Example:

```text
Process customer support request

Refinements:
- Before repeating, validate and address: missing customer id
```

The original task is preserved while the lesson adds guidance for the next attempt.

### Repeat Implementation

The `repeat()` function executes the task using a deterministic executor.

Execution is controlled by:

```text
max_attempts
```

The loop can never execute more than the configured limit.

For every attempt, the implementation:

1. Preserves the original task.
2. Applies active lessons using `refine()`.
3. Executes the planned task.
4. Stores the `RunOutcome` in history.
5. Stops immediately if the run succeeds.
6. Reflects on a failed run.
7. Passes the generated lesson through the memory-write policy.
8. Repeats only while the attempt budget remains.

### First Failure and Second Success

The demonstration executor intentionally fails on the first attempt because of:

```text
missing customer id
```

The failure contains execution evidence:

```text
validator:customer_id_required
```

The reflection stage creates a lesson from this failure.

Because its confidence passes the memory-write policy, the lesson becomes active.

On the second attempt, the active lesson is applied to the original task before execution.

The second execution succeeds and the loop stops.

### Attempt Limit

The repeat loop uses:

```python
for attempt in range(1, max_attempts + 1):
```

This creates a hard upper boundary on the number of executions.

If all attempts fail, the loop stops after the configured maximum and records the terminal result as failure.

### Stop on Success

When an execution returns:

```text
status="success"
```

the loop immediately stops.

This prevents unnecessary additional execution after the task has already completed successfully.

### Execution History

Every `RunOutcome` is stored in order.

This preserves the complete execution history rather than keeping only the final result.

### Loop Trace

Task 4 creates:

```text
outputs/loop_trace.json
```

### Run the Implementation

```bash
python loop.py
```

### Run Automated Tests

```bash
pytest tests/test_loop.py -v
```

### Automated Tests

The tests verify:

- the first attempt can fail and the second can succeed after reflection
- repeated failures stop at `max_attempts`
- non-active lessons do not modify the task
- execution cannot enter an infinite loop

### Guardrails

The following guardrails are implemented in this task:

- **Step limit:** `max_attempts` creates a hard execution boundary.
- **Validation:** Reflected lessons pass through the existing validation and memory-write policy.
- **Provenance:** Lessons continue to preserve their source run and execution evidence.
- **Feedback-loop prevention:** Only active lessons can influence future plans.
- **Stop on success:** Successful execution immediately ends the repeat cycle.
- **Secret hygiene:** No credentials or sensitive configuration values are stored in loop traces.

The executor used in this task is deterministic and local, so an artificial timeout or transient retry mechanism is not added. Bounded repetition is handled by the explicit attempt limit.

