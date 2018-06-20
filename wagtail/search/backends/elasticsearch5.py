from .elasticsearch2 import (
    Elasticsearch2Index, Elasticsearch2Mapping, Elasticsearch2SearchBackend,
    Elasticsearch2SearchQueryCompiler, Elasticsearch2SearchResults, ElasticsearchAutocompleteQueryCompilerImpl)


class Elasticsearch5Mapping(Elasticsearch2Mapping):
    keyword_type = 'keyword'
    text_type = 'text'
    set_index_not_analyzed_on_filter_fields = False


class Elasticsearch5Index(Elasticsearch2Index):
    pass


class Elasticsearch5SearchQueryCompiler(Elasticsearch2SearchQueryCompiler):
    mapping_class = Elasticsearch5Mapping

    def _process_lookup(self, field, lookup, value):
        column_name = self.mapping.get_field_column_name(field)

        if lookup == 'isnull':
            query = {
                'exists': {
                    'field': column_name,
                }
            }

            if value:
                query = {
                    'bool': {
                        'mustNot': query
                    }
                }

            return query

        return super()._process_lookup(field, lookup, value)

    def _connect_filters(self, filters, connector, negated):
        if filters:
            if len(filters) == 1:
                filter_out = filters[0]
            elif connector == 'AND':
                filter_out = {
                    'bool': {
                        'must': [
                            fil for fil in filters if fil is not None
                        ]
                    }
                }
            elif connector == 'OR':
                filter_out = {
                    'bool': {
                        'should': [
                            fil for fil in filters if fil is not None
                        ]
                    }
                }

            if negated:
                filter_out = {
                    'bool': {
                        'mustNot': filter_out
                    }
                }

            return filter_out

    def get_query(self):
        inner_query = self.get_inner_query()
        filters = self.get_filters()

        if len(filters) == 1:
            return {
                'bool': {
                    'must': inner_query,
                    'filter': filters[0],
                }
            }
        elif len(filters) > 1:
            return {
                'bool': {
                    'must': inner_query,
                    'filter': filters,
                }
            }
        else:
            return inner_query


class Elasticsearch5AutocompleteQueryCompiler(Elasticsearch5SearchQueryCompiler, ElasticsearchAutocompleteQueryCompilerImpl):
    pass


class Elasticsearch5SearchResults(Elasticsearch2SearchResults):
    fields_param_name = 'stored_fields'


class Elasticsearch5SearchBackend(Elasticsearch2SearchBackend):
    mapping_class = Elasticsearch5Mapping
    index_class = Elasticsearch5Index
    query_compiler_class = Elasticsearch5SearchQueryCompiler
    autocomplete_query_compiler_class = Elasticsearch5AutocompleteQueryCompiler
    results_class = Elasticsearch5SearchResults


SearchBackend = Elasticsearch5SearchBackend
