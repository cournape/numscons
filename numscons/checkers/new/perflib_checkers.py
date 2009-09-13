from numscons.checkers.new.common import \
    save_and_set, restore, get_initialized_perflib_config

# Performance library checks
def _check_perflib(context, autoadd, info):
    context.Message("Checking for %s ... " % info.name)

    if info.disabled():
        context.Result('no - disabled from user environment')
        return 0

    saved = save_and_set(context.env, info._core, info._core.keys())
    ret = context.TryLink(info.test_code, extension='.c')
    if not ret or not autoadd:
        restore(context.env, saved)

    context.Result(ret)
    return ret

def CheckAtlas(context, autoadd=1):
    return _check_perflib(context, autoadd,
            get_initialized_perflib_config(context.env, 'ATLAS'))

def CheckMkl(context, autoadd=1):
    return _check_perflib(context, autoadd,
            get_initialized_perflib_config(context.env, 'MKL'))
