#!/usr/bin/env python
import os
import shutil

from setuptools import setup
from distutils.dist import Distribution as old_Distribution
from distutils.command.install import install as old_install
from distutils.command.install_data import install_data as old_install_data

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

# We implement our own add_data_dir method, to avoid depending on numpy
# distutils, which would create an obvious boostrapping problem once we want to
# build numpy with scons 
class Distribution(old_Distribution):
    """This new Distribution class is necessary to support the new data_dir
    argument in setup files."""
    def __init__(self, attrs = None):
        assert not hasattr(self, 'data_dir')
        self.data_dir = []
        old_Distribution.__init__(self, attrs)

        # Butt ugly: we add the data directories when the distribution is
        # initialized. But it does not work with eggs otherwise ?
        for d in self.data_dir:
            install_data_files = []
            for roots, dirs, files in os.walk(d):
                for file in files:
                    install_data_files.append((roots, [os.path.join(roots, file)]))

        if self.data_files:
            self.data_files.extend(install_data_files)
        else:
            self.data_files = install_data_files

# Main setup method
setup(distclass = Distribution,
      name = 'numscons',
      version = '0.3.1dev',
      description = 'Enable to use scons within distutils to build extensions',
      classifiers = filter(None, CLASSIFIERS.split('\n')),
      author = 'David Cournapeau',
      author_email = 'david@ar.media.kyoto-u.ac.jp',
      packages = ['numscons', 'numscons.core', 'numscons.checkers',
                  'numscons.tools', 'numscons.numdist',
                  'numscons.checkers.tests', 'numscons.checkers.fortran'],
      package_data = {'numscons.core' : ['compiler.cfg', 'fcompiler.cfg'], 
                      'numscons.checkers' : ['perflib.cfg']},
      data_dir = ['numscons/scons-local'],
      )
