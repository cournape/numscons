#! /usr/bin/env python
# Last Change: Wed Jan 16 08:00 PM 2008 J

"""This module defines checkers for performances libs providing standard API,
such as MKL (Intel), ATLAS, Sunperf (solaris and linux), Accelerate (Mac OS X),
etc... Those checkers merely only check whether the library is found using a
library specific check if possible, or other heuristics.

Generally, you don't use those directly: they are used in 'meta' checkers, such
as BLAS, CBLAS, LAPACK checkers."""

from copy import deepcopy

from configuration import ConfigRes, add_perflib_info
from common import check_code as _check
from perflib_config import IsFactory, GetVersionFactory, CONFIG
from version_checkers import atlas_version_checker, mkl_version_checker
from misc import get_sunperf_link_options

#--------------
# MKL checker
#--------------
def CheckMKL(context, autoadd = 1, check_version = 0):
    cfg = CONFIG['MKL']

    st, res =  _check(context, cfg.name, cfg.section, cfg.opts_factory, cfg.headers,
                      cfg.funcs, check_version, mkl_version_checker, autoadd)
    if st:
        add_perflib_info(context.env, 'MKL', res)
    return st, res

IsMKL = IsFactory('MKL').get_func()
GetMKLVersion = GetVersionFactory('MKL').get_func()

#---------------
# ATLAS Checker
#---------------
def CheckATLAS(context, autoadd = 1, check_version = 0):
    """Check whether ATLAS is usable in C."""
    cfg = CONFIG['ATLAS']

    st, res = _check(context, cfg.name, cfg.section, cfg.opts_factory, cfg.headers,
                     cfg.funcs, check_version, atlas_version_checker, autoadd)
    if st:
        add_perflib_info(context.env, 'ATLAS', res)
    return st, res

IsATLAS = IsFactory('ATLAS').get_func()
GetATLASVersion = GetVersionFactory('ATLAS').get_func()

#------------------------------
# Mac OS X Frameworks checkers
#------------------------------
def CheckAccelerate(context, autoadd = 1, check_version = 0):
    """Checker for Accelerate framework (on Mac OS X >= 10.3). """
    # According to
    # http://developer.apple.com/hardwaredrivers/ve/vector_libraries.html:
    #
    #   This page contains a continually expanding set of vector libraries
    #   that are available to the AltiVec programmer through the Accelerate
    #   framework on MacOS X.3, Panther. On earlier versions of MacOS X,
    #   these were available in vecLib.framework. The currently available
    #   libraries are described below.

    #XXX: get_platform does not seem to work...
    #if get_platform()[-4:] == 'i386':
    #    is_intel = 1
    #    cflags.append('-msse3')
    #else:
    #    is_intel = 0
    #    cflags.append('-faltivec')

    cfg = CONFIG['Accelerate']

    st, res = _check(context, cfg.name, cfg.section, cfg.opts_factory, cfg.headers,
                     cfg.funcs, check_version, None, autoadd)
    if st:
        add_perflib_info(context.env, 'Accelerate', res)
    return st, res

IsAccelerate = IsFactory('Accelerate').get_func()

def CheckVeclib(context, autoadd = 1, check_version = 0):
    """Checker for Veclib framework (on Mac OS X < 10.3)."""
    cfg = CONFIG['vecLib']

    st, res = _check(context, cfg.name, cfg.section, cfg.opts_factory, cfg.headers,
                     cfg.funcs, check_version, None, autoadd)
    if st:
        add_perflib_info(context.env, 'vecLib', res)
    return st, res

IsVeclib = IsFactory('vecLib').get_func()

#-----------------
# Sunperf checker
#-----------------
def CheckSunperf(context, autoadd = 1, check_version = 0):
    """Checker for sunperf."""
    cfg = CONFIG['Sunperf']
    
    st, res = _check(context, cfg.name, cfg.section, cfg.opts_factory, cfg.headers,
                     cfg.funcs, check_version, None, autoadd)
    if not st:
        return st, res

    # We are not done: the option -xlic_lib=sunperf is not used by the linker
    # for shared libraries, I have no idea why. So if the test is succesfull,
    # we need more work to get the link options necessary to make the damn
    # thing work.
    st, flags = get_sunperf_link_options(context, res)
    if st:
        opts = res.cfgopts
        for k, v in flags.items():
            opts[k].extend(deepcopy(v))
        res = ConfigRes(cfg.name, opts, res.is_customized())
        add_perflib_info(context.env, 'Sunperf', res)
        context.Result('Succeeded !')
    else:
        context.Result('Failed !')

    return st, res

IsSunperf = IsFactory('Sunperf').get_func()

def CheckGenericBlas(context, autoadd = 1, check_version = 0):
    """Generic (fortran) blas checker."""
    cfg = CONFIG['GenericBlas']

    res = ConfigRes("Generic", cfg.opts_factory, 0)
    add_perflib_info(context.env, 'GenericBlas', res)
    return 1, res

def CheckGenericLapack(context, autoadd = 1, check_version = 0):
    """Generic (fortran) lapack checker."""
    cfg = CONFIG['GenericLapack']

    res = ConfigRes("Generic", cfg.opts_factory, 0)
    add_perflib_info(context.env, 'GenericLapack', res)
    return 1, res

#--------------------
# FFT related perflib
#--------------------
def CheckFFTW3(context, autoadd = 1, check_version = 0):
    """This checker tries to find fftw3."""
    cfg = CONFIG['FFTW3']
    
    st, res = _check(context, cfg.name, cfg.section, cfg.opts_factory, cfg.headers,
                     cfg.funcs, check_version, None, autoadd)
    if st:
        add_perflib_info(context.env, 'FFTW3', res)
    return st, res

IsFFTW3 = IsFactory('FFTW3').get_func()

def CheckFFTW2(context, autoadd = 1, check_version = 0):
    """This checker tries to find fftw2."""
    cfg = CONFIG['FFTW2']
    
    st, res = _check(context, cfg.name, cfg.section, cfg.opts_factory, cfg.headers,
                     cfg.funcs, check_version, None, autoadd)
    if st:
        add_perflib_info(context.env, 'FFTW2', res)
    return st, res

IsFFTW2 = IsFactory('FFTW2').get_func()

_PERFLIBS_CHECKERS = {
    'GenericBlas': CheckGenericBlas,
    'GenericLapack': CheckGenericLapack,
    'MKL': CheckMKL,
    'ATLAS': CheckATLAS,
    'Accelerate': CheckAccelerate,
    'vecLib': CheckVeclib,
    'Sunperf': CheckSunperf,
    'FFTW2': CheckFFTW2,
    'FFTW3': CheckFFTW3}

def checker(name):
    return _PERFLIBS_CHECKERS[name]
