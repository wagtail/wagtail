# pyenchant
#
# Copyright (C) 2004-2008, Ryan Kelly
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

enchant.checker:  High-level spellchecking functionality
========================================================

This package is designed to host higher-level spellchecking functionality
than is available in the base enchant package.  It should make writing
applications that follow common usage idioms significantly easier.

The most useful class is SpellChecker, which implements a spellchecking
loop over a block of text.  It is capable of modifying the text in-place
if given an array of characters to work with.

This package also contains several interfaces to the SpellChecker class,
such as a wxPython GUI dialog and a command-line interface.

"""

import array
import warnings

import enchant
from enchant.errors import (
    DefaultLanguageNotFoundError,
    DictNotFoundError,
    TokenizerNotFoundError,
)
from enchant.tokenize import get_tokenizer
from enchant.utils import get_default_language


class SpellChecker:
    """Class implementing stateful spellchecking behaviour.

    This class is designed to implement a spell-checking loop over
    a block of text, correcting/ignoring/replacing words as required.
    This loop is implemented using an iterator paradigm so it can be
    embedded inside other loops of control.

    The SpellChecker object is stateful, and the appropriate methods
    must be called to alter its state and affect the progress of
    the spell checking session.  At any point during the checking
    session, the attribute 'word' will hold the current erroneously
    spelled word under consideration.  The action to take on this word
    is determined by calling methods such as 'replace', 'replace_always'
    and 'ignore_always'.  Once this is done, calling 'next' advances
    to the next misspelled word.

    As a quick (and rather silly) example, the following code replaces
    each misspelled word with the string "SPAM":

        >>> text = "This is sme text with a fw speling errors in it."
        >>> chkr = SpellChecker("en_US",text)
        >>> for err in chkr:
        ...   err.replace("SPAM")
        ...
        >>> chkr.get_text()
        'This is SPAM text with a SPAM SPAM errors in it.'
        >>>

    Internally, the SpellChecker always works with arrays of (possibly
    unicode) character elements.  This allows the in-place modification
    of the string as it is checked, and is the closest thing Python has
    to a mutable string.  The text can be set as any of a normal string,
    unicode string, character array or unicode character array. The
    'get_text' method will return the modified array object if an
    array is used, or a new string object if a string it used.

    Words input to the SpellChecker may be either plain strings or
    unicode objects.  They will be converted to the same type as the
    text being checked, using python's default encoding/decoding
    settings.

    If using an array of characters with this object and the
    array is modified outside of the spellchecking loop, use the
    'set_offset' method to reposition the internal loop pointer
    to make sure it doesn't skip any words.

    """

    _DOC_ERRORS = ["sme", "fw", "speling", "chkr", "chkr", "chkr"]

    def __init__(
        self, lang=None, text=None, tokenize=None, chunkers=None, filters=None
    ):
        """Constructor for the SpellChecker class.

        SpellChecker objects can be created in two ways, depending on
        the nature of the first argument.  If it is a string, it
        specifies a language tag from which a dictionary is created.
        Otherwise, it must be an enchant Dict object to be used.

        Optional keyword arguments are:

            * text:  to set the text to be checked at creation time
            * tokenize:  a custom tokenization function to use
            * chunkers:  a list of chunkers to apply during tokenization
            * filters:  a list of filters to apply during tokenization

        If <tokenize> is not given and the first argument is a Dict,
        its 'tag' attribute must be a language tag so that a tokenization
        function can be created automatically.  If this attribute is missing
        the user's default language will be used.
        """
        if lang is None:
            lang = get_default_language()
        if isinstance(lang, (str, bytes)):
            try:
                dict = enchant.Dict(lang)
            except DictNotFoundError:
                raise DefaultLanguageNotFoundError(lang) from None
        else:
            dict = lang
            try:
                lang = dict.tag
            except AttributeError:
                lang = get_default_language()
        if lang is None:
            raise DefaultLanguageNotFoundError from None
        self.lang = lang
        self.dict = dict
        if tokenize is None:
            try:
                tokenize = get_tokenizer(lang, chunkers, filters)
            except TokenizerNotFoundError:
                # Fall back to default tokenization if no match for 'lang'
                tokenize = get_tokenizer(None, chunkers, filters)
        self._tokenize = tokenize

        self.word = None
        self.wordpos = None
        self._ignore_words = {}
        self._replace_words = {}
        # Default to the empty string as the text to be checked
        self._text = array.array("u")
        self._use_tostring = False
        self._tokens = iter([])

        if text is not None:
            self.set_text(text)

    def __iter__(self):
        """Each SpellChecker object is its own iterator"""
        return self

    def set_text(self, text):
        """Set the text to be spell-checked.

        This method must be called, or the 'text' argument supplied
        to the constructor, before calling the 'next()' method.
        """
        # Convert to an array object if necessary
        if isinstance(text, (str, bytes)):
            if type(text) is str:
                self._text = array.array("u", text)
            else:
                self._text = array.array("c", text)
            self._use_tostring = True
        else:
            self._text = text
            self._use_tostring = False
        self._tokens = self._tokenize(self._text)

    def get_text(self):
        """Return the spell-checked text."""
        if self._use_tostring:
            return self._array_to_string(self._text)
        return self._text

    def _array_to_string(self, text):
        """Format an internal array as a standard string."""
        if text.typecode == "u":
            return text.tounicode()
        return text.tostring()

    def wants_unicode(self):
        """Check whether the checker wants unicode strings.

        This method will return True if the checker wants unicode strings
        as input, False if it wants normal strings.  It's important to
        provide the correct type of string to the checker.
        """
        if self._text.typecode == "u":
            return True
        return False

    def coerce_string(self, text, enc=None):
        """Coerce string into the required type.

        This method can be used to automatically ensure that strings
        are of the correct type required by this checker - either unicode
        or standard.  If there is a mismatch, conversion is done using
        python's default encoding unless another encoding is specified.
        """
        if self.wants_unicode():
            if not isinstance(text, str):
                if enc is None:
                    return text.decode()
                else:
                    return text.decode(enc)
            return text
        if not isinstance(text, bytes):
            if enc is None:
                return text.encode()
            else:
                return text.encode(enc)
        return text

    def __next__(self):
        return self.next()

    def next(self):
        """Process text up to the next spelling error.

        This method is designed to support the iterator protocol.
        Each time it is called, it will advance the 'word' attribute
        to the next spelling error in the text.  When no more errors
        are found, it will raise StopIteration.

        The method will always return self, so that it can be used
        sensibly in common idioms such as:

            for err in checker:
                err.do_something()

        """
        # Find the next spelling error.
        # The uncaught StopIteration from next(self._tokens)
        # will provide the StopIteration for this method
        while True:
            (word, pos) = next(self._tokens)
            # decode back to a regular string
            word = self._array_to_string(word)
            if self.dict.check(word):
                continue
            if word in self._ignore_words:
                continue
            self.word = word
            self.wordpos = pos
            if word in self._replace_words:
                self.replace(self._replace_words[word])
                continue
            break
        return self

    def replace(self, repl):
        """Replace the current erroneous word with the given string."""
        repl = self.coerce_string(repl)
        a_repl = array.array(self._text.typecode, repl)
        if repl:
            self.dict.store_replacement(self.word, repl)
        self._text[self.wordpos : self.wordpos + len(self.word)] = a_repl
        incr = len(repl) - len(self.word)
        self._tokens.set_offset(self._tokens.offset + incr, replaced=True)

    def replace_always(self, word, repl=None):
        """Always replace given word with given replacement.

        If a single argument is given, this is used to replace the
        current erroneous word.  If two arguments are given, that
        combination is added to the list for future use.
        """
        if repl is None:
            repl = word
            word = self.word
        repl = self.coerce_string(repl)
        word = self.coerce_string(word)
        self._replace_words[word] = repl
        if self.word == word:
            self.replace(repl)

    def ignore_always(self, word=None):
        """Add given word to list of words to ignore.

        If no word is given, the current erroneous word is added.
        """
        if word is None:
            word = self.word
        word = self.coerce_string(word)
        if word not in self._ignore_words:
            self._ignore_words[word] = True

    def add_to_personal(self, word=None):
        """Add given word to the personal word list.

        If no word is given, the current erroneous word is added.
        """
        warnings.warn(
            "SpellChecker.add_to_personal is deprecated, "
            "please use SpellChecker.add",
            category=DeprecationWarning,
            stacklevel=2,
        )
        self.add(word)

    def add(self, word=None):
        """Add given word to the personal word list.

        If no word is given, the current erroneous word is added.
        """
        if word is None:
            word = self.word
        self.dict.add(word)

    def suggest(self, word=None):
        """Return suggested spellings for the given word.

        If no word is given, the current erroneous word is used.
        """
        if word is None:
            word = self.word
        suggs = self.dict.suggest(word)
        return suggs

    def check(self, word):
        """Check correctness of the given word."""
        return self.dict.check(word)

    def set_offset(self, off, whence=0):
        """Set the offset of the tokenization routine.

        For more details on the purpose of the tokenization offset,
        see the documentation of the 'enchant.tokenize' module.
        The optional argument whence indicates the method by
        which to change the offset:

            * 0 (the default) treats <off> as an increment
            * 1 treats <off> as a distance from the start
            * 2 treats <off> as a distance from the end
        """
        if whence == 0:
            self._tokens.set_offset(self._tokens.offset + off)
        elif whence == 1:
            assert off > 0
            self._tokens.set_offset(off)
        elif whence == 2:
            assert off > 0
            self._tokens.set_offset(len(self._text) - 1 - off)
        else:
            raise ValueError("Invalid value for whence: %s" % (whence,))

    def leading_context(self, chars):
        """Get <chars> characters of leading context.

        This method returns up to <chars> characters of leading
        context - the text that occurs in the string immediately
        before the current erroneous word.
        """
        start = max(self.wordpos - chars, 0)
        context = self._text[start : self.wordpos]
        return self._array_to_string(context)

    def trailing_context(self, chars):
        """Get <chars> characters of trailing context.

        This method returns up to <chars> characters of trailing
        context - the text that occurs in the string immediately
        after the current erroneous word.
        """
        start = self.wordpos + len(self.word)
        end = min(start + chars, len(self._text))
        context = self._text[start:end]
        return self._array_to_string(context)
