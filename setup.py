#!/usr/bin/env python
import os

CLASSIFIERS = """\
Development Status :: 4 - Beta
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

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from distutils.core import setup

setup(name = 'numscons',
      version = '0.1',
      description = 'Enable to use scons within distutils to build extensions',
      author = 'David Cournapeau',
      author_email = 'david@ar.media.kyoto-u.ac.jp',
      packages = ['numscons', 'numscons.core'],
     )
