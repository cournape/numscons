import os

def set_cblas(config, config_info):
    if config_info['cblas_libraries']:
        config._interfaces['CBLAS']['LIBS']  = config_info['cblas_libraries']
    elif config_info['blas_libraries']:
        config._interfaces['CBLAS']['LIBS']  = config_info['blas_libraries']
    elif config_info['libraries']:
        config._interfaces['CBLAS']['LIBS']  = config_info['libraries']

    _set_common(config._interfaces['CBLAS'], config_info)

def set_blas(config, config_info):
    if config_info['blas_libraries']:
        config._interfaces['BLAS']['LIBS']  = config_info['blas_libraries']
    elif config_info['libraries']:
        config._interfaces['BLAS']['LIBS']  = config_info['libraries']

    _set_common(config._interfaces['BLAS'], config_info)

def set_lapack(config, config_info):
    if config_info['lapack_libraries']:
        config._interfaces['LAPACK']['LIBS']  = config_info['lapack_libraries']
    elif config_info['libraries']:
        config._interfaces['LAPACK']['LIBS']  = config_info['libraries']

    _set_common(config._interfaces['LAPACK'], config_info)

def set_core(config, config_info):
    if config_info['libraries']:
        config._core['LIBS']  = config_info['libraries']
    _set_common(config._core, config_info)

def _set_common(build_info, config_info):
    if config_info['cflags']:
        build_info['CFLAGS']  = config_info['cflags']

    if config_info['ldflags']:
        build_info['LINKFLAGS']  = config_info['ldflags']

    if config_info['include_dirs']:
        build_info['CPPPATH']  = config_info['include_dirs']

    if config_info['library_dirs']:
        build_info['LIBPATH']  = config_info['library_dirs']

    if config_info['frameworks']:
        build_info['FRAMEWORKS']  = config_info['frameworks']

class _Config:
    def __init__(self, config_info):
        self._config_info = config_info

    def interfaces(self):
        return self._interfaces.keys()

    def disabled(self):
        try:
            val = os.environ[self.name]
            return val == 'None'
        except KeyError:
            return False

    def __str__(self):
        msg = ['Uses perflib %s' % self.name]
        msg.extend(["\t%s: %s" % (k, v) for k, v in self._config_info.items()])
        return "\n".join(msg)

class AtlasConfig(_Config):
    def __init__(self, config_info):
        _Config.__init__(self, config_info)

        self.name = 'ATLAS'
        self._core = {}
        self._interfaces = {'BLAS': {}, 'LAPACK': {}, 'CBLAS': {}}

        set_blas(self, config_info)
        set_cblas(self, config_info)
        set_lapack(self, config_info)
        set_core(self, config_info)

        self.test_code = """
void ATL_buildinfo();

int
main()
{
    ATL_buildinfo();
}
"""

class MklConfig(_Config):
    def __init__(self, config_info):
        _Config.__init__(self, config_info)

        self.name = 'MKL'
        self._core = {}
        self._interfaces = {'BLAS': {}, 'LAPACK': {}, 'CBLAS': {}}

        set_blas(self, config_info)
        set_cblas(self, config_info)
        set_lapack(self, config_info)
        set_core(self, config_info)

        self.test_code = """
#include <mkl.h>

int
main ()
{
    MKLVersion v;
    MKLGetVersion(&v);
};
        """

class AccelerateConfig(_Config):
    def __init__(self, config_info):
        _Config.__init__(self, config_info)

        self.name = 'ACCELERATE'
        self._core = {}
        self._interfaces = {'BLAS': {}, 'LAPACK': {}, 'CBLAS': {}}

        set_blas(self, config_info)
        set_cblas(self, config_info)
        set_lapack(self, config_info)
        set_core(self, config_info)

        self.test_code = """
#include <Accelerate/Accelerate.h>

int
main ()
{
};
        """

# Generic* config objects are used as last resort when no optimized performance
# library is found. Those may also be used for not yet supported optimized
# library, by setting manually every field.
class GenericBlasConfig(_Config):
    def __init__(self, config_info):
        _Config.__init__(self, config_info)

        self.name = 'GenericBlas'
        self._core = {}
        self._interfaces = {'BLAS': {}}

        set_blas(self, config_info)

        self.test_code = "int main(void) {}"

class GenericLapackConfig(_Config):
    def __init__(self, config_info):
        _Config.__init__(self, config_info)

        self.name = 'GenericLapack'
        self._core = {}
        self._interfaces = {'BLAS': {}, 'LAPACK': {}}

        set_blas(self, config_info)
        set_lapack(self, config_info)

        self.test_code = "int main(void) {}"
