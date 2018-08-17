FROM python:3.6
LABEL maintainer="hello@wagtail.io"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev

WORKDIR /code/
COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt && \
    pip install gunicorn

COPY . /code/
RUN python manage.py migrate && \
    useradd wagtail && \
    chown -R wagtail /code

USER wagtail

EXPOSE 8000
CMD exec gunicorn {{ project_name }}.wsgi:application --bind 0.0.0.0:8000 --workers 3
