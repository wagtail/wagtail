
import pytest

from itertools import count, dropwhile, chain

from glom import Iter
from glom import glom, SKIP, STOP, T, Call, Spec, Glommer, Check, SKIP


RANGE_5 = list(range(5))


def test_iter():
    assert list(glom(['1', '2', '3'], Iter(int))) == [1, 2, 3]
    cnt = count()
    cnt_1 = glom(cnt, Iter(lambda t: t + 1))
    assert (next(cnt_1), next(cnt_1)) == (1, 2)
    assert next(cnt) == 2

    assert list(glom(['1', '2', '3'], (Iter(int), enumerate))) == [(0, 1), (1, 2), (2, 3)]

    assert list(glom([1, SKIP, 2], Iter())) == [1, 2]
    assert list(glom([1, STOP, 2], Iter())) == [1]

    with pytest.raises(TypeError):
        Iter(nonexistent_kwarg=True)


def test_filter():
    is_odd = lambda x: x % 2
    odd_spec = Iter().filter(is_odd)
    out = glom(RANGE_5, odd_spec)
    assert list(out) == [1, 3]

    # let's just make sure we're actually streaming just in case
    counter = count()
    out = glom(counter, odd_spec)
    assert next(out) == 1
    assert next(out) == 3
    assert next(counter) == 4
    assert next(counter) == 5
    assert next(out) == 7

    bools = [True, False, False, True, False]
    spec = Iter().filter().all()
    out = glom(bools, spec)
    assert out == [True, True]

    imags = [0j, 1j, 2, 2j, 3j]
    spec = Iter().filter(Check(T.imag.real, type=float, one_of=(0, 2), default=SKIP)).all()
    out = glom(imags, spec)
    assert out == [0j, 2j]

    assert repr(Iter().filter(T.a.b)) == 'Iter().filter(T.a.b)'
    assert repr(Iter(list).filter(sum)) == 'Iter(list).filter(sum)'


def test_map():
    spec = Iter().map(lambda x: x * 2)
    out = glom(RANGE_5, spec)
    assert list(out) == [0, 2, 4, 6, 8]
    assert repr(Iter().map(T.a.b)) == 'Iter().map(T.a.b)'


def test_split_flatten():
    falsey_stream = [1, None, None, 2, 3, None, 4]
    spec = Iter().split()
    out = glom(falsey_stream, spec)
    assert list(out) == [[1], [2, 3], [4]]

    spec = Iter().split().flatten()
    out = glom(falsey_stream, spec)
    assert list(out) == [1, 2, 3, 4]

    assert repr(Iter().split(sep=None, maxsplit=2)) == 'Iter().split(sep=None, maxsplit=2)'
    assert repr(Iter(T.a.b[1]).flatten()) == 'Iter(T.a.b[1]).flatten()'


def test_chunked():
    int_list = list(range(9))

    spec = Iter().chunked(3)
    out = glom(int_list, spec)
    assert list(out) == [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

    spec = Iter().chunked(3).map(sum)
    out = glom(int_list, spec)
    assert list(out) == [3, 12, 21]


def test_windowed():
    int_list = list(range(5))

    spec = Iter().windowed(3)
    out = glom(int_list, spec)
    assert list(out) == [(0, 1, 2), (1, 2, 3), (2, 3, 4)]
    assert repr(spec) == 'Iter().windowed(3)'

    spec = spec.filter(lambda x: bool(x[0] % 2)).map(sum)
    out = glom(int_list, spec)
    assert next(out) == 6

    out = glom(range(10), spec)
    assert list(out) == [6, 12, 18, 24]


def test_unique():
    int_list = list(range(10))

    spec = Iter().unique()
    out = glom(int_list, spec)
    assert list(out) == int_list

    spec = Iter(lambda x: x % 4).unique()
    out = glom(int_list, spec)
    assert list(out) == int_list[:4]
    assert repr(Iter().unique(T.a)) == 'Iter().unique(T.a)'


def test_slice():
    cnt = count()

    spec = Iter().slice(3)
    out = glom(cnt, spec)

    assert list(out) == [0, 1, 2]
    assert next(cnt) == 3

    out = glom(range(10), Iter().slice(1, 5))
    assert list(out) == [1, 2, 3, 4]

    out = glom(range(10), Iter().slice(1, 6, 2))
    assert list(out) == [1, 3, 5]
    assert repr(Iter().slice(1, 6, 2)) == 'Iter().slice(1, 6, 2)'

    out = glom(range(10), Iter().limit(3))
    assert list(out) == [0, 1, 2]
    assert repr(Iter().limit(3)) == 'Iter().limit(3)'

    out = glom(range(5), Iter().limit(10))
    assert list(out) == [0, 1, 2, 3, 4]

    # test broken args
    with pytest.raises(TypeError):
        Iter().slice(1, 2, 3, 4)


def test_while():
    cnt = count()
    out = glom(cnt, Iter().takewhile(lambda x: x < 3))
    assert list(out) == [0, 1, 2]
    assert next(cnt) == 4
    assert repr(Iter().takewhile(T.a) == 'Iter().takewhile(T.a)')

    range_iter = iter(range(7))
    out = glom(range_iter, Iter().dropwhile(lambda x: x < 3 or x > 5))
    assert list(out) == [3, 4, 5, 6]  # 6 still here despite the x>5 above

    out = glom(range(10), Iter().dropwhile(lambda x: x >= 0).limit(10))
    assert list(out) == []

    out = glom(range(8), Iter().dropwhile((T.bit_length(), lambda x: x < 3)))
    assert list(out) == [4, 5, 6, 7]
    assert repr(Iter().dropwhile(T.a) == 'Iter().dropwhile(T.a)')


def test_iter_composition():
    int_list = list(range(10))
    out = glom(int_list, (Iter(), Iter(), list))
    assert out == int_list

    out = glom([int_list] * 3, Iter(Iter(lambda x: x % 4)).flatten().unique())
    assert list(out) == [0, 1, 2, 3]


def test_faulty_iterate():
    glommer = Glommer()

    def bad_iter(obj):
        raise RuntimeError('oops')

    glommer.register(str, iterate=bad_iter)

    with pytest.raises(TypeError):
        glommer.glom('abc', (Iter(), list))


def test_first():
    spec = Iter().first(T.imag)

    target = iter([1, 2, 3j, 4])
    out = glom(target, spec)
    assert out == 3j
    assert next(target) == 4
    assert repr(spec) == '(Iter(), First(T.imag))'

    spec = Iter().first(T.imag, default=0)
    target = iter([1, 2, 4])
    out = glom(target, spec)
    assert out == 0
    assert repr(spec) == '(Iter(), First(T.imag, default=0))'


def test_all():
    int_iter = iter(range(10))

    out = glom(int_iter, Iter().all())
    assert out == list(range(10))
    assert next(int_iter, None) is None
    assert repr(Iter().all()) == repr((Iter(), list))
