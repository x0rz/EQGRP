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

set heading on
prompt
prompt User Tables:
prompt -------------

prompt

ttitle center 'TABLES FOR USER &1 ' skip skip

col table_name for a30 wrap
col comments for a49 wrap


select unique a.table_name, c.comments
from all_tab_columns a, all_tab_comments c
where a.table_name = c.table_name(+)
and a.owner=c.owner(+)
and a.owner= upper('&&1')
order by a.table_name
/

col table_name for a30 wrap
col column_name for a30 wrap
col t for a1
col len for 9999
col pr for 99
col Sc for 99
col N for a1
break on table_name skip 0

prompt
prompt Table Columns:
prompt ---------------

prompt

ttitle center 'TABLE COLUMNS FOR USER &&1 ' skip skip

select a.table_name, a.column_name, 
       DECODE(a.data_type, 
          'CHAR', 'C', 
          'VARCHAR', 'V', 
          'VARCHAR2', 'V', 
          'NUMBER', 'N', 
          'DATE', 'D', 
          '?') "T", 
       a.data_length "Len", 
       a.data_precision "Pr", 
       a.data_scale "Sc", 
       a.nullable "N" 
from all_tab_columns a
where a.owner= upper('&&1')
order by a.table_name, a.column_name
/
Prompt
prompt Column Comments:
prompt -----------------

prompt


ttitle center 'TABLE COLUMN COMMENTS FOR USER &&1 ' skip skip

col table_name for a15 
col com for a64 wrap
break on table_name skip 2

select table_name, '<'||column_name||'>  '||comments com
from all_col_comments
where comments is not null
and owner = upper('&&1')
order by 1
/

ttitle off

Prompt
prompt End of Report

col cnm for a20 wrap
col com for a40 wrap

select table_name, column_name cnm, comments com
from all_col_comments
where comments is not null
and owner = upper('&&1')
order by 1
/


clear breaks
clear columns
clear computes


set escape ~
set heading on


ttitle off
set linesize 80

prompt
prompt User Views:
prompt ------------

prompt

ttitle center 'VIEWS FOR USER &1 ' skip skip

column view_name for a30 wrap
column text for a80 wrap
column sp heading ''

set linesize 81
set heading on

select view_name, text,
'*******************************************************************************' sp
from sys.all_views
where owner = upper('&&1')
order by view_name
/

set linesize 80

ttitle off

prompt
prompt Number of User DB Links:
prompt -------------------------

prompt

select count(*) from user_db_links;

prompt
prompt Number of All DB Links:
prompt ------------------------

prompt

select count(*) from all_db_links where owner=upper('&1');

prompt
prompt Number of Snapshots:
prompt ---------------------

prompt

select count(*) from all_snapshots where owner=upper('&1');

set echo off

set linesize 85

col db format a30 wrap heading 'DB Link Name'
col h format a20 wrap heading 'Host'
col u format a15 wrap heading 'Username'
col p format a15 wrap heading 'Password'

prompt
prompt Database Links:
prompt ----------------

prompt

ttitle center 'Database Links ' skip skip

select username u, password p, db_link db, host h
from user_db_links;

set linesize 85

col db format a30 wrap heading 'DB Link Name'
col h format a20 wrap heading 'Host'
col u format a15 wrap heading 'Username'
col o format a15 wrap heading 'Owner'

prompt
prompt User Database Links:
prompt ---------------------

prompt

ttitle center 'Database Links For User &&1 ' skip skip

select owner o, username u, db_link db, host h
from all_db_links
where owner=upper('&1');

prompt
prompt User Snapshots:
prompt ----------------

prompt

ttitle center 'Snapshots For User &&1 ' skip skip

col n heading 'Snapshot Name'
col t heading 'Table Name'
col sp heading ''

select Name n, Table_Name t, Query,
'************************************************************************************' sp
from all_snapshots
where owner=upper('&1');


ttitle off
