"""Module to handle compiler configuration. Configuration itself is kept in
.ini like files"""

from ConfigParser import ConfigParser
from os.path import join as pjoin, dirname as pdirname

from numscons.core.utils import DefaultDict

_OPTIONS = ['optim', 'warn', 'debug_sym', 'debug', 'thread', 'extra',
            'link_optim']

class NoCompilerConfig(Exception):
    """This exception is thrown when no configuration for a compiler was
    found."""
    pass

class CompilerConfig(DefaultDict):
    """Place holder for compiler configuration. Behaves like a dictionary."""
    def __init__(self):
        DefaultDict.__init__(self, _OPTIONS)
        for k in self.keys():
            self[k] = []

def get_config(name, language):
    """Returns a CompilerConfig instance for given compiler name and
    language.

    name should be a string (corresponding to the section name in the .cfg
    file), and language should be 'C', 'CXX' or 'F77'."""
    # XXX name should be a list
    config = ConfigParser()
    if language == 'C':
        cfgfname = pjoin(pdirname(__file__), "configurations", "compiler.cfg")
    elif language == 'F77':
        cfgfname = pjoin(pdirname(__file__), "configurations", "fcompiler.cfg")
    elif language == 'CXX':
        cfgfname = pjoin(pdirname(__file__), "configurations",
                         "cxxcompiler.cfg")
    else:
        raise NoCompilerConfig("language %s not recognized !" % language)

    st = config.read(cfgfname)
    if len(st) < 1:
        raise IOError("config file %s not found" % cfgfname)
    if not config.has_section(name):
        raise NoCompilerConfig("compiler %s (lang %s) has no configuration "\
                               "in %s" % (name, language, cfgfname))

    cfg = CompilerConfig()

    for o in config.options(name):
        r = config.get(name, o)
        if r:
            cfg[o] = r.split()

    return cfg
