class ElasticSearchField(object):
    """
    This represents a field inside an ElasticSearchType.

    This has three jobs:
     - Find the ElasticSearch type for a particular field in a Django model.
     - Convert values to formats that ElasticSearch will recognise.
     - Produces mapping code for fields.
    """
    TYPE_MAP = {
        'TextField': 'string',
        'SlugField': 'string',
        'CharField': 'string',
        'PositiveIntegerField': 'integer',
        'BooleanField': 'boolean',
        'OneToOneField': 'string',
        'ForeignKey': 'string',
        'AutoField': 'integer',
        'DateField': 'date',
        'TimeField': 'date',
        'DateTimeField': 'date',
        'IntegerField': 'integer',
    }

    def __init__(self, name, **kwargs):
        self.name = name
        self.attname = kwargs['attname'] if 'attname' in kwargs else self.name
        self.search_field = kwargs['search'] if 'search' in kwargs else False
        self.filter_field = kwargs['filter'] if 'filter' in kwargs else False
        self.type = self.convert_type(kwargs['type']) if 'type' in kwargs else 'string'
        self.boost = kwargs['boost'] if 'boost' in kwargs else None
        self.partial_match = kwargs['partial_match'] if 'partial_match' in kwargs else False
        self.es_extra = kwargs['es_extra'] if 'es_extra' in kwargs else {}

    def get_filter_name(self):
        return self.attname + '_filter'

    def get_search_name(self):
        return self.attname

    def can_be_indexed(self):
        """
        Returns true if this field can be indexed in ElasticSearch.
        """
        return self.type is not None

    def convert_type(self, django_type):
        """
        This takes a Django field type (eg, TextField, IntegerField) and
        converts it to an ElasticSearch type (eg, string, integer).

        Returns None if the type cannot be indexed.
        """
        # Lookup es type from TYPE_MAP
        if django_type in self.TYPE_MAP:
            return self.TYPE_MAP[django_type]

    def convert_value(self, value):
        """
        This converts a value to a format that can be sent to ElasticSearch.
        It uses the type of this field.
        """
        if value is None:
            return

        if self.type == 'string':
            return unicode(value)
        elif self.type == 'integer':
            return int(value)
        elif self.type == 'boolean':
            return bool(value)
        elif self.type == 'date':
            return value.isoformat()

    def get_search_mapping(self):
        mapping = {
            'type': self.type,
            'include_in_all': True,
        }

        if self.boost is not None:
            mapping['boost'] = self.boost

        if self.partial_match:
            mapping['analyzer'] = 'edgengram_analyzer'

        if self.es_extra:
            mapping.update(self.es_extra)

        return mapping

    def get_filter_mapping(self):
        return {
            'type': self.type,
            'index': 'not_analyzed',
            'include_in_all': False,
        }

    def get_mapping(self):
        if not self.can_be_indexed():
            return

        mappings = {}

        if self.search_field:
            mappings[self.get_search_name()] = self.get_search_mapping()

        if self.filter_field:
            mappings[self.get_filter_name()] = self.get_filter_mapping()

        return mappings


class ElasticSearchType(object):
    """
    This represents a Django model which can be indexed inside ElasticSearch.
    It provides helper methods to help build ES mappings for a Django model.
    """
    def __init__(self, model):
        self.model = model
        self._fields = None

    def get_doc_type(self):
        """
        Returns the value to use for the doc_type attribute when refering to this
        type in ElasticSearch requests.
        """
        return self.model._get_qualified_content_type_name()

    def _get_fields(self):
        # Get field list
        fields = self.model.get_search_fields()

        # Build ES fields
        fields = [
            (name, ElasticSearchField(name, **config))
            for name, config in fields.items()
        ]

        # Remove fields that can't be indexed
        fields = [(field.attname, field) for name, field in fields if field.can_be_indexed()]

        # Return
        return dict(fields)

    def get_fields(self):
        """
        Gets a mapping of fieldnames to ElasticSearchField objects.
        """
        # Do some caching to prevent having to keep building the field list
        if self._fields is None:
            self._fields = self._get_fields()
        return self._fields

    def get_field(self, name):
        """
        Returns an ElasticSearchField object for the specified field.
        """
        return self.get_fields()[name]

    def has_field(self, name):
        """
        Returns True if the specified field exists in this type.
        """
        return name in self.get_fields()

    def get_mapping(self):
        """
        This method builds a mapping for this type which can be sent to ElasticSearch using
        the put mapping API.
        """
        # Make field list
        fields = {
            'pk': {
                'type': 'string',
                'index': 'not_analyzed',
                'store': 'yes',
                'include_in_all': False,
            },
            'content_type': {
                'type': 'string',
                'index': 'not_analyzed',
                'include_in_all': False,
            },
            'partials': {
                'type': 'string',
                'analyzer': 'edgengram_analyzer',
                'include_in_all': False,
            }
        }

        for name, field in self.get_fields().items():
            fields.update(field.get_mapping().items())

        return {
            self.get_doc_type(): {
                'properties': fields,
            }
        }


class ElasticSearchDocument(object):
    """
    This represents a Django object to be indexed in ElasticSearch.
    """
    def __init__(self, obj):
        self.obj = obj
        self.es_type = ElasticSearchType(obj.__class__)

    def get_id(self):
        """
        This returns the value to be used in this documents 'id' field.

        This takes the objects "base content type name" and concatenates it
        with the objects primary key.

        See the description in "wagtail.search.indexed.Indexed._get_base_content_type_name"
        for info on what the "base content type name" is.
        """
        return self.obj._get_base_content_type_name() + ':' + str(self.obj.pk)

    def build_document(self):
        """
        This builds a JSON document in ElasticSearch Index API format for the object.
        """
        # Build document
        doc = {
            'pk': str(self.obj.pk),
            'content_type': self.obj._get_qualified_content_type_name(),
            'id': self.get_id(),
        }

        # Add fields
        partials = []
        for name, field in self.es_type.get_fields().items():
            if hasattr(self.obj, field.attname):
                # Get field value
                value = getattr(self.obj, field.attname)

                # Check if this field is callable
                if hasattr(value, '__call__'):
                    # Call it
                    value = value()

                # Convert it
                value = field.convert_value(value)

                # Add to document
                if field.search_field:
                    doc[field.get_search_name()] = value
                if field.filter_field:
                    doc[field.get_filter_name()] = value

                # Add value to partials if this has partial match enabled
                if field.partial_match:
                    partials.append(str(value))

        # Partials must be sorted to allow them to be easily checked in unit tests
        partials.sort()

        # Add partials to doc
        doc['partials'] = partials

        return doc
