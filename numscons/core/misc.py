from os.path import join, dirname

import numscons

def get_scons_path():
    return join(dirname(numscons.__file__), 'scons-local')

# Those built_* are not good: we should have a better way to get the real type
# of compiler instead of being based on names (to support things like colorgcc,
# gcc-4.2, etc...). Fortunately, we mostly need this on MS platform only.
def built_with_mstools(env):
    """Return True if built with MS tools (compiler + linker)."""
    return env['cc_opt'] == 'msvc'

def built_with_mingw(env):
    """Return true if built with mingw compiler."""
    return env['cc_opt'] == 'mingw'

def built_with_gnu_f77(env):
    """Return true if f77 compiler is gnu (g77, gfortran, etc...)."""
    return env['f77_opt'] == 'g77' or env['f77_opt'] == 'gfortran'

def get_pythonlib_name(debug = 0):
    """Return the name of python library (necessary to link on NT with
    mingw."""
    # Yeah, distutils burried the link option on NT deep down in
    # Extension module, we cannot reuse it !
    if debug == 1:
        template = 'python%d%d_d'
    else:
        template = 'python%d%d'

    return template % (sys.hexversion >> 24, 
		       (sys.hexversion >> 16) & 0xff)


