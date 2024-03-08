
from boltons.iterutils import unique

import face.utils

class FaceException(Exception):
    """The basest base exception Face has. Rarely directly instantiated
    if ever, but useful for catching.
    """
    pass


class ArgumentParseError(FaceException):
    """A base exception used for all errors raised during argument
    parsing.

    Many subtypes have a ".from_parse()" classmethod that creates an
    exception message from the values available during the parse
    process.
    """
    pass


class ArgumentArityError(ArgumentParseError):
    """Raised when too many or too few positional arguments are passed to
    the command. See PosArgSpec for more info.
    """
    pass


class InvalidSubcommand(ArgumentParseError):
    """
    Raised when an unrecognized subcommand is passed.
    """
    @classmethod
    def from_parse(cls, prs, subcmd_name):
        # TODO: add edit distance calculation
        valid_subcmds = unique([path[:1][0] for path in prs.subprs_map.keys()])
        msg = ('unknown subcommand "%s", choose from: %s'
               % (subcmd_name, ', '.join(valid_subcmds)))
        return cls(msg)


class UnknownFlag(ArgumentParseError):
    """
    Raised when an unrecognized flag is passed.
    """
    @classmethod
    def from_parse(cls, cmd_flag_map, flag_name):
        # TODO: add edit distance calculation
        valid_flags = unique([face.utils.format_flag_label(flag) for flag in
                              cmd_flag_map.values() if not flag.display.hidden])
        msg = ('unknown flag "%s", choose from: %s'
               % (flag_name, ', '.join(valid_flags)))
        return cls(msg)


class InvalidFlagArgument(ArgumentParseError):
    """Raised when the argument passed to a flag (the value directly
    after it in argv) fails to parse. Tries to automatically detect
    when an argument is missing.
    """
    @classmethod
    def from_parse(cls, cmd_flag_map, flag, arg, exc=None):
        if arg is None:
            return cls('expected argument for flag %s' % flag.name)

        val_parser = flag.parse_as
        vp_label = getattr(val_parser, 'display_name', face.utils.FRIENDLY_TYPE_NAMES.get(val_parser))
        if vp_label is None:
            vp_label = repr(val_parser)
            tmpl = 'flag %s converter (%r) failed to parse value: %r'
        else:
            tmpl = 'flag %s expected a valid %s value, not %r'
        msg = tmpl % (flag.name, vp_label, arg)

        if exc:
            # TODO: put this behind a verbose flag?
            msg += ' (got error: %r)' % exc
        if arg.startswith('-'):
            msg += '. (Did you forget to pass an argument?)'

        return cls(msg)


class InvalidPositionalArgument(ArgumentParseError):
    """Raised when one of the positional arguments does not
    parse/validate as specified. See PosArgSpec for more info.
    """
    @classmethod
    def from_parse(cls, posargspec, arg, exc):
        prep, type_desc = face.utils.get_type_desc(posargspec.parse_as)
        return cls('positional argument failed to parse %s'
                   ' %s: %r (got error: %r)' % (prep, type_desc, arg, exc))


class MissingRequiredFlags(ArgumentParseError):
    """
    Raised when a required flag is not passed. See Flag for more info.
    """
    @classmethod
    def from_parse(cls, cmd_flag_map, parsed_flag_map, missing_flag_names):
        flag_names = set(missing_flag_names)
        labels = []
        for flag_name in flag_names:
            flag = cmd_flag_map[flag_name]
            labels.append(face.utils.format_flag_label(flag))
        msg = ('missing required arguments for flags: %s'
               % ', '.join(sorted(labels)))
        return cls(msg)


class DuplicateFlag(ArgumentParseError):
    """Raised when a flag is passed multiple times, and the flag's
    "multi" setting is set to 'error'.
    """
    @classmethod
    def from_parse(cls, flag, arg_val_list):
        avl_text = ', '.join([repr(v) for v in arg_val_list])
        if callable(flag.parse_as):
            msg = ('more than one value was passed for flag "%s": %s'
                   % (flag.name, avl_text))
        else:
            msg = ('flag "%s" was used multiple times, but can be used only once' % flag.name)
        return cls(msg)


## Non-parse related exceptions (used primarily in command.py instead of parser.py)

class CommandLineError(FaceException, SystemExit):
    """A :exc:`~face.FaceException` and :exc:`SystemExit` subtype that
    enables safely catching runtime errors that would otherwise cause
    the process to exit.

    If instances of this exception are left uncaught, they will exit
    the process.

    If raised from a :meth:`~face.Command.run()` call and
    ``print_error`` is True, face will print the error before
    reraising. See :meth:`face.Command.run()` for more details.
    """
    def __init__(self, msg, code=1):
        SystemExit.__init__(self, msg)
        self.code = code


class UsageError(CommandLineError):
    """Application developers should raise this :exc:`CommandLineError`
    subtype to indicate to users that the application user has used
    the command incorrectly.

    Instead of printing an ugly stack trace, Face will print a
    readable error message of your choosing, then exit with a nonzero
    exit code.
    """

    def format_message(self):
        msg = self.args[0]
        lines = msg.splitlines()
        msg = '\n       '.join(lines)
        return 'error: ' + msg
