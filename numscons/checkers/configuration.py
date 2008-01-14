#! /usr/bin/env python
# Last Change: Sat Jan 12 06:00 PM 2008 J
import os
from copy import deepcopy, copy

from numscons.core.utils import DefaultDict

def add_info(env, name, opt):
    cfg = env['NUMPY_PKG_CONFIG']
    cfg[name] = opt

def write_info(env):
    dir = os.path.dirname(env['NUMPY_PKG_CONFIG_FILE'])
    if not os.path.exists(dir):
        os.makedirs(dir)
    cfg = env['NUMPY_PKG_CONFIG']
    config_str = {}
    for k, i in cfg.items():
        config_str[k] = str(i)
    f = open(env['NUMPY_PKG_CONFIG_FILE'], 'w')
    f.writelines("config = %s" % str(config_str))
    f.close()

# List of options that BuildOpts can keep. If later additional variables should
# be added (e.g. cpp flags, etc...), they should be added here.
_BUILD_OPTS_FLAGS = ('cpppath', 'cflags', 'libpath', 'libs', 'linkflags',
                     'rpath', 'frameworks')

# List of options that BuildOptsFactory can keep. If later additional variables
# should be added, they should be added here.
_BUILD_OPTS_FACTORY_FLAGS = _BUILD_OPTS_FLAGS + ('cblas_libs', 'blas_libs',
                            'clapack_libs', 'lapack_libs', 'htc', 'ftc')

def available_build_opts_flags():
    return _BUILD_OPTS_FLAGS

def available_build_opts_factory_flags():
    return _BUILD_OPTS_FACTORY_FLAGS

class BuildOpts(DefaultDict):
    """Small container class to keep all necessary options to build with a
    given library/package, such as cflags, libs, library paths, etc..."""
    _keys = _BUILD_OPTS_FLAGS
    @classmethod
    def fromcallable(cls, default = None):
        return DefaultDict.fromcallable(BuildOpts._keys, default)

    def __init__(self, default = None):
        DefaultDict.__init__(self, BuildOpts._keys, default)

    def __repr__(self):
        msg = [r'%s : %s' % (k, i) for k, i in self.items() if len(i) > 0]
        return '\n'.join(msg)

    def __copy__(self):
        cpy = BuildOpts()
        for k in self.keys():
            cpy[k] = deepcopy(self[k])
        return cpy 

class BuildOptsFactory:
    """This class can return cutomized BuildOpts instances according to some
    options.
    
    For example, you would create a BuildOptsFactory with a MKL BuildOpts
    instance, and the factory would return customized BuildOpts for blas,
    lapack, 64 vs 32 bits, etc..."""
    def __init__(self, bld_opts):
        self._data = bld_opts

        self._bld = BuildOpts()
        for k in self._bld:
            self._bld[k] = self._data[k]

    def get_core_config(self):
        return self._bld

    def _get_libs(self, supp):
        res = copy(self._bld)
        tmp = copy(res['libs'])
        res['libs'] = []
        for i in supp:
            res['libs'] += self._data[i]
        res['libs'] += tmp
        return res

    def get_blas_config(self):
        return self._get_libs(['blas_libs'])

    def get_cblas_config(self):
        return self._get_libs(['cblas_libs'])

    def get_lapack_config(self):
        return self._get_libs(['lapack_libs', 'blas_libs'])

    def get_clapack_config(self):
        return self._get_libs(['clapack_libs', 'cblas_libs'])

    def __repr__(self):
        return self._data.__repr__()

class ConfigRes:
    def __init__(self, name, cfgopts, origin, version = None):
        self.name = name
        self.cfgopts = cfgopts
        self.origin = origin
        self.version = version

    def is_customized(self):
        return bool(self.origin)

    def __repr__(self):
        msg = ['Using %s' % self.name]
        if self.is_customized():
            msg += [  'Customized items site.cfg:']
        else:
            msg += ['  Using default configuration:']

        msg += ['  %s : %s' % (k, i) for k, i in self.cfgopts.items() if len(i) > 0]
        msg += ['  Version is : %s' % self.version]
        return '\n'.join(msg)

    def __str__(self):
        return self.__repr__()

if __name__ == '__main__':
    from numscons.checkers.perflib_config import CONFIG, _PERFLIBS
    a = DefaultDict(avkeys = _BUILD_OPTS_FACTORY_FLAGS)
    for p in _PERFLIBS:
        mkl = CONFIG[p]
        for k in mkl.values:
            a[k] = mkl.values[k]

        b = BuildOptsFactory(a)
        print b.get_core_config()
        print b.get_blas_config()
        print b.get_cblas_config()
        print b.get_lapack_config()
        print b.get_clapack_config()
