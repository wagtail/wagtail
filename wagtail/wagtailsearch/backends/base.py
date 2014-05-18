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

    def search(self, query_set, query_string, fields=None):
        return NotImplemented


class BaseSearchResults(object):
    def __init__(self, backend, queryset, query_string, fields=None):
        self.backend = backend
        self.queryset = queryset
        self.query_string = query_string
        self.fields = fields
        self.start = 0
        self.stop = None
        self._results_cache = None
        self._hit_count = None

    def _do_search(self):
        return NotImplemented

    def _do_count(self):
        return NotImplemented

    def _clone(self):
        klass = self.__class__
        new = klass(self.backend, self.queryset, self.query_string, self.fields)
        new.start = self.start
        new.stop = self.stop
        return new

    def results(self):
        if self._results_cache is None:
            self._results_cache = self._do_search()
        return self._results_cache

    def count(self):
        if self._hit_count is None:
            if self._results_cache is not None:
                self._hit_count = len(self._results_cache)
            else:
                self._hit_count = self._do_count()
        return self._hit_count

    def _set_limits(self, start=None, stop=None):
        if stop is not None:
            if self.stop is not None:
                self.stop = min(self.stop, self.start + stop)
            else:
                self.stop = self.start + stop

        if start is not None:
            if self.stop is not None:
                self.start = min(self.stop, self.start + start)
            else:
                self.start = self.start + start

    def __getitem__(self, key):
        new = self._clone()

        if isinstance(key, slice):
            # Set limits
            start = int(key.start) if key.start else None
            stop = int(key.stop) if key.stop else None
            new._set_limits(start, stop)

            # Copy results cache
            if self._results_cache is not None:
                new._results_cache = self._results_cache[key]

            return new
        else:
            # Return a single item
            if self._results_cache is not None:
                return self._results_cache[key]

            new.start = key
            new.stop = key + 1
            return list(new)[0]
  
    def __len__(self):
        return len(self.results())

    def __iter__(self):
        return iter(self.results())

    def __repr__(self):
        data = list(self[:21])
        if len(data) > 20:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)
