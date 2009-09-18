import os
import subprocess
import re

import _winreg

import SCons
import SCons.Tool.msvc

from SCons.Tool.cc import CSuffixes

_ROOT = {"amd64": r"Software\Wow6432Node\Intel\Suites"}

_ABI2INTEL = {"amd64": "intel64"}

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

def product_dir(abi, version):
    try:
        root = _ROOT[abi]
    except KeyError:
        # Unsupported ABI
        raise NotImplementedError("Unsupported abi: %s" % str(abi))

    k = get_key(os.path.join(root, "%d.%d" % (version[0], version[1]),
                             "0%d" % version[2], "C++"))
    return _winreg.QueryValueEx(k, "ProductDir")[0]

# Both get_output and parse_output are taken from scons
# vs_revamp branch - when our own scons copy will be updated,
# use scons instead of those copies here
logfile = os.environ.get('SCONS_MSCOMMON_DEBUG')
if logfile == '-':
    def debug(x):
        print x
elif logfile:
    try:
        import logging
    except ImportError:
        debug = lambda x: open(logfile, 'a').write(x + '\n')
    else:
        logging.basicConfig(filename=logfile, level=logging.DEBUG)
        debug = logging.debug
else:
    debug = lambda x: None


def get_output(vcbat, args = None, env = None):
    """Parse the output of given bat file, with given args."""
    if args:
        debug("Calling '%s %s'" % (vcbat, args))
        popen = subprocess.Popen('"%s" %s & set' % (vcbat, args),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)
    else:
        debug("Calling '%s'" % vcbat)
        popen = Popen('"%s" & set' % vcbat,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=env)

    # Use the .stdout and .stderr attributes directly because the
    # .communicate() method uses the threading module on Windows
    # and won't work under Pythons not built with threading.
    stdout = popen.stdout.read()
    if popen.wait() != 0:
        raise IOError(popen.stderr.read().decode("mbcs"))

    output = stdout.decode("mbcs")
    return output

def parse_output(output, keep = ("INCLUDE", "LIB", "LIBPATH", "PATH")):
    # dkeep is a dict associating key: path_list, where key is one item from
    # keep, and pat_list the associated list of paths

    # TODO(1.5):  replace with the following list comprehension:
    #dkeep = dict([(i, []) for i in keep])
    dkeep = dict(map(lambda i: (i, []), keep))

    # rdk will  keep the regex to match the .bat file output line starts
    rdk = {}
    for i in keep:
        rdk[i] = re.compile('%s=(.*)' % i, re.I)

    def add_env(rmatch, key, dkeep=dkeep):
        plist = rmatch.group(1).split(os.pathsep)
        for p in plist:
            # Do not add empty paths (when a var ends with ;)
            if p:
                p = p.encode('mbcs')
                # XXX: For some reason, VC98 .bat file adds "" around the PATH
                # values, and it screws up the environment later, so we strip
                # it. 
                p = p.strip('"')
                dkeep[key].append(p)

    for line in output.splitlines():
        for k,v in rdk.items():
            m = v.match(line)
            if m:
                add_env(m, k)

    return dkeep
# end of copied code from scons trunk (upcoming 1.3.0)


def generate(env):
    try:
        abi = env["INTEL_ABI"]
    except KeyError:
        abi = "x86"

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

def exists(env):
    return 1
