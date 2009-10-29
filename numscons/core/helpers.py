# Last Changed: .

"""This initialize a scons environment using info from distutils, and all our
customization (python extension builders, build_dir, etc...)."""
from os.path import join as pjoin

from numscons.core.custom_builders import DistutilsSharedLibrary, NumpyCtypes, \
     DistutilsPythonExtension, DistutilsStaticExtLibrary, NumpyPythonExtension, \
     DistutilsInstalledStaticExtLibrary
from numscons.core.siteconfig import get_config
from numscons.core.extension_scons import createStaticExtLibraryBuilder
from numscons.core.misc import get_scons_build_dir, \
     get_scons_configres_filename
from numscons.core.template_generators import generate_from_c_template, \
     generate_from_f_template, generate_from_template_emitter, \
     generate_from_template_scanner
import numscons.core.trace

from numscons.tools.substinfile import TOOL_SUBST

def GetNumpyOptions(args):
    """Call this with args=ARGUMENTS to take into account command line args."""
    from SCons.Variables import Variables, EnumVariable, BoolVariable

    opts = Variables(None, args)

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
    opts.Add('distutils_clibdir',
             'build dir for pure C libraries (clib), NOT including '\
             'the package name)',
             pjoin('build', 'lib'))
    opts.Add('distutils_install_prefix',
             'install directory prefix (the one from --prefix)', None)
    opts.Add('include_bootstrap',
             "include directories for boostraping numpy (if you do not know" \
             " what that means, you don't need it)" ,
             '')
    opts.Add('pkg_path', "UNDOCUMENTED", '')
    opts.Add(BoolVariable('inplace',
                        "true if building in place numpy, false if not", 0))

    # Add compiler related info
    opts.Add('cc_opt', 'name of C compiler', '')
    opts.Add('cc_opt_path', 'path of the C compiler set in cc_opt', '')

    opts.Add('f77_opt', 'name of F77 compiler', '')
    opts.Add('f77_opt_path', 'path of the F77 compiler set in cc_opt', '')

    opts.Add('cxx_opt', 'name of C compiler', '')
    opts.Add('cxx_opt_path', 'path of the C compiler set in cc_opt', '')

    opts.Add(BoolVariable('bypass',
                        "true if bypassing compiler detection by distutils", 0))
    opts.Add(BoolVariable('import_env',
                        "true if importing user env into numscons env['ENV'].", 0))
    opts.Add(BoolVariable('debug', "True if debug mode", 0))

    # Silent mode
    opts.Add(EnumVariable('silent',
                        '0 means max verbose, 1 less verbose, and 2 '\
                        'almost nothing',
                        '0', allowed_values = ('0', '1', '2', '3')))
    opts.Add(BoolVariable('bootstrapping',
                        "true if bootrapping numpy, false if not", 0))

    # Logging option
    opts.Add('log_level',
             '0 means max log, Any positive integer is OK '\
             '(logging value)', numscons.core.trace.CRITICAL)

    return opts

def set_bootstrap(env):
    import __builtin__
    if env['bootstrapping']:
        __builtin__.__NUMPY_SETUP__ = True

def set_verbosity(env):
    level = int(env['silent'])

    if level > 0:
        env['F2PYCOMSTR']           = "F2PY               $SOURCE"
        env['SUBSTVARCOMSTR']       = "SUBSTVAR           $SOURCE"

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

        env['ARRAYPIGENCOMSTR']     = "GENERATE ARRAY API        "
        env['UFUNCAPIGENCOMSTR']    = "GENERATE UFUNC API        "
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
    env['BUILDERS']['DistutilsInstalledStaticExtLibrary'] = \
            DistutilsInstalledStaticExtLibrary
