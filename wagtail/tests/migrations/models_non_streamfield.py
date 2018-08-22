from django.apps.registry import Apps
from django.db import models

from wagtail.core.blocks import RichTextBlock
from wagtail.core.fields import StreamField


class StreamModel(models.Model):
    body = StreamField([("section", RichTextBlock())])
    title = models.TextField(blank=True)

    class Meta:
        # Disable auto loading of this model as we load it on our own
        apps = Apps()
