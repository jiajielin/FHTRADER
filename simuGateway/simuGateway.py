# coding=utf-8

"""
Time : 2016/8/4 14:10
Author : Jia Jielin
Company: fhhy.co
File : simuGateway.py
Description:

"""

# system module
import json
import socket
from copy import copy
import datetime
# third party module

# own module
from fhGateway import *
from fhRetCode import *
from fhDb import DbUtils


class SimuGateway(FhGateway):
    taskMap = {}
    taskMap['objectClass'] = 'objectClass'  # 标的类型，股票或期货
    taskMap['no'] = 'no'                    # 序号
    taskMap['subNo'] = 'subNo'              # 子序号
    taskMap['insertTime'] = 'insertTime'    # 下发时间
    taskMap['state'] = 'state'              # 状态
    taskMap['product'] = 'product'          # 产品
    taskMap['fhSymbol'] = 'fhSymbol'        # 代码
    taskMap['buySell'] = 'buySell'          # 买卖
    taskMap['limitPrice'] = 'limitPrice'    # 价格
    taskMap['volume'] = 'volume'            # 数量
    taskMap['fundManager'] = 'fundManager'  # 基金经理
    taskMap['trader'] = 'trader'            # 交易员
    taskMap['buyPrice'] = 'buyPrice'        # 买入价格
    taskMap['finishTime'] = 'finishTime'    # 完成时间
    taskMap['cancelTime'] = 'cancelTime'    # 撤销时间
    taskMap['offset'] = 'offset'            # 开平-期货专有
    taskMap['price'] = 'price'              # 当前价格-wind获取

    positionReqInterval = 2
    accountReqInterval = 2
    taskReqInterval = 1

    def __init__(self, eventEngine, gatewayName='Simu'):
        super(SimuGateway, self).__init__(eventEngine, gatewayName)
        self.tickDict = {}
        settingFlag = self.loadSettings()
        self.user = ''
        self.encPwd = ''
        self.registerEvent()
        self.countTimeout = 0
        self.logFlag = True
        # 订阅任务标记
        self.hasSubscribed = False
        self.subscribeTimer = None

        # 账户监控标记
        self.accountFlag = False
        self.accountTimer = None
        self.accountProduct = 'all'

        # 持仓监控标记
        self.positionFlag = False
        self.positionTimer = None
        self.positionProduct = 'all'

        # 登录标记
        self.loginFlag = False

        # 挂起标记，需订阅后方起作用
        self.haltFlag = False
        # 数据库类
        self.dbUtils = DbUtils(self.eventEngine)

    # ----------------------
    def loadSettings(self):
        try:
            f = file("setting.json")
            setting = json.load(f)
            f.close()
            self.host = setting['host']
            self.port = setting['port']
            self.bufSize = setting['bufSize']
            self.initFlag = True
            self.simuLog(u'配置加载成功')
        except:
            self.host = 'localhost'
            self.port = 3333
            self.bufSize = 1024
            self.simuLog(u'配置加载失败')
            return False
        return True

    # -----------------------------
    def simuLog(self, logContent):
        log = FhLogData()
        log.gatewayName = self.gatewayName
        log.logContent = logContent
        self.onLog(log)

    # -----------------------------
    def login(self, user, encPwd):
        self.user = user
        self.encPwd = encPwd

    # ----------------------
    def sLogin(self, event):
        transData = {}
        transData['user'] = self.user
        transData['encPwd'] = self.encPwd
        flag, ret = self.sendMessage(TYPE_LOGIN, transData, self.user)
        if flag == False:
            self.simuLog(u'连接超时，注册失败')
        else:
            if ret['retCode'] == RETCODE_SUCCESS:
                if 'verifyFlag' in ret['data']:
                    if ret['data']['verifyFlag'] != VERIFY_NOUSER:
                        self.simuLog(u'注册服务器成功')
                        self.loginFlag = True
                    else:
                        self.user = None
                        self.simuLog(u'注册服务器权限不足')
                        self.loginFlag = False
                else:
                    self.user = None
                    self.simuLog(u'交易返回解析数据有误')
                    self.loginFlag = False
            else:
                self.user = None
                self.simuLog(u'交易返回错误,'+ u'错误码：'+ unicode(ret['retCode']) + u',错误内容：'+ unicode(ret['comment']))
                self.loginFlag = False
        if self.loginFlag:
            self.subscribe('on')

    # -----------------------------
    def sendMessage(self, transType, transData, user=None):
        """
        发送：
        transType:发送交易类型
        transData:发送数据，为字典
        接收：
        retCode：返回码
        comment：返回码对应中文
        data：返回数据
        continueFlag：是否已完成
        """
        sendDict = {}
        if user:
            sendDict['user'] = user
        else:
            sendDict['user'] = self.user
        sendDict['transType'] = transType
        sendDict['transData'] = transData
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)  # 设置超时时间1.5秒
        timeoutFlag = True  # 为False时表示有问题
        try:
            sock.connect((self.host, self.port))
            self.countTimeout = 0
            if self.logFlag == False:
                self.logFlag = True
        except:
            self.countTimeout += 1
            timeoutFlag = False

        if self.countTimeout == 3:
            self.simuLog(u'服务器连接超时')
            self.logFlag = False
        if self.countTimeout == 10:
            self.simuLog(u'服务器连接超时过长，已断开，请重新连接！')
            self.countTimeout = 0
            self.sLogout(None)
            self.offAccount()
            self.offPosition()


        if timeoutFlag:
            sendStr = repr(sendDict)
            sock.send(sendStr)
            try:
                szBuf = sock.recv(self.bufSize)
            except:
                self.simuLog(u'未收到信息')
                self.countTimeout += 1
                szDict = {}
                szDict['retCode'] = RETCODE_ERROR
                szDict['comment'] = RETCODE_COMMENT[szDict['retCode']]
                szDict['data'] = {}
            try:
                szDict = eval(szBuf)
                retCode = szDict['retCode']
                comment = szDict['comment']
                data = szDict['data']
            except:
                self.simuLog(u'返回数据解析错误')
                szDict = {}
                szDict['retCode'] = RETCODE_DATAPARSEERROR
                szDict['comment'] = RETCODE_COMMENT[szDict['retCode']]
                szDict['data'] = {}
            sock.close()
            return timeoutFlag, szDict
        sock.close()
        return timeoutFlag, {}

    # -----------------------------
    def connect(self):
        event = Event(type_=EVENT_TASK_LOGIN)
        self.eventEngine.put(event)

    # ----------------------------------
    def disconnect(self):
        if self.hasSubscribed:
            self.subscribe('off')
            self.hasSubscribed = False
            self.simuLog(u'关闭任务监控')
        else:
            self.simuLog(u'任务监控未开启，操作无效')
        event = Event(type_=EVENT_TASK_LOGOUT)
        self.eventEngine.put(event)
    # -----------------------------
    def registerEvent(self):
        self.eventEngine.register(EVENT_TASK_LOGIN, self.sLogin)
        self.eventEngine.register(EVENT_TASK_REQ, self.getUpdate)
        self.eventEngine.register(EVENT_TASK_ALL, self.updateAll)
        self.eventEngine.register(EVENT_TASK_LOGOUT, self.sLogout)
        self.eventEngine.register(EVENT_ACCOUNT_REQ, self.getAccount)
        self.eventEngine.register(EVENT_POSITION_REQ, self.getPosition)
        self.eventEngine.register(EVENT_OPTIONAL_REQ, self.getOptional)

    # --------------------------------
    def updateAll(self, event):
        timeoutFlag, szDict = self.sendMessage(TYPE_UPDATE, {})
        if timeoutFlag:
            if self.user in szDict['data']:
                taskTick = copy(szDict['data'][self.user])
                self.onTask(taskTick)

    # -------------------------------
    def halt(self, haltSwitch='on'):
        if haltSwitch == 'on':
            if self.loginFlag:
                if self.hasSubscribed:
                    timeoutFlag, szDict = self.sendMessage(TYPE_HALT_ON, {})
                    self.haltFlag = True
                else:
                    self.simuLog(u'尚未订阅，请开启监控后进行操作')
            else:
                self.simuLog(u'尚未开启监控，操作无效')
        elif haltSwitch == 'off':
            if self.loginFlag:
                if self.hasSubscribed:
                    timeoutFlag, szDict = self.sendMessage(TYPE_HALT_OFF, {})
                    if timeoutFlag:
                        if szDict['retCode'] == RETCODE_SUCCESS:
                            self.haltFlag = False
                        else:
                            self.simuLog(u'')
                else:
                    self.simuLog(u'尚未开启')
            else:
                self.simuLog(u'尚未开启监控，操作无效')

    # -------------------------------
    def subscribe(self, subscribeSwitch='on'):
        if subscribeSwitch == 'on':
            if self.loginFlag:
                self.hasSubscribed = True
                self.subscribeTimer = Thread(target=self.onSubscriberTimer)
                self.subscribeTimer.start()
                self.simuLog(u'开启任务监控')
            else:
                self.simuLog(u'尚未登录服务器，请登录后操作')
        elif subscribeSwitch == 'off':
            if self.hasSubscribed:
                self.hasSubscribed = False
                self.subscribeTimer.join()
            else:
                self.simuLog(u'任务监控未开启，操作无效')

    # --------------------------------------
    def getOptional(self, event):
        data = self.dbUtils.getOptionalInfo()
        for optional in data:
            self.pushOptional(optional)

    # ----------------------------------------
    def onSubscriberTimer(self):
        while self.hasSubscribed:
            if self.loginFlag:
                event = Event(type_=EVENT_TASK_REQ)
                self.eventEngine.put(event)
                sleep(self.taskReqInterval)
            else:
                self.subscribe('off')
                self.simuLog(u'尚未登录服务器，取消订阅')

    # -----------------------------------
    def onAccount(self, product):
        self.accountFlag = True
        self.accountProduct = product
        # self.getAccountAll()
        self.accountTimer = Thread(target=self.onAccountTimer)
        self.accountTimer.start()

    # ---------------------------------
    def onAccountTimer(self):
        while self.accountFlag:
            event = Event(type_=EVENT_ACCOUNT_REQ)
            self.eventEngine.put(event)
            sleep(self.accountReqInterval)

    # ----------------------------------
    def offAccount(self, product=None):
        if self.accountFlag:
            self.accountFlag = False
            self.accountTimer.join()
            self.accountProduct = 'all'

    # -------------------------------------
    def getAccount(self, event):
        # 得到账户信息
        transData = {}
        transData['product'] = self.accountProduct
        timeoutFlag, szDict = self.sendMessage(TYPE_ACCOUNT_QUERY, transData)
        if timeoutFlag:
            if 'data' in szDict and 'retCode' in szDict:
                if szDict['retCode'] == RETCODE_SUCCESS:
                    if szDict['data'] != []:
                        accountTick = copy(szDict['data'])
                        self.pushAccount(accountTick)

    # ---------------------------------
    def pushAccount(self, tick):
        """任务推送"""
        event = Event(type_=EVENT_ACCOUNT)
        event.dict_['data'] = tick
        self.eventEngine.put(event)

    # ----------------------------------
    def pushOptional(self, tick):
        event = Event(type_=EVENT_OPTIONAL)
        event.dict_['data'] = tick
        self.eventEngine.put(event)

    # ---------------------------------------
    def onPosition(self, product):
        self.positionFlag = True
        self.positionProduct = product
        # self.getPositionAll()
        self.positionTimer = Thread(target=self.onPositionTimer)
        self.positionTimer.start()

    # ---------------------------------------
    def onPositionTimer(self):
        while self.positionFlag:
            event = Event(type_=EVENT_POSITION_REQ)
            self.eventEngine.put(event)
            sleep(self.positionReqInterval)

    # ---------------------------------------
    def offPosition(self, product=None):
        if self.positionFlag:
            self.positionFlag = False
            self.positionTimer.join()
            self.positionProduct = 'all'
        # else:
        #     self.simuLog(u'尚未监控账户，操作无效')

    # ---------------------------------
    def getPosition(self, event):
        # 得到持仓股票信息

        transData = {}
        transData['product'] = self.positionProduct
        timeoutFlag, szDict = self.sendMessage(TYPE_POSITION_QUERY, transData)
        if timeoutFlag:
            if 'changeFlag' in szDict['data']:
                changeFlag = szDict['data']['changeFlag']
                if changeFlag:
                    data = self.dbUtils.getProductPosition(self.positionProduct)
                    if self.positionProduct in data:
                        positionTick = copy(data[self.positionProduct])
                        self.pushPosition(positionTick)
            else:
                self.simuLog(u'返回数据出错')
                data = self.dbUtils.getProductPosition(self.positionProduct)
                if self.positionProduct in data:
                    positionTick = copy(data[self.positionProduct])
                    self.pushPosition(positionTick)
        else:
            data = self.dbUtils.getProductPosition(self.positionProduct)
            if self.positionProduct in data:
                positionTick = copy(data[self.positionProduct])
                self.pushPosition(positionTick)

    # -----------------------------------
    def pushPosition(self, tick):
        """任务推送"""
        event = Event(type_=EVENT_POSITION)
        event.dict_['data'] = tick
        self.eventEngine.put(event)

    # ---------------------------------------
    def getUpdate(self, event):
        # 得到超时标记和返回字典，当为timeoutFlag为False时，表示超时
        timeoutFlag, szDict = self.sendMessage(TYPE_TASK_QUERY, {})
        if timeoutFlag:
            if self.user in szDict['data']:
                if szDict['data'][self.user] != []:
                    taskTick = copy(szDict['data'][self.user])
                    self.onTask(taskTick)

    # ---------------------------------
    def getAllTask(self):
        if self.loginFlag:
            event = Event(type_=EVENT_TASK_ALL)
            self.eventEngine.put(event)
        else:
            self.simuLog(u'尚未登录服务器，请登录后操作')

    # ----------------------------------
    def onTask(self, taskTick):
        """任务推送"""
        event = Event(type_=EVENT_TASK)
        event.dict_['data'] = taskTick
        self.eventEngine.put(event)

    # ------------------------------
    def sendOrder(self, data):
        if self.loginFlag:
            self.sendMessage(TYPE_TASK_ADD, data)
        else:
            self.simuLog(u'尚未登录服务器')

    # ------------------------------
    def sLogout(self, event):
        if self.user:
            transData = {}
            transData['user'] = self.user
            self.subscribe('off')
            self.simuLog(u'已停止任务监控')
            timeoutFlag, szDict = self.sendMessage(TYPE_LOGOUT, transData)
            if timeoutFlag:
                if 'retCode' in szDict:
                    if szDict['retCode'] == RETCODE_SUCCESS:
                        self.simuLog(u'注销成功')
                else:
                    self.simuLog(u'数据解析出错，请重新操作，或重新登录后再注销')
        else:
            self.simuLog(u'系统未发现用户，状态出错')

    # --------------------------------------
    def close(self):
        super(SimuGateway, self).close()
        self.sLogout(None)
        self.offAccount()
        self.offPosition()

    # -------------------------------
    def sendOption(self, option, data):
        transData = {}
        transData['option'] = option
        transData['data'] = data
        self.sendMessage(TYPE_TASK_MOD, transData)

    # ---------------------------------
    def addRemark(self, text, taskNo, subNo):
        if self.user:
            transData = {}
            transData['user'] = self.user
            transData['remark'] = text
            transData['taskNo'] = str(taskNo)
            transData['subNo'] = str(subNo)
            self.sendMessage(TYPE_REMARK_ADD, transData)

    # ----------------------------------
    def saveSecValue(self, product, totalValue):
        if self.positionProduct != product:
            return
        transData = {}
        transData['product'] = self.positionProduct
        transData['totalValue'] = totalValue
        flag, ret = self.sendMessage(TPYE_UPDATE_SECVALUE, transData, self.user)

    # ----------------------------------
    def saveFuturesTodayInfo(self, product, margin, todayProfit):
        if self.positionProduct != product:
            return
        transData = {}
        transData['product'] = self.positionProduct
        transData['margin'] = margin
        transData['todayProfit'] = todayProfit
        flag, ret = self.sendMessage(TYPE_UPDATE_FUTURES_TODAY_INFO, transData, self.user)







