from models import Lesson
from validation import validate
from memory import ReflectiveMemory


def test_lesson_cannot_confirm_itself():

    lesson = Lesson(
        lesson_id="lesson-self",
        condition="missing customer id",
        refinement=("Validate customer id before retry"),
        evidence=(),
        source_run="run-001",
        confidence=0.90,
    )

    assert validate(lesson) is False

    memory = ReflectiveMemory()

    result = memory.write(lesson)

    assert result == "rejected_invalid"

    assert "lesson-self" not in memory.lessons
    