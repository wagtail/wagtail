
import time

import pytest

from face import face_middleware, Command, Flag


def test_mw_basic_sig():
    @face_middleware(provides='time')
    def time_mw(next_):
        return next_(time=time.time())

    with pytest.raises(TypeError):
        face_middleware(bad_kwarg=True)


def test_mw_flags():
    with pytest.raises(TypeError):
        @face_middleware(provides='time', flags=['not_valid'])
        def time_mw(next_):
            return next_(time=time.time())

    # TODO: an actual flags test


def test_no_provides():
    @face_middleware
    def time_mw(next_):
        print(time.time())
        return next_()


def test_next_reserved():
    def bad_cmd(next_):
        return

    cmd = Command(bad_cmd)

    with pytest.raises(NameError):
        cmd.run(['bad_cmd'])



def test_mw_unres():
    def unres_cmd(unresolved_arg):
        return unresolved_arg

    cmd = Command(unres_cmd)
    assert cmd.func is unres_cmd

    with pytest.raises(NameError, match="unresolved middleware or handler arguments: .*unresolved_arg.*"):
        cmd.run(['unres_cmd'])

    def inner_mw(next_, arg):
        return next_()

    @face_middleware(provides='arg', flags=[Flag('--verbose', parse_as=True)])
    def outer_mw(next_):
        return next_(arg=1)

    def ok_cmd(arg):
        return None

    cmd = Command(ok_cmd, middlewares=[outer_mw])
    cmd.add_middleware(inner_mw)

    with pytest.raises(NameError, match="unresolved middleware or handler arguments: .*arg.* check middleware order."):
        cmd.run(['ok_cmd'])
    return


def test_check_mw():
    with pytest.raises(TypeError, match='be a function'):
        face_middleware()('not a function')

    with pytest.raises(TypeError, match='take at least one argument'):
        face_middleware()(lambda: None)

    with pytest.raises(TypeError, match='as the first parameter'):
        face_middleware()(lambda bad_first_arg_name: None)

    with pytest.raises(TypeError, match=r'explicitly named arguments, not "\*a'):
        face_middleware()(lambda next_, *a: None)

    with pytest.raises(TypeError, match=r'explicitly named arguments, not "\*\*kw'):
        face_middleware()(lambda next_, **kw: None)

    with pytest.raises(TypeError, match='provides conflict with reserved face builtins'):
        face_middleware(provides='flags_')(lambda next_: None)
