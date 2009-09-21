import os
from os.path import join as pjoin
import sys
from distutils.sysconfig import get_config_var

from numscons.core.utils import flatten
from numscons.core.misc import get_numscons_toolpaths, get_pythonlib_name, \
     is_f77_gnu, get_vs_version, built_with_mstools, \
     isfortran, isf2py, scons_get_paths, built_with_mingw, is_debug
from numscons.core.errors import InternalError
from numscons.numdist import msvc_runtime_library

def get_pythonlib_dir():
    """Returns a list of path to look for the python engine library
    (pythonX.X.lib on win32, libpythonX.X.so on unix, etc...)."""
    if os.name == 'nt':
        return [pjoin(sys.exec_prefix, 'libs')]
    else:
        return [pjoin(sys.exec_prefix, 'lib')]

def is_bootstrapping(env):
    return env['bootstrapping']

def is_bypassed(env):
    return env['bypass']

def is_importing_environment(env):
    return env['import_env']

def has_f77(env):
    return len(env['f77_opt']) > 0

def customize_tools(env):
    customize_pyext(env)

    finalize_env(env)

    apply_compilers_customization(env)

    customize_link_flags(env)

def customize_pyext(env):
    from SCons.Tool import Tool
    from SCons.Tool.FortranCommon import CreateDialectActions, ShFortranEmitter

    if sys.platform == 'win32' and is_debug(env):
        env['PYEXTSUFFIX'] = "_d%s" % get_config_var('SO')
    else:
        env['PYEXTSUFFIX'] = get_config_var('SO')


    t = Tool('pyext', toolpath = get_numscons_toolpaths(env))
    t(env)

    #-----------------------------------------------
    # Extending pyext to handle fortran source code.
    #-----------------------------------------------
    # XXX: This is ugly: I don't see any way to do this cleanly.
    pyext_obj = t._tool_module().createPythonObjectBuilder(env)

    if env.has_key('F77') and env['F77']:
        shcompaction = CreateDialectActions('F77')[2]
        for suffix in env['F77FILESUFFIXES']:
            pyext_obj.add_action(suffix, shcompaction)
            pyext_obj.add_emitter(suffix, ShFortranEmitter)

    # Customizing pyext to handle windows platform (msvc runtime, etc...)
    # We don't do this in pyext because scons has no infrastructure to know
    # whether we are using mingw or ms
    if sys.platform == 'win32':
        _customize_pyext_win32(env, t)

    # XXX: Add numpy header path (will be used by NumpyExtension builder).
    if is_bootstrapping(env):
        env['NUMPYCPPPATH'] = scons_get_paths(env['include_bootstrap'])
    else:
        from numpy.distutils.misc_util import get_numpy_include_dirs
        env['NUMPYCPPPATH'] = get_numpy_include_dirs()

def _customize_pyext_win32(env, pyext_tool):
    from SCons.Action import Action
    from SCons.Node.FS import default_fs

    env.PrependUnique(LIBPATH = get_pythonlib_dir())

    def dummy(target, source, env):
        return target, source

    def pyext_runtime(target = None, source = None, env = None):
        # Action to handle msvc runtime problem with fortran/mingw: normally,
        # when we link a python extension with mingw, we need to add the msvc
        # runtime. BUT, if the extensions uses fortran, we should not.
        # XXX: Is action the right way to do that ?
        snodes = [default_fs.Entry(s) for s in source]
        if isfortran(env, snodes) or isf2py(env, snodes):
            env["PYEXTRUNTIME"] = [get_pythonlib_name()]
        else:
            env["PYEXTRUNTIME"] = [get_pythonlib_name(),
                                   msvc_runtime_library()]
        return 0

    # We override the default emitter here because SHLIB emitter
    # does a lot of checks we don't care about and are wrong
    # anyway for python extensions.
    env["BUILDERS"]["PythonExtension"].emitter = dummy
    if built_with_mingw(env):
        # We are overriding pyext coms here.
        # XXX: This is ugly
        pycc, pycxx, pylink = pyext_tool._tool_module().pyext_coms('posix')
        env['PYEXTCCCOM'] = pycc
        env['PYEXTCXXCOM'] = pycxx
        env['PYEXTLINKCOM'] = pylink

        pyext_runtime_action = Action(pyext_runtime, '')
        old_action = env['BUILDERS']['PythonExtension'].action
        env['BUILDERS']['PythonExtension'].action = \
            Action([pyext_runtime_action, old_action])

def customize_link_flags(env):
    # We sometimes need to put link flags at the really end of the command
    # line, so we add a construction variable for it
    env['LINKFLAGSEND'] = []
    env['SHLINKFLAGSEND'] = ['$LINKFLAGSEND']
    env['LDMODULEFLAGSEND'] = []

    if built_with_mstools(env):
        from SCons.Action import Action
        # Sanity check: in case scons changes and we are not
        # aware of it
        if not isinstance(env["SHLINKCOM"], list):
            msg = "Internal consistency check failed for MS compiler. This " \
                  "is bug, please contact the maintainer"
            raise InternalError(msg)
        if not isinstance(env["LDMODULECOM"], list):
            msg = "Internal consistency check failed for MS compiler. This " \
                  "is bug, please contact the maintainer"
            raise InternalError(msg)
        # We replace the "real" shlib action of mslink by our
        # own, which only differ in the linkdlagsend flags.
        newshlibaction = Action('${TEMPFILE("$SHLINK $SHLINKFLAGS ' \
                                '$_SHLINK_TARGETS $( $_LIBDIRFLAGS $) ' \
                                '$_LIBFLAGS $SHLINKFLAGSEND $_PDB' \
                                '$_SHLINK_SOURCES")}')
        env["SHLINKCOM"][0] = newshlibaction
        env["LDMODULECOM"][0] = newshlibaction

        newlibaction = '${TEMPFILE("$LINK $LINKFLAGS /OUT:$TARGET.windows ' \
                       '$( $_LIBDIRFLAGS $) $_LIBFLAGS $LINKFLAGSEND $_PDB ' \
                       '$SOURCES.windows")}'
        env["LINKCOM"] = newlibaction
        env['PYEXTLINKCOM'] = '%s $PYEXTLINKFLAGSEND' % env['PYEXTLINKCOM']
    else:
        env['LINKCOM'] = '%s $LINKFLAGSEND' % env['LINKCOM']
        env['SHLINKCOM'] = '%s $SHLINKFLAGSEND' % env['SHLINKCOM']
        env['LDMODULECOM'] = '%s $LDMODULEFLAGSEND' % env['LDMODULECOM']
        env['PYEXTLINKCOM'] = '%s $PYEXTLINKFLAGSEND' % env['PYEXTLINKCOM']

def finalize_env(env):
    """Call this at the really end of the numpy environment initialization."""
    # This will customize some things, to cope with some idiosyncraties with
    # some tools, and are too specific to be in tools.
    if built_with_mstools(env):
        major = get_vs_version(env)[0]
        # For VS 8 and above (VS 2005), use manifest for DLL
        # XXX: this has nothing to do here, too
        if major >= 8:
            env['LINKCOM'] = [env['LINKCOM'],
                      'mt.exe -nologo -manifest ${TARGET}.manifest '\
                      '-outputresource:$TARGET;1']
            env['SHLINKCOM'] = [env['SHLINKCOM'],
                        'mt.exe -nologo -manifest ${TARGET}.manifest '\
                        '-outputresource:$TARGET;2']
            env['LDMODULECOM'] = [env['LDMODULECOM'],
                        'mt.exe -nologo -manifest ${TARGET}.manifest '\
                        '-outputresource:$TARGET;2']

    if is_f77_gnu(env):
        env.AppendUnique(F77FLAGS = ['-fno-second-underscore'])

    if built_with_mingw(env):
        env.AppendUnique(CFLAGS = '-mno-cygwin')

def apply_compilers_customization(env):
    """Apply customization to compilers' flags from the environment. Also take
    into account user customization through shell variables."""
    #------------------------------
    # C compiler last customization
    #------------------------------
    # Apply optim and warn flags considering context
    custom = env['NUMPY_CUSTOMIZATION']['C']
    if 'CFLAGS' in os.environ:
        env.Append(CFLAGS = "%s" % os.environ['CFLAGS'])
        env.AppendUnique(CFLAGS = custom['extra'] + custom['thread'])
    else:
        env.AppendUnique(CFLAGS  = flatten(custom.values()))

    #--------------------------------
    # F77 compiler last customization
    #--------------------------------
    if env.has_key('F77'):
        custom = env['NUMPY_CUSTOMIZATION']['F77']
        if 'FFLAGS' in os.environ:
            env.Append(F77FLAGS = "%s" % os.environ['FFLAGS'])
            env.AppendUnique(F77FLAGS = custom['extra'] + custom['thread'])
        else:
            env.AppendUnique(F77FLAGS  = flatten(custom.values()))

    #--------------------------------
    # CXX compiler last customization
    #--------------------------------
    if env.has_key('CXX'):
        custom = env['NUMPY_CUSTOMIZATION']['CXX']
        if 'CXXFLAGS' in os.environ:
            env.Append(CXXFLAGS = "%s" % os.environ['CXXFLAGS'])
            env.AppendUnique(CXXFLAGS = custom['extra'] + custom['thread'])
        else:
            env.AppendUnique(CXXFLAGS  = flatten(custom.values()))

    if 'LDFLAGS' in os.environ:
        env.Prepend(LINKFLAGS = os.environ['LDFLAGS'])
