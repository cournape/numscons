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

def generate(env):
    if sys.platform.startswith('linux'):
        return generate_linux(env)
    else:
        raise RuntimeError('Intel c on %s not supported' % sys.platform)

def exists(env):
    pass
