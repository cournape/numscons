import os
import shutil
import sys

from copy import deepcopy

from numscons.core.misc import \
    get_scons_configres_dir
from numscons.checkers.perflib_config import \
        AtlasConfig, MklConfig, AccelerateConfig, GenericBlasConfig, \
        GenericLapackConfig
from numscons.checkers.config import \
        read_atlas, read_mkl, read_accelerate, read_generic_blas, \
        read_generic_lapack

def save_and_set(env, opts, keys=None):
    """Put informations from option configuration into a scons environment, and
    returns the savedkeys given as config opts args."""
    saved_keys = {}
    if keys is None:
        keys = opts.keys()
    for k in keys:
        saved_keys[k] = (env.has_key(k) and deepcopy(env[k])) or []

    kw = dict(zip(keys, [opts[k] for k in keys]))
    if kw.has_key('LINKFLAGSEND'):
        env.AppendUnique(**{'LINKFLAGSEND' : kw['LINKFLAGSEND']})
        del kw['LINKFLAGSEND']

    env.Prepend(**kw)
    return saved_keys

def restore(env, saved):
    keys = saved.keys()
    kw = dict(zip(keys, [saved[k] for k in keys]))
    env.Replace(**kw)

def get_initialized_perflib_config(env, name):
    """Return initialized configuration of the given name."""
    try:
        return env['__NUMSCONS']['CONFIGURATION']['PERFLIB_CONFIG'][name]
    except KeyError, e:
        raise RuntimeError("Could not find config for perflib %s " \
                           "(exception: %s)" % (name, str(e)))

def get_perflib_names(env):
    """Return list of perflibs to test before using generic code (if any)."""
    return env['__NUMSCONS']['CONFIGURATION']['PERFLIBS_TO_TEST']

def set_perflib_names(env, list):
    """Set list of perflibs to test before using generic code (if any)."""
    env['__NUMSCONS']['CONFIGURATION']['PERFLIBS_TO_TEST'] = list

def set_checker_result(env, name, info):
    """Set config results for the given checker.
    
    Arguments
    ---------
    name: str
        name of the checker (Lapack, Blas, etc...)
    info: object
        Usually a *Config instance, but can be any object with a str method"""
    env['__NUMSCONS']['CONFIGURATION']['RESULTS'][name] = info

def init_configuration(env):
    env['__NUMSCONS']['CONFIGURATION'] = {}
    env['__NUMSCONS']['CONFIGURATION']['RESULTS'] = {}
    env['__NUMSCONS']['CONFIGURATION']['PERFLIB_CONFIG'] = {}

    env['__NUMSCONS']['CONFIGURATION']['PERFLIB_CONFIG'] = {
            'Atlas': AtlasConfig(read_atlas(env)),
            'Mkl': MklConfig(read_mkl(env)),
            'Accelerate': AccelerateConfig(read_accelerate(env)),
            'GenericBlas': GenericBlasConfig(read_generic_blas(env)),
            'GenericLapack': GenericLapackConfig(read_generic_lapack(env))
        }

    perflibs = []
    if sys.platform == "darwin":
        perflibs.extend(["Accelerate", "Atlas", "Mkl"])
    elif sys.platform == "win32":
        perflibs.extend(["Atlas", "Mkl"])
    else:
        perflibs.extend(["Atlas", "Mkl"])
    perflibs.extend(["GenericLapack", "GenericBlas"])

    set_perflib_names(env, perflibs)

def write_configuration_results(env):
    cfg = env['__NUMSCONS']['CONFIGURATION']['RESULTS']
    config_str = {}
    for k, i in cfg.items():
        config_str[k] = str(i)

    # XXX: do it the scons way to put this in the DAG
    f = open(env['NUMPY_PKG_CONFIG_FILE'], 'w')
    f.writelines("%s" % str(config_str))
    f.close()

    target = os.path.join(str(env.fs.Top), get_scons_configres_dir(),
            env['src_dir'], "__configres.py")

    if not os.path.exists(os.path.dirname(target)):
        os.makedirs(os.path.dirname(target))
    shutil.copy(env['NUMPY_PKG_CONFIG_FILE'], target)

def get_perflib_implementation(env, interface):
    try:
        return env['__NUMSCONS']['CONFIGURATION']['RESULTS'][interface].name
    except KeyError, e:
        return RuntimeError("Could not get perflib implementing interface %s" \
                            " (was %s)" % (interface, str(e)))
