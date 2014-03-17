from django.db import models
from django.core.exceptions import ImproperlyConfigured

from wagtail.wagtailsearch.indexed import Indexed


class InvalidSearchBackendError(ImproperlyConfigured):
    pass


class BaseSearch(object):
    def __init__(self, params):
        pass

    def object_can_be_indexed(self, obj):
        # Object must be a decendant of Indexed and be a django model
        if not isinstance(obj, Indexed) or not isinstance(obj, models.Model):
            return False

        return True

    def reset_index(self):
        return NotImplemented

    def add_type(self, model):
        return NotImplemented

    def refresh_index(self):
        return NotImplemented

    def add(self, obj):
        return NotImplemented

    def add_bulk(self, obj_list):
        return NotImplemented

    def delete(self, obj):
        return NotImplemented

    def search(self, query_string, model, fields=None, filters=None, prefetch_related=None):
        if not prefetch_related: prefetch_related = []
        if not filters: filters = {}
        return NotImplemented
