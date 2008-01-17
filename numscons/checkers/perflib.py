#! /usr/bin/env python
# Last Change: Wed Jan 16 09:00 PM 2008 J

"""This module defines checkers for performances libs providing standard API,
such as MKL (Intel), ATLAS, Sunperf (solaris and linux), Accelerate (Mac OS X),
etc... Those checkers merely only check whether the library is found using a
library specific check if possible, or other heuristics.

Generally, you don't use those directly: they are used in 'meta' checkers, such
as BLAS, CBLAS, LAPACK checkers."""

from copy import deepcopy

from numscons.core.utils import partial

from configuration import ConfigRes, add_perflib_info, PerflibInfo
from common import check_code
from perflib_config import IsFactory, GetVersionFactory, CONFIG
from version_checkers import atlas_version_checker, mkl_version_checker
from misc import get_sunperf_link_options

def _check(context, cfg, check_version, version_checker, autoadd):
    return check_code(context, cfg.name, cfg.section, cfg.opts_factory,
                      cfg.headers, cfg.funcs, check_version,
                      mkl_version_checker, autoadd)

class CheckPerflibFactory:
    def __init__(self, name):
        def checker(context, autoadd = 1, check_version = 0):
            cfg = CONFIG[name]

            st, res =  _check(context, cfg, check_version, mkl_version_checker,
                              autoadd)
            #if st:
            #    add_perflib_info(context.env, name, res)
            return st, res
        self.checker = checker

#--------------
# MKL checker
#--------------
CheckMKL = CheckPerflibFactory('MKL').checker

IsMKL = IsFactory('MKL').get_func()
GetMKLVersion = GetVersionFactory('MKL').get_func()

#---------------
# ATLAS Checker
#---------------
CheckATLAS = CheckPerflibFactory('ATLAS').checker

IsATLAS = IsFactory('ATLAS').get_func()
GetATLASVersion = GetVersionFactory('ATLAS').get_func()

#------------------------------
# Mac OS X Frameworks checkers
#------------------------------
# According to
# http://developer.apple.com/hardwaredrivers/ve/vector_libraries.html:
#
#   This page contains a continually expanding set of vector libraries
#   that are available to the AltiVec programmer through the Accelerate
#   framework on MacOS X.3, Panther. On earlier versions of MacOS X,
#   these were available in vecLib.framework. The currently available
#   libraries are described below.
CheckAccelerate = CheckPerflibFactory('Accelerate').checker
IsAccelerate = IsFactory('Accelerate').get_func()

CheckVeclib = CheckPerflibFactory('vecLib').checker
IsVeclib = IsFactory('vecLib').get_func()

#-----------------
# Sunperf checker
#-----------------
def CheckSunperf(context, autoadd = 1, check_version = 0):
    """Checker for sunperf."""
    cfg = CONFIG['Sunperf']
    
    st, res = _check(context, cfg, check_version, None, autoadd)
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
        add_perflib_info(context.env, 'Sunperf', PerflibInfo(cfg.opts_factory))
        context.Result('Succeeded !')
    else:
        context.Result('Failed !')

    return st, res

IsSunperf = IsFactory('Sunperf').get_func()

#---------------------
# Generic BLAS checker
#---------------------
def CheckGenericBlas(context, autoadd = 1, check_version = 0):
    """Generic (fortran) blas checker."""
    cfg = CONFIG['GenericBlas']

    res = ConfigRes("Generic", cfg.opts_factory, 0)
    add_perflib_info(context.env, 'GenericBlas', PerflibInfo(cfg.opts_factory))
    return 1, res

#-----------------------
# Generic Lapack checker
#-----------------------
def CheckGenericLapack(context, autoadd = 1, check_version = 0):
    """Generic (fortran) lapack checker."""
    cfg = CONFIG['GenericLapack']

    res = ConfigRes("Generic", cfg.opts_factory, 0)
    add_perflib_info(context.env, 'GenericLapack', PerflibInfo(cfg.opts_factory))
    return 1, res

#--------------------
# FFT related perflib
#--------------------
CheckFFTW3 = CheckPerflibFactory('FFTW3').checker

IsFFTW3 = IsFactory('FFTW3').get_func()

CheckFFTW2 = CheckPerflibFactory('FFTW3').checker

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
