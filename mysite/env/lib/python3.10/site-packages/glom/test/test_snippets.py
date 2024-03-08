import copy
from collections import deque
from decimal import Decimal
import json
import os
import textwrap

import pytest

import glom


def _get_codeblock(lines, offset):
    if lines[offset:offset + 2] != [".. code-block:: python\n", "\n"]:
        return None
    start = offset + 2
    try:
        finish = lines.index('\n', start)
    except ValueError:
        return None
    return textwrap.dedent("".join(lines[start:finish]))


def _find_snippets():
    path = os.path.dirname(os.path.abspath(__file__)) + '/../../docs/snippets.rst'
    with open(path, 'r') as snippet_file:
        lines = list(snippet_file)
    snippets = []
    for line_no in range(len(lines)):
        source = _get_codeblock(lines, line_no)
        if source:
            snippets.append((line_no, source))
    return snippets


try:
    SNIPPETS = _find_snippets()
except:
    SNIPPETS = []  # in case running in an environment without docs

SNIPPETS_GLOBALS = copy.copy(glom.__dict__)
SNIPPETS_GLOBALS.update(dict(
    json=json,
    deque=deque,
    Decimal=Decimal,
    data=json.dumps({'a': ['b']}),
    contacts=[{'primary_email': {'email': 'a@example.com'}}, {}],
    glom=glom.glom))


@pytest.mark.parametrize("line,source", SNIPPETS)
def test_snippet(line, source):
    if '>>>' in source:
        return  # maybe doctest output checking
    code = compile(source, 'snippets.rst', 'exec')
    if 'django' in source:
        return  # maybe in the future
    eval(code, SNIPPETS_GLOBALS)

