from django.apps import apps
from django_tasks import task


@task()
def set_image_focal_point_task(app_label, model_name, pk):
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(pk=pk)
    instance.set_focal_point(instance.get_suggested_focal_point())

    instance.save(
        update_fields=[
            "focal_point_x",
            "focal_point_y",
            "focal_point_width",
            "focal_point_height",
        ]
    )
