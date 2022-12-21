from dataclasses import dataclass


@dataclass
class WrittenTestStudentAnswer:
    text: str
    mark: float

@dataclass
class WrittenTestQuestionData:
    question: str
    answer: str
    max_mark: float

@dataclass
class WrittenTestStudentData:
    name: str
    group: str
    id: int
    answers: list[WrittenTestStudentAnswer]

@dataclass
class WrittenTestVariantSheet:
    name: str
    questions: list[WrittenTestQuestionData]
    students: list[WrittenTestStudentData]

@dataclass
class WrittenTestGroup:
    group: str
    students: list[WrittenTestStudentData]

@dataclass
class WrittenTestSummarySheet:
    groups: list[WrittenTestGroup]

@dataclass
class WrittenTestExcel:
    name: str
    date: str
    variants: list[WrittenTestVariantSheet]
    summary: WrittenTestSummarySheet


@dataclass
class UpdatedTestExcel:
    name: str
    date: str
    students: list[UpdatedStudentData]

@dataclass
class UpdatedStudentData:
    name: str
    marks: list[float]
