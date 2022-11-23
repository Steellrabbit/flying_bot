# import dotenv

from src.services.bot import Bot
from src.services.tests import TestsTable
from src.models.test import RawTest



def main() -> None:
    # dotenv.load_dotenv()
    token = '5740305400:AAFrJczOygRrm4208qABXXe5UuLRFoaUSxI' # dotenv.dotenv_values()['telegram_token']
    # date_format = dotenv.dotenv_values()['date_format']

    #  bot = Bot(token) #, date_format)
    #  bot.idle()
    tests = TestsTable()
    tests.create_test(RawTest('шаблон летучки.xlsx'))


if __name__ == '__main__':
    main()
