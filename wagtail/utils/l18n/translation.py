import os
import gettext
import bisect
from locale import getdefaultlocale
from collections import MutableMapping
from copy import copy, deepcopy

import six


class Trans(object):

    def __init__(self):
        self.registry = {}
        self.current = None
        self.set(getdefaultlocale()[0])

    def __getitem__(self, language):
        if language:
            try:
                return self.registry[language]
            except KeyError:
                self.registry[language] = gettext.translation(
                    'l18n',
                    os.path.join(os.path.dirname(__file__), 'locale'),
                    languages=[language],
                    fallback=True
                )
                return self.registry[language]
        else:
            return None

    def set(self, language):
        self.current = self[language]

    def gettext(self, s):
        try:
            return self.current.gettext(s)
        except AttributeError:
            return s

    if six.PY2:
        def ugettext(self, s):
            try:
                return self.current.ugettext(s)
            except AttributeError:
                return s


_trans = Trans()


def set_language(language=None):
    _trans.set(language)


if six.PY2:
    def translate(s, utf8=True, trans=_trans):
        if trans:
            if utf8:
                return trans.ugettext(s)
            return trans.gettext(s)
        else:
            return s
else:
    def translate(s, utf8=True, trans=_trans):
        if trans:
            t = trans.gettext(s)
            if utf8:
                return t
            return t.encode()
        else:
            return s


class L18NLazyObject(object):

    def _value(self, utf8=True):
        raise NotImplementedError

    def __str__(self):
        return self._value(utf8=six.PY3)

    def __bytes__(self):
        return self._value(utf8=False)

    def __unicode__(self):
        return self._value(utf8=True)


class L18NLazyString(L18NLazyObject):

    def __init__(self, s):
        self._str = s

    def __copy__(self):
        return self.__class__(self._str)

    def __deepcopy__(self, memo):
        result = self.__copy__()
        memo[id(self)] = result
        return result

    def _value(self, utf8=True):
        return translate(self._str, utf8)

    def __repr__(self):
        return 'L18NLazyString <%s>' % repr(self._str)

    def __getattr__(self, name):
        # fallback to call the value's attribute in case it's not found in
        # L18NLazyString
        return getattr(self._value(), name)


class L18NLazyStringsList(L18NLazyObject):

    def __init__(self, sep='/', *s):
        # we assume that the separator and the strings have the same encoding
        # (text_type)
        self._sep = sep
        self._strings = s

    def __copy__(self):
        return self.__class__(self._sep, *self._strings)

    def __deepcopy__(self, memo):
        result = self.__copy__()
        memo[id(self)] = result
        return result

    def _value(self, utf8=True):
        sep = self._sep
        if utf8 and isinstance(sep, six.binary_type):
            sep = sep.decode(encoding='utf-8')
        elif not utf8 and isinstance(sep, six.text_type):
            sep = sep.encode(encoding='utf-8')
        return sep.join([translate(s, utf8)
                         for s in self._strings])

    def __repr__(self):
        return 'L18NLazyStringsList <%s>' % self._sep.join([
            repr(s) for s in self._strings
        ])

    def __getattr__(self, name):
        # fallback to call the value's attribute in case it's not found in
        # L18NLazyStringsList
        return getattr(self._value(), name)


class L18NBaseMap(MutableMapping):
    """
    Generic dictionary that returns lazy string or lazy string lists
    """

    def __init__(self, *args, **kwargs):
        self.store = dict(*args, **kwargs)
        self.sorted = {}

    def __copy__(self):
        result = self.__class__()
        result.store = self.store
        result.sorted = self.sorted
        return result

    def __deepcopy__(self, memo):
        result = self.__class__()
        memo[id(self)] = result
        result.store = deepcopy(self.store, memo)
        result.sorted = deepcopy(self.sorted, memo)
        return result

    def __getitem__(self, key):
        raise NotImplementedError

    def __setitem__(self, key, value):
        self.store[key] = value
        for locale, (keys, values) in six.iteritems(self.sorted):
            tr = translate(value, trans=_trans[locale])
            i = bisect.bisect_left(values, tr)
            keys.insert(i, key)
            values.insert(i, tr)

    def __delitem__(self, key):
        del self.store[key]
        for keys, values in self.sorted.values():
            i = keys.index(key)
            del keys[i]
            del values[i]

    def __iter__(self):
        loc = _trans.current._info['language'] if _trans.current else None
        try:
            return iter(self.sorted[loc][0])
        except KeyError:
            keys = []
            values = []
            # we can't use iteritems here, as we need to call __getitem__
            # via self[key]
            for key in iter(self.store):
                value = six.text_type(self[key])
                i = bisect.bisect_left(values, value)
                keys.insert(i, key)
                values.insert(i, value)
            self.sorted[loc] = (keys, values)
            return iter(keys)

    def __len__(self):
        return len(self.store)

    def subset(self, keys):
        """
        Generates a subset of the current map (e.g. to retrieve only tzs in
        common_timezones from the tz_cities or tz_fullnames maps)
        """
        sub = self.__class__()

        self_keys = set(self.store.keys())
        subset_keys = self_keys.intersection(keys)
        removed_keys = self_keys.difference(subset_keys)

        sub.store = {k: self.store[k] for k in subset_keys}
        for loc, sorted_items in six.iteritems(self.sorted):
            loc_keys = copy(self.sorted[loc][0])
            loc_values = copy(self.sorted[loc][1])
            for k in removed_keys:
                i = loc_keys.index(k)
                del loc_keys[i]
                del loc_values[i]
            sub.sorted[loc] = (loc_keys, loc_values)
        return sub


class L18NMap(L18NBaseMap):

    def __getitem__(self, key):
        return L18NLazyString(self.store[key])


class L18NListMap(L18NBaseMap):

    def __init__(self, sep='/', aux=None, *args, **kwargs):
        self._sep = sep
        self._aux = aux
        super(L18NListMap, self).__init__(*args, **kwargs)

    def __copy__(self):
        result = super(L18NListMap, self).__copy__()
        result._sep = self._sep
        result._aux = self._aux
        return result

    def __deepcopy__(self, memo):
        result = super(L18NListMap, self).__deepcopy__(memo)
        result._sep = self._sep
        result._aux = None if self._aux is None else deepcopy(self._aux, memo)
        return result

    def __getitem__(self, key):
        strs = key.split(self._sep)
        strs[-1] = key
        lst = []
        for s in strs:
            try:
                lst.append(self.store[s])
            except KeyError:
                lst.append(self._aux[s])
        return L18NLazyStringsList(self._sep, *lst)

    def subset(self, keys):
        sub = super(L18NListMap, self).subset(keys)
        sub._sep = self._sep
        sub._aux = deepcopy(self._aux)
        return sub
