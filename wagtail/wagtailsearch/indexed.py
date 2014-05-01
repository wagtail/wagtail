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
    def _get_search_fields_config(cls):
        """
        Get config for full-text search fields
        """
        # Get local search_fields or indexed_fields configs
        if 'search_fields' in cls.__dict__:
            search_fields = cls.search_fields
        elif 'indexed_fields' in cls.__dict__:
            indexed_fields = cls.indexed_fields

            # Convert to dict
            if isinstance(indexed_fields, tuple):
                indexed_fields = list(indexed_fields)
            if isinstance(indexed_fields, basestring):
                indexed_fields = [indexed_fields]
            if isinstance(indexed_fields, list):
                indexed_fields = dict((field, {}) for field in indexed_fields)
            if not isinstance(indexed_fields, dict):
                raise ValueError()

            # Filter out fields that are not being searched
            search_fields = {}
            for field, config in indexed_fields.items():
                if not config.get('indexed', None) == 'not_indexed' and not config.get('index', None) == 'not_analyzed':
                    search_fields[field] = config
        else:
            return {}

        # Convert to dict
        if isinstance(search_fields, tuple):
            search_fields = list(search_fields)
        if isinstance(search_fields, basestring):
            search_fields = [search_fields]
        if isinstance(search_fields, list):
            search_fields = dict((field, {}) for field in search_fields)
        if not isinstance(search_fields, dict):
            raise ValueError()

        return search_fields

    @classmethod
    def _add_field_types(cls, fields):
        # Find fields without types set
        for field, config in fields.items():
            if 'type' not in config and 'django_type' not in config:
                try:
                    # Try getting the Django field
                    if field.endswith('_id'):
                        field_obj = cls._meta.get_field_by_name(field[:-3])[0]
                    else:
                        field_obj = cls._meta.get_field_by_name(field)[0]

                    # Add "django_type" to the config. This will be
                    # converted to the real type name by the backend
                    config['django_type'] = field_obj.get_internal_type()
                except models.fields.FieldDoesNotExist:
                    # Not a Django field
                    pass

                # Check if this is a class attribute that defines a search_type
                if hasattr(cls, field):
                    attr = getattr(cls, field)

                    # Check if the attribute defines a search type
                    if hasattr(attr, 'search_type'):
                        config['type'] = attr['search_type']
                        continue

    @classmethod
    def _get_filterable_fields(cls):
        """
        Gets a list of field names that can be filtered on
        If an external search index is being used (eg, ElasticSearch),
        these fields must be added to that index
        """
        # Get local filterable fields
        fields = {}
        if issubclass(cls, models.Model):
            for field in list(cls._meta.local_concrete_fields):
                fields[field.attname] = {
                    'index': 'not_analyzed',
                }

        # Add field types
        cls._add_field_types(fields)

        # Append to parents filterable fields
        parent = cls._get_indexed_parent(require_model=False)
        if parent:
            parent_fields = parent._get_filterable_fields()
            fields = dict(parent_fields.items() + fields.items())
        return fields

    @classmethod
    def _get_searchable_fields(cls):
        """
        Gets a mapping of field/configs that have full text search enabled
        The configs contain settings such as boosting and edgengram settings
        """
        # Get local searchable fields
        fields = {}
        search_fields_config = cls._get_search_fields_config()
        if search_fields_config:
            for field, config in search_fields_config.items():
                fields[field] = config.copy()

        # Add field types
        cls._add_field_types(fields)

        # Append to parents searchable fields
        parent = cls._get_indexed_parent(require_model=False)
        if parent:
            parent_fields = parent._get_searchable_fields()
            fields = dict(parent_fields.items() + fields.items())

        return fields
