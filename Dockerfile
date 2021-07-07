FROM python:3.9-buster
ENV FLASK_APP=servicer

RUN apt update
RUN apt -y install python3-pip git
RUN pip3 install pipenv

WORKDIR /opt/app

COPY * .

RUN pipenv install --system

CMD flask run --host=0.0.0.0
