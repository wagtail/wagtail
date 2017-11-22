from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchQuery, SearchVectorField
from django.db.models import CASCADE, ForeignKey, Model, TextField, FloatField
from django.db.models.functions import Cast
from django.utils.translation import ugettext_lazy as _

from ...wagtailsearch.index import class_is_indexed
from .utils import get_descendants_content_types_pks


class SearchAutocomplete(SearchQuery):
    def as_sql(self, compiler, connection):
        params = [self.value]
        if self.config:
            config_sql, config_params = compiler.compile(self.config)
            template = "to_tsquery({}::regconfig, ''%s':*')".format(config_sql)
            params = config_params + [self.value]
        else:
            template = "to_tsquery(''%s':*')"
        if self.invert:
            template = '!!({})'.format(template)
        return template, params


class TextIDGenericRelation(GenericRelation):
    def get_content_type_lookup(self, alias, remote_alias):
        field = self.remote_field.model._meta.get_field(
            self.content_type_field_name)
        return field.get_lookup('in')(
            field.get_col(remote_alias),
            get_descendants_content_types_pks(self.model))

    def get_object_id_lookup(self, alias, remote_alias):
        from_field = self.remote_field.model._meta.get_field(
            self.object_id_field_name)
        to_field = self.model._meta.pk
        return from_field.get_lookup('exact')(
            from_field.get_col(remote_alias),
            Cast(to_field.get_col(alias), from_field))

    def get_extra_restriction(self, where_class, alias, remote_alias):
        cond = where_class()
        cond.add(self.get_content_type_lookup(alias, remote_alias), 'AND')
        cond.add(self.get_object_id_lookup(alias, remote_alias), 'AND')
        return cond

    def resolve_related_fields(self):
        return []


class IndexEntry(Model):
    content_type = ForeignKey(ContentType, on_delete=CASCADE)
    # We do not use an IntegerField since primary keys are not always integers.
    object_id = TextField()
    content_object = GenericForeignKey()

    boost = FloatField(default=1)

    autocomplete = SearchVectorField()
    body = SearchVectorField()

    class Meta:
        unique_together = ('content_type', 'object_id')
        verbose_name = _('index entry')
        verbose_name_plural = _('index entries')
        indexes = [GinIndex(['autocomplete']), GinIndex(['body'])]

    def __str__(self):
        return '%s: %s' % (self.content_type.name, self.content_object)

    @property
    def model(self):
        return self.content_type.model

    @classmethod
    def add_generic_relations(cls):
        for model in apps.get_models():
            if class_is_indexed(model):
                TextIDGenericRelation(cls).contribute_to_class(model,
                                                               'index_entries')
