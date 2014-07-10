from django.contrib.contenttypes.models import ContentType
from django.db import models

SETTING_MODELS = []

SETTING_CONTENT_TYPES = None


def get_setting_content_types():
    global SETTING_CONTENT_TYPES
    if SETTING_CONTENT_TYPES is None:
        SETTING_CONTENT_TYPES = [
            ContentType.objects.get_for_model(model)
            for model in SETTING_MODELS
        ]

    return SETTING_CONTENT_TYPES


def register_setting(model):
    if model not in SETTING_MODELS:
        SETTING_MODELS.append(model)
    return model


class BaseSetting(models.Model):
    site = models.ForeignKey('wagtailcore.Site', unique=True, db_index=True,
                             editable=False)

    class Meta:
        abstract = True

    @classmethod
    def for_site(cls, site):
        instance, created = cls.objects.get_or_create(site=site)
        return instance
