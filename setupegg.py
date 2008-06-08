#!/usr/bin/env python
import os
import shutil

from setuptools import setup

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

# Main setup method
import release as R

R.write_version()
setup(name          = R.NAME,
      version       = R.build_fverstring(),
      description   = R.DESCRIPTION,
      author        = R.AUTHOR,
      author_email  = R.AUTHOR_EMAIL,
      packages      = R.PACKAGES,
      package_data  = R.PACKAGE_DATA,
      include_package_data = True)
