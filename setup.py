#!/usr/bin/env python
import os
import shutil

from distutils.dir_util import copy_tree
from distutils.core import setup
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
# build numpy with scons ... Thanks to distutils wonderful design, this means
# we have to reimplement 3 classes, yeah !

class Distribution(old_Distribution):
    """This new Distribution class is necessary to support the new data_dir
    argument in setup files."""
    def __init__(self, attrs = None):
        assert not hasattr(self, 'data_dir')
        self.data_dir = []
        old_Distribution.__init__(self, attrs)

class install_data(old_install_data):
    """this install_data command does not install data files into the wild, but
    put them into the package directory."""
    def finalize_options(self):
        if self.install_dir is None:
            installobj = self.distribution.get_command_obj('install')
            self.install_dir = installobj.install_purelib

    def run(self):
        old_install_data.run(self)

class install(old_install):
    """This install command extends the data_files list of data files using the
    data_dir argument."""
    def run(self):
        dist = self.distribution

        if dist.data_files is None:
            dist.data_files = []

        for d in dist.data_dir:
            install_data_files = []
            for roots, dirs, files in os.walk(d):
                for file in files:
                    install_data_files.append((roots, [os.path.join(roots, file)]))

            dist.data_files.extend(install_data_files)

        old_install.run(self)

# Main setup method
setup(cmdclass = {'install': install, 'install_data': install_data},
      distclass = Distribution,
      name = 'numscons',
      version = '0.2dev',
      description = 'Enable to use scons within distutils to build extensions',
      classifiers = filter(None, CLASSIFIERS.split('\n')),
      author = 'David Cournapeau',
      author_email = 'david@ar.media.kyoto-u.ac.jp',
      packages = ['numscons', 'numscons.core', 'numscons.checkers',
                  'numscons.tools'],
      package_data = {'numscons.core' : ['compiler.cfg', 'fcompiler.cfg'], 
                      'numscons.checkers' : ['perflib.cfg']},
      data_dir = ['numscons/scons-local'],
      )
