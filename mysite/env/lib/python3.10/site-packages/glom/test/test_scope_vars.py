
import pytest

from glom import glom, Path, S, A, T, Vars, Val, GlomError, M, SKIP, Let

from glom.core import ROOT
from glom.mutation import PathAssignError

def test_s_scope_assign():
    data = {'a': 1, 'b': [{'c': 2}, {'c': 3}]}
    output = [{'a': 1, 'c': 2}, {'a': 1, 'c': 3}]
    assert glom(data, (S(a='a'), ('b', [{'a': S['a'], 'c': 'c'}]))) == output
    assert glom(data, ('b', [{'a': S[ROOT][Val(T)]['a'], 'c': 'c'}])) == output

    with pytest.raises(TypeError):
        S('posarg')
    with pytest.raises(TypeError):
        S()

    assert glom([[1]], (S(v=Vars()), [[A.v.a]], S.v.a)) == 1
    assert glom(1, (S(v=lambda t: {}), A.v['a'], S.v['a'])) == 1
    with pytest.raises(GlomError):
        glom(1, (S(v=lambda t: 1), A.v.a))

    class FailAssign(object):
        def __setattr__(self, name, val):
            raise Exception('nope')

    with pytest.raises(PathAssignError):
        glom(1, (S(v=lambda t: FailAssign()), Path(A.v, 'a')))

    assert repr(S(a=T.a.b)) == 'S(a=T.a.b)'

    spec = (S(a='x'), S.a)
    assert glom({'x': 'y'}, spec) == 'y'

    return


def test_globals():
    assert glom([[1]], ([[A.globals.a]], S.globals.a)) == 1


def test_vars():
    assert glom(1, A.a) == 1  # A should not change the target
    assert glom(1, (A.a, S.a)) == 1
    # check that tuple vars don't "leak" into parent tuple
    assert glom(1, (A.t, Val(2), A.t, S.t)) == 2
    assert glom(1, (A.t, (Val(2), A.t), S.t)) == 1
    let = S(v=Vars({'b': 2}, c=3))
    assert glom(1, (let, A.v.a, S.v.a)) == 1
    with pytest.raises(AttributeError):
        glom(1, (let, S.v.a))  # check that Vars() inside a spec doesn't hold state
    assert glom(1, (let, Path(A, 'v', 'a'), S.v.a)) == 1
    assert glom(1, (let, S.v.b)) == 2
    assert glom(1, (let, S.v.c)) == 3
    assert repr(let) == "S(v=Vars({'b': 2}, c=3))"
    assert repr(Vars(a=1, b=2)) in (
        "Vars(a=1, b=2)", "Vars(b=2, a=1)")
    assert repr(Vars(a=1, b=2).glomit(None, None)) in (
        "ScopeVars({'a': 1, 'b': 2})", "Vars({'b': 2, 'a': 1})")

    assert repr(A.b["c"]) == "A.b['c']"


def test_scoped_vars():
    target = list(range(10)) + list(range(5))

    scope_globals = glom(target, ([A.globals.last], S.globals))
    assert scope_globals.last == 4
    assert dict(scope_globals) == {'last': 4}


def test_max_skip():
    target = list(range(10)) + list(range(5))

    max_spec = (S(max=Vars(max=0)),
                [((M > M(S.max.max)) & A.max.max) | Val(SKIP)],
                 S.max)
    result = glom(target, max_spec)
    assert result.max == 9


def test_let():  # backwards compat 2020-07
    data = {'a': 1, 'b': [{'c': 2}, {'c': 3}]}
    output = [{'a': 1, 'c': 2}, {'a': 1, 'c': 3}]
    assert glom(data, (Let(a='a'), ('b', [{'a': S['a'], 'c': 'c'}]))) == output
    assert glom(data, ('b', [{'a': S[ROOT][Val(T)]['a'], 'c': 'c'}])) == output

    with pytest.raises(TypeError):
        Let('posarg')
    with pytest.raises(TypeError):
        Let()

    assert glom([[1]], (Let(v=Vars()), [[A.v.a]], S.v.a)) == 1
    assert glom(1, (Let(v=lambda t: {}), A.v['a'], S.v['a'])) == 1
    with pytest.raises(GlomError):
        glom(1, (Let(v=lambda t: 1), A.v.a))

    class FailAssign(object):
        def __setattr__(self, name, val):
            raise Exception('nope')

    with pytest.raises(PathAssignError):
        glom(1, (Let(v=lambda t: FailAssign()), Path(A.v, 'a')))

    assert repr(Let(a=T.a.b)) == 'Let(a=T.a.b)'
