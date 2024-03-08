
from __future__ import print_function

import sys
from collections import OrderedDict

from face.utils import unwrap_text, get_rdep_map, echo
from face.errors import ArgumentParseError, CommandLineError, UsageError
from face.parser import Parser, Flag
from face.helpers import HelpHandler
from face.middleware import (inject,
                             get_arg_names,
                             is_middleware,
                             face_middleware,
                             check_middleware,
                             get_middleware_chain,
                             _BUILTIN_PROVIDES)

from boltons.strutils import camel2under
from boltons.iterutils import unique


def _get_default_name(func):
    from functools import partial
    if isinstance(func, partial):
        func = func.func  # just one level of partial for now

    # func_name on py2, __name__ on py3
    ret = getattr(func, 'func_name', getattr(func, '__name__', None))  # most functions hit this

    if ret is None:
        ret = camel2under(func.__class__.__name__).lower()  # callable instances, etc.

    return ret


def _docstring_to_doc(func):
    doc = func.__doc__
    if not doc:
        return ''

    unwrapped = unwrap_text(doc)
    try:
        ret = [g for g in unwrapped.splitlines() if g][0]
    except IndexError:
        ret = ''

    return ret


def default_print_error(msg):
    return echo.err(msg)


DEFAULT_HELP_HANDLER = HelpHandler()


# TODO: should name really go here?
class Command(Parser):
    """The central type in the face framework. Instantiate a Command,
    populate it with flags and subcommands, and then call
    command.run() to execute your CLI.

    Note that only the first three constructor arguments are
    positional, the rest are keyword-only.

    Args:
       func (callable): The function called when this command is
          run with an argv that contains no subcommands.
       name (str): The name of this command, used when this
          command is included as a subcommand. (Defaults to name
          of function)
       doc (str): A description or message that appears in various
           help outputs.
       flags (list): A list of Flag instances to initialize the
          Command with. Flags can always be added later with the
          .add() method.
       posargs (bool): Pass True if the command takes positional
          arguments. Defaults to False. Can also pass a PosArgSpec
          instance.
       post_posargs (bool): Pass True if the command takes
          additional positional arguments after a conventional '--'
          specifier.
       help (bool): Pass False to disable the automatically added
          --help flag. Defaults to True. Also accepts a HelpHandler
          instance, see those docs for more details.
       middlewares (list): A list of @face_middleware decorated
          callables which participate in dispatch. Also addable
          via the .add() method. See Middleware docs for more
          details.

    """
    def __init__(self, func, name=None, doc=None, **kwargs):
        name = name if name is not None else _get_default_name(func)

        if doc is None:
            doc = _docstring_to_doc(func)

        # TODO: default posargs if none by inspecting func
        super(Command, self).__init__(name, doc,
                                      flags=kwargs.pop('flags', None),
                                      posargs=kwargs.pop('posargs', None),
                                      post_posargs=kwargs.pop('post_posargs', None),
                                      flagfile=kwargs.pop('flagfile', True))

        _help = kwargs.pop('help', DEFAULT_HELP_HANDLER)
        self.help_handler = _help

        # TODO: if func is callable, check that "next_" isn't taken
        self._path_func_map = OrderedDict()
        self._path_func_map[()] = func

        middlewares = list(kwargs.pop('middlewares', None) or [])
        self._path_mw_map = OrderedDict()
        self._path_mw_map[()] = []
        self._path_wrapped_map = OrderedDict()
        self._path_wrapped_map[()] = func
        for mw in middlewares:
            self.add_middleware(mw)

        if kwargs:
            raise TypeError('unexpected keyword arguments: %r' % sorted(kwargs.keys()))

        if _help:
            if _help.flag:
                self.add(_help.flag)
            if _help.subcmd:
                self.add(_help.func, _help.subcmd)  # for 'help' as a subcmd

        if not func and not _help:
            raise ValueError('Command requires a handler function or help handler'
                             ' to be set, not: %r' % func)

        return

    @property
    def func(self):
        return self._path_func_map[()]

    def add(self, *a, **kw):
        """Add a flag, subcommand, or middleware to this Command.

        If the first argument is a callable, this method contructs a
        Command from it and the remaining arguments, all of which are
        optional. See the Command docs for for full details on names
        and defaults.

        If the first argument is a string, this method constructs a
        Flag from that flag string and the rest of the method
        arguments, all of which are optional. See the Flag docs for
        more options.

        If the argument is already an instance of Flag or Command, an
        exception is only raised on conflicting subcommands and
        flags. See add_command for details.

        Middleware is only added if it is already decorated with
        @face_middleware. Use .add_middleware() for automatic wrapping
        of callables.

        """
        # TODO: need to check for middleware provides names + flag names
        # conflict

        target = a[0]

        if is_middleware(target):
            return self.add_middleware(target)

        subcmd = a[0]
        if not isinstance(subcmd, Command) and callable(subcmd) or subcmd is None:
            subcmd = Command(*a, **kw)  # attempt to construct a new subcmd

        if isinstance(subcmd, Command):
            self.add_command(subcmd)
            return subcmd

        flag = a[0]
        if not isinstance(flag, Flag):
            flag = Flag(*a, **kw)  # attempt to construct a Flag from arguments
        super(Command, self).add(flag)

        return flag

    def add_command(self, subcmd):
        """Add a Command, and all of its subcommands, as a subcommand of this
        Command.

        Middleware from the current command is layered on top of the
        subcommand's. An exception may be raised if there are
        conflicting middlewares or subcommand names.
        """
        if not isinstance(subcmd, Command):
            raise TypeError('expected Command instance, not: %r' % subcmd)
        self_mw = self._path_mw_map[()]
        super(Command, self).add(subcmd)
        # map in new functions
        for path in self.subprs_map:
            if path not in self._path_func_map:
                self._path_func_map[path] = subcmd._path_func_map[path[1:]]
                sub_mw = subcmd._path_mw_map[path[1:]]
                self._path_mw_map[path] = self_mw + sub_mw  # TODO: check for conflicts
        return

    def add_middleware(self, mw):
        """Add a single middleware to this command. Outermost middleware
        should be added first. Remember: first added, first called.

        """
        if not is_middleware(mw):
            mw = face_middleware(mw)
        check_middleware(mw)

        for flag in mw._face_flags:
            self.add(flag)

        for path, mws in self._path_mw_map.items():
            self._path_mw_map[path] = [mw] + mws  # TODO: check for conflicts

        return

    # TODO: add_flag()

    def get_flag_map(self, path=(), with_hidden=True):
        """Command's get_flag_map differs from Parser's in that it filters
        the flag map to just the flags used by the endpoint at the
        associated subcommand *path*.
        """
        flag_map = super(Command, self).get_flag_map(path=path, with_hidden=with_hidden)
        dep_names = self.get_dep_names(path)
        if 'args_' in dep_names or 'flags_' in dep_names:
            # the argument parse result and flag dict both capture
            # _all_ the flags, so for functions accepting these
            # arguments we bypass filtering.

            # Also note that by setting an argument default in the
            # function definition, the dependency becomes "weak", and
            # this bypassing of filtering will not trigger, unless
            # another function in the chain has a non-default,
            # "strong" dependency. This behavior is especially useful
            # for middleware.

            # TODO: add decorator for the corner case where a function
            # accepts these arguments and doesn't use them all.
            return OrderedDict(flag_map)

        return OrderedDict([(k, f) for k, f in flag_map.items() if f.name in dep_names
                            or f is self.flagfile_flag or f is self.help_handler.flag])

    def get_dep_names(self, path=()):
        """Get a list of the names of all required arguments of a command (and
        any associated middleware).

        By specifying *path*, the same can be done for any subcommand.
        """
        func = self._path_func_map[path]
        if not func:
            return []  # for when no handler is specified

        mws = self._path_mw_map[path]

        # start out with all args of handler function, which gets stronger dependencies
        required_args = set(get_arg_names(func, only_required=False))
        dep_map = {func: set(required_args)}
        for mw in mws:
            arg_names = set(get_arg_names(mw, only_required=True))
            for provide in mw._face_provides:
                dep_map[provide] = arg_names
            if not mw._face_optional:
                # all non-optional middlewares get their args required, too.
                required_args.update(arg_names)

        rdep_map = get_rdep_map(dep_map)

        recursive_required_args = rdep_map[func].union(required_args)

        return sorted(recursive_required_args)

    def prepare(self, paths=None):
        """Compile and validate one or more subcommands to ensure all
        dependencies are met. Call this once all flags, subcommands,
        and middlewares have been added (using .add()).

        This method is automatically called by .run() method, but it
        only does so for the specific subcommand being invoked. More
        conscientious users may want to call this method with no
        arguments to validate that all subcommands are ready for
        execution.
        """
        # TODO: also pre-execute help formatting to make sure all
        # values are sane there, too
        if paths is None:
            paths = self._path_func_map.keys()

        for path in paths:
            func = self._path_func_map[path]
            if func is None:
                continue  # handled by run()

            prs = self.subprs_map[path] if path else self
            provides = []
            if prs.posargs.provides:
                provides += [prs.posargs.provides]
            if prs.post_posargs.provides:
                provides += [prs.post_posargs.provides]

            deps = self.get_dep_names(path)
            flag_names = [f.name for f in self.get_flags(path=path)]
            all_mws = self._path_mw_map[path]

            # filter out unused middlewares
            mws = [mw for mw in all_mws if not mw._face_optional
                   or [p for p in mw._face_provides if p in deps]]
            provides += _BUILTIN_PROVIDES + flag_names
            try:
                wrapped = get_middleware_chain(mws, func, provides)
            except NameError as ne:
                ne.args = (ne.args[0] + ' (in path: %r)' % (path,),)
                raise

            self._path_wrapped_map[path] = wrapped

        return

    def run(self, argv=None, extras=None, print_error=None):
        """Parses arguments and dispatches to the appropriate subcommand
        handler. If there is a parse error due to invalid user input,
        an error is printed and a CommandLineError is raised. If not
        caught, a CommandLineError will exit the process, typically
        with status code 1. Also handles dispatching to the
        appropriate HelpHandler, if configured.

        Defaults to handling the arguments on the command line
        (``sys.argv``), but can also be explicitly passed arguments
        via the *argv* parameter.

        Args:
           argv (list): A sequence of strings representing the
              command-line arguments. Defaults to ``sys.argv``.
           extras (dict): A map of additional arguments to be made
              available to the subcommand's handler function.
           print_error (callable): The function that formats/prints
               error messages before program exit on CLI errors.

        .. note::

           For efficiency, :meth:`run()` only checks the subcommand
           invoked by *argv*. To ensure that all subcommands are
           configured properly, call :meth:`prepare()`.

        """
        if print_error is None or print_error is True:
            print_error = default_print_error
        elif print_error and not callable(print_error):
            raise TypeError('expected callable for print_error, not %r'
                            % print_error)

        kwargs = dict(extras) if extras else {}
        kwargs['print_error_'] = print_error  # TODO: print_error_ in builtin provides?

        try:
            prs_res = self.parse(argv=argv)
        except ArgumentParseError as ape:
            prs_res = ape.prs_res

            # even if parsing failed, check if the caller was trying to access the help flag
            cmd = prs_res.to_cmd_scope()['subcommand_']
            if cmd.help_handler and prs_res.flags and prs_res.flags.get(cmd.help_handler.flag.name):
                kwargs.update(prs_res.to_cmd_scope())
                return inject(cmd.help_handler.func, kwargs)

            msg = 'error: ' + (prs_res.name or self.name)
            if prs_res.subcmds:
                msg += ' ' + ' '.join(prs_res.subcmds or ())

            # args attribute, nothing to do with cmdline args this is
            # the standard-issue Exception
            e_msg = ape.args[0]
            if e_msg:
                msg += ': ' + e_msg
            cle = CommandLineError(msg)
            if print_error:
                print_error(msg)
            raise cle

        kwargs.update(prs_res.to_cmd_scope())

        # default in case no middlewares have been installed
        func = self._path_func_map[prs_res.subcmds]

        cmd = kwargs['subcommand_']
        if cmd.help_handler and (not func or (prs_res.flags and prs_res.flags.get(cmd.help_handler.flag.name))):
            return inject(cmd.help_handler.func, kwargs)
        elif not func:  # pragma: no cover
            raise RuntimeError('expected command handler or help handler to be set')

        self.prepare(paths=[prs_res.subcmds])
        wrapped = self._path_wrapped_map.get(prs_res.subcmds, func)

        try:
            ret = inject(wrapped, kwargs)
        except UsageError as ue:
            if print_error:
                print_error(ue.format_message())
            raise
        return ret
