
import sys
import shlex
import codecs
import os.path
from collections import OrderedDict

from boltons.iterutils import split, unique
from boltons.dictutils import OrderedMultiDict as OMD
from boltons.funcutils import format_exp_repr, format_nonexp_repr

from face.utils import (ERROR,
                        get_type_desc,
                        flag_to_identifier,
                        normalize_flag_name,
                        process_command_name,
                        get_minimal_executable)
from face.errors import (FaceException,
                         ArgumentParseError,
                         ArgumentArityError,
                         InvalidSubcommand,
                         UnknownFlag,
                         DuplicateFlag,
                         InvalidFlagArgument,
                         InvalidPositionalArgument,
                         MissingRequiredFlags)

try:
    unicode
except NameError:
    unicode = str


def _arg_to_subcmd(arg):
    return arg.lower().replace('-', '_')


def _multi_error(flag, arg_val_list):
    "Raise a DuplicateFlag if more than one value is specified for an argument"
    if len(arg_val_list) > 1:
        raise DuplicateFlag.from_parse(flag, arg_val_list)
    return arg_val_list[0]


def _multi_extend(flag, arg_val_list):
    "Return a list of all arguments specified for a flag"
    ret = [v for v in arg_val_list if v is not flag.missing]
    return ret


def _multi_override(flag, arg_val_list):
    "Return only the last argument specified for a flag"
    return arg_val_list[-1]

# TODO: _multi_ignore?

_MULTI_SHORTCUTS = {'error': _multi_error,
                    False: _multi_error,
                    'extend': _multi_extend,
                    True: _multi_extend,
                    'override': _multi_override}


_VALID_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!*+./?@_'
def _validate_char(char):
    orig_char = char
    if char[0] == '-' and len(char) > 1:
        char = char[1:]
    if len(char) > 1:
        raise ValueError('char flags must be exactly one character, optionally'
                         ' prefixed by a dash, not: %r' % orig_char)
    if char not in _VALID_CHARS:
        raise ValueError('expected valid flag character (ASCII letters, numbers,'
                         ' or shell-compatible punctuation), not: %r' % orig_char)
    return char


def _posargs_to_provides(posargspec, posargs):
    '''Automatically unwrap injectable posargs into a more intuitive
    format, similar to an API a human might design. For instance, a
    function which takes exactly one argument would not take a list of
    exactly one argument.

    Cases as follows:

    1. min_count > 1 or max_count > 1, pass through posargs as a list
    2. max_count == 1 -> single argument or None

    Even if min_count == 1, you can get a None back. This compromise
    was made necessary to keep "to_cmd_scope" robust enough to pass to
    help/error handler funcs when validation fails.
    '''
    # all of the following assumes a valid posargspec, with min_count
    # <= max_count, etc.
    pas = posargspec
    if pas.max_count is None or pas.min_count > 1 or pas.max_count > 1:
        return posargs
    if pas.max_count == 1:
        # None is considered sufficiently unambiguous, even for cases when pas.min_count==1
        return posargs[0] if posargs else None
    raise RuntimeError('invalid posargspec/posargs configuration %r -- %r'
                       % (posargspec, posargs))  # pragma: no cover (shouldn't get here)


class CommandParseResult(object):
    """The result of :meth:`Parser.parse`, instances of this type
    semantically store all that a command line can contain. Each
    argument corresponds 1:1 with an attribute.

    Args:
       name (str): Top-level program name, typically the first
          argument on the command line, i.e., ``sys.argv[0]``.
       subcmds (tuple): Sequence of subcommand names.
       flags (OrderedDict): Mapping of canonical flag names to matched values.
       posargs (tuple): Sequence of parsed positional arguments.
       post_posargs (tuple): Sequence of parsed post-positional
          arguments (args following ``--``)
       parser (Parser): The Parser instance that parsed this
          result. Defaults to None.
       argv (tuple): The sequence of strings parsed by the Parser to
          yield this result. Defaults to ``()``.

    Instances of this class can be injected by accepting the "args_"
    builtin in their Command handler function.

    """
    def __init__(self, parser, argv=()):
        self.parser = parser
        self.argv = tuple(argv)

        self.name = None  # str
        self.subcmds = None  # tuple
        self.flags = None  # OrderedDict
        self.posargs = None  # tuple
        self.post_posargs = None  # tuple

    def to_cmd_scope(self):
        "returns a dict which can be used as kwargs in an inject call"
        _subparser = self.parser.subprs_map[self.subcmds] if self.subcmds else self.parser

        if not self.argv:
            cmd_ = self.parser.name
        else:
            cmd_ = self.argv[0]
            path, basename = os.path.split(cmd_)
            if basename == '__main__.py':
                pkg_name = os.path.basename(path)
                executable_path = get_minimal_executable()
                cmd_ = '%s -m %s' % (executable_path, pkg_name)

        ret = {'args_': self,
               'cmd_': cmd_,
               'subcmds_': self.subcmds,
               'flags_': self.flags,
               'posargs_': self.posargs,
               'post_posargs_': self.post_posargs,
               'subcommand_': _subparser,
               'command_': self.parser}
        if self.flags:
            ret.update(self.flags)

        prs = self.parser if not self.subcmds else self.parser.subprs_map[self.subcmds]
        if prs.posargs.provides:
            posargs_provides = _posargs_to_provides(prs.posargs, self.posargs)
            ret[prs.posargs.provides] = posargs_provides
        if prs.post_posargs.provides:
            posargs_provides = _posargs_to_provides(prs.posargs, self.post_posargs)
            ret[prs.post_posargs.provides] = posargs_provides

        return ret

    def __repr__(self):
        return format_nonexp_repr(self, ['name', 'argv', 'parser'])


# TODO: allow name="--flag / -F" and do the split for automatic
# char form?
class Flag(object):
    """The Flag object represents all there is to know about a resource
    that can be parsed from argv and consumed by a Command
    function. It also references a FlagDisplay, used by HelpHandlers
    to control formatting of the flag during --help output

    Args:
       name (str): A string name for the flag, starting with a letter,
          and consisting of only ASCII letters, numbers, '-', and '_'.
       parse_as: How to interpret the flag. If *parse_as* is a
         callable, it will be called with the argument to the flag,
         the return value of which is stored in the parse result. If
         *parse_as* is not a callable, then the flag takes no
         argument, and the presence of the flag will produce this
         value in the parse result. Defaults to ``str``, meaning a
         default flag will take one string argument.
       missing: How to interpret the absence of the flag. Can be any
         value, which will be in the parse result when the flag is not
         present. Can also be the special value ``face.ERROR``, which
         will make the flag required. Defaults to ``None``.
       multi (str): How to handle multiple instances of the same
         flag. Pass 'overwrite' to accept the last flag's value. Pass
         'extend' to collect all values into a list. Pass 'error' to
         get the default behavior, which raises a DuplicateFlag
         exception. *multi* can also take a callable, which accepts a
         list of flag values and returns the value to be stored in the
         :class:`CommandParseResult`.
       char (str): A single-character short form for the flag. Can be
         user-friendly for commonly-used flags. Defaults to ``None``.
       doc (str): A summary of the flag's behavior, used in automatic
         help generation.
       display: Controls how the flag is displayed in automatic help
         generation. Pass False to hide the flag, pass a string to
         customize the label, and pass a FlagDisplay instance for full
         customizability.
    """
    def __init__(self, name, parse_as=str, missing=None, multi='error',
                 char=None, doc=None, display=None):
        self.name = flag_to_identifier(name)
        self.doc = doc
        self.parse_as = parse_as
        self.missing = missing
        if missing is ERROR and not callable(parse_as):
            raise ValueError('cannot make an argument-less flag required.'
                             ' expected non-ERROR for missing, or a callable'
                             ' for parse_as, not: %r' % parse_as)
        self.char = _validate_char(char) if char else None

        if callable(multi):
            self.multi = multi
        elif multi in _MULTI_SHORTCUTS:
            self.multi = _MULTI_SHORTCUTS[multi]
        else:
            raise ValueError('multi expected callable, bool, or one of %r, not: %r'
                             % (list(_MULTI_SHORTCUTS.keys()), multi))

        self.set_display(display)

    def set_display(self, display):
        """Controls how the flag is displayed in automatic help
        generation. Pass False to hide the flag, pass a string to
        customize the label, and pass a FlagDisplay instance for full
        customizability.
        """
        if display is None:
            display = {}
        elif isinstance(display, bool):
            display = {'hidden': not display}
        elif isinstance(display, str):
            display = {'label': display}
        if isinstance(display, dict):
            display = FlagDisplay(self, **display)
        if not isinstance(display, FlagDisplay):
            raise TypeError('expected bool, text name, dict of display'
                            ' options, or FlagDisplay instance, not: %r'
                            % display)
        self.display = display

    def __repr__(self):
        return format_nonexp_repr(self, ['name', 'parse_as'], ['missing', 'multi'],
                                  opt_key=lambda v: v not in (None, _multi_error))


class FlagDisplay(object):
    """Provides individual overrides for most of a given flag's display
    settings, as used by HelpFormatter instances attached to Parser
    and Command objects. Pass an instance of this to
    Flag.set_display() for full control of help output.

    FlagDisplay instances are meant to be used 1:1 with Flag
    instances, as they maintain a reference back to their associated
    Flag. They are generally automatically created by a Flag
    constructor, based on the "display" argument.

    Args:
       flag (Flag): The Flag instance to which this FlagDisplay applies.
       label (str): The formatted version of the string used to
         represent the flag in help and error messages. Defaults to
         None, which allows the label to be autogenerated by the
         HelpFormatter.
       post_doc (str): An addendum string added to the Flag's own
         doc. Defaults to a parenthetical describing whether the flag
         takes an argument, and whether the argument is required.
       full_doc (str): A string of the whole flag's doc, overriding
         the doc + post_doc default.
       value_name (str): For flags which take an argument, the string
         to use as the placeholder of the flag argument in help and
         error labels.
       hidden (bool): Pass True to hide this flag in general help and
         error messages. Defaults to False.
       group: An integer or string indicating how this flag should be
         grouped in help messages, improving readability. Integers are
         unnamed groups, strings are for named groups. Defaults to 0.
       sort_key: Flags are sorted in help output, pass an integer or
         string to override the sort order.

    """
    # value_name -> arg_name?
    def __init__(self, flag, **kw):
        self.flag = flag

        self.doc = flag.doc
        if self.doc is None and callable(flag.parse_as):
            _prep, desc = get_type_desc(flag.parse_as)
            self.doc = 'Parsed with ' + desc
            if _prep == 'as':
                self.doc = desc

        self.post_doc = kw.pop('post_doc', None)
        self.full_doc = kw.pop('full_doc', None)

        self.value_name = ''
        if callable(flag.parse_as):
            # TODO: use default when it's set and it's a basic renderable type
            self.value_name = kw.pop('value_name', None) or self.flag.name.upper()

        self.group = kw.pop('group', 0)   # int or str
        self._hide = kw.pop('hidden', False)  # bool
        self.label = kw.pop('label', None)  # see hidden property below for more info
        self.sort_key = kw.pop('sort_key', 0)  # int or str
        # TODO: sort_key is gonna need to be partitioned on type for py3
        # TODO: maybe sort_key should be a counter so that flags sort
        # in the order they are created

        if kw:
            raise TypeError('unexpected keyword arguments: %r' % kw.keys())
        return

    @property
    def hidden(self):
        return self._hide or self.label == ''

    def __repr__(self):
        return format_nonexp_repr(self, ['label', 'doc'], ['group', 'hidden'], opt_key=bool)


class PosArgDisplay(object):
    """Provides individual overrides for PosArgSpec display in automated
    help formatting. Pass to a PosArgSpec constructor, which is in
    turn passed to a Command/Parser.

    Args:
       spec (PosArgSpec): The associated PosArgSpec.
       name (str): The string name of an individual positional
         argument. Automatically pluralized in the label according to
         PosArgSpec values. Defaults to 'arg'.
       label (str): The full display label for positional arguments,
         bypassing the automatic formatting of the *name* parameter.
       doc (str): A summary description of the positional arguments.
       post_doc (str): An informational addendum about the arguments,
         often describes default behavior.

    """
    def __init__(self, **kw):
        self.name = kw.pop('name', None) or 'arg'
        self.doc = kw.pop('doc', '')
        self.post_doc = kw.pop('post_doc', None)
        self._hide = kw.pop('hidden', False)  # bool
        self.label = kw.pop('label', None)

        if kw:
            raise TypeError('unexpected keyword arguments: %r' % kw.keys())
        return

    @property
    def hidden(self):
        return self._hide or self.label == ''

    def __repr__(self):
        return format_nonexp_repr(self, ['name', 'label'])


class PosArgSpec(object):
    """Passed to Command/Parser as posargs and post_posargs parameters to
    configure the number and type of positional arguments.

    Args:
       parse_as (callable): A function to call on each of the passed
          arguments. Also accepts special argument ERROR, which will raise
          an exception if positional arguments are passed. Defaults to str.
       min_count (int): A minimimum number of positional
          arguments. Defaults to 0.
       max_count (int): A maximum number of positional arguments. Also
          accepts None, meaning no maximum. Defaults to None.
       display: Pass a string to customize the name in help output, or
          False to hide it completely. Also accepts a PosArgDisplay
          instance, or a dict of the respective arguments.
       provides (str): name of an argument to be passed to a receptive
          handler function.
       name (str): A shortcut to set *display* name and *provides*
       count (int): A shortcut to set min_count and max_count to a single value
          when an exact number of arguments should be specified.

    PosArgSpec instances are stateless and safe to be used multiple
    times around the application.

    """
    def __init__(self, parse_as=str, min_count=None, max_count=None, display=None, provides=None, **kwargs):
        if not callable(parse_as) and parse_as is not ERROR:
            raise TypeError('expected callable or ERROR for parse_as, not %r' % parse_as)
        name = kwargs.pop('name', None)
        count = kwargs.pop('count', None)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % list(kwargs.keys()))
        self.parse_as = parse_as

        # count convenience alias
        min_count = count if min_count is None else min_count
        max_count = count if max_count is None else max_count

        self.min_count = int(min_count) if min_count else 0
        self.max_count = int(max_count) if max_count is not None else None

        if self.min_count < 0:
            raise ValueError('expected min_count >= 0, not: %r' % self.min_count)
        if self.max_count is not None and self.max_count <= 0:
            raise ValueError('expected max_count > 0, not: %r' % self.max_count)
        if self.max_count and self.min_count > self.max_count:
            raise ValueError('expected min_count > max_count, not: %r > %r'
                             % (self.min_count, self.max_count))

        provides = name if provides is None else provides
        self.provides = provides

        if display is None:
            display = {}
        elif isinstance(display, bool):
            display = {'hidden': not display}
        elif isinstance(display, str):
            display = {'name': display}
        if isinstance(display, dict):
            display.setdefault('name', name)
            display = PosArgDisplay(**display)
        if not isinstance(display, PosArgDisplay):
            raise TypeError('expected bool, text name, dict of display'
                            ' options, or PosArgDisplay instance, not: %r'
                            % display)

        self.display = display

        # TODO: default? type check that it's a sequence matching min/max reqs

    def __repr__(self):
        return format_nonexp_repr(self, ['parse_as', 'min_count', 'max_count', 'display'])

    @property
    def accepts_args(self):
        """True if this PosArgSpec is configured to accept one or
        more arguments.
        """
        return self.parse_as is not ERROR

    def parse(self, posargs):
        """Parse a list of strings as positional arguments.

        Args:
           posargs (list): List of strings, likely parsed by a Parser
              instance from sys.argv.

        Raises an ArgumentArityError if there are too many or too few
        arguments.

        Raises InvalidPositionalArgument if the argument doesn't match
        the configured *parse_as*. See PosArgSpec for more info.

        Returns a list of arguments, parsed with *parse_as*.
        """
        len_posargs = len(posargs)
        if posargs and not self.accepts_args:
            # TODO: check for likely subcommands
            raise ArgumentArityError('unexpected positional arguments: %r' % posargs)
        min_count, max_count = self.min_count, self.max_count
        if min_count == max_count:
            # min_count must be >0 because max_count cannot be 0
            arg_range_text = '%s argument' % min_count
            if min_count > 1:
                arg_range_text += 's'
        else:
            if min_count == 0:
                arg_range_text = 'up to %s argument' % max_count
                arg_range_text += 's' if (max_count and max_count > 1) else ''
            elif max_count is None:
                arg_range_text = 'at least %s argument' % min_count
                arg_range_text += 's' if min_count > 1 else ''
            else:
                arg_range_text = '%s - %s arguments' % (min_count, max_count)

        if len_posargs < min_count:
            raise ArgumentArityError('too few arguments, expected %s, got %s'
                                     % (arg_range_text, len_posargs))
        if max_count is not None and len_posargs > max_count:
            raise ArgumentArityError('too many arguments, expected %s, got %s'
                                     % (arg_range_text, len_posargs))
        ret = []
        for pa in posargs:
            try:
                val = self.parse_as(pa)
            except Exception as exc:
                raise InvalidPositionalArgument.from_parse(self, pa, exc)
            else:
                ret.append(val)
        return ret


FLAGFILE_ENABLED = Flag('--flagfile', parse_as=str, multi='extend', missing=None, display=False, doc='')


def _ensure_posargspec(posargs, posargs_name):
    if not posargs:
        # take no posargs
        posargs = PosArgSpec(parse_as=ERROR)
    elif posargs is True:
        # take any number of posargs
        posargs = PosArgSpec()
    elif isinstance(posargs, int):
        # take an exact number of posargs
        # (True and False are handled above, so only real nonzero ints get here)
        posargs = PosArgSpec(min_count=posargs, max_count=posargs)
    elif isinstance(posargs, str):
        posargs = PosArgSpec(display=posargs, provides=posargs)
    elif isinstance(posargs, dict):
        posargs = PosArgSpec(**posargs)
    elif callable(posargs):
        # take any number of posargs of a given format
        posargs = PosArgSpec(parse_as=posargs)

    if not isinstance(posargs, PosArgSpec):
        raise TypeError('expected %s as True, False, number of args, text name of args,'
                        ' dict of PosArgSpec options, or instance of PosArgSpec, not: %r'
                        % (posargs_name, posargs))

    return posargs


class Parser(object):
    """The Parser lies at the center of face, primarily providing a
    configurable validation logic on top of the conventional grammar
    for CLI argument parsing.

    Args:
       name (str): A name used to identify this command. Important
          when the command is embedded as a subcommand of another
          command.
       doc (str): An optional summary description of the command, used
          to generate help and usage information.
       flags (list): A list of Flag instances. Optional, as flags can
          be added with :meth:`~Parser.add()`.
       posargs (bool): Defaults to disabled, pass ``True`` to enable
          the Parser to accept positional arguments. Pass a callable
          to parse the positional arguments using that
          function/type. Pass a :class:`PosArgSpec` for full
          customizability.
       post_posargs (bool): Same as *posargs*, but refers to the list
          of arguments following the ``--`` conventional marker. See
          ``git`` and ``tox`` for examples of commands using this
          style of positional argument.
       flagfile (bool): Defaults to enabled, pass ``False`` to disable
          flagfile support. Pass a :class:`Flag` instance to use a
          custom flag instead of ``--flagfile``. Read more about
          Flagfiles below.

    Once initialized, parsing is performed by calling
    :meth:`Parser.parse()` with ``sys.argv`` or any other list of strings.
    """
    def __init__(self, name, doc=None, flags=None, posargs=None,
                 post_posargs=None, flagfile=True):
        self.name = process_command_name(name)
        self.doc = doc
        flags = list(flags or [])

        self.posargs = _ensure_posargspec(posargs, 'posargs')
        self.post_posargs = _ensure_posargspec(post_posargs, 'post_posargs')

        if flagfile is True:
            self.flagfile_flag = FLAGFILE_ENABLED
        elif isinstance(flagfile, Flag):
            self.flagfile_flag = flagfile
        elif not flagfile:
            self.flagfile_flag = None
        else:
            raise TypeError('expected True, False, or Flag instance for'
                            ' flagfile, not: %r' % flagfile)

        self.subprs_map = OrderedDict()
        self._path_flag_map = OrderedDict()
        self._path_flag_map[()] = OrderedDict()

        for flag in flags:
            self.add(flag)
        if self.flagfile_flag:
            self.add(self.flagfile_flag)
        return

    def get_flag_map(self, path, with_hidden=True):
        flag_map = self._path_flag_map[path]
        return OrderedDict([(k, f) for k, f in flag_map.items()
                            if with_hidden or not f.display.hidden])

    def get_flags(self, path=(), with_hidden=True):
        flag_map = self.get_flag_map(path=path, with_hidden=with_hidden)

        return unique(flag_map.values())

    def __repr__(self):
        cn = self.__class__.__name__
        return ('<%s name=%r subcmd_count=%r flag_count=%r posargs=%r>'
                % (cn, self.name, len(self.subprs_map), len(self.get_flags()), self.posargs))

    def _add_subparser(self, subprs):
        """Process subcommand name, check for subcommand conflicts, check for
        subcommand flag conflicts, then finally add subcommand.

        To add a command under a different name, simply make a copy of
        that parser or command with a different name.
        """
        if self.posargs.accepts_args:
            raise ValueError('commands accepting positional arguments'
                             ' cannot take subcommands')

        # validate that the subparser's name can be used as a subcommand
        subprs_name = process_command_name(subprs.name)

        # then, check for conflicts with existing subcommands and flags
        for prs_path in self.subprs_map:
            if prs_path[0] == subprs_name:
                raise ValueError('conflicting subcommand name: %r' % subprs_name)
        parent_flag_map = self._path_flag_map[()]

        check_no_conflicts = lambda parent_flag_map, subcmd_path, subcmd_flags: True
        for path, flags in subprs._path_flag_map.items():
            if not check_no_conflicts(parent_flag_map, path, flags):
                # TODO
                raise ValueError('subcommand flags conflict with parent command: %r' % flags)

        # with checks complete, add parser and all subparsers
        self.subprs_map[(subprs_name,)] = subprs
        for path, cur_subprs in list(subprs.subprs_map.items()):
            new_path = (subprs_name,) + path
            self.subprs_map[new_path] = cur_subprs

        # Flags inherit down (a parent's flags are usable by the child)
        for path, flags in subprs._path_flag_map.items():
            new_flags = parent_flag_map.copy()
            new_flags.update(flags)
            self._path_flag_map[(subprs_name,) + path] = new_flags

        # If two flags have the same name, as long as the "parse_as"
        # is the same, things should be ok. Need to watch for
        # overlapping aliases, too. This may allow subcommands to
        # further document help strings. Should the same be allowed
        # for defaults?

    def add(self, *a, **kw):
        """Add a flag or subparser.

        Unless the first argument is a Parser or Flag object, the
        arguments are the same as the Flag constructor, and will be
        used to create a new Flag instance to be added.

        May raise ValueError if arguments are not recognized as
        Parser, Flag, or Flag parameters. ValueError may also be
        raised on duplicate definitions and other conflicts.
        """
        if isinstance(a[0], Parser):
            subprs = a[0]
            self._add_subparser(subprs)
            return

        if isinstance(a[0], Flag):
            flag = a[0]
        else:
            try:
                flag = Flag(*a, **kw)
            except TypeError as te:
                raise ValueError('expected Parser, Flag, or Flag parameters,'
                                 ' not: %r, %r (got %r)' % (a, kw, te))
        return self._add_flag(flag)

    def _add_flag(self, flag):
        # first check there are no conflicts...
        for subcmds, flag_map in self._path_flag_map.items():
            conflict_flag = flag_map.get(flag.name) or (flag.char and flag_map.get(flag.char))
            if conflict_flag is None:
                continue
            if flag.name in (conflict_flag.name, conflict_flag.char):
                raise ValueError('pre-existing flag %r conflicts with name of new flag %r'
                                 % (conflict_flag, flag.name))
            if flag.char and flag.char in (conflict_flag.name, conflict_flag.char):
                raise ValueError('pre-existing flag %r conflicts with short form for new flag %r'
                                 % (conflict_flag, flag))

        # ... then we add the flags
        for flag_map in self._path_flag_map.values():
            flag_map[flag.name] = flag
            if flag.char:
                flag_map[flag.char] = flag
        return

    def parse(self, argv):
        """This method takes a list of strings and converts them into a
        validated :class:`CommandParseResult` according to the flags,
        subparsers, and other options configured.

        Args:
           argv (list): A required list of strings. Pass ``None`` to
              use ``sys.argv``.

        This method may raise ArgumentParseError (or one of its
        subtypes) if the list of strings fails to parse.

        .. note:: The *argv* parameter does not automatically default
                  to using ``sys.argv`` because it's best practice for
                  implementing codebases to perform that sort of
                  defaulting in their ``main()``, which should accept
                  an ``argv=None`` parameter. This simple step ensures
                  that the Python CLI application has some sort of
                  programmatic interface that doesn't require
                  subprocessing. See here for an example.

        """
        if argv is None:
            argv = sys.argv
        cpr = CommandParseResult(parser=self, argv=argv)
        if not argv:
            ape = ArgumentParseError('expected non-empty sequence of arguments, not: %r' % (argv,))
            ape.prs_res = cpr
            raise ape
        for arg in argv:
            if not isinstance(arg, (str, unicode)):
                raise TypeError('parse expected all args as strings, not: %r (%s)' % (arg, type(arg).__name__))
        '''
        for subprs_path, subprs in self.subprs_map.items():
            if len(subprs_path) == 1:
                # _add_subparser takes care of recurring so we only
                # need direct subparser descendants
                self._add_subparser(subprs, overwrite=True)
        '''
        flag_map = None
        # first snip off the first argument, the command itself
        cmd_name, args = argv[0], list(argv)[1:]
        cpr.name = cmd_name

        # we record our progress as we parse to provide the most
        # up-to-date info possible to the error and help handlers

        try:
            # then figure out the subcommand path
            subcmds, args = self._parse_subcmds(args)
            cpr.subcmds = tuple(subcmds)

            prs = self.subprs_map[tuple(subcmds)] if subcmds else self

            # then look up the subcommand's supported flags
            # NOTE: get_flag_map() is used so that inheritors, like Command,
            # can filter by actually-used arguments, not just
            # available arguments.
            cmd_flag_map = self.get_flag_map(path=tuple(subcmds))

            # parse supported flags and validate their arguments
            flag_map, flagfile_map, posargs = self._parse_flags(cmd_flag_map, args)
            cpr.flags = OrderedDict(flag_map)
            cpr.posargs = tuple(posargs)

            # take care of dupes and check required flags
            resolved_flag_map = self._resolve_flags(cmd_flag_map, flag_map, flagfile_map)
            cpr.flags = OrderedDict(resolved_flag_map)

            # separate out any trailing arguments from normal positional arguments
            post_posargs = None  # TODO: default to empty list?
            parsed_post_posargs = None
            if '--' in posargs:
                posargs, post_posargs = split(posargs, '--', 1)
                cpr.posargs, cpr.post_posargs = posargs, post_posargs

                parsed_post_posargs = prs.post_posargs.parse(post_posargs)
                cpr.post_posargs = tuple(parsed_post_posargs)

            parsed_posargs = prs.posargs.parse(posargs)
            cpr.posargs = tuple(parsed_posargs)
        except ArgumentParseError as ape:
            ape.prs_res = cpr
            raise

        return cpr

    def _parse_subcmds(self, args):
        """Expects arguments after the initial command (i.e., argv[1:])

        Returns a tuple of (list_of_subcmds, remaining_args).

        Raises on unknown subcommands."""
        ret = []

        for arg in args:
            if arg.startswith('-'):
                break  # subcmd parsing complete

            arg = _arg_to_subcmd(arg)
            if tuple(ret + [arg]) not in self.subprs_map:
                prs = self.subprs_map[tuple(ret)] if ret else self
                if prs.posargs.parse_as is not ERROR or not prs.subprs_map:
                    # we actually have posargs from here
                    break
                raise InvalidSubcommand.from_parse(prs, arg)
            ret.append(arg)
        return ret, args[len(ret):]

    def _parse_single_flag(self, cmd_flag_map, args):
        advance = 1
        arg = args[0]
        arg_text = None
        try:
            arg, arg_text = arg.split('=', maxsplit=1)
        except ValueError:
            pass
        flag = cmd_flag_map.get(normalize_flag_name(arg))
        if flag is None:
            raise UnknownFlag.from_parse(cmd_flag_map, arg)
        parse_as = flag.parse_as
        if not callable(parse_as):
            if arg_text:
                raise InvalidFlagArgument.from_parse(cmd_flag_map, flag, arg_text)
            # e.g., True is effectively store_true, False is effectively store_false
            return flag, parse_as, args[1:]

        try:
            if arg_text is None:
                arg_text = args[1]
                advance = 2
        except IndexError:
            raise InvalidFlagArgument.from_parse(cmd_flag_map, flag, arg=None)
        try:
            arg_val = parse_as(arg_text)
        except Exception as e:
            raise InvalidFlagArgument.from_parse(cmd_flag_map, flag, arg_text, exc=e)

        return flag, arg_val, args[advance:]

    def _parse_flags(self, cmd_flag_map, args):
        """Expects arguments after the initial command and subcommands (i.e.,
        the second item returned from _parse_subcmds)

        Returns a tuple of (multidict of flag names to parsed and validated values, remaining_args).

        Raises on unknown subcommands.
        """
        flag_value_map = OMD()
        ff_path_res_map = OrderedDict()
        ff_path_seen = set()

        orig_args = args
        while args:
            arg = args[0]
            if not arg or arg[0] != '-' or arg == '-' or arg == '--':
                # posargs or post_posargs beginning ('-' is a conventional pos arg for stdin)
                break
            flag, value, args = self._parse_single_flag(cmd_flag_map, args)
            flag_value_map.add(flag.name, value)

            if flag is self.flagfile_flag:
                self._parse_flagfile(cmd_flag_map, value, res_map=ff_path_res_map)
                for path, ff_flag_value_map in ff_path_res_map.items():
                    if path in ff_path_seen:
                        continue
                    flag_value_map.update_extend(ff_flag_value_map)
                    ff_path_seen.add(path)

        return flag_value_map, ff_path_res_map, args

    def _parse_flagfile(self, cmd_flag_map, path_or_file, res_map=None):
        ret = res_map if res_map is not None else OrderedDict()
        if callable(getattr(path_or_file, 'read', None)):
            # enable StringIO and custom flagfile opening
            f_name = getattr(path_or_file, 'name', None)
            path = os.path.abspath(f_name) if f_name else repr(path_or_file)
            ff_text = path_or_file.read()
        else:
            path = os.path.abspath(path_or_file)
            try:
                with codecs.open(path_or_file, 'r', 'utf-8') as f:
                    ff_text = f.read()
            except (UnicodeError, EnvironmentError) as ee:
                raise ArgumentParseError('failed to load flagfile "%s", got: %r' % (path, ee))
        if path in res_map:
            # we've already seen this file
            return res_map
        ret[path] = cur_file_res = OMD()
        lines = ff_text.splitlines()
        for lineno, line in enumerate(lines, 1):
            try:
                args = shlex.split(line, comments=True)
                if not args:
                    continue  # comment or empty line
                flag, value, leftover_args = self._parse_single_flag(cmd_flag_map, args)

                if leftover_args:
                    raise ArgumentParseError('excessive flags or arguments for flag "%s",'
                                             ' expected one flag per line' % flag.name)

                cur_file_res.add(flag.name, value)
                if flag is self.flagfile_flag:
                    self._parse_flagfile(cmd_flag_map, value, res_map=ret)

            except FaceException as fe:
                fe.args = (fe.args[0] + ' (on line %s of flagfile "%s")' % (lineno, path),)
                raise

        return ret

    def _resolve_flags(self, cmd_flag_map, parsed_flag_map, flagfile_map=None):
        ret = OrderedDict()
        cfm, pfm = cmd_flag_map, parsed_flag_map
        flagfile_map = flagfile_map or {}

        # check requireds and set defaults and then...
        missing_flags = []
        for flag_name, flag in cfm.items():
            if flag.name in pfm:
                continue
            if flag.missing is ERROR:
                missing_flags.append(flag.name)
            else:
                pfm[flag.name] = flag.missing
        if missing_flags:
            raise MissingRequiredFlags.from_parse(cfm, pfm, missing_flags)

        # ... resolve dupes
        for flag_name in pfm:
            flag = cfm[flag_name]
            arg_val_list = pfm.getlist(flag_name)
            try:
                ret[flag_name] = flag.multi(flag, arg_val_list)
            except FaceException as fe:
                ff_paths = []
                for ff_path, ff_value_map in flagfile_map.items():
                    if flag_name in ff_value_map:
                        ff_paths.append(ff_path)
                if ff_paths:
                    ff_label = 'flagfiles' if len(ff_paths) > 1 else 'flagfile'
                    msg = ('\n\t(check %s with definitions for flag "%s": %s)'
                           % (ff_label, flag_name, ', '.join(ff_paths)))
                    fe.args = (fe.args[0] + msg,)
                raise
        return ret


def parse_sv_line(line, sep=','):
    """Parse a single line of values, separated by the delimiter
    *sep*. Supports quoting.

    """
    # TODO: this doesn't support unicode, which is intended to be
    # handled at the layer above.
    from csv import reader, Dialect, QUOTE_MINIMAL

    class _face_dialect(Dialect):
        delimiter = sep
        escapechar = '\\'
        quotechar = '"'
        doublequote = True
        skipinitialspace = False
        lineterminator = '\n'
        quoting = QUOTE_MINIMAL

    parsed = list(reader([line], dialect=_face_dialect))
    return parsed[0]


class ListParam(object):
    """The ListParam takes an argument as a character-separated list, and
    produces a Python list of parsed values. Basically, the argument
    equivalent of CSV (Comma-Separated Values)::

      --flag a1,b2,c3

    By default, this yields a ``['a1', 'b2', 'c3']`` as the value for
    ``flag``. The format is also similar to CSV in that it supports
    quoting when values themselves contain the separator::

      --flag 'a1,"b,2",c3'

    Args:
       parse_one_as (callable): Turns a single value's text into its
          parsed value.
       sep (str): A single-character string representing the list
         value separator. Defaults to ``,``.
       strip (bool): Whether or not each value in the list should have
          whitespace stripped before being passed to
          *parse_one_as*. Defaults to False.

    .. note:: Aside from using ListParam, an alternative method for
              accepting multiple arguments is to use the
              ``multi=True`` on the :class:`Flag` constructor. The
              approach tends to be more verbose and can be confusing
              because arguments can get spread across the command
              line.

    """
    def __init__(self, parse_one_as=str, sep=',', strip=False):
        # TODO: min/max limits?
        self.parse_one_as = parse_one_as
        self.sep = sep
        self.strip = strip

    def parse(self, list_text):
        "Parse a single string argument into a list of arguments."
        split_vals = parse_sv_line(list_text, self.sep)
        if self.strip:
            split_vals = [v.strip() for v in split_vals]
        return [self.parse_one_as(v) for v in split_vals]

    __call__ = parse

    def __repr__(self):
        return format_exp_repr(self, ['parse_one_as'], ['sep', 'strip'])


class ChoicesParam(object):
    """Parses a single value, limited to a set of *choices*. The actual
    converter used to parse is inferred from *choices* by default, but
    an explicit one can be set *parse_as*.
    """
    def __init__(self, choices, parse_as=None):
        if not choices:
            raise ValueError('expected at least one choice, not: %r' % choices)
        try:
            self.choices = sorted(choices)
        except Exception:
            # in case choices aren't sortable
            self.choices = list(choices)
        if parse_as is None:
            parse_as = type(self.choices[0])
            # TODO: check for builtins, raise if not a supported type
        self.parse_as = parse_as

    def parse(self, text):
        choice = self.parse_as(text)
        if choice not in self.choices:
            raise ArgumentParseError('expected one of %r, not: %r' % (self.choices, text))
        return choice

    __call__ = parse

    def __repr__(self):
        return format_exp_repr(self, ['choices'], ['parse_as'])


class FilePathParam(object):
    """TODO

    ideas: exists, minimum permissions, can create, abspath, type=d/f
    (technically could also support socket, named pipe, and symlink)

    could do missing=TEMP, but that might be getting too fancy tbh.
    """

class FileValueParam(object):
    """
    TODO: file with a single value in it, like a pidfile
    or a password file mounted in. Read in and treated like it
    was on the argv.
    """
