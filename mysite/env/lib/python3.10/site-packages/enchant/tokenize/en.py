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

    enchant.tokenize.en:    Tokenizer for the English language

    This module implements a PyEnchant text tokenizer for the English
    language, based on very simple rules.

"""

import unicodedata

import enchant.tokenize


class tokenize(enchant.tokenize.tokenize):  # noqa: N801
    """Iterator splitting text into words, reporting position.

    This iterator takes a text string as input, and yields tuples
    representing each distinct word found in the text.  The tuples
    take the form:

        (<word>,<pos>)

    Where <word> is the word string found and <pos> is the position
    of the start of the word within the text.

    The optional argument <valid_chars> may be used to specify a
    list of additional characters that can form part of a word.
    By default, this list contains only the apostrophe ('). Note that
    these characters cannot appear at the start or end of a word.
    """

    _DOC_ERRORS = ["pos", "pos"]

    def __init__(self, text, valid_chars=None):
        self._valid_chars = valid_chars
        self._text = text
        self._offset = 0
        # Select proper implementation of self._consume_alpha.
        # 'text' isn't necessarily a string (it could be e.g. a mutable array)
        # so we can't use isinstance(text, str) to detect unicode.
        # Instead we typetest the first character of the text.
        # If there's no characters then it doesn't matter what implementation
        # we use since it won't be called anyway.
        try:
            char1 = text[0]
        except IndexError:
            self._initialize_for_binary()
        else:
            if isinstance(char1, str):
                self._initialize_for_unicode()
            else:
                self._initialize_for_binary()

    def _initialize_for_binary(self):
        self._consume_alpha = self._consume_alpha_b
        if self._valid_chars is None:
            self._valid_chars = ("'",)

    def _initialize_for_unicode(self):
        self._consume_alpha = self._consume_alpha_u
        if self._valid_chars is None:
            # XXX TODO: this doesn't seem to work correctly with the
            # MySpell provider, disabling for now.
            # Allow unicode typographic apostrophe
            # self._valid_chars = (u"'",u"\u2019")
            self._valid_chars = ("'",)

    def _consume_alpha_b(self, text, offset):
        """Consume an alphabetic character from the given bytestring.

        Given a bytestring and the current offset, this method returns
        the number of characters occupied by the next alphabetic character
        in the string.  Non-ASCII bytes are interpreted as utf-8 and can
        result in multiple characters being consumed.
        """
        assert offset < len(text)
        if text[offset].isalpha():
            return 1
        elif text[offset] >= "\x80":
            return self._consume_alpha_utf8(text, offset)
        return 0

    def _consume_alpha_utf8(self, text, offset):
        """Consume a sequence of utf8 bytes forming an alphabetic character."""
        incr = 2
        u = ""
        while not u and incr <= 4:
            try:
                try:
                    #  In the common case this will be a string
                    u = text[offset : offset + incr].decode("utf8")
                except AttributeError:
                    #  Looks like it was e.g. a mutable char array.
                    try:
                        s = text[offset : offset + incr].tostring()
                    except AttributeError:
                        s = "".join([c for c in text[offset : offset + incr]])
                    u = s.decode("utf8")
            except UnicodeDecodeError:
                incr += 1
        if not u:
            return 0
        if u.isalpha():
            return incr
        if unicodedata.category(u)[0] == "M":
            return incr
        return 0

    def _consume_alpha_u(self, text, offset):
        """Consume an alphabetic character from the given unicode string.

        Given a unicode string and the current offset, this method returns
        the number of characters occupied by the next alphabetic character
        in the string.  Trailing combining characters are consumed as a
        single letter.
        """
        assert offset < len(text)
        incr = 0
        if text[offset].isalpha():
            incr = 1
            while offset + incr < len(text):
                if unicodedata.category(text[offset + incr])[0] != "M":
                    break
                incr += 1
        return incr

    def next(self):
        text = self._text
        offset = self._offset
        while offset < len(text):
            # Find start of next word (must be alpha)
            while offset < len(text):
                incr = self._consume_alpha(text, offset)
                if incr:
                    break
                offset += 1
            cur_pos = offset
            # Find end of word using, allowing valid_chars
            while offset < len(text):
                incr = self._consume_alpha(text, offset)
                if not incr:
                    if text[offset] in self._valid_chars:
                        incr = 1
                    else:
                        break
                offset += incr
            # Return if word isn't empty
            if cur_pos != offset:
                # Make sure word doesn't end with a valid_char
                while text[offset - 1] in self._valid_chars:
                    offset = offset - 1
                self._offset = offset
                return (text[cur_pos:offset], cur_pos)
        self._offset = offset
        raise StopIteration()
