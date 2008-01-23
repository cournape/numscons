#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J
import unittest

from numscons.checkers.perflib_info import PerflibInfo, MetalibInfo

class test_PerflibInfo(unittest.TestCase):
    def setUp(self):
        from numscons.checkers.perflib_config import CONFIG
        self.fa = CONFIG['MKL']

    def test_init(self):
        a = PerflibInfo(self.fa)

    def test_print(self):
        print PerflibInfo(self.fa)

class test_MetalibInfo(unittest.TestCase):
    def setUp(self):
        from numscons.checkers.perflib_config import CONFIG
        self.cfg = CONFIG['MKL'].opts_factory.core_config()

    def test_init(self):
        a = MetalibInfo('blas', 'MKL', self.cfg)

    def test_print(self):
        print MetalibInfo('blas', 'MKL', self.cfg)
