"""This module initialize compilers, linkers, etc... from informations passed
from distutils, and using scons tools.

The main function is initialize_tools: this is the top function which
initialize all the tools."""

from os.path import join as pjoin
import sys

from numscons.core.misc import built_with_mstools, built_with_mingw, \
    pyplat2sconsplat, cc_version, iscplusplus, is_python_win64
from numscons.core.compiler_detection import get_cc_type, get_f77_type, \
    get_cxx_type
from numscons.core.compiler_config import get_config as get_compiler_config, \
    NoCompilerConfig, CompilerConfig
from numscons.core.default import tool_list
from numscons.core.allow_undefined import get_darwin_allow_undefined
from numscons.core.trace import warn, debug, info
from numscons.core.errors import UnknownCompiler
from numscons.core.customization import \
    is_bypassed

DEF_LINKERS, DEF_C_COMPILERS, DEF_CXX_COMPILERS, DEF_ASSEMBLERS, \
DEF_FORTRAN_COMPILERS, DEF_ARS, DEF_OTHER_TOOLS = tool_list(pyplat2sconsplat())

def configure_compiler(name, env, lang):
    """Customize compilers flags using the .cfg compiler configuration
    files."""
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

def initialize_cc(env):
    """Initialize C compiler from distutils info."""
    from SCons.Tool import FindTool

    def set_cc_from_distutils():
        if len(env['cc_opt_path']) > 0:
            debug('Setting cc_opt_path from distutils (%s).' % env['cc_opt_path'])
            cc = pjoin(env["cc_opt_path"], env["cc_opt"])
        else:
            debug('Setting wo cc_opt_path')
            cc = env["cc_opt"]

        if built_with_mstools(env):
            info('Detecting ms build.')
            name = "msvc"
            # We need msvs tool too (before customization !)
            env.Tool('msvs')
        else:
            name = get_cc_type(env, cc)
            if name == 'gcc' and sys.platform == 'win32':
                name = 'mingw'
                debug('Changing cc => mingw')

            info('Detected CC type: %s' % name)
            try:
                env.Tool(name)
                env['CC'] = env['cc_opt']
            except ImportError:
                raise UnknownCompiler(env['cc_opt'])

        return name

    if is_bypassed(env):
        # Here, the --compiler option is the scons tool name
        debug('Setting cc_opt from scons.')
        name = env['cc_opt']
        if name == 'msvc':
            env.Tool('msvs')
        env.Tool(name)
    elif len(env['cc_opt']) > 0:
        debug('Setting cc_opt from distutils.')
        name = set_cc_from_distutils()
    else:
        debug('Setting cc_opt from default list.')
        name = FindTool(DEF_C_COMPILERS, env)
        env.Tool(name)

    warn('Setting for C tool: %s' % name)
    configure_compiler(name, env, "C")

def initialize_f77(env):
    """Initialize F77 compiler from distutils info."""
    from SCons.Tool import FindTool
    def set_f77_from_distutils():
        if len(env['f77_opt']) > 0:
            debug('Setting F77 from distutils: %s' % env['f77_opt'])
            if len(env['f77_opt_path']) > 0:
                f77 = pjoin(env['f77_opt_path'], env['f77_opt'])
            else:
                f77 = env['f77_opt']

            name = get_f77_type(env, f77)
            info('Detecting F77 type: %s' % name)
            env.Tool(name)
        else:
            debug('Setting F77 from default list')
            name =  FindTool(DEF_FORTRAN_COMPILERS, env)
            debug('Found: %s' % name)
            if name:
                env.Tool(name)

        return name

    env.AppendUnique(F77FILESUFFIXES = ['.f'])
    if is_bypassed(env):
        # Here, the --compiler option is the scons tool name
        debug('Setting f77_opt from scons.')
        name = env['f77_opt']
        env.Tool(name)
    else:
        name = set_f77_from_distutils()
    if name:
        warn("Setting for F77 tool: %s" % name)
        configure_compiler(name, env, "F77")
    else:
        warn("Found no F77 tool")

def initialize_cxx(env):
    """Initialize C++ compiler from distutils info."""
    from SCons.Tool import FindTool
    def set_cxx_from_distutils():
        if len(env['cxx_opt']) > 0:
            if len(env['cxx_opt_path']) > 0:
                cxx = pjoin(env['cxx_opt_path'], env['cxx_opt'])
            else:
                cxx = env['cxx_opt']

            if built_with_mstools(env):
                name = "msvc"
                env.Tool(name)
            else:
                name = get_cxx_type(env, cxx)
            info("Detected CXX type: %s" % name)
            env.Tool(name)
        else:
            name =  FindTool(DEF_CXX_COMPILERS, env)
            info("Detected CXX type: %s" % name)
            if name:
                env.Tool(name)
        return name

    if is_bypassed(env):
        # Here, the --compiler option is the scons tool name
        debug('Setting cxx_opt from scons.')
        name = env['cxx_opt']
        # Do not initialize twice the same tool
        if not name == env['cc_opt']:
            env.Tool(name)
    else:
        name = set_cxx_from_distutils()

    if name:
        warn("Setting for CXX tool: %s" % name)
        configure_compiler(name, env, "CXX")
        env['CXXFILESUFFIX'] = '.cxx'
    else:
        warn("Found no CXX tool: %s")
        # Some scons tools initialize CXX env var even if no CXX available.
        # This is just confusing, so remove the key here since we could not
        # initialize any CXX tool.
        if env.has_key('CXX'):
            del env['CXX']

def initialize_tools(env):
    from SCons.Tool import FindTool

    if sys.platform == "win32":
        if is_python_win64():
            env["ICC_ABI"] = "amd64"
            env["IFORT_ABI"] = "amd64"

    # Initialize CC tool from distutils info
    initialize_cc(env)

    # Initialize F77 tool from distutils info
    initialize_f77(env)

    # Initialize CXX tool from distutils info
    initialize_cxx(env)

    # Adding default tools for the one we do not customize: mingw is special
    # according to scons, don't ask me why, but this does not work as expected
    # for this tool.
    if not built_with_mingw(env):
        for i in [DEF_LINKERS, DEF_ASSEMBLERS, DEF_ARS]:
            t = FindTool(i, env) or i[0]
            env.Tool(t)
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
