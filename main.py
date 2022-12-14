# import dotenv

import os
import shutil
from src.services.bot import Bot
from src.services.tests import TestsTable
from src.models.test import RawTest



def main() -> None:
    # dotenv.load_dotenv()
    token = '5740305400:AAFrJczOygRrm4208qABXXe5UuLRFoaUSxI' # dotenv.dotenv_values()['telegram_token']
    db_url = 'mongodb://localhost:27017'
    # date_format = dotenv.dotenv_values()['date_format']

    # shutil.rmtree('assets/runtime')
    # os.mkdir('assets/runtime')
    # os.mkdir('assets/runtime/tests')
    # os.mkdir('assets/runtime/results')
    bot = Bot(token, db_url) #, date_format)
    bot.idle()
    # tests = TestsTable()
    # tests.create_test(RawTest('шаблон летучки.xlsx'))


if __name__ == '__main__':
    main()
