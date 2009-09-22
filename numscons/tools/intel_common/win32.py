import _winreg
import os

from SCons.Tool.MSCommon.common import get_output, debug, parse_output

_ROOT = {"amd64": r"Software\Wow6432Node\Intel\Suites",
         "ia32": r"Software\Intel\Compilers"}

_FC_ROOT = {"amd64": r"Software\Wow6432Node\Intel\Compilers",
         "ia32": r"Software\Intel\Compilers"}

def get_key(k):
    return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, k)

def list_keys(key):
    s = []
    try:
        i = 0
        while True:
            s.append(_winreg.EnumKey(key, i))
            i += 1
    except WindowsError:
        pass

    return s

def find_versions(abi):
    """Return the list of found versions of Intel C/C++ compiler for the given
    ABI."""
    try:
        root = _ROOT[abi]
    except KeyError:
        # Unsupported ABI
        raise NotImplementedError("Unsupported abi: %s" % str(abi))

    availables = []
    versions = list_keys(get_key(root))
    for v in versions:
        verk = os.path.join(root, v)
        bld = list_keys(get_key(verk))
        for b in bld:
            bldk = os.path.join(verk, b)
            try:
                get_key(os.path.join(bldk, "C++"))
                availables.append(tuple([int(i) for i in v.split(".") + [b]]))
            except WindowsError:
                pass

    return availables

def find_fc_versions(abi):
    """Return the dict of found versions of Intel Fortran compiler
    for the given ABI.

    Each key is a tuple (maj, min, rev) and each value is the key
    where to find the product dir"""
    try:
        root = _FC_ROOT[abi]
    except KeyError:
        # Unsupported ABI
        raise NotImplementedError("Unsupported abi: %s" % str(abi))

    root = os.path.join(root, "Fortran")
    availables = {}
    versions = list_keys(get_key(root))
    for v in versions:
        verk = os.path.join(root, v)
        min = _winreg.QueryValueEx(get_key(verk), "Major Version")[0]
        maj = _winreg.QueryValueEx(get_key(verk), "Minor Version")[0]
        bld = _winreg.QueryValueEx(get_key(verk), "Revision")[0]
	availables[(min, maj, bld)] = verk

    return availables

def product_dir_fc(root):
    k = get_key(root)
    return _winreg.QueryValueEx(k, "ProductDir")[0]

def product_dir(abi, version):
    try:
        root = _ROOT[abi]
    except KeyError:
        # Unsupported ABI
        raise NotImplementedError("Unsupported abi: %s" % str(abi))

    k = get_key(os.path.join(root, "%d.%d" % (version[0], version[1]),
                             "0%d" % version[2], "C++"))
    return _winreg.QueryValueEx(k, "ProductDir")[0]

def generate(env):
    SCons.Tool.msvc.generate(env)

    # YOYOYOY
    batfile = r"C:\Program Files (x86)\Intel\Compiler\11.1\038\bin\iclvars.bat"
    out = get_output(batfile, args=_ABI2INTEL[abi])
    d = parse_output(out)
    for k, v in d.items():
	env.PrependENVPath(k, v, delete_existing=True)

    #static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    #for suffix in CSuffixes:
    #    static_obj.add_action(suffix, SCons.Defaults.CAction)
    #    shared_obj.add_action(suffix, SCons.Defaults.ShCAction)
    #    static_obj.add_emitter(suffix, SCons.Defaults.StaticObjectEmitter)
    #    shared_obj.add_emitter(suffix, SCons.Defaults.SharedObjectEmitter)
    env["CC"] = "icl"
    env["CFLAGS"] = SCons.Util.CLVar("/nologo")
    env["SHCC"] = "$CC"

