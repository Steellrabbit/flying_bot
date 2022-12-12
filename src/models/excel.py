from datetime import datetime
from dataclasses import dataclass


@dataclass
class WrittenTestCalculable:
    value: float | str
    cell: str 

@dataclass
class WrittenTestStudentAnswer:
    text: str
    mark: WrittenTestCalculable

@dataclass
class WrittenTestQuestionData:
    question: str
    answer: str
    max_mark: WrittenTestCalculable

@dataclass
class WrittenTestStudentData:
    name: str
    group: str
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
    date: datetime
    variants: list[WrittenTestVariantSheet]
    summary: WrittenTestSummarySheet
