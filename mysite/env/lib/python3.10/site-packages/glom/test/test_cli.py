# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import subprocess

import pytest
from face import CommandChecker, CommandLineError

from glom import cli


BASIC_TARGET = '{"a": {"b": "c"}}'
BASIC_SPEC = '{"a": "a.b"}'
BASIC_OUT = '{"a": "c"}\n'

@pytest.fixture
def cc():
    cmd = cli.get_command()
    # TODO: don't mix stderr
    return CommandChecker(cmd, mix_stderr=True)

@pytest.fixture
def basic_spec_path(tmp_path):
    spec_path = str(tmp_path) + '/basic_spec.txt'
    with open(spec_path, 'w') as f:
        f.write(BASIC_SPEC)
    return spec_path

@pytest.fixture
def basic_target_path(tmp_path):
    target_path = str(tmp_path) + '/basic_target.txt'
    with open(target_path, 'w') as f:
        f.write(BASIC_TARGET)
    return target_path


def test_cli_blank(cc):
    res = cc.run(['glom'])
    res.stdout == '{}'


def test_cli_spec_target_argv_basic(cc):
    res = cc.run(['glom', '--indent', '0', BASIC_SPEC, BASIC_TARGET])
    assert res.stdout == BASIC_OUT

    # json format, too
    res = cc.run(['glom', '--indent', '0', '--spec-format', 'json', BASIC_SPEC, BASIC_TARGET])
    assert res.stdout == BASIC_OUT


def test_cli_spec_argv_target_stdin_basic(cc):
    res = cc.run(['glom', '--indent', '0', BASIC_SPEC],
                 input=BASIC_TARGET)
    assert res.stdout == BASIC_OUT

    res = cc.run(['glom', '--indent', '0', BASIC_SPEC, '-'],
                 input=BASIC_TARGET)
    assert res.stdout == BASIC_OUT

    res = cc.run(['glom', '--indent', '0', '--target-file', '-', BASIC_SPEC],
                 input=BASIC_TARGET)
    assert res.stdout == BASIC_OUT


def test_cli_spec_target_files_basic(cc, basic_spec_path, basic_target_path):
    res = cc.run(['glom', '--indent', '0', '--target-file',
                  basic_target_path, '--spec-file', basic_spec_path])
    assert res.stdout == BASIC_OUT


def test_usage_errors(cc, basic_spec_path, basic_target_path):
    # bad target json
    res = cc.fail_1(['glom', BASIC_SPEC, '{' + BASIC_TARGET])
    assert 'could not load target data' in res.stdout  # TODO: stderr

    # bad target yaml
    res = cc.fail_1(['glom', '--target-format', 'yaml', BASIC_SPEC, '{' + BASIC_TARGET])
    assert 'could not load target data' in res.stdout  # TODO: stderr

    # TODO: bad target python?

    # bad target format  TODO: fail_2
    res = cc.fail_1(['glom', '--target-format', 'lol', BASIC_SPEC, BASIC_TARGET])
    assert 'target-format to be one of' in res.stdout  # TODO: stderr

    # bad spec format  TODO: fail_2
    res = cc.fail_1(['glom', '--spec-format', 'lol', BASIC_SPEC, BASIC_TARGET])
    assert 'spec-format to be one of' in res.stdout  # TODO: stderr

    # test conflicting spec file and spec posarg
    res = cc.fail_1(['glom', '--spec-file', basic_spec_path, BASIC_SPEC, BASIC_TARGET])
    assert 'spec' in res.stdout
    assert 'not both' in res.stdout  # TODO: stderr

    # test conflicting target file and target posarg
    res = cc.fail_1(['glom', '--target-file', basic_target_path, BASIC_SPEC, BASIC_TARGET])
    assert 'target' in res.stdout
    assert 'not both' in res.stdout  # TODO: stderr


    # TODO: if spec-file is present, maybe single posarg should become target?
    res = cc.fail_1(['glom', '--spec-file', basic_spec_path + 'abra', '--target-file', basic_target_path])
    assert 'could not read spec file' in res.stdout  # TODO: stderr

    res = cc.fail_1(['glom', '--spec-file', basic_spec_path, '--target-file', basic_target_path + 'abra'])
    assert 'could not read target file' in res.stdout  # TODO: stderr


def test_main_basic():
    argv = ['__', 'a.b.fail', '{"a": {"b": "c"}}']
    assert cli.main(argv) == 1

    argv = ['__', 'a.b.c', '{"a": {"b": {"c": "d"}}}']
    assert cli.main(argv) == 0


def test_main_yaml_target():
    cwd = os.path.dirname(os.path.abspath(__file__))
    # Handles the filepath if running tox
    if '.tox' in cwd:
        cwd = os.path.join(cwd.split('.tox')[0] + '/glom/test/')
    path = os.path.join(cwd, 'data/test_valid.yaml')
    argv = ['__', '--target-file', path, '--target-format', 'yml', 'Hello']
    assert cli.main(argv) == 0

    path = os.path.join(cwd, 'data/test_invalid.yaml')
    argv = ['__', '--target-file', path, '--target-format', 'yml', 'Hello']
    # Makes sure correct improper yaml exception is raised
    with pytest.raises(CommandLineError) as excinfo:
        cli.main(argv)
    assert 'expected <block end>, but found' in str(excinfo.value)


def test_main_python_full_spec_python_target():
    argv = ['__', '--target-format', 'python', '--spec-format', 'python-full', 'T[T[3].bit_length()]', '{1: 2, 2: 3, 3: 4}']
    assert cli.main(argv) == 0

    argv = ['__', '--target-format', 'python', '--spec-format', 'python-full', '(T.values(), [T])', '{1: 2, 2: 3, 3: 4}']
    assert cli.main(argv) == 0


def test_main(tmp_path):
    # TODO: pytest-cov knows how to make coverage work across
    # subprocess boundaries...
    os.chdir(str(tmp_path))
    res = subprocess.check_output(['glom', 'a', '{"a": 3}'])
    assert res.decode('utf8') in ('3\n', '3\r\n')  # unix or windows line end okay
