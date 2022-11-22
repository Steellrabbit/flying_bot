import uuid
import pandas as pd
import numpy as np
import random
from typing import List, Union
from datetime import datetime

from ..models.test import RawTest, Test, TestQuestion, RawTestQuestion, TestVariant, StudentWrittenTest, WrittenTest, TestAnswer


class TestsTable():

    def __init__(self) -> None:
        self.entities: List[Test] = []
        self.written: List[WrittenTest] = []

    def create_test(self, source: RawTest) -> Test:
        filename = source.filename
        id = uuid.uuid4()
        variants = self.__parse_test_file(filename)
        
        test = Test(filename, id, variants)
        print(test)
        self.entities.append(test)
        return test

    def __parse_test_file(self, filename: str) -> List[TestVariant]:
        frame = pd.read_excel(filename, sheet_name=None)
        variants: List[TestVariant] = []

        for sheet_name in frame.keys():
            id = uuid.uuid4()
            name = sheet_name
            sheet: pd.DataFrame = frame[sheet_name]
            questions: List[TestQuestion] = []

            for row in sheet.to_dict(orient='records'):
                id = uuid.uuid4()
                text = row['вопрос']
                type = row['тип ответа']
                answer = None if pd.isna(row['ответ']) else row['ответ']
                max_mark = row['макс балл']
                question = RawTestQuestion(id, type, text, answer, max_mark)
                questions.append(question)

            variant = TestVariant(id, name, questions)
            variants.append(variant)

        return variants

    def get_test(self, id: uuid.UUID) -> Union[Test, None]:
        for entity in self.entities:
            if entity.id == id:
                return entity
        return None

    def get_tests(self) -> List[Test]:
        return self.entities


    # region Writing Tests

    def start_test(self,
            test_id: uuid.UUID,
            student_ids: List[uuid.UUID]) -> None:
        test = self.get_test(test_id)
        if test is None:
            raise Exception('Test was not found')

        id = uuid.uuid4()
        start_time = datetime()
        finish_time = None
        student_tests: List[StudentWrittenTest] = []

        for student_id in student_ids:
            id = uuid.uuid4()
            finish_time = None
            variant_id = self.get_random_variant(test_id).id
            answers = []
            student_test = StudentWrittenTest(id, variant_id, finish_time, student_id, answers)
            student_tests.append(student_test)

        written_test = WrittenTest(id, test_id, start_time, finish_time, student_tests)
        self.written.append(written_test)

    def get_written_test(self, id: uuid.UUID) -> Union[WrittenTest, None]:
        for entity in self.written:
            if entity.id == id:
                return entity
        return None

    def finish_test(self, written_test_id: uuid.UUID) -> None:
        test = self.get_written_test(written_test_id)
        if test is None:
            raise Exception('Written test was not found')

        finish_time = datetime()
        test.finish_time = finish_time
        for student_test in test.student_tests:
            if student_test.finish_time is None:
                student_test.finish_time = finish_time

    def finish_student_test(self,
            written_test_id: uuid.UUID,
            student_id: uuid.UUID) -> None:
        student_test = self.get_student_test(written_test_id, student_id)
        if student_test is None:
            raise Exception('Written test was not found')

        finish_time = datetime()
        student_test.finish_time = finish_time

    def get_student_test(self,
            written_test_id: uuid.UUID,
            student_id: uuid.UUID) -> Union[StudentWrittenTest, None]:
        test = self.get_written_test(student_id)
        if test is None:
            return None

        for student_test in test.student_tests:
            if student_test.student_id == student_id:
                return student_test
        return None;

    def save_question_answer(self,
            student_id: uuid.UUID,
            written_test_id: uuid.UUID,
            question_id: uuid.UUID,
            text: str) -> None:
        id = uuid.uuid4()
        mark = None
        answer = TestAnswer(id, question_id, text, mark)
        test = self.get_student_test(written_test_id, student_id)
        test.answers.append(answer)


    # endregion


    # region Variants

    def get_random_variant(self, test_id: uuid.UUID) -> Union[TestVariant, None]:
        test = self.get_test(test_id)
        if test is None:
            return None
        return random.choice(test.variants)

    def get_variant(self,
            test_id: uuid.UUID,
            variant_id: uuid.UUID) -> Union[TestVariant, None]:
        test = self.get_test(test_id)
        if test is None:
            return None
        for variant in test.variants:
            if variant.id == variant_id:
                return variant
        return None

    # endregion


    def get_question(self,
            test_id: uuid.UUID,
            variant_id: uuid.UUID,
            index: Union[int, None] = None,
            question_id: [uuid.UUID, None] = None) -> Union[TestQuestion, None]:
        variant = self.get_variant(test_id, variant_id)
        if variant is None:
            return None

        if question_id is not None:
            for question in variant.questions:
                if question.id == question_id:
                    return question

        if index is None:
            return None
        if len(variant.questions) <= index:
            return None
        return variant.questions[index]

