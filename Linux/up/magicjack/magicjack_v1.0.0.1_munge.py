#!/usr/bin/env python

import sys
import re

sub_blacklist = []
var_blacklist = ['ENV', 'z']

def main():

    if len(sys.argv) != 3:
        print 'usage: %s infile outfile' % sys.argv[0]
        sys.exit(1)

    try:
        infile = open(sys.argv[1], 'r')
    except:
        print 'error opening %s' % sys.argv[1]
        sys.exit(1)

    lines = infile.readlines()
    infile.close()

    fnames = {}
    vnames = {}
    fnum = 0
    vnum = 0

    for line in lines:
        # find subroutine names
        r = re.search('^\s*sub (\w+)', line)
        if r != None and not r.groups()[0] in sub_blacklist:
            fnames[r.groups()[0]] = 'f%d' % fnum
            fnum += 1

        # find variable names
        if re.search('^\s*my[ \(]', line) != None:
            parts = line.split(',')
            for p in parts:
                r = re.search('[@$%]([_a-zA-Z]\w*)', p)
                if r != None and not r.groups()[0] in var_blacklist:
                    vnames[r.groups()[0]] = 'z%d' % vnum
                    vnum += 1

    # sort by length to replace longer names first
    fname_keys = fnames.keys()
    fname_keys.sort(cmp=lambda x, y: len(y) - len(x))
    vname_keys = vnames.keys()
    vname_keys.sort(cmp=lambda x, y: len(y) - len(x))

    try:
        outfile = open(sys.argv[2], 'w')
    except:
        print 'error opening %s' % sys.argv[2]
        sys.exit(1)

    for i in xrange(0, len(lines)):
        for k in fname_keys:
            lines[i] = re.sub('([^@$%%\w]*)%s(\W*)' % k, r'\1%s\2' % fnames[k], lines[i])

        for k in vname_keys:
            lines[i] = re.sub('([@$%%][#{]?)%s(\W)' % k, r'\1%s\2' % vnames[k], lines[i])

        outfile.write(lines[i])

    outfile.close()


if __name__ == '__main__':
    main()
