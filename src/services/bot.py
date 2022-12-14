import telegram as tg
import telegram.ext as tg_ext

from ..models.test import RawTest
from ..models.user import RawStudent
from ..models.group import RawGroup

from .db import DataBase
from .dialogs import TEST_QUESTION_ID, StudentSettingsBranch, TutorSettingsBranch, TutorTestBranch, TutorTestSuccessOptions, student_abort_test, student_exists_branch, student_settings_branch, student_test_branch, tutorStartDialog

class Bot:

    def __init__(self, token: str, db_url: str) -> None:

        self.__updater = tg_ext.Updater(token=token)
        self.__dispatcher = self.__updater.dispatcher
        self.__db = DataBase(db_url)
        self.__dialogs = dict()
        self.__rawStudents = dict()

        self.__register_handlers()

    def __register_handlers(self) -> None:
        self.__dispatcher.add_handler(tg_ext.CommandHandler('start', self.__start_command_handler))
        self.__dispatcher.add_handler(tg_ext.MessageHandler(tg_ext.Filters.text | tg_ext.Filters.document, self.__message_handler))

    #region Command handlers

    def __start_command_handler(self,
                                update: tg.Update,
                                context: tg_ext.CallbackContext) -> None:
        tg_user = update.effective_user
        self.__dialogs[tg_user.id] = dict()

        if (not self.__db.users.has_tutor()):
            self.__db.users.create_tutor(tg_user.id)


        if (self.__db.users.get_user(tg_user.id) != None and self.__db.users.get_user(tg_user.id).is_tutor):
            self.__dialogs[tg_user.id]['generator'] = tutorStartDialog(self.__db.tests.get_all(), self.__db.groups.get_all())
        elif (self.__db.users.get_user(tg_user.id) == None):
            self.__dialogs[tg_user.id]['generator'] = student_settings_branch(self.__db.groups.get_all())
        else:
            self.__dialogs[tg_user.id]['generator'] = student_exists_branch()
        
        self.__dialogs[tg_user.id]['answer'] = next(self.__dialogs[tg_user.id]['generator'])
        for message in self.__dialogs[tg_user.id]['answer'].text.messages:
            context.bot.sendMessage(chat_id=tg_user.id, text=message, reply_markup=self.__dialogs[tg_user.id]['answer'].markup)
    #endregion

    #region Message handler

    def __message_handler(self, 
                          update: tg.Update,
                          context: tg_ext.CallbackContext) -> None:
        print("\nReceived", update, context, sep="\n")
        tg_user = update.effective_user

        if not(tg_user.id in self.__dialogs):
            return self.__start_command_handler(update, context)

        #handle block
        previousMessageId = self.__dialogs[tg_user.id]['answer'].text.id

        # Введите группы этого семестра списком (элементы разделяйте переносом строки)
        # Для пропуска этого шага отправьте '-'
        if (previousMessageId == TutorSettingsBranch.ENTER_GROUPS.value.id):
            if update.message.text != '-':
                for name in update.message.text.split('\n'):
                    self.__db.groups.create(RawGroup(name))
        # Загрузите файлы с летучками по этому шаблону. Будьте внимательны, название файла будет названием летучки.
        # или
        # Пришлите файл в формате .xlsx
        elif (previousMessageId in [TutorSettingsBranch.ENTER_TESTS.value.id, TutorSettingsBranch.FILE_FORMAT_ERROR.value.id]):
            if update.message.document:
                self.__download_file(update, context, 'tests/')
                self.__db.tests.create(RawTest('assets/runtime/tests/' + update.message.document.file_name))
                return

        # Привет!
        # Из какой ты группы?
        elif (previousMessageId == StudentSettingsBranch.SELECT_GROUP.value.id):
            self.__rawStudents[tg_user.id] = RawStudent(tg_user.id, '', self.__db.groups.get('name', update.message.text).id)
        # Введи своё ФИО
        elif (previousMessageId == StudentSettingsBranch.ENTER_FIO.value.id):
            self.__rawStudents[tg_user.id].name = update.message.text
            self.__db.users.create_student(self.__rawStudents[tg_user.id])

        # Выберите летучку
        elif (previousMessageId == TutorTestBranch.SELECT_TEST.value.id):
            self.__testId = self.__db.tests.get('name', update.message.text).id
        # Выберете группу
        elif (previousMessageId == TutorTestBranch.SELECT_GROUP.value.id):
            student_ids = [student.id for student in self.__db.users.get_students(self.__db.groups.get('name', update.message.text).id)]
            self.__writtenTest = self.__db.tests.start(self.__testId, student_ids)
            for student_id in student_ids:
                test_name = self.__db.tests.get('_id', self.__testId).name
                variant_questions = self.__db.tests.get_variant(self.__testId, 'id', self.__db.tests.get_student(self.__writtenTest.id, 'student_id', student_id).variant_id).questions
                # FIXME: если студент в текущем запуске бота не общался с ним, вылетает KeyError
                self.__dialogs[student_id]['generator'] = student_test_branch(test_name, variant_questions)
                self.__dialogs[student_id]['answer'] = next(self.__dialogs[student_id]['generator'])
                for message in self.__dialogs[student_id]['answer'].text.messages:
                    context.bot.sendMessage(chat_id=student_id, text=message, reply_markup=self.__dialogs[student_id]['answer'].markup)
        # Летучка началась
        # 
        # Можете остановить летучку кнопкой ниже
        elif (previousMessageId == TutorTestBranch.SUCCESS.value.id):
            if (update.message.text == TutorTestSuccessOptions.STOP.value):
                filename = self.__db.tests.finish(self.__writtenTest.id)
                print(filename)
                context.bot.sendMessage(chat_id=tg_user.id, text=filename)
                student_ids = [test.student_id for test in self.__writtenTest.student_tests]
                for student_id in student_ids:
                    self.__dialogs[student_id]['generator'] = student_abort_test()
                    self.__dialogs[student_id]['answer'] = next(self.__dialogs[student_id]['generator'])
                    for message in self.__dialogs[student_id]['answer'].text.messages:
                        context.bot.sendMessage(chat_id=student_id, text=message, reply_markup=self.__dialogs[student_id]['answer'].markup)
                self.__writtenTest == None


        # Любой вопрос теста
        elif (previousMessageId == TEST_QUESTION_ID):
            # FIXME: если прервать тест, студенту продолжают задаваться вопросы
            student_test = self.__db.tests.get_student(self.__writtenTest.id, 'student_id', tg_user.id)
            question_id = self.__db.tests.get_question(self.__testId, student_test.variant_id, len(student_test.answers)).id
            self.__db.tests.save_answer(tg_user.id, self.__writtenTest.id, question_id, update.message.text)
        

            



        #answer block
        print('User:', self.__db.users.get_user(tg_user.id))
        
        try:
            self.__dialogs[tg_user.id]['answer'] = self.__dialogs[tg_user.id]['generator'].send(update.message)
        except StopIteration:
            del self.__dialogs[tg_user.id]
            return self.__message_handler(update, context)

        print("\nAnswer: %r" % self.__dialogs[tg_user.id]['answer'].text.messages)
        for message in self.__dialogs[tg_user.id]['answer'].text.messages:
            context.bot.sendMessage(chat_id=tg_user.id, text=message, reply_markup=self.__dialogs[tg_user.id]['answer'].markup)

    #endregion

    #region helpers

    def __download_file(self, update, context, subpath = ''):
        name = update.message.document.file_name
        with open('assets/runtime/' + subpath + name, 'wb') as f:
            context.bot.get_file(update.message.document).download(out=f)

    # def __get_group_id(self, name):
    #     return [group.id for group in self.__db.groups.get_all() if group.name == name][0]

    # def __get_test_id(self, name):
    #     return [test.id for test in self.__db.tests.get_all() if test.name == name][0]
    #endregion

    #region State

    def idle(self) -> None:
        self.__updater.start_polling()
        print('Bot has started')
        self.__updater.idle()

    #endregion
