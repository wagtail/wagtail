FROM python:3.6-stretch
LABEL maintainer="hello@wagtail.io"

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    # Use production settings as default for the runtime.
    DJANGO_SETTINGS_MODULE={{ project_name }}.settings.production \
    # Set the PYTHONPATH so django-admin can be used.
    PYTHONPATH=/app \
    # Set Gunicorn's workers to 2 and its port to 8000 as default.
    WEB_CONCURRENCY=2 \
    PORT=8000 \
    GUNICORN_CMD_ARGS="--access-logfile -"

# Expose Gunicorn's port outside of the container.
EXPOSE 8000

# Install the application server - Gunicorn.
RUN pip install "gunicorn>=19.8,<19.9"

# Install your application's required dependencies.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Don't use the root user.
RUN useradd wagtail
RUN chown -R wagtail .
USER wagtail

# Copy your application's files.
COPY . .

# Collect static assets.
RUN SECRET_KEY=none django-admin collectstatic --noinput --clear

# Migrate the database and start the server.
CMD exec sh -xec "django-admin migrate --noinput && gunicorn {{ project_name }}.wsgi:application"
