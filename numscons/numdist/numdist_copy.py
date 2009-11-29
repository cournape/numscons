# Last Change: Sun Jul 06 03:00 PM 2008 J

"""This module contains all the duplicate functions we need from
numpy.distutils and cannot use because of bootstrapping problems."""
import sys
import os.path
import distutils.sysconfig

def msvc_runtime_library():
    "Return name of MSVC runtime library if Python was built with MSVC >= 7"
    msc_pos = sys.version.find('MSC v.')
    if msc_pos != -1:
        msc_ver = sys.version[msc_pos+6:msc_pos+10]
        lib = {'1300' : 'msvcr70',    # MSVC 7.0
               '1310' : 'msvcr71',    # MSVC 7.1
               '1400' : 'msvcr80',    # MSVC 8
               '1500' : 'msvcr90',    # MSVC 9
              }.get(msc_ver, None)
    else:
        lib = None
    return lib

def get_mathlibs(path):
    """Return the MATHLIB line from numpyconfig.h
    """
    # XXX: fix this bootstrapping issue for real at some point instead of
    # relying on numpy.distutils
    if path is None:
       from numpy.distutils.misc_util import get_numpy_include_dirs
       path = os.path.join(get_numpy_include_dirs()[0], 'numpy')
    config_file = os.path.join(path,'numpyconfig.h')
    fid = open(config_file)
    mathlibs = []
    s = '#define MATHLIB'
    for line in fid.readlines():
        if line.startswith(s):
            value = line[len(s):].strip()
            if value:
                mathlibs.extend(value.split(','))
    fid.close()
    return mathlibs
