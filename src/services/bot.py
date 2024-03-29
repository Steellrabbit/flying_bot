import telegram as tg
import telegram.ext as tg_ext

from config import RUNTIME_FOLDER, TESTS_FOLDERNAME, WRITTEN_TESTS_FOLDERNAME

from ..models.test import RawTest
from ..models.user import RawStudent
from ..models.group import RawGroup

from .db import DataBase
from .dialogs import TEST_QUESTION_ID, StudentSettingsBranch, TutorCheckBranch,\
        TutorSettingsBranch, TutorSettingsClearDatabaseOptions, TutorTestBranch, TutorTestSuccessOptions,\
        student_abort_test, student_check_branch, student_exists_branch,\
        student_settings_branch, student_test_branch, tutorStartDialog

class Bot:

    def __init__(self, token: str, db_url: str) -> None:

        self.__updater = tg_ext.Updater(token=token)
        self.__dispatcher = self.__updater.dispatcher
        self.__db = DataBase(db_url)
        self.__dialogs = dict([(user.id, dict()) for user in self.__db.users.get_users()])
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
        self.__send_message(context, tg_user.id, self.__dialogs[tg_user.id]['answer'])
    #endregion

    #region Message handler

    def __message_handler(self, 
                          update: tg.Update,
                          context: tg_ext.CallbackContext) -> None:
        print("\nReceived", update)
        tg_user = update.effective_user

        if not(tg_user.id in self.__dialogs) or not(self.__dialogs[tg_user.id].get('generator', None)):
            return self.__start_command_handler(update, context)

        #handle block
        previousMessageId = self.__dialogs[tg_user.id]['answer'].text.id

        # Введите группы этого семестра списком (элементы разделяйте переносом строки)
        if (previousMessageId == TutorSettingsBranch.ENTER_GROUPS.value.id):
            if update.message.text != '-':
                for name in update.message.text.split('\n'):
                    self.__db.groups.create(RawGroup(name))
        # Загрузите файлы с летучками по этому шаблону. Будьте внимательны, название файла будет названием летучки.
        # или
        # Пришлите файл в формате .xlsx
        elif (previousMessageId in [TutorSettingsBranch.ENTER_TESTS.value.id, TutorSettingsBranch.FILE_FORMAT_ERROR.value.id]):
            if update.message.document:
                self.__download_file(update, context, f'{TESTS_FOLDERNAME}/')
                self.__db.tests.create(RawTest(\
                    f'{RUNTIME_FOLDER}/{TESTS_FOLDERNAME}/' +\
                    update.message.document.file_name))
                return
        
        # База успешно очищена, можно заново настраивать бота.
        elif (previousMessageId == TutorSettingsBranch.CLEAR_DATABASE.value.id):
            if update.message.text == TutorSettingsClearDatabaseOptions.CONFIRM.value:
                self.__db.clear_database()

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
                self.__send_message(context, student_id, self.__dialogs[student_id]['answer'])
        # Летучка началась
        # 
        # Можете остановить летучку кнопкой ниже
        elif (previousMessageId == TutorTestBranch.SUCCESS.value.id):
            if (update.message.text == TutorTestSuccessOptions.STOP.value):
                filename = self.__db.tests.finish(self.__writtenTest.id)
                with open(filename, 'rb') as f:
                    context.bot.sendDocument(chat_id=tg_user.id, document=f)
                student_ids = [test.student_id for test in self.__writtenTest.student_tests]
                for student_id in student_ids:
                    self.__dialogs[student_id]['generator'] = student_abort_test()
                    self.__dialogs[student_id]['answer'] = next(self.__dialogs[student_id]['generator'])
                    self.__send_message(context, student_id, self.__dialogs[student_id]['answer'])
                self.__writtenTest == None


        # Любой вопрос теста
        elif (previousMessageId == TEST_QUESTION_ID):
            student_test = self.__db.tests.get_student(self.__writtenTest.id, 'student_id', tg_user.id)
            question_id = self.__db.tests.get_question(self.__testId, student_test.variant_id, len(student_test.answers)).id
            self.__db.tests.save_answer(tg_user.id, self.__writtenTest.id, question_id, update.message.text)
        

        # Оцените результаты, выставьте баллы в соответствующую графу и пришлите изменённый файл в ответном сообщении
        elif (previousMessageId == TutorCheckBranch.SEND_FILE.value.id):
            if update.message.document:
                self.__download_file(update, context, f'{WRITTEN_TESTS_FOLDERNAME}/')
                finished_test = self.__db.tests.post_finished(\
                        f'{RUNTIME_FOLDER}/{WRITTEN_TESTS_FOLDERNAME}/' +\
                        update.message.document.file_name)
                test_name = self.__db.tests.get('_id', finished_test.test_id).name
                for test in finished_test.student_tests:
                    max_mark = self.__db.tests.get_variant(finished_test.test_id, 'id', test.variant_id).sum_max_mark
                    student_id = test.student_id
                    self.__dialogs[student_id]['generator'] = student_check_branch(test_name, test.sum_mark, max_mark)
                    self.__dialogs[student_id]['answer'] = next(self.__dialogs[student_id]['generator'])
                    self.__send_message(context, student_id, self.__dialogs[student_id]['answer'])
                    





        #answer block
        print('\nUser:', self.__db.users.get_user(tg_user.id))
        
        try:
            self.__dialogs[tg_user.id]['answer'] = self.__dialogs[tg_user.id]['generator'].send(update.message)
        except StopIteration:
            self.__restart_dialog(update, context, tg_user.id)

        print("\nAnswer: %r" % self.__dialogs[tg_user.id]['answer'].text.messages)
        self.__send_message(context, tg_user.id, self.__dialogs[tg_user.id]['answer'])

        #Рестарт диалога, если конец ветки
        sentMessageId = self.__dialogs[tg_user.id]['answer'].text.id
        if  (sentMessageId == TutorSettingsBranch.SUCCESS.value.id) or \
            (sentMessageId == TutorTestBranch.FINISH.value.id) or \
            (sentMessageId == TutorCheckBranch.SUCCESS.value.id) or \
            (sentMessageId == TutorSettingsBranch.CLEAR_DATABASE_SUCCESS.value.id) or \
            (sentMessageId == TutorSettingsBranch.CLEAR_DATABASE_DECLINE.value.id):
            self.__restart_dialog(update, context, tg_user.id)


    #endregion

    #region helpers

    def __send_message(self, context, user_id, answer):
        for message in answer.text.messages:
            context.bot.sendMessage(chat_id=user_id, text=message, reply_markup=answer.markup)

    def __restart_dialog(self, update, context, user_id):
        del self.__dialogs[user_id]
        return self.__message_handler(update, context)

    def __download_file(self, update, context, subpath = ''):
        name = update.message.document.file_name
        with open(f'{RUNTIME_FOLDER}/' + subpath + name, 'wb') as f:
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
