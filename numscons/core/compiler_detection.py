"""This module implements detection of compilers types from their command
line."""
import re
import sys
import os

from numscons.core.utils import popen_wrapper
from numscons.core.errors import UnknownCompiler

# How to detect a new compiler:
#   - implements a function is_*, which takes the (full) path of the compiler,
#   and returns a tuple (st, version), where st is a boolean set to True is the
#   given compiler is of the expected type, and version a string.
#   - the function is_ can use the function _parse

GNUCC = [re.compile('gcc version ([0-9-.]+)')]
ICC = [re.compile(r'Intel.*?C Compiler.*?Version ([0-9-.]+)')]
IFORT = [re.compile(r'Intel.*?Fortran Compiler.*?Version ([0-9-.]+)')]
SUNCC = [re.compile('Sun Ceres C ([0-9-.]+)'), re.compile('Sun C ([0-9-.]+)')]
SUNCXX = [re.compile('Sun Ceres C\+\+ ([0-9-.]+)'), re.compile('Sun C\+\+ ([0-9-.]+)')]
SUNFC = [re.compile('Sun Ceres Fortran 95 ([0-9-.]+)'), re.compile('Sun Fortran 95 ([0-9-.]+)')]

def _parse(regex, string):
    for r in regex:
        m = r.search(string)
        if m:
            return True, m.group(1)
    return False, None

def parse_icc(string):
    return _parse(ICC, string)

def parse_ifort(string):
    return _parse(IFORT, string)

def parse_suncc(string):
    return _parse(SUNCC, string)

def parse_suncxx(string):
    return _parse(SUNCXX, string)

def parse_sunfortran(string):
    return _parse(SUNFC, string)

def parse_gnu(string):
    return _parse(GNUCC, string)

def _is_compiler(path, cmdargs, parser):
    # cmdargs is a list of arguments to get verbose information
    cmd = [path] + cmdargs
    try:
        env={'LC_ALL': 'C'}
        try:
            env['PATH'] = os.environ['PATH']
        except KeyError, e:
            pass
        st, cnt = popen_wrapper(cmd, merge=True, shell=False, env=env)
    except OSError, e:
        return False, None
    ret, ver = parser(cnt)
    if st == 0 and ret:
        return ret, ver
    else:
        return False, None

def is_suncc(path):
    """Return True if the compiler in path is sun C compiler."""
    # If the Sun compiler is not given a file as an argument, it returns an
    # error code, even when using dry run and version. So we give a non
    # existing file as an argument: this seems to work, at least for Sun Studio
    # 12 (5.9)
    return _is_compiler(path, ['-V', "-###", "nonexistingfile.fakec"], 
                        parse_suncc)

def is_suncxx(path):
    """Return True if the compiler in path is sun CXX compiler."""
    # Note that the C++ compiler works in a
    # sensible manner when given -V compared to the C compiler...
    return _is_compiler(path, ['-V'], parse_suncxx)

def is_sunfortran(path):
    """Return True if the compiler in path is sun fortran compiler."""
    return _is_compiler(path, ['-V'], parse_sunfortran)

def is_icc(path):
    """Return True if the compiler in path is Intel C compiler."""
    return _is_compiler(path, ['-V'], parse_icc)

def is_ifort(path):
    """Return True if the compiler in path is Intel Fortran compiler."""
    return _is_compiler(path, ['-V'], parse_ifort)

def is_gcc(path):
    """Return True if the compiler in path is GNU compiler."""
    return _is_compiler(path, ['-v'], parse_gnu)

def is_g77(path):
    """Return True if the compiler in path is GNU F77 compiler."""
    st, v = is_gcc(path)
    if st:
        try:
            major = int(v.split(".")[0])
            return major < 4, v
        except ValueError:
            raise UnknownCompiler("Could not parse version %v" % v)
    else:
        return st, v

def is_gfortran(path):
    """Return True if the compiler in path is GNU F77/F90/F95 compiler."""
    st, v = is_gcc(path)
    if st:
        try:
            major = int(v.split(".")[0])
            return major >= 4, v
        except ValueError:
            raise UnknownCompiler("Could not parse version %v" % v)
    else:
        return st, v

# XXX: support default compiler for platforms where it makes sense (unix)
def get_cc_type(env, path):
    # If not cached, detect type of CC, otherwise just return the cached value
    if not env.has_key("NUMPY_CC_TYPE"):
        if is_gcc(path)[0]:
            type = "gcc"
        elif is_suncc(path)[0]:
            type = "suncc"
        elif is_icc(path)[0]:
            type = "intelc"
        else:
            if sys.platform != "win32":
                type = "cc"
            else:
                raise UnknownCompiler("Unknown C compiler %s" % path)
        env["NUMPY_CC_TYPE"] = type
    return env["NUMPY_CC_TYPE"]

def get_cxx_type(env, path):
    # If not cached, detect type of CXX, otherwise just return the cached value
    if not env.has_key("NUMPY_CXX_TYPE"):
        if is_gcc(path)[0]:
            type = "g++"
        elif is_suncxx(path)[0]:
            type = "suncc"
        elif is_icc(path)[0]:
            type = "intelc"
        else:
            raise UnknownCompiler("Unknown CXX compiler %s" % path)
        env["NUMPY_CXX_TYPE"] = type
    return env["NUMPY_CXX_TYPE"]

def get_f77_type(env, path):
    # If not cached, detect type of F77, otherwise just return the cached value
    if not env.has_key("NUMPY_F77_TYPE"):
        if is_g77(path)[0]:
            type =  "g77"
        elif is_gfortran(path)[0]:
            type =  "gfortran"
        elif is_sunfortran(path)[0]:
            type =  "sunf77"
        elif is_ifort(path)[0]:
            type =  "ifort"
        else:
            raise UnknownCompiler("Unknown F77 compiler %s" % path)
        env["NUMPY_F77_TYPE"] = type
    return env["NUMPY_F77_TYPE"]

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise ValueError("Usage: %s compiler" % __file__)
    cc = sys.argv[1]

    for f in [get_cc_type, get_cxx_type, get_f77_type]:
        try:
            print f({}, cc)
        except UnknownCompiler, e:
            print e
