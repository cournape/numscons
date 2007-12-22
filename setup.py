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

from numpy.distutils.core import setup

def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration(None, parent_package, top_path)
    config.add_subpackage('numscons')
    config.add_data_dir('numscons/scons-local')
    return config

setup(name = 'numscons',
      version = '0.1dev',
      description = 'Enable to use scons within distutils to build extensions',
      classifiers = filter(None, CLASSIFIERS.split('\n')),
      author = 'David Cournapeau',
      author_email = 'david@ar.media.kyoto-u.ac.jp',
      configuration = configuration)
