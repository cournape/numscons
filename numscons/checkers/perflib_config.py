#! /usr/bin/env python
# Last Change: Wed Jan 09 12:00 AM 2008 J
from os.path import join as pjoin, dirname as pdirname
from ConfigParser import SafeConfigParser, RawConfigParser

from numscons.numdist import default_lib_dirs

from numscons.core.utils import DefaultDict

_PERFLIBS = ('GenericBlas', 'GenericLapack', 'MKL', 'ATLAS', 'Accelerate',
             'vecLib', 'Sunperf', 'FFTW2', 'FFTW3')

#------------------------
# Generic functionalities
#------------------------
class PerflibConfig:
    """A class which contain all the information for a given performance
    library, including build options (cflags, libs, path, etc....) and meta
    information (name, version, how to check)."""
    def __init__(self, name, section, defopts, headers, funcs, 
                 version_checker = None):
        """Initialize the configuration.

        Args:
            - name : str
                the name of the perflib
            - section : str
                the name of the section used in site.cfg for customization
            - defopts : BuildOpts
                the compilation configuration for the checker
            - headers : list
                the list of headers to test in the checker
            - funcs : list
                the list of functions to test in the checker.
            - version_checker : callable
                optional function to check version of the perflib. Its
                arguments should be env and opts, where env is a scons
                environment and opts a BuildOpts instance. It should return an
                integer (1 if successfull) and a version string."""
                
        self.name = name
        self.section = section
        self.defopts = defopts
        self.headers = headers
        self.funcs = funcs
        self.version_checker = version_checker

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
    opts = ['cpppath', 'cflags', 'libpath', 'libs', 'linkflags', 'rpath',
            'frameworks']
    defint = {'atlas_def_libs' : 
              ','.join([pjoin(i, 'atlas') for i in default_lib_dirs])}
    cfg = SafeConfigParser()

    st = cfg.read(pjoin(pdirname(__file__), 'perflib.cfg'))
    # XXX: check this properly
    assert len(st) > 0

    def get_perflib_config(name):
        yop = {}
        for i in cfg.options(name):
            yop[i] =  cfg.get(name, i, vars = defint)

        dispname = yop['dispname']
        sitename = yop['sitename']

        htc = None
        if yop.has_key('htc'):
            htc = yop['htc'].split(',')
        ftc = None
        if yop.has_key('ftc'):
            ftc = yop['ftc'].split(',')

        defopts = DefaultDict(avkeys = opts)
        for k in yop.keys():
            if defopts.has_key(k):
                defopts[k] = yop[k].split(',')

        return PerflibConfig(dispname, sitename, defopts, htc, ftc)

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
