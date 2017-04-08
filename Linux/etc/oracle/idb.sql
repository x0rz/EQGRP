connect / as sysdba
set newpage 0
set pagesize 9999
set linesize 1000
set verify off
set trimspool on
set trimout on
set feedback 6
set recsep off
set maxdata 60000
set Numwidth 20
set longchunk 60000
set long 9999999
set termout off
set arraysize 3


set linesize 120

prompt .                     Auditing Report
prompt ----------------------------------------------------------- 

prompt
Prompt
prompt Statement Auditing:
prompt -------------------- 

prompt

ttitle center 'STATEMENT AUDITING ' skip skip

select * from DBA_STMT_AUDIT_OPTS;

Prompt
prompt Privilege Auditing:
prompt -------------------- 

prompt

ttitle center 'PRIVILEGE AUDITING ' skip skip

select * from DBA_PRIV_AUDIT_OPTS;

Prompt
prompt Object Auditing:
prompt ----------------- 

prompt

ttitle center 'OBJECT AUDITING ' skip skip

select * from sys.dba_obj_audit_opts
where alt !='-/-' or alt !='-/-' or aud !='-/-' or com !='-/-' or
	del !='-/-' or gra !='-/-' or ind !='-/-' or ins !='-/-' or
	loc !='-/-' or ren !='-/-' or sel !='-/-' or upd !='-/-' or
	ref !='-/-' or exe !='-/-';

Prompt
prompt Audit Configuration:
prompt --------------------- 

prompt

ttitle center 'AUDIT CONFIGURATION ' skip skip

select * from sm$audit_config;


Prompt
prompt Session Audit Records:
prompt -----------------------

prompt

ttitle center 'SESSION AUDIT RECORDS FOR &1 ' skip skip

select OS_Username, Username, Terminal, 
        DECODE(Returncode, '0', 'Connected', 
                                 '1005', 'FailedNull', 
                                 '1017', 'Failed', Returncode),
        TO_CHAR(Timestamp, 'DD-MON-YYYY HH24:MI:SS'),
        TO_CHAR(Logoff_Time, 'DD-MON-YYYY HH24:MI:SS')
from DBA_AUDIT_SESSION 
where TO_CHAR(Timestamp, 'DD-MON-YYYY') like '%&&1%' and rownum < 10;



Prompt
prompt Object Audit Records:
prompt ----------------------

prompt

ttitle center 'OBJECT AUDIT RECORDS FOR &&1 ' skip skip

select OS_Username, Username, Terminal, 
        Owner, Obj_Name, Action_Name,
        DECODE(Returncode, '0', 'Success', Returncode),
        TO_CHAR(Timestamp, 'DD-MON-YYYY HH24:MI:SS')
from DBA_AUDIT_OBJECT
where TO_CHAR(Timestamp, 'DD-MON-YYYY') like '%&&1%' and rownum < 10;

prompt
prompt .                 End of Auditing Report
prompt ----------------------------------------------------------- 

Prompt
prompt NOTE: "no rows selected" means that auditing is turned off
prompt
Prompt
ttitle off


set linesize 125

prompt
prompt Database Users and Passwords:
prompt ------------------------------

prompt
ttitle center 'Database Users and Passwords' skip skip

col spare4 format a64 wrap heading 'ORACLE 11g PASSWORD'
col PASSWORD format a26 wrap
select name, password, spare4 from user$ where password != 'NULL' order by name;


set linesize 60

Prompt
prompt Partitioned Tables:
prompt -----------------------

prompt

ttitle center 'Partitioned Tables' skip skip

col OwnTab format a45 wrap heading 'Owner.Table (rows)'
col Partitioned format a11 heading 'Partitioned'
select owner || '.' || table_name || ' (' || num_rows || ')' OwnTab, partitioned 
from dba_tables where partitioned='YES' order by owner, table_name;

set linesize 110

Prompt
prompt Partition Names:
prompt -----------------------

prompt

ttitle center 'Partition Names' skip skip
col subpartition_count format 9999999999 heading 'SubPart Count'
col high_value format a45 wrap heading 'HIGH_VALUE'
col OwnTabPart format a45 wrap heading 'Owner.Table-Partition(rows)'
select table_owner || '.' || table_name || '-' || partition_name || '(' || num_rows || ')' ownTabPart, high_value, subpartition_count 
from dba_tab_partitions order by table_owner, table_name, partition_name;


set linesize 80

prompt
prompt Object Counts By User:
prompt -----------------------

prompt
ttitle center 'Object Counts by User' skip skip

col ow format a18 heading 'Owner'
col ta format 999,999 heading 'Tables'
col ind format 999,999 heading 'Indexes'
col sy format 999,999 heading 'Synonyms'
col se format 999,999 heading 'Sequences'
col ve format 999,999 heading 'Views'

compute sum of ta on report
compute sum of ow on report
compute sum of sy on report
compute sum of se on report
compute sum of ind on report
compute sum of ve on report

break on report

set heading on

select owner ow,
       sum(decode(object_type,'TABLE',1,0)) ta ,
       sum(decode(object_type,'INDEX',1,0)) ind ,
       sum(decode(object_type,'SYNONYM',1,0)) sy ,
       sum(decode(object_type,'SEQUENCE',1,0)) se ,
       sum(decode(object_type,'VIEW',1,0)) ve
from dba_objects
group by owner
order by owner
/

ttitle off

Prompt
prompt End of Report

col dbl format 999,999 heading 'Database|Links'
col pkg format 999,999 heading 'Packages'
col pkb format 999,999 heading 'Package|Bodies'
col pro format 999,999 heading 'Procedures'
col ve format 999,999 heading 'Views'

set verify off

compute sum of dbl on report
compute sum of ow on report
compute sum of pkg on report
compute sum of pkb on report
compute sum of pro on report
compute sum of ve on report
compute sum of clu on report

break on report

prompt
prompt PL/SQL Procedure Counts By User:
prompt ---------------------------------

prompt
ttitle center 'PL/SQL Procedure Counts by User' skip skip

select owner ow,
       sum(decode(object_type,'DATABASE LINK',1,0)) dbl ,
       sum(decode(object_type,'PACKAGE',1,0)) pkg ,
       sum(decode(object_type,'PACKAGE BODY',1,0)) pkb ,
       sum(decode(object_type,'PROCEDURE',1,0)) pro
from dba_objects
group by owner
order by owner
/




prompt
prompt Database Usage by User and Tablespace:
prompt ---------------------------------------

prompt
ttitle center 'Database Usage by User and Tablespace' skip skip

prompt

break on owner skip 2

col K format 999,999,999 heading 'Size K'
col ow format a24 heading 'Owner'
col ta format a30 heading 'Tablespace'


select  us.name                                 ow,
        ts.name                                 ta,
        sum(seg.blocks*ts.blocksize)/1024       K
from    sys.ts$ ts,
        sys.user$ us,
        sys.seg$ seg
where   seg.user# = us.user#
and     ts.ts# = seg.ts#
group by us.name,ts.name                                
order by us.name                                
/

Prompt
clear computes

select owner ow, tablespace_name ta, sum(bytes)/1024 K
from dba_segments
group by owner, tablespace_name
order by owner, tablespace_name
/


prompt

prompt End of Report

ttitle off

clear breaks
clear columns
clear computes


prompt
prompt
prompt Users of Interest:
prompt ------------------

prompt
ttitle 'Object Counts for Users of Interest' skip skip

col ow format a18 heading 'Owner'
col ta format 999,999 heading 'Tables'
col ve format 999,999 heading 'Views'

set heading on

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
order by ta
/

clear columns



prompt
prompt Database Links:
prompt ----------------

prompt

set linesize 130
ttitle center 'Database Links' skip skip

set heading on

select u.name owner_name, l.*
from link$ l, user$ u
where u.user# = l.owner#    
/

set linesize 80
prompt
prompt DB Initialization Parameters:
prompt ------------------------------

prompt

ttitle center "DB Initialization Parameters" skip 2

column name format a25 wrapped
column value format a20 wrapped
column description format a33 word_wrapped


select name, value,  description
from v$parameter
order by name
/
prompt
prompt DB Datafiles, Controlfiles, and Logfiles:
prompt -----------------------------------------

prompt
ttitle center "DB Datafiles, Controlfiles, and Logfiles" skip skip

column file_type format a10 wrapped
column name format a50 wrapped

select 'DATA' file_type, name from v$datafile
union
select 'CONTROL' file_type, name from v$controlfile
union 
select 'LOG' file_type, member from v$logfile
/

set linesize 90

prompt
prompt Database Tablespaces and Mappings to Datafiles:
prompt ------------------------------------------------

prompt
ttitle center "Database Tablespaces and Mappings to Datafiles" -
        skip center "(Sorted by Tablespace)" skip 2

column tablespace_name format a25 wrapped
column file_name format a40 wrapped
column bytes format 999,999,999,999 wrapped


select tablespace_name, file_name, bytes
from dba_data_files
order by tablespace_name, file_name
/

set linesize 80
set pagesize 55
set linesize 80
set arraysize 15
set maxdata 60000
set termout on
host ls -alrt $ORACLE_HOME/rdbms/audit/*.aud | tail

