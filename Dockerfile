FROM python:3.11.1-alpine3.17
WORKDIR /app/telegram_bot

RUN apk add --no-cache gcc g++
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
CMD python main.py
