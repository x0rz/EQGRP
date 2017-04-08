set echo off
set feedback off
set heading off
set linesize 200
set pagesize 0
set trimspool on
set trimout on
set termout off
set verify off
set escape ~

col a fold_after

spool s3.sql

prompt set heading on
prompt set feedback on
prompt set pagesize 9999
prompt set linesize 80
prompt set null "~~~~~~"

select unique 'desc &1~.' || table_name a, 'set linesize 1000' a, 'select /*+ FIRST_ROWS(150) */ * from &1~.' || table_name || ' where rownum < 151;' a, 'set linesize 80' a,  'select count(*) from &1~.' || table_name || ';' 
from all_tab_columns where owner=upper('&1');

spool off
spool s4.sql

prompt set heading on
prompt set feedback on
prompt set pagesize 9999
prompt set linesize 80
prompt set null "~~~~~~"

select unique 'set linesize 80' a, 'desc &1~.' || table_name a, 'set linesize 1000' a, 'select /*+ FIRST_ROWS(150) */ * from &1~.' || table_name || ' where rownum < 151;' 
from all_tab_columns where owner=upper('&1');

spool off
spool s5.sql

prompt set heading on
prompt set feedback on
prompt set pagesize 9999
prompt set linesize 80
prompt set null "~~~~~~"

select unique 'desc &1~.' || table_name a, 'select count(*) from &1~.' || table_name || ';' 
from all_tab_columns where owner=upper('&1');

spool off
spool s6.sql

prompt set heading on
prompt set feedback on
prompt set pagesize 9999
prompt set linesize 1000
prompt set null "~~~~~~"


select unique 'select /*+ FIRST_ROWS(150) */ * from &1~.' || table_name || ' PARTITION(' || partition_name || ') where rownum < 151;' 
from dba_tab_partitions where table_owner=upper('&1');

prompt set linesize 80
select unique 'desc &1~.' || table_name a, 'select count(*) from &1~.' || table_name || ';' 
from all_tables where owner=upper('&1') AND partitioned='YES';

select unique 'set linesize 80' a, 'desc &1~.' || table_name a, 'set linesize 1000' a, 'select /*+ FIRST_ROWS(150) */ * from &1~.' || table_name || ' where rownum < 151;' a, 
'select count(*) from &1~.' || table_name || ';' 
from all_tables where owner=upper('&1') AND partitioned='NO';

spool off

spool s7.sql

prompt set heading on
prompt set feedback on
prompt set pagesize 9999
prompt set linesize 1000
prompt set null "~~~~~~"


select unique 'select /*+ FIRST_ROWS(150) */ * from &1~.' || table_name || ' PARTITION(' || partition_name || ') where rownum < 151;' 
from dba_tab_partitions where table_owner=upper('&1');

prompt set linesize 80
select unique 'desc &1~.' || table_name  
from all_tables where owner=upper('&1') AND partitioned='YES';

select unique 'set linesize 80' a, 'desc &1~.' || table_name a, 'set linesize 1000' a, 'select /*+ FIRST_ROWS(150) */ * from &1~.' || table_name || ' where rownum < 151;'
from all_tables where owner=upper('&1') AND partitioned='NO';

spool off

set heading on
set feedback on
set pagesize 9999
set linesize 1000
set termout on
