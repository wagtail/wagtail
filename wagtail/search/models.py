import datetime

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.db.models.fields import TextField
from django.db.models.fields.related import OneToOneField
from django.db.models.functions import Cast
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from wagtail.search.utils import MAX_QUERY_STRING_LENGTH, normalise_query_string

from .index import class_is_indexed
from .utils import get_descendants_content_types_pks


class Query(models.Model):
    query_string = models.CharField(max_length=MAX_QUERY_STRING_LENGTH, unique=True)

    def save(self, *args, **kwargs):
        # Normalise query string
        self.query_string = normalise_query_string(self.query_string)

        super().save(*args, **kwargs)

    def add_hit(self, date=None):
        if date is None:
            date = timezone.now().date()
        daily_hits, created = QueryDailyHits.objects.get_or_create(
            query=self, date=date
        )
        daily_hits.hits = models.F("hits") + 1
        daily_hits.save()

    def __str__(self):
        return self.query_string

    @property
    def hits(self):
        hits = self.daily_hits.aggregate(models.Sum("hits"))["hits__sum"]
        return hits if hits else 0

    @classmethod
    def garbage_collect(cls):
        """
        Deletes all Query records that have no daily hits or editors picks
        """
        extra_filter_kwargs = (
            {
                "editors_picks__isnull": True,
            }
            if hasattr(cls, "editors_picks")
            else {}
        )
        cls.objects.filter(daily_hits__isnull=True, **extra_filter_kwargs).delete()

    @classmethod
    def get(cls, query_string):
        return cls.objects.get_or_create(
            query_string=normalise_query_string(query_string)
        )[0]

    @classmethod
    def get_most_popular(cls, date_since=None):
        # TODO: Implement date_since
        return (
            cls.objects.filter(daily_hits__isnull=False)
            .annotate(_hits=models.Sum("daily_hits__hits"))
            .distinct()
            .order_by("-_hits")
        )


class QueryDailyHits(models.Model):
    query = models.ForeignKey(
        Query, db_index=True, related_name="daily_hits", on_delete=models.CASCADE
    )
    date = models.DateField()
    hits = models.IntegerField(default=0)

    @classmethod
    def garbage_collect(cls, days=None):
        """
        Deletes all QueryDailyHits records that are older than a set number of days
        """
        days = (
            getattr(settings, "WAGTAILSEARCH_HITS_MAX_AGE", 7) if days is None else days
        )
        min_date = timezone.now().date() - datetime.timedelta(days)

        cls.objects.filter(date__lt=min_date).delete()

    class Meta:
        unique_together = (("query", "date"),)
        verbose_name = _("Query Daily Hits")
        verbose_name_plural = _("Query Daily Hits")


class TextIDGenericRelation(GenericRelation):
    auto_created = True

    def get_content_type_lookup(self, alias, remote_alias):
        field = self.remote_field.model._meta.get_field(self.content_type_field_name)
        return field.get_lookup("in")(
            field.get_col(remote_alias), get_descendants_content_types_pks(self.model)
        )

    def get_object_id_lookup(self, alias, remote_alias):
        from_field = self.remote_field.model._meta.get_field(self.object_id_field_name)
        to_field = self.model._meta.pk
        return from_field.get_lookup("exact")(
            from_field.get_col(remote_alias), Cast(to_field.get_col(alias), from_field)
        )

    def get_extra_restriction(self, where_class, alias, remote_alias):
        cond = where_class()
        cond.add(self.get_content_type_lookup(alias, remote_alias), "AND")
        cond.add(self.get_object_id_lookup(alias, remote_alias), "AND")
        return cond

    def resolve_related_fields(self):
        return []


class BaseIndexEntry(models.Model):
    """
    This is an abstract class that only contains fields common to all database vendors.
    It should be extended by the models specific for each backend.
    """

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    # We do not use an IntegerField since primary keys are not always integers.
    object_id = models.CharField(max_length=50)
    content_object = GenericForeignKey()

    # TODO: Add per-object boosting.
    # This field stores the "Title Normalisation Factor"
    # This factor is multiplied onto the the rank of the title field.
    # This allows us to apply a boost to results with shorter titles
    # elevating more specific matches to the top.
    title_norm = models.FloatField(default=1.0)

    class Meta:
        unique_together = ("content_type", "object_id")
        verbose_name = _("index entry")
        verbose_name_plural = _("index entries")
        abstract = True

    def __str__(self):
        return "%s: %s" % (self.content_type.name, self.content_object)

    @property
    def model(self):
        return self.content_type.model

    @classmethod
    def add_generic_relations(cls):
        for model in apps.get_models():
            if class_is_indexed(model):
                TextIDGenericRelation(cls).contribute_to_class(model, "index_entries")


# AbstractIndexEntry will be defined depending on which database system we're using.
if connection.vendor == 'postgresql':
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.search import SearchVectorField

    class AbstractPostgresIndexEntry(BaseIndexEntry):
        """
        This class is the specific IndexEntry model for PostgreSQL database systems.
        It inherits the fields defined in BaseIndexEntry, and adds PostgreSQL-specific
        fields (tsvectors), plus indexes for doing full-text search on those fields.
        """

        # TODO: Add per-object boosting.
        autocomplete = SearchVectorField()
        title = SearchVectorField()
        body = SearchVectorField()

        class Meta(BaseIndexEntry.Meta):
            abstract = True
            # An additional computed GIN index on 'title || body' is created in a SQL migration
            # covers the default case of PostgresSearchQueryCompiler.get_index_vectors.
            indexes = [
                GinIndex(fields=["autocomplete"]),
                GinIndex(fields=["title"]),
                GinIndex(fields=["body"]),
            ]

    AbstractIndexEntry = AbstractPostgresIndexEntry

elif connection.vendor == 'sqlite':

    class AbstractSQLiteIndexEntry(BaseIndexEntry):
        """
        This class is the specific IndexEntry model for SQLite database systems. The autocomplete, title, and body fields store additional
        """

        autocomplete = TextField(null=True)
        title = TextField(null=False)
        body = TextField(null=True)

        class Meta(BaseIndexEntry.Meta):
            abstract = True

    AbstractIndexEntry = AbstractSQLiteIndexEntry

    class SQLiteFTSIndexEntry(models.Model):
        autocomplete = TextField(null=True)
        title = TextField(null=False)
        body = TextField(null=True)
        index_entry = OneToOneField(primary_key=True, to='wagtailsearch.indexentry', on_delete=models.CASCADE, db_column='rowid')

        class Meta:
            db_table = "wagtailsearch_indexentry_fts"

elif connection.vendor == 'mysql':

    class AbstractMySQLIndexEntry(BaseIndexEntry):
        """
        This class is the specific IndexEntry model for MySQL database systems.
        """

        autocomplete = TextField(null=True)
        title = TextField(null=False)
        body = TextField(null=True)

        class Meta(BaseIndexEntry.Meta):
            abstract = True

    AbstractIndexEntry = AbstractMySQLIndexEntry

else:
    AbstractIndexEntry = BaseIndexEntry


class IndexEntry(AbstractIndexEntry):
    """
    The IndexEntry model that will get created in the database.
    """
    class Meta(AbstractIndexEntry.Meta):
        """
        Contains everything in the AbstractIndexEntry Meta class, but makes this model concrete.
        """
        abstract = False
