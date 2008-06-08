#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J

"""Module which implements version checkers for perflib."""

import re

from numscons.checkers.support import save_and_set, restore

def mkl_version_checker(context, opts):
    env = context.env
    version_code = r"""
#include <stdio.h>
#include <mkl.h>

int main(void)
{
MKLVersion ver;
MKLGetVersion(&ver);

printf("Full version: %d.%d.%d\n", ver.MajorVersion,
       ver.MinorVersion,
       ver.BuildNumber);

return 0;
}
"""

    opts['rpath'] = opts['library_dirs']
    saved = save_and_set(env, opts)
    try:
        vst, out = context.TryRun(version_code, '.c')
    finally:
        restore(env, saved)

    if vst:
        m = re.search(r'Full version: (\d+[.]\d+[.]\d+)', out)
        if m:
            version = m.group(1)
    else:
        version = ''

    return vst, version

def atlas_version_checker(context, opts):
    env = context.env
    version_code = """
void ATL_buildinfo(void);
int main(void) {
ATL_buildinfo();
return 0;
}
"""
    opts['rpath'] = opts['library_dirs']
    saved = save_and_set(env, opts)
    try:
        vst, out = context.TryRun(version_code, '.c')
    finally:
        restore(env, saved)

    if vst:
        m = re.search('ATLAS version (?P<version>\d+[.]\d+[.]\d+)', out)
        if m:
            version = m.group(1)
        else:
            version = ''
    else:
        version = ''

    return vst, version
