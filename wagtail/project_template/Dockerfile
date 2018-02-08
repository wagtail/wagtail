FROM python:3.6
# Uncomment the line below and replace your email address
# LABEL maintainer="your@email.com"

# Enables manage.py output to be visible when using Docker
ENV PYTHONUNBUFFERED 1

# Install requirements
# Copying in requirements.txt separately speeds up subsequent builds
COPY ./requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt
# gunicorn is a deployment choice so it doesn't belong in requirements.txt
RUN pip install gunicorn

# Copy our project files into the image
COPY . /code
WORKDIR /code

# Run wagtail as a non-root user
RUN useradd wagtail
RUN chown -R wagtail /code
USER wagtail

EXPOSE 8000
CMD exec gunicorn {{ project_name }}.wsgi:application --bind 0.0.0.0:8000 --workers 3
