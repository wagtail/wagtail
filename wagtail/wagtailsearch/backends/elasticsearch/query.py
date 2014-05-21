from .document import ElasticSearchType
import json


class FilterError(Exception):
    pass


class FieldError(Exception):
    pass


class ElasticSearchQuery(object):
    """
    Represents a query to be run on an Elasticsearch backend.

    These queries combine the filters from a Django QuerySet with a query string and
    produce the JSON Query DSL code to be run on an ElasticSearch backend.
    """
    def __init__(self, queryset, query_string, fields=None):
        self.queryset = queryset
        self.query_string = query_string
        self.fields = fields or ['_all', 'partials']
        self._es_type = ElasticSearchType(self.queryset.model)

    def _get_filters_from_where(self, where_node):
        """
        This method takes the filters from a Django Query and converts them
        to ElasticSearch format.
        """
        # Check if this is a leaf node
        if isinstance(where_node, tuple):
            field = where_node[0].col
            lookup = where_node[1]
            value = where_node[3]

            # Get field
            try:
                es_field = self._es_type.get_field(field)

                # Make sure this field is filterable
                assert es_field.filter_field
            except (IndexError, AssertionError):
                raise FieldError('Cannot filter ElasticSearch results with field "' + field + '". Is it added to search_filter_fields?')

            filter_field = es_field.get_filter_name()

            # Find lookup
            if lookup == 'exact':
                if value is None:
                    return {
                        'missing': {
                            'field': filter_field,
                        }
                    }
                else:
                    return {
                        'term': {
                            filter_field: es_field.convert_value(value)
                        }
                    }

            if lookup == 'isnull':
                if value:
                    return {
                        'missing': {
                            'field': filter_field,
                        }
                    }
                else:
                    return {
                        'not': {
                            'missing': {
                                'field': filter_field,
                            }
                        }
                    }

            if lookup in ['startswith', 'prefix']:
                return {
                    'prefix': {
                        filter_field: es_field.convert_value(value)
                    }
                }

            if lookup in ['gt', 'gte', 'lt', 'lte']:
                return {
                    'range': {
                        filter_field: {
                            lookup: es_field.convert_value(value),
                        }
                    }
                }

            if lookup == 'range':
                lower, upper = value

                return {
                    'range': {
                        filter_field: {
                            'gte': es_field.convert_value(lower),
                            'lte': es_field.convert_value(upper),
                        }
                    }
                }

            raise FilterError('Could not apply filter on ElasticSearch results "' + field + '__' + lookup + ' = ' + str(value) + '". Lookup "' + lookup + '"" not recognosed.')

        # Get child filters
        connector = where_node.connector
        child_filters = [self._get_filters_from_where(child) for child in where_node.children]
        child_filters = [child_filter for child_filter in child_filters if child_filter]

        # Connect them
        if child_filters:
            if len(child_filters) == 1:
                filter_out = child_filters[0]
            else:
                filter_out = {
                    connector.lower(): [
                        fil for fil in child_filters if fil is not None
                    ]
                }

            if where_node.negated:
                filter_out = {
                    'not': filter_out
                }

            return filter_out

    def _get_filters(self):
        """
        This method builds the 'filter' section of the query.
        """
        # Filters
        filters = []

        # Filter by content type
        filters.append({
            'prefix': {
                'content_type': self.queryset.model._get_qualified_content_type_name()
            }
        })

        # Apply filters from queryset
        queryset_filters = self._get_filters_from_where(self.queryset.query.where)
        if queryset_filters:
            filters.append(queryset_filters)

        return filters

    def to_es(self):
        """
        This method builds the ElasticSearch JSON Query DSL code for this query.
        """
        # Query
        if self.query_string is not None:
            query = {
                'query_string': {
                    'query': self.query_string,
                }
            }

            # Fields
            if self.fields:
                query['query_string']['fields'] = self.fields
        else:
            query = {
                'match_all': {}
            }

        # Filters
        filters = self._get_filters()
        if len(filters) == 1:
            query = {
                'filtered': {
                    'query': query,
                    'filter': filters[0],
                }
            }
        elif len(filters) > 1:
            query = {
                'filtered': {
                    'query': query,
                    'filter': {
                        'and': filters,
                    }
                }
            }

        return query

    def __repr__(self):
        return json.dumps(self.to_es())
