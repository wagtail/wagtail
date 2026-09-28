"""
Wagtail's own test project on PostgreSQL and django-tasks-db.

Everything is Wagtail's (``wagtail.test.settings``) except what makes it a
deployment: a PostgreSQL database from the PG* environment variables, the
database task backend with its tables, media in a scratch directory, and a
frontend cache (a CDN) whose purges are recorded.
"""

import os
import tempfile

from wagtail.test.settings import *  # noqa: F403
from wagtail.test.settings import INSTALLED_APPS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PGDATABASE", "wagtail_due_work"),
        "USER": os.environ.get("PGUSER", "postgres"),
        "PASSWORD": os.environ.get("PGPASSWORD", "postgres"),
        "HOST": os.environ.get("PGHOST", "localhost"),
        "PORT": os.environ.get("PGPORT", "5432"),
    }
}

INSTALLED_APPS = [*INSTALLED_APPS, "django_tasks", "django_tasks_db"]

# Wagtail's background work, run by django-tasks-db's db_worker as in production.
TASKS = {"default": {"BACKEND": "django_tasks_db.DatabaseBackend"}}

MEDIA_ROOT = tempfile.mkdtemp(prefix="wagtail-due-work-media-")

# The CDN in front of the site: its purge API is the external seam.
WAGTAILFRONTENDCACHE = {"cdn": {"BACKEND": "due_work_contract.cdn.RecordingCDN"}}
