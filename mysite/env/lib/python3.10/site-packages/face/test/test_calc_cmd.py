
from __future__ import print_function

import os
import getpass

import pytest

from face import (Command,
                  Parser,
                  PosArgSpec,
                  ArgumentParseError,
                  CommandLineError,
                  CommandChecker,
                  CheckError,
                  prompt)


def get_calc_cmd(as_parser=False):
    cmd = Command(None, 'calc')

    cmd.add(_add_cmd, name='add', posargs={'min_count': 2, 'parse_as': float})
    cmd.add(_add_two_ints, name='add_two_ints', posargs={'count': 2, 'parse_as': int, 'provides': 'ints'})
    cmd.add(_is_odd, name='is_odd', posargs={'count': 1, 'parse_as': int, 'provides': 'target_int'})
    cmd.add(_ask_halve, name='halve', posargs=False)
    cmd.add(_ask_blackjack, name='blackjack')

    if as_parser:
        cmd.__class__ = Parser

    return cmd


def _add_cmd(posargs_):
    "add numbers together"
    assert posargs_
    ret = sum(posargs_)
    print(ret)
    return ret


def _add_two_ints(ints):
    assert ints
    ret = sum(ints)
    # TODO: stderr
    return ret


def _ask_halve():
    val = float(prompt('Enter a number: '))
    print()
    ret = val / float(os.getenv('CALC_TWO', 2))
    print(ret)
    return ret


def _is_odd(target_int):
    return bool(target_int % 2)


def _ask_blackjack():
    bottom = int(prompt.secret('Bottom card: ', confirm=True))
    top = int(prompt('Top card: '))
    total = top + bottom
    if total > 21:
        res = 'bust'
    elif total == 21:
        res = 'blackjack!'
    else:
        res = 'hit (if you feel lucky)'
    print(res)
    return


def test_calc_basic():
    prs = cmd = get_calc_cmd()

    res = prs.parse(['calc', 'add', '1.1', '2.2'])
    assert res

    with pytest.raises(ArgumentParseError):
        prs.parse(['calc', 'add-two-ints', 'not', 'numbers'])
    with pytest.raises(ArgumentParseError):
        prs.parse(['calc', 'add-two-ints', '1', '2', '3'])
    with pytest.raises(ArgumentParseError):
        prs.parse(['calc', 'add-two-ints', '1'])

    res = cmd.run(['calc', 'add-two-ints', '1', '2'])
    assert res == 3

    cmd.run(['calc', 'add-two-ints', '-h'])

    with pytest.raises(TypeError):
        prs.parse(['calc', 'is-odd', 3])  # fails bc 3 isn't a str

    res = cmd.run(['calc', 'is-odd', '3'])
    assert res == True
    res = cmd.run(['calc', 'is-odd', '4'])
    assert res == False


def test_calc_stream():
    cmd = get_calc_cmd()

    tc = CommandChecker(cmd, reraise=True)

    res = tc.run(['calc', 'add', '1', '2'])

    assert res.stdout.strip() == '3.0'

    res = tc.run(['calc', 'halve'], input='30')
    assert res.stdout.strip() == 'Enter a number: \n15.0'

    res = tc.run('calc halve', input='4', env={'CALC_TWO': '-2'})
    assert res.stdout.strip() == 'Enter a number: \n-2.0'
    assert not res.exception

    with pytest.raises(ZeroDivisionError):
        tc.run('calc halve', input='4', env={'CALC_TWO': '0'})

    return


def test_cc_exc():
    cmd = get_calc_cmd()
    cc_no_reraise = CommandChecker(cmd)
    res = cc_no_reraise.fail('calc halve', input='4', env={'CALC_TWO': '0'})
    assert res.exception
    assert res.stdout == 'Enter a number: \n'

    res = cc_no_reraise.fail('calc halve nonexistentarg')
    assert type(res.exception) is CommandLineError

    # NB: expect to update these as error messaging improves
    assert str(res.exception) == "error: calc halve: unexpected positional arguments: ['nonexistentarg']"
    assert res.stderr.startswith("error: calc halve: unexpected positional arguments: ['nonexistentarg']")
    assert 'stderr=' in repr(res)

    with pytest.raises(TypeError):
        cc_no_reraise.run('calc halve', input=object())
    return


def test_cc_mixed(tmpdir):
    cmd = get_calc_cmd()
    cc_mixed = CommandChecker(cmd, mix_stderr=True)
    res = cc_mixed.fail_1('calc halve nonexistentarg', chdir=tmpdir)
    assert type(res.exception) is CommandLineError
    assert res.stdout.startswith("error: calc halve: unexpected positional arguments: ['nonexistentarg']")
    assert repr(res)

    with pytest.raises(ValueError):
        res.stderr

    return


def test_cc_getpass():
    cmd = get_calc_cmd()
    cc = CommandChecker(cmd, mix_stderr=True)
    res = cc.run('calc blackjack', input=['20', '20', '1'])
    assert res.stdout.endswith('blackjack!\n')

    # check newline-autoadding behavior when getpass is aborted
    cc = CommandChecker(cmd)
    def _raise_eof(*a, **kw):
        raise EOFError()

    real_getpass = getpass.getpass
    try:
        getpass.getpass = _raise_eof
        res = cc.fail('calc blackjack')
    finally:
        getpass.getpass = real_getpass
    assert res.stderr.endswith('\n')


def test_cc_edge_cases():
    cmd = get_calc_cmd()
    cc = CommandChecker(cmd)

    with pytest.raises(AttributeError):
        cc.nonexistentattr
    with pytest.raises(AttributeError, match='end in integers'):
        cc.fail_x

    with pytest.raises(TypeError, match='Container of ints'):
        cc.run('calc blackjack', exit_code=object())

    # disable automatic checking
    res = cc.run('calc blackjack', input=['20', '20', '1'], exit_code=None)
    assert res.exit_code == 0
    assert res.stderr == 'Bottom card: Retype bottom card: '

    # CheckError is also an AssertionError
    with pytest.raises(AssertionError) as exc_info:
        cc.run('calc halve nonexistentarg', input='tldr')
    assert exc_info.value.result.stderr.startswith('error: calc halve: unexpected')

    with pytest.raises(CheckError):
        cc.fail('calc halve', input='4')

    with pytest.raises(CheckError):
        cc.fail('calc halve', input='4', exit_code=(1, 2))
