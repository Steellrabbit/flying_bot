import uuid
from dataclasses import dataclass
from enum import Enum


# region Test Question

class TestAnswerType(Enum):
    LECTURE = "из лекции"
    FREE = "в свободной форме"
    MULTIPLE_CHOICE = "множественный выбор"
    SINGLE_CHOICE = "единичный выбор"

TestAnswerValue = str | int | list[int]

@dataclass
class RawTestQuestion:
    type: TestAnswerType
    text: str
    answer_variants: list[str] | None
    answer: TestAnswerValue | None
    max_mark: float

@dataclass
class TestQuestion(RawTestQuestion):
    id: uuid.UUID

# endregion


# region Test Variant

@dataclass
class TestVariant:
    id: uuid.UUID
    name: str
    questions: list[TestQuestion]
    sum_max_mark: float

# endregion


# region Test

@dataclass
class RawTest:
    filename: str

@dataclass
class Test(RawTest):
    id: uuid.UUID
    name: str
    variants: list[TestVariant]

# endregion


# region Written test

@dataclass
class TestAnswer:
    id: uuid.UUID
    question_id: uuid.UUID
    value: TestAnswerValue 
    mark: float | None

@dataclass
class StudentWrittenTest:
    id: uuid.UUID
    finish_time: str | None
    student_id: int
    variant_id: uuid.UUID
    answers: list[TestAnswer]
    sum_mark: float | None

@dataclass
class WrittenTest:
    id: uuid.UUID
    test_id: uuid.UUID
    start_time: str
    finish_time: str | None
    student_tests: list[StudentWrittenTest]

# endregion
