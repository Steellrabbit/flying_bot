import os
import dotenv

from src.services.bot import Bot


def main() -> None:
    dotenv.load_dotenv()
    env = os.environ
    mandatory_vars = [
            'TELEGRAM_TOKEN',
            'MONGODB_DATABASE',
            'MONGODB_USERNAME',
            'MONGODB_PASSWORD',
            'MONGODB_HOSTNAME',
            ]
    for key in mandatory_vars:
        if key not in env:
            raise Exception('One of mandatory environment variables is not provided')
    db_uri = f'mongodb://{env["MONGODB_USERNAME"]}:{env["MONGODB_PASSWORD"]}@{env["MONGODB_HOST"]}:27017/{env["MONGODB_DATABASE"]}?authSource=admin'
    
    bot = Bot(env['TELEGRAM_TOKEN'], db_uri)
    bot.idle()


if __name__ == '__main__':
    main()
