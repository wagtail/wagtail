#!/bin/bash
set -e

# Run database migrations before starting the server.
#
# For production deployments on platforms that support a dedicated
# "release phase" (e.g. Heroku Procfile, Fly.io deploy.yml, Render
# pre-deploy command, Railway start command), set DJANGO_MIGRATE=0 and
# run "python manage.py migrate --noinput" as the release step instead.
# That avoids running migrations on every instance startup and prevents
# race conditions in multi-replica deployments.
if [ "${DJANGO_MIGRATE:-1}" = "1" ]; then
    python manage.py migrate --noinput
fi

exec "$@"
