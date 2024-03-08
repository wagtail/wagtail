
import sys
from xml.etree import cElementTree as ElementTree

import pytest

from glom import glom, SKIP, STOP, Path, Inspect, Coalesce, CoalesceError, Val, Call, T, S, Invoke, Spec, Ref
from glom import Auto, Fill, Iter, A, Vars, Val, Literal, GlomError, Pipe

import glom.core as glom_core
from glom.core import UP, ROOT, bbformat, bbrepr
from glom.mutation import PathAssignError

from glom import OMIT, Let, Literal  # backwards compat


def test_initial_integration():
    class Example(object):
        pass

    example = Example()
    subexample = Example()
    subexample.name = 'good_name'
    example.mapping = {'key': subexample}

    val = {'a': {'b': 'c'},  # basic dictionary nesting
           'example': example,  # basic object
           'd': {'e': ['f'],    # list in dictionary
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],  # list of dictionaries
           'n': 'o'}

    spec = {'a': (Inspect(recursive=True), 'a', 'b'),  # inspect just prints here
            'name': 'example.mapping.key.name',  # test object access
            'e': 'd.e',  # d.e[0] or d.e: (callable to fetch 0)
            'i': ('i', [{'j': 'j'}]),  # TODO: support True for cases when the value should simply be mapped into the field name?
            'n': ('n', lambda n: n.upper()),
            'p': Coalesce('xxx',
                          'yyy',
                          default='zzz')}

    ret = glom(val, spec)

    print('in: ', val)
    print('got:', ret)
    expected = {'a': 'c',
                'name': 'good_name',
                'e': ['f'],
                'i': [{'j': 'k'}],
                'n': 'O',
                'p': 'zzz'}
    print('exp:', expected)

    assert ret == expected


def test_list_item_lift_and_access():
    val = {'d': {'e': ['f']}}

    assert glom(val, ('d.e', lambda x: x[0])) == 'f'
    assert glom(val, ('d.e', [(lambda x: {'f': x[0]}, 'f')])) == ['f']


def test_coalesce():
    val = {'a': {'b': 'c'},  # basic dictionary nesting
           'd': {'e': ['f'],    # list in dictionary
                 'g': 'h'},
           'i': [{'j': 'k', 'l': 'm'}],  # list of dictionaries
           'n': 'o'}

    assert glom(val, 'a.b') == 'c'
    assert glom(val, Coalesce('xxx', 'yyy', 'a.b')) == 'c'

    # check that defaulting works
    spec = Coalesce('xxx', 'yyy', default='zzz')
    assert glom(val, spec) == 'zzz'
    assert repr(spec) == "Coalesce('xxx', 'yyy', default='zzz')"

    # check that default_factory works
    sentinel_list = []
    factory = lambda: sentinel_list
    assert glom(val, Coalesce('xxx', 'yyy', default_factory=factory)) is sentinel_list

    with pytest.raises(ValueError):
        Coalesce('x', 'y', default=1, default_factory=list)

    # check that arbitrary values can be skipped
    assert glom(val, Coalesce('xxx', 'yyy', 'a.b', default='zzz', skip='c')) == 'zzz'

    # check that arbitrary exceptions can be ignored
    assert glom(val, Coalesce(lambda x: 1/0, 'a.b', skip_exc=ZeroDivisionError)) == 'c'

    target = {'a': 1, 'b': 3, 'c': 4}
    spec = Coalesce('a', 'b', 'c', skip=lambda x: x % 2)
    assert glom(target, spec) == 4

    spec = Coalesce('a', 'b', 'c', skip=(1,))
    assert glom(target, spec) == 3

    with pytest.raises(TypeError):
        Coalesce(bad_kwarg=True)



def test_skip():
    assert OMIT is SKIP  # backwards compat

    target = {'a': {'b': 'c'},  # basic dictionary nesting
              'd': {'e': ['f'],    # list in dictionary
                    'g': 'h'},
              'i': [{'j': 'k', 'l': 'm'}],  # list of dictionaries
              'n': 'o'}

    res = glom(target, {'a': 'a.b',
                        'z': Coalesce('x', 'y', default=SKIP)})
    assert res['a'] == 'c'  # sanity check

    assert 'x' not in target
    assert 'y' not in target
    assert 'z' not in res

    # test that skip works on lists
    target = range(7)
    res = glom(target, [lambda t: t if t % 2 else SKIP])
    assert res == [1, 3, 5]

    # test that skip works on chains (enable conditional applications of transforms)
    target = range(7)
    # double each value if it's even, but convert all values to floats
    res = glom(target, [(lambda x: x * 2 if x % 2 == 0 else SKIP, float)])
    assert res == [0.0, 1.0, 4.0, 3.0, 8.0, 5.0, 12.0]


def test_stop():
    # test that stop works on iterables
    target = iter([0, 1, 2, STOP, 3, 4])
    assert glom(target, [T]) == [0, 1, 2]

    # test that stop works on chains (but doesn't stop iteration up the stack)
    target = ['a', ' b', ' c ', '   ', '  done']
    assert glom(target, [(lambda x: x.strip(),
                          lambda x: x if x else STOP,
                          lambda x: x[0])]) == ['a', 'b', 'c', '', 'd']
    return


def test_top_level_default():
    expected = object()
    val = glom({}, 'a.b.c', default=expected)
    assert val is expected

    val = glom({}, lambda x: 1/0, skip_exc=ZeroDivisionError)
    assert val is None

    val = glom({}, lambda x: 1/0, skip_exc=ZeroDivisionError, default=expected)
    assert val is expected

    with pytest.raises(KeyError):
        # p degenerate case if you ask me
        glom({}, 'x', skip_exc=KeyError, default=glom_core._MISSING)

    return


def test_val():
    assert Literal is Val
    expected = {'value': 'c',
                'type': 'a.b'}
    target = {'a': {'b': 'c'}}
    val = glom(target, {'value': 'a.b',
                        'type': Val('a.b')})

    assert val == expected

    assert glom(None, Val('success')) == 'success'
    assert repr(Val(3.14)) == 'Val(3.14)'
    assert repr(Val(3.14)) == 'Val(3.14)'


def test_abstract_iterable():
    assert isinstance([], glom_core._AbstractIterable)

    class MyIterable(object):
        def __iter__(self):
            return iter([1, 2, 3])
    mi = MyIterable()
    assert list(mi) == [1, 2, 3]

    assert isinstance(mi, glom_core._AbstractIterable)


def test_call_and_target():
    class F(object):
        def __init__(s, a, b, c): s.a, s.b, s.c = a, b, c

    call_f = Call(F, kwargs=dict(a=T, b=T, c=T))
    assert repr(call_f)
    val = glom(1, call_f)
    assert (val.a, val.b, val.c) == (1, 1, 1)
    class F(object):
        def __init__(s, a): s.a = a
    val = glom({'one': F('two')}, Call(F, args=(T['one'].a,)))
    assert val.a == 'two'
    assert glom({'a': 1}, Call(F, kwargs=T)).a == 1
    assert glom([1], Call(F, args=T)).a == 1
    assert glom(F, T(T)).a == F
    assert glom([F, 1], T[0](T[1]).a) == 1
    assert glom([[1]], S[UP][Val(T)][0][0]) == 1
    assert glom([[1]], S[UP][UP][UP][Val(T)]) == [[1]]  # tops out

    assert list(glom({'a': 'b'}, Call(T.values))) == ['b']

    with pytest.raises(TypeError, match='expected func to be a callable or T'):
        Call(func=object())

    assert glom(lambda: 'hi', Call()) == 'hi'
    return


def test_invoke():
    args = []
    def test(*a, **kw):
        args.append(a)
        args.append(kw)
        return 'test'

    assert glom('a', Invoke(len).specs(T)) == 1
    data = {
        'args': (1, 2),
        'args2': (4, 5),
        'kwargs': {'a': 'a'},
        'c': 'C',
    }
    spec = Invoke(test).star(args='args'
        ).constants(3, b='b').specs(c='c'
        ).star(args='args2', kwargs='kwargs')
    repr(spec)  # no exceptions
    assert repr(Invoke(len).specs(T)) == 'Invoke(len).specs(T)'
    assert (repr(Invoke.specfunc(next).constants(len).constants(1))
            == 'Invoke.specfunc(next).constants(len).constants(1)')
    assert glom(data, spec) == 'test'
    assert args == [
        (1, 2, 3, 4, 5),
        {'a': 'a', 'b': 'b', 'c': 'C'}]
    args = []
    assert glom(test, Invoke.specfunc(T)) == 'test'
    assert args == [(), {}]
    repr_spec = Invoke.specfunc(T).star(args='args'
        ).constants(3, b='b').specs(c='c'
        ).star(args='args2', kwargs='kwargs')
    assert repr(eval(repr(repr_spec), locals(), globals())) == repr(repr_spec)

    with pytest.raises(TypeError, match='expected func to be a callable or Spec instance'):
        Invoke(object())
    with pytest.raises(TypeError, match='expected one or both of args/kwargs'):
        Invoke(T).star()

    # test interleaved pos args
    def ret_args(*a, **kw):
        return a, kw

    spec = Invoke(ret_args).constants(1).specs({}).constants(3)
    assert glom({}, spec) == ((1, {}, 3), {})
    # .endswith because ret_arg's repr includes a memory location
    assert repr(spec).endswith(').constants(1).specs({}).constants(3)')

    # test overridden kwargs
    should_stay_empty = []
    spec = Invoke(ret_args).constants(a=1).specs(a=should_stay_empty.append).constants(a=3)
    assert glom({}, spec) == ((), {'a': 3})
    assert len(should_stay_empty) == 0
    assert repr(spec).endswith(').constants(a=3)')

    # bit of coverage
    target = (lambda: 'hi', {})
    spec = Invoke(T[0])
    assert glom(target, spec) == 'hi'
    # and a bit more
    spec = spec.star(kwargs=T[1])
    assert repr(spec) == 'Invoke(T[0]).star(kwargs=T[1])'
    assert glom(target, spec) == 'hi'



def test_spec_and_recursion():
    assert repr(Spec('a.b.c')) == "Spec('a.b.c')"

    # Call doesn't normally recurse, but Spec can make it do so
    assert glom(
        ['a', 'b', 'c'],
        Call(list, args=(
            Spec(Call(reversed, args=(Spec(T),))),)
        )) == ['c', 'b', 'a']
    assert glom(['cat', {'cat': 1}], T[1][T[0]]) == 1
    assert glom(
        [['ab', 'cd', 'ef'], ''.join],
        Call(T[1], args=(Spec((T[0], [T[1:]])),))) == 'bdf'

    # test that spec works on the left of a dict spec
    assert glom({'a': 'A'}, {Spec('a'): 'a', 'a': 'a'}) == {'A': 'A', 'a': 'A'}


def test_scope():
    assert glom(None, S['foo'], scope={'foo': 'bar'}) == 'bar'

    target = range(3)
    spec = [(S, lambda S: S['multiplier'] * S[T])]
    scope = {'multiplier': 2}
    assert glom(target, spec, scope=scope) == [0, 2, 4]
    scope = {'multiplier': 2.5}
    assert glom(target, spec, scope=scope) == [0.0, 2.5, 5.0]


def test_seq_getitem():
    assert glom({'items': [0, 1, 2, 3]}, 'items.1') == 1
    assert glom({'items': (9, 8, 7, 6)}, 'items.-3') == 8

    with pytest.raises(glom_core.PathAccessError):
        assert glom({'items': (9, 8, 7, 6)}, 'items.fun')


# examples from http://sedimental.org/glom_restructured_data.html

def test_beyond_access():
    # 1
    target = {'galaxy': {'system': {'planet': 'jupiter'}}}
    spec = 'galaxy.system.planet'

    output = glom(target, spec)
    assert output == 'jupiter'

    # 2
    target = {'system': {'planets': [{'name': 'earth'}, {'name': 'jupiter'}]}}

    output = glom(target, ('system.planets', ['name']))
    assert output == ['earth', 'jupiter']

    # 3
    target = {'system': {'planets': [{'name': 'earth', 'moons': 1},
                                     {'name': 'jupiter', 'moons': 69}]}}
    spec = {'names': ('system.planets', ['name']),
            'moons': ('system.planets', ['moons'])}

    output = glom(target, spec)
    assert output == {'names': ['earth', 'jupiter'], 'moons': [1, 69]}


def test_python_native():
    # 4
    target = {'system': {'planets': [{'name': 'earth', 'moons': 1},
                                     {'name': 'jupiter', 'moons': 69}]}}


    output = glom(target, {'moon_count': ('system.planets', ['moons'], sum)})
    assert output == {'moon_count': 70}

    # 5
    spec = T['system']['planets'][-1].values()

    output = glom(target, spec)
    assert set(output) == set(['jupiter', 69])  # for ordering reasons

    with pytest.raises(glom_core.GlomError):
        spec = T['system']['comets'][-1].values()
        output = glom(target, spec)


def test_glom_extra_kwargs():
    # for coverage
    with pytest.raises(TypeError):
        glom({'a': 'a'}, 'a', invalid_kwarg='yes')


def test_inspect():
    # test repr
    assert repr(Inspect()) == '<INSPECT>'

    target = {'a': {'b': 'c'}}

    import pdb
    # test breakpoint
    assert Inspect(breakpoint=True).breakpoint == pdb.set_trace
    with pytest.raises(TypeError):
        Inspect(breakpoint='lol')

    tracker = []
    spec = {'a': Inspect('a.b', echo=False, breakpoint=lambda: tracker.append(True))}

    glom(target, spec)

    assert len(tracker) == 1

    # test post_mortem
    assert Inspect(post_mortem=True).post_mortem == pdb.post_mortem
    with pytest.raises(TypeError):
        Inspect(post_mortem='lol')

    tracker = []
    spec = {'a': Inspect('nope.nope', post_mortem=lambda: tracker.append(True))}

    assert glom(target, spec, default='default') == 'default'
    assert len(tracker) == 1


def test_ref():
    assert glom([[[]]], Ref('item', [Ref('item')])) == [[[]]]
    with pytest.raises(Exception):  # check that it recurses downards and dies on int iteration
        glom([[[1]]], Ref('item', [Ref('item')]))
    assert repr(Ref('item', (T[1], Ref('item')))) == "Ref('item', (T[1], Ref('item')))"

    etree2dicts = Ref('ElementTree',
        {"tag": "tag", "text": "text", "attrib": "attrib", "children": (iter, [Ref('ElementTree')])})
    etree2tuples = Fill(Ref('ElementTree', (T.tag, Iter(Ref('ElementTree')).all())))
    etree = ElementTree.fromstring('''
    <html>
      <head>
        <title>the title</title>
      </head>
      <body id="the-body">
        <p>A paragraph</p>
      </body>
    </html>''')
    glom(etree, etree2dicts)
    glom(etree, etree2tuples)


def test_pipe():
    assert glom(1, Pipe("__class__", "__name__", str.upper)) == 'INT'
    assert repr(Pipe(1, Pipe([2], dict))) == 'Pipe(1, Pipe([2], dict))'


_IS_PYPY = '__pypy__' in sys.builtin_module_names
@pytest.mark.skipif(_IS_PYPY, reason='pypy othertype.__repr__ is never object.__repr__')
def test_api_repr():
    import glom

    spec_types_wo_reprs = []
    for k, v in glom.__dict__.items():
        if not callable(getattr(v, 'glomit', None)):
            continue
        if v.__repr__ is object.__repr__:
            spec_types_wo_reprs.append(k)  # pragma: no cover

    assert set(spec_types_wo_reprs) == set([])


def test_bbformat():
    assert bbformat("{0.__name__}", int) == "int"


def test_bbrepr():
    assert bbrepr({int: dict}) == "{int: dict}"
