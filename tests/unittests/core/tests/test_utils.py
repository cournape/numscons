#! /usr/bin/env python
# Last Change: Wed Jul 30 02:00 PM 2008 J

# test module for utils module
import os
import unittest
from copy import deepcopy

from numscons.core.utils import pkg_to_path, DefaultDict
from numscons.core.utils import unique

class PkgToPathTester(unittest.TestCase):
    def setUp(self):
        self.pkg1 = "foo"
        self.pkg2 = "foo.bar"

        self.path1_expected = "foo"
        self.path2_expected = "foo" + os.sep + "bar"

    def test1(self):
        assert pkg_to_path(self.pkg1) == self.path1_expected
        assert pkg_to_path(self.pkg2) == self.path2_expected

class DefaultDictTester(unittest.TestCase):
    def test_basic1(self):
        d = DefaultDict(('a', 'b'))
        a = d['a']
        b = d['b']

    def test_defval(self):
        d = DefaultDict(('a', 'b'), default = 1)
        a = d['a']
        b = d['b']
        assert a == b == 1

    def test_nonav(self):
        # Check that setting a key not given in the ctor fails
        d = DefaultDict(('a', 'b'))
        d['a'] = 1
        try:
            d['c'] = 2
            raise AssertionError('Setting a non existing key succeeded, '\
                                 'should have failed.')
        except KeyError:
            pass

    def test_fromcallable(self):
        a = DefaultDict.fromcallable(('1', '2'), lambda: [])
        assert not a['1'] is a['2']

        b = DefaultDict(('1', '2'), [])
        assert b['1'] is b['2']

    def test_copy(self):
        from copy import copy
        a = DefaultDict(('a', 'b'))
        a['a'] = ['a']
        a['b'] = ['b']
        b = copy(a)
        b['b'] += 'c'

        assert not b['b'] == a['b']
        assert b['a'] == a['a']
        assert b['a'] is not a['a']

class UniqueTest(unittest.TestCase):
    def test_donothing(self):
        a = [1, 2]
        b = deepcopy(a)
        assert unique(b) == a

    def test_basic(self):
        a = [1, 2, 2, 1]
        assert unique(a) == [1, 2]

if __name__ == "__main__":
    unittest.main()
