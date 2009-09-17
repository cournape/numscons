import os

from numscons.core.helpers import \
        GetNumpyOptions, set_bootstrap, set_site_config, set_verbosity, \
        add_custom_builders
from numscons.core.initialization import \
        initialize_tools
from numscons.core.customization import \
        customize_tools, is_importing_environment
from numscons.checkers.common import \
        init_configuration

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

    if is_importing_environment(env):
        env['ENV'] = os.environ

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
    init_configuration(env)

    return env
