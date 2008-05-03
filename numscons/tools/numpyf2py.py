"""numpyf2py Tool

f2py tool which knows about distutils directories.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""
from copy import deepcopy

from numscons.core import distutils_dirs_emitter

import numscons.tools.f2py as f2py

def generate(env):
    if not env['BUILDERS'].has_key('F2py'):
        f2py.generate(env)

    bld = deepcopy(env['BUILDERS']['F2py'])
    bld.emitter.insert(0, distutils_dirs_emitter)
    env['BUILDERS']['NumpyF2py'] = bld

def exists(env):
    return f2py.exists(env)
