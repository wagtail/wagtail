# pyenchant
#
# Copyright (C) 2004-2009, Ryan Kelly
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#
# In addition, as a special exception, you are
# given permission to link the code of this program with
# non-LGPL Spelling Provider libraries (eg: a MSFT Office
# spell checker backend) and distribute linked combinations including
# the two.  You must obey the GNU Lesser General Public License in all
# respects for all of the code used other than said providers.  If you modify
# this file, you may extend this exception to your version of the
# file, but you are not obligated to do so.  If you do not wish to
# do so, delete this exception statement from your version.
#
"""

enchant.tokenize:    String tokenization functions for PyEnchant
================================================================

An important task in spellchecking is breaking up large bodies of
text into their constituent words, each of which is then checked
for correctness.  This package provides Python functions to split
strings into words according to the rules of a particular language.

Each tokenization function accepts a string as its only positional
argument, and returns an iterator that yields tuples of the following
form, one for each word found::

    (<word>,<pos>)

The meanings of these fields should be clear: <word> is the word
that was found and <pos> is the position within the text at which
the word began (zero indexed, of course).  The function will work
on any string-like object that supports array-slicing; in particular
character-array objects from the 'array' module may be used.

The iterator also provides the attribute 'offset' which gives the current
position of the tokenizer inside the string being split, and the method
'set_offset' for manually adjusting this position.  This can be used for
example if the string's contents have changed during the tokenization
process.

To obtain an appropriate tokenization function for the language
identified by <tag>, use the function 'get_tokenizer(tag)'::

    tknzr = get_tokenizer("en_US")
    for (word,pos) in tknzr("text to be tokenized goes here")
        do_something(word)

This library is designed to be easily extendible by third-party
authors.  To register a tokenization function for the language
<tag>, implement it as the function 'tokenize' within the
module enchant.tokenize.<tag>.  The 'get_tokenizer' function
will automatically detect it.  Note that the underscore must be
used as the tag component separator in this case, in order to
form a valid python module name. (e.g. "en_US" rather than "en-US")

Currently, a tokenizer has only been implemented for the English
language.  Based on the author's limited experience, this should
be at least partially suitable for other languages.

This module also provides various implementations of "Chunkers" and
"Filters".  These classes are designed to make it easy to work with
text in a variety of common formats, by detecting and excluding parts
of the text that don't need to be checked.

A Chunker is a class designed to break a body of text into large chunks
of checkable content; for example the HTMLChunker class extracts the
text content from all HTML tags but excludes the tags themselves.
A Filter is a class designed to skip individual words during the checking
process; for example the URLFilter class skips over any words that
have the format of a URL.

For example, to spellcheck an HTML document it is necessary to split the
text into chunks based on HTML tags, and to filter out common word forms
such as URLs and WikiWords.  This would look something like the following::

    tknzr = get_tokenizer("en_US",(HTMLChunker,),(URLFilter,WikiWordFilter)))

    text = "<html><body>the url is http://example.com</body></html>"
    for (word,pos) in tknzer(text):
        ...check each word and react accordingly...

"""
_DOC_ERRORS = [
    "pos",
    "pos",
    "tknzr",
    "URLFilter",
    "WikiWordFilter",
    "tkns",
    "tknzr",
    "pos",
    "tkns",
]

import re
import warnings
import array

from enchant.errors import TokenizerNotFoundError

#  For backwards-compatibility.  This will eventually be removed, but how
#  does one mark a module-level constant as deprecated?
Error = TokenizerNotFoundError


class tokenize:  # noqa: N801
    """Base class for all tokenizer objects.

    Each tokenizer must be an iterator and provide the 'offset'
    attribute as described in the documentation for this module.

    While tokenizers are in fact classes, they should be treated
    like functions, and so are named using lower_case rather than
    the CamelCase more traditional of class names.
    """

    _DOC_ERRORS = ["CamelCase"]

    def __init__(self, text):
        self._text = text
        self._offset = 0

    def __next__(self):
        return self.next()

    def next(self):
        raise NotImplementedError()

    def __iter__(self):
        return self

    def set_offset(self, offset, replaced=False):
        self._offset = offset

    def _get_offset(self):
        return self._offset

    def _set_offset(self, offset):
        msg = (
            "changing a tokenizers 'offset' attribute is deprecated;"
            " use the 'set_offset' method"
        )
        warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
        self.set_offset(offset)

    offset = property(_get_offset, _set_offset)


def get_tokenizer(tag=None, chunkers=None, filters=None):
    """Locate an appropriate tokenizer by language tag.

    This requires importing the function 'tokenize' from an appropriate
    module.  Modules tried are named after the language tag, tried in the
    following order:

        * the entire tag (e.g. "en_AU.py")
        * the base country code of the tag (e.g. "en.py")

    If the language tag is None, a default tokenizer (actually the English
    one) is returned.  It's unicode aware and should work OK for most
    latin-derived languages.

    If a suitable function cannot be found, raises TokenizerNotFoundError.

    If given and not None, 'chunkers' and 'filters' must be lists of chunker
    classes and filter classes respectively.  These will be applied to the
    tokenizer during creation.
    """
    if tag is None:
        tag = "en"
    # "filters" used to be the second argument.  Try to catch cases
    # where it is given positionally and issue a DeprecationWarning.
    if chunkers is not None and filters is None:
        chunkers = list(chunkers)
        if chunkers:
            try:
                chunkers_are_filters = issubclass(chunkers[0], Filter)
            except TypeError:
                pass
            else:
                if chunkers_are_filters:
                    msg = (
                        "passing 'filters' as a non-keyword argument "
                        "to get_tokenizer() is deprecated"
                    )
                    warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
                    filters = chunkers
                    chunkers = None
    # Ensure only '_' used as separator
    tag = tag.replace("-", "_")
    # First try the whole tag
    tk_func = _try_tokenizer(tag)
    if tk_func is None:
        # Try just the base
        base = tag.split("_")[0]
        tk_func = _try_tokenizer(base)
        if tk_func is None:
            msg = "No tokenizer found for language '%s'" % (tag,)
            raise TokenizerNotFoundError(msg)
    # Given the language-specific tokenizer, we now build up the
    # end result as follows:
    #    * chunk the text using any given chunkers in turn
    #    * begin with basic whitespace tokenization
    #    * apply each of the given filters in turn
    #    * apply language-specific rules
    tokenizer = basic_tokenize
    if chunkers is not None:
        chunkers = list(chunkers)
        for i in range(len(chunkers) - 1, -1, -1):
            tokenizer = wrap_tokenizer(chunkers[i], tokenizer)
    if filters is not None:
        for f in filters:
            tokenizer = f(tokenizer)
    tokenizer = wrap_tokenizer(tokenizer, tk_func)
    return tokenizer


get_tokenizer._DOC_ERRORS = ["py", "py"]


class empty_tokenize(tokenize):  # noqa: N801
    """Tokenizer class that yields no elements."""

    _DOC_ERRORS = []

    def __init__(self):
        super().__init__("")

    def next(self):
        raise StopIteration()


class unit_tokenize(tokenize):  # noqa: N801
    """Tokenizer class that yields the text as a single token."""

    _DOC_ERRORS = []

    def __init__(self, text):
        super().__init__(text)
        self._done = False

    def next(self):
        if self._done:
            raise StopIteration()
        self._done = True
        return (self._text, 0)


class basic_tokenize(tokenize):  # noqa: N801
    """Tokenizer class that performs very basic word-finding.

    This tokenizer does the most basic thing that could work - it splits
    text into words based on whitespace boundaries, and removes basic
    punctuation symbols from the start and end of each word.
    """

    _DOC_ERRORS = []

    # Chars to remove from start/end of words
    strip_from_start = '"' + "'`(["
    strip_from_end = '"' + "'`]).!,?;:"

    def next(self):
        text = self._text
        offset = self._offset
        while True:
            if offset >= len(text):
                break
            # Find start of next word
            while offset < len(text) and text[offset].isspace():
                offset += 1
            s_pos = offset
            # Find end of word
            while offset < len(text) and not text[offset].isspace():
                offset += 1
            e_pos = offset
            self._offset = offset
            # Strip chars from font/end of word
            while s_pos < len(text) and text[s_pos] in self.strip_from_start:
                s_pos += 1
            while 0 < e_pos and text[e_pos - 1] in self.strip_from_end:
                e_pos -= 1
            # Return if word isn't empty
            if s_pos < e_pos:
                return (text[s_pos:e_pos], s_pos)
        raise StopIteration()


def _try_tokenizer(mod_name):
    """Look for a tokenizer in the named module.

    Returns the function if found, None otherwise.
    """
    mod_base = "enchant.tokenize."
    func_name = "tokenize"
    mod_name = mod_base + mod_name
    try:
        mod = __import__(mod_name, globals(), {}, func_name)
        return getattr(mod, func_name)
    except ImportError:
        return None


def wrap_tokenizer(tk1, tk2):
    """Wrap one tokenizer inside another.

    This function takes two tokenizer functions 'tk1' and 'tk2',
    and returns a new tokenizer function that passes the output
    of tk1 through tk2 before yielding it to the calling code.
    """
    # This logic is already implemented in the Filter class.
    # We simply use tk2 as the _split() method for a filter
    # around tk1.
    tkw = Filter(tk1)
    tkw._split = tk2
    return tkw


wrap_tokenizer._DOC_ERRORS = ["tk", "tk", "tk", "tk"]


class Chunker(tokenize):
    """Base class for text chunking functions.

    A chunker is designed to chunk text into large blocks of tokens.  It
    has the same interface as a tokenizer but is for a different purpose.
    """

    pass


class Filter:
    """Base class for token filtering functions.

    A filter is designed to wrap a tokenizer (or another filter) and do
    two things:

      * skip over tokens
      * split tokens into sub-tokens

    Subclasses have two basic options for customising their behaviour.  The
    method _skip(word) may be overridden to return True for words that
    should be skipped, and false otherwise.  The method _split(word) may
    be overridden as tokenization function that will be applied to further
    tokenize any words that aren't skipped.
    """

    def __init__(self, tokenizer):
        """Filter class constructor."""
        self._tokenizer = tokenizer

    def __call__(self, *args, **kwds):
        tkn = self._tokenizer(*args, **kwds)
        return self._TokenFilter(tkn, self._skip, self._split)

    def _skip(self, word):
        """Filter method for identifying skippable tokens.

        If this method returns true, the given word will be skipped by
        the filter.  This should be overridden in subclasses to produce the
        desired functionality.  The default behaviour is not to skip any words.
        """
        return False

    def _split(self, word):
        """Filter method for sub-tokenization of tokens.

        This method must be a tokenization function that will split the
        given word into sub-tokens according to the needs of the filter.
        The default behaviour is not to split any words.
        """
        return unit_tokenize(word)

    class _TokenFilter:
        """Private inner class implementing the tokenizer-wrapping logic.

        This might seem convoluted, but we're trying to create something
        akin to a meta-class - when Filter(tknzr) is called it must return
        a *callable* that can then be applied to a particular string to
        perform the tokenization.  Since we need to manage a lot of state
        during tokenization, returning a class is the best option.
        """

        _DOC_ERRORS = ["tknzr"]

        def __init__(self, tokenizer, skip, split):
            self._skip = skip
            self._split = split
            self._tokenizer = tokenizer
            # for managing state of sub-tokenization
            self._curtok = empty_tokenize()
            self._curword = ""
            self._curpos = 0

        def __iter__(self):
            return self

        def __next__(self):
            return self.next()

        def next(self):
            # Try to get the next sub-token from word currently being split.
            # If unavailable, move on to the next word and try again.
            while True:
                try:
                    (word, pos) = next(self._curtok)
                    return (word, pos + self._curpos)
                except StopIteration:
                    (word, pos) = next(self._tokenizer)
                    while self._skip(self._to_string(word)):
                        (word, pos) = next(self._tokenizer)
                    self._curword = word
                    self._curpos = pos
                    self._curtok = self._split(word)

        def _to_string(self, word):
            if type(word) is array.array:
                if word.typecode == "u":
                    return word.tounicode()
                elif word.typecode == "c":
                    return word.tostring()
            return word

        # Pass on access to 'offset' to the underlying tokenizer.
        def _get_offset(self):
            return self._tokenizer.offset

        def _set_offset(self, offset):
            msg = (
                "changing a tokenizers 'offset' attribute is deprecated;"
                " use the 'set_offset' method"
            )
            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            self.set_offset(offset)

        offset = property(_get_offset, _set_offset)

        def set_offset(self, val, replaced=False):
            old_offset = self._tokenizer.offset
            self._tokenizer.set_offset(val, replaced=replaced)
            # If we move forward within the current word, also set on _curtok.
            # Otherwise, throw away _curtok and set to empty iterator.
            keep_curtok = True
            curtok_offset = val - self._curpos
            if old_offset > val:
                keep_curtok = False
            if curtok_offset < 0:
                keep_curtok = False
            if curtok_offset >= len(self._curword):
                keep_curtok = False
            if keep_curtok and not replaced:
                self._curtok.set_offset(curtok_offset)
            else:
                self._curtok = empty_tokenize()
                self._curword = ""
                self._curpos = 0


#  Pre-defined chunkers and filters start here


class URLFilter(Filter):
    r"""Filter skipping over URLs.
    This filter skips any words matching the following regular expression:

           ^[a-zA-Z]+:\/\/[^\s].*

    That is, any words that are URLs.
    """
    _DOC_ERRORS = ["zA"]
    _pattern = re.compile(r"^[a-zA-Z]+:\/\/[^\s].*")

    def _skip(self, word):
        if self._pattern.match(word):
            return True
        return False


class WikiWordFilter(Filter):
    r"""Filter skipping over WikiWords.
    This filter skips any words matching the following regular expression:

           ^([A-Z]\w+[A-Z]+\w+)

    That is, any words that are WikiWords.
    """
    _pattern = re.compile(r"^([A-Z]\w+[A-Z]+\w+)")

    def _skip(self, word):
        if self._pattern.match(word):
            return True
        return False


class EmailFilter(Filter):
    r"""Filter skipping over email addresses.
    This filter skips any words matching the following regular expression:

           ^.+@[^\.].*\.[a-z]{2,}$

    That is, any words that resemble email addresses.
    """
    _pattern = re.compile(r"^.+@[^\.].*\.[a-z]{2,}$")

    def _skip(self, word):
        if self._pattern.match(word):
            return True
        return False


class MentionFilter(Filter):
    r"""Filter skipping over @mention.
    This filter skips any words matching the following regular expression:

           (\A|\s)@(\w+)

    That is, any words that are @mention.
    """
    _DOC_ERRORS = ["zA"]
    _pattern = re.compile(r"(\A|\s)@(\w+)")

    def _skip(self, word):
        if self._pattern.match(word):
            return True
        return False


class HashtagFilter(Filter):
    r"""Filter skipping over #hashtag.
    This filter skips any words matching the following regular expression:

           (\A|\s)#(\w+)

    That is, any words that are #hashtag.
    """
    _DOC_ERRORS = ["zA"]
    _pattern = re.compile(r"(\A|\s)#(\w+)")

    def _skip(self, word):
        if self._pattern.match(word):
            return True
        return False


class HTMLChunker(Chunker):
    """Chunker for breaking up HTML documents into chunks of checkable text.

    The operation of this chunker is very simple - anything between a "<"
    and a ">" will be ignored.  Later versions may improve the algorithm
    slightly.
    """

    def next(self):
        text = self._text
        offset = self.offset
        while True:
            if offset >= len(text):
                break
            #  Skip to the end of the current tag, if any.
            if text[offset] == "<":
                maybe_tag = offset
                if self._is_tag(text, offset):
                    while text[offset] != ">":
                        offset += 1
                        if offset == len(text):
                            offset = maybe_tag + 1
                            break
                    else:
                        offset += 1
                else:
                    offset = maybe_tag + 1
            s_pos = offset
            #  Find the start of the next tag.
            while offset < len(text) and text[offset] != "<":
                offset += 1
            self._offset = offset
            # Return if chunk isn't empty
            if s_pos < offset:
                return (text[s_pos:offset], s_pos)
        raise StopIteration()

    def _is_tag(self, text, offset):
        if offset + 1 < len(text):
            if text[offset + 1].isalpha():
                return True
            if text[offset + 1] == "/":
                return True
        return False


# TODO: LaTeXChunker
