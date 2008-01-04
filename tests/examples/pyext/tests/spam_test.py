import unittest

from numsconstests.scons_fake.pyext import spam

class test_ra(unittest.TestCase):
    def test(self):
        spam.system('dir')
