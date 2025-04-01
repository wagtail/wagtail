from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save

from wagtail.images import get_image_model
from wagtail.tasks import delete_file_from_storage_task

from .tasks import set_image_focal_point_task


def post_delete_file_cleanup(instance, **kwargs):
    transaction.on_commit(
        lambda: delete_file_from_storage_task.enqueue(
            instance.file.storage.deconstruct(), instance.file.name
        )
    )


def post_delete_purge_rendition_cache(instance, **kwargs):
    instance.purge_from_cache()


def post_save_image_feature_detection(instance, **kwargs):
    if getattr(settings, "WAGTAILIMAGES_FEATURE_DETECTION_ENABLED", False):
        # Make sure the image is not from a fixture
        # and the image doesn't already have a focal point
        if kwargs["raw"] is False and not instance.has_focal_point():
            # Set the focal point
            set_image_focal_point_task.enqueue(
                instance._meta.app_label, instance._meta.model_name, str(instance.pk)
            )


def register_signal_handlers():
    Image = get_image_model()
    Rendition = Image.get_rendition_model()

    post_save.connect(post_save_image_feature_detection, sender=Image)
    post_delete.connect(post_delete_file_cleanup, sender=Image)
    post_delete.connect(post_delete_file_cleanup, sender=Rendition)
    post_delete.connect(post_delete_purge_rendition_cache, sender=Rendition)
