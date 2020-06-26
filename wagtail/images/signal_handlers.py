from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, pre_save

from wagtail.images import get_image_model


def post_delete_file_cleanup(instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    transaction.on_commit(lambda: instance.file.delete(False))


def post_delete_purge_rendition_cache(instance, **kwargs):
    instance.purge_from_cache()


def pre_save_image_feature_detection(instance, **kwargs):
    if getattr(settings, 'WAGTAILIMAGES_FEATURE_DETECTION_ENABLED', False):
        # Make sure the image doesn't already have a focal point
        if not instance.has_focal_point():
            # Set the focal point
            instance.set_focal_point(instance.get_suggested_focal_point())


def register_signal_handlers():
    Image = get_image_model()
    Rendition = Image.get_rendition_model()

    pre_save.connect(pre_save_image_feature_detection, sender=Image)
    post_delete.connect(post_delete_file_cleanup, sender=Image)
    post_delete.connect(post_delete_file_cleanup, sender=Rendition)
    post_delete.connect(post_delete_purge_rendition_cache, sender=Rendition)
