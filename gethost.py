
#!/usr/bin/python
import json
import pymysql
myurl = {"host":"monitor.db.ymatou.com", "port":30001, "user":"monitoruser","passwd":"mmowhci$53nZH2whc@452276w", "db":"dbmonitor", "charset":"UTF8"}
def readmysql(sqlstr,myurl):
    myconn=pymysql.connect(host=myurl['host'],user=myurl['user'],passwd=myurl['passwd'],port=myurl['port'],db=myurl['db'],charset=myurl['charset'])
    cur=myconn.cursor()
    cur.execute(sqlstr)
    sqlresult = cur.fetchall()
    return sqlresult
hostlist={}
sql="SELECT  DISTINCT serverip FROM  t_mysqlserverinfo"
ds=readmysql(sql,myurl)
hostlist["mysql"]=[]
for li in ds:
    hostlist["mysql"].append(li[0])
sql="SELECT DISTINCT  serverip FROM  t_mongoserverinfo"
ds=readmysql(sql,myurl)
hostlist["mongodb"]=[]
for li in ds:
    hostlist["mongodb"].append(li[0])
print json.dumps(hostlist)

