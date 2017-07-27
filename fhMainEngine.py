# coding=utf-8

"""
Time : 2016/7/12 15:02
Author : Jia Jielin
Company: fhhy.co
File : fhMainEngine.py
Software:PyCharm
Description:

"""

# system module
from collections import OrderedDict
from eventEngine import *
from fhDb import DbUtils
from fhGateway import FhLogData


# =================================
class MainEngine:
    """主引擎，负责调度"""

    # -------------------------------------
    def __init__(self):
        # 创建事件驱动引擎
        self.eventEngine = EventEngine2()
        self.eventEngine.start()  # 启动引擎

        # 创建数据引擎
        self.dataEngine = DataEngine(self.eventEngine)

        # 数据库相关
        self.dbUtils = None  # MySQL数据库对象

        # 调用初始化函数，目前只接Wind
        self.initGateway()

    # -----------------------------
    def initGateway(self):
        """初始化接口对象，目前只有Wind"""
        self.gatewayDict = OrderedDict()
        # # Choice接口初始化
        # try:
        #     from choiceGateway.choiceGateway import ChoiceGateway
        #     self.addGateway(ChoiceGateway, 'Choice')
        # except Exception, e:
        #     print e  # 随后需改为日志输出 todo
        # Wind接口初始化
        try:
            from windGateway.windGateway import WindGateway
            self.addGateway(WindGateway, 'Wind')
        except Exception, e:
            print e  # 随后需改为日志输出 todo

        # 设计SimuGateway是为了模拟查询数据库交易
        try:
            from simuGateway.simuGateway import SimuGateway
            self.addGateway(SimuGateway, 'Simu')
        except Exception, e:
            print e

    # ------------------------------------
    def addGateway(self, gateway, gatewayName=None):
        self.gatewayDict[gatewayName] = gateway(self.eventEngine, gatewayName)

    # -------------------------------------------
    def connect(self, gatewayName):  # gatewayName不是接口名，是'Wind','CTP'等
        """连接特定名称的接口"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.connect()
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ---------------------------------------
    def login(self, gatewayName, user, encPwd):
        """注册特定名称的接口"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.login(user, encPwd)

    # ----------------------------------
    def logout(self, gatewayName, user, encPwd):
        """注册特定名称的接口"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.logout(user, encPwd)
    # -----------------------------
    def disconnect(self, gatewayName):
        """注册特定名称的接口"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.disconnect()

    # -----------------------------------------
    def isConnected(self, gatewayName):
        """确认连接状态"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            return gateway.isConnected()
        else:
            return False
            self.writeLog(u'接口不存在：%s' % gatewayName)

    def subscribe(self, subscribeReq, gatewayName):
        """订阅特定接口的行情"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]

            gateway.subscribe(subscribeReq)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ------------------------------------------------
    def stopSubscribe(self, reqId, gatewayName):
        """订阅特定接口的行情"""
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Wind':
                gateway = self.gatewayDict[gatewayName]
                gateway.stopSubscribe(reqId)
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # -------------------------------------------------
    # def onAccount(self, product, gatewayName):
    #     """订阅特定接口的行情"""
    #     if gatewayName in self.gatewayDict:
    #         if gatewayName == 'Simu':
    #             gateway = self.gatewayDict[gatewayName]
    #             gateway.onAccount(product)
    #         else:
    #             self.writeLog(u'接口不存在：%s' % gatewayName)
    #     else:
    #         self.writeLog(u'接口不存在：%s' % gatewayName)

    # ---------------------------------------------------
    def offAccount(self, gatewayName, product=None):
        """订阅特定接口的行情"""
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Simu':
                gateway = self.gatewayDict[gatewayName]
                gateway.offAccount(product)
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ---------------------------------------------------
    # def onPosition(self, product, gatewayName):
    #     """订阅特定接口的行情"""
    #     if gatewayName in self.gatewayDict:
    #         if gatewayName == 'Simu':
    #             gateway = self.gatewayDict[gatewayName]
    #             gateway.onPosition(product)
    #         else:
    #             self.writeLog(u'接口不存在：%s' % gatewayName)
    #     else:
    #         self.writeLog(u'接口不存在：%s' % gatewayName)

    # ---------------------------------------------------
    def offPosition(self, gatewayName, product=None):
        """订阅特定接口的行情"""
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Simu':
                gateway = self.gatewayDict[gatewayName]
                gateway.offPosition(product)
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ---------------------------------------------------
    def getHigh5(self, objectList, gatewayName):
        """"""
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Wind':
                gateway = self.gatewayDict[gatewayName]
                return gateway.getHigh5(objectList)
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
                return {}
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)
            return {}

    # ------------------------------------------------
    def halt(self, haltReq, gatewayName):
        """挂起态，simuGateway中用于交易员不再接收任务"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]

            gateway.halt(haltReq)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # -----------------------------------------
    def getPrice(self, subscribeReq, gatewayName):
        """获取一次数据行情"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            return gateway.getPrice(subscribeReq)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)
            return 0

    # ------------------------------------------------
    def sendOrder(self, orderReq, gatewayName):
        """对特定接口发单"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            return gateway.sendOrder(orderReq)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)  # todo 需返回标志，用于上层处理

    # ----------------------------------------------------------------
    def cancelOrder(self, cancelOrderReq, gatewayName):
        """对特定接口撤单"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.cancelOrder(cancelOrderReq)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)
            # todo 需返回标志，用于上层处理

    # -----------------------------------------
    def qryAccont(self, gatewayName):
        """查询特定接口的账户"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.getAccount()
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ------------------------------------------------
    def onAccount(self, account, gatewayName):
        """查询特定接口的账户"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.onAccount(account)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ------------------------------------------------
    def onPosition(self, account, gatewayName):
        """查询特定接口的账户"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.onPosition(account)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ------------------------------------------------
    def close(self, gatewayName):
        """对特定接口发单"""
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            return gateway.close()
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ------------------------------------------------
    def exit(self):
        """退出程序前调用，保证正常退出"""
        # 安全关闭所有接口
        for gateway in self.gatewayDict.values():
            gateway.close()

        # 停止事件引擎
        self.eventEngine.stop()

        # 保存数据引擎里的合约数据到硬盘
        # self.dataEngine.saveData()     # todo

    # -------------------------------------------------
    def writeLog(self, content):
        log = FhLogData()
        log.logContent = content
        event = Event(type_=EVENT_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)

    # ----------------------------------------------
    def addDb(self, dbUtils):
        if not self.dbUtils:
            self.dbUtils = dbUtils

    # ------------------------------------------------
    def dbConnect(self):
        """连接MySQL数据库"""
        if not self.dbUtils:
            self.dbUtils = DbUtils()
        if self.dbUtils.isConnected():
            self.writeLog(u'数据库连接成功')
        else:
            self.writeLog(u'数据库连接失败')

    # ------------------------------------------------
    def dbConnected(self):
        return self.dbUtils.isConnected()

    # ----------------------------------------------
    def getSecPrice(self):
        pass

    # -------------------------
    def getAllTask(self, gatewayName):
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Simu':
                gateway = self.gatewayDict[gatewayName]
                gateway.getAllTask()
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # -----------------------------------
    def sendOption(self, option, data, gatewayName):
        if gatewayName in self.gatewayDict:
            gateway = self.gatewayDict[gatewayName]
            gateway.sendOption(option, data)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # -----------------------------------
    def addRemark(self, text, taskNo, subNo, gatewayName):
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Simu':
                gateway = self.gatewayDict[gatewayName]
                gateway.addRemark(text, taskNo, subNo)
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

    # ---------------------------------------
    def saveSecValue(self, product, totalValue, gatewayName):
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Simu':
                gateway = self.gatewayDict[gatewayName]
                gateway.saveSecValue(product, totalValue)
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)
    # ---------------------------------------
    def saveFuturesTodayInfo(self, product, margin, todayProfit, gatewayName):
        if gatewayName in self.gatewayDict:
            if gatewayName == 'Simu':
                gateway = self.gatewayDict[gatewayName]
                gateway.saveFuturesTodayInfo(product, margin, todayProfit)
            else:
                self.writeLog(u'接口不存在：%s' % gatewayName)
        else:
            self.writeLog(u'接口不存在：%s' % gatewayName)

# ============================
class DataEngine(object):
    """数据引擎"""
    billFileName = 'BillData.fh'

    def __init__(self, eventEngine):
        self.eventEngine = eventEngine
        # 订单/任务详细信息字典
        self.billDict = {}
        # 订单数据字典
        self.orderDict = {}
        # 活动订单/任务字典（即可撤销）
        self.workingOrderDict = {}
        # 读取任务信息 todo 需从Mysql中读取
        self.loadBills()
        # 注册事件监听
        self.registerEvent()
        # MySQL数据库类型
        self.dbUtils = None

    # ---------------------------------------------
    def addDb(self, dbUtils):
        if not self.dbUtils:
            self.dbUtils = dbUtils

    def dbConnect(self):
        """连接MySQL数据库"""
        if not self.dbUtils:
            self.dbUtils = DbUtils()
        if self.dbUtils.isConnected():
            self.writeLog(u'数据库连接成功')
        else:
            self.writeLog(u'数据库连接失败')

    def dbConnected(self):
        return self.dbUtils.isConnected()

    def getOrder(self, fhOrderId):
        """查询下单委托"""
        try:
            return self.orderDict[fhOrderId]
        except KeyError:
            return None

    # ----------------------------------------------
    def updateOrder(self, event):
        order = event.dict_['data']
        self.billDict[order.fhSymbol] = order
        self.billDict[order.symbol] = order

    # ---------------------------------------------
    def getAllWorkingOrders(self):
        """查询目前活动委托"""
        return self.workingOrderDict.values()

    # --------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_ORDER, self.updateOrder)

    # -------------------------------------------------
    def saveData(self):
        """保存到数据库"""

    # ---------------------
    def loadBills(self):
        pass
