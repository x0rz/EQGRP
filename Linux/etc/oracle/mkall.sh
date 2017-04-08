./mkuser.sh $1 $2 $4 > $1$4_user
./mksch.sh $1 $2 > $1_sch
./mkexp.sh $1$4_user > exp_$1$4
./mkexp.sh $1_sch > exp_$1_sch
./mktab.sh $1 > r3_$1.sql
./mkg3.sh > g3
./mkscript.sh $1 $3 $4 $5 > $1_exp_script
