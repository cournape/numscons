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
VERSION     = '0.6.3.1'
DESCRIPTION = 'Enable to use scons within distutils to build extensions'
CLASSIFIERS = filter(None, CLASSIFIERS.split('\n'))
AUTHOR      = 'David Cournapeau'
AUTHOR_EMAIL = 'david@ar.media.kyoto-u.ac.jp'
PACKAGES    = ['numscons', 'numscons.core', 'numscons.checkers',
               'numscons.tools', 'numscons.numdist',
               'numscons.checkers.tests', 'numscons.checkers.fortran']
PACKAGE_DATA = {'numscons.core' : ['compiler.cfg', 'fcompiler.cfg', 'cxxcompiler.cfg'], 
              'numscons.checkers' : ['perflib.cfg']}
DATA_DIR    = ['numscons/scons-local']
