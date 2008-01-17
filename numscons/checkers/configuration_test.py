#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J

# test module for utils module
import os
from copy import copy
import unittest

from numscons.core.utils import DefaultDict
from numscons.checkers.configuration import BuildOpts, BuildOptsFactory, \
                                            available_build_opts_factory_flags

class test_BuildOpts(unittest.TestCase):
    def test_default(self):
        a = BuildOpts()
        assert not  a['libraries'] is a['rpath']
        for k, v in a.items():
            assert v == []

    def test_copy(self):
        a = BuildOpts()
        b = copy(a)
        assert type(a) == type(b)
        a['libraries'] = [1]
        assert len(b['libraries']) == 0

class test_BuildOptsFactory(unittest.TestCase):
    def setUp(self):
        bld = DefaultDict.fromcallable(
                avkeys = available_build_opts_factory_flags(),
                default = lambda: [])
        self.fa = BuildOptsFactory(bld)

    def test_init(self):
        bld = BuildOpts()
        fa = BuildOptsFactory(bld)

    def test_getitem(self):
        assert self.fa['blas'] == self.fa.blas_config

    def test_replace(self):
        b = BuildOpts()
        b['libraries'] = ['yop']
        self.fa.replace(b)
        cfg = self.fa.core_config()
        #print self.fa._data
        for k, v in b.items():
            assert cfg[k] == v
