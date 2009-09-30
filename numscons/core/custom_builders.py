import copy
from os.path import join as pjoin, dirname as pdirname

def DistutilsSharedLibrary(env, *args, **kw):
    """This builder is the same as SharedLibrary, except for the fact that
    it put the target into where distutils expects it."""
    lib = env.SharedLibrary(*args, **kw)
    inst_lib = env.Install("$distutils_installdir", lib)
    return lib, inst_lib

def DistutilsPythonExtension(env, *args, **kw):
    """this builder is the same than pythonextension, except for the fact that
    it put the target into where distutils expects it."""
    lib = env.PythonExtension(*args, **kw)
    inst_lib = env.Install("$distutils_installdir", lib)
    return lib, inst_lib

def NumpyPythonExtension(env, *args, **kw):
    """this builder is the same than pythonextension, except for the fact that
    it put the target into where distutils expects it."""
    if kw.has_key('NUMPYCPPPATH'):
        npy_cpppath = kw['NUMPYCPPPATH']
    else:
        npy_cpppath = env['NUMPYCPPPATH']

    if kw.has_key('PYEXTCPPPATH'):
        py_cpppath = kw['PYEXTCPPPATH']
    else:
        py_cpppath = env['PYEXTCPPPATH']

    oldval = copy.copy(py_cpppath)
    try:
        kw['PYEXTCPPPATH'] = npy_cpppath + py_cpppath
        lib = env.PythonExtension(*args, **kw)
    finally:
        kw['PYEXTCPPPATH'] = oldval

    # XXX: hack so that if the install builder source contains a directory, the
    # directory is aknowledged, e.g. installing 'bin/foo' into 'bar' should
    # give 'bar/bin/foo', whereas Install('bar', 'bin/foo') install 'foo' into
    # 'bar'
    inst_lib = []
    for t in lib:
        d = pdirname(str(t))
        if d:
            install_dir = pjoin(env.subst('$distutils_installdir'), d)
        else:
            install_dir = env.subst('$distutils_installdir')
        inst_lib.extend(env.Install(install_dir, t))
    return lib, inst_lib

def DistutilsStaticExtLibrary(env, *args, **kw):
    """This builder is the same as StaticExtLibrary, except for the fact that
    it put the target into where numpy.distutils expects it."""
    lib = env.StaticExtLibrary(*args, **kw)
    inst_lib = env.Install("$distutils_clibdir", lib)
    return lib, inst_lib

def DistutilsInstalledStaticExtLibrary(env, *args, **kw):
    """This builder is the same as StaticExtLibrary, except for the fact that
    it put the target into where numpy.distutils expects it."""
    try:
        install_dir = kw['install_dir']
        del kw['install_dir']
    except KeyError:
        install_dir = '.'

    lib = env.StaticExtLibrary(*args, **kw)
    inst_lib = env.Install(pjoin("$distutils_clibdir"), lib)
    inst_lib.extend(
        env.Install(pjoin("$distutils_installdir", install_dir),
        lib))
    return lib, inst_lib

def NumpyCtypes(env, target, source, *args, **kw):
    """This builder is essentially the same than SharedLibrary, but should be
    used for libraries which will only be used through ctypes.

    In particular, it does not install .exp/.lib files on windows. """
    # XXX: why target is a list ? It is always true ?
    # XXX: handle cases where SHLIBPREFIX is in args
    lib = env.SharedLibrary(target,
                            source,
                            SHLIBPREFIX = '',
                            *args,
                            **kw)
    lib = [i for i in lib if not (str(i).endswith('.exp')
                             or str(i).endswith('.lib')) ]
    inst_lib = env.Install("$distutils_installdir", lib)
    return lib, inst_lib
