from models import RunOutcome, Lesson
from memory import ReflectiveMemory
from loop import refine, repeat


def test_first_failure_second_success():
    memory = ReflectiveMemory()

    def executor(task: str, attempt: int) -> RunOutcome:
        if attempt == 1:
            return RunOutcome(
                run_id="run-1",
                task=task,
                status="failure",
                cause="missing customer id",
                evidence=("validator:customer_id_required"),
            )

        return RunOutcome(
            run_id="run-2",
            task=task,
            status="success",
            output="Request processed",
            evidence=("validator:passed"),
        )

    history = repeat(
        task="Process support request",
        memory=memory,
        executor=executor,
        max_attempts=3,
    )

    assert len(history) == 2
    assert history[0].status == "failure"
    assert history[1].status == "success"

    assert len(memory.lessons) == 1

    stored_lesson = list(memory.lessons.values())[0]

    assert stored_lesson.status == "active"

    assert "Refinements:" in history[1].task
    assert "missing customer id" in history[1].task


def test_repeated_failure_until_limit():
    memory = ReflectiveMemory()

    def failing_executor(task: str,attempt: int) -> RunOutcome:

        return RunOutcome(
            run_id=f"run-{attempt}",
            task=task,
            status="failure",
            cause="temporary processing failure",
            evidence=f"executor:failure_{attempt}",
        )

    history = repeat(task="Process support request", memory=memory, executor=failing_executor, max_attempts=3)

    assert len(history) == 3

    assert all(outcome.status == "failure" for outcome in history)


def test_no_active_lesson_keeps_original_task():
    memory = ReflectiveMemory()

    lesson = Lesson(
        lesson_id="lesson-pending",
        condition="authorization missing",
        refinement="Check authorization before action",
        evidence=("policy:authorization_failed",),
        source_run="run-001",
        confidence=0.90,
        status="pending_review",
    )

    memory.lessons[lesson.lesson_id] = lesson

    original_task = "Process support request"

    refined_task = refine(original_task, memory)

    assert refined_task == original_task
    assert "Refinements:" not in refined_task


def test_no_infinite_loop():
    memory = ReflectiveMemory()

    call_count = 0

    def failing_executor(task: str, attempt: int) -> RunOutcome:

        nonlocal call_count

        call_count += 1

        return RunOutcome(
            run_id=f"run-{attempt}",
            task=task,
            status="failure",
            cause="processing failed",
            evidence=("executor:failure",),
        )

    history = repeat(task="Process support request", memory=memory, executor=failing_executor, max_attempts=2)

    assert call_count == 2
    assert len(history) == 2