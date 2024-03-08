"""glom's helpers for streaming use cases.

Specifier types which yield their results incrementally so that they
can be applied to targets which are themselves streaming (e.g. chunks
of rows from a database, lines from a file) without excessive memory
usage.

glom's streaming functionality revolves around a single :class:`Iter`
Specifier type, which has methods to transform the target stream.
"""

from itertools import islice, dropwhile, takewhile, chain
from functools import partial
try:
    from itertools import imap, ifilter
except ImportError:
    # py3
    imap = map
    ifilter = filter

from boltons.iterutils import split_iter, chunked_iter, windowed_iter, unique_iter, first
from boltons.funcutils import FunctionBuilder

from .core import glom, T, STOP, SKIP, _MISSING, Path, TargetRegistry, Call, Spec, S, bbrepr, format_invocation
from .matching import Check

class Iter(object):
    """``Iter()`` is glom's counterpart to Python's built-in :func:`iter()`
    function. Given an iterable target, ``Iter()`` yields the result
    of applying the passed spec to each element of the target, similar
    to the built-in ``[]`` spec, but streaming.

    The following turns a list of strings into integers using Iter(),
    before deduplicating and converting it to a tuple:

    >>> glom(['1', '2', '1', '3'], (Iter(int), set, tuple))
    (1, 2, 3)

    ``Iter()`` also has many useful methods which can be chained to
    compose a stream processing pipeline. The above can also be
    written as:

    >>> glom(['1', '2', '1', '3'], (Iter().map(int).unique(), tuple))
    (1, 2, 3)

    ``Iter()`` also respects glom's :data:`~glom.SKIP` and
    :data:`~glom.STOP` singletons for filtering and breaking
    iteration.

    Args:

       subspec: A subspec to be applied on each element from the iterable.
       sentinel: Keyword-only argument, which, when found in the
         iterable stream, causes the iteration to stop. Same as with the
         built-in :func:`iter`.

    """
    def __init__(self, subspec=T, **kwargs):
        self.subspec = subspec
        self._iter_stack = kwargs.pop('_iter_stack', [])

        self.sentinel = kwargs.pop('sentinel', STOP)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % sorted(kwargs))
        return

    def __repr__(self):
        base_args = ()
        if self.subspec != T:
            base_args = (self.subspec,)
        base = format_invocation(self.__class__.__name__, base_args, repr=bbrepr)
        chunks = [base]
        for fname, args, _ in reversed(self._iter_stack):
            meth = getattr(self, fname)
            fb = FunctionBuilder.from_func(meth)
            fb.args = fb.args[1:]  # drop self
            arg_names = fb.get_arg_names()
            # TODO: something fancier with defaults:
            kwargs = []
            if len(args) > 1 and arg_names:
                args, kwargs = (), zip(arg_names, args)
            chunks.append('.' + format_invocation(fname, args, kwargs, repr=bbrepr))
        return ''.join(chunks)

    def glomit(self, target, scope):
        iterator = self._iterate(target, scope)

        for _, _, callback in reversed(self._iter_stack):
            iterator = callback(iterator, scope)

        return iter(iterator)

    def _iterate(self, target, scope):
        iterate = scope[TargetRegistry].get_handler('iterate', target, path=scope[Path])
        try:
            iterator = iterate(target)
        except Exception as e:
            raise TypeError('failed to iterate on instance of type %r at %r (got %r)'
                            % (target.__class__.__name__, Path(*scope[Path]), e))

        base_path = scope[Path]
        for i, t in enumerate(iterator):
            scope[Path] = base_path + [i]
            yld = (t if self.subspec is T else scope[glom](t, self.subspec, scope))
            if yld is SKIP:
                continue
            elif yld is self.sentinel or yld is STOP:
                # NB: sentinel defaults to STOP so I was torn whether
                # to also check for STOP, and landed on the side of
                # never letting STOP through.
                return
            yield yld
        return

    def _add_op(self, opname, args, callback):
        return type(self)(subspec=self.subspec, _iter_stack=[(opname, args, callback)] + self._iter_stack)

    def map(self, subspec):
        """Return a new :class:`Iter()` spec which will apply the provided
        *subspec* to each element of the iterable.

        >>> glom(range(5), Iter().map(lambda x: x * 2).all())
        [0, 2, 4, 6, 8]

        Because a spec can be a callable, :meth:`Iter.map()` does
        everything the built-in :func:`map` does, but with the full
        power of glom specs.

        >>> glom(['a', 'B', 'C'], Iter().map(T.islower()).all())
        [True, False, False]
        """
        # whatever validation you want goes here
        # TODO: DRY the self._add_op with a decorator?
        return self._add_op(
            'map',
            (subspec,),
            lambda iterable, scope: imap(
                lambda t: scope[glom](t, subspec, scope), iterable))

    def filter(self, key=T):
        """Return a new :class:`Iter()` spec which will include only elements matching the
        given *key*.

        >>> glom(range(6), Iter().filter(lambda x: x % 2).all())
        [1, 3, 5]

        Because a spec can be a callable, :meth:`Iter.filter()` does
        everything the built-in :func:`filter` does, but with the full
        power of glom specs. For even more power, combine,
        :meth:`Iter.filter()` with :class:`Check()`.

        >>> # PROTIP: Python's ints know how many binary digits they require, using the bit_length method
        >>> glom(range(9), Iter().filter(Check(T.bit_length(), one_of=(2, 4), default=SKIP)).all())
        [2, 3, 8]

        """
        # NB: Check's validate function defaults to bool, and
        # *default* is returned on access errors as well validation
        # errors, so the lambda passed to ifilter below works fine.
        check_spec = key if isinstance(key, Check) else Check(key, default=SKIP)
        return self._add_op(
            'filter',
            (key,),
            lambda iterable, scope: ifilter(
                lambda t: scope[glom](t, check_spec, scope) is not SKIP, iterable))

    def chunked(self, size, fill=_MISSING):
        """Return a new :class:`Iter()` spec which groups elements in the iterable
        into lists of length *size*.

        If the optional *fill* argument is provided, iterables not
        evenly divisible by *size* will be padded out by the *fill*
        constant. Otherwise, the final chunk will be shorter than *size*.

        >>> list(glom(range(10), Iter().chunked(3)))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        >>> list(glom(range(10), Iter().chunked(3, fill=None)))
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, None, None]]
        """
        kw = {'size': size}
        args = size,
        if fill is not _MISSING:
            kw['fill'] = fill
            args += (fill,)
        return self._add_op(
            'chunked', args, lambda it, scope: chunked_iter(it, **kw))

    def windowed(self, size):
        """Return a new :class:`Iter()` spec which will yield a sliding window of
        adjacent elements in the iterable. Each tuple yielded will be
        of length *size*.

        Useful for getting adjacent pairs and triples.

        >>> list(glom(range(4), Iter().windowed(2)))
        [(0, 1), (1, 2), (2, 3)]
        """
        return self._add_op(
            'windowed', (size,), lambda it, scope: windowed_iter(it, size))

    def split(self, sep=None, maxsplit=None):
        """Return a new :class:`Iter()` spec which will lazily split an iterable based
        on a separator (or list of separators), *sep*. Like
        :meth:`str.split()`, but for all iterables.

        ``split_iter()`` yields lists of non-separator values. A separator will
        never appear in the output.

        >>> target = [1, 2, None, None, 3, None, 4, None]
        >>> list(glom(target, Iter().split()))
        [[1, 2], [3], [4]]

        Note that ``split_iter`` is based on :func:`str.split`, so if
        *sep* is ``None``, ``split()`` **groups** separators. If empty lists
        are desired between two contiguous ``None`` values, simply use
        ``sep=[None]``:

        >>> list(glom(target, Iter().split(sep=[None])))
        [[1, 2], [], [3], [4], []]

        A max number of splits may also be set:

        >>> list(glom(target, Iter().split(maxsplit=2)))
        [[1, 2], [3], [4, None]]

        """
        return self._add_op(
            'split',
            (sep, maxsplit),
            lambda it, scope: split_iter(it, sep=sep, maxsplit=maxsplit))

    def flatten(self):
        """Returns a new :class:`Iter()` instance which combines iterables into a
        single iterable.

        >>> target = [[1, 2], [3, 4], [5]]
        >>> list(glom(target, Iter().flatten()))
        [1, 2, 3, 4, 5]
        """
        return self._add_op(
            'flatten',
            (),
            lambda it, scope: chain.from_iterable(it))

    def unique(self, key=T):
        """Return a new :class:`Iter()` spec which lazily filters out duplicate
        values, i.e., only the first appearance of a value in a stream will
        be yielded.

        >>> target = list('gloMolIcious')
        >>> out = list(glom(target, Iter().unique(T.lower())))
        >>> print(''.join(out))
        gloMIcus
        """
        return self._add_op(
            'unique',
            (key,),
            lambda it, scope: unique_iter(it, key=lambda t: scope[glom](t, key, scope)))


    def slice(self, *args):
        """Returns a new :class:`Iter()` spec which trims iterables in the
        same manner as :func:`itertools.islice`.

        >>> target = [0, 1, 2, 3, 4, 5]
        >>> glom(target, Iter().slice(3).all())
        [0, 1, 2]
        >>> glom(target, Iter().slice(2, 4).all())
        [2, 3]

        This method accepts only positional arguments.
        """
        # TODO: make a kwarg-compatible version of this (islice takes no kwargs)
        # TODO: also support slice syntax Iter()[::]
        try:
            islice([], *args)
        except TypeError:
            raise TypeError('invalid slice arguments: %r' % (args,))
        return self._add_op('slice', args, lambda it, scope: islice(it, *args))

    def limit(self, count):
        """A convenient alias for :meth:`~Iter.slice`, which takes a single
        argument, *count*, the max number of items to yield.
        """
        return self._add_op('limit', (count,), lambda it, scope: islice(it, count))

    def takewhile(self, key=T):
        """Returns a new :class:`Iter()` spec which stops the stream once
        *key* becomes falsy.

        >>> glom([3, 2, 0, 1], Iter().takewhile().all())
        [3, 2]

        :func:`itertools.takewhile` for more details.
        """
        return self._add_op(
            'takewhile',
            (key,),
            lambda it, scope: takewhile(
                lambda t: scope[glom](t, key, scope), it))

    def dropwhile(self, key=T):
        """Returns a new :class:`Iter()` spec which drops stream items until
        *key* becomes falsy.

        >>> glom([0, 0, 3, 2, 0], Iter().dropwhile(lambda t: t < 1).all())
        [3, 2, 0]

        Note that while similar to :meth:`Iter.filter()`, the filter
        only applies to the beginning of the stream. In a way,
        :meth:`Iter.dropwhile` can be thought of as
        :meth:`~str.lstrip()` for streams. See
        :func:`itertools.dropwhile` for more details.

        """

        return self._add_op(
            'dropwhile',
            (key,),
            lambda it, scope: dropwhile(
                lambda t: scope[glom](t, key, scope), it))

    # Terminal methods follow

    def all(self):
        """A convenience method which returns a new spec which turns an
        iterable into a list.

        >>> glom(range(5), Iter(lambda t: t * 2).all())
        [0, 2, 4, 6, 8]

        Note that this spec will always consume the whole iterable, and as
        such, the spec returned is *not* an :class:`Iter()` instance.
        """
        return (self, list)

    def first(self, key=T, default=None):
        """A convenience method for lazily yielding a single truthy item from
        an iterable.

        >>> target = [False, 1, 2, 3]
        >>> glom(target, Iter().first())
        1

        This method takes a condition, *key*, which can also be a
        glomspec, as well as a *default*, in case nothing matches the
        condition.

        As this spec yields at most one item, and not an iterable, the
        spec returned from this method is not an :class:`Iter()` instance.
        """
        return (self, First(key=key, default=default))


class First(object):
    """Get the first element of an iterable which matches *key*, if there
    is one, otherwise return *default* (``None`` if unset).

    >>> is_odd = lambda x: x % 2
    >>> glom([0, 1, 2, 3], First(is_odd))
    1
    >>> glom([0, 2, 4], First(is_odd, default=False))
    False
    """
    # The impl of this ain't pretty and basically just exists for a
    # nicer-looking repr. (Iter(), First()) is the equivalent of doing
    # (Iter().filter(spec), Call(first, args=(T,), kwargs={'default':
    # default}))
    __slots__ = ('_spec', '_default', '_first')

    def __init__(self, key=T, default=None):
        self._spec = key
        self._default = default

        spec_glom = Spec(Call(partial, args=(Spec(self._spec).glom,), kwargs={'scope': S}))
        self._first = Call(first, args=(T,), kwargs={'default': default, 'key': spec_glom})

    def glomit(self, target, scope):
        return self._first.glomit(target, scope)

    def __repr__(self):
        cn = self.__class__.__name__
        if self._default is None:
            return '%s(%s)' % (cn, bbrepr(self._spec))
        return '%s(%s, default=%s)' % (cn, bbrepr(self._spec), bbrepr(self._default))
