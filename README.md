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

