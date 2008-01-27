#! /usr/bin/env python
import sys
from subprocess import Popen, PIPE, STDOUT

def generate_output(fcomp, vflag, fflag, objsuff = '.o'):
    cmd = '%s %s %s' % (fcomp, fflag, 'empty.f')
    p = Popen(cmd, shell = True)
    st = p.wait()
    if st:
        raise RuntimeError("Compilation failed: status is %s. output is %s" %\
                           (st, p.stdout.read()))
    cmd = '%s %s %s' % (fcomp, vflag, 'empty%s' % objsuff)
    p = Popen(cmd, stdout = PIPE, stderr = STDOUT, shell = True)
    st = p.wait()
    if st:
        raise RuntimeError("Link failed (cmd was %s): status is %s. output is %s" %\
                           (cmd, st, p.stdout.read()))
    output = p.stdout.read()
    return output

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-c", "--compile-flag", dest="fflag",
                      help="compiler flag (-c, etc...)")
    parser.add_option("-v", "--verbose-flag", dest="vflag",
                      help = "verbose flag (-v, etc...). This should be the "
                      "*linker* verbose flag, not the compiler one.")

    (options, args) = parser.parse_args()
    if options.fflag:
        fflag = options.fflag
    else:
        fflag = '-c'
    if options.vflag:
        vflag = options.vflag
    else:
        vflag = '-v'

    if len(args) < 1:
        raise "You should give the compiler as argument"
    fcomp = args[0]

    output = generate_output(fcomp, vflag, fflag)
    print output
