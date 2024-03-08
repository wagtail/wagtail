
import pytest

from face import (Command,
                  Parser,
                  PosArgSpec,
                  ArgumentParseError)


def get_vcs_cmd(as_parser=False):
    cmd = Command(None, 'vcs')

    cmd.add(_add_cmd, name='add', posargs={'min_count': 1}, post_posargs=True)
    cmd.add(_checkout_cmd, name='checkout', posargs={'max_count': 1})

    if as_parser:
        cmd.__class__ = Parser

    return cmd


def _add_cmd(posargs_):
    "add files to the vcs"
    assert posargs_
    return

def _checkout_cmd(posargs_, post_posargs_):
    "checkout a branch or files"
    assert posargs_ or post_posargs_
    return


def test_vcs_basic():
    prs = get_vcs_cmd(as_parser=True)

    with pytest.raises(ArgumentParseError):
        prs.parse(['vcs', 'add'])

    res = prs.parse(['vcs', 'add', 'myfile.txt'])
    assert res

    res = prs.parse(['vcs', 'checkout', 'trunk'])
    assert res
