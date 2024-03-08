
import os
import re
import sys
import getpass
import keyword

from boltons.strutils import pluralize, strip_ansi
from boltons.iterutils import split, unique
from boltons.typeutils import make_sentinel

import face

try:
    unicode
except NameError:
    unicode = str
    raw_input = input

ERROR = make_sentinel('ERROR')  # used for parse_as=ERROR

# keep it just to subset of valid ASCII python identifiers for now
VALID_FLAG_RE = re.compile(r"^[A-z][-_A-z0-9]*\Z")

FRIENDLY_TYPE_NAMES = {int: 'integer',
                       float: 'decimal'}


def process_command_name(name):
    """Validate and canonicalize a Command's name, generally on
    construction or at subcommand addition. Like
    ``flag_to_identifier()``, only letters, numbers, '-', and/or
    '_'. Must begin with a letter, and no trailing underscores or
    dashes.

    Python keywords are allowed, as subcommands are never used as
    attributes or variables in injection.

    """

    if not name or not isinstance(name, (str, unicode)):
        raise ValueError('expected non-zero length string for subcommand name, not: %r' % name)

    if name.endswith('-') or name.endswith('_'):
        raise ValueError('expected subcommand name without trailing dashes'
                         ' or underscores, not: %r' % name)

    name_match = VALID_FLAG_RE.match(name)
    if not name_match:
        raise ValueError('valid subcommand name must begin with a letter, and'
                         ' consist only of letters, digits, underscores, and'
                         ' dashes, not: %r' % name)

    subcmd_name = normalize_flag_name(name)

    return subcmd_name


def normalize_flag_name(flag):
    ret = flag.lstrip('-')
    if (len(flag) - len(ret)) > 1:
        # only single-character flags are considered case-sensitive (like an initial)
        ret = ret.lower()
    ret = ret.replace('-', '_')
    return ret


def flag_to_identifier(flag):
    """Validate and canonicalize a flag name to a valid Python identifier
    (variable name).

    Valid input strings include only letters, numbers, '-', and/or
    '_'. Only single/double leading dash allowed (-/--). No trailing
    dashes or underscores. Must not be a Python keyword.

    Input case doesn't matter, output case will always be lower.
    """
    orig_flag = flag
    if not flag or not isinstance(flag, (str, unicode)):
        raise ValueError('expected non-zero length string for flag, not: %r' % flag)

    if flag.endswith('-') or flag.endswith('_'):
        raise ValueError('expected flag without trailing dashes'
                         ' or underscores, not: %r' % orig_flag)

    if flag[:2] == '--':
        flag = flag[2:]

    flag_match = VALID_FLAG_RE.match(flag)
    if not flag_match:
        raise ValueError('valid flag names must begin with a letter, optionally'
                         ' prefixed by two dashes, and consist only of letters,'
                         ' digits, underscores, and dashes, not: %r' % orig_flag)

    flag_name = normalize_flag_name(flag)

    if keyword.iskeyword(flag_name):
        raise ValueError('valid flag names must not be Python keywords: %r'
                         % orig_flag)

    return flag_name


def identifier_to_flag(identifier):
    """
    Turn an identifier back into its flag format (e.g., "Flag" -> --flag).
    """
    if identifier.startswith('-'):
        raise ValueError('expected identifier, not flag name: %r' % identifier)
    ret = identifier.lower().replace('_', '-')
    return '--' + ret


def format_flag_label(flag):
    "The default flag label formatter, used in help and error formatting"
    if flag.display.label is not None:
        return flag.display.label
    parts = [identifier_to_flag(flag.name)]
    if flag.char:
        parts.append('-' + flag.char)
    ret = ' / '.join(parts)
    if flag.display.value_name:
        ret += ' ' + flag.display.value_name
    return ret


def format_posargs_label(posargspec):
    "The default positional argument label formatter, used in help formatting"
    if posargspec.display.label:
        return posargspec.display.label
    if not posargspec.accepts_args:
        return ''
    return get_cardinalized_args_label(posargspec.display.name, posargspec.min_count, posargspec.max_count)


def get_cardinalized_args_label(name, min_count, max_count):
    '''
    Examples for parameter values: (min_count, max_count): output for name=arg:

      1, 1: arg
      0, 1: [arg]
      0, None: [args ...]
      1, 3: args ...
    '''
    if min_count == max_count:
        return ' '.join([name] * min_count)
    if min_count == 1:
        return name + ' ' + get_cardinalized_args_label(name,
                                                        min_count=0,
                                                        max_count=max_count - 1 if max_count is not None else None)

    tmpl = '[%s]' if min_count == 0 else '%s'
    if max_count == 1:
        return tmpl % name
    return tmpl % (pluralize(name) + ' ...')


def format_flag_post_doc(flag):
    "The default positional argument label formatter, used in help formatting"
    if flag.display.post_doc is not None:
        return flag.display.post_doc
    if flag.missing is face.ERROR:
        return '(required)'
    if flag.missing is None or repr(flag.missing) == object.__repr__(flag.missing):
        # avoid displaying unhelpful defaults
        return ''
    return '(defaults to %r)' % (flag.missing,)


def get_type_desc(parse_as):
    "Kind of a hacky way to improve message readability around argument types"
    if not callable(parse_as):
        raise TypeError('expected parse_as to be callable, not %r' % parse_as)
    try:
        return 'as', FRIENDLY_TYPE_NAMES[parse_as]
    except KeyError:
        pass
    try:
        # return the type name if it looks like a type
        return 'as', parse_as.__name__
    except AttributeError:
        pass
    try:
        # return the func name if it looks like a function
        return 'with', parse_as.func_name
    except AttributeError:
        pass
    # if all else fails
    return 'with', repr(parse_as)


def unwrap_text(text):
    """Turn wrapped text into flowing paragraphs, ready for rewrapping by
    the console, browser, or textwrap.
    """
    all_grafs = []
    cur_graf = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            cur_graf.append(line)
        else:
            all_grafs.append(' '.join(cur_graf))
            cur_graf = []
    if cur_graf:
        all_grafs.append(' '.join(cur_graf))
    return '\n\n'.join(all_grafs)


def get_rdep_map(dep_map):
    """
    expects and returns a dict of {item: set([deps])}

    item can be a string or any other hashable object.
    """
    # TODO: the way this is used, this function doesn't receive
    # information about what functions take what args. this ends up
    # just being args depending on args, with no mediating middleware
    # names. this can make circular dependencies harder to debug.
    ret = {}
    for key in dep_map:
        to_proc, rdeps, cur_chain = [key], set(), []
        while to_proc:
            cur = to_proc.pop()
            cur_chain.append(cur)

            cur_rdeps = dep_map.get(cur, [])

            if key in cur_rdeps:
                raise ValueError('dependency cycle: %r recursively depends'
                                 ' on itself. full dep chain: %r' % (cur, cur_chain))

            to_proc.extend([c for c in cur_rdeps if c not in to_proc])
            rdeps.update(cur_rdeps)

        ret[key] = rdeps
    return ret


def get_minimal_executable(executable=None, path=None, environ=None):
    """Get the shortest form of a path to an executable,
    based on the state of the process environment.

    Args:
      executable (str): Name or path of an executable
      path (list): List of directories on the "PATH", or ':'-separated
        path list, similar to the $PATH env var. Defaults to ``environ['PATH']``.
      environ (dict): Mapping of environment variables, will be used
        to retrieve *path* if it is None. Ignored if *path* is
        set. Defaults to ``os.environ``.

    Used by face's default help renderer for a more readable usage string.
    """
    executable = sys.executable if executable is None else executable
    environ = os.environ if environ is None else environ
    path = environ.get('PATH', '') if path is None else path
    if isinstance(path, (str, unicode)):
        path = path.split(':')

    executable_basename = os.path.basename(executable)
    for p in path:
        if os.path.relpath(executable, p) == executable_basename:
            return executable_basename
        # TODO: support "../python" as a return?
    return executable


# prompt and echo owe a decent amount of design to click (and
# pocket_protector)
def isatty(stream):
    "Returns True if *stream* is a tty"
    try:
        return stream.isatty()
    except Exception:
        return False


def should_strip_ansi(stream):
    "Returns True when ANSI color codes should be stripped from output to *stream*."
    return not isatty(stream)


def echo(msg, **kw):
    """A better-behaved :func:`print()` function for command-line applications.

    Writes text or bytes to a file or stream and flushes. Seamlessly
    handles stripping ANSI color codes when the output file is not a
    TTY.

      >>> echo('test')
      test

    Args:

      msg (str): A text or byte string to echo.
      err (bool): Set the default output file to ``sys.stderr``
      file (file): Stream or other file-like object to output
        to. Defaults to ``sys.stdout``, or ``sys.stderr`` if *err* is
        True.
      nl (bool): If ``True``, sets *end* to ``'\\n'``, the newline character.
      end (str): Explicitly set the line-ending character. Setting this overrides *nl*.
      color (bool): Set to ``True``/``False`` to always/never echo ANSI color
        codes. Defaults to inspecting whether *file* is a TTY.

    """
    msg = msg or ''
    if not isinstance(msg, (unicode, bytes)):
        msg = unicode(msg)
    is_err = kw.pop('err', False)
    _file = kw.pop('file', sys.stdout if not is_err else sys.stderr)
    end = kw.pop('end', None)
    enable_color = kw.pop('color', None)

    if enable_color is None:
        enable_color = not should_strip_ansi(_file)

    if end is None:
        if kw.pop('nl', True):
            end = u'\n' if isinstance(msg, unicode) else b'\n'
    if end:
        msg += end

    if msg:
        if not enable_color:
            msg = strip_ansi(msg)
        _file.write(msg)

    _file.flush()

    return


def echo_err(*a, **kw):
    """
    A convenience function which works exactly like :func:`echo`, but
    always defaults the output *file* to ``sys.stderr``.
    """
    kw['err'] = True
    return echo(*a, **kw)


# variant-style shortcut to help minimize kwarg noise and imports
echo.err = echo_err


def _get_text(inp):
    if not isinstance(inp, unicode):
        return inp.decode('utf8')
    return inp


def prompt(label, confirm=None, confirm_label=None, hide_input=False, err=False):
    """A better-behaved :func:`input()` function for command-line applications.

    Ask a user for input, confirming if necessary, returns a text
    string. Handles Ctrl-C and EOF more gracefully than Python's built-ins.

    Args:

       label (str): The prompt to display to the user.
       confirm (bool): Pass ``True`` to ask the user to retype the input to confirm it.
         Defaults to False, unless *confirm_label* is passed.
       confirm_label (str): Override the confirmation prompt. Defaults
         to "Retype *label*" if *confirm* is ``True``.
       hide_input (bool): If ``True``, disables echoing the user's
         input as they type. Useful for passwords and other secret
         entry. See :func:`prompt_secret` for a more convenient
         interface. Defaults to ``False``.
       err (bool): If ``True``, prompts are printed on
         ``sys.stderr``. Defaults to ``False``.

    :func:`prompt` is primarily intended for simple plaintext
    entry. See :func:`prompt_secret` for handling passwords and other
    secret user input.

    Raises :exc:`UsageError` if *confirm* is enabled and inputs do not match.

    """
    do_confirm = confirm or confirm_label
    if do_confirm and not confirm_label:
        confirm_label = 'Retype %s' % (label.lower(),)

    def prompt_func(label):
        func = getpass.getpass if hide_input else raw_input
        try:
            # Write the prompt separately so that we get nice
            # coloring through colorama on Windows (someday)
            echo(label, nl=False, err=err)
            ret = func('')
        except (KeyboardInterrupt, EOFError):
            # getpass doesn't print a newline if the user aborts input with ^C.
            # Allegedly this behavior is inherited from getpass(3).
            # A doc bug has been filed at https://bugs.python.org/issue24711
            if hide_input:
                echo(None, err=err)
            raise

        return ret

    ret = prompt_func(label)
    ret = _get_text(ret)
    if do_confirm:
        ret2 = prompt_func(confirm_label)
        ret2 = _get_text(ret2)
        if ret != ret2:
            raise face.UsageError('Sorry, inputs did not match.')

    return ret


def prompt_secret(label, **kw):
    """A convenience function around :func:`prompt`, which is
    preconfigured for secret user input, like passwords.

    All arguments are the same, except *hide_input* is always
    ``True``, and *err* defaults to ``True``, for consistency with
    :func:`getpass.getpass`.

    """
    kw['hide_input'] = True
    kw.setdefault('err', True)  # getpass usually puts prompts on stderr
    return prompt(label, **kw)


# variant-style shortcut to help minimize kwarg noise and imports
prompt.secret = prompt_secret
