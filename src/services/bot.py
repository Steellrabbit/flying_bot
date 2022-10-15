import telegram as tg
import telegram.ext as tg_ext

class Bot:

    def __init__(self, token: str) -> None:

        self.__updater = tg_ext.Updater(token=token)
        self.__dispatcher = self.__updater.dispatcher

        self.__register_handlers()

    def __register_handlers(self) -> None:
        self.__dispatcher.add_handler(tg_ext.CommandHandler('start', self.__start_command_handler))

    #region Command handlers

    def __start_command_handler(self,
                                update: tg.Update,
                                context: tg_ext.CallbackContext) -> None:
        tg_user = update.effective_user

        context.bot.sendMessage(chat_id=tg_user.id,
                                text='Привет! Пока что всё, что я могу - поздороваться, но дальше будет лучше ;)')

    #endregion

    #region State

    def idle(self) -> None:
        self.__updater.start_polling()
        print('Bot has started')
        self.__updater.idle()

    #endregion