
from __future__ import print_function

import pytest

import glom
from glom import Glommer, PathAccessError, UnregisteredTarget
from glom.core import TargetRegistry


class A(object):
    pass

class B(object):
    pass

class C(A):
    pass

class D(B):
    pass

class E(C, D, A):
    pass

class F(E):
    pass


def test_types_leave_one_out():
    ALL_TYPES = [A, B, C, D, E, F]
    for cur_t in ALL_TYPES:

        treg = TargetRegistry(register_default_types=False)

        treg.register(object, get=lambda: object)
        for t in ALL_TYPES:
            if t is cur_t:
                continue
            treg.register(t, get=(lambda t: lambda: t)(t))

        obj = cur_t()
        assert treg.get_handler('get', obj)() == obj.__class__.mro()[1]

        if cur_t is E:
            assert treg.get_handler('get', obj)() is C  # sanity check

    return


def test_types_bare():
    glommer = Glommer(register_default_types=False)

    treg = glommer.scope[TargetRegistry]
    assert treg._get_closest_type(object(), treg._op_type_tree.get('get', {})) is None

    # test that bare glommers can't glom anything
    with pytest.raises(UnregisteredTarget) as exc_info:
        glommer.glom(object(), {'object_repr': '__class__.__name__'})
    assert repr(exc_info.value) == "UnregisteredTarget('get', <type 'object'>, OrderedDict(), ('__class__',))"
    assert str(exc_info.value).find(
        "glom() called without registering any types for operation 'get'."
        " see glom.register() or Glommer's constructor for details.") != -1

    with pytest.raises(UnregisteredTarget, match='without registering') as exc_info:
        glommer.glom([{'hi': 'hi'}], ['hi'])
    assert not exc_info.value.type_map

    glommer.register(object, get=getattr)
    glommer.register(dict, get=dict.__getitem__, exact=True)

    # check again that registering object for 'get' doesn't change the
    # fact that we don't have iterate support yet
    with pytest.raises(UnregisteredTarget) as exc_info:
        glommer.glom({'test': [{'hi': 'hi'}]}, ('test', ['hi']))
    # feel free to update the "(at ['test'])" part to improve path display
    assert (
        "target type 'list' not registered for 'iterate', "
        "expected one of registered types: (dict)" in str(exc_info.value))
    return


def test_invalid_register():
    glommer = Glommer()
    with pytest.raises(TypeError):
        glommer.register(1)
    return


def test_exact_register():
    glommer = Glommer(register_default_types=False)

    class BetterList(list):
        pass

    glommer.register(BetterList, iterate=iter, exact=True)

    expected = [0, 2, 4]
    value = glommer.glom(BetterList(range(3)), [lambda x: x * 2])
    assert value == expected

    with pytest.raises(UnregisteredTarget):
        glommer.glom(list(range(3)), ['unused'])

    return


def test_duck_register():
    class LilRanger(object):
        def __init__(self):
            self.lil_list = list(range(5))

        def __iter__(self):
            return iter(self.lil_list)

    glommer = Glommer(register_default_types=False)

    target = LilRanger()

    with pytest.raises(UnregisteredTarget):
        float_range = glommer.glom(target, [float])

    glommer.register(LilRanger)

    float_range = glommer.glom(target, [float])

    assert float_range == [0.0, 1.0, 2.0, 3.0, 4.0]

    glommer = Glommer()  # now with just defaults
    float_range = glommer.glom(target, [float])
    assert float_range == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_bypass_getitem():
    target = list(range(3)) * 3

    with pytest.raises(PathAccessError):
        glom.glom(target, 'count')

    res = glom.glom(target, lambda list_obj: list_obj.count(1))

    assert res == 3


def test_iter_set():
    some_ints = set(range(5))
    some_floats = glom.glom(some_ints, [float])

    assert sorted(some_floats) == [0.0, 1.0, 2.0, 3.0, 4.0]

    # now without defaults
    glommer = Glommer(register_default_types=False)
    glommer.register(set, iterate=iter)
    some_floats = glom.glom(some_ints, [float])

    assert sorted(some_floats) == [0.0, 1.0, 2.0, 3.0, 4.0]


def test_iter_str():
    # check that strings are not iterable by default, one of the most
    # common sources of bugs
    glom_buddy = 'kurt'

    with pytest.raises(UnregisteredTarget):
        glom.glom(glom_buddy, {'name': [glom_buddy]})

    # also check that someone can override this

    glommer = Glommer()
    glommer.register(str, iterate=iter)
    res = glommer.glom(glom_buddy, {'name_chars_for_some_reason': [str]})
    assert len(res['name_chars_for_some_reason']) == 4

    # the better way, for any dissenter reading this

    assert glom.glom(glom_buddy, {'name_chars': list}) == {'name_chars': ['k', 'u', 'r', 't']}

    # and for the really passionate: how about making strings
    # non-iterable and just giving them a .chars() method that returns
    # a list of single-character strings.


def test_default_scope_register():
    # just hit it to make sure it exists, it behaves exactly like Glommer.register
    glom.register(type, exact=False)


def test_faulty_iterate():
    glommer = Glommer()

    def bad_iter(obj):
        raise RuntimeError('oops')

    glommer.register(str, iterate=bad_iter)

    with pytest.raises(TypeError):
        glommer.glom({'a': 'fail'}, ('a', {'chars': [str]}))


def test_faulty_op_registration():
    treg = TargetRegistry()

    with pytest.raises(TypeError, match="text name, not:"):
        treg.register_op(None, len)
    with pytest.raises(TypeError, match="callable, not:"):
        treg.register_op('fake_op', object())

    class NewType(object):
        pass

    def _autodiscover_raise(type_obj):
        raise Exception('noperino')

    with pytest.raises(TypeError, match="noperino"):
        treg.register_op('fake_op', _autodiscover_raise)

    assert 'fake_op' not in treg._op_auto_map

    # check op with no autodiscovery
    treg.register_op('lol', exact=True)
    lol_type_map = treg.get_type_map('lol')
    assert all([v is False for v in lol_type_map.values()])

    # check op reregistration, this time not exact
    assert not treg._op_type_tree.get('lol')
    treg.register_op('lol', exact=False)
    assert treg._op_type_tree.get('lol')


    def _autodiscover_faulty_return(type_obj):
        return 'hideeho'

    with pytest.raises(TypeError, match="hideeho"):
        treg.register_op('fake_op', _autodiscover_faulty_return)

    def _autodiscover_sneaky(type_obj):
        # works with default registrations, but fails later on sets and frozensets
        if type_obj is set:
            return 'this should have been False or a callable, but was intentionally a string'
        if type_obj is frozenset:
            raise ValueError('this should have been False or a callable, but was intentionally a ValueError')
        return False

    treg.register_op('sneak', _autodiscover_sneaky)

    with pytest.raises(TypeError, match="intentionally a string"):
        treg.register(set)
    with pytest.raises(TypeError, match="intentionally a ValueError"):
        treg.register(frozenset)

    return


def test_reregister_type():
    treg = TargetRegistry()

    class NewType(object):
        pass

    treg.register(NewType, op=lambda obj: obj)

    obj = NewType()
    handler = treg.get_handler('op', obj)

    assert handler(obj) == obj

    # assert no change in reregistering same
    treg.register(NewType, op=lambda obj: obj)
    handler = treg.get_handler('op', obj)
    assert handler(obj) == obj

    # assert change in reregistering new
    treg.register(NewType, op=lambda obj: obj.__class__.__name__)
    handler = treg.get_handler('op', obj)
    assert handler(obj) == 'NewType'
