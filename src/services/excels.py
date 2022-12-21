import uuid
from pathlib import Path

import pandas as pd
import xlsxwriter as xls

from ..models.excel import WrittenTestExcel,\
        WrittenTestQuestionData,\
        WrittenTestStudentData,\
        UpdatedTestExcel,\
        UpdatedStudentData
from ..models.test import RawTest,\
        RawTestQuestion,\
        Test,\
        TestQuestion,\
        TestVariant,\
        TestAnswerType


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
            sum_max_mark = sum(map(lambda q: q.max_mark, questions))

            variant = TestVariant(id, name, questions, sum_max_mark)
            variants.append(variant)

        return variants

    def __read_questions(self, sheet: pd.DataFrame) -> list[TestQuestion]:
        questions: list[TestQuestion] = []

        for row in sheet.to_dict(orient='records'):
            id = uuid.uuid4()

            text = row['вопрос']
            answer_variants = None
            type = row['тип ответа']
            if type == TestAnswerType.MULTIPLE_CHOICE.value\
                    or type == TestAnswerType.SINGLE_CHOICE.value:
                text = text.split('\n')
                answer_variants = text[1:]
                text = text[0]

            answer = None if pd.isna(row['ответ']) else row['ответ']
            if type == TestAnswerType.MULTIPLE_CHOICE.value:
                answer = map(lambda a: int(a.strip()), answer.split(','))
            elif type == TestAnswerType.SINGLE_CHOICE.value:
                answer = int(answer)

            max_mark = row['макс балл']

            question = RawTestQuestion(id, type, text, answer_variants, answer, max_mark)
            questions.append(question)

        return questions

    def read_written_test(self, filename: str) -> UpdatedTestExcel:
        name = Path(filename).stem
        test_name, test_date = name.split('_')
        student_datas: list[UpdatedStudentData] = []

        frame = pd.read_excel(filename, sheet_name=None)
        for sheet_name in list(frame.keys())[:-1]:
            sheet_frame = frame[sheet_name]
            student_rows = [sheet_frame.columns.tolist()] + sheet_frame.values.tolist()
            if (len(student_rows) <= 3):
                continue

            for student_row in student_rows[3:]:
                student_name = student_row[0]
                marks = student_row[3:-1:2]
                student_data = UpdatedStudentData(student_name, marks)
                student_datas.append(student_data)
        return UpdatedTestExcel(test_name, test_date, student_datas)


    # endregion


    # region Writing

    def write_written_test(self,
            test: WrittenTestExcel) -> str:
        """Writes test results into excel and returns excel filename"""
        filename = f'assets/runtime/results/{test.name}_{test.date}.xlsx'
        book = xls.Workbook(filename)

        student_mark_cells = dict()
        for variant in test.variants:
            sheet = book.add_worksheet(variant.name)
            self.__write_questions(sheet, variant.questions)
            mark_cells = self.__write_students(sheet, variant.students, len(variant.questions))
            for key in mark_cells.keys():
                student_mark_cells[key] = { 'mark_cell': mark_cells[key], 'sheet': variant.name }

        sheet = book.add_worksheet('группы')
        row_offset = 0
        for group in test.summary.groups:
            sheet.write(0 + row_offset, 0, group.group)
            sheet.write(0 + row_offset, 1, 'студент')
            sheet.write(0 + row_offset, 2, 'балл')
            row_offset += 1
            student_number = 1
            for student in group.students:
                mark_cell = sum_mark_cells[str(student.id)]
                sheet.write(0 + row_offset, 0, student_number)
                sheet.write(0 + row_offset, 1, student.name)
                sheet.write_formula(0 + row_offset, 2, f"'{mark_cell['sheet']}'!{mark_cell['mark_cell']}")
                student_number += 1
                row_offset += 1
            row_offset += 1

        book.close()
        return filename

    def __write_questions(self,
            sheet: xls.worksheet.Worksheet,
            questions: list[WrittenTestQuestionData]) -> None:
        sheet.write('B1', 'вопрос')
        sheet.write('B2', 'ответ')

        col_offset = 1
        mark_cells = []
        for question in questions:
            sheet.write(0, 1 + col_offset, question.question)
            sheet.write(1, 1 + col_offset, question.answer)

            sheet.write(0, 1 + col_offset + 1, 'балл')
            mark_cell = xls.utility.xl_rowcol_to_cell(1, 1 + col_offset + 1)
            mark_cells.append(mark_cell)
            sheet.write(mark_cell, question.max_mark.value)

            col_offset += 2

        sheet.write(0, 1 + col_offset, 'сумма')
        sheet.write(1, 1 + col_offset, f"=SUM({', '.join(mark_cells)})")

    def __write_students(self,
            sheet: xls.worksheet.Worksheet(),
            students: list[WrittenTestStudentData],
            question_count: int) -> dict[str, str]:
        """
        Writes student test data into excel sheet

        Returns: student.id-sum_mark_cell map
        """
        sheet.write('A3', 'студент')
        sheet.write('B3', 'группа')

        row_offset = 1
        sum_mark_cell_map = dict()
        for student in students:
            sheet.write(2 + row_offset, 0, student.name)
            sheet.write(2 + row_offset, 1, student.group)

            col_offset = 1
            mark_cells = []
            for i in len(range(question_count)):
                answer = student.answers[index].text if i < len(student.answers) else ''
                sheet.write(2 + row_offset, 1 + col_offset, answer)

                mark = student.answers[index].mark if i < len(student.answers) else 0
                mark_cell = xls.utility.xl_rowcol_to_cell(2 + row_offset, 1 + col_offset)
                max_mark_cell = xls.utility.xl_rowcol_to_cell(1, 1 + col_offset)
                mark_cells.append(mark_cell)
                sheet.write_formula(mark_cell, f'={mark} * max_mark_cell')

                col_offset += 2

            sum_mark_cell = xls.utility.xl_rowcol_to_cell(2 + row_offset, 1 + col_offset)
            sheet.write_formula(sum_mark_cell, f"=SUM({', '.join(mark_cells)})")
            sum_mark_cell_map[str(student.id)] = sum_mark_cell

            row_offset += 1
        return sum_mark_cell_map


    # endregion
