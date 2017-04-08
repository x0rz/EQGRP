echo spool $1_sch.txt
echo @sch.sql $1 
echo spool off
echo @s1.sql $1
echo set termout off
echo spool $1_sam.txt
echo set echo on
echo @s3.sql
echo spool off
echo set echo off
echo set pagesize 55
echo set linesize 80
echo set arraysize 15
echo set maxdata 60000
echo set termout on

