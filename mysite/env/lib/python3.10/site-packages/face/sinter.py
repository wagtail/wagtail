# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import types
import inspect
import hashlib
import linecache

from boltons import iterutils
from boltons.strutils import camel2under
from boltons.funcutils import FunctionBuilder

PY3 = (sys.version_info[0] == 3)
_VERBOSE = False
_INDENT = '    '


def get_fb(f, drop_self=True):
    # TODO: support partials
    if not (inspect.isfunction(f) or inspect.ismethod(f) or \
            inspect.isbuiltin(f)) and hasattr(f, '__call__'):
        if isinstance(getattr(f, '_sinter_fb', None), FunctionBuilder):
            return f._sinter_fb
        f = f.__call__  # callable objects

    if isinstance(getattr(f, '_sinter_fb', None), FunctionBuilder):
        return f._sinter_fb  # we'll take your word for it; good luck, lil buddy.

    ret = FunctionBuilder.from_func(f)

    if not all([isinstance(a, str) for a in ret.args]):  # pragma: no cover (2 only)
        raise TypeError('does not support anonymous tuple arguments'
                        ' or any other strange args for that matter.')
    if drop_self and isinstance(f, types.MethodType):
        ret.args = ret.args[1:]  # discard "self" on methods
    return ret


def get_arg_names(f, only_required=False):
    fb = get_fb(f)

    return fb.get_arg_names(only_required=only_required)


def inject(f, injectables):
    __traceback_hide__ = True  # TODO

    fb = get_fb(f)

    all_kwargs = fb.get_defaults_dict()
    all_kwargs.update(injectables)

    if fb.varkw:
        return f(**all_kwargs)

    kwargs = dict([(k, v) for k, v in all_kwargs.items() if k in fb.get_arg_names()])
    return f(**kwargs)


def get_callable_labels(obj):
    ctx_parts = []
    if isinstance(obj, types.MethodType):
        # bit of 2/3 messiness below
        im_self = getattr(obj, 'im_self', getattr(obj, '__self__', None))
        if im_self:
            ctx_parts.append(im_self.__class__.__name__)
        obj = getattr(obj, 'im_func', getattr(obj, '__func__', None))

    fb = get_fb(obj)
    if fb.module:
        ctx_parts.insert(0, fb.module)


    return '.'.join(ctx_parts), fb.name, fb.get_invocation_str()



# TODO: turn the following into an object (keeps inner_name easier to
# track, as well as better handling of state the func_aliaser will
# need

def chain_argspec(func_list, provides, inner_name):
    provided_sofar = set([inner_name])  # the inner function name is an extremely special case
    optional_sofar = set()
    required_sofar = set()
    for f, p in zip(func_list, provides):
        # middlewares can default the same parameter to different values;
        # can't properly keep track of default values
        fb = get_fb(f)
        arg_names = fb.get_arg_names()
        defaults_dict = fb.get_defaults_dict()

        defaulted, undefaulted = iterutils.partition(arg_names, key=defaults_dict.__contains__)

        optional_sofar.update(defaulted)
        # keep track of defaults so that e.g. endpoint default param
        # can pick up request injected/provided param
        required_sofar |= set(undefaulted) - provided_sofar
        provided_sofar.update(p)

    return required_sofar, optional_sofar


#funcs[0] = function to call
#params[0] = parameters to take
def build_chain_str(funcs, params, inner_name, params_sofar=None, level=0,
                    func_aliaser=None, func_names=None):
    if not funcs:
        return ''  # stopping case
    if params_sofar is None:
        params_sofar = set([inner_name])

    params_sofar.update(params[0])
    inner_args = get_fb(funcs[0]).args
    inner_arg_dict = dict([(a, a) for a in inner_args])
    inner_arg_items = sorted(inner_arg_dict.items())
    inner_args = ', '.join(['%s=%s' % kv for kv in inner_arg_items
                           if kv[0] in params_sofar])
    outer_indent = _INDENT * level
    inner_indent = outer_indent + _INDENT
    outer_arg_str = ', '.join(params[0])
    def_str = '%sdef %s(%s):\n' % (outer_indent, inner_name, outer_arg_str)
    body_str = build_chain_str(funcs[1:], params[1:], inner_name, params_sofar, level + 1)
    #func_name = get_func_name(funcs[0])
    #func_alias = get_inner_func_alias(funcs[0])
    htb_str = '%s__traceback_hide__ = True\n' % (inner_indent,)
    return_str = '%sreturn funcs[%s](%s)\n' % (inner_indent, level, inner_args)
    return ''.join([def_str, body_str, htb_str + return_str])


def compile_chain(funcs, params, inner_name, verbose=_VERBOSE):
    call_str = build_chain_str(funcs, params, inner_name)
    return compile_code(call_str, inner_name, {'funcs': funcs}, verbose=verbose)


def compile_code(code_str, name, env=None, verbose=_VERBOSE):
    code_hash = hashlib.sha1(code_str.encode('utf8')).hexdigest()[:16]
    unique_filename = "<sinter generated %s %s>" % (name, code_hash)
    code = compile(code_str, unique_filename, 'single')
    if verbose:
        print(code_str)  # pragma: no cover
    if PY3:
        exec(code, env)
    else:
        exec("exec code in env")

    linecache.cache[unique_filename] = (
        len(code_str),
        None,
        code_str.splitlines(True),
        unique_filename,
    )
    return env[name]


def make_chain(funcs, provides, final_func, preprovided, inner_name):
    funcs = list(funcs)
    provides = list(provides)
    preprovided = set(preprovided)
    reqs, opts = chain_argspec(funcs + [final_func],
                               provides + [()], inner_name)

    unresolved = tuple(reqs - preprovided)
    args = reqs | (preprovided & opts)
    chain = compile_chain(funcs + [final_func],
                          [args] + provides, inner_name)
    return chain, set(args), set(unresolved)
