#! /usr/bin/env python
# Last Change: Wed Jan 16 07:00 PM 2008 J

# test module for utils module
import os
from copy import copy
import unittest

from numscons.checkers.configuration import BuildOpts

class test_BuildOpts(unittest.TestCase):
    def test_default(self):
        a = BuildOpts()
        assert not  a['libraries'] is a['rpath']
        for k, v in a.items():
            assert v == []

