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
    def _get_search_config(cls, local=False):
        # Copy config from class
        if 'search_fields' in cls.__dict__:
            search_fields = cls.__dict__['search_fields']

            if isinstance(search_fields, (list, tuple, set)):
                search_fields = dict((field, {}) for field in search_fields)
        else:
            search_fields = {}

        if 'search_filter_fields' in cls.__dict__:
            filter_fields = cls.__dict__['search_filter_fields']
        else:
            filter_fields = set()

        # Merge with parent config
        if not local:
            parent = cls._get_indexed_parent(require_model=False)
            if parent:
                parent_search_fields, parent_filter_fields = parent._get_search_config()

                parent_search_fields.update(search_fields)
                search_fields = parent_search_fields

                parent_filter_fields.update(filter_fields)
                filter_fields = parent_filter_fields

        return search_fields, filter_fields

    @classmethod
    def get_search_fields(cls, exclude_search=False, exclude_filter=False, local=False):
        # Get search config
        search_fields, filter_fields = cls._get_search_config(local)

        # Make sure primary key is always filterable
        filter_fields.add(cls._meta.pk.name)

        # Get set of field names
        field_names = set()
        field_names.update(search_fields.keys())
        field_names.update(filter_fields)

        # Build field dictionary
        fields = {}

        for field in field_names:
            field_config = {}

            # Get Django field
            try:
                field_obj = cls._meta.get_field_by_name(field)[0]
                field_config['type'] = field_obj.get_internal_type()
                field_config['attname'] = field_obj.attname
            except models.fields.FieldDoesNotExist:
                # Not a Django field
                pass

            # Search/filter booleans
            field_config['search'] = field in search_fields.keys()
            field_config['filter'] = field in filter_fields

            # Extra search configuration
            if field in search_fields and search_fields[field]:
                field_config['predictive'] = search_fields[field].get('predictive', False)
                field_config['boost'] = search_fields[field].get('boost', None)
                field_config['es_extra'] = search_fields[field].get('es_extra', {})

            # Add to fields dictionary if this field is not excluded
            if field_config['search'] and not exclude_search or field_config['filter'] and not exclude_filter:
                fields[field] = field_config

        return fields
