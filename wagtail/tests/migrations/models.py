from django.apps.registry import Apps
from django.db import models
from wagtail.core.fields import StreamField
from .blocks import SectionBlock


class StreamModel(models.Model):
    body = StreamField([("section", SectionBlock())])

    class Meta:
        # Disable auto loading of this model as we load it on our own
        apps = Apps()
