"""This module implements wrappers around numpy.distutils template functions so
that they can be used in scons builders. Both C and Fortran .src files
generators are implemented."""
import re
from os.path import basename as pbasename, splitext, join as pjoin, \
                    dirname as pdirname

from numscons.numdist import process_c_file
from numscons.numdist import process_f_file

def do_generate_from_c_template(targetfile, sourcefile, env):
    """Generate a C source file from template using numpy.distutils
    process_file."""
    t = open(targetfile, 'w')
    writestr = process_c_file(sourcefile)
    t.write(writestr)
    t.close()
    return 0

def do_generate_from_f_template(targetfile, sourcefile, env):
    """Generate a Fortran source file from template using numpy.distutils
    process_file."""
    t = open(targetfile, 'w')
    writestr = process_f_file(sourcefile)
    t.write(writestr)
    t.close()
    return 0

def generate_from_c_template(target, source, env):
    """This function can be used directly in scons builders."""
    for t, s in zip(target, source):
        do_generate_from_c_template(str(t), str(s), env)
    return 0

def generate_from_f_template(target, source, env):
    """This function can be used directly in scons builders."""
    for t, s in zip(target, source):
        do_generate_from_f_template(str(t), str(s), env)
    return 0

def generate_from_template_emitter(target, source, env):
    """Scons emitter for both C and Fortran generated files from template (.src
    files)."""
    base = splitext(pbasename(str(source[0])))[0]
    t = pjoin(pdirname(str(target[0])), base)
    return ([t], source)

_INCLUDE_RE = re.compile(r"include\s*['\"](\S+)['\"]", re.M)

def generate_from_template_scanner(node, env, path, arg = None):
    cnt = node.get_contents()
    return _INCLUDE_RE.findall(cnt)
