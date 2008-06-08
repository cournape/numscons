#! /usr/bin/env python
# Last Change: Wed Jan 16 08:00 PM 2008 J
"""misc module: everything which has not other place to go."""
import shlex
import os
from os.path import join as pjoin, basename, dirname

from numscons.testcode_snippets import cblas_sgemm
from numscons.core.utils import popen_wrapper

from numscons.checkers.support import save_and_set, restore

def get_sunperf_link_options(context, config):
    """If successefull, returns the link flags.

    Returns:
        - st: int
            0 : failed
            1 : succeeded
        - flags: dict
            dictionary of the options.
    """
    context.Message('Getting link options of sunperf ... ')

    opts = config
    test_code = cblas_sgemm
    env = context.env
    saved = save_and_set(env, opts)
    try:
        st = context.TryCompile(test_code, '.c')
    finally:
        restore(env, saved)

    if not st:
        return context.Result('Failed !'), None

    saved = save_and_set(env, opts)
    env.Append(LINKFLAGS = '-#')
    oldLINK = env['LINK']
    env['LINK'] = '$CC'
    try:
        # XXX: does this scheme to get the program name always work ? Can
        # we use Scons to get the target name from the object name ?
        slast = str(context.lastTarget)
        prdir = dirname(slast)
        test_prog = pjoin(prdir, basename(slast).split('.')[0])

        cmd = context.env.subst('$LINKCOM',
                            target = context.env.File(test_prog),
                            source = context.lastTarget)
        st, out = popen_wrapper(cmd, merge = True)
    finally:
        restore(env, saved)
        env['LINK'] = oldLINK

    # If getting the verbose output succeeds, parse the output
    if not st:
        return 1, sunperf_parser_link(out)
    else:
        return 0, None


def sunperf_parser_link(out):
    """out should be a string representing the output of the sun linker, when
    sunperf is linked."""
    lexer = shlex.shlex(out, posix = True)
    lexer.whitespace_split = True

    accept_libs = ['sunperf', 'fui', 'fsu', 'mtsk', 'sunmath']
    keep = dict(zip(['libraries', 'library_dirs', 'rpath'], [[], [], []]))
    t = lexer.get_token()
    while t:
        def parse(token):
            """Parse one token of linker output.

            token is expected to be the return value of shlex.get_token
            method."""
            if token.startswith('-l'):
                n = token.split('-l')[1]
                if n in accept_libs:
                    keep['libraries'].append(n)
                t = lexer.get_token()
            elif token.startswith('-Y'):
                n = token
                t = lexer.get_token()
                if t.startswith('P,'):
                    t = t[2:]
                nt = t.split(os.pathsep)
                keep['library_dirs'].extend(nt)
            elif token.startswith('-Qy'):
                n = token
                t = lexer.get_token()
                if t.startswith('-R'):
                    arg = t.split('-R', 1)[1]
                    nt = arg.split(os.pathsep)
                    keep['rpath'].extend(nt)
            else:
                t = lexer.get_token()
            return t
        t = parse(t)

    return keep
