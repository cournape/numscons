import copy

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

    inst_lib = env.Install("$distutils_installdir", lib)
    return lib, inst_lib

def DistutilsStaticExtLibrary(env, *args, **kw):
    """This builder is the same as StaticExtLibrary, except for the fact that
    it put the target into where distutils expects it."""
    lib = env.StaticExtLibrary(*args, **kw)
    inst_lib = env.Install("$distutils_installdir", lib)
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
