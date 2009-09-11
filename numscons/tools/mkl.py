from os.path import join as pjoin, exists as pexists, split as psplit
import _winreg

import SCons.Util

_ARCHS = {
        'amd64': 'EM64T',
        'x86': 'ia32',
        'EM64T': 'EM64T',
}

class StalledEntry(WindowsError):
    pass

class UnavailableArch(RuntimeError):
    pass

# Basic utilities
def read_value(key):
    """Return the value of the key."""
    return SCons.Util.RegGetValue(SCons.Util.HKEY_LOCAL_MACHINE, key)[0]

def has_key(key):
    """Return true if the key exists."""
    try:
        k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)
        _winreg.CloseKey(k)
        return True
    except WindowsError, e:
        return False

def list_subkeys(key):
    """List all subkeys of the given key.

    """
    k = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key)
    try:
        subs = []
        try:
            i = 0
            while True:
                sk = _winreg.EnumKey(k, i)
                subs.append(sk)
                i += 1
        except WindowsError:
            pass

        return subs
    finally:
        _winreg.CloseKey(k)

def mkl_config(root_path, arch, suite=False):
    arch_str = _ARCHS[arch]
    config = {}
    top_dir = pjoin(root_path, arch_str)
    if not pexists(top_dir):
        raise UnavailableArch("arch %s for mkl in %s not available" % (arch, top_dir))

    # Only useful for suite case
    suite_dir = psplit(root_path)[0]

    libdir = [pjoin(top_dir, "lib")]
    if not pexists(libdir[0]):
        raise RuntimeError("no lib dir in %s" % top_dir)
    if suite:
        d = pjoin(suite_dir, 'lib', arch_str)
        if not pexists(d):
            raise UnavailableArch("arch %s for mkl in %s not available" % (arch, d))
        libdir.append(d)

    config['import_dirs'] = libdir

    dlldir = pjoin(top_dir, "bin")
    if not pexists(dlldir):
        raise RuntimeError("no bin dir in %s" % top_dir)
    config['dll_dirs'] = [pjoin(top_dir, 'bin')]

    incdir = pjoin(root_path, "include")
    if not pexists(incdir):
        raise RuntimeError("no include dir %s" % incdir)
    config['include_dirs'] = [incdir]

    return config

# Work only for MKL as a product
def query_product_mkl():
    """query available MKL versions.

    Return a dictionary version: install-path."""
    prod_versions = {}
    root = pjoin(r"Software\Intel Corporation")
    if has_key(root):
        mklk = pjoin(root, "MKL")
        if has_key(mklk):
            vers = list_subkeys(mklk)
            for v in vers:
                fullk = pjoin(mklk, v)
                uuid = list_subkeys(fullk)
                fullk = pjoin(fullk, uuid[0], "InstallDir")
                prod_versions[v] = read_value(fullk)
                
    return prod_versions

def _get_version(top, version, build):
    mklk = pjoin(top, version, build, "MKL")
    if has_key(mklk):
        maj = read_value(pjoin(mklk, "Major Version"))
        min = read_value(pjoin(mklk, "Minor Version"))
        pdir = read_value(pjoin(mklk, "ProductDir"))
        return "%s.%s" % (maj, min), pdir
    else:
        raise StalledEntry("entry %s not found" % mklk)

def query_suites_mkl():
    suites_versions = {}
    suitesk =  r"Software\Intel\Suites"
    if has_key(suitesk):
        vers = list_subkeys(suitesk)
        for v in vers:
            blds = list_subkeys(pjoin(suitesk, v))
            for b in blds:
                try:
                    v, pdir = _get_version(suitesk, v, b)
                    suites_versions[v] = pdir
                except StalledEntry:
                    pass

    return suites_versions

env = DefaultEnvironment(tools=['msvs', 'mslib', 'mslink', 'msvc'])

versions1 = query_product_mkl()
versions2 = query_suites_mkl()
for root in versions1.values():
    for arch in ['x86', 'amd64']:
        try:
            print mkl_config(root, arch)
        except UnavailableArch, e:
            print "+++ ", e

for root in versions2.values():
    for arch in ['x86', 'amd64']:
        try:
            print mkl_config(root, arch, suite=True)
        except UnavailableArch, e:
            print "+++ ", e

config = mkl_config(versions2.values()[0], "x86", suite=True)
env.Prepend(LIBPATH=config["import_dirs"])
env.Prepend(CPPPATH=config["include_dirs"])
env.Program('hello.c', LIBS=["mkl_lapack95", "mkl_blas95", "mkl_intel_thread", "mkl_intel_c", "mkl_core", "libiomp5md"])
