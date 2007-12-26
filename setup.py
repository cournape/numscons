#!/usr/bin/env python
import os
import shutil

from distutils.dir_util import copy_tree
from distutils.core import setup
from distutils.dist import Distribution as old_Distribution
from distutils.command.install import install as old_install

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

class Distribution(old_Distribution):
    def __init__(self, attrs = None):
        assert not hasattr(self, 'data_dir')
        self.data_dir = []
        old_Distribution.__init__(self, attrs)

# We implement our own add_data_dir method, to avoid depending on numpy
# distutils, which would create an obvious boostrapping problem once we want to
# build numpy with scons ...
class install(old_install):
    def initialize_options(self):
        old_install.initialize_options(self)

    def run(self):
        old_install.run(self)
        dist = self.distribution
        for d in dist.data_dir:
            install_data_dir = os.path.join(self.install_purelib, d)
            copy_tree(d, install_data_dir)
        
setup(cmdclass = {'install': install},
      distclass = Distribution,
      name = 'numscons',
      version = '0.1dev',
      description = 'Enable to use scons within distutils to build extensions',
      classifiers = filter(None, CLASSIFIERS.split('\n')),
      author = 'David Cournapeau',
      author_email = 'david@ar.media.kyoto-u.ac.jp',
      packages = ['numscons', 'numscons.core', 'numscons.checkers', 'numscons.tools'],
      package_data = {'numscons.core' : ['compiler.cfg']},
      data_dir = ['numscons/scons-local'],
      )
