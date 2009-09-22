import sys
import os
import warnings

from SCons.Util import \
        WhereIs
from SCons.Tool.ifort import \
        generate as old_generate

from numscons.tools.intel_common import get_abi
from numscons.tools.intel_common.win32 import find_fc_versions, product_dir_fc

_ABI2BATABI = {"amd64": "intel64", "ia32": "ia32"}

def generate_linux(env):
    ifort = WhereIs('ifort')
    if not ifort:
        warnings.warn("ifort not found")
    return old_generate(env)

def generate_win32(env):
    # Import here to avoid importing msvc tool on every platform
    from SCons.Tool.MSCommon.common import get_output, parse_output

    abi = get_abi(env, lang='FORTRAN')

    # Get product dir
    versdict = find_fc_versions(abi)
    vers = sorted(versdict.keys())[::-1]
    pdir = product_dir_fc(versdict[vers[0]])
    batfile = os.path.join(pdir, "bin", "ifortvars.bat")

    out = get_output(batfile, args=_ABI2BATABI[abi])
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
