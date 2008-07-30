"""This module initialize compilers, linkers, etc... from informations passed
from distutils, and using scons tools.

The main function is initialize_tools: this is the top function which
initialize all the tools."""

from os.path import join as pjoin
import sys

from numscons.core.misc import built_with_mstools, built_with_mingw, \
    get_numscons_toolpaths, pyplat2sconsplat, cc_version, iscplusplus
from numscons.core.compiler_detection import get_cc_type, get_f77_type, \
    get_cxx_type
from numscons.core.compiler_config import get_config as get_compiler_config, \
    NoCompilerConfig, CompilerConfig
from numscons.core.default import tool_list
from numscons.core.allow_undefined import get_darwin_allow_undefined

DEF_LINKERS, DEF_C_COMPILERS, DEF_CXX_COMPILERS, DEF_ASSEMBLERS, \
DEF_FORTRAN_COMPILERS, DEF_ARS, DEF_OTHER_TOOLS = tool_list(pyplat2sconsplat())

def configure_compiler(name, env, lang):
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
        print "%s => using default configuration." % e
        cfg = CompilerConfig()
    env["NUMPY_CUSTOMIZATION"][lang] = cfg

def initialize_cc(env, path_list):
    """Initialize C compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    def set_cc_from_distutils():
        # XXX: To keep backward compatibility with numpy 1.1.1. Can be dropped
        # at 1.1.2
        if env["cc_opt"] == "intelc":
            env["cc_opt"] = "icc"

        if len(env['cc_opt_path']) > 0:
            if built_with_mstools(env):
                t = Tool("msvc", toolpath = get_numscons_toolpaths(env))
                # We need msvs tool too (before customization !)
                Tool('msvs')(env)
                path_list.insert(0, env['cc_opt_path'])
            else:
                cc = get_cc_type(pjoin(env['cc_opt_path'], env['cc_opt']))
                if cc == 'gcc' and sys.platform == 'win32':
                    cc = 'mingw'
                t = Tool(cc, toolpath = get_numscons_toolpaths(env))
                path_list.insert(0, env['cc_opt_path'])
        else:
            # Do not care about PATH info because none given from scons
            # distutils command
            try:
                t = Tool(env['cc_opt'], toolpath = get_numscons_toolpaths(env))
            except ImportError:
                raise UnknownCompiler(env['cc_opt'])

        return t

    if len(env['cc_opt']) > 0:
        t = set_cc_from_distutils()
    else:
        t = Tool(FindTool(DEF_C_COMPILERS, env),
                 toolpath = get_numscons_toolpaths(env))
    t(env)

    configure_compiler(t.name, env, "C")

def initialize_f77(env, path_list):
    """Initialize F77 compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    def set_f77_from_distutils():
        t = None
        env.AppendUnique(F77FILESUFFIXES = ['.f'])
        if len(env['f77_opt']) > 0:
            if len(env['f77_opt_path']) > 0:
                f77 = pjoin(env['f77_opt_path'], env['f77_opt'])
                t = Tool(get_f77_type(f77),
                         toolpath = get_numscons_toolpaths(env))
                path_list.insert(0, env['f77_opt_path'])
            else:
                t = Tool(get_f77_type(env["f77_opt"]),
                         toolpath = get_numscons_toolpaths(env))
        else:
            def_fcompiler =  FindTool(DEF_FORTRAN_COMPILERS, env)
            if def_fcompiler:
                t = Tool(def_fcompiler, toolpath = get_numscons_toolpaths(env))

        return t

    t = set_f77_from_distutils()
    if t:
        t(env)
        configure_compiler(t.name, env, "F77")

def initialize_cxx(env, path_list):
    """Initialize C++ compiler from distutils info."""
    from SCons.Tool import Tool, FindTool

    def set_cxx_from_distutils():
        t = None
        if len(env['cxx_opt']) > 0:
            if len(env['cxx_opt_path']) > 0:
                if built_with_mstools(env):
                    t = Tool("msvc", toolpath = get_numscons_toolpaths(env))
                    # We need msvs tool too (before customization !)
                else:
                    cxx = get_cxx_type(pjoin(env['cxx_opt_path'],
                                             env['cxx_opt']))
                    t = Tool(cxx, toolpath = get_numscons_toolpaths(env))
                    path_list.insert(0, env['cxx_opt_path'])
        else:
            def_cxxcompiler =  FindTool(DEF_CXX_COMPILERS, env)
            if def_cxxcompiler:
                t = Tool(def_cxxcompiler,
                         toolpath = get_numscons_toolpaths(env))
        return t

    t = set_cxx_from_distutils()
    if t:
        t(env)
        configure_compiler(t.name, env, "CXX")
        env['CXXFILESUFFIX'] = '.cxx'
    else:
        # Some scons tools initialize CXX env var even if no CXX available.
        # This is just confusing, so remove the key here since we could not
        # initialize any CXX tool.
        if env.has_key('CXX'):
            del env['CXX']

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
    if not built_with_mingw(env):
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

    # Set ALLOW_UNDEFINED link flags to allow undefined symbols in dynamic
    # libraries
    initialize_allow_undefined(env)

    # Use our own stupid link, because we handle this with conf checkers and
    # link flags.
    env['SMARTLINK']   = dumb_link

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

    if sys.platform == 'darwin':
        env['ALLOW_UNDEFINED'] = get_darwin_allow_undefined()
    else:
        env['ALLOW_UNDEFINED'] = SCons.Util.CLVar('')
