#!/bin/bash
	echo "Use ^c twice to stop ./jl.command..."
	echo "   1 for nc, 1 for while loop"
	while true; do
		port=$RANDOM
		echo
		echo "---> Listening on $port <---"
		echo
		echo $port  > /projects/etk/implants/jackladder/bin/.PORT
		echo $(tty) > /projects/etk/implants/jackladder/bin/.TTY
		nc -l -p $port
		sleep 2
	done
