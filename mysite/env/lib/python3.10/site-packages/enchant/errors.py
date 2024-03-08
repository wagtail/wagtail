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
enchant.errors:  Error class definitions for the enchant library
================================================================

All error classes are defined in this separate sub-module, so that they
can safely be imported without causing circular dependencies.

"""


class Error(Exception):
    """Base exception class for the enchant module."""

    pass


class DictNotFoundError(Error):
    """Exception raised when a requested dictionary could not be found."""

    pass


class TokenizerNotFoundError(Error):
    """Exception raised when a requested tokenizer could not be found."""

    pass


class DefaultLanguageNotFoundError(Error):
    """Exception raised when a default language could not be found."""

    pass
