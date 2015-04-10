from django.db import models, connection, transaction
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailsearch.backends.base import BaseSearch, BaseSearchQuery, BaseSearchResults
from wagtail.wagtailsearch import index

from wagtail.contrib.wagtailpostgressearch.models import IndexedItem


def get_content_types(model):
    # Returns the content type objects for the specified model and all of its
    # subclasses
    return ContentType.objects.get_for_models(*[
        child_model for child_model in apps.get_models()
        if child_model == model or issubclass(child_model, model)
    ]).values()


class PostgresSearchQuery(BaseSearchQuery):
    def _process_lookup(self, field, lookup, value):
        return models.Q(**{field.get_attname(self.queryset.model) + '__' + lookup: value})

    def _connect_filters(self, filters, connector, negated):
        if connector == 'AND':
            q = models.Q(*filters)
        elif connector == 'OR':
            q = models.Q(filters[0])
            for fil in filters[1:]:
                q |= fil
        else:
            return

        if negated:
            q = ~q

        return q

    def get_pks(self):
        queryset = self.queryset

        # Filters
        queryset = queryset.filter(self._get_filters_from_queryset())

        indexed_items = IndexedItem.objects.filter(
            object_id__in=queryset.values_list('id'),
            content_type__in=get_content_types(self.queryset.model),
        )

        # Search query
        if self.query_string is not None:
            indexed_items = indexed_items.extra(
                 select={'score': "ts_rank_cd(content, plainto_tsquery('simple', unaccent(%s)))"},
                 select_params=[self.query_string],

                 where=["content @@ plainto_tsquery('simple', unaccent(%s))"],
                 params=[self.query_string],

                 order_by=['-score'],
            )

        return indexed_items.values_list('object_id', flat=True)


class PostgresSearchResults(BaseSearchResults):
    def get_pks(self):
        return self.query.get_pks()[self.start:self.stop]

    def _do_search(self):
        pks = self.get_pks()

        # Initialise results dictionary
        results = dict((str(pk), None) for pk in pks)

        # Find objects in database and add them to dict
        queryset = self.query.queryset.filter(pk__in=pks)
        for obj in queryset:
            results[str(obj.pk)] = obj

        # Return results in order given by search
        return [results[str(pk)] for pk in pks if results[str(pk)]]

    def _do_count(self):
        return self.get_pks().count()


class PostgresSearch(BaseSearch):
    search_query_class = PostgresSearchQuery
    search_results_class = PostgresSearchResults

    def __init__(self, params):
        super(PostgresSearch, self).__init__(params)

    def reset_index(self):
        IndexedItem.objects.all().delete()

    def add_type(self, model):
        pass # Not needed

    def refresh_index(self):
        pass # Not needed

    def add(self, obj):
        model = type(obj)
        content_parts = []

        for field in model.get_search_fields():
            value = field.get_value(obj)

            if isinstance(field, index.SearchField) and value:
                content_parts.append(value)

        content_type = ContentType.objects.get_for_model(type(obj))

        with transaction.atomic():
            IndexedItem.objects.filter(content_type=content_type, object_id=obj.id).delete()

            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO wagtailpostgressearch_indexeditem "
                    "(content_type_id, object_id, content) "
                    "VALUES (%s, %s, to_tsvector('simple', unaccent(%s)))",
                    (content_type.id, obj.id, " ".join(content_parts))
                )

    def add_bulk(self, model, obj_list):
        for obj in obj_list:
            self.add(obj)

    def delete(self, obj):
        content_type = ContentType.objects.get_for_model(type(obj))
        IndexedItem.objects.filter(content_type=content_type, object_id=obj.id).delete()


SearchBackend = PostgresSearch
