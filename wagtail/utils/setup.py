from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess

from setuptools import Command
from setuptools.command.bdist_egg import bdist_egg
from setuptools.command.sdist import sdist as base_sdist


class assets_mixin(object):

    def compile_assets(self):
        try:
            subprocess.check_call(['npm', 'run', 'build'])
        except (OSError, subprocess.CalledProcessError) as e:
            print('Error compiling assets: ' + str(e))
            raise SystemExit(1)


class assets(Command, assets_mixin):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.compile_assets()


class sdist(base_sdist, assets_mixin):
    def run(self):
        self.compile_assets()
        base_sdist.run(self)


class check_bdist_egg(bdist_egg):

    # If this file does not exist, warn the user to compile the assets
    sentinel_dir = 'wagtail/wagtailadmin/static/'

    def run(self):
        bdist_egg.run(self)
        if not os.path.isdir(self.sentinel_dir):
            print("\n".join([
                "************************************************************",
                "The front end assets for Wagtail are missing.",
                "To generate the assets, please refer to the documentation in",
                "docs/contributing/css_guidelines.rst",
                "************************************************************",
            ]))
