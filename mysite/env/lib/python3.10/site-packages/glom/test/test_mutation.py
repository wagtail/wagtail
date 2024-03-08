import pytest

from glom import glom, Path, T, S, Spec, Glommer, PathAssignError, PathAccessError
from glom import assign, Assign, delete, Delete, PathDeleteError
from glom import core
from glom.core import UnregisteredTarget


def test_assign():
    class Foo(object):
        pass

    assert glom({}, Assign(T['a'], 1)) == {'a': 1}
    assert glom({'a': {}}, Assign(T['a']['a'], 1)) == {'a': {'a': 1}}
    assert glom({'a': {}}, Assign('a.a', 1)) == {'a': {'a': 1}}
    assert glom(Foo(), Assign(T.a, 1)).a == 1
    assert glom({}, Assign('a', 1)) == {'a': 1}
    assert glom(Foo(), Assign('a', 1)).a == 1
    assert glom({'a': Foo()}, Assign('a.a', 1))['a'].a == 1
    def r():
        r = {}
        r['r'] = r
        return r
    assert glom(r(), Assign('r.r.r.r.r.r.r.r.r', 1)) == {'r': 1}
    assert glom(r(), Assign(T['r']['r']['r']['r'], 1)) == {'r': 1}
    assert glom(r(), Assign(Path('r', 'r', T['r']), 1)) == {'r': 1}
    assert assign(r(), Path('r', 'r', T['r']), 1) == {'r': 1}
    with pytest.raises(TypeError, match='path argument must be'):
        Assign(1, 'a')
    with pytest.raises(ValueError, match='path must have at least one element'):
        Assign(T, 1)

    assert repr(Assign(T.a, 1)) == 'Assign(T.a, 1)'
    assign_spec = Assign(T.a, 1, missing=dict)
    assert repr(assign_spec) == "Assign(T.a, 1, missing=dict)"
    assert repr(assign_spec) == repr(eval(repr(assign_spec)))


def test_assign_spec_val():
    output = glom({'b': 'c'}, Assign('a', Spec('b')))
    assert output['a'] == output['b'] == 'c'


def test_unregistered_assign():
    # test with bare target registry
    glommer = Glommer(register_default_types=False)

    with pytest.raises(UnregisteredTarget, match='assign'):
        glommer.glom({}, Assign('a', 'b'))

    # test for unassignable tuple
    with pytest.raises(UnregisteredTarget, match='assign'):
        glom({'a': ()}, Assign('a.0', 'b'))


def test_bad_assign_target():
    class BadTarget(object):
        def __setattr__(self, name, val):
            raise Exception("and you trusted me?")

    # sanity check
    spec = Assign('a', 'b')
    ok_target = lambda: None
    glom(ok_target, spec)
    assert ok_target.a == 'b'

    with pytest.raises(PathAssignError, match='could not assign'):
        glom(BadTarget(), spec)

    with pytest.raises(PathAccessError, match='could not access'):
        assign({}, 'a.b.c', 'moot')
    return


def test_sequence_assign():
    target = {'alist': [0, 1, 2]}
    assign(target, 'alist.2', 3)
    assert target['alist'][2] == 3

    with pytest.raises(PathAssignError, match='could not assign') as exc_info:
        assign(target, 'alist.3', 4)

    # the following test is because pypy's IndexError is different than CPython's:
    # E         - PathAssignError(IndexError('list index out of range',), Path('alist'), '3')
    # E         + PathAssignError(IndexError('list assignment index out of range',), Path('alist'), '3')
    # E         ?                                  +++++++++++

    exc_repr = repr(exc_info.value)
    assert exc_repr.startswith('PathAssignError(')
    assert exc_repr.endswith("'3')")
    return


def test_invalid_assign_op_target():
    target = {'afunc': lambda x: 'hi %s' % x}
    spec = T['afunc'](x=1)

    with pytest.raises(ValueError):
        assign(target, spec, None)
    return


def test_assign_missing_signature():
    # test signature (non-callable missing hook)
    with pytest.raises(TypeError, match='callable'):
        assign({}, 'a.b.c', 'lol', missing='invalidbcnotcallable')
    return


def test_assign_missing_dict():
    target = {}
    val = object()

    from itertools import count
    counter = count()
    def debugdict():
        ret = dict()
        #ret['id'] = id(ret)
        #ret['inc'] = counter.next()
        return ret

    assign(target, 'a.b.c.d', val, missing=debugdict)

    assert target == {'a': {'b': {'c': {'d': val}}}}


def test_assign_missing_object():
    val = object()
    class Container(object):
        pass

    target = Container()
    target.a = extant_a = Container()
    assign(target, 'a.b.c.d', val, missing=Container)

    assert target.a.b.c.d is val
    assert target.a is extant_a  # make sure we didn't overwrite anything on the path


def test_assign_missing_with_extant_keys():
    """This test ensures that assign with missing doesn't overwrite
    perfectly fine extant keys that are along the path it needs to
    assign to. call count is also checked to make sure missing() isn't
    invoked too many times.

    """
    target = {}
    value = object()
    default_struct = {'b': {'c': {}}}

    call_count = [0]

    def _get_default_struct():
        call_count[0] += 1  # make sure this is only called once
        return default_struct

    assign(target, 'a.b.c', value, missing=_get_default_struct)

    assert target['a']['b']['c'] is value
    assert target['a']['b'] is default_struct['b']
    assert call_count == [1]


def test_assign_missing_unassignable():
    """Check that the final assignment to the target object comes last,
    ensuring that failed assignments don't leave targets in a bad
    state.

    """

    class Tarjay(object):
        init_count = 0
        def __init__(self):
            self.__class__.init_count += 1

        @property
        def unassignable(self):
            return

    value = object()
    target = {"preexisting": "ok"}

    with pytest.raises(PathAssignError):
        assign(target, 'tarjay.unassignable.a.b.c', value, missing=Tarjay)

    assert target == {'preexisting': 'ok'}

    # why 3? "c" gets the value of "value", while "b", "a", and
    # "tarjay" all succeed and are set to Tarjay instances. Then
    # unassignable is already present, but not possible to assign to,
    # raising the PathAssignError.
    assert Tarjay.init_count == 3


def test_s_assign():
    '''
    check that assign works when storing things into S
    '''
    glom({}, (Assign(S['foo'], 'bar'), S['foo'])) == 'bar'


def test_delete():
    class Foo(object):
        def __init__(self, d=None):
            for k, v in d.items():
                setattr(self, k, v)

    assert glom({'a': 1}, Delete(T['a'])) == {}
    assert glom({'a': {'a': 1}}, Delete(T['a']['a'])) == {'a': {}}
    assert glom({'a': {'a': 1}}, Delete('a.a')) == {'a': {}}
    assert not hasattr(glom(Foo({'a': 1}), Delete(T.a)), 'a')
    assert glom({'a': 1}, Delete('a')) == {}
    assert not hasattr(glom(Foo({'a': 1}), Delete('a')), 'a')
    assert not hasattr(glom({'a': Foo({'a': 1})}, Delete('a.a'))['a'], 'a')

    def r():
        r = {}
        r['r'] = r
        return r

    assert glom(r(), Delete('r.r.r.r.r.r.r.r.r')) == {}
    assert glom(r(), Delete(T['r']['r']['r']['r'])) == {}
    assert glom(r(), Delete(Path('r', 'r', T['r']))) == {}
    assert delete(r(), Path('r', 'r', T['r'])) == {}
    with pytest.raises(TypeError, match='path argument must be'):
        Delete(1, 'a')
    with pytest.raises(ValueError, match='path must have at least one element'):
        Delete(T, 1)

    assert repr(Delete(T.a)) == 'Delete(T.a)'

    # test delete from scope
    assert glom(1, (S(x=T), S['x'])) == 1
    with pytest.raises(PathAccessError):
        glom(1, (S(x=T), Delete(S['x']), S['x']))

    # test raising on missing parent
    with pytest.raises(PathAccessError):
        glom({}, Delete(T['a']['b']))

    # test raising on missing index
    with pytest.raises(PathDeleteError):
        glom([], Delete(T[0]))
    target = []
    assert glom(target, Delete(T[0], ignore_missing=True)) is target

    # test raising on missing attr
    with pytest.raises(PathDeleteError):
        glom(object(), Delete(T.does_not_exist))
    target = object()
    assert glom(target, Delete(T.does_not_exist, ignore_missing=True)) is target


def test_unregistered_delete():
    glommer = Glommer(register_default_types=False)

    with pytest.raises(UnregisteredTarget, match='delete'):
        glommer.glom({'a': 1}, Delete('a'))

    with pytest.raises(UnregisteredTarget, match='delete'):
        glom({'a': (1,)}, Delete('a.0'))


def test_bad_delete_target():
    class BadTarget(object):
        def __delattr__(self, name):
            raise Exception("and you trusted me?")

    spec = Delete('a')
    ok_target = lambda: None
    ok_target.a = 1
    glom(ok_target, spec)
    assert not hasattr(ok_target, 'a')

    with pytest.raises(PathDeleteError, match='could not delete'):
        glom(BadTarget(), spec)

    with pytest.raises(PathDeleteError, match='could not delete'):
        delete({}, 'a')
    return


def test_sequence_delete():
    target = {'alist': [0, 1, 2]}
    delete(target, 'alist.1')
    assert target['alist'] == [0, 2]

    with pytest.raises(PathDeleteError, match='could not delete') as exc_info:
        delete(target, 'alist.2')

    exc_repr = repr(exc_info.value)
    assert exc_repr.startswith('PathDeleteError(')
    assert exc_repr.endswith("'2')")
    return


def test_invalid_delete_op_target():
    target = {'afunc': lambda x: 'hi %s' % x}
    spec = T['afunc'](x=1)

    with pytest.raises(ValueError):
        delete(target, spec, None)
    return


def test_delete_ignore_missing():
    assert delete({}, 'a', ignore_missing=True) == {}
    assert delete({}, 'a.b', ignore_missing=True) == {}


def test_star_broadcast():
    core.PATH_STAR = True
    val = {'a': [{'b': [{'c': 1}, {'c': 2}, {'c': 3}]}]}
    assert glom(val, (Assign('a.*.b.*.d', 'a'), 'a.*.b.*.d')) == [['a', 'a', 'a']]
    glom(val, Delete('a.*.b.*.d'))
    assert 'c' in val['a'][0]['b'][0]
    assert 'd' not in val['a'][0]['b'][0]
    core.PATH_STAR = False
