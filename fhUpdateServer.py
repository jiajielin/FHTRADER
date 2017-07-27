# coding=utf-8

"""
Time : 2016/11/25 16:52
Author : Jia Jielin
Company: fhhy.co
File : fhUpdateServer.py
Description:

"""

import MySQLdb
from WindPy import w
import json
import logging
import time
import datetime
import logging.handlers
from fhConstant import *


class FhUpdateServer(object):
    """"""
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
        # Wind订阅ID
        self.reqId = -1
        # 时间间隔
        self.interval = 1.1
        # 记录器
        self.counter = 0

        # 工作开始时间
        self.startTime = '09:00:00'
        # 工作结束时间
        self.endTime = '15:10:00'

        # 期货参数字典 key:code, value:dict key:'weight','marginRatio'
        self.futuresParameter = {}

        # 日志类
        self.fhLog = fhLog

        print '--------- Update Data -------------'

        # 加载服务器及数据库信息
        self.loadSettings()
        # 数据库连接标识
        self.connectDbFlag = False
        # 连接数据库
        self.connectDb()

        # 连接Wind标记
        self.connectWindFlag = False
        # 连接Wind
        self.initWind()

        self.updateDict = {}    # 更新字典
        self.subscribeList = self.getObjectList()
        self.subscribeFlag = False

        self.updateTask()
        self.fhLog.info('结束更新')

    # ----------------------------------------
    def loadSettings(self):
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

    # ---------------------------------------
    def connectDb(self):
        if self.connectDbFlag == False:
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

    # ---------------------------------
    def reconnectDb(self):
        if self.isConnectedDb():
            pass
        else:
            self.fhLog.warning('数据库断连，重新连接')
            print u'重连数据库'
            self.connectDb()

    # ---------------------------
    def isConnectedDb(self):
        if self.connectDbFlag == False:
            return self.connectDbFlag
        try:
            self.db.ping()
        except MySQLdb.Error:
            self.connectDbFlag = False
            return self.connectDbFlag
        return self.connectDbFlag

    # -----------------------------------
    def initWind(self):
        self.w.start()
        self.connectWindFlag = True

    # ----------------------------
    def stopWind(self):
        self.w.stop()
        self.connectWindFlag = False

    # ----------------------------
    def updateTask(self):
        while 1:
            if self.inWorkTime():
                time.sleep(self.interval)
                if self.counter % 2 == 1:
                    self.updatePrice()
                if self.counter % 3 == 2:
                    self.updateAccount()
                if self.counter % 5 == 0:
                    self.updateSubscribe()
                self.counter += 1
                if self.counter >= 30:
                    self.counter = 0
            else:
                self.stopSubscribe()
                self.db.close()
                self.fhLog.info('更新程序结束')
                break

    # ----------------------------------
    def updatePrice(self):
        """更新持仓标的价格"""
        updateSql = """update products_details set price=%s where objectcode=%s"""
        updateList = []
        for code in self.updateDict:
            if 'price' in self.updateDict[code]:
                price = self.updateDict[code]['price']
                updateTup = tuple([price, code])
                updateList.append(updateTup)
            else:
                continue
        if updateList:
            updateTuple = tuple(updateList)
            try:
                if self.cursor.executemany(updateSql, updateTuple):
                    for code in self.updateDict:
                        self.updateDict[code] = {}
                    self.db.commit()
            except:
                self.reconnectDb()  # 重连db

    # --------------------------------
    def updateAccount(self):
        """更新账户信息"""
        # 更新sec
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
                    pass

                updateSql = """update products_account set total=%s, secvalue=%s where product=%s and accountclass='sec'"""
                updateList = []
                for key in totalDict:
                    updateList.append(tuple([totalDict[key], secValueDict[key], key]))
                if updateList:
                    updateTuple = tuple(updateList)
                    try:
                        if self.cursor.executemany(updateSql, updateTuple):
                            self.db.commit()
                    except:
                        pass
        except:
            pass

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
                    pass

                updateSql = """update products_account set margin=%s, todayprofit=%s where product=%s and accountclass='futures'"""
                updateList = []
                for key in balanceDict:
                    updateList.append(tuple([marginDict[key], todayProfitDict[key], key]))
                updateTuple = tuple(updateList)
                try:
                    if self.cursor.executemany(updateSql, updateTuple):
                        self.db.commit()
                except:
                    pass

        except:
            pass

    # ------------------------------
    def getFuturesParameterByPrefix(self, code):
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
    def getFuturesParameter(self, code):
        if len(code) > 2:
            retList = []
            if code in self.futuresParameter:
                weight = self.futuresParameter[code]['weight']
                marginRatio = self.futuresParameter[code]['marginRatio']
                return [weight, marginRatio]
            selectSql = """select weight, marginratio from futures_list where futurescode=%s"""
            selectTuple = tuple([code])
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

    # --------------------------------
    def updateSubscribe(self):
        """判断是否需重新订阅"""
        if self.subscribeFlag:
            if self.compareObjectList():
                pass
            else:
                self.stopSubscribe()
        else:
            self.subscribe()

    # ----------------------------------
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
            return ['-1']

    # -----------------------------------
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
    def subscribe(self):
        """如果订阅列表subscribeList有元素，则订阅，否则，重新获取subscribeList"""
        if self.subscribeList:
            self.initUpdateDict()
            self.fitReq()
            if self.connectWindFlag:
                data = self.w.wsq(self.req, self.wsqParam, func=self.wsqCallBack)
                if data.ErrorCode == 0:
                    self.reqId = data.RequestID
                    self.subscribeFlag = True
            else:
                print u'尚未连接Wind'
        else:
            self.subscribeList = self.getObjectList()

    # ------------------------------
    def fitReq(self):
        retStr = ''
        for code in self.subscribeList:
            retStr += code
            retStr += ','
        self.req = retStr

    # ------------------------
    def initUpdateDict(self):
        d = {}
        for code in self.subscribeList:
            d[code] = {}
        self.updateDict = d

    # -------------------------------------
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
    def inWorkTime(self):
        return datetime.datetime.now().strftime('%H:%m:%S') > self.startTime and datetime.datetime.now().strftime('%H:%m:%S') < self.endTime


# =========================================
if __name__ == '__main__':
    fhLog = logging.getLogger("updateTickLog")
    fhLog.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    fileHandler = logging.handlers.TimedRotatingFileHandler('logs/updateTickLog', 'midnight', 1, 50)
    fileHandler.suffix = "%Y%m%d"
    fileHandler.setFormatter(formatter)
    fhLog.addHandler(fileHandler)
    updateServer = FhUpdateServer()
    # raw_input('UpdateServer Stopped, Please press ENTER to continue...')
    # fhLog.info('更新程序结束')

