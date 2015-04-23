from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess

from distutils.core import Command

from setuptools.command.bdist_egg import bdist_egg


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


class check_bdist_egg(bdist_egg):

    # If this file does not exist, warn the user to compile the assets
    sentinel_file = 'wagtail/wagtailadmin/static/wagtailadmin/css/core.css'

    def run(self):
        bdist_egg.run(self)
        if not os.path.isfile(self.sentinel_file):
            print("\n".join([
                "************************************************************",
                "The front end assets for Wagtail are missing.",
                "To generate the assets, please refer to the documentation in",
                "docs/contributing/css_guidelines.rst",
                "************************************************************",
            ]))


def add_subcommand(command, extra_sub_commands):
    # Sadly, as commands are old-style classes, `type()` can not be used to
    # construct these.
    class CompileAnd(command):
        sub_commands = command.sub_commands + extra_sub_commands
    CompileAnd.__name__ = command.__name__
    return CompileAnd
