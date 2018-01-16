

#!/bin/bash

IPStr=`/sbin/ifconfig  | grep 'inet '| grep -v '127.0.0.1'|awk '{print $2}'`
IP=`echo ${IPStr##*:}`

echo ----------------start backup $1 at `date` ----------------

rootPath=/data/backup/
BackupPath="$rootPath"$1FULL/
LogFile="$rootPath"mysqlback.log

DumpFile="$rootPath""$IP"_$1FULL_$(date +%Y%m%d).tgz

echo $BackupPath
echo $LogFile
echo $DumpFile

mkdir -p $BackupPath


find $rootPath -mmin +2160 -name "*.tgz" -exec rm -rf {} \;

innobackupex --defaults-file=/etc/my$1.cnf --user=test --password=123456 --use-memory=3G --no-timestamp  $BackupPath >> $LogFile

innobackupex --defaults-file=/etc/my$1.cnf --user=test --password=123456  --use-memory=3G --no-timestamp --apply-log  $BackupPath >> $LogFile


if [ $? -eq 0 ]
 then
          echo ----------------start tar $1 backup file at `date` ----------------
          tar czf "$DumpFile" "$BackupPath" >> $LogFile 2>&1
          rm -rf $BackupPath
 else
  echo "insert into t_sms_alert(phonenum,message) select mobile,'$IP:$1 daily backup failed' from dba_mobile ; "|mysql  -h db.ymatou.com --user=test  --password='123456' --port=30001 --database=dbmonitor
  echo "insert into t_mail_alert(title,mailaddress,message) select '$IP:$1 daily backup failed','DBA@xxx.com','$IP:30001 daily backup failed'; "|mysql  -h db.xxx.com --user=test --password='123456' --port=30001 --database=dbmonitor
fi

echo ----------------backup $1 complete at `date` ----------------
