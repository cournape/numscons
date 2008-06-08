from subprocess import Popen, PIPE

from release import build_verstring, build_fverstring
import release

if release.DEV:
    raise Exception("Dev version ?")

def nofailexec(cmd, cwd = None):
    p = Popen(cmd, cwd = cwd, shell = True)
    p.wait()
    assert p.returncode == 0

def make_tarballs():
    cmd = "python setup.py sdist --formats=bztar,zip"
    nofailexec(cmd)

def test_sanity():
    # This executes numscons unit tests: this is far from convering everything,
    # but at least guarantees basic sanity of the package
    ver = build_verstring()
    cmd = "tar -xjf numscons-%s.tar.bz2" % ver
    nofailexec([cmd], cwd = "dist")

    cmd = "python setup.py scons"
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

make_tarballs()
test_sanity()

make_eggs()
register()
