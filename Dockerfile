FROM docker.io/balaant/iu5-common-python:latest
WORKDIR /usr/app

COPY . .
CMD python main.py
