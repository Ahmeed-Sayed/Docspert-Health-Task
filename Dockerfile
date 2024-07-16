FROM python:3.12
RUN apt-get -y update && apt-get -y upgrade &&  apt-get install -y ffmpeg  && apt-get install -y supervisor
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/
