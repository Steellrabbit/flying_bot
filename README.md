# Летучий бот

Бот для проведения летучек Ю. Н. Кротова.

## Production

Сборка и развертывание бота производится на базе [Docker
Compose](https://docs.docker.com/compose/install/).

### Определение переменных окружения

В файле `docker-compose.yml` необходимо заменить значения переменных.

Сервис `telegram_bot`:
* `TELEGRAM_TOKEN` &mdash; токен бота в Telegram;
* `MONGODB_PASSWORD` &mdash; пароль пользователя MongoDB.

Сервис `mongodb`:
* `MONGO_INITDB_ROOT_PASSWORD` &mdash; пароль пользователя MongoDB (указанный
  ранее в сервисе `telegram_bot`).

### Запуск

Запуск бота производится командой в корневой директории проекта:
```sh
docker-compose up -d
```

## Development

### Установка

#### Определение переменных окружения

Для работы бота необходимо добавить в корневую директорию проекта файл `.env`
со следующим содержимым:

```python
TELEGRAM_TOKEN="paste your token here"
MONGODB_DATABASE="paste db name here"
MONGODB_USERNAME="paste db username here"
MONGODB_PASSWORD="paste db password here"
MONGODB_HOST="paste db host here"
```

где:
* `TELEGRAM_TOKEN` &mdash; токен бота в Telegram;
* `MONGODB_DATABASE` &mdash; имя базы данных MongoDB;
* `MONGODB_USERNAME` &mdash; имя пользователя MongoDB;
* `MONGODB_PASSWORD` &mdash; пароль пользователя MongoDB;
* `MONGODB_HOST` &mdash; хост, по которому расположена БД MongoDB.

#### Создание виртуального окружения

Создайте виртуальное окружение:

```shell
python3 -m venv .venv
```

Далее, активируйте его:

```shell
. .venv/bin/activate
```

Деактивировать виртуальное окружение можно командой `deactivate`.

Установите зависимости:

```shell
pip3 install -r requirements.txt
```

### Запуск

Чтобы запустить бота, выполните следующее с запущенным виртуальным окружением:

```shell
python3 main.py
```
