#! /usr/bin/env python
# Last Change: Sun Jul 06 02:00 PM 2008 J
"""This module contains the infrastructure to get all the necessary options for
perflib checkers from the perflib configuration file."""

from os.path import join as pjoin, dirname as pdirname
from ConfigParser import SafeConfigParser

from numscons.core.utils import DefaultDict
from numscons.checkers.configuration import build_config_factory_flags, \
     BuildConfigFactory

__all__ = ['CONFIG', 'IsFactory', 'GetVersionFactory']

# List of perflibs supported: this must correspond to the sections in
# perflib.cfg
_PERFLIBS = ('GenericBlas', 'GenericLapack', 'MKL', 'ATLAS', 'Accelerate',
             'vecLib', 'Sunperf', 'FFTW2', 'FFTW3')

#------------------------
# Generic functionalities
#------------------------
class _PerflibConfig:
    """A class which contain all the information read from the configuration
    file (perflib.cfg).

    For a given performance library, this includes build options (cflags, libs,
    path, etc....) and meta information (name, version, how to check)."""
    def __init__(self, dispname, sitename, values):
        """Initialize the configuration."""
        self.name = dispname
        self.section = sitename

        self._values = values
        self.headers = values['htc']
        self.funcs = values['ftc']
        #self.version_checker = version_checker

        self.opts_factory = BuildConfigFactory(values)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        rep = ["Display name: %s" % self.name]
        rep += ["Section name: %s" % self.section]
        rep += ["Headers to check : %s" % self.headers]
        rep += ["Funcs to check : %s" % self.funcs]
        return '\n'.join(rep)

#-------------------------------------------
# Perflib specific configuration and helpers
#-------------------------------------------
def build_config():
    # list_opts contain a list of all available options available in
    # perflib.cfg which can be a list.
    list_opts = build_config_factory_flags()

    cfg = SafeConfigParser()

    pfcname = pjoin(pdirname(__file__), 'perflib.cfg')
    st = cfg.read(pfcname)
    if len(st) == 0:
        raise IOError("the file %s was not found. "\
                      "This is an installation problem." % pfcname)

    def get_perflib_config(name):
        yop = DefaultDict.fromcallable(list_opts, lambda: [])
        opts = cfg.options(name)

        # Get mandatory options first
        def get_opt(opt):
            opts.pop(opts.index(opt))
            o = cfg.get(name, opt)
            return o
        dispname = get_opt('dispname')
        sitename = get_opt('sitename')

        # Now get all optional options
        for i in opts:
            # XXX: this condition is an hack. This is necessary to avoid
            # writing default values, but there may be a better solution.
            if i in list_opts:
                #yop[i] =  cfg.get(name, i, vars = defint)
                yop[i] =  cfg.get(name, i).split(',')

        return _PerflibConfig(dispname, sitename, yop)

    ret = {}
    for i in _PERFLIBS:
        ret[i] = get_perflib_config(i)

    return ret

# A dictionary which keys are the name of the perflib (same than perflib.cfg
# section name) and values a _PerflibConfig instance.
CONFIG = build_config()

class IsFactory:
    def __init__(self, name):
        """Name should be one key of CONFIG."""
        def func(env, libname):
            cache = env['NUMPY_PKG_CONFIG']['LIB'][libname]
            if cache:
                return cache.uses_perflib(name)
            else:
                return False

        self.func = func

class GetVersionFactory:
    def __init__(self, name):
        """Name should be one key of CONFIG."""
        def func(env):
            return env['NUMPY_PKG_CONFIG']['PERFLIB'][name].version
        self.func = func

if __name__ == '__main__':
    for k, v in  CONFIG.items():
        print "++++++++++++++++++++++"
        print k, v
        print '\t',v.opts_factory.clapack_config()
