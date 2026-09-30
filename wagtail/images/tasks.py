from django.apps import apps
from django.db import transaction
from django_tasks import task


@task()
def set_image_focal_point_task(app_label, model_name, pk):
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(pk=pk)
    if instance.has_focal_point():
        return

    suggested = instance.get_suggested_focal_point()
    with transaction.atomic():
        instance = model.objects.select_for_update().get(pk=pk)
        # The editor may have chosen a crop while detection was queued or running.
        if instance.has_focal_point():
            return
        instance.set_focal_point(suggested)

        instance.save(
            update_fields=[
                "focal_point_x",
                "focal_point_y",
                "focal_point_width",
                "focal_point_height",
            ]
        )
