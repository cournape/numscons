#! /usr/bin/env python
# Last Change: Fri Nov 16 01:00 PM 2007 J

# test module for utils module
import os
import unittest
from copy import deepcopy

from numscons.core.utils import pkg_to_path, _rsplit, DefaultDict, delconsdup
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

class RsplitTester(unittest.TestCase):
    def test1(self):
        a1 = 'a.b.c'
        assert a1.split('.', -1) == a1.rsplit('.', -1) == _rsplit(a1, '.', -1)
        assert a1.rsplit('.', 1) == _rsplit(a1, '.', 1)
        assert a1.rsplit('.', 0) == _rsplit(a1, '.', 0)
        assert a1.rsplit('.', 2) == _rsplit(a1, '.', 2)

    def test2(self):
        a2 = 'floupi'
        assert a2.rsplit('.') ==  _rsplit(a2, '.', -1)
        assert a2.rsplit('.', 1) == _rsplit(a2, '.', 1)

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

class DelConsDupTester(unittest.TestCase):
    def test_basic1(self):
        """Check seq wo dup is identical."""
        a = [1, 2, 3]
        assert delconsdup(a) == a

    def test_basic2(self):
        """Check seq with one dup is correctly processed."""
        a = [1, 2, 3, 3]
        assert delconsdup(a) == [1, 2, 3]

    def test_basic3(self):
        """Check seq with several dups is correctly processed."""
        a = [1, 2, 3, 3, 2, 1, 1, 2]
        assert delconsdup(a) == [1, 2, 3, 2, 1, 2]

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
