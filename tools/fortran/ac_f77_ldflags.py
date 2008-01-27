from subprocess import Popen, PIPE, STDOUT
import re

def parse_autoconf_output(lines):
    LINK = re.compile('checking for Fortran 77 libraries of (\S*)\.\.\. ([\S\s]*)\s$')
    for line in lines:
        m = LINK.match(line)
        if m:
            return (m.group(1), m.group(2))

    raise RuntimeError("no F77 libraries output found in autoconf ?")

def autoconf_output(fcomp):
    cmd = "./configure F77=%s" % fcomp
    p = Popen(cmd, shell = True, stdout = PIPE)
    st = p.wait()
    if st:
        raise RuntimeError("Failed running comd %s" % cmd)

    output = p.stdout.readlines()

    return output

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser()

    (options, args) = parser.parse_args()
    if len(args) < 1:
        raise "You should give the compiler as an argument"

    out = autoconf_output(args[0])
    res = parse_autoconf_output(out)
    print "Compiler %s output is %s" % (res[0], res[1])
