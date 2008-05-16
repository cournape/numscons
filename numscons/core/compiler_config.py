from ConfigParser import SafeConfigParser, ConfigParser
from os.path import join as pjoin, dirname as pdirname

from numscons.core.utils import partial

"""Module to handle compiler configuration.

Configurations are set into config files, and are obtained from get_*_config
functions. The object returned by those functions have a method get_flags_dict
which returns a dictionary which can be copied into scons environments objects
as construction variables."""

# XXX: customization from site.cfg or other ?
# XXX: how to cache this between different scons calls
_OPTIONS = ['optim', 'warn', 'debug_sym', 'debug', 'thread', 'extra',
            'link_optim']

class NoCompilerConfig(Exception):
    """This exception is throw when no configuration for a compiler was
    found."""
    pass

class Config:
    """Place holder for compiler configuration."""
    def __init__(self):
        self._dic = dict([(i, None) for i in _OPTIONS])

    def __getitem__(self, key):
        return self._dic[key]

    def __setitem__(self, key, item):
        self._dic[key] = item

class CompilerConfig:
    """Put config objects value into a dictionary usable by scons. C compiler
    version"""
    def __init__(self, cfg):
        self._cfg = cfg

    def get_flags_dict(self):
        d = {'NUMPY_OPTIM_CFLAGS' : self._cfg['optim'],
             'NUMPY_OPTIM_LDFLAGS' : self._cfg['link_optim'],
             'NUMPY_WARN_CFLAGS' : self._cfg['warn'],
             'NUMPY_THREAD_CFLAGS' : self._cfg['thread'],
             'NUMPY_EXTRA_CFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_CFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_SYMBOL_CFLAGS' : self._cfg['debug_sym']}
        for k, v in d.items():
            if v is None:
                d[k] = []
            else:
                d[k] = v.split()
        return d

class F77CompilerConfig:
    """Put config objects value into a dictionary usable by scons. Fortran 77
    compiler version"""
    def __init__(self, cfg):
        self._cfg = cfg

    def get_flags_dict(self):
        d = {'NUMPY_OPTIM_FFLAGS' : self._cfg['optim'],
             'NUMPY_WARN_FFLAGS' : self._cfg['warn'],
             'NUMPY_THREAD_FFLAGS' : self._cfg['thread'],
             'NUMPY_EXTRA_FFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_FFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_SYMBOL_FFLAGS' : self._cfg['debug_sym']}
        for k, v in d.items():
            if v is None:
                d[k] = []
            else:
                d[k] = v.split()
        return d

class CXXCompilerConfig:
    """Put config objects value into a dictionary usable by scons. C++ compiler
    version"""
    def __init__(self, cfg):
        self._cfg = cfg

    def get_flags_dict(self):
        d = {'NUMPY_OPTIM_CXXFLAGS' : self._cfg['optim'],
             'NUMPY_WARN_CXXFLAGS' : self._cfg['warn'],
             'NUMPY_THREAD_CXXFLAGS' : self._cfg['thread'],
             'NUMPY_EXTRA_CXXFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_CXXFLAGS' : self._cfg['debug'],
             'NUMPY_DEBUG_SYMBOL_CXXFLAGS' : self._cfg['debug_sym']}
        for k, v in d.items():
            if v is None:
                d[k] = []
            else:
                d[k] = v.split()
        return d

def get_config(name, language):
    # XXX name should be a list
    config = ConfigParser()
    if language == 'c':
        cfgfname = pjoin(pdirname(__file__), "compiler.cfg")
        cmpcfg = CompilerConfig
    elif language == 'f77':
        cfgfname = pjoin(pdirname(__file__), "fcompiler.cfg")
        cmpcfg = F77CompilerConfig
    elif language == 'cxx':
        cfgfname = pjoin(pdirname(__file__), "cxxcompiler.cfg")
        cmpcfg = CXXCompilerConfig
    else:
        raise NoCompilerConfig("language %s not recognized !" % language)

    st = config.read(cfgfname)
    if len(st) < 1:
        raise IOError("config file %s not found" % cfgfname)
    if not config.has_section(name):
        raise NoCompilerConfig("compiler %s has no configuration" % name)

    cfg = Config()

    for o in config.options(name):
        cfg[o] = config.get(name, o)

    return cmpcfg(cfg)

get_cc_config = partial(get_config, language = 'c')
get_f77_config = partial(get_config, language = 'f77')
get_cxx_config = partial(get_config, language = 'cxx')

if __name__ == '__main__':
    cfg = get_cc_config('gcc')
    cc = CompilerConfig(cfg)
    print cc.get_flags_dict()

    cfg = get_f77_config('g77')
    cc = CompilerConfig(cfg)
    print cc.get_flags_dict()
