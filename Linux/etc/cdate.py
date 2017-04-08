#!/usr/bin/env python
version = "3.0.0.0"

import sys
import time
import os
import re
import getopt
import calendar

def usage(prog):

    prog = prog.split(os.sep)[-1]
    print 'usage: %s [options] [date [+/-hr]]\n' % (prog)
    print 'options:'
    print '  -e    show epoch seconds'
    print '  -d    show YYYYMMDDHHMM.SS format'
    print '  -u    show MM/DD HH:MM (sulog) format'
    print '  -s    show string format\n'
    print '  -h    show help and exit'
    print '  -v    show version and exit\n'
    print 'date can be in the following formats:\n'
    print '  epoch in secs                    ex. 1000000000'
    print '  YYYYMMDDHHMM[.SS]                ex. 200109090146.40'
    print '  MM/DD HH:MM [YYYY]               ex. 09/09 01:46 2001'
    print '  [Ddd] Mmm DD HH:MM[:SS] [YYYY]   ex. Sun Sep 09 01:46:40 2001\n'
    print '+/-hr  specifies an offset in hours, ex. +8\n'
    print '%s version %s' % (os.path.basename(prog), version)
    sys.exit(1)

def to_epoch(t):

    return str(calendar.timegm(t))


def to_date(t):

    return time.strftime('%Y%m%d%H%M.%S', t)


def to_str(t):

    return time.strftime('%b %d %H:%M:%S %Y', t)


def to_sulog(t):

    return time.strftime('%m/%d %H:%M %Y', t)

def parse_str(s):

    try:
        if re.match('^\d{1,10}$', s):
            thedate = time.gmtime(int(s))
        elif re.match('^\d{12}$', s):
            thedate = time.strptime(s, '%Y%m%d%H%M')
        elif re.match('^\d{12}\.\d\d$', s):
            thedate = time.strptime(s, '%Y%m%d%H%M.%S')
        elif re.match('^\w{3} \d{1,2} \d\d:\d\d:\d\d \d{4}$', s): # Mmm DD HH:HH:SS YYYY
            thedate = time.strptime(s, '%b %d %H:%M:%S %Y')
        elif re.match('^\w{3} \d{1,2} \d\d:\d\d \d{4}$', s): # Mmm DD HH:HH YYYY
            thedate = time.strptime(s, '%b %d %H:%M %Y')
        elif re.match('^\w{3} \d{1,2} \d\d:\d\d:\d\d$', s): # Mmm DD HH:HH:SS 
            thedate = time.strptime(s + ' %d' % (time.localtime()[0]), '%b %d %H:%M:%S %Y')
        elif re.match('^\w{3} \d{1,2} \d\d:\d\d$', s): # Mmm DD HH:HH
            thedate = time.strptime(s + ' %d' % (time.localtime()[0]), '%b %d %H:%M %Y')
        elif re.match('^\w{3} \w{3} \d{1,2} \d\d:\d\d:\d\d \d{4}$', s): # Ddd Mmm DD HH:HH:SS YYYY
            thedate = time.strptime(s, '%a %b %d %H:%M:%S %Y') 
        elif re.match('^\w{3} \w{3} \d{1,2} \d\d:\d\d \d{4}$', s): # Ddd Mmm DD HH:HH YYYY
            thedate = time.strptime(s, '%a %b %d %H:%M %Y')
        elif re.match('^\w{3} \w{3} \d{1,2} \d\d:\d\d:\d\d$', s): # Ddd Mmm DD HH:HH:SS
            thedate = time.strptime(s + ' %d' % (time.localtime()[0]), '%a %b %d %H:%M:%S %Y')
        elif re.match('^\w{3} \w{3} \d{1,2} \d\d:\d\d$', s): # Ddd Mmm DD HH:HH
            thedate = time.strptime(s + ' %d' % (time.localtime()[0]), '%a %b %d %H:%M %Y')
        elif re.match('^\d\d\/\d\d \d\d:\d\d$', s): # MM/DD HH:MM
            thedate = time.strptime(s + ' %d' % (time.localtime()[0]), '%m/%d %H:%M %Y')
        elif re.match('^\d\d\/\d\d \d\d:\d\d \d\d\d\d$', s): # MM/DD HH:MM YYYY
            thedate = time.strptime(s, '%m/%d %H:%M %Y')
        else:
            return None
    except Exception, e:
        print str(e)
        return None

    return thedate


def print_pretty(t):

    print ''
    print 'epoch time        :   %s' % (t[0])
    print 'YYYYMMDDHHMM.SS   :   %s' % (t[1])
    print 'MM/DD HH:MM YYYY  :   %s' % (t[2])
    print 'full string       :   %s' % (t[3])
    print ''


def convert(args):
    thedate = None
    thedate_woff = None # The date shifted for proper epoch time done by tzoffset
    offset = 0 # To arbitrarily shift all timestamps
    tzoffset = 0 # To set the offset for timezones, properly computing epoch time

    if args == None or len(args) == 0:
        thedate = time.localtime()
    else:
        if len(args[-1]) == 1: # Looks like we were handed a string, so going to do a split here
            args = args.split()
        if re.match('^[+-]\d\d?$', args[-1]):
            offset = int(args[-1])
            if offset < -23 or offset > 23:
                print 'error: bad offset value'
                usage(sys.argv[0])
            args = args[:-1]
        if re.match('^[+-]\d\d\d\d$', args[-1]):
            tzoffset = int(args[-1])/100.0 + (0-int(args[-1])/100.0) % 1 - (abs(int(args[-1])) % 100.0)/60.0
            if tzoffset < -23 or tzoffset > 23:
                print 'error: bad offset value'
                usage(sys.argv[0])
            args = args[:-1]

        thedate = parse_str(' '.join(args))

    if thedate == None:
        print 'error: bad date format'
        usage(sys.argv[0])

    if tzoffset:
        t = calendar.timegm(thedate)
        t -= (tzoffset * 60 * 60)
        thedate_woff = time.gmtime(t)
        return to_epoch(thedate_woff), to_date(thedate), to_sulog(thedate), to_str(thedate)
    if offset:
        t = calendar.timegm(thedate)
        t += (offset * 60 * 60)
        thedate = time.gmtime(t)
    return to_epoch(thedate), to_date(thedate), to_sulog(thedate), to_str(thedate)


def main():

    showe = False
    showd = False
    shows = False
    showu = False

    if len(sys.argv) == 1:
        thedates = convert(None)
        print_pretty(thedates)
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvedsu')
    except getopt.GetoptError, err:
        print str(err)
        usage(sys.argv[0])

    for o, a in opts:
        if o == '-h':
            usage(sys.argv[0])
        elif o == '-v':
            print '%s version %s' % (os.path.basename(sys.argv[0]), version)
            sys.exit(1)
        elif o == '-e':
            showe = True
        elif o == '-d':
            showd = True
        elif o == '-s':
            shows = True
        elif o == '-u':
            showu = True


    thedates = convert(args)


    if showe or showd or shows or showu:
        if showe:
            print thedates[0]
        if showd:
            print thedates[1]
        if showu:
            print thedates[2]
        if shows:
            print thedates[3]
    else:
        print_pretty(thedates)

   

if __name__ == '__main__':
    main() 
