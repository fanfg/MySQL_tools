#!/usr/bin/python
# __author__ = 'fanfugui'
# desc: mgr monitor

import pymysql
import paramiko
from collections import namedtuple
import time
import click

hostinfo = namedtuple('hostinfo',
                      ['CHANNEL_NAME', 'MEMBER_ID', 'MEMBER_HOST', 'MEMBER_IP', 'MEMBER_PORT', 'ROLE', 'MEMBER_STATE'])


def select_data(ssql, **connstr):
    conn = pymysql.connect(host=connstr['host'],
                           user=connstr['user'],
                           passwd=connstr['password'],
                           port=connstr['port'],
                           db=connstr['db'])
    ds = {}
    try:
        with conn.cursor() as cur:
            cur.execute(ssql)
            ds = cur.fetchall()
    except Exception as e:
        print('except:', e)
    finally:
        conn.commit()
        conn.close()
    return ds


def resolve_hostname(server_ip, hostname):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #ssh.connect(hostname=server_ip, port=22, username='root', password='root@1234')
    ssh.connect(hostname=server_ip, port=22, username='root')
    #key_filename='/root/.ssh/authorized_keys ')
    stdin, stdout, stderr = ssh.exec_command('ping %s' % (hostname,))
    return stdout.readline().split()[2].encode('utf8')[1:-1]


# state  delay  tps/qps connections  system metrics
"""
insert query update delete getmore command % dirty % used flushes vsize   res qr|qw ar|aw netIn netOut conn        set repl     time
     1    *0      3      3       8    39|0     0.0   80.0       0 99.3G 85.0G   0|0   1|0   31k    63k  358 productset  PRI 14:11:47
     1    *0      6      1      12    44|0     0.0   80.0       0 99.3G 85.0G   0|0   1|0   48k    60k  358 productset  PRI 14:11:48
    *0     3     *0     *0       0    14|0     0.0   80.0       0 99.3G 85.0G   0|0   1|0    2k    56k  358 productset  PRI 14:11:49
    *0    *0     *0     *0       0    13|0     0.0   80.0       0 99.3G 85.0G   0|0   1|0  880b    55k  358 productset  PRI 14:11:50
"""


def get_metrics(server_ip,**strconn):
    strconn["host"]=server_ip
    rs = {}
    t_time = select_data("SELECT c_currtime FROM  dbmanager.t_dba_timediff ", **strconn)[0]
    rs['time'] = t_time
    metrics_data = select_data("""
        SHOW  GLOBAL STATUS WHERE variable_name IN  ('Threads_connected','Com_select','Com_delete','Com_insert','com_update','Bytes_received','Bytes_sent')""",
                               **strconn)
    for i in metrics_data:
        rs[i[0]] = i[1]
    # return rs['time']
    return rs


@click.command()
@click.option('--host', default='127.0.0.1', help='host to connect MySQL', type=str)
@click.option('--user', default='root', help='user to connect MySQL', type=str)
@click.option('--password', default='stressMysql', help='password to connect MySQL', type=str)
@click.option('--port', default=40001, help=' MySQL port', type=int)
@click.option('--count', default=600, help="display n times interval 1s ", type=int)
@click.option('--interval', default=1, help="display n times interval 1s ", type=int)
def print_monitor_data(count, host, port, user, password,interval):
    """get the information of  the MGR members ."""
    conn_str = {"host": host, "user": user, "password": password, "port": port,
                "db": "performance_schema"}
    vsql = """SELECT   CHANNEL_NAME , a. MEMBER_ID  , MEMBER_HOST ,
                        CASE
                             WHEN b.MEMBER_ID IS NOT NULL THEN 'Primary'
                             ELSE 'Secondary'
                             END    'role'                        ,
                        MEMBER_PORT ,
                        MEMBER_STATE
                 FROM   replication_group_members  a
                 LEFT JOIN  (SELECT variable_value AS 'MEMBER_ID'
                              FROM performance_schema. GLOBAL_STATUS
                              WHERE variable_name = 'GROUP_REPLICATION_PRIMARY_MEMBER'
                 ) b
                 ON a.MEMBER_ID=b.MEMBER_ID
                order by role asc """
    res = select_data(vsql, **conn_str)
    lhostinfo = []
    for i in res:
        host_ip = resolve_hostname(host, i[2])
        if host_ip=='127.0.0.1':
 	    host_ip=host
        lhostinfo.append(
            hostinfo(CHANNEL_NAME=i[0], MEMBER_ID=i[1], MEMBER_HOST=i[2], MEMBER_IP=host_ip, ROLE=i[3], MEMBER_PORT=i[4]
                     , MEMBER_STATE=i[5]))
    temp_metrics_data = {}
    # init the metrics value
    for i in lhostinfo:
        temp_metrics_data[i.MEMBER_IP] = get_metrics(i.MEMBER_IP,**conn_str)
    for t in range(count):
        click.secho(
            '---ROLE------MEMBER_IP------MEMBER_HOST -------MEMBER_PORT---MEMBER_STATE--------TIME-----THREADS--INSERT---UPDATE---SELECT---DELETE-----NETWORKIN--NETWORKOUT',
            fg='green', underline=True)
        for i in lhostinfo:
            metrics_data = get_metrics(i.MEMBER_IP,**conn_str)
            res = {}
            # com_select = long(metrics_data['Com_select']) - long(temp_metrics_data[i.MEMBER_IP]['Com_select'])
            # com_insert = long(metrics_data['Com_insert']) - long(temp_metrics_data[i.MEMBER_IP]['Com_insert'])
            # com_delete = long(metrics_data['Com_delete']) - long(temp_metrics_data[i.MEMBER_IP]['Com_delete'])
            # com_update = long(metrics_data['Com_update']) - long(temp_metrics_data[i.MEMBER_IP]['Com_update'])
            # network_in = long(metrics_data['Bytes_received']) - long(temp_metrics_data[i.MEMBER_IP]['Bytes_received'])
            # network_out = long(metrics_data['Bytes_sent']) - long(temp_metrics_data[i.MEMBER_IP]['Bytes_sent'])
            for current_val, before_val in zip(metrics_data.items(), temp_metrics_data[i.MEMBER_IP].items()):
                if current_val[0] != 'time':
                    res[current_val[0]] = long(current_val[1]) - long(before_val[1])
            print('%10s %10s %10s %10s %10s | %10s %5s %8s %8s %8s %8s | %10s %10s' % (
                i.ROLE, i.MEMBER_IP, i.MEMBER_HOST, i.MEMBER_PORT, i.MEMBER_STATE,
                metrics_data['time'][0], metrics_data['Threads_connected'], res['Com_insert'], res['Com_update'],
                res['Com_select'],
                res['Com_delete'], res['Bytes_received'], res['Bytes_sent']))
            temp_metrics_data[i.MEMBER_IP] = metrics_data
        time.sleep(interval)
        print (' ')


if __name__ == "__main__":
    print_monitor_data()
