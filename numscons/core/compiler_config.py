"""Module to handle compiler configuration.

Configurations are set into config files, and are obtained from get_*_config
functions. The object returned by those functions have a method get_flags_dict
which returns a dictionary which can be copied into scons environments objects
as construction variables."""

from ConfigParser import SafeConfigParser, ConfigParser
from os.path import join as pjoin, dirname as pdirname

from numscons.core.utils import partial, DefaultDict

# XXX: customization from site.cfg or other ?
# XXX: how to cache this between different scons calls
_OPTIONS = ['optim', 'warn', 'debug_sym', 'debug', 'thread', 'extra',
            'link_optim']

class NoCompilerConfig(Exception):
    """This exception is throw when no configuration for a compiler was
    found."""
    pass

class CompilerConfig(DefaultDict):
    """Place holder for compiler configuration."""
    def __init__(self):
        DefaultDict.__init__(self, _OPTIONS)
        for k in self.keys():
            self[k] = []

def get_config(name, language):
    # XXX name should be a list
    config = ConfigParser()
    if language == 'c':
        cfgfname = pjoin(pdirname(__file__), "compiler.cfg")
    elif language == 'f77':
        cfgfname = pjoin(pdirname(__file__), "fcompiler.cfg")
    elif language == 'cxx':
        cfgfname = pjoin(pdirname(__file__), "cxxcompiler.cfg")
    else:
        raise NoCompilerConfig("language %s not recognized !" % language)

    st = config.read(cfgfname)
    if len(st) < 1:
        raise IOError("config file %s not found" % cfgfname)
    if not config.has_section(name):
        raise NoCompilerConfig("compiler %s (lang %s) has no configuration in %s" % (name, language, cfgfname))

    cfg = CompilerConfig()

    for o in config.options(name):
        r = config.get(name, o)
        if r:
            cfg[o] = r.split()

    return cfg

get_cc_config = partial(get_config, language = 'c')
get_f77_config = partial(get_config, language = 'f77')
get_cxx_config = partial(get_config, language = 'cxx')

if __name__ == '__main__':
    cfg = get_cc_config('gcc')
    print cfg.items()

    cfg = get_f77_config('g77')
    print cfg.items()
