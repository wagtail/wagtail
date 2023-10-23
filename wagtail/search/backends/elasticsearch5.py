from django.db import models

from wagtail.search.backends.base import (
    get_model_root,
)
from wagtail.search.index import (
    AutocompleteField,
    FilterField,
    Indexed,
    RelatedFields,
    SearchField,
)


class Elasticsearch5Mapping:
    all_field_name = "_all"

    # Was originally named '_partials' but renamed '_edgengrams' when we added Elasticsearch 6 support
    # The ES 5 backend still uses the old name for backwards compatibility
    edgengrams_field_name = "_partials"

    type_map = {
        "AutoField": "integer",
        "BinaryField": "binary",
        "BooleanField": "boolean",
        "CharField": "string",
        "CommaSeparatedIntegerField": "string",
        "DateField": "date",
        "DateTimeField": "date",
        "DecimalField": "double",
        "FileField": "string",
        "FilePathField": "string",
        "FloatField": "double",
        "IntegerField": "integer",
        "BigIntegerField": "long",
        "IPAddressField": "string",
        "GenericIPAddressField": "string",
        "NullBooleanField": "boolean",
        "PositiveIntegerField": "integer",
        "PositiveSmallIntegerField": "integer",
        "SlugField": "string",
        "SmallIntegerField": "integer",
        "TextField": "string",
        "TimeField": "date",
    }

    keyword_type = "keyword"
    text_type = "text"
    set_index_not_analyzed_on_filter_fields = False
    edgengram_analyzer_config = {
        "analyzer": "edgengram_analyzer",
        "search_analyzer": "standard",
    }

    def __init__(self, model):
        self.model = model

    def get_parent(self):
        for base in self.model.__bases__:
            if issubclass(base, Indexed) and issubclass(base, models.Model):
                return type(self)(base)

    def get_document_type(self):
        return self.model.indexed_get_content_type()

    def get_field_column_name(self, field):
        # Fields in derived models get prefixed with their model name, fields
        # in the root model don't get prefixed at all
        # This is to prevent mapping clashes in cases where two page types have
        # a field with the same name but a different type.
        root_model = get_model_root(self.model)
        definition_model = field.get_definition_model(self.model)

        if definition_model != root_model:
            prefix = (
                definition_model._meta.app_label.lower()
                + "_"
                + definition_model.__name__.lower()
                + "__"
            )
        else:
            prefix = ""

        if isinstance(field, FilterField):
            return prefix + field.get_attname(self.model) + "_filter"
        elif isinstance(field, AutocompleteField):
            return prefix + field.get_attname(self.model) + "_edgengrams"
        elif isinstance(field, SearchField):
            return prefix + field.get_attname(self.model)
        elif isinstance(field, RelatedFields):
            return prefix + field.field_name

    def get_content_type(self):
        """
        Returns the content type as a string for the model.

        For example: "wagtailcore.Page"
                     "myapp.MyModel"
        """
        return self.model._meta.app_label + "." + self.model.__name__

    def get_all_content_types(self):
        """
        Returns all the content type strings that apply to this model.
        This includes the models' content type and all concrete ancestor
        models that inherit from Indexed.

        For example: ["myapp.MyPageModel", "wagtailcore.Page"]
                     ["myapp.MyModel"]
        """
        # Add our content type
        content_types = [self.get_content_type()]

        # Add all ancestor classes content types as well
        ancestor = self.get_parent()
        while ancestor:
            content_types.append(ancestor.get_content_type())
            ancestor = ancestor.get_parent()

        return content_types

    def get_field_mapping(self, field):
        if isinstance(field, RelatedFields):
            mapping = {"type": "nested", "properties": {}}
            nested_model = field.get_field(self.model).related_model
            nested_mapping = type(self)(nested_model)

            for sub_field in field.fields:
                sub_field_name, sub_field_mapping = nested_mapping.get_field_mapping(
                    sub_field
                )
                mapping["properties"][sub_field_name] = sub_field_mapping

            return self.get_field_column_name(field), mapping
        else:
            mapping = {"type": self.type_map.get(field.get_type(self.model), "string")}

            if isinstance(field, SearchField):
                if mapping["type"] == "string":
                    mapping["type"] = self.text_type

                if field.boost:
                    mapping["boost"] = field.boost

                mapping["include_in_all"] = True

            if isinstance(field, AutocompleteField):
                mapping["type"] = self.text_type
                mapping["include_in_all"] = False
                mapping.update(self.edgengram_analyzer_config)

            elif isinstance(field, FilterField):
                if mapping["type"] == "string":
                    mapping["type"] = self.keyword_type

                if self.set_index_not_analyzed_on_filter_fields:
                    # Not required on ES5 as that uses the "keyword" type for
                    # filtered string fields
                    mapping["index"] = "not_analyzed"

                mapping["include_in_all"] = False

            if "es_extra" in field.kwargs:
                for key, value in field.kwargs["es_extra"].items():
                    mapping[key] = value

            return self.get_field_column_name(field), mapping

    def get_mapping(self):
        # Make field list
        fields = {
            "pk": {"type": self.keyword_type, "store": True, "include_in_all": False},
            "content_type": {"type": self.keyword_type, "include_in_all": False},
            self.edgengrams_field_name: {
                "type": self.text_type,
                "include_in_all": False,
            },
        }
        fields[self.edgengrams_field_name].update(self.edgengram_analyzer_config)

        if self.set_index_not_analyzed_on_filter_fields:
            # Not required on ES5 as that uses the "keyword" type for
            # filtered string fields
            fields["pk"]["index"] = "not_analyzed"
            fields["content_type"]["index"] = "not_analyzed"

        fields.update(
            {
                self.get_field_mapping(field)[0]: self.get_field_mapping(field)[1]
                for field in self.model.get_search_fields()
            }
        )

        return {
            self.get_document_type(): {
                "properties": fields,
            }
        }

    def get_document_id(self, obj):
        return obj.indexed_get_toplevel_content_type() + ":" + str(obj.pk)

    def _get_nested_document(self, fields, obj):
        doc = {}
        edgengrams = []
        model = type(obj)
        mapping = type(self)(model)

        for field in fields:
            value = field.get_value(obj)
            doc[mapping.get_field_column_name(field)] = value

            # Check if this field should be added into _edgengrams
            if isinstance(field, AutocompleteField):
                edgengrams.append(value)

        return doc, edgengrams

    def get_document(self, obj):
        # Build document
        doc = {"pk": str(obj.pk), "content_type": self.get_all_content_types()}
        edgengrams = []
        for field in self.model.get_search_fields():
            value = field.get_value(obj)

            if isinstance(field, RelatedFields):
                if isinstance(value, (models.Manager, models.QuerySet)):
                    nested_docs = []

                    for nested_obj in value.all():
                        nested_doc, extra_edgengrams = self._get_nested_document(
                            field.fields, nested_obj
                        )
                        nested_docs.append(nested_doc)
                        edgengrams.extend(extra_edgengrams)

                    value = nested_docs
                elif isinstance(value, models.Model):
                    value, extra_edgengrams = self._get_nested_document(
                        field.fields, value
                    )
                    edgengrams.extend(extra_edgengrams)
            elif isinstance(field, FilterField):
                if isinstance(value, (models.Manager, models.QuerySet)):
                    value = list(value.values_list("pk", flat=True))
                elif isinstance(value, models.Model):
                    value = value.pk
                elif isinstance(value, (list, tuple)):
                    value = [
                        item.pk if isinstance(item, models.Model) else item
                        for item in value
                    ]

            doc[self.get_field_column_name(field)] = value

            # Check if this field should be added into _edgengrams
            if isinstance(field, AutocompleteField):
                edgengrams.append(value)

        # Add partials to document
        doc[self.edgengrams_field_name] = edgengrams

        return doc

    def __repr__(self):
        return f"<ElasticsearchMapping: {self.model.__name__}>"
