#! /usr/bin/env python
# Last Change: Wed Jul 30 02:00 PM 2008 J
"""This module defines the default tools for each platform, as well as the
default compiler configurations."""

# This is a copy of scons/Tools/__init__.py, because scons does not offer any
# public api for this
def tool_list(platform):
    """platform should be the value returned by enbv['PLATFORM'], not
    sys.platform. """

    if str(platform) == 'win32':
        # prefer Microsoft tools on Windows
        linkers = ['mslink', 'gnulink', 'ilink', 'linkloc', 'ilink32' ]
        c_compilers = ['msvc', 'mingw', 'gcc', 'intelc', 'icl', 'icc', 'cc',
                       'bcc32' ]
        cxx_compilers = ['msvc', 'intelc', 'icc', 'g++', 'c++', 'bcc32' ]
        assemblers = ['masm', 'nasm', 'gas', '386asm' ]
        fortran_compilers = ['g77', 'ifl', 'cvf', 'f95', 'f90', 'fortran']
        ars = ['mslib', 'ar', 'tlib']
    elif str(platform) == 'sunos':
        # prefer Forte tools on SunOS
        linkers = ['sunlink', 'gnulink']
        c_compilers = ['suncc', 'gcc', 'cc']
        cxx_compilers = ['sunc++', 'g++', 'c++']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'f77', 'g77', 'fortran']
        ars = ['sunar']
    elif str(platform) == 'hpux':
        # prefer aCC tools on HP-UX
        linkers = ['hplink', 'gnulink']
        c_compilers = ['hpcc', 'gcc', 'cc']
        cxx_compilers = ['hpc++', 'g++', 'c++']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'f77', 'g77', 'fortran']
        ars = ['ar']
    elif str(platform) == 'aix':
        # prefer AIX Visual Age tools on AIX
        linkers = ['aixlink', 'gnulink']
        c_compilers = ['aixcc', 'gcc', 'cc']
        cxx_compilers = ['aixc++', 'g++', 'c++']
        assemblers = ['as', 'gas']
        fortran_compilers = ['f95', 'f90', 'aixf77', 'g77', 'fortran']
        ars = ['ar']
    elif str(platform) == 'darwin':
        # prefer GNU tools on Mac OS X, except for some linkers and IBM tools
        linkers = ['applelink', 'gnulink']
        c_compilers = ['gcc', 'cc']
        cxx_compilers = ['g++', 'c++']
        assemblers = ['as']
        fortran_compilers = ['f95', 'f90', 'g77']
        ars = ['ar']
    else:
        # prefer GNU tools on all other platforms
        linkers = ['gnulink', 'mslink', 'ilink']
        c_compilers = ['gcc', 'msvc', 'intelc', 'icc', 'cc']
        cxx_compilers = ['g++', 'msvc', 'intelc', 'icc', 'c++']
        assemblers = ['gas', 'nasm', 'masm']
        fortran_compilers = ['f95', 'f90', 'g77', 'ifort', 'ifl', 'fortran']
        ars = ['ar', 'mslib']

    other_tools = ['BitKeeper', 'CVS', 'dmd', 'dvipdf', 'dvips', 'gs', 'jar',
            'javac', 'javah', 'latex', 'lex', 'm4', 'midl', 'msvs', 'pdflatex',
            'pdftex', 'Perforce', 'RCS', 'rmic', 'rpcgen', 'SCCS', 'swig',
            'tar', 'tex', 'yacc', 'zip']
    return linkers, c_compilers, cxx_compilers, assemblers, fortran_compilers, \
           ars, other_tools
