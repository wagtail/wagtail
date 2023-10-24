from django.db import models
from elasticsearch import NotFoundError
from elasticsearch.helpers import bulk

from wagtail.search.backends.base import (
    get_model_root,
)
from wagtail.search.index import (
    AutocompleteField,
    FilterField,
    Indexed,
    RelatedFields,
    SearchField,
    class_is_indexed,
)


class Field:
    def __init__(self, field_name, boost=1):
        self.field_name = field_name
        self.boost = boost


class Elasticsearch6Mapping:
    all_field_name = "_all_text"
    edgengrams_field_name = "_edgengrams"

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
        return "doc"

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

    def get_boost_field_name(self, boost):
        # replace . with _ to avoid issues with . in field names
        boost = str(float(boost)).replace(".", "_")
        return f"{self.all_field_name}_boost_{boost}"

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
                mapping.update(self.edgengram_analyzer_config)

            elif isinstance(field, FilterField):
                if mapping["type"] == "string":
                    mapping["type"] = self.keyword_type

            if "es_extra" in field.kwargs:
                for key, value in field.kwargs["es_extra"].items():
                    mapping[key] = value

            return self.get_field_column_name(field), mapping

    def get_mapping(self):
        # Make field list
        fields = {
            "pk": {"type": self.keyword_type, "store": True},
            "content_type": {"type": self.keyword_type},
            self.edgengrams_field_name: {"type": self.text_type},
        }
        fields[self.edgengrams_field_name].update(self.edgengram_analyzer_config)

        for field in self.model.get_search_fields():
            key, val = self.get_field_mapping(field)
            fields[key] = val

        # Add _all_text field
        fields[self.all_field_name] = {"type": "text"}

        unique_boosts = set()

        # Replace {"include_in_all": true} with {"copy_to": ["_all_text", "_all_text_boost_2"]}
        def replace_include_in_all(properties):
            for field_mapping in properties.values():
                if "include_in_all" in field_mapping:
                    if field_mapping["include_in_all"]:
                        field_mapping["copy_to"] = self.all_field_name

                        if "boost" in field_mapping:
                            # added to unique_boosts to avoid duplicate fields, or cases like 2.0 and 2
                            unique_boosts.add(field_mapping["boost"])
                            field_mapping["copy_to"] = [
                                field_mapping["copy_to"],
                                self.get_boost_field_name(field_mapping["boost"]),
                            ]
                            del field_mapping["boost"]

                    del field_mapping["include_in_all"]

                if field_mapping["type"] == "nested":
                    replace_include_in_all(field_mapping["properties"])

        replace_include_in_all(fields)
        for boost in unique_boosts:
            fields[self.get_boost_field_name(boost)] = {"type": "text"}

        return {
            self.get_document_type(): {
                "properties": fields,
            }
        }

    def get_document_id(self, obj):
        return str(obj.pk)

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


class Elasticsearch6Index:
    def __init__(self, backend, name):
        self.backend = backend
        self.es = backend.es
        self.mapping_class = backend.mapping_class
        self.name = name

    def put(self):
        self.es.indices.create(self.name, self.backend.settings)

    def delete(self):
        try:
            self.es.indices.delete(self.name)
        except NotFoundError:
            pass

    def exists(self):
        return self.es.indices.exists(self.name)

    def is_alias(self):
        return self.es.indices.exists_alias(name=self.name)

    def aliased_indices(self):
        """
        If this index object represents an alias (which appear the same in the
        Elasticsearch API), this method can be used to fetch the list of indices
        the alias points to.

        Use the is_alias method if you need to find out if this an alias. This
        returns an empty list if called on an index.
        """
        return [
            self.backend.index_class(self.backend, index_name)
            for index_name in self.es.indices.get_alias(name=self.name).keys()
        ]

    def put_alias(self, name):
        """
        Creates a new alias to this index. If the alias already exists it will
        be repointed to this index.
        """
        self.es.indices.put_alias(name=name, index=self.name)

    def add_model(self, model):
        # Get mapping
        mapping = self.mapping_class(model)

        # Put mapping
        self.es.indices.put_mapping(
            # pass update_all_types=True as a workaround to avoid "Can't redefine search field" errors -
            # see https://github.com/wagtail/wagtail/issues/2968
            index=self.name,
            doc_type=mapping.get_document_type(),
            body=mapping.get_mapping(),
            update_all_types=True,
        )

    def add_item(self, item):
        # Make sure the object can be indexed
        if not class_is_indexed(item.__class__):
            return

        # Get mapping
        mapping = self.mapping_class(item.__class__)

        # Add document to index
        self.es.index(
            self.name,
            mapping.get_document_type(),
            mapping.get_document(item),
            id=mapping.get_document_id(item),
        )

    def add_items(self, model, items):
        if not class_is_indexed(model):
            return

        # Get mapping
        mapping = self.mapping_class(model)
        doc_type = mapping.get_document_type()

        # Create list of actions
        actions = []
        for item in items:
            # Create the action
            action = {
                "_type": doc_type,
                "_id": mapping.get_document_id(item),
            }
            action.update(mapping.get_document(item))
            actions.append(action)

        # Run the actions
        bulk(self.es, actions, index=self.name)

    def delete_item(self, item):
        # Make sure the object can be indexed
        if not class_is_indexed(item.__class__):
            return

        # Get mapping
        mapping = self.mapping_class(item.__class__)

        # Delete document
        try:
            self.es.delete(
                self.name,
                mapping.get_document_type(),
                mapping.get_document_id(item),
            )
        except NotFoundError:
            pass  # Document doesn't exist, ignore this exception

    def refresh(self):
        self.es.indices.refresh(self.name)

    def reset(self):
        # Delete old index
        self.delete()

        # Create new index
        self.put()
