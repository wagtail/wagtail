import subprocess

from setuptools import setup
from setuptools.command.sdist import sdist as base_sdist


class sdist(base_sdist):
    def compile_assets(self):
        try:
            subprocess.check_call(["npm", "run", "build"])
        except (OSError, subprocess.CalledProcessError) as error:
            print("Error compiling assets: " + str(error))  # noqa: T201
            raise SystemExit(1) from error

    def run(self):
        self.compile_assets()
        super().run()


setup(
    name="wagtail",
    cmdclass={"sdist": sdist},
)
