#!/usr/bin/env python
version = '1.0.0.0'

import os
import re
import sys
import math
import getopt
import os.path
import binascii
import subprocess

STOREBIN = 'Store'

def compute_mu(n, radix_bits=32):

    b = 2**radix_bits
    k = 1

    while n >= b**k:
        k += 1

    return long(b**(2*k)/n)


def get_hex_bytes(data, i):

    num = ''

    while i < len(data):
        if data[i].startswith(' '):
            bytes = data[i].strip().split(':')
            if bytes[-1] == '':
                bytes.pop()
            num += ''.join(bytes)
            i += 1
        else:
            i += 1
            break

    if num[0:2] == '00':
        num = num[2:]

    return binascii.unhexlify(num)


def get_idx(data, s):

    i = 0

    while i < len(data):
        if data[i].startswith(s):
            i += 1
            break
        i += 1

    return i


def fix_num(n):

    if n[-1] == 'L' or n[-1] == 'l':
        n = n[:-1]
    if len(n) % 2 == 1:
        n = '0%s' % (n)

    return n


def get_key_params(keyfile):

    try:
        f = open(keyfile)
        data = f.readlines()
        f.close()
    except:
        print 'ERROR: Could not open "%s"' % (keyfile)
        return None

    i = get_idx(data, 'prime1')
    p = get_hex_bytes(data, i)
    i = get_idx(data, 'prime2')
    q = get_hex_bytes(data, i)

    p_num = long(binascii.hexlify(p), 16)
    q_num = long(binascii.hexlify(q), 16)

    i = get_idx(data, 'modulus')
    m = get_hex_bytes(data, i)
    i = get_idx(data, 'exponent1')
    dp = get_hex_bytes(data, i)
    i = get_idx(data, 'exponent2')
    dq = get_hex_bytes(data, i)
    i = get_idx(data, 'coefficient')
    qinv = get_hex_bytes(data, i)
    i = get_idx(data, 'publicExponent')
    exp_num = long(data[i-1].split()[1])

    i = get_idx(data, 'clientAuth')
    cli = get_hex_bytes(data, i)
    i = get_idx(data, 'serverAuth')
    svr = get_hex_bytes(data, i)

    mup_num = compute_mu(p_num)
    muq_num = compute_mu(q_num)
    mu_num = compute_mu(p_num*q_num)

    exp = binascii.unhexlify(fix_num(hex(exp_num)[2:]))
    mup = binascii.unhexlify(fix_num(hex(mup_num)[2:]))
    muq = binascii.unhexlify(fix_num(hex(muq_num)[2:]))
    mu = binascii.unhexlify(fix_num(hex(mu_num)[2:]))

    params = {}
    params['m'] = m
    params['mu'] = mu
    params['exp'] = exp
    params['p'] = p
    params['q'] = q
    params['dp'] = dp
    params['dq'] = dq
    params['qinv'] = qinv
    params['mup'] = mup
    params['muq'] = muq
    params['cli'] = cli
    params['svr'] = svr

    return params


def usage(prog):

    print 'usage: %s [-p] [-s storebin] -k keyfile <binary> [binary ...]\n' % (prog)
    print 'options:'
    print '  -p           add the private key to the binary'
    print '               NOTE: should ONLY be done for the client binary'
    print '  -k keyfile   the key text file to inject'
    print '  -s storebin  use storebin as the Store executable\n'
    sys.exit(1)

def main():

    addpriv = False
    keyfile = None
    storebin = STOREBIN

    if len(sys.argv) == 1:
        usage(sys.argv[0])

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvps:k:')
    except getopt.GetoptError, err:
        print str(err)
        usage(sys.argv[0])
    
    for o, a in opts:
        if o == '-h':
            usage(sys.argv[0])
        elif o == '-v':
            print '%s version %s' % (os.path.basename(sys.argv[0]), version)
            sys.exit(0)
        elif o == '-p':
            addpriv = True
        elif o == '-k':
            keyfile = a
        elif o == '-s':
            storebin = a
    
    if len(args) < 1:
        print 'ERROR: No binary specified'
        usage(sys.argv[0])

    if keyfile == None or not os.path.exists(keyfile):
        print 'ERROR: key file "%s" does not exist' % (keyfile)
        sys.exit(1)

    for f in args:
        if not os.path.exists(f):
            print 'ERROR: "%s" does not exist' % (f)
            sys.exit(1)

    key_params = get_key_params(keyfile)
    if key_params == None:
        exit(1)

    for k in key_params.iterkeys():
        p = binascii.hexlify(key_params[k])
        p_arr = [ p[i:i+2] for i in xrange(0, len(p), 2) ]
        p_arr.reverse()
        key_params[k] = '\\\\x%s' % ('\\\\x'.join(p_arr))

    for b in args:
        print 'Storing: %s' % (b)

        os.system('%s --file="%s" --wipe > /dev/null' % (storebin, b))
        os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['cli'], storebin, b, 'cli'))
        os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['svr'], storebin, b, 'svr'))

        if addpriv:
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['p'], storebin, b, 'p'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['q'], storebin, b, 'q'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['dp'], storebin, b, 'dp'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['dq'], storebin, b, 'dq'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['qinv'], storebin, b, 'qinv'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['mup'], storebin, b, 'mup'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['muq'], storebin, b, 'muq'))
        else:
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['m'], storebin, b, 'm'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['mu'], storebin, b, 'mu'))
            os.system('/bin/bash -c \'echo -ne %s | %s --file="%s" --set="%s" > /dev/null\'' % (key_params['exp'], storebin, b, 'exp'))
        #os.system('%s --file="%s" --list' % (storebin, b))
            

if __name__ == '__main__':
    main()
