"""like jq, but with the full power of python in the spec.

Usage: python -m glom [FLAGS] [spec [target]]

Command-line interface to the glom library, providing nested data
access and data restructuring with the power of Python.


Flags:

  --help / -h                 show this help message and exit
  --target-file TARGET_FILE   path to target data source (optional)
  --target-format TARGET_FORMAT
                              format of the source data (json or python)
                              (defaults to 'json')
  --spec-file SPEC_FILE       path to glom spec definition (optional)
  --spec-format SPEC_FORMAT   format of the glom spec definition (json, python,
                              python-full) (defaults to 'python')
  --indent INDENT             number of spaces to indent the result, 0 to disable
                              pretty-printing (defaults to 2)
  --debug                     interactively debug any errors that come up
  --inspect                   interactively explore the data

try out:
`
curl -s https://api.github.com/repos/mahmoud/glom/events | python -m glom '[{"type": "type", "date": "created_at", "user": "actor.login"}]'

"""


from __future__ import print_function

import os
import ast
import sys
import json

from face import (Command,
                  Flag,
                  face_middleware,
                  PosArgSpec,
                  PosArgDisplay,
                  CommandLineError,
                  UsageError)
from face.utils import isatty

import glom
from glom import Path, GlomError, Inspect

PY3 = (sys.version_info[0] == 3)

def glom_cli(target, spec, indent, debug, inspect):
    """Command-line interface to the glom library, providing nested data
    access and data restructuring with the power of Python.
    """
    if debug or inspect:
        stdin_open = not sys.stdin.closed
        spec = Inspect(spec,
                       echo=inspect,
                       recursive=inspect,
                       breakpoint=inspect and stdin_open,
                       post_mortem=debug and stdin_open)

    try:
        result = glom.glom(target, spec)
    except GlomError as ge:
        print('%s: %s' % (ge.__class__.__name__, ge))
        return 1

    if not indent:
        indent = None
    print(json.dumps(result, indent=indent, sort_keys=True))
    return


def get_command():
    posargs = PosArgSpec(str, max_count=2, display={'label': '[spec [target]]'})
    cmd = Command(glom_cli, posargs=posargs, middlewares=[mw_get_target])
    cmd.add('--target-file', str, missing=None, doc='path to target data source')
    cmd.add('--target-format', str, missing='json',
            doc='format of the source data (json or python)')
    cmd.add('--spec-file', str, missing=None, doc='path to glom spec definition')
    cmd.add('--spec-format', str, missing='python',
            doc='format of the glom spec definition (json, python, python-full)')

    cmd.add('--indent', int, missing=2,
            doc='number of spaces to indent the result, 0 to disable pretty-printing')

    cmd.add('--debug', parse_as=True, doc='interactively debug any errors that come up')
    cmd.add('--inspect', parse_as=True, doc='interactively explore the data')
    return cmd


def main(argv):
    cmd = get_command()
    return cmd.run(argv) or 0


def console_main():
    _enable_debug = os.getenv('GLOM_CLI_DEBUG')
    if _enable_debug:
        print(sys.argv)
    try:
        sys.exit(main(sys.argv) or 0)
    except Exception:
        if _enable_debug:
            import pdb;pdb.post_mortem()
        raise


def mw_handle_target(target_text, target_format):
    """ Handles reading in a file specified in cli command.

    Args:
        target_text (str): String that specifies where 6
        target_format (str): Valid formats include `.json` and `.yml` or `.yaml`
    Returns:
        The content of the file that you specified
    Raises:
        CommandLineError: Issue with file format or appropriate file reading package not installed.
    """
    if not target_text:
        return {}
    target = {}
    if target_format == 'json':
        load_func = json.loads
    elif target_format in ('yaml', 'yml'):
        try:
            import yaml
            load_func = yaml.load
        except ImportError:
            raise UsageError('No YAML package found. To process yaml files, run: pip install PyYAML')
    elif target_format == 'python':
        load_func = ast.literal_eval
    else:
        raise UsageError('expected target-format to be one of python, json, or yaml')


    try:
        target = load_func(target_text)
    except Exception as e:
        raise UsageError('could not load target data, got: %s: %s'
                         % (e.__class__.__name__, e))


    return target


@face_middleware(provides=['spec', 'target'])
def mw_get_target(next_, posargs_, target_file, target_format, spec_file, spec_format):
    spec_text, target_text = None, None
    if len(posargs_) == 2:
        spec_text, target_text = posargs_
    elif len(posargs_) == 1:
        spec_text, target_text = posargs_[0], None

    if spec_text and spec_file:
        raise UsageError('expected spec file or spec argument, not both')
    elif spec_file:
        try:
            with open(spec_file, 'r') as f:
                spec_text = f.read()
        except IOError as ose:
            raise UsageError('could not read spec file %r, got: %s' % (spec_file, ose))

    if not spec_text:
        spec = Path()
    elif spec_format == 'python':
        if spec_text[0] not in ('"', "'", "[", "{", "("):
            # intention: handle trivial path access, assume string
            spec_text = repr(spec_text)
        spec = ast.literal_eval(spec_text)
    elif spec_format == 'json':
        spec = json.loads(spec_text)
    elif spec_format == 'python-full':
        spec = _eval_python_full_spec(spec_text)
    else:
        raise UsageError('expected spec-format to be one of json, python, or python-full')

    if target_text and target_file:
        raise UsageError('expected target file or target argument, not both')
    elif target_text == '-' or target_file == '-':
        target_text = sys.stdin.read()
    elif target_file:
        try:
            target_text = open(target_file, 'r').read()
        except IOError as ose:
            raise UsageError('could not read target file %r, got: %s' % (target_file, ose))
    elif not target_text and not isatty(sys.stdin):
        target_text = sys.stdin.read()

    target = mw_handle_target(target_text, target_format)

    return next_(spec=spec, target=target)


def _from_glom_import_star():
    ret = dict(glom.__dict__)
    for k in ('__builtins__', '__name__', '__doc__', '__package__'):
        ret.pop(k, None)
    for k, v in list(ret.items()):
        if type(v) == type(glom):
            ret.pop(k)
    return ret


def _eval_python_full_spec(py_text):
    name = '__cli_glom_spec__'
    code_str = '%s = %s' % (name, py_text)
    env = _from_glom_import_star()
    spec = _compile_code(code_str, name=name, env=env)
    return spec


def _compile_code(code_str, name, env=None, verbose=False):
    code = compile(code_str, '<glom-generated code>', 'single')
    if verbose:
        print(code_str)
    if env is None:
        env = {}
    if PY3:
        exec(code, env)
    else:
        exec("exec code in env")

    return env[name]
