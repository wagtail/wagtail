from django.db import models


class Indexed(object):
    @classmethod
    def indexed_get_parent(cls, require_model=True):
        for base in cls.__bases__:
            if issubclass(base, Indexed) and (issubclass(base, models.Model) or require_model is False):
                return base

    @classmethod
    def indexed_get_content_type(cls):
        # Work out content type
        content_type = (cls._meta.app_label + "_" + cls.__name__).lower()

        # Get parent content type
        parent = cls.indexed_get_parent()
        if parent:
            parent_content_type = parent.indexed_get_content_type()
            return parent_content_type + "_" + content_type
        else:
            return content_type

    @classmethod
    def indexed_get_toplevel_content_type(cls):
        # Get parent content type
        parent = cls.indexed_get_parent()
        if parent:
            return parent.indexed_get_content_type()
        else:
            # At toplevel, return this content type
            return (cls._meta.app_label + "_" + cls.__name__).lower()

    @classmethod
    def indexed_get_search_fields(cls):
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
        parent = cls.indexed_get_parent(require_model=False)
        if parent:
            # Add parent fields into this list
            search_fields = dict(parent.indexed_get_search_fields().items() + search_fields.items())

        # Make sure we didn't accidentally index the id field
        if 'id' in search_fields:
            del search_fields['id']

        return search_fields

    def indexed_get_document_id(self):
        return self.indexed_get_toplevel_content_type() + ":" + str(self.pk)

    def indexed_build_document(self):
        # Get content type, indexed fields and id
        content_type = self.indexed_get_content_type()
        indexed_fields = self.indexed_get_search_fields()
        doc_id = self.indexed_get_document_id()

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
