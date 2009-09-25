import os

from copy import \
        deepcopy
from os.path import \
        join as pjoin, dirname as pdirname
from ConfigParser \
        import ConfigParser

import numscons
from numscons.core.utils import DefaultDict

_CONFDIR = pjoin(pdirname(numscons.__file__), 'configurations')

def get_config_files(env):
    """Return the list of configuration files to consider for perflib
    configuration."""
    files = [pjoin(_CONFDIR, 'perflib.cfg')]
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
        for k, v in config_dict.items():
            ret[cls.__convert_dict[k]] = v
        return ret

    def __init__(self):
        DefaultDict.__init__(self, self.__keys)
        for k in self.keys():
            self[k] = []

def _read_section(section, env):
    parser = ConfigParser()
    files = get_config_files(env)
    r = parser.read(files)
    if len(r) < 1:
        raise IOError("No config file found (looked for %s)" % files)

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

if __name__ == '__main__':
    print read_atlas()
    print read_mkl()
    print read_accelerate()
