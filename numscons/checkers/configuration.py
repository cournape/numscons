#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J

"""This module implements the functionality to:
    - keep all necessary build informations about perflib and meta lib, so that
      those info can be passed from one function to the other.
    - add/retrieve info about checked meta-lib for show_config functionality.
"""
import os
from copy import copy

from numscons.core.utils import DefaultDict

def add_perflib_info(env, name, opt):
    assert opt is not None
    assert isinstance(opt, PerflibInfo)
    cfg = env['NUMPY_PKG_CONFIG']['PERFLIB']
    cfg[name] = opt

def add_empty_perflib_info(env, name):
    cfg = env['NUMPY_PKG_CONFIG']['PERFLIB']
    cfg[name] = None

def add_lib_info(env, name, opt):
    cfg = env['NUMPY_PKG_CONFIG']['LIB']
    cfg[name] = opt

class CacheError(RuntimeError):
    pass

def get_cached_perflib_info(env, name):
    try:
        cached = env['NUMPY_PKG_CONFIG']['PERFLIB'][name]
    except KeyError:
        msg = "perflib %s was not in cache; you should call the "\
              "corresponding  checker first" % name
        raise CacheError(msg)

    return cached

def write_info(env):
    cfgdir = os.path.dirname(env['NUMPY_PKG_CONFIG_FILE'])
    if not os.path.exists(cfgdir):
        os.makedirs(cfgdir)
    cfg = env['NUMPY_PKG_CONFIG']['PERFLIB']
    config_str = {}
    for k, i in cfg.items():
        config_str[k] = str(i)
    f = open(env['NUMPY_PKG_CONFIG_FILE'], 'w')
    f.writelines("config = %s" % str(config_str))
    f.close()

class PerflibInfo:
    """Instances of this class will keep all informations about a perflib (MKL,
    etc...). 

    The goal is that the first time a perflib checker is called, it will create
    an instance of this class, put it into a scons environment, and next time
    the perflib is called, it will retrieve all info from the object.

    It will also be used to retrieve info from scons scripts (such as version,
    etc...).

    As such, this class handle both caching and information sharing."""
    def __init__(self, opts_factory, is_customized = False, version =
                 None):
        self.is_customized = is_customized
        self.opts_factory = opts_factory
        self.version = version

    def __repr__(self):
        msg = []
        if self.is_customized:
            msg += ['\n\t- Customized from site.cfg -']
        else:
            msg += ['\n\t- Using default configuration -']

        if self.version:
            msg += ['- version is : %s' % self.version]
        else:
            msg += ['- Version is : Unknown or not checked -']
        return '\n\t'.join(msg)


class MetalibInfo:
    """Instances of this class will keep all informations about a meta lib
    (BLAS, etc...). 

    This will primaly be used to generate build info, retrived from numpy/scipy
    through show_config function.."""
    def __init__(self, name, perflib_name, bld_opts, is_customized = False):
        self.name = name
        self.pname = perflib_name
        self.is_customized = is_customized
        self.opts = bld_opts

    def __repr__(self):
        msg = ['%s: uses %s' % (self.name, self.pname)]
        msg += [repr(self.opts)]
        return '\n\t'.join(msg)

# List of options that BuildOpts can keep. If later additional variables should
# be added (e.g. cpp flags, etc...), they should be added here.
_BUILD_OPTS_FLAGS = ('include_dirs', 'cflags', 'library_dirs', 'libraries',
                     'linkflags', 'rpath', 'frameworks')

# List of options that BuildOptsFactory can keep. If later additional variables
# should be added, they should be added here.
_BUILD_OPTS_FACTORY_FLAGS = \
    _BUILD_OPTS_FLAGS + \
    ('cblas_libs', 'blas_libs', 'clapack_libs', 'lapack_libs', 'htc', 'ftc')

def available_build_opts_flags():
    return _BUILD_OPTS_FLAGS

def available_build_opts_factory_flags():
    return _BUILD_OPTS_FACTORY_FLAGS

class BuildOpts(DefaultDict):
    """Small container class to keep all necessary options to build with a
    given library/package, such as cflags, libs, library paths, etc..."""
    _keys = _BUILD_OPTS_FLAGS
    def __init__(self):
        DefaultDict.__init__(self, self._keys)
        for k in self._keys:
            self[k] = []

    def __repr__(self):
        msg = [r'%s : %s' % (k, i) for k, i in self.items() if len(i) > 0]
        return '\n'.join(msg)

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

        self._cfgs = {
            'blas':     self.blas_config,
            'lapack':   self.lapack_config,
            'cblas':    self.cblas_config,
            'clapack':  self.clapack_config}

    def __getitem__(self, k):
        return self._cfgs[k]

    def core_config(self):
        return self._bld

    def _get_libraries(self, supp):
        res = copy(self._bld)
        tmp = copy(res['libraries'])
        res['libraries'] = []
        for i in supp:
            res['libraries'] += self._data[i]
        res['libraries'] += tmp
        return res

    def blas_config(self):
        return self._get_libraries(['blas_libs'])

    def cblas_config(self):
        return self._get_libraries(['cblas_libs'])

    def lapack_config(self):
        return self._get_libraries(['lapack_libs', 'blas_libs'])

    def clapack_config(self):
        return self._get_libraries(['clapack_libs', 'cblas_libs'])

    def __repr__(self):
        return '\n\t'.join(['%s: %s' % (k, v) 
                            for k, v in self._data.items() if len(v) > 0])

    def replace(self, cfg):
        """Given a dictionary cfg, replace all its value with the one of cfg,
        for every key in cfg.
        
        Example: you have a BuildOptsFactory instance, and you want to modify
        some of its options from a BuildOpts instance (obtained from site.cfg
        customization)."""
        for k, v in cfg.items():
            self._bld[k] = v

    def merge(self, cfg, append = False):
        """Given a dictionary cfg, merge all its value with the one of cfg, for
        every key in cfg.
        
        Example: you have a BuildOptsFactory instance, and you want to modify
        some of its options from a BuildOpts instance (obtained from site.cfg
        customization)."""
        if append:
            for k, v in cfg.items():
                self._bld[k] += v
        else:
            for k, v in cfg.items():
                swap = copy(self._bld[k])
                self._bld[k] = v + self._bld[k]

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

        msg += [self.cfgopts.__repr__()]
        if self.version:
            msg += ['  Version is : %s' % self.version]
        else:
            msg += ['  Version is : Unknown or not checked']
        return '\n'.join(msg)

    def __str__(self):
        return self.__repr__()

if __name__ == '__main__':
    from numscons.checkers.perflib_config import CONFIG, _PERFLIBS
    a = DefaultDict(avkeys = _BUILD_OPTS_FACTORY_FLAGS)
    for p in _PERFLIBS:
        print CONFIG[p].opts_factory
