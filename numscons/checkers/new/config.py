import os

from copy import \
        deepcopy
from os.path import \
        join as pjoin, dirname as pdirname
from ConfigParser \
        import ConfigParser

from numscons.core.utils import DefaultDict

def get_config_files():
    """Return the list of configuration files to consider for perflib
    configuration."""
    files = [pjoin(pdirname(__file__), 'numscons.cfg')]
    try:
        from numpy.distutils.command.scons import get_perflib_config
        files.extend(get_perflib_config())
    except ImportError:
        pass
    files.append(pjoin(os.getcwd(), 'numscons.cfg'))
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

def _read_section(section):
    parser = ConfigParser()
    files = get_config_files()
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

def read_atlas():
    return _read_section('atlas')

def read_mkl():
    return _read_section('mkl')

if __name__ == '__main__':
    print read_atlas()
    print read_mkl()