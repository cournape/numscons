# Last Changed: .

"""This initialize a scons environment using info from distutils, and all our
customization (python extension builders, build_dir, etc...)."""

import sys
import os
from os.path import join as pjoin, basename

from numscons.core.custom_builders import DistutilsSharedLibrary, NumpyCtypes, \
     DistutilsPythonExtension, DistutilsStaticExtLibrary, NumpyPythonExtension
from numscons.core.initialization import initialize_tools
from numscons.core.siteconfig import get_config
from numscons.core.extension_scons import createStaticExtLibraryBuilder
from numscons.core.extension import get_pythonlib_dir
from numscons.core.utils import pkg_to_path, flatten
from numscons.core.misc import get_numscons_toolpaths, get_pythonlib_name, \
     is_f77_gnu, get_vs_version, built_with_mstools, \
     isfortran, isf2py, scons_get_paths, get_scons_build_dir, \
     get_scons_configres_filename, built_with_mingw

from numscons.core.template_generators import generate_from_c_template, \
     generate_from_f_template, generate_from_template_emitter, \
     generate_from_template_scanner

from numscons.tools.substinfile import TOOL_SUBST

from numscons.numdist import msvc_runtime_library

__all__ = ['GetNumpyEnvironment', 'GetInitEnvironment']

def GetNumpyOptions(args):
    """Call this with args=ARGUMENTS to take into account command line args."""
    from SCons.Options import Options, EnumOption, BoolOption

    opts = Options(None, args)

    opts.Add('scons_tool_path',
             'comma-separated list of directories to look '\
             'for tools (take precedence over internal ones)',
             '')

    # Add directories related info
    opts.Add('pkg_name',
             'name of the package (including parent package if any)', '')
    opts.Add('src_dir', 'src dir relative to top called', '.')
    opts.Add('build_prefix', 'build prefix (NOT including the package name)',
             get_scons_build_dir())
    opts.Add('distutils_libdir',
             'build dir for libraries of distutils (NOT including '\
             'the package name)',
             pjoin('build', 'lib'))
    opts.Add('include_bootstrap',
             "include directories for boostraping numpy (if you do not know" \
             " what that means, you don't need it)" ,
             '')

    # Add compiler related info
    opts.Add('cc_opt', 'name of C compiler', '')
    opts.Add('cc_opt_path', 'path of the C compiler set in cc_opt', '')

    opts.Add('f77_opt', 'name of F77 compiler', '')
    opts.Add('f77_opt_path', 'path of the F77 compiler set in cc_opt', '')

    opts.Add('cxx_opt', 'name of C compiler', '')
    opts.Add('cxx_opt_path', 'path of the C compiler set in cc_opt', '')

    # Silent mode
    # XXX: scons does not have a canned option for integer, EnumOption won't
    # accept integers...
    opts.Add(EnumOption('silent',
                        '0 means max verbose, 1 less verbose, and 2 '\
                        'almost nothing',
                        '0', allowed_values = ('0', '1', '2')))
    opts.Add(BoolOption('bootstrapping',
                        "true if bootrapping numpy, false if not", 0))

    return opts

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
    """Apply customization for compilers' flags to the environment."""
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

    # XXX: what to do about linkflags ?
    #env.AppendUnique(LINKFLAGS = env['NUMPY_OPTIM_LDFLAGS'])

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

def GetNumpyEnvironment(args):
    """Returns a correctly initialized scons environment.

    This environment contains builders for python extensions, ctypes
    extensions, fortran builders, etc... Generally, call it with args =
    ARGUMENTS, which contain the arguments given to the scons process.

    This method returns an environment with fully customized flags."""
    env = _get_numpy_env(args)

    return env

def has_f77(env):
    return len(env['f77_opt']) > 0

def set_bootstrap(env):
    import __builtin__
    if env['bootstrapping']:
        __builtin__.__NUMPY_SETUP__ = True

def is_bootstrapping(env):
    return env['bootstrapping']

def _init_environment(args):
    from numscons.core.numpyenv import NumpyEnvironment
    from SCons.Defaults import DefaultEnvironment
    from SCons.Script import Help

    opts = GetNumpyOptions(args)
    env = NumpyEnvironment(options = opts)

    set_bootstrap(env)

    # We explicily set DefaultEnvironment to avoid wasting time on initializing
    # tools a second time.
    DefaultEnvironment(tools = [])

    Help(opts.GenerateHelpText(env))

    return env

def GetInitEnvironment(args):
    return _init_environment(args)

def _get_numpy_env(args):
    """Call this with args = ARGUMENTS."""
    env = _init_environment(args)

    customize_scons_env(env)
    customize_scons_dirs(env)

    # Getting the config options from *.cfg files
    set_site_config(env)

    set_verbosity(env)

    #------------------------------------------------
    # Setting tools according to command line options
    #------------------------------------------------
    initialize_tools(env)

    #---------------
    #     Misc
    #---------------
    customize_tools(env)

    # Adding custom builders
    add_custom_builders(env)

    return env

def customize_scons_env(env):
    #--------------------------------------------------
    # Customize scons environment from user environment
    #--------------------------------------------------
    env["ENV"]["PATH"] = os.environ["PATH"]

    # Add HOME in the environment: some tools seem to require it (Intel
    # compiler, for licenses stuff)
    if os.environ.has_key('HOME'):
        env['ENV']['HOME'] = os.environ['HOME']

    # XXX: Make up my mind about importing env or not at some point
    if os.environ.has_key('LD_LIBRARY_PATH'):
        env["ENV"]["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH"]

def set_verbosity(env):
    level = int(env['silent'])

    if level > 0:
        env['F2PYCOMSTR']           = "F2PY               $SOURCE"

        env['CCCOMSTR']             = "CC                 $SOURCE"
        env['SHCCCOMSTR']           = "SHCC               $SOURCE"

        env['CXXCOMSTR']            = "CXX                $SOURCE"
        env['SHCXXCOMSTR']          = "SHCXX              $SOURCE"

        env['PYEXTCCCOMSTR']        = "PYEXTCC            $SOURCE"
        env['PYEXTCXXCOMSTR']       = "PYEXTCXX           $SOURCE"
        env['PYEXTLINKCOMSTR']      = "PYEXTLINK          $SOURCE"

        env['F77COMSTR']            = "F77                $SOURCE"
        env['SHF77COMSTR']          = "SHF77              $SOURCE"

        env['ARCOMSTR']             = "AR                 $SOURCE"
        env['RANLIBCOMSTR']         = "RANLIB             $SOURCE"
        env['LDMODULECOMSTR']       = "LDMODULE           $SOURCE"

        env['INSTALLSTR']           = "INSTALL            $SOURCE"

        env['ARRAPIGENCOMSTR']      = "GENERATE ARRAY API $SOURCE"
        env['UFUNCAPIGENCOMSTR']    = "GENERATE UFUNC API $SOURCE"
        env['TEMPLATECOMSTR']       = "FROM TEMPLATE      $SOURCE"
        env['UMATHCOMSTR']          = "GENERATE UMATH     $SOURCE"

        env['CTEMPLATECOMSTR']      = "FROM C TEMPLATE    $SOURCE"
        env['FTEMPLATECOMSTR']      = "FROM F TEMPLATE    $SOURCE"

def set_site_config(env):
    config = get_config(str(env.fs.Top))
    env['NUMPY_SITE_CONFIG'] = config

    # This will be used to keep configuration information on a per package basis
    env['NUMPY_PKG_CONFIG'] = {'PERFLIB' : {}, 'LIB' : {}}
    env['NUMPY_PKG_CONFIG_FILE'] = get_scons_configres_filename()

def customize_scons_dirs(env):
    # Keep NumpyConfigure for backward compatibility...
    env.NumpyConfigure = env.Configure

    # Put sconsign file in build dir

    # XXX: ugly hack ! SConsign needs an absolute path or a path relative to
    # where the SConstruct file is. We have to find the path of the build dir
    # relative to the src_dir: we add n .., where n is the number of occurances
    # of the path separator in the src dir.
    def get_build_relative_src(srcdir, builddir):
        n = srcdir.count(os.sep)
        if len(srcdir) > 0 and not srcdir == '.':
            n += 1
        return pjoin(os.sep.join([os.pardir for i in range(n)]), builddir)

    sconsign = pjoin(get_build_relative_src(env['src_dir'],
                                            env['build_dir']),
                     'sconsign.dblite')
    env.SConsignFile(sconsign)

def add_custom_builders(env):
    """Call this to add all our custom builders to the environment."""
    from SCons.Scanner import Scanner
    from SCons.Builder import Builder
    from SCons.Action import Action

    # Add the file substitution tool
    TOOL_SUBST(env)

    # XXX: Put them into tools ?
    env['BUILDERS']['DistutilsSharedLibrary'] = DistutilsSharedLibrary
    env['BUILDERS']['NumpyCtypes'] = NumpyCtypes
    env['BUILDERS']['DistutilsPythonExtension'] = DistutilsPythonExtension
    env['BUILDERS']['NumpyPythonExtension'] = NumpyPythonExtension

    tpl_scanner = Scanner(function = generate_from_template_scanner,
                          skeys = ['.src'])
    env['BUILDERS']['FromCTemplate'] = Builder(
                action = Action(generate_from_c_template, '$CTEMPLATECOMSTR'),
                emitter = generate_from_template_emitter,
                source_scanner = tpl_scanner)

    env['BUILDERS']['FromFTemplate'] = Builder(
                action = Action(generate_from_f_template, '$FTEMPLATECOMSTR'),
                emitter = generate_from_template_emitter,
                source_scanner = tpl_scanner)

    createStaticExtLibraryBuilder(env)
    env['BUILDERS']['DistutilsStaticExtLibrary'] = DistutilsStaticExtLibrary

def customize_tools(env):
    customize_pyext(env)

    finalize_env(env)

    apply_compilers_customization(env)

    customize_link_flags(env)

def customize_pyext(env):
    from SCons.Tool import Tool

    from distutils.sysconfig import get_config_var
    from SCons.Node.FS import default_fs
    from SCons.Action import Action

    ext = get_config_var('SO')
    env['PYEXTSUFFIX'] = ext

    t = Tool('pyext', toolpath = get_numscons_toolpaths(env))
    t(env)

    # Extending pyext to handle fortran source code.
    # XXX: This is ugly: I don't see any way to do this cleanly.
    pyext_obj = t._tool_module().createPythonObjectBuilder(env)
    from SCons.Tool.FortranCommon import CreateDialectActions, ShFortranEmitter

    if has_f77(env):
        shcompaction = CreateDialectActions('F77')[2]
        for suffix in env['F77FILESUFFIXES']:
            pyext_obj.add_action(suffix, shcompaction)
            pyext_obj.add_emitter(suffix, ShFortranEmitter)

    # We don't do this in pyext because scons has no infrastructure to know
    # whether we are using mingw or ms
    if sys.platform == 'win32':
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
                env["PYEXTRUNTIME"] = [get_pythonlib_name(), msvc_runtime_library()]
            return 0

        # We override the default emitter here because SHLIB emitter
        # does a lot of checks we don&t care about and are wrong
        # anyway for python extensions.
        env["BUILDERS"]["PythonExtension"].emitter = dummy
        if built_with_mingw(env):
            # We are overrind pyext coms here.
            # XXX: This is ugly
            pycc, pycxx, pylink = t._tool_module().pyext_coms('posix')
            env['PYEXTCCCOM'] = pycc
            env['PYEXTCXXCOM'] = pycxx
            env['PYEXTLINKCOM'] = pylink

            pyext_runtime_action = Action(pyext_runtime, '')
            old_action = env['BUILDERS']['PythonExtension'].action
            env['BUILDERS']['PythonExtension'].action = Action([pyext_runtime_action, old_action])

    # Add numpy path
    if is_bootstrapping(env):
        env['NUMPYCPPPATH'] = scons_get_paths(env['include_bootstrap'])
    else:
        from numpy.distutils.misc_util import get_numpy_include_dirs
        env['NUMPYCPPPATH'] = get_numpy_include_dirs()

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
