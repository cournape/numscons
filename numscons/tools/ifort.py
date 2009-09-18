import sys
import warnings

from SCons.Util import \
        WhereIs
from SCons.Tool.ifort import \
        generate as old_generate

def generate_linux(env):
    ifort = WhereIs('ifort')
    if not ifort:
        warnings.warn("ifort not found")
    return old_generate(env)

def generate(env):
    if sys.platform.startswith('linux'):
        return generate_linux(env)
    else:
        raise RuntimeError('Intel fortran on %s not supported' % sys.platform)

def exists(env):
    pass
