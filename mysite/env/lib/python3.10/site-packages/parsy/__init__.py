# -*- coding: utf-8 -*- #

import operator
import re
import sys
from collections import namedtuple
from functools import wraps

from .version import __version__  # noqa: F401


def line_info_at(stream, index):
    if index > len(stream):
        raise ValueError("invalid index")
    line = stream.count("\n", 0, index)
    last_nl = stream.rfind("\n", 0, index)
    col = index - (last_nl + 1)
    return (line, col)


class ParseError(RuntimeError):
    def __init__(self, expected, stream, index):
        self.expected = expected
        self.stream = stream
        self.index = index

    def line_info(self):
        try:
            return '{}:{}'.format(*line_info_at(self.stream, self.index))
        except (TypeError, AttributeError):  # not a str
            return str(self.index)

    def __str__(self):
        expected_list = sorted(repr(e) for e in self.expected)

        if len(expected_list) == 1:
            return 'expected {} at {}'.format(expected_list[0], self.line_info())
        else:
            return 'expected one of {} at {}'.format(', '.join(expected_list), self.line_info())


class Result(namedtuple('Result', 'status index value furthest expected')):
    @staticmethod
    def success(index, value):
        return Result(True, index, value, -1, frozenset())

    @staticmethod
    def failure(index, expected):
        return Result(False, -1, None, index, frozenset([expected]))

    # collect the furthest failure from self and other
    def aggregate(self, other):
        if not other:
            return self

        if self.furthest > other.furthest:
            return self
        elif self.furthest == other.furthest:
            # if we both have the same failure index, we combine the expected messages.
            return Result(self.status, self.index, self.value, self.furthest, self.expected | other.expected)
        else:
            return Result(self.status, self.index, self.value, other.furthest, other.expected)


class Parser(object):
    """
    A Parser is an object that wraps a function whose arguments are
    a string to be parsed and the index on which to begin parsing.
    The function should return either Result.success(next_index, value),
    where the next index is where to continue the parse and the value is
    the yielded value, or Result.failure(index, expected), where expected
    is a string indicating what was expected, and the index is the index
    of the failure.
    """

    def __init__(self, wrapped_fn):
        self.wrapped_fn = wrapped_fn

    def __call__(self, stream, index):
        return self.wrapped_fn(stream, index)

    def parse(self, stream):
        """Parse a string or list of tokens and return the result or raise a ParseError."""
        (result, _) = (self << eof).parse_partial(stream)
        return result

    def parse_partial(self, stream):
        """
        Parse the longest possible prefix of a given string.
        Return a tuple of the result and the rest of the string,
        or raise a ParseError.
        """
        result = self(stream, 0)

        if result.status:
            return (result.value, stream[result.index:])
        else:
            raise ParseError(result.expected, stream, result.furthest)

    def bind(self, bind_fn):
        @Parser
        def bound_parser(stream, index):
            result = self(stream, index)

            if result.status:
                next_parser = bind_fn(result.value)
                return next_parser(stream, result.index).aggregate(result)
            else:
                return result

        return bound_parser

    def map(self, map_fn):
        return self.bind(lambda res: success(map_fn(res)))

    def combine(self, combine_fn):
        return self.bind(lambda res: success(combine_fn(*res)))

    def combine_dict(self, combine_fn):
        return self.bind(lambda res: success(combine_fn(**res)))

    def concat(self):
        return self.map(''.join)

    def then(self, other):
        return seq(self, other).combine(lambda left, right: right)

    def skip(self, other):
        return seq(self, other).combine(lambda left, right: left)

    def result(self, res):
        return self >> success(res)

    def many(self):
        return self.times(0, float('inf'))

    def times(self, min, max=None):
        # max=None means exactly min
        # min=max=None means from 0 to infinity
        if max is None:
            max = min

        @Parser
        def times_parser(stream, index):
            values = []
            times = 0
            result = None

            while times < max:
                result = self(stream, index).aggregate(result)
                if result.status:
                    values.append(result.value)
                    index = result.index
                    times += 1
                elif times >= min:
                    break
                else:
                    return result

            return Result.success(index, values).aggregate(result)

        return times_parser

    def at_most(self, n):
        return self.times(0, n)

    def at_least(self, n):
        return self.times(n) + self.many()

    def optional(self):
        return self.times(0, 1).map(lambda v: v[0] if v else None)

    def sep_by(self, sep, *, min=0, max=float('inf')):
        zero_times = success([])
        if max == 0:
            return zero_times
        res = self.times(1) + (sep >> self).times(min - 1, max - 1)
        if min == 0:
            res |= zero_times
        return res

    def desc(self, description):
        @Parser
        def desc_parser(stream, index):
            result = self(stream, index)
            if result.status:
                return result
            else:
                return Result.failure(index, description)

        return desc_parser

    def mark(self):
        @generate
        def marked():
            start = yield line_info
            body = yield self
            end = yield line_info
            return (start, body, end)

        return marked

    def tag(self, name):
        return self.map(lambda v: (name, v))

    def should_fail(self, description):
        @Parser
        def fail_parser(stream, index):
            res = self(stream, index)
            if res.status:
                return Result.failure(index, description)
            return Result.success(index, res)

        return fail_parser

    def __add__(self, other):
        return seq(self, other).combine(operator.add)

    def __mul__(self, other):
        if isinstance(other, range):
            return self.times(other.start, other.stop - 1)
        return self.times(other)

    def __or__(self, other):
        return alt(self, other)

    # haskelley operators, for fun #

    # >>
    def __rshift__(self, other):
        return self.then(other)

    # <<
    def __lshift__(self, other):
        return self.skip(other)


def alt(*parsers):
    if not parsers:
        return fail('<empty alt>')

    @Parser
    def alt_parser(stream, index):
        result = None
        for parser in parsers:
            result = parser(stream, index).aggregate(result)
            if result.status:
                return result

        return result

    return alt_parser


if sys.version_info >= (3, 6):
    # Only 3.6 and later supports kwargs that remember their order,
    # so only have this kwarg signature on Python 3.6 and above
    def seq(*parsers, **kw_parsers):
        """
        Takes a list of list of parsers, runs them in order,
        and collects their individuals results in a list
        """
        if not parsers and not kw_parsers:
            return success([])

        if parsers and kw_parsers:
            raise ValueError("Use either positional arguments or keyword arguments with seq, not both")

        if parsers:
            @Parser
            def seq_parser(stream, index):
                result = None
                values = []
                for parser in parsers:
                    result = parser(stream, index).aggregate(result)
                    if not result.status:
                        return result
                    index = result.index
                    values.append(result.value)
                return Result.success(index, values).aggregate(result)

            return seq_parser
        else:
            @Parser
            def seq_kwarg_parser(stream, index):
                result = None
                values = {}
                for name, parser in kw_parsers.items():
                    result = parser(stream, index).aggregate(result)
                    if not result.status:
                        return result
                    index = result.index
                    values[name] = result.value
                return Result.success(index, values).aggregate(result)

            return seq_kwarg_parser

else:
    def seq(*parsers):
        """
        Takes a list of list of parsers, runs them in order,
        and collects their individuals results in a list
        """
        if not parsers:
            return success([])

        @Parser
        def seq_parser(stream, index):
            result = None
            values = []
            for parser in parsers:
                result = parser(stream, index).aggregate(result)
                if not result.status:
                    return result
                index = result.index
                values.append(result.value)

            return Result.success(index, values).aggregate(result)

        return seq_parser


# combinator syntax
def generate(fn):
    if isinstance(fn, str):
        return lambda f: generate(f).desc(fn)

    @Parser
    @wraps(fn)
    def generated(stream, index):
        # start up the generator
        iterator = fn()

        result = None
        value = None
        try:
            while True:
                next_parser = iterator.send(value)
                result = next_parser(stream, index).aggregate(result)
                if not result.status:
                    return result
                value = result.value
                index = result.index
        except StopIteration as stop:
            returnVal = stop.value
            if isinstance(returnVal, Parser):
                return returnVal(stream, index).aggregate(result)

            return Result.success(index, returnVal).aggregate(result)

    return generated


index = Parser(lambda _, index: Result.success(index, index))
line_info = Parser(lambda stream, index: Result.success(index, line_info_at(stream, index)))


def success(val):
    return Parser(lambda _, index: Result.success(index, val))


def fail(expected):
    return Parser(lambda _, index: Result.failure(index, expected))


def string(s):
    slen = len(s)

    @Parser
    def string_parser(stream, index):
        if stream[index:index + slen] == s:
            return Result.success(index + slen, s)
        else:
            return Result.failure(index, s)

    return string_parser


def regex(exp, flags=0):
    if isinstance(exp, str):
        exp = re.compile(exp, flags)

    @Parser
    def regex_parser(stream, index):
        match = exp.match(stream, index)
        if match:
            return Result.success(match.end(), match.group(0))
        else:
            return Result.failure(index, exp.pattern)

    return regex_parser


def test_item(func, description):
    @Parser
    def test_item_parser(stream, index):
        if index < len(stream):
            item = stream[index]
            if func(item):
                return Result.success(index + 1, item)
        return Result.failure(index, description)

    return test_item_parser


def test_char(func, description):
    # Implementation is identical to test_item
    return test_item(func, description)


def match_item(item, description=None):
    if description is None:
        description = str(item)
    return test_item(lambda i: item == i, description)


def string_from(*strings):
    # Sort longest first, so that overlapping options work correctly
    return alt(*map(string, sorted(strings, key=len, reverse=True)))


def char_from(string):
    return test_char(lambda c: c in string, "[" + string + "]")


any_char = test_char(lambda c: True, "any character")

whitespace = regex(r'\s+')

letter = test_char(lambda c: c.isalpha(), 'a letter')

digit = test_char(lambda c: c.isdigit(), 'a digit')

decimal_digit = char_from("0123456789")


@Parser
def eof(stream, index):
    if index >= len(stream):
        return Result.success(index, None)
    else:
        return Result.failure(index, 'EOF')
