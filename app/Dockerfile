FROM python:3.9-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/usr/src/app

RUN apt-get update --fix-missing && apt-get install -y -f \
    && apt-get install build-essential python-dev -y

COPY . .

RUN python3 -m pip install --upgrade pip \
    && pip install -r requirements.txt --no-cache-dir \
    && rm requirements.txt
