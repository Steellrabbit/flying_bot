import uuid
import random
from typing import Any, Union, cast

from pymongo import database
import Levenshtein

from config import TEST_COLLECTION_NAME, WRITTEN_TEST_COLLECTION_NAME

from .excels import ExcelService
from ..utils.get_current_time import get_current_time
from .users import UsersTable
from .groups import GroupsTable
from ..models.excel import WrittenTestExcel, WrittenTestGroup, WrittenTestStudentAnswer, WrittenTestStudentData, WrittenTestVariantSheet,\
        WrittenTestSummarySheet, WrittenTestQuestionData
from ..models.test import RawTest, Test, TestAnswerValue, TestQuestion,\
        TestVariant, StudentWrittenTest,\
        WrittenTest, TestAnswer, TestAnswerType
from ..utils.get_from_list import get_from_list


class TestsTable():

    def __init__(self,
            db: database.Database) -> None:
        self.__collection = db[TEST_COLLECTION_NAME]
        self.__written_collection = db[WRITTEN_TEST_COLLECTION_NAME]

        self.__students = UsersTable(db)
        self.__groups = GroupsTable(db)
        self.__excel = ExcelService()


    # region Test entities

    def create(self, source: RawTest) -> Test:
        test = self.__excel.read_test(source)

        doc = self.__test_to_document(test)
        insert_result = self.__collection.insert_one(doc)
        found = self.__collection.find_one({ '_id': insert_result.inserted_id })

        return self.__test_from_document(cast(dict, found))

    def get(self, property: str, value: Any) -> Union[Test, None]:
        found = self.__collection.find_one({ property: value })
        if found is None: return
        return self.__test_from_document(found)

    def get_all(self) -> list[Test]:
        found = self.__collection.find()
        return list(map(lambda doc: self.__test_from_document(doc), found))

    def remove_all(self) -> None:
        self.__collection.delete_many({})

    def __convert_to_excel(self, written_test: WrittenTest) -> WrittenTestExcel:
        test = self.get('_id', written_test.test_id)
        if test is None:
            raise Exception('Cannot convert to excel. Test was not found.');

        groups: dict[str, list[WrittenTestStudentData]] = dict()

        variant_sheets: list[WrittenTestVariantSheet] = []
        for variant in test.variants:
            sheet_name = variant.name

            question_data: list[WrittenTestQuestionData] = []
            for question in variant.questions:
                question_text = question.text
                answer = question.answer or ''
                max_mark = question.max_mark

                question_data_element = WrittenTestQuestionData(question_text, answer, max_mark)
                question_data.append(question_data_element)

            student_data: list[WrittenTestStudentData] = []
            student_tests = filter(
                    lambda t: t.variant_id == variant.id,
                    written_test.student_tests)
            for student_test in student_tests:
                student = self.__students.get_student('telegram_id', student_test.student_id)
                if student is None:
                    raise Exception(f'Cannot convert to excel.' +\
                            'Student {student_test.student_id} was not found.');

                group = self.__groups.get('_id', student.group_id)
                if group is None:
                    raise Exception(f'Cannot convert to excel.' +\
                            'Group {student.group_id} was not found.');

                student_group = group.name

                answer_data: list[WrittenTestStudentAnswer] = []
                for answer in student_test.answers:
                    answer_value = answer.value
                    mark = answer.mark

                    answer_data_element = WrittenTestStudentAnswer(answer_value, mark)
                    answer_data.append(answer_data_element)

                student_data_element = WrittenTestStudentData(\
                        student.name, student_group, student.id, answer_data)
                student_data.append(student_data_element)

                student_datas: list[WrittenTestStudentData] = groups.get(group.name, [])
                student_datas.append(student_data_element)
                groups[group.name] = student_datas

            variant_sheet = WrittenTestVariantSheet(sheet_name, question_data, student_data)
            variant_sheets.append(variant_sheet)

        group_data: list[WrittenTestGroup] = []
        for name in groups.keys():
            group_name = name
            group_students = groups[name]
            group_data_element = WrittenTestGroup(group_name, group_students)
            group_data.append(group_data_element)
        summary_sheet = WrittenTestSummarySheet(group_data)

        if written_test.finish_time is None:
            raise Exception(f'Cannot convert to excel.' +\
                    'Test is not finished yet.')
        return WrittenTestExcel(test.name, written_test.finish_time, variant_sheets, summary_sheet)

    def __test_to_document(self, test: Test) -> dict:
        variant_docs = []
        for variant in test.variants:
            doc = { 'id': str(variant.id), 'name': variant.name, 'sum_max_mark': variant.sum_max_mark }
            question_docs = []

            for question in variant.questions:
                question_doc = { 'id': str(question.id),\
                        'type': question.type,\
                        'text': question.text,\
                        'answer_variants': question.answer_variants,\
                        'answer': question.answer,\
                        'max_mark': question.max_mark }
                question_docs.append(question_doc)

            doc['questions'] = question_docs
            variant_docs.append(doc)

        return { 'filename': test.filename, 'name': test.name, 'variants': variant_docs}

    def __test_from_document(self, doc: dict) -> Test:
        variants = []
        for variant_doc in doc['variants']:
            questions = []

            for question_doc in variant_doc['questions']:
                question = TestQuestion(
                        question_doc['type'],\
                        question_doc['text'],\
                        question_doc['answer_variants'],\
                        question_doc['answer'],\
                        question_doc['max_mark'],\
                        uuid.UUID(question_doc['id']))
                questions.append(question)

            variant = TestVariant(uuid.UUID(variant_doc['id']), variant_doc['name'], questions, variant_doc['sum_max_mark'])
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
        start_time = get_current_time()
        finish_time = None
        student_tests: list[StudentWrittenTest] = []

        for student_id in student_ids:
            id = uuid.uuid4()
            finish_time = None
            variant = self.get_random_variant(test_id)
            if variant is None:
                raise Exception('Random variant was not found')
            answers = []
            student_test = StudentWrittenTest(id, finish_time, student_id, variant.id, answers, None)
            student_tests.append(student_test)

        doc = self.__written_to_document(WrittenTest(id, test_id, start_time, finish_time, student_tests))
        insert_result = self.__written_collection.insert_one(doc)
        found = self.__written_collection.find_one({ '_id': insert_result.inserted_id })
        return self.__written_from_document(cast(dict, found))

    def get_written(self, property: str, value: Any) -> Union[WrittenTest, None]:
        found = self.__written_collection.find_one({ property: value })
        if found is None: return
        return self.__written_from_document(found)

    def remove_written(self) -> None:
        self.__written_collection.delete_many({})

    def finish(self, written_test_id: uuid.UUID) -> str:
        test = self.get_written('_id', written_test_id)
        if test is None:
            raise Exception('Written test was not found')

        finish_time = get_current_time()
        test.finish_time = finish_time
        for student_test in test.student_tests:
            if student_test.finish_time is None:
                student_test.finish_time = finish_time

        self.__written_collection.update_one({ '_id': test.id }, {'$set': self.__written_to_document(test)})


        excel = self.__convert_to_excel(test)
        return self.__excel.write_written_test(excel)

    def finish_student(self,
            written_test_id: uuid.UUID,
            student_id: int) -> None:
        """
        Finishes test for a single student.

        Sets finish time on his test.
        """
        student_test = self.get_student(written_test_id, 'student_id', student_id)
        if student_test is None:
            raise Exception('Written test was not found')

        finish_time = get_current_time()
        student_test.finish_time = finish_time

        test = self.get_written('_id', written_test_id)
        if test is None:
            raise Exception('Cannot finish test for a student. Test was not found')
        self.__written_collection.update_one({ '_id': test.id }, {'$set': self.__written_to_document(test)})


    def get_student(self,
            written_test_id: Union[uuid.UUID, None],
            student_test_prop: str,
            value: Any,
            written_test: Union[WrittenTest, None] = None) -> Union[StudentWrittenTest, None]:
        test = self.get_written('_id', written_test_id) if written_test_id else written_test
        if test is None: return None
        return get_from_list(test.student_tests, student_test_prop, value)

    def save_answer(self,
            student_id: int,
            written_test_id: uuid.UUID,
            question_id: uuid.UUID,
            text: str) -> None:
        written_test = self.get_written('_id', written_test_id)
        if written_test is None:
            raise Exception('Cannot save student\'s answer for a test. WrittenTest was not found')
        student_test = self.get_student(None, 'student_id', student_id, written_test)
        if student_test is None:
            raise Exception('Cannot save student\'s answer for a test. StudentTest was not found')
        question = self.get_question(written_test.test_id, student_test.variant_id, None, question_id)
        if question is None:
            raise Exception('Cannot save student\'s answer for a test. Question was not found')

        mark = self.__check_answer(question, text)
        id = uuid.uuid4()
        answer = TestAnswer(id, question_id, text, mark)

        if student_test is None:
            raise Exception('Written test was not found')
        student_test.answers.append(answer)

        self.__written_collection.update_one({ '_id': written_test.id }, {'$set': self.__written_to_document(written_test)})

    def __written_to_document(self, test: WrittenTest) -> dict:
        student_docs = []
        for student_test in test.student_tests:
            doc = { 'id': str(student_test.id),\
                    'finish_time': student_test.finish_time,\
                    'student_id': student_test.student_id,\
                    'variant_id': str(student_test.variant_id),\
                    'sum_mark': student_test.sum_mark }
            answer_docs = []
            for answer in student_test.answers:
                answer_doc = { 'id': str(answer.id),\
                        'question_id': str(answer.question_id),\
                        'value': answer.value,\
                        'mark': answer.mark }
                answer_docs.append(answer_doc)
            doc['answers'] = answer_docs
            student_docs.append(doc)
        return { 'test_id': test.test_id,\
                'start_time': test.start_time,\
                'finish_time': test.finish_time,\
                'student_tests': student_docs }

    def __written_from_document(self, doc: dict) -> WrittenTest:
        students = []
        for student_doc in doc['student_tests']:
            answers = []

            for answer_doc in student_doc['answers']:
                answer = TestAnswer(uuid.UUID(answer_doc['id']),\
                        uuid.UUID(answer_doc['question_id']),\
                        answer_doc['value'],\
                        answer_doc['mark'])
                answers.append(answer)

            student = StudentWrittenTest(uuid.UUID(student_doc['id']),\
                    student_doc['finish_time'],\
                    student_doc['student_id'],\
                    uuid.UUID(student_doc['variant_id']),\
                    answers,\
                    student_doc['sum_mark'])
            students.append(student)

        return WrittenTest(doc['_id'],\
                doc['test_id'],\
                doc['start_time'],\
                doc['finish_time'],\
                students)

    # endregion


    # region Check

    def __check_answer(self,
            question: TestQuestion,
            answer: TestAnswerValue) -> Union[float, None]:
        """Checks test question answer and returns mark if possible"""
        if question.type == TestAnswerType.LECTURE.value:
            return Levenshtein.ratio(\
                    cast(str, question.answer),\
                    cast(str, answer))

        if question.type == TestAnswerType.SINGLE_CHOICE.value:
            return int(question.answer == answer)

        if question.type == TestAnswerType.MULTIPLE_CHOICE.value:
            if question.answer_variants is None:
                raise Exception('Cannot check answer. Answer variants' +\
                        ' are not provided for a MULTIPLE_CHOICE question.')

            correct_answers = []
            student_answers = []
            for i in range(len(question.answer_variants)):
                correct_answers.append(i + 1 in cast(list[int], question.answer))
                student_answers.append(i in cast(list[int], answer))
            variant_count = len(question.answer_variants)
            student_count = 0
            for i in range(variant_count):
                if correct_answers[i] == student_answers[i]:
                    student_count += 1
            return student_count / variant_count

        return None

    def post_finished(self, filename: str) -> WrittenTest:
        """
        Saves updated test results.
        
        Returns written test id.
        """
        updated_test = self.__excel.read_written_test(filename)
        written_test = self.get_written('finish_time', updated_test.date)
        if written_test is None:
            raise Exception('Cannot save test results. Written test was not found')

        for student in updated_test.students:
            student_user = self.__students.get_student('name', student.name)
            if student_user is None:
                raise Exception('Cannot save test results. Student was not found')
            student_test = self.get_student(None, 'student_id', student_user.id, written_test)
            if student_test is None:
                raise Exception('Cannot save test results. Student test was not found')

            student_test.sum_mark = 0
            for i in range(len(student_test.answers)):
                question = self.get_question(written_test.test_id, student_test.variant_id, i)
                if question is None:
                    raise Exception('Cannot save test results. Question was not found')

                mark = student.marks[i]
                if mark is not None:
                    student_test.answers[i].mark = mark / question.max_mark
                student_test.sum_mark += (student_test.answers[i].mark or 0) * question.max_mark

        self.__written_collection.update_one({ '_id': written_test.id },\
                {'$set': self.__written_to_document(written_test)})

        return written_test

    # endregion


    # region Variants

    def get_random_variant(self, test_id: uuid.UUID) -> Union[TestVariant, None]:
        test = self.get('_id', test_id)
        if test is None: return None
        return random.choice(test.variants)

    def get_variant(self,
            test_id: uuid.UUID,
            variant_prop: str,
            value: Any) -> Union[TestVariant, None]:
        test = self.get('_id', test_id)
        if test is None: return None

        return get_from_list(test.variants, variant_prop, value)

    def get_question(self,
            test_id: uuid.UUID,
            variant_id: uuid.UUID,
            index: Union[int, None] = None,
            question_id: Union[uuid.UUID, None] = None) -> Union[TestQuestion, None]:
        variant = self.get_variant(test_id, 'id', variant_id)
        if variant is None: return None

        if question_id is not None:
            question = get_from_list(variant.questions, 'id', question_id)
            if question is not None: return question

        if index is None: return None
        if len(variant.questions) <= index: return None
        return variant.questions[index]

    # endregion
