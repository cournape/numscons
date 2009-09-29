#! /usr/bin/env python
# Last Change: Sun Jun 15 04:00 PM 2008 J

"""Module for support to look for external code (replacement of
numpy.distutils.system_info). scons dependant code."""
import os

from numscons.core.siteconfig import get_config_from_section, \
                                     get_paths, parse_config_param

from numscons.checkers.config import \
    BuildDict, _read_section
from numscons.checkers.common import \
    save_and_set, restore

def check_symbol(context, headers, sym, extra = r''):
    # XXX: add dep vars in code
    #code = [r'#include <%s>' %h for h in headers]
    code = []
    code.append(r'''
#undef %(func)s
#ifdef __cplusplus
extern "C"
#endif
char %(func)s();

int main()
{
return %(func)s();
return 0;
}
''' % {'func' : sym})
    code.append(extra)
    return context.TryLink('\n'.join(code), '.c')

def NumpyCheckLibAndHeader(context, libs, symbols=None, headers=None,
        language=None, section=None, name=None, autoadd=1):
    from SCons.Util import is_List

    env = context.env

    # XXX: handle language
    if language:
        raise NotImplementedError("FIXME: language selection not "\
                                  "implemented yet !")

    # Make sure libs and symbols are lists
    if libs and not is_List(libs):
        libs = [libs]
    if symbols and not is_List(symbols):
        symbols = [symbols]
    if headers and not is_List(headers):
        headers = [headers]

    if not name:
        name = libs[0]

    # Get user customization (numscons.cfg) if any
    # opts will keep all user cusstomization, and put into config check source
    # files in comment so that scons will automatically consider sources as
    # obsolete whenever config change
    opts = []
    build_info = None
    if section:
        cfg = _read_section(section, env)
        if cfg:
            opts.append(cfg)
            build_info = BuildDict.from_config_dict(cfg)

    if build_info is None:
        build_info = BuildDict()

    if not build_info['LIBS']:
        build_info['LIBS'] = libs
    opts.append(build_info)

    # Display message
    if symbols:
        sbstr = ', '.join(symbols)
        msg = 'Checking for symbol(s) %s in %s... ' % (sbstr, name)
    else:
        msg = 'Checking for %s... ' % name
    context.Message(msg)

    # Disable from environment if name=None is in it
    try:
        value = os.environ[name]
        if value == 'None':
            msg = 'Disabled from env through var %s !' % name
            return context.Result(msg), {}
    except KeyError:
        pass

    # Check whether the header is available (CheckHeader-like checker)
    saved = save_and_set(env, build_info)
    try:
        src_code = [r'#include <%s>' % h for h in headers]
        src_code.extend([r'#if 0', str(opts), r'#endif', '\n'])
        src = '\n'.join(src_code)
        st = context.TryCompile(src, '.c')
    finally:
        restore(env, saved)

    if not st:
        context.Result('Failed (could not check header(s) : check config.log '\
                       'in %s for more details)' % env['build_dir'])
        return st

    # Check whether the library is available (CheckLib-like checker)
    saved = save_and_set(env, build_info)
    try:
        if symbols:
            for sym in symbols:
                # Add opts at the end of the source code to force dependency of
                # check from options.
                extra = [r'#if 0', str(build_info), r'#endif', '\n']
                st = check_symbol(context, None, sym, '\n'.join(extra))
                if not st:
                    break
    finally:
        if st == 0 or autoadd == 0:
            restore(env, saved)

    if not st:
        context.Result('Failed (could not check symbol %s : check config.log '\
                       'in %s for more details))' % (sym, env['build_dir']))
        return st

    context.Result(st)
    return st
