import sys
import os
import warnings

from os.path import \
        join as pjoin, dirname as pdirname, normpath

from SCons.Util import \
        WhereIs
from SCons.Tool.intelc import \
        generate as old_generate

from numscons.tools.intel_common import get_abi

def generate_linux(env):
    icc = WhereIs('icc')
    if not icc:
        warnings.warn("icc not found")
    topdir = normpath(pjoin(pdirname(icc), os.pardir, os.pardir))
    abi = get_abi(env)
    return old_generate(env, abi=abi, topdir=topdir)

def generate_win32(env):
    # Import here to avoid importing msvc tool on every platform
    import SCons.Tool.msvc
    from SCons.Tool.MSCommon.common import get_output, parse_output
    SCons.Tool.msvc.generate(env)

    abi = get_abi(env)

    # Set up environment
    # XXX: detect this properly
    batfile = r"C:\Program Files (x86)\Intel\Compiler\11.1\038\bin\iclvars.bat"
    out = get_output(batfile, args=abi)
    d = parse_output(out)
    for k, v in d.items():
        env.PrependENVPath(k, v, delete_existing=True)

    env["CC"] = "icl"
    env["SHCC"] = "$CC"

    env["CXX"] = "icl"
    env["SHCXX"] = "$CXX"

    env["CCFLAGS"] = SCons.Util.CLVar("/nologo")

def generate(env):
    if sys.platform.startswith('linux'):
        return generate_linux(env)
    elif sys.platform == 'win32':
        return generate_win32(env)
    else:
        raise RuntimeError('Intel c on %s not supported' % sys.platform)

def exists(env):
    pass
