#! /usr/bin/env python
# Last Change: Fri Nov 16 01:00 PM 2007 J

# test module for utils module
import os
import unittest

from numscons.core.compiler_detection import *

# Output of gcc -v
GCC_4_2_3 = """
Using built-in specs.
Target: i486-linux-gnu
Configured with: ../src/configure -v --enable-languages=c,c++,fortran,objc,obj-c++,treelang --prefix=/usr --enable-shared --with-system-zlib --libexecdir=/usr/lib --without-included-gettext --enable-threads=posix --enable-nls --with-gxx-include-dir=/usr/include/c++/4.2 --program-suffix=-4.2 --enable-clocale=gnu --enable-libstdcxx-debug --enable-objc-gc --enable-mpfr --enable-targets=all --enable-checking=release --build=i486-linux-gnu --host=i486-linux-gnu --target=i486-linux-gnu
Thread model: posix
gcc version 4.2.3 (Ubuntu 4.2.3-2ubuntu7)"""

# Output of suncc -V -### main.c
SUNCC_12 = """
cc: Sun C 5.9 Linux_i386 Patch 124871-01 2007/07/31
### Note: NLSPATH = /home/david/opt/sunstudio12/prod/bin/../lib/locale/%L/LC_MESSAGES/%N.cat:/home/david/opt/sunstudio12/prod/bin/../../lib/locale/%L/LC_MESSAGES/%N.cat
###     command line files and options (expanded):
### -V main.c
/home/david/opt/sunstudio12/prod/bin/acomp -xldscope=global -i main.c -y-fbe -y/home/david/opt/sunstudio12/prod/bin/fbe -y-xarch=generic -y-o -ymain.o -y-verbose -y-xthreadvar=no%dynamic -y-comdat -xdbggen=no%stabs+dwarf2+usedonly -V -xdbggen=incl -y-s -m32 -fparam_ir -Qy -D__SUNPRO_C=0x590 -D__unix -D__unix__ -D__i386 -D__i386__ -D__linux__ -D__linux -Dlinux -D__gnu__linux__ -D__BUILTIN_VA_ARG_INCR -D__C99FEATURES__ -Xa -D__PRAGMA_REDEFINE_EXTNAME -Dunix -Di386 -D__RESTRICT -xc99=%all,no%lib -D__FLT_EVAL_METHOD__=-1 -c99OS -I/home/david/opt/sunstudio12/prod/include/cc "-g/home/david/opt/sunstudio12/prod/bin/cc -V -c " -fsimple=0 -D__SUN_PREFETCH -destination_ir=yabe
### Note: LD_LIBRARY_PATH = /home/david/opt/sunstudio12/lib:/home/david/opt/sunstudio12/rtlibs:
### Note: LD_RUN_PATH = <null>
/usr/bin/ld -m elf_i386 -dynamic-linker /lib/ld-linux.so.2 --enable-new-dtags /home/david/opt/sunstudio12/prod/lib/crti.o /home/david/opt/sunstudio12/prod/lib/crt1.o /home/david/opt/sunstudio12/prod/lib/values-xa.o -V main.o -Y "/home/david/opt/sunstudio12/prod/lib:/lib:/usr/lib" -Qy -lc /home/david/opt/sunstudio12/prod/lib/libc_supp.a /home/david/opt/sunstudio12/prod/lib/crtn.o
"""

# Output of sunCC -V
SUNCXX_12 = """sunCC: Sun C++ 5.9 Linux_i386 Patch 124865-01 2007/07/30"""

# Output of sunf77 -V
SUNFORTRAN_12 = """
NOTICE: Invoking /home/david/opt/sunstudio12/bin/f90 -f77 -ftrap=%none -V
f90: Sun Fortran 95 8.3 Linux_i386 Patch 127145-01 2007/07/31
Usage: f90 [ options ] files.  Use 'f90 -flags' for details"""

# Output of icc -V, 10.1.015
ICC_10 = """
Intel(R) C Compiler for applications running on IA-32, Version 10.1    Build 20080312 Package ID: l_cc_p_10.1.015
Copyright (C) 1985-2008 Intel Corporation.  All rights reserved.
FOR NON-COMMERCIAL USE ONLY

"""

# Output of ifort -V, 10.1.015
IFORT_10 = """
Intel(R) Fortran Compiler for applications running on IA-32, Version 10.1 Build 20080312 Package ID: l_fc_p_10.1.015
Copyright (C) 1985-2008 Intel Corporation.  All rights reserved.
FOR NON-COMMERCIAL USE ONLY

"""


class OutputParser(unittest.TestCase):
    def test_gnu(self):
        ret = parse_gnu(GCC_4_2_3)
        assert ret == (True, "4.2.3")

    def test_suncc(self):
        ret = parse_suncc(SUNCC_12)
        assert ret == (True, "5.9")

    def test_suncxx(self):
        ret = parse_suncxx(SUNCXX_12)
        assert ret == (True, "5.9")

    def test_sunfortran(self):
        ret = parse_sunfortran(SUNFORTRAN_12)
        assert ret == (True, "8.3")

    def test_icc(self):
        ret = parse_icc(ICC_10)
        assert ret == (True, "10.1")

    def test_ifort(self):
        ret = parse_ifort(IFORT_10)
        assert ret == (True, "10.1")

if __name__ == "__main__":
    unittest.main()
