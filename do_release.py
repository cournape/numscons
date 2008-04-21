from subprocess import call

from release import VERSION

yop = VERSION.split('.')
try:
    micro = int(yop[-1])
except ValueError:
    raise Exception("Bad micro version: version is %s" % VERSION)
