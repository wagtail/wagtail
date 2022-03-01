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

        # Replace {"include_in_all": true} with {"copy_to": "_all_text"}
        def replace_include_in_all(mapping):
            for name, field_mapping in mapping["properties"].items():
                if "include_in_all" in field_mapping:
                    if field_mapping["include_in_all"]:
                        field_mapping["copy_to"] = self.all_field_name

                    del field_mapping["include_in_all"]

                if field_mapping["type"] == "nested":
                    replace_include_in_all(field_mapping)

        replace_include_in_all(mapping[self.get_document_type()])

        return mapping


class Elasticsearch6Index(Elasticsearch5Index):
    pass


class Elasticsearch6SearchQueryCompiler(Elasticsearch5SearchQueryCompiler):
    mapping_class = Elasticsearch6Mapping


class Elasticsearch6SearchResults(Elasticsearch5SearchResults):
    pass


class Elasticsearch6AutocompleteQueryCompiler(
    Elasticsearch6SearchQueryCompiler, ElasticsearchAutocompleteQueryCompilerImpl
):
    pass


class Elasticsearch6SearchBackend(Elasticsearch5SearchBackend):
    mapping_class = Elasticsearch6Mapping
    index_class = Elasticsearch6Index
    query_compiler_class = Elasticsearch6SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch6AutocompleteQueryCompiler
    results_class = Elasticsearch6SearchResults


SearchBackend = Elasticsearch6SearchBackend
