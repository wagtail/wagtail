# Design (and some implementation) of this owes heavily to Click's
# CliRunner (TODO: bring in license?)

"""Porting notes:

* EchoingStdin.read1() needed to exist for py3 and raw_input
* Not sure why the isolate context manager deals in byte streams and
  then relegates to the Result to do late encoding (in properties no
  less). This is especially troublesome because sys.stdout/stderr
  isn't the same stream as stdout/stderr as returned by the context
  manager. (see the extra flush calls in run's finally block.) Is
  it just for parity with py2? There was a related bug, sys.stdout was
  flushed, but not sys.stderr, which caused py3's error_bytes to come
  through as blank.
* sys.stderr had to be flushed, too, on py3 (in invoke's finally)
* Result.exception was redundant with exc_info
* Result.stderr raised a ValueError when stderr was empty, not just
  when it wasn't captured.
* Instead of isolated_filesystem, I just added chdir to run,
  because pytest already does temporary directories.
* Removed echo_stdin (stdin never echos, as it wouldn't with subprocess)

"""

import os
import sys
import shlex
import getpass
import contextlib
from subprocess import list2cmdline
from functools import partial

try:
    from collections.abc import Container
except ImportError:
    from collections import Container

PY2 = sys.version_info[0] == 2

if PY2:
    from cStringIO import StringIO
else:
    import io
    unicode = str


from boltons.setutils import complement


def _make_input_stream(input, encoding):
    if input is None:
        input = b''
    elif isinstance(input, unicode):
        input = input.encode(encoding)
    elif not isinstance(input, bytes):
        raise TypeError('expected bytes, text, or None, not: %r' % input)
    if PY2:
        return StringIO(input)
    return io.BytesIO(input)


def _fake_getpass(prompt='Password: ', stream=None):
    if not stream:
        stream = sys.stderr
    input = sys.stdin
    prompt = str(prompt)
    if prompt:
        stream.write(prompt)
        stream.flush()
    line = input.readline()
    if not line:
        raise EOFError
    if line[-1] == '\n':
        line = line[:-1]
    return line


class RunResult(object):
    """Returned from :meth:`CommandChecker.run()`, complete with the
    relevant inputs and outputs of the run.

    Instances of this object are especially valuable for verifying
    expected output via the :attr:`~RunResult.stdout` and
    :attr:`~RunResult.stderr` attributes.

    API modeled after :class:`subprocess.CompletedProcess` for
    familiarity and porting of tests.

    """

    def __init__(self, args, input, exit_code, stdout_bytes, stderr_bytes, exc_info=None, checker=None):
        self.args = args
        self.input = input
        self.checker = checker
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.exit_code = exit_code  # integer

        # if an exception occurred:
        self.exc_info = exc_info
        # TODO: exc_info won't be available in subprocess... maybe the
        # text of a parsed-out traceback? But in general, tracebacks
        # aren't usually part of CLI UX...

    @property
    def exception(self):
        """Exception instance, if an uncaught error was raised.
        Equivalent to ``run_res.exc_info[1]``, but more readable."""
        return self.exc_info[1] if self.exc_info else None

    @property
    def returncode(self):  # for parity with subprocess.CompletedProcess
        "Alias of :attr:`exit_code`, for parity with :class:`subprocess.CompletedProcess`"
        return self.exit_code

    @property
    def stdout(self):
        """The text output ("stdout") of the command, as a decoded
        string. See :attr:`stdout_bytes` for the bytestring.
        """
        return (self.stdout_bytes
                .decode(self.checker.encoding, 'replace')
                .replace('\r\n', '\n'))

    @property
    def stderr(self):
        """The error output ("stderr") of the command, as a decoded
        string. See :attr:`stderr_bytes` for the bytestring. May be
        ``None`` if *mix_stderr* was set to ``True`` in the
        :class:`~face.CommandChecker`.
        """
        if self.stderr_bytes is None:
            raise ValueError("stderr not separately captured")
        return (self.stderr_bytes
                .decode(self.checker.encoding, 'replace')
                .replace('\r\n', '\n'))

    def __repr__(self):
        # very similar to subprocess.CompleteProcess repr
        args = ['args={!r}'.format(self.args),
                'returncode={!r}'.format(self.returncode)]
        if self.stdout_bytes:
            args.append('stdout=%r' % (self.stdout,))
        if self.stderr_bytes is not None:
            args.append('stderr=%r' % (self.stderr,))
        if self.exception:
            args.append('exception=%r' % (self.exception,))
        return "%s(%s)" % (self.__class__.__name__, ', '.join(args))



def _get_exp_code_text(exp_codes):
    try:
        codes_len = len(exp_codes)
    except Exception:
        comp_codes = complement(exp_codes)
        try:
            comp_codes = tuple(comp_codes)
            return 'any code but %r' % (comp_codes[0] if len(comp_codes) == 1 else comp_codes)
        except Exception:
            return repr(exp_codes)
    if codes_len == 1:
        return repr(exp_codes[0])
    return 'one of %r' % (tuple(exp_codes),)


class CheckError(AssertionError):
    """Rarely raised directly, :exc:`CheckError` is automatically
    raised when a :meth:`CommandChecker.run()` call does not terminate
    with an expected error code.

    This error attempts to format the stdout, stderr, and stdin of the
    run for easier debugging.
    """
    def __init__(self, result, exit_codes):
        self.result = result
        exp_code = _get_exp_code_text(exit_codes)
        msg = ('Got exit code %r (expected %s) when running command: %s'
               % (result.exit_code, exp_code, list2cmdline(result.args)))
        if result.stdout:
            msg += '\nstdout = """\n'
            msg += result.stdout
            msg += '"""\n'
        if result.stderr_bytes:
            msg += '\nstderr = """\n'
            msg += result.stderr
            msg += '"""\n'
        if result.input:
            msg += '\nstdin = """\n'
            msg += result.input
            msg += '"""\n'
        AssertionError.__init__(self, msg)


class CommandChecker(object):
    """Face's main testing interface.

    Wrap your :class:`Command` instance in a :class:`CommandChecker`,
    :meth:`~CommandChecker.run()` commands with arguments, and get
    :class:`RunResult` objects to validate your Command's behavior.

    Args:

       cmd: The :class:`Command` instance to test.
       env (dict): An optional base environment to use for subsequent
         calls issued through this checker. Defaults to ``{}``.
       chdir (str): A default path to execute this checker's commands
         in. Great for temporary directories to ensure test isolation.
       mix_stderr (bool): Set to ``True`` to capture stderr into
         stdout. This makes it easier to verify order of standard
         output and errors. If ``True``, this checker's results'
         error_bytes will be set to ``None``. Defaults to ``False``.
       reraise (bool): Reraise uncaught exceptions from within *cmd*'s
         endpoint functions, instead of returning a :class:`RunResult`
         instance. Defaults to ``False``.

    """
    def __init__(self, cmd, env=None, chdir=None, mix_stderr=False, reraise=False):
        self.cmd = cmd
        self.base_env = env or {}
        self.reraise = reraise
        self.mix_stderr = mix_stderr
        self.encoding = 'utf8'  # not clear if this should be an arg yet
        self.chdir = chdir

    @contextlib.contextmanager
    def _isolate(self, input=None, env=None, chdir=None):
        old_cwd = os.getcwd()
        old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
        old_getpass = getpass.getpass

        tmp_stdin = _make_input_stream(input, self.encoding)

        full_env = dict(self.base_env)

        chdir = chdir or self.chdir
        if env:
            full_env.update(env)

        if PY2:
            tmp_stdout = bytes_output = StringIO()
            if self.mix_stderr:
                tmp_stderr = tmp_stdout
            else:
                bytes_error = tmp_stderr = StringIO()
        else:
            bytes_output = io.BytesIO()
            tmp_stdin = io.TextIOWrapper(tmp_stdin, encoding=self.encoding)
            tmp_stdout = io.TextIOWrapper(
                bytes_output, encoding=self.encoding)
            if self.mix_stderr:
                tmp_stderr = tmp_stdout
            else:
                bytes_error = io.BytesIO()
                tmp_stderr = io.TextIOWrapper(
                    bytes_error, encoding=self.encoding)

        old_env = {}
        try:
            _sync_env(os.environ, full_env, old_env)
            if chdir:
                os.chdir(str(chdir))
            sys.stdin, sys.stdout, sys.stderr = tmp_stdin, tmp_stdout, tmp_stderr
            getpass.getpass = _fake_getpass

            yield (bytes_output, bytes_error if not self.mix_stderr else None)
        finally:
            if chdir:
                os.chdir(old_cwd)

            _sync_env(os.environ, old_env)

            # see note above
            tmp_stdout.flush()
            tmp_stderr.flush()
            sys.stdin, sys.stdout, sys.stderr = old_stdin, old_stdout, old_stderr
            getpass.getpass = old_getpass

        return

    def fail(self, *a, **kw):
        """Convenience method around :meth:`~CommandChecker.run()`, with the
        same signature, except that this will raise a
        :exc:`CheckError` if the command completes with exit code
        ``0``.
        """
        kw.setdefault('exit_code', complement(set([0])))
        return self.run(*a, **kw)

    def __getattr__(self, name):
        if not name.startswith('fail_'):
            return super(CommandChecker, self).__getattr__(name)
        _, _, code_str = name.partition('fail_')
        try:
            code = [int(cs) for cs in code_str.split('_')]
        except Exception:
            raise AttributeError('fail_* shortcuts must end in integers, not %r'
                                 % code_str)
        return partial(self.fail, exit_code=code)

    def run(self, args, input=None, env=None, chdir=None, exit_code=0):
        """The :meth:`run` method acts as the primary entrypoint to the
        :class:`CommandChecker` instance. Pass arguments as a list or
        string, and receive a :class:`RunResult` with which to verify
        your command's output.

        If the arguments do not result in an expected *exit_code*, a
        :exc:`CheckError` will be raised.

        Args:

           args: A list or string representing arguments, as one might
              find in :attr:`sys.argv` or at the command line.
           input (str): A string (or list of lines) to be passed to
              the command's stdin. Used for testing
              :func:`~face.prompt` interactions, among others.
           env (dict): A mapping of environment variables to apply on
              top of the :class:`CommandChecker`'s base env vars.
           chdir (str): A string (or stringifiable path) path to
              switch to before running the command. Defaults to
              ``None`` (runs in current directory).
           exit_code (int): An integer or list of integer exit codes
             expected from running the command with *args*. If the
             actual exit code does not match *exit_code*,
             :exc:`CheckError` is raised. Set to ``None`` to disable
             this behavior and always return
             :class:`RunResult`. Defaults to ``0``.

        .. note::

           At this time, :meth:`run` interacts with global process
           state, and is not designed for parallel usage.

        """
        if isinstance(input, (list, tuple)):
            input = '\n'.join(input)
        if exit_code is None:
            exit_codes = ()
        elif isinstance(exit_code, int):
            exit_codes = (exit_code,)
        elif not isinstance(exit_code, Container):
            raise TypeError('expected exit_code to be None, int, or'
                            ' Container of ints, representing expected'
                            ' exit_codes, not: %r' % (exit_code,))
        else:
            exit_codes = exit_code
        with self._isolate(input=input, env=env, chdir=chdir) as (stdout, stderr):
            exc_info = None
            exit_code = 0

            if isinstance(args, (str, unicode)):
                args = shlex.split(args)

            try:
                res = self.cmd.run(args or ())
            except SystemExit as se:
                exc_info = sys.exc_info()
                exit_code = se.code if se.code is not None else 0
            except Exception:
                if self.reraise:
                    raise
                exit_code = -1  # TODO: something better?
                exc_info = sys.exc_info()
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
                stdout_bytes = stdout.getvalue()
                stderr_bytes = stderr.getvalue() if not self.mix_stderr else None

        run_res = RunResult(checker=self,
                            args=args,
                            input=input,
                            stdout_bytes=stdout_bytes,
                            stderr_bytes=stderr_bytes,
                            exit_code=exit_code,
                            exc_info=exc_info)
        if exit_codes and exit_code not in exit_codes:
            exc = CheckError(run_res, exit_codes)
            raise exc
        return run_res


# syncing os.environ (as opposed to modifying a copy and setting it
# back) takes care of cases when someone has a reference to environ
def _sync_env(env, new, backup=None):
    if PY2:
        # py2 expects bytes in os.environ
        encode = lambda x: x.encode('utf8') if isinstance(x, unicode) else x
        new = {encode(k): encode(v) for k, v in new.items()}

    for key, value in new.items():
        if backup is not None:
            backup[key] = env.get(key)
        if value is not None:
            env[key] = value
            continue
        try:
            del env[key]
        except Exception:
            pass
    return backup
