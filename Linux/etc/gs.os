#NOGS
-lsh if  [ "$NOPEN_SERVERINFO" ] ; then  echo $NOPEN_SERVERINFO ;  else  grep "^OS:" /current/down/hostinfo.$NOPEN_RHOSTNAME ; fi -nohist
