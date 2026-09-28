from django_tasks_db.compat import task_finished, task_started
from due_work_harness import configure
from due_work_harness.integrations.django import django_host
from due_work_harness.integrations.django.receivers import django_receiver_breaker

from wagtail.signals import page_published

# The system under test is Wagtail, its tasks run by django-tasks-db, on Django: bindings must
# reach one of them. Wagtail's migrations seed its root page, default site and root collection,
# so committing cases restore them after each flush. Crash histories fail each receiver of the
# worker's signals and of page_published in turn.
configure(
    django_host(
        production_packages={"wagtail", "django_tasks", "django_tasks_db", "django"},
        lifecycle_proofs=False,
        serialized_rollback=True,
        receiver_breaker=django_receiver_breaker(
            task_started, task_finished, page_published
        ),
    )
)
