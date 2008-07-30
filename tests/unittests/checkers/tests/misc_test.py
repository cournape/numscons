import unittest

from numscons.checkers.misc import sunperf_parser_link

output_v12 = r"""
cc -o build/scons/numpy/scons_fake/checkers/.sconf/conftest_5 -xlic_lib=sunperf -# build/scons/numpy/scons_fake/checkers/.sconf/conftest_5.o
### Note: NLSPATH = /opt/SUNWspro/prod/bin/../lib/locale/%L/LC_MESSAGES/%N.cat:/opt/SUNWspro/prod/bin/../../lib/locale/%L/LC_MESSAGES/%N.cat
###     command line files and options (expanded):
	### -xlic_lib=sunperf build/scons/numpy/scons_fake/checkers/.sconf/conftest_5.o -o build/scons/numpy/scons_fake/checkers/.sconf/conftest_5
	### Note: LD_LIBRARY_PATH = <null>
	### Note: LD_RUN_PATH = <null>
	/usr/ccs/bin/ld /opt/SUNWspro/prod/lib/crti.o /opt/SUNWspro/prod/lib/crt1.o /opt/SUNWspro/prod/lib/values-xa.o -o build/scons/numpy/scons_fake/checkers/.sconf/conftest_5 -lsunperf -lfui -lfsu -lmtsk -lsunmath -lpicl -lm build/scons/numpy/scons_fake/checkers/.sconf/conftest_5.o -Y "P,/opt/SUNWspro/lib:/opt/SUNWspro/prod/lib:/usr/ccs/lib:/lib:/usr/lib" -Qy -R/opt/SUNWspro/lib -lc /opt/SUNWspro/prod/lib/crtn.o"""

expect_v12 = {
    'libraries': ['sunperf', 'fui', 'fsu', 'mtsk', 'sunmath'],
    'rpath': ['/opt/SUNWspro/lib'],
    'library_dirs': ['/opt/SUNWspro/lib', '/opt/SUNWspro/prod/lib',
                     '/usr/ccs/lib', '/lib', '/usr/lib']}

class TestSunperfParser(unittest.TestCase):
    def test_v12(self):
        """Test parse of output from sun studio 12."""
        res = sunperf_parser_link(output_v12)
        for k, v in res.items():
            assert v == expect_v12[k]
