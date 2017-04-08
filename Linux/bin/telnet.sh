#!/bin/sh
# Wrapper script for spawn.
#v1.0.1.1
#export SU HIDEME HIDECON LD_PRELOAD
echo -e "\n==============="
echo $0: The spawn/telnet wrapper v1.0.1.1
echo -e "\n==============="
echo -e "\n\nENVIRONMENT:"
echo -e "env  | egrep \"(RA|RP|CMD|SU|HIDE|LD_PRELOAD|NOPEN).*=\""
env  | egrep "(RA|RP|CMD|SU|HIDE|LD_PRELOAD|NOPEN).*="
echo -e "\n==============="
unset SPAWN FTSHELL TELNETMODE FORCEDPORT
type spawn && [ ! "$NOSPAWN" ] && SPAWN=spawn
type ftshell && FTSHELL=ftshell
[ "$2" = "23" ] && [ "$3" = "" ] && TELNETMODE=telnet
BASE=`basename $0`
[ "$BASE" = "telnet" ] && [ "$2" = "23" -o "$2" = "" ] && TELNETMODE=telnet
if [ "x$SPAWN" = "x" ] ; then
  [ -x /usr/bin/telnet ] && SPAWN=/usr/bin/telnet
fi
[ "$TELNETMODE" ] && [ ! "$2" ] && FORCEDPORT=23
[ "$NOTELNETMODE" ] && unset TELNETMODE
[ "$SPAWN" = "/usr/bin/telnet" ] && unset TELNETMODE
[ "$3" = "telnet" ] && unset TELNETMODE
if [ ! "${WINTYPE:0:7}" = "JACKPOP" -a ! "$BASE" = "spawn" ] ; then
   echo -e  "\n\n\nWARNING: You are about to use $SPAWN as your $BASE client via:\n\n\t\t$SPAWN $* $FORCEDPORT $TELNETMODE
\n"
   echo -en "\a         Are you sure you want to? [N] "
   read ans
   [ "x$ans" = "x" -o "${ans:0:1}" = "n" -o "${ans:0:1}" = "N" ] && \
      echo -e "\n\nUse /usr/bin/telnet if you do not want spawn.\n\n" &&  \
      exit 1
fi
# never mind---ftshell doesn't seem to play nice inside scripme windows
unset FTSHELL
echo -e "\n==============="
echo -e "\ndate -u\n"`date -u`"\n===============\n"
echo $0 wrapper execing: $FTSHELL $SPAWN $* $TELNETMODE
exec $FTSHELL $SPAWN $* $FORCEDPORT $TELNETMODE
