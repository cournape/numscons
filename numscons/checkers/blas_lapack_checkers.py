#! /usr/bin/env python
# Last Change: Tue Dec 04 03:00 PM 2007 J

# Module for custom, common checkers for numpy (and scipy)
import sys
from copy import deepcopy

from numscons.core.libinfo import get_config_from_section, get_config
from numscons.testcode_snippets import \
        cblas_sgemm as cblas_src, \
        lapack_sgesv, c_sgemm2, \
        clapack_sgesv as clapack_src
from numscons.fortran_scons import CheckF77Mangling, CheckF77Clib

from configuration import add_info, BuildOpts, ConfigRes
from perflib import CONFIG, checker
from support import check_include_and_run

def _check(perflibs, context, libname, check_version, msg_template, test_src,
           autoadd):
    """Generic perflib checker to be used in meta checkers.

    perflibs should be a list of perflib to check."""
    def _check_perflib(func, name):
        st, res = func(context, autoadd, check_version)
        if st:
            cfgopts = res.cfgopts[libname]()
            st = check_include_and_run(context, msg_template % name, 
                                       cfgopts, [], test_src, autoadd)
            if st:
                add_info(context.env, libname, res)
            return st
    for p in perflibs:
        st = _check_perflib(checker(p), CONFIG[p].name)
        if st:
            return st

def _get_customization(context, section, libname, autoadd):
    # If section cblas is in site.cfg, use those options. Otherwise, use default
    siteconfig, cfgfiles = get_config()
    cfg, found = get_config_from_section(siteconfig, section)
    if found:
        if check_include_and_run(context, '% (from site.cfg) ' % libname, cfg,
                                 [], cblas_src, autoadd):
            add_info(context.env, libname, ConfigRes('Generic %s' % libname,
                     cfg, found))
            return 1
    return 0

def CheckCBLAS(context, autoadd = 1, check_version = 0):
    """This checker tries to find optimized library for cblas."""
    libname = 'cblas'
    section = 'cblas'
    env = context.env

    def check(perflibs):
        return _check(perflibs, context, libname, check_version, 'CBLAS (%s)',
                      cblas_src, autoadd) 

    if _get_customization(context, section, libname, autoadd):
        return 1
    else:
        if sys.platform == 'darwin':
            if check(('Accelerate', 'vecLib')):
                return 1
        else:
            if check(('MKL', 'ATLAS', 'Sunperf')):
                return 1

    add_info(env, libname, None)
    return 0

def CheckF77BLAS(context, autoadd = 1, check_version = 0):
    """This checker tries to find optimized library for blas (fortran F77)."""
    libname = 'blas'
    section = "blas"
    env = context.env

    # Get Fortran things we need
    if not env.has_key('F77_NAME_MANGLER'):
        if not CheckF77Mangling(context):
            add_info(env, libname, None)
            return 0

    if not env.has_key('F77_LDFLAGS'):
        if not CheckF77Clib(context):
            add_info(env, 'blas', None)
            return 0

    func_name = env['F77_NAME_MANGLER']('sgemm')
    test_src = c_sgemm2 % {'func' : func_name}

    def check(perflibs):
        return _check(perflibs, context, libname, check_version, 'BLAS (%s)',
                      test_src, autoadd) 

    if _get_customization(context, section, libname, autoadd):
        return 1
    else:
        if sys.platform == 'darwin':
            if check(('Accelerate', 'vecLib')):
                return 1
        else:
            if check(('MKL', 'ATLAS', 'Sunperf')):
                return 1

    def check_generic_blas():
        name = 'Generic'
        cfg = CONFIG['GenericBlas']
        res = ConfigRes(name, cfg.defopts, 0)
        st = check_include_and_run(context, 'BLAS (%s)' % name, res.cfgopts,
                                   [], test_src, autoadd)
        if st:
            add_info(env, libname, res)
        return st

    # Check generic blas last
    st = check_generic_blas()
    if st:
        return st

    add_info(env, libname, None)
    return 0

def CheckF77LAPACK(context, autoadd = 1, check_version = 0):
    """This checker tries to find optimized library for F77 lapack.

    This test is pretty strong: it first detects an optimized library, and then
    tests that a simple (C) program can be run using this (F77) lib.
    
    It looks for the following libs:
        - Mac OS X: Accelerate, and then vecLib.
        - Others: MKL, then ATLAS."""
    libname = 'lapack'
    section = "lapack"
    env = context.env

    if not env.has_key('F77_NAME_MANGLER'):
        if not CheckF77Mangling(context):
            add_info(env, 'lapack', None)
            return 0
    
    if not env.has_key('F77_LDFLAGS'):
        if not CheckF77Clib(context):
            add_info(env, 'lapack', None)
            return 0
    
    # Get the mangled name of our test function
    sgesv_string = env['F77_NAME_MANGLER']('sgesv')
    test_src = lapack_sgesv % sgesv_string

    def check(perflibs):
        return _check(perflibs, context, libname, check_version, 'LAPACK (%s)',
                      test_src, autoadd) 

    # XXX: handle F77_LDFLAGS
    if _get_customization(context, section, libname, autoadd):
        return 1
    else:
        if sys.platform == 'darwin':
            if check(('Accelerate', 'vecLib')):
                return 1
        else:
            if check(('MKL', 'ATLAS', 'Sunperf')):
                return 1

    def check_generic_lapack():
        name = 'Generic'
        cfg = CONFIG['GenericLapack']
        res = ConfigRes(name, cfg.defopts, 0)
        st = check_include_and_run(context, 'LAPACK (%s)' % name, res.cfgopts,
                                   [], test_src, autoadd)
        if st:
            add_info(env, libname, res)
        return st

    # Check generic blas last
    st = check_generic_lapack()
    if st:
        return st

    add_info(env, libname, None)
    return 0

def CheckCLAPACK(context, autoadd = 1, check_version = 0):
    """This checker tries to find optimized library for lapack.

    This test is pretty strong: it first detects an optimized library, and then
    tests that a simple cblas program can be run using this lib.
    
    It looks for the following libs:
        - Mac OS X: Accelerate, and then vecLib.
        - Others: MKL, then ATLAS."""
    libname = 'clapack'
    section = "clapack"
    env = context.env

    def check(perflibs):
        return _check(perflibs, context, libname, check_version, 'CLAPACK (%s)',
                      clapack_src, autoadd) 

    if _get_customization(context, section, libname, autoadd):
        return 1
    else:
        if sys.platform == 'darwin':
            pass
        else:
            if check(('ATLAS',)):
                return 1

    add_info(env, libname, None)
    return 0
