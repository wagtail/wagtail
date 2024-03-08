# Load in our dependencies
from __future__ import absolute_import
import argparse
from collections import OrderedDict
import json
import os
import sys

from docutils.utils import Reporter

from restructuredtext_lint.lint import lint_file

# Generate our levels mapping constant
# DEV: We use an ordered dict for ordering in `--help`
# http://repo.or.cz/docutils.git/blob/422cede485668203abc01c76ca317578ff634b30:/docutils/docutils/utils/__init__.py#l65
WARNING_LEVEL_KEY = 'warning'
LEVEL_MAP = OrderedDict([
    ('debug', Reporter.DEBUG_LEVEL),  # 0
    ('info', Reporter.INFO_LEVEL),  # 1
    (WARNING_LEVEL_KEY, Reporter.WARNING_LEVEL),  # 2
    ('error', Reporter.ERROR_LEVEL),  # 3
    ('severe', Reporter.SEVERE_LEVEL),  # 4
])


# Load in VERSION from standalone file
with open(os.path.join(os.path.dirname(__file__), 'VERSION'), 'r') as version_file:
    VERSION = version_file.read().strip()

# Define default contents
DEFAULT_FORMAT = 'text'
DEFAULT_LEVEL_KEY = WARNING_LEVEL_KEY


# Define our CLI function
def _main(paths, format=DEFAULT_FORMAT, stream=sys.stdout, encoding=None, level=LEVEL_MAP[DEFAULT_LEVEL_KEY],
          **kwargs):
    error_dicts = []
    error_occurred = False
    filepaths = []

    for path in paths:
        # Check if the given path is a file or a directory
        if os.path.isfile(path):
            filepaths.append(path)
        elif os.path.isdir(path):
            # Recurse over subdirectories to search for *.rst files
            for root, subdir, files in os.walk(path):
                for file in files:
                    if file.endswith('.rst'):
                        filepaths.append(os.path.join(root, file))
        else:
            stream.write('Path "{path}" not found as a file nor directory\n'.format(path=path))
            sys.exit(1)
            return

    for filepath in filepaths:
        # Read and lint the file
        unfiltered_file_errors = lint_file(filepath, encoding=encoding, **kwargs)
        file_errors = [err for err in unfiltered_file_errors if err.level >= level]

        if file_errors:
            error_occurred = True
            if format == 'text':
                for err in file_errors:
                    # e.g. WARNING readme.rst:12 Title underline too short.
                    stream.write('{err.type} {err.source}:{err.line} {err.message}\n'.format(err=err))
            elif format == 'json':
                error_dicts.extend({
                    'line': error.line,
                    'source': error.source,
                    'level': error.level,
                    'type': error.type,
                    'message': error.message,
                    'full_message': error.full_message,
                } for error in file_errors)

    if format == 'json':
        stream.write(json.dumps(error_dicts))

    if error_occurred:
        sys.exit(2)  # Using 2 for linting failure, 1 for internal error
    else:
        sys.exit(0)  # Success!


def main():
    # Set up options and parse arguments
    parser = argparse.ArgumentParser(description='Lint reStructuredText files. Returns 0 if all files pass linting, '
                                     '1 for an internal error, and 2 if linting failed.')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('paths', metavar='path', nargs='+', type=str, help='File/folder to lint')
    parser.add_argument('--format', default=DEFAULT_FORMAT, type=str, choices=('text', 'json'),
                        help='Format of the output (default: "{default}")'.format(default=DEFAULT_FORMAT))
    parser.add_argument('--encoding', type=str, help='Encoding of the input file (e.g. "utf-8")')
    parser.add_argument('--level', default=DEFAULT_LEVEL_KEY, type=str, choices=LEVEL_MAP.keys(),
                        help='Minimum error level to report (default: "{default}")'.format(default=DEFAULT_LEVEL_KEY))
    parser.add_argument('--rst-prolog', type=str,
                        help='reStructuredText content to prepend to all files (useful for substitutions)')
    args = parser.parse_args()

    # Convert our level from string to number for `_main`
    args.level = LEVEL_MAP[args.level]

    # Run the main argument
    _main(**args.__dict__)


if __name__ == '__main__':
    main()
