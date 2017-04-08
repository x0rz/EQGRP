#!/usr/bin/env python
version = "1.0.0.0"

import os
import os.path
import re
import sys
import binascii
import subprocess


def lo_execute(cmd):
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read()

    return output


def main():

    if len(sys.argv) != 2:
        print 'usage: %s <outfile>' % os.path.basename(sys.argv[0])
        sys.exit(1)

    rsakey_txt = lo_execute('openssl genrsa 2048 2> /dev/null | openssl rsa -text 2> /dev/null')
    client_auth = binascii.hexlify(lo_execute('openssl rand 16'))
    server_auth = binascii.hexlify(lo_execute('openssl rand 16'))

    rsakey_txt_arr = []
    incl = True

    for line in rsakey_txt.split('\n'):
        if line == '-----BEGIN RSA PRIVATE KEY-----':
            incl = False
        elif line == '-----END RSA PRIVATE KEY-----':
            incl = True
            continue

        if incl:
            rsakey_txt_arr.append(line)

    rsakey_txt = '\n'.join(rsakey_txt_arr)

    f = open(sys.argv[1], 'w')

    f.write(rsakey_txt)
    f.write('clientAuth:\n  %s\n' % client_auth)
    f.write('serverAuth:\n  %s\n' % server_auth)

    f.close()


if __name__ == '__main__':
    main()
