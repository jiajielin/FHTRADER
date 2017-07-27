# coding=utf-8

"""
Time : 2016/12/21 15:22
Author : Jia Jielin
Company: fhhy.co
File : task2History.py
Description:
task导入历史库脚本

"""

# system module
import MySQLdb as MS


db = MS.connect('10.82.12.134', 'fhhy0', 'fhhy0', 'fhhydb', charset='utf8')
cursor = db.cursor()

sql_select = """select taskno, subno, tasktime, finishtime, state, product, objectcode, objectname, objectclass, direction, buysell, taskprice, offset, transprice, taskvolume, transvolume, fundmanager, trader, remark, mainstate from task_flow_present"""
if cursor.execute(sql_select):
    insert_sql = """insert into task_flow_history VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    data = cursor.fetchall()
    print data
    for idata in data:
        taskNo = idata[0]
        subNo = idata[1]
        taskTime = idata[2]
        finishTime = idata[3]
        if finishTime == None:
            finishTime = '2099-12-31'
        state = idata[4]
        product = idata[5]
        objectCode = idata[6]
        objectName = idata[7]
        objectClass = idata[8]
        direction = idata[9]
        buySell = idata[10]
        taskPrice = idata[11]
        offset = idata[12]
        transPrice = idata[13]
        if transPrice == None:
            transPrice = 0.0
        taskVolume = idata[14]
        transVolume = idata[15]
        if transVolume == None:
            transVolume = 0
        fundManager = idata[16]
        trader = idata[17]
        remark = idata[18]
        if remark == None:
            remark = ''
        mainState = idata[19]
        insert_tup = tuple([taskNo, subNo, taskTime, finishTime, state, product, objectCode, objectName, objectClass, direction, buySell, taskPrice, offset, transPrice, taskVolume, transVolume, fundManager, trader, remark, mainState])
        select_sql = """select * from task_flow_history where taskno=%s and subno=%s"""
        select_tup = tuple([taskNo, subNo])
        if cursor.execute(select_sql, select_tup):
            delete_sql = """delete from task_flow_present where taskno=%s and subNo=%s"""
            delete_tup = tuple([taskNo, subNo])
            if cursor.execute(delete_sql, delete_tup):
                db.commit()
            continue
        if cursor.execute(insert_sql, insert_tup):
            db.commit()
            delete_sql = """delete from task_flow_present where taskno=%s and subNo=%s"""
            delete_tup = tuple([taskNo, subNo])
            if cursor.execute(delete_sql, delete_tup):
                db.commit()
db.close()


