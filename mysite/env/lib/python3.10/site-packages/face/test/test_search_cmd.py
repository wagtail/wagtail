
import os
import sys
import datetime
# from StringIO import StringIO

from pytest import raises

from face import (Command,
                  Parser,
                  Flag,
                  ERROR,
                  ListParam,
                  face_middleware,
                  ArgumentParseError,
                  InvalidFlagArgument,
                  DuplicateFlag,
                  CommandLineError,
                  InvalidSubcommand,
                  UnknownFlag,
                  UsageError,
                  ChoicesParam)

CUR_PATH = os.path.dirname(os.path.abspath(__file__))


def _rg(glob, max_count):
    "Great stuff from the regrep"
    print('regrepping', glob, max_count)
    return


def _ls(file_paths):
    print(file_paths)
    for fp in file_paths:
        if '*' in fp:
            raise UsageError('no wildcards, ya hear?')
    return file_paths


@face_middleware(provides=['timestamp'])
def _timestamp_mw(next_):
    return next_(timestamp=datetime.datetime.now())


def get_search_command(as_parser=False):
    """A command which provides various subcommands mimicking popular
    command-line text search tools to test power, compatiblity, and
    flexibility.

    """
    cmd = Command(None, 'search')
    cmd.add('--verbose', char='-V', parse_as=True)

    strat_flag = Flag('--strategy', multi='override', missing='fast')
    rg_subcmd = Command(_rg, 'rg', flags=[strat_flag])
    rg_subcmd.add('--glob', char='-g', multi=True, parse_as=str,
                   doc='Include or exclude files/directories for searching'
                   ' that match the given glob. Precede with ! to exclude.')
    rg_subcmd.add('--max-count', char='-m', parse_as=int,
                  doc='Limit the number of matching lines per file.')
    rg_subcmd.add('--filetype', ChoicesParam(['py', 'js', 'html']))
    rg_subcmd.add('--extensions', ListParam(strip=True))

    cmd.add(rg_subcmd)

    ls_subcmd = Command(_ls, 'ls',
                        posargs={'display': 'file_path', 'provides': 'file_paths'},
                        post_posargs={'provides': 'diff_paths'})
    cmd.add(ls_subcmd)

    class TwoFour(object):
        def __call__(self, posargs_):
            return ', '.join(posargs_)

    cmd.add(TwoFour(), posargs=dict(min_count=2, max_count=4))

    cmd.add(_timestamp_mw)

    if as_parser:
        cmd.__class__ = Parser

    return cmd


def test_search_prs_basic():
    prs = get_search_command(as_parser=True)
    assert repr(prs).startswith('<Parser')

    res = prs.parse(['search', '--verbose'])
    assert repr(res).startswith('<CommandParseResult')
    assert res.name == 'search'
    assert res.flags['verbose'] is True

    assert prs.parse(['/search_pkg/__main__.py']).to_cmd_scope()['cmd_'] == 'python -m search_pkg'

    res = prs.parse(['search', 'rg', '--glob', '*.py', '-g', '*.md', '--max-count', '5'])
    assert res.subcmds == ('rg',)
    assert res.flags['glob'] == ['*.py', '*.md']

    res = prs.parse(['search', 'rg', '--extensions', 'py,html,css'])
    assert res.flags['extensions'] == ['py', 'html', 'css']

    res = prs.parse(['search', 'rg', '--strategy', 'fast', '--strategy', 'slow'])
    assert res.flags['strategy'] == 'slow'


def test_prs_sys_argv():
    prs = get_search_command(as_parser=True)
    old_argv = sys.argv
    try:
        sys.argv = ['search', 'ls', 'a', 'b', 'c']
        res = prs.parse(argv=None)
        scope = res.to_cmd_scope()
        assert scope['file_paths'] == ('a', 'b', 'c')
    finally:
        sys.argv = old_argv


def test_post_posargs():
    prs = get_search_command(as_parser=True)

    res = prs.parse(['search', 'ls', 'path1', '--', 'diff_path1', 'diff_path2'])

    scope = res.to_cmd_scope()
    assert scope['file_paths'] == ('path1',)
    assert scope['diff_paths'] == ('diff_path1', 'diff_path2')


def test_search_prs_errors():
    prs = get_search_command(as_parser=True)

    with raises(ValueError, match='expected Parser, Flag, or Flag parameters'):
        prs.add('bad_arg', name='bad_kwarg')

    with raises(ValueError, match='conflicts with name of new flag'):
        prs.add('verbose')

    with raises(ValueError, match='conflicts with short form for new flag'):
        prs.add('--verbosity', char='V')

    with raises(UnknownFlag):
        prs.parse(['search', 'rg', '--unknown-flag'])

    with raises(ArgumentParseError):
        prs.parse(['splorch', 'splarch'])

    with raises(InvalidFlagArgument):
        prs.parse(['search', 'rg', '--max-count', 'not-an-int'])

    with raises(InvalidFlagArgument):
        prs.parse(['search', 'rg', '--max-count', '--glob', '*'])  # max-count should have an arg but doesn't

    with raises(InvalidFlagArgument):
        prs.parse(['search', 'rg', '--max-count'])  # gets a slightly different error message than above

    with raises(DuplicateFlag):
        prs.parse(['search', 'rg', '--max-count', '4', '--max-count', '5'])

    with raises(InvalidSubcommand):
        prs.parse(['search', 'nonexistent-subcommand'])

    with raises(ArgumentParseError):
        prs.parse(['search', 'rg', '--filetype', 'c'])

    with raises(DuplicateFlag, match="was used multiple times"):
        # TODO: is this really so bad?
        prs.parse(['search', '--verbose', '--verbose'])

    with raises(ArgumentParseError, match='expected non-empty') as exc_info:
        prs.parse(argv=[])
    assert exc_info.value.prs_res.to_cmd_scope()['cmd_'] == 'search'

    with raises(ArgumentParseError, match='2 - 4 arguments'):
        prs.parse(argv=['search', 'two-four', '1', '2', '3', '4', '5'])

    prs.add('--req-flag', missing=ERROR)
    with raises(ArgumentParseError, match='missing required'):
        prs.parse(argv=['search', 'rg', '--filetype', 'py'])

    return


def test_search_flagfile():
    prs = get_search_command(as_parser=True)

    with raises(ArgumentParseError):
        prs.parse(['search', 'rg', '--flagfile', '_nonexistent_flagfile'])

    flagfile_path = CUR_PATH + '/_search_cmd_a.flags'

    res = prs.parse(['search', 'rg', '--flagfile', flagfile_path])

    cmd = Command(lambda: None, name='cmd', flagfile=False)
    assert cmd.flagfile_flag is None

    # check that flagfile being passed False causes the flag to error
    with raises(ArgumentParseError):
        cmd.parse(['cmd', '--flagfile', 'doesnt_have_to_exist'])

    cmd = Command(lambda: None, name='cmd', flagfile=Flag('--flags'))
    assert cmd.flagfile_flag.name == 'flags'

    with open(flagfile_path) as f:
        flagfile_text = f.read()

    # does this even make sense as a case?
    # flagfile_strio = StringIO(flagfile_text)

    with raises(TypeError, match='Flag instance for flagfile'):
        Command(lambda: None, name='cmd', flagfile=object())


def test_search_cmd_basic(capsys):
    cmd = get_search_command()

    cmd.run(['search', 'rg', '--glob', '*', '-m', '10'])

    out, err = capsys.readouterr()
    assert 'regrepping' in out

    with raises(SystemExit) as exc_info:
        cmd.run(['search', 'rg', 'badposarg'])
    out, err = capsys.readouterr()
    assert 'error:' in err

    with raises(CommandLineError):
        cmd.run(['search', 'rg', '--no-such-flag'])
    out, err = capsys.readouterr()
    assert 'error: search rg: unknown flag "--no-such-flag",' in err

    cmd.run(['search', 'rg', '-h', 'badposarg'])
    out, err = capsys.readouterr()
    assert '[FLAGS]' in out  # help printed bc flag

    cmd.prepare()  # prepares all paths/subcmds


def test_search_help(capsys):
    # pdb won't work in here bc of the captured stdout/err
    cmd = get_search_command()

    cmd.run(['search', '-h'])

    out, err = capsys.readouterr()
    assert '[FLAGS]' in out
    assert '--help' in out
    assert 'show this help message and exit' in out


def test_search_ls(capsys):
    cmd = get_search_command()

    res = cmd.run(['search', 'ls', 'a', 'b'])

    assert res == ('a', 'b')

    cmd.run(['search', 'ls', '-h'])

    out, err = capsys.readouterr()
    assert 'file_paths' in out


def test_usage_error(capsys):
    cmd = get_search_command()

    with raises(UsageError, match='no wildcards'):
        cmd.run(['search', 'ls', '*'])

    out, err = capsys.readouterr()
    assert 'no wildcards' in err
