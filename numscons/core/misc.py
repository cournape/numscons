"""Misc utilities which did not find they way elsewhere."""

import sys
import os
import re

from os.path import join as pjoin, dirname as pdirname, basename as pbasename

import numscons

_CONFDIR = pjoin(pdirname(numscons.__file__), 'configurations')

# XXX: this is ugly, better find the mathlibs with a checker 
# XXX: this had nothing to do here, too...
def scons_get_paths(paths):
    return paths.split(os.pathsep)

def get_scons_path():
    """Returns the name of the directory where our local scons is."""
    return pjoin(pdirname(numscons.__file__), 'scons-local')

def get_scons_build_dir():
    """Return the top path where everything produced by scons will be put.

    The path is relative to the top setup.py"""
    return pjoin('build', 'scons')

def get_scons_configres_dir():
    """Return the top path where everything produced by scons will be put.

    The path is relative to the top setup.py"""
    return pjoin('build', 'scons-configres')

def get_scons_configres_filename():
    """Return the top path where everything produced by scons will be put.

    The path is relative to the top setup.py"""
    return '__configres.py'

# Those built_* are not good: we should have a better way to get the real type
# of compiler instead of being based on names (to support things like colorgcc,
# gcc-4.2, etc...). Fortunately, we mostly need this on MS platform only.
def built_with_mstools(env):
    """Return True if built with MS tools (compiler + linker)."""
    return env['cc_opt'] == 'msvc'

def built_with_mingw(env):
    """Return true if C code built with mingw compiler."""
    return env['CC'] == 'gcc' and sys.platform == 'win32'

def built_with_gnu_f77(env):
    """Return true if f77 compiler is gnu (g77, gfortran, etc...)."""
    return env['f77_opt'] == 'g77' or env['f77_opt'] == 'gfortran'

def built_with_ifort(env):
    """Return true if f77 compiler is Intel Fortran compiler."""
    return env['f77_opt'] == 'ifort'

def is_python_win64():
    # XXX: import it here because it takes some time
    import platform
    return sys.platform == "win32" and platform.architecture()[0] == '64bit'

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

def pyplat2sconsplat():
    """Returns the scons platform."""
    # XXX: should see how env['PLATFORM'] is defined, make this a dictionary
    if sys.platform[:5] == 'linux':
        return 'posix'
    elif sys.platform[:5] == 'sunos':
        return 'sunos'
    else:
        return sys.platform

def get_local_toolpaths():
    """Returns the full pathname for the numscons tools directory."""
    return [pdirname(numscons.tools.__file__)]

def get_custom_toolpaths(env):
    """Returns the list of user-customized pathnames for scons tools."""
    if env['scons_tool_path']:
        return env['scons_tool_path'].split(os.pathsep)
    else:
        return []

def get_numscons_toolpaths(env):
    """Returns the full list of pathnames where to look for scons tools."""
    toolp = []
    # Put custom toolpath FIRST !
    toolp.extend(get_custom_toolpaths(env))
    toolp.extend(get_local_toolpaths())
    return toolp

def is_f77_gnu(env):
    """Returns true if F77 in env is a Gnu fortran
    compiler."""
    # XXX: do this properly
    if env.has_key('F77'):
        fullpath = env['F77']
        return pbasename(fullpath) == 'g77' or pbasename(fullpath) == 'gfortran'
    else:
        return False

def get_vs_version(env):
    """Returns the visual studio version."""
    try:
        version = env['MSVS']['VERSION']
        m = re.compile("([0-9]).([0-9])").match(version)
        if m:
            major = int(m.group(1))
            minor = int(m.group(2))
            return (major, minor)
        else:
            raise RuntimeError("FIXME: failed to parse VS version")
    except KeyError:
        raise RuntimeError("Could not get VS version !")

def cc_version(env):
    """Return version number as a float of the C compiler, if available, None
    otherwise."""
    if built_with_mstools(env):
        ma, mi = get_vs_version(env)
        return ma + 0.1 * mi

    return None

def isfortran(env, source):
    """Return 1 if any of code in source has fortran files in it, 0
    otherwise."""
    try:
        fsuffixes = env['FORTRANSUFFIXES']
    except KeyError:
        # If no FORTRANSUFFIXES, no fortran tool, so there is no need to look
        # for fortran sources.
        return 0

    if not source:
        # Source might be None for unusual cases like SConf.
        return 0
    for s in source:
        if s.sources:
            ext = os.path.splitext(str(s.sources[0]))[1]
            if ext in fsuffixes:
                return 1
    return 0

def isf2py(env, source):
    """Return 1 if any of code in source has f2py interface files in it, 0
    otherwise."""
    fsuffixes = ['.pyf']

    if not source:
        # Source might be None for unusual cases like SConf.
        return 0
    for s in source:
        if s.sources:
            ext = os.path.splitext(str(s.sources[0]))[1]
            if ext in fsuffixes:
                return 1
    return 0

# No easy way to retrieve this function from scons (because of the + in the
# module name, cannot be easily imported).
def iscplusplus(source):
    import SCons

    # We neeed to copy this too...
    CXXSuffixes = ['.cpp', '.cc', '.cxx', '.c++', '.C++', '.mm']
    if SCons.Util.case_sensitive_suffixes('.c', '.C'):
        CXXSuffixes.append('.C')

    if not source:
        # Source might be None for unusual cases like SConf.
        return 0
    for s in source:
        if s.sources:
            ext = os.path.splitext(str(s.sources[0]))[1]
            if ext in CXXSuffixes:
                return 1
    return 0

def is_debug(env):
    try:
        r = env["debug"]
        if r:
            return 1
        return 0
    except KeyError:
        return 0

def get_last_error_from_config(lines, ncontexts = 1):
    """Parse the content the config.log to get the last error only from it."""
    # Each failed target in config file display its output or command in a list
    # of strings prefixed by |. So we find all the lines from the end of the
    # log content up to the before last section with such a prefix. For
    # example, if the end of the content is this:
    #
    # bla bla error N
    # | bla bla
    # bla bla error N+1
    # | bla bla
    # bla bla
    #
    # we want to get only
    #
    # bla bla error N+1
    # | bla bla
    # bla bla
    #
    # One block with | is one context.
    YOP = re.compile(r"^\s*\|")

    i = len(lines) - 1
    while not YOP.match(lines[i]):
        i -= 1
    for n in range(ncontexts):
        while YOP.match(lines[i]) and i >= 0:
            i -= 1
        while not YOP.match(lines[i]) and i >= 0:
            i -= 1
        if i < 0:
            break

    return lines[i+1:]
