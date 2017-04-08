echo connect / as sysdba
echo spool $4_$1_idb.txt
echo @idb.sql $2-$3
echo spool off
