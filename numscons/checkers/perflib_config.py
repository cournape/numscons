#! /usr/bin/env python
# Last Change: Wed Jan 09 12:00 AM 2008 J
from os.path import join as pjoin, dirname as pdirname
from ConfigParser import SafeConfigParser, RawConfigParser

from numscons.numdist import default_lib_dirs

from numscons.core.utils import DefaultDict
from configuration import available_opts_flags

_PERFLIBS = ('GenericBlas', 'GenericLapack', 'MKL', 'ATLAS', 'Accelerate',
             'vecLib', 'Sunperf', 'FFTW2', 'FFTW3')

#------------------------
# Generic functionalities
#------------------------
class PerflibConfig:
    """A class which contain all the information for a given performance
    library, including build options (cflags, libs, path, etc....) and meta
    information (name, version, how to check)."""
    def __init__(self, values):
        """Initialize the configuration."""
        self.values = values
        self.name = values['dispname']
        self.section = values['sitename']
        #self.defopts = defopts
        self.headers = values['htc']
        self.funcs = values['ftc']
        #self.version_checker = version_checker

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        repr = ["Display name: %s" % self.name]
        repr += ["Section name: %s" % self.section]
        repr += ["Headers to check : %s" % self.headers]
        repr += ["Funcs to check : %s" % self.funcs]
        return '\n'.join(repr)

#-------------------------------------------
# Perflib specific configuration and helpers
#-------------------------------------------
def build_config():
    # opts contain a list of all available options available in perflib.cfg
    list_opts = list(available_opts_flags())
    list_opts.append('htc')
    list_opts.append('ftc')
    str_opts = ['dispname', 'sitename']

    defint = {'atlas_def_libs' : 
              ','.join([pjoin(i, 'atlas') for i in default_lib_dirs])}

    cfg = SafeConfigParser()

    st = cfg.read(pjoin(pdirname(__file__), 'perflib.cfg'))
    # XXX: check this properly
    assert len(st) > 0

    def get_perflib_config(name):
        yop = DefaultDict(avkeys = str_opts + list_opts)
        for i in cfg.options(name):
            yop[i] =  cfg.get(name, i, vars = defint)

        for k  in list_opts:
            v = yop[k]
            if v is not None:
                v.split(',')

        return PerflibConfig(yop)

    ret = {}
    for i in _PERFLIBS:
        ret[i] = get_perflib_config(i)

    return ret
        
CONFIG = build_config()

class IsFactory:
    def __init__(self, name):
        """Name should be one key of CONFIG."""
        try:
            CONFIG[name]
        except KeyError, e:
            raise RuntimeError("name %s is unknown")

        def f(env, libname):
            if env['NUMPY_PKG_CONFIG'][libname] is None:
                return 0 == 1
            else:
                return env['NUMPY_PKG_CONFIG'][libname].name == \
                       CONFIG[name].name
        self.func = f

    def get_func(self):
        return self.func

class GetVersionFactory:
    def __init__(self, name):
        """Name should be one key of CONFIG."""
        try:
            CONFIG[name]
        except KeyError, e:
            raise RuntimeError("name %s is unknown")

        def f(env, libname):
            if env['NUMPY_PKG_CONFIG'][libname] is None or \
               not env['NUMPY_PKG_CONFIG'][libname].name == CONFIG[name].name:
                return 'No version info'
            else:
                return env['NUMPY_PKG_CONFIG'][libname].version
        self.func = f

    def get_func(self):
        return self.func

if __name__ == '__main__':
    for k, v in CONFIG.items():
        print "++++++++++++++++++"
        print k
        print v
