#! Last Change: Sun Jan 27 04:00 PM 2008 J

# This module defines some functions/classes useful for testing fortran-related
# features (name mangling, F77/C runtime, etc...).

# KEEP THIS INDEPENDENT OF SCONS, PLEASE !!!

import sys
import re
import os
from os.path import join, basename
import shlex
import shutil

from numscons.core.utils import unique

GCC_DRIVER_LINE = re.compile('^Driving:')
POSIX_STATIC_EXT = re.compile('\S+\.a')
POSIX_LIB_FLAGS = re.compile('-l\S+')

# linkflags which match those are ignored
LINKFLAGS_IGNORED = [r'-lang*', r'-lcrt[a-zA-Z0-9]*\.o', r'-lc$', r'-lSystem',
                     r'-libmil', r'-LIST:*', r'-LNO:*']
if os.name == 'nt':
    LINKFLAGS_IGNORED.extend([r'-lfrt*', r'-luser32',
            r'-lkernel32', r'-ladvapi32', r'-lmsvcrt',
            r'-lshell32', r'-lmingw', r'-lmoldname'])
else:
    LINKFLAGS_IGNORED.append(r'-lgcc*')

RLINKFLAGS_IGNORED = [re.compile(f) for f in LINKFLAGS_IGNORED]

def gnu_to_scons_flags(linkflags):
    # XXX: This is bogus. Instead of manually playing with those flags, we
    # should use scons facilities, but this is not so easy because we want to
    # use posix environment and MS environment at the same time. If we need it
    # at several places, we will have to think on a better way.
    newflags = {'LIBPATH': [], 'LIBS': []}
    for flag in linkflags:
        if flag.startswith('-L'):
            newflags['LIBPATH'].append(r'%s' % flag[2:])
        elif flag.startswith('-l'):
            newflags['LIBS'].append(r'%s' % flag[2:])
    return newflags

def find_libs_paths(libs, libpaths, prefix = "lib", suffix = ".a"):
    """Given a list of libraries and libpaths, return the fullpath of the
    libraries."""
    ret = []

    def fdlib(libn, libpaths):
        for libpath in libpaths:
                if os.path.exists(join(libpath, libname)):
                    return join(libpath, libname)
        return None

    for lib in libs:
        libname = "%s%s%s" % (prefix, lib, suffix)
        if fdlib(libname, libpaths):
            ret.append(fdlib(libname, libpaths))
        else:
            raise RuntimeError("%s not found ?" % libname)
    return ret

def get_g2c_libs(env, final_flags):
    # XXX:Fix me this ugly piece of code
    pf = gnu_to_scons_flags(final_flags)
    pf["LIBS"] = unique(pf["LIBS"])
    rtlibs = find_libs_paths(pf["LIBS"], pf["LIBPATH"])
    msrtlibs =[]
    tmpdir = join("build", "g77_runtime")
    # XXX: clean the path before
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir)
    for i in rtlibs:
        mslib = gnulib2mslib(i)
        mslibpath = join(tmpdir, mslib)
        #print "Copying %s in %s" % (i, mslibpath)
        shutil.copy(i, mslibpath)
        msrtlibs.append(mslib)

    return tmpdir, msrtlibs

def gnulib2mslib(lib, gprefix = "lib", gsuffix = ".a", msprefix = "", mssuffix = ".lib"):
    p = len(gprefix)
    s = len(gsuffix)
    return "%s%s%s" % (msprefix, basename(lib)[p:-s], mssuffix)

def _check_link_verbose_posix(lines):
    """Returns true if useful link options can be found in output.

    POSIX implementation.

    Expect lines to be a list of lines."""
    for line in lines:
        if not GCC_DRIVER_LINE.search(line):
            if POSIX_STATIC_EXT.search(line) or POSIX_LIB_FLAGS.search(line):
                return True
    return False

def check_link_verbose(lines):
    """Return true if useful link option can be found in output."""
    if sys.platform == 'win32':
        raise NotImplementedError("FIXME: not implemented on win32")
    else:
        return _check_link_verbose_posix(lines)

def _match_ignore(line):
    """True if the line should be ignored."""
    if [i for i in RLINKFLAGS_IGNORED if i.match(line)]:
        return True
    else:
        return False

def parse_f77link(lines):
    """Given the output of verbose link of F77 compiler, this returns a list of
    flags necessary for linking using the standard linker."""
    # TODO: On windows ?
    final_flags = []
    for line in lines:
        if not GCC_DRIVER_LINE.match(line):
            _parse_f77link_line(line, final_flags)
    return final_flags

SPACE_OPTS = re.compile('^-[LRuYz]$')
NOSPACE_OPTS = re.compile('^-[RL]')

def _parse_f77link_line(line, final_flags):
    lexer = shlex.shlex(line, posix = True)
    lexer.whitespace_split = True

    t = lexer.get_token()
    tmp_flags = []
    while t:
        def parse(token):
            # Here we go (convention for wildcard is shell, not regex !)
            #   1 TODO: we first get some root .a libraries
            #   2 TODO: take everything starting by -bI:*
            #   3 Ignore the following flags: -lang* | -lcrt*.o | -lc |
            #   -lgcc* | -lSystem | -libmil | -LANG:=* | -LIST:* | -LNO:*)
            #   4 take into account -lkernel32
            #   5 For options of the kind -[[LRuYz]], as they take one argument
            #   after, the actual option is the next token
            #   6 For -YP,*: take and replace by -Larg where arg is the old
            #   argument
            #   7 For -[lLR]*: take

            # step 3
            if _match_ignore(token):
                pass
            # step 4
            elif token.startswith('-lkernel32') and sys.platform == 'cygwin':
                tmp_flags.append(token)
            # step 5
            elif SPACE_OPTS.match(token):
                t = lexer.get_token()
                if t.startswith('P,'):
                    t = t[2:]
                for opt in t.split(os.pathsep):
                    tmp_flags.append('-L%s' % opt)
            # step 6
            elif NOSPACE_OPTS.match(token):
                tmp_flags.append(token)
            # step 7
            elif POSIX_LIB_FLAGS.match(token):
                tmp_flags.append(token)
            else:
                # ignore anything not explicitely taken into account
                pass

            t = lexer.get_token()
            return t
        t = parse(t)

    final_flags.extend(tmp_flags)
    return final_flags
