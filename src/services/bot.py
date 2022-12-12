import telegram as tg
import telegram.ext as tg_ext

from ..models.user import RawStudent
from ..models.group import RawGroup
from .db import DataBase
from .dialogs import StudentSettingsBranch, TutorSettingsBranch, student_settings_branch, tutorStartDialog

class Bot:

    def __init__(self, token: str) -> None:

        self.__updater = tg_ext.Updater(token=token)
        self.__dispatcher = self.__updater.dispatcher
        self.__db = DataBase()
        self.__dialogs = dict()
        self.__answers = dict()
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

        if (not self.__db.users.has_tutor()):
            self.__db.users.create_tutor(tg_user.id)


        if (self.__db.users.get_user(tg_user.id) != None and self.__db.users.get_user(tg_user.id).is_tutor):
            self.__dialogs[tg_user.id] = tutorStartDialog()
        else:
            self.__dialogs[tg_user.id] = student_settings_branch(self.__db.groups.get_groups())
        
        self.__answers[tg_user.id] = next(self.__dialogs[tg_user.id])
        context.bot.sendMessage(chat_id=tg_user.id, text=self.__answers[tg_user.id].text, reply_markup=self.__answers[tg_user.id].markup)
    #endregion

    #region Message handler

    def __message_handler(self, 
                          update: tg.Update,
                          context: tg_ext.CallbackContext) -> None:
        print("\nReceived", update.message)
        tg_user = update.effective_user

        #handle block
        if (self.__answers[tg_user.id].text == TutorSettingsBranch.ENTER_GROUPS.value):
            for name in update.message.text.split('\n'):
                self.__db.groups.create_group(RawGroup(name))
        if (self.__answers[tg_user.id].text == TutorSettingsBranch.ENTER_TESTS.value):
            print("\nЭто документ?", update.message.document) # Тут должна быть обработка файла
        
        if (self.__answers[tg_user.id].text == StudentSettingsBranch.SELECT_GROUP.value):
            self.__rawStudents[tg_user.id] = RawStudent(tg_user.id, '', [group.id for group in self.__db.groups.get_groups() if group.name == update.message])
        if (self.__answers[tg_user.id].text == StudentSettingsBranch.ENTER_FIO.value):
            self.__rawStudents[tg_user.id].name = update.message
            self.__db.users.create_student(self.__rawStudents[tg_user.id])

        #answer block
        print('User:')
        if tg_user.id in self.__dialogs:
            try:
                self.__answers[tg_user.id] = self.__dialogs[tg_user.id].send(update.message)
            except StopIteration:
                del self.__dialogs[tg_user.id]
                del self.__answers[tg_user.id]
                return self.__message_handler(update, context)
        else:
            self.__start_command_handler(update, context)

        print("\nAnswer: %r" % self.__answers[tg_user.id].text)
        context.bot.sendMessage(chat_id=tg_user.id, text=self.__answers[tg_user.id].text, reply_markup=self.__answers[tg_user.id].markup)

        

    #endregion

    #region State

    def idle(self) -> None:
        self.__updater.start_polling()
        print('Bot has started')
        self.__updater.idle()

    #endregion
