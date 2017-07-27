# coding=utf-8

"""
Time : 2016/7/29 15:02
Author : Jia Jielin
Company: fhhy.co
File : fhGateway.py
Description:

"""

# system module

# third party module

# own module
from eventEngine import *
from fhConstant import *
import time


class FhGateway(object):
    """交易接口，用于其他接口来继承"""

    # ------------------------
    def __init__(self, eventEngine, gatewayName):
        self.eventEngine = eventEngine
        self.gatewayName = gatewayName

    # -------------------------
    def onTick(self, tick):
        """行情推送"""
        event1 = Event(type_=EVENT_TICK)
        event1.dict_['data'] = tick
        self.eventEngine.put(event1)

        # 特定合约代码事件
        # event2 = Event(type_=EVENT_TICK + tick.fhSymbol)
        # event2.dict_['data'] = tick
        # self.eventEngine.put(event2)

    # ----------------------------
    def onTrade(self, trade):
        """成交信息推送，目前不需要"""
        # todo
        pass

    # ---------------------------
    def onOrder(self, order):
        """订单变化推送，目前不需要"""
        pass

    # ------------------------
    def onPosition(self, position):
        """持仓信息推送，目前不需要"""
        pass

    # -----------------------
    def onAccount(self, account):
        """账户信息推送，目前不需要"""
        pass

    # -------------------
    def onError(self, error):
        """错误信息推送"""
        pass

    # -------------------------
    def onLog(self, log):
        """日志推送"""
        event1 = Event(type_=EVENT_LOG)
        event1.dict_['data'] = log
        self.eventEngine.put(event1)

    # -----------------------------
    def isConnected(self):
        """判断连接状态"""

    # ----------------------------
    def connect(self):
        """连接"""
        pass

    # ---------------------------------
    def subscribe(self, subscribeReq):
        """订阅行情"""
        pass

    # ---------------------------------
    def stopSubscribe(self, reqId=None):
        """订阅行情"""
        pass

    # ---------------------------------
    def getPrice(self, subscribeReq):
        """获取一次"""
        pass

    # ---------------------------------
    def sendOrder(self, orderReq):
        """发单"""
        pass

    # -------------------------------------
    def cancelOrder(self, cancelOrderReq):
        """撤单"""
        pass

    # -----------------------------------
    def qryAccount(self):
        """查询账户资金"""
        pass

    # ------------------------
    def qryPosition(self):
        """查询持仓"""
        pass

    # -----------------------------------
    def close(self):
        """关闭"""
        pass

    # ---------------------------------
    def sendOption(self, option):
        # 目前只Simu需要
        pass


# ================================================
class FhBaseData(object):
    """基础数据类"""

    def __init__(self):
        self.gatewayName = EMPTY_STRING  # Gateway名称
        self.rawData = None  # 原始数据


# ===================================================
class FhTickData(FhBaseData):
    """Tick行情数据类"""

    # --------------------------------------
    def __init__(self):
        super(FhTickData, self).__init__()

        # 代码相关
        self.symbol = EMPTY_STRING  # 合约代码/股票代码
        self.exchange = EMPTY_STRING  # 交易所代码
        self.fhSymbol = EMPTY_STRING  # 合约在FHTrader中的唯一代码，通常是 合约代码.交易所代码，实际中，Wind代码即是该代码

        # 成交数据
        self.lastPrice = EMPTY_STRING  # 最新成交价
        self.lastVolume = EMPTY_INT  # 最新成交量
        self.volume = EMPTY_INT  # 今天总成交量
        self.openInterest = EMPTY_INT  # 持仓量
        self.time = EMPTY_STRING  # 时间
        self.date = EMPTY_STRING  # 日期

        self.upperLimit = EMPTY_STRING  # 涨停价
        self.lowerLimit = EMPTY_STRING  # 跌停价


# ===========================
class FhLogData(FhBaseData):
    """"""

    # --------------------------------
    def __init__(self):
        super(FhLogData, self).__init__()
        self.logTime = time.strftime('%X', time.localtime())  # 生成日志事件
        self.gatewayName = EMPTY_UNICODE
        self.logContent = EMPTY_UNICODE


# ===============================
class FhOptionalData(FhBaseData):
    """"""

    # --------------------------------
    def __init__(self):
        super(FhOptionalData, self).__init__()
        self.secId = EMPTY_UNICODE
        self.secName = EMPTY_UNICODE
        self.updateTime = EMPTY_UNICODE
        self.lastReferrer = EMPTY_UNICODE
        self.firstTime = EMPTY_UNICODE
        self.firstReferrer = EMPTY_UNICODE
        self.remark = EMPTY_UNICODE


# ===============================
class FhSubscribeReq(object):
    """订阅行情时传入的对象类"""

    def __init__(self):
        self.symbol = EMPTY_STRING  # 代码
        self.exchange = EMPTY_STRING  # 交易所
        self.objectClass = EMPTY_INT # 产品类型，一般就股票和期货，股票0，期货1
        self.fields = ''            # 请求字段，Wind需要


class FhOrderReq(object):
    """下单对象类，实际下单用，目前暂时不需要"""

    def __init__(self):
        self.symbol = EMPTY_STRING  # 代码
        self.exchange = EMPTY_STRING  # 交易所
        self.price = EMPTY_FLOAT  # 价格
        self.volume = EMPTY_INT  # 数量

        self.priceType = EMPTY_STRING  # 价格类型
        self.direction = EMPTY_STRING  # 买卖
        self.offset = EMPTY_STRING  # 开平

        # 以下为IB相关
        self.productClass = EMPTY_UNICODE  # 合约类型
        self.currency = EMPTY_STRING  # 合约货币
        self.expiry = EMPTY_STRING  # 到期日
        self.strikePrice = EMPTY_FLOAT  # 行权价
        self.optionType = EMPTY_UNICODE  # 期权类型


# =============================
class FhCancelOrderReq(object):
    """撤单传入对象类，实际下单用，目前暂时不需要"""

    def __init__(self):
        self.symbol = EMPTY_STRING  # 代码
        self.exchange = EMPTY_STRING  # 交易所

        # 以下字段主要和CTP、LTS类接口相关
        self.orderID = EMPTY_STRING  # 报单号
        self.frontID = EMPTY_STRING  # 前置机号
        self.sessionID = EMPTY_STRING  # 会话号


# ========================================
class FhTaskReq(object):
    """任务下单对象类"""

    def __init__(self):
        self.taskId = EMPTY_STRING
        self.subtaskId = EMPTY_STRING

        self.symbol = EMPTY_STRING
        self.exchange = EMPTY_STRING
        self.price = EMPTY_FLOAT
        self.volume = EMPTY_INT
        self.priceType = EMPTY_STRING
        self.direction = EMPTY_STRING

        self.fundManager = EMPTY_STRING
        self.trader = EMPTY_STRING


# ===========================================
class FhCancelTaskReq(object):
    """任务下单取消对象类"""

    def __init__(self):
        self.taskId = EMPTY_STRING
        self.subtaskId = EMPTY_STRING
