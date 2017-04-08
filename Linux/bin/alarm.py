#!/usr/bin/env python
version = "1.0.0.1"

###############################################################################
#
# 17 Mar 2011
#
# A commandline script to build and run an alarm script. When alarm expires,
# an xterm is exec'd to show alarm content.
#
###############################################################################

import os
import sys
import re
import getopt
import time


#########################################################
# CONFIGURATION
#########################################################

# 
TIMEOUT = '360'


# Other
dbg = False



#########################################################
# Functions for LOCAL ops box
#########################################################




def lo_execute(cmd):
    
    if dbg:
        print '# ' + cmd
    
    outfile = os.tmpfile()
    proc = subprocess.Popen(cmd, stdout=outfile, shell=True)
    proc.wait()
    outfile.seek(0)
    output = outfile.read()
    outfile.close()

    return output


def lo_get_rules():

    return lo_execute(ipt + '-L -n -v --line-numbers')


def lo_clear_rules():
    
    lo_execute(ipt + '-F')


def lo_set_default_rules():
    
    in_rules = [
        ipt + '-t filter -P INPUT DROP',
        ipt + '-t filter -A INPUT -i lo -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth1 -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth0 -p tcp -s 0.0.0.0/0 -d ' + ext_ip + ' --sport 80 -m state --state ESTABLISHED -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth0 -p tcp -s 0.0.0.0/0 -d ' + ext_ip + ' --sport 443 -m state --state ESTABLISHED -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth0 -p udp -s 0.0.0.0/0 -d ' + ext_ip + ' --sport 53 -m state --state ESTABLISHED -j ACCEPT',
        ipt + '-t filter -A INPUT -i eth0 -p icmp -s 0.0.0.0/0 -d ' + ext_ip + ' -m state --state ESTABLISHED,RELATED -j ACCEPT'
        ]
    out_rules = [
        ipt + '-t filter -P OUTPUT DROP',
        ipt + '-t filter -A OUTPUT -o lo -j ACCEPT',
        ipt + '-t filter -A OUTPUT -o eth1 -j ACCEPT',
        ipt + '-t filter -A OUTPUT -o eth0 -p tcp -s ' + ext_ip + ' -d 0.0.0.0/0 --dport 80 -j ACCEPT -m state --state NEW,ESTABLISHED',
        ipt + '-t filter -A OUTPUT -o eth0 -p tcp -s ' + ext_ip + ' -d 0.0.0.0/0 --dport 443 -j ACCEPT -m state --state NEW,ESTABLISHED',
        ipt + '-t filter -A OUTPUT -o eth0 -p udp -s ' + ext_ip + ' -d 0.0.0.0/0 --dport 53 -j ACCEPT',
        ipt + '-t filter -A OUTPUT -o eth0 -p icmp -s ' + ext_ip + ' -d 0.0.0.0/0 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT'
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


def lo_allow_ip(ip):
    
    lo_execute(ipt + '-t filter -A INPUT -i eth0 -p all -s ' + ip + ' -d ' + ext_ip + ' -j ACCEPT')
    lo_execute(ipt + '-t filter -A OUTPUT -p all -s ' + ext_ip + ' -d ' + ip + ' -j ACCEPT')


def lo_remove_ip(ip):
    
    lo_execute(ipt + '-t filter -D INPUT -i eth0 -p all -s ' + ip + ' -d ' + ext_ip + ' -j ACCEPT')
    lo_execute(ipt + '-t filter -D OUTPUT -p all -s ' + ext_ip + ' -d ' + ip + ' -j ACCEPT')


# check if the local rules are set for http to communicate with
# the gateway
def lo_rules_set():

    rules = lo_get_rules()

    if re.search('0.0.0.0/0 +' + ext_ip + ' +tcp spt:80', rules) != None and \
            re.search(ext_ip + ' +0.0.0.0/0 +tcp dpt:80', rules) != None:
        return True
    else:
        return False
    


#########################################################
# Other Functions
#########################################################


def check_ipv4_fmt(ip):
    
    if re.match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) != None:
        return True
    else:
        return False


def get_login():

    global user
    global password

    if user == '':
        user = lo_execute('perl -e \'require ' + 
                          '"/current/down/hostvars.global";' +
                          'print "$gbl_opuser";\'')
        if user == '':
            user = raw_input('username: ')

    if password == '':
        password = lo_execute('perl -e \'require ' +
                              '"/current/down/hostvars.global";' + 
                              'print "$gbl_oppasswd";\'')
        if password == '':
            password = getpass.getpass('password: ')

    return (user, password)


def write_alarm(alarm_file, alarm_sleep_file, timeout_mins):

    expires = time.ctime(time.time() + (timeout_mins * 60))
    sleep_secs = (timeout_mins - 30) * 60

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
    script += '  echo -e "If necessary, use \\"fwrules.py -t <timeout>\\" to re-set it,\\n"\n'
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


def start_alarm(timeout):

        kill_alarms('Alarm')
        write_alarm('/tmp/Alarm.sh', '/tmp/AlarmSleep.sh', timeout)
        os.system('/tmp/AlarmSleep.sh&')


def kill_alarms(alarm_grep):
    
    ps_line = lo_execute('ps -ef | grep ' + alarm_grep + ' | egrep -v grep')
    
    if len(ps_line) > 0:
        lo_execute('pkill ' + alarm_grep)


def usage(prog):
    
    prog = prog.split(os.sep)[-1]

    print 'usage: ' + prog + ' [-t <timeout>] [-f content]'
    print '  options:'
    print '    -h             show this help'
    print '    -v             print the version and exit'
    print '    -d             debug, print the commands being executed'
    print '    -t <timeout>   set the alarm timeout           ['
    print '\n'



#########################################################
# Main
#########################################################


def main():
    
    global dbg
    global ext_ip
    global int_ip
    global gw_ip
    global logged_in
    global duration
    global user
    global password

    user = ''
    password = ''
    print_it = False
    reset = False
    clear = False
    set = False
    ipaddr = None
    addrule = False
    set_timeout = False
    duration = TIMEOUT
    logged_in = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvdU:P:pscrt:A:D:')
    except getopt.GetoptError, err:
        print str(err)
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
            print '%s version %s' % (sys.argv[0].split(os.sep)[-1], version)
            sys.exit(0)
        elif o == '-p':
            print_it = True
        elif o == '-r':
            reset = True
        elif o == '-A':
            if ipaddr is not None:
                print 'ERROR: either -A or -D can be specified, not both'
                sys.exit(1)
            ipaddr = a
            addrule = True
        elif o == '-D':
            if ipaddr is not None:
                print 'ERROR: either -A or -D can be specified, not both'
                sys.exit(1)
            ipaddr = a
            addrule = False
        elif o == '-d':
            dbg = True
        elif o == '-c':
            clear = True
        elif o == '-t':
            if re.match('^\d+[mh]?$', a) is None:
                print 'ERROR: bad timeout format'
                sys.exit(1)
            if a[-1] == 'm':
                duration = a[:-1]
            elif a[-1] == 'h':
                duration = str(int(a[:-1]) * 60)
            else:
                duration = str(int(a) * 60)
            if int(duration) > 480:
                print 'ERROR: timeout max is 480m or 8h'
                sys.exit(1)
            set_timeout = True
        elif o == '-s':
            set = True
        elif o == '-U':
            user = a
        elif o == '-P':
            password = a

    if (clear or set or reset) and not ((clear and not set and not reset) or
                                        (not clear and set and not reset) or
                                        (not clear and not set and reset)):
        print 'ERROR: Only one of -s, -c, and -r can be specified'
        sys.exit(1)

    if lo_execute('uname -s').strip() != 'Linux':
        print 'ERROR: This script is only meant to be run in Linux.'
        sys.exit(1)

    if ipaddr != None and not check_ipv4_fmt(ipaddr):
        print 'ERROR: invalid IP address format'
        sys.exit(1)

    ext_ip = lo_get_ip('eth0')
    if ext_ip is None:
        print 'ERROR: Could not get IP address for eth0'
        sys.exit(1)

    int_ip = lo_get_ip('eth1')
    if int_ip is None:
        print 'ERROR: Could not get IP address for eth1'
        sys.exit(1)

    gw_ip = gw_get_ip()
    if gw_ip is None:
        print 'ERROR: Could not get IP address for the gateway'
        sys.exit(1)

    if clear:
        print 'Removing firewall rules'
        gw_clear_rules()
        lo_clear_rules()
        if print_it:
            print gw_get_rules()
            print lo_get_rules()
        sys.exit(1)

    if set or reset:
        if reset:
            print 'Removing firewall rules'
            gw_clear_rules()
            lo_clear_rules()

        print 'Setting default firewall rules'
        lo_set_default_rules()
        gw_set_default_rules()
        start_alarm(int(duration))

    if ipaddr is not None and addrule and lo_rules_set():
        print 'Allowing all traffic to/from ' + ipaddr
        gw_get_rules()
        gw_allow_ip(ipaddr)
        lo_allow_ip(ipaddr)
    elif ipaddr is not None and not addrule and lo_rules_set():
        print 'Removing rule for ' + ipaddr
        gw_get_rules()
        gw_remove_ip(ipaddr)
        lo_remove_ip(ipaddr)

    if set_timeout:
        gw_set_timeout()
        start_alarm(int(duration))

    if print_it:
        print 'Local iptables rules:\n'
        print lo_get_rules()
        print 'Gateway firewall rules:\n'
        print gw_get_rules()

    gw_logout()


if __name__ == '__main__':
    main()
