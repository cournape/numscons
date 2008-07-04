# Last Changed: .

"""This initialize a scons environment using info from distutils, and all our
customization (python extension builders, build_dir, etc...)."""

import sys
import os
from os.path import join as pjoin, basename

from numscons.core.default import tool_list
from numscons.core.compiler_config import get_config as get_compiler_config, \
     NoCompilerConfig, CompilerConfig
from numscons.core.custom_builders import DistutilsSharedLibrary, NumpyCtypes, \
     DistutilsPythonExtension, DistutilsStaticExtLibrary
from numscons.core.siteconfig import get_config
from numscons.core.extension_scons import createStaticExtLibraryBuilder
from numscons.core.extension import get_pythonlib_dir
from numscons.core.utils import pkg_to_path, flatten
from numscons.core.misc import pyplat2sconsplat, is_cc_suncc, \
     get_numscons_toolpaths, iscplusplus, get_pythonlib_name, \
     is_f77_gnu, get_vs_version, built_with_mstools, cc_version, \
     isfortran, isf2py, is_cxx_suncc, is_cc_gnu

from numscons.core.template_generators import generate_from_c_template, \
     generate_from_f_template, generate_from_template_emitter, \
     generate_from_template_scanner

from numscons.tools.substinfile import TOOL_SUBST

from numscons.numdist import msvc_runtime_library

from misc import get_scons_build_dir, \
                 get_scons_configres_filename, built_with_mingw

__all__ = ['GetNumpyEnvironment', 'GetInitEnvironment']

DEF_LINKERS, DEF_C_COMPILERS, DEF_CXX_COMPILERS, DEF_ASSEMBLERS, \
DEF_FORTRAN_COMPILERS, DEF_ARS, DEF_OTHER_TOOLS = tool_list(pyplat2sconsplat())

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

def customize_compiler(name, env, lang):
    """Customize env options related to the given tool and language."""
    # XXX: we have to fix how to detect compilers/version instead of hack after
    # hack...
    if lang == "C":
        ver = cc_version(env)
        if ver:
            name = '%s%1.0f' % (name, ver)

    try:
        cfg = get_compiler_config(name, lang)
    except NoCompilerConfig, e:
        print e
        cfg = CompilerConfig()
    env["NUMPY_CUSTOMIZATION"][lang] = cfg

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
    custom = env['NUMPY_CUSTOMIZATION']['F77']
    if env.has_key('F77'):
        if 'FFLAGS' in os.environ:
            env.Append(F77FLAGS = "%s" % os.environ['FFLAGS'])
            env.AppendUnique(F77FLAGS = custom['extra'] + custom['thread'])
        else:
            env.AppendUnique(F77FLAGS  = flatten(custom.values()))

    #--------------------------------
    # CXX compiler last customization
    #--------------------------------
    custom = env['NUMPY_CUSTOMIZATION']['CXX']
    if env.has_key('CXX'):
        if 'CXXFLAGS' in os.environ:
            env.Append(CXXFLAGS = "%s" % os.environ['CXXFLAGS'])
            env.AppendUnique(CXXFLAGS = custom['extra'] + custom['thread'])
        else:
            env.AppendUnique(CXXFLAGS  = flatten(custom.values()))


def GetNumpyEnvironment(args):
    """Returns a correctly initialized scons environment.

    This environment contains builders for python extensions, ctypes
    extensions, fortran builders, etc... Generally, call it with args =
    ARGUMENTS, which contain the arguments given to the scons process.
    
    This method returns an environment with fully customized flags."""
    env = _get_numpy_env(args)

    apply_compilers_customization(env)

    return env

def initialize_cc(env, path_list):
    """Initialize C compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    def set_cc_from_distutils():
        if len(env['cc_opt_path']) > 0:
            if env['cc_opt'] == 'intelc':
                # Intel Compiler SCons.Tool has a special way to set the
                # path, so we use this one instead of changing
                # env['ENV']['PATH'].
                t = Tool(env['cc_opt'],
                         toolpath = get_numscons_toolpaths(env),
                         topdir = os.path.split(env['cc_opt_path'])[0])
                t(env)
            elif built_with_mstools(env):
                 t = Tool(env['cc_opt'],
                          toolpath = get_numscons_toolpaths(env))
                 t(env)
                 # We need msvs tool too (before customization !)
                 Tool('msvs')(env)
                 path_list.append(env['cc_opt_path'])
            else:
                # XXX: hack to handle pyCC/pycc wrapper in open solaris.
                # Solving this in a nice and efficient way is not
                # trivial.
                if is_cc_suncc(pjoin(env['cc_opt_path'], env['cc_opt'])):
                    env['cc_opt'] = 'suncc'
                elif is_cc_gnu(pjoin(env['cc_opt_path'], env['cc_opt'])):
                    env['cc_opt'] = 'gcc'
                elif env['cc_opt'] == 'icc':
                    env['cc_opt'] = 'intelc'
                t = Tool(env['cc_opt'],
                         toolpath = get_numscons_toolpaths(env))
                t(env)
                path_list.append(env['cc_opt_path'])
        else:
            # Do not care about PATH info because none given from scons
            # distutils command
            t = Tool(env['cc_opt'], toolpath = get_numscons_toolpaths(env))
            t(env)

        return t

    if len(env['cc_opt']) > 0:
        t = set_cc_from_distutils()
    else:
        t = Tool(FindTool(DEF_C_COMPILERS, env),
                 toolpath = get_numscons_toolpaths(env))
        t(env)
    
    customize_compiler(t.name, env, "C")

def has_f77(env):
    return len(env['f77_opt']) > 0

def initialize_f77(env, path_list):
    """Initialize F77 compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    if len(env['f77_opt']) > 0:
        if len(env['f77_opt_path']) > 0:
            env.AppendUnique(F77FILESUFFIXES = ['.f'])
            t = Tool(env['f77_opt'],
                     toolpath = get_numscons_toolpaths(env))
            t(env)
            path_list.append(env['f77_opt_path'])
    else:
        def_fcompiler =  FindTool(DEF_FORTRAN_COMPILERS, env)
        if def_fcompiler:
            t = Tool(def_fcompiler, toolpath = get_numscons_toolpaths(env))
            t(env)

    customize_compiler(t.name, env, "F77")

def initialize_cxx(env, path_list):
    """Initialize C++ compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    if len(env['cxx_opt']) > 0:
        if len(env['cxx_opt_path']) > 0:
            # XXX: hack to handle pyCC/pycc wrapper in open solaris.
            # Solving this in a nice and efficient way is not
            # trivial.
            toolname = env['cxx_opt']
            if is_cxx_suncc(pjoin(env['cxx_opt_path'], env['cxx_opt'])):
                toolname = 'sunc++'
            elif is_cc_gnu(pjoin(env['cxx_opt_path'], env['cxx_opt'])):
                toolname = 'g++'
            t = Tool(toolname,
                     toolpath = get_numscons_toolpaths(env))
            t(env)
        # XXX: this is an hack around scons sunc++ which does not work on
        # open solaris
        if not env['CXX']:
            env['CXX'] = basename(env['cxx_opt'])
            path_list.append(env['cxx_opt_path'])
    else:
        def_cxxcompiler =  FindTool(DEF_CXX_COMPILERS, env)
        if def_cxxcompiler:
            t = Tool(def_cxxcompiler, toolpath = get_numscons_toolpaths(env))
            t(env)
        else:
            # Some scons tools initialize CXX env var even if no CXX available.
            # This is just confusing, so remove the key here since we could not
            # initialize any CXX tool.
            try:
                del env['CXX']
            except KeyError:
                pass

    customize_compiler(t.name, env, "CXX")
    env['CXXFILESUFFIX'] = '.cxx'

def set_bootstrap(env):
    import __builtin__
    if env['bootstrapping']:
        __builtin__.__NUMPY_SETUP__ = True

def is_bootstrapping(env):
    return env['bootstrapping']

def _init_environment(args):
    from numpyenv import NumpyEnvironment
    from SCons.Defaults import DefaultEnvironment
    from SCons.Script import Help

    opts = GetNumpyOptions(args)
    env = NumpyEnvironment(options = opts, tools = [])

    # We explicily set DefaultEnvironment to avoid wasting time on initializing
    # tools a second time.
    DefaultEnvironment(tools = [])

    # Setting dirs according to command line options
    env.AppendUnique(build_dir = pjoin(env['build_prefix'], env['src_dir']))
    env.AppendUnique(distutils_installdir = pjoin(env['distutils_libdir'],
                                                  pkg_to_path(env['pkg_name'])))

    # This will keep our compiler dependent customization (optimization,
    # warning, etc...)
    env['NUMPY_CUSTOMIZATION'] = {}

    Help(opts.GenerateHelpText(env))

    return env

def GetInitEnvironment(args):
    return _init_environment(args)

def _get_numpy_env(args):
    """Call this with args = ARGUMENTS."""
    env = _init_environment(args)

    #------------------------------------------------
    # Setting tools according to command line options
    #------------------------------------------------
    initialize_tools(env)

    #---------------
    #     Misc
    #---------------
    customize_link_flags(env)

    customize_scons_dirs(env)

    # Adding custom builders
    add_custom_builders(env)

    # Getting the config options from *.cfg files
    set_site_config(env)

    # Add HOME in the environment: some tools seem to require it (Intel
    # compiler, for licenses stuff)
    if os.environ.has_key('HOME'):
        env['ENV']['HOME'] = os.environ['HOME']

    if sys.platform == "win32":
        env["ENV"]["PATH"] = os.environ["PATH"]

    set_verbosity(env)

    return env

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
    env['NUMPY_PKG_CONFIG_FILE'] = pjoin(get_scons_configres_filename())

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

# Our own smart_link: the one in scons is not that smart.
def dumb_link(source, target, env, for_signature):
    has_cplusplus = iscplusplus(source)
    # XXX: it would be nice to raise a warning if F77_LDFLAGS is not found in
    # env and we link some fortran code.
    if has_cplusplus:
        return '$CXX'
    return '$CC'

def initialize_allow_undefined(env):
    import SCons
    from allow_undefined import get_darwin_allow_undefined

    if sys.platform == 'darwin':
        env['ALLOW_UNDEFINED'] = get_darwin_allow_undefined()
    else:
        env['ALLOW_UNDEFINED'] = SCons.Util.CLVar('')

def initialize_tools(env):
    from SCons.Tool import Tool, FindTool

    # List of supplemental paths to take into account
    path_list = []

    # Initialize CC tool from distutils info
    initialize_cc(env, path_list)

    # Initialize F77 tool from distutils info
    initialize_f77(env, path_list)

    # Initialize CXX tool from distutils info
    initialize_cxx(env, path_list)

    # Adding default tools for the one we do not customize: mingw is special
    # according to scons, don't ask me why, but this does not work as expected
    # for this tool.
    if not env['cc_opt'] == 'mingw':
        for i in [DEF_LINKERS, DEF_ASSEMBLERS, DEF_ARS]:
            t = FindTool(i, env) or i[0]
            Tool(t)(env)
    else:
        try:
            t = FindTool(['g++'], env)
            #env['LINK'] = None
        except EnvironmentError:
            raise RuntimeError('g++ not found: this is necessary with mingw32 '\
                               'to build numpy !')
        # XXX: is this really the right place ?
        env.AppendUnique(CFLAGS = '-mno-cygwin')

    # Set ALLOW_UNDEFINED link flags to allow undefined symbols in dynamic
    # libraries
    initialize_allow_undefined(env)

    # Use our own stupid link, because we handle this with conf checkers and
    # link flags.
    env['SMARTLINK']   = dumb_link

    customize_pyext(env)

    finalize_env(env)

    # Add the tool paths in the environment
    if env['ENV'].has_key('PATH'):
        path_list += env['ENV']['PATH'].split(os.pathsep)
    env['ENV']['PATH'] = os.pathsep.join(path_list)

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
