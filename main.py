import dotenv

from src.services.bot import Bot


def main() -> None:
    env = dotenv.dotenv_values('.env')
    if env['TELEGRAM_TOKEN'] is None\
            or env['DB_URL'] is None:
        raise Exception('Bot token or database url is not provided in .env')
    
    bot = Bot(env['TELEGRAM_TOKEN'], env['DB_URL']) #, date_format)
    bot.idle()


if __name__ == '__main__':
    main()
