#! Last Change: Fri Jan 25 05:00 PM 2008 J
import unittest

from numscons.checkers.fortran.fortran import parse_f77link
from numscons.checkers.fortran.fortran import gnu_to_scons_flags, find_libs_paths

from fortran_output import g77_link_output, gfortran_link_output, \
    sunfort_v12_link_output, ifort_v10_link_output, \
    mingw_g77_link_output, cygwin_g77_link_output, \
    g77_link_expected, gfortran_link_expected, \
    sunfort_v12_link_expected, ifort_v10_link_expected, \
    cygwin_g77_link_expected, mingw_g77_link_expected, \
    cygwin_g77_link_parsed, g77_link_parsed

class test_CheckF77Verbose(unittest.TestCase):
    def setUp(self):
        pass

    def test_g77(self):
        """Parsing g77 link output."""
        assert parse_f77link(g77_link_output.split('\n')) == g77_link_expected

    def test_gfortran(self):
        """Parsing gfortran link output."""
        assert parse_f77link(gfortran_link_output.split('\n')) == \
               gfortran_link_expected

    def test_sunf77(self):
        """Parsing sunfort link output."""
        assert parse_f77link(sunfort_v12_link_output.split('\n')) == \
               sunfort_v12_link_expected

    def test_intel_posix(self):
        """Parsing ifort link output."""
        assert parse_f77link(ifort_v10_link_output.split('\n')) == \
               ifort_v10_link_expected

    def test_intel_win(self):
        """Parsing ifort link output on win32."""
        print "FIXME: testing verbose output of win32 intel fortran"

    def test_mingw_g77(self):
        """Parsing mingw g77 link output on win32 (native, i.e. no cygwin)"""
        print "FIXME: testing verbose output of mingw g77"
        #assert parse_f77link(mingw_g77_link_output.split('\n')) == \
        #       mingw_g77_link_expected

    def test_cygwin_g77(self):
        """Parsing cygwin g77 link output on win32."""
        assert parse_f77link(cygwin_g77_link_output.split('\n')) == \
               cygwin_g77_link_expected

class test_gnu_to_scons_flags(unittest.TestCase):
	def test1(self):
		flags = gnu_to_scons_flags(cygwin_g77_link_expected)
		assert cygwin_g77_link_parsed == flags

#class test_find_libs_paths(unittest.TestCase):
#	def test1(self):
#		paths = g77_link_parsed['LIBPATH']
#		print find_libs_paths(['g2c'], paths)
