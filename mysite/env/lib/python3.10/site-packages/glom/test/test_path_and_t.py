
from pytest import raises

from glom import glom, Path, S, T, A, PathAccessError, GlomError, BadSpec, Assign, Delete
from glom import core

def test_list_path_access():
    assert glom(list(range(10)), Path(1)) == 1


def test_path():
    _obj = object()
    target = {'a': {'b.b': [None, {_obj: [None, None, 'd']}]}}

    assert glom(target, Path('a', 'b.b', 1, _obj, -1)) == 'd'


def test_empty_path_access():
    target = {}

    assert glom(target, Path()) is target
    assert glom(target, (Path(), Path(), Path())) is target

    dup_dict = glom(target, {'target': Path(),
                             'target2': Path()})
    dup_dict['target'] is target
    dup_dict['target2'] is target


def test_path_t_roundtrip():
    # check that T repr roundrips
    assert repr(T['a'].b.c()) == "T['a'].b.c()"
    assert repr(T[1:]) == "T[1:]"
    assert repr(T[::3, 1:, 1:2, :2:3]) == "T[::3, 1:, 1:2, :2:3]"

    # check that Path repr roundtrips
    assert repr(Path('a', 1, 'b.b', -1.0)) == "Path('a', 1, 'b.b', -1.0)"

    # check that Path repr roundtrips when it contains Ts
    assert repr(Path(T['a'].b, 'c', T['d'].e)) == "Path(T['a'].b, 'c', T['d'].e)"

    # check that T instances containing Path access revert to repring with Path
    assert repr(Path(T['a'].b, 'c', T['d'].e).path_t) == "Path(T['a'].b, 'c', T['d'].e)"

    # check that Paths containing only T objects reduce to a T (joining the T objects)
    assert repr(Path(T['a'].b, T.c())) == "T['a'].b.c()"

    # check that multiple nested paths reduce
    assert repr(Path(Path(Path('a')))) == "Path('a')"

    # check builtin repr
    assert repr(T[len]) == 'T[len]'
    assert repr(T.func(len, sum)) == 'T.func(len, sum)'

    # check * and **
    assert repr(T.__star__().__starstar__()) == 'T.__star__().__starstar__()'
    assert repr(Path('a', T.__star__().__starstar__())) == "Path('a', T.__star__().__starstar__())"


def test_path_access_error_message():

    # test fuzzy access
    with raises(GlomError) as exc_info:
        glom({}, 'a.b')
    assert ("PathAccessError: could not access 'a', part 0 of Path('a', 'b'), got error: KeyError"
            in exc_info.exconly())
    ke = repr(KeyError('a'))  # py3.7+ changed the keyerror repr
    assert repr(exc_info.value) == "PathAccessError(" + ke + ", Path('a', 'b'), 0)"

    # test multi-part Path with T, catchable as a KeyError
    with raises(KeyError) as exc_info:
        # don't actually use glom to copy your data structures please
        glom({'a': {'b': 'c'}}, Path('a', T.copy(), 'd'))
    assert ("PathAccessError: could not access 'd', part 3 of Path('a', T.copy(), 'd'), got error: KeyError"
            in exc_info.exconly())
    ke = repr(KeyError('d'))  # py3.7+ changed the keyerror repr
    assert repr(exc_info.value) == "PathAccessError(" + ke + ", Path('a', T.copy(), 'd'), 3)"

    # test AttributeError
    with raises(GlomError) as exc_info:
        glom({'a': {'b': 'c'}}, Path('a', T.b))
    assert ("PathAccessError: could not access 'b', part 1 of Path('a', T.b), got error: AttributeError"
            in exc_info.exconly())
    ae = repr(AttributeError("'dict' object has no attribute 'b'"))
    assert repr(exc_info.value) == "PathAccessError(" + ae + ", Path(\'a\', T.b), 1)"


def test_t_picklability():
    import pickle

    class TargetType(object):
        def __init__(self):
            self.attribute = lambda: None
            self.attribute.method = lambda: {'key': lambda x: x * 2}

    spec = T.attribute.method()['key'](x=5)

    rt_spec = pickle.loads(pickle.dumps(spec))
    assert repr(spec) == repr(rt_spec)

    assert glom(TargetType(), spec) == 10

    s_spec = S.attribute
    assert repr(s_spec) == repr(pickle.loads(pickle.dumps(s_spec)))


def test_a_forbidden():
    with raises(BadSpec):
        A()  # cannot assign to function call
    with raises(BadSpec):
        glom(1, A)  # cannot assign without destination


def test_s_magic():
    assert glom(None, S.test, scope={'test': 'value'}) == 'value'

    with raises(PathAccessError):
        glom(1, S.a)  # ref to 'a' which doesn't exist in scope

    with raises(PathAccessError):
        glom(1, A.b.c)

    return


def test_path_len():

    assert len(Path()) == 0
    assert len(Path('a', 'b', 'c')) == 3
    assert len(Path.from_text('1.2.3.4')) == 4

    assert len(Path(T)) == 0
    assert len(Path(T.a.b.c)) == 3
    assert len(Path(T.a()['b'].c.d)) == 5


def test_path_getitem():
    path = Path(T.a.b.c)

    assert path[0] == Path(T.a)
    assert path[1] == Path(T.b)
    assert path[2] == Path(T.c)
    assert path[-1] == Path(T.c)
    assert path[-2] == Path(T.b)

    with raises(IndexError, match='Path index out of range'):
        path[4]

    with raises(IndexError, match='Path index out of range'):
        path[-14]
    return


def test_path_slices():
    path = Path(T.a.b, 1, 2, T(test='yes'))

    assert path[::] == path

    # positive indices
    assert path[3:] == Path(2, T(test='yes'))
    assert path[1:3] == Path(T.b, 1)
    assert path[:3] == Path(T.a.b, 1)

    # positive indices backwards
    assert path[2:1] == Path()

    # negative indices forward
    assert path[-1:] == Path(T(test='yes'))
    assert path[:-2] == Path(T.a.b, 1)
    assert path[-3:-1] == Path(1, 2)

    # negative indices backwards
    assert path[-1:-3] == Path()

    # slicing and stepping
    assert path[1::2] == Path(T.b, 2)


def test_path_values():
    path = Path(T.a.b, 1, 2, T(test='yes'))

    assert path.values() == ('a', 'b', 1, 2, ((), {'test': 'yes'}))

    assert Path().values() == ()


def test_path_items():
    path = Path(T.a, 1, 2, T(test='yes'))

    assert path.items() == (('.', 'a'),
                            ('P', 1), ('P', 2),
                            ('(', ((), {'test': 'yes'})))

    assert Path().items() == ()


def test_path_star():
    core.PATH_STAR = True
    val = {'a': [1, 2, 3]}
    assert glom(val, 'a.*') == [1, 2, 3]
    val['a'] = [{'b': v} for v in val['a']]
    assert glom(val, 'a.*.b') == [1, 2, 3]
    assert glom(val, T['a'].__star__()['b']) == [1, 2, 3]
    assert glom(val, Path('a', T.__star__(), 'b')) == [1, 2, 3]
    # multi-paths eat errors
    assert glom(val, Path('a', T.__star__(), T.b)) == []
    val = [[[1]]]
    assert glom(val, '**') == [ [[1]], [1], 1]
    val = {'a': [{'b': [{'c': 1}, {'c': 2}, {'d': {'c': 3}}]}]}
    assert glom(val, '**.c') == [1, 2, 3]
    assert glom(val, 'a.**.c') == [1, 2, 3]
    assert glom(val, T['a'].__starstar__()['c']) == [1, 2, 3]
    assert glom(val, 'a.*.b.*.c') == [[1, 2]]
    # errors
    class ErrDict(dict):
        def __getitem__(key): 1/0
    assert ErrDict(val).keys()  # it will try to iterate
    assert glom(ErrDict(val), '**') == []
    # object access
    class A:
        def __init__(self):
            self.a = 1
            self.b = {'c': 2}
    val = A()
    assert glom(val, '*') == [1, {'c': 2}]
    assert glom(val, '**') == [1, {'c': 2}, 2]
    core.PATH_STAR = False


def test_star_broadcast():
    core.PATH_STAR = True
    val = {'a': [1, 2, 3]}
    assert glom(val, Path.from_text('a.*').path_t + 1) == [2, 3, 4]
    val = {'a': [{'b': [{'c': 1}, {'c': 2}, {'c': 3}]}]}
    assert glom(val, Path.from_text('**.c').path_t + 1) == [2, 3, 4]
    core.PATH_STAR = False


def test_star_warning():
    '''check that the default behavior is as expected; this will change when * is default on'''
    assert glom({'*': 1}, '*') == 1
    assert Path._STAR_WARNED


def test_path_eq():
    assert Path('a', 'b') == Path('a', 'b')
    assert Path('a') != Path('b')

    assert Path() != object()


def test_path_eq_t():
    assert Path(T.a.b) == T.a.b
    assert Path(T.a.b.c) != T.a.b


def test_startswith():
    ref = T.a.b[1]

    assert Path(ref).startswith(T)
    assert Path(ref).startswith(T.a.b)
    assert Path(ref).startswith(ref)
    assert Path(ref).startswith(ref.c) is False

    assert Path('a.b.c').startswith(Path())
    assert Path('a.b.c').startswith('a.b.c')

    with raises(TypeError):
        assert Path('a.b.c').startswith(None)

    return


def test_from_t_identity():
    ref = Path(T.a.b)
    assert ref.from_t() == ref
    assert ref.from_t() is ref


def test_t_dict_key():
    target = {'a': 'A'}
    assert glom(target, {T['a']: 'a'}) == {'A': 'A'}


def test_t_arithmetic():
    t = 2
    assert glom(t, T + T) == 4
    assert glom(t, T * T) == 4
    assert glom(t, T ** T) == 4
    assert glom(t, T / 1) == 2
    assert glom(t, T % 1) == 0
    assert glom(t, T - 1) == 1
    assert glom(t, T & T) == 2
    assert glom(t, T | 1) == 3
    assert glom(t, T ^ T) == 0
    assert glom(2, ~T) == -3
    assert glom(t, -T) == -2


def test_t_arithmetic_reprs():
    assert repr(T + T) == "T + T"
    assert repr(T + (T / 2 * (T - 5) % 4)) == "T + (T / 2 * (T - 5) % 4)"
    assert repr(T & 7 | (T ^ 6)) == "T & 7 | (T ^ 6)"
    assert repr(-(~T)) == "-(~T)"


def test_t_arithmetic_errors():
    with raises(PathAccessError, match='zero'):
        glom(0, T / 0)

    with raises(PathAccessError, match='unsupported operand type'):
        glom(None, T / 2)

    return


def test_t_dunders():
    with raises(AttributeError) as exc_info:
        T.__name__

    assert 'use T.__("name__")' in str(exc_info.value)

    assert glom(1, T.__('class__')) is int


def test_path_cache():
    assert Path.from_text('a.b.c') is Path.from_text('a.b.c')
    pre = Path._MAX_CACHE
    Path._MAX_CACHE = 0
    assert Path.from_text('d.e.f') is not Path.from_text('d.e.f')
