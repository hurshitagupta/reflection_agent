import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from models import RunOutcome, Lesson


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_reflection_event(outcome: RunOutcome,lesson: Lesson) -> None:

    event = {
        "event": "reflection_created",
        "run_id": outcome.run_id,
        "cause": outcome.cause,
        "evidence": list(outcome.evidence),
        "confidence": lesson.confidence,
        "lesson": asdict(lesson),
    }

    with open( OUTPUT_DIR / "reflection_event.json", "w", encoding="utf-8") as file:
        json.dump(event, file, indent=4)


def reflect(outcome: RunOutcome) -> Lesson | None:

    if outcome.status != "failure":
        return None

    if not outcome.cause.strip():
        return None

    condition = outcome.cause.strip().lower()

    refinement = f"Before repeating, validate and address: {condition}"

    raw_id = f"{condition}|{refinement}"

    lesson_id = sha256(raw_id.encode("utf-8")).hexdigest()[:12]

    lesson = Lesson(
        lesson_id=lesson_id,
        condition=condition,
        refinement=refinement,
        evidence=outcome.evidence,
        source_run=outcome.run_id,
        confidence=0.75,
    )

    save_reflection_event(outcome, lesson)

    return lesson


if __name__ == "__main__":

    failed_run = RunOutcome(
        run_id="run-001",
        task="Process customer support request",
        status="failure",
        cause="Missing customer ID",
        evidence=("validator:customer_id_required",),
    )

    lesson = reflect(failed_run)

    print("Run outcome:")
    print(failed_run)

    print("\nReflected lesson:")
    print(lesson)