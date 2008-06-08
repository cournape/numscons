#! /usr/bin/env python
# Last Change: Sat Jan 26 07:00 PM 2008 J

"""This module implements the functionality to keep all necessary build
informations about perflib and meta lib, so that those info can be passed from
one function to the other.  """
from copy import copy

from numscons.core.utils import DefaultDict

# List of options that BuildConfig can keep. If later additional variables
# should be added (e.g. cpp flags, etc...), they should be added here.
_BUILD_OPTS_FLAGS = ('include_dirs', 'cflags', 'library_dirs', 'libraries',
                     'linkflags', 'linkflagsend', 'rpath', 'frameworks')

# List of options that BuildConfigFactory can keep. If later additional
# variables should be added, they should be added here.
_BUILD_OPTS_FACTORY_FLAGS = _BUILD_OPTS_FLAGS + \
    ('cblas_libs', 'blas_libs', 'clapack_libs', 'lapack_libs', 'fft_libs',
     'htc', 'ftc')

def build_config_flags():
    return _BUILD_OPTS_FLAGS

def build_config_factory_flags():
    return _BUILD_OPTS_FACTORY_FLAGS

class BuildConfig(DefaultDict):
    """Small container class to keep all necessary options to build with a
    given library/package, such as cflags, libs, library paths, etc..."""
    _keys = _BUILD_OPTS_FLAGS
    def __init__(self):
        DefaultDict.__init__(self, self._keys)
        for k in self._keys:
            self[k] = []

    def __repr__(self):
        msg = [r'%s : %s' % (k, i) for k, i in self.items() if len(i) > 0]
        return '\n'.join(msg)

class BuildConfigFactory:
    """This class can return cutomized BuildConfig instances according to some
    options.

    For example, you would create a BuildConfigFactory with a MKL BuildConfig
    instance, and the factory would return customized BuildConfig for blas,
    lapack, 64 vs 32 bits, etc..."""
    def __init__(self, bld_opts):
        self._data = bld_opts

        self._bld = BuildConfig()
        self._update_bld()

        self._cfgs = {
            'fft':      self.fft_config,
            'blas':     self.blas_config,
            'lapack':   self.lapack_config,
            'cblas':    self.cblas_config,
            'clapack':  self.clapack_config}

    def _update_bld(self):
        """Update _bld info. Necessary whenever _data is modified."""
        for k in self._bld:
            self._bld[k] = self._data[k]

    def _get_libraries(self, supp):
        res = copy(self._bld)
        tmp = copy(res['libraries'])
        res['libraries'] = []
        for i in supp:
            res['libraries'] += self._data[i]
        res['libraries'] += tmp
        return res

    #--------------------------------------------------------------------
    # Functions to get a special configuration (for blas, lapack, etc...)
    #--------------------------------------------------------------------
    def core_config(self):
        return self._bld

    def blas_config(self):
        return self._get_libraries(['blas_libs'])

    def cblas_config(self):
        return self._get_libraries(['cblas_libs'])

    def lapack_config(self):
        return self._get_libraries(['lapack_libs', 'cblas_libs', 'blas_libs'])

    def clapack_config(self):
        return self._get_libraries(['clapack_libs', 'cblas_libs'])

    def fft_config(self):
        return self._get_libraries(['fft_libs'])

    #----------------------------------------------------------------
    # Functions useful to merge informations from another BuildConfig
    #----------------------------------------------------------------
    def replace(self, cfg):
        """Given a dictionary cfg, replace all its value with the one of cfg,
        for every key in cfg.

        Similar to merge, but replace values instead of merging."""
        for k, v in cfg.items():
            self._data[k] = v
        self._update_bld()

    def merge(self, cfg, append = False):
        """Given a dictionary cfg, merge all its value with the one of cfg, for
        every key in cfg.

        Example: you have a BuildConfigFactory instance, and you want to modify
        some of its options from a BuildConfig instance (obtained from site.cfg
        customization)."""
        if append:
            for k, v in cfg.items():
                self._data[k] += v
        else:
            for k, v in cfg.items():
                self._data[k] = v + self._data[k]
        self._update_bld()

    def __repr__(self):
        return '\n\t'.join(['%s: %s' % (k, v)
                            for k, v in self._data.items() if len(v) > 0])

    def __getitem__(self, k):
        return self._cfgs[k]
