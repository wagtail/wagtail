# pyenchant
#
# Copyright (C) 2004-2008 Ryan Kelly
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

enchant.utils:    Misc utilities for the enchant package
========================================================

This module provides miscellaneous utilities for use with the
enchant spellchecking package.  Currently available functionality
includes:

    * functions for dealing with locale/language settings
    * ability to list supporting data files (win32 only)
    * functions for bundling supporting data files from a build

"""

from enchant.errors import Error
import locale


def levenshtein(s1, s2):
    """Calculate the Levenshtein distance between two strings.

    This is straight from Wikipedia.
    """
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if not s1:
        return len(s2)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def trim_suggestions(word, suggs, maxlen, calcdist=None):
    """Trim a list of suggestions to a maximum length.

    If the list of suggested words is too long, you can use this function
    to trim it down to a maximum length.  It tries to keep the "best"
    suggestions based on similarity to the original word.

    If the optional "calcdist" argument is provided, it must be a callable
    taking two words and returning the distance between them.  It will be
    used to determine which words to retain in the list.  The default is
    a simple Levenshtein distance.
    """
    if calcdist is None:
        calcdist = levenshtein
    decorated = [(calcdist(word, s), s) for s in suggs]
    decorated.sort()
    return [s for (l, s) in decorated[:maxlen]]


def get_default_language(default=None):
    """Determine the user's default language, if possible.

    This function uses the 'locale' module to try to determine
    the user's preferred language.  The return value is as
    follows:

        * if a locale is available for the LC_MESSAGES category,
          that language is used
        * if a default locale is available, that language is used
        * if the keyword argument <default> is given, it is used
        * if nothing else works, None is returned

    Note that determining the user's language is in general only
    possible if they have set the necessary environment variables
    on their system.
    """
    try:
        tag = locale.getlocale()[0]
        if tag is None:
            tag = locale.getdefaultlocale()[0]
            if tag is None:
                raise Error("No default language available")
        return tag
    except Exception:
        pass
    return default


get_default_language._DOC_ERRORS = ["LC"]
