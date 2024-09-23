from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models
from django.db.models.fields import TextField
from django.db.models.fields.related import OneToOneField
from django.db.models.functions import Cast
from django.db.models.sql.where import WhereNode
from django.utils.translation import gettext_lazy as _

from .index import class_is_indexed
from .utils import get_descendants_content_types_pks


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

    def get_extra_restriction(self, alias, remote_alias):
        cond = WhereNode()
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
    # This factor is multiplied onto the rank of the title field.
    # This allows us to apply a boost to results with shorter titles
    # elevating more specific matches to the top.
    title_norm = models.FloatField(default=1.0)

    wagtail_reference_index_ignore = True

    class Meta:
        unique_together = ("content_type", "object_id")
        verbose_name = _("index entry")
        verbose_name_plural = _("index entries")
        abstract = True

    def __str__(self):
        return f"{self.content_type.name}: {self.content_object}"

    @property
    def model(self):
        return self.content_type.model

    @classmethod
    def add_generic_relations(cls):
        for model in apps.get_models():
            if class_is_indexed(model):
                TextIDGenericRelation(cls).contribute_to_class(model, "index_entries")


# AbstractIndexEntry will be defined depending on which database system we're using.
if connection.vendor == "postgresql":
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

elif connection.vendor == "sqlite":
    from wagtail.search.backends.database.sqlite.utils import fts5_available

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

    if fts5_available():

        class SQLiteFTSIndexEntry(models.Model):
            autocomplete = TextField(null=True)
            title = TextField(null=False)
            body = TextField(null=True)
            index_entry = OneToOneField(
                primary_key=True,
                to="wagtailsearch.indexentry",
                on_delete=models.CASCADE,
                db_column="rowid",
            )

            class Meta:
                db_table = "wagtailsearch_indexentry_fts"

elif connection.vendor == "mysql":

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
