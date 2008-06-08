#!/usr/bin/env python
import os
import shutil

from distutils.dir_util import copy_tree
from distutils.core import setup
from distutils.dist import Distribution as old_Distribution
from distutils.command.install import install as old_install
from distutils.command.install_data import install_data as old_install_data
from distutils.command.sdist import sdist as old_sdist

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

# We implement our own add_data_dir method, to avoid depending on numpy
# distutils, which would create an obvious boostrapping problem once we want to
# build numpy with scons ... 
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

class sdist(old_sdist):
    def add_defaults (self):
        old_sdist.add_defaults(self)

        dist = self.distribution

        if dist.data_files is None:
            dist.data_files = []

        for d in dist.data_dir:
            src_data_files = []
            for roots, dirs, files in os.walk(d):
                for file in files:
                    src_data_files.append(os.path.join(roots, file))
            self.filelist.extend(src_data_files)

# Main setup method
import release as R

R.write_version()
setup(cmdclass = {'install': install, 'install_data': install_data, 'sdist': sdist},
      distclass     = Distribution,
      name          = R.NAME,
      version       = R.build_fverstring(),
      description   = R.DESCRIPTION,
      author        = R.AUTHOR,
      author_email  = R.AUTHOR_EMAIL,
      packages      = R.PACKAGES,
      package_data  = R.PACKAGE_DATA,
      data_dir      = R.DATA_DIR
      )
