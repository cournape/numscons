#! /usr/bin/env python
# Last Change: Sat Jan 26 06:00 PM 2008 J

"""Module for blas/lapack/cblas/clapack checkers. Use perflib checkers
implementations if available."""
import sys
from copy import copy

from numscons.core.siteconfig import get_config_from_section, get_config
from numscons.testcode_snippets import \
        cblas_sgemm as cblas_src, \
        lapack_sgesv, c_sgemm2, \
        clapack_sgesv as clapack_src
from fortran import CheckF77Mangling, CheckF77Clib

from numscons.checkers.perflib_info import add_lib_info, \
     get_cached_perflib_info, MetalibInfo, CacheError as PerflibCacheError
from numscons.checkers.perflib import CONFIG, checker
from numscons.checkers.support import check_include_and_run

__all__ = ['CheckF77BLAS', 'CheckF77LAPACK', 'CheckCBLAS', 'CheckCLAPACK']

def _check(perflibs, context, libname, check_version, msg_template, test_src,
           autoadd, language = 'C'):
    """Generic perflib checker to be used in meta checkers.

    perflibs should be a list of perflib to check (the names which can be used
    are the keys of CONFIG."""
    moreopts = {}
    if language == 'C':
        pass
    elif language == 'F77':
        # We need C/F77 runtime info, otherwise, cannot proceed further
        if not context.env.has_key('F77_LDFLAGS') and not CheckF77Clib(context):
            add_lib_info(context.env, libname, None)
            return 0
        moreopts['linkflagsend'] = copy(context.env['F77_LDFLAGS'])
    else:
        raise ValueError("language %s unknown" % language)

    def _check_perflib(pname):
        """pname is the name of the perflib."""
        try:
            cache = get_cached_perflib_info(context.env, pname)
        except PerflibCacheError:
            # Do not autoadd in the perflib checker. If the meta lib check works,
            # it will add all the flags if autoadd is asked.
            if not checker(pname)(context, 0, check_version):
                return 0
            cache = get_cached_perflib_info(context.env, pname)

        cfgopts = cache.opts_factory[libname]()
        if moreopts:
            # More options are necessary to check the code snippet (fortran
            # runtime, etc...), so we create a new BuildConfig which contain
            # those info.
            testopts = copy(cfgopts)
            for k, v in moreopts.items():
                testopts[k].extend(v)
        else:
            # Nothing to do, testopts and cfgopts are the same
            testopts = cfgopts
        st = check_include_and_run(context, msg_template % CONFIG[pname].name,
                                   testopts, [], test_src, autoadd)
        if st:
            add_lib_info(context.env, libname, MetalibInfo(pname, cfgopts))
        return st

    for p in perflibs:
        if _check_perflib(p):
            return 1

def _get_customization(context, section, libname, autoadd):
    """Check whether customization is available through config files."""
    siteconfig = get_config()[0]
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

    func_name = env['F77_NAME_MANGLER']('sgemm')
    test_src = c_sgemm2 % {'func' : func_name}

    def check(perflibs):
        return _check(perflibs, context, libname, check_version, 'BLAS (%s)',
                      test_src, autoadd, language = 'F77') 

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
    
    # Get the mangled name of our test function
    sgesv_string = env['F77_NAME_MANGLER']('sgesv')
    test_src = lapack_sgesv % sgesv_string

    def check(perflibs):
        return _check(perflibs, context, libname, check_version, 'LAPACK (%s)',
                      test_src, autoadd, language = 'F77') 

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
