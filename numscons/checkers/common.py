#! /usr/bin/env python
"""Module implementing check_code function, which is the common function used
by most perflib checkers for the actual check.

This function checks that a list of headers can be found, as well as a list of
symbols, given a list of path and libraries to look for. It also supports
customization using site.cfg, as well being disabled from the user environment
(e.g. ATLAS=None)."""

import os
from copy import copy

from numscons.core.siteconfig import get_config_from_section
from numscons.core.trace import debug, info, warn
from numscons.checkers.perflib_info import PerflibInfo
from numscons.checkers.support import save_and_set, restore, check_symbol

def _get_site_cfg_customization(siteconfig, section, defopts_factory):
    """defopts_factory should be an instance of BuildConfigFactory."""
    opts, found = get_config_from_section(siteconfig, section)
    defopts_factory.merge(opts)

    return found

def _check_header(context, opts, headers_to_check):
    """Check if a program with the given list of headers can compile with the
    given options.

    Returns 1 if successfull, 0 otherwise."""
    saved = save_and_set(context.env, opts)
    try:
        src_code = [r'#include <%s>' % h for h in headers_to_check]
        src_code.extend([r'#if 0', str(opts), r'#endif', '\n'])
        src = '\n'.join(src_code)
        st = context.TryCompile(src, '.c')
    finally:
        restore(context.env, saved)

    if not st:
        context.Result('Failed (could not check header(s) : check config.log '\
                       'in %s for more details)' % context.env['build_dir'])
    return st

def _check_symbol(context, opts, headers_to_check, funcs_to_check, autoadd):
    """Check if a program with the given list of headers and the given
    functions can compile and link with the given options.

    Returns 1 if successfull, 0 otherwise."""
    saved = save_and_set(context.env, opts)
    st = 1
    try:
        for sym in funcs_to_check:
            extra = [r'#if 0', str(opts), r'#endif', '\n']
            st = check_symbol(context, headers_to_check, sym, '\n'.join(extra))
            if not st:
                break
    finally:
        if st == 0 or autoadd == 0:
            restore(context.env, saved)

    if not st:
        context.Result('Failed (could not check symbol %s : check config.log '\
                       'in %s for more details))' % \
                       (sym, context.env['build_dir']))
    return st

def _check_version(context, opts, version_checker):
    """Check version using the given callable."""
    if version_checker:
        vst, v = version_checker(context, opts)
        if vst:
            version = v
        else:
            version = 'Unknown (checking version failed)'
    else:
        version = 'Unkown (not implemented)'

    return version

def check_code(context, name, section, opts_factory, headers_to_check,
               funcs_to_check, check_version, version_checker, autoadd,
               rpath_is_libpath = True):
    """Generic implementation for perflib check.

    This checks for header (by compiling code including them) and symbols in
    libraries (by linking code calling for given symbols). Optionnaly, it can
    get the version using some specific function.

    See CheckATLAS or CheckMKL for examples."""
    context.Message("Checking %s ... " % name)

    # Is customized from user environment ?
    if os.environ.has_key(name) and os.environ[name] == 'None':
        context.Result('Disabled from env through var %s !' % name)
        return None

    # Get site.cfg customization if any
    found = _get_site_cfg_customization(context.env['NUMPY_SITE_CONFIG'][0],
                                        section, opts_factory)
    opts = opts_factory.core_config()
    if rpath_is_libpath:
        opts['rpath'] = copy(opts['library_dirs'])

    info('\n=====\nPerflib check %s: configuration factory is %s '
         '(customized ? %d)\n=====' % (name, opts, found))
    # Check whether the header is available (CheckHeader-like checker)
    st = _check_header(context, opts, headers_to_check)
    if not st:
        return None

    # Check whether the library is available (CheckLib-like checker)
    st = _check_symbol(context, opts, headers_to_check, funcs_to_check,
                       autoadd)
    if not st:
        return None

    context.Result(st)

    # Check version if requested
    if check_version:
        version = _check_version(context, opts, version_checker)
        plinfo = PerflibInfo(opts_factory, found, version)
    else:
        plinfo = PerflibInfo(opts_factory, found)

    return plinfo
