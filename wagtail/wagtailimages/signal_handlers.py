from django.db.models.signals import post_delete, pre_save
from django.conf import settings

from wagtail.wagtailimages.models import Image, Rendition


def post_delete_file_cleanup(instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


def pre_save_image_feature_detection(instance, **kwargs):
    if getattr(settings, 'WAGTAILIMAGES_FEATURE_DETECTION_ENABLED', False):
        # Make sure the image doesn't already have a focal point
        if not instance.has_focal_point():
            # Set the focal point
            instance.set_focal_point(instance.get_suggested_focal_point())


def register_signal_handlers():
    pre_save.connect(pre_save_image_feature_detection, sender=Image)
    post_delete.connect(post_delete_file_cleanup, sender=Image)
    post_delete.connect(post_delete_file_cleanup, sender=Rendition)
