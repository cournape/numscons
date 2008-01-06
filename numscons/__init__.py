# XXX those are needed by the scons command only...
from core.misc import get_scons_path, get_scons_build_dir, \
                      get_scons_configres_dir, get_scons_configres_filename

# XXX those should not be needed by the scons command only...
from core.extension import get_python_inc, get_pythonlib_dir

# Those functions really belong to the public API
from core.numpyenv import GetNumpyEnvironment
from core.libinfo_scons import NumpyCheckLibAndHeader

from checkers import CheckF77BLAS, CheckCBLAS, CheckCLAPACK, CheckF77LAPACK, CheckFFT
from fortran_scons import CheckF77Mangling
#import tools
