
import operator
import itertools
from pprint import pprint

from boltons.typeutils import make_sentinel

from .core import T, glom, GlomError, format_invocation, bbrepr, UnregisteredTarget, MODE
from .grouping import GROUP, target_iter, ACC_TREE, CUR_AGG

_MISSING = make_sentinel('_MISSING')


try:
    basestring
except NameError:
    basestring = str


class FoldError(GlomError):
    """Error raised when Fold() is called on non-iterable
    targets, and possibly other uses in the future."""
    pass


class Fold(object):
    """The `Fold` specifier type is glom's building block for reducing
    iterables in data, implementing the classic `fold
    <https://en.wikipedia.org/wiki/Fold_(higher-order_function)>`_
    from functional programming, similar to Python's built-in
    :func:`reduce`.

    Args:
       subspec: A spec representing the target to fold, which must be
          an iterable, or otherwise registered to 'iterate' (with
          :func:`~glom.register`).
       init (callable): A function or type which will be invoked to
          initialize the accumulator value.
       op (callable): A function to call on the accumulator value and
          every value, the result of which will become the new
          accumulator value. Defaults to :func:`operator.iadd`.

    Usage is as follows:

       >>> target = [set([1, 2]), set([3]), set([2, 4])]
       >>> result = glom(target, Fold(T, init=frozenset, op=frozenset.union))
       >>> result == frozenset([1, 2, 3, 4])
       True

    Note the required ``spec`` and ``init`` arguments. ``op`` is
    optional, but here must be used because the :class:`set` and
    :class:`frozenset` types do not work with addition.

    While :class:`~glom.Fold` is powerful, :class:`~glom.Flatten` and
    :class:`~glom.Sum` are subtypes with more convenient defaults for
    day-to-day use.
    """
    def __init__(self, subspec, init, op=operator.iadd):
        self.subspec = subspec
        self.init = init
        self.op = op
        if not callable(op):
            raise TypeError('expected callable for %s op param, not: %r' %
                            (self.__class__.__name__, op))
        if not callable(init):
            raise TypeError('expected callable for %s init param, not: %r' %
                            (self.__class__.__name__, init))

    def glomit(self, target, scope):
        is_agg = False
        if scope[MODE] is GROUP and scope.get(CUR_AGG) is None:
            scope[CUR_AGG] = self
            is_agg = True

        if self.subspec is not T:
            target = scope[glom](target, self.subspec, scope)

        if is_agg:
            return self._agg(target, scope[ACC_TREE])
        try:
            return self._fold(target_iter(target, scope))
        except UnregisteredTarget as ut:
            raise FoldError('can only %s on iterable targets, not %s type (%s)'
                            % (self.__class__.__name__, type(target).__name__, ut))

    def _fold(self, iterator):
        ret, op = self.init(), self.op

        for v in iterator:
            ret = op(ret, v)

        return ret

    def _agg(self, target, tree):
        if self not in tree:
            tree[self] = self.init()
        tree[self] = self.op(tree[self], target)
        return tree[self]

    def __repr__(self):
        cn = self.__class__.__name__
        kwargs = {'init': self.init}
        if self.op is not operator.iadd:
            kwargs['op'] = self.op
        return format_invocation(cn, (self.subspec,), kwargs, repr=bbrepr)


class Sum(Fold):
    """The `Sum` specifier type is used to aggregate integers and other
    numericals using addition, much like the :func:`sum()` builtin.

       >>> glom(range(5), Sum())
       10

    Note that this specifier takes a callable *init* parameter like
    its friends, so to change the start value, be sure to wrap it in a
    callable::

       >>> glom(range(5), Sum(init=lambda: 5.0))
       15.0

    To "sum" lists and other iterables, see the :class:`Flatten`
    spec. For other objects, see the :class:`Fold` specifier type.

    """
    def __init__(self, subspec=T, init=int):
        super(Sum, self).__init__(subspec=subspec, init=init, op=operator.iadd)

    def __repr__(self):
        cn = self.__class__.__name__
        args = () if self.subspec is T else (self.subspec,)
        kwargs = {'init': self.init} if self.init is not int else {}
        return format_invocation(cn, args, kwargs, repr=bbrepr)


class Count(Fold):
    """
    takes a count of how many values occurred

    >>> glom([1, 2, 3], Count())
    3
    """
    __slots__ = ()

    def __init__(self):
        super(Count, self).__init__(
            subspec=T, init=int, op=lambda cur, val: cur + 1)

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Flatten(Fold):
    """The `Flatten` specifier type is used to combine iterables. By
    default it flattens an iterable of iterables into a single list
    containing items from all iterables.

    >>> target = [[1], [2, 3]]
    >>> glom(target, Flatten())
    [1, 2, 3]

    You can also set *init* to ``"lazy"``, which returns a generator
    instead of a list. Use this to avoid making extra lists and other
    collections during intermediate processing steps.
    """
    def __init__(self, subspec=T, init=list):
        if init == 'lazy':
            self.lazy = True
            init = list
        else:
            self.lazy = False
        super(Flatten, self).__init__(subspec=subspec, init=init, op=operator.iadd)

    def _fold(self, iterator):
        if self.lazy:
            return itertools.chain.from_iterable(iterator)
        return super(Flatten, self)._fold(iterator)

    def __repr__(self):
        cn = self.__class__.__name__
        args = () if self.subspec is T else (self.subspec,)
        kwargs = {}
        if self.lazy:
            kwargs['init'] = 'lazy'
        elif self.init is not list:
            kwargs['init'] = self.init
        return format_invocation(cn, args, kwargs, repr=bbrepr)


def flatten(target, **kwargs):
    """At its most basic, ``flatten()`` turns an iterable of iterables
    into a single list. But it has a few arguments which give it more
    power:

    Args:

       init (callable): A function or type which gives the initial
          value of the return. The value must support addition. Common
          values might be :class:`list` (the default), :class:`tuple`,
          or even :class:`int`. You can also pass ``init="lazy"`` to
          get a generator.
       levels (int): A positive integer representing the number of
          nested levels to flatten. Defaults to 1.
       spec: The glomspec to fetch before flattening. This defaults to the
          the root level of the object.

    Usage is straightforward.

      >>> target = [[1, 2], [3], [4]]
      >>> flatten(target)
      [1, 2, 3, 4]

    Because integers themselves support addition, we actually have two
    levels of flattening possible, to get back a single integer sum:

      >>> flatten(target, init=int, levels=2)
      10

    However, flattening a non-iterable like an integer will raise an
    exception:

      >>> target = 10
      >>> flatten(target)
      Traceback (most recent call last):
      ...
      FoldError: can only Flatten on iterable targets, not int type (...)

    By default, ``flatten()`` will add a mix of iterables together,
    making it a more-robust alternative to the built-in
    ``sum(list_of_lists, list())`` trick most experienced Python
    programmers are familiar with using:

      >>> list_of_iterables = [range(2), [2, 3], (4, 5)]
      >>> sum(list_of_iterables, [])
      Traceback (most recent call last):
      ...
      TypeError: can only concatenate list (not "tuple") to list

    Whereas flatten() handles this just fine:

      >>> flatten(list_of_iterables)
      [0, 1, 2, 3, 4, 5]

    The ``flatten()`` function is a convenient wrapper around the
    :class:`Flatten` specifier type. For embedding in larger specs,
    and more involved flattening, see :class:`Flatten` and its base,
    :class:`Fold`.

    """
    subspec = kwargs.pop('spec', T)
    init = kwargs.pop('init', list)
    levels = kwargs.pop('levels', 1)
    if kwargs:
        raise TypeError('unexpected keyword args: %r' % sorted(kwargs.keys()))

    if levels == 0:
        return target
    if levels < 0:
        raise ValueError('expected levels >= 0, not %r' % levels)
    spec = (subspec,)
    spec += (Flatten(init="lazy"),) * (levels - 1)
    spec += (Flatten(init=init),)

    return glom(target, spec)


class Merge(Fold):
    """By default, Merge turns an iterable of mappings into a single,
    merged :class:`dict`, leveraging the behavior of the
    :meth:`~dict.update` method. The start state can be customized
    with *init*, as well as the update operation, with *op*.

    Args:
       subspec: The location of the iterable of mappings. Defaults to ``T``.
       init (callable): A type or callable which returns a base
          instance into which all other values will be merged.
       op (callable): A callable, which takes two arguments, and
          performs a merge of the second into the first. Can also be
          the string name of a method to fetch on the instance created
          from *init*. Defaults to ``"update"``.

    .. note::

       Besides the differing defaults, the primary difference between
       :class:`Merge` and other :class:`Fold` subtypes is that its
       *op* argument is assumed to be a two-argument function which
       has no return value and modifies the left parameter
       in-place. Because the initial state is a new object created with
       the *init* parameter, none of the target values are modified.

    """
    def __init__(self, subspec=T, init=dict, op=None):
        if op is None:
            op = 'update'
        if isinstance(op, basestring):
            test_init = init()
            op = getattr(type(test_init), op, None)
        if not callable(op):
            raise ValueError('expected callable "op" arg or an "init" with an .update()'
                             ' method not %r and %r' % (op, init))
        super(Merge, self).__init__(subspec=subspec, init=init, op=op)

    def _fold(self, iterator):
        # the difference here is that ret is mutated in-place, the
        # variable not being reassigned, as in base Fold.
        ret, op = self.init(), self.op

        for v in iterator:
            op(ret, v)

        return ret


    def _agg(self, target, tree):
        if self not in tree:
            acc = tree[self] = self.init()
        else:
            acc = tree[self]
        self.op(acc, target)
        return acc


def merge(target, **kwargs):
    """By default, ``merge()`` turns an iterable of mappings into a
    single, merged :class:`dict`, leveraging the behavior of the
    :meth:`~dict.update` method. A new mapping is created and none of
    the passed mappings are modified.

    >>> target = [{'a': 'alpha'}, {'b': 'B'}, {'a': 'A'}]
    >>> res = merge(target)
    >>> pprint(res)
    {'a': 'A', 'b': 'B'}

    Args:
       target: The list of dicts, or some other iterable of mappings.

    The start state can be customized with the *init* keyword
    argument, as well as the update operation, with the *op* keyword
    argument. For more on those customizations, see the :class:`Merge`
    spec.

    """
    subspec = kwargs.pop('spec', T)
    init = kwargs.pop('init', dict)
    op = kwargs.pop('op', None)
    if kwargs:
        raise TypeError('unexpected keyword args: %r' % sorted(kwargs.keys()))
    spec = Merge(subspec, init, op)
    return glom(target, spec)
