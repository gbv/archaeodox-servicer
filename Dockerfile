FROM osgeo/gdal
RUN apt update

RUN apt -y install python3-pip
RUN pip3 install pipenv

COPY * ./

RUN pipenv install --system

ENV FLASK_APP=servicer
ENV FLASK_ENV=development

WORKDIR /opt/app
CMD flask run --host=0.0.0.0
