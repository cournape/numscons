#! Last Change: Mon Nov 12 07:00 PM 2007 J

# This module defines some functions/classes useful for testing fortran-related
# features (name mangling, F77/C runtime, etc...).

# KEEP THIS INDEPENDENT OF SCONS, PLEASE !!!

import sys
import re
import os
import shlex

GCC_DRIVER_LINE = re.compile('^Driving:')
POSIX_STATIC_EXT = re.compile('\S+\.a')
POSIX_LIB_FLAGS = re.compile('-l\S+')

# linkflags which match those are ignored
LINKFLAGS_IGNORED = [r'-lang*', r'-lcrt[a-zA-Z0-9]*\.o', r'-lc', r'-lSystem', r'-libmil', r'-LIST:*', r'-LNO:*']
if os.name == 'nt':
    LINKFLAGS_IGNORED.extend([r'-lfrt*', r'-luser32',
	    r'-lkernel32', r'-ladvapi32', r'-lmsvcrt',
	    r'-lshell32', r'-lmingw', r'-lmoldname'])
else:
    LINKFLAGS_IGNORED.append(r'-lgcc*')

RLINKFLAGS_IGNORED = [re.compile(i) for i in LINKFLAGS_IGNORED]

# linkflags which match those are the one we are interested in
LINKFLAGS_INTERESTING = [r'-[lLR][a-zA-Z0-9]*']
RLINKFLAGS_INTERESTING = [re.compile(i) for i in LINKFLAGS_INTERESTING]

def gnu_to_ms_link(linkflags):
    # XXX: This is bogus. Instead of manually playing with those flags, we
    # should use scons facilities, but this is not so easy because we want to
    # use posix environment and MS environment at the same time. If we need it
    # at several places, we will have to think on a better way.
    newflags = []
    for flag in linkflags:
        if flag.startswith('-L'):
            newflags.append(r'/LIBPATH:%s' % flag[2:])
        elif flag.startswith('-l'):
            newflags.append(r'lib%s.a' % flag[2:])
    return newflags

def get_g2c_libs(libs, libpaths):
    """Given a list of libraries and libpaths, return the fullpath of the
    libraries.

    Only works on windows platform, for windows convention (should be used only
    for gcc<-> VS interop."""  
    g2c_support = []
    def _get_lib(lib, libpaths):
        for path in libpaths:
            fullname = os.path.join(path, 'lib%s.a' % lib)
            if os.path.exists(fullname):
                return fullname
        return ''

    for lib in libs:
        fname = _get_lib(lib, libpaths)     
        if len(fname) > 0:
            g2c_support.append(fname)
            
    return g2c_support 

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

def match_ignore(str):
    if [i for i in RLINKFLAGS_IGNORED if i.match(str)]:
        return True
    else:
        return False

def parse_f77link(lines):
    """Given the output of verbose link of F77 compiler, this returns a list of
    flags necessary for linking using the standard linker."""
    # TODO: On windows ?
    # TODO: take into account quotting...
    # Those options takes an argument, so concatenate any following item
    # until the end of the line or a new option.
    remove_space = ['-[LRuYz]*']
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
    keep = dict(zip(('libraries', 'library_dirs', 'rpath'), ([], [], [])))
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
            #   6 For -YP,*: take and replace by -Larg where arg is the old argument
            #   7 For -[lLR]*: take

            # step 3
            if match_ignore(token):
                t = lexer.get_token()
            # step 4
            elif token.startswith('-lkernel32'):
                final_flags.append(t)
            # step 5
            elif SPACE_OPTS.match(token):
                n = token
                t = lexer.get_token()
                if t.startswith('P,'):
                    t = t[2:]
                for opt in t.split(os.pathsep):
                    final_flags.append('-L%s' % opt)
            # step 6
            elif NOSPACE_OPTS.match(token):
                final_flags.append(token)
                t = lexer.get_token()
            # step 7
            elif POSIX_LIB_FLAGS.match(token):
                final_flags.append(token)
                t = lexer.get_token()
            else:
                t = lexer.get_token()

            return t
        t = parse(t)
    return final_flags
