from numscons.core.helpers import \
        GetNumpyOptions, set_bootstrap, set_site_config, set_verbosity, \
        add_custom_builders
from numscons.core.initialization import \
        initialize_tools
from numscons.core.customization import \
        customize_tools
from numscons.checkers.perflib_config import \
        AtlasConfig, MklConfig
from numscons.checkers.config import \
        read_atlas, read_mkl

__all__ = ['GetNumpyEnvironment', 'GetInitEnvironment']

def GetNumpyEnvironment(args):
    """Returns a correctly initialized scons environment.

    This environment contains builders for python extensions, ctypes
    extensions, fortran builders, etc... Generally, call it with args =
    ARGUMENTS, which contain the arguments given to the scons process.

    This method returns an environment with fully customized flags."""
    env = _get_numpy_env(args)

    return env

def GetInitEnvironment(args):
    return _init_environment(args)

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

def _get_numpy_env(args):
    """Call this with args = ARGUMENTS."""
    env = _init_environment(args)

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

    # Initialized numscons checkers internal variables
    env['__NUMSCONS'] = {}
    env['__NUMSCONS']['CONFIGURATION'] = {}
    env['__NUMSCONS']['CONFIGURATION']['RESULTS'] = {}
    env['__NUMSCONS']['CONFIGURATION']['PERFLIB_CONFIG'] = {}
    env['__NUMSCONS']['CONFIGURATION']['PERFLIBS_TO_TEST'] = ('Mkl', 'Atlas')
    env['__NUMSCONS']['CONFIGURATION']['PERFLIB_CONFIG'] = {
            'Atlas': AtlasConfig(read_atlas()), 'Mkl': MklConfig(read_mkl()),
        }

    return env
