#!/usr/bin/env python
version = "1.3.4.1"

###############################################################################
#
# 17 Jun 2013
#
# A commandline script to configure the FK firewall. Can be used to set up and 
# tear down the default rules, and add rules allowing traffic to a specific IP.
#
###############################################################################

import os
import sys
import re
import getopt
import fcntl
import socket
import struct
import urllib
import urllib2
import cookielib
import time
import getpass
import subprocess
import os.path

#########################################################
# CONFIGURATION
#########################################################

# Set FW rules duration, in minutes
TIMEOUT = '360'

# Config settings
config = {}
pw_retry = 0          # Current retry number
ask_username = False  # True if need to ask for new username
PW_MAX_RETRY = 3

# Local globals
global my_ip      # external IP

# FW globals
global gw_ip       # gateway IP
global httpobj
global logged_in
global duration

# Other
dbg = False
SIOCGIFADDR = 0x8915
ipt = '/sbin/iptables '
iptsave = '/sbin/iptables-save'
iptrestore = '/sbin/iptables-restore'
BASEURL = 'http://'
configfile = '/current/tmp/fwconfig'
autoutils = '/current/etc/autoutils'
hostvars = '/current/down/hostvars.global'
logfile = '/tmp/getopdatalog'
COLOR_NORMAL = '\033[0;39m'
COLOR_FAILURE = '\033[2;31m'
COLOR_NOTE = '\033[0;34m'
DIR_BI = 1
DIR_IN = 2
DIR_OUT = 3


#########################################################
# Functions for LOCAL ops box
#########################################################


def lo_get_ip(ifname):
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        return socket.inet_ntoa(
            fcntl.ioctl(s.fileno(), SIOCGIFADDR,
                        struct.pack('256s', ifname[:15]))[20:24])
    except:
        return None


def lo_execute(cmd):
    
    if dbg:
        printmsg('# ' + cmd, COLOR_NOTE)
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    output = proc.stdout.read()

    return output


def lo_get_rules():

    return lo_execute(ipt + '-L -n -v --line-numbers')


def lo_clear_rules():
    
    lo_execute(ipt + '-F')


def lo_flush_accept():

    lo_execute(ipt + '-t filter -P INPUT ACCEPT')
    lo_execute(ipt + '-t filter -P OUTPUT ACCEPT')
    lo_execute(ipt + '-t filter -P FORWARD ACCEPT')
    lo_execute(ipt + '-F')


def lo_set_local_rules():

    in_rules = [
        ipt + '-t filter -P INPUT DROP',
        ipt + '-t filter -A INPUT -i lo -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth1 -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth2 -j ACCEPT',
        ]
    out_rules = [
        ipt + '-t filter -P OUTPUT DROP',
        ipt + '-t filter -A OUTPUT -o lo -j ACCEPT',
        ipt + '-t filter -A OUTPUT -o eth1 -j ACCEPT',
        ipt + '-t filter -A OUTPUT -o eth2 -j ACCEPT',
        ]
    fwd_rules = [
        ipt + '-t filter -P FORWARD DROP'
        ]

    for r in in_rules:
        lo_execute(r)
    for r in out_rules:
        lo_execute(r)
    for r in fwd_rules:
        lo_execute(r)


def lo_set_default_rules():
    
    in_rules = [
        ipt + '-t filter -A INPUT -i eth0 -s 0.0.0.0/0 -d ' + my_ip + ' -m state --state ESTABLISHED -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth0 -p icmp -s 0.0.0.0/0 -d ' + my_ip + ' -m state --state ESTABLISHED,RELATED -j ACCEPT'
        ]
    out_rules = [
        ipt + '-t filter -A OUTPUT -o eth0 -p tcp -s ' + my_ip + ' -d 0.0.0.0/0 --dport 80 -j ACCEPT -m state --state NEW,ESTABLISHED',
        ipt + '-t filter -A OUTPUT -o eth0 -p tcp -s ' + my_ip + ' -d 0.0.0.0/0 --dport 443 -j ACCEPT -m state --state NEW,ESTABLISHED',
        ipt + '-t filter -A OUTPUT -o eth0 -p udp -s ' + my_ip + ' -d 0.0.0.0/0 --dport 53 -j ACCEPT',
        ipt + '-t filter -A OUTPUT -o eth0 -p icmp -s ' + my_ip + ' -d 0.0.0.0/0 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT',
        ]

    lo_set_local_rules()
    
    for r in in_rules:
        lo_execute(r)
    for r in out_rules:
        lo_execute(r)


def lo_allow_ip(ipports, dir):

    a = ipports.split(':')
    ip = a[0]

    if ip == '0.0.0.0':
        ip += '/0'

    if len(a) > 1:
        ports = parse_ports(a[1])
        ports = [':'.join(x) if x.__class__() == () else x for x in ports]
    else:
        ports = None

    if dir == DIR_BI or dir == DIR_IN:
        str1 = ipt + '-t filter -A INPUT -i eth0 '
        str2 = ' -s ' + ip + ' -d ' + my_ip + ' -j ACCEPT'

        if ports != None:
            if ports[0] != '0':
                ports_str = '--sport %s' % ports[0]
            else:
                ports_str = ''

            if len(ports) == 2 and ports[1] != '0':
                ports_str += ' --dport %s' % ports[1]

            lo_execute(str1 + '-p tcp ' + ports_str + str2)
            lo_execute(str1 + '-p udp ' + ports_str + str2)
        else:
            lo_execute(str1 + '-p all' + str2)

    if dir == DIR_BI or dir == DIR_OUT:
        str1 = ipt + '-t filter -A OUTPUT -o eth0 '
        str2 = ' -s ' + my_ip + ' -d ' + ip + ' -j ACCEPT'

        if ports != None:
            if ports[0] != '0':
                ports_str = '--dport %s' % ports[0]
            else:
                ports_str = ''

            if len(ports) == 2 and ports[1] != '0':
                ports_str += ' --sport %s' % ports[1]

            lo_execute(str1 + '-p tcp ' + ports_str + str2)
            lo_execute(str1 + '-p udp ' + ports_str + str2)
        else:
            lo_execute(str1 + '-p all' + str2)


def lo_block_ip(ip, dir):

    if dir == DIR_BI or dir == DIR_IN:
        lo_execute(ipt + '-t filter -I INPUT -i eth0 -p all -s ' + ip + ' -d ' + my_ip + ' -j DROP')
    if dir == DIR_BI or dir == DIR_OUT:
        lo_execute(ipt + '-t filter -I OUTPUT -o eth0 -p all -s ' + my_ip + ' -d ' + ip + ' -j REJECT')


def lo_remove_ip(ip):

    while True:
        todel = lo_execute(ipt + '-t filter -L INPUT -n -v --line-numbers | egrep ' + ip + ' | head -1')
        if len(todel) == 0:
            break
        n = todel.split(None, 1)[0]
        lo_execute(ipt + '-t filter -D INPUT ' + n)

    while True:
        todel = lo_execute(ipt + '-t filter -L OUTPUT -n -v --line-numbers | egrep ' + ip + ' | head -1')
        if len(todel) == 0:
            break
        n = todel.split(None, 1)[0]
        lo_execute(ipt + '-t filter -D OUTPUT ' + n)


# check if the local rules are set for http to communicate with the gateway
def lo_rules_set():

    rules = lo_get_rules()

    if (re.search('0.0.0.0/0 +' + my_ip + ' +state ESTABLISHED', rules) != None or \
        re.search('INPUT \(policy ACCEPT', rules) != None) and \
       (re.search(my_ip + ' +0.0.0.0/0 +tcp dpt:80', rules) != None or \
        re.search('OUTPUT \(policy ACCEPT', rules) != None):
        return True
    else:
        return False
    


#########################################################
# Functions for GATEWAY
#########################################################


def gw_get_ip():
    
    ip = lo_execute('route -n | egrep "^default|^0\.0\.0\.0" | awk \'{print $2}\'').strip()
    if(check_ipv4_fmt(ip)):
        return ip
    else:
        return None


def gw_execute_get(url):

    geturl = BASEURL + gw_ip + url

    if dbg:
        printmsg('# GET ' + geturl, COLOR_NOTE)

    try:
        res = httpobj.open(geturl)
    except urllib2.HTTPError, err:
        printmsg(str(err), COLOR_FAILURE)
        return None
    
    return res.read()
    

def gw_execute_post(url, data):

    posturl = BASEURL + gw_ip + url

    if dbg:
        printmsg('# POST ' + posturl, COLOR_NOTE)
        printmsg('# ' + data, COLOR_NOTE)

    try:
        res = httpobj.open(posturl, data)
    except urllib2.HTTPError, err:
        printmsg(str(err), COLOR_FAILURE)
        return None
    
    return res.read()


def gw_login():

    global pw_retry
    global httpobj
    global logged_in
    global ask_username

    if not lo_rules_set():
        printmsg('ERROR: Can\'t connect to gateway - local rules not set', COLOR_FAILURE)
        return False

    while(pw_retry < PW_MAX_RETRY):
        (user, password) = get_login()

        # get login page for cookies
        try:
            req = urllib2.Request(BASEURL + gw_ip)
            res = urllib2.urlopen(req)
            cookies = cookielib.CookieJar()
            cookies.extract_cookies(res, req)
            cookie_handler = urllib2.HTTPCookieProcessor(cookies)
            httpobj = urllib2.build_opener(cookie_handler)
        except urllib2.URLError:
            printmsg('ERROR: could not connect to %s%s' % (BASEURL, gw_ip), COLOR_FAILURE)
            return False

        login_str = urllib.urlencode({ 'user' : user, 'pass' : password })

        # login
        data = gw_execute_get('/session_login.cgi?page=%%2F&' + login_str)
        if data == None:
            return False

        # check if worked, clear creds if didn't and retry
        if re.search('login failed', data, re.IGNORECASE):
            printmsg('ERROR: login to %s failed' % (gw_ip), COLOR_FAILURE)
            clear_login()
            pw_retry += 1
            continue

        logged_in = True
        save_login(user, password)
        
        return True

    return False


def gw_logout():
    
    global logged_in

    if logged_in:
        gw_execute_get('/session_login.cgi?logout=1')
        logged_in = False


def gw_get_rules():

    global duration

    if not logged_in and not gw_login():
        return None

    data = gw_execute_get('/firewall/index.cgi')
    if data == None:
        return None
    
    data = data.split('\n')

    rules = {}
    def_pol = ''
    processing = False
    tm_re = re.compile('input type=hidden name=duration value=(\d*)>')
    pol_re = re.compile('default action is (\w+)', re.IGNORECASE)

    for line in data:
        if line.startswith('<!-- BEGIN RULES'):
            processing = True
            continue
        
        if processing:
            if line.startswith('END RULES'):
                processing = False
                continue

            values = line.split('&')
            i = int(values[0].split('=')[1])
            rules[i] = {}

            for val in values[1:]:
                [k, v] = val.split('=')
                rules[i][k] = v
        else:
            s = tm_re.search(line)
            if s is not None:
                duration = s.groups()[0]
                
            s = pol_re.search(line)
            if s is not None:
                def_pol = s.groups()[0]

    rules_str = 'Chain FORWARD (policy ' + def_pol + ')\n'
    rules_str += 'num  target   prot  source              destination         options\n'
    keys = rules.keys()
    keys.sort()

    for k in keys:
        rules_str += '%-5d%-9s' % (k, rules[k]['jump'])
        if rules[k]['proto'] != '':
            rules_str += '%-6s' % (rules[k]['proto'])
        else:
            rules_str += 'all   '
        if rules[k]['src'] != '':
            rules_str += '%-20s' % rules[k]['src']
        else:
            rules_str += '%-20s' % '0.0.0.0/0'
        if rules[k]['dest'] != '':
            rules_str += '%-20s' % rules[k]['dest']
        else:
            rules_str += '%-20s' % '0.0.0.0/0'
        if rules[k]['sport'] != '':
            rules_str += 'spt:' + rules[k]['sport'] + ' '
        if rules[k]['dport'] != '':
            rules_str += 'dpt:' + rules[k]['dport'] + ' '
        if rules[k]['state'] != '':
            rules_str += 'state ' + rules[k]['state']
        rules_str += '\n'

    rules_str += 'Duration of rules: ' + duration + ' minutes\n'

    return rules_str


def gw_clear_rules():

    if not logged_in and not gw_login():
        return False

    if gw_execute_get('/firewall/save_policy.cgi?table=0&chain=FORWARD&modip=' + my_ip + '&clear=Clear+All+Rules') == None:
        return False
    if gw_execute_get('/firewall/save_policy.cgi?table=0&chain=FORWARD&modip=' + my_ip + '&clear=1&confirm=Delete+Now') == None:
        return False
    if gw_execute_get('/firewall/index.cgi?reset=1&modip=' + my_ip) == None:
        return False
    if gw_execute_get('/firewall/apply.cgi?table=0&modip=' + my_ip + '&duration=' + duration + '&duration_units=1') == None:
        return False

    return True


def gw_set_default_rules():

    rules = [
        # TCP 80, my_ip -> any, state NEW,ESTABLISHED
        'table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=' + my_ip + '&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=&source_mode=1&source=' + my_ip + '&dest_radio=0&dest_other=&dest_mode=0&dest=' + my_ip + '&frag=0&proto_mode=1&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=1&dport_type=0&dport=80&dport_from=&dport_to=&show_adv=1&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=1&state=NEW&state=ESTABLISHED&tos_mode=0&tos=Minimize-Delay',
        # TCP 443, my_ip -> any, state NEW,ESTABLISHED
        'table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=' + my_ip + '&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=&source_mode=1&source=' + my_ip + '&dest_radio=0&dest_other=&dest_mode=0&dest=' + my_ip + '&frag=0&proto_mode=1&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=1&dport_type=0&dport=443&dport_from=&dport_to=&show_adv=1&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=1&state=NEW&state=ESTABLISHED&tos_mode=0&tos=Minimize-Delay',
        # UDP 53, my_ip -> any, state NEW,ESTABLISHED
        'table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=' + my_ip + '&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=&source_mode=1&source=' + my_ip + '&dest_radio=0&dest_other=&dest_mode=0&dest=' + my_ip + '&frag=0&proto_mode=1&proto=udp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=1&dport_type=0&dport=53&dport_from=&dport_to=&show_adv=1&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=1&state=NEW&state=ESTABLISHED&tos_mode=0&tos=Minimize-Delay',
        # any -> my_ip, state ESTABLISHED
        'table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=' + my_ip + '&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=0&source_other=&source_mode=0&source=' + my_ip + '&dest_radio=on&dest_other=&dest_mode=1&dest=' + my_ip + '&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=1&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=1&state=ESTABLISHED&tos_mode=0&tos=Minimize-Delay',
        ]

    if not logged_in and not gw_login():
        return False

    for r in rules:
        if gw_execute_post('/firewall/save_rule.cgi', r) == None:
            return False

    if gw_execute_get('/firewall/apply.cgi?table=0&modip=' + my_ip + '&duration=' + TIMEOUT + '&duration_units=1') == None:
        return False

    return True
    

def gw_allow_ip(ipports, dir):

    if not logged_in and not gw_login():
        return False

    a = ipports.split(':')
    ip = a[0]

    if len(a) > 1:
        ports = parse_ports(a[1])
    else:
        ports = None
        ports_str = '&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to='
        proto_str = '&proto_mode=0&proto=tcp&proto_other='

    # my_ip -> ip
    if dir == DIR_BI or dir == DIR_OUT:
        str1 = 'table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=' + my_ip + '&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=&source_mode=1&source=' + my_ip

        if ip == '0.0.0.0':
            str1 += '&dest_radio=0&dest_other=&dest_mode=0&dest=' + my_ip
        else:
            str1 += '&dest_radio=on&dest_other=' + ip + '&dest_mode=1&dest=' + ip

        str1 += '&frag=0'
        str2 = '&show_adv=0&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay'

        if ports != None:
            if ports[0].__class__() == ():
                dport_str = '&dport_mode=1&dport_type=1&dport=&dport_from=%s&dport_to=%s' % (ports[0][0], ports[0][1])
            elif ports[0] != '0':
                dport_str = '&dport_mode=1&dport_type=0&dport=%s&dport_from=&dport_to=' % ports[0]
            else:
                dport_str = '&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to='

            if len(ports) == 2:
                if ports[1].__class__() == ():
                    sport_str = '&sport_mode=1&sport_type=1&sport=&sport_from=%s&sport_to=%s' % (ports[1][0], ports[1][1])
                elif ports[1] != '0':
                    sport_str = '&sport_mode=1&sport_type=0&sport=%s&sport_from=&sport_to=' % ports[1]
                else:
                    sport_str = '&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to='
            else:
                sport_str = '&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to='

            proto_str = '&proto_mode=1&proto=tcp&proto_other='
            if gw_execute_post('/firewall/save_rule.cgi', str1 + proto_str + sport_str + dport_str + str2) == None:
                return False
                
            proto_str = '&proto_mode=1&proto=udp&proto_other='
            if gw_execute_post('/firewall/save_rule.cgi', str1 + proto_str + sport_str + dport_str + str2) == None:
                return False
        else:
            if gw_execute_post('/firewall/save_rule.cgi', str1 + proto_str + ports_str + str2) == None:
                return False
    
    # ip -> my_ip
    if dir == DIR_BI or dir == DIR_IN:
        str1 = 'table=0&idx=&new=1&chain=FORWARD&before=&after=&modip=' + my_ip + '&cmt=&jump=ACCEPT&rwithdef=1&rwithtype=icmp-net-unreachable'

        if ip == '0.0.0.0':
            str1 += '&source_radio=0&source_other=&source_mode=0&source=' + my_ip
        else:
            str1 += '&source_radio=on&source_other=' + ip + '&source_mode=1&source=' + ip

        str1 += '&dest_radio=on&dest_other=&dest_mode=1&dest=' + my_ip + '&frag=0'
        str2 = '&show_adv=0&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay'

        if ports != None:
            if ports[0].__class__() == ():
                sport_str = '&sport_mode=1&sport_type=1&sport=&sport_from=%s&sport_to=%s' % (ports[0][0], ports[0][1])
            elif ports[0] != '0':
                sport_str = '&sport_mode=1&sport_type=0&sport=%s&sport_from=&sport_to=' % ports[0]
            else:
                sport_str = '&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to='

            if len(ports) == 2:
                if ports[1].__class__() == ():
                    dport_str = '&dport_mode=1&dport_type=1&dport=&dport_from=%s&dport_to=%s' % (ports[1][0], ports[1][1])
                elif ports[1] != '0':
                    dport_str = '&dport_mode=1&dport_type=0&dport=%s&dport_from=&dport_to=' % ports[1]
                else:
                    dport_str = '&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to='
            else:
                dport_str = '&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to='

            proto_str = '&proto_mode=1&proto=tcp&proto_other='
            if gw_execute_post('/firewall/save_rule.cgi', str1 + proto_str + sport_str + dport_str + str2) == None:
                return False

            proto_str = '&proto_mode=1&proto=udp&proto_other='
            if gw_execute_post('/firewall/save_rule.cgi', str1 + proto_str + sport_str + dport_str + str2) == None:
                return False
        else:
            if gw_execute_post('/firewall/save_rule.cgi', str1 + proto_str + ports_str + str2) == None:
                return False

    # apply rules
    if gw_execute_get('/firewall/apply.cgi?table=0&modip=' + my_ip + '&duration=' + duration + '&duration_units=1') == None:
        return False

    return True


def gw_block_ip(ip, dir):

    if not logged_in and not gw_login():
        return False

    # my_ip -> ip
    if dir == DIR_BI or dir == DIR_OUT:
        data = gw_execute_post('/firewall/save_rule.cgi', 'table=0&idx=&new=1&chain=FORWARD&before=0&after=&modip=' + my_ip + '&cmt=&jump=REJECT&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=&source_mode=1&source=' + my_ip + '&dest_radio=on&dest_other=' + ip + '&dest_mode=1&dest=' + ip + '&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=0&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay')
        if data == None:
            return False
    
    # ip -> my_ip
    if dir == DIR_BI or dir == DIR_IN:
        data = gw_execute_post('/firewall/save_rule.cgi', 'table=0&idx=&new=1&chain=FORWARD&before=0&after=&modip=' + my_ip + '&cmt=&jump=DROP&rwithdef=1&rwithtype=icmp-net-unreachable&source_radio=on&source_other=' + ip + '&source_mode=1&source=' + ip + '&dest_radio=on&dest_other=&dest_mode=1&dest=' + my_ip + '&frag=0&proto_mode=0&proto=tcp&proto_other=&sport_mode=0&sport_type=0&sport=&sport_from=&sport_to=&dport_mode=0&dport_type=0&dport=&dport_from=&dport_to=&show_adv=0&tcpflags_mode=0&tcpoption_mode=0&tcpoption=&icmptype_mode=0&icmptype=any&macsource_mode=0&macsource=&limit_mode=0&limit0=&limit1=second&limitburst_mode=0&limitburst=&state_mode=0&tos_mode=0&tos=Minimize-Delay')
        if data == None:
            return False
    
    # apply rules
    if gw_execute_get('/firewall/apply.cgi?table=0&modip=' + my_ip + '&duration=' + duration + '&duration_units=1') == None:
        return False

    return True


def gw_remove_ip(ip):
    
    to_rem = ''
    
    if not logged_in and not gw_login():
        return False

    rules = gw_get_rules()
    if rules is None:
        return False

    for r in rules.split('\n'):
        if re.search(ip, r) is not None:
            to_rem += 'd=%s&' % (r.split(' ')[0])
    
    if to_rem != '':
        if gw_execute_get('/firewall/save_policy.cgi?table=0&modip=' + my_ip + '&chain=FORWARD&' + to_rem + 'delsel=Delete+Selected') == None:
            return False
        if gw_execute_get('/firewall/apply.cgi?table=0&modip=' + my_ip + '&duration=' + duration + '&duration_units=1') == None:
            return False

    return True


def gw_set_timeout():

    if not logged_in and not gw_login():
        return False

    if gw_execute_get('/firewall/apply.cgi?table=0&modip=' + my_ip + '&duration=' + duration + '&duration_units=1') == None:
        return False

    return True



#########################################################
# Other Functions
#########################################################


# allows ex. 1.1.1.1
def check_ipv4_fmt(ip):
    
    if re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) != None:
        return True
    return False


# allows ex. 1.1.1.1:22-33,44-55
def check_ipv4_port_fmt(ip):

    if re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d{1,5}(-\d{1,5})?(,\d{1,5}(-\d{1,5})?)?)?$', ip) != None:
        return True
    return False


# allows ex. 1.1.1.0/24
def check_ipv4_cidr_fmt(ip):

    if re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$', ip) != None:
        return True
    return False


# converts "100,200-300,400" to [ 100, (200, 300), 400 ]
def parse_ports(port_str):

    port_list = []
    ports = port_str.split(',')
    ports = [x for x in ports if x != '']

    for p in ports:
        a = p.split('-')
        if len(a) == 1:
            port_list.append(a[0])
        elif len(a) == 2:
            port_list.append((a[0], a[1]))

    return port_list


def set_hostvar(hv, val):

    lo_execute('perl -e \'require "%s";newhostvar("%s","%s");\'' % (autoutils, hv, re.escape(val)))


def get_hostvar(hv):

    # use grep/awk because can't get the escaping correct with special chars
    #var = lo_execute('perl -e \'require "%s";print "$%s";\'' % (hostvars, hv))
    var = lo_execute('egrep "%s" %s | awk \'{print $3}\' | awk -F\\" \'{print $2}\'' % (hv, hostvars)).strip()
    
    return re.sub(r'([^\\])\\([^\\])', r'\1\2', var)


def get_login():

    user = config['user']
    password = config['password']

    try:
        while user == '':
            if not ask_username:
                user = get_hostvar('gbl_opuser')
                if user == '':
                    sys.stderr.write('username: ')
                    user = raw_input()
            else:
                sys.stderr.write('username: ')
                user = raw_input()

        printmsg('Logging in with user \'%s\'' % (user), COLOR_NOTE)
    
        if password == '' and user != 'user':
            password = get_hostvar('gbl_oppasswd')
            if password == '':
                password = getpass.getpass('password: ', sys.stderr)
    except EOFError:
        printmsg('\nLogin cancelled. Exiting.', COLOR_FAILURE)
        sys.exit(1)
    except KeyboardInterrupt:
        printmsg('\nLogin cancelled. Exiting.', COLOR_FAILURE)
        sys.exit(1)

    return (user, password)


def clear_login():

    global ask_username
    global config

    ask_username = True
    config['user'] = ''
    config['password'] = ''
    write_config(config)


def save_login(user, password):

    global ask_username
    global config
    
    ask_username = False
    config['user'] = user
    config['password'] = password
    write_config(config)


def read_config():

    tmpconfig = {}
    
    try:
        file = open(configfile, 'r')
        lines = file.readlines()
        file.close()

        for line in lines:
            line = line.strip()
            s = line.split(None, 1)
            if len(s) == 2:
                tmpconfig[s[0]] = s[1]
    except:
        return {}

    return tmpconfig


def write_config(conf):
    
    try:
        file = open(configfile, 'w')
        for k,v in conf.iteritems():
            if v != '':
                file.write('%s %s\n' % (k, v))
        file.close()
    except:
        printmsg('WARNING: Could not save configuration', COLOR_FAILURE)


def write_alarm(alarm_file, alarm_sleep_file, timeout_mins):

    expires = time.ctime(time.time() + (timeout_mins * 60))
    sleep_secs = (timeout_mins - 30) * 60

    if sleep_secs < 0:
        return False

    # build alarm_file
    script = '#!/bin/sh\n'
    script += '/bin/rm -f $0\n'
    script += 'EXPIRES="' + expires + '"\n'
    script += 'while [ 1 ]; do\n'
    script += '  clear\n'
    script += '  echo -e "\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\a"\n'
    script += '  echo -e "Current time: `date`\\n\\n\\n"\n'
    script += '  [ "$EXPIRES" ] && echo -e "EXPIRES time: $EXPIRES\\n\\n\\n"\n'
    script += '  echo -e "Your firewall rules will expire in 30 minutes.\\n\\n"\n'
    script += '  echo -e "If necessary, use \\"fwrules.py -t 3h\\" to give 3 more hrs,\\n"\n'
    script += '  echo -e "or use the browser GUI to add more time.\\n\\n"\n'
    script += '  echo -e "\\n\\n\\n\\n\\n\\n"\n'
    script += '  echo "^C or close this window as desired, but this alarm has no snooze!"\n'
    script += '  sleep 5\n'
    script += 'done\n'

    f = open(alarm_file, 'w')
    f.write(script)
    f.close()

    # build alarm_sleep_file
    script = '#!/bin/sh\n'
    script += '/bin/rm -f $0\n'
    script += 'chmod 0777 ' + alarm_file + '\n'
    script += 'sleep ' + str(sleep_secs) + '\n'
    script += 'exec xterm -ut +cm +cn -sk -sb -ls -title ALARM '
    script += '-geometry 174x52-53+26 -bg white -fg red -e '
    script += alarm_file + '\n'

    f = open(alarm_sleep_file, 'w')
    f.write(script)
    f.close()
    os.system('chmod 0777 ' + alarm_sleep_file)

    return True


def start_alarm(timeout):

        kill_alarms('FW_Alarm')
        if write_alarm('/tmp/FW_Alarm.sh', '/tmp/FW_AlarmSleep.sh', timeout):
            os.system('/tmp/FW_AlarmSleep.sh&')


def kill_alarms(alarm_grep):
    
    ps_line = lo_execute('ps -ef | grep ' + alarm_grep + ' | egrep -v grep')
    
    if len(ps_line) > 0:
        lo_execute('pkill ' + alarm_grep)


def printmsg(msg, color=COLOR_NORMAL):
    
    logit(msg)

    if color == COLOR_NORMAL:
        print msg
    else:
        print '%s%s%s' % (color, msg, COLOR_NORMAL)


def logit(msg):

    prog = os.path.basename(sys.argv[0])
    pid = os.getpid()
    currtime = time.strftime('%Y-%m-%d %H:%M:%S')
    outstr = '%s %s[%d]: %s\n' % (currtime, prog, pid, msg)

    try:
        f = open(logfile, 'a')
    except:
        printmsg('ERROR: Cannot open logfile', COLOR_FAILURE)
        return

    f.write(outstr)
    f.close()


def usage(prog):
    
    prog = os.path.basename(prog)

    print 'usage: ' + prog + ' [-dplSRF] [-L|-u] [-s|-c|-r] [-t <timeout>] [[-I|-O] -A|-D|-B ...]'
    print '  helpful options:'
    print '    -h             show this help'
    print '    -v             print the version and exit'
    print '    -d             debug, print the commands being executed'
    print '    -p             print the table (if running with other options, will print at the end)'
    print '    -l             only perform actions on the LOCAL iptables firewall'
    print '    -L             same as "-l", but remembers for subsequent runs'
    print '    -u             unremember "-L" option, i.e. operate on both local and external firewalls'
    print '  logging in:'
    print '    -U USER        specify the firewall login username'
    print '    -P PASS        specify the firewall login password'
    print '  setting rules:'
    print '    -s             sets the default rules (allow Web/DNS/ICMP, drop all else)'
    print '    -c             clear all rules and exits (still allows all on eth1 and eth2)'
    print '    -r             reset the rules (clears then sets)'
    print '  local only options:'
    print '    -S FILE        save the LOCAL iptables rules to FILE, does this first'
    print '    -R FILE        restore the LOCAL iptables rules from FILE, does this first (or after save)'
    print '    -F             flush LOCAL tables and allow all, then exit'
    print '  modify firewall rules:'
    print '    -t TIMEOUT     set the gateway timeout in hours, or like 300m for mins (max is 8h)'
    print '    -I             only set rule for inbound traffic'
    print '    -O             only set rule for outbound traffic'
    print '    -A IP[:DSTPORT[,SRCPORT]]'
    print '                   allows all traffic to and from IP on eth0'
    print '                   DSTPORT and SRCPORT can each be a single port or range or "0" for any port'
    print '                   call-in ex: 192.168.1.1:80 or 192.168.1.1:80,3000-4000'
    print '                   callback ex: 192.168.1.1:0,80 or 192.168.1.1:30000-65000,80'
    print '    -B IP[/MASK]   blocks traffic to and from IP or network'
    print '                   MASK is the short notation, range 1-32'
    print '    -D IP          deletes all rules with IP'
    print '\n'



#########################################################
# Main
#########################################################


def main():
    
    global dbg
    global my_ip
    global gw_ip
    global logged_in
    global duration
    global config

    print_it = False
    reset = False
    clear = False
    set = False
    newuser = False
    newpass = False
    addips = []
    delips = []
    blkips = []
    set_timeout = False
    duration = TIMEOUT
    logged_in = False
    save_file = None
    restore_file = None
    local_only = False
    local_only_all = False
    local_only_all_u = False
    flush = False
    dir = DIR_BI
    retcode = 0

    # log this call
    ppid = os.getppid()
    pname = lo_execute('ps -p %d -o comm=' % ppid).rstrip()
    args = ' '.join(sys.argv)
    logit('Called by %s[%d] as \'%s\'' % (pname, ppid, args))
    
    config = read_config()

    if not config.has_key('user'):
        config['user'] = 'user'
    if not config.has_key('password'):
        config['password'] = ''
    if not config.has_key('local'):
        config['local'] = 'false'

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvdlLuU:P:pscrS:R:Ft:A:B:D:IO')
    except getopt.GetoptError, err:
        printmsg(str(err), COLOR_FAILURE)
        usage(sys.argv[0])
        sys.exit(1)

    if len(opts) == 0:
        usage(sys.argv[0])
        sys.exit(1)
        
    for o, a in opts:
        if o == '-h':
            usage(sys.argv[0])
            sys.exit(0)
        elif o == '-v':
            printmsg('%s version %s' % (os.path.basename(sys.argv[0]), version))
            sys.exit(0)
        elif o == '-p':
            print_it = True
        elif o == '-l':
            local_only = True
        elif o == '-L':
            local_only = True
            local_only_all = True
        elif o == '-u':
            local_only_all_u = True
        elif o == '-r':
            reset = True
        elif o == '-A':
            addips.append(a)
        elif o == '-D':
            delips.append(a)
        elif o == '-B':
            blkips.append(a)
        elif o == '-I':
            if dir == DIR_OUT:
                dir = DIR_BI
            else:
                dir = DIR_IN
        elif o == '-O':
            if dir == DIR_IN:
                dir = DIR_BI
            else:
                dir = DIR_OUT
        elif o == '-d':
            dbg = True
        elif o == '-c':
            clear = True
        elif o == '-t':
            if re.match('^\d+[mh]?$', a) is None:
                printmsg('ERROR: bad timeout format', COLOR_FAILURE)
                sys.exit(1)
            if a[-1] == 'm':
                duration = a[:-1]
            elif a[-1] == 'h':
                duration = str(int(a[:-1]) * 60)
            else:
                duration = str(int(a) * 60)
            if int(duration) > 480:
                printmsg('ERROR: timeout max is 480m or 8h', COLOR_FAILURE)
                sys.exit(1)
            set_timeout = True
        elif o == '-s':
            set = True
        elif o == '-U':
            newuser = True
            config['user'] = a
        elif o == '-P':
            newpass = True
            config['password'] = a
        elif o == '-S':
            save_file = a
        elif o == '-R':
            restore_file = a
        elif o == '-F':
            flush = True

    if local_only_all and local_only_all_u:
        printmsg('ERROR: Only either -L or -u can be specified, not both.', COLOR_FAILURE)
        sys.exit(1)

    if (clear or set or reset) and not ((clear and not set and not reset) or
                                        (not clear and set and not reset) or
                                        (not clear and not set and reset)):
        printmsg('ERROR: Only one of -s, -c, and -r can be specified', COLOR_FAILURE)
        sys.exit(1)

    if os.uname()[0] != 'Linux':
        printmsg('ERROR: This script is only meant to be run in Linux.', COLOR_FAILURE)
        sys.exit(1)

    for ip in addips:
        if not check_ipv4_port_fmt(ip):
            printmsg('ERROR: invalid IP address format [%s]' % (ip), COLOR_FAILURE)
            sys.exit(1)
    for ip in delips:
        if not check_ipv4_fmt(ip):
            printmsg('ERROR: invalid IP address format [%s]' % (ip), COLOR_FAILURE)
            sys.exit(1)
    for ip in blkips:
        if not check_ipv4_fmt(ip) and not check_ipv4_cidr_fmt(ip):
            printmsg('ERROR: invalid IP address format [%s]' % (ip), COLOR_FAILURE)
            sys.exit(1)

    # clear the password if setting a new user
    if newuser and not newpass:
        config['password'] = ''

    if local_only_all:
        config['local'] = 'true'
    elif local_only_all_u:
        config['local'] = 'false'

    if config['local'] == 'true':
        local_only = True

    my_ip = lo_get_ip('eth0')
    if my_ip is None and not local_only:
        printmsg('ERROR: Could not get IP address for eth0', COLOR_FAILURE)
        sys.exit(1)

    if not local_only:
        gw_ip = gw_get_ip()
        if gw_ip is None:
            printmsg('ERROR: Could not get IP address for the gateway', COLOR_FAILURE)
            sys.exit(1)

    if save_file != None:
        lo_execute('%s > %s' % (iptsave, save_file))

    if restore_file != None:
        if os.path.exists(restore_file):
            lo_execute('%s < %s' % (iptrestore, restore_file))
        else:
            printmsg('ERROR: Could not restore rules - file does not exist', COLOR_FAILURE)
            retcode = 1

    if flush:
        printmsg('Flushing all rules and setting policies to ACCEPT', COLOR_FAILURE)
        lo_flush_accept()
        sys.exit(retcode)

    if clear:
        printmsg('Removing firewall rules')
        if not local_only and gw_clear_rules() == False:
            printmsg('')
            printmsg('!!! COULD NOT CLEAR GATEWAY RULES !!!', COLOR_FAILURE)
            printmsg('To fix this, try running "fwrules.py -s" then "fwrules.py -c" again,', COLOR_FAILURE)
            printmsg('or use "-U <username>" and "-P <password>" with a new login if it failed.', COLOR_FAILURE)
            printmsg('')
            retcode = 1
        lo_clear_rules()
        lo_set_local_rules()

        if print_it:
            printmsg('Local iptables rules:\n', COLOR_NOTE)
            printmsg(lo_get_rules(), COLOR_NORMAL)

        kill_alarms('FW_Alarm')
        printmsg('Done')
        sys.exit(retcode)

    if set or reset:
        printmsg('Setting default firewall rules')
        lo_clear_rules()
        lo_set_default_rules()
        if not local_only:
            if gw_clear_rules() == False or gw_set_default_rules() == False:
                printmsg('')
                printmsg('!!! Could not set default gateway rules !!!', COLOR_FAILURE)
                printmsg('You\'ll need to run "fwrules.py -s" again with the correct login', COLOR_FAILURE)
                printmsg('and make sure your default gateway is correct.', COLOR_FAILURE)
                printmsg('')
                retcode = 1
            else:
                start_alarm(int(duration))
        printmsg('Done.')

    # need to get rules first to get the current timeout (if adding rules)
    if not local_only and (len(addips) + len(blkips) + len(delips)) > 0:
        if gw_get_rules() == None:
            printmsg('Error getting rules on gateway.', COLOR_FAILURE)
            sys.exit(1)

    for ip in addips:
        printmsg('Allowing traffic to/from ' + ip)
        if not local_only:
            if gw_allow_ip(ip, dir):
                lo_allow_ip(ip, dir)
            else:
                printmsg('Error setting rule on gateway.', COLOR_FAILURE)
                sys.exit(1)
        else:
            lo_allow_ip(ip, dir)
        printmsg('Done.')

    for ip in blkips:
        printmsg('Blocking all traffic to/from ' + ip)
        if not local_only and not check_ipv4_cidr_fmt(ip):
            if gw_block_ip(ip, dir):
                lo_block_ip(ip, dir)
            else:
                printmsg('Error setting rule on gateway.', COLOR_FAILURE)
                sys.exit(1)
        else:
            lo_block_ip(ip, dir)
        printmsg('Done.')

    for ip in delips:
        printmsg('Removing rule for ' + ip)
        if not local_only and not check_ipv4_cidr_fmt(ip):
            if not gw_remove_ip(ip):
                printmsg('Error removing rule on gateway.', COLOR_FAILURE)
                retcode = 1
        lo_remove_ip(ip)
        printmsg('Done.')

    if set_timeout:
        if gw_set_timeout():
            start_alarm(int(duration))
            printmsg('Timeout set to %s minutes.' % (duration))
        else:
            printmsg('Setting timeout failed.', COLOR_FAILURE)

    if print_it:
        printmsg('Local iptables rules:\n', COLOR_NOTE)
        printmsg(lo_get_rules())
        if not local_only:
            printmsg('Gateway firewall rules:\n', COLOR_NOTE)
            printmsg(gw_get_rules())

    if not local_only:
        gw_logout()

    write_config(config)
    
    sys.exit(retcode)


if __name__ == '__main__':
    main()
