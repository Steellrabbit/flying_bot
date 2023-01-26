FROM docker.io/balaant/iu5-common-python:3
WORKDIR /usr/app

COPY . .
CMD python main.py
