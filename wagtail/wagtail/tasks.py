from django.apps import apps
from django.db import transaction
from django.utils.module_loading import import_string
from django_tasks import task
from modelcluster.fields import ParentalKey

from wagtail.models import ReferenceIndex


@task()
def update_reference_index_task(app_label, model_name, pk):
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(pk=pk)

    # If the model is a child model, find the parent instance and index that instead
    while True:
        parental_keys = list(
            filter(
                lambda field: isinstance(field, ParentalKey),
                instance._meta.get_fields(),
            )
        )
        if not parental_keys:
            break

        instance = getattr(instance, parental_keys[0].name)
        if instance is None:
            # parent is null, so there is no valid object to record references against
            return

    if ReferenceIndex.is_indexed(instance._meta.model):
        with transaction.atomic():
            ReferenceIndex.create_or_update_for_object(instance)


@task()
def delete_file_from_storage_task(deconstructed_storage, path):
    storage_module, storage_args, storage_kwargs = deconstructed_storage
    storage = import_string(storage_module)(*storage_args, **storage_kwargs)

    storage.delete(path)
