from django.db import models


class Indexed(object):
    @classmethod
    def _get_indexed_parent(cls, require_model=True):
        """
        Gets the first parent of this class that derives from Indexed
        """
        for base in cls.__bases__:
            if issubclass(base, Indexed) and (issubclass(base, models.Model) or require_model is False):
                return base

    @classmethod
    def _get_qualified_content_type_name(cls):
        """
        Returns the qualified content type name for this class
        This is all the content type names of each class from the one that inherits
        from Indexed all the way down to this one
        eg. The qualified content type name for a class "EventPage"
        which inherits from "Page will be: wagtailcore_page_myapp_eventpage
        """
        # Work out content type
        content_type = (cls._meta.app_label + '_' + cls.__name__).lower()

        # Get parent content type
        parent = cls._get_indexed_parent()
        if parent:
            # Append this content type to the parents qualified content type
            parent_content_type = parent._get_qualified_content_type_name()
            return parent_content_type + '_' + content_type
        else:
            # At toplevel, return this content type
            return content_type

    @classmethod
    def _get_base_content_type_name(cls):
        """
        Returns the base content type name for this class
        This is the ancestor class that inherits from Indexed (could be this one)
        eg. The base content type name for a class "EventPage"
        which inherits from "Page will be: wagtailcore_page
        """
        # Get parent content type
        parent = cls._get_indexed_parent()
        if parent:
            # Return parents content type
            return parent._get_base_content_type_name()
        else:
            # At toplevel, return this content type
            return (cls._meta.app_label + '_' + cls.__name__).lower()

    @classmethod
    def _get_search_config(cls):
        search_config = {
            'search_fields': [],
            'search_filter_fields': [],
            'search_field_boost': {},
            'search_predictive_fields': [],
            'search_es_extra': {},
        }

        # Copy config from class
        if 'search_fields' in cls.__dict__:
            search_config['search_fields'] = cls.__dict__['search_fields']

        if 'search_filter_fields' in cls.__dict__:
            search_config['search_filter_fields'] = cls.__dict__['search_filter_fields']

        if 'search_field_boost' in cls.__dict__:
            search_config['search_field_boost'] = cls.__dict__['search_field_boost']

        if 'search_predictive_fields' in cls.__dict__:
            search_config['search_predictive_fields'] = cls.__dict__['search_predictive_fields']

        if 'search_es_extra' in cls.__dict__:
            search_config['search_es_extra'] = cls.__dict__['search_es_extra']

        return search_config

    @classmethod
    def _get_search_fields(cls, search_fields=None, filter_fields=None, local=False):
        # If neither search_fields nor filter_fields were explicity set,
        # set them both to True.
        if search_fields is None and filter_fields is None:
            search_fields = filter_fields = True

        # Get search config
        search_config = cls._get_search_config()

        # Get list of field names
        field_names = set()

        if search_fields:
            field_names.update(search_config['search_fields'])

        if filter_fields:
            field_names.update(search_config['search_filter_fields'])

        # Build field dictionary
        fields = {}

        for field in field_names:
            field_config = {}

            # Search, filter and predictive booleans
            field_config['search'] = field in search_config['search_fields']
            field_config['filter'] = field in search_config['search_filter_fields']
            field_config['predictive'] = field in search_config['search_predictive_fields']

            # Boost
            if field in search_config['search_field_boost']:
                field_config['boost'] = search_config['search_field_boost'][field]

            # Extra ElasticSearch configuration
            if field in search_config['search_es_extra']:
                field_config['es_extra'] = search_config['search_es_extra'][field]

            fields[field] = field_config

        # Append to parents fields
        if not local:
            parent = cls._get_indexed_parent(require_model=False)
            if parent:
                parent_fields = parent._get_search_fields(search_fields, filter_fields)
                parent_fields.update(fields)
                fields = parent_fields

        return fields

    @classmethod
    def get_search_fields(cls, search_fields=None, filter_fields=None, local=False):
        fields = cls._get_search_fields(search_fields, filter_fields, local)

        # Add types
        for field in fields.keys():
            # Get Django field
            try:
                field_obj = cls._meta.get_field_by_name(field)[0]
                fields[field]['type'] = field_obj.get_internal_type()
                fields[field]['attname'] = field_obj.attname
            except models.fields.FieldDoesNotExist:
                # Not a Django field
                pass

        return fields

    def get_search_field_value(self, field):
        if hasattr(self, field):
            # Get field value
            value = getattr(self, field)

            # Check if this field is callable
            if hasattr(value, '__call__'):
                # Call it
                value = value()

            # Return
            return value   
