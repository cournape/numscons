#! /usr/bin/env python
# Last Change: Sun Jan 06 08:00 PM 2008 J
from os.path import join as pjoin, dirname as pdirname
from ConfigParser import SafeConfigParser, RawConfigParser

from numscons.numdist import default_lib_dirs

from numscons.core.utils import DefaultDict

#------------------------
# Generic functionalities
#------------------------
class PerflibConfig:
    def __init__(self, name, section, defopts, headers, funcs, version_checker = None):
        """Initialize the configuration.

        Args:
            - name : str
                the name of the perflib
            - section : str
                the name of the section used in site.cfg for customization
            - defopts : ConfigOpts
                the compilation configuration for the checker
            - headers : list
                the list of headers to test in the checker
            - funcs : list
                the list of functions to test in the checker.
            - version_checker : callable
                optional function to check version of the perflib. Its
                arguments should be env and opts, where env is a scons
                environment and opts a ConfigOpts instance. It should return an
                integer (1 if successfull) and a version string."""
                
        self.name = name
        self.section = section
        self.defopts = defopts
        self.headers = headers
        self.funcs = funcs
        self.version_checker = version_checker

#-------------------------------------------
# Perflib specific configuration and helpers
#-------------------------------------------
def build_config():
    perflib = ['GenericBlas', 'GenericLapack', 'MKL', 'ATLAS', 'Accelerate',
               'vecLib', 'Sunperf', 'FFTW2', 'FFTW3']
    opts = ['cpppath', 'cflags', 'libpath', 'libs', 'linkflags', 'rpath',
            'frameworks']
    defint = {'atlas_def_libs' : 
              ','.join([pjoin(i, 'atlas') for i in default_lib_dirs])}
    cfg = SafeConfigParser()

    st = cfg.read(pjoin(pdirname(__file__), 'perflib.cfg'))
    # XXX: check this properly
    assert len(st) > 0

    def get_perflib_config(name):
        yop =  DefaultDict(avkeys = opts)
        for i in cfg.options(name):
            yop[i] =  cfg.get(name, i, vars = defint).split(',')

        return yop

    ret = {}
    for i in perflib:
        ret[i] = get_perflib_config(i)

    return ret
        
_PCONFIG = build_config()

CONFIG = {
        'GenericBlas': PerflibConfig('BLAS', 'blas', 
                                    _PCONFIG['GenericBlas'],
                                    [], []),
        'GenericLapack': PerflibConfig('LAPACK', 'lapack', 
                                      _PCONFIG['GenericLapack'],
                                      [], []),
        'MKL': PerflibConfig('MKL', 'mkl', _PCONFIG['MKL'],
                             ['mkl.h'], ['MKLGetVersion']),
        'ATLAS': PerflibConfig('ATLAS', 'atlas', _PCONFIG['ATLAS'], 
                               ['atlas_enum.h'], ['ATL_sgemm']),
        'Accelerate' : PerflibConfig('Framework: Accelerate', 'accelerate', 
                                      _PCONFIG['Accelerate'],
                                      ['Accelerate/Accelerate.h'],
                                      ['cblas_sgemm']),
        'vecLib' : PerflibConfig('Framework: vecLib', 'vecLib', 
                                 _PCONFIG['vecLib'],
                                 ['vecLib/vecLib.h'],
                                 ['cblas_sgemm']),
        'Sunperf' : PerflibConfig('Sunperf', 'sunperf', 
                                  _PCONFIG['Sunperf'],
                                  ['sunperf.h'],
                                  ['cblas_sgemm']),
        'FFTW3' : PerflibConfig('FFTW3', 'fftw', _PCONFIG['FFTW3'],
                                ['fftw3.h'], ['fftw_cleanup']),
        'FFTW2' : PerflibConfig('FFTW2', 'fftw', _PCONFIG['FFTW2'],
                                ['fftw.h'], ['fftw_forget_wisdom'])
        }

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
