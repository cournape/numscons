# Last Change: Fri Mar 07 07:00 PM 2008 J

"""This module contains all the duplicate functions we need from
numpy.distutils and cannot use because of bootstrapping problems."""
import sys
import os.path
import distutils.sysconfig

if sys.platform == 'win32':
    default_lib_dirs = ['C:\\',
                        os.path.join(distutils.sysconfig.EXEC_PREFIX,
                                     'libs')]
    default_include_dirs = []
    default_src_dirs = ['.']
    default_x11_lib_dirs = []
    default_x11_include_dirs = []
else:
    #default_lib_dirs = ['/usr/local/lib', '/opt/lib', '/usr/lib',
    #                    '/opt/local/lib', '/sw/lib']
    default_lib_dirs = []
    default_include_dirs = ['/usr/local/include',
                            '/opt/include', '/usr/include',
                            '/opt/local/include', '/sw/include']
    default_src_dirs = ['.','/usr/local/src', '/opt/src','/sw/src']

    try:
        platform = os.uname()
        bit64 = platform[-1].endswith('64')
    except:
        bit64 = False

    if bit64:
        default_x11_lib_dirs = ['/usr/lib64']
    else:
        default_x11_lib_dirs = ['/usr/X11R6/lib','/usr/X11/lib','/usr/lib']

    default_x11_include_dirs = ['/usr/X11R6/include','/usr/X11/include',
                                '/usr/include']

#if os.path.join(sys.prefix, 'lib') not in default_lib_dirs:
#    default_lib_dirs.insert(0,os.path.join(sys.prefix, 'lib'))
#    default_include_dirs.append(os.path.join(sys.prefix, 'include'))
#    default_src_dirs.append(os.path.join(sys.prefix, 'src'))

default_lib_dirs = filter(os.path.isdir, default_lib_dirs)
default_include_dirs = filter(os.path.isdir, default_include_dirs)
default_src_dirs = filter(os.path.isdir, default_src_dirs)

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
