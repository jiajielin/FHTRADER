# coding=utf-8

"""
Time : 2016/12/23 16:22
Author : Jia Jielin
Company: fhhy.co
File : choiceGateway.py
Description:
东方财富choice接口
"""

isChoiceSetup = True
# system module
from copy import copy
import datetime
import json
# third party module
try:
    from EmQuantAPI import *
except ImportError:
    isChoiceSetup = False
    print u'请先安装EmQuantAPI'
# own module
from fhGateway import *
from fhUtils import *


exchangeMap = {}
exchangeMap[EXCHANGE_SSE] = 'SH'
exchangeMap[EXCHANGE_SZSE] = 'SZ'
exchangeMap[EXCHANGE_CFFEX] = 'CFE'
exchangeMap[EXCHANGE_SHFE] = 'SHF'
exchangeMap[EXCHANGE_DCE] = 'DCE'
exchangeMap[EXCHANGE_CZCE] = 'CZC'
exchangeMap[EXCHANGE_UNKNOWN] = ''
exchangeMapReverse = {v: k for k, v in exchangeMap.items()}


# ============================
class ChoiceGateway(FhGateway):
    """东方财富choice接口"""
    # 订阅csq时传入的字段
    csqParamMap = {}
    csqParamMap['Now'] = 'price'  # 现价

    csqParamMap['PctChange'] = 'changeRatio'  # 涨跌幅
    # csqParamMap['RT_CHG'] = 'change'  # 涨跌
    csqParamMap['High'] = 'high'     # 当天最高

    csqParam = ','.join(csqParamMap.keys())

    # -----------------------------
    def __init__(self, eventEngine, gatewayName='Choice'):
        super(ChoiceGateway, self).__init__(eventEngine, gatewayName)
        self.user = ''
        self.pwd = ''

        self.loadSettings()

        self.c = c
        self.connectFlag = False

        self.registerEvent()
        self.requestIdList = []

    # ----------------------------
    def loadSettings(self):
        try:
            f = file("accountInfo.json")
            setting = json.load(f)
            self.user = setting['choiceUser']
            self.pwd = setting['choicePwd']
            self.choiceLog(u'配置加载成功')
        except:
            self.user = 'fhhy0'
            self.pwd = 'fhhy0'
            self.choiceLog(u'配置加载失败')

    # --------------------------
    def choiceLog(self, logContent):
        log = FhLogData()
        log.gatewayName = self.gatewayName
        log.logContent = logContent
        self.onLog(log)

    # ---------------------------
    def registerEvent(self):
        self.eventEngine.register(EVENT_CHOICE_CONNECTREQ, self.cConnect)

    # ----------------------------------
    def connect(self):
        event = Event(type_=EVENT_CHOICE_CONNECTREQ)
        self.eventEngine.put(event)

    # --------------------------------------
    def isConnected(self):
        return self.connectFlag

    # -------------------------------------
    def subscribe(self, subscribeReq):
        if self.isConnected():
            if self.requestIdList:
                return self.requestIdList[0]
            symbols = subscribeReq.symbol.split('.')
            choiceSymbol = ''
            for i in range(0, len(symbols)):
                if symbols[i] != '':
                    choiceSymbol = choiceSymbol + getSymbolExchange(symbols[i], subscribeReq.objectClass) + ','
            data = self.c.csq(choiceSymbol, self.csqParam, self.csqCallBack)
            if data.ErrorCode == 0:
                if data.SerialID not in self.requestIdList:
                    self.requestIdList.append(data.SerialID)
                return data.SerialID
            else:
                self.choiceLog(u'订阅返回报错')
        else:
            self.choiceLog(u'尚未连接')

    # ----------------------------
    def stopSubscribe(self, reqId=None):
        if reqId:
            if reqId == -1:
                for request in self.requestIdList:
                    self.c.csqcancel(request)
                self.requestIdList = []
                return 0
            elif reqId in self.requestIdList:
                self.c.csqcancel(reqId)
                self.requestIdList.remove(reqId)
                return 0
        else:
            for request in self.requestIdList:
                self.c.csqcancel(request)
            self.requestIdList = []
            return 0
        return 0

    # ---------------------------------------
    def getPrice(self, subscribeReq):
        if len(subscribeReq.symbol.split('.')) == 2:
            choiceSymbol = subscribeReq.symbol
        elif len(subscribeReq.symbol.split('.')) == 1:
            choiceSymbol = '.'.join([subscribeReq.symbol, exchangeMap[subscribeReq.exchange]])
        else:
            self.choiceLog(u'订阅输入代码非法')
            return 0
        data = self.c.csq(choiceSymbol, 'Now', options=None, fncallback=None)  # todo 需确认是否正确
        print data
        if data.ErrorCode == 0:
            if choiceSymbol in data.Data:
                if data.Data[choiceSymbol]:
                    if data.Data[choiceSymbol][0]:
                        return data.Data[choiceSymbol][0]
            else:
                self.choiceLog(u'返回数据为空')
        else:
            self.choiceLog(u'返回错误码：%d' % data.ErrorCode)
        return 0

    # ---------------------------------------
    def sendOrder(self, orderReq):
        self.choiceLog(u'Choice接口未实现发单功能')

    # ------------------------------------
    def cancelOrder(self, cancelOrderReq):
        self.choiceLog(u'Choice接口未实现撤单功能')

    # ---------------------------------------------
    def getAccount(self):
        self.choiceLog(u'Choice接口未实现查询账户功能')

    # -----------------------------------------------
    def getPosition(self):
        self.choiceLog(u'Choice接口未实现查询持仓功能')

    # -----------------------------------------
    def close(self):
        self.stopSubscribe(-1)

    # ----------------------------------------
    def csqCallBack(self, data):
        if data.ErrorCode == 0:
            da = data.Data
            tick = []
            for code in da:
                d = {}
                d['objectCode'] = code
                for n, field in enumerate(self.csqParamMap.keys()):
                    if da[code][n]: # 增量更新时需判断是否为None
                        d[self.csqParamMap[field]] = da[code][n]
                tick.append(d)
            newtick = copy(tick)

            self.onTick(newtick)

    # -------------------------------------
    def cConnect(self, event):
        """"""
        result = self.c.start(self.user, self.pwd, "ForceLogin=0")
        if not result.ErrorCode:
            self.choiceLog(u'Choice接口连接成功')
            self.connectFlag = True
        else:
            logContent = u'Choice接口连接失败，错误代码%d' % result.ErrorCode
            self.choiceLog(logContent)

    # ---------------------------------
    def getHigh5(self, objectList):
        retDict = {}

        if objectList:
            endDay = (datetime.datetime.now() - datetime.timedelta(1)).strftime("%Y%m%d")
            dayList = [endDay]
            for i in range(1, 5):
                data = self.c.getdate(endDay, -i)
                if data.ErrorCode == 0:
                    startDay = data.Data[0]
                    dayList.append(startDay)

            for obj in objectList:
                retDict[obj] = 0
            for day in dayList:
                option = 'TradeDate=' + day + 'AdjustFlag=3'
                data = c.css(objectList, 'High', option)
                if data.ErrorCode == 0:
                    d = data.Data
                    for obj in d:
                        if obj in retDict:
                            if d[obj]:
                                if d[obj] > retDict[obj]:
                                    retDict[obj] = d[obj]
        return retDict


# ==================================
