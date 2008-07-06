#! /usr/bin/env python
# Last Change: Sun Jul 06 03:00 PM 2008 J

"""This module defines some helper functions, to be used by high level
checkers."""
from copy import deepcopy

# Tools to save and restore environments construction variables (the ones often
# altered for configuration tests).
_arg2env = {'include_dirs' : 'CPPPATH',
            'cflags' : 'CFLAGS',
            'library_dirs' : 'LIBPATH',
            'libraries' : 'LIBS',
            'linkflags' : 'LINKFLAGS',
            'linkflagsend' : 'LINKFLAGSEND',
            'rpath' : 'RPATH',
            'frameworks' : 'FRAMEWORKS'}

def save_and_set(env, opts, keys = None):
    """Put informations from option configuration into a scons environment, and
    returns the savedkeys given as config opts args."""
    saved_keys = {}
    if keys is None:
        keys = opts.keys()
    for k in keys:
        saved_keys[k] = (env.has_key(_arg2env[k]) and\
                         deepcopy(env[_arg2env[k]])) or\
                        []
    kw = zip([_arg2env[k] for k in keys], [opts[k] for k in keys])
    kw = dict(kw)
    if kw.has_key('LINKFLAGSEND'):
        env.AppendUnique(**{'LINKFLAGSEND' : kw['LINKFLAGSEND']})
        del kw['LINKFLAGSEND']

    env.Append(**kw)
    return saved_keys

def restore(env, saved):
    keys = saved.keys()
    kw = zip([_arg2env[k] for k in keys],
             [saved[k] for k in keys])
    kw = dict(kw)
    env.Replace(**kw)

# Implementation function to check symbol in a library
def check_symbol(context, headers, sym, extra = r''):
    # XXX: add dep vars in code
    #code = [r'#include <%s>' %h for h in headers]
    code = []
    code.append(r'''
#undef %(func)s
#ifdef __cplusplus
extern "C"
#endif
char %(func)s();

int main()
{
return %(func)s();
return 0;
}
''' % {'func' : sym})
    code.append(extra)
    return context.TryLink('\n'.join(code), '.c')

def _check_headers(context, opts, headers, autoadd):
    """Try to compile code including the given headers."""
    env = context.env

    #----------------------------
    # Check headers are available
    #----------------------------
    keys = ('include_dirs', 'cflags')
    saved = save_and_set(context.env, opts, keys)
    try:
        # XXX: handle context
        hcode = ['#include <%s>' % h for h in headers]

        # HACK: we add cpppath in the command of the source, to add dependency of
        # the check on the cpppath.
        hcode.extend(['#if 0', str(opts), '#endif\n'])
        src = '\n'.join(hcode)
        ret = context.TryCompile(src, '.c')
    finally:
        if ret == 0 or autoadd == 0:
            restore(context.env, saved)

    return ret

def check_include_and_run(context, name, opts, headers, run_src, autoadd = 1):
    """This is a basic implementation for generic "test include and run"
    testers.

    For example, for library foo, which implements function do_foo, and with
    include header foo.h, this will:
        - test that foo.h is found and compilable by the compiler
        - test that the given source code can be compiled. The source code
          should contain a simple program with the function.

    XXX: this doc is not up-to-date
    Arguments:
        - name: name of the library
        - include_dirs: list of directories
        - headers: list of headers
        - run_src: the code for the run test
        - libs: list of libraries to link
        - library_dirs: list of library path.
        - linkflags: list of link flags to add."""

    context.Message('Checking for %s ... ' % name)
    env = context.env

    ret = _check_headers(context, opts, headers, autoadd)
    if not ret:
        context.Result('Failed: %s include not found' % name)
        return 0

    #------------------------------
    # Check a simple example works
    #------------------------------
    keys = ('library_dirs', 'cflags')
    saved = save_and_set(env, opts)
    try:
        # HACK: we add libpath and libs at the end of the source as a comment,
        # to add dependency of the check on those.
        src = '\n'.join([r'#include <%s>' % h for h in headers] +\
                        [run_src, r'#if  0', r'%s' % str(opts), r'#endif',
                         '\n'])
        ret, out = context.TryRun(src, '.c')
    finally:
        if (not ret or not autoadd):
            # If test failed or autoadd is disabled, restore everything
            restore(env, saved)

    if not ret:
        context.Result('Failed: %s test could not be linked and run' % name)
        return 0

    context.Result(ret)
    return ret

def check_run_f77(context, name, opts, run_src, autoadd = 1):
    """This is a basic implementation for generic "run" testers.

    For example, for library foo, which implements function do_foo
        - test that the given source code can be compiled. The source code
          should contain a simple program with the function.

    Arguments:
        - name: name of the library."""

    context.Message('Checking for %s ... ' % name)
    env = context.env

    #------------------------------
    # Check a simple example works
    #------------------------------
    saved = save_and_set(env, opts)
    try:
        # HACK: we add libpath and libs at the end of the source as a comment,
        # to add dependency of the check on those.
        src = '\n'.join([run_src] + [r'* %s' % s for s in
                                     str(opts).split('\n')])
        ret, out = context.TryRun(src, '.f')
    finally:
        if (not ret or not autoadd):
            # If test failed or autoadd is disabled, restore everything
            restore(env, saved)

    if not ret:
        context.Result('Failed: %s test could not be linked and run' % name)
        return 0

    context.Result(ret)
    return ret
