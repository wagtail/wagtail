
import operator

import pytest
from boltons.dictutils import OMD

from glom import glom, T, Sum, Fold, Flatten, Coalesce, flatten, FoldError, Glommer, Merge, merge


def test_sum_integers():
    target = list(range(5))

    assert glom(target, Sum()) == 10

    assert glom(target, Sum(init=lambda: 2)) == 12

    target = []
    assert glom(target, Sum()) == 0


    target = [{"num": 3}, {"num": 2}, {"num": -1}]
    assert glom(target, Sum(['num'])) == 4

    target = target + [{}]  # add a non-compliant dict
    assert glom(target, Sum([Coalesce('num', default=0)])) ==4

    assert repr(Sum()) == 'Sum()'
    assert repr(Sum(len, init=float)) == 'Sum(len, init=float)'


def test_sum_seqs():
    target = [(x,) for x in range(4)]
    assert glom(target, Sum(init=tuple)) == (0, 1, 2, 3)

    # would not work with builtin sum(), gets:
    # "TypeError: sum() can't sum strings [use ''.join(seq) instead]"
    # Works here for now. If we're ok with that error, then we can
    # switch to sum().
    target = ['a', 'b', 'cd']
    assert glom(target, Sum(init=str)) == 'abcd'

    target = [['a'], ['b'], ['cde'], ['']]

    assert glom(target, Sum(Sum(init=list), init=str)) == 'abcde'


def test_fold():
    target = range(1, 5)
    assert glom(target, Fold(T, int)) == 10
    assert glom(target, Fold(T, init=lambda: 2)) == 12

    assert glom(target, Fold(T, lambda: 1, op=lambda l, r: l * r)) == 24

    assert repr(Fold(T, int)) == 'Fold(T, init=int)'
    assert repr(Fold(T, int, op=operator.imul)).startswith('Fold(T, init=int, op=<')

    # signature coverage
    with pytest.raises(TypeError):
        Fold(T, list, op=None)  # noncallable op

    with pytest.raises(TypeError):
        Fold(T, init=None)  # noncallable init


def test_fold_bad_iter():
    glommer = Glommer(register_default_types=False)

    def bad_iter(obj):
        raise RuntimeError('oops')

    glommer.register(list, iterate=bad_iter)

    with pytest.raises(TypeError):
        target = []
        glommer.glom(target, Flatten())


def test_flatten():
    target = [[1], [2], [3, 4]]
    assert glom(target, Flatten()) == [1, 2, 3, 4]

    target = [(1, 2), [3]]
    assert glom(target, Flatten()) == [1, 2, 3]

    gen = glom(target, Flatten(init='lazy'))
    assert next(gen) == 1
    assert list(gen) == [2, 3]

    assert repr(Flatten()) == 'Flatten()'
    assert repr(Flatten(init='lazy')) == "Flatten(init='lazy')"
    assert repr(Flatten(init=tuple)) == "Flatten(init=tuple)"


def test_flatten_func():
    target = [[1], [2], [3, 4]]
    assert flatten(target) == [1, 2, 3, 4]

    two_level_target = [[x] for x in target]
    assert flatten(two_level_target, levels=2) == [1, 2, 3, 4]
    assert flatten(two_level_target, levels=0) == two_level_target

    unflattenable = 2

    with pytest.raises(FoldError):
        assert flatten(unflattenable)

    # kind of an odd use, but it works for now
    assert flatten(['a', 'b', 'cd'], init=str) == 'abcd'

    # another odd case
    subspec_target = {'items': {'numbers': [1, 2, 3]}}
    assert (flatten(subspec_target, spec='items.numbers', init=int) == 6)

    # basic signature tests
    with pytest.raises(ValueError):
        flatten([], levels=-1)

    with pytest.raises(TypeError):
        flatten([], nonexistentkwarg=False)

    return


def test_merge():

    target = [{'a': 'A'}, {'b': 'B'}]

    assert glom(target, Merge()) == {'a': 'A', 'b': 'B'}

    assert glom(target, Merge(op=dict.update)) == {'a': 'A', 'b': 'B'}

    with pytest.raises(ValueError):
        Merge(init=list)  # has no .update()

    with pytest.raises(ValueError):
        Merge(op='update_extend')  # doesn't work on base dict, the default init


def test_merge_omd():
    target = [{'a': 'A'}, {'a': 'aleph'}]

    assert glom(target, Merge(init=OMD)) == OMD({'a': 'aleph'})
    assert glom(target, Merge(init=OMD, op='update_extend')) == OMD([('a', 'A'), ('a', 'aleph')])


def test_merge_func():

    target = [{'a': 'A'}, {'b': 'B'}]
    assert merge(target) == {'a': 'A', 'b': 'B'}
    assert merge([]) == {}

    # basic signature test
    with pytest.raises(TypeError):
        merge([], nonexistentkwarg=False)
