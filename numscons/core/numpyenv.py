# This module cannot be imported directly, because it needs scons module.
from os.path import join as pjoin

from SCons.Environment import Environment

from numscons.core.misc import get_numscons_toolpaths
from numscons.core.errors import NumsconsError
from numscons.core.utils import pkg_to_path

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
        self.AppendUnique(build_dir = pjoin(self['build_prefix'],
                                           self['src_dir']))
        self.AppendUnique(distutils_installdir =
                          pjoin(self['distutils_libdir'],
                                pkg_to_path(self['pkg_name'])))

        # This will keep our compiler dependent customization (optimization,
        # warning, etc...)
        self['NUMPY_CUSTOMIZATION'] = {}

    def Configure(self, *args, **kw):
        if kw.has_key('conf_dir') or kw.has_key('log_file'):
            # XXX handle this gracefully
            assert 0 == 1
        else:
            kw['conf_dir'] = 'sconf'
            kw['log_file'] = 'config.log'
        return Environment.Configure(self, *args, **kw)

    def Tool(self, toolname, path = None):
        """Like SCons.Tool, but knows about numscons specific toolpaths."""
        if path:
            return Environment.Tool(self, toolname,
                    path + get_numscons_toolpaths(self))
        else:
            return Environment.Tool(self, toolname, get_numscons_toolpaths(self))

    def DistutilsSConscript(self, name):
        """This sets up build directory correctly to play nice with
        distutils."""
        if self['src_dir']:
            sname = pjoin('$src_dir', name)
        else:
            sname = name
        Environment.SConscript(self, sname,
                               build_dir = '$build_dir', src_dir = '$src_dir')
