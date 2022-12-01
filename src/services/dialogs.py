from enum import Enum
from typing import List
from telegram import ReplyKeyboardMarkup

from ..models.group import Group

class DialogAnswer():
    def __init__(self, text: str, markup: ReplyKeyboardMarkup = None):
        self.text = text
        self.markup = markup

class TutorDialogOptions(Enum):
    SETTINGS = "Настроить бота"
    START = "Начать летучку"
    CHECK = "Проверить летучки"

class TutorSettingsBranch(Enum):
    ENTER_GROUPS = "Введите группы этого семестра списком (элементы разделяйте переносом строки)"
    ENTER_TESTS = "Загрузите файлы с летучками по этому шаблону. Будьте внимательны, название файла будет названием летучки."
    SUCCESS = "Настройка завершена"

class StudentSettingsBranch(Enum):
    SELECT_GROUP = "Привет!\n Из какой ты группы?"
    ENTER_FIO = "Введи своё ФИО"
    SUCCESS = "Добро пожаловать в Летучий бот. Здесь ты будешь выполнять летучки по предмету МППР \nЖди сообщения о начале летучки"

def create_keyboard(buttons: list[list[str]]):
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def ask_file(question):
    answer = yield DialogAnswer(question)
    while not ('.xlsx' in answer.document.file_name):
        answer = yield DialogAnswer("Пришлите файл в формате .xlsx")
    return True

def tutorStartDialog():
    answer = yield DialogAnswer("Здравствуйте \nЧто необходимо сделать?", create_keyboard([[option.value for option in TutorDialogOptions]]))
    if answer.text == TutorDialogOptions.SETTINGS.value:
        yield from tutor_settings_branch()
    else:
        yield DialogAnswer("Я пока так не умею, но скоро обязательно научусь ;)")

def student_settings_branch(groups: List[Group]):
    yield DialogAnswer(StudentSettingsBranch.SELECT_GROUP.value, create_keyboard([[group.name for group in groups]]))
    yield DialogAnswer(StudentSettingsBranch.ENTER_FIO.value)
    yield DialogAnswer(StudentSettingsBranch.SUCCESS.value)

def tutor_settings_branch():
    yield DialogAnswer(TutorSettingsBranch.ENTER_GROUPS.value)
    yield from ask_file(TutorSettingsBranch.ENTER_TESTS.value)
    yield DialogAnswer(TutorSettingsBranch.SUCCESS.value)
