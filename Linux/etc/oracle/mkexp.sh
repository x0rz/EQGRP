echo ORA_NLS=\$ORACLE_HOME/ocommon/nls/admin/data
echo export ORA_NLS
echo " "
echo PATH=/usr/bin:/usr/ucb:/etc:\$ORACLE_HOME/bin:/usr/ccs/bin:/usr/ccs/lib:/usr/local/bin:/usr/sbin
echo LD_LIBRARY_PATH=\$ORACLE_HOME/lib
echo " "
echo export PATH LD_LIBRARY_PATH
echo " "
echo "echo ORACLE_BASE  = \$ORACLE_BASE"
echo "echo ORACLE_HOME  = \$ORACLE_HOME"
echo "echo ORACLE_SID   = \$ORACLE_SID"
echo "echo NLS_LANG     = \$NLS_LANG"
echo "echo ORA_NLS      = \$ORA_NLS"

echo exp parfile=$1
