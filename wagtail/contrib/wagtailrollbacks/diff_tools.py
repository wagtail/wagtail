from operator import itemgetter
from dictdiffer import diff, patch, swap, revert
import six
import difflib
from difflib import HtmlDiff, SequenceMatcher
from django.core.exceptions import ObjectDoesNotExist
from datetime import date
from django.db import models
from django.db.models.fields.related import OneToOneField
from modelcluster.models import ClusterableModel


a = ['one', 'two', 'three', 'monkey']
b = ['one', 'five', 'two', 'three', 'four']


obj1 = {
    'title': 'some title',
    'some_list': ['a', 'b']
}


obj2 = {
    'title': 'some other title',
    'some_list': ['b', 'c', 'd']
}


def string_diff(a, b):
    s = SequenceMatcher(None, a, b)
    items = []

    for tag, i1, i2, j1, j2 in s.get_opcodes():
        print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" % (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
        items.append((tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))

    return items


def object_diff(a, b):
    result = diff(a, b)
    return list(result)


def model_diff(obj1, obj2, excluded_keys=['created_at', 'user', 'uid', '_state']):
    d1, d2 = obj1.__dict__, obj2.__dict__
    old, new = {}, {}

    for k, v in d1.items():
        if k in excluded_keys:
            continue
        try:
            if v != d2[k]:
                old.update({k: v})
                new.update({k: d2[k]})
        except KeyError:
            old.update({k: v})

    return [old, new]



def list_diff(a, b):
    # print a, b
    pairs = zip(a, b)

    difference = sum(x != y for x, y in pairs)
    difference += abs(len(a) - len(b))

    if difference == 0:
        print 'The lists are the same length and appear to contain the same items'
        return 0, [], [], []

    # added = in list b but not in list a
    added = [x for x in b if x not in a]
    removed = [x for x in a if x not in b]
    modified = [(x, y) for x, y in pairs if x != y and x not in added and x not in removed]

    modified_strings = [string_diff(x, y) for x, y in modified if isinstance(x, six.string_types) and isinstance(y, six.string_types)]
    modified_items = [object_diff(x, y) for x, y in modified if isinstance(x, dict) and isinstance(y, dict)]
    modified_models = [model_diff(x, y) for x, y in modified if isinstance(x, models.Model) and isinstance(y, models.Model)]

    if len(modified_strings):
        modified = modified_strings

    if len(modified_items):
        print 'has modified items!'
        modified = modified_items

    if len(modified_models):
        print 'models!'
        modified = modified_models

    return (difference, added, removed, modified)


def model_to_dict(obj, exclude=['AutoField', \
    'OneToOneField', 'revisions']):
    '''
        serialize model object to dict with related objects

        author: Vadym Zakovinko <vp@zakovinko.com>
        date: January 31, 2011
        http://djangosnippets.org/snippets/2342/
    '''
    tree = {}
    for field_name in obj._meta.get_all_field_names():
        if field_name == 'revisions':
            continue

        try:
            field = getattr(obj, field_name)
        except (ObjectDoesNotExist, AttributeError):
            continue

        if field.__class__.__name__ in ['DeferringRelatedManager', 'RelatedManager', 'ManyRelatedManager']:
            if field.model.__name__ in exclude:
                continue

            if field.__class__.__name__ == 'ManyRelatedManager':
                exclude.append(obj.__class__.__name__)
            subtree = []
            for related_obj in getattr(obj, field_name).all():
                value = model_to_dict(related_obj, \
                    exclude=exclude)
                if value:
                    subtree.append(value)
            if subtree:
                tree[field_name] = subtree

            continue

        field = obj._meta.get_field_by_name(field_name)[0]
        if field.__class__.__name__ in exclude:
            continue

        if field.__class__.__name__ == 'RelatedObject':
            exclude.append(field.model.__name__)
            tree[field_name] = model_to_dict(getattr(obj, field_name), \
                exclude=exclude)
            continue

        value = getattr(obj, field_name)
        if value:
            tree[field_name] = value

    return tree


def common_entries(*dcts):
    for i in set(dcts[0]).intersection(*dcts[1:]):
        yield (i,) + tuple(d[i] for d in dcts)


def diff_text(a, b):
    d = difflib.HtmlDiff()
    lines_a = a.splitlines()
    lines_b = b.splitlines()
    return d.make_table(lines_a, lines_b, context=True)


def diff_bool(a, b):
    d = difflib.HtmlDiff()
    lines_a = ['%s' % a]
    lines_b = ['%s' % b]
    return d.make_table(lines_a, lines_b, context=True)


def diff_date(a, b):
    d = difflib.HtmlDiff()
    lines_a = ['%s' % a]
    lines_b = ['%s' % b]
    return d.make_table(lines_a, lines_b, context=True)


def diff_fields(a, b):
    """
    Determine which differ to use. These work on the string
    representation of the field's value, so we transform values into strings
    if they're not already.
    """
    if isinstance(a, date) and isinstance(b, date):
        return diff_date(a, b)

    if isinstance(a, bool) and isinstance(b, bool):
        return diff_bool(a, b)

    if isinstance(a, six.string_types) and isinstance(b, six.string_types):
        return diff_text(a, b)

    if isinstance(a, list) and isinstance(b, list):
        print 'hey it\'s a list!'

    return None
