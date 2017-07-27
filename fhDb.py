# coding=utf-8

"""
Time : 2016/7/25 14:21
Author : Jia Jielin
Company: fhhy.co
File : fhDb.py
Description:

"""

# system module
import MySQLdb
# third party module
import json
# own module
from fhConstant import *
import time
from eventEngine import *
from fhGateway import FhLogData, FhOptionalData
from datetime import datetime


class DbUtils(object):
    """数据库类操作"""

    def __init__(self, eventEngine=None, isLog=False):
        self.connectFlag = False
        self.isLog = isLog
        self.eventEngine = eventEngine
        self.loadDbSetting()
        self.connectDb()

    # ------------------------------------------
    def loadDbSetting(self):
        try:
            f = file("setting.json")
            setting = json.load(f)
            f.close()
            self.host = setting['dbHost']
            self.port = setting['dbPort']
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
        except:
            self.host = '10.82.12.134'
            self.port = 3306
            self.user = 'fhhy0'
            self.password = 'fhhy0'
            self.dbName = 'fhhydb'
            self.dbTimeout = 1

    # -------------------------------------------
    def connectDb(self):
        if self.connectFlag == False:
            try:
                self.db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.dbName,
                                          port=self.port, connect_timeout=self.dbTimeout)
                self.cursor = self.db.cursor()
            except MySQLdb.Error:
                self.onLog(u'尝试连接失败')
                self.connectFlag = False
                return False
            self.connectFlag = True
            self.onLog(u'连接成功')
            return True
        self.onLog(u'DB已连接')
        return True

    # -----------------------------------------------
    def isConnected(self):
        if self.connectFlag == False:
            return self.connectFlag
        try:
            self.db.ping()
        except MySQLdb.Error:
            self.connectFlag = False
            self.onLog(u'DB连接异常')
            return self.connectFlag
        return self.connectFlag

    # ------------------------------------------------
    def onLog(self, logContent):
        """日志推送"""
        log = FhLogData()
        log.gatewayName = 'DataBase'
        log.logContent = logContent
        event1 = Event(type_=EVENT_LOG)
        event1.dict_['data'] = log
        if self.isLog:
            self.eventEngine.put(event1)

    # ----------------------------
    def getUserVerify(self, user, encPwd):
        sql_select = """select authority from userverify where loginname=%s and pwd=%s"""
        selectTuple = tuple([user, encPwd])
        if self.connectFlag and self.isConnected():
            if self.cursor.execute(sql_select, selectTuple):
                data = self.cursor.fetchone()
                return data[0]
            return VERIFY_NOUSER
        else:
            self.onLog(u'DB未连接或连接异常')
        return DB_DISCONNECT

    # -------------------------------------------------
    def getProductsByManager(self, user=None):
        """state: 表示产品状态，PRODUCT_ON 运作中   PRODUCT_OFF 已结束"""
        if user:
            sql_select = """select product from products_info WHERE fundmanager=%s and state='运作中'"""
            sql_tuple = tuple([user])
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select, sql_tuple):
                    data = self.cursor.fetchall()
                    ldata = [data[i][0] for i in range(0, len(data))]
                    return ldata
            else:
                self.onLog(u'DB未连接或连接异常')
        else:
            sql_select = """select product from products_info WHERE state='运作中'"""
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select):
                    data = self.cursor.fetchall()
                    ldata = [data[i][0] for i in range(0, len(data))]
                    return ldata
            else:
                self.onLog(u'DB未连接或连接异常')
        return []

    # ------------------------------------------------------
    def getProductsRatioByManager(self, user=None):
        """state: 表示产品状态，PRODUCT_ON 运作中   PRODUCT_OFF 已结束"""
        if user:
            sql_select = """select product, secratio, futuresratio from products_info WHERE fundmanager=%s and state='运作中'"""
            sql_tuple = tuple([user])
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select, sql_tuple):
                    data = self.cursor.fetchall()
                    ldata = [{'product': data[i][0], 'secRatio':data[i][1], 'futuresRatio':data[i][2]} for i in range(0, len(data))]
                    return ldata
            else:
                self.onLog(u'DB未连接或连接异常')
        else:
            sql_select = """select product from products_info WHERE state='运作中'"""
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select):
                    data = self.cursor.fetchall()
                    ldata = [data[i][0] for i in range(0, len(data))]
                    return ldata
            else:
                self.onLog(u'DB未连接或连接异常')
        return []

    # ------------------------------------------------------
    def getProducts(self, state=PRODUCT_ON):
        """state: 表示产品状态，PRODUCT_ON 运作中   PRODUCT_OFF 已结束"""
        if state == PRODUCT_ON:
            sql_select = """select product, perserving from products_info WHERE state='运作中'"""
        elif state == PRODUCT_OFF:
            sql_select = """select product, perserving from products_info WHERE state='已结束'"""
        else:
            return []
        if self.connectFlag and self.isConnected():
            if self.cursor.execute(sql_select):
                data = self.cursor.fetchall()
                ldata = [data[i][0] for i in range(0, len(data))]

                return data
        else:
            self.onLog(u'DB未连接或连接异常')
        return []

    # ------------------------------------------------------
    def getProductInfo(self, product):
        # print type(product)
        sql_select = """select product, fundmanager, trader, startdate, finishdate, fundscale, secratio, futuresratio, perserving, seccompany, futurescompany, state from products_info WHERE product=%s"""
        insertProduct = tuple([product])
        if self.connectFlag and self.isConnected():
            if self.cursor.execute(sql_select, insertProduct):
                data = self.cursor.fetchone()
                return data
        else:
            self.onLog(u'DB未连接或连接异常')
        return []

    # --------------------------------
    def getAccountInfo(self, product):
        retDict = {}
        if product:
            selectSql = """select accountclass, total, balance, secvalue, margin from products_account where product=%s"""
            selectTuple = tuple([product])
            if self.cursor.execute(selectSql, selectTuple):
                data = self.cursor.fetchall()
                for idata in data:
                    accountClass = idata[0]
                    total = idata[1]
                    balance = idata[2]
                    secValue = idata[3]
                    margin = idata[4]
                    retDict[accountClass] = {}
                    retDict[accountClass]['total'] = total
                    retDict[accountClass]['balance'] = balance
                    retDict[accountClass]['secValue'] = secValue
                    retDict[accountClass]['margin'] = margin
        return retDict

    # ------------------------------
    def getProductDetails(self, product=None):
        """返回结构{product1:[{...}, {...}],  product2:[{...}, {...}],...}"""
        retDict = {}
        if product:
            sql_select = """select product, objectcode, objectname, objectclass, direction, volume, costprice, availablevolume from products_details where product=%s"""
            sqlTuple = tuple([product])
            retDict[product] = []
            if self.cursor.execute(sql_select, sqlTuple):
                data = self.cursor.fetchall()
                for i in range(0, len(data)):
                    tmpDict = {}
                    tmpDict['product'] = data[i][0]
                    tmpDict['objectCode'] = data[i][1]
                    tmpDict['objectName'] = data[i][2]
                    tmpDict['objectClass'] = data[i][3]
                    tmpDict['direction'] = data[i][4]
                    tmpDict['volume'] = data[i][5]
                    tmpDict['costPrice'] = data[i][6]
                    tmpDict['availableVolume'] = data[i][7]
                    retDict[product].append(tmpDict)
        else:
            sql_select = """select product, objectcode, objectname, objectclass, direction, volume, costprice, availablevolume from products_details"""
            if self.cursor.execute(sql_select):
                data = self.cursor.fetchall()
                for i in range(0, len(data)):
                    product = data[i][0]
                    if product not in retDict:
                        retDict[product] = []
                    tmpDict = {}
                    tmpDict['product'] = data[i][0]
                    tmpDict['objectCode'] = data[i][1]
                    tmpDict['objectName'] = data[i][2]
                    tmpDict['objectClass'] = data[i][3]
                    tmpDict['direction'] = data[i][4]
                    tmpDict['volume'] = data[i][5]
                    tmpDict['costPrice'] = data[i][6]
                    tmpDict['availableVolume'] = data[i][7]
                    retDict[product].append(tmpDict)
        return retDict

    # ------------------------------------------------------
    def getProductPosition(self, product=None):
        """返回结构{product1:{},product2:{,...}}"""
        retDict = {}
        if product:
            sql_select = """select product, objectcode, objectname, objectclass, direction, volume, costprice, availablevolume, settleprice, todaybuyprice, todaybuyvolume, remark from products_details where product=%s"""
            sqlTuple = tuple([product])
            retDict[product] = []
            if self.cursor.execute(sql_select, sqlTuple):
                data = self.cursor.fetchall()
                # self.db.commit()
                retDict[product] = []
                for i in range(0, len(data)):
                    tem = {}
                    tem['product'] = data[i][0]
                    tem['objectCode'] = data[i][1]
                    tem['objectName'] = data[i][2]
                    tem['objectClass'] = data[i][3]
                    tem['direction'] = data[i][4]
                    tem['volume'] = data[i][5]
                    tem['costPrice'] = data[i][6]
                    tem['availableVolume'] = data[i][7]
                    tem['settlePrice'] = data[i][8]
                    tem['todayBuyPrice'] = data[i][9]
                    tem['todayBuyVolume'] = data[i][10]
                    tem['remark'] = data[i][11]
                    retDict[product].append(tem)
        else:
            sql_select = """select product, objectcode, objectname, objectclass, direction, volume, costprice, availablevolume, settleprice, todaybuyprice, todaybuyvolume, remark from products_details"""
            if self.cursor.execute(sql_select):
                # self.db.commit()
                data = self.cursor.fetchall()
                for i in range(0, len(data)):
                    product = data[i][0]
                    if product not in retDict:
                        retDict[product] = []
                    tem = {}
                    tem['product'] = data[i][0]
                    tem['objectCode'] = data[i][1]
                    tem['objectName'] = data[i][2]
                    tem['objectClass'] = data[i][3]
                    tem['direction'] = data[i][4]
                    tem['volume'] = data[i][5]
                    tem['costPrice'] = data[i][6]
                    tem['availableVolume'] = data[i][7]
                    tem['settlePrice'] = data[i][8]
                    tem['todayBuyPrice'] = data[i][9]
                    tem['todayBuyVolume'] = data[i][10]
                    tem['remark'] = data[i][11]
                    retDict[product].append(tem)
        return retDict

    # ------------------------------------------------------
    def getProductAccount(self, product=None):
        """返回结构,list,每个元素为dict"""
        retDict = []
        if product:
            sql_select = """select product, accountclass, total, balance, available, secvalue, margin, todayprofit from products_account where product=%s"""
            sqlTuple = tuple([product])
            if self.cursor.execute(sql_select, sqlTuple):
                data = self.cursor.fetchall()
                for i in range(0, len(data)):
                    tem = {}
                    tem['product'] = data[i][0]
                    tem['accountClass'] = data[i][1]
                    tem['total'] = data[i][2]
                    tem['balance'] = data[i][3]
                    tem['available'] = data[i][4]
                    tem['secValue'] = data[i][5]
                    tem['margin'] = data[i][6]
                    tem['todayProfit'] = data[i][7]
                    retDict.append(tem)
        else:
            sql_select = """select product, accountclass, total, balance, available, secvalue, margin, todayprofit from products_account"""
            if self.cursor.execute(sql_select):
                data = self.cursor.fetchall()
                for i in range(0, len(data)):
                    tem = {}
                    tem['product'] = data[i][0]
                    tem['accountClass'] = data[i][1]
                    tem['total'] = data[i][2]
                    tem['balance'] = data[i][3]
                    tem['available'] = data[i][4]
                    tem['secValue'] = data[i][5]
                    tem['margin'] = data[i][6]
                    tem['todayProfit'] = data[i][7]
                    retDict.append(tem)
        return retDict

    # ------------------------------------------------------
    def getSecList(self, segment, limit=0):
        if len(segment):
            if segment[0] >= '0' and segment <= '9':
                if limit:
                    sql_select = """SELECT * FROM sec_list WHERE secid LIKE %s LIMIT %s"""
                    inp = ([segment + '%', limit])
                else:
                    sql_select = """SELECT * FROM sec_list WHERE secid LIKE %s"""
                    inp = ([segment + '%'])
            else:
                if limit:
                    sql_select = """SELECT * FROM sec_list WHERE secletter LIKE %s LIMIT %s"""
                    inp = (['%' + segment + '%', limit])
                else:
                    sql_select = """SELECT * FROM sec_list WHERE secletter LIKE %s"""
                    inp = (['%' + segment + '%'])
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select, inp):
                    data = self.cursor.fetchall()
                    return [[data[i][j] for j in range(0, len(data[i]))] for i in range(0, len(data))]
            else:
                self.onLog(u'DB未连接或连接异常')
        else:
            sql_select = """SELECT * FROM sec_list"""
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select):
                    data = self.cursor.fetchall()
                    return [[data[i][j] for j in range(0, len(data[i]))] for i in range(0, len(data))]
            else:
                self.onLog(u'DB未连接或连接异常')
        return []

    # -----------------------------------------------------------
    def getFuturesPositionInfo(self, product):
        retDict = {}
        if product:
            selectSql = """select direction, volume from products_details where product=%s and objectclass='futures'"""
            selectTuple = tuple([product])
            if self.cursor.execute(selectSql, selectTuple):
                data = self.cursor.fetchall()
                longVolume = 0
                shortVolume = 0
                for idata in data:
                    direction = idata[0]
                    volume = idata[1]
                    if direction == TRADE_BUY:
                        longVolume += volume
                    elif direction == TRADE_SELL:
                        shortVolume += volume
                retDict[TRADE_BUY] = longVolume
                retDict[TRADE_SELL] = shortVolume
        return retDict

    # -----------------------------------------------------------
    def getFuturesList(self, segment, limit=0):
        if len(segment):
            if segment[0] >= '0' and segment <= '9':
                if limit:
                    sql_select = """SELECT * FROM futures_list WHERE futurescode LIKE %s LIMIT %s"""
                    inp = ([segment + '%', limit])
                else:
                    sql_select = """SELECT * FROM futures_list WHERE futurescode LIKE %s"""
                    inp = ([segment + '%'])
            else:
                if limit:
                    sql_select = """SELECT * FROM futures_list WHERE futuresletter LIKE %s LIMIT %s"""
                    inp = (['%' + segment + '%', limit])
                else:
                    sql_select = """SELECT * FROM futures_list WHERE futuresletter LIKE %s"""
                    inp = (['%' + segment + '%'])
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select, inp):
                    data = self.cursor.fetchall()
                    return [[data[i][j] for j in range(0, len(data[i]))] for i in range(0, len(data))]
            else:
                self.onLog(u'DB未连接或连接异常')
        else:
            sql_select = """SELECT * FROM futures_list"""
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select):
                    data = self.cursor.fetchall()
                    return [[data[i][j] for j in range(0, len(data[i]))] for i in range(0, len(data))]
            else:
                self.onLog(u'DB未连接或连接异常')
        return []
    # --------------------------------------------------------
    def updateProduct(self, productBuffer):
        if len(productBuffer) == 12:
            sql_update = """update products_info set fundmanager=%s, trader=%s, startdate=%s, finishdate=%s, fundscale=%s,secratio=%s, futuresratio=%s, perserving=%s, seccompany=%s, futurescompany=%s, state=%s  where product=%s"""
            update = []
            # for i in range(0, len(productBuffer)):
            #     update.append(productBuffer[(i + 1) % len(productBuffer)])
            for i in range(0, len(productBuffer)):
                update.append(productBuffer[(i+1) % len(productBuffer)])
            tup = tuple(update)
            if self.connectFlag and self.isConnected():
                try:
                    if self.cursor.execute(sql_update, tup):
                        self.db.commit()
                        return 1
                except:
                    return 0
            else:
                self.onLog(u'DB未连接或连接异常')
            return 0

    # --------------------------------
    def getExchange(self, code):
        if len(code) >= 2:
            prefix = code[0:2] + '%'
            selectSql = """select suffix from exchange_mapping where prefix like %s"""
            selectTuple = tuple([prefix])
            if self.cursor.execute(selectSql, selectTuple):
                suffix = self.cursor.fetchone()
            codeSplit = code.split('.')
        return code

    # ---------------------------------
    def getFuturesParameter(self, code):
        d = {}
        if len(code) > 2:
            selectSql = """select marginratio, weight from futures_list where futurescode=%s"""
            selectTuple = tuple([code])
            if self.cursor.execute(selectSql, selectTuple):
                data = self.cursor.fetchone()
                d['marginRatio'] = data[0]
                d['weight'] = data[1]
        return d

    # -----------------------------
    def saveSecValue(self, product, value):
        selectSql = """select balance from products_account where product=%s and accountclass='sec'"""
        selectTuple = tuple([product])
        if self.cursor.execute(selectSql, selectTuple):
            data = self.cursor.fetchone()
            balance = data[0]
            total = balance + value
            updateSql = """update products_account set total=%s, secvalue=%s where product=%s and accountclass='sec'"""
            updateTuple = tuple([total, value, product])
            if self.cursor.execute(updateSql, updateTuple):
                self.db.commit()

    # -------------------------------
    def saveFuturesTodayInfo(self, product, margin, todayProfit):
        updateSql = """update products_account set todayprofit=%s, margin=%s where product=%s and accountclass='futures'"""
        updateTuple = tuple([todayProfit, margin, product])
        if self.cursor.execute(updateSql, updateTuple):
            self.db.commit()

    # --------------------------------------
    def saveProduct(self, productBuffer):
        if len(productBuffer) == 12:
            sql_insert = """insert into products_info (product, fundmanager, trader, startdate, finishdate, fundscale, secratio, futuresratio, perserving, seccompany, futurescompany, state) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            ins = []
            for i in range(0, len(productBuffer)):
                ins.append(productBuffer[i])
            tup = tuple(ins)
            if self.connectFlag and self.isConnected():
                try:
                    if self.cursor.execute(sql_insert, tup):
                        self.db.commit()
                        return 1
                except Exception, e:
                    return 0
            else:
                self.onLog(u'DB未连接或连接异常')
            return 0

    # -----------------------------------------------------
    def addAccount(self, productAccount):
        if 'product' in productAccount and 'total' in productAccount and 'secRatio' in productAccount and 'futuresRatio' in productAccount:
            product = productAccount['product']
            total = productAccount['total']
            secRatio = productAccount['secRatio']
            futuresRatio = productAccount['futuresRatio']
            secTotal = secRatio * total
            futuresTotal = futuresRatio * total
            # 建立股票账户
            if secRatio > 0.0:
                selectSql = """select * from products_account where product=%s and accountclass='sec'"""
                selectTuple = tuple([product])
                if self.cursor.execute(selectSql, selectTuple):
                    pass
                else:
                    insertSql = """insert into products_account values(%s, %s, %s, %s, %s, %s, %s, %s)"""
                    insertTuple = tuple([product, 'sec', secTotal, secTotal, secTotal, 0, 0, 0])
                    if self.cursor.execute(insertSql, insertTuple):
                        self.db.commit()
                    else:
                        return 0
            # 建立期货账户
            if futuresRatio:
                selectSql = """select * from products_account where product=%s and accountclass='futures'"""
                selectTuple = tuple([product])
                if self.cursor.execute(selectSql, selectTuple):
                    pass
                else:
                    insertSql = """insert into products_account values(%s, %s, %s, %s, %s, %s, %s, %s)"""
                    insertTuple = tuple([product, 'futures', futuresTotal, futuresTotal, futuresTotal, 0, 0, 0])
                    if self.cursor.execute(insertSql, insertTuple):
                        self.db.commit()
                    else:
                        return 0

            return 1
        else:
            return 0

    # -----------------------------------------------------
    def getSecIdName(self, segment, option=0):
        if option:
            sql_select = """SELECT secid,secname FROM sec_list WHERE secletter LIKE %s"""
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select, (['%' + segment + '%'])):
                    ret = self.cursor.fetchone()
                    return [ret[0], ret[1]]
            else:
                self.onLog(u'DB未连接或连接异常')
        else:
            sql_select = """SELECT secid, secname FROM sec_list WHERE secid LIKE %s"""
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select, ([segment + '%'])):
                    ret = self.cursor.fetchone()
                    return [ret[0], ret[1]]
            else:
                self.onLog(u'DB未连接或连接异常')
        return []

    # ------------------------------
    def getFuturesCodeName(self, segment, option=0):
        if option:
            if segment:
                length = len(segment)
                if length == 1:
                    letterSegment = segment[0]
                    selectSql = """SELECT futurescode,futuresname FROM futures_list WHERE futuresletter LIKE %s"""
                    selectTuple = tuple(['%' + letterSegment + '%'])
                elif length == 2:
                    letterSegment = segment[0]
                    nameSegment = segment[1]
                    if nameSegment:
                        selectSql = """SELECT futurescode,futuresname FROM futures_list WHERE futurescode LIKE %s AND futuresletter LIKE %s"""
                        selectTuple = tuple(['%' + letterSegment + '%', '%' + nameSegment + '%'])
                    else:
                        selectSql = """SELECT futurescode,futuresname FROM futures_list WHERE futuresletter LIKE %s"""
                        selectTuple = tuple(['%' + letterSegment + '%'])
                else:
                    return []
                if self.connectFlag and self.isConnected():
                    if self.cursor.execute(selectSql, selectTuple):
                        ret = self.cursor.fetchall()
                        if len(ret) > 1:
                            return []
                        return [ret[0][0], ret[0][1]]
                else:
                    self.onLog(u'DB未连接或连接异常')

        else:
            sql_select = """SELECT futurescode, futuresname FROM futures_list WHERE futurescode LIKE %s"""
            if self.connectFlag and self.isConnected():
                if self.cursor.execute(sql_select, ([segment + '%'])):
                    ret = self.cursor.fetchall()
                    if len(ret) > 1:
                        return []
                    return [ret[0][0], ret[0][1]]
            else:
                self.onLog(u'DB未连接或连接异常')
        return []

    # ------------------------------
    def isSecId(self, secid):
        sql_select = """SELECT * FROM sec_list WHERE secid=%s"""
        if self.connectFlag and self.isConnected():
            return self.cursor.execute(sql_select, ([secid]))
        self.onLog(u'DB未连接或连接异常')
        return 0

    # -------------------------------------------------------
    def isFuturesCode(self, futuresCode):
        sql_select = """SELECT * FROM futures_list WHERE futurescode=%s"""
        if self.connectFlag and self.isConnected():
            return self.cursor.execute(sql_select, ([futuresCode]))
        self.onLog(u'DB未连接或连接异常')
        return 0

    # -------------------------------------------------------
    def stopDb(self):
        if self.connectFlag:
            try:
                self.db.close()
            except:
                pass

    # ----------------------------
    def getProductVolume(self, productList, objectCode, objectClass='sec', direction=TRADE_BUY):
        retDict = {}
        if objectClass == 'sec':
            for product in productList:
                selectSql = """select volume from products_details where product=%s and objectcode=%s"""
                selectTuple = tuple([product, objectCode])
                if self.cursor.execute(selectSql, selectTuple):
                    data = self.cursor.fetchone()
                    retDict[product] = data[0]
                else:
                    retDict[product] = 0
        else:
            for product in productList:
                selectSql = """select volume from products_details where product=%s and objectcode=%s and direction=%s"""
                selectTuple = tuple([product, objectCode, direction])
                if self.cursor.execute(selectSql, selectTuple):
                    data = self.cursor.fetchone()
                    retDict[product] = data[0]
                else:
                    retDict[product] = 0
        return retDict

    # -------------------------------------------
    def deleteProduct(self, product):
        sql_delete = """DELETE FROM products_info WHERE product=%s"""
        deleteProduct = tuple([product])
        if self.connectFlag and self.isConnected():
            try:
                ret = self.cursor.execute(sql_delete, deleteProduct)
                self.db.commit()
                return ret
            except:
                return 0
        else:
            self.onLog(u'DB未连接或连接异常')
            return 0

    # ----------------------------
    def getObjectInProduct(self, product, objectclass='sec'):
        """objectclass enum('sec', 'futures')"""
        sql_select = """select * from products_details where product=%s and objectclass=%s"""
        con = tuple([product, objectclass])
        if self.connectFlag and self.isConnected():
            if self.cursor.execute(sql_select, con):
                return self.cursor.fetchall()
        else:
            self.onLog(u'DB未连接或连接异常')
        return []

    # ------------------------------------
    def getRetrace5d(self, user):
        """"
        返回retrace5d
        若查询有误，返回 0
        """
        sql_select = """select content from config where cfgname='retrace5d' and remark=%s"""
        sql_tuple = tuple([user])
        if self.connectFlag and self.isConnected():
            if self.cursor.execute(sql_select, sql_tuple):
                data = self.cursor.fetchone()
                if data:
                    return float(data[0])
            else:
                sql_select = """select content from config where cfgname='retrace5d' and remark='all'"""
                if self.cursor.execute(sql_select):
                    data = self.cursor.fetchone()
                    if data:
                        return float(data[0])
        else:
            self.onLog(u'DB未连接或连接异常')
        return 0

    # ------------------------------
    def saveRetrace5d(self, retrace5d, user=None):
        """更新Retrace5d，更新成功，返回True，反之False"""
        if user:
            updateSql = """update config set content=%s where cfgname='retrace5d' and remark=%s"""
            updateTuple = tuple([retrace5d, user])
            if self.cursor.execute(updateSql, updateTuple):
                self.db.commit()
                return True
            else:
                insertSql = """insert into config (cfgname, content, remark) values ('retrace5d', %s, %s)"""
                insertTuple = tuple([retrace5d, user])
                if self.cursor.execute(insertSql, insertTuple):
                    self.db.commit()
                    return True
        else:
            updateSql = """update config set content=%s where cfgname='retrace5d' and remark='all'"""
            updateTuple = tuple([retrace5d])
            if self.cursor.execute(updateSql, updateTuple):
                self.db.commit()
                return True
        return False

    # -----------------------------------------
    def getUpdateDate(self, product, objectClass):
        ret = None
        if objectClass == 'sec' or objectClass == 'futures':
            selectSql = """select content from config where cfgname='updatetime' and remark=%s"""
            selectTup = tuple([product + '.' + objectClass])
            type(product)
            if self.cursor.execute(selectSql, selectTup):
                data = self.cursor.fetchone()[0]
                if len(data) > 9:
                    try:
                        ret = datetime.strptime(data[0:10], '%Y-%m-%d')
                    except:
                        pass
        return ret
    # -----------------------------------------------
    def getOptionalStockList(self):
        ret = []
        selectSql = """select DISTINCT secid from optional_stock_pool"""
        try:
            self.cursor.execute(selectSql)
            data = self.cursor.fetchall()
            for item in data:
                ret.append(item[0])
        except:
            pass
        return ret

    # ---------------------------------------------------
    def getOptionalInfo(self):
        ret = []
        selectSql = """select DISTINCT secid, secname, updatetime, lastreferrer, firsttime, firstreferrer, remark from optional_stock_pool"""
        try:
            self.cursor.execute(selectSql)
            data = self.cursor.fetchall()
            for item in data:
                d = FhOptionalData()
                d.secId = item[0]
                d.secName = item[1]
                d.updateTime = item[2]
                d.lastReferrer = item[3]
                d.firstTime = item[4]
                d.firstReferrer = item[5]
                d.remark = item[6]
                ret.append(d)
        except:
            pass
        return ret

    # ----------------------------------------
    def updateOptional(self, code, loginName):
        updateSql = """update optional_stock_pool set updatetime=now(), lastreferrer=%s where secid=%s"""
        updateTup = tuple([loginName, code])
        if self.cursor.execute(updateSql, updateTup):
            self.db.commit()
            return True
        return False

    # -------------------------------------------
    def updataOptionalRemark(self, code, name, remark, loginName):
        # 0，成功；-1，失败；-2，添加失败1，添加成功，3，remark长度超标
        selectSql = """select secid from optional_stock_pool where secid=%s"""
        selectTup = tuple([code])
        if self.cursor.execute(selectSql, selectTup):
            updateSql = """update optional_stock_pool set remark=%s where secid=%s"""
            updateTup = tuple([remark, code])
            try:
                if len(remark.encode('utf-8'))> 125:
                    return 1
            except:
                pass
            if self.cursor.execute(updateSql, updateTup):
                self.db.commit()
                return 0
            return -1
        else:
            ret = self.addOptional(code, name, remark, loginName)
            if ret == 0:
                return 1
            elif ret == -1:
                return -2
            elif ret == 3:
                return 3
            else:
                return 999

    # ----------------------------------------------
    def addOptional(self, code, name, remark, loginName):
        # 0，成功；-1，失败；2，有重复；3，remark长度超标
        selectSql = """select secid from optional_stock_pool where secid=%s"""
        selectTup = tuple([code])
        if self.cursor.execute(selectSql, selectTup):
            return 2
        try:
            if len(remark.encode('utf-8')) > 125:
                return 3
        except:
            pass
        insertSql = """insert into optional_stock_pool (secid, secname, updatetime, lastreferrer, firsttime, firstreferrer, remark) VALUES (%s, %s, now(), %s, now(), %s, %s)"""
        insertTup = tuple([code, name, loginName, loginName, remark])
        if self.cursor.execute(insertSql, insertTup):
            self.db.commit()
            return 0
        return -1

    # ---------------------------------------
    def deleteOptional(self, code):
        deleteSql = """delete from optional_stock_pool where secid=%s"""
        deleteTup = tuple([code])
        if self.cursor.execute(deleteSql, deleteTup):
            self.db.commit()
            return 0
        return -1

    # -------------------------------------------
    def getOptionalControlFlag(self):
        selectSql = """select content from config where cfgname='optionalControlFlag'"""
        if self.cursor.execute(selectSql):
            data = self.cursor.fetchone()
            if data[0] == '0':
                return 0
            elif data[0] == '1':
                return 1
            else:
                return 0
        return 0

    # ---------------------------------------------------
    def getTrendData(self, code):
        selectSql = """select datetime, close, rankc from trend_index where code=%s"""
        selectTup = tuple([code])
        ret = {}
        if self.cursor.execute(selectSql, selectTup):
            data = self.cursor.fetchall()
            ret['datetime'] = []
            ret['close'] = []
            ret['RankC'] = []
            for item in data:
                ret['datetime'].append(item[0])
                ret['close'].append(item[1])
                ret['RankC'].append(item[2])
        return ret

# ===========================================

if __name__ == '__main__':
    startTime = time.clock()
    print startTime
    dbUtils = DbUtils()
    finishTime = time.clock()
    print finishTime
    print finishTime - startTime
    productInfo = dbUtils.getProductInfo()
    productList = [productInfo[i][0] for i in range(0, len(productInfo))]
    productRatio = [productInfo[i][1] for i in range(0, len(productInfo))]
    print productList
    print productRatio
