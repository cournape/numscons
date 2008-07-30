"""Implements CheckerFactory class, which can be used to create meta-lib
checkers, that is libraries which can have widely different build options
(BLAS, LAPACK, FFT, etc...).

Do NOT use this for 'normal' libraries, just use NumpyCheckLibAndHeader, which
is straightforward, and much easier to use."""
import os
import sys
from copy import copy, deepcopy

from numscons.core.misc import built_with_mstools
from numscons.core.siteconfig import get_config_from_section
from numscons.core.trace import debug, info

from numscons.checkers.perflib_info import add_lib_info, MetalibInfo
from numscons.checkers.perflib import CONFIG, get_perflib_info
from numscons.checkers.support import check_include_and_run
from numscons.checkers.configuration import BuildConfig

from fortran import CheckF77Mangling, CheckF77Clib

def _get_language_opts(context, language):
    """Return additional options necessary depending on the language.

    If no options is necessary (for C, for example), return None. Otherwise,
    returns a dictionary whose possible keys are the same than BuildConfig
    instances."""
    if language == 'C':
        moreopts = None
    elif language == 'F77':
        # We need C/F77 runtime info, otherwise, cannot proceed further
        if not context.env.has_key('F77_LDFLAGS') and not CheckF77Clib(context):
            #add_lib_info(context.env, libname, None)
            return 0
        moreopts = {'linkflagsend' : copy(context.env['F77_LDFLAGS'])}
    else:
        raise ValueError("language %s unknown" % language)

    return moreopts

def _check(perflibs, context, libname, check_version, msg_template, test_src,
           autoadd, language = 'C'):
    """Generic perflib checker to be used in meta checkers.

    perflibs should be a list of perflib to check (the names which can be used
    are the keys of CONFIG."""
    info('Checking for perflibs %s' % str(perflibs))

    moreopts = _get_language_opts(context, language)
    debug('Options for language %s : %s' % (language, moreopts))
    def _check_perflib(pname):
        """pname is the name of the perflib."""
        cache = get_perflib_info(context, pname)
        if not cache:
            debug('Failed getting perflib info from cache for %s' % pname)
            return 0
        cfgopts = cache.opts_factory[libname]()
        info('Config options for %s: %s' % (libname, cfgopts))
        if moreopts:
            # More options are necessary to check the code snippet (fortran
            # runtime, etc...), so we create a new BuildConfig which contain
            # those info.
            testopts = copy(cfgopts)
            for k, v in moreopts.items():
                testopts[k].extend(v)
        else:
            # Nothing to do, testopts and cfgopts are the same
            testopts = cfgopts
        info('Final options for %s: %s' % (libname, testopts))
        st = check_include_and_run(context, msg_template % CONFIG[pname].name,
                                   testopts, [], test_src, autoadd)
        if st:
            add_lib_info(context.env, libname, MetalibInfo(pname, cfgopts))
        return st

    for p in perflibs:
        if _check_perflib(p):
            return 1

def _get_customization(context, section, libname, test_src, autoadd, language = 'C'):
    """Check whether customization is available through config files."""
    siteconfig = context.env['NUMPY_SITE_CONFIG'][0]
    cfgopts, found = get_config_from_section(siteconfig, section)
    if found:
        ncfgopts = BuildConfig()
        for k, v in cfgopts.items():
            ncfgopts[k] = v
        # XXX: grrr....
        if ncfgopts.has_key('library_dirs'):
            ncfgopts['rpath'] = copy(ncfgopts['library_dirs'])
        moreopts = _get_language_opts(context, language)
        if moreopts:
            # More options are necessary to check the code snippet (fortran
            # runtime, etc...), so we create a new BuildConfig which contain
            # those info.
            testopts = copy(ncfgopts)
            for k, v in moreopts.items():
                testopts[k].extend(v)
        else:
            # Nothing to do, testopts and cfgopts are the same
            testopts = ncfgopts
        if check_include_and_run(context, '%s (from site.cfg) ' % libname, testopts,
                                 [], test_src, autoadd):
            add_lib_info(context.env, libname, MetalibInfo(None, cfgopts, found))
            return 1
    return 0

class CheckerFactory:
    def __init__(self, perflibs, section, libname, dispname, test, language = 'C'):
        """Create a Meta-Checker from a list of perlibs and basic informations.

        perflibs: dict
            values should be sequence of perflibs to check. keys should
            correspond to the string returned by sys.platform, or default, or
            fallback.
        section: str
            name of the section in customization file (site.cfg, etc...)
        libname: str
            name of the library
        msg_template: str
            template of the displayed message at configuration stage
        test: callable
            should returns a tuple (test, st) where test is a string, and st
            the status code (1 for success, 0 for failure).
        language: str
            language of the test ('C', 'F77', etc...)
        """
        self._libname = libname
        self._section = section
        self._disp = dispname

        self._test = test
        self._perflibs = perflibs
        self._lang = language

    def _check(self, context, perflibs, check_version, test_src, autoadd):
        return _check(perflibs, context, self._libname, check_version,
                      self._disp + ' (%s)',
                      test_src, autoadd, self._lang)

    def __call__(self, context, autoadd = 1, check_version = 0):

        debug('Calling CheckerFactory (%s)' % self._libname)

        # Is customized from user environment ?
        if os.environ.has_key(self._disp) and os.environ[self._disp] == 'None':
            context.Message("Checking %s ... " % self._disp)
            context.Result('Disabled from env through var %s !' % self._disp)
            return 0

        # Get the source code of the test
        src, st = self._test(context)
        if st:
            add_lib_info(context.env, self._libname, None)
            return 0

        # Get customization from site.cfg, etc... if available
        if _get_customization(context, self._section, self._libname, src, autoadd,
                      self._lang):
            return 1
        else:
            # Test if any performance library provides the whished API
            try:
                pf = self._perflibs[sys.platform]
                debug('Got optimized perflibs info')
            except KeyError:
                pf = self._perflibs['default']
                debug('Got default perflibs info')

            if self._check(context, pf, check_version, src, autoadd):
                return 1

        # try a fallback if available
        try:
            pf = self._perflibs['fallback']
            if self._check(context, pf, check_version, src, autoadd):
                return 1
        except KeyError:
            pass

        # Nothing worked, fail
        add_lib_info(context.env, self._libname, None)
        return 0
