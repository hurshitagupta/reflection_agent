import json
from dataclasses import asdict
from pathlib import Path

from models import Lesson
from validation import validate


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


class ReflectiveMemory:

    def __init__(self, confidence_floor: float = 0.70, durable_review_floor: float = 0.85):
        self.confidence_floor = confidence_floor
        self.durable_review_floor = durable_review_floor

        self.lessons: dict[str, Lesson] = {}

        self.events: list[dict] = []

        self.metrics = {
            "active_lessons": 0,
            "pending_review": 0,
            "rejected_writes": 0,
            "duplicate_writes": 0,
        }


    def save_memory_events(self) -> None:

        with open(OUTPUT_DIR / "memory_events.json", "w", encoding="utf-8") as file:
            json.dump(self.events, file, indent=4)


    def save_metrics(self) -> None:

        with open(OUTPUT_DIR / "memory_quality.json", "w", encoding="utf-8") as file:
            json.dump( self.metrics, file, indent=4)


    def write(self, lesson: Lesson, approved: bool = False) -> str:

        if not validate(lesson):

            self.metrics["rejected_writes"] += 1

            result = "rejected_invalid"

            self.events.append({
                "event": "memory_write",
                "lesson_id": lesson.lesson_id,
                "status": result,
            })

            self.save_memory_events()
            self.save_metrics()

            return result

        if lesson.confidence < self.confidence_floor:

            self.metrics["rejected_writes"] += 1

            result = "rejected_low_confidence"

            self.events.append({
                "event": "memory_write",
                "lesson_id": lesson.lesson_id,
                "status": result,
            })

            self.save_memory_events()
            self.save_metrics()

            return result

        if lesson.lesson_id in self.lessons:

            self.metrics["duplicate_writes"] += 1

            result = "duplicate_ignored"

            self.events.append({
                "event": "memory_write",
                "lesson_id": lesson.lesson_id,
                "status": result,
            })

            self.save_memory_events()
            self.save_metrics()

            return result

        if lesson.confidence >= self.durable_review_floor and not approved:
            status = "pending_review"

            self.metrics["pending_review"] += 1

        else:
            status = "active"

            self.metrics["active_lessons"] += 1


        stored_lesson = Lesson(**{ **asdict(lesson), "status": status})

        self.lessons[lesson.lesson_id] = stored_lesson


        self.events.append({
            "event": "memory_write",
            "lesson_id": lesson.lesson_id,
            "status": status,
            "source_run": lesson.source_run,
            "confidence": lesson.confidence,
        })


        self.save_memory_events()
        self.save_metrics()

        return status


if __name__ == "__main__":

    memory = ReflectiveMemory()

    normal_lesson = Lesson(
        lesson_id="lesson-001",
        condition="missing customer id",
        refinement="Validate customer id before retry",
        evidence=("validator:customer_id_required",),
        source_run="run-001",
        confidence=0.75,
    )

    high_confidence_lesson = Lesson(
        lesson_id="lesson-002",
        condition="authorization missing",
        refinement="Check authorization before action",
        evidence=("policy:authorization_failed",),
        source_run="run-002",
        confidence=0.90,
    )

    print("Normal lesson:")
    print(memory.write(normal_lesson))

    print("\nHigh-confidence lesson:")
    print(memory.write(high_confidence_lesson))

    print("\nApproved high-confidence lesson:")

    approved_memory = ReflectiveMemory()

    print(approved_memory.write(high_confidence_lesson, approved=True))

    print("\nStored lessons:")
    print(memory.lessons)

    print("\nMetrics:")
    print(memory.metrics)