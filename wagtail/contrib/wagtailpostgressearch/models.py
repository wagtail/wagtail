from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class TSVectorField(models.TextField):
    def db_type(self, connection):
        return 'tsvector'


class IndexedItem(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    content = TSVectorField()

    class Meta:
        unique_together = (
            ('content_type', 'object_id'),
        )
