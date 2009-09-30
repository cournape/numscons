# This module cannot be imported directly, because it needs scons module.
import os
from os.path import join as pjoin
import new

from SCons.Environment import Environment

from numscons.core.misc import get_numscons_toolpaths, get_last_error_from_config
from numscons.core.errors import NumsconsError
from numscons.core.utils import pkg_to_path
from numscons.core.trace import set_logging

class NumpyEnvironment(Environment):
    """An SCons Environment subclass which knows how to deal with distutils
    idiosyncraties."""
    def __init__(self, *args, **kw):
        if kw.has_key('tools'):
            raise NumsconsError("NumpyEnvironment has received a tools "\
                                "argument.")
        else:
            kw['tools'] = []

        Environment.__init__(self, *args, **kw)

        # Setting dirs according to command line options
        self['build_dir'] = pjoin(self['build_prefix'], pkg_to_path(self['pkg_name']))

        # Set directory where to "install" built C extensions
        if self["inplace"]:
            self['distutils_installdir'] = pjoin(str(self.fs.Top), self["pkg_path"])
        else:
            if not self.has_key('distutils_installdir'):
                # XXX: compatibility with upstream numpy trunk - this can be
                # removed once install_clib is merged
                self["distutils_installdir"] = ''
            self['distutils_installdir'] = pjoin(self['distutils_libdir'], pkg_to_path(self['pkg_name']))

        if not self.has_key('distutils_install_prefix'):
            # XXX: compatibility with upstream numpy trunk - this can be
            # removed once install_clib is merged
            self["distutils_install_prefix"] = ''
        else:
            self["distutils_install_prefix"] = os.path.abspath(pjoin(str(self.fs.Top), self["distutils_install_prefix"]))

        # This will keep our compiler dependent customization (optimization,
        # warning, etc...)
        self['NUMPY_CUSTOMIZATION'] = {}

        self._set_sconsign_location()
        self._customize_scons_env()
        set_logging(self)

    def _set_sconsign_location(self):
        """Put sconsign file in build dir. This is surprisingly difficult to do
        because of build_dir interactions."""

        # SConsign needs an absolute path or a path relative to where the
        # SConstruct file is. We have to find the path of the build dir
        # relative to the src_dir: we add n .., where n is the number of
        # occurances of the path separator in the src dir.
        def get_build_relative_src(srcdir, builddir):
            n = srcdir.count(os.sep)
            if len(srcdir) > 0 and not srcdir == '.':
                n += 1
            return pjoin(os.sep.join([os.pardir for i in range(n)]), builddir)

        sconsign = pjoin(get_build_relative_src(self['src_dir'],
                                                self['build_dir']),
                         'sconsign.dblite')
        self.SConsignFile(sconsign)

    def _customize_scons_env(self):
        """Customize scons environment from user environment."""
        self["ENV"]["PATH"] = os.environ["PATH"]

        # Add HOME in the environment: some tools seem to require it (Intel
        # compiler, for licenses stuff)
        if os.environ.has_key('HOME'):
            self['ENV']['HOME'] = os.environ['HOME']

        # XXX: Make up my mind about importing self or not at some point
        if os.environ.has_key('LD_LIBRARY_PATH'):
            self["ENV"]["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH"]

    def NumpyConfigure(self, *args, **kw):
        # Import here to avoid addint import times when configuration is not needed
        from numscons.checkers import CheckF77BLAS, CheckF77LAPACK
        from numscons.checkers.simple_check import NumpyCheckLibAndHeader
        from numscons.checkers.fortran import CheckF77Mangling

        if kw.has_key('conf_dir') or kw.has_key('log_file'):
            # XXX handle this gracefully
            assert 0 == 1
        else:
            kw['conf_dir'] = 'sconf'
            kw['log_file'] = 'config.log'

        if not kw.has_key("custom_tests"):
            kw["custom_tests"] = {}
        if not kw["custom_tests"].has_key("CheckF77Mangling"):
            kw["custom_tests"]["CheckF77Mangling"] = CheckF77Mangling
        if not kw["custom_tests"].has_key("CheckF77BLAS"):
            kw["custom_tests"]["CheckF77BLAS"] = CheckF77BLAS
        if not kw["custom_tests"].has_key("CheckF77LAPACK"):
            kw["custom_tests"]["CheckF77LAPACK"] = CheckF77LAPACK
        kw["custom_tests"]["NumpyCheckLibAndHeader"] = NumpyCheckLibAndHeader

        config = Environment.Configure(self, *args, **kw)

        def GetLastError(self):
            self.logstream.flush()
            errlines = open(str(self.logfile)).readlines()
            return get_last_error_from_config(errlines)

        config.GetLastError = new.instancemethod(GetLastError, config)
        return config

    def Tool(self, toolname, path = None):
        """Like SCons.Tool, but knows about numscons specific toolpaths."""
        if path:
            return Environment.Tool(self, toolname,
                    path + get_numscons_toolpaths(self))
        else:
            return Environment.Tool(self, toolname,
                                    get_numscons_toolpaths(self))

    def DistutilsSConscript(self, name):
        """This sets up build directory correctly to play nice with
        distutils."""
        if self['src_dir']:
            sname = pjoin('$src_dir', name)
        else:
            sname = name
        Environment.SConscript(self, sname,
                               build_dir = '$build_dir', src_dir = '$src_dir')
