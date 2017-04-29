from __future__ import absolute_import, unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchRank, SearchVectorField
from django.db.models import (
    CASCADE, AutoField, BigAutoField, BigIntegerField, F, ForeignKey, IntegerField, Model, QuerySet,
    TextField)
from django.db.models.functions import Cast
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .utils import WEIGHTS_VALUES, get_descendants_content_types_pks


class IndexQuerySet(QuerySet):
    def for_models(self, *models):
        if not models:
            return self.none()
        return self.filter(
            content_type_id__in=get_descendants_content_types_pks(models,
                                                                  self._db))

    def for_object(self, obj):
        db_alias = obj._state.db
        return (self.using(db_alias).for_models(obj._meta.model)
                .filter(object_id=force_text(obj.pk)))

    def add_rank(self, search_query):
        return self.annotate(
            rank=SearchRank(
                F('body_search'), search_query,
                weights='{' + ','.join(map(str, WEIGHTS_VALUES)) + '}'))

    def rank(self, search_query):
        return self.add_rank(search_query).order_by('-rank')

    def annotate_typed_pk(self):
        cast_field = self.model._meta.pk
        if isinstance(cast_field, BigAutoField):
            cast_field = BigIntegerField()
        elif isinstance(cast_field, AutoField):
            cast_field = IntegerField()
        return self.annotate(typed_pk=Cast('object_id', cast_field))

    def pks(self):
        return self.annotate_typed_pk().values_list('typed_pk', flat=True)


@python_2_unicode_compatible
class IndexEntry(Model):
    content_type = ForeignKey(ContentType, on_delete=CASCADE)
    # We do not use an IntegerField since primary keys are not always integers.
    object_id = TextField()
    content_object = GenericForeignKey()

    # TODO: Add per-object boosting.
    body_search = SearchVectorField()

    objects = IndexQuerySet.as_manager()

    class Meta:
        unique_together = ('content_type', 'object_id')
        verbose_name = _('index entry')
        verbose_name_plural = _('index entries')
        # TODO: Move here the GIN index from the migration.

    def __str__(self):
        return '%s: %s' % (self.content_type.name, self.content_object)

    @property
    def model(self):
        return self.content_type.model
