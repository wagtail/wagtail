from six import string_types

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
    def indexed_get_indexed_fields(cls):
        # Get indexed fields for this class as dictionary
        indexed_fields = cls.indexed_fields
        if isinstance(indexed_fields, dict):
            # Make sure we have a copy to prevent us accidentally changing the configuration
            indexed_fields = indexed_fields.copy()
        else:
            # Convert to dict
            if isinstance(indexed_fields, tuple):
                indexed_fields = list(indexed_fields)
            if isinstance(indexed_fields, string_types):
                indexed_fields = [indexed_fields]
            if isinstance(indexed_fields, list):
                indexed_fields = dict((field, dict(type="string")) for field in indexed_fields)
            if not isinstance(indexed_fields, dict):
                raise ValueError()

        # Get indexed fields for parent class
        parent = cls.indexed_get_parent(require_model=False)
        if parent:
            # Add parent fields into this list
            parent_indexed_fields = parent.indexed_get_indexed_fields().copy()
            parent_indexed_fields.update(indexed_fields)
            indexed_fields = parent_indexed_fields
        return indexed_fields

    def indexed_get_document_id(self):
        return self.indexed_get_toplevel_content_type() + ":" + str(self.pk)

    def indexed_build_document(self):
        # Get content type, indexed fields and id
        content_type = self.indexed_get_content_type()
        indexed_fields = self.indexed_get_indexed_fields()
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

        return doc

    indexed_fields = ()
