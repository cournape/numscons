"""Module to handle compiler configuration. Configuration itself is kept in
.ini like files"""
import sys

from ConfigParser import ConfigParser
from os.path import join as pjoin, dirname as pdirname

from numscons.core.utils import DefaultDict
from numscons.core.misc import _CONFDIR

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

def _get_win32_config_files(filename):
    # We import platform here as we only need it for windows and platform
    # import is relatively slow
    import platform

    files = [pjoin(_CONFDIR, 'win32', filename)]
    if platform.architecture()[0] == '64bit':
        files.append(pjoin(_CONFDIR, 'win64', filename))
    return files

def get_config_files(filename):
    """Return the list of configuration files to consider for perflib
    configuration."""
    if sys.platform == 'win32':
        return _get_win32_config_files(filename)
    else:
        return [pjoin(_CONFDIR, filename)]

def get_config(name, language):
    """Returns a CompilerConfig instance for given compiler name and
    language.

    name should be a string (corresponding to the section name in the .cfg
    file), and language should be 'C', 'CXX' or 'F77'."""
    # XXX: ugly backward compat stuff
    if name == 'intelc':
        name = 'icc'
    # XXX name should be a list
    config = ConfigParser()
    if language == 'C':
        files = get_config_files("compiler.cfg")
    elif language == 'F77':
        files = get_config_files("fcompiler.cfg")
    elif language == 'CXX':
        files = get_config_files("cxxcompiler.cfg")
    else:
        raise NoCompilerConfig("language %s not recognized !" % language)

    st = config.read(files)
    if len(st) < 1:
        raise IOError("config file %s not found" % files)
    if not config.has_section(name):
        raise NoCompilerConfig("compiler %s (lang %s) has no configuration "\
                               "in %s" % (name, language, files))

    cfg = CompilerConfig()

    for o in config.options(name):
        r = config.get(name, o)
        if r:
            cfg[o] = r.split()

    return cfg
