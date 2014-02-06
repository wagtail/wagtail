#!/bin/sh

# Script that takes source code quality measurements.
# In shell because it will run in a *NIX node.

pip install pylint pep8 pytest coverage
coverage erase

# Combining the coverage data of all the test runs
# in the different OS/Python combinations.
find $WORKSPACE -mindepth 1 -maxdepth 2 -name '.coverage.*' -exec cp -v \{\} . \;
coverage combine
coverage report
coverage xml
coverage erase

SRCFILES=treebeard/*.py
PYFILES=`find . -name '*.py'`
ALLFILES=`find . -type f`
sloccount --duplicates --wide --details $ALLFILES > sloccount.sc 2>&1
pep8 $PYFILES > violations-pep8.txt 2>&1
pylint -f parseable $SRCFILES > violations-pylint.txt 2>&1
