from wagtail.search.index import get_indexed_models

from .elasticsearch5 import (
    Elasticsearch5Index,
    Elasticsearch5Mapping,
    Elasticsearch5SearchBackend,
    Elasticsearch5SearchQueryCompiler,
    Elasticsearch5SearchResults,
    ElasticsearchAutocompleteQueryCompilerImpl,
)


class Elasticsearch6Mapping(Elasticsearch5Mapping):
    all_field_name = "_all_text"
    edgengrams_field_name = "_edgengrams"

    def get_boost_field_name(self, boost):
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

    def get_boosted_fields(self, fields):
        models = get_indexed_models()
        unique_boosts = set()
        for model in models:
            for field in model.get_searchable_search_fields():
                if field.boost:
                    unique_boosts.add(field.boost)
        for boost in unique_boosts:
            fields.append(f"{self.mapping.get_boost_field_name(boost)}^{boost}")
        return fields

    def _compile_fuzzy_query(self, query, fields):
        super()._compile_fuzzy_query(query, fields)

        return {
            "multi_match": {
                "query": query.query_string,
                "fields": self.get_boosted_fields(fields),
                "fuzziness": "AUTO",
            }
        }

    def _compile_plaintext_query(self, query, fields, boost=1):
        return super()._compile_plaintext_query(query, self.get_boosted_fields(fields))

    def _compile_phrase_query(self, query, fields):
        return super()._compile_phrase_query(query, self.get_boosted_fields(fields))


class Elasticsearch6SearchResults(Elasticsearch5SearchResults):
    pass


class Elasticsearch6AutocompleteQueryCompiler(
    ElasticsearchAutocompleteQueryCompilerImpl, Elasticsearch6SearchQueryCompiler
):
    pass


class Elasticsearch6SearchBackend(Elasticsearch5SearchBackend):
    mapping_class = Elasticsearch6Mapping
    index_class = Elasticsearch6Index
    query_compiler_class = Elasticsearch6SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch6AutocompleteQueryCompiler
    results_class = Elasticsearch6SearchResults


SearchBackend = Elasticsearch6SearchBackend
