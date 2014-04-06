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
    def _get_search_fields(cls):
        """
        Gets a mapping of fields/configs that should be indexed
        """
        # Get search fields for this class as a dictionary
        search_fields = list(cls.search_fields or cls.indexed_fields)
        if isinstance(search_fields, tuple):
            search_fields = list(search_fields)
        if isinstance(search_fields, basestring):
            search_fields = [search_fields]
        if isinstance(search_fields, list):
            search_fields = {field: {} for field in search_fields}
        if not isinstance(search_fields, dict):
            raise ValueError()

        # Add other fields to list
        if issubclass(cls, models.Model):
            for field in cls._meta.local_concrete_fields:
                search_fields[field.attname] = {}

        # Set defaults
        for field, config in search_fields.items():
            if 'type' not in config:
                config['type'] = 'string'
            if 'boost' not in config:
                config['boost'] = 1.0

        # Get search fields for parent class
        parent = cls._get_indexed_parent(require_model=False)
        if parent:
            # Add parent fields into this list
            search_fields = dict(parent._get_search_fields().items() + search_fields.items())

        # Make sure we didn't accidentally index the id field
        if 'id' in search_fields:
            del search_fields['id']

        return search_fields

    def _get_search_document_id(self):
        return self._get_base_content_type_name() + ':' + str(self.pk)

    def _build_search_document(self):
        # Get content type, indexed fields and id
        content_type = self._get_qualified_content_type_name()
        indexed_fields = self._get_search_fields()
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

    search_fields = ()
    indexed_fields = ()
