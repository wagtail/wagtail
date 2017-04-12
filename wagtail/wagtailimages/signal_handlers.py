from __future__ import absolute_import, unicode_literals

from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, pre_save

from wagtail.wagtailimages import get_image_model


TRANSACTION_ON_COMMIT_AVAILABLE = (1, 8) < DJANGO_VERSION[:2]
if TRANSACTION_ON_COMMIT_AVAILABLE:
    on_commit_handler = lambda f: transaction.on_commit(f)
else:
    on_commit_handler = lambda f: f()

def post_delete_file_cleanup(instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    on_commit_handler(lambda: instance.file.delete(False))


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
