"""SCons.Tool.dlltool

Tool-specific initialization for dlltool.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.

"""

#
# Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007 The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "src/engine/SCons/Tool/ifort.py 2446 2007/09/18 11:41:57 knight"

import string

import SCons.Defaults
import SCons.Node

def dlltoolEmitter(target, source, env):
    rtarget = []
    dllname = env.FindIxes(target, "SHLIBPREFIX", "SHLIBSUFFIX")

    if not dllname:
        raise SCons.Errors.UserError, \
	      "A shared library should have exactly one target with the "\
	      "suffix: %s" % env.subst("$SHLIBSUFFIX")
    
    defname = env.ReplaceIxes(dllname, "SHLIBPREFIX", "SHLIBSUFFIX",
		    "WINDOWSDEFPREFIX", "WINDOWSDEFSUFFIX")
    libname = env.ReplaceIxes(dllname, "SHLIBPREFIX", "SHLIBSUFFIX",
		    "LIBPREFIX", "LIBSUFFIX")
    expname = env.ReplaceIxes(dllname, "SHLIBPREFIX", "SHLIBSUFFIX",
		    "WINDOWSEXPPREFIX", "WINDOWSEXPSUFFIX")

    for i in (defname, libname, expname):
	rtarget.append(SCons.Node.FS.default_fs.Entry(i))
    return (rtarget, source)


def generate(env):
    """Add Builders and construction variables for dlltool."""
    # dlltool cwcan generate .def and .lib from static archive or object files
    env['DLLTOOL'] 	= 'dlltool'
    env['DLLTOOLFLAGS'] = SCons.Util.CLVar('')
    env['_DLLTOOLLINKFLAGS'] = SCons.Util.CLVar('')
    env['_DLLTOOLLIBS'] = SCons.Util.CLVar('')
    env['DLLTOOLCOM'] 	= '$DLLTOOL -o $TARGET $DLLTOOLFLAGS $SOURCES ' \
    			  '$_DLLTOOLLIBS $_DLLTOOLLINKFLAGS'
    env["DLLTOOLEMITTER"] = dlltoolEmitter

def exists(env):
    return env.Detect('dlltool')
