#! /usr/bin/env python
# Last Change: Sat Jan 26 06:00 PM 2008 J

"""This module implements the functionality to:
    - add/retrieve info about checked meta-lib for show_config functionality.
"""
import os

__all__ = ['write_info']

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
    cfg = env['NUMPY_PKG_CONFIG']['LIB']
    config_str = {}
    for k, i in cfg.items():
        config_str[k] = str(i)
    f = open(env['NUMPY_PKG_CONFIG_FILE'], 'w')
    f.writelines("%s" % str(config_str))
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
    def __init__(self, perflib_name, bld_opts, is_customized = False):
        self.pname = perflib_name
        self.is_customized = is_customized
        self.opts = bld_opts

    def __repr__(self):
        msg = ['uses %s' % self.pname]
        msg += [repr(self.opts)]
        return '\n\t'.join(msg)

    def uses_perflib(self, pname):
        """Return true is the lib uses pname as the underlying performance
        library."""
        return pname == self.pname

