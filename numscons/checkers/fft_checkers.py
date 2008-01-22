#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J

# Module for custom, common checkers for numpy (and scipy)
import sys
import os.path
from copy import deepcopy
from distutils.util import get_platform

# from numpy.distutils.scons.core.libinfo import get_config_from_section, get_config
# from numpy.distutils.scons.testcode_snippets import cblas_sgemm as cblas_src, \
#         c_sgemm as sunperf_src, lapack_sgesv, blas_sgemm, c_sgemm2, \
#         clapack_sgesv as clapack_src
# from numpy.distutils.scons.fortran_scons import CheckF77Mangling, CheckF77Clib
from perflib import CheckMKL, CheckFFTW3, CheckFFTW2, checker
from support import check_include_and_run
from configuration import BuildConfig
from perflib_info import add_lib_info, MetalibInfo, get_cached_perflib_info

__all__ = ['CheckFFT']

def CheckFFT(context, autoadd = 1, check_version = 0):
    """This checker tries to find optimized library for fft"""
    libname = 'fft'
    env = context.env

    def check_fft_perflib(perflibs):
        def check(pname):
            func = checker(pname)
            if func(context, autoadd, check_version):
                # XXX: check for fft code ?
                cache = get_cached_perflib_info(context.env, pname)
                cfgopts = cache.opts_factory[libname]()
                add_lib_info(env, libname, MetalibInfo(pname, cfgopts))
                st = 1
            else:
                st = 0

            return st

        for p in perflibs:
            if check(p):
                return 1
        return 0

    if check_fft_perflib(('MKL', 'FFTW3', 'FFTW2')):
        return 1

    add_lib_info(env, libname, None)
    return 0
