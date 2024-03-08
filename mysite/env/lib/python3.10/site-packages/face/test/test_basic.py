# -*- coding: utf-8 -*-

from random import shuffle

import pytest

from face import (Command, Flag, ERROR, FlagDisplay, PosArgSpec,
                  PosArgDisplay, ChoicesParam, CommandLineError,
                  ArgumentParseError, echo, prompt, CommandChecker)
from face.utils import format_flag_label, identifier_to_flag, get_minimal_executable

def test_cmd_name():

    def handler():
        return 0

    Command(handler, name='ok_cmd')

    name_err_map = {'': 'non-zero length string',
                    5: 'non-zero length string',
                    'name_': 'without trailing dashes or underscores',
                    'name--': 'without trailing dashes or underscores',
                    'n?me': ('valid subcommand name must begin with a letter, and'
                             ' consist only of letters, digits, underscores, and'
                             ' dashes')}

    for name, err in name_err_map.items():
        with pytest.raises(ValueError, match=err):
            Command(handler, name=name)

    return


def test_flag_name():
    flag = Flag('ok_name')
    assert repr(flag).startswith('<Flag name=')

    assert format_flag_label(flag) == '--ok-name OK_NAME'
    assert format_flag_label(Flag('name', display={'label': '--nAmE'})) == '--nAmE'
    assert format_flag_label(Flag('name', display='--nAmE')) == '--nAmE'

    assert Flag('name', display='').display.hidden == True
    assert repr(Flag('name', display='').display).startswith('<FlagDisplay')

    with pytest.raises(TypeError, match='or FlagDisplay instance'):
        Flag('name', display=object())

    with pytest.raises(TypeError, match='unexpected keyword arguments'):
        Flag('name', display={'badkw': 'val'})

    with pytest.raises(ValueError, match='expected identifier.*'):
        assert identifier_to_flag('--flag')

    name_err_map = {'': 'non-zero length string',
                    5: 'non-zero length string',
                    'name_': 'without trailing dashes or underscores',
                    'name--': 'without trailing dashes or underscores',
                    'n?me': ('must begin with a letter.*and'
                             ' consist only of letters, digits, underscores, and'
                             ' dashes'),
                    'for': 'valid flag names must not be Python keywords'}

    for name, err in name_err_map.items():
        with pytest.raises(ValueError, match=err):
            Flag(name=name)
    return


def test_flag_char():
    with pytest.raises(ValueError, match='char flags must be exactly one character'):
        Flag('flag', char='FLAG')
    with pytest.raises(ValueError, match='expected valid flag character.*ASCII letters, numbers.*'):
        Flag('flag', char=u'é')

    assert Flag('flag', char='-f').char == 'f'


def test_flag_hidden():
    # TODO: is display='' sufficient for hiding (do we need hidden=True)
    cmd = Command(lambda tiger, dragon: None, 'cmd')
    cmd.add('--tiger', display='')
    flags = cmd.get_flags(with_hidden=False)
    assert 'tiger' not in [f.name for f in flags]

    cmd.add('--dragon', display={'label': ''})
    flags = cmd.get_flags(with_hidden=False)
    assert 'dragon' not in [f.name for f in flags]


def test_command_misc_api():
    with pytest.raises(TypeError, match='unexpected keyword'):
        Command(lambda: None, name='ok', bad_kwarg=True)


def test_flag_init():
    cmd = Command(lambda flag, part: None, name='cmd')

    with pytest.raises(ValueError, match='cannot make an argument-less flag required'):
        cmd.add('--flag', missing=ERROR, parse_as=True)

    # test custom callable multi
    cmd.add(Flag('--part', multi=lambda flag, vals: ''.join(vals)))
    res = cmd.parse(['cmd', '--part', 'a', '--part', 'b'])
    assert res.flags['part'] == 'ab'

    with pytest.raises(ValueError, match='multi expected callable, bool, or one of.*'):
        cmd.add('--badflag', multi='nope')


def test_char_missing_error():
    # testing required flags
    cmd = Command(lambda req_flag: None, name='cmd')
    cmd.add('--req-flag', char='-R', missing=ERROR)
    res = cmd.parse(['cmd', '--req-flag', 'val'])
    assert res.flags['req_flag'] == 'val'

    res = cmd.parse(['cmd', '-R', 'val'])
    assert res.flags['req_flag'] == 'val'

    with pytest.raises(ArgumentParseError, match='--req-flag'):
        cmd.parse(['cmd'])

    return

def test_minimal_exe():
    venv_exe_path = '/home/mahmoud/virtualenvs/face/bin/python'
    res = get_minimal_executable(venv_exe_path,
                                 environ={'PATH': ('/home/mahmoud/virtualenvs/face/bin'
                                                   ':/home/mahmoud/bin:/usr/local/sbin'
                                                   ':/usr/local/bin:/usr/sbin'
                                                   ':/usr/bin:/sbin:/bin:/snap/bin')})
    assert res == 'python'

    res = get_minimal_executable(venv_exe_path,
                                 environ={'PATH': ('/home/mahmoud/bin:/usr/local/sbin'
                                                   ':/usr/local/bin:/usr/sbin'
                                                   ':/usr/bin:/sbin:/bin:/snap/bin')})
    assert res == venv_exe_path

    # TODO: where is PATH not a string?
    res = get_minimal_executable(venv_exe_path, environ={'PATH': []})
    assert res == venv_exe_path


def test_posargspec_init():
    with pytest.raises(TypeError, match='expected callable or ERROR'):
        PosArgSpec(parse_as=object())
    with pytest.raises(TypeError, match='unexpected keyword'):
        PosArgSpec(badkw='val')

    with pytest.raises(ValueError, match='expected min_count >= 0'):
        PosArgSpec(min_count=-1)

    with pytest.raises(ValueError, match='expected max_count > 0'):
        PosArgSpec(max_count=-1)

    with pytest.raises(ValueError, match='expected min_count > max_count'):
        PosArgSpec(max_count=3, min_count=4)

    with pytest.raises(TypeError, match='.*PosArgDisplay instance.*'):
        PosArgSpec(display=object())
    with pytest.raises(TypeError, match='unexpected keyword'):
        PosArgSpec(display={'badkw': 'val'})

    # cmd = Command(lambda posargs_: posargs_, posargs=PosArgSpec(display=False))
    assert PosArgSpec(display=False).display.hidden == True
    assert PosArgSpec(display=PosArgDisplay(name='posargs'))

    cmd = Command(lambda: None, name='cmd', posargs=1)
    assert cmd.posargs.min_count == 1
    assert cmd.posargs.max_count == 1

    cmd = Command(lambda targs: None, name='cmd', posargs='targs')
    assert cmd.posargs.display.name == 'targs'
    assert cmd.posargs.provides == 'targs'

    cmd = Command(lambda targs: None, name='cmd', posargs=int)
    assert cmd.posargs.parse_as == int

    with pytest.raises(TypeError, match='.*instance of PosArgSpec.*'):
        Command(lambda targs: None, name='cmd', posargs=object())

    return


def test_bad_posargspec():
    # issue #11
    assert PosArgSpec(name=None).display.name is not None
    assert PosArgDisplay(name=None).name is not None

    posargs_args = [
        {'name': None},
        {'provides': 'x'},
        {'display': {'doc': 'wee'}},
        {'display': {'name': 'better_name'}}
    ]

    for arg in posargs_args:
        cmd = Command(lambda targs: None, name='cmd', posargs=arg)
        cmd_chk = CommandChecker(cmd, mix_stderr=True)
        res = cmd_chk.run(['cmd', '-h'])
        assert res.stdout.startswith('Usage')

    return


def test_bad_subprs():
    with pytest.raises(ValueError,
                       match='commands accepting positional arguments cannot take subcommands'):
        posarg_cmd = Command(lambda: None, 'pa', posargs=True)
        posarg_cmd.add(lambda: None, 'bad_subcmd')

    cmd = Command(lambda: None, 'base')
    cmd.add(lambda: None, 'twin')
    with pytest.raises(ValueError, match='conflicting subcommand name'):
        cmd.add(lambda: None, 'twin')

    with pytest.raises(TypeError, match='expected Command instance'):
        cmd.add_command(object())


def test_choices_init():
    with pytest.raises(ValueError, match='expected at least one'):
        ChoicesParam(choices=[])

    class Unsortable(object):
        def __gt__(self, other):
            raise TypeError()
        __cmp__ = __lt__ = __gt__

    choices = [Unsortable() for _ in range(100)]
    choices_param = ChoicesParam(choices=choices)
    assert choices == choices_param.choices
    assert choices is not choices_param.choices


def test_echo(capsys):
    test_str = u'tést'
    echo(test_str)
    echo.err(test_str.upper())
    captured = capsys.readouterr()
    assert captured.out == test_str + '\n'
    assert captured.err == test_str.upper() + '\n'

    echo(test_str, end='\n\n')
    assert capsys.readouterr().out == test_str + '\n\n'
    echo(test_str, nl=False)
    assert capsys.readouterr().out == test_str


def test_multi_extend():
    cmd = Command(lambda override: None, name='cmd')
    cmd.add('--override', char='o', multi=True)
    res = cmd.parse(['cmd', '-o', 'x=y', '-o', 'a=b'])

    assert res.flags['override'] == ['x=y', 'a=b']

    res = cmd.parse(['cmd'])
    assert res.flags['override'] == []

    res = cmd.parse(['cmd', '-o=x'])
    assert res.flags['override'] == ['x']
    

def test_post_posargs():
    cmd = Command(lambda posargs, post_posargs: None, name='cmd')

    res = cmd.parse(['cmd'])
    assert res.posargs == ()
    assert res.post_posargs == None  
    # TODO: if this ^ isn't a useful signal, it would be more convenient to have the 
    # behavior be the same as below

    res = cmd.parse(['cmd', '--'])
    assert res.posargs == ()
    assert res.post_posargs == ()
