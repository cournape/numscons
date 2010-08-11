import os
import sys

from copy import \
        deepcopy
from os.path import \
        join as pjoin, dirname as pdirname
from ConfigParser \
        import ConfigParser

import numscons
from numscons.core.utils import DefaultDict
from numscons.core.misc import _CONFDIR

def _get_win32_config_files():
    # We import platform here as we only need it for windows and platform
    # import is relatively slow
    import platform

    files = [pjoin(_CONFDIR, 'win32', 'perflib.cfg')]
    if platform.architecture()[0] == '64bit':
        files.append(pjoin(_CONFDIR, 'win64', 'perflib.cfg'))
    return files

def get_config_files(env):
    """Return the list of configuration files to consider for perflib
    configuration."""
    files = [pjoin(_CONFDIR, 'perflib.cfg')]
    if sys.platform == 'win32':
        files.extend(_get_win32_config_files())
    if env:
        files.append(pjoin(str(env.fs.Top), 'numscons.cfg'))
    return files

class ConfigDict(DefaultDict):
    __keys = ['libraries', 'blas_libraries', 'lapack_libraries', 'cblas_libraries',
            'cflags', 'ldflags', 'include_dirs', 'library_dirs', 'frameworks']
    @classmethod
    def fromcallable(cls, avkeys, default=None):
        raise UnimplementedError()

    def __init__(self):
        DefaultDict.__init__(self, self.__keys)
        for k in self.keys():
            self[k] = []

class BuildDict(DefaultDict):
    __keys = ['CFLAGS', 'LIBS', 'LINKFLAGS', 'CPPPATH', 'LIBPATH', 'FRAMEWORKS']
    __convert_dict = {'cflags': 'CFLAGS',
            'libraries': 'LIBS',
            'ldflags': 'LINKFLAGS',
            'include_dirs': 'CPPPATH',
            'library_dirs': 'LIBPATH',
            'frameworks': 'FRAMEWORKS'
            }
    @classmethod
    def fromcallable(cls, avkeys, default=None):
        raise UnimplementedError()

    @classmethod
    def from_config_dict(cls, config_dict):
        ret = cls()
        for k in cls.__convert_dict.keys():
            ret[cls.__convert_dict[k]] = config_dict[k]
        return ret

    def __init__(self):
        DefaultDict.__init__(self, self.__keys)
        for k in self.keys():
            self[k] = []

def _read_section(section, env):
    """Attempt to build a ConfigDict instance from given section in the
    configuration files detected by numscons.

    If no file has a section, return None"""
    parser = ConfigParser()
    files = get_config_files(env)
    r = parser.read(files)
    if len(r) < 1:
        raise IOError("No config file found (looked for %s)" % files)

    if not parser.has_section(section):
        return None

    config = ConfigDict()

    for o in ['libraries', 'blas_libraries', 'lapack_libraries',
            'cblas_libraries', 'cflags', 'ldflags', 'frameworks']:
        if parser.has_option(section, o):
            config[o] = parser.get(section, o).split(',')

    for o in ['include_dirs', 'library_dirs']:
        if parser.has_option(section, o):
            config[o] = parser.get(section, o).split(os.pathsep)

    return config

def read_atlas(env=None):
    return _read_section('atlas', env)

def read_mkl(env=None):
    return _read_section('mkl', env)

def read_accelerate(env=None):
    return _read_section('accelerate', env)

def read_generic_blas(env=None):
    return _read_section('generic_blas', env)

def read_generic_lapack(env=None):
    return _read_section('generic_lapack', env)

if __name__ == '__main__':
    print read_atlas()
    print read_mkl()
    print read_accelerate()
