# coding=utf-8

"""
Time : 2016/11/21 14:02
Author : Jia Jielin
Company: fhhy.co
File : fhUpdateTick.py
Description:

"""


import MySQLdb
from WindPy import w
import json
import logging
import time
import datetime
from threading import *
import logging.handlers

from fhConstant import *

class FhUpdateTick(object):
    """数据更新类，每次开启订阅所有信息"""
     # 订阅wsq时传入的字段列表
    wsqParamMap = {}
    wsqParamMap['RT_LAST'] = 'price'  # 现价
    # wsqParamMap['rt_last_vol'] = 'volume'  # 现量

    # wsqParamMap['rt_open'] = 'openPrice'  # 开盘价
    # wsqParamMap['rt_high'] = 'highPrice'  # 最高价
    # wsqParamMap['rt_low'] = 'lowPrice'  # 最低价
    # wsqParamMap['rt_pre_close'] = 'preClosePrice'  # 前收

    # wsqParamMap['RT_PCT_CHG'] = 'changeRatio'  # 涨跌幅
    # wsqParamMap['RT_CHG'] = 'change'  # 涨跌
    # wsqParamMap['RT_HIGH'] = 'high'     # 当天最高

    wsqParam = ','.join(wsqParamMap.keys())
    def __init__(self):
        self.w = w
        # 请求代码字符串
        self.req = ''
        # 数据订阅ID
        self.reqId = -1
        # 数据订阅更新判断时间
        self.updateInterVal = 5.1

        # 期货参数字典 key:code, value:dict key:'weight','marginRatio'
        self.futuresParameter = {}

        self.fhLog = fhLog
        self.loadSetting()
        self.connectDbFlag = False
        self.connectDb()

        self.initWind()
        self.subscribeList = self.getObjectList()
        self.subscribeFlag = False

        # 持仓查询并根据结果更改订阅
        self.updateFlag = True
        self.onUpdateTimer = Thread(target=self.onTimerThread)

        # 数据库连接判断线程
        self.reconnectDbFlag = False
        self.isConnectedDbInterval = 1.9
        # self.onReconnectDbTimer = Thread(target=self.onReconnectDbThread)

        # 插入数据队列
        # self.updateQueue = Queue.Queue()
        # 更新字典，并获取之
        self.updateDict = {}
        self.initUpdateDict()

        # 更新数据扫描时间
        self.updateDbInterval = 2.1
        self.updateDbTimer = Thread(target=self.onUpdateDbThread)

        # 更新账户信息
        self.updateAccountInterval = 3.1
        self.updateAccountTimer = Thread(target=self.onUpdateAccount)

        # 启动进程
        self.onUpdateTimer.start()
        self.updateDbTimer.start()
        self.updateAccountTimer.start()
        # self.onReconnectDbTimer.start()
        self.onReconnectDbThread()

    # ------------------------------------------
    def initUpdateDict(self):
        d = {}
        for code in self.subscribeList:
            d[code] = {}
        self.updateDict = d

    # -------------------------------------
    def onTimerThread(self):
        while self.updateFlag:
            time.sleep(self.updateInterVal)
            print datetime.datetime.now()
            print self.subscribeList
            # print 'subscribeFlag:' + repr(self.subscribeFlag)
            if self.subscribeFlag:
                if self.compareObjectList():
                    pass
                else:
                    self.stopSubscribe()
            else:
                # print 11
                self.subscribe()

    # -----------------------------------
    def loadSetting(self):
        try:
            f = file("setting.json")
            setting = json.load(f)
            f.close()
            self.dbHost = setting['dbHost']
            self.dbPort = setting['dbPort']
            if 'dbUser' in setting:
                self.user = setting['dbUser']
            else:
                self.user = 'fhhy0'
            if 'dbPwd' in setting:
                self.password = setting['dbPwd']
            else:
                self.password = 'fhhy0'
            if 'dbName' in setting:
                self.dbName = setting['dbName']
            else:
                self.dbName = 'fhhydb'
            self.dbTimeout = setting['dbTimeout']
            self.host = setting['host']
            self.port = setting['port']
            self.bufSize = setting['bufSize']
            self.taskBufSize = setting['taskBufSize']
            self.initFlag = True
            self.fhLog.info('加载配置文件成功')
        except:
            self.dbHost = '10.82.12.134'
            self.dbPort = 3306
            self.user = 'fhhy0'
            self.password = 'fhhy0'
            self.dbName = 'fhhydb'
            self.dbTimeout = 1
            self.host = 'localhost'
            self.port = 3333
            self.bufSize = 20480
            self.taskBufSize = 10
            self.fhLog.error('加载配置文件失败，已开启默认值，请判断是否正确')

    # ------------------------------------------
    def getObjectList(self):
        selectSql = """SELECT distinct objectcode FROM products_details"""
        retList = []
        try:
            if self.cursor.execute(selectSql):
                data = self.cursor.fetchall()
                # print 'getObjectList:' + repr(data)
                for idata in data:
                    retList.append(idata[0])
            return retList
        except:
            return retList

    # ---------------------------
    def compareObjectList(self):
        """比较新旧订阅列表是否一致，若一致，则返回True，若不一致，则返回False，并更新订阅列表"""
        newList = self.getObjectList()
        compareFlag = True
        for item in newList:
            if item not in self.subscribeList:
                compareFlag = False
                break
        if compareFlag:
            for item in self.subscribeList:
                if item not in newList:
                    compareFlag = False
                    break
        if compareFlag == False:
            self.subscribeList = newList
        return compareFlag

    # ---------------------------
    def subscribe(self):
        if self.subscribeList:
            self.initUpdateDict()
            self.fitReq()
            if self.connectWindFlag:
                data = self.w.wsq(self.req, self.wsqParam, func=self.wsqCallBack)
                # print data
                if data.ErrorCode == 0:
                    self.reqId = data.RequestID
                    self.subscribeFlag = True
            else:
                print u'尚未连接Wind'
        else:
            self.subscribeList = self.getObjectList()

    # ------------------------------
    def wsqCallBack(self, data):
        if data.ErrorCode == 0:
            codeList = data.Codes
            for i in range(0, len(codeList)):
                if type(codeList[i]) == unicode:
                    code = codeList[i].encode('utf8')
                else:
                    code = codeList[i]
                if codeList[i] not in self.updateDict:
                    self.updateDict[codeList[i]] = {}
                d = {}

                for n in range(0, len(data.Fields)):
                    if type(data.Fields[n]) == unicode:
                         field = data.Fields[n]
                    else:
                        field = data.Fields[n]
                    d[self.wsqParamMap[field]] = data.Data[n][i]
                self.updateDict[codeList[i]] = d
                # self.updateQueue.put(d)

    # ----------------------------
    def onUpdateDbThread(self):
        updateSql1 = """update products_details set price=%s where objectcode=%s"""
        # updateSql2 = """update produtcts_account set"""
        while 1:
            updateList = []
            for code in self.updateDict:
                if 'price' in self.updateDict[code]:
                    price = self.updateDict[code]['price']
                    updateTup = tuple([price, code])
                    updateList.append(updateTup)
                else:
                    continue

            # while self.updateQueue.qsize():
            #     d = self.updateQueue.get()
            #     if 'objectCode' in d and 'price' in d:
            #         code = d['objectCode']
            #         price = d['price']
            #         updateTup = tuple([price, code])
            #         updateList.append(updateTup)
            if updateList:
                updateTuple = tuple(updateList)
                try:
                    if self.cursor.executemany(updateSql1, updateTuple):
                        for code in self.updateDict:
                            self.updateDict[code] = {}
                        self.db.commit()
                except:
                    pass

            time.sleep(self.updateDbInterval)

    # --------------------
    def onUpdateAccount(self):
        # selectSql = """select distinct product from products_account where state='运作中'"""
        # productList = []
        # if self.cursor.execute(selectSql):
        #     data = self.cursor.fetchall()
        #     for idata in data:
        #         productList = idata[0]
        # if productList:
        # 更新sec
        while 1:
            selectSql = """select product, price, volume from products_details where objectclass='sec'"""
            secValueDict = {}
            try:
                if self.cursor.execute(selectSql):
                    data = self.cursor.fetchall()
                    for idata in data:
                        product = idata[0]
                        if product not in secValueDict:
                            secValueDict[product] = 0
                        price = idata[1]
                        volume = idata[2]
                        secValueDict[product] += price * volume
                    selectSql = """select product, balance from products_account where accountclass='sec'"""
                    totalDict = {}
                    try:
                        if self.cursor.execute(selectSql):
                            data = self.cursor.fetchall()
                            for idata in data:
                                product = idata[0]
                                balance = idata[1]
                                if product in secValueDict:
                                    if product not in totalDict:
                                        totalDict[product] = balance + secValueDict[product]
                    except:
                        time.sleep(self.updateAccountInterval)
                        continue

                    updateSql = """update products_account set total=%s, secvalue=%s where product=%s and accountclass='sec'"""
                    updateList = []
                    for key in totalDict:
                        updateList.append(tuple([totalDict[key], secValueDict[key], key]))
                    updateTuple = tuple(updateList)
                    try:
                        if self.cursor.executemany(updateSql, updateTuple):
                            self.db.commit()
                    except:
                        time.sleep(self.updateAccountInterval)
                        continue
                # 更新futures
                selectSql = """select product, objectcode, direction, volume, costprice, price, settleprice, todaybuyvolume, todaybuyprice from products_details where objectclass='futures'"""
                marginDict = {}
                todayProfitDict = {}
                try:
                    if self.cursor.execute(selectSql):
                        data = self.cursor.fetchall()
                        for idata in data:
                            product = idata[0]
                            if product not in marginDict:
                                marginDict[product] = 0
                            if product not in todayProfitDict:
                                todayProfitDict[product] = 0
                            objectCode = idata[1]
                            direction = idata[2]
                            volume = idata[3]
                            costPrice = idata[4]
                            price = idata[5]
                            settlePrice = idata[6]
                            todayBuyVolume = idata[7]
                            todayBuyPrice = idata[8]
                            [weight, marginRatio] = self.getFuturesParameter(objectCode)
                            marginDict[product] += price * volume * marginRatio * weight
                            if direction == TRADE_BUY:
                                todayProfitDict[product] += (price - settlePrice) * (volume - todayBuyVolume) * weight + (price - todayBuyPrice) * todayBuyVolume * weight
                            else:
                                todayProfitDict[product] += (settlePrice - price) * (volume - todayBuyVolume) * weight + (todayBuyPrice - price) * todayBuyVolume * weight
                except:
                    time.sleep(self.updateAccountInterval)
                    continue

                    balanceDict = {}
                    selectSql = """select product, balance from products_account where accountclass='futures'"""
                    try:
                        if self.cursor.execute(selectSql):
                            data = self.cursor.fetchall()
                            for idata in data:
                                product = idata[0]
                                balance = idata[1]
                                if product not in balanceDict and product in todayProfitDict:
                                    balanceDict[product] = balance
                    except:
                        time.sleep(self.updateAccountInterval)
                        continue

                    updateSql = """update products_account set margin=%s, todayprofit=%s where product=%s and accountclass='futures'"""
                    updateList = []
                    for key in balanceDict:
                        updateList.append(tuple([marginDict[key], todayProfitDict[key], key]))
                    updateTuple = tuple(updateList)
                    try:
                        if self.cursor.executemany(updateSql, updateTuple):
                            self.db.commit()
                    except:
                        time.sleep(self.updateAccountInterval)
                        continue
            except:
                time.sleep(self.updateAccountInterval)
                continue

            time.sleep(self.updateAccountInterval)

    # ----------------------------------
    def stopSubscribe(self):
        if self.reqId != -1:
            self.w.cancelRequest(self.reqId)
            self.updateDict = {}
            self.subscribeFlag = False
            self.reqId = -1
        else:
            print u'已停止订阅，勿重复操作'
        return 0

    # ----------------------
    def fitReq(self):
        retStr = ''
        for code in self.subscribeList:
            retStr += code
            retStr += ','
        self.req = retStr

    # ------------------------
    def getFuturesParameter(self, code):
        if len(code) > 2:
            retList = []
            if code in self.futuresParameter:
                weight = self.futuresParameter[code]['weight']
                marginRatio = self.futuresParameter[code]['marginRatio']
                return [weight, marginRatio]
            numTag = 0
            for i in range(0, len(code)):
                if code[i] >= '0' and code[i] <= '9':
                    numTag = i
                    break
            if numTag:
                prefix = code[0:numTag]
                selectSql = """select weight, marginratio from parameter_futures where prefix=%s"""
                selectTuple = tuple([prefix])
                try:
                    if self.cursor.execute(selectSql, selectTuple):
                        data = self.cursor.fetchone()
                        weight = data[0]
                        marginRatio = data[1]
                        self.futuresParameter[code] = {}
                        self.futuresParameter[code]['weight'] = weight
                        self.futuresParameter[code]['marginRatio'] = marginRatio
                        return [weight, marginRatio]
                except:
                    return [1, 1]
            else:
                return [1, 1]
        else:
            return [1, 1]

    # ---------------------------
    def connectDb(self):
        # try:
        #     db = MySQLdb.connect(host=self.dbHost, user=self.user, passwd=self.password, db=self.dbName,
        #                          port=self.dbPort, connect_timeout=self.dbTimeout)
        #     cursor = db.cursor()
        #     return [db, cursor]
        # except:
        #     return []

        if self.connectDbFlag == False:
            # print 4
            try:
                self.db = MySQLdb.connect(host=self.dbHost, user=self.user, passwd=self.password, db=self.dbName, port=self.dbPort)
                self.cursor = self.db.cursor()
                self.fhLog.info('数据库连接成功')
            except:
                self.fhLog.error('数据库连接失败')
                self.connectDbFlag = False
                return False
            self.connectDbFlag = True
            return True
        else:
            if self.isConnectedDb():
                self.fhLog.warning('数据库已连接')
            else:
                try:
                    self.db = MySQLdb.connect(host=self.dbHost, user=self.user, passwd=self.password, db=self.dbName,
                                              port=self.dbPort, connect_timeout=self.dbTimeout)
                    self.cursor = self.db.cursor()
                    self.fhLog.info('数据库连接成功')
                except:
                    self.fhLog.error('数据库连接失败')
                    self.connectDbFlag = False
                    return False
                self.connectDbFlag = True
                return True
            return True

    # -----------------------
    def disConnectDb(self, db):
        db.close()

    # ----------------------------------
    def isConnectedDb(self):
        if self.connectDbFlag == False:
            # print "False"
            return self.connectDbFlag
        try:
            self.db.ping()
        except MySQLdb.Error:
            self.connectDbFlag = False
            # print 'isConnectedDb:False'
            return self.connectDbFlag
        return self.connectDbFlag

    # ------------------------------------
    def reconnectDb(self):
        if self.reconnectDbFlag == False:
            self.reconnectDbFlag = True
            if self.isConnectedDb():
                pass
            else:
                self.connectDb()
            self.reconnectDbFlag = False
        else:
            pass
    # ---------------------------
    def onReconnectDbThread(self):
        while 1:
            time.sleep(self.isConnectedDbInterval)
            if self.isConnectedDb() == False:
                self.reconnectDb()

    # -------------------------------
    def initWind(self):
        self.w.start()
        self.connectWindFlag = True

    # ----------------------------
    def stopWind(self):
        self.w.stop()
        self.connectWindFlag = False

    # ----------------------------
    def stop(self):
        self.updateDbTimer.join()
        self.updateAccountTimer.join()
        time.sleep(1)
        self.stopSubscribe()

# ===============================================
if __name__ == '__main__':
    fhLog = logging.getLogger("updateTickLog")
    fhLog.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    fileHandler = logging.handlers.TimedRotatingFileHandler('updateTickLog', 'midnight', 1, 50)
    fileHandler.suffix = "%Y%m%d"
    fileHandler.setFormatter(formatter)
    fhLog.addHandler(fileHandler)
    updateServer = FhUpdateTick()
    # raw_input('UpdateTickServer Stopped, Please press ENTER to continue...')
    # fhLog.info('更新程序结束')