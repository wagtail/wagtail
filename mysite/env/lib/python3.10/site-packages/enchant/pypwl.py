# pyenchant
#
# Copyright (C) 2004-2011 Ryan Kelly
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

pypwl:  pure-python personal word list in the style of Enchant
==============================================================

This module provides a pure-python version of the personal word list
functionality found in the spellchecking package Enchant.  While the
same effect can be achieved (with better performance) using the python
bindings for Enchant, it requires a C extension.

This pure-python implementation uses the same algorithm but without any
external dependencies or C code (in fact, it was the author's original
prototype for the C version found in Enchant).

"""


import os
import warnings


class Trie:
    """Class implementing a trie-based dictionary of words.

    A Trie is a recursive data structure storing words by their prefix.
    "Fuzzy matching" can be done by allowing a certain number of missteps
    when traversing the Trie.
    """

    def __init__(self, words=()):
        self._eos = False  # whether I am the end of a word
        self._keys = {}  # letters at this level of the trie
        for w in words:
            self.insert(w)

    def insert(self, word):
        if word == "":
            self._eos = True
        else:
            key = word[0]
            try:
                subtrie = self[key]
            except KeyError:
                subtrie = Trie()
                self[key] = subtrie
            subtrie.insert(word[1:])

    def remove(self, word):
        if word == "":
            self._eos = False
        else:
            key = word[0]
            try:
                subtrie = self[key]
            except KeyError:
                pass
            else:
                subtrie.remove(word[1:])

    def search(self, word, nerrs=0):
        """Search for the given word, possibly making errors.

        This method searches the trie for the given <word>, making
        precisely <nerrs> errors.  It returns a list of words found.
        """
        res = []
        # Terminate if we've run out of errors
        if nerrs < 0:
            return res
        # Precise match at the end of the word
        if nerrs == 0 and word == "":
            if self._eos:
                res.append("")
        # Precisely match word[0]
        try:
            subtrie = self[word[0]]
            subres = subtrie.search(word[1:], nerrs)
            for w in subres:
                w2 = word[0] + w
                if w2 not in res:
                    res.append(w2)
        except (IndexError, KeyError):
            pass
        # match with deletion of word[0]
        try:
            subres = self.search(word[1:], nerrs - 1)
            for w in subres:
                if w not in res:
                    res.append(w)
        except (IndexError,):
            pass
        # match with insertion before word[0]
        try:
            for k in self._keys:
                subres = self[k].search(word, nerrs - 1)
                for w in subres:
                    w2 = k + w
                    if w2 not in res:
                        res.append(w2)
        except (IndexError, KeyError):
            pass
        # match on substitution of word[0]
        try:
            for k in self._keys:
                subres = self[k].search(word[1:], nerrs - 1)
                for w in subres:
                    w2 = k + w
                    if w2 not in res:
                        res.append(w2)
        except (IndexError, KeyError):
            pass
        # All done!
        return res

    search._DOC_ERRORS = ["nerrs"]

    def __getitem__(self, key):
        return self._keys[key]

    def __setitem__(self, key, val):
        self._keys[key] = val

    def __iter__(self):
        if self._eos:
            yield ""
        for k in self._keys:
            for w2 in self._keys[k]:
                yield k + w2


class PyPWL:
    """Pure-python implementation of Personal Word List dictionary.
    This class emulates the PWL objects provided by PyEnchant, but
    implemented purely in python.
    """

    def __init__(self, pwl=None):
        """PyPWL constructor.
        This method takes as its only argument the name of a file
        containing the personal word list, one word per line.  Entries
        will be read from this file, and new entries will be written to
        it automatically.

        If <pwl> is not specified or None, the list is maintained in
        memory only.
        """
        self.provider = None
        self._words = Trie()
        if pwl is not None:
            self.pwl = os.path.abspath(pwl)
            self.tag = self.pwl
            pwl_f = open(pwl)
            for ln in pwl_f:
                word = ln.strip()
                self.add_to_session(word)
            pwl_f.close()
        else:
            self.pwl = None
            self.tag = "PyPWL"

    def check(self, word):
        """Check spelling of a word.

        This method takes a word in the dictionary language and returns
        True if it is correctly spelled, and false otherwise.
        """
        res = self._words.search(word)
        return bool(res)

    def suggest(self, word):
        """Suggest possible spellings for a word.

        This method tries to guess the correct spelling for a given
        word, returning the possibilities in a list.
        """
        limit = 10
        maxdepth = 5
        # Iterative deepening until we get enough matches
        depth = 0
        res = self._words.search(word, depth)
        while len(res) < limit and depth < maxdepth:
            depth += 1
            for w in self._words.search(word, depth):
                if w not in res:
                    res.append(w)
        # Limit number of suggs
        return res[:limit]

    def add(self, word):
        """Add a word to the user's personal dictionary.
        For a PWL, this means appending it to the file.
        """
        if self.pwl is not None:
            pwl_f = open(self.pwl, "a")
            pwl_f.write("%s\n" % (word.strip(),))
            pwl_f.close()
        self.add_to_session(word)

    def add_to_pwl(self, word):
        """Add a word to the user's personal dictionary.
        For a PWL, this means appending it to the file.
        """
        warnings.warn(
            "PyPWL.add_to_pwl is deprecated, please use PyPWL.add",
            category=DeprecationWarning,
            stacklevel=2,
        )
        self.add(word)

    def remove(self, word):
        """Add a word to the user's personal exclude list."""
        # There's no exclude list for a stand-alone PWL.
        # Just remove it from the list.
        self._words.remove(word)
        if self.pwl is not None:
            pwl_f = open(self.pwl, "wt")
            for w in self._words:
                pwl_f.write("%s\n" % (w.strip(),))
            pwl_f.close()

    def add_to_session(self, word):
        """Add a word to the session list."""
        self._words.insert(word)

    def store_replacement(self, mis, cor):
        """Store a replacement spelling for a miss-spelled word.

        This method makes a suggestion to the spellchecking engine that the
        miss-spelled word <mis> is in fact correctly spelled as <cor>.  Such
        a suggestion will typically mean that <cor> appears early in the
        list of suggested spellings offered for later instances of <mis>.
        """
        # Too much work for this simple spellchecker
        pass

    store_replacement._DOC_ERRORS = ["mis", "mis"]

    def is_added(self, word):
        """Check whether a word is in the personal word list."""
        return self.check(word)

    def is_removed(self, word):
        """Check whether a word is in the personal exclude list."""
        return False

    #  No-op methods to support internal use as a Dict() replacement

    def _check_this(self, msg):
        pass

    def _free(self):
        pass
