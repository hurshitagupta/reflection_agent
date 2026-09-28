from models import Lesson
from validation import validate


def test_valid_lesson():
    lesson = Lesson( lesson_id="lesson-001", condition="missing customer id", refinement="Before repeating, validate customer id", evidence=("validator:customer_id_required"), source_run="run-001", confidence=0.75 )

    assert validate(lesson) is True


def test_incomplete_lesson():
    lesson = Lesson( lesson_id="lesson-002", condition="", refinement="Validate customer id", evidence=("validator:customer_id_required"), source_run="run-002", confidence=0.75)

    assert validate(lesson) is False


def test_out_of_range_confidence():
    lesson = Lesson( lesson_id="lesson-003", condition="missing customer id", refinement="Validate customer id", evidence=("validator:customer_id_required"), source_run="run-003", confidence=1.5)

    assert validate(lesson) is False


def test_missing_evidence():
    lesson = Lesson( lesson_id="lesson-004", condition="missing customer id", refinement="Validate customer id", evidence=(), source_run="run-004", confidence=0.75)

    assert validate(lesson) is False


def test_missing_source_run():
    lesson = Lesson(lesson_id="lesson-005", condition="missing customer id", refinement="Validate customer id",
        evidence=("validator:customer_id_required"), source_run="", confidence=0.75)

    assert validate(lesson) is False