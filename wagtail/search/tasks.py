from django.apps import apps
from django_tasks import task

from wagtail.search import index


@task()
def insert_or_update_object_task(app_label, model_name, pk):
    model = apps.get_model(app_label, model_name)
    index.insert_or_update_object(model.objects.get(pk=pk))
