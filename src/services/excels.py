import uuid
from pathlib import Path

import pandas as pd
import xlsxwriter as xls
import xlsxwriter.worksheet as xls_worksheet
import xlsxwriter.utility as xls_utility

from config import BOTTOM_BORDERED_FORMAT, CENTERED_HEADING_FORMAT,\
        COLUMN_BG_COLORED_FORMAT, DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE,\
        HEADING_FORMAT, RIGHT_BORDERED_FORMAT, ROW_BG_COLORED_FORMAT,\
        RUNTIME_FOLDER, WRAPPED_FORMAT, WRITTEN_TESTS_FOLDERNAME

from ..models.excel import WrittenTestExcel, WrittenTestGroup,\
        WrittenTestQuestionData,\
        WrittenTestStudentData,\
        UpdatedTestExcel,\
        UpdatedStudentData
from ..models.test import RawTest,\
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

    def __read_variants(self, frame: dict[str, pd.DataFrame]) -> list[TestVariant]:
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
            if answer is not None:
                if type == TestAnswerType.MULTIPLE_CHOICE.value:
                    answer = list(map(lambda a: int(a.strip()), answer.split(',')))
                elif type == TestAnswerType.SINGLE_CHOICE.value:
                    answer = int(answer)

            max_mark = row['макс балл']

            question = TestQuestion(type, text, answer_variants, answer, max_mark, id)
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
                marks = list(map(lambda mark: None if pd.isna(mark) else float(mark),\
                        student_row[3:-1:2]))
                student_data = UpdatedStudentData(student_name, marks)
                student_datas.append(student_data)
        return UpdatedTestExcel(test_name, test_date, student_datas)


    # endregion


    # region Writing

    def write_written_test(self,
            test: WrittenTestExcel) -> str:
        """Writes test results into excel and returns excel filename"""
        filename = f'{RUNTIME_FOLDER}/{WRITTEN_TESTS_FOLDERNAME}/{test.name}_{test.date}.xlsx'
        book = xls.Workbook(filename)
        book.formats[0].set_font_size(DEFAULT_FONT_SIZE)
        book.formats[0].set_font_name(DEFAULT_FONT_NAME)

        student_mark_cells: dict[str, dict[str, str]] = dict()
        for variant in test.variants:
            sheet = book.add_worksheet(variant.name)
            sheet.freeze_panes(2, 2)
            self.__write_questions(book, sheet, variant.questions)
            mark_cells = self.__write_students(book, sheet, variant.students, len(variant.questions))
            for key in mark_cells.keys():
                student_mark_cells[key] = { 'mark_cell': mark_cells[key], 'sheet': variant.name }

        sheet = book.add_worksheet('Группы')
        self.__write_summary(book, sheet, test.summary.groups, student_mark_cells)

        book.close()
        return filename

    def __write_questions(self,
            book: xls.Workbook,
            sheet: xls_worksheet.Worksheet,
            questions: list[WrittenTestQuestionData]) -> None:
        right_bordered_format = book.add_format(RIGHT_BORDERED_FORMAT)
        column_bg_colored_format = book.add_format(COLUMN_BG_COLORED_FORMAT)
        row_bg_colored_format = book.add_format(ROW_BG_COLORED_FORMAT)

        sheet.set_row(0, None, row_bg_colored_format)
        sheet.set_row(1, None, book.add_format({
            **BOTTOM_BORDERED_FORMAT,
            **ROW_BG_COLORED_FORMAT,
            }))
        sheet.set_column(0, 0, 250, column_bg_colored_format) # Column A
        sheet.set_column(1, 1, 160, book.add_format({
            **RIGHT_BORDERED_FORMAT,
            **COLUMN_BG_COLORED_FORMAT,
            })) # Column B

        sheet.write('B1', 'Вопрос', book.add_format({
            **HEADING_FORMAT,
            **COLUMN_BG_COLORED_FORMAT,
            **RIGHT_BORDERED_FORMAT,
            }))
        sheet.write('B2', 'Ответ', book.add_format({
            **HEADING_FORMAT,
            **COLUMN_BG_COLORED_FORMAT,
            **RIGHT_BORDERED_FORMAT,
            }))

        col_offset = 1
        mark_cells = []
        for question in questions:
            sheet.set_column(1 + col_offset, 1 + col_offset, 350)
            sheet.write(0, 1 + col_offset, question.question, book.add_format({
                **ROW_BG_COLORED_FORMAT,
                **WRAPPED_FORMAT,
                }))
            sheet.write(1, 1 + col_offset, question.answer, book.add_format({
                **ROW_BG_COLORED_FORMAT,
                **WRAPPED_FORMAT,
                }))

            sheet.set_column(1 + col_offset + 1, 1 + col_offset + 1, 45, right_bordered_format)
            sheet.write(0, 1 + col_offset + 1, 'Балл', book.add_format({
                **CENTERED_HEADING_FORMAT,
                **ROW_BG_COLORED_FORMAT,
                **RIGHT_BORDERED_FORMAT,
                }))
            mark_cell = xls_utility.xl_rowcol_to_cell(1, 1 + col_offset + 1)
            mark_cells.append(mark_cell)
            sheet.write(mark_cell, question.max_mark, book.add_format({
                **ROW_BG_COLORED_FORMAT,
                **RIGHT_BORDERED_FORMAT,
                }))

            col_offset += 2

        sheet.set_column(1 + col_offset, 1 + col_offset, 55)
        sheet.write(0, 1 + col_offset, 'Сумма', book.add_format({
            **CENTERED_HEADING_FORMAT,
            **ROW_BG_COLORED_FORMAT,
            }))
        sheet.write(1, 1 + col_offset, f"=SUM({', '.join(mark_cells)})", book.add_format({
            **ROW_BG_COLORED_FORMAT,
            }))

    def __write_students(self,
            book: xls.Workbook,
            sheet: xls_worksheet.Worksheet,
            students: list[WrittenTestStudentData],
            question_count: int) -> dict[str, str]:
        """
        Writes student test data into excel sheet

        Returns: student.id-sum_mark_cell map
        """
        wrapped_format = book.add_format(WRAPPED_FORMAT)
        sheet.write('A3', 'Студент', book.add_format({
            **HEADING_FORMAT,
            **COLUMN_BG_COLORED_FORMAT,
            }))
        sheet.write('B3', 'Группа', book.add_format({
            **HEADING_FORMAT,
            **COLUMN_BG_COLORED_FORMAT,
            }))

        row_offset = 1
        sum_mark_cell_map = dict()
        for student in students:
            sheet.write(2 + row_offset, 0, student.name, book.add_format({
                **COLUMN_BG_COLORED_FORMAT,
                }))
            sheet.write(2 + row_offset, 1, student.group, book.add_format({
                **COLUMN_BG_COLORED_FORMAT,
                }))

            col_offset = 1
            mark_cells = []
            for i in range(question_count):
                answer = student.answers[i].value if i < len(student.answers) else ''

                sheet.write(2 + row_offset, 1 + col_offset, answer, wrapped_format)

                mark = student.answers[i].mark if i < len(student.answers) else 0
                mark_cell = xls_utility.xl_rowcol_to_cell(2 + row_offset, 2 + col_offset)
                max_mark_cell = xls_utility.xl_rowcol_to_cell(1, 2 + col_offset)
                mark_cells.append(mark_cell)
                sheet.write(mark_cell, f'={mark or 0} * {max_mark_cell}')

                col_offset += 2

            sum_mark_cell = xls_utility.xl_rowcol_to_cell(2 + row_offset, 1 + col_offset)
            sheet.write(sum_mark_cell, f"=SUM({', '.join(mark_cells)})")
            sum_mark_cell_map[str(student.id)] = sum_mark_cell

            row_offset += 1
        return sum_mark_cell_map

    def __write_summary(self,
            book: xls.Workbook,
            sheet: xls_worksheet.Worksheet,
            groups: list[WrittenTestGroup],
            mark_cells: dict[str, dict[str, str]]) -> None:
        sheet.set_column(0, 0, 160) # Column A
        sheet.set_column(1, 1, 250) # Column B
        sheet.set_column(2, 2, 45) # Column C

        heading_format = book.add_format(HEADING_FORMAT)
        centered_heading_format = book.add_format(CENTERED_HEADING_FORMAT)

        row_offset = 0
        for group in groups:
            sheet.write(0 + row_offset, 0, group.group, heading_format)
            sheet.write(0 + row_offset, 1, 'Студент', heading_format)
            sheet.write(0 + row_offset, 2, 'Балл', centered_heading_format)

            row_offset += 1
            student_number = 1
            for student in group.students:
                mark_cell = mark_cells[str(student.id)]

                sheet.write(0 + row_offset, 0, student_number)
                sheet.write(0 + row_offset, 1, student.name)
                sheet.write_formula(0 + row_offset, 2, f"'{mark_cell['sheet']}'!{mark_cell['mark_cell']}")

                student_number += 1
                row_offset += 1
            row_offset += 1


    # endregion
