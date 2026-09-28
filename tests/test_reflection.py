from models import RunOutcome
from reflection import reflect


def test_failure_creates_lesson():
    outcome = RunOutcome(
        run_id="run-001",
        task="Process support request",
        status="failure",
        cause="Missing customer ID",
        evidence=("validator:customer_id_required",),
    )

    lesson = reflect(outcome)

    assert lesson is not None
    assert lesson.condition == "missing customer id"
    assert lesson.source_run == "run-001"
    assert lesson.evidence == ("validator:customer_id_required",)
    assert lesson.confidence == 0.75


def test_success_creates_no_lesson():
    outcome = RunOutcome(
        run_id="run-002",
        task="Process support request",
        status="success",
        output="Request processed successfully",
        evidence=("executor:success",),
    )

    lesson = reflect(outcome)

    assert lesson is None


def test_missing_cause_is_rejected():
    outcome = RunOutcome(
        run_id="run-003",
        task="Process support request",
        status="failure",
        cause="",
        evidence=("executor:failed",),
    )

    lesson = reflect(outcome)

    assert lesson is None


def test_lesson_id_is_deterministic():
    outcome1 = RunOutcome(
        run_id="run-004",
        task="Process first request",
        status="failure",
        cause="Missing customer ID",
        evidence=("validator:first",),
    )

    outcome2 = RunOutcome(
        run_id="run-005",
        task="Process second request",
        status="failure",
        cause="Missing customer ID",
        evidence=("validator:second",),
    )

    lesson1 = reflect(outcome1)
    lesson2 = reflect(outcome2)

    assert lesson1 is not None
    assert lesson2 is not None
    assert lesson1.lesson_id == lesson2.lesson_id