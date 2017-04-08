echo "###########################################################"
echo "# OPTIONAL - Edit these files to set the correct password #"
echo "###########################################################"
echo vi /current/up/$2/$1$3_user
echo vi /current/up/$2/$1_sch
echo
echo "###########################################"
echo "# Set the ORACLE_SID environment variable #"
echo "###########################################"
echo -setenv ORACLE_SID=$2
echo 
echo "####################################"
echo "# Upload the Export Schema scripts #"
echo "####################################"
echo -put /current/up/$2/exp_$1_sch $4/exp_$1_sch
echo -put /current/up/$2/$1_sch $4/$1_sch
echo 
echo "#########################################################################################"
echo "# OPTIONAL - Run query to retrieve table names to append to the "$1$3_user" file. 	#"
echo "# 	          This will allow you to limit the export to a specific set of tables.	#"
echo "#########################################################################################"
echo -put /current/up/$2/g3 $4/g3
echo -put /current/up/$2/r3_$1.sql $4/r3.sql
echo chmod 777 g3 r3.sql
echo "g3 > g3_$1.txt"
echo -vget g3_$1.txt
echo -vget $1_tables.txt
echo -rm g3_$1.txt
echo -rm $1_tables.txt
echo -rm r3.sql
echo -rm g3
echo 
echo "#########################################################################################"
echo "# OPTIONAL - Edit the $1$3_user" file to add the list of tables you want for the export 	#"
echo "#            Your additions to the END of the file should look like this:			#"
echo "#########################################################################################"
echo "#              TABLES=(									#"
echo "#              table_a,									#"
echo "#              table_b,									#"
echo "#              table_c,									#"
echo "#              table_x 									#"
echo "#              ) 									#"
echo "#########################################################################################"
echo vi /current/up/$2/$1$3_user
echo
echo "################################"
echo "# Upload the Export DB scripts #"
echo "################################"
echo -put /current/up/$2/exp_$1$3 $4/exp_$1$3
echo -put /current/up/$2/$1$3_user $4/$1$3_user
echo 
echo "#############################################"
echo "# Set the permissions of the uploaded files #"
echo "#############################################"
echo chmod 777 $1_sch exp_$1_sch $1$3_user exp_$1$3
echo 
echo "#####################"
echo "# Export the Schema #"
echo "#####################"
echo "exp_$1_sch > exp_$1_sch.txt"
echo -vget exp_$1_sch.txt
echo -get $1_sch.dmp
echo -rm exp_$1_sch.txt
echo -rm $1_sch.dmp
echo -rm exp_$1_sch
echo -rm $1_sch
echo 
echo "########################"
echo "# Export the User Data #"
echo "######################## "
echo "exp_$1$3 > exp_$1$3.txt"
echo -vget exp_$1.txt
echo -get $1.dmp
echo -rm exp_$1.txt
echo -rm $1.dmp
echo -rm exp_$1$3
echo -rm $1$3_user
echo 

