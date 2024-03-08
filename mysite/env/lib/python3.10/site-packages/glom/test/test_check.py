
from pytest import raises

from glom import glom, Check, CheckError, Coalesce, SKIP, STOP, T

try:
    unicode
except NameError:
    unicode = str


def test_check_basic():
    assert glom([0, SKIP], [T]) == [0]  # sanity check SKIP

    target = [{'id': 0}, {'id': 1}, {'id': 2}]

    # check that skipping non-passing values works
    assert glom(target, ([Coalesce(Check('id', equal_to=0), default=SKIP)], T[0])) == {'id': 0}
    assert glom(target, ([Check('id', equal_to=0, default=SKIP)], T[0])) == {'id': 0}

    # check that stopping iteration on non-passing values works
    assert glom(target, [Check('id', equal_to=0, default=STOP)]) == [{'id': 0}]

    # check that stopping chain execution on non-passing values works
    spec = (Check(validate=lambda x: len(x) > 0, default=STOP), T[0])
    assert glom('hello', spec) == 'h'
    assert glom('', spec) == ''  # would fail with IndexError if STOP didn't work

    assert repr(Check()) == 'Check()'
    assert repr(Check(T.a)) == 'Check(T.a)'
    assert repr(Check(equal_to=1)) == 'Check(equal_to=1)'
    assert repr(Check(instance_of=dict)) == 'Check(instance_of=dict)'
    assert repr(Check(T(len), validate=sum)) == 'Check(T(len), validate=sum)'

    target = [1, u'a']
    assert glom(target, [Check(type=unicode, default=SKIP)]) == ['a']
    assert glom(target, [Check(type=(unicode, int))]) == [1, 'a']
    assert glom(target, [Check(instance_of=unicode, default=SKIP)]) == ['a']
    assert glom(target, [Check(instance_of=(unicode, int))]) == [1, 'a']

    target = ['1']
    assert glom(target, [Check(validate=(int, float))])
    assert glom(target, [Check()])  # bare check does a truthy check

    failing_checks = [({'a': {'b': 1}}, {'a': ('a', 'b', Check(type=str))},
                       '''target at path ['a', 'b'] failed check, got error: "expected type to be 'str', found type 'int'"'''),
                      ({'a': {'b': 1}}, {'a': ('a', Check('b', type=str))},
                       '''target at path ['a'] failed check, subtarget at 'b' got error: "expected type to be 'str', found type 'int'"'''),
                      (1, Check(type=(unicode, bool))),
                      (1, Check(instance_of=unicode)),
                      (1, Check(instance_of=(unicode, bool))),
                      (1, Check(equal_to=0)),
                      (1, Check(one_of=(0,))),
                      (1, Check(one_of=(0, 2))),
                      ('-3.14', Check(validate=int)),
                      ('', Check(validate=lambda x: False)),]

    for fc in failing_checks:
        if len(fc) == 2:
            target, check = fc
            msg = None
        else:
            target, check, msg = fc

        with raises(CheckError) as exc_info:
            glom(target, check)

        if msg is not None:
            assert str(exc_info.value).find(msg) != -1
        assert repr(exc_info.value)


def test_check_multi():
    target = 1
    with raises(CheckError) as exc_info:
        glom(target, Check(instance_of=float, validate=lambda x: x > 3.14))

    assert "2 errors" in str(exc_info.value)



def test_check_signature():
    with raises(ValueError):
        Check(instance_of=())
    with raises(ValueError):
        Check(type=())

    with raises(TypeError):
        Check(fake_kwarg=True)

    with raises(ValueError):
        Check(one_of=1)
    with raises(ValueError):
        Check(one_of=())
    with raises(TypeError):
        Check(one_of=(1, 2), equal_to=3)

    with raises(ValueError):
        Check(validate='bad, not callable, value')
