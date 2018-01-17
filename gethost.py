


#!/usr/bin/python
import json
import pymysql


myurl = {"host":"db.xxx.com", "port":1000, "user":"test","passwd":"123456", "db":"serverinfo", "charset":"UTF8"}

def readmysql(sqlstr,myurl):
    myconn=pymysql.connect(host=myurl['host'],user=myurl['user'],passwd=myurl['passwd'],port=myurl['port'],db=myurl['db'],charset=myurl['charset'])
    sqlresult=[]
    try:
        with myconn.cursor() as cur:
            cur.execute(sqlstr)
            sqlresult = cur.fetchall()
    finally:
        myconn.commit()
        myconn.close()
    return sqlresult

if __name__== '__main__':
    hostlist={}
    sql="SELECT  DISTINCT serverip FROM  mysqlserverinfo;"
    ds=readmysql(sql,myurl)
    hostlist["mysql"]=[]
    for li in ds:
        hostlist["mysql"].append(li[0])
    
    sql="SELECT DISTINCT  serverip FROM  mongoserverinfo;"
    ds=readmysql(sql,myurl)
    hostlist["mongodb"]=[]
    for li in ds:
        hostlist["mongodb"].append(li[0])

    print json.dumps(hostlist)                     

