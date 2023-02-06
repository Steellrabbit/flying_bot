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
            'MONGODB_HOST',
            ]
    for key in mandatory_vars:
        if key not in env:
            raise Exception('Mandatory environment variable is not provided ' + key)
    db_uri = f'mongodb://{env["MONGODB_USERNAME"]}:{env["MONGODB_PASSWORD"]}@{env["MONGODB_HOST"]}:27017/{env["MONGODB_DATABASE"]}?authSource=admin'
        
    # Для локального подъёма закомментить mandatory_vars и заменить db_uri на
    # db_uri = f'mongodb://{env["MONGODB_HOST"]}:27017/{env["MONGODB_DATABASE"]}?authSource=admin'
    
    bot = Bot(env['TELEGRAM_TOKEN'], db_uri)
    bot.idle()


if __name__ == '__main__':
    main()
