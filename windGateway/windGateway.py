# coding=utf-8

"""
Time : 2016/7/29 14:45
Author : Jia Jielin
Company: fhhy.co
File : windGateway.py
Description:

"""

isWindSetup = True
# system module
from copy import copy
import datetime
# third party module
try:
    from WindPy import w
except ImportError:
    isWindSetup = False
    print u'请先安装WindPy接口'
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


# ========================
class WindGateway(FhGateway):
    """Wind接口"""
    # 订阅wsq时传入的字段列表
    wsqParamMap = {}
    wsqParamMap['RT_LAST'] = 'price'  # 现价
    # wsqParamMap['rt_last_vol'] = 'volume'  # 现量

    # wsqParamMap['rt_open'] = 'openPrice'  # 开盘价
    # wsqParamMap['rt_high'] = 'highPrice'  # 最高价
    # wsqParamMap['rt_low'] = 'lowPrice'  # 最低价
    # wsqParamMap['rt_pre_close'] = 'preClosePrice'  # 前收

    wsqParamMap['RT_PCT_CHG'] = 'changeRatio'  # 涨跌幅
    wsqParamMap['RT_CHG'] = 'change'  # 涨跌
    wsqParamMap['RT_HIGH'] = 'high'     # 当天最高

    wsqParam = ','.join(wsqParamMap.keys())

    # -------------------------------------
    def __init__(self, eventEngine, gatewayName='Wind'):
        super(WindGateway, self).__init__(eventEngine, gatewayName)

        self.w = w
        self.connectFlag = False

        # Wind的wsq更新采用的是增量更新模式，每次推送只会更新发生变化的字段
        # # 而FHTrader中的tick是完整更新，因此需要本地维护一个所有字段的快照
        # self.tickDict = {}
        self.registerEvent()
        self.requestIdList = []

    # ------------------------------------------
    def connect(self):
        event = Event(type_=EVENT_WIND_CONNECTREQ)
        self.eventEngine.put(event)

    # -----------------------------------------
    def isConnected(self):
        return self.connectFlag

    # ---------------------------------------
    def windLog(self, logContent):
        log = FhLogData()
        log.gatewayName = self.gatewayName
        log.logContent = logContent
        self.onLog(log)

    # ------------------------------------------
    def subscribe(self, subscribeReq):
        if self.isConnected():
            if self.requestIdList:
                return self.requestIdList[0]
            symbols = subscribeReq.symbol.split(',')
            windSymbol = ''
            for i in range(0, len(symbols)):
                if symbols[i] != '':
                    windSymbol = windSymbol + getSymbolExchange(symbols[i], subscribeReq.objectClass)+','
            data = self.w.wsq(windSymbol, self.wsqParam, func=self.wsqCallBack)
            if data.ErrorCode == 0:
                if data.RequestID not in self.requestIdList:
                    self.requestIdList.append(data.RequestID)
                return data.RequestID
            else:
                self.windLog(u'订阅返回报错')
        else:
            self.windLog(u'尚未连接')

    # -----------------------------------------------
    def stopSubscribe(self, requestID):
        if requestID == -1:
            for request in self.requestIdList:
                self.w.cancelRequest(request)
            self.requestIdList = []
            return 0
        if requestID in self.requestIdList:
            self.w.cancelRequest(requestID)
            self.requestIdList.remove(requestID)
            return 0
        return 0

    # ----------------------------------------------
    def getPrice(self, subscribeReq):
        if len(subscribeReq.symbol.split('.')) == 2:
            windSymbol = subscribeReq.symbol
        elif len(subscribeReq.symbol.split('.')) == 1:
            windSymbol = '.'.join([subscribeReq.symbol, exchangeMap[subscribeReq.exchange]])
        else:
            self.windLog(u'订阅输入代码非法')
            return 0
        data = self.w.wsq(windSymbol, 'rt_last', func=None)
        if data.ErrorCode == 0:
            if len(data.Data):
                return data.Data[0][0]
            else:
                self.windLog(u'返回数据为空')
        else:
            self.windLog(u'返回错误码：%d' % data.ErrorCode)
            return 0
        self.w.tlogon()

    # -------------------------------------------
    def sendOrder(self, orderReq):
        self.windLog(u'Wind接口未实现发单功能')

    # ---------------------------------------------
    def cancelOrder(self, cancelOrderReq):
        self.windLog(u'Wind接口未实现撤单功能')

    # ---------------------------------------------
    def getAccount(self):
        self.windLog(u'Wind接口未实现查询账户功能')

    # -----------------------------------------------
    def getPosition(self):
        self.windLog(u'Wind接口未实现查询持仓功能')

    # ------------------------------------------------
    def close(self):
        self.stopSubscribe(-1)
        # self.w.stop()   # 调用w.stop()会出错，暂时注释掉

    # --------------------------------------------
    def registerEvent(self):
        self.eventEngine.register(EVENT_WIND_CONNECTREQ, self.wConnect)

    # ----------------------------------------------
    def wsqCallBack(self, data):
        if data.ErrorCode == 0:
            windSymbols = data.Codes
            tick = []
            for i in range(0, len(windSymbols)):
                # if windSymbols[i] in self.tickDict:
                #     tick = self.tickDict[windSymbols[i]]
                # else:
                #     tick = FhTickData()
                #     tick.gatewayName = self.gatewayName
                #     symbolSplit = windSymbols[i].split('.')
                #     tick.symbol = symbolSplit[0]
                #     tick.exchange = exchangeMapReverse[symbolSplit[1]]
                #     tick.fhSymbol = windSymbols[i]
                #     self.tickDict[windSymbols[i]] = tick
                # dt = data.Times[0]
                # tick.time = dt.strftime('%H:%M:%S')
                # tick.date = dt.strftime('%Y:%m:%d')
                #
                # fields = data.Fields
                # values = data.Data
                #
                # d = tick.__dict__
                # for n, field in enumerate(fields):
                #     field = field.lower()
                #     key = self.wsqParamMap[field]
                #     value = values[n][i]
                #     d[key] = value
                d = {}
                d['objectCode'] = windSymbols[i]
                for n, field in enumerate(data.Fields):
                    d[self.wsqParamMap[field]] = data.Data[n][i]
                tick.append(d)
            newtick = copy(tick)

            # print newtick
            self.onTick(newtick)

    # ---------------------------------
    def wConnect(self, event):
        """"""
        result = self.w.start()

        if not result.ErrorCode:
            self.windLog(u'Wind接口连接成功')
            self.connectFlag = True
        else:
            logContent = u'Wind接口连接失败，错误代码%d' % result.ErrorCode
            self.windLog(logContent)

    # -------------------------------
    def getHigh5(self, objectList):
        retDict = {}
        endDay = (datetime.datetime.now() - datetime.timedelta(1)).strftime("%Y%m%d")
        startDay = 'ED-4TD'
        if objectList:
            req = ''
            for object in objectList:
                req += object
                req += ','
            # data = self.w.wsd(req, 'high', startDay, endDay, 'PriceAdj=F')
            para = 'startDate=' + startDay + ';endDate=' + endDay + ';priceAdj=F'
            data = w.wss(req, 'high_per', para)
            if data.ErrorCode == 0:
                for i in range(0, len(data.Codes)):
                    maxd = data.Data[0][i]
                    if maxd == maxd:
                        retDict[data.Codes[i]] = maxd
                    else:
                        retDict[data.Codes[i]] = 0
        return retDict

# =====================================

