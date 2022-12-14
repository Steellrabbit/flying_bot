import uuid
import random
from typing import Any
from datetime import datetime
from pathlib import Path

from pymongo import database
import pandas as pd
import numpy as np
import Levenshtein

from .excels import ExcelService
from .users import UsersTable
from .groups import GroupsTable
from ..models.user import Student
from ..models.excel import WrittenTestExcel, WrittenTestGroup, WrittenTestStudentAnswer, WrittenTestStudentData, WrittenTestVariantSheet,\
        WrittenTestSummarySheet, WrittenTestQuestionData,\
        WrittenTestCalculable
from ..models.group import Group
from ..models.test import RawTest, Test, TestQuestion,\
        RawTestQuestion, TestVariant, StudentWrittenTest,\
        WrittenTest, TestAnswer, TestAnswerType
from ..utils.get_from_list import get_from_list


TEST_COLLECTION = 'tests'
WRITTEN_TEST_COLLECTION = 'written-tests'

class TestsTable():

    def __init__(self,
            db: database.Database) -> None:
        self.__collection = db[TEST_COLLECTION]
        self.__written_collection = db[WRITTEN_TEST_COLLECTION]

        self.__students = UsersTable(db)
        self.__groups = GroupsTable(db)
        self.__excel = ExcelService()


    # region Test entities

    def create(self, source: RawTest) -> Test:
        test = self.__excel.read_test(source)

        doc = self.__test_to_document(test)
        insert_result = self.__collection.insert_one(doc)
        found = self.__collection.find_one({ '_id': insert_result.inserted_id })

        return self.__test_from_document(found)

    def get(self, property: str, value: Any) -> Test | None:
        found = self.__collection.find_one({ property: value })
        if found is None: return
        return self.__test_from_document(found)

    def get_all(self) -> list[Test]:
        found = self.__collection.find()
        return list(map(lambda doc: self.__test_from_document(doc), found))

    def __convert_to_excel(self, written_test: WrittenTest) -> WrittenTestExcel:
        test: Test = self.get('_id', written_test.test_id)

        groups: dict[list[WrittenTestStudentData]] = dict()

        variant_sheets: list[WrittenTestVariantSheet] = []
        for variant in test.variants:
            sheet_name = variant.name

            question_data: list[WrittenTestQuestionData] = []
            max_mark_offset = 3
            for question in variant.questions:
                question_text = question.text
                answer = question.answer or ''

                max_mark_value = question.max_mark
                max_mark_cell = f'=OFFSET(A2, 0, {max_mark_offset})'
                max_mark_offset += 2
                max_mark = WrittenTestCalculable(max_mark_value, max_mark_cell)

                question_data_element = WrittenTestQuestionData(question_text, answer, max_mark)
                question_data.append(question_data_element)

            student_data: list[WrittenTestStudentData] = []
            student_tests = filter(
                    lambda t: t.variant_id == variant.id,
                    written_test.student_tests)
            mark_row_offset = 3
            for student_test in student_tests:
                student = self.__students.get_student(student_test.student_id)
                student_name = student.name
                group: Group = self.__groups.get('_id', student.group_id)
                student_group = group.name

                answer_data: list[WrittenTestStudentAnswer] = []
                mark_column_offset = 3
                print('--------------------------------', student_test.answers)
                for answer in student_test.answers:
                    answer_text = answer.text

                    mark_value = answer.mark
                    mark_cell = f'=OFFSET(A1, {mark_row_offset}, {mark_column_offset})'
                    mark_column_offset += 2
                    mark_row_offset += 1
                    mark = WrittenTestCalculable(mark_value, mark_cell)

                    answer_data_element = WrittenTestStudentAnswer(answer_text, mark)
                    answer_data.append(answer_data_element)

                student_data_element = WrittenTestStudentData(student_name, student_group, answer_data)
                student_data.append(student_data_element)

                group_data: list[WrittenTestStudentData] = groups.get(group.name, [])
                group_data.append(student_data_element)
                groups[group.name] = group_data

            variant_sheet = WrittenTestVariantSheet(sheet_name, question_data, student_data)
            variant_sheets.append(variant_sheet)

        group_data: list[WrittenTestGroup] = []
        for name in groups.keys():
            group_name = name
            group_students = groups[name]
            group_data_element = WrittenTestGroup(group_name, group_students)
            group_data.append(group_data_element)
        summary_sheet = WrittenTestSummarySheet(group_data)
        return WrittenTestExcel(test.name, written_test.finish_time, variant_sheets, summary_sheet)

    def __test_to_document(self, test: Test) -> dict:
        variant_docs = []
        for variant in test.variants:
            doc = { 'id': str(variant.id), 'name': variant.name }
            question_docs = []

            for question in variant.questions:
                question_doc = { 'id': str(question.id), 'type': question.type, 'text': question.text, 'answer': question.answer, 'max_mark': question.max_mark }
                question_docs.append(question_doc)

            doc['questions'] = question_docs
            variant_docs.append(doc)

        return { 'filename': test.filename, 'name': test.name, 'variants': variant_docs }

    def __test_from_document(self, doc: dict) -> Test:
        variants = []
        for variant_doc in doc['variants']:
            questions = []

            for question_doc in variant_doc['questions']:
                question = RawTestQuestion(uuid.UUID(question_doc['id']), question_doc['type'], question_doc['text'], question_doc['answer'], question_doc['max_mark'])
                questions.append(question)

            variant = TestVariant(uuid.UUID(variant_doc['id']), variant_doc['name'], questions)
            variants.append(variant)

        return Test(doc['filename'], doc['_id'], doc['name'], variants)

    # endregion


    # region Writing

    def start(self,
            test_id: uuid.UUID,
            student_ids: list[int]) -> WrittenTest:
        test = self.get('_id', test_id)
        if test is None:
            raise Exception('Test was not found')

        id = uuid.uuid4()
        start_time = datetime.today()
        finish_time = None
        student_tests: list[StudentWrittenTest] = []

        for student_id in student_ids:
            id = uuid.uuid4()
            finish_time = None
            variant_id = self.get_random_variant(test_id).id
            answers = []
            student_test = StudentWrittenTest(id, finish_time, student_id, variant_id, answers)
            student_tests.append(student_test)

        doc = self.__written_to_document(WrittenTest(id, test_id, start_time, finish_time, student_tests))
        insert_result = self.__written_collection.insert_one(doc)
        found = self.__written_collection.find_one({ '_id': insert_result.inserted_id })
        return self.__written_from_document(found)

    def get_written(self, property: str, value: Any) -> WrittenTest | None:
        found = self.__written_collection.find_one({ property: value })
        if found is None: return
        return self.__written_from_document(found)

    def finish(self, written_test_id: uuid.UUID) -> str:
        test = self.get_written('_id', written_test_id)
        if test is None:
            raise Exception('Written test was not found')

        finish_time = datetime.today()
        test.finish_time = finish_time
        for student_test in test.student_tests:
            print('##########################################', student_test)
            if student_test.finish_time is None:
                student_test.finish_time = finish_time

        self.__written_collection.update_one({ '_id': test.id }, {'$set': self.__written_to_document(test)})


        excel = self.__convert_to_excel(test)
        return self.__excel.write_written_test(excel)

    def finish_student(self,
            written_test_id: uuid.UUID,
            student_id: int) -> None:
        student_test = self.get_student(written_test_id, 'student_id', student_id)
        if student_test is None:
            raise Exception('Written test was not found')

        finish_time = datetime.today()
        student_test.finish_time = finish_time

        test = self.get_written('_id', written_test_id)
        self.__written_collection.update_one({ '_id': test.id }, {'$set': self.__written_to_document(test)})


    def get_student(self,
            written_test_id: uuid.UUID | None,
            student_test_prop: str,
            value: Any,
            written_test: WrittenTest | None = None) -> StudentWrittenTest | None:
        test = self.get_written('_id', written_test_id) if written_test_id else written_test
        if test is None: return None
        return get_from_list(test.student_tests, student_test_prop, value)

    def save_answer(self,
            student_id: int,
            written_test_id: uuid.UUID,
            question_id: uuid.UUID,
            text: str) -> None:
        written_test = self.get_written('_id', written_test_id)
        student_test = self.get_student(None, 'student_id', student_id, written_test)
        question = self.get_question(written_test.test_id, student_test.variant_id, None, question_id)

        mark = self.__check_answer(question, text)
        print('++++++++++++++++++++++++++++++++++++++++++++++++++++', mark)
        id = uuid.uuid4()
        answer = TestAnswer(id, question_id, text, mark)

        if student_test is None:
            raise Exception('Written test was not found')
        student_test.answers.append(answer)

        self.__written_collection.update_one({ '_id': written_test.id }, {'$set': self.__written_to_document(written_test)})

    def __written_to_document(self, test: WrittenTest) -> dict:
        student_docs = []
        for student_test in test.student_tests:
            doc = { 'id': str(student_test.id), 'finish_time': student_test.finish_time, 'student_id': student_test.student_id, 'variant_id': str(student_test.variant_id) }
            answer_docs = []
            for answer in student_test.answers:
                answer_doc = { 'id': str(answer.id), 'question_id': str(answer.question_id), 'text': answer.text, 'mark': answer.mark }
                answer_docs.append(answer_doc)
            doc['answers'] = answer_docs
            student_docs.append(doc)
        return { 'test_id': test.test_id, 'start_time': test.start_time, 'finish_time': test.finish_time, 'student_tests': student_docs }

    def __written_from_document(self, doc: dict) -> WrittenTest:
        students = []
        for student_doc in doc['student_tests']:
            answers = []

            for answer_doc in student_doc['answers']:
                answer = TestAnswer(uuid.UUID(answer_doc['id']), uuid.UUID(answer_doc['question_id']), answer_doc['text'], answer_doc['mark'])
                answers.append(answer)

            student = StudentWrittenTest(uuid.UUID(student_doc['id']), student_doc['finish_time'], student_doc['student_id'], uuid.UUID(student_doc['variant_id']), answers)
            students.append(student)

        return WrittenTest(doc['_id'], doc['test_id'], doc['start_time'], doc['finish_time'], students)

    # endregion


    # region Check

    def __check_answer(self,
            question: TestQuestion,
            text: str) -> float | None:
        """Checks test question answer and returns mark if possible"""
        print('????????????????????????????????????????', question.type, TestAnswerType.LECTURE.value, question.type == TestAnswerType.LECTURE.value)
        if question.type == TestAnswerType.LECTURE.value:
           return Levenshtein.ratio(question.answer, text) * question.max_mark
        return None

    # endregion


    # region Variants

    def get_random_variant(self, test_id: uuid.UUID) -> TestVariant | None:
        test = self.get('_id', test_id)
        if test is None: return None
        return random.choice(test.variants)

    def get_variant(self,
            test_id: uuid.UUID,
            variant_prop: str,
            value: Any) -> TestVariant | None:
        test = self.get('_id', test_id)
        if test is None: return None

        return get_from_list(test.variants, variant_prop, value)

    def get_question(self,
            test_id: uuid.UUID,
            variant_id: uuid.UUID,
            index: int | None = None,
            question_id: uuid.UUID | None = None) -> TestQuestion | None:
        variant = self.get_variant(test_id, 'id', variant_id)
        print(variant.questions)
        if variant is None: return None

        if question_id is not None:
            question = get_from_list(variant.questions, 'id', question_id)
            if question is not None: return question

        if index is None: return None
        if len(variant.questions) <= index: return None
        print(variant.questions)
        return variant.questions[index]

    # endregion
