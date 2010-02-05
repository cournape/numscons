from numscons.checkers.perflib_checkers import \
        _check_perflib
from numscons.checkers.common import \
        get_perflib_names, get_initialized_perflib_config, \
        save_and_set, restore, set_checker_result
from numscons.checkers.testcode_snippets import \
        BLAS_TEST_CODE, LAPACK_TEST_CODE, CBLAS_TEST_CODE
from numscons.checkers.fortran import CheckF77Mangling, CheckF77Clib

__all__ = ['CheckF77Lapack', 'CheckF77Blas', 'CheckCblas']

def _check_fortran(context, name, autoadd, test_code_tpl, func):
    # Generate test code using name mangler
    try:
        mangler = context.env['F77_NAME_MANGLER']
    except KeyError:
        if not CheckF77Mangling(context):
            return 0
        mangler = context.env['F77_NAME_MANGLER']
    test_code = test_code_tpl % {'func': mangler(func)}

    try:
        f77_ldflags = context.env['F77_LDFLAGS']
    except KeyError:
        if not CheckF77Clib(context, autoadd=0):
            return 0
        f77_ldflags = context.env['F77_LDFLAGS']

    # Detect which performance library to use
    info = None
    for perflib in get_perflib_names(context.env):
        _info = get_initialized_perflib_config(context.env, perflib)
        if  name in _info.interfaces() and _check_perflib(context, 0, _info):
            info = _info
            break

    context.Message("Checking for F77 %s ... " % name)

    if info is None:
        context.Result('no')
        return 0

    if not info._interfaces[name].has_key("LINKFLAGSEND"):
        info._interfaces[name]["LINKFLAGSEND"] = f77_ldflags[:]
    else:
        info._interfaces[name]["LINKFLAGSEND"].extend(f77_ldflags[:])

    if not name in info.interfaces():
        raise RuntimeError("%s does not support %s interface" % \
                (info.__class__, name))

    saved = save_and_set(context.env, info._interfaces[name],
                info._interfaces[name].keys())
    ret = context.TryLink(test_code, extension='.c')
    if not ret or not autoadd:
        restore(context.env, saved)
    if not ret:
        context.Result('no')
    context.Result('yes - %s' % info.name)
    set_checker_result(context.env, name, info)
    return ret

def _check_c(context, name, autoadd, test_code):
    # Detect which performance library to use
    info = None
    for perflib in get_perflib_names(context.env):
        _info = get_initialized_perflib_config(context.env, perflib)
        if  name in _info.interfaces() and _check_perflib(context, 0, _info):
            info = _info
            break

    context.Message("Checking for %s ... " % name.upper())

    if info is None:
        context.Result('no')
        return 0

    if not name in info.interfaces():
        raise RuntimeError("%s does not support %s interface" % \
                (info.__class__, name.upper()))

    saved = save_and_set(context.env, info._interfaces[name],
                info._interfaces[name].keys())
    ret = context.TryLink(test_code, extension='.c')
    if not ret or not autoadd:
        restore(context.env, saved)
    if not ret:
        context.Result('no')
    context.Result('yes - %s' % info.name)
    return ret

def CheckF77Lapack(context, autoadd=1, check_version=0):
    return _check_fortran(context, 'LAPACK', autoadd, LAPACK_TEST_CODE,
            'sgesv')

def CheckF77Blas(context, autoadd=1, check_version=0):
    return _check_fortran(context, 'BLAS', autoadd, BLAS_TEST_CODE, 'sgemm')

def CheckCblas(context, autoadd=1, check_version=0):
    return _check_c(context, 'CBLAS', autoadd, CBLAS_TEST_CODE)
