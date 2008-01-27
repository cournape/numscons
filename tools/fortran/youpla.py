from subprocess import Popen, PIPE, STDOUT
import re

LINK = re.compile('checking for Fortran 77 libraries of (\S*)\.\.\. ([\S\s]*)\s$')
cmd = "./configure F77=g77"
p = Popen(cmd, shell = True, stdout = PIPE)
st = p.wait()
if st:
    raise "BOU"

output = p.stdout.readlines()
for line in output:
    m = LINK.match(line)
    if m:
        print "LDFLAGS for F77 compiler %s are: %s" % (m.group(1), m.group(2))
