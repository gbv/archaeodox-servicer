FROM ghcr.io/osgeo/gdal:latest
RUN apt update --fix-missing

ENV PIP_BREAK_SYSTEM_PACKAGES=true
RUN apt -y install python3-pip
RUN pip3 install pipenv

COPY * ./

RUN pipenv install --system

WORKDIR /opt/servicer
CMD waitress-serve --port=5000 app.main:app
