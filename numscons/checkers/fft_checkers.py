#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J

"""Module for fft checkers."""
from numscons.checkers.perflib import checker
from numscons.checkers.perflib_info import add_lib_info, MetalibInfo, \
     get_cached_perflib_info

__all__ = ['CheckFFT']

def CheckFFT(context, autoadd = 1, check_version = 0):
    """This checker tries to find optimized library for fft"""
    libname = 'fft'
    env = context.env

    def check_fft_perflib(perflibs):
        def check(pname):
            func = checker(pname)
            # Do not autoadd in the perflib checker. If the meta lib check works,
            # it will add all the flags if autoadd is asked.
            if func(context, 0, check_version):
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
