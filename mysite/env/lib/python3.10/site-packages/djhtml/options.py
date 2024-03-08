"""
Options set by command-line arguments. Usage:

    import options
    print(f"Tabwidth is {options.tabwidth}")

"""

import argparse
import sys
from importlib.metadata import version

parser = argparse.ArgumentParser(
    description=(
        """
DjHTML indents mixed HTML/CSS/JavaScript templates that
contain Django or Jinja template tags. It works similar to
other code-formatting tools such as Black and interoperates
nicely with pre-commit."""
    ),
    epilog="Full documentation at https://github.com/rtts/djhtml",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    add_help=False,
)
parser.add_argument(
    "-h",
    "--help",
    dest="show_help",
    action="store_true",
    help="show this help message and exit",
)
parser.add_argument(
    "-v",
    "--version",
    dest="show_version",
    action="store_true",
    help="show version number and exit",
)
parser.add_argument(
    "-c",
    "--check",
    action="store_true",
    help="check indentation without modifying files",
)
parser.add_argument(
    "-t",
    "--tabwidth",
    metavar="N",
    type=int,
    default=0,
    help="tabwidth (the default is to guess)",
)
parser.add_argument(
    "input_filenames",
    metavar="SOURCE",
    nargs="*",
    help="file or directory name(s) to indent",
)
parser.add_argument("-d", "--debug", action="store_true", help=argparse.SUPPRESS)
parser.add_argument("-i", "--in-place", action="store_true", help=argparse.SUPPRESS)

# Parse arguments and assign attributes to self
self = sys.modules[__name__]
args = parser.parse_args(namespace=self)

if show_version:
    print(version("djhtml"))
    sys.exit()
elif show_help or not input_filenames:
    parser.print_help()
    sys.exit()
elif in_place:
    sys.exit(
        """
You have called DjHTML with the -i or --in-place argument which
has been deprecated as it's now the default. If you have a custom
pre-commit entry for DjHTML, remove the -i argument from it and
everything will continue to work as before.
"""
    )
