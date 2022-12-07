from enum import Enum
from typing import List
import uuid
from telegram import ReplyKeyboardMarkup

from ..models.group import Group
from ..models.test import Test, TestQuestion

class DialogAnswerText():
    def __init__(self, messages: str | List[str]):
        if type(messages) is str:
            self.messages = [messages]
        else:
            self.messages = messages
        self.id = uuid.uuid4()
class DialogAnswer():
    def __init__(self, text: DialogAnswerText, markup: ReplyKeyboardMarkup = None):
        self.text = text
        self.markup = markup

class TutorDialogOptions(Enum):
    SETTINGS = "Настроить бота"
    TEST = "Начать летучку"
    CHECK = "Проверить летучки"

class TutorSettingsEnterTestsOptions(Enum):
    FINISH = "Загрузил все летучки"
class TutorTestSuccessOptions(Enum):
    STOP = "Остановить летучку"

class TutorStartDialog(Enum):
    HELLO = DialogAnswerText("Здравствуйте \nЧто необходимо сделать?")
class TutorSettingsBranch(Enum):
    ENTER_GROUPS = DialogAnswerText("Введите группы этого семестра списком (элементы разделяйте переносом строки)")
    ENTER_TESTS = DialogAnswerText("Загрузите файлы с летучками по этому шаблону. Будьте внимательны, название файла будет названием летучки.")
    MORE_TESTS = DialogAnswerText("Вы можете загрузить ещё файлы, либо завершить настройку.")
    FILE_FORMAT_ERROR = DialogAnswerText("Пришлите файл в формате .xlsx")
    SUCCESS = DialogAnswerText("Настройка завершена")

class TutorTestBranch(Enum):
    SELECT_TEST = DialogAnswerText("Выберите летучку")
    SELECT_GROUP = DialogAnswerText("Выберете группу")
    SUCCESS = DialogAnswerText(["Летучка началась", "Можете остановить летучку кнопкой ниже"])

class StudentSettingsBranch(Enum):
    SELECT_GROUP = DialogAnswerText("Привет!\n Из какой ты группы?")
    ENTER_FIO = DialogAnswerText("Введи своё ФИО")
    SUCCESS = DialogAnswerText(["Добро пожаловать в Летучий бот. Здесь ты будешь выполнять летучки по предмету МППР", "Жди сообщения о начале летучки"])

def create_keyboard(buttons: list[list[str]]):
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def ask_file(question): #deprecated - Пока не придумал, как использовать для множественных файлов
    answer = yield question
    while not ('.xlsx' in answer.document.file_name):
        answer = yield DialogAnswer(TutorSettingsBranch.FILE_FORMAT_ERROR.value)
    return True

def tutorStartDialog(tests: List[Test], groups: List[Group]):
    answer = yield DialogAnswer(TutorStartDialog.HELLO.value, create_keyboard([[option.value for option in TutorDialogOptions]]))
    if answer.text == TutorDialogOptions.SETTINGS.value:
        yield from tutor_settings_branch()
    elif answer.text == TutorDialogOptions.TEST.value:
        yield from tutor_test_branch(tests, groups)
    else:
        yield DialogAnswer(DialogAnswerText("Я пока так не умею, но скоро обязательно научусь ;)"))

def tutor_settings_branch():
    yield DialogAnswer(TutorSettingsBranch.ENTER_GROUPS.value)
    answer = yield DialogAnswer(TutorSettingsBranch.ENTER_TESTS.value, create_keyboard([[option.value for option in TutorSettingsEnterTestsOptions]]))
    while not(answer.text == TutorSettingsEnterTestsOptions.FINISH.value):
        answer = yield DialogAnswer([])
    yield DialogAnswer(TutorSettingsBranch.SUCCESS.value)

def tutor_test_branch(tests: List[Test], groups: List[Group]):
    yield DialogAnswer(TutorTestBranch.SELECT_TEST.value, create_keyboard([[test.name for test in tests]]))
    yield DialogAnswer(TutorTestBranch.SELECT_GROUP.value, create_keyboard([[group.name for group in groups]]))
    yield DialogAnswer(TutorTestBranch.SUCCESS.value, create_keyboard([[option.value for option in TutorTestSuccessOptions]]))

def student_settings_branch(groups: List[Group]):
    yield DialogAnswer(StudentSettingsBranch.SELECT_GROUP.value, create_keyboard([[group.name for group in groups]]))
    yield DialogAnswer(StudentSettingsBranch.ENTER_FIO.value)
    yield DialogAnswer(StudentSettingsBranch.SUCCESS.value)

def student_test_branch(questions: List[TestQuestion]):
    for question in questions:
        yield DialogAnswer(DialogAnswerText(question.text))