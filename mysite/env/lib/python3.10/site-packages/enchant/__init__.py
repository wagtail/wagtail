# pyenchant
#
# Copyright (C) 2004-2011, Ryan Kelly
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
enchant:  Access to the enchant spellchecking library
=====================================================

This module provides several classes for performing spell checking
via the Enchant spellchecking library.  For more details on Enchant,
visit the project website:

    https://abiword.github.io/enchant/

Spellchecking is performed using 'Dict' objects, which represent
a language dictionary.  Their use is best demonstrated by a quick
example::

    >>> import enchant
    >>> d = enchant.Dict("en_US")   # create dictionary for US English
    >>> d.check("enchant")
    True
    >>> d.check("enchnt")
    False
    >>> d.suggest("enchnt")
    ['enchant', 'enchants', 'enchanter', 'penchant', 'incant', 'enchain', 'enchanted']

Languages are identified by standard string tags such as "en" (English)
and "fr" (French).  Specific language dialects can be specified by
including an additional code - for example, "en_AU" refers to Australian
English.  The later form is preferred as it is more widely supported.

To check whether a dictionary exists for a given language, the function
'dict_exists' is available.  Dictionaries may also be created using the
function 'request_dict'.

A finer degree of control over the dictionaries and how they are created
can be obtained using one or more 'Broker' objects.  These objects are
responsible for locating dictionaries for a specific language.

Note that unicode strings are expected throughout the entire API.
Bytestrings should not be passed into any function.

Errors that occur in this module are reported by raising subclasses
of 'Error'.

"""
_DOC_ERRORS = ["enchnt", "enchnt", "incant", "fr"]

__version__ = "3.2.2"

import os
import warnings

try:
    from enchant import _enchant as _e
except ImportError:
    if not os.environ.get("PYENCHANT_IGNORE_MISSING_LIB", False):
        raise
    _e = None

from enchant.errors import Error, DictNotFoundError
from enchant.utils import get_default_language
from enchant.pypwl import PyPWL


class ProviderDesc:
    """Simple class describing an Enchant provider.

    Each provider has the following information associated with it:

        * name:        Internal provider name (e.g. "aspell")
        * desc:        Human-readable description (e.g. "Aspell Provider")
        * file:        Location of the library containing the provider

    """

    _DOC_ERRORS = ["desc"]

    def __init__(self, name, desc, file):
        self.name = name
        self.desc = desc
        self.file = file

    def __str__(self):
        return "<Enchant: %s>" % self.desc

    def __repr__(self):
        return str(self)

    def __eq__(self, pd):
        """Equality operator on ProviderDesc objects."""
        return self.name == pd.name and self.desc == pd.desc and self.file == pd.file

    def __hash__(self):
        """Hash operator on ProviderDesc objects."""
        return hash(self.name + self.desc + self.file)


class _EnchantObject:
    """Base class for enchant objects.

    This class implements some general functionality for interfacing with
    the '_enchant' C-library in a consistent way.  All public objects
    from the 'enchant' module are subclasses of this class.

    All enchant objects have an attribute '_this' which contains the
    pointer to the underlying C-library object.  The method '_check_this'
    can be called to ensure that this point is not None, raising an
    exception if it is.
    """

    def __init__(self):
        """_EnchantObject constructor."""
        self._this = None
        #  To be importable when enchant C lib is missing, we need
        #  to create a dummy default broker.
        if _e is not None:
            self._init_this()

    def _check_this(self, msg=None):
        """Check that self._this is set to a pointer, rather than None."""
        if self._this is None:
            if msg is None:
                msg = "%s unusable: the underlying C-library object has been freed."
                msg = msg % (self.__class__.__name__,)
            raise Error(msg)

    def _init_this(self):
        """Initialise the underlying C-library object pointer."""
        raise NotImplementedError

    def _raise_error(self, default="Unspecified Error", eclass=Error):
        """Raise an exception based on available error messages.

        This method causes an Error to be raised.  Subclasses should
        override it to retrieve an error indication from the underlying
        API if possible.  If such a message cannot be retrieved, the
        argument value <default> is used.  The class of the exception
        can be specified using the argument <eclass>
        """
        raise eclass(default)

    _raise_error._DOC_ERRORS = ["eclass"]

    def __getstate__(self):
        """Customize pickling of PyEnchant objects.

        Since it's not safe for multiple objects to share the same C-library
        object, we make sure it's unset when pickling.
        """
        state = self.__dict__.copy()
        state["_this"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._init_this()


class Broker(_EnchantObject):
    """Broker object for the Enchant spellchecker.

    Broker objects are responsible for locating and managing dictionaries.
    Unless custom functionality is required, there is no need to use Broker
    objects directly. The 'enchant' module provides a default broker object
    so that 'Dict' objects can be created directly.

    The most important methods of this class include:

        * :py:meth:`dict_exists`:   check existence of a specific language dictionary
        * :py:meth:`request_dict`:  obtain a dictionary for specific language
        * :py:meth:`set_ordering`:  specify which dictionaries to try for a given language.

    """

    def __init__(self):
        """Broker object constructor.

        This method is the constructor for the 'Broker' object.  No
        arguments are required.
        """
        super().__init__()

    def _init_this(self):
        self._this = _e.broker_init()
        if not self._this:
            raise Error("Could not initialise an enchant broker.")
        self._live_dicts = {}

    def __del__(self):
        """Broker object destructor."""
        # Calling free() might fail if python is shutting down
        try:
            self._free()
        except (AttributeError, TypeError):
            pass

    def __getstate__(self):
        state = super().__getstate__()
        state.pop("_live_dicts")
        return state

    def _raise_error(self, default="Unspecified Error", eclass=Error):
        """Overrides _EnchantObject._raise_error to check broker errors."""
        err = _e.broker_get_error(self._this)
        if err == "" or err is None:
            raise eclass(default)
        raise eclass(err.decode())

    def _free(self):
        """Free system resource associated with a Broker object.

        This method can be called to free the underlying system resources
        associated with a Broker object.  It is called automatically when
        the object is garbage collected.  If called explicitly, the
        Broker and any associated Dict objects must no longer be used.
        """
        if self._this is not None:
            # During shutdown, this finalizer may be called before
            # some Dict finalizers.  Ensure all pointers are freed.
            for (dict, count) in list(self._live_dicts.items()):
                while count:
                    self._free_dict_data(dict)
                    count -= 1
            _e.broker_free(self._this)
            self._this = None

    def request_dict(self, tag=None):
        """Request a Dict object for the language specified by <tag>.

        This method constructs and returns a Dict object for the
        requested language.  'tag' should be a string of the appropriate
        form for specifying a language, such as "fr" (French) or "en_AU"
        (Australian English).  The existence of a specific language can
        be tested using the 'dict_exists' method.

        If <tag> is not given or is None, an attempt is made to determine
        the current language in use.  If this cannot be determined, Error
        is raised.

        .. note::
            this method is functionally equivalent to calling the Dict()
            constructor and passing in the <broker> argument.

        """
        return Dict(tag, self)

    request_dict._DOC_ERRORS = ["fr"]

    def _request_dict_data(self, tag):
        """Request raw C pointer data for a dictionary.

        This method call passes on the call to the C library, and does
        some internal bookkeeping.
        """
        self._check_this()
        new_dict = _e.broker_request_dict(self._this, tag.encode())
        if new_dict is None:
            e_str = "Dictionary for language '%s' could not be found\n"
            e_str += "Please check https://pyenchant.github.io/pyenchant/ for details"
            self._raise_error(e_str % (tag,), DictNotFoundError)
        if new_dict not in self._live_dicts:
            self._live_dicts[new_dict] = 1
        else:
            self._live_dicts[new_dict] += 1
        return new_dict

    def request_pwl_dict(self, pwl):
        """Request a Dict object for a personal word list.

        This method behaves as 'request_dict' but rather than returning
        a dictionary for a specific language, it returns a dictionary
        referencing a personal word list.  A personal word list is a file
        of custom dictionary entries, one word per line.
        """
        self._check_this()
        new_dict = _e.broker_request_pwl_dict(self._this, pwl.encode())
        if new_dict is None:
            e_str = "Personal Word List file '%s' could not be loaded"
            self._raise_error(e_str % (pwl,))
        if new_dict not in self._live_dicts:
            self._live_dicts[new_dict] = 1
        else:
            self._live_dicts[new_dict] += 1
        d = Dict(False)
        d._switch_this(new_dict, self)
        return d

    def _free_dict(self, dict):
        """Free memory associated with a dictionary.

        This method frees system resources associated with a Dict object.
        It is equivalent to calling the object's 'free' method.  Once this
        method has been called on a dictionary, it must not be used again.
        """
        self._free_dict_data(dict._this)
        dict._this = None
        dict._broker = None

    def _free_dict_data(self, dict):
        """Free the underlying pointer for a dict."""
        self._check_this()
        _e.broker_free_dict(self._this, dict)
        self._live_dicts[dict] -= 1
        if self._live_dicts[dict] == 0:
            del self._live_dicts[dict]

    def dict_exists(self, tag):
        """Check availability of a dictionary.

        This method checks whether there is a dictionary available for
        the language specified by 'tag'.  It returns True if a dictionary
        is available, and False otherwise.
        """
        self._check_this()
        val = _e.broker_dict_exists(self._this, tag.encode())
        return bool(val)

    def set_ordering(self, tag, ordering):
        """Set dictionary preferences for a language.

        The Enchant library supports the use of multiple dictionary programs
        and multiple languages.  This method specifies which dictionaries
        the broker should prefer when dealing with a given language.  'tag'
        must be an appropriate language specification and 'ordering' is a
        string listing the dictionaries in order of preference.  For example
        a valid ordering might be "aspell,myspell,ispell".
        The value of 'tag' can also be set to "*" to set a default ordering
        for all languages for which one has not been set explicitly.
        """
        self._check_this()
        _e.broker_set_ordering(self._this, tag.encode(), ordering.encode())

    def describe(self):
        """Return list of provider descriptions.

        This method returns a list of descriptions of each of the
        dictionary providers available.  Each entry in the list is a
        ProviderDesc object.
        """
        self._check_this()
        self.__describe_result = []
        _e.broker_describe(self._this, self.__describe_callback)
        return [ProviderDesc(*r) for r in self.__describe_result]

    def __describe_callback(self, name, desc, file):
        """Collector callback for dictionary description.

        This method is used as a callback into the _enchant function
        'enchant_broker_describe'.  It collects the given arguments in
        a tuple and appends them to the list '__describe_result'.
        """
        name = name.decode()
        desc = desc.decode()
        file = file.decode()
        self.__describe_result.append((name, desc, file))

    def list_dicts(self):
        """Return list of available dictionaries.

        This method returns a list of dictionaries available to the
        broker.  Each entry in the list is a two-tuple of the form:

            (tag,provider)

        where <tag> is the language lag for the dictionary and
        <provider> is a ProviderDesc object describing the provider
        through which that dictionary can be obtained.
        """
        self._check_this()
        self.__list_dicts_result = []
        _e.broker_list_dicts(self._this, self.__list_dicts_callback)
        return [(r[0], ProviderDesc(*r[1])) for r in self.__list_dicts_result]

    def __list_dicts_callback(self, tag, name, desc, file):
        """Collector callback for listing dictionaries.

        This method is used as a callback into the _enchant function
        'enchant_broker_list_dicts'.  It collects the given arguments into
        an appropriate tuple and appends them to '__list_dicts_result'.
        """
        tag = tag.decode()
        name = name.decode()
        desc = desc.decode()
        file = file.decode()
        self.__list_dicts_result.append((tag, (name, desc, file)))

    def list_languages(self):
        """List languages for which dictionaries are available.

        This function returns a list of language tags for which a
        dictionary is available.
        """
        langs = []
        for (tag, prov) in self.list_dicts():
            if tag not in langs:
                langs.append(tag)
        return langs

    def __describe_dict(self, dict_data):
        """Get the description tuple for a dict data object.
        <dict_data> must be a C-library pointer to an enchant dictionary.
        The return value is a tuple of the form:
                (<tag>,<name>,<desc>,<file>)
        """
        # Define local callback function
        cb_result = []

        def cb_func(tag, name, desc, file):
            tag = tag.decode()
            name = name.decode()
            desc = desc.decode()
            file = file.decode()
            cb_result.append((tag, name, desc, file))

        # Actually call the describer function
        _e.dict_describe(dict_data, cb_func)
        return cb_result[0]

    __describe_dict._DOC_ERRORS = ["desc"]

    def get_param(self, name):
        """Get the value of a named parameter on this broker.

        Parameters are used to provide runtime information to individual
        provider backends.  See the method :py:meth:`set_param` for more details.

        .. warning::

            This method does **not** work when using the Enchant C
            library version 2.0 and above
        """
        param = _e.broker_get_param(self._this, name.encode())
        if param is not None:
            param = param.decode()
        return param

    get_param._DOC_ERRORS = ["param"]

    def set_param(self, name, value):
        """Set the value of a named parameter on this broker.

        Parameters are used to provide runtime information to individual
        provider backends.

        .. warning::

            This method does **not** work when using the Enchant C
            library version 2.0 and above
        """
        name = name.encode()
        if value is not None:
            value = value.encode()
        _e.broker_set_param(self._this, name, value)


class Dict(_EnchantObject):
    """Dictionary object for the Enchant spellchecker.

    Dictionary objects are responsible for checking the spelling of words
    and suggesting possible corrections.  Each dictionary is owned by a
    Broker object, but unless a new Broker has explicitly been created
    then this will be the 'enchant' module default Broker and is of little
    interest.

    The important methods of this class include:

        * check():              check whether a word id spelled correctly
        * suggest():            suggest correct spellings for a word
        * add():                add a word to the user's personal dictionary
        * remove():             add a word to the user's personal exclude list
        * add_to_session():     add a word to the current spellcheck session
        * store_replacement():  indicate a replacement for a given word

    Information about the dictionary is available using the following
    attributes:

        * tag:        the language tag of the dictionary
        * provider:   a ProviderDesc object for the dictionary provider

    """

    def __init__(self, tag=None, broker=None):
        """Dict object constructor.

        A dictionary belongs to a specific language, identified by the
        string <tag>.  If the tag is not given or is None, an attempt to
        determine the language currently in use is made using the 'locale'
        module.  If the current language cannot be determined, Error is raised.

        If <tag> is instead given the value of False, a 'dead' Dict object
        is created without any reference to a language.  This is typically
        only useful within PyEnchant itself.  Any other non-string value
        for <tag> raises Error.

        Each dictionary must also have an associated Broker object which
        obtains the dictionary information from the underlying system. This
        may be specified using <broker>.  If not given, the default broker
        is used.
        """
        # Initialise misc object attributes to None
        self.provider = None
        # If no tag was given, use the default language
        if tag is None:
            tag = get_default_language()
            if tag is None:
                err = "No tag specified and default language could not "
                err = err + "be determined."
                raise Error(err)
        self.tag = tag
        # If no broker was given, use the default broker
        if broker is None:
            broker = _broker
        self._broker = broker
        # Now let the superclass initialise the C-library object
        super().__init__()

    def _init_this(self):
        # Create dead object if False was given as the tag.
        # Otherwise, use the broker to get C-library pointer data.
        self._this = None
        if self.tag:
            this = self._broker._request_dict_data(self.tag)
            self._switch_this(this, self._broker)

    def __del__(self):
        """Dict object destructor."""
        # Calling free() might fail if python is shutting down
        try:
            self._free()
        except (AttributeError, TypeError):
            pass

    def _switch_this(self, this, broker):
        """Switch the underlying C-library pointer for this object.

        As all useful state for a Dict is stored by the underlying C-library
        pointer, it is very convenient to allow this to be switched at
        run-time.  Pass a new dict data object into this method to affect
        the necessary changes.  The creating Broker object (at the Python
        level) must also be provided.

        This should *never* *ever* be used by application code.  It's
        a convenience for developers only, replacing the clunkier <data>
        parameter to __init__ from earlier versions.
        """
        # Free old dict data
        Dict._free(self)
        # Hook in the new stuff
        self._this = this
        self._broker = broker
        # Update object properties
        desc = self.__describe(check_this=False)
        self.tag = desc[0]
        self.provider = ProviderDesc(*desc[1:])

    _switch_this._DOC_ERRORS = ["init"]

    def _check_this(self, msg=None):
        """Extend _EnchantObject._check_this() to check Broker validity.

        It is possible for the managing Broker object to be freed without
        freeing the Dict.  Thus validity checking must take into account
        self._broker._this as well as self._this.
        """
        if self._broker is None or self._broker._this is None:
            self._this = None
        super()._check_this(msg)

    def _raise_error(self, default="Unspecified Error", eclass=Error):
        """Overrides _EnchantObject._raise_error to check dict errors."""
        err = _e.dict_get_error(self._this)
        if err == "" or err is None:
            raise eclass(default)
        raise eclass(err.decode())

    def _free(self):
        """Free the system resources associated with a Dict object.

        This method frees underlying system resources for a Dict object.
        Once it has been called, the Dict object must no longer be used.
        It is called automatically when the object is garbage collected.
        """
        if self._this is not None:
            # The broker may have been freed before the dict.
            # It will have freed the underlying pointers already.
            if self._broker is not None and self._broker._this is not None:
                self._broker._free_dict(self)

    def check(self, word):
        """Check spelling of a word.

        This method takes a word in the dictionary language and returns
        True if it is correctly spelled, and false otherwise.
        """
        self._check_this()
        # Enchant asserts that the word is non-empty.
        # Check it up-front to avoid nasty warnings on stderr.
        if len(word) == 0:
            raise ValueError("can't check spelling of empty string")
        val = _e.dict_check(self._this, word.encode())
        if val == 0:
            return True
        if val > 0:
            return False
        self._raise_error()

    def suggest(self, word):
        """Suggest possible spellings for a word.

        This method tries to guess the correct spelling for a given
        word, returning the possibilities in a list.
        """
        self._check_this()
        # Enchant asserts that the word is non-empty.
        # Check it up-front to avoid nasty warnings on stderr.
        if len(word) == 0:
            raise ValueError("can't suggest spellings for empty string")
        suggs = _e.dict_suggest(self._this, word.encode())
        return [w.decode() for w in suggs]

    def add(self, word):
        """Add a word to the user's personal word list."""
        self._check_this()
        _e.dict_add(self._this, word.encode())

    def remove(self, word):
        """Add a word to the user's personal exclude list."""
        self._check_this()
        _e.dict_remove(self._this, word.encode())

    def add_to_pwl(self, word):
        """Add a word to the user's personal word list."""
        warnings.warn(
            "Dict.add_to_pwl is deprecated, please use Dict.add",
            category=DeprecationWarning,
            stacklevel=2,
        )
        self._check_this()
        _e.dict_add_to_pwl(self._this, word.encode())

    def add_to_session(self, word):
        """Add a word to the session personal list."""
        self._check_this()
        _e.dict_add_to_session(self._this, word.encode())

    def remove_from_session(self, word):
        """Add a word to the session exclude list."""
        self._check_this()
        _e.dict_remove_from_session(self._this, word.encode())

    def is_added(self, word):
        """Check whether a word is in the personal word list."""
        self._check_this()
        return _e.dict_is_added(self._this, word.encode())

    def is_removed(self, word):
        """Check whether a word is in the personal exclude list."""
        self._check_this()
        return _e.dict_is_removed(self._this, word.encode())

    def store_replacement(self, mis, cor):
        """Store a replacement spelling for a miss-spelled word.

        This method makes a suggestion to the spellchecking engine that the
        miss-spelled word <mis> is in fact correctly spelled as <cor>.  Such
        a suggestion will typically mean that <cor> appears early in the
        list of suggested spellings offered for later instances of <mis>.
        """
        if not mis:
            raise ValueError("can't store replacement for an empty string")
        if not cor:
            raise ValueError("can't store empty string as a replacement")
        self._check_this()
        _e.dict_store_replacement(self._this, mis.encode(), cor.encode())

    store_replacement._DOC_ERRORS = ["mis", "mis"]

    def __describe(self, check_this=True):
        """Return a tuple describing the dictionary.

        This method returns a four-element tuple describing the underlying
        spellchecker system providing the dictionary.  It will contain the
        following strings:

            * language tag
            * name of dictionary provider
            * description of dictionary provider
            * dictionary file

        Direct use of this method is not recommended - instead, access this
        information through the 'tag' and 'provider' attributes.
        """
        if check_this:
            self._check_this()
        _e.dict_describe(self._this, self.__describe_callback)
        return self.__describe_result

    def __describe_callback(self, tag, name, desc, file):
        """Collector callback for dictionary description.

        This method is used as a callback into the _enchant function
        'enchant_dict_describe'.  It collects the given arguments in
        a tuple and stores them in the attribute '__describe_result'.
        """
        tag = tag.decode()
        name = name.decode()
        desc = desc.decode()
        file = file.decode()
        self.__describe_result = (tag, name, desc, file)


class DictWithPWL(Dict):
    """Dictionary with separately-managed personal word list.

    .. note::
        As of version 1.4.0, enchant manages a per-user pwl and
        exclude list.  This class is now only needed if you want
        to explicitly maintain a separate word list in addition to
        the default one.

    This class behaves as the standard Dict class, but also manages a
    personal word list stored in a separate file.  The file must be
    specified at creation time by the 'pwl' argument to the constructor.
    Words added to the dictionary are automatically appended to the pwl file.

    A personal exclude list can also be managed, by passing another filename
    to the constructor in the optional 'pel' argument.  If this is not given,
    requests to exclude words are ignored.

    If either 'pwl' or 'pel' are None, an in-memory word list is used.
    This will prevent calls to add() and remove() from affecting the user's
    default word lists.

    The Dict object managing the PWL is available as the 'pwl' attribute.
    The Dict object managing the PEL is available as the 'pel' attribute.

    To create a DictWithPWL from the user's default language, use None
    as the 'tag' argument.
    """

    _DOC_ERRORS = ["pel", "pel", "PEL", "pel"]

    def __init__(self, tag, pwl=None, pel=None, broker=None):
        """DictWithPWL constructor.

        The argument 'pwl', if not None, names a file containing the
        personal word list.  If this file does not exist, it is created
        with default permissions.

        The argument 'pel', if not None, names a file containing the personal
        exclude list.  If this file does not exist, it is created with
        default permissions.
        """
        super().__init__(tag, broker)
        if pwl is not None:
            if not os.path.exists(pwl):
                f = open(pwl, "wt")
                f.close()
                del f
            self.pwl = self._broker.request_pwl_dict(pwl)
        else:
            self.pwl = PyPWL()
        if pel is not None:
            if not os.path.exists(pel):
                f = open(pel, "wt")
                f.close()
                del f
            self.pel = self._broker.request_pwl_dict(pel)
        else:
            self.pel = PyPWL()

    def _check_this(self, msg=None):
        """Extend Dict._check_this() to check PWL validity."""
        if self.pwl is None:
            self._free()
        if self.pel is None:
            self._free()
        super()._check_this(msg)
        self.pwl._check_this(msg)
        self.pel._check_this(msg)

    def _free(self):
        """Extend Dict._free() to free the PWL as well."""
        if self.pwl is not None:
            self.pwl._free()
            self.pwl = None
        if self.pel is not None:
            self.pel._free()
            self.pel = None
        super()._free()

    def check(self, word):
        """Check spelling of a word.

        This method takes a word in the dictionary language and returns
        True if it is correctly spelled, and false otherwise.  It checks
        both the dictionary and the personal word list.
        """
        if self.pel.check(word):
            return False
        if self.pwl.check(word):
            return True
        if super().check(word):
            return True
        return False

    def suggest(self, word):
        """Suggest possible spellings for a word.

        This method tries to guess the correct spelling for a given
        word, returning the possibilities in a list.
        """
        suggs = super().suggest(word)
        suggs.extend([w for w in self.pwl.suggest(word) if w not in suggs])
        for i in range(len(suggs) - 1, -1, -1):
            if self.pel.check(suggs[i]):
                del suggs[i]
        return suggs

    def add(self, word):
        """Add a word to the associated personal word list.

        This method adds the given word to the personal word list, and
        automatically saves the list to disk.
        """
        self._check_this()
        self.pwl.add(word)
        self.pel.remove(word)

    def remove(self, word):
        """Add a word to the associated exclude list."""
        self._check_this()
        self.pwl.remove(word)
        self.pel.add(word)

    def add_to_pwl(self, word):
        """Add a word to the associated personal word list.

        This method adds the given word to the personal word list, and
        automatically saves the list to disk.
        """
        self._check_this()
        self.pwl.add_to_pwl(word)
        self.pel.remove(word)

    def is_added(self, word):
        """Check whether a word is in the personal word list."""
        self._check_this()
        return self.pwl.is_added(word)

    def is_removed(self, word):
        """Check whether a word is in the personal exclude list."""
        self._check_this()
        return self.pel.is_added(word)


##  Create a module-level default broker object, and make its important
##  methods available at the module level.
_broker = Broker()
request_dict = _broker.request_dict
request_pwl_dict = _broker.request_pwl_dict
dict_exists = _broker.dict_exists
list_dicts = _broker.list_dicts
list_languages = _broker.list_languages
get_param = _broker.get_param
set_param = _broker.set_param

#  Expose the "get_version" function.
def get_enchant_version():
    """Get the version string for the underlying enchant library."""
    return _e.get_version().decode()


#  Expose the "set_prefix_dir" function.
def set_prefix_dir(path):
    """Set the prefix used by the Enchant library to find its plugins

    Called automatically when the Python library is imported when
    required.
    """
    return _e.set_prefix_dir(path)

    set_prefix_dir._DOC_ERRORS = ["plugins"]


def get_user_config_dir():
    """Return the path that will be used by some
    Enchant providers to look for custom dictionaries.
    """
    return _e.get_user_config_dir().decode()
