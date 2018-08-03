FROM python:3.6
LABEL maintainer="hello@wagtail.io"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev

WORKDIR /code/
COPY . /code/

RUN pip install -r /code/requirements.txt && \
    pip install gunicorn

RUN python manage.py migrate && \
    useradd wagtail && \
    chown -R wagtail /code

USER wagtail

EXPOSE 8000
CMD exec gunicorn {{ project_name }}.wsgi:application --bind 0.0.0.0:8000 --workers 3
