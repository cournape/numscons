#! /usr/bin/env python
# Last Change: Sat Jun 07 07:00 PM 2008 J

"""This module has helper functions to get basic information from site.cfg-like
files."""
import os
import ConfigParser

from numscons.numdist import default_lib_dirs, default_include_dirs, \
                             default_src_dirs, get_standard_file
from numscons.core.utils import DefaultDict

# List of options that ConfigOpts can keep. If later additional variables
# should be added (e.g. cpp flags, etc...), they should be added here.
_SITE_CONFIG_PATH_FLAGS = ('library_dirs', 'include_dirs')
_SITE_CONFIG_NONPATH_FLAGS = ('libraries',)

_SITE_OPTS_FLAGS = _SITE_CONFIG_PATH_FLAGS + _SITE_CONFIG_NONPATH_FLAGS

class ConfigOpts(DefaultDict):
    """Small container class to keep all necessary options to build with a
    given library/package, such as cflags, libs, library paths, etc..."""
    _keys = _SITE_OPTS_FLAGS
    def __init__(self):
        DefaultDict.__init__(self, self._keys)
        for k in self._keys:
            self[k] = []

    def __repr__(self):
        msg = [r'%s : %s' % (k, i) for k, i in self.items() if len(i) > 0]
        return '\n'.join(msg)

# Think about a cache mechanism, to avoid reparsing the config file everytime.
def get_config():
    """ This tries to read .cfg files in several locations, and merge its
    information into a ConfigParser object for the first found file.

    Returns the ConfigParser instance. This copies the logic in system_info
    from numpy.distutils."""
    # Below is the feature we are copying from numpy.distutils:
    #
    # The file 'site.cfg' is looked for in

    # 1) Directory of main setup.py file being run.
    # 2) Home directory of user running the setup.py file as ~/.numpy-site.cfg
    # 3) System wide directory (location of this file...)

    # The first one found is used to get system configuration options The
    # format is that used by ConfigParser (i.e., Windows .INI style). 

    defaults = {}
    defaults['libraries'] = ''
    defaults['library_dirs'] = os.pathsep.join(default_lib_dirs)
    defaults['include_dirs'] = os.pathsep.join(default_include_dirs)
    defaults['src_dirs'] = os.pathsep.join(default_src_dirs)
    cp = ConfigParser.ConfigParser(defaults)
    files = []
    files.extend(get_standard_file('.numpy-site.cfg'))
    files.extend(get_standard_file('site.cfg'))

    return cp, files

def parse_config_param(var):
    """Given var, the output of ConfirParser.get(section, name), returns a list
    of each item of its content."""
    varl = var.split(',')
    return [i.strip() for i in varl if len(i) > 0]

def get_paths(var):
    """Given var, the output of ConfirParser.get(section, name), returns a list
    of each item of its content, assuming the content is a list of directoris.

    Example: if var is foo:bar, it will return ['foo', 'bar'] on posix."""
    return var.split(os.pathsep)

def get_config_from_section(siteconfig, section):
    """For the given siteconfig and section, return the found information.

    Returns a tuple (info, found), where:
        info : ConfigOpts instance
        found: True if the section was found, False otherwise."""
    cfgopts = ConfigOpts()
    found = False
    defaults = siteconfig.defaults()
    if len(defaults) > 0:
        # the customization file has a default section: we add all its options
        # into cfgopts (only the ones which make sense)
        for k, v in defaults.items():
            if k in _SITE_CONFIG_PATH_FLAGS:
                cfgopts[k].extend(get_paths(v))
            elif k in _SITE_CONFIG_NONPATH_FLAGS:
                cfgopts[k].extend(parse_config_param(v))

    if siteconfig.has_section(section):
        found = True
        for opt in _SITE_CONFIG_PATH_FLAGS:
            if siteconfig.has_option(section, opt):
                cfgopts[opt].extend(get_paths(siteconfig.get(section, opt)))

        for opt in _SITE_CONFIG_NONPATH_FLAGS:
            if siteconfig.has_option(section, opt):
                cfgopts[opt].extend(parse_config_param(siteconfig.get(section, opt)))

    return cfgopts, found
