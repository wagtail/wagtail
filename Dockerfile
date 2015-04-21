FROM python:2.7.9
RUN apt-get update -y
RUN apt-get install -y libpq-dev
RUN pip install tox coveralls psycopg2 pillow
WORKDIR /app
ADD requirements-dev.txt /app/
RUN pip install -r /app/requirements-dev.txt
ADD . /app/
RUN python setup.py install
