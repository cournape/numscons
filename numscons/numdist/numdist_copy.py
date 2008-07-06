# Last Change: Sun Jul 06 02:00 PM 2008 J

"""This module contains all the duplicate functions we need from
numpy.distutils and cannot use because of bootstrapping problems."""
import sys
import os.path
import distutils.sysconfig

def get_standard_file(fname):
    """Returns a list of files named 'fname' from
    1) System-wide directory (directory-location of this module)
    2) Users HOME directory (os.environ['HOME'])
    3) Local directory
    """
    # System-wide file
    filenames = []
    try:
        f = __file__
    except NameError:
        f = sys.argv[0]
    else:
        sysfile = os.path.join(os.path.split(os.path.abspath(f))[0],
                               fname)
        if os.path.isfile(sysfile):
            filenames.append(sysfile)

    # Home directory
    # And look for the user config file
    try:
        f = os.environ['HOME']
    except KeyError:
        pass
    else:
        user_file = os.path.join(f, fname)
        if os.path.isfile(user_file):
            filenames.append(user_file)

    # Local file
    if os.path.isfile(fname):
        filenames.append(os.path.abspath(fname))

    return filenames

def msvc_runtime_library():
    "Return name of MSVC runtime library if Python was built with MSVC >= 7"
    msc_pos = sys.version.find('MSC v.')
    if msc_pos != -1:
        msc_ver = sys.version[msc_pos+6:msc_pos+10]
        lib = {'1300' : 'msvcr70',    # MSVC 7.0
               '1310' : 'msvcr71',    # MSVC 7.1
               '1400' : 'msvcr80',    # MSVC 8
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
