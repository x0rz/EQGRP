#!/usr/bin/env python
VERSION = '1.0.0.4'

import os
import re
import sys
import time
import getopt
import os.path
import subprocess


def usage(prog):

    print 'usage: python %s [options] ifname [logfile]' % prog
    print 'options:'
    print '  -h            show this help and exit'
    print '  -e            show extended stats (kbpm, kbp10m, kbph)'
    print '  -n interval   update interval in seconds (default 5)'
    print '  -v            show version and exit'
    show_version(prog)
    sys.exit(0)


def show_version(prog):

    print '%s version %s' % (prog, VERSION)


def lo_execute(cmd):
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read()

    return output


def print_data(ifname, rx_bytes, rx_pkts, rx_kbps, rx_kbpm, rx_kbp10m, rx_kbph,
               tx_bytes, tx_pkts, tx_kbps, tx_kbpm, tx_kbp10m, tx_kbph,
               show_extended, logfile):

    t = int(time.time())
    tstr = time.strftime('%a %b %d %H:%M:%S %Z %Y')

    rx_MB = float(rx_bytes) / 1048576.0
    tx_MB = float(tx_bytes) / 1048576.0

    rx_kBps = rx_kbps / 8.0
    tx_kBps = tx_kbps / 8.0

    outstr = '%s\n' % tstr
    outstr += '%3s  %11s %9s %10s %8s %9s' % (ifname, 'bytes', '(MB)', 'packets', 'kbps', '(kBps)')
    if show_extended:
        outstr += ' %9s %9s %9s' % ('kbps-1m', 'kbps-10m', 'kbps-hr')
    outstr += '\n'
    outstr += '  TX  %11d %9s %10d %8.1f %9s' % (tx_bytes, '(%.1f)' % tx_MB, tx_pkts, tx_kbps, '(%.1f)' % tx_kBps)
    if show_extended:
        outstr += ' %9.1f %9.1f %9.1f' % (tx_kbpm, tx_kbp10m, tx_kbph)
    outstr += '\n'
    outstr += '  RX  %11d %9s %10d %8.1f %9s' % (rx_bytes, '(%.1f)' % rx_MB, rx_pkts, rx_kbps, '(%.1f)' % rx_kBps)
    if show_extended:
        outstr += ' %9.1f %9.1f %9.1f' % (rx_kbpm, rx_kbp10m, rx_kbph)

    print outstr

    if logfile != None:
        try:
            fd = open(logfile, 'a')
            fd.write(outstr + '\n')
            fd.close()
        except:
            pass

    return


def get_bw_info(ifname):

    rx_bytes = 0
    rx_pkts = 0
    tx_bytes = 0
    tx_pkts = 0

    try:
        fd = open('/proc/net/dev', 'r')
        lines = fd.readlines()
        fd.close()

        for line in lines:
            if re.search('^ *%s:' % ifname, line):
                data = line.split(':')[1].split()
                rx_bytes = int(data[0])
                rx_pkts = int(data[1])
                tx_bytes = int(data[8])
                tx_pkts = int(data[9])
    except:
        out = lo_execute('/sbin/ifconfig %s' % ifname)

        if re.search('not found', out):
            return (0, 0, 0, 0)

        rx_bytes = int(re.search('RX bytes:([0-9]+) ', out).group(1))
        tx_bytes = int(re.search('TX bytes:([0-9]+) ', out).group(1))

        rx_pkts = int(re.search('RX packets:([0-9]+) ', out).group(1))
        tx_pkts = int(re.search('TX packets:([0-9]+) ', out).group(1))

    return (rx_bytes, rx_pkts, tx_bytes, tx_pkts)


def doloop(ifname, interval, show_extended, logfile):

    prev_rx, prev_rxp, prev_tx, prev_txp = get_bw_info(ifname)

    # extended stats
    prev_rx_min = [prev_rx] * 60
    prev_rx_10min = [prev_rx] * 600
    prev_rx_hr = [prev_rx] * 3600
    prev_tx_min = [prev_tx] * 60
    prev_tx_10min = [prev_tx] * 600
    prev_tx_hr = [prev_tx] * 3600

    print_data(ifname, prev_rx, prev_rxp, 0, 0, 0, 0,
               prev_tx, prev_txp, 0, 0, 0, 0, show_extended, logfile)

    counter = 1

    while True:
        curr_sec = int(time.time())

        rx, rpkts, tx, tpkts = get_bw_info(ifname)

        if counter % interval == 0:
            rx_kbps = ((rx - prev_rx) * 8) / 1024.0 / interval
            tx_kbps = ((tx - prev_tx) * 8) / 1024.0 / interval
            prev_rx = rx
            prev_tx = tx

        i = curr_sec % 60
        rx_kbpm = ((rx - prev_rx_min[i]) * 8) / 1024.0 / 60
        tx_kbpm = ((tx - prev_tx_min[i]) * 8) / 1024.0 / 60
        prev_rx_min[i] = rx
        prev_tx_min[i] = tx

        i = curr_sec % 600
        rx_kbp10m = ((rx - prev_rx_10min[i]) * 8) / 1024.0 / 600
        tx_kbp10m = ((tx - prev_tx_10min[i]) * 8) / 1024.0 / 600
        prev_rx_10min[i] = rx
        prev_tx_10min[i] = tx

        i = curr_sec % 3600
        rx_kbph = ((rx - prev_rx_hr[i]) * 8) / 1024.0 / 3600
        tx_kbph = ((tx - prev_tx_hr[i]) * 8) / 1024.0 / 3600
        prev_rx_hr[i] = rx
        prev_tx_hr[i] = tx

        if counter % interval == 0:
            print_data(ifname, rx, rpkts, rx_kbps, rx_kbpm, rx_kbp10m, rx_kbph,
                       tx, tpkts, tx_kbps, tx_kbpm, tx_kbp10m, tx_kbph,
                       show_extended, logfile)

        time.sleep(1)
        counter += 1

    return


def main(argv):

    prog = os.path.basename(argv[0])
    interval = 5
    ext_stats = False

    try:
        opts, args = getopt.getopt(argv[1:], 'hvn:e')
    except getopt.GetoptError, err:
        print str(err)
        usage(prog)

    for o, a in opts:
        if o == '-h':
            usage(prog)
        elif o == '-v':
            show_version(prog)
            sys.exit(0)
        elif o == '-n':
            try:
                interval = int(a)
            except:
                print 'ERROR: invalid interval %s' % a
                sys.exit(1)

            if interval <= 0:
                print 'interval must be > 0'
                sys.exit(1)
        elif o == '-e':
            ext_stats = True
        else:
            print 'unknown option'
            usage(prog)

    if len(args) < 1 or len(args) > 2:
        usage(prog)

    ifname = args[0]

    if len(args) == 2:
        logfile = args[1]
    else:
        logfile = None

    doloop(ifname, interval, ext_stats, logfile)


if __name__ == '__main__':

    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass
