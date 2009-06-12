import os

CLASSIFIERS = """\
Development Status :: 3 - Alpha
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved
Programming Language :: Python
Topic :: Software Development
Topic :: Scientific/Engineering
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

NAME        = 'numscons'
MAJOR       = 0
MINOR       = 10
MICRO       = 0
DEV         = False
DESCRIPTION = 'Enable to use scons within distutils to build extensions'
CLASSIFIERS = filter(None, CLASSIFIERS.split('\n'))
AUTHOR      = 'David Cournapeau'
AUTHOR_EMAIL = 'david@ar.media.kyoto-u.ac.jp'
PACKAGES    = ['numscons', 'numscons.core', 'numscons.checkers',
               'numscons.tools', 'numscons.numdist',
               'numscons.checkers.fortran']
PACKAGE_DATA = {'numscons.core' :
                    [os.path.join('configurations', i) for i in
                     ['compiler.cfg', 'fcompiler.cfg', 'cxxcompiler.cfg']],
              'numscons.checkers' : ['perflib.cfg']}
DATA_DIR    = ['numscons/scons-local']

def build_verstring():
    return '%d.%d.%d' % (MAJOR, MINOR, MICRO)

def build_fverstring():
    if DEV:
        return build_verstring() + 'dev'
    else:
        return build_verstring()

def write_version():
    fname = os.path.join("numscons", "version.py")
    f = open(fname, "w")
    f.writelines("VERSION = '%s'\n" % build_verstring())
    f.writelines("DEV = %s" % DEV)
    f.close()
