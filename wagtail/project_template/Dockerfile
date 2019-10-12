# Use an official Python runtime as a parent image
FROM python:3.7
LABEL maintainer="hello@wagtail.io"

# Set the working directory to /code/
WORKDIR /code/

# Set environment varibles
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev

RUN useradd wagtail && chown -R wagtail /code
USER wagtail

COPY ./requirements.txt /code/requirements.txt
# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && pip install -r /code/requirements.txt && pip install gunicorn

# Copy the current directory contents into the container at /code/
COPY . /code/

RUN python manage.py migrate

EXPOSE 8000
CMD exec gunicorn {{ project_name }}.wsgi:application --bind 0.0.0.0:8000 --workers 3
