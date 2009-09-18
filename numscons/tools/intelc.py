import sys
import os
import warnings

from os.path import \
        join as pjoin, dirname as pdirname, normpath

from SCons.Util import \
        WhereIs
from SCons.Tool.intelc import \
        generate as old_generate

# INPUTS:
#   ICC_ABI: x86, amd64

_ARG2ABI = {'x86': 'ia32', 'amd64': 'em64t', 'default': 'ia32'}

def get_abi(env):
    try:
        abi = env['ICC_ABI']
    except KeyError:
        abi = 'default'

    try:
        return _ARG2ABI[abi]
    except KeyError:
        ValueError("Unknown abi %s" % abi)

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
