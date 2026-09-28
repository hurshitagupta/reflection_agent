from dataclasses import dataclass


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    task: str
    status: str
    output: str = ""
    cause: str = ""
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    condition: str
    refinement: str
    evidence: tuple[str, ...]
    source_run: str
    confidence: float
    status: str = "candidate"