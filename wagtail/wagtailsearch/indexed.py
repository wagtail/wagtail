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
        FIELD_DEFAULTS = {
            'type': 'string',
        }

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
                indexed_fields = dict((field, FIELD_DEFAULTS) for field in indexed_fields)
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
            search_fields = dict((field, FIELD_DEFAULTS) for field in search_fields)
        if not isinstance(search_fields, dict):
            raise ValueError()

        return search_fields

    @classmethod
    def _get_search_fields(cls):
        """
        Returns a list of all fields to index and a mapping of
        field/configs for fields to enable full-text search on.
        """
        fields = []
        searchable_fields = {}

        # Get fields
        if issubclass(cls, models.Model):
            for field in list(cls._meta.local_concrete_fields):
                if field.attname != 'id':
                    fields.append(field.attname)

        # Get searchable fields
        search_fields_config = cls._get_search_fields_config()
        if search_fields_config:
            for field, config in search_fields_config.items():
                searchable_fields[field] = config.copy()

        # Get search fields for parent class
        parent = cls._get_indexed_parent(require_model=False)
        if parent:
            # Merge parent search fields
            parent_fields, parent_searchable_fields = parent._get_search_fields()
            fields = parent_fields + fields
            searchable_fields = dict(parent_searchable_fields.items() + searchable_fields.items())

        return fields, searchable_fields

    @classmethod
    def _get_indexed_fields(cls):
        """
        Gets a mapping of fields/configs that should be indexed
        """
        # Get fields for this class as a dictionary
        fields, searchable_fields = cls._get_search_fields()

        # Initialise indexed_fields with searchable_fields
        indexed_fields = searchable_fields.copy()

        # Add other fields to list
        if issubclass(cls, models.Model):
            for field in fields:
                if field not in searchable_fields:
                    indexed_fields[field] = {
                        'type': 'string',
                        'indexed': 'not_indexed',
                    }

        return indexed_fields

    def _get_search_document_id(self):
        return self._get_base_content_type_name() + ':' + str(self.pk)

    def _build_search_document(self):
        # Get content type, indexed fields and id
        content_type = self._get_qualified_content_type_name()
        indexed_fields = self._get_indexed_fields()
        doc_id = self._get_search_document_id()

        # Build document
        doc = dict(pk=str(self.pk), content_type=content_type, id=doc_id)
        for field in indexed_fields.keys():
            if hasattr(self, field):
                doc[field] = getattr(self, field)

                # Check if this field is callable
                if hasattr(doc[field], "__call__"):
                    # Call it
                    doc[field] = doc[field]()

                # Make sure field value is a string
                doc[field] = unicode(doc[field])

        return doc
