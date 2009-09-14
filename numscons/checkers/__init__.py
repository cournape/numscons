from numscons.checkers.netlib_checkers import \
        CheckCblas as CheckCBLAS, \
        CheckF77Blas as CheckF77BLAS, \
        CheckF77Lapack as CheckF77LAPACK
from numscons.checkers.common import \
        get_perflib_implementation
from numscons.checkers.common import \
        write_configuration_results as write_info

from numscons.checkers.simple_check import \
        NumpyCheckLibAndHeader
from numscons.checkers.fortran import *
from numscons.checkers import fortran

# Those are for compatibility only
def CheckCLAPACK(context, autoadd=1, check_version=0):
    context.Message("Checking for CLAPACK ... ")
    context.Result(0)
    return 0

def IsVeclib(env, interface):
    return get_perflib_implementation(env, interface.upper()) == 'VECLIB'

def IsAccelerate(env, interface):
    return get_perflib_implementation(env, interface.upper()) == 'ACCELERATE'

def IsATLAS(env, interface):
    return get_perflib_implementation(env, interface.upper()) == 'ATLAS'

def GetATLASVersion(env):
    return ''

__all__ = []
__all__ += ['CheckCBLAS', 'CheckF77LAPACK', 'CheckF77BLAS', 'CheckCLAPACK',
        'write_info', 'IsVeclib', 'IsAccelerate', 'IsATLAS', 'GetATLASVersion']
__all__ += fortran.__all__
__all__ += ['NumpyCheckLibAndHeader']
