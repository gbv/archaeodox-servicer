FROM python:3.9-buster

RUN apt update
RUN apt -y install python3-pip git
RUN pip3 install pipenv

WORKDIR /opt/app

COPY * ./

RUN pipenv install --system

ENV FLASK_APP=servicer
ENV FLASK_ENV=development

CMD flask run --host=0.0.0.0
