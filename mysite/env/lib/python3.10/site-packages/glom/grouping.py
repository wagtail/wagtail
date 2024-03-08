"""
Group mode
"""
from __future__ import division

import random

from boltons.typeutils import make_sentinel

from .core import glom, MODE, SKIP, STOP, TargetRegistry, Path, T, BadSpec, _MISSING


ACC_TREE = make_sentinel('ACC_TREE')
ACC_TREE.__doc__ = """
tree of accumulators for aggregation;
structure roughly corresponds to the result,
but is not 1:1; instead the main purpose is to ensure
data is kept until the Group() finishes executing
"""

CUR_AGG = make_sentinel('CUR_AGG')
CUR_AGG.__doc__ = """
the spec which is currently performing aggregation --
useful for specs that want to work in either "aggregate"
mode, or "spec" mode depending on if they are in Group mode
or not; this sentinel in the Scope allows a spec to decide
if it is "closest" to the Group and so should behave
like an aggregate, or if it is further away and so should
have normal spec behavior.
"""


def target_iter(target, scope):
    iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])

    try:
        iterator = iterate(target)
    except Exception as e:
        raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                        % (target.__class__.__name__, Path(*scope[Path]), e))
    return iterator


class Group(object):
    """supports nesting grouping operations --
    think of a glom-style recursive boltons.iterutils.bucketize

    the "branches" of a Group spec are dicts;
    the leaves are lists, or an Aggregation object
    an Aggregation object is any object that defines the
    method agg(target, accumulator)

    For example, here we get a map of even and odd counts::

    >>> glom(range(10), Group({lambda x: x % 2: T}))
    {0: 8, 1: 9}

    And here we create a `"bucketized"
    <https://boltons.readthedocs.io/en/latest/iterutils.html#boltons.iterutils.bucketize>`_
    map of even and odd numbers::

    >>> glom(range(10), Group({lambda x: x % 2: [T]}))
    {0: [0, 2, 4, 6, 8], 1: [1, 3, 5, 7, 9]}

    target is the current target, accumulator is a dict
    maintained by Group mode

    unlike Iter(), Group() converts an iterable target
    into a single result; Iter() converts an iterable
    target into an iterable result

    """
    def __init__(self, spec):
        self.spec = spec

    def glomit(self, target, scope):
        scope[MODE] = GROUP
        scope[CUR_AGG] = None  # reset aggregation tripwire for sub-specs
        scope[ACC_TREE] = {}

        # handle the basecase where the spec stops immediately
        # TODO: something smarter
        if type(self.spec) in (dict, list):
            ret = type(self.spec)()
        else:
            ret = None

        for t in target_iter(target, scope):
            last, ret = ret, scope[glom](t, self.spec, scope)
            if ret is STOP:
                return last
        return ret

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r)' % (cn, self.spec)


def GROUP(target, spec, scope):
    """
    Group mode dispatcher; also sentinel for current mode = group
    """
    recurse = lambda spec: scope[glom](target, spec, scope)
    tree = scope[ACC_TREE]  # current acuumulator support structure
    if callable(getattr(spec, "agg", None)):
        return spec.agg(target, tree)
    elif callable(spec):
        return spec(target)
    _spec_type = type(spec)
    if _spec_type not in (dict, list):
        raise BadSpec("Group mode expected dict, list, callable, or"
                      " aggregator, not: %r" % (spec,))
    _spec_id = id(spec)
    try:
        acc = tree[_spec_id]  # current accumulator
    except KeyError:
        acc = tree[_spec_id] = _spec_type()
    if _spec_type is dict:
        done = True
        for keyspec, valspec in spec.items():
            if tree.get(keyspec, None) is STOP:
                continue
            key = recurse(keyspec)
            if key is SKIP:
                done = False  # SKIP means we still want more vals
                continue
            if key is STOP:
                tree[keyspec] = STOP
                continue
            if key not in acc:
                # TODO: guard against key == id(spec)
                tree[key] = {}
            scope[ACC_TREE] = tree[key]
            result = recurse(valspec)
            if result is STOP:
                tree[keyspec] = STOP
                continue
            done = False  # SKIP or returning a value means we still want more vals
            if result is not SKIP:
                acc[key] = result
        if done:
            return STOP
        return acc
    elif _spec_type is list:
        for valspec in spec:
            if type(valspec) is dict:
                # doesn't make sense due to arity mismatch. did you mean [Auto({...})] ?
                raise BadSpec('dicts within lists are not'
                              ' allowed while in Group mode: %r' % spec)
            result = recurse(valspec)
            if result is STOP:
                return STOP
            if result is not SKIP:
                acc.append(result)
        return acc
    raise ValueError("{} not a valid spec type for Group mode".format(_spec_type))  # pragma: no cover


class First(object):
    """
    holds onto the first value

    >>> glom([1, 2, 3], Group(First()))
    1
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree:
            tree[self] = STOP
            return target
        return STOP

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Avg(object):
    """
    takes the numerical average of all values;
    raises exception on non-numeric value

    >>> glom([1, 2, 3], Group(Avg()))
    2.0
    """
    __slots__ = ()

    def agg(self, target, tree):
        try:
            avg_acc = tree[self]
        except KeyError:
            # format is [sum, count]
            avg_acc = tree[self] = [0.0, 0]
        avg_acc[0] += target
        avg_acc[1] += 1
        return avg_acc[0] / avg_acc[1]

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Max(object):
    """
    takes the maximum of all values;
    raises exception on values that are not comparable

    >>> glom([1, 2, 3], Group(Max()))
    3
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree or target > tree[self]:
            tree[self] = target
        return tree[self]

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Min(object):
    """
    takes the minimum of all values;
    raises exception on values that are not comparable

    >>> glom([1, 2, 3], Group(Min()))
    1
    """
    __slots__ = ()

    def agg(self, target, tree):
        if self not in tree or target < tree[self]:
            tree[self] = target
        return tree[self]

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Sample(object):
    """takes a random sample of the values

    >>> glom([1, 2, 3], Group(Sample(2)))  # doctest: +SKIP
    [1, 3]
    >>> glom(range(5000), Group(Sample(2)))  # doctest: +SKIP
    [272, 2901]

    The advantage of this over :func:`random.sample` is that this can
    take an arbitrarily-sized, potentially-very-long streaming input
    and returns a fixed-size output. Note that this does not stream
    results out, so your streaming input must have finite length.
    """
    __slots__ = ('size',)

    def __init__(self, size):
        self.size = size

    def agg(self, target, tree):
        # simple reservoir sampling scheme
        # https://en.wikipedia.org/wiki/Reservoir_sampling#Simple_algorithm
        if self not in tree:
            tree[self] = [0, []]
        num_seen, sample = tree[self]
        if len(sample) < self.size:
            sample.append(target)
        else:
            pos = random.randint(0, num_seen)
            if pos < self.size:
                sample[pos] = target
        tree[self][0] += 1
        return sample

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.size)



class Limit(object):
    """
    Limits the number of values passed to sub-accumulator

    >>> glom([1, 2, 3], Group(Limit(2)))
    [1, 2]

    To override the default untransformed list output, set the subspec kwarg:

    >>> glom(range(10), Group(Limit(3, subspec={(lambda x: x % 2): [T]})))
    {0: [0, 2], 1: [1]}

    You can even nest Limits in other ``Group`` specs:

    >>> glom(range(10), Group(Limit(5, {(lambda x: x % 2): Limit(2)})))
    {0: [0, 2], 1: [1, 3]}

    """
    __slots__ = ('n', 'subspec')

    def __init__(self, n, subspec=_MISSING):
        if subspec is _MISSING:
            subspec = [T]
        self.n = n
        self.subspec = subspec

    def glomit(self, target, scope):
        if scope[MODE] is not GROUP:
            raise BadSpec("Limit() only valid in Group mode")
        tree = scope[ACC_TREE]  # current accumulator support structure
        if self not in tree:
            tree[self] = [0, {}]
        scope[ACC_TREE] = tree[self][1]
        tree[self][0] += 1
        if tree[self][0] > self.n:
            return STOP
        return scope[glom](target, self.subspec, scope)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.n, self.subspec)
