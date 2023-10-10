from typing import Any, List, Union

from wagtail.search.index import get_indexed_models
from wagtail.search.query import Fuzzy, MatchAll, Not, Phrase, PlainText

from .elasticsearch5 import (
    Elasticsearch5Index,
    Elasticsearch5Mapping,
    Elasticsearch5SearchBackend,
    Elasticsearch5SearchQueryCompiler,
    Elasticsearch5SearchResults,
    ElasticsearchAutocompleteQueryCompilerImpl,
)


class Field:
    def __init__(self, field_name, boost=1):
        self.field_name = field_name
        self.boost = boost


class Elasticsearch6Mapping(Elasticsearch5Mapping):
    all_field_name = "_all_text"
    edgengrams_field_name = "_edgengrams"

    def get_boost_field_name(self, boost):
        # replace . with _ to avoid issues with . in field names
        boost = str(float(boost)).replace(".", "_")
        return f"{self.all_field_name}_boost_{boost}"

    def get_document_id(self, obj):
        return str(obj.pk)

    def get_document_type(self):
        return "doc"

    def get_mapping(self):
        mapping = super().get_mapping()

        # Add _all_text field
        mapping[self.get_document_type()]["properties"][self.all_field_name] = {
            "type": "text"
        }

        unique_boosts = set()

        # Replace {"include_in_all": true} with {"copy_to": ["_all_text", "_all_text_boost_2"]}
        def replace_include_in_all(mapping):
            for field_mapping in mapping["properties"].values():
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
                    replace_include_in_all(field_mapping)

        replace_include_in_all(mapping[self.get_document_type()])
        for boost in unique_boosts:
            mapping[self.get_document_type()]["properties"][
                self.get_boost_field_name(boost)
            ] = {"type": "text"}

        return mapping


class Elasticsearch6Index(Elasticsearch5Index):
    pass


class Elasticsearch6SearchQueryCompiler(Elasticsearch5SearchQueryCompiler):
    mapping_class = Elasticsearch6Mapping

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = self.to_field_objects(self.fields)
        remapped_fields = self.remapped_fields or [self.to_field(self.mapping.all_field_name)]

        models = get_indexed_models()
        unique_boosts = set()
        for model in models:
            for field in model.get_searchable_search_fields():
                if field.boost:
                    unique_boosts.add(float(field.boost))

        self.remapped_fields = remapped_fields + [
            Field(self.mapping.get_boost_field_name(boost), boost)
            for boost in unique_boosts
        ]

    def _remap_fields(self, fields):
        if fields is None:
            return None

        return self.to_field_objects(super()._remap_fields(fields))

    def get_boosted_fields(self, fields):
        boosted_fields = []
        if not isinstance(fields, list):
            fields = [fields]
        for field in fields:
            if field.boost != 1:
                boosted_fields.append(f"{field.field_name}^{field.boost}")
            else:
                boosted_fields.append(field.field_name)
        return boosted_fields

    def _compile_fuzzy_query(self, query, fields):
        if len(fields) == 1:
            return {
                "match": {
                    self.to_string(fields[0]): {
                        "query": query.query_string,
                        "fuzziness": "AUTO",
                    }
                }
            }
        return {
            "multi_match": {
                "query": query.query_string,
                "fields": self.to_field_names(self.get_boosted_fields(fields)),
                "fuzziness": "AUTO",
            }
        }

    def _compile_plaintext_query(self, query, fields, boost=1.0):
        return super()._compile_plaintext_query(
            query, self.to_field_names(self.get_boosted_fields(fields)), boost
        )

    def _compile_phrase_query(self, query, fields):
        return super()._compile_phrase_query(
            query, self.to_field_names(self.get_boosted_fields(fields))
        )

    def get_inner_query(self):
        fields = self.to_field_objects(self.remapped_fields)

        if len(fields) == 0:
            # No fields. Return a query that'll match nothing
            return {"bool": {"mustNot": {"match_all": {}}}}

        # Handle MatchAll and PlainText separately as they were supported
        # before "search query classes" was implemented and we'd like to
        # keep the query the same as before
        if isinstance(self.query, MatchAll):
            return {"match_all": {}}

        elif isinstance(self.query, PlainText):
            return self._compile_plaintext_query(self.query, fields)

        elif isinstance(self.query, Phrase):
            return self._compile_phrase_query(self.query, fields)

        elif isinstance(self.query, Fuzzy):
            return self._compile_fuzzy_query(self.query, fields)

        elif isinstance(self.query, Not):
            return {
                "bool": {
                    "mustNot": [
                        self._compile_query(self.query.subquery, field)
                        for field in fields
                    ]
                }
            }

        else:
            return self._join_and_compile_queries(self.query, fields)

    # Helpers to manage type-safe transition between field names
    # and field objects stored in e.g. self.fields

    def to_string(self, field: Union[str, Field]) -> str:
        if isinstance(field, Field):
            return field.field_name
        return field

    def to_field(self, field: Union[str, Field]) -> Field:
        if isinstance(field, Field):
            return field
        return Field(field)

    def to_field_names(self, fields: List[Any]) -> List[str]:
        """
        Convert a list of Field objects to a list of strings to be compatible
        with older versions of the code.
        """
        if not fields:
            return fields

        if not isinstance(fields[0], list):
            return [self.to_string(f) for f in fields]

        new_fields = []
        for field in fields:
            backported_fields = self.to_field_names(field)
            for backported_field in backported_fields:
                new_fields.append(backported_field)
        return new_fields

    def to_field_objects(self, fields: List[Any]) -> List[Field]:
        """
        Convert a list of Field name strings to a list of objects to be
        compatible with newer versions of the code.
        """
        if not fields:
            return fields

        return [self.to_field(f) for f in fields]


class Elasticsearch6SearchResults(Elasticsearch5SearchResults):
    pass


class Elasticsearch6AutocompleteQueryCompiler(
    ElasticsearchAutocompleteQueryCompilerImpl, Elasticsearch6SearchQueryCompiler
):
    def get_inner_query(self):
        fields = self.remapped_fields or [self.mapping.edgengrams_field_name]
        fields = [Field(field) for field in fields]
        if len(fields) == 0:
            # No fields. Return a query that'll match nothing
            return {"bool": {"mustNot": {"match_all": {}}}}

        return self._compile_plaintext_query(self.query, fields)


class Elasticsearch6SearchBackend(Elasticsearch5SearchBackend):
    mapping_class = Elasticsearch6Mapping
    index_class = Elasticsearch6Index
    query_compiler_class = Elasticsearch6SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch6AutocompleteQueryCompiler
    results_class = Elasticsearch6SearchResults


SearchBackend = Elasticsearch6SearchBackend
