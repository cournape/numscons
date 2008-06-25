import SCons.Util
import SCons.Tool

from imp import find_module, load_module

def get_cxx():
    fp, pathname, descr = find_module('c++', SCons.Tool.__path__)

    try:
	return load_module('c++', fp, pathname, descr)
    finally:
	if fp:
            fp.close()

    raise ImportError("Could not load c++")

compilers = ['CC']

def generate(env):
    """Add Builders and construction variables for SunPRO C++."""
    get_cxx().generate(env)

    cxx = env.Detect(compilers)

    env['CXX'] = cxx
    env['SHCXXFLAGS']   = SCons.Util.CLVar('$CXXFLAGS -KPIC')
    env['SHOBJPREFIX']  = 'so_'
    env['SHOBJSUFFIX']  = '.o'
    
def exists(env):
    return env.Detect(compilers)
