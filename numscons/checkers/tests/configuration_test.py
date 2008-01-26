#! /usr/bin/env python
# Last Change: Sat Jan 26 07:00 PM 2008 J

# test module for utils module
import os
from copy import copy
import unittest

from numscons.core.utils import DefaultDict
from numscons.checkers.configuration import BuildConfig, BuildConfigFactory, \
    build_config_factory_flags

class test_BuildConfig(unittest.TestCase):
    def test_default(self):
        a = BuildConfig()
        assert not  a['libraries'] is a['rpath']
        for k, v in a.items():
            assert v == []

    def test_copy(self):
        a = BuildConfig()
        b = copy(a)
        assert type(a) == type(b)
        a['libraries'] = [1]
        assert len(b['libraries']) == 0

class test_BuildConfigFactory(unittest.TestCase):
    def setUp(self):
        bld = DefaultDict.fromcallable(
                avkeys = build_config_factory_flags(),
                default = lambda: [])
        self.fa = BuildConfigFactory(bld)

    def test_init(self):
        bld = BuildConfig()
        fa = BuildConfigFactory(bld)

    def test_getitem(self):
        assert self.fa['blas'] == self.fa.blas_config

    def test_replace(self):
        b = BuildConfig()
        b['libraries'] = ['yop']
        self.fa.replace(b)
        cfg = self.fa.core_config()
        #print self.fa._data
        for k, v in b.items():
            assert cfg[k] == v

    def test_merge(self):
        tmp = BuildConfig()
        tmp['libraries'] = ['1']
        fa = BuildConfigFactory(tmp)

        tmp = BuildConfig()
        tmp['libraries'] = ['2']
        fa.merge(tmp)
        cfg = fa.core_config()
        assert cfg['libraries'] == ['2', '1']

    def test_merge_append(self):
        tmp = BuildConfig()
        tmp['libraries'] = ['1']
        fa = BuildConfigFactory(tmp)

        tmp = BuildConfig()
        tmp['libraries'] = ['2']
        fa.merge(tmp, append = True)
        cfg = fa.core_config()
        assert cfg['libraries'] == ['1', '2']
