from copy import deepcopy

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
