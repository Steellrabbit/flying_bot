import uuid
from pathlib import Path

import pandas as pd
import xlsxwriter as xls

from ..models.excel import WrittenTestExcel
from ..models.test import RawTest, RawTestQuestion, Test, TestQuestion, TestVariant


class ExcelService():


    # region Reading

    def read_test(self, source: RawTest) -> Test:
        filename = source.filename
        name = Path(filename).stem
        id = uuid.uuid4()

        frame = pd.read_excel(filename, sheet_name=None)
        variants = self.__read_variants(frame)

        return Test(filename, id, name, variants)

    def __read_variants(self, frame: pd.DataFrame) -> list[TestVariant]:
        variants: list[TestVariant] = []

        for sheet_name in frame.keys():
            id = uuid.uuid4()
            name = sheet_name
            sheet: pd.DataFrame = frame[sheet_name]
            questions = self.__read_questions(sheet)

            variant = TestVariant(id, name, questions)
            variants.append(variant)

        return variants

    def __read_questions(self, sheet: pd.DataFrame) -> list[TestQuestion]:
        questions: list[TestQuestion] = []

        for row in sheet.to_dict(orient='records'):
            id = uuid.uuid4()
            text = row['вопрос']
            type = row['тип ответа']
            answer = None if pd.isna(row['ответ']) else row['ответ']
            max_mark = row['макс балл']

            question = RawTestQuestion(id, type, text, answer, max_mark)
            questions.append(question)

        return question

    # endregion


    # region Writing

    def write_written_test(self,
            test: WrittenTestExcel) -> str:
        """Writes test results into excel and returns excel filename"""
        filename = f'${test.name}_{str(test.date)}.xlsx'
        book = xls.Workbook(filename)

        for variant in test.variants:
            sheet = book.add_worksheet(variant.name)
            sheet.write(0, 1, 'вопрос')
            sheet.write(1, 1, 'ответ')

            question_column_offset = 1
            for question in variant.questions:
                sheet.write(0, 1 + question_column_offset, question.question)
                sheet.write(1, 1 + question_column_offset, question.answer)
                sheet.write(0, 1 + question_column_offset + 1, 'балл')
                sheet.write(1, 1 + question_column_offset + 1, question.max_mark.value)
                question_column_offset += 2
            sheet.write(0, 1 + question_column_offset, 'сумма')
            sheet.write(1, 1 + question_column_offset, sum(map(lambda q: q.max_mark.value, variant.questions)))

            student_row_offset = 1
            sheet.write(2, 0, 'студент')
            sheet.write(2, 1, 'группа')
            for student in variant.students:
                sheet.write(2 + student_row_offset, 0, student.name)
                sheet.write(2 + student_row_offset, 1, student.group)
                answer_column_offset = 1
                for answer in student.answers:
                    sheet.write(2 + student_row_offset, 1 + answer_column_offset, answer.text)
                    sheet.write(2 + student_row_offset, 1 + answer_column_offset + 1, answer.mark.value)
                    answer_column_offset += 2
                sheet.write(2 + student_row_offset, 1 + answer_column_offset, sum(map(lambda a: a.mark.value, student.answers)))
                student_row_offset += 1

        sheet = book.add_worksheet('группы')
        row_offset = 0
        for group in test.summary.groups:
            sheet.write(0 + row_offset, 0, group.group)
            sheet.write(0 + row_offset, 1, 'студент')
            sheet.write(0 + row_offset, 2, 'балл')
            row_offset += 1
            student_number = 1
            for student in group.students:
                sheet.write(0 + row_offset, 0, student_number)
                sheet.write(0 + row_offset, 1, student.name)
                sheet.write(0 + row_offset, 2, sum(map(lambda a: a.mark.value, student.answers)))
                student_number += 1
                row_offset += 1
            row_offset += 1

        book.close()
        return filename

    # endregion
