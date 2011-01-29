import sys
import getopt

from subprocess import Popen, PIPE
import os

from release import build_verstring, build_fverstring
import release

def nofailexec(cmd, cwd = None):
    p = Popen(cmd, cwd = cwd, shell = True)
    p.wait()
    assert p.returncode == 0

def make_tarballs(fast = False):
    if fast:
        cmd = "python setup.py sdist --formats=zip"
    else:
        cmd = "python setup.py sdist --formats=bztar,zip"
    nofailexec(cmd)

def test_sanity():
    # This executes numscons unit tests: this is far from covering everything,
    # but at least guarantees basic sanity of the package
    ver = build_fverstring()
    cmd = "tar -xjf numscons-%s.tar.bz2" % ver
    nofailexec([cmd], cwd = "dist")

    cmd = "PYTHONPATH=%s:$PYTHONPATH python setup.py scons" % \
            os.path.join(os.getcwd(), "dist", "numscons-%s" % ver)
    nofailexec([cmd], cwd = "dist/numscons-%s/tests" % ver)

def make_eggs():
    # Build eggs for 2.4 and 2.5
    cmd = "python setupegg.py bdist_egg"
    nofailexec([cmd])

    cmd = "python2.4 setupegg.py bdist_egg"
    nofailexec([cmd])

def register():
    # Register tarballs and eggs on pypi
    cmd = "python setup.py register sdist --formats=bztar,zip upload"
    nofailexec([cmd])

    cmd = "python setupegg.py register bdist_egg upload"
    nofailexec([cmd])

    cmd = "python2.4 setupegg.py register bdist_egg upload"
    nofailexec([cmd])

def process(arg):
    if arg == 'test':
        make_tarballs()
        test_sanity()
    elif arg == 'release':
        if release.DEV:
            raise Exception("Dev version ?")
        make_tarballs()
        test_sanity()

        make_eggs()
        register()
    else:
        raise ValueError("Unknown option %s" % arg)



USAGE = """Small program to automatize tasks for a numscons release.

Usage:
    - %s test: basic sanity checks (numscons import, unit tests)
    - %s release: do the release""" % (__file__, __file__)

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print USAGE
            sys.exit(0)
    # process arguments
    for arg in args:
        process(arg) # process() is defined elsewhere


if __name__ == '__main__':
    main()
