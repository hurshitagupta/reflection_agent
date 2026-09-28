from models import Lesson
from memory import ReflectiveMemory


def test_low_confidence_rejected():
    memory = ReflectiveMemory()

    lesson = Lesson(
        lesson_id="lesson-low",
        condition="missing field",
        refinement="Validate the field before retry",
        evidence=("validator:missing_field"),
        source_run="run-001",
        confidence=0.50,
    )

    result = memory.write(lesson)

    assert result == "rejected_low_confidence"
    assert "lesson-low" not in memory.lessons
    assert memory.metrics["rejected_writes"] == 1


def test_duplicate_ignored():
    memory = ReflectiveMemory()

    lesson = Lesson(
        lesson_id="lesson-duplicate",
        condition="missing customer id",
        refinement="Validate customer id before retry",
        evidence=("validator:customer_id_required"),
        source_run="run-002",
        confidence=0.75,
    )

    first_result = memory.write(lesson)
    second_result = memory.write(lesson)

    assert first_result == "active"
    assert second_result == "duplicate_ignored"
    assert memory.metrics["duplicate_writes"] == 1
    assert len(memory.lessons) == 1


def test_high_confidence_pending_review():
    memory = ReflectiveMemory()

    lesson = Lesson(
        lesson_id="lesson-review",
        condition="authorization missing",
        refinement="Check authorization before execution",
        evidence=("policy:authorization_failed"),
        source_run="run-003",
        confidence=0.90,
    )

    result = memory.write(lesson)

    assert result == "pending_review"
    assert memory.lessons["lesson-review"].status == "pending_review"
    assert memory.metrics["pending_review"] == 1


def test_approved_high_confidence_becomes_active():
    memory = ReflectiveMemory()

    lesson = Lesson(
        lesson_id="lesson-approved",
        condition="authorization missing",
        refinement="Check authorization before execution",
        evidence=("policy:authorization_failed"),
        source_run="run-004",
        confidence=0.90,
    )

    result = memory.write(lesson, approved=True)

    assert result == "active"
    assert memory.lessons["lesson-approved"].status == "active"
    assert memory.metrics["active_lessons"] == 1


def test_status_persistence():
    memory = ReflectiveMemory()

    lesson = Lesson(
        lesson_id="lesson-persist",
        condition="missing customer id",
        refinement="Validate customer id before retry",
        evidence=("validator:customer_id_required"),
        source_run="run-005",
        confidence=0.75,
    )

    memory.write(lesson)

    stored_lesson = memory.lessons["lesson-persist"]

    assert stored_lesson.status == "active"
    assert stored_lesson.lesson_id == "lesson-persist"
    assert stored_lesson.source_run == "run-005"
    assert stored_lesson.evidence == "validator:customer_id_required"
    