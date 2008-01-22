#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J

# Module for custom, common checkers for numpy (and scipy)
import sys

from numscons.core.libinfo import get_config_from_section, get_config
from numscons.testcode_snippets import \
        cblas_sgemm as cblas_src, \
        lapack_sgesv, c_sgemm2, \
        clapack_sgesv as clapack_src
from numscons.fortran_scons import CheckF77Mangling, CheckF77Clib

from configuration import add_lib_info, get_cached_perflib_info, \
                          MetalibInfo
from perflib import CONFIG, checker
from support import check_include_and_run

def _check(perflibs, context, libname, check_version, msg_template, test_src,
           autoadd):
    """Generic perflib checker to be used in meta checkers.

    perflibs should be a list of perflib to check (the names which can be used
    are the keys of CONFIG."""
    def _check_perflib(pname):
        """pname is the name of the perflib."""
        func = checker(pname)
        name = CONFIG[pname].name
        st = func(context, autoadd, check_version)
        if st:
            cache = get_cached_perflib_info(context.env, pname)
            cfgopts = cache.opts_factory[libname]()
            st = check_include_and_run(context, msg_template % name, 
                                       cfgopts, [], test_src, autoadd)
            if st:
                add_lib_info(context.env, libname, MetalibInfo(pname, cfgopts))
            return st
    for p in perflibs:
        if _check_perflib(p):
            return 1

def _get_customization(context, section, libname, autoadd):
    # If section is in site.cfg, use those options. Otherwise, use default
    siteconfig, cfgfiles = get_config()
    cfg, found = get_config_from_section(siteconfig, section)
    if found:
        if check_include_and_run(context, '% (from site.cfg) ' % libname, cfg,
                                 [], cblas_src, autoadd):
            add_lib_info(context.env, libname, MetalibInfo(None, cfg, found))
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
        if sys.platform == 'darwin' and check(('Accelerate', 'vecLib')):
            return 1
        elif check(('MKL', 'ATLAS', 'Sunperf')):
            return 1

    add_lib_info(env, libname, None)
    return 0

def CheckF77BLAS(context, autoadd = 1, check_version = 0):
    """This checker tries to find optimized library for blas (fortran F77)."""
    libname = 'blas'
    section = "blas"
    env = context.env

    # Get Fortran things we need
    if not env.has_key('F77_NAME_MANGLER') and not CheckF77Mangling(context):
        add_lib_info(env, libname, None)
        return 0

    if not env.has_key('F77_LDFLAGS') and not CheckF77Clib(context):
        add_lib_info(env, libname, None)
        return 0

    func_name = env['F77_NAME_MANGLER']('sgemm')
    test_src = c_sgemm2 % {'func' : func_name}

    def check(perflibs):
        return _check(perflibs, context, libname, check_version, 'BLAS (%s)',
                      test_src, autoadd) 

    if _get_customization(context, section, libname, autoadd):
        return 1
    else:
        if sys.platform == 'darwin' and check(('Accelerate', 'vecLib')):
            return 1
        elif check(('MKL', 'ATLAS', 'Sunperf')):
            return 1

    # Check generic blas last
    if check(('GenericBlas',)):
        return 1

    add_lib_info(env, libname, None)
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

    if not env.has_key('F77_NAME_MANGLER') and not CheckF77Mangling(context):
        add_lib_info(env, 'lapack', None)
        return 0
    
    if not env.has_key('F77_LDFLAGS') and not CheckF77Clib(context):
        add_lib_info(env, 'lapack', None)
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
        if sys.platform == 'darwin' and check(('Accelerate', 'vecLib')):
            return 1
        elif check(('MKL', 'ATLAS', 'Sunperf')):
            return 1

    # Check generic blas last
    if check(('GenericLapack',)):
        return 1

    add_lib_info(env, libname, None)
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
        elif check(('ATLAS',)):
            return 1

    add_lib_info(env, libname, None)
    return 0
