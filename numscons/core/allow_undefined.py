"""This module handle platform specific link options to allow undefined symbols
in shared libraries and dynamically loaded libraries."""
import os
from subprocess import Popen, PIPE

def get_darwin_version():
    p = Popen(["sw_vers", "-productVersion"], stdout = PIPE, stderr = PIPE)
    st = p.wait()
    if st:
        raise RuntimeError(
                "Could not execute sw_vers -productVersion to get version")

    verstring = p.stdout.next()
    a, b, c = verstring.split(".")
    try:
        major = int(a)
        minor = int(b)
        micro = int(c)

        return major, minor, micro
    except ValueError:
        raise ValueError("Could not parse version string %s" % verstring)

def get_darwin_allow_undefined():
    """Return the list of flags to allow undefined symbols in a shared library.

    On MAC OS X, takes MACOSX_DEPLOYMENT_TARGET into account."""
    major, minor, micro = get_darwin_version()
    if major == 10:
        if minor < 3:
            flag = ["-Wl,-undefined", "-Wl,suppress"]
        else:
            try:
                deptarget = os.environ['MACOSX_DEPLOYMENT_TARGET']
                ma, mi = deptarget.split(".")
                if mi < 3:
                    flag = ['-Wl,-flat_namespace', '-Wl,-undefined', 
			    '-Wl,suppress']
                else:
                    flag = ['-Wl,-undefined', '-Wl,dynamic_lookup']
            except KeyError:
                flag = ['-Wl,-flat_namespace', '-Wl,-undefined', '-Wl,suppress']
    else:
        # Non existing mac os x ? Just set to empty list
        flag = []

    return flag
