#!/usr/bin/env python2.7

import sys
import os
from optparse import OptionParser


def main():
    parser = OptionParser(usage='strangeFiles.py [options]')
    parser.add_option('-f', dest='FINDFILE', type='string', action='store', help='The find file to search through')
    opts, args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    if opts.FINDFILE:
        if os.path.isfile(opts.FINDFILE):
            #>>> a = ["".join(x) for x in list(itertools.product(",. ", repeat=2))]
            #>>> b = ["".join(x) for x in list(itertools.product(",. ", repeat=3))]
            #>>> c = [x for x in b if x[1]==" "]
            strange_dirs = [',,', ',.', ', ', '.,', '..', '. ', ' ,', ' .', '  ', ', ,', ', .', ',  ', '. ,', '. .', '.  ', '  ,', '  .', ' ']
            print "Searching for the following strange directories:\n%s" % "\""+"\"   \"".join(strange_dirs)+"\""
            found_dirs = 0
            for line in open(opts.FINDFILE):
                if "|" in line:
                    for dir in strange_dirs:
                        # Get only the file name by splitting on white space and then rejoining with spaces
                        # This eliminates tab characters and makes them a single space
                        array = line.split()
                        try:
                            theline = " ".join(array[22:array.index("--")])
                        except:
                            theline = " ".join(array[22:])
                        if "/"+dir in theline or dir+"/" in theline:
                            print "HIT:\n\"%s\"\t%s" % (dir,theline)
                            found_dirs = 1
                            break
            if not found_dirs:
                print "\n\tNo strange directories found.\n"
            else:
                print "\n\nSearching complete.  You may close this window once these have been checked."
        else:
            print "\nError: file %s not found.\n" % opts.FINDFILE
            parser.print_help()


if __name__ == '__main__':
    main()

