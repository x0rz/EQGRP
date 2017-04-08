echo connect / as sysdba
echo "set echo off"
echo set heading off
echo set pagesize 1000
echo set trimout on
echo set trimspool on
echo set feedback off
echo set verify off
echo 
echo spool $1_tables.txt
echo "prompt TABLES=("
echo "select table_name || ','"
echo from all_tables
echo where owner=upper\(\'$1\'\)
echo "order by table_name;"
echo "prompt )"
echo spool off
echo 
