#! /usr/bin/env python
# Last Change: Wed Jan 09 11:00 PM 2008 J
import os
from copy import deepcopy

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

def available_opts_flags():
    return _BUILD_OPTS_FLAGS

class BuildOpts(DefaultDict):
    """Small container class to keep all necessary options to build with a
    given library/package, such as cflags, libs, library paths, etc..."""
    _keys = _BUILD_OPTS_FLAGS
    def __init__(self, default = None):
        DefaultDict.__init__(self, avkeys = BuildOpts._keys)

    def __repr__(self):
        msg = [r'%s : %s' % (k, i) for k, i in self.items()]
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
    lapack, etc..."""
    def __init__(self, bld_opts):
        pass

    def get_blas_config(self):
        pass

    def get_cblas_config(self):
        pass

    def get_lapack_config(self):
        pass

    def get_clapack_config(self):
        pass

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

        msg += ['  %s : %s' % (k, i) for k, i in self.cfgopts.items() if i is not None]
        msg += ['  Version is : %s' % self.version]
        return '\n'.join(msg)

    def __str__(self):
        return self.__repr__()
