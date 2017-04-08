set echo off
set pagesize 9999
set linesize 1000
set verify off
set trimspool on
set trimout on
set feedback 6
set recsep off
set maxdata 60000
set numwidth 20
set longchunk 60000
set long 9999999
set termout on
set arraysize 3
set escape ~
set heading on

ttitle "Passwords" skip, skip
column username format a25
column password format a25
select username, password from dba_users order by username;

prompt
prompt
prompt NLS Parameters:
prompt ---------------

prompt
ttitle "Session Parameters" skip, skip
column  parameter format a31
column  value format a41
select * from NLS_SESSION_PARAMETERS;

prompt
ttitle "Instance Parameters" skip, skip
select * from NLS_INSTANCE_PARAMETERS;
prompt

prompt
ttitle "Database Parameters" skip, skip
select * from NLS_DATABASE_PARAMETERS;
prompt
prompt
prompt


ttitle off
set heading off
set termout off

clear breaks
clear columns
clear computes

col a fold_after

spool getr2.sql
select 'set termout off' a, 
'spool r2_' || owner || '.sql' a, 
'prompt connect / as SYSDBA' a,
'prompt set termout off' a,
'prompt @s1.sql ' || owner a, 
'prompt set termout off' a, 
'prompt spool ' || owner || '_sam.txt' a, 
'prompt set echo on' a, 
'prompt @s2.sql' a, 
'prompt spool off' a, 
'prompt set echo off' a, 
'prompt set pagesize 55' a, 
'prompt set linesize 80' a, 
'prompt set arraysize 15' a, 
'prompt set maxdata 60000' a, 
'prompt set termout on' a, 
'spool off' a, 
'set termout on'
from dba_objects
where owner != 'SYS' AND 
      owner != 'SYSTEM' AND
      owner != 'ANONYMOUS' AND
      owner != 'APEX_PUBLIC_USER' AND
      owner != 'AURORA$JIS$UTILITY$' AND
      owner != 'AURORA$ORB$UNAUTHENTICATED' AND
      owner != 'BI' AND
      owner != 'CTXSYS' AND
      owner != 'DBADMIN' AND 
      owner != 'DBSNMP' AND
      owner != 'DEMO' AND
      owner != 'DIP' AND
      owner != 'DMSYS' AND
      owner != 'DRSYS' AND
      owner != 'EXFSYS' AND
      owner != 'FLOWS_030000' AND
      owner != 'FLOWS_FILES' AND
      owner != 'HR' AND
      owner != 'IX' AND
      owner != 'MDDATA' AND
      owner != 'MDSYS' AND
      owner != 'MGMT_VIEW' AND
      owner != 'MTSSYS' AND
      owner != 'ODM' AND
      owner != 'ODM_MTR' AND
      owner != 'OE' AND
      owner != 'OLAPDBA' AND
      owner != 'OLAPSVR' AND
      owner != 'OLAPSYS' AND
      owner != 'ORA_MONITOR' AND 
      owner != 'ORACLE_OCM' AND
      owner != 'ORDPLUGINS' AND
      owner != 'ORDSYS' AND
      owner != 'OSE$HTTP$ADMIN' AND
      owner != 'OUTLN' AND
      owner != 'OWBSYS' AND
      owner != 'PM' AND
      owner != 'PUBLIC' AND 
      owner != 'QS' AND
      owner != 'QS_ADM' AND
      owner != 'QS_CB' AND
      owner != 'QS_CBADM' AND
      owner != 'QS_CS' AND
      owner != 'QS_ES' AND
      owner != 'QS_OS' AND
      owner != 'QS_WS' AND
      owner != 'RMAN'AND
      owner != 'SCOTT' AND
      owner != 'SH' AND
      owner != 'SI_INFORMTN_SCHEMA' AND
      owner != 'SPATIAL_CSW_ADMIN_USR' AND
      owner != 'SPATIAL_WFS_ADMIN_USR' AND
      owner != 'SYSMAN' AND
      owner != 'TSMSYS' AND
      owner != 'WKPROXY' AND
      owner != 'WKSYS' AND
      owner != 'WK_TEST' AND
      owner != 'WMSYS' AND
      owner != 'XDB' AND
      owner != 'XS$NULL'
group by owner;

spool off

clear columns


col a fold_after

spool getr2_80.sql
select 'set termout off' a, 
'spool r2_80_' || owner || '.sql' a, 
'prompt connect internal/' a,
'prompt set termout off' a,
'prompt @s1.sql ' || owner a, 
'prompt set termout off' a, 
'prompt spool ' || owner || '_sam.txt' a, 
'prompt set echo on' a, 
'prompt @s2.sql' a, 
'prompt spool off' a, 
'prompt set echo off' a, 
'prompt set pagesize 55' a, 
'prompt set linesize 80' a, 
'prompt set arraysize 15' a, 
'prompt set maxdata 60000' a, 
'prompt set termout on' a, 
'spool off' a, 
'set termout on'
from dba_objects
where owner != 'SYS' AND 
      owner != 'SYSTEM' AND
      owner != 'ANONYMOUS' AND
      owner != 'APEX_PUBLIC_USER' AND
      owner != 'AURORA$JIS$UTILITY$' AND
      owner != 'AURORA$ORB$UNAUTHENTICATED' AND
      owner != 'BI' AND
      owner != 'CTXSYS' AND
      owner != 'DBADMIN' AND 
      owner != 'DBSNMP' AND
      owner != 'DEMO' AND
      owner != 'DIP' AND
      owner != 'DMSYS' AND
      owner != 'DRSYS' AND
      owner != 'EXFSYS' AND
      owner != 'FLOWS_030000' AND
      owner != 'FLOWS_FILES' AND
      owner != 'HR' AND
      owner != 'IX' AND
      owner != 'MDDATA' AND
      owner != 'MDSYS' AND
      owner != 'MGMT_VIEW' AND
      owner != 'MTSSYS' AND
      owner != 'ODM' AND
      owner != 'ODM_MTR' AND
      owner != 'OE' AND
      owner != 'OLAPDBA' AND
      owner != 'OLAPSVR' AND
      owner != 'OLAPSYS' AND
      owner != 'ORA_MONITOR' AND 
      owner != 'ORACLE_OCM' AND
      owner != 'ORDPLUGINS' AND
      owner != 'ORDSYS' AND
      owner != 'OSE$HTTP$ADMIN' AND
      owner != 'OUTLN' AND
      owner != 'OWBSYS' AND
      owner != 'PM' AND
      owner != 'PUBLIC' AND 
      owner != 'QS' AND
      owner != 'QS_ADM' AND
      owner != 'QS_CB' AND
      owner != 'QS_CBADM' AND
      owner != 'QS_CS' AND
      owner != 'QS_ES' AND
      owner != 'QS_OS' AND
      owner != 'QS_WS' AND
      owner != 'RMAN'AND
      owner != 'SCOTT' AND
      owner != 'SH' AND
      owner != 'SI_INFORMTN_SCHEMA' AND
      owner != 'SPATIAL_CSW_ADMIN_USR' AND
      owner != 'SPATIAL_WFS_ADMIN_USR' AND
      owner != 'SYSMAN' AND
      owner != 'TSMSYS' AND
      owner != 'WKPROXY' AND
      owner != 'WKSYS' AND
      owner != 'WK_TEST' AND
      owner != 'WMSYS' AND
      owner != 'XDB' AND
      owner != 'XS$NULL'
group by owner;

spool off

clear columns
@getr2.sql
@getr2_80.sql

set termout off

col a fold_after

spool sam8i.txt
prompt These are commands to run against Oracle 8i and higher databases
prompt rm r2_80_*
prompt
select '=======================' a,
'----------Begin - ' || owner || '---------' a,
'-rm r2.sql' a, 
'mv r2_' || owner || '.sql r2.sql' a,
'g2 > /dev/null 2>~&1' a,
'-get ' || owner || '_sam.txt' a,
'-rm ' || owner || '_sam.txt' a,
'----------Done - ' || owner || '---------' a
from dba_objects do
where owner != 'SYS' AND 
      owner != 'SYSTEM' AND
      owner != 'ANONYMOUS' AND
      owner != 'APEX_PUBLIC_USER' AND
      owner != 'AURORA$JIS$UTILITY$' AND
      owner != 'AURORA$ORB$UNAUTHENTICATED' AND
      owner != 'BI' AND
      owner != 'CTXSYS' AND
      owner != 'DBADMIN' AND 
      owner != 'DBSNMP' AND
      owner != 'DEMO' AND
      owner != 'DIP' AND
      owner != 'DMSYS' AND
      owner != 'DRSYS' AND
      owner != 'EXFSYS' AND
      owner != 'FLOWS_030000' AND
      owner != 'FLOWS_FILES' AND
      owner != 'HR' AND
      owner != 'IX' AND
      owner != 'MDDATA' AND
      owner != 'MDSYS' AND
      owner != 'MGMT_VIEW' AND
      owner != 'MTSSYS' AND
      owner != 'ODM' AND
      owner != 'ODM_MTR' AND
      owner != 'OE' AND
      owner != 'OLAPDBA' AND
      owner != 'OLAPSVR' AND
      owner != 'OLAPSYS' AND
      owner != 'ORA_MONITOR' AND 
      owner != 'ORACLE_OCM' AND
      owner != 'ORDPLUGINS' AND
      owner != 'ORDSYS' AND
      owner != 'OSE$HTTP$ADMIN' AND
      owner != 'OUTLN' AND
      owner != 'OWBSYS' AND
      owner != 'PM' AND
      owner != 'PUBLIC' AND 
      owner != 'QS' AND
      owner != 'QS_ADM' AND
      owner != 'QS_CB' AND
      owner != 'QS_CBADM' AND
      owner != 'QS_CS' AND
      owner != 'QS_ES' AND
      owner != 'QS_OS' AND
      owner != 'QS_WS' AND
      owner != 'RMAN'AND
      owner != 'SCOTT' AND
      owner != 'SH' AND
      owner != 'SI_INFORMTN_SCHEMA' AND
      owner != 'SPATIAL_CSW_ADMIN_USR' AND
      owner != 'SPATIAL_WFS_ADMIN_USR' AND
      owner != 'SYSMAN' AND
      owner != 'TSMSYS' AND
      owner != 'WKPROXY' AND
      owner != 'WKSYS' AND
      owner != 'WK_TEST' AND
      owner != 'WMSYS' AND
      owner != 'XDB' AND
      owner != 'XS$NULL'
group by owner;

spool off

spool sam80.txt
prompt These are commands to run against Oracle 80 databases
select '=======================' a,
'----------Begin - ' || owner || '---------' a,
'-rm r2.sql' a, 
'mv r2_80_' || owner || '.sql r2.sql' a,
'g2 > /dev/null 2>~&1' a,
'-get ' || owner || '_sam.txt' a,
'-rm ' || owner || '_sam.txt' a,
'----------Done - ' || owner || '---------' a
from dba_objects
where owner != 'SYS' AND 
      owner != 'SYSTEM' AND
      owner != 'ANONYMOUS' AND
      owner != 'APEX_PUBLIC_USER' AND
      owner != 'AURORA$JIS$UTILITY$' AND
      owner != 'AURORA$ORB$UNAUTHENTICATED' AND
      owner != 'BI' AND
      owner != 'CTXSYS' AND
      owner != 'DBADMIN' AND 
      owner != 'DBSNMP' AND
      owner != 'DEMO' AND
      owner != 'DIP' AND
      owner != 'DMSYS' AND
      owner != 'DRSYS' AND
      owner != 'EXFSYS' AND
      owner != 'FLOWS_030000' AND
      owner != 'FLOWS_FILES' AND
      owner != 'HR' AND
      owner != 'IX' AND
      owner != 'MDDATA' AND
      owner != 'MDSYS' AND
      owner != 'MGMT_VIEW' AND
      owner != 'MTSSYS' AND
      owner != 'ODM' AND
      owner != 'ODM_MTR' AND
      owner != 'OE' AND
      owner != 'OLAPDBA' AND
      owner != 'OLAPSVR' AND
      owner != 'OLAPSYS' AND
      owner != 'ORA_MONITOR' AND 
      owner != 'ORACLE_OCM' AND
      owner != 'ORDPLUGINS' AND
      owner != 'ORDSYS' AND
      owner != 'OSE$HTTP$ADMIN' AND
      owner != 'OUTLN' AND
      owner != 'OWBSYS' AND
      owner != 'PM' AND
      owner != 'PUBLIC' AND 
      owner != 'QS' AND
      owner != 'QS_ADM' AND
      owner != 'QS_CB' AND
      owner != 'QS_CBADM' AND
      owner != 'QS_CS' AND
      owner != 'QS_ES' AND
      owner != 'QS_OS' AND
      owner != 'QS_WS' AND
      owner != 'RMAN'AND
      owner != 'SCOTT' AND
      owner != 'SH' AND
      owner != 'SI_INFORMTN_SCHEMA' AND
      owner != 'SPATIAL_CSW_ADMIN_USR' AND
      owner != 'SPATIAL_WFS_ADMIN_USR' AND
      owner != 'SYSMAN' AND
      owner != 'TSMSYS' AND
      owner != 'WKPROXY' AND
      owner != 'WKSYS' AND
      owner != 'WK_TEST' AND
      owner != 'WMSYS' AND
      owner != 'XDB' AND
      owner != 'XS$NULL'
group by owner;

spool off

set termout on

prompt
prompt
prompt Users of Interest:
prompt ------------------
prompt
ttitle "Passwords" skip, skip
column username format a25
column password format a25
select username, password from dba_users
where username != 'SYS' AND 
      username != 'SYSTEM' AND 
      username != 'ANONYMOUS' AND
      username != 'APEX_PUBLIC_USER' AND
      username != 'AURORA$JIS$UTILITY$' AND
      username != 'AURORA$ORB$UNAUTHENTICATED' AND
      username != 'BI' AND
      username != 'CTXSYS' AND
      username != 'DBADMIN' AND 
      username != 'DBSNMP' AND
      username != 'DEMO' AND
      username != 'DIP' AND
      username != 'DMSYS' AND
      username != 'DRSYS' AND
      username != 'EXFSYS' AND
      username != 'FLOWS_030000' AND
      username != 'FLOWS_FILES' AND
      username != 'HR' AND
      username != 'IX' AND
      username != 'MDDATA' AND
      username != 'MDSYS' AND
      username != 'MGMT_VIEW' AND
      username != 'MTSSYS' AND
      username != 'ODM' AND
      username != 'ODM_MTR' AND
      username != 'OE' AND
      username != 'OLAPDBA' AND
      username != 'OLAPSVR' AND
      username != 'OLAPSYS' AND
      username != 'ORA_MONITOR' AND 
      username != 'ORACLE_OCM' AND
      username != 'ORDPLUGINS' AND
      username != 'ORDSYS' AND
      username != 'OSE$HTTP$ADMIN' AND
      username != 'OUTLN' AND
      username != 'OWBSYS' AND
      username != 'PM' AND
      username != 'PUBLIC' AND 
      username != 'QS' AND
      username != 'QS_ADM' AND
      username != 'QS_CB' AND
      username != 'QS_CBADM' AND
      username != 'QS_CS' AND
      username != 'QS_ES' AND
      username != 'QS_OS' AND
      username != 'QS_WS' AND
      username != 'RMAN'AND
      username != 'SCOTT' AND
      username != 'SH' AND
      username != 'SI_INFORMTN_SCHEMA' AND
      username != 'SPATIAL_CSW_ADMIN_USR' AND
      username != 'SPATIAL_WFS_ADMIN_USR' AND
      username != 'SYSMAN' AND
      username != 'TSMSYS' AND
      username != 'WKPROXY' AND
      username != 'WKSYS' AND
      username != 'WK_TEST' AND
      username != 'WMSYS' AND
      username != 'XDB' AND
      username != 'XS$NULL'
order by username;
prompt ----------------------------------------

prompt
ttitle 'Object Counts for Users of Interest' skip skip
prompt -------------------------------------
 
prompt
col ow format a18 heading 'Owner'
col ta format 999,999 heading 'Tables'
col ve format 999,999 heading 'Views'

select owner ow,
       sum(decode(object_type,'TABLE',1,0)) ta ,
       sum(decode(object_type,'VIEW',1,0)) ve
from dba_objects
where owner != 'SYS' AND 
      owner != 'SYSTEM' AND
      owner != 'ANONYMOUS' AND
      owner != 'APEX_PUBLIC_USER' AND
      owner != 'AURORA$JIS$UTILITY$' AND
      owner != 'AURORA$ORB$UNAUTHENTICATED' AND
      owner != 'BI' AND
      owner != 'CTXSYS' AND
      owner != 'DBADMIN' AND 
      owner != 'DBSNMP' AND
      owner != 'DEMO' AND
      owner != 'DIP' AND
      owner != 'DMSYS' AND
      owner != 'DRSYS' AND
      owner != 'EXFSYS' AND
      owner != 'FLOWS_030000' AND
      owner != 'FLOWS_FILES' AND
      owner != 'HR' AND
      owner != 'IX' AND
      owner != 'MDDATA' AND
      owner != 'MDSYS' AND
      owner != 'MGMT_VIEW' AND
      owner != 'MTSSYS' AND
      owner != 'ODM' AND
      owner != 'ODM_MTR' AND
      owner != 'OE' AND
      owner != 'OLAPDBA' AND
      owner != 'OLAPSVR' AND
      owner != 'OLAPSYS' AND
      owner != 'ORA_MONITOR' AND 
      owner != 'ORACLE_OCM' AND
      owner != 'ORDPLUGINS' AND
      owner != 'ORDSYS' AND
      owner != 'OSE$HTTP$ADMIN' AND
      owner != 'OUTLN' AND
      owner != 'OWBSYS' AND
      owner != 'PM' AND
      owner != 'PUBLIC' AND 
      owner != 'QS' AND
      owner != 'QS_ADM' AND
      owner != 'QS_CB' AND
      owner != 'QS_CBADM' AND
      owner != 'QS_CS' AND
      owner != 'QS_ES' AND
      owner != 'QS_OS' AND
      owner != 'QS_WS' AND
      owner != 'RMAN'AND
      owner != 'SCOTT' AND
      owner != 'SH' AND
      owner != 'SI_INFORMTN_SCHEMA' AND
      owner != 'SPATIAL_CSW_ADMIN_USR' AND
      owner != 'SPATIAL_WFS_ADMIN_USR' AND
      owner != 'SYSMAN' AND
      owner != 'TSMSYS' AND
      owner != 'WKPROXY' AND
      owner != 'WKSYS' AND
      owner != 'WK_TEST' AND
      owner != 'WMSYS' AND
      owner != 'XDB' AND
      owner != 'XS$NULL'
group by owner
order by ta;
prompt ----------------------------------------

prompt

ttitle off
set heading off

prompt ----------------------------------------------------------------------------

prompt
prompt
prompt
ttitle "Auditing Parameters Of Interest" skip, skip
prompt ---------------------------------

column name format a30 wrapped
column value format a50 wrapped
select name, value
from v$parameter
where name like 'audit%';

prompt ----------------------------------------------------------------------------

prompt
prompt
prompt
ttitle "Language Parameters Of Interest" skip, skip
prompt ---------------------------------
 
select * from NLS_DATABASE_PARAMETERS where PARAMETER like '%CHARACTERSET';
prompt
prompt
prompt
 
prompt Run this to set the NLS_LANG variable:
prompt ---------------------------------------
 
select '-setenv NLS_LANG=AMERICAN_AMERICA.' || value from NLS_DATABASE_PARAMETERS where PARAMETER = 'NLS_CHARACTERSET';
prompt
prompt ----------------------------------------------------------------------------
 
prompt
prompt
prompt

set termout off
set heading on
spool pass.txt
prompt
prompt ----------------------------------------------

prompt
column username format a25
column password format a25
select username, password from dba_users
where username != 'ANONYMOUS' AND
      username != 'APEX_PUBLIC_USER' AND
      username != 'AURORA$JIS$UTILITY$' AND
      username != 'AURORA$ORB$UNAUTHENTICATED' AND
      username != 'BI' AND
      username != 'CTXSYS' AND
      username != 'DBADMIN' AND 
      username != 'DBSNMP' AND
      username != 'DEMO' AND
      username != 'DIP' AND
      username != 'DMSYS' AND
      username != 'DRSYS' AND
      username != 'EXFSYS' AND
      username != 'FLOWS_030000' AND
      username != 'FLOWS_FILES' AND
      username != 'HR' AND
      username != 'IX' AND
      username != 'MDDATA' AND
      username != 'MDSYS' AND
      username != 'MGMT_VIEW' AND
      username != 'MTSSYS' AND
      username != 'ODM' AND
      username != 'ODM_MTR' AND
      username != 'OE' AND
      username != 'OLAPDBA' AND
      username != 'OLAPSVR' AND
      username != 'OLAPSYS' AND
      username != 'ORA_MONITOR' AND 
      username != 'ORACLE_OCM' AND
      username != 'ORDPLUGINS' AND
      username != 'ORDSYS' AND
      username != 'OSE$HTTP$ADMIN' AND
      username != 'OUTLN' AND
      username != 'OWBSYS' AND
      username != 'PM' AND
      username != 'PUBLIC' AND 
      username != 'QS' AND
      username != 'QS_ADM' AND
      username != 'QS_CB' AND
      username != 'QS_CBADM' AND
      username != 'QS_CS' AND
      username != 'QS_ES' AND
      username != 'QS_OS' AND
      username != 'QS_WS' AND
      username != 'RMAN'AND
      username != 'SCOTT' AND
      username != 'SH' AND
      username != 'SI_INFORMTN_SCHEMA' AND
      username != 'SPATIAL_CSW_ADMIN_USR' AND
      username != 'SPATIAL_WFS_ADMIN_USR' AND
      username != 'SYSMAN' AND
      username != 'TSMSYS' AND
      username != 'WKPROXY' AND
      username != 'WKSYS' AND
      username != 'WK_TEST' AND
      username != 'WMSYS' AND
      username != 'XDB' AND
      username != 'XS$NULL'
order by username;
prompt ----------------------------------------------------
 
prompt
spool off
 

