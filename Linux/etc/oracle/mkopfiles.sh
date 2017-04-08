#PATH=/usr/bin:/usr/sbin:$PATH
#export PATH

#Passed to this
#$1 - orasid
#$2 - thismonth (JAN)
#$3 - year (2012)
#$4 - hostname (short)

cd /current/etc/oracle
if [ ! -d /current/up/oracle ]
then
	mkdir /current/up/oracle
fi

./mkt0sql.sh $1 > ./t0.sql
./mkr1sql.sh $1 $2 $3 $4 > ./r1.sql

umask 13
cp t0 g* *.sql mkall.sh mkuser.sh mksch.sh mkexp.sh mktab.sh mkg3.sh mkscript.sh mkr2_schema.sh mkr2sql.sh mkquery.sh /current/up/oracle
rm -f t0.sql r1.sql
umask 0
umask 22

cd /current/down
