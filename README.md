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

### Task 1 Result

Task 1 demonstrates the Reflect phase of the workflow by converting a structured failure into a deterministic and provenance-bearing lesson while rejecting invalid reflection cases.