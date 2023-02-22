FROM osgeo/gdal
RUN apt update

RUN apt -y install python3-pip
RUN pip3 install pipenv

COPY * ./

RUN pipenv install --system

ENV FLASK_ENV=production

WORKDIR /opt/servicer
CMD waitress-serve --port=5000 app.main:app
