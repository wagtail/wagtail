from __future__ import absolute_import, print_function, unicode_literals
import subprocess

from distutils.core import Command


class assets(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            subprocess.check_call(['npm', 'run', 'build'])
        except (OSError, subprocess.CalledProcessError) as e:
            print('Error compiling assets: ' + str(e))
            raise SystemExit(1)


def add_subcommand(command, extra_sub_commands):
    # Sadly, as commands are old-style classes, `type()` can not be used to
    # construct these. Additionally, old-style classes do not have a `name`
    # attribute, so naming them nicely is also impossible.
    class CompileAnd(command):
        sub_commands = command.sub_commands + extra_sub_commands
    CompileAnd.__name__ = command.__name__
    return CompileAnd
