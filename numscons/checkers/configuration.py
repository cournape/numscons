#! /usr/bin/env python
# Last Change: Thu Nov 22 12:00 PM 2007 J
import os

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
