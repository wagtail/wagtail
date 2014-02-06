"""Remove `.coverage.$HOST.$ID` files from previous runs.

In Python because of portability with Windows.
"""

import sys

import os


def main():
    workspace = os.environ['WORKSPACE']
    for filename in os.listdir(workspace):
        if filename.startswith('.coverage.'):
            file_full_name = os.path.join(workspace, filename)
            sys.stdout.write(
                '* Removing old .coverage file: `%s`\n' % file_full_name)
            os.unlink(file_full_name)
    sys.stdout.flush()

if __name__ == '__main__':
    main()
