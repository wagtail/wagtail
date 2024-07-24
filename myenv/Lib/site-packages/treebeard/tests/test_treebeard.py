"""Unit/Functional tests"""

import datetime
import os

from django.contrib.admin.sites import AdminSite
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Template, Context
from django.test import TestCase
from django.test.client import RequestFactory
from django.templatetags.static import static
from django.contrib.admin.options import TO_FIELD_VAR
from django import VERSION as DJANGO_VERSION

import pytest

from treebeard import numconv
from treebeard.admin import admin_factory
from treebeard.exceptions import (
    InvalidPosition,
    InvalidMoveToDescendant,
    PathOverflow,
    MissingNodeOrderBy,
    NodeAlreadySaved,
)
from treebeard.forms import movenodeform_factory
from treebeard.tests import models
from treebeard.tests.admin import register_all as admin_register_all


admin_register_all()


BASE_DATA = [
    {"data": {"desc": "1"}},
    {
        "data": {"desc": "2"},
        "children": [
            {"data": {"desc": "21"}},
            {"data": {"desc": "22"}},
            {
                "data": {"desc": "23"},
                "children": [
                    {"data": {"desc": "231"}},
                ],
            },
            {"data": {"desc": "24"}},
        ],
    },
    {"data": {"desc": "3"}},
    {
        "data": {"desc": "4"},
        "children": [
            {"data": {"desc": "41"}},
        ],
    },
]
UNCHANGED = [
    ("1", 1, 0),
    ("2", 1, 4),
    ("21", 2, 0),
    ("22", 2, 0),
    ("23", 2, 1),
    ("231", 3, 0),
    ("24", 2, 0),
    ("3", 1, 0),
    ("4", 1, 1),
    ("41", 2, 0),
]


@pytest.fixture(scope="function", params=models.BASE_MODELS + models.PROXY_MODELS)
def model(request):
    request.param.load_bulk(BASE_DATA)
    return request.param


@pytest.fixture(scope="function", params=models.BASE_MODELS + models.PROXY_MODELS)
def model_without_data(request):
    return request.param


@pytest.fixture(scope="function", params=models.BASE_MODELS)
def model_without_proxy(request):
    request.param.load_bulk(BASE_DATA)
    return request.param


@pytest.fixture(scope="function", params=models.UNICODE_MODELS)
def model_with_unicode(request):
    return request.param


@pytest.fixture(scope="function", params=models.SORTED_MODELS)
def sorted_model(request):
    return request.param


@pytest.fixture(scope="function", params=models.RELATED_MODELS)
def related_model(request):
    return request.param


@pytest.fixture(scope="function", params=models.INHERITED_MODELS)
def inherited_model(request):
    return request.param


@pytest.fixture(scope="function", params=models.MP_SHORTPATH_MODELS)
def mpshort_model(request):
    return request.param


@pytest.fixture(scope="function", params=[models.MP_TestNodeShortPath])
def mpshortnotsorted_model(request):
    return request.param


@pytest.fixture(scope="function", params=[models.MP_TestNodeAlphabet])
def mpalphabet_model(request):
    return request.param


@pytest.fixture(scope="function", params=[models.MP_TestNodeSortedAutoNow])
def mpsortedautonow_model(request):
    return request.param


@pytest.fixture(scope="function", params=[models.MP_TestNodeSmallStep])
def mpsmallstep_model(request):
    return request.param


@pytest.fixture(scope="function", params=[models.MP_TestManyToManyWithUser])
def mpm2muser_model(request):
    return request.param


# Compat helper, and be dropped after Django 3.2 is dropped
def get_changelist_args(*args):
    new_args = list(args)
    if DJANGO_VERSION > (4,):
        new_args.append("")     # New search_help_text arg
    return new_args


class TestTreeBase:
    def got(self, model):
        if model in [models.NS_TestNode, models.NS_TestNode_Proxy]:
            # this slows down nested sets tests quite a bit, but it has the
            # advantage that we'll check the node edges are correct
            d = {}
            for tree_id, lft, rgt in model.objects.values_list("tree_id", "lft", "rgt"):
                d.setdefault(tree_id, []).extend([lft, rgt])
            for tree_id, got_edges in d.items():
                assert len(got_edges) == max(got_edges)
                good_edges = list(range(1, len(got_edges) + 1))
                assert sorted(got_edges) == good_edges

        return [
            (o.desc, o.get_depth(), o.get_children_count()) for o in model.get_tree()
        ]

    def _assert_get_annotated_list(self, model, expected, parent=None):
        results = model.get_annotated_list(parent)
        got = [
            (obj[0].desc, obj[1]["open"], obj[1]["close"], obj[1]["level"])
            for obj in results
        ]
        assert expected == got
        assert all([type(obj[0]) == model for obj in results])


@pytest.mark.django_db
class TestEmptyTree(TestTreeBase):
    def test_load_bulk_empty(self, model_without_data):
        ids = model_without_data.load_bulk(BASE_DATA)
        got_descs = [obj.desc for obj in model_without_data.objects.filter(pk__in=ids)]
        expected_descs = [x[0] for x in UNCHANGED]
        assert sorted(got_descs) == sorted(expected_descs)
        assert self.got(model_without_data) == UNCHANGED

    def test_dump_bulk_empty(self, model_without_data):
        assert model_without_data.dump_bulk() == []

    def test_add_root_empty(self, model_without_data):
        model_without_data.add_root(desc="1")
        expected = [("1", 1, 0)]
        assert self.got(model_without_data) == expected

    def test_get_root_nodes_empty(self, model_without_data):
        got = model_without_data.get_root_nodes()
        expected = []
        assert [node.desc for node in got] == expected

    def test_get_first_root_node_empty(self, model_without_data):
        got = model_without_data.get_first_root_node()
        assert got is None

    def test_get_last_root_node_empty(self, model_without_data):
        got = model_without_data.get_last_root_node()
        assert got is None

    def test_get_tree(self, model_without_data):
        got = list(model_without_data.get_tree())
        assert got == []

    def test_get_annotated_list(self, model_without_data):
        expected = []
        self._assert_get_annotated_list(model_without_data, expected)

    def test_add_multiple_root_nodes_adds_sibling_leaves(self, model_without_data):
        model_without_data.add_root(desc="1")
        model_without_data.add_root(desc="2")
        model_without_data.add_root(desc="3")
        model_without_data.add_root(desc="4")
        # these are all sibling root nodes (depth=1), and leaf nodes (children=0)
        expected = [("1", 1, 0), ("2", 1, 0), ("3", 1, 0), ("4", 1, 0)]
        assert self.got(model_without_data) == expected


class TestNonEmptyTree(TestTreeBase):
    pass


@pytest.mark.django_db
class TestClassMethods(TestNonEmptyTree):
    def test_load_bulk_existing(self, model):
        # inserting on an existing node
        node = model.objects.get(desc="231")
        ids = model.load_bulk(BASE_DATA, node)
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 4),
            ("1", 4, 0),
            ("2", 4, 4),
            ("21", 5, 0),
            ("22", 5, 0),
            ("23", 5, 1),
            ("231", 6, 0),
            ("24", 5, 0),
            ("3", 4, 0),
            ("4", 4, 1),
            ("41", 5, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        expected_descs = ["1", "2", "21", "22", "23", "231", "24", "3", "4", "41"]
        got_descs = [obj.desc for obj in model.objects.filter(pk__in=ids)]
        assert sorted(got_descs) == sorted(expected_descs)
        assert self.got(model) == expected

    def test_get_tree_all(self, model):
        nodes = model.get_tree()
        got = [(o.desc, o.get_depth(), o.get_children_count()) for o in nodes]
        assert got == UNCHANGED
        assert all([type(o) == model for o in nodes])

    def test_dump_bulk_all(self, model):
        assert model.dump_bulk(keep_ids=False) == BASE_DATA

    def test_get_tree_node(self, model):
        node = model.objects.get(desc="231")
        model.load_bulk(BASE_DATA, node)

        # the tree was modified by load_bulk, so we reload our node object
        node = model.objects.get(pk=node.pk)

        nodes = model.get_tree(node)
        got = [(o.desc, o.get_depth(), o.get_children_count()) for o in nodes]
        expected = [
            ("231", 3, 4),
            ("1", 4, 0),
            ("2", 4, 4),
            ("21", 5, 0),
            ("22", 5, 0),
            ("23", 5, 1),
            ("231", 6, 0),
            ("24", 5, 0),
            ("3", 4, 0),
            ("4", 4, 1),
            ("41", 5, 0),
        ]
        assert got == expected
        assert all([type(o) == model for o in nodes])

    def test_get_tree_leaf(self, model):
        node = model.objects.get(desc="1")

        assert 0 == node.get_children_count()
        nodes = model.get_tree(node)
        got = [(o.desc, o.get_depth(), o.get_children_count()) for o in nodes]
        expected = [("1", 1, 0)]
        assert got == expected
        assert all([type(o) == model for o in nodes])

    def test_get_annotated_list_all(self, model):
        expected = [
            ("1", True, [], 0),
            ("2", False, [], 0),
            ("21", True, [], 1),
            ("22", False, [], 1),
            ("23", False, [], 1),
            ("231", True, [0], 2),
            ("24", False, [0], 1),
            ("3", False, [], 0),
            ("4", False, [], 0),
            ("41", True, [0, 1], 1),
        ]
        self._assert_get_annotated_list(model, expected)

    def test_get_annotated_list_node(self, model):
        node = model.objects.get(desc="2")
        expected = [
            ("2", True, [], 0),
            ("21", True, [], 1),
            ("22", False, [], 1),
            ("23", False, [], 1),
            ("231", True, [0], 2),
            ("24", False, [0, 1], 1),
        ]
        self._assert_get_annotated_list(model, expected, node)

    def test_get_annotated_list_leaf(self, model):
        node = model.objects.get(desc="1")
        expected = [("1", True, [0], 0)]
        self._assert_get_annotated_list(model, expected, node)

    def test_dump_bulk_node(self, model):
        node = model.objects.get(desc="231")
        model.load_bulk(BASE_DATA, node)

        # the tree was modified by load_bulk, so we reload our node object
        node = model.objects.get(pk=node.pk)

        got = model.dump_bulk(node, False)
        expected = [{"data": {"desc": "231"}, "children": BASE_DATA}]
        assert got == expected

    def test_load_and_dump_bulk_keeping_ids(self, model):
        exp = model.dump_bulk(keep_ids=True)
        model.objects.all().delete()
        model.load_bulk(exp, None, True)
        got = model.dump_bulk(keep_ids=True)
        assert got == exp
        # do we really have an unchanged tree after the dump/delete/load?
        got = [
            (o.desc, o.get_depth(), o.get_children_count()) for o in model.get_tree()
        ]
        assert got == UNCHANGED

    def test_load_and_dump_bulk_with_fk(self, related_model):
        # https://bitbucket.org/tabo/django-treebeard/issue/48/
        related_model.objects.all().delete()
        related, created = models.RelatedModel.objects.get_or_create(
            desc="Test %s" % related_model.__name__
        )

        related_data = [
            {"data": {"desc": "1", "related": related.pk}},
            {
                "data": {"desc": "2", "related": related.pk},
                "children": [
                    {"data": {"desc": "21", "related": related.pk}},
                    {"data": {"desc": "22", "related": related.pk}},
                    {
                        "data": {"desc": "23", "related": related.pk},
                        "children": [
                            {"data": {"desc": "231", "related": related.pk}},
                        ],
                    },
                    {"data": {"desc": "24", "related": related.pk}},
                ],
            },
            {"data": {"desc": "3", "related": related.pk}},
            {
                "data": {"desc": "4", "related": related.pk},
                "children": [
                    {"data": {"desc": "41", "related": related.pk}},
                ],
            },
        ]
        related_model.load_bulk(related_data)
        got = related_model.dump_bulk(keep_ids=False)
        assert got == related_data

    def test_get_root_nodes(self, model):
        got = model.get_root_nodes()
        expected = ["1", "2", "3", "4"]
        assert [node.desc for node in got] == expected
        assert all([type(node) == model for node in got])

    def test_get_first_root_node(self, model):
        got = model.get_first_root_node()
        assert got.desc == "1"
        assert type(got) == model

    def test_get_last_root_node(self, model):
        got = model.get_last_root_node()
        assert got.desc == "4"
        assert type(got) == model

    def test_add_root(self, model):
        obj = model.add_root(desc="5")
        assert obj.get_depth() == 1
        got = model.get_last_root_node()
        assert got.desc == "5"
        assert type(got) == model

    def test_add_root_with_passed_instance(self, model):
        obj = model(desc="5")
        result = model.add_root(instance=obj)
        assert result == obj
        got = model.get_last_root_node()
        assert got.desc == "5"
        assert type(got) == model

    def test_add_root_with_already_saved_instance(self, model):
        obj = model.objects.get(desc="4")
        with pytest.raises(NodeAlreadySaved):
            model.add_root(instance=obj)


@pytest.mark.django_db
class TestSimpleNodeMethods(TestNonEmptyTree):
    def test_is_root(self, model):
        data = [
            ("2", True),
            ("1", True),
            ("4", True),
            ("21", False),
            ("24", False),
            ("22", False),
            ("231", False),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).is_root()
            assert got == expected

    def test_is_leaf(self, model):
        data = [
            ("2", False),
            ("23", False),
            ("231", True),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).is_leaf()
            assert got == expected

    def test_get_root(self, model):
        data = [
            ("2", "2"),
            ("1", "1"),
            ("4", "4"),
            ("21", "2"),
            ("24", "2"),
            ("22", "2"),
            ("231", "2"),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_root()
            assert node.desc == expected
            assert type(node) == model

    def test_get_parent(self, model):
        data = [
            ("2", None),
            ("1", None),
            ("4", None),
            ("21", "2"),
            ("24", "2"),
            ("22", "2"),
            ("231", "23"),
        ]
        data = dict(data)
        objs = {}
        for desc, expected in data.items():
            node = model.objects.get(desc=desc)
            parent = node.get_parent()
            if expected:
                assert parent.desc == expected
                assert type(parent) == model
            else:
                assert parent is None
            objs[desc] = node
            # corrupt the objects' parent cache
            node._parent_obj = "CORRUPTED!!!"

        for desc, expected in data.items():
            node = objs[desc]
            # asking get_parent to not use the parent cache (since we
            # corrupted it in the previous loop)
            parent = node.get_parent(True)
            if expected:
                assert parent.desc == expected
                assert type(parent) == model
            else:
                assert parent is None

    def test_get_children(self, model):
        data = [
            ("2", ["21", "22", "23", "24"]),
            ("23", ["231"]),
            ("231", []),
        ]
        for desc, expected in data:
            children = model.objects.get(desc=desc).get_children()
            assert [node.desc for node in children] == expected
            assert all([type(node) == model for node in children])

    def test_get_children_count(self, model):
        data = [
            ("2", 4),
            ("23", 1),
            ("231", 0),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).get_children_count()
            assert got == expected

    def test_get_siblings(self, model):
        data = [
            ("2", ["1", "2", "3", "4"]),
            ("21", ["21", "22", "23", "24"]),
            ("231", ["231"]),
        ]
        for desc, expected in data:
            siblings = model.objects.get(desc=desc).get_siblings()
            assert [node.desc for node in siblings] == expected
            assert all([type(node) == model for node in siblings])

    def test_get_first_sibling(self, model):
        data = [
            ("2", "1"),
            ("1", "1"),
            ("4", "1"),
            ("21", "21"),
            ("24", "21"),
            ("22", "21"),
            ("231", "231"),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_first_sibling()
            assert node.desc == expected
            assert type(node) == model

    def test_get_prev_sibling(self, model):
        data = [
            ("2", "1"),
            ("1", None),
            ("4", "3"),
            ("21", None),
            ("24", "23"),
            ("22", "21"),
            ("231", None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_prev_sibling()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected
                assert type(node) == model

    def test_get_next_sibling(self, model):
        data = [
            ("2", "3"),
            ("1", "2"),
            ("4", None),
            ("21", "22"),
            ("24", None),
            ("22", "23"),
            ("231", None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_next_sibling()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected
                assert type(node) == model

    def test_get_last_sibling(self, model):
        data = [
            ("2", "4"),
            ("1", "4"),
            ("4", "4"),
            ("21", "24"),
            ("24", "24"),
            ("22", "24"),
            ("231", "231"),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_last_sibling()
            assert node.desc == expected
            assert type(node) == model

    def test_get_first_child(self, model):
        data = [
            ("2", "21"),
            ("21", None),
            ("23", "231"),
            ("231", None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_first_child()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected
                assert type(node) == model

    def test_get_last_child(self, model):
        data = [
            ("2", "24"),
            ("21", None),
            ("23", "231"),
            ("231", None),
        ]
        for desc, expected in data:
            node = model.objects.get(desc=desc).get_last_child()
            if expected is None:
                assert node is None
            else:
                assert node.desc == expected
                assert type(node) == model

    def test_get_ancestors(self, model):
        data = [
            ("2", []),
            ("21", ["2"]),
            ("231", ["2", "23"]),
        ]
        for desc, expected in data:
            nodes = model.objects.get(desc=desc).get_ancestors()
            assert [node.desc for node in nodes] == expected
            assert all([type(node) == model for node in nodes])

    def test_get_descendants(self, model):
        data = [
            ("2", ["21", "22", "23", "231", "24"]),
            ("23", ["231"]),
            ("231", []),
            ("1", []),
            ("4", ["41"]),
        ]
        for desc, expected in data:
            nodes = model.objects.get(desc=desc).get_descendants()
            assert [node.desc for node in nodes] == expected
            assert all([type(node) == model for node in nodes])

    def test_get_descendant_count(self, model):
        data = [
            ("2", 5),
            ("23", 1),
            ("231", 0),
            ("1", 0),
            ("4", 1),
        ]
        for desc, expected in data:
            got = model.objects.get(desc=desc).get_descendant_count()
            assert got == expected

    def test_is_sibling_of(self, model):
        data = [
            ("2", "2", True),
            ("2", "1", True),
            ("21", "2", False),
            ("231", "2", False),
            ("22", "23", True),
            ("231", "23", False),
            ("231", "231", True),
        ]
        for desc1, desc2, expected in data:
            node1 = model.objects.get(desc=desc1)
            node2 = model.objects.get(desc=desc2)
            assert node1.is_sibling_of(node2) == expected

    def test_is_child_of(self, model):
        data = [
            ("2", "2", False),
            ("2", "1", False),
            ("21", "2", True),
            ("231", "2", False),
            ("231", "23", True),
            ("231", "231", False),
        ]
        for desc1, desc2, expected in data:
            node1 = model.objects.get(desc=desc1)
            node2 = model.objects.get(desc=desc2)
            assert node1.is_child_of(node2) == expected

    def test_is_descendant_of(self, model):
        data = [
            ("2", "2", False),
            ("2", "1", False),
            ("21", "2", True),
            ("231", "2", True),
            ("231", "23", True),
            ("231", "231", False),
        ]
        for desc1, desc2, expected in data:
            node1 = model.objects.get(desc=desc1)
            node2 = model.objects.get(desc=desc2)
            assert node1.is_descendant_of(node2) == expected


@pytest.mark.django_db
class TestAddChild(TestNonEmptyTree):
    def test_add_child_to_leaf(self, model):
        model.objects.get(desc="231").add_child(desc="2311")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 1),
            ("2311", 4, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_child_to_node(self, model):
        model.objects.get(desc="2").add_child(desc="25")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("25", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_child_with_passed_instance(self, model):
        child = model(desc="2311")
        result = model.objects.get(desc="231").add_child(instance=child)
        assert result == child
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 1),
            ("2311", 4, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_child_with_already_saved_instance(self, model):
        child = model.objects.get(desc="21")
        with pytest.raises(NodeAlreadySaved):
            model.objects.get(desc="2").add_child(instance=child)

    def test_add_child_with_pk_set(self, model):
        """
        If the model is using a natural primary key then it will be
        already set when the instance is inserted.
        """
        child = model(pk=999999, desc="natural key")
        result = model.objects.get(desc="2").add_child(instance=child)
        assert result == child

    def test_add_child_post_save(self, model):
        try:

            @receiver(post_save, dispatch_uid="test_add_child_post_save")
            def on_post_save(instance, **kwargs):
                parent = instance.get_parent()
                parent.refresh_from_db()
                assert parent.get_descendant_count() == 1

            # It's important that we're testing a leaf node
            parent = model.objects.get(desc="231")
            assert parent.is_leaf()

            parent.add_child(desc="2311")
        finally:
            post_save.disconnect(dispatch_uid="test_add_child_post_save")


@pytest.mark.django_db
class TestAddSibling(TestNonEmptyTree):
    def test_add_sibling_invalid_pos(self, model):
        with pytest.raises(InvalidPosition):
            model.objects.get(desc="231").add_sibling("invalid_pos")

    def test_add_sibling_missing_nodeorderby(self, model):
        node_wchildren = model.objects.get(desc="2")
        with pytest.raises(MissingNodeOrderBy):
            node_wchildren.add_sibling("sorted-sibling", desc="aaa")

    def test_add_sibling_last_root(self, model):
        node_wchildren = model.objects.get(desc="2")
        obj = node_wchildren.add_sibling("last-sibling", desc="5")
        assert obj.get_depth() == 1
        assert node_wchildren.get_last_sibling().desc == "5"

    def test_add_sibling_last(self, model):
        node = model.objects.get(desc="231")
        obj = node.add_sibling("last-sibling", desc="232")
        assert obj.get_depth() == 3
        assert node.get_last_sibling().desc == "232"

    def test_add_sibling_first_root(self, model):
        node_wchildren = model.objects.get(desc="2")
        obj = node_wchildren.add_sibling("first-sibling", desc="new")
        assert obj.get_depth() == 1
        expected = [
            ("new", 1, 0),
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_first(self, model):
        node_wchildren = model.objects.get(desc="23")
        obj = node_wchildren.add_sibling("first-sibling", desc="new")
        assert obj.get_depth() == 2
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("new", 2, 0),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_left_root(self, model):
        node_wchildren = model.objects.get(desc="2")
        obj = node_wchildren.add_sibling("left", desc="new")
        assert obj.get_depth() == 1
        expected = [
            ("1", 1, 0),
            ("new", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_left(self, model):
        node_wchildren = model.objects.get(desc="23")
        obj = node_wchildren.add_sibling("left", desc="new")
        assert obj.get_depth() == 2
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("new", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_left_noleft_root(self, model):
        node = model.objects.get(desc="1")
        obj = node.add_sibling("left", desc="new")
        assert obj.get_depth() == 1
        expected = [
            ("new", 1, 0),
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_left_noleft(self, model):
        node = model.objects.get(desc="231")
        obj = node.add_sibling("left", desc="new")
        assert obj.get_depth() == 3
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 2),
            ("new", 3, 0),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_right_root(self, model):
        node_wchildren = model.objects.get(desc="2")
        obj = node_wchildren.add_sibling("right", desc="new")
        assert obj.get_depth() == 1
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("new", 1, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_right(self, model):
        node_wchildren = model.objects.get(desc="23")
        obj = node_wchildren.add_sibling("right", desc="new")
        assert obj.get_depth() == 2
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("new", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_right_noright_root(self, model):
        node = model.objects.get(desc="4")
        obj = node.add_sibling("right", desc="new")
        assert obj.get_depth() == 1
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
            ("new", 1, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_right_noright(self, model):
        node = model.objects.get(desc="231")
        obj = node.add_sibling("right", desc="new")
        assert obj.get_depth() == 3
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 2),
            ("231", 3, 0),
            ("new", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_add_sibling_with_passed_instance(self, model):
        node_wchildren = model.objects.get(desc="2")
        obj = model(desc="5")
        result = node_wchildren.add_sibling("last-sibling", instance=obj)
        assert result == obj
        assert obj.get_depth() == 1
        assert node_wchildren.get_last_sibling().desc == "5"

    def test_add_sibling_already_saved_instance(self, model):
        node_wchildren = model.objects.get(desc="2")
        existing_node = model.objects.get(desc="4")
        with pytest.raises(NodeAlreadySaved):
            node_wchildren.add_sibling("last-sibling", instance=existing_node)

    def test_add_child_with_pk_set(self, model):
        """
        If the model is using a natural primary key then it will be
        already set when the instance is inserted.
        """
        child = model(pk=999999, desc="natural key")
        result = model.objects.get(desc="2").add_child(instance=child)
        assert result == child


@pytest.mark.django_db
class TestDelete(TestTreeBase):
    @staticmethod
    @pytest.fixture(
        scope="function",
        params=zip(models.BASE_MODELS, models.DEP_MODELS),
        ids=lambda fv: f"base={fv[0].__name__} dep={fv[1].__name__}",
    )
    def delete_dep_model_pair(request):
        base_model, dep_model = request.param
        base_model.load_bulk(BASE_DATA)
        for node in base_model.objects.all():
            dep_model(node=node).save()
        return base_model, dep_model

    def test_delete_leaf(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.get(desc="231").delete()
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(delete_model) == expected
        assert result == (2, {delete_model._meta.label: 1, dep_model._meta.label: 1})

    def test_delete_node(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.get(desc="23").delete()
        expected = [
            ("1", 1, 0),
            ("2", 1, 3),
            ("21", 2, 0),
            ("22", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(delete_model) == expected
        assert result == (4, {delete_model._meta.label: 2, dep_model._meta.label: 2})

    def test_delete_root(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.get(desc="2").delete()
        expected = [("1", 1, 0), ("3", 1, 0), ("4", 1, 1), ("41", 2, 0)]
        assert self.got(delete_model) == expected
        assert result == (12, {delete_model._meta.label: 6, dep_model._meta.label: 6})

    def test_delete_filter_root_nodes(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.filter(desc__in=("2", "3")).delete()
        expected = [("1", 1, 0), ("4", 1, 1), ("41", 2, 0)]
        assert self.got(delete_model) == expected
        assert result == (14, {delete_model._meta.label: 7, dep_model._meta.label: 7})

    def test_delete_filter_children(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.filter(desc__in=("2", "23", "231")).delete()
        expected = [("1", 1, 0), ("3", 1, 0), ("4", 1, 1), ("41", 2, 0)]
        assert self.got(delete_model) == expected
        assert result == (12, {delete_model._meta.label: 6, dep_model._meta.label: 6})

    def test_delete_nonexistant_nodes(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.filter(desc__in=("ZZZ", "XXX")).delete()
        assert self.got(delete_model) == UNCHANGED
        assert result == (0, {})

    def test_delete_same_node_twice(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.filter(desc__in=("2", "2")).delete()
        expected = [("1", 1, 0), ("3", 1, 0), ("4", 1, 1), ("41", 2, 0)]
        assert self.got(delete_model) == expected
        assert result == (12, {delete_model._meta.label: 6, dep_model._meta.label: 6})

    def test_delete_all_root_nodes(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.get_root_nodes().delete()
        assert result == (20, {delete_model._meta.label: 10, dep_model._meta.label: 10})
        assert delete_model.objects.count() == 0

    def test_delete_all_nodes(self, delete_dep_model_pair):
        delete_model, dep_model = delete_dep_model_pair
        result = delete_model.objects.all().delete()
        assert result == (20, {delete_model._meta.label: 10, dep_model._meta.label: 10})
        assert delete_model.objects.count() == 0


@pytest.mark.django_db
class TestMoveErrors(TestNonEmptyTree):
    def test_move_invalid_pos(self, model):
        node = model.objects.get(desc="231")
        with pytest.raises(InvalidPosition):
            node.move(node, "invalid_pos")

    def test_move_to_descendant(self, model):
        node = model.objects.get(desc="2")
        target = model.objects.get(desc="231")
        with pytest.raises(InvalidMoveToDescendant):
            node.move(target, "first-sibling")

    def test_move_missing_nodeorderby(self, model):
        node = model.objects.get(desc="231")
        with pytest.raises(MissingNodeOrderBy):
            node.move(node, "sorted-child")
        with pytest.raises(MissingNodeOrderBy):
            node.move(node, "sorted-sibling")


@pytest.mark.django_db
class TestMoveSortedErrors(TestTreeBase):
    def test_nonsorted_move_in_sorted(self, sorted_model):
        node = sorted_model.add_root(val1=3, val2=3, desc="zxy")
        with pytest.raises(InvalidPosition):
            node.move(node, "left")


@pytest.mark.django_db
class TestMoveLeafRoot(TestNonEmptyTree):
    def test_move_leaf_last_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="231").move(target, "last-sibling")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
            ("231", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_first_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="231").move(target, "first-sibling")
        expected = [
            ("231", 1, 0),
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_left_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="231").move(target, "left")
        expected = [
            ("1", 1, 0),
            ("231", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_right_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="231").move(target, "right")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("231", 1, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_last_child_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="231").move(target, "last-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("231", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_first_child_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="231").move(target, "first-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("231", 2, 0),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected


@pytest.mark.django_db
class TestMoveLeaf(TestNonEmptyTree):
    def test_move_leaf_last_sibling(self, model):
        target = model.objects.get(desc="22")
        model.objects.get(desc="231").move(target, "last-sibling")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("231", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_first_sibling(self, model):
        target = model.objects.get(desc="22")
        model.objects.get(desc="231").move(target, "first-sibling")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("231", 2, 0),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_left_sibling(self, model):
        target = model.objects.get(desc="22")
        model.objects.get(desc="231").move(target, "left")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("231", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_right_sibling(self, model):
        target = model.objects.get(desc="22")
        model.objects.get(desc="231").move(target, "right")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("231", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_left_sibling_itself(self, model):
        target = model.objects.get(desc="231")
        model.objects.get(desc="231").move(target, "left")
        assert self.got(model) == UNCHANGED

    def test_move_leaf_last_child(self, model):
        target = model.objects.get(desc="22")
        model.objects.get(desc="231").move(target, "last-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 1),
            ("231", 3, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_leaf_first_child(self, model):
        target = model.objects.get(desc="22")
        model.objects.get(desc="231").move(target, "first-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 1),
            ("231", 3, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected


@pytest.mark.django_db
class TestMoveBranchRoot(TestNonEmptyTree):
    def test_move_branch_first_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="4").move(target, "first-sibling")
        expected = [
            ("4", 1, 1),
            ("41", 2, 0),
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_last_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="4").move(target, "last-sibling")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_left_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="4").move(target, "left")
        expected = [
            ("1", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_right_sibling_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="4").move(target, "right")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("4", 1, 1),
            ("41", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_left_noleft_sibling_root(self, model):
        target = model.objects.get(desc="2").get_first_sibling()
        model.objects.get(desc="4").move(target, "left")
        expected = [
            ("4", 1, 1),
            ("41", 2, 0),
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_right_noright_sibling_root(self, model):
        target = model.objects.get(desc="2").get_last_sibling()
        model.objects.get(desc="4").move(target, "right")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_first_child_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="4").move(target, "first-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("4", 2, 1),
            ("41", 3, 0),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_last_child_root(self, model):
        target = model.objects.get(desc="2")
        model.objects.get(desc="4").move(target, "last-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("4", 2, 1),
            ("41", 3, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected


@pytest.mark.django_db
class TestMoveBranch(TestNonEmptyTree):
    def test_move_branch_first_sibling(self, model):
        target = model.objects.get(desc="23")
        model.objects.get(desc="4").move(target, "first-sibling")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("4", 2, 1),
            ("41", 3, 0),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_last_sibling(self, model):
        target = model.objects.get(desc="23")
        model.objects.get(desc="4").move(target, "last-sibling")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("4", 2, 1),
            ("41", 3, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_left_sibling(self, model):
        target = model.objects.get(desc="23")
        model.objects.get(desc="4").move(target, "left")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("4", 2, 1),
            ("41", 3, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_right_sibling(self, model):
        target = model.objects.get(desc="23")
        model.objects.get(desc="4").move(target, "right")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("4", 2, 1),
            ("41", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_left_noleft_sibling(self, model):
        target = model.objects.get(desc="23").get_first_sibling()
        model.objects.get(desc="4").move(target, "left")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("4", 2, 1),
            ("41", 3, 0),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_right_noright_sibling(self, model):
        target = model.objects.get(desc="23").get_last_sibling()
        model.objects.get(desc="4").move(target, "right")
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 1),
            ("231", 3, 0),
            ("24", 2, 0),
            ("4", 2, 1),
            ("41", 3, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_left_itself_sibling(self, model):
        target = model.objects.get(desc="4")
        model.objects.get(desc="4").move(target, "left")
        assert self.got(model) == UNCHANGED

    def test_move_branch_first_child(self, model):
        target = model.objects.get(desc="23")
        model.objects.get(desc="4").move(target, "first-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 2),
            ("4", 3, 1),
            ("41", 4, 0),
            ("231", 3, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected

    def test_move_branch_last_child(self, model):
        target = model.objects.get(desc="23")
        model.objects.get(desc="4").move(target, "last-child")
        expected = [
            ("1", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 2),
            ("231", 3, 0),
            ("4", 3, 1),
            ("41", 4, 0),
            ("24", 2, 0),
            ("3", 1, 0),
        ]
        assert self.got(model) == expected


@pytest.mark.django_db
class TestTreeSorted(TestTreeBase):
    def got(self, sorted_model):
        return [
            (o.val1, o.val2, o.desc, o.get_depth(), o.get_children_count())
            for o in sorted_model.get_tree()
        ]

    def test_add_root_sorted(self, sorted_model):
        sorted_model.add_root(val1=3, val2=3, desc="zxy")
        sorted_model.add_root(val1=1, val2=4, desc="bcd")
        sorted_model.add_root(val1=2, val2=5, desc="zxy")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=4, val2=1, desc="fgh")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=2, val2=2, desc="qwe")
        sorted_model.add_root(val1=3, val2=2, desc="vcx")
        expected = [
            (1, 4, "bcd", 1, 0),
            (2, 2, "qwe", 1, 0),
            (2, 5, "zxy", 1, 0),
            (3, 2, "vcx", 1, 0),
            (3, 3, "abc", 1, 0),
            (3, 3, "abc", 1, 0),
            (3, 3, "zxy", 1, 0),
            (4, 1, "fgh", 1, 0),
        ]
        assert self.got(sorted_model) == expected

    def test_add_child_root_sorted(self, sorted_model):
        root = sorted_model.add_root(val1=0, val2=0, desc="aaa")
        root.add_child(val1=3, val2=3, desc="zxy")
        root.add_child(val1=1, val2=4, desc="bcd")
        root.add_child(val1=2, val2=5, desc="zxy")
        root.add_child(val1=3, val2=3, desc="abc")
        root.add_child(val1=4, val2=1, desc="fgh")
        root.add_child(val1=3, val2=3, desc="abc")
        root.add_child(val1=2, val2=2, desc="qwe")
        root.add_child(val1=3, val2=2, desc="vcx")
        expected = [
            (0, 0, "aaa", 1, 8),
            (1, 4, "bcd", 2, 0),
            (2, 2, "qwe", 2, 0),
            (2, 5, "zxy", 2, 0),
            (3, 2, "vcx", 2, 0),
            (3, 3, "abc", 2, 0),
            (3, 3, "abc", 2, 0),
            (3, 3, "zxy", 2, 0),
            (4, 1, "fgh", 2, 0),
        ]
        assert self.got(sorted_model) == expected

    def test_add_child_nonroot_sorted(self, sorted_model):
        get_node = lambda node_id: sorted_model.objects.get(pk=node_id)

        root_id = sorted_model.add_root(val1=0, val2=0, desc="a").pk
        node_id = get_node(root_id).add_child(val1=0, val2=0, desc="ac").pk
        get_node(root_id).add_child(val1=0, val2=0, desc="aa")
        get_node(root_id).add_child(val1=0, val2=0, desc="av")
        get_node(node_id).add_child(val1=0, val2=0, desc="aca")
        get_node(node_id).add_child(val1=0, val2=0, desc="acc")
        get_node(node_id).add_child(val1=0, val2=0, desc="acb")

        expected = [
            (0, 0, "a", 1, 3),
            (0, 0, "aa", 2, 0),
            (0, 0, "ac", 2, 3),
            (0, 0, "aca", 3, 0),
            (0, 0, "acb", 3, 0),
            (0, 0, "acc", 3, 0),
            (0, 0, "av", 2, 0),
        ]
        assert self.got(sorted_model) == expected

    def test_move_sorted(self, sorted_model):
        sorted_model.add_root(val1=3, val2=3, desc="zxy")
        sorted_model.add_root(val1=1, val2=4, desc="bcd")
        sorted_model.add_root(val1=2, val2=5, desc="zxy")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=4, val2=1, desc="fgh")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=2, val2=2, desc="qwe")
        sorted_model.add_root(val1=3, val2=2, desc="vcx")
        root_nodes = sorted_model.get_root_nodes()
        target = root_nodes[0]
        for node in root_nodes[1:]:
            # because raw queries don't update django objects
            node = sorted_model.objects.get(pk=node.pk)
            target = sorted_model.objects.get(pk=target.pk)
            node.move(target, "sorted-child")
        expected = [
            (1, 4, "bcd", 1, 7),
            (2, 2, "qwe", 2, 0),
            (2, 5, "zxy", 2, 0),
            (3, 2, "vcx", 2, 0),
            (3, 3, "abc", 2, 0),
            (3, 3, "abc", 2, 0),
            (3, 3, "zxy", 2, 0),
            (4, 1, "fgh", 2, 0),
        ]
        assert self.got(sorted_model) == expected

    def test_move_sortedsibling(self, sorted_model):
        # https://bitbucket.org/tabo/django-treebeard/issue/27
        sorted_model.add_root(val1=3, val2=3, desc="zxy")
        sorted_model.add_root(val1=1, val2=4, desc="bcd")
        sorted_model.add_root(val1=2, val2=5, desc="zxy")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=4, val2=1, desc="fgh")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=2, val2=2, desc="qwe")
        sorted_model.add_root(val1=3, val2=2, desc="vcx")
        root_nodes = sorted_model.get_root_nodes()
        target = root_nodes[0]
        for node in root_nodes[1:]:
            # because raw queries don't update django objects
            node = sorted_model.objects.get(pk=node.pk)
            target = sorted_model.objects.get(pk=target.pk)
            node.val1 -= 2
            node.save()
            node.move(target, "sorted-sibling")
        expected = [
            (0, 2, "qwe", 1, 0),
            (0, 5, "zxy", 1, 0),
            (1, 2, "vcx", 1, 0),
            (1, 3, "abc", 1, 0),
            (1, 3, "abc", 1, 0),
            (1, 3, "zxy", 1, 0),
            (1, 4, "bcd", 1, 0),
            (2, 1, "fgh", 1, 0),
        ]
        assert self.got(sorted_model) == expected


@pytest.mark.django_db
class TestInheritedModels(TestTreeBase):
    @staticmethod
    @pytest.fixture(
        scope="function",
        params=zip(models.BASE_MODELS, models.INHERITED_MODELS),
        ids=lambda fv: f"base={fv[0].__name__} inherited={fv[1].__name__}",
    )
    def inherited_model(request):
        base_model, inherited_model = request.param
        base_model.add_root(desc="1")
        base_model.add_root(desc="2")

        node21 = inherited_model(desc="21")
        base_model.objects.get(desc="2").add_child(instance=node21)

        base_model.objects.get(desc="21").add_child(desc="211")
        base_model.objects.get(desc="21").add_child(desc="212")
        base_model.objects.get(desc="2").add_child(desc="22")

        node3 = inherited_model(desc="3")
        base_model.add_root(instance=node3)
        return inherited_model

    def test_get_tree_all(self, inherited_model):
        got = [
            (o.desc, o.get_depth(), o.get_children_count())
            for o in inherited_model.get_tree()
        ]
        expected = [
            ("1", 1, 0),
            ("2", 1, 2),
            ("21", 2, 2),
            ("211", 3, 0),
            ("212", 3, 0),
            ("22", 2, 0),
            ("3", 1, 0),
        ]
        assert got == expected

    def test_get_tree_node(self, inherited_model):
        node = inherited_model.objects.get(desc="21")

        got = [
            (o.desc, o.get_depth(), o.get_children_count())
            for o in inherited_model.get_tree(node)
        ]
        expected = [
            ("21", 2, 2),
            ("211", 3, 0),
            ("212", 3, 0),
        ]
        assert got == expected

    def test_get_root_nodes(self, inherited_model):
        got = inherited_model.get_root_nodes()
        expected = ["1", "2", "3"]
        assert [node.desc for node in got] == expected

    def test_get_first_root_node(self, inherited_model):
        got = inherited_model.get_first_root_node()
        assert got.desc == "1"

    def test_get_last_root_node(self, inherited_model):
        got = inherited_model.get_last_root_node()
        assert got.desc == "3"

    def test_is_root(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.is_root() is False
        assert node3.is_root() is True

    def test_is_leaf(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.is_leaf() is False
        assert node3.is_leaf() is True

    def test_get_root(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_root().desc == "2"
        assert node3.get_root().desc == "3"

    def test_get_parent(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_parent().desc == "2"
        assert node3.get_parent() is None

    def test_get_children(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert [node.desc for node in node21.get_children()] == ["211", "212"]
        assert [node.desc for node in node3.get_children()] == []

    def test_get_children_count(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_children_count() == 2
        assert node3.get_children_count() == 0

    def test_get_siblings(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert [node.desc for node in node21.get_siblings()] == ["21", "22"]
        assert [node.desc for node in node3.get_siblings()] == ["1", "2", "3"]

    def test_get_first_sibling(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_first_sibling().desc == "21"
        assert node3.get_first_sibling().desc == "1"

    def test_get_prev_sibling(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_prev_sibling() is None
        assert node3.get_prev_sibling().desc == "2"

    def test_get_next_sibling(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_next_sibling().desc == "22"
        assert node3.get_next_sibling() is None

    def test_get_last_sibling(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_last_sibling().desc == "22"
        assert node3.get_last_sibling().desc == "3"

    def test_get_first_child(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_first_child().desc == "211"
        assert node3.get_first_child() is None

    def test_get_last_child(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_last_child().desc == "212"
        assert node3.get_last_child() is None

    def test_get_ancestors(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert [node.desc for node in node21.get_ancestors()] == ["2"]
        assert [node.desc for node in node3.get_ancestors()] == []

    def test_get_descendants(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert [node.desc for node in node21.get_descendants()] == ["211", "212"]
        assert [node.desc for node in node3.get_descendants()] == []

    def test_get_descendant_count(self, inherited_model):
        node21 = inherited_model.objects.get(desc="21")
        node3 = inherited_model.objects.get(desc="3")
        assert node21.get_descendant_count() == 2
        assert node3.get_descendant_count() == 0

    def test_cascading_deletion(self, inherited_model):
        # Deleting a node by calling delete() on the inherited_model class
        # should delete descendants, even if those descendants are not
        # instances of inherited_model
        base_model = inherited_model.__bases__[0]

        node21 = inherited_model.objects.get(desc="21")
        node21.delete()
        node2 = base_model.objects.get(desc="2")
        for desc in ["21", "211", "212"]:
            assert not base_model.objects.filter(desc=desc).exists()
        assert [node.desc for node in node2.get_descendants()] == ["22"]


@pytest.mark.django_db
class TestMP_TreeAlphabet(TestTreeBase):
    @pytest.mark.skipif(
        not os.getenv("TREEBEARD_TEST_ALPHABET", False),
        reason="TREEBEARD_TEST_ALPHABET env variable not set.",
    )
    def test_alphabet(self, mpalphabet_model):
        """This isn't actually a test, it's an informational routine."""
        basealpha = numconv.BASE85
        got_err = False
        last_good = None
        for alphabetlen in range(3, len(basealpha) + 1):
            alphabet = basealpha[0:alphabetlen]
            assert len(alphabet) >= 3
            expected = [alphabet[0] + char for char in alphabet[1:]]
            expected.extend([alphabet[1] + char for char in alphabet])
            expected.append(alphabet[2] + alphabet[0])

            # remove all nodes
            mpalphabet_model.objects.all().delete()

            # change the model's alphabet
            mpalphabet_model.alphabet = alphabet
            mpalphabet_model.numconv_obj_ = None

            # insert root nodes
            for pos in range(len(alphabet) * 2):
                try:
                    mpalphabet_model.add_root(numval=pos)
                except:
                    got_err = True
                    break
            if got_err:
                break
            got = [obj.path for obj in mpalphabet_model.objects.all()]
            if got != expected:
                break
            last_good = alphabet
        assert False, "Best BASE85 based alphabet for your setup: {} (base {})".format(
            last_good, len(last_good)
        )


@pytest.mark.django_db
class TestHelpers(TestTreeBase):
    @staticmethod
    @pytest.fixture(scope="function", params=models.BASE_MODELS + models.PROXY_MODELS)
    def helpers_model(request):
        model = request.param
        model.load_bulk(BASE_DATA)
        for node in model.get_root_nodes():
            model.load_bulk(BASE_DATA, node)
        model.add_root(desc="5")
        return model

    def test_descendants_group_count_root(self, helpers_model):
        expected = [
            (o.desc, o.get_descendant_count()) for o in helpers_model.get_root_nodes()
        ]
        got = [
            (o.desc, o.descendants_count)
            for o in helpers_model.get_descendants_group_count()
        ]
        assert got == expected

    def test_descendants_group_count_node(self, helpers_model):
        parent = helpers_model.get_root_nodes().get(desc="2")
        expected = [(o.desc, o.get_descendant_count()) for o in parent.get_children()]
        got = [
            (o.desc, o.descendants_count)
            for o in helpers_model.get_descendants_group_count(parent)
        ]
        assert got == expected


@pytest.mark.django_db
class TestMP_TreeSortedAutoNow(TestTreeBase):
    """
    The sorting mechanism used by treebeard when adding a node can fail if the
    ordering is using an "auto_now" field
    """

    def test_sorted_by_autonow_workaround(self, mpsortedautonow_model):
        # workaround
        for i in range(1, 5):
            mpsortedautonow_model.add_root(
                desc="node%d" % (i,), created=datetime.datetime.now()
            )

    def test_sorted_by_autonow_FAIL(self, mpsortedautonow_model):
        """
        This test asserts that we have a problem.
        fix this, somehow
        """
        mpsortedautonow_model.add_root(desc="node1")
        with pytest.raises(ValueError):
            mpsortedautonow_model.add_root(desc="node2")


@pytest.mark.django_db
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
        positions = ("first-sibling", "left", "right", "last-sibling")
        for pos in positions:
            with pytest.raises(PathOverflow):
                root.get_last_child().add_sibling(pos)

    def test_move(self, mpsmallstep_model):
        root = mpsmallstep_model.add_root()
        for i in range(1, 10):
            root.add_child()
        newroot = mpsmallstep_model.add_root()
        targets = [
            (root, ["first-child", "last-child"]),
            (
                root.get_first_child(),
                ["first-sibling", "left", "right", "last-sibling"],
            ),
        ]
        for target, positions in targets:
            for pos in positions:
                with pytest.raises(PathOverflow):
                    newroot.move(target, pos)


@pytest.mark.django_db
class TestMP_TreeShortPath(TestTreeBase):
    """Test a tree with a very small path field (max_length=4) and a
    steplen of 1
    """

    def test_short_path(self, mpshortnotsorted_model):
        obj = mpshortnotsorted_model.add_root()
        obj = obj.add_child().add_child().add_child()
        with pytest.raises(PathOverflow):
            obj.add_child()


@pytest.mark.django_db
class TestMP_TreeFindProblems(TestTreeBase):
    def test_find_problems(self, mpalphabet_model):
        mpalphabet_model.alphabet = "01234"
        mpalphabet_model(path="01", depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path="1", depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path="111", depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path="abcd", depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path="qa#$%!", depth=1, numchild=0, numval=0).save()
        mpalphabet_model(path="0201", depth=2, numchild=0, numval=0).save()
        mpalphabet_model(path="020201", depth=3, numchild=0, numval=0).save()
        mpalphabet_model(path="03", depth=1, numchild=2, numval=0).save()
        mpalphabet_model(path="0301", depth=2, numchild=0, numval=0).save()
        mpalphabet_model(path="030102", depth=3, numchild=10, numval=0).save()
        mpalphabet_model(path="04", depth=10, numchild=1, numval=0).save()
        mpalphabet_model(path="0401", depth=20, numchild=0, numval=0).save()

        def got(ids):
            return [o.path for o in mpalphabet_model.objects.filter(pk__in=ids)]

        (
            evil_chars,
            bad_steplen,
            orphans,
            wrong_depth,
            wrong_numchild,
        ) = mpalphabet_model.find_problems()
        assert ["abcd", "qa#$%!"] == got(evil_chars)
        assert ["1", "111"] == got(bad_steplen)
        assert ["0201", "020201"] == got(orphans)
        assert ["03", "0301", "030102"] == got(wrong_numchild)
        assert ["04", "0401"] == got(wrong_depth)


@pytest.mark.django_db
class TestMP_TreeFix(TestTreeBase):

    expected_no_holes = {
        models.MP_TestNodeShortPath: [
            ("1", "b", 1, 2),
            ("11", "u", 2, 1),
            ("111", "i", 3, 1),
            ("1111", "e", 4, 0),
            ("12", "o", 2, 0),
            ("2", "d", 1, 0),
            ("3", "g", 1, 0),
            ("4", "a", 1, 4),
            ("41", "a", 2, 0),
            ("42", "a", 2, 0),
            ("43", "u", 2, 1),
            ("431", "i", 3, 1),
            ("4311", "e", 4, 0),
            ("44", "o", 2, 0),
        ],
        models.MP_TestSortedNodeShortPath: [
            ("1", "a", 1, 4),
            ("11", "a", 2, 0),
            ("12", "a", 2, 0),
            ("13", "o", 2, 0),
            ("14", "u", 2, 1),
            ("141", "i", 3, 1),
            ("1411", "e", 4, 0),
            ("2", "b", 1, 2),
            ("21", "o", 2, 0),
            ("22", "u", 2, 1),
            ("221", "i", 3, 1),
            ("2211", "e", 4, 0),
            ("3", "d", 1, 0),
            ("4", "g", 1, 0),
        ],
    }
    expected_with_holes = {
        models.MP_TestNodeShortPath: [
            ("1", "b", 1, 2),
            ("13", "u", 2, 1),
            ("134", "i", 3, 1),
            ("1343", "e", 4, 0),
            ("14", "o", 2, 0),
            ("2", "d", 1, 0),
            ("3", "g", 1, 0),
            ("4", "a", 1, 4),
            ("41", "a", 2, 0),
            ("42", "a", 2, 0),
            ("43", "u", 2, 1),
            ("434", "i", 3, 1),
            ("4343", "e", 4, 0),
            ("44", "o", 2, 0),
        ],
        models.MP_TestSortedNodeShortPath: [
            ("1", "b", 1, 2),
            ("13", "u", 2, 1),
            ("134", "i", 3, 1),
            ("1343", "e", 4, 0),
            ("14", "o", 2, 0),
            ("2", "d", 1, 0),
            ("3", "g", 1, 0),
            ("4", "a", 1, 4),
            ("41", "a", 2, 0),
            ("42", "a", 2, 0),
            ("43", "u", 2, 1),
            ("434", "i", 3, 1),
            ("4343", "e", 4, 0),
            ("44", "o", 2, 0),
        ],
    }

    def got(self, model):
        return [
            (o.path, o.desc, o.get_depth(), o.get_children_count())
            for o in model.get_tree()
        ]

    def add_broken_test_data(self, model):
        model(path="4", depth=2, numchild=2, desc="a").save()
        model(path="13", depth=1000, numchild=0, desc="u").save()
        model(path="14", depth=4, numchild=500, desc="o").save()
        model(path="134", depth=321, numchild=543, desc="i").save()
        model(path="1343", depth=321, numchild=543, desc="e").save()
        model(path="42", depth=1, numchild=1, desc="a").save()
        model(path="43", depth=1000, numchild=0, desc="u").save()
        model(path="44", depth=4, numchild=500, desc="o").save()
        model(path="434", depth=321, numchild=543, desc="i").save()
        model(path="4343", depth=321, numchild=543, desc="e").save()
        model(path="41", depth=1, numchild=1, desc="a").save()
        model(path="3", depth=221, numchild=322, desc="g").save()
        model(path="1", depth=10, numchild=3, desc="b").save()
        model(path="2", depth=10, numchild=3, desc="d").save()

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

    def test_fix_tree_with_fix_paths(self, mpshort_model):
        self.add_broken_test_data(mpshort_model)
        mpshort_model.fix_tree(fix_paths=True)
        got = self.got(mpshort_model)
        expected = self.expected_no_holes[mpshort_model]
        assert got == expected
        mpshort_model.find_problems()


@pytest.mark.django_db
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
                root.get_children().filter(Q(name="first") | Q(users=user)), expected
            )

        user = User.objects.create_user("test_user", "test@example.com", "testpasswd")
        user.save()
        root = mpm2muser_model.add_root(name="the root node")

        root.add_child(name="first")
        second = root.add_child(name="second")

        qs_check(root.get_children(), ["first", "second"])
        qs_check(root.get_children().filter(Q(name="first")), ["first"])
        qs_check(root.get_children().filter(Q(users=user)), [])

        qs_check_first_or_user(["first"], root, user)

        qs_check_first_or_user(["first", "second"], root, anonuserobj)

        user = User.objects.get(username="test_user")
        second.users.add(user)
        qs_check_first_or_user(["first", "second"], root, user)

        qs_check_first_or_user(["first"], root, anonuserobj)


@pytest.mark.django_db
class TestMoveNodeForm(TestNonEmptyTree):
    def _get_nodes_list(self, nodes):
        return [
            (pk, "%s%s" % ("&nbsp;" * 4 * (depth - 1), str)) for pk, str, depth in nodes
        ]

    def _assert_nodes_in_choices(self, form, nodes):
        choices = form.fields["_ref_node_id"].choices
        assert choices.pop(0)[0] is None
        assert nodes == [(choice[0], choice[1]) for choice in choices]

    def _move_node_helper(self, node, safe_parent_nodes):
        form_class = movenodeform_factory(type(node))
        form = form_class(instance=node)
        assert ["desc", "_position", "_ref_node_id"] == list(form.base_fields.keys())
        got = [choice[0] for choice in form.fields["_position"].choices]
        assert ["first-child", "left", "right"] == got
        nodes = self._get_nodes_list(safe_parent_nodes)
        self._assert_nodes_in_choices(form, nodes)

    def _get_node_ids_strs_and_depths(self, nodes):
        return [(node.pk, str(node), node.get_depth()) for node in nodes]

    def test_form_root_node(self, model):
        nodes = list(model.get_tree())
        node = nodes.pop(0)
        safe_parent_nodes = self._get_node_ids_strs_and_depths(nodes)
        self._move_node_helper(node, safe_parent_nodes)

    def test_form_leaf_node(self, model):
        nodes = list(model.get_tree())
        safe_parent_nodes = self._get_node_ids_strs_and_depths(nodes)
        node = nodes.pop()
        self._move_node_helper(node, safe_parent_nodes)

    def test_form_admin(self, model):
        request = None
        nodes = list(model.get_tree())
        safe_parent_nodes = self._get_node_ids_strs_and_depths(nodes)
        for node in model.objects.all():
            site = AdminSite()
            form_class = movenodeform_factory(model)
            admin_class = admin_factory(form_class)
            ma = admin_class(model, site)
            got = list(ma.get_form(request).base_fields.keys())
            desc_pos_refnodeid = ["desc", "_position", "_ref_node_id"]
            assert desc_pos_refnodeid == got
            got = ma.get_fieldsets(request)
            expected = [(None, {"fields": desc_pos_refnodeid})]
            assert got == expected
            got = ma.get_fieldsets(request, node)
            assert got == expected
            form = ma.get_form(request)()
            nodes = self._get_nodes_list(safe_parent_nodes)
            self._assert_nodes_in_choices(form, nodes)


@pytest.mark.django_db
class TestModelAdmin(TestNonEmptyTree):
    def test_default_fields(self, model):
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        ma = admin_class(model, site)
        assert list(ma.get_form(None).base_fields.keys()) == [
            "desc",
            "_position",
            "_ref_node_id",
        ]


@pytest.mark.django_db
class TestSortedForm(TestTreeSorted):
    def test_sorted_form(self, sorted_model):
        sorted_model.add_root(val1=3, val2=3, desc="zxy")
        sorted_model.add_root(val1=1, val2=4, desc="bcd")
        sorted_model.add_root(val1=2, val2=5, desc="zxy")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=4, val2=1, desc="fgh")
        sorted_model.add_root(val1=3, val2=3, desc="abc")
        sorted_model.add_root(val1=2, val2=2, desc="qwe")
        sorted_model.add_root(val1=3, val2=2, desc="vcx")

        form_class = movenodeform_factory(sorted_model)
        form = form_class()
        assert list(form.fields.keys()) == [
            "val1",
            "val2",
            "desc",
            "_position",
            "_ref_node_id",
        ]

        form = form_class(instance=sorted_model.objects.get(desc="bcd"))
        assert list(form.fields.keys()) == [
            "val1",
            "val2",
            "desc",
            "_position",
            "_ref_node_id",
        ]
        assert "id__position" in str(form)
        assert "id__ref_node_id" in str(form)


@pytest.mark.django_db
class TestForm(TestNonEmptyTree):
    def test_form(self, model):
        form_class = movenodeform_factory(model)
        form = form_class()
        assert list(form.fields.keys()) == ["desc", "_position", "_ref_node_id"]

        form = form_class(instance=model.objects.get(desc="1"))
        assert list(form.fields.keys()) == ["desc", "_position", "_ref_node_id"]
        assert "id__position" in str(form)
        assert "id__ref_node_id" in str(form)

    def test_move_node_form(self, model):
        form_class = movenodeform_factory(model)

        bad_node = model.objects.get(desc="1").add_child(
            desc='Benign<script>alert("Compromised");</script>'
        )

        form = form_class(instance=bad_node)
        rendered_html = form.as_p()
        assert "Benign" in rendered_html
        assert "<script>" not in rendered_html
        assert "&lt;script&gt;" in rendered_html

    def test_get_position_ref_node(self, model):
        form_class = movenodeform_factory(model)

        instance_parent = model.objects.get(desc="1")
        form = form_class(instance=instance_parent)
        assert form._get_position_ref_node(instance_parent) == {
            "_position": "first-child",
            "_ref_node_id": "",
        }

        instance_child = model.objects.get(desc="21")
        form = form_class(instance=instance_child)
        assert form._get_position_ref_node(instance_child) == {
            "_position": "first-child",
            "_ref_node_id": model.objects.get(desc="2").pk,
        }

        instance_grandchild = model.objects.get(desc="22")
        form = form_class(instance=instance_grandchild)
        assert form._get_position_ref_node(instance_grandchild) == {
            "_position": "right",
            "_ref_node_id": model.objects.get(desc="21").pk,
        }

        instance_grandchild = model.objects.get(desc="231")
        form = form_class(instance=instance_grandchild)
        assert form._get_position_ref_node(instance_grandchild) == {
            "_position": "first-child",
            "_ref_node_id": model.objects.get(desc="23").pk,
        }

    def test_clean_cleaned_data(self, model):
        instance_parent = model.objects.get(desc="1")
        _position = "first-child"
        _ref_node_id = ""
        form_class = movenodeform_factory(model)
        form = form_class(
            instance=instance_parent,
            data={
                "_position": _position,
                "_ref_node_id": _ref_node_id,
                "desc": instance_parent.desc,
            },
        )
        assert form.is_valid()
        assert form._clean_cleaned_data() == (_position, _ref_node_id)

    def test_save_edit(self, model):
        instance_parent = model.objects.get(desc="1")
        original_count = len(model.objects.all())
        form_class = movenodeform_factory(model)
        form = form_class(
            instance=instance_parent,
            data={
                "_position": "first-child",
                "_ref_node_id": model.objects.get(desc="2").pk,
                "desc": instance_parent.desc,
            },
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
                "_position": "first-child",
                "_ref_node_id": "",
                "desc": saved_instance.desc,
            },
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
        _position = "first-child"
        form_class = movenodeform_factory(model)
        form = form_class(data={"_position": _position, "desc": "New Form Test"})
        assert form.is_valid()
        assert form.save() is not None
        assert original_count < model.objects.all().count()

    def test_save_new_with_pk_set(self, model):
        """
        If the model is using a natural primary key then it will be
        already set when the instance is inserted.
        """
        original_count = model.objects.all().count()
        assert original_count == 10
        _position = "first-child"
        form_class = movenodeform_factory(model)
        form = form_class(
            data={"_position": _position, "id": 999999, "desc": "New Form Test"}
        )
        assert form.is_valid()
        # Fake a natural key by updating the instance directly, because
        # the model form will have removed the id from cleaned data because
        # it thinks it is an AutoField.
        form.instance.id = 999999
        assert form.save() is not None
        assert original_count < model.objects.all().count()

    def test_save_instance(self, model):
        form_class = movenodeform_factory(model)
        form = form_class(data={'_position': 'first-child', 'desc': 'Test Instance'})
        assert form.is_valid()
        form.instance.desc = "Modified Instance"
        instance = form.save()
        assert instance.desc == "Modified Instance"


@pytest.mark.django_db
class TestAdminTree(TestNonEmptyTree):
    template = Template(
        "{% load admin_tree %}{% spaceless %}"
        "{% result_tree cl request %}{% endspaceless %}"
    )

    def test_result_tree(self, model_without_proxy):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        model = model_without_proxy
        request = RequestFactory().get("/admin/tree/")
        request.user = AnonymousUser()
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
        table_output = self.template.render(context)
        # We have the same amount of drag handlers as objects
        drag_handler = '<td class="drag-handler"><span>&nbsp;</span></td>'
        assert table_output.count(drag_handler) == model.objects.count()
        # All nodes are in the result tree
        for object in model.objects.all():
            url = cl.url_for_result(object)
            node = '<a href="%s">%s</a>' % (url, str(object))
            assert node in table_output
        # Unfiltered
        assert '<input type="hidden" id="has-filters" value="0"/>' in table_output

    def test_unicode_result_tree(self, model_with_unicode):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        model = model_with_unicode
        # Add a unicode description
        model.add_root(desc="áéîøü")
        request = RequestFactory().get("/admin/tree/")
        request.user = AnonymousUser()
        site = AdminSite()
        form_class = movenodeform_factory(model)
        ModelAdmin = admin_factory(form_class)

        class UnicodeModelAdmin(ModelAdmin):
            list_display = ("__str__", "desc")

        m = UnicodeModelAdmin(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
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
        assert '<input type="hidden" id="has-filters" value="0"/>' in table_output

    def test_result_filtered(self, model_without_proxy):
        """Test template changes with filters or pagination."""
        model = model_without_proxy
        # Filtered GET
        request = RequestFactory().get("/admin/tree/?desc=1")
        request.user = AnonymousUser()
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
        table_output = self.template.render(context)
        # Filtered
        assert '<input type="hidden" id="has-filters" value="1"/>' in table_output

        # Not Filtered GET, it should ignore pagination
        request = RequestFactory().get("/admin/tree/?p=1")
        request.user = AnonymousUser()
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
        table_output = self.template.render(context)
        # Not Filtered
        assert '<input type="hidden" id="has-filters" value="0"/>' in table_output

        # Not Filtered GET, it should ignore all
        request = RequestFactory().get("/admin/tree/?all=1")
        request.user = AnonymousUser()
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
        table_output = self.template.render(context)
        # Not Filtered
        assert '<input type="hidden" id="has-filters" value="0"/>' in table_output


@pytest.mark.django_db
class TestAdminTreeList(TestNonEmptyTree):
    template = Template(
        "{% load admin_tree_list %}{% spaceless %}"
        "{% result_tree cl request %}{% endspaceless %}"
    )

    def test_result_tree_list(self, model_without_proxy):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        model = model_without_proxy
        request = RequestFactory().get("/admin/tree/")
        request.user = AnonymousUser()
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
        table_output = self.template.render(context)
        output_template = '<li><a href="%s/" >%s</a>'
        for object in model.objects.all():
            expected_output = output_template % (object.pk, str(object))
            assert expected_output in table_output

    def test_result_tree_list_with_action(self, model_without_proxy):
        model = model_without_proxy
        request = RequestFactory().get("/admin/tree/")
        request.user = AnonymousUser()
        site = AdminSite()
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request, "action_form": True})
        table_output = self.template.render(context)
        output_template = (
            '<input type="checkbox" class="action-select" '
            'value="%s" name="_selected_action" />'
            '<a href="%s/" >%s</a>'
        )

        for object in model.objects.all():
            expected_output = output_template % (object.pk, object.pk, str(object))
            assert expected_output in table_output

    def test_result_tree_list_with_get(self, model_without_proxy):
        model = model_without_proxy
        pk_field = model._meta.pk.attname
        # Test t GET parameter with value id
        request = RequestFactory().get(
            "/admin/tree/?{0}={1}".format(TO_FIELD_VAR, pk_field)
        )
        request.user = AnonymousUser()
        site = AdminSite()
        admin_register_all(site)
        form_class = movenodeform_factory(model)
        admin_class = admin_factory(form_class)
        m = admin_class(model, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
        table_output = self.template.render(context)
        output_template = "opener.dismissRelatedLookupPopup(window, '%s');"
        for object in model.objects.all():
            expected_output = output_template % object.pk
            assert expected_output in table_output

    def test_result_tree_list_escapes_labels(self, model_with_unicode):
        """
        Verifies that inclusion tag result_list generates a table when with
        default ModelAdmin settings.
        """
        object = model_with_unicode.add_root(desc="<>")
        request = RequestFactory().get("/admin/tree/")
        request.user = AnonymousUser()
        site = AdminSite()
        form_class = movenodeform_factory(model_with_unicode)
        admin_class = admin_factory(form_class)
        m = admin_class(model_with_unicode, site)
        list_display = m.get_list_display(request)
        list_display_links = m.get_list_display_links(request, list_display)
        cl = ChangeList(*get_changelist_args(
            request,
            model_with_unicode,
            list_display,
            list_display_links,
            m.list_filter,
            m.date_hierarchy,
            m.search_fields,
            m.list_select_related,
            m.list_per_page,
            m.list_max_show_all,
            m.list_editable,
            m,
            [],
        ))
        cl.formset = None
        context = Context({"cl": cl, "request": request})
        table_output = self.template.render(context)
        expected_output = f'<li><a href="{object.pk}/" >&lt;&gt;</a>'
        assert expected_output in table_output


@pytest.mark.django_db
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
        request = request_factory.post("/", data=data)
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    def _get_admin_obj(self, model_class):
        form_class = movenodeform_factory(model_class)
        admin_class = admin_factory(form_class)
        return admin_class(model_class, self.site)

    def test_changelist_view(self):
        tmp_user = self._create_superuser("changelist_tmp")
        request = self._mocked_authenticated_request("/", tmp_user)
        admin_obj = self._get_admin_obj(models.AL_TestNode)
        admin_obj.changelist_view(request)
        assert admin_obj.change_list_template == "admin/tree_list.html"

        admin_obj = self._get_admin_obj(models.MP_TestNode)
        admin_obj.changelist_view(request)
        assert admin_obj.change_list_template != "admin/tree_list.html"

    def test_get_node(self, model):
        admin_obj = self._get_admin_obj(model)
        target = model.objects.get(desc="2")
        assert admin_obj.get_node(target.pk) == target

    def test_move_node_validate_keyerror(self, model):
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.move_node(request)
        assert response.status_code == 400
        request = self._mocked_request(data={"node_id": 1})
        response = admin_obj.move_node(request)
        assert response.status_code == 400

    def test_move_node_validate_valueerror(self, model):
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(
            data={"node_id": 1, "sibling_id": 2, "as_child": "invalid"}
        )
        response = admin_obj.move_node(request)
        assert response.status_code == 400

    def test_move_validate_missing_nodeorderby(self, model):
        node = model.objects.get(desc="231")
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.try_to_move_node(
            True, node, "sorted-child", request, target=node
        )
        assert response.status_code == 400

        response = admin_obj.try_to_move_node(
            True, node, "sorted-sibling", request, target=node
        )
        assert response.status_code == 400

    def test_move_validate_invalid_pos(self, model):
        node = model.objects.get(desc="231")
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.try_to_move_node(
            True, node, "invalid_pos", request, target=node
        )
        assert response.status_code == 400

    def test_move_validate_to_descendant(self, model):
        node = model.objects.get(desc="2")
        target = model.objects.get(desc="231")
        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(data={})
        response = admin_obj.try_to_move_node(
            True, node, "first-sibling", request, target
        )
        assert response.status_code == 400

    def test_move_left(self, model):
        node = model.objects.get(desc="231")
        target = model.objects.get(desc="2")

        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(
            data={"node_id": node.pk, "sibling_id": target.pk, "as_child": 0}
        )
        response = admin_obj.move_node(request)
        assert response.status_code == 200
        expected = [
            ("1", 1, 0),
            ("231", 1, 0),
            ("2", 1, 4),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected

    def test_move_last_child(self, model):
        node = model.objects.get(desc="231")
        target = model.objects.get(desc="2")

        admin_obj = self._get_admin_obj(model)
        request = self._mocked_request(
            data={"node_id": node.pk, "sibling_id": target.pk, "as_child": 1}
        )
        response = admin_obj.move_node(request)
        assert response.status_code == 200
        expected = [
            ("1", 1, 0),
            ("2", 1, 5),
            ("21", 2, 0),
            ("22", 2, 0),
            ("23", 2, 0),
            ("24", 2, 0),
            ("231", 2, 0),
            ("3", 1, 0),
            ("4", 1, 1),
            ("41", 2, 0),
        ]
        assert self.got(model) == expected


@pytest.mark.django_db
class TestMPFormPerformance(object):
    def test_form_add_subtree_no_of_queries(self, django_assert_num_queries):
        model = models.MP_TestNode
        model.load_bulk(BASE_DATA)
        form_class = movenodeform_factory(model)
        form = form_class()
        with django_assert_num_queries(len(model.get_root_nodes()) + 1):
            form.mk_dropdown_tree(model)


@pytest.mark.django_db
class TestMP_TreeDescendantsPerformance(TestTreeBase):
    def test_get_descendants_no_of_queries(self, django_assert_num_queries):
        model = models.MP_TestNode
        model.load_bulk(BASE_DATA)

        data = [
            ("2", 1),
            ("23", 1),
            ("231", 0),
            ("1", 0),
            ("4", 1),
        ]

        for desc, expected in data:
            node = model.objects.get(desc=desc)
            with django_assert_num_queries(expected):
                # converting to list to force queryset evaluation
                list(node.get_descendants())
