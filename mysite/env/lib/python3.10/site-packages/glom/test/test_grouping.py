from __future__ import division

from pytest import raises

from glom import glom, T, SKIP, STOP, Auto, BadSpec
from glom.grouping import Group, First, Avg, Max, Min, Sample, Limit

from glom.reduction import Merge, Flatten, Sum, Count


def test_bucketing():
    assert glom(range(4), Group({lambda t: t % 2 == 0: [T]})) == {True: [0, 2], False: [1, 3]}
    assert (glom(range(6), Group({lambda t: t % 3: {lambda t: t % 2: [lambda t: t / 10.0]}})) ==
        {0: {0: [0.0], 1: [0.3]}, 1: {1: [0.1], 0: [0.4]}, 2: {0: [0.2], 1: [0.5]}})



def test_corner_cases():
    target = range(5)

    # immediate stop dict
    assert glom(target, Group({(lambda t: STOP): [T]})) == {}

    # immediate stop list
    assert glom(target, Group([lambda t: STOP])) == []

    # dict key SKIP
    assert glom(target, Group({(lambda t: SKIP if t < 3 else t): T})) == {3: 3, 4: 4}

    # dict val SKIP
    assert glom(target, Group({T: lambda t: t if t % 2 else SKIP})) == {3: 3, 1: 1}

    # list val SKIP
    assert glom(target, Group([lambda t: t if t % 2 else SKIP])) == [1, 3]

    # embedded auto spec (lol @ 0 being 0 bit length)
    assert glom(target, Group({Auto(('bit_length', T())): [T]})) == {0: [0], 1: [1], 2: [2, 3], 3: [4]}

    # no dicts inside lists in Group mode
    with raises(BadSpec):
        assert glom(target, Group([{T: T}]))

    # check only supported types
    with raises(BadSpec):
        assert glom(target, Group('no string support yet'))

    # bucket ints by their bit length and then odd/even, limited to 3 per bucket
    spec = Group({T.bit_length(): {lambda t: t % 2: Limit(3)}})
    res = glom(range(20), spec)
    assert res == {0: {0: [0]},
                   1: {1: [1]},
                   2: {0: [2], 1: [3]},
                   3: {0: [4, 6], 1: [5, 7]},
                   4: {0: [8, 10, 12], 1: [9, 11, 13]}}

    return


def test_agg():
    t = list(range(10))
    assert glom(t, Group(First())) == 0
    assert glom(t, Group(T)) == 9  # this is basically Last

    assert glom(t, Group(Avg())) == sum(t) / len(t)
    assert glom(t, Group(Sum())) == sum(t)

    assert glom([0, 1, 0], Group(Max())) == 1
    assert glom([1, 0, 1], Group(Min())) == 0

    assert repr(Group(First())) == 'Group(First())'
    assert repr(Avg()) == 'Avg()'
    assert repr(Max()) == 'Max()'
    assert repr(Min()) == 'Min()'
    assert repr(Sum()) == 'Sum()'
    assert repr(Count()) == 'Count()'

    assert glom(range(10), Group({lambda t: t % 2: Count()})) == {
		0: 5, 1: 5}


def test_limit():
    t = list(range(10))
    assert glom(t, Group(Limit(1, T))) == 0
    assert glom(t, Group(Limit(3, Max()))) == 2
    assert glom(t, Group(Limit(3, [T]))) == [0, 1, 2]

    assert repr(Group(Limit(3, Max()))) == 'Group(Limit(3, Max()))'

    with raises(BadSpec):
        assert glom(t, Limit(1))  # needs to be wrapped in Group for now
    return


def test_reduce():
    assert glom([[1], [2, 3]], Group(Flatten())) == [1, 2, 3]
    assert glom([{'a': 1}, {'b': 2}], Group(Merge())) == {'a': 1, 'b': 2}
    assert glom([[[1]], [[2, 3], [4]]], Group(Flatten(Flatten()))) == [1, 2, 3, 4]


def test_sample():
    spec = Group(Sample(5))
    assert glom([1, 2, 3], spec) == [1, 2, 3]

    assert repr(spec) == 'Group(Sample(5))'

    s = glom([1, 2, 3], Group(Sample(2)))
    assert s in [[1, 2], [1, 3], [2, 1], [2, 3], [3, 1], [3, 2]]
