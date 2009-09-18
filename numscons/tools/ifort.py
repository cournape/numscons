import sys
import warnings

from SCons.Util import \
        WhereIs
from SCons.Tool.ifort import \
        generate as old_generate

from numscons.tools.intel_common import get_abi

def generate_linux(env):
    ifort = WhereIs('ifort')
    if not ifort:
        warnings.warn("ifort not found")
    return old_generate(env)

def generate_win32(env):
    # Import here to avoid importing msvc tool on every platform
    from SCons.Tool.MSCommon.common import get_output, parse_output

    abi = get_abi(env, lang='FORTRAN')

    # Set up environment
    # XXX: detect this properly
    batfile = r"C:\Program Files\Intel\Compiler\11.1\038\bin\ifortvars.bat"
    out = get_output(batfile, args=abi)
    d = parse_output(out)
    for k, v in d.items():
        env.PrependENVPath(k, v, delete_existing=True)

    return old_generate(env)

def generate(env):
    if sys.platform.startswith('linux'):
        return generate_linux(env)
    elif sys.platform == 'win32':
        return generate_win32(env)
    else:
        raise RuntimeError('Intel fortran on %s not supported' % sys.platform)

def exists(env):
    pass
