# Last Changed: .

"""This initialize a scons environment using info from distutils, and all our
customization (python extension builders, build_dir, etc...)."""

import sys
import os
import os.path
from os.path import join as pjoin, dirname as pdirname, basename as pbasename, \
    exists as pexists, abspath as pabspath
from distutils.sysconfig import get_config_vars
from copy import deepcopy

from numscons.core.default import tool_list
from numscons.core.compiler_config import get_cc_config, get_f77_config, get_cxx_config, \
     NoCompilerConfig, Config, CompilerConfig, F77CompilerConfig, CXXCompilerConfig
from numscons.core.custom_builders import NumpySharedLibrary, NumpyCtypes, \
     NumpyPythonExtension, NumpyStaticExtLibrary
from numscons.core.siteconfig import get_config
from numscons.core.extension_scons import PythonExtension, built_with_mstools, \
     createStaticExtLibraryBuilder
from numscons.core.utils import pkg_to_path, partial
from numscons.core.misc import pyplat2sconsplat, is_cc_suncc, \
     get_numscons_toolpaths, \
     is_f77_gnu, get_vs_version
from numscons.core.template_generators import generate_from_c_template, \
     generate_from_f_template, generate_from_template_emitter, \
     generate_from_template_scanner
from numscons.core.custom_builders import NumpyFromCTemplate, NumpyFromFTemplate

from numscons.tools.substinfile import TOOL_SUBST

from misc import get_scons_build_dir, get_scons_configres_dir,\
                 get_scons_configres_filename, built_with_mingw

__all__ = ['GetNumpyEnvironment', 'distutils_dirs_emitter']

DEF_LINKERS, DEF_C_COMPILERS, DEF_CXX_COMPILERS, DEF_ASSEMBLERS, \
DEF_FORTRAN_COMPILERS, DEF_ARS, DEF_OTHER_TOOLS = tool_list(pyplat2sconsplat())

def _glob(env, path):
    """glob function to handle src_dir issues."""
    #import glob
    #files = glob.glob(pjoin(env['src_dir'], path))
    files = env.Glob(pjoin(env['src_dir'], path), strings = True)
    rdir = pdirname(path)
    return [pjoin(rdir, pbasename(f)) for f in files]

def GetNumpyOptions(args):
    """Call this with args=ARGUMENTS to take into account command line args."""
    from SCons.Options import Options, EnumOption

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

    return opts

def customize_cc(name, env):
    """Customize env options related to the given tool (C compiler)."""
    try:
        cfg = get_cc_config(name)
    except NoCompilerConfig, e:
        print "compiler %s has no customization available" % name
        cfg = CompilerConfig(Config())
    env.AppendUnique(**cfg.get_flags_dict())

def customize_f77(name, env):
    """Customize env options related to the given tool (F77 compiler)."""
    # XXX: this should be handled somewhere else...
    if sys.platform == "win32" and is_f77_gnu(env):
        name = "%s_mingw" % name

    try:
        cfg = get_f77_config(name)
    except NoCompilerConfig, e:
        print "compiler %s has no customization available" % name
        cfg = F77CompilerConfig(Config())
    env.AppendUnique(**cfg.get_flags_dict())

def customize_cxx(name, env):
    """Customize env options related to the given tool (CXX compiler)."""
    try:
        cfg = get_cxx_config(name)
    except NoCompilerConfig, e:
        print "compiler %s has no customization available" % name
        cfg = CXXCompilerConfig(Config())
    env.AppendUnique(**cfg.get_flags_dict())

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

def GetNumpyEnvironment(args):
    """Returns a correctly initialized scons environment. 

    This environment contains builders for python extensions, ctypes
    extensions, fortran builders, etc... Generally, call it with args =
    ARGUMENTS, which contain the arguments given to the scons process."""
    env = _get_numpy_env(args)

    # XXX: this is messy, refactor that crap

    #------------------------------
    # C compiler last customization
    #------------------------------
    # Apply optim and warn flags considering context
    if 'CFLAGS' in os.environ:
        env.Append(CFLAGS = "%s" % os.environ['CFLAGS'])
        env.AppendUnique(CFLAGS = env['NUMPY_EXTRA_CFLAGS'] +
                                  env['NUMPY_THREAD_CFLAGS'])
    else:
        env.AppendUnique(CFLAGS  = env['NUMPY_WARN_CFLAGS'] +\
                                   env['NUMPY_OPTIM_CFLAGS'] +\
                                   env['NUMPY_DEBUG_SYMBOL_CFLAGS'] +\
                                   env['NUMPY_EXTRA_CFLAGS'] +\
                                   env['NUMPY_THREAD_CFLAGS'])
    env.AppendUnique(LINKFLAGS = env['NUMPY_OPTIM_LDFLAGS'])

    #--------------------------------
    # F77 compiler last customization
    #--------------------------------
    # XXX: For now, only handle F77 case, but will have to think about multiple
    # fortran standard at some points ?
    if env.has_key('F77'):
        if 'FFLAGS' in os.environ:
            env.Append(F77FLAGS = "%s" % os.environ['FFLAGS'])
            env.AppendUnique(F77FLAGS = env['NUMPY_EXTRA_FFLAGS'] +
                                        env['NUMPY_THREAD_FFLAGS'])
        else: 
    	    env.AppendUnique(F77FLAGS  = env['NUMPY_WARN_FFLAGS'] +
                                         env['NUMPY_OPTIM_FFLAGS'] +
                                         env['NUMPY_DEBUG_SYMBOL_FFLAGS'] +
                                         env['NUMPY_EXTRA_FFLAGS'] +
                                         env['NUMPY_THREAD_FFLAGS'])

    #--------------------------------
    # CXX compiler last customization
    #--------------------------------
    if env.has_key('CXX'):
        if 'CXXFLAGS' in os.environ:
            env.Append(CXXFLAGS = "%s" % os.environ['CXXFLAGS'])
            env.AppendUnique(CXXFLAGS = env['NUMPY_EXTRA_CXXFLAGS'] +
                                        env['NUMPY_THREAD_CXXFLAGS'])
        else: 
    	    env.AppendUnique(CXXFLAGS  = env['NUMPY_WARN_CXXFLAGS'] +
                                         env['NUMPY_OPTIM_CXXFLAGS'] +
                                         env['NUMPY_DEBUG_SYMBOL_CXXFLAGS'] +
                                         env['NUMPY_EXTRA_CXXFLAGS'] +
                                         env['NUMPY_THREAD_CXXFLAGS'])
    #print env.Dump('F77')
    #print env.Dump('F77FLAGS')
    #print env.Dump('SHF77FLAGS')
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
                customize_cc(t.name, env)
            else:
                if is_cc_suncc(pjoin(env['cc_opt_path'], env['cc_opt'])):
                    env['cc_opt'] = 'suncc'
                t = Tool(env['cc_opt'], 
                         toolpath = get_numscons_toolpaths(env))
                t(env) 
                customize_cc(t.name, env)
                path_list.append(env['cc_opt_path'])
        else:
            # Do not care about PATH info because none given from scons
            # distutils command
            t = Tool(env['cc_opt'], toolpath = get_numscons_toolpaths(env))
            t(env) 
            customize_cc(t.name, env)

    if len(env['cc_opt']) > 0:
        set_cc_from_distutils()
    else:
        t = Tool(FindTool(DEF_C_COMPILERS, env), 
                 toolpath = get_numscons_toolpaths(env))
        t(env)
        customize_cc(t.name, env)

def initialize_f77(env, path_list):
    """Initialize F77 compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    has_f77 = False
    if len(env['f77_opt']) > 0:
        if len(env['f77_opt_path']) > 0:
            t = Tool(env['f77_opt'], 
                     toolpath = get_numscons_toolpaths(env))
            t(env) 
            path_list.append(env['f77_opt_path'])
            customize_f77(t.name, env)
	    has_f77 = True
    else:
        def_fcompiler =  FindTool(DEF_FORTRAN_COMPILERS, env)
        if def_fcompiler:
            t = Tool(def_fcompiler, toolpath = get_numscons_toolpaths(env))
            t(env)
            customize_f77(t.name, env)
	    has_f77 = True
        else:
            print "========== NO FORTRAN COMPILER FOUND ==========="

    # scons handles fortran tools in a really convoluted way which does not
    # much make sense to me. Depending on the tool, different set of
    # construction variables are defined. As long as this is not fixed or
    # better understood, I do the following:
    #   - if F77* variables do not exist, define them
    #   - the only guaranteed variables for fortran are the list generators, so
    #   use them through env.subst to get any compiler, and set F77* to them if
    #   they are not already defined.
    if has_f77:
        if not env.has_key('F77'):
            env['F77'] = env.subst('$_FORTRANG')
            # Basic safeguard against buggy fortran tools ...
            assert len(env['F77']) > 0
        if not env.has_key('F77FLAGS'):
            env['F77FLAGS'] = env.subst('$_FORTRANFLAGSG')
        if not env.has_key('SHF77FLAGS'):
            env['SHF77FLAGS'] = '$F77FLAGS %s' % env.subst('$_SHFORTRANFLAGSG')

def initialize_cxx(env, path_list):
    """Initialize C++ compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    if len(env['cxx_opt']) > 0:
        if len(env['cxx_opt_path']) > 0:
            t = Tool(env['cxx_opt'], 
                     toolpath = get_numscons_toolpaths(env))
            t(env) 
            path_list.append(env['cxx_opt_path'])
            customize_cxx(t.name, env)
    else:
        def_cxxcompiler =  FindTool(DEF_CXX_COMPILERS, env)
        if def_cxxcompiler:
            t = Tool(def_cxxcompiler, toolpath = get_numscons_toolpaths(env))
            t(env)
            customize_cxx(t.name, env)
        else:
            print "========== NO CXX COMPILER FOUND ==========="

def _get_numpy_env(args):
    """Call this with args = ARGUMENTS."""
    from SCons.Script import BuildDir, Help
    from numpyenv import NumpyEnvironment

    # XXX: this function is too long and clumsy...

    # XXX: I would prefer subclassing Environment, because we really expect
    # some different behaviour than just Environment instances...
    opts = GetNumpyOptions(args)

    # Get the python extension suffix
    # XXX this should be defined somewhere else. Is there a way to reliably get
    # all the necessary informations specific to python extensions (linkflags,
    # etc...) dynamically ?
    pyextsuffix = get_config_vars('SO')

    # We set tools to an empty list, to be sure that the custom options are
    # given first. We have to 
    env = NumpyEnvironment(options = opts, tools = [], PYEXTSUFFIX = pyextsuffix)

    # Setting dirs according to command line options
    env.AppendUnique(build_dir = pjoin(env['build_prefix'], env['src_dir']))
    env.AppendUnique(distutils_installdir = pjoin(env['distutils_libdir'], 
                                                  pkg_to_path(env['pkg_name'])))

    #------------------------------------------------
    # Setting tools according to command line options
    #------------------------------------------------
    customize_tools(env)

    #---------------
    #     Misc
    #---------------
    customize_link_flags(env)

    customize_scons_dirs(env)

    # Adding custom builders
    add_custom_builders(env)

    # Getting the config options from *.cfg files
    set_site_config(env)

    # Setting build directory according to command line option
    if len(env['src_dir']) > 0:
        BuildDir(env['build_dir'], env['src_dir'])
    else:
        BuildDir(env['build_dir'], '.')

    # Add HOME in the environment: some tools seem to require it (Intel
    # compiler, for licenses stuff)
    if os.environ.has_key('HOME'):
        env['ENV']['HOME'] = os.environ['HOME']

    set_verbosity(env)

    # Generate help (if calling scons directly during debugging, this could be
    # useful)
    Help(opts.GenerateHelpText(env))

    import sys
    if sys.platform == "win32":
	    env["ENV"]["PATH"] = os.environ["PATH"]
    return env

def set_verbosity(env):
    level = int(env['silent'])

    if level > 0:
        env['F2PYCOMSTR']       = "F2PY               $SOURCE"

        env['CCCOMSTR']         = "CC                 $SOURCE"
        env['SHCCCOMSTR']       = "SHCC               $SOURCE"

        env['CXXCOMSTR']        = "CXX                $SOURCE"
        env['SHCXXCOMSTR']      = "SHCXX              $SOURCE"

        env['F77COMSTR']        = "F77                $SOURCE"
        env['SHF77COMSTR']      = "SHF77              $SOURCE"

        env['ARCOMSTR']         = "AR                 $SOURCE"
        env['RANLIBCOMSTR']     = "RANLIB             $SOURCE"
        env['LDMODULECOMSTR']   = "LDMODULE           $SOURCE"

        env['INSTALLSTR']       = "INSTALL            $SOURCE"

        env['ARRAPIGENCOMSTR']  = "GENERATE ARRAY API $SOURCE"
        env['UFUNCAPIGENCOMSTR']= "GENERATE UFUNC API $SOURCE"
        env['TEMPLATECOMSTR']   = "FROM TEMPLATE      $SOURCE"
        env['UMATHCOMSTR']      = "GENERATE UMATH     $SOURCE"

        env['CTEMPLATECOMSTR']  = "FROM C TEMPLATE    $SOURCE"
        env['FTEMPLATECOMSTR']  = "FROM F TEMPLATE    $SOURCE"

def set_site_config(env):
    config = get_config()
    env['NUMPY_SITE_CONFIG'] = config

    # This will be used to keep configuration information on a per package basis
    env['NUMPY_PKG_CONFIG'] = {'PERFLIB' : {}, 'LIB' : {}}
    env['NUMPY_PKG_CONFIG_FILE'] = pjoin(get_scons_configres_dir(), 
                                         env['src_dir'], 
                                         get_scons_configres_filename())

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
                     '.sconsign.dblite')
    asconsign = pabspath(env['build_dir'])
    if not pexists(asconsign):
        os.makedirs(asconsign)
    env.SConsignFile(sconsign)

    # Change Glob to take into account our particular need wrt build
    # directories, etc...
    env.NumpyGlob = partial(_glob, env)

def add_custom_builders(env):
    """Call this to add all our custom builders to the environment."""
    from SCons.Scanner import Scanner
    from SCons.Builder import Builder
    from SCons.Action import Action

    # Add the file substitution tool
    TOOL_SUBST(env)

    # XXX: Put them into tools ?
    env['BUILDERS']['NumpySharedLibrary'] = NumpySharedLibrary
    env['BUILDERS']['NumpyCtypes'] = NumpyCtypes
    env['BUILDERS']['PythonExtension'] = PythonExtension
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

    env['BUILDERS']['NumpyFromCTemplate'] = NumpyFromCTemplate
    env['BUILDERS']['NumpyFromFTemplate'] = NumpyFromFTemplate

    createStaticExtLibraryBuilder(env)
    env['BUILDERS']['NumpyStaticExtLibrary'] = NumpyStaticExtLibrary


def customize_tools(env):
    from SCons.Tool import Tool, FindTool, FindAllTools

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
        for i in [DEF_LINKERS, DEF_CXX_COMPILERS, DEF_ASSEMBLERS, DEF_ARS]:
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
            
    for t in FindAllTools(DEF_OTHER_TOOLS, env):
        Tool(t)(env)

    if built_with_mingw(env):
        t = Tool("dllwrap", toolpath = get_numscons_toolpaths(env))
        t(env)
        t = Tool("dlltool", toolpath = get_numscons_toolpaths(env))
        t(env)

    # Add our own, custom tools (f2py, from_template, etc...)
    #t = Tool('f2py', toolpath = get_numscons_toolpaths(env))
    #if t.exists(env):
    #    t(env)

    #t = Tool('numpyf2py', toolpath = get_numscons_toolpaths(env))
    #if t.exists(env):
    #    t(env)

    # XXX: understand how registration of source files work before reenabling
    # those

    # t = Tool('npyctpl', 
    #          toolpath = )
    # t(env)

    # t = Tool('npyftpl', 
    #          toolpath = )
    # t(env)

    finalize_env(env)

    # Add the tool paths in the environment
    if env['ENV'].has_key('PATH'):
        path_list += env['ENV']['PATH'].split(os.pathsep)
    env['ENV']['PATH'] = os.pathsep.join(path_list)

def customize_link_flags(env):
    from SCons.Action import ListAction, Action
    # We sometimes need to put link flags at the really end of the command
    # line, so we add a construction variable for it
    env['LINKFLAGSEND'] = []
    env['SHLINKFLAGSEND'] = ['$LINKFLAGSEND']
    env['LDMODULEFLAGSEND'] = []

    if built_with_mingw(env) and not built_with_mstools(env):
	# For mingw tools, we do it in our custom mingw
	# scons tool XXX: this should be done at the tool
	# level, that's the only way to avoid screwing
	# things up....
	pass
    elif built_with_mstools(env):
	# Sanity check: in case scons changes and we are not
	# aware of it
	assert isinstance(env["SHLINKCOM"], ListAction)
	assert isinstance(env["LDMODULECOM"], ListAction)
	# We replace the "real" shlib action of mslink by our
	# own, which only differ in the linkdlagsend flags.
	newshlibaction = Action('${TEMPFILE("$SHLINK $SHLINKFLAGS $_SHLINK_TARGETS $( $_LIBDIRFLAGS $) $_LIBFLAGS $SHLINKFLAGSEND $_PDB $_SHLINK_SOURCES")}')
	env["SHLINKCOM"].list[0] = newshlibaction
	env["LDMODULECOM"].list[0] = newshlibaction

	newlibaction = '${TEMPFILE("$LINK $LINKFLAGS /OUT:$TARGET.windows $( $_LIBDIRFLAGS $) $_LIBFLAGS $LINKFLAGSEND $_PDB $SOURCES.windows")}'
	env["LINKCOM"] = newlibaction
    else:
        env['LINKCOM'] = '%s $LINKFLAGSEND' % env['LINKCOM']
        env['SHLINKCOM'] = '%s $SHLINKFLAGSEND' % env['SHLINKCOM']
        env['LDMODULECOM'] = '%s $LDMODULEFLAGSEND' % env['LDMODULECOM']

def distutils_dirs_emitter(target, source, env):
    from SCons.Node.FS import default_fs 

    source = [default_fs.Entry(pjoin(env['build_dir'], str(i))) for i in source]
    target = [default_fs.Entry(pjoin(env['build_dir'], str(i))) for i in target]

    return target, source

