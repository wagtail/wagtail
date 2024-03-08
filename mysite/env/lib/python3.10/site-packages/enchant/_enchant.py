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

    enchant._enchant:  ctypes-based wrapper for enchant C library

    This module implements the low-level interface to the underlying
    C library for enchant.  The interface is based on ctypes and tries
    to do as little as possible while making the higher-level components
    easier to write.

    The following conveniences are provided that differ from the underlying
    C API:

        * the "enchant" prefix has been removed from all functions, since
          python has a proper module system
        * callback functions do not take a user_data argument, since
          python has proper closures that can manage this internally
        * string lengths are not passed into functions such as dict_check,
          since python strings know how long they are

"""

import sys
import os
import os.path
import ctypes
from ctypes import c_char_p, c_int, c_size_t, c_void_p, pointer, CFUNCTYPE, POINTER
import ctypes.util
import platform
import textwrap


def from_prefix(prefix):
    find_message("finding from prefix ", prefix)
    assert os.path.exists(prefix), prefix + "  does not exist"
    bin_path = os.path.join(prefix, "bin")
    enchant_dll_path = os.path.join(bin_path, "libenchant-2.dll")
    assert os.path.exists(enchant_dll_path), enchant_dll_path + " does not exist"
    # Make sure all the dlls found next to libenchant-2.dll
    # (libglib-2.0-0.dll, libgmodule-2.0-0.dll, ...) can be
    # used without having to modify %PATH%
    new_path = bin_path + os.pathsep + os.environ["PATH"]
    find_message("Prepending ", bin_path, " to %PATH%")
    os.environ["PATH"] = new_path
    return enchant_dll_path


def from_env_var(library_path):
    find_message("using PYENCHANT_LIBRARY_PATH env var")
    assert os.path.exists(library_path), library_path + " does not exist"
    return library_path


def from_package_resources():
    if sys.platform != "win32":
        return None
    bits, _ = platform.architecture()
    if bits == "64bit":
        subdir = "mingw64"  # hopefully this is compatible
    else:
        subdir = "mingw32"  # ditto
    this_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(this_path, "data", subdir)
    find_message("looking in ", data_path)
    if os.path.exists(data_path):
        return from_prefix(data_path)


def from_system():
    # Note: keep enchant-2 first
    find_message("looking in system")
    candidates = [
        "enchant-2",
        "libenchant-2",
        "enchant",
        "libenchant",
        "enchant-1",
        "libenchant-1",
    ]

    for name in candidates:
        find_message("with name ", name)
        res = ctypes.util.find_library(name)
        if res:
            return res


VERBOSE_FIND = False


def find_message(*args):
    if not VERBOSE_FIND:
        return
    print("pyenchant:: ", *args, sep="")


def find_c_enchant_lib():
    verbose = os.environ.get("PYENCHANT_VERBOSE_FIND")
    if verbose:
        global VERBOSE_FIND
        VERBOSE_FIND = True
    prefix = os.environ.get("PYENCHANT_ENCHANT_PREFIX")
    if prefix:
        return from_prefix(prefix)

    library_path = os.environ.get("PYENCHANT_LIBRARY_PATH")
    if library_path:
        return from_env_var(library_path)

    from_package = from_package_resources()
    if from_package:
        return from_package

    # Last chance
    return from_system()


enchant_lib_path = find_c_enchant_lib()

if enchant_lib_path is None:
    msg = textwrap.dedent(
        """\
        The 'enchant' C library was not found and maybe needs to be installed.
        See  https://pyenchant.github.io/pyenchant/install.html
        for details
        """
    )
    raise ImportError(msg)


find_message("loading library ", enchant_lib_path)
e = ctypes.cdll.LoadLibrary(enchant_lib_path)

# Always assume the found enchant C dll is inside
# the correct directory layout
prefix_dir = os.path.dirname(os.path.dirname(enchant_lib_path))
if hasattr(e, "enchant_set_prefix_dir") and prefix_dir:
    find_message("setting prefix ", prefix_dir)
    e.enchant_set_prefix_dir(prefix_dir.encode())


def callback(restype, *argtypes):
    """Factory for generating callback function prototypes.

    This is factored into a factory so I can easily change the definition
    for experimentation or debugging.
    """
    return CFUNCTYPE(restype, *argtypes)


t_broker_desc_func = callback(None, c_char_p, c_char_p, c_char_p, c_void_p)
t_dict_desc_func = callback(None, c_char_p, c_char_p, c_char_p, c_char_p, c_void_p)


# Simple typedefs for readability

t_broker = c_void_p
t_dict = c_void_p


# Now we can define the types of each function we are going to use

broker_init = e.enchant_broker_init
broker_init.argtypes = []
broker_init.restype = t_broker

broker_free = e.enchant_broker_free
broker_free.argtypes = [t_broker]
broker_free.restype = None

broker_request_dict = e.enchant_broker_request_dict
broker_request_dict.argtypes = [t_broker, c_char_p]
broker_request_dict.restype = t_dict

broker_request_pwl_dict = e.enchant_broker_request_pwl_dict
broker_request_pwl_dict.argtypes = [t_broker, c_char_p]
broker_request_pwl_dict.restype = t_dict

broker_free_dict = e.enchant_broker_free_dict
broker_free_dict.argtypes = [t_broker, t_dict]
broker_free_dict.restype = None

broker_dict_exists = e.enchant_broker_dict_exists
broker_dict_exists.argtypes = [t_broker, c_char_p]
broker_dict_exists.restype = c_int

broker_set_ordering = e.enchant_broker_set_ordering
broker_set_ordering.argtypes = [t_broker, c_char_p, c_char_p]
broker_set_ordering.restype = None

broker_get_error = e.enchant_broker_get_error
broker_get_error.argtypes = [t_broker]
broker_get_error.restype = c_char_p

broker_describe1 = e.enchant_broker_describe
broker_describe1.argtypes = [t_broker, t_broker_desc_func, c_void_p]
broker_describe1.restype = None


def broker_describe(broker, cbfunc):
    def cbfunc1(*args):
        cbfunc(*args[:-1])

    broker_describe1(broker, t_broker_desc_func(cbfunc1), None)


broker_list_dicts1 = e.enchant_broker_list_dicts
broker_list_dicts1.argtypes = [t_broker, t_dict_desc_func, c_void_p]
broker_list_dicts1.restype = None


def broker_list_dicts(broker, cbfunc):
    def cbfunc1(*args):
        cbfunc(*args[:-1])

    broker_list_dicts1(broker, t_dict_desc_func(cbfunc1), None)


try:
    broker_get_param = e.enchant_broker_get_param
except AttributeError:
    #  Make the lookup error occur at runtime
    def broker_get_param(broker, name):
        return e.enchant_broker_get_param(broker, name)


else:
    broker_get_param.argtypes = [t_broker, c_char_p]
    broker_get_param.restype = c_char_p

try:
    broker_set_param = e.enchant_broker_set_param
except AttributeError:
    #  Make the lookup error occur at runtime
    def broker_set_param(broker, name, value):
        return e.enchant_broker_set_param(broker, name, value)


else:
    broker_set_param.argtypes = [t_broker, c_char_p, c_char_p]
    broker_set_param.restype = None

try:
    get_version = e.enchant_get_version
except AttributeError:
    #  Make the lookup error occur at runtime
    def get_version():
        return e.enchant_get_version()


else:
    get_version.argtypes = []
    get_version.restype = c_char_p

try:
    set_prefix_dir = e.enchant_set_prefix_dir
except AttributeError:
    #  Make the lookup error occur at runtime
    def set_prefix_dir(path):
        return e.enchant_set_prefix_dir(path)


else:
    set_prefix_dir.argtypes = [c_char_p]
    set_prefix_dir.restype = None

try:
    get_user_config_dir = e.enchant_get_user_config_dir
except AttributeError:
    #  Make the lookup error occur at runtime
    def get_user_config_dir():
        return e.enchant_get_user_config_dir()


else:
    get_user_config_dir.argtypes = []
    get_user_config_dir.restype = c_char_p

dict_check1 = e.enchant_dict_check
dict_check1.argtypes = [t_dict, c_char_p, c_size_t]
dict_check1.restype = c_int


def dict_check(dict, word):
    return dict_check1(dict, word, len(word))


dict_suggest1 = e.enchant_dict_suggest
dict_suggest1.argtypes = [t_dict, c_char_p, c_size_t, POINTER(c_size_t)]
dict_suggest1.restype = POINTER(c_char_p)


def dict_suggest(dict, word):
    num_suggs_p = pointer(c_size_t(0))
    suggs_c = dict_suggest1(dict, word, len(word), num_suggs_p)
    suggs = []
    n = 0
    while n < num_suggs_p.contents.value:
        suggs.append(suggs_c[n])
        n = n + 1
    if num_suggs_p.contents.value > 0:
        dict_free_string_list(dict, suggs_c)
    return suggs


dict_add1 = e.enchant_dict_add
dict_add1.argtypes = [t_dict, c_char_p, c_size_t]
dict_add1.restype = None


def dict_add(dict, word):
    return dict_add1(dict, word, len(word))


dict_add_to_pwl1 = e.enchant_dict_add
dict_add_to_pwl1.argtypes = [t_dict, c_char_p, c_size_t]
dict_add_to_pwl1.restype = None


def dict_add_to_pwl(dict, word):
    return dict_add_to_pwl1(dict, word, len(word))


dict_add_to_session1 = e.enchant_dict_add_to_session
dict_add_to_session1.argtypes = [t_dict, c_char_p, c_size_t]
dict_add_to_session1.restype = None


def dict_add_to_session(dict, word):
    return dict_add_to_session1(dict, word, len(word))


dict_remove1 = e.enchant_dict_remove
dict_remove1.argtypes = [t_dict, c_char_p, c_size_t]
dict_remove1.restype = None


def dict_remove(dict, word):
    return dict_remove1(dict, word, len(word))


dict_remove_from_session1 = e.enchant_dict_remove_from_session
dict_remove_from_session1.argtypes = [t_dict, c_char_p, c_size_t]
dict_remove_from_session1.restype = c_int


def dict_remove_from_session(dict, word):
    return dict_remove_from_session1(dict, word, len(word))


dict_is_added1 = e.enchant_dict_is_added
dict_is_added1.argtypes = [t_dict, c_char_p, c_size_t]
dict_is_added1.restype = c_int


def dict_is_added(dict, word):
    return dict_is_added1(dict, word, len(word))


dict_is_removed1 = e.enchant_dict_is_removed
dict_is_removed1.argtypes = [t_dict, c_char_p, c_size_t]
dict_is_removed1.restype = c_int


def dict_is_removed(dict, word):
    return dict_is_removed1(dict, word, len(word))


dict_store_replacement1 = e.enchant_dict_store_replacement
dict_store_replacement1.argtypes = [t_dict, c_char_p, c_size_t, c_char_p, c_size_t]
dict_store_replacement1.restype = None


def dict_store_replacement(dict, mis, cor):
    return dict_store_replacement1(dict, mis, len(mis), cor, len(cor))


dict_free_string_list = e.enchant_dict_free_string_list
dict_free_string_list.argtypes = [t_dict, POINTER(c_char_p)]
dict_free_string_list.restype = None

dict_get_error = e.enchant_dict_get_error
dict_get_error.argtypes = [t_dict]
dict_get_error.restype = c_char_p

dict_describe1 = e.enchant_dict_describe
dict_describe1.argtypes = [t_dict, t_dict_desc_func, c_void_p]
dict_describe1.restype = None


def dict_describe(dict, cbfunc):
    def cbfunc1(tag, name, desc, file, data):
        cbfunc(tag, name, desc, file)

    dict_describe1(dict, t_dict_desc_func(cbfunc1), None)
