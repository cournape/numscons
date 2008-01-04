from unittest import TestCase

from numsconstests.scons_fake.ctypesext import foo

class test_ra(TestCase):
    def test(self):
        foo()
