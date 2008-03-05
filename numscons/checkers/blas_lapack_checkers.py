#! /usr/bin/env python
# Last Change: Wed Mar 05 02:00 PM 2008 J

"""Module for blas/lapack/cblas/clapack checkers. Use perflib checkers
implementations if available."""
import sys
from copy import copy, deepcopy

from numscons.core.extension_scons import built_with_mstools
from numscons.core.siteconfig import get_config_from_section, get_config
from numscons.testcode_snippets import \
        cblas_sgemm as cblas_src, \
        lapack_sgesv, c_sgemm2, \
        clapack_sgesv as clapack_src
from fortran import CheckF77Mangling, CheckF77Clib

from numscons.checkers.perflib_info import add_lib_info, MetalibInfo
from numscons.checkers.perflib import CONFIG, get_perflib_info
from numscons.checkers.support import check_include_and_run

__all__ = ['CheckF77BLAS', 'CheckF77LAPACK', 'CheckCBLAS', 'CheckCLAPACK']

def _get_language_opts(context, language):
    """Return additional options necessary depending on the language.
    
    If no options is necessary (for C, for example), return None. Otherwise,
    returns a dictionary whose possible keys are the same than BuildConfig
    instances."""
    if language == 'C':
        moreopts = None
    elif language == 'F77':
        # We need C/F77 runtime info, otherwise, cannot proceed further
        if not context.env.has_key('F77_LDFLAGS') and not CheckF77Clib(context):
            #add_lib_info(context.env, libname, None)
            return 0
        if built_with_mstools(context.env):
            moreopts = deepcopy(context.env["F77_LDFLAGS"])
        else:
            moreopts = {'linkflagsend' : copy(context.env['F77_LDFLAGS'])}
    else:
        raise ValueError("language %s unknown" % language)

    return moreopts

def _check(perflibs, context, libname, check_version, msg_template, test_src,
           autoadd, language = 'C'):
    """Generic perflib checker to be used in meta checkers.

    perflibs should be a list of perflib to check (the names which can be used
    are the keys of CONFIG."""
    moreopts = _get_language_opts(context, language)
    def _check_perflib(pname):
        """pname is the name of the perflib."""
        cache = get_perflib_info(context, pname)
        if not cache:
            return 0
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

def _get_customization(context, section, libname, test_src, autoadd, language = 'C'):
    """Check whether customization is available through config files."""
    siteconfig = get_config()[0]
    cfgopts, found = get_config_from_section(siteconfig, section)
    if found:
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
        if check_include_and_run(context, '% (from site.cfg) ' % libname, testopts,
                                 [], test_src, autoadd):
            add_lib_info(context.env, libname, MetalibInfo(None, cfgopts, found))
            return 1
    return 0

class CheckerFactory:
    def __init__(self, perflibs, section, libname, msg_template, test, language = 'C'):
        """Create a Meta-Checker from a list of perlibs and basic informations.

        perflibs: dict
            values should be sequence of perflibs to check. keys should
            correspond to the string returned by sys.platform, or default, or
            fallback.
        section: str
            name of the section in customization file (site.cfg, etc...)
        libname: str
            name of the library
        msg_template: str
            template of the displayed message at configuration stage
        test: callable
            should returns a tuple (test, st) where test is a string, and st
            the status code (1 for success, 0 for failure).
        language: str
            language of the test ('C', 'F77', etc...)
        """
        self._libname = libname
        self._section = section
        self._msg = msg_template

        self._test = test    
        self._perflibs = perflibs
        self._lang = language

    def _check(self, context, perflib, check_version, test_src, autoadd):
        return _check(perflib, context, self._libname, check_version, self._msg,
                      test_src, autoadd, self._lang) 

    def __call__(self, context, autoadd = 1, check_version = 0):
        # Get the source code of the test
        src, st = self._test(context)
        if st:
            add_lib_info(context.env, self._libname, None)
            return 0

        # Get customization from site.cfg, etc... if available
        if _get_customization(context, self._section, self._libname, src, autoadd,
                      self._lang):
            return 1
        else:
            # Test if any performance library provides the whished API
            try:
                pf = self._perflibs[sys.platform]
            except KeyError:
                pf = self._perflibs['default']

            if self._check(context, pf, check_version, src, autoadd):
                return 1

        # try a fallback if available
        try:
            pf = self._perflibs['fallback']
            if self._check(context, pf, check_version, src, autoadd):
                return 1
        except KeyError:
            pass

        # Nothing worked, fail
        add_lib_info(context.env, self._libname, None)
        return 0

# CBLAS configuration
CBLAS_PERFLIBS = {
        'darwin': ('Accelerate', 'vecLib'), 
        'default': ('MKL', 'ATLAS', 'Sunperf')}

# BLAS configuration
BLAS_PERFLIBS = {
        'darwin': ('Accelerate', 'vecLib'), 
        'default': ('MKL', 'ATLAS', 'Sunperf'),
        'fallback' : ('GenericBlas',)}

# CLAPACK configuration
CLAPACK_PERFLIBS = { 'default': ('ATLAS',)}

# LAPACK configuration
LAPACK_PERFLIBS = {
        'darwin': ('Accelerate', 'vecLib'), 
        'default': ('MKL', 'ATLAS', 'Sunperf'),
        'fallback' : ('GenericLapack',)}

# Functions to compute test code snippets
def _cblas_test_src(context):
    return cblas_src, 0

def _blas_test_src(context):
    if not context.env.has_key('F77_NAME_MANGLER') and \
       not CheckF77Mangling(context):
        return None, 1

    func_name = context.env['F77_NAME_MANGLER']('sgemm')
    src = c_sgemm2 % {'func': func_name}
    return src, 0

def _clapack_test_src(context):
    return clapack_src, 0

def _lapack_test_src(context):
    if not context.env.has_key('F77_NAME_MANGLER') and \
       not CheckF77Mangling(context):
        return None, 1
    
    # Get the mangled name of our test function
    sgesv_string = context.env['F77_NAME_MANGLER']('sgesv')
    test_src = lapack_sgesv % sgesv_string
    return test_src, 0

# Checkers
CheckCBLAS = CheckerFactory(CBLAS_PERFLIBS, 'cblas', 'cblas', 'CBLAS (%s)',
                            _cblas_test_src)
CheckF77BLAS = CheckerFactory(BLAS_PERFLIBS, 'blas', 'blas', 'BLAS (%s)',
                              _blas_test_src, language = 'F77')
CheckCLAPACK = CheckerFactory(CLAPACK_PERFLIBS, 'clapack', 'clapack', 'CLAPACK (%s)',
                              _lapack_test_src, language = 'F77')
CheckF77LAPACK = CheckerFactory(LAPACK_PERFLIBS, 'lapack', 'lapack', 'LAPACK (%s)',
                              _lapack_test_src, language = 'F77')
