#! /usr/bin/env python
# Last Change: Fri Mar 07 10:00 PM 2008 J

"""Module for blas/lapack/cblas/clapack checkers. Use perflib checkers
implementations if available."""
from numscons.testcode_snippets import \
        cblas_sgemm as cblas_src, \
        lapack_sgesv, c_sgemm2, \
        clapack_sgesv as clapack_src
from numscons.checkers.checker_factory import CheckerFactory

from fortran import CheckF77Mangling, CheckF77Clib

__all__ = ['CheckF77BLAS', 'CheckF77LAPACK', 'CheckCBLAS', 'CheckCLAPACK']

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
CheckCBLAS = CheckerFactory(CBLAS_PERFLIBS, 'cblas', 'cblas', 'CBLAS',
                            _cblas_test_src)
CheckCLAPACK = CheckerFactory(CLAPACK_PERFLIBS, 'clapack', 'clapack', 'CLAPACK',
                              _clapack_test_src, language = 'F77')

CheckF77BLAS = CheckerFactory(BLAS_PERFLIBS, 'blas', 'blas', 'BLAS',
                              _blas_test_src, language = 'F77')
CheckF77LAPACK = CheckerFactory(LAPACK_PERFLIBS, 'lapack', 'lapack', 'LAPACK',
                              _lapack_test_src, language = 'F77')
