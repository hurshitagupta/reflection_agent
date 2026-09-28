import json
import time
from pathlib import Path
from typing import Callable

from models import RunOutcome
from reflection import reflect
from memory import ReflectiveMemory


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def refine(task: str, memory: ReflectiveMemory) -> str:

    active_refinements = [lesson.refinement
        for lesson in memory.lessons.values()
        if lesson.status == "active"
    ]

    if not active_refinements:
        return task

    refined_task = task + "\nRefinements:\n- " + "\n- ".join(active_refinements)

    return refined_task


def save_loop_trace(trace: dict) -> None:

    with open( OUTPUT_DIR / "loop_trace.json", "w", encoding="utf-8") as file:
        json.dump(trace, file, indent=4)


def repeat( task: str, memory: ReflectiveMemory, executor: Callable[[str, int], RunOutcome], max_attempts: int = 3) -> list[RunOutcome]:

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    history: list[RunOutcome] = []
    attempt_traces = []

    start_time = time.perf_counter()

    for attempt in range(1, max_attempts + 1):

        before_plan = task

        planned_task = refine( task, memory)

        attempt_start = time.perf_counter()

        outcome = executor( planned_task, attempt)

        attempt_duration = time.perf_counter() - attempt_start

        history.append(outcome)

        attempt_trace = {
            "attempt": attempt,
            "before_plan": before_plan,
            "after_plan": planned_task,
            "run_id": outcome.run_id,
            "status": outcome.status,
            "cause": outcome.cause,
            "evidence": list(outcome.evidence),
            "duration_seconds": round(attempt_duration, 6)
        }

        attempt_traces.append(attempt_trace)

        if outcome.status == "success":
            break

        lesson = reflect(outcome)

        if lesson is not None:
            memory.write(lesson)

    total_duration = time.perf_counter() - start_time
    

    terminal_status = "success" if history and history[-1].status == "success" else "failure"

    trace = {
        "task": task,
        "max_attempts": max_attempts,
        "attempts_used": len(history),
        "terminal_status": terminal_status,
        "total_duration_seconds": round(total_duration, 6),
        "attempts": attempt_traces
    }

    save_loop_trace(trace)

    return history


def demo_executor( task: str, attempt: int) -> RunOutcome:

    if attempt == 1:
        return RunOutcome(
            run_id="run-1",
            task=task,
            status="failure",
            cause="missing customer id",
            evidence=("validator:customer_id_required"),
        )

    return RunOutcome(
        run_id=f"run-{attempt}",
        task=task,
        status="success",
        output="Request processed successfully",
        evidence=("validator:passed"),
    )


if __name__ == "__main__":

    memory = ReflectiveMemory()

    history = repeat(
        task="Process customer support request",
        memory=memory,
        executor=demo_executor,
        max_attempts=3,
    )

    print("Run history:")

    for outcome in history:
        print(outcome)

    print("\nStored lessons:")

    for lesson in memory.lessons.values():
        print(lesson)