import json
from pathlib import Path

from models import Lesson


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_validation_trace(lesson: Lesson, valid: bool, reason: str) -> None:

    trace = {
        "event": "lesson_validated",
        "lesson_id": lesson.lesson_id,
        "source_run": lesson.source_run,
        "evidence": list(lesson.evidence),
        "confidence": lesson.confidence,
        "valid": valid,
        "reason": reason,
    }

    with open(OUTPUT_DIR / "validation_trace.json", "w", encoding="utf-8") as file:
        json.dump(trace, file, indent=4)


def validate(lesson: Lesson) -> bool:

    if not lesson.condition.strip():
        save_validation_trace( lesson, False, "Missing condition")
        return False

    if not lesson.refinement.strip():
        save_validation_trace(lesson, False, "Missing refinement")
        return False

    if not lesson.source_run.strip():
        save_validation_trace(lesson, False, "Missing source run")
        return False

    if not lesson.evidence:
        save_validation_trace(lesson, False, "Missing independent evidence")
        return False

    if not 0.0 <= lesson.confidence <= 1.0:
        save_validation_trace(lesson, False, "Confidence must be between 0 and 1")
        return False

    save_validation_trace(lesson, True, "Lesson is valid")

    return True


if __name__ == "__main__":

    lesson = Lesson(
        lesson_id="lesson-001",
        condition="missing customer id",
        refinement=("Before repeating, validate and address: missing customer id"),
        evidence=("validator:customer_id_required",),
        source_run="run-001",
        confidence=0.75,
    )

    result = validate(lesson)

    print("Lesson:")
    print(lesson)

    print("\nValidation result:")
    print(result)