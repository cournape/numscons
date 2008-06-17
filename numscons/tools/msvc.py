"""Tool-specific initialization for Microsoft Visual C/C++.

This version is customized for numscons: it uses vcvarsall.bat instead of the
registry, to be simpler and more reliable.
"""

import os.path
import re
import string
import subprocess

import _winreg

import SCons.Action
import SCons.Builder
import SCons.Errors
import SCons.Platform.win32
import SCons.Tool
import SCons.Tool.msvs
import SCons.Util
import SCons.Warnings

CSuffixes = ['.c', '.C']
CXXSuffixes = ['.cc', '.cpp', '.cxx', '.c++', '.C++']

RegOpenKeyEx = _winreg.OpenKeyEx
RegEnumKey = _winreg.EnumKey
RegEnumValue = _winreg.EnumValue
RegError = _winreg.error

HKEYS = (_winreg.HKEY_USERS,
         _winreg.HKEY_CURRENT_USER,
         _winreg.HKEY_LOCAL_MACHINE,
         _winreg.HKEY_CLASSES_ROOT)

VS_BASE = r"Software\Microsoft\VisualStudio\%0.1f"
WINSDK_BASE = r"Software\Microsoft\Microsoft SDKs\Windows"
NET_BASE = r"Software\Microsoft\.NETFramework"

# A map keyed by get_platform() return values to values accepted by
# 'vcvarsall.bat'.  Note a cross-compile may combine these (eg, 'x86_amd64' is
# the param to cross-compile on x86 targetting amd64.)
PLAT_TO_VCVARS = {
    'win32' : 'x86',
    'win-amd64' : 'amd64',
    'win-ia64' : 'ia64',
}

class Reg:
    """Helper class to read values from the registry
    """

    @classmethod
    def get_value(cls, path, key):
        for base in HKEYS:
            d = cls.read_values(base, path)
            if d and key in d:
                return d[key]
        raise KeyError(key)

    @classmethod
    def read_keys(cls, base, key):
        """Return list of registry keys."""
        try:
            handle = RegOpenKeyEx(base, key)
        except RegError:
            return None
        L = []
        i = 0
        while True:
            try:
                k = RegEnumKey(handle, i)
            except RegError:
                break
            L.append(k)
            i += 1
        return L

    @classmethod
    def read_values(cls, base, key):
        """Return dict of registry keys and values.

        All names are converted to lowercase.
        """
        try:
            handle = RegOpenKeyEx(base, key)
        except RegError:
            return None
        d = {}
        i = 0
        while True:
            try:
                name, value, type = RegEnumValue(handle, i)
            except RegError:
                break
            name = name.lower()
            d[cls.convert_mbcs(name)] = cls.convert_mbcs(value)
            i += 1
        return d

    @staticmethod
    def convert_mbcs(s):
        dec = getattr(s, "decode", None)
        if dec is not None:
            try:
                s = dec("mbcs")
            except UnicodeError:
                pass
        return s

def find_vcvarsall(version):
    """Find the vcvarsall.bat file

    At first it tries to find the productdir of VS 2008 in the registry. If
    that fails it falls back to the VS90COMNTOOLS env var.
    """
    vsbase = VS_BASE % version
    try:
        productdir = Reg.get_value(r"%s\Setup\VC" % vsbase,
                                   "productdir")
    except KeyError:
        productdir = None

    if not productdir or not os.path.isdir(productdir):
        toolskey = "VS%0.f0COMNTOOLS" % version
        toolsdir = os.environ.get(toolskey, None)

        if toolsdir and os.path.isdir(toolsdir):
            productdir = os.path.join(toolsdir, os.pardir, os.pardir, "VC")
            productdir = os.path.abspath(productdir)
            if not os.path.isdir(productdir):
                return None

    if not productdir:
        return None

    vcvarsall = os.path.join(productdir, "vcvarsall.bat")
    if os.path.isfile(vcvarsall):
        return vcvarsall
    return None

def query_vcvarsall(version, arch="x86"):
    """Launch vcvarsall.bat and read the settings from its environment
    """
    vcvarsall = find_vcvarsall(version)
    interesting = set(("include", "lib", "libpath", "path"))
    result = {}

    if vcvarsall is None:
        raise IOError("Unable to find vcvarsall.bat")
    popen = subprocess.Popen('"%s" %s & set' % (vcvarsall, arch),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

    stdout, stderr = popen.communicate()
    if popen.wait() != 0:
        raise IOError(stderr.decode("mbcs"))

    stdout = stdout.decode("mbcs")
    for line in stdout.split("\n"):
        line = Reg.convert_mbcs(line)
        if '=' not in line:
            continue
        line = line.strip()
        key, value = line.split('=')
        key = key.lower()
        if key in interesting:
            if value.endswith(os.pathsep):
                value = value[:-1]
            result[key] = value

    if len(result) != len(interesting):
        raise ValueError("Error while parsing vcvarsall.bat settings")

    return result

def validate_vars(env):
    """Validate the PCH and PCHSTOP construction variables."""
    if env.has_key('PCH') and env['PCH']:
        if not env.has_key('PCHSTOP'):
            raise SCons.Errors.UserError, "The PCHSTOP construction must be defined if PCH is defined."
        if not SCons.Util.is_String(env['PCHSTOP']):
            raise SCons.Errors.UserError, "The PCHSTOP construction variable must be a string: %r"%env['PCHSTOP']

def pch_emitter(target, source, env):
    """Adds the object file target."""

    validate_vars(env)

    pch = None
    obj = None

    for t in target:
        if SCons.Util.splitext(str(t))[1] == '.pch':
            pch = t
        if SCons.Util.splitext(str(t))[1] == '.obj':
            obj = t

    if not obj:
        obj = SCons.Util.splitext(str(pch))[0]+'.obj'

    target = [pch, obj] # pch must be first, and obj second for the PCHCOM to work

    return (target, source)

def object_emitter(target, source, env, parent_emitter):
    """Sets up the PCH dependencies for an object file."""

    validate_vars(env)

    parent_emitter(target, source, env)

    if env.has_key('PCH') and env['PCH']:
        env.Depends(target, env['PCH'])

    return (target, source)

def static_object_emitter(target, source, env):
    return object_emitter(target, source, env,
                          SCons.Defaults.StaticObjectEmitter)

def shared_object_emitter(target, source, env):
    return object_emitter(target, source, env,
                          SCons.Defaults.SharedObjectEmitter)

pch_action = SCons.Action.Action('$PCHCOM', '$PCHCOMSTR')
pch_builder = SCons.Builder.Builder(action=pch_action, suffix='.pch',
                                    emitter=pch_emitter,
                                    source_scanner=SCons.Tool.SourceFileScanner)
res_action = SCons.Action.Action('$RCCOM', '$RCCOMSTR')
res_builder = SCons.Builder.Builder(action=res_action,
                                    src_suffix='.rc',
                                    suffix='.res',
                                    src_builder=[],
                                    source_scanner=SCons.Tool.SourceFileScanner)
SCons.Tool.SourceFileScanner.add_scanner('.rc', SCons.Defaults.CScan)

def generate(env):
    """Add Builders and construction variables for MSVC++ to an Environment."""
    static_obj, shared_obj = SCons.Tool.createObjBuilders(env)

    for suffix in CSuffixes:
        static_obj.add_action(suffix, SCons.Defaults.CAction)
        shared_obj.add_action(suffix, SCons.Defaults.ShCAction)
        static_obj.add_emitter(suffix, static_object_emitter)
        shared_obj.add_emitter(suffix, shared_object_emitter)

    for suffix in CXXSuffixes:
        static_obj.add_action(suffix, SCons.Defaults.CXXAction)
        shared_obj.add_action(suffix, SCons.Defaults.ShCXXAction)
        static_obj.add_emitter(suffix, static_object_emitter)
        shared_obj.add_emitter(suffix, shared_object_emitter)

    env['CCPDBFLAGS'] = SCons.Util.CLVar(['${(PDB and "/Z7") or ""}'])
    env['CCPCHFLAGS'] = SCons.Util.CLVar(['${(PCH and "/Yu%s /Fp%s"%(PCHSTOP or "",File(PCH))) or ""}'])
    #env['CCCOMFLAGS'] = '$CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS /c $SOURCES /Fo$TARGET $CCPCHFLAGS $CCPDBFLAGS'
    env['_CCCOMCOM']  = '$CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS $CCPCHFLAGS $CCPDBFLAGS'
    env['CC']         = 'cl'
    env['CCFLAGS']    = SCons.Util.CLVar('/nologo')
    env['CFLAGS']     = SCons.Util.CLVar('')
    env['CCCOM']      = '$CC /Fo$TARGET /c $SOURCES $CFLAGS $CCFLAGS $_CCCOMCOM'
    env['SHCC']       = '$CC'
    env['SHCCFLAGS']  = SCons.Util.CLVar('$CCFLAGS')
    env['SHCFLAGS']   = SCons.Util.CLVar('$CFLAGS')
    env['SHCCCOM']    = '$SHCC /Fo$TARGET /c $SOURCES $SHCFLAGS $SHCCFLAGS $_CCCOMCOM'
    env['CXX']        = '$CC'
    env['CXXFLAGS']   = SCons.Util.CLVar('$CCFLAGS $( /TP $)')
    env['CXXCOM']     = '$CXX /Fo:$TARGET /c $SOURCES $CXXFLAGS $CCFLAGS $_CCCOMCOM'
    env['SHCXX']      = '$CXX'
    env['SHCXXFLAGS'] = SCons.Util.CLVar('$CXXFLAGS')
    env['SHCXXCOM']   = '$SHCXX /Fo:$TARGET /c $SOURCES $SHCXXFLAGS $SHCCFLAGS $_CCCOMCOM'
    env['CPPDEFPREFIX']  = '/D'
    env['CPPDEFSUFFIX']  = ''
    env['INCPREFIX']  = '/I'
    env['INCSUFFIX']  = ''
#    env.Append(OBJEMITTER = [static_object_emitter])
#    env.Append(SHOBJEMITTER = [shared_object_emitter])
    env['STATIC_AND_SHARED_OBJECTS_ARE_THE_SAME'] = 1

    env['RC'] = 'rc'
    env['RCFLAGS'] = SCons.Util.CLVar('')
    env['RCCOM'] = '$RC $_CPPDEFFLAGS $_CPPINCFLAGS $RCFLAGS /fo$TARGET $SOURCES'
    env['BUILDERS']['RES'] = res_builder
    env['OBJPREFIX']      = ''
    env['OBJSUFFIX']      = '.obj'
    env['SHOBJPREFIX']    = '$OBJPREFIX'
    env['SHOBJSUFFIX']    = '$OBJSUFFIX'

    try:
        # XXX: handle VS version correctly
        version = 9.0
        res = query_vcvarsall(version)

        env.PrependENVPath('INCLUDE', res['include'])
        env.PrependENVPath('LIBPATH', res['libpath'])
        env.PrependENVPath('LIB', res['lib'])
        env.PrependENVPath('PATH', res['path'])
    except (SCons.Util.RegError, SCons.Errors.InternalError):
        pass

    env['CFILESUFFIX'] = '.c'
    env['CXXFILESUFFIX'] = '.cc'

    env['PCHPDBFLAGS'] = SCons.Util.CLVar(['${(PDB and "/Yd") or ""}'])
    env['PCHCOM'] = '$CXX $CXXFLAGS $CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS /c $SOURCES /Fo${TARGETS[1]} /Yc$PCHSTOP /Fp${TARGETS[0]} $CCPDBFLAGS $PCHPDBFLAGS'
    env['BUILDERS']['PCH'] = pch_builder

    if not env.has_key('ENV'):
        env['ENV'] = {}
    if not env['ENV'].has_key('SystemRoot'):    # required for dlls in the winsxs folders
        env['ENV']['SystemRoot'] = SCons.Platform.win32.get_system_root()

def exists(env):
    return env.Detect('cl')

