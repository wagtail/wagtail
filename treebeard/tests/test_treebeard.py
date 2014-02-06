# -*- coding: utf-8 -*-
"""Unit/Functional tests"""

from __future__ import with_statement, unicode_literals
import datetime
import os
import sys

from django.contrib.admin.sites import AdminSite
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db.models import Q
from django.template import Template, Context
from django.test import TestCase
from django.test.client import RequestFactory
import pytest

from treebeard import numconv
from treebeard.admin import admin_factory
from treebeard.exceptions import InvalidPosition, InvalidMoveToDescendant,\
    PathOverflow, MissingNodeOrderBy
from treebeard.forms import movenodeform_factory
from treebeard.templatetags.admin_tree import get_static_url
from treebeard.tests import models


BASE_DATA = [
    {'data': {'desc': '1'}},
    {'data': {'desc': '2'}, 'children': [
        {'data': {'desc': '21'}},
        {'data': {'desc': '22'}},
        {'data': {'desc': '23'}, 'children': [
            {'data': {'desc': '231'}},
        ]},
        {'data': {'desc': '24'}},
    ]},
    {'data': {'desc': '3'}},
    {'data': {'desc': '4'}, 'children': [
        {'data': {'desc': '41'}},
    ]}]
UNCHANGED = [
    ('1', 1, 0),
    ('2', 1, 4),
    ('21', 2, 0),
    ('22', 2, 0),
    ('23', 2, 1),
    ('231', 3, 0),
    ('24', 2, 0),
    ('3', 1, 0),
    ('4', 1, 1),
    ('41', 2, 0)]


def _prepare_db_test(request):
    case = TestCase(methodName='__init__')
    case._pre_setup()
    request.addfinalizer(case._post_teardown)
    return request.param


@pytest.fixture(scope='function',
                params=models.BASE_MODELS + models.PROXY_MODELS)
def model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=models.BASE_MODELS)
def model_without_proxy(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=models.UNICODE_MODELS)
def model_with_unicode(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=models.SORTED_MODELS)
def sorted_model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=models.RELATED_MODELS)
def related_model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=models.MP_SHORTPATH_MODELS)
def mpshort_model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=[models.MP_TestNodeShortPath])
def mpshortnotsorted_model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=[models.MP_TestNodeAlphabet])
def mpalphabet_model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=[models.MP_TestNodeSortedAutoNow])
def mpsortedautonow_model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=[models.MP_TestNodeSmallStep])
def mpsmallstep_model(request):
    return _prepare_db_test(request)


@pytest.fixture(scope='function', params=[models.MP_TestManyToManyWithUser])
def mpm2muser_model(request):
    return _prepare_db_test(request)


class TestTreeBase(object):
    def got(self, model):
        if model in [models.NS_TestNode, models.NS_TestNode_Proxy]:
            # this slows down nested sets tests quite a bit, but it has the
            # advantage that we'll check the node edges are correct
            d = {}
            for tree_id, lft, rgt in model.objects.values_list('tree_id',
                                                               'lft',
                                                               'rgt'):
                d.setdefault(tree_id, []).extend([lft, rgt])
            for tree_id, got_edges in d.items():
                assert len(got_edges) == max(got_edges)
                good_edges = list(range(1, len(got_edges) + 1))
                assert sorted(got_edges) == good_edges

        return [(o.desc, o.get_depth(), o.get_children_count())
                for o in model.get_tree()]

    def _assert_get_annotated_list(self, model, expected, parent=None):
        got = [
            (obj[0].desc, obj[1]['open'], obj[1]['close'], obj[1]['level'])
            for obj in model.get_annotated_list(parent)
        ]
        assert expected == got


class TestEmptyTree(TestTreeBase):

    def test_load_bulk_empty(self, model):
        ids = model.load_bulk(BASE_DATA)
        got_descs = [obj.desc
                     for obj in model.objects.filter(id__in=ids)]
        expected_descs = [x[0] for x in UNCHANGED]
        assert sorted(got_descs) == sorted(expected_descs)
        assert self.got(model) == UNCHANGED

    def test_dump_bulk_empty(self, model):
        assert model.dump_bulk() == []

    def test_add_root_empty(self, model):
        model.add_root(desc='1')
        expected = [('1', 1, 0)]
        assert self.got(model) == expected

    def test_get_root_nodes_empty(self, model):
        got = model.get_root_nodes()
        expected = []
        assert [node.desc for node in got] == expected

    def test_get_first_root_node_empty(self, model):
        got = model.get_first_root_node()
        assert got is None

    def test_get_last_root_node_empty(self, model):
        got = model.get_last_root_node()
        assert got is None

    def test_get_tree(self, model):
        got = list(model.get_tree())
        assert got == []

    def test_get_annotated_list(self, model):
        expected = []
        self._assert_get_annotated_list(model, expected)


class TestNonEmptyTree(TestTreeBase):

    @classmethod
    def setup_class(cls):
        for model in models.BASE_MODELS:
            model.load_bulk(BASE_DATA)

    @classmethod
    def teardown_class(cls):
        models.empty_models_tables(models.BASE_MODELS)


class TestClassMethods(TestNonEmptyTree):

    def test_load_bulk_existing(self, model):
        # inserting on an existing node
        node = model.objects.get(desc='231')
        ids = model.load_bulk(BASE_DATA, node)
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 4),
                    ('1', 4, 0),
                    ('2', 4, 4),
                    ('21', 5, 0),
                    ('22', 5, 0),
                    ('23', 5, 1),
                    ('231', 6, 0),
                    ('24', 5, 0),
                    ('3', 4, 0),
                    ('4', 4, 1),
                    ('41', 5, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        expected_descs = ['1', '2', '21', '22', '23', '231', '24',
                          '3', '4', '41']
        got_descs = [obj.desc for obj in model.objects.filter(id__in=ids)]
        assert sorted(got_descs) == sorted(expected_descs)
        assert self.got(model) == expected

    def test_get_tree_all(self, model):
        got = [(o.desc, o.get_depth(), o.get_children_count())
               for o in model.get_tree()]
        assert got == UNCHANGED

    def test_dump_bulk_all(self, model):
        assert model.dump_bulk(keep_ids=False) == BASE_DATA

    def test_get_tree_node(self, model):
        node = model.objects.get(desc='231')
        model.load_bulk(BASE_DATA, node)

        # the tree was modified by load_bulk, so we reload our node object
        node = model.objects.get(pk=node.pk)

        got = [(o.desc, o.get_depth(), o.get_children_count())
               for o in model.get_tree(node)]
        expected = [('231', 3, 4),
                    ('1', 4, 0),
                    ('2', 4, 4),
                    ('21', 5, 0),
                    ('22', 5, 0),
                    ('23', 5, 1),
                    ('231', 6, 0),
                    ('24', 5, 0),
                    ('3', 4, 0),
                    ('4', 4, 1),
                    ('41', 5, 0)]
        assert got == expected

    def test_get_tree_leaf(self, model):
        node = model.objects.get(desc='1')

        assert 0 == node.get_children_count()
        got = [(o.desc, o.get_depth(), o.get_children_count())
               for o in model.get_tree(node)]
        expected = [('1', 1, 0)]
        assert got == expected

    def test_get_annotated_list_all(self, model):
        expected = [('1', True, [], 0), ('2', False, [], 0),
                    ('21', True, [], 1), ('22', False, [], 1),
                    ('23', False, [], 1), ('231', True, [0], 2),
                    ('24', False, [0], 1), ('3', False, [], 0),
                    ('4', False, [], 0), ('41', True, [0, 1], 1)]
        self._assert_get_annotated_list(model, expected)

    def test_get_annotated_list_node(self, model):
        node = model.objects.get(desc='2')
        expected = [('2', True, [], 0), ('21', True, [], 1),
                    ('22', False, [], 1), ('23', False, [], 1),
                    ('231', True, [0], 2), ('24', False, [0, 1], 1)]
        self._assert_get_annotated_list(model, expected, node)

    def test_get_annotated_list_leaf(self, model):
        node = model.objects.get(desc='1')
        expected = [('1', True, [0], 0)]
        self._assert_get_annotated_list(model, expected, node)

    def test_dump_bulk_node(self, model):
        node = model.objects.get(desc='231')
        model.load_bulk(BASE_DATA, node)

        # the tree was modified by load_bulk, so we reload our node object
        node = model.objects.get(pk=node.pk)

        got = model.dump_bulk(node, False)
        expected = [{'data': {'desc': '231'}, 'children': BASE_DATA}]
        assert got == expected

    def test_load_and_dump_bulk_keeping_ids(self, model):
        exp = model.dump_bulk(keep_ids=True)
        model.objects.all().delete()
        model.load_bulk(exp, None, True)
        got = model.dump_bulk(keep_ids=True)
        assert got == exp
        # do we really have an unchaged tree after the dump/delete/load?
        got = [(o.desc, o.get_depth(), o.get_children_count())
               for o in model.get_tree()]
        assert got == UNCHANGED

    def test_load_and_dump_bulk_with_fk(self, related_model):
        # https://bitbucket.org/tabo/django-treebeard/issue/48/
        related_model.objects.all().delete()
        related, created = models.RelatedModel.objects.get_or_create(
            desc="Test %s" % related_model.__name__)

        related_data = [
            {'data': {'desc': '1', 'related': related.pk}},
            {'data': {'desc': '2', 'related': related.pk}, 'children': [
                {'data': {'desc': '21', 'related': related.pk}},
                {'data': {'desc': '22', 'related': related.pk}},
                {'data': {'desc': '23', 'related': related.pk}, 'children': [
                    {'data': {'desc': '231', 'related': related.pk}},
                ]},
                {'data': {'desc': '24', 'related': related.pk}},
            ]},
            {'data': {'desc': '3', 'related': related.pk}},
            {'data': {'desc': '4', 'related': related.pk}, 'children': [
                {'data': {'desc': '41', 'related': related.pk}},
            ]}]
        related_model.load_bulk(related_data)
        got = related_model.dump_bulk(keep_ids=False)
        assert got == related_data

    def test_get_root_nodes(self, model):
        got = model.get_root_nodes()
        expected = ['1', '2', '3', '4']
        assert [node.desc for node in got] == expected

    def test_get_first_root_node(self, model):
        got = model.get_first_root_node()
        assert got.desc == '1'

    def test_get_last_root_node(self, model):
        got = model.get_last_root_node()
        assert got.desc == '4'

    def test_add_root(self, model):
        obj = model.add_root(desc='5')
        assert obj.get_depth() == 1
        assert model.get_last_root_node().desc == '5'


class TestSimpleNodeMethods(TestNonEmptyTree):
    def test_is_root(self, model):
        data = [
            ('2', True),
            ('1', True),
            ('4', True),
            ('21', False),
            ('24', False),
            ('22', False),
            ('231', False),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).is_root()
            assert got == expected

    def test_is_leaf(self, model):
        data = [
            ('2', False),
            ('23', False),
            ('231', True),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).is_leaf()
            assert got == expected

    def test_get_root(self, model):
        data = [
            ('2', '2'),
            ('1', '1'),
            ('4', '4'),
            ('21', '2'),
            ('24', '2'),
            ('22', '2'),
            ('231', '2'),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_root()
            assert node.desc == expected

    def test_get_parent(self, model):
        data = [
            ('2', None),
            ('1', None),
            ('4', None),
            ('21', '2'),
            ('24', '2'),
            ('22', '2'),
            ('231', '23'),
        ]
        data = dict(data)
        objs = {}
        for desc, expected in data.items():
            node = model.objects.get(desc=desc)
            parent = node.get_parent()
            if expected:
                assert parent.desc == expected
            else:
                assert parent is None
            objs[desc] = node
            # corrupt the objects' parent cache
            node._parent_obj = 'CORRUPTED!!!'

        for desc, expected in data.items():
            node = objs[desc]
            # asking get_parent to not use the parent cache (since we
            # corrupted it in the previous loop)
            parent = node.get_parent(True)
            if expected:
                assert parent.desc == expected
            else:
                assert parent is None

    def test_get_children(self, model):
        data = [
            ('2', ['21', '22', '23', '24']),
            ('23', ['231']),
            ('231', []),
        ]
        for desc, expected in data:
            children = model.objects.get(desc=desc).get_children()
            assert [node.desc for node in children] == expected

    def test_get_children_count(self, model):
        data = [
            ('2', 4),
            ('23', 1),
            ('231', 0),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).get_children_count()
            assert got == expected

    def test_get_siblings(self, model):
        data = [
            ('2', ['1', '2', '3', '4']),
            ('21', ['21', '22', '23', '24']),
            ('231', ['231']),
        ]
        for desc, expected in data:
            siblings = model.objects.get(desc=desc).get_siblings()
            assert [node.desc for node in siblings] == expected

    def test_get_first_sibling(self, model):
        data = [
            ('2', '1'),
            ('1', '1'),
            ('4', '1'),
            ('21', '21'),
            ('24', '21'),
            ('22', '21'),
            ('231', '231'),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_first_sibling()
            assert node.desc == expected

    def test_get_prev_sibling(self, model):
        data = [
            ('2', '1'),
            ('1', None),
            ('4', '3'),
            ('21', None),
            ('24', '23'),
            ('22', '21'),
            ('231', None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_prev_sibling()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected

    def test_get_next_sibling(self, model):
        data = [
            ('2', '3'),
            ('1', '2'),
            ('4', None),
            ('21', '22'),
            ('24', None),
            ('22', '23'),
            ('231', None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_next_sibling()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected

    def test_get_last_sibling(self, model):
        data = [
            ('2', '4'),
            ('1', '4'),
            ('4', '4'),
            ('21', '24'),
            ('24', '24'),
            ('22', '24'),
            ('231', '231'),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_last_sibling()
            assert node.desc == expected

    def test_get_first_child(self, model):
        data = [
            ('2', '21'),
            ('21', None),
            ('23', '231'),
            ('231', None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_first_child()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected

    def test_get_last_child(self, model):
        data = [
            ('2', '24'),
            ('21', None),
            ('23', '231'),
            ('231', None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_last_child()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected

    def test_get_ancestors(self, model):
        data = [
            ('2', []),
            ('21', ['2']),
            ('231', ['2', '23']),
        ]
        for desc, expected in data:
            nodes = model.objects.get(desc=desc).get_ancestors()
            assert [node.desc for node in nodes] == expected

    def test_get_descendants(self, model):
        data = [
            ('2', ['21', '22', '23', '231', '24']),
            ('23', ['231']),
            ('231', []),
            ('1', []),
            ('4', ['41']),
        ]
        for desc, expected in data:
            nodes = model.objects.get(desc=desc).get_descendants()
            assert [node.desc for node in nodes] == expected

    def test_get_descendant_count(self, model):
        data = [
            ('2', 5),
            ('23', 1),
            ('231', 0),
            ('1', 0),
            ('4', 1),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).get_descendant_count()
            assert got == expected

    def test_is_sibling_of(self, model):
        data = [
            ('2', '2', True),
            ('2', '1', True),
            ('21', '2', False),
            ('231', '2', False),
            ('22', '23', True),
            ('231', '23', False),
            ('231', '231', True),
        ]
        for desc1, desc2, expected in data:
            node1 = model.objects.get(desc=desc1)
            node2 = model.objects.get(desc=desc2)
            assert node1.is_sibling_of(node2) == expected

    def test_is_child_of(self, model):
        data = [
            ('2', '2', False),
            ('2', '1', False),
            ('21', '2', True),
            ('231', '2', False),
            ('231', '23', True),
            ('231', '231', False),
        ]
        for desc1, desc2, expected in data:
            node1 = model.objects.get(desc=desc1)
            node2 = model.objects.get(desc=desc2)
            assert node1.is_child_of(node2) == expected

    def test_is_descendant_of(self, model):
        data = [
            ('2', '2', False),
            ('2', '1', False),
            ('21', '2', True),
            ('231', '2', True),
            ('231', '23', True),
            ('231', '231', False),
        ]
        for desc1, desc2, expected in data:
            node1 = model.objects.get(desc=desc1)
            node2 = model.objects.get(desc=desc2)
            assert node1.is_descendant_of(node2) == expected


class TestAddChild(TestNonEmptyTree):
    def test_add_child_to_leaf(self, model):
        model.objects.get(desc='231').add_child(desc='2311')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 1),
                    ('2311', 4, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_child_to_node(self, model):
        model.objects.get(desc='2').add_child(desc='25')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('25', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected


class TestAddSibling(TestNonEmptyTree):
    def test_add_sibling_invalid_pos(self, model):
        with pytest.raises(InvalidPosition):
            model.objects.get(desc='231').add_sibling('invalid_pos')

    def test_add_sibling_missing_nodeorderby(self, model):
        node_wchildren = model.objects.get(desc='2')
        with pytest.raises(MissingNodeOrderBy):
            node_wchildren.add_sibling('sorted-sibling', desc='aaa')

    def test_add_sibling_last_root(self, model):
        node_wchildren = model.objects.get(desc='2')
        obj = node_wchildren.add_sibling('last-sibling', desc='5')
        assert obj.get_depth() == 1
        assert node_wchildren.get_last_sibling().desc == '5'

    def test_add_sibling_last(self, model):
        node = model.objects.get(desc='231')
        obj = node.add_sibling('last-sibling', desc='232')
        assert obj.get_depth() == 3
        assert node.get_last_sibling().desc == '232'

    def test_add_sibling_first_root(self, model):
        node_wchildren = model.objects.get(desc='2')
        obj = node_wchildren.add_sibling('first-sibling', desc='new')
        assert obj.get_depth() == 1
        expected = [('new', 1, 0),
                    ('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_first(self, model):
        node_wchildren = model.objects.get(desc='23')
        obj = node_wchildren.add_sibling('first-sibling', desc='new')
        assert obj.get_depth() == 2
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('new', 2, 0),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_left_root(self, model):
        node_wchildren = model.objects.get(desc='2')
        obj = node_wchildren.add_sibling('left', desc='new')
        assert obj.get_depth() == 1
        expected = [('1', 1, 0),
                    ('new', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_left(self, model):
        node_wchildren = model.objects.get(desc='23')
        obj = node_wchildren.add_sibling('left', desc='new')
        assert obj.get_depth() == 2
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('new', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_left_noleft_root(self, model):
        node = model.objects.get(desc='1')
        obj = node.add_sibling('left', desc='new')
        assert obj.get_depth() == 1
        expected = [('new', 1, 0),
                    ('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_left_noleft(self, model):
        node = model.objects.get(desc='231')
        obj = node.add_sibling('left', desc='new')
        assert obj.get_depth() == 3
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 2),
                    ('new', 3, 0),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_right_root(self, model):
        node_wchildren = model.objects.get(desc='2')
        obj = node_wchildren.add_sibling('right', desc='new')
        assert obj.get_depth() == 1
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('new', 1, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_right(self, model):
        node_wchildren = model.objects.get(desc='23')
        obj = node_wchildren.add_sibling('right', desc='new')
        assert obj.get_depth() == 2
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('new', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_add_sibling_right_noright_root(self, model):
        node = model.objects.get(desc='4')
        obj = node.add_sibling('right', desc='new')
        assert obj.get_depth() == 1
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0),
                    ('new', 1, 0)]
        assert self.got(model) == expected

    def test_add_sibling_right_noright(self, model):
        node = model.objects.get(desc='231')
        obj = node.add_sibling('right', desc='new')
        assert obj.get_depth() == 3
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 2),
                    ('231', 3, 0),
                    ('new', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected


class TestDelete(TestNonEmptyTree):

    @classmethod
    def setup_class(cls):
        TestNonEmptyTree.setup_class()
        for model, dep_model in zip(models.BASE_MODELS, models.DEP_MODELS):
            for node in model.objects.all():
                dep_model(node=node).save()

    @classmethod
    def teardown_class(cls):
        models.empty_models_tables(models.DEP_MODELS + models.BASE_MODELS)

    def test_delete_leaf(self, model):
        model.objects.get(desc='231').delete()
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_delete_node(self, model):
        model.objects.get(desc='23').delete()
        expected = [('1', 1, 0),
                    ('2', 1, 3),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_delete_root(self, model):
        model.objects.get(desc='2').delete()
        expected = [('1', 1, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_delete_filter_root_nodes(self, model):
        model.objects.filter(desc__in=('2', '3')).delete()
        expected = [('1', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_delete_filter_children(self, model):
        model.objects.filter(desc__in=('2', '23', '231')).delete()
        expected = [('1', 1, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_delete_nonexistant_nodes(self, model):
        model.objects.filter(desc__in=('ZZZ', 'XXX')).delete()
        assert self.got(model) == UNCHANGED

    def test_delete_same_node_twice(self, model):
        model.objects.filter(desc__in=('2', '2')).delete()
        expected = [('1', 1, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_delete_all_root_nodes(self, model):
        model.get_root_nodes().delete()
        count = model.objects.count()
        assert count == 0

    def test_delete_all_nodes(self, model):
        model.objects.all().delete()
        count = model.objects.count()
        assert count == 0


class TestMoveErrors(TestNonEmptyTree):
    def test_move_invalid_pos(self, model):
        node = model.objects.get(desc='231')
        with pytest.raises(InvalidPosition):
            node.move(node, 'invalid_pos')

    def test_move_to_descendant(self, model):
        node = model.objects.get(desc='2')
        target = model.objects.get(desc='231')
        with pytest.raises(InvalidMoveToDescendant):
            node.move(target, 'first-sibling')

    def test_move_missing_nodeorderby(self, model):
        node = model.objects.get(desc='231')
        with pytest.raises(MissingNodeOrderBy):
            node.move(node, 'sorted-child')
        with pytest.raises(MissingNodeOrderBy):
            node.move(node, 'sorted-sibling')


class TestMoveSortedErrors(TestTreeBase):

    def test_nonsorted_move_in_sorted(self, sorted_model):
        node = sorted_model.add_root(val1=3, val2=3, desc='zxy')
        with pytest.raises(InvalidPosition):
            node.move(node, 'left')


class TestMoveLeafRoot(TestNonEmptyTree):
    def test_move_leaf_last_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='231').move(target, 'last-sibling')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0),
                    ('231', 1, 0)]
        assert self.got(model) == expected

    def test_move_leaf_first_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='231').move(target, 'first-sibling')
        expected = [('231', 1, 0),
                    ('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_left_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='231').move(target, 'left')
        expected = [('1', 1, 0),
                    ('231', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_right_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='231').move(target, 'right')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('231', 1, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_last_child_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='231').move(target, 'last-child')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('231', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_first_child_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='231').move(target, 'first-child')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('231', 2, 0),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected


class TestMoveLeaf(TestNonEmptyTree):
    def test_move_leaf_last_sibling(self, model):
        target = model.objects.get(desc='22')
        model.objects.get(desc='231').move(target, 'last-sibling')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('231', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_first_sibling(self, model):
        target = model.objects.get(desc='22')
        model.objects.get(desc='231').move(target, 'first-sibling')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('231', 2, 0),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_left_sibling(self, model):
        target = model.objects.get(desc='22')
        model.objects.get(desc='231').move(target, 'left')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('231', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_right_sibling(self, model):
        target = model.objects.get(desc='22')
        model.objects.get(desc='231').move(target, 'right')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('231', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_left_sibling_itself(self, model):
        target = model.objects.get(desc='231')
        model.objects.get(desc='231').move(target, 'left')
        assert self.got(model) == UNCHANGED

    def test_move_leaf_last_child(self, model):
        target = model.objects.get(desc='22')
        model.objects.get(desc='231').move(target, 'last-child')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 1),
                    ('231', 3, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_leaf_first_child(self, model):
        target = model.objects.get(desc='22')
        model.objects.get(desc='231').move(target, 'first-child')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 1),
                    ('231', 3, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected


class TestMoveBranchRoot(TestNonEmptyTree):
    def test_move_branch_first_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='4').move(target, 'first-sibling')
        expected = [('4', 1, 1),
                    ('41', 2, 0),
                    ('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_last_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='4').move(target, 'last-sibling')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_branch_left_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='4').move(target, 'left')
        expected = [('1', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_right_sibling_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='4').move(target, 'right')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('4', 1, 1),
                    ('41', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_left_noleft_sibling_root(self, model):
        target = model.objects.get(desc='2').get_first_sibling()
        model.objects.get(desc='4').move(target, 'left')
        expected = [('4', 1, 1),
                    ('41', 2, 0),
                    ('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_right_noright_sibling_root(self, model):
        target = model.objects.get(desc='2').get_last_sibling()
        model.objects.get(desc='4').move(target, 'right')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_branch_first_child_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='4').move(target, 'first-child')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_last_child_root(self, model):
        target = model.objects.get(desc='2')
        model.objects.get(desc='4').move(target, 'last-child')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected


class TestMoveBranch(TestNonEmptyTree):
    def test_move_branch_first_sibling(self, model):
        target = model.objects.get(desc='23')
        model.objects.get(desc='4').move(target, 'first-sibling')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_last_sibling(self, model):
        target = model.objects.get(desc='23')
        model.objects.get(desc='4').move(target, 'last-sibling')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_left_sibling(self, model):
        target = model.objects.get(desc='23')
        model.objects.get(desc='4').move(target, 'left')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_right_sibling(self, model):
        target = model.objects.get(desc='23')
        model.objects.get(desc='4').move(target, 'right')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_left_noleft_sibling(self, model):
        target = model.objects.get(desc='23').get_first_sibling()
        model.objects.get(desc='4').move(target, 'left')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_right_noright_sibling(self, model):
        target = model.objects.get(desc='23').get_last_sibling()
        model.objects.get(desc='4').move(target, 'right')
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 1),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('4', 2, 1),
                    ('41', 3, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_left_itself_sibling(self, model):
        target = model.objects.get(desc='4')
        model.objects.get(desc='4').move(target, 'left')
        assert self.got(model) == UNCHANGED

    def test_move_branch_first_child(self, model):
        target = model.objects.get(desc='23')
        model.objects.get(desc='4').move(target, 'first-child')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 2),
                    ('4', 3, 1),
                    ('41', 4, 0),
                    ('231', 3, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected

    def test_move_branch_last_child(self, model):
        target = model.objects.get(desc='23')
        model.objects.get(desc='4').move(target, 'last-child')
        expected = [('1', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 2),
                    ('231', 3, 0),
                    ('4', 3, 1),
                    ('41', 4, 0),
                    ('24', 2, 0),
                    ('3', 1, 0)]
        assert self.got(model) == expected


class TestTreeSorted(TestTreeBase):

    def got(self, sorted_model):
        return [(o.val1, o.val2, o.desc, o.get_depth(), o.get_children_count())
                for o in sorted_model.get_tree()]

    def test_add_root_sorted(self, sorted_model):
        sorted_model.add_root(val1=3, val2=3, desc='zxy')
        sorted_model.add_root(val1=1, val2=4, desc='bcd')
        sorted_model.add_root(val1=2, val2=5, desc='zxy')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=4, val2=1, desc='fgh')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=2, val2=2, desc='qwe')
        sorted_model.add_root(val1=3, val2=2, desc='vcx')
        expected = [(1, 4, 'bcd', 1, 0),
                    (2, 2, 'qwe', 1, 0),
                    (2, 5, 'zxy', 1, 0),
                    (3, 2, 'vcx', 1, 0),
                    (3, 3, 'abc', 1, 0),
                    (3, 3, 'abc', 1, 0),
                    (3, 3, 'zxy', 1, 0),
                    (4, 1, 'fgh', 1, 0)]
        assert self.got(sorted_model) == expected

    def test_add_child_root_sorted(self, sorted_model):
        root = sorted_model.add_root(val1=0, val2=0, desc='aaa')
        root.add_child(val1=3, val2=3, desc='zxy')
        root.add_child(val1=1, val2=4, desc='bcd')
        root.add_child(val1=2, val2=5, desc='zxy')
        root.add_child(val1=3, val2=3, desc='abc')
        root.add_child(val1=4, val2=1, desc='fgh')
        root.add_child(val1=3, val2=3, desc='abc')
        root.add_child(val1=2, val2=2, desc='qwe')
        root.add_child(val1=3, val2=2, desc='vcx')
        expected = [(0, 0, 'aaa', 1, 8),
                    (1, 4, 'bcd', 2, 0),
                    (2, 2, 'qwe', 2, 0),
                    (2, 5, 'zxy', 2, 0),
                    (3, 2, 'vcx', 2, 0),
                    (3, 3, 'abc', 2, 0),
                    (3, 3, 'abc', 2, 0),
                    (3, 3, 'zxy', 2, 0),
                    (4, 1, 'fgh', 2, 0)]
        assert self.got(sorted_model) == expected

    def test_add_child_nonroot_sorted(self, sorted_model):
        get_node = lambda node_id: sorted_model.objects.get(pk=node_id)

        root_id = sorted_model.add_root(val1=0, val2=0, desc='a').pk
        node_id = get_node(root_id).add_child(val1=0, val2=0, desc='ac').pk
        get_node(root_id).add_child(val1=0, val2=0, desc='aa')
        get_node(root_id).add_child(val1=0, val2=0, desc='av')
        get_node(node_id).add_child(val1=0, val2=0, desc='aca')
        get_node(node_id).add_child(val1=0, val2=0, desc='acc')
        get_node(node_id).add_child(val1=0, val2=0, desc='acb')

        expected = [(0, 0, 'a', 1, 3),
                    (0, 0, 'aa', 2, 0),
                    (0, 0, 'ac', 2, 3),
                    (0, 0, 'aca', 3, 0),
                    (0, 0, 'acb', 3, 0),
                    (0, 0, 'acc', 3, 0),
                    (0, 0, 'av', 2, 0)]
        assert self.got(sorted_model) == expected

    def test_move_sorted(self, sorted_model):
        sorted_model.add_root(val1=3, val2=3, desc='zxy')
        sorted_model.add_root(val1=1, val2=4, desc='bcd')
        sorted_model.add_root(val1=2, val2=5, desc='zxy')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=4, val2=1, desc='fgh')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=2, val2=2, desc='qwe')
        sorted_model.add_root(val1=3, val2=2, desc='vcx')
        root_nodes = sorted_model.get_root_nodes()
        target = root_nodes[0]
        for node in root_nodes[1:]:
            # because raw queries don't update django objects
            node = sorted_model.objects.get(pk=node.pk)
            target = sorted_model.objects.get(pk=target.pk)
            node.move(target, 'sorted-child')
        expected = [(1, 4, 'bcd', 1, 7),
                    (2, 2, 'qwe', 2, 0),
                    (2, 5, 'zxy', 2, 0),
                    (3, 2, 'vcx', 2, 0),
                    (3, 3, 'abc', 2, 0),
                    (3, 3, 'abc', 2, 0),
                    (3, 3, 'zxy', 2, 0),
                    (4, 1, 'fgh', 2, 0)]
        assert self.got(sorted_model) == expected

    def test_move_sortedsibling(self, sorted_model):
        # https://bitbucket.org/tabo/django-treebeard/issue/27
        sorted_model.add_root(val1=3, val2=3, desc='zxy')
        sorted_model.add_root(val1=1, val2=4, desc='bcd')
        sorted_model.add_root(val1=2, val2=5, desc='zxy')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=4, val2=1, desc='fgh')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=2, val2=2, desc='qwe')
        sorted_model.add_root(val1=3, val2=2, desc='vcx')
        root_nodes = sorted_model.get_root_nodes()
        target = root_nodes[0]
        for node in root_nodes[1:]:
            # because raw queries don't update django objects
            node = sorted_model.objects.get(pk=node.pk)
            target = sorted_model.objects.get(pk=target.pk)
            node.val1 -= 2
            node.save()
            node.move(target, 'sorted-sibling')
        expected = [(0, 2, 'qwe', 1, 0),
                    (0, 5, 'zxy', 1, 0),
                    (1, 2, 'vcx', 1, 0),
                    (1, 3, 'abc', 1, 0),
                    (1, 3, 'abc', 1, 0),
                    (1, 3, 'zxy', 1, 0),
                    (1, 4, 'bcd', 1, 0),
                    (2, 1, 'fgh', 1, 0)]
        assert self.got(sorted_model) == expected


class TestMP_TreeAlphabet(TestTreeBase):
    def test_alphabet(self, mpalphabet_model):
        if not os.getenv('TREEBEARD_TEST_ALPHABET', False):
            # run this test only if the enviroment variable is set
            return
        basealpha = numconv.BASE85
        got_err = False
        last_good = None
        for alphabetlen in range(35, len(basealpha) + 1):
            alphabet = basealpha[0:alphabetlen]
            expected = [alphabet[0] + char for char in alphabet[1:]]
            expected.extend([alphabet[1] + char for char in alphabet])
            expected.append(alphabet[2] + alphabet[0])

            # remove all nodes
            mpalphabet_model.objects.all().delete()

            # change the model's alphabet
            mpalphabet_model.alphabet = alphabet

            # insert root nodes
            for pos in range(len(alphabet) * 2):
                try:
                    mpalphabet_model.add_root(numval=pos)
                except:
                    got_err = True
                    break
            if got_err:
                break
            got = [obj.path
                   for obj in mpalphabet_model.objects.all()]
            if got != expected:
                got_err = True
            last_good = alphabet
        sys.stdout.write(
            '\nThe best BASE85 based alphabet for your setup is: %s\n' % (
                last_good, )
        )
        sys.stdout.flush()


class TestHelpers(TestTreeBase):

    @classmethod
    def setup_class(cls):
        for model in models.BASE_MODELS:
            model.load_bulk(BASE_DATA)
            for node in model.get_root_nodes():
                model.load_bulk(BASE_DATA, node)
            model.add_root(desc='5')

    @classmethod
    def teardown_class(cls):
        models.empty_models_tables(models.BASE_MODELS)

    def test_descendants_group_count_root(self, model):
        expected = [(o.desc, o.get_descendant_count())
                    for o in model.get_root_nodes()]
        got = [(o.desc, o.descendants_count)
               for o in model.get_descendants_group_count()]
        assert got == expected

    def test_descendants_group_count_node(self, model):
        parent = model.get_root_nodes().get(desc='2')
        expected = [(o.desc, o.get_descendant_count())
                    for o in parent.get_children()]
        got = [(o.desc, o.descendants_count)
               for o in model.get_descendants_group_count(parent)]
        assert got == expected


class TestMP_TreeSortedAutoNow(TestTreeBase):
    """
    The sorting mechanism used by treebeard when adding a node can fail if the
    ordering is using an "auto_now" field
    """

    def test_sorted_by_autonow_workaround(self, mpsortedautonow_model):
        # workaround
        for i in range(1, 5):
            mpsortedautonow_model.add_root(desc='node%d' % (i, ),
                                           created=datetime.datetime.now())

    def test_sorted_by_autonow_FAIL(self, mpsortedautonow_model):
        """
        This test asserts that we have a problem.
        fix this, somehow
        """
        mpsortedautonow_model.add_root(desc='node1')
        with pytest.raises(ValueError):
            mpsortedautonow_model.add_root(desc='node2')


class TestMP_TreeStepOverflow(TestTreeBase):
    def test_add_root(self, mpsmallstep_model):
        method = mpsmallstep_model.add_root
        for i in range(1, 10):
            method()
        with pytest.raises(PathOverflow):
            method()

    def test_add_child(self, mpsmallstep_model):
        root = mpsmallstep_model.add_root()
        method = root.add_child
        for i in range(1, 10):
            method()
        with pytest.raises(PathOverflow):
            method()

    def test_add_sibling(self, mpsmallstep_model):
        root = mpsmallstep_model.add_root()
        for i in range(1, 10):
            root.add_child()
        positions = ('first-sibling', 'left', 'right', 'last-sibling')
        for pos in positions:
            with pytest.raises(PathOverflow):
                root.get_last_child().add_sibling(pos)

    def test_move(self, mpsmallstep_model):
        root = mpsmallstep_model.add_root()
        for i in range(1, 10):
            root.add_child()
        newroot = mpsmallstep_model.add_root()
        targets = [(root, ['first-child', 'last-child']),
                   (root.get_first_child(), ['first-sibling',
                                             'left',
                                             'right',
                                             'last-sibling'])]
        for target, positions in targets:
            for pos in positions:
                with pytest.raises(PathOverflow):
                    newroot.move(target, pos)


class TestMP_TreeShortPath(TestTreeBase):
    """Test a tree with a very small path field (max_length=4) and a
    steplen of 1
    """

    def test_short_path(self, mpshortnotsorted_model):
        obj = mpshortnotsorted_model.add_root()
        obj = obj.add_child().add_child().add_child()
        with pytest.raises(PathOverflow):
            obj.add_child()


class TestMP_TreeFindProblems(TestTreeBase):
    def test_find_problems(self, mpalphabet_model):
        mpalphabet_model.alphabet = '01234'
        mpalphabet_model(path='01', depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path='1', depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path='111', depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path='abcd', depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path='qa#$%!', depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path='0201', depth=2, numchild=0, numval=0).save()
        mpalphabet_model(path='020201', depth=3, numchild=0, numval=0).save()
        mpalphabet_model(path='03', depth=1, numchild=2, numval=0).save()
        mpalphabet_model(path='0301', depth=2, numchild=0, numval=0).save()
        mpalphabet_model(path='030102', depth=3, numchild=10, numval=0).save()
        mpalphabet_model(path='04', depth=10, numchild=1, numval=0).save()
        mpalphabet_model(path='0401', depth=20, numchild=0, numval=0).save()

        def got(ids):
            return [o.path for o in
                    mpalphabet_model.objects.filter(id__in=ids)]

        (evil_chars, bad_steplen, orphans, wrong_depth, wrong_numchild) = (
            mpalphabet_model.find_problems())
        assert ['abcd', 'qa#$%!'] == got(evil_chars)
        assert ['1', '111'] == got(bad_steplen)
        assert ['0201', '020201'] == got(orphans)
        assert ['03', '0301', '030102'] == got(wrong_numchild)
        assert ['04', '0401'] == got(wrong_depth)


class TestMP_TreeFix(TestTreeBase):

    expected_no_holes = {
        models.MP_TestNodeShortPath: [
            ('1', 'b', 1, 2),
            ('11', 'u', 2, 1),
            ('111', 'i', 3, 1),
            ('1111', 'e', 4, 0),
            ('12', 'o', 2, 0),
            ('2', 'd', 1, 0),
            ('3', 'g', 1, 0),
            ('4', 'a', 1, 4),
            ('41', 'a', 2, 0),
            ('42', 'a', 2, 0),
            ('43', 'u', 2, 1),
            ('431', 'i', 3, 1),
            ('4311', 'e', 4, 0),
            ('44', 'o', 2, 0)],
        models.MP_TestSortedNodeShortPath: [
            ('1', 'a', 1, 4),
            ('11', 'a', 2, 0),
            ('12', 'a', 2, 0),
            ('13', 'o', 2, 0),
            ('14', 'u', 2, 1),
            ('141', 'i', 3, 1),
            ('1411', 'e', 4, 0),
            ('2', 'b', 1, 2),
            ('21', 'o', 2, 0),
            ('22', 'u', 2, 1),
            ('221', 'i', 3, 1),
            ('2211', 'e', 4, 0),
            ('3', 'd', 1, 0),
            ('4', 'g', 1, 0)]}
    expected_with_holes = {
        models.MP_TestNodeShortPath: [
            ('1', 'b', 1, 2),
            ('13', 'u', 2, 1),
            ('134', 'i', 3, 1),
            ('1343', 'e', 4, 0),
            ('14', 'o', 2, 0),
            ('2', 'd', 1, 0),
            ('3', 'g', 1, 0),
            ('4', 'a', 1, 4),
            ('41', 'a', 2, 0),
            ('42', 'a', 2, 0),
            ('43', 'u', 2, 1),
            ('434', 'i', 3, 1),
            ('4343', 'e', 4, 0),
            ('44', 'o', 2, 0)],
        models.MP_TestSortedNodeShortPath: [
            ('1', 'b', 1, 2),
            ('13', 'u', 2, 1),
            ('134', 'i', 3, 1),
            ('1343', 'e', 4, 0),
            ('14', 'o', 2, 0),
            ('2', 'd', 1, 0),
            ('3', 'g', 1, 0),
            ('4', 'a', 1, 4),
            ('41', 'a', 2, 0),
            ('42', 'a', 2, 0),
            ('43', 'u', 2, 1),
            ('434', 'i', 3, 1),
            ('4343', 'e', 4, 0),
            ('44', 'o', 2, 0)]}

    def got(self, model):
        return [(o.path, o.desc, o.get_depth(), o.get_children_count())
                for o in model.get_tree()]

    def add_broken_test_data(self, model):
        model(path='4', depth=2, numchild=2, desc='a').save()
        model(path='13', depth=1000, numchild=0, desc='u').save()
        model(path='14', depth=4, numchild=500, desc='o').save()
        model(path='134', depth=321, numchild=543, desc='i').save()
        model(path='1343', depth=321, numchild=543, desc='e').save()
        model(path='42', depth=1, numchild=1, desc='a').save()
        model(path='43', depth=1000, numchild=0, desc='u').save()
        model(path='44', depth=4, numchild=500, desc='o').save()
        model(path='434', depth=321, numchild=543, desc='i').save()
        model(path='4343', depth=321, numchild=543, desc='e').save()
        model(path='41', depth=1, numchild=1, desc='a').save()
        model(path='3', depth=221, numchild=322, desc='g').save()
        model(path='1', depth=10, numchild=3, desc='b').save()
        model(path='2', depth=10, numchild=3, desc='d').save()

    def test_fix_tree_non_destructive(self, mpshort_model):
        self.add_broken_test_data(mpshort_model)
        mpshort_model.fix_tree(destructive=False)
        got = self.got(mpshort_model)
        expected = self.expected_with_holes[mpshort_model]
        assert got == expected
        mpshort_model.find_problems()

    def test_fix_tree_destructive(self, mpshort_model):
        self.add_broken_test_data(mpshort_model)
        mpshort_model.fix_tree(destructive=True)
        got = self.got(mpshort_model)
        expected = self.expected_no_holes[mpshort_model]
        assert got == expected
        mpshort_model.find_problems()


class TestIssues(TestTreeBase):
    # test for http://code.google.com/p/django-treebeard/issues/detail?id=14

    def test_many_to_many_django_user_anonymous(self, mpm2muser_model):
        # Using AnonymousUser() in the querysets will expose non-treebeard
        # related problems in Django 1.0
        #
        # Postgres:
        #   ProgrammingError: can't adapt
        # SQLite:
        #   InterfaceError: Error binding parameter 4 - probably unsupported
        #   type.
        # MySQL compared a string to an integer field:
        #   `treebeard_mp_testissue14_users`.`user_id` = 'AnonymousUser'
        #
        # Using a None field instead works (will be translated to IS NULL).
        #
        # anonuserobj = AnonymousUser()
        anonuserobj = None

        def qs_check(qs, expected):
            assert [o.name for o in qs] == expected

        def qs_check_first_or_user(expected, root, user):
            qs_check(
                root.get_children().filter(Q(name="first") | Q(users=user)),
                expected)

        user = User.objects.create_user('test_user', 'test@example.com',
                                        'testpasswd')
        user.save()
        root = mpm2muser_model.add_root(name="the root node")

        root.add_child(name="first")
        second = root.add_child(name="second")

        qs_check(root.get_children(), ['first', 'second'])
        qs_check(root.get_children().filter(Q(name="first")), ['first'])
        qs_check(root.get_children().filter(Q(users=user)), [])

        qs_check_first_or_user(['first'], root, user)

        qs_check_first_or_user(['first', 'second'], root, anonuserobj)

        user = User.objects.get(username="test_user")
        second.users.add(user)
        qs_check_first_or_user(['first', 'second'], root, user)

        qs_check_first_or_user(['first'], root, anonuserobj)


class TestMoveNodeForm(TestNonEmptyTree):
    def _get_nodes_list(self, nodes):
        return [(pk, '%sNode %d' % ('&nbsp;' * 4 * (depth - 1), pk))
                for pk, depth in nodes]

    def _assert_nodes_in_choices(self, form, nodes):
        choices = form.fields['_ref_node_id'].choices
        assert 0 == choices.pop(0)[0]
        assert nodes == [(choice[0], choice[1]) for choice in choices]

    def _move_node_helper(self, node, safe_parent_nodes):
        form_class = movenodeform_factory(type(node))
        form = form_class(instance=node)
        assert ['desc', '_position', '_ref_node_id'] == list(
            form.base_fields.keys())
        got = [choice[0] for choice in form.fields['_position'].choices]
        assert ['first-child', 'left', 'right'] == got
        nodes = self._get_nodes_list(safe_parent_nodes)
        self._assert_nodes_in_choices(form, nodes)

    def _get_node_ids_and_depths(self, nodes):
        return [(node.id, node.get_depth()) for node in nodes]

    def test_form_root_node(self, model):
        nodes = list(model.get_tree())
        node = nodes.pop(0)
        safe_parent_nodes = self._get_node_ids_and_depths(nodes)
        self._move_node_helper(node, safe_parent_nodes)

    def test_form_leaf_node(self, model):
        nodes = list(model.get_tree())
        node = nodes.pop()
        safe_parent_nodes = self._get_node_ids_and_depths(nodes)
        self._move_node_helper(node, safe_parent_nodes)

    def test_form_admin(self, model):
        request = None
        nodes = list(model.get_tree())
        safe_parent_nodes = self._get_node_ids_and_depths(nodes)
        for node in model.objects.all():
            site = AdminSite()
            form_class = movenodeform_factory(model)
            admin_class = admin_factory(form_class)
            ma = admin_class(model, site)
            got = list(ma.get_form(request).base_fields.keys())
            desc_pos_refnodeid = ['desc', '_position', '_ref_node_id']
            assert desc_pos_refnodeid == got
            got = ma.get_fieldsets(request)
            expected = [(None, {'fields': desc_pos_refnodeid})]
            assert got == expected
            got = ma.get_fieldsets(request, node)
            assert got == expected
            form = ma.get_form(request)()
            nodes = self._get_nodes_list(safe_parent_nodes)
            self._assert_nodes_in_choices(form, nodes)


class TestModelAdmin(TestNonEmptyTree):
    def test_default_fields(self, model):
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        ma = admin_class(model, site)
        assert list(ma.get_form(None).base_fields.keys()) == [
            'desc', '_position', '_ref_node_id']


class TestSortedForm(TestTreeSorted):
    def test_sorted_form(self, sorted_model):
        sorted_model.add_root(val1=3, val2=3, desc='zxy')
        sorted_model.add_root(val1=1, val2=4, desc='bcd')
        sorted_model.add_root(val1=2, val2=5, desc='zxy')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=4, val2=1, desc='fgh')
        sorted_model.add_root(val1=3, val2=3, desc='abc')
        sorted_model.add_root(val1=2, val2=2, desc='qwe')
        sorted_model.add_root(val1=3, val2=2, desc='vcx')

        form_class = movenodeform_factory(sorted_model)
        form = form_class()
        assert list(form.fields.keys()) == ['val1', 'val2', 'desc',
                                            '_position', '_ref_node_id']

        form = form_class(instance=sorted_model.objects.get(desc='bcd'))
        assert list(form.fields.keys()) == ['val1', 'val2', 'desc',
                                            '_position', '_ref_node_id']
        assert 'id__position' in str(form)
        assert 'id__ref_node_id' in str(form)


class TestForm(TestNonEmptyTree):
    def test_form(self, model):
        form_class = movenodeform_factory(model)
        form = form_class()
        assert list(form.fields.keys()) == ['desc', '_position',
                                            '_ref_node_id']

        form = form_class(instance=model.objects.get(desc='1'))
        assert list(form.fields.keys()) == ['desc', '_position',
                                            '_ref_node_id']
        assert 'id__position' in str(form)
        assert 'id__ref_node_id' in str(form)

    def test_get_position_ref_node(self, model):
        form_class = movenodeform_factory(model)

        instance_parent = model.objects.get(desc='1')
        form = form_class(instance=instance_parent)
        assert form._get_position_ref_node(instance_parent) == {
            '_position': 'first-child',
            '_ref_node_id': ''
        }

        instance_child = model.objects.get(desc='21')
        form = form_class(instance=instance_child)
        assert form._get_position_ref_node(instance_child) == {
            '_position': 'first-child',
            '_ref_node_id': model.objects.get(desc='2').pk
        }

        instance_grandchild = model.objects.get(desc='22')
        form = form_class(instance=instance_grandchild)
        assert form._get_position_ref_node(instance_grandchild) == {
            '_position': 'right',
            '_ref_node_id': model.objects.get(desc='21').pk
        }

        instance_grandchild = model.objects.get(desc='231')
        form = form_class(instance=instance_grandchild)
        assert form._get_position_ref_node(instance_grandchild) == {
            '_position': 'first-child',
            '_ref_node_id': model.objects.get(desc='23').pk
        }

    def test_clean_cleaned_data(self, model):
        instance_parent = model.objects.get(desc='1')
        _position = 'first-child'
        _ref_node_id = ''
        form_class = movenodeform_factory(model)
        form = form_class(
            instance=instance_parent,
            data={
                '_position': _position,
                '_ref_node_id': _ref_node_id,
                'desc': instance_parent.desc
            }
        )
        assert form.is_valid()
        assert form._clean_cleaned_data() == (_position, _ref_node_id)

    def test_save_edit(self, model):
        instance_parent = model.objects.get(desc='1')
        original_count = len(model.objects.all())
        form_class = movenodeform_factory(model)
        form = form_class(
            instance=instance_parent,
            data={
                '_position': 'first-child',
                '_ref_node_id': model.objects.get(desc='2').pk,
                'desc': instance_parent.desc
            }
        )
        assert form.is_valid()
        saved_instance = form.save()
        assert original_count == model.objects.all().count()
        assert saved_instance.get_children_count() == 0
        assert saved_instance.get_depth() == 2
        assert not saved_instance.is_root()
        assert saved_instance.is_leaf()

        # Return to original state
        form_class = movenodeform_factory(model)
        form = form_class(
            instance=saved_instance,
            data={
                '_position': 'first-child',
                '_ref_node_id': '',
                'desc': saved_instance.desc
            }
        )
        assert form.is_valid()
        restored_instance = form.save()
        assert original_count == model.objects.all().count()
        assert restored_instance.get_children_count() == 0
        assert restored_instance.get_depth() == 1
        assert restored_instance.is_root()
        assert restored_instance.is_leaf()

    def test_save_new(self, model):
        original_count = model.objects.all().count()
        assert original_count == 10
        _position = 'first-child'
        form_class = movenodeform_factory(model)
        form = form_class(
            data={'_position': _position, 'desc': 'New Form Test'})
        assert form.is_valid()
        assert form.save() is not None
        assert original_count < model.objects.all().count()


class TestAdminTreeTemplateTags(TestCase):
    def test_treebeard_css(self):
        template = Template("{% load admin_tree %}{% treebeard_css %}")
        context = Context()
        rendered = template.render(context)
        expected = ('<link rel="stylesheet" type="text/css" '
                    'href="/treebeard/treebeard-admin.css"/>')
        assert expected == rendered

    def test_treebeard_js(self):
        template = Template("{% load admin_tree %}{% treebeard_js %}")
        context = Context()
        rendered = template.render(context)
        expected = ('<script type="text/javascript" src="jsi18n"></script>'
                    '<script type="text/javascript" '
                    'src="/treebeard/treebeard-admin.js"></script>'
                    '<script>(function($){'
                    'jQuery = $.noConflict(true);'
                    '})(django.jQuery);</script>'
                    '<script type="text/javascript" '
                    'src="/treebeard/jquery-ui-1.8.5.custom.min.js"></script>')
        assert expected == rendered

    def test_get_static_url(self):
        with self.settings(STATIC_URL=None, MEDIA_URL=None):
            assert get_static_url() == '/'
        with self.settings(STATIC_URL='/static/', MEDIA_URL=None):
            assert get_static_url() == '/static/'
        with self.settings(STATIC_URL=None, MEDIA_URL='/media/'):
            assert get_static_url() == '/media/'
        with self.settings(STATIC_URL='/static/', MEDIA_URL='/media/'):
            assert get_static_url() == '/static/'


class TestAdminTree(TestNonEmptyTree):
    template = Template('{% load admin_tree %}{% spaceless %}'
                        '{% result_tree cl request %}{% endspaceless %}')

    def test_result_tree(self, model_without_proxy):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        model = model_without_proxy
        request = RequestFactory().get('/admin/tree/')
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request})
        table_output = self.template.render(context)
        # We have the same amount of drag handlers as objects
        drag_handler = '<td class="drag-handler"><span>&nbsp;</span></td>'
        assert table_output.count(drag_handler) == model.objects.count()
        # All nodes are in the result tree
        for object in model.objects.all():
            url = cl.url_for_result(object)
            node = '<a href="%s">Node %i</a>' % (url, object.pk)
            assert node in table_output
        # Unfiltered
        assert '<input type="hidden" id="has-filters" value="0"/>' in \
               table_output

    def test_unicode_result_tree(self, model_with_unicode):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        model = model_with_unicode
        # Add a unicode description
        model.add_root(desc='áéîøü')
        request = RequestFactory().get('/admin/tree/')
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request})
        table_output = self.template.render(context)
        # We have the same amount of drag handlers as objects
        drag_handler = '<td class="drag-handler"><span>&nbsp;</span></td>'
        assert table_output.count(drag_handler) == model.objects.count()
        # All nodes are in the result tree
        for object in model.objects.all():
            url = cl.url_for_result(object)
            node = '<a href="%s">%s</a>' % (url, object.desc)
            assert node in table_output
        # Unfiltered
        assert '<input type="hidden" id="has-filters" value="0"/>' in \
               table_output

    def test_result_filtered(self, model_without_proxy):
        """ Test template changes with filters or pagination.
        """
        model = model_without_proxy
        # Filtered GET
        request = RequestFactory().get('/admin/tree/?desc=1')
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request})
        table_output = self.template.render(context)
        # Filtered
        assert '<input type="hidden" id="has-filters" value="1"/>' in \
               table_output

        # Not Filtered GET, it should ignore pagination
        request = RequestFactory().get('/admin/tree/?p=1')
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request})
        table_output = self.template.render(context)
        # Not Filtered
        assert '<input type="hidden" id="has-filters" value="0"/>' in \
               table_output

        # Not Filtered GET, it should ignore all
        request = RequestFactory().get('/admin/tree/?all=1')
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request})
        table_output = self.template.render(context)
        # Not Filtered
        assert '<input type="hidden" id="has-filters" value="0"/>' in \
               table_output


class TestAdminTreeList(TestNonEmptyTree):
    template = Template('{% load admin_tree_list %}{% spaceless %}'
                        '{% result_tree cl request %}{% endspaceless %}')

    def test_result_tree_list(self, model_without_proxy):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        model = model_without_proxy
        request = RequestFactory().get('/admin/tree/')
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request})
        table_output = self.template.render(context)

        output_template = '<li><a href="%i/" >Node %i</a>'
        for object in model.objects.all():
            expected_output = output_template % (object.pk, object.pk)
            assert expected_output in table_output

    def test_result_tree_list_with_action(self, model_without_proxy):
        model = model_without_proxy
        request = RequestFactory().get('/admin/tree/')
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request,
                           'action_form': True})
        table_output = self.template.render(context)
        output_template = ('<input type="checkbox" class="action-select" '
                           'value="%i" name="_selected_action" />'
                           '<a href="%i/" >Node %i</a>')

        for object in model.objects.all():
            expected_output = output_template % (object.pk, object.pk,
                                                 object.pk)
            assert expected_output in table_output


    def test_result_tree_list_with_get(self, model_without_proxy):
        model = model_without_proxy
        # Test t GET parameter with value id
        request = RequestFactory().get('/admin/tree/?t=id')
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(request, model, list_display, list_display_links,
                        m.list_filter, m.date_hierarchy, m.search_fields,
                        m.list_select_related, m.list_per_page,
                        m.list_max_show_all, m.list_editable, m)
        cl.formset = None
        context = Context({'cl': cl,
                           'request': request})
        table_output = self.template.render(context)
        output_template = "opener.dismissRelatedLookupPopup(window, '%i');"
        for object in model.objects.all():
            expected_output = output_template % object.pk
            assert expected_output in table_output


class TestTreeAdmin(TestNonEmptyTree):
    site = AdminSite()

    def _create_superuser(self, username):
        return User.objects.create(username=username, is_superuser=True)

    def _mocked_authenticated_request(self, url, user):
        request_factory = RequestFactory()
        request = request_factory.get(url)
        request.user = user
        return request

    def _mocked_request(self, data):
        request_factory = RequestFactory()
        request = request_factory.post('/', data=data)
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def _get_admin_obj(self, model_class):
        form_class = movenodeform_factory(model_class)
        admin_class = admin_factory(form_class)
        return admin_class(model_class, self.site)

    def test_changelist_view(self):
        tmp_user = self._create_superuser('changelist_tmp')
        request = self._mocked_authenticated_request('/', tmp_user)
        admin_obj = self._get_admin_obj(models.AL_TestNode)
        admin_obj.changelist_view(request)
        assert admin_obj.change_list_template == 'admin/tree_list.html'

        admin_obj = self._get_admin_obj(models.MP_TestNode)
        admin_obj.changelist_view(request)
        assert admin_obj.change_list_template != 'admin/tree_list.html'

    def test_get_node(self, model):
        admin_obj = self._get_admin_obj(model)
        target = model.objects.get(desc='2')
        assert admin_obj.get_node(target.pk) == target

    def test_move_node_validate_keyerror(self, model):
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.move_node(request)
        assert response.status_code == 400
        request = self._mocked_request(data={'node_id': 1})
        response = admin_obj.move_node(request)
        assert response.status_code == 400

    def test_move_node_validate_valueerror(self, model):
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={'node_id': 1,
                                             'sibling_id': 2,
                                             'as_child': 'invalid'})
        response = admin_obj.move_node(request)
        assert response.status_code == 400

    def test_move_validate_missing_nodeorderby(self, model):
        node = model.objects.get(desc='231')
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.try_to_move_node(True, node, 'sorted-child',
                                              request, target=node)
        assert response.status_code == 400

        response = admin_obj.try_to_move_node(True, node, 'sorted-sibling',
                                              request, target=node)
        assert response.status_code == 400

    def test_move_validate_invalid_pos(self, model):
        node = model.objects.get(desc='231')
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.try_to_move_node(True, node, 'invalid_pos',
                                              request, target=node)
        assert response.status_code == 400

    def test_move_validate_to_descendant(self, model):
        node = model.objects.get(desc='2')
        target = model.objects.get(desc='231')
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.try_to_move_node(True, node, 'first-sibling',
                                              request, target)
        assert response.status_code == 400

    def test_move_left(self, model):
        node = model.objects.get(desc='231')
        target = model.objects.get(desc='2')

        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={'node_id': node.pk,
                                             'sibling_id': target.pk,
                                             'as_child': 0})
        response = admin_obj.move_node(request)
        assert response.status_code == 200
        expected = [('1', 1, 0),
                    ('231', 1, 0),
                    ('2', 1, 4),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

    def test_move_last_child(self, model):
        node = model.objects.get(desc='231')
        target = model.objects.get(desc='2')

        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={'node_id': node.pk,
                                             'sibling_id': target.pk,
                                             'as_child': 1})
        response = admin_obj.move_node(request)
        assert response.status_code == 200
        expected = [('1', 1, 0),
                    ('2', 1, 5),
                    ('21', 2, 0),
                    ('22', 2, 0),
                    ('23', 2, 0),
                    ('24', 2, 0),
                    ('231', 2, 0),
                    ('3', 1, 0),
                    ('4', 1, 1),
                    ('41', 2, 0)]
        assert self.got(model) == expected

