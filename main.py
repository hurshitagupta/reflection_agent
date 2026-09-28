import json
from dataclasses import asdict
from pathlib import Path

from models import RunOutcome
from memory import ReflectiveMemory
from loop import repeat


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def executor(task: str, attempt: int) -> RunOutcome:

    if attempt == 1:
        return RunOutcome(
            run_id="run-1",
            task=task,
            status="failure",
            cause="missing customer id",
            evidence=("validator:customer_id_required",),
        )

    return RunOutcome(
        run_id=f"run-{attempt}",
        task=task,
        status="success",
        output="Customer request processed",
        evidence=("validator:passed",),
    )


def build_metrics(history: list[RunOutcome], memory: ReflectiveMemory) -> dict:

    successful_runs = sum(1 for outcome in history if outcome.status == "success")

    success_rate = (successful_runs / len(history) if history else 0.0)

    metrics = {
        "attempts": len(history),
        "reflected_lessons": len(memory.lessons),
        "active_lessons": sum(1 for lesson in memory.lessons.values() if lesson.status == "active"),
        "pending_review": sum(1 for lesson in memory.lessons.values() if lesson.status == "pending_review"),
        "rejected_writes": memory.metrics["rejected_writes"],
        "duplicate_writes": memory.metrics["duplicate_writes"],
        "success_rate": round(success_rate, 2),
    }

    return metrics


def save_final_evidence( history: list[RunOutcome], memory: ReflectiveMemory, metrics: dict) -> None:

    evidence = {"runs": [asdict(outcome) for outcome in history],
        "lessons": [asdict(lesson) for lesson in memory.lessons.values()],
        "metrics": metrics,
    }

    with open(OUTPUT_DIR / "final_evidence.json","w", encoding="utf-8") as file:
        json.dump(evidence, file, indent=4)

    with open(OUTPUT_DIR / "metrics.json", "w", encoding="utf-8") as file:
        json.dump( metrics, file, indent=4)


def main() -> None:

    memory = ReflectiveMemory()

    history = repeat( task="Process customer support request", memory=memory, executor=executor, max_attempts=3)

    metrics = build_metrics(history, memory)

    save_final_evidence(history, memory,metrics)

    print("=== Reflect, Refine, Repeat ===")

    for index, outcome in enumerate( history,start=1):
        print(f"Attempt {index}: {outcome.status}")

    print("\nStored lessons:")

    for lesson in memory.lessons.values():
        print(lesson.lesson_id, lesson.status, lesson.condition)

    print("\nMetrics:")
    print(metrics)

if __name__ == "__main__":
    main()