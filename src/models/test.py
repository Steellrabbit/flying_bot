import uuid
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


# region Test Question

class TestAnswerType(Enum):
    LECTURE = "из лекции",
    FREE = "в свободной форме",

@dataclass
class RawTestQuestion:
    id: uuid.UUID
    type: TestAnswerType
    text: str
    answer: str | None
    max_mark: float

@dataclass
class LectureTestQuestion(RawTestQuestion):
    type: TestAnswerType.LECTURE
    answer: str

@dataclass
class FreeTestQuestion(RawTestQuestion):
    type: TestAnswerType.FREE
    answer: None

TestQuestion = LectureTestQuestion | FreeTestQuestion

# endregion


# region Test Variant

@dataclass
class TestVariant:
    id: uuid.UUID
    name: str
    questions: list[TestQuestion]

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
    text: str
    mark: float | None

@dataclass
class StudentWrittenTest:
    id: uuid.UUID
    finish_time: datetime | None
    student_id: int
    variant_id: uuid.UUID
    answers: list[TestAnswer]

@dataclass
class WrittenTest:
    id: uuid.UUID
    test_id: uuid.UUID
    start_time: datetime
    finish_time: datetime | None
    student_tests: list[StudentWrittenTest]

# endregion
