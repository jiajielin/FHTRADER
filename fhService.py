# coding=utf-8

"""
Time : 2016/7/25 16:00
Author : Jia Jielin
Company: fhhy.co
File : fhService.py
Description:本文件用于服务端认证与任务

"""

# system module
import time
import copy
import datetime
import socket
import json
import logging
import logging.handlers
import random
from threading import Thread
# third party module
import MySQLdb
from MySQLdb.cursors import DictCursor
from DBUtils.PooledDB import PooledDB
# own module
from fhRetCode import *
from fhConstant import *
import SocketServer
from SocketServer import StreamRequestHandler as SRH



class FhServer(object):
    """
    该类为服务端类
    服务端收发为字典类型强制转换的字符串
    客户端发，服务端收：user, transType，transData(字典)
    服务端发，客户单收：retCode，comment，data(字典)，
    """
    insertFieldSec = ['product', 'objectCode', 'objectName', 'buySell', 'offset', 'taskPrice', 'taskVolume', 'fundManager']
    insertFieldFutures = ['product', 'objectCode', 'objectName', 'buySell', 'offset', 'taskPrice', 'taskVolume', 'fundManager','direction']

    def __init__(self, listenFlag=True):
        self.fhLog = fhLog
        # 用户注册列表 key为用户登录名，value为字典，包含用户地址addr，权限verifyFlag，最近一次非
        self.registerList = {}
        # 投资总监列表，用于判断是否为投资总监，以确定显示列表
        self.investManagerList = []
        # 用户缓存列表 key为用户登录名，value为列表，列表中每一个元素为字典，保存更新信息{key:[{key:value},{key:value}],key:...}
        self.cacheList = {}
        # 更新列表，key为用户登录名，value为列表，列表中每一个元素为字典，只保存taskNo和subNo
        self.updateList = {}
        # 挂起用户列表
        self.haltOnList = []
        # 任务列表，只包含子任务，key为用户登录名，value为列表，列表每一个元素为字典，只保存taskNo和subNo，在updateList pop后放入，用于任务状态改变时使用
        self.taskList = {}
        # 交易分配列表，key为用户登录名，value为当前未完成订单数，用户注册时初始化，与用户权限无关，在任务分配时根据任务所在产品进行分配
        self.traderTaskNum = {}
        # 活跃列表，元素为用户
        self.userAliveList = []
        # 连接DB标记
        self.connectFlag = False
        # 监听标记，用于控制是否监听，在startListen中设为True，在stopListen中设为False
        self.listenFlag = False
        # 初始化是否成功标记，成功为True
        self.initFlag = False
        # 产品信息列表，用于任务信息的校验，key为数据库中的字段，value为【】，因为可能存在多个值的情况
        self.productInfo = {}
        # 任务主序号记录，初始化时从config表中读取，每次addTask需增加
        self.recordTaskNo = '201601010001'
        # account缓存，key为用户，value为list，list中每个元素为字典，保存更新信息{key:[{key:value},{key:value}],key:...}
        # self.cacheAccount = {}
        # position缓存，key为用户，value为list，list中每个元素为字典，保存更新信息{key:[{key:value},{key:value}],key:...}
        # self.cachePosition = {}
        # 读取配置，在json文件中
        self.loadSetting()
        # 连接DB
        self.db = None
        self.cursor = None
        self.connectDb()
        # 用于记录主序号日期部分，当发现日期变化时，修改date值
        self.date = time.strftime('%Y%m%d', time.localtime(time.time()))
        # 主序号后缀内容，日期确定后自增，连接日期时，需补足3位，按字符串输出，当date改变时，从0开始
        self.suffixNo = self.getSuffixNo() + 1
        # 初始化socket，若成功，initFlag会设为True
        self.initSocket()
        # 加载产品信息，设置productInfo中信息
        self.loadProductInfo()

        # 用户调用产品持仓变化标记字典 key:user, value:dict - > key:product value:changeFlag(bool)
        self.cachePositionChangeDict = {}

        # 持仓更新Flag，False表示不对持仓进行更新，True表示对持仓进行更新
        self.updateFlag = False

        # 账户更新程序
        self.accountInterval = 2
        self.updateAccountFlag = True
        # 账户信息字典key:product, value:list -> list中值为dict -> key:各字段[product, accountclass, total, balance, available, secvalue, margin, todayprofit] value:各字段值
        self.accountDict = {}
        self.accountTimer = Thread(target=self.onAccountTimer)
        self.accountTimer.start()

        print '----- fhService ------'

        # 若initFlag为True，则开启监听
        if self.initFlag:
            self.startListen()
        else:
            self.fhLog.warning('socket初始化失败，无法监听')
        # 开启更新数据
        # self.secValueCache = {}         # key:产品名称， value，字典，所需字段及其值
        # self.futuresToday = {} # key:产品名称， value，字典，所需字段及其值
        # print self.futuresToday
        # self.updateFlag = True
        # self.updateInterval = 2
        # self.updateHandlerList = [] # 执行函数的更新列表，每一个item是一个headler
        # self.updateThread = Thread(target=self.onUpdateTimer)
        # self.updateThread.start()

    # ------------------------------------
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

    # ------------------------------------
    def connectDb(self):
        if self.connectFlag == False:
            try:
                self.fhLog.info('建立数据库连接池')
                self.pool = PooledDB(creator=MySQLdb, mincached=1, maxcached=30, host=self.dbHost, port=self.dbPort, user=self.user, passwd=self.password, db=self.dbName, use_unicode=False, charset='utf8', cursorclass=DictCursor)
                # self.db = MySQLdb.connect(host=self.dbHost, user=self.user, passwd=self.password, db=self.dbName,
                #                           port=self.dbPort, connect_timeout=self.dbTimeout)
                self.fhLog.info('建立数据库连接池成功')
                self.db = self.getConn()
                if self.db:
                    self.cursor = self.db.cursor()
                    self.fhLog.info('数据库连接成功')
                else:
                    self.fhLog.error('数据库连接失败')

            except:
                self.fhLog.error('数据库连接失败')
                self.connectFlag = False
                return False
            self.connectFlag = True
            return True
        else:
            self.fhLog.warning('数据库已连接')
            return True

    # ------------------------------------
    def getConn(self):
        if self.pool is None:
            return None
        return self.pool.connection()

    # --------------------------------------
    def loadProductInfo(self):
        """
        加载产品信息，目前只有fundManager、trader，其中，trader为list
        """
        sql_select = """select product,fundmanager,trader from products_info WHERE state='运作中'"""
        if self.connectFlag and self.isConnectedDb():
            num = self.cursor.execute(sql_select)
            if num:
                data = self.cursor.fetchall()
                for i in range(0, num):
                    product = data[i]['product']
                    fundManager = data[i]['fundmanager'].split(';')
                    trader = data[i]['trader'].split(';')
                    self.productInfo[product] = {}
                    self.productInfo[product]['fundManager'] = fundManager
                    self.productInfo[product]['trader'] = trader
        else:
            self.fhLog.warning('DB未连接或连接异常，无法加载产品信息')

    # -------------------------------------
    def initSocket(self):
        try:
            # 创建TCP Socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.fhLog.info('创建socket成功')
            self.sock.bind((self.host, self.port))
            self.fhLog.info('socket绑定成功')
            self.sock.listen(5)
            self.fhLog.info('监听成功')
            self.initFlag = True
        except:
            self.initFlag = False
            self.fhLog.error('初始化socket失败')

    # --------------------------------------
    def isConnectedDb(self):
        if self.connectFlag:
            try:
                self.db.ping()
            except:
                self.connectFlag = False
                self.fhLog.error('数据库连接异常')
                try:
                    self.db = self.getConn()
                    if self.db:
                        self.cursor = self.db.cursor()
                        self.connectFlag = True
                    else:
                        self.fhLog.error('获取数据库连接失败')
                except:
                    self.fhLog.error('数据库连接异常')

        return self.connectFlag

    # ----------------------------------
    def getSuffixNo(self):
        select_sql = """select taskno from task_flow_present order by taskno DESC limit 1"""
        try:
            if self.cursor.execute(select_sql):
                tem = self.cursor.fetchone()['taskno']
                if self.date == tem[0:8]:
                    return int(tem[8:12])
                else:
                    return 0
            else:
                return 0
        except:
            return 0

    # -----------------------------------
    def startListen(self):
        if self.listenFlag == False:
            self.fhLog.info('开始监听')
            self.listenFlag = True
            self.listen()
        else:
            self.fhLog.warning('已开启监听，重复开启无效')

    # ------------------------------------
    def stopListen(self):
        self.listenFlag = False
        self.fhLog.info('关闭监听')

    # ----------------------------
    def listen(self):
        while self.listenFlag:
            conn, addr = self.sock.accept()
            conn.settimeout(2)
            try:
                szBuf = conn.recv(self.bufSize)
            except:
                continue
            flag = False
            try:
                szDict = eval(szBuf)
                flag = True
            except:
                # 数据解析错误处理
                retDict = {}
                retDict['retCode'] = RETCODE_DATAPARSEERROR
                retDict['comment'] = RETCODE_COMMENT[retDict['retCode']]
                self.fhLog.error(retDict['comment']+'，错误数据：'+ szBuf)
            inDict = False
            if flag:
                try:
                    user = szDict['user']
                    transType = szDict['transType']
                    transData = szDict['transData']
                    inDict = self.verify(user, addr, transType)
                except:
                    # 若无transType字段，返回数据解析错误
                    retDict = {}
                    retDict['retCode'] = RETCODE_DATAPARSEERROR
                    retDict['comment'] = RETCODE_COMMENT[retDict['retCode']]
                    self.fhLog.error(retDict['comment'])
                if True:
                    if inDict:
                        if transType == TYPE_TASK_QUERY:        # 任务查询类型数据处理
                            retDict = self.queryTask(user)
                        elif transType ==TYPE_TASK_ADD:         # 新加任务处理
                            verifyFlag = self.registerList[user]['verifyFlag']
                            retDict = self.addTask(user, transData, verifyFlag)
                        elif transType == TYPE_LOGIN:           # 登录认证类型数据处理
                            retDict = self.userRegister(transData, addr)
                        elif transType == TYPE_LOGOUT:          # 登出认证类型数据处理
                            retDict = self.userUnregister(user)
                        elif transType == TYPE_HALT_ON:          # 挂起类型数据处理
                            retDict = self.halt(user, 'on')
                        elif transType == TYPE_HALT_OFF:         # 解挂起类型数据处理
                            retDict = self.halt(user, 'off')
                        elif transType == TYPE_CLOSE:            # 关闭类型数据处理
                            retDict = self.closeOption()
                        elif transType == TYPE_UPDATE:         # 刷新操作数据处理
                            retDict = {}
                            if self.update(user):
                                retDict['retCode'] = RETCODE_SUCCESS
                            else:
                                retDict['retCode'] = RETCODE_ERROR
                        elif transType == TYPE_TASK_MOD:        # 修改状态操作
                            retDict = self.modifyState(transData, user)
                        elif transType == TYPE_REMARK_ADD:
                            retDict = self.addRemark(transData)
                        elif transType == TYPE_POSITION_QUERY:  # 持仓查询
                            retDict = self.queryPositionChange(user, transData)
                        # elif transType == TYPE_POSITION_ALL:
                        #     retDict = self.queryPositionAll(user, transData)
                        elif transType == TYPE_ACCOUNT_QUERY:
                            retDict = self.queryAccount(user, transData)
                        # elif transType == TYPE_ACCOUNT_ALL:
                        #     retDict = self.queryAccountAll(user, transData)
                        # elif transType == TPYE_UPDATE_SECVALUE:
                        #     retDict = self.updateSecValue(transData)
                        # elif transType == TYPE_UPDATE_FUTURES_TODAY_INFO:
                        #     retDict = self.updateFuturesTodayInfo(transData)
                        else:
                            retDict = {}
                            retDict['retCode'] = RETCODE_TYPEERROR
                            retDict['comment'] = RETCODE_COMMENT[retDict['retCode']]
                            self.fhLog.error(retDict['comment'])
                    else:
                        self.fhLog.warning('非注册地址请求')
            if inDict:
                self.retCheck(retDict)
                retStr = repr(retDict)
                conn.send(retStr)
                self.fhLog.info('返回数据：' + retStr)
            conn.close()

    # ------------------------------------
    def verify(self, user, addr, transType):
        if transType != TYPE_LOGIN:
            if user in self.registerList:
                try:
                    ip = addr[0]
                except:
                    self.fhLog.warning('地址获取错误，使用用户：'+ user)
                    return False
                if self.registerList[user]['addr'] == ip:
                    return True
                else:
                    self.fhLog.warning("非法请求地址："+ ip + ' 使用用户：'+ user)
                    return False
            self.fhLog.warning('非法请求用户：'+ user)
            return False
        return True

    # --------------------------
    def retCheck(self, retDict):
        if 'retCode' not in retDict:
            retDict['retCode'] = RETCODE_FORMATERROR
            retDict['comment'] = RETCODE_COMMENT[retDict['retCode']]
            retDict['data'] = {}
            self.fhLog.error('格式错误：缺少retCode字段')
            return

        if 'comment' not in retDict:
            try:
                retDict['comment'] = RETCODE_COMMENT[retDict['retCode']]
            except:
                retDict['retCode'] = RETCODE_FORMATERROR
                retDict['comment'] = RETCODE_COMMENT[retDict['retCode']]
                retDict['data'] = {}
                self.fhLog.error('格式错误：retCode字段不合法')
                return
        if 'data' not in retDict:
            retDict['data'] = {}

    # ----------------------------------------------
    def userRegister(self, data, addr):
        """
        1、数据库验证
        2、在registerList增加key
        3、在cacheList中增加key
        4、在traderTaskNum中增加key
        5、在haltOnList中增加user
        6、在cachePositionChangeDict中增加user
        7、在investManagerList中增加user
        8、填充cacheList
        """
        user = data['user']
        encPwd = data['encPwd']
        sql_select = """select authority from userverify where loginname=%s and pwd=%s"""
        selectTuple = tuple([user, encPwd])
        retDict = {}
        if self.connectFlag and self.isConnectedDb():
            if self.cursor.execute(sql_select, selectTuple):
                data = self.cursor.fetchone()
                retDict['data'] = {}
                retDict['retCode'] = RETCODE_SUCCESS
                retDict['data']['verifyFlag'] = data['authority']
                self.registerList[user] = {}
                self.registerList[user]['addr'] = addr[0]
                self.registerList[user]['verifyFlag'] = data['authority']
                self.cacheList[user] = []
                self.updateList[user] = []
                self.cachePositionChangeDict[user] = {}
                if self.registerList[user]['verifyFlag'] == VERIFY_INVESTMANAGER:
                    self.investManagerList.append(user)
                if user not in self.haltOnList:
                    self.haltOnList.append(user)
                self.update(user)   # 更新操作，填充cacheList
                self.traderTaskNum[user] = 0    # 不管注册用户是否是交易员，均对其进行初始化，在分配任务时根据
                self.taskList[user] = []
                return retDict
            else:
                retDict['data'] = {}
                retDict['retCode'] = RETCODE_SUCCESS
                retDict['data']['verifyFlag'] = VERIFY_NOUSER
                return retDict
        else:
            retDict['retCode'] = RETCODE_DBDISCONNECT
            return retDict

    # ----------------------------------------------
    def userUnregister(self, user):
        if user in self.registerList:
            self.registerList.pop(user)
        if user in self.updateList:
            self.updateList.pop(user)
        if user in self.cacheList:
            self.cacheList.pop(user)
        if user in self.haltOnList:
            self.haltOnList.remove(user)
        if user in self.traderTaskNum:
            self.traderTaskNum.pop(user)
        if user in self.taskList:
            self.taskList.pop(user)
        if user in self.cachePositionChangeDict:
            self.cachePositionChangeDict.pop(user)
        if user in self.investManagerList:
            self.investManagerList.remove(user)

        retDict = {}
        retDict['retCode'] = RETCODE_SUCCESS
        return retDict

    # ----------------------------------
    def halt(self, user, haltSwitch='on'):
        retDict = {}
        retDict['data'] = {}
        if haltSwitch == 'on':
            if user not in self.haltOnList:
                self.haltOnList.append(user)
            retDict['retCode'] = RETCODE_SUCCESS
            return retDict
        elif haltSwitch == 'off':
            if user in self.haltOnList:
                self.haltOnList.remove(user)
            retDict['retCode'] = RETCODE_SUCCESS
            return retDict
        else:
            retDict['retCode'] = RETCODE_ERROR
            return retDict
    # --------------------------------
    def queryTask(self, user):
        retDict = {}
        retDict['data'] = {}
        if user in self.cacheList:
            if len(self.cacheList[user]) > self.taskBufSize:
                retDict['data'][user] = []
                for i in range(0, self.taskBufSize):
                    retDict['data'][user].append(self.cacheList[user].pop())
            else:
                retDict['data'][user] = []
                for i in range(0, len(self.cacheList[user])):
                    retDict['data'][user].append(self.cacheList[user].pop())
        else:
            self.cacheList[user] = []
        retDict['retCode'] = RETCODE_SUCCESS
        return retDict

    # ----------------------------
    def closeOption(self):
        self.stopListen()
        # self.updateThread.join()
        self.updateAccountFlag = False
        self.accountTimer.join()
        self.db.close()
        retDict = {}
        retDict['retCode'] = RETCODE_SUCCESS
        retDict['comment'] = RETCODE_COMMENT[retDict['retCode']]
        retDict['data'] = {}
        return retDict

    # -------------------------------------------
    def addTask(self, user, data, verifyFlag):
        """
        1、判读data字段是否齐全
        2、判断用户权限、分配交易员trader字段
        3、补足no、subNo、state字段
        4、data为list，其中每个值为字典，字典数为子任务数，按产品分，没有总的任务。字典中给出字段及其值
        """
        retDict = {}
        if verifyFlag == VERIFY_FUNDMANAGER or verifyFlag == VERIFY_INVESTMANAGER:
            count = 0   # 子任务计数，当不为0时，建立主任务
            taskNo = self.genNo()
            for i in range(0, len(data)):
                insertDict = {} # 插入数据字典
                if 'objectClass' in data[i]:
                    objectFlag = data[i]['objectClass']
                    if objectFlag == 'sec':
                        checkFlag = self.checkFields(data[i], self.insertFieldSec)
                    else:
                        checkFlag = self.checkFields(data[i], self.insertFieldFutures)
                    if checkFlag:
                        product = data[i]['product']
                        if user in self.productInfo[product]['fundManager']:
                            # 将本任务分配给交易员minTrader
                            minNum = 100000
                            minTrader = ''
                            for trader in self.productInfo[product]['trader']:
                                if trader in self.traderTaskNum:
                                    # 当用户用户量大于最小值，且不在挂起时，分配其给minTrader
                                    if minNum > self.traderTaskNum[trader] and trader not in self.haltOnList:
                                        minNum = self.traderTaskNum[trader]
                                        minTrader = trader
                            if minTrader == '':
                                # 当无当前产品交易员登录时，随机分配
                                self.fhLog.warning('暂无登录交易员，随机分配，任务要素：'+ repr(data[i]))
                                difList = self.differencSet(self.productInfo[product]['trader'], self.haltOnList)
                                if difList:
                                    minTrader = self.randSelect(difList)
                                else:
                                    minTrader = self.randSelect(self.productInfo[product]['trader'])
                            if minTrader:
                                insertDict['trader'] = minTrader
                                self.copyFields(insertDict, data[i])
                                insertDict['taskNo'] = taskNo
                                insertDict['subNo'] = '%d' % i
                                insertDict['state'] = STATUS_NOTTRADED
                                insertDict['mainstate'] = STATUS_NOTTRADED
                                if 'objectName' in data[i]:
                                    insertDict['objectName'] = data[i]['objectName']
                                else:
                                    insertDict['objectName'] = ''
                                insertDict['direction'] = ''
                                if objectFlag == 'futures':
                                    if 'direction' in data[i]:
                                        insertDict['direction'] = data[i]['direction']
                                insertSql = """insert into task_flow_present (taskno, subno, state, product, objectcode, objectname, objectclass, direction, buysell, taskprice, offset, taskvolume, fundmanager, trader, mainstate) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                                insertList = [insertDict['taskNo'], insertDict['subNo'], insertDict['state'], insertDict['product'], insertDict['objectCode'], insertDict['objectName'],  insertDict['objectClass'], insertDict['direction'], insertDict['buySell'], insertDict['taskPrice'], insertDict['offset'], insertDict['taskVolume'], insertDict['fundManager'], insertDict['trader'], insertDict['mainstate']]
                                insertTup = tuple(insertList)
                                try:
                                    if self.cursor.execute(insertSql, insertTup):
                                        self.db.commit()
                                        count += 1
                                        item = {}
                                        item['taskNo'] = insertDict['taskNo']
                                        item['subNo'] = insertDict['subNo']
                                        # 将数据放入更新列表
                                        if user in self.updateList:
                                            self.updateList[user].append(item)
                                        if minTrader in self.updateList:
                                            self.updateList[minTrader].append(item)
                                        for manager in self.investManagerList:
                                            if manager != user and manager != minTrader:
                                                if manager in self.updateList:
                                                    self.updateList[manager].append(item)
                                        # 将任务添加到任务列表，只添加子任务
                                        self.taskList[user].append(item)
                                        # self.accountCheck(item['taskNo'], item['subNo'])
                                except:
                                    if self.isConnectedDb():
                                        try:
                                            if self.cursor.execute(insertSql, insertTup):
                                                self.db.commit()
                                                count += 1
                                                item = {}
                                                item['taskNo'] = insertDict['taskNo']
                                                item['subNo'] = insertDict['subNo']
                                                # 将数据放入更新列表
                                                if user in self.updateList:
                                                    self.updateList[user].append(item)
                                                if minTrader in self.updateList:
                                                    self.updateList[minTrader].append(item)
                                                for manager in self.investManagerList:
                                                    if manager != user and manager != minTrader:
                                                        if manager in self.updateList:
                                                            self.updateList[manager].append(item)
                                                # 将任务添加到任务列表，只添加子任务
                                                self.taskList[user].append(item)
                                                # self.accountCheck(item['taskNo'], item['subNo'])
                                        except:
                                            self.fhLog.error('新建任务失败，数据库连接失败')
                                            retDict['retCode'] = RETCODE_DBERROR
                                            return retDict
                                    else:
                                        self.fhLog.error('新建任务失败，数据库连接失败')
                                        retDict['retCode'] = RETCODE_DBERROR
                                        return retDict

                            else:
                                self.fhLog.error('信息有误，无法分配交易员，产品：'+ product +  ',任务要素：' + repr(data[i]))
                        else:
                            self.fhLog.error('新建任务使用用户权限不足，用户：'+ user)
                            retDict['retCode'] = RETCODE_AUTHORITYERROR
                            return retDict
                    else:
                        self.fhLog.warning('新建任务要素不全，任务要素：' + repr(data[i]))
                        retDict['retCode'] = RETCODE_DATAINCOMPLETE
                        return retDict
                else:
                    self.fhLog.warning('新建任务要素不全，无品种信息，任务要素：' + repr(data[i]))
                    retDict['retCode'] = RETCODE_DATAINCOMPLETE
                    return retDict
            if count:
                insertDict = {}
                insertDict['taskNo'] = taskNo
                insertDict['state'] = STATUS_NOTTRADED
                insertDict['objectClass'] = data[0]['objectClass']
                insertDict['objectCode'] = data[0]['objectCode']
                # insertDict['state'] = STATUS_NOTTRADED
                insertDict['state'] = ''
                insertDict['direction'] = ''
                if objectFlag == 'futures':
                    if 'direction' in data[i]['direction']:
                        insertDict['direction'] = data[0]['direction']
                if 'objectName' in data[0]:
                    insertDict['objectName'] = data[0]['objectName']
                else:
                    insertDict['objectName'] = ''
                insertDict['buySell'] = data[0]['buySell']
                insertDict['taskPrice'] = data[0]['taskPrice']
                insertDict['offset'] = data[0]['offset']
                insertDict['fundManager'] = data[0]['fundManager']

                insertSql = """insert into task_flow_present (taskno, state, objectcode, objectname, objectclass, direction, buysell, taskprice, offset, fundmanager) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                insertList = [insertDict['taskNo'], insertDict['state'], insertDict['objectCode'], insertDict['objectName'], insertDict['objectClass'],
                              insertDict['direction'], insertDict['buySell'], insertDict['taskPrice'], insertDict['offset'], insertDict['fundManager']]
                insertTup = tuple(insertList)
                try:
                    if self.cursor.execute(insertSql, insertTup):
                        self.db.commit()
                        item = {}
                        item['taskNo'] = insertDict['taskNo']
                        item['subNo'] = ''
                        self.updateList[user].append(item)
                except:
                    if self.isConnectedDb():
                        try:
                            if self.cursor.execute(insertSql, insertTup):
                                self.db.commit()
                                item = {}
                                item['taskNo'] = insertDict['taskNo']
                                item['subNo'] = ''
                                self.updateList[user].append(item)
                        except:
                            self.fhLog.error('新建任务失败，数据库连接失败')
                            retDict['retCode'] = RETCODE_DBERROR
                            return retDict
                    else:
                        self.fhLog.error('新建任务失败，数据库连接失败')
                        retDict['retCode'] = RETCODE_DBERROR
                        return retDict
            retDict['retCode'] = RETCODE_SUCCESS
            self.updateCache()
            return retDict
        else:
            if VERIFY_COMMENT.get(verifyFlag):
                self.fhLog.warning('权限不足，无法新建任务，用户：' + VERIFY_COMMENT.get(verifyFlag))
            else:
                self.fhLog.warning('权限不足，无法新建任务，用户：' + VERIFY_COMMENT.get(None))
            retDict['retCode'] = RETCODE_AUTHORITYERROR
            return retDict

    # ----------------------------------------------
    def differencSet(self, set1, set2):
        """获得set1与set2的差集，即set1-set2"""
        difList = []
        for item in set1:
            if item not in set2:
                difList.append(item)
        return difList

    # ----------------------------------
    def genNo(self):
        if self.date != time.strftime('%Y%m%d', time.localtime(time.time())):
            self.date = time.strftime('%Y%m%d', time.localtime(time.time()))
            self.suffixNo = 0
        no = self.date+'%04d' % self.suffixNo
        self.suffixNo += 1
        return no

    # -----------------------------------
    def queryPositionChange(self, user, transData):
        retDict = {}
        retDict['data'] = {}
        if 'product' in transData:
            product = transData['product']
        if user in self.cachePositionChangeDict:
            if product in self.cachePositionChangeDict[user]:
                changeFlag = self.cachePositionChangeDict[user][product]
                retDict['data']['changeFlag'] = changeFlag
                self.cachePositionChangeDict[user][product] = False
                retDict['retCode'] = RETCODE_SUCCESS
                for iproduct in self.cachePositionChangeDict[user]:
                    if iproduct != product:
                        self.cachePositionChangeDict[user][iproduct] = True
                return retDict
            else:
                self.cachePositionChangeDict[user][product] = False
                retDict['data']['changeFlag'] = True
                retDict['retCode'] = RETCODE_SUCCESS
                return retDict
        else:
            # self.cachePositionChangeDict[user] = {}
            # self.cachePositionChangeDict[user][product] = False
            retDict['data']['changeFlag'] = False
            retDict['retCode'] = RETCODE_AUTHORITYERROR
            return retDict



        if user in self.cachePosition:
            if len(self.cachePosition[user]) > self.taskBufSize:
                retDict['data'][user] = []
                for i in range(0, self.taskBufSize):
                    retDict['data'][user].append(self.cachePosition[user].pop())
            else:
                retDict['data'][user] = []
                for i in range(0, len(self.cachePosition[user])):
                    retDict['data'][user].append(self.cachePosition[user].pop())
        else:
            self.cachePosition[user] = []
        retDict['retCode'] = RETCODE_SUCCESS
        return retDict

    # # ------------------------------------
    # def queryPositionAll(self, user, transData):
    #     pass
    #
    # # ------------------------------------
    # def queryAccountAll(self, user, transData):
    #     pass

    # ------------------------------------
    # def accountCheck(self, taskNo, subNo):
    #     """
    #     调用情景：
    #     1、添加任务
    #     2、更改状态：在positionCheck中调用 已撤销：可用余额增加；已完成：余额减少
    #     判断逻辑：查询任务状态，根据状态修改
    #     """
    #     selectSql = """select state, taskprice, taskvolume, objectclass, objectcode, transprice, transvolume, product, buysell, direction from task_flow_present where taskno=%s and subno=%s"""
    #     selectTuple = tuple([taskNo, subNo])
    #     if self.cursor.execute(selectSql, selectTuple):
    #         data = self.cursor.fetchone()
    #         state = data[0]
    #         taskPrice = data[1]
    #         taskVolume = data[2]
    #         objectClass = data[3]
    #         objectCode = data[4]
    #         transPrice = data[5]
    #         transVolume = data[6]
    #         product = data[7]
    #         buysell = data[8]
    #         direction = data[9]
    #         selectSql = """select total, balance, available, secvalue, margin from products_account where product=%s and accountclass=%s"""
    #         selectTuple = tuple([product, objectClass])
    #         if self.cursor.execute(selectSql, selectTuple):
    #             data = self.cursor.fetchone()
    #             total = data[0]
    #             balance = data[1]
    #             available = data[2]
    #             secvalue = data[3]
    #             margin = data[4]
    #             updateFlag = False
    #             if objectClass == 'futures':
    #                 marginRatio, priceWeight = self.getFuturesConfig(objectCode)
    #                 if state == STATUS_NOTTRADED:
    #                     if direction == POSITION_ON:
    #                         bias = taskPrice * priceWeight * taskVolume * marginRatio
    #                         newAvailable = available - bias
    #                         updateSql = """update products_account set available=%s where product=%s and accountclass=%s"""
    #                         updateTuple = tuple([newAvailable, product, objectClass])
    #                         updateFlag = True
    #                     elif direction == POSITION_OFF:
    #                         pass
    #                 elif state == STATUS_CANCELLED:
    #                     if direction == POSITION_ON:
    #                         bias = taskPrice * priceWeight * taskVolume * marginRatio
    #                         newAvailable = available + bias
    #                         updateSql = """update products_account set available=%s where product=%s and accountclass=%s"""
    #                         updateTuple = tuple([newAvailable, product, objectClass])
    #                         updateFlag = True
    #                     elif direction == POSITION_OFF:
    #                         pass
    #                 elif state == STATUS_ALLTRADED:
    #                     if direction == POSITION_ON:
    #                         bias = transPrice * priceWeight * transVolume * marginRatio
    #                         newBalance = balance - bias
    #                         newMargin = margin + bias
    #                         updateSql = """update balance set available=%s margin=%s where product=%s and accountclass=%s"""
    #                         updateTuple = tuple([newBalance, newMargin, product, objectClass])
    #                         updateFlag = True
    #                     elif direction == POSITION_OFF:
    #                         selectSql = """select direction, volume, costprice from products_details where product=%s and objectcode=%s"""
    #                         selectTuple = tuple([product, objectCode])
    #                         if self.cursor.execute(selectSql, selectTuple):
    #                             data = self.cursor.fetchone()
    #                             temDirection = data[0]
    #                             temVolume = data[1]
    #                             temCostPrice = data[2]
    #                             if temDirection == TRADE_BUY:
    #                                 profit = transPrice * (transVolume + temVolume)
    #
    #                         pass    # todo 需在持仓中判断
    #                 else:
    #                     pass
    #             elif objectClass == 'sec':
    #                 if state == STATUS_NOTTRADED:
    #                     if buysell == TRADE_BUY:
    #                         bias = taskPrice * taskVolume
    #                         newAvailable = available - bias
    #                         updateSql = """update products_account set available=%s where product=%s and accountclass=%s"""
    #                         updateTuple = tuple([newAvailable, product, objectClass])
    #                         updateFlag = True
    #                     elif buysell == TRADE_SELL:
    #                         pass
    #                 elif state == STATUS_CANCELLED:
    #                     if buysell == TRADE_BUY:
    #                         bias = transPrice * transVolume
    #                         newAvailable = available + bias
    #                         updateSql = """update products_account set available=%s where product=%s and accountclass=%s"""
    #                         updateTuple = tuple([newAvailable, product, objectClass])
    #                         updateFlag = True
    #                     elif buysell == TRADE_SELL:
    #                         pass
    #                 elif state == STATUS_ALLTRADED:
    #                     if buysell == TRADE_BUY:
    #                         bias = transPrice * transVolume
    #                         newBalance = balance - bias
    #                         updateSql = """update products_account set balance=%s where product=%s and accountclass=%s"""
    #                         updateTuple = tuple([newBalance, product, objectClass])
    #                         updateFlag = True
    #                     elif buysell == TRADE_SELL:
    #                         bias = transPrice * transVolume
    #                         newBalance = balance + bias
    #                         updateSql = """update products_account set balance=%s where product=%s and accountclass=%s"""
    #                         updateTuple = tuple([newBalance, product, objectClass])
    #                         updateFlag = True
    #                 else:
    #                     pass
    #             if updateFlag:
    #                 if self.cursor.execute(updateSql, updateTuple):
    #                     self.db.commit()

    # ------------------------------------
    def positionCheck(self, taskNo, subNo, flag=1):
        """
        调用情景：
        1、更改状态-已完成：增减持仓，并更改账户,账户的可用余额不实时更新，只更新可用资金，在买卖时更新，
        2、股票加入了交易成本，期货未加
        注：当为futures时，task_flow_present中的buysell与products_details中的direction意义相同
        flag: 当flag为0时，若数据库异常出错，不再循环调用
        """
        selectSql = """select state, transprice, transvolume, buysell, objectclass, objectcode, direction, product, objectname from task_flow_present where taskno=%s and subno=%s"""
        selectTuple = tuple([taskNo, subNo])
        try:
            if self.cursor.execute(selectSql, selectTuple):
                data = self.cursor.fetchone()
                state = data['state']
                transPrice = data['transprice']
                transVolume = data['transvolume']
                buySell = data['buysell']
                objectClass = data['objectclass']
                objectCode = data['objectcode']
                direction = data['direction']
                product = data['product']
                objectName = data['objectname']
                # 如果未成交，不做操作
                if state != STATUS_ALLTRADED:
                    return
                addBalance = 0  # 用于记录需更改的账户余额
                # 如果为期货
                if objectClass == 'futures':
                    marginRatio, weight = self.getFuturesConfig(objectCode)
                    selectSql = """select costprice, volume, settleprice, todaybuyvolume, todaybuyprice from products_details where product=%s and objectcode=%s and direction=%s"""
                    selectTuple = tuple([product, objectCode, buySell])
                    # 如果查询到信息
                    if self.cursor.execute(selectSql, selectTuple):
                        data = self.cursor.fetchone()
                        costPrice = data['costprice']
                        volume = data['volume']
                        settlePrice = data['settleprice']
                        todayBuyVolume = data['todaybuyvolume']
                        todayBuyPrice = data['todaybuyprice']
                        # 当为平仓时，需判断是否清仓
                        if direction == POSITION_OFF:
                            newVolume = volume - transVolume
                            # 如果新的持仓为0，删除之
                            if newVolume <= 0:
                                updateSql = """delete from products_details where product=%s and objectcode=%s and direction=%s"""
                                updateTuple = tuple([product, objectCode, buySell])
                                # 可用资金应为结算价计算 考虑今日买入合约
                                if buySell == TRADE_BUY:
                                    addBalance = (transPrice - settlePrice) * weight * (volume - todayBuyVolume) + (transPrice - todayBuyPrice) * weight * todayBuyVolume + transPrice * weight * volume * marginRatio
                                elif buySell == TRADE_SELL:
                                    addBalance = (settlePrice - transPrice) * weight * (volume - todayBuyVolume) + (todayBuyPrice - transPrice) * weight * todayBuyVolume + transPrice * weight * volume * marginRatio
                                else:
                                    addBalance = (transPrice - settlePrice) * weight * (volume - todayBuyVolume) + (transPrice - todayBuyPrice) * weight * todayBuyVolume + transPrice * weight * volume * marginRatio
                            # 持仓不为0，更新量价信息，需考虑今日买入的情况
                            else:
                                newCostPrice = (costPrice * volume - transPrice * transVolume) / newVolume
                                # 多单的情况
                                if buySell == TRADE_BUY:
                                    if newVolume < todayBuyVolume:
                                        addBalance = (transPrice - settlePrice) * weight * (volume - todayBuyVolume) + (transPrice - todayBuyPrice) * weight * (todayBuyVolume - newVolume) + transPrice * weight * transVolume * marginRatio
                                        todayBuyVolume = newVolume
                                        updateSql = """update products_details set costprice=%s, volume=%s, price=%s,todaybuyvolume=%s where product=%s and objectcode=%s and direction=%s"""
                                        updateTuple = tuple([newCostPrice, newVolume, transPrice, todayBuyVolume, product, objectCode, buySell])
                                    else:
                                        updateSql = """update products_details set costprice=%s, volume=%s, price=%s, where product=%s and objectcode=%s and direction=%s"""
                                        updateTuple = tuple([newCostPrice, newVolume, transPrice, product, objectCode, buySell])
                                        addBalance = (transPrice - settlePrice) * weight * transVolume + transPrice * weight * transVolume * marginRatio
                                # 为空单的情况
                                else:
                                    if newVolume < todayBuyVolume:
                                        addBalance = (settlePrice - transPrice) * weight * (volume - todayBuyVolume) + (todayBuyPrice - transPrice) * weight * (todayBuyVolume - newVolume) + transPrice * weight * transVolume * marginRatio
                                        todayBuyVolume = newVolume
                                        updateSql = """update products_details set costprice=%s, volume=%s, price=%s,todaybuyvolume=%s where product=%s and objectcode=%s and direction=%s"""
                                        updateTuple = tuple([newCostPrice, newVolume, transPrice, todayBuyVolume, product, objectCode, buySell])
                                    else:
                                        updateSql = """update products_details set costprice=%s, volume=%s, price=%s, where product=%s and objectcode=%s and direction=%s"""
                                        updateTuple = tuple([newCostPrice, newVolume, transPrice, product, objectCode, buySell])
                                        addBalance = (settlePrice - transPrice) * weight * transVolume + transPrice * weight * transVolume * marginRatio
                        # 当为开仓时
                        elif direction == POSITION_ON:
                            newVolume = volume + transVolume
                            newCostPrice = (costPrice * volume + transPrice * transVolume) / newVolume
                            todayBuyPrice = (todayBuyPrice * todayBuyVolume + transPrice * transVolume) / (todayBuyVolume + transVolume)
                            todayBuyVolume += transVolume
                            updateSql = """update products_details set costprice=%s, volume=%s, price=%s, todaybuyprice=%s, todaybuyvolume=%s where product=%s and objectcode=%s and direction=%s"""
                            updateTuple = tuple([newCostPrice, newVolume, transPrice, todayBuyPrice, todayBuyVolume, product, objectCode, buySell])
                            addBalance = - transPrice * transVolume * weight * marginRatio
                    # 若未查询到结果，即无相关信息，直接返回
                    else:
                        if direction == POSITION_OFF:
                            return
                        elif direction == POSITION_ON:
                            updateSql = """insert into products_details (product, objectcode, objectname, objectclass, direction, volume, costprice, price, todaybuyprice, todaybuyvolume) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                            updateTuple = tuple([product, objectCode, objectName, objectClass, buySell, transVolume, transPrice, transPrice, transPrice, transVolume])
                            addBalance = - transPrice * transVolume * weight * marginRatio
                # 如果为股票
                elif objectClass == 'sec':
                    selectSql = """select costprice, volume from products_details where product=%s and objectcode=%s"""
                    selectTuple = tuple([product, objectCode])
                    # 如果查询到信息
                    if self.cursor.execute(selectSql, selectTuple):
                        data = self.cursor.fetchone()
                        costPrice = data['costprice']
                        volume = data['volume']
                        if buySell == TRADE_BUY:
                            newVolume = volume + transVolume
                            newCostPrice = (costPrice * volume + transPrice * transVolume * (1 + SEC_BUY_COST)) / newVolume
                            updateSql = """update products_details set costprice=%s, volume=%s, price=%s where product=%s and objectcode=%s"""
                            updateTuple = tuple([newCostPrice, newVolume, transPrice, product, objectCode])
                            addBalance = - transVolume * transVolume * (1 + SEC_BUY_COST)
                        # 如果是卖出，需判断是否清仓
                        elif buySell == TRADE_SELL:
                            newVolume = volume - transVolume
                            if newVolume <= 0:
                                updateSql = """delete from products_details where product=%s and objectcode=%s"""
                                updateTuple = tuple([product, objectCode])
                                addBalance = transPrice * volume * (1 - SEC_SELL_COST)
                            # 否则，更新量价信息
                            else:
                                newCostPrice = (costPrice * volume - transPrice * transVolume * 0.9987) / newVolume
                                updateSql = """update products_details set costprice=%s, volume=%s, price=%s where product=%s and objectcode=%s"""
                                updateTuple = tuple([newCostPrice, newVolume, transPrice, product, objectCode])
                                addBalance = transPrice * transVolume * (1 - SEC_SELL_COST)
                    # 如果无信息
                    else:
                        if buySell == TRADE_BUY:
                            costPrice = transPrice * (1 + SEC_BUY_COST) / transVolume
                            updateSql = """insert into products_details (product, objectcode, objectname, objectclass, volume, costprice, price) values (%s, %s, %s, %s, %s, %s, %s)"""
                            updateTuple = tuple([product, objectCode, objectName, objectClass, transVolume, costPrice, transPrice])
                            addBalance = - transPrice * transVolume * (1 + SEC_BUY_COST)
                        # 无信息情况下，直接返回
                        else:
                            return
                try:
                    if self.cursor.execute(updateSql, updateTuple):
                        self.db.commit()
                        selectSql = """select balance from products_account where product=%s and accountclass=%s"""
                        selectTuple = tuple([product, objectClass])
                        try:
                            if self.cursor.execute(selectSql, selectTuple):
                                oldBalance = self.cursor.fetchone()['balance']
                                newBalance = oldBalance + addBalance
                                updateSql = """update products_account set balance=%s where product=%s and accountclass=%s"""
                                updateTuple = tuple([newBalance, product, objectClass])

                                try:
                                    if self.cursor.execute(updateSql, updateTuple):
                                        self.db.commit()
                                        for user in self.cachePositionChangeDict:
                                            if product in self.cachePositionChangeDict[user]:
                                                self.cachePositionChangeDict[user][product] = True
                                            else:
                                                self.cachePositionChangeDict[user][product] = True
                                except:
                                    if self.isConnectedDb():
                                        try:
                                            if self.cursor.execute(updateSql, updateTuple):
                                                self.db.commit()
                                                for user in self.cachePositionChangeDict:
                                                    if product in self.cachePositionChangeDict[user]:
                                                        self.cachePositionChangeDict[user][product] = True
                                                    else:
                                                        self.cachePositionChangeDict[user][product] = True
                                        except:
                                            self.fhLog.error('数据库连接失败')
                        except:
                            if self.isConnectedDb():
                                if self.cursor.execute(selectSql, selectTuple):
                                    oldBalance = self.cursor.fetchone()['balance']
                                    newBalance = oldBalance + addBalance
                                    updateSql = """update products_account set balance=%s where product=%s and accountclass=%s"""
                                    updateTuple = tuple([newBalance, product, objectClass])

                                    try:
                                        if self.cursor.execute(updateSql, updateTuple):
                                            self.db.commit()
                                            for user in self.cachePositionChangeDict:
                                                if product in self.cachePositionChangeDict[user]:
                                                    self.cachePositionChangeDict[user][product] = True
                                                else:
                                                    self.cachePositionChangeDict[user][product] = True
                                    except:
                                        if self.isConnectedDb():
                                            try:
                                                if self.cursor.execute(updateSql, updateTuple):
                                                    self.db.commit()
                                                    for user in self.cachePositionChangeDict:
                                                        if product in self.cachePositionChangeDict[user]:
                                                            self.cachePositionChangeDict[user][product] = True
                                                        else:
                                                            self.cachePositionChangeDict[user][product] = True
                                            except:
                                                self.fhLog.error('数据库连接失败')
                except:
                    if self.isConnectedDb():
                        if self.cursor.execute(updateSql, updateTuple):
                            self.db.commit()
                            selectSql = """select balance from products_account where product=%s and accountclass=%s"""
                            selectTuple = tuple([product, objectClass])
                            try:
                                if self.cursor.execute(selectSql, selectTuple):
                                    oldBalance = self.cursor.fetchone()['balance']
                                    newBalance = oldBalance + addBalance
                                    updateSql = """update products_account set balance=%s where product=%s and accountclass=%s"""
                                    updateTuple = tuple([newBalance, product, objectClass])

                                    try:
                                        if self.cursor.execute(updateSql, updateTuple):
                                            self.db.commit()
                                            for user in self.cachePositionChangeDict:
                                                if product in self.cachePositionChangeDict[user]:
                                                    self.cachePositionChangeDict[user][product] = True
                                                else:
                                                    self.cachePositionChangeDict[user][product] = True
                                    except:
                                        if self.isConnectedDb():
                                            try:
                                                if self.cursor.execute(updateSql, updateTuple):
                                                    self.db.commit()
                                                    for user in self.cachePositionChangeDict:
                                                        if product in self.cachePositionChangeDict[user]:
                                                            self.cachePositionChangeDict[user][product] = True
                                                        else:
                                                            self.cachePositionChangeDict[user][product] = True
                                            except:
                                                self.fhLog.error('数据库连接失败')
                            except:
                                if self.isConnectedDb():
                                    if self.cursor.execute(selectSql, selectTuple):
                                        oldBalance = self.cursor.fetchone()['balance']
                                        newBalance = oldBalance + addBalance
                                        updateSql = """update products_account set balance=%s where product=%s and accountclass=%s"""
                                        updateTuple = tuple([newBalance, product, objectClass])

                                        try:
                                            if self.cursor.execute(updateSql, updateTuple):
                                                self.db.commit()
                                                for user in self.cachePositionChangeDict:
                                                    if product in self.cachePositionChangeDict[user]:
                                                        self.cachePositionChangeDict[user][product] = True
                                                    else:
                                                        self.cachePositionChangeDict[user][product] = True
                                        except:
                                            if self.isConnectedDb():
                                                try:
                                                    if self.cursor.execute(updateSql, updateTuple):
                                                        self.db.commit()
                                                        for user in self.cachePositionChangeDict:
                                                            if product in self.cachePositionChangeDict[user]:
                                                                self.cachePositionChangeDict[user][product] = True
                                                            else:
                                                                self.cachePositionChangeDict[user][product] = True
                                                except:
                                                    self.fhLog.error('数据库连接失败')

        except:
            if self.isConnectedDb() and flag:
                newFlag = 0
                self.positionCheck(taskNo, subNo, newFlag)

    # ------------------------------------
    def getFuturesConfig(self, code):
        if len(code) > 2:
            pre = code[0:2]
            selectSql = """select marginratio, weight from parameter_futures where prefix like %s"""
            selectTup = tuple([pre+'%'])
            try:
                if self.cursor.execute(selectSql, selectTup):
                    data = self.cursor.fetchone()
                    marginRatio = data['marginratio']
                    weight = data['weight']
                    return marginRatio, weight
            except:
                if self.isConnectedDb():
                    try:
                        if self.cursor.execute(selectSql, selectTup):
                            data = self.cursor.fetchone()
                            marginRatio = data['marginratio']
                            weight = data['weight']
                            return marginRatio, weight
                    except:
                        self.fhLog.error('数据库连接失败')
                        return 1, 1
        return 1, 1

    # ---------------------------------
    def randSelect(self, data):
        if type(data) != list:
            return None
        length = len(data)
        if length >= 2:
            ind = random.randint(0, length-1)
            return data[ind]
        elif length == 1:
            return data[0]
        else:
            return None

    # ---------------------------------------
    def checkFields(self, data, fields):
        for field in fields:
            if field not in data:
                return False
        return True

    # -------------------------------------
    def copyFields(self, dict, data):
        for field in data:
            dict[field] = data[field]

    # -------------------------------------------
    def getProductUser(self, product):
        retDict = {}
        selectSql = """select fundmanager, trader from products_info where product=%s"""
        selectTuple = tuple([product])
        try:
            if self.cursor.execute(selectSql, selectTuple):
                data = self.cursor.fetchone()
                fundManager = data['fundmanager']
                traderStr = data['trader']
                retDict['user'] = []
                retDict['fundManager'] = fundManager
                retDict['user'].append(fundManager)
                traderList = traderStr.split(';')
                retDict['trader'] = traderList
                for trader in traderList:
                    retDict['user'].append(trader)
        except:
            if self.isConnectedDb():
                try:
                    if self.cursor.execute(selectSql, selectTuple):
                        data = self.cursor.fetchone()
                        fundManager = data['fundmanager']
                        traderStr = data['trader']
                        retDict['user'] = []
                        retDict['fundManager'] = fundManager
                        retDict['user'].append(fundManager)
                        traderList = traderStr.split(';')
                        retDict['trader'] = traderList
                        for trader in traderList:
                            retDict['user'].append(trader)
                except:
                    self.fhLog.error('数据库连接失败')
        return retDict

    # -------------------------------------------------
    def getTaskUser(self, taskNo, subNo):
        """
        获取任务的相关方，fundManager、trader
        """
        retDict = {}
        retDict['user'] = []
        retDict['fundManager'] = []
        retDict['trader'] = []

        if subNo:
            selectSql = """select fundmanager, trader from task_flow_present where taskno=%s and subno=%s"""
            selectTuple = tuple([taskNo, subNo])
            try:
                if self.cursor.execute(selectSql, selectTuple):
                    data = self.cursor.fetchone()
                    fundManager = data['fundmanager']
                    trader = data['trader']
                    retDict['user'] = []
                    retDict['fundManager'] = fundManager
                    retDict['user'].append(fundManager)
                    retDict['trader'] = trader
                    retDict['user'].append(trader)
            except:
                if self.isConnectedDb():
                    try:
                        if self.cursor.execute(selectSql, selectTuple):
                            data = self.cursor.fetchone()
                            fundManager = data['fundmanager']
                            trader = data['trader']
                            retDict['user'] = []
                            retDict['fundManager'] = fundManager
                            retDict['user'].append(fundManager)
                            retDict['trader'] = trader
                            retDict['user'].append(trader)
                    except:
                        self.fhLog.error('数据库连接失败')
        else:
            selectSql = """select fundmanager, trader from task_flow_present where taskno=%s"""
            selectTuple = tuple([taskNo])
            try:
                if self.cursor.execute(selectSql, selectTuple):
                    data = self.cursor.fetchall()
                    for item in data:
                        fundManager = item['fundmanager']
                        if fundManager:
                            if fundManager not in retDict['fundManager']:
                                retDict['fundManager'].append(fundManager)
                                retDict['user'].append(fundManager)
                        trader = item['trader']
                        if trader:
                            if trader not in retDict['trader']:
                                retDict['trader'].append(trader)
                                retDict['user'].append(trader)
            except:
                if self.isConnectedDb():
                    try:
                        if self.cursor.execute(selectSql, selectTuple):
                            data = self.cursor.fetchall()
                            for item in data:
                                fundManager = item['fundmanager']
                                if fundManager:
                                    if fundManager not in retDict['fundManager']:
                                        retDict['fundManager'].append(fundManager)
                                        retDict['user'].append(fundManager)
                                trader = item['trader']
                                if trader:
                                    if trader not in retDict['trader']:
                                        retDict['trader'].append(trader)
                                        retDict['user'].append(trader)
                    except:
                        self.fhLog.error('数据库连接失败')
        return retDict

    # ---------------------------------------------
    def update(self, user):
        """
        更新cashList信息，将数据库中符合条件的任务全部选出来
        条件：今天 or 状态为未完成、部分完成
        维度：状态以主任务状态为准，通过subno为空进行判断
        """
        today = datetime.date.today()
        if user in self.investManagerList:
            select_sql = """select * from task_flow_present where tasktime>=%s"""
            selectFactor = tuple([today])
        else:
            select_sql = """select * from task_flow_present where (fundmanager like %s or trader like %s) and tasktime>=%s"""
            selectFactor = tuple(['%'+user+'%', '%'+user+'%', today])
        try:
            num = self.cursor.execute(select_sql, selectFactor)
            if num:
                data = self.cursor.fetchall()
                cacheFlag = False
                if user in self.cacheList:
                    self.cacheList.pop(user)
                    self.cacheList[user] = []
                    cacheFlag = True
                taskFlag = False
                if user in self.taskList:
                    self.taskList.pop(user)
                    self.taskList[user] = []
                    taskFlag = True
                for i in range(0, len(data)):
                    szDict = {}
                    szDict['taskNo'] = data[i]['taskno']
                    szDict['subNo'] = data[i]['subno']
                    szDict['taskTime'] = data[i]['tasktime']
                    szDict['finishTime'] = data[i]['finishtime']
                    szDict['state'] = data[i]['state']
                    szDict['product'] = data[i]['product']
                    szDict['objectCode'] = data[i]['objectcode']
                    szDict['objectName'] = data[i]['objectname']
                    szDict['objectClass'] = data[i]['objectclass']
                    szDict['direction'] = data[i]['direction']
                    szDict['buySell'] = data[i]['buysell']
                    szDict['taskPrice'] = data[i]['taskprice']
                    szDict['offset'] = data[i]['offset']
                    szDict['transPrice'] = data[i]['transprice']
                    szDict['taskVolume'] = data[i]['taskvolume']
                    szDict['transVolume'] = data[i]['transvolume']
                    szDict['fundManager'] = data[i]['fundmanager']
                    szDict['trader'] = data[i]['trader']
                    szDict['remark'] = data[i]['remark']
                    if szDict['subNo']:
                        item = {}
                        item['taskNo'] = szDict['taskNo']
                        item['subNo'] = szDict['subNo']
                        if taskFlag:
                            self.taskList[user].append(item)
                    if cacheFlag:
                        self.cacheList[user].append(szDict)
        except:
            if self.isConnectedDb():
                try:
                    num = self.cursor.execute(select_sql, selectFactor)
                    if num:
                        data = self.cursor.fetchall()
                        cacheFlag = False
                        if user in self.cacheList:
                            self.cacheList.pop(user)
                            self.cacheList[user] = []
                            cacheFlag = True
                        taskFlag = False
                        if user in self.taskList:
                            self.taskList.pop(user)
                            self.taskList[user] = []
                            taskFlag = True
                        for i in range(0, len(data)):
                            szDict = {}
                            szDict['taskNo'] = data[i]['taskno']
                            szDict['subNo'] = data[i]['subno']
                            szDict['taskTime'] = data[i]['tasktime']
                            szDict['finishTime'] = data[i]['finishtime']
                            szDict['state'] = data[i]['state']
                            szDict['product'] = data[i]['product']
                            szDict['objectCode'] = data[i]['objectcode']
                            szDict['objectName'] = data[i]['objectname']
                            szDict['objectClass'] = data[i]['objectclass']
                            szDict['direction'] = data[i]['direction']
                            szDict['buySell'] = data[i]['buysell']
                            szDict['taskPrice'] = data[i]['taskprice']
                            szDict['offset'] = data[i]['offset']
                            szDict['transPrice'] = data[i]['transprice']
                            szDict['taskVolume'] = data[i]['taskvolume']
                            szDict['transVolume'] = data[i]['transvolume']
                            szDict['fundManager'] = data[i]['fundmanager']
                            szDict['trader'] = data[i]['trader']
                            szDict['remark'] = data[i]['remark']
                            if szDict['subNo']:
                                item = {}
                                item['taskNo'] = szDict['taskNo']
                                item['subNo'] = szDict['subNo']
                                if taskFlag:
                                    self.taskList[user].append(item)
                            if cacheFlag:
                                self.cacheList[user].append(szDict)
                except:
                    self.fhLog.error('数据库连接失败')
                    return False
        return True

    # ------------------------------
    def updateCache(self):
        for user in self.updateList:
            while self.updateList[user]:
                item = self.updateList[user].pop()
                taskNo = item['taskNo']
                subNo = item['subNo']
                self.pushCache(user, taskNo, subNo)

    # ------------------------------------------
    def pushCache(self, user, taskNo, subNo):
        selectSql = """select * from task_flow_present where taskno=%s and subno=%s"""
        selectTuple = tuple([taskNo, subNo])
        try:
            if self.cursor.execute(selectSql, selectTuple):
                data = self.cursor.fetchone()
                szDict = {}
                szDict['taskNo'] = data['taskno']
                szDict['subNo'] = data['subno']
                szDict['taskTime'] = data['tasktime']
                szDict['finishTime'] = data['finishtime']
                szDict['state'] = data['state']
                szDict['product'] = data['product']
                szDict['objectCode'] = data['objectcode']
                szDict['objectName'] = data['objectname']
                szDict['objectClass'] = data['objectclass']
                szDict['direction'] = data['direction']
                szDict['buySell'] = data['buysell']
                szDict['taskPrice'] = data['taskprice']
                szDict['offset'] = data['offset']
                szDict['transPrice'] = data['transprice']
                szDict['taskVolume'] = data['taskvolume']
                szDict['transVolume'] = data['transvolume']
                szDict['fundManager'] = data['fundmanager']
                szDict['trader'] = data['trader']
                szDict['remark'] = data['remark']
                self.cacheList[user].append(szDict)
        except:
            if self.isConnectedDb():
                # try:
                if self.cursor.execute(selectSql, selectTuple):
                    data = self.cursor.fetchone()
                    szDict = {}
                    szDict['taskNo'] = data['taskno']
                    szDict['subNo'] = data['subno']
                    szDict['taskTime'] = data['tasktime']
                    szDict['finishTime'] = data['finishtime']
                    szDict['state'] = data['state']
                    szDict['product'] = data['product']
                    szDict['objectCode'] = data['objectcode']
                    szDict['objectName'] = data['objectname']
                    szDict['objectClass'] = data['objectclass']
                    szDict['direction'] = data['direction']
                    szDict['buySell'] = data['buysell']
                    szDict['taskPrice'] = data['taskprice']
                    szDict['offset'] = data['offset']
                    szDict['transPrice'] = data['transprice']
                    szDict['taskVolume'] = data['taskvolume']
                    szDict['transVolume'] = data['transvolume']
                    szDict['fundManager'] = data['fundmanager']
                    szDict['trader'] = data['trader']
                    szDict['remark'] = data['remark']
                    self.cacheList[user].append(szDict)
                # except:
                #     self.fhLog.error('数据库连接失败')

    # ------------------------------
    def modifyState(self, transData, user):
        """
        状态更改操作逻辑：
        1、只能修改子任务状态，前端操作只能是针对子任务的操作，需加提醒
        2、主任务不再设置任务状态，在数据库中不做更新
        3、对于前端所有任务完成后的额外操作，可前端自行判断，后端不做判断
        """
        retDict = {}
        if 'data' in transData and 'option' in transData:
            data = transData['data']
            option = transData['option']
            verifyFlag = self.registerList[user]['verifyFlag']
            # 如果 不是基金经理或管理员，且进行取消和撤销取消操作，直接返回，不处理
            if verifyFlag != VERIFY_FUNDMANAGER and verifyFlag != VERIFY_ADMIN and verifyFlag != VERIFY_INVESTMANAGER:
                if option == OPTION_CANCEL or option == OPTION_REVOKECANCEL:
                    retDict['retCode'] = RETCODE_AUTHORITYERROR
                    return retDict
            for item in data:
                taskNo = item['taskNo']
                subNo = item['subNo']
                # 如果为子任务
                if subNo:
                    if self.changeState(option, taskNo, subNo, item):
                        pass
                else:
                    changeFlag = False
                    for field in self.taskList[user]:
                        if field['taskNo'] == taskNo:
                            if self.changeState(option, taskNo, field['subNo'], item):
                                changeFlag = True
                            else:
                                self.fhLog.warning('状态更改出错，交易数据：'+ repr(transData))
             # 更新Cache
            self.updateCache()
            retDict['retCode'] = RETCODE_SUCCESS
            return retDict
        retDict['retCode'] = RETCODE_DATAPARSEERROR
        return retDict

    # -------------------------------------------
    def changeState(self, option, taskNo, subNo, item):
        """subNo需不为空，即更改子任务"""
        if subNo:
            selectSql = """select state from task_flow_present where taskno=%s and subno=%s"""
            selectData = ([taskNo, subNo])
            # 得到原有状态
            if self.cursor.execute(selectSql, selectData):
                oldState = self.cursor.fetchone()['state']

            if option == OPTION_TRADED:
                if 'transPrice' in item:
                    transPrice = item['transPrice']
                    selectSql = """select taskvolume from task_flow_present where taskno=%s and subno=%s"""
                    selectTuple = tuple([taskNo, subNo])
                    if self.cursor.execute(selectSql, selectTuple):
                        transVolume = self.cursor.fetchone()['taskvolume']
                    else:
                        return False
                    nowtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    newState = STATUS_ALLTRADED
                    updateSql = """update task_flow_present set state=%s, transprice=%s, transvolume=%s, finishtime=%s where taskno=%s and subno=%s"""
                    updateData = ([newState, transPrice, transVolume, nowtime, taskNo, subNo])
                else:
                    self.fhLog.warning('字段不全，部分字段：'+ repr(item))
                    return False
            elif option == OPTION_NOTTRADED:
                newState = STATUS_NOTTRADED
                # 交易价格和交易量设为0
                if oldState == STATUS_ALLTRADED:
                    # 如果为‘已完成’
                    updateSql = """update task_flow_present set state=%s, transprice=0, transvolume=0 where taskno=%s and subno=%s"""
                    updateData = ([newState, taskNo, subNo])
                else:
                    # 否则，返回True，不更新
                    return True
            elif option == OPTION_CANCEL:
                if oldState == STATUS_NOTTRADED:
                    newState = STATUS_CANCELLED
                    updateSql = """update task_flow_present set state=%s where taskno=%s and subno=%s"""
                    updateData = ([newState, taskNo, subNo])
                else:
                    # 否则，返回True，不更新
                    return True
            elif option == OPTION_REVOKECANCEL:
                if oldState == STATUS_CANCELLED:
                    # 如果为 已撤销
                    newState = STATUS_NOTTRADED
                    updateSql = """update task_flow_present set state=%s where taskno=%s and subno=%s"""
                    updateData = ([newState, taskNo, subNo])
                else:
                    # 否则，返回True，不更新
                    return True
            # 若不在上述操作中
            else:
                return False

            # 更新数据库
            try:
                if self.cursor.execute(updateSql, updateData):
                    # self.db.commit()
                    # 更新持仓及账户信息
                    if self.updateFlag:
                        if option == OPTION_TRADED and oldState != STATUS_ALLTRADED:
                            self.positionCheck(taskNo, subNo)
                    # 将任务放入updateList中
                    item = {}
                    item['taskNo'] = taskNo
                    item['subNo'] = subNo
                    taskUsers = self.getTaskUser(item['taskNo'], item['subNo'])
                    for user in taskUsers['user']:
                        if user in self.updateList:
                            self.updateList[user].append(item)
                    return True
            except:
                if self.isConnectedDb():
                    try:
                        if self.cursor.execute(updateSql, updateData):
                            # self.db.commit()
                            # 更新持仓及账户信息
                            if self.updateFlag:
                                if option == OPTION_TRADED and oldState != STATUS_ALLTRADED:
                                    self.positionCheck(taskNo, subNo)
                                # 将任务放入updateList中
                                item = {}
                                item['taskNo'] = taskNo
                                item['subNo'] = subNo
                                taskUsers = self.getTaskUser(item['taskNo'], item['subNo'])
                                for user in taskUsers['user']:
                                    if user in self.updateList:
                                        self.updateList[user].append(item)
                            return True
                    except:
                        self.fhLog.error('数据库连接失败')
        return False

    # ----------------------------------------------
    def addRemark(self, transData):
        retDict = {}
        if 'user' in transData and 'remark' in transData and 'taskNo' in transData and 'subNo' in transData:
            user = transData['user']
            remark = transData['remark']
            taskNo = transData['taskNo']
            subNo = transData['subNo']
            item = {}
            item['taskNo'] = taskNo
            item['subNo'] = subNo
            self.updateList[user].append(item)
            oldRemark = self.getRemark(taskNo, subNo)
            if oldRemark:
                oldSplit = oldRemark.split('\n')
                newSplit = []
                for userRemark in oldSplit:
                    tem = userRemark.split(':')
                    if tem[0] == user:
                        tSplit = user + ':' + remark
                        newSplit.append(tSplit)
                    else:
                        newSplit.append(userRemark)
                newRemark = '\n'.join(newSplit)
            else:
                newRemark = user + ':' + remark
            if self.updateRemark(newRemark, taskNo, subNo):
                retDict['retCode'] = RETCODE_SUCCESS
            else:
                retDict['retCode'] = RETCODE_ERROR
            self.updateCache()
        else:
            self.fhLog.warning('格式错误：缺少相关字段，交易数据：' + transData)
            retDict['retCode'] = RETCODE_DATAPARSEERROR
        return retDict

    # --------------------------------------------
    def getRemark(self, taskNo, subNo):
        selectSql = """select remark from task_flow_present where taskno=%s and subno=%s"""
        selectTuple = tuple([taskNo, subNo])
        try:
            if self.cursor.execute(selectSql, selectTuple):
                data = self.cursor.fetchone()['remark']
                if data:
                    return data
                else:
                    return ''
        except:
            if self.isConnectedDb():
                try:
                    if self.cursor.execute(selectSql, selectTuple):
                        data = self.cursor.fetchone()['remark']
                        if data:
                            return data
                        else:
                            return ''
                except:
                    self.fhLog.error('数据库连接失败')
                    return ''

    # ---------------------------
    def updateRemark(self, remark, taskNo, subNo):
        updateSql = """update task_flow_present set remark=%s where taskno=%s and subno=%s"""
        updateTuple = tuple([remark, taskNo, subNo])
        try:
            if self.cursor.execute(updateSql, updateTuple):
                # self.db.commit()
                return True
        except:
            if self.isConnectedDb():
                try:
                    if self.cursor.execute(updateSql, updateTuple):
                        # self.db.commit()
                        return True
                except:
                    self.fhLog.error('数据库连接失败')
        return False

    # -----------------------------------------------
    def onAccountTimer(self):
        while self.updateAccountFlag:
            if self.updateFlag:
                temDict = {}
                selectSql = """select product, accountclass, total, balance, available, secvalue, margin, todayprofit from products_account where accountclass=%s"""
                selectTuple = tuple(['sec'])
                try:
                    if self.cursor.execute(selectSql, selectTuple):
                        data = self.cursor.fetchall()
                        for i in range(len(data)):
                            tem = {}
                            tem['product'] = data[i]['product']
                            tem['accountClass'] = data[i]['accountclass']
                            tem['total'] = data[i]['total']
                            tem['balance'] = data[i]['balance']
                            tem['available'] = data[i]['available']
                            tem['secValue'] = data[i]['secvalue']
                            tem['margin'] = data[i]['margin']
                            tem['todayProfit'] = data[i]['todayprofit']
                            if tem['product'] not in temDict:
                                temDict[tem['product']] = []
                            temDict[tem['product']].append(tem)
                except:
                    if self.isConnectedDb():
                        try:
                            if self.cursor.execute(selectSql, selectTuple):
                                data = self.cursor.fetchall()
                                for i in range(len(data)):
                                    tem = {}
                                    tem['product'] = data[i]['product']
                                    tem['accountClass'] = data[i]['accountclass']
                                    tem['total'] = data[i]['total']
                                    tem['balance'] = data[i]['balance']
                                    tem['available'] = data[i]['available']
                                    tem['secValue'] = data[i]['secvalue']
                                    tem['margin'] = data[i]['margin']
                                    tem['todayProfit'] = data[i]['todayprofit']
                                    if tem['product'] not in temDict:
                                        temDict[tem['product']] = []
                                    temDict[tem['product']].append(tem)
                        except:
                            self.fhLog.error('数据库连接失败')
                            continue
                selectSql = """select product, accountclass, total, balance, available, secvalue, margin, todayprofit from products_account where accountclass=%s"""
                selectTuple = tuple(['futures'])
                try:
                    if self.cursor.execute(selectSql, selectTuple):
                        data = self.cursor.fetchall()
                        for i in range(len(data)):
                            tem = {}
                            tem['product'] = data[i]['product']
                            tem['accountClass'] = data[i]['accountclass']
                            tem['total'] = data[i]['total']
                            tem['balance'] = data[i]['balance']
                            tem['available'] = data[i]['available']
                            tem['secValue'] = data[i]['secvalue']
                            tem['margin'] = data[i]['margin']
                            tem['todayProfit'] = data[i]['todayprofit']
                            if tem['product'] not in temDict:
                                temDict[tem['product']] = []
                            temDict[tem['product']].append(tem)
                except:
                    if self.isConnectedDb():
                        try:
                            if self.cursor.execute(selectSql, selectTuple):
                                data = self.cursor.fetchall()
                                for i in range(len(data)):
                                    tem = {}
                                    tem['product'] = data[i]['product']
                                    tem['accountClass'] = data[i]['accountclass']
                                    tem['total'] = data[i]['total']
                                    tem['balance'] = data[i]['balance']
                                    tem['available'] = data[i]['available']
                                    tem['secValue'] = data[i]['secvalue']
                                    tem['margin'] = data[i]['margin']
                                    tem['todayProfit'] = data[i]['todayprofit']
                                    if tem['product'] not in temDict:
                                        temDict[tem['product']] = []
                                    temDict[tem['product']].append(tem)
                        except:
                            self.fhLog.error('数据库连接失败')
                            continue
                self.accountDict = temDict

            time.sleep(self.accountInterval)

    # -------------------------------------
    def queryAccount(self, user, transData):
        retDict = {}
        if 'product' in transData:
            product = transData['product']
        else:
            retDict['retCode'] = RETCODE_DATAPARSEERROR
            retDict['data'] = []
        if product in self.accountDict:
            retDict['data'] = self.accountDict[product]
            retDict['retCode'] = RETCODE_SUCCESS
            return retDict
        else:
            retDict['retCode'] = RETCODE_ERROR
            retDict['data'] = []
            return retDict

    # -------------------------------
    # def onUpdateTimer(self):
    #     while self.updateFlag:
    #         time.sleep(self.updateInterval)
    #         if self.connectFlag:
    #             while self.updateHandlerList:
    #                 hander = self.updateHandlerList.pop()
    #                 hander()
    #         else:
    #             self.connectDb()

    # -------------------------------
    # def onSecValue(self):
    #     for product in self.secValueCache:
    #         if 'secValue' in self.secValueCache[product]:
    #             value = self.secValueCache[product]['secValue']
    #             selectSql = """select balance from products_account where product=%s and accountclass='sec'"""
    #             selectTuple = tuple([product])
    #             if self.cursor.execute(selectSql, selectTuple):
    #                 data = self.cursor.fetchone()
    #                 balance = data[0]
    #                 total = balance + value
    #                 updateSql = """update products_account set total=%s, secvalue=%s where product=%s and accountclass='sec'"""
    #                 updateTuple = tuple([total, value, product])
    #                 if self.cursor.execute(updateSql, updateTuple):
    #                     self.db.commit()

    # --------------------------------------
    # def onFuturesTodayInfo(self):
    #     for product in self.futuresToday:
    #         if 'margin' in self.futuresToday[product] and 'todayProfit' in self.futuresToday[product]:
    #             margin =  self.futuresToday[product]['margin']
    #             todayProfit =  self.futuresToday[product]['todayProfit']
    #             updateSql = """update products_account set todayprofit=%s, margin=%s where product=%s and accountclass='futures'"""
    #             updateTuple = tuple([todayProfit, margin, product])
    #             if self.cursor.execute(updateSql, updateTuple):
    #                 self.db.commit()

    # ------------------------------
    # def updateSecValue(self, data):
    #     if 'product' in data and 'secValue' in data:
    #         product = data['product']
    #         if product not in self.secValueCache:
    #             self.secValueCache[product] = {}
    #             self.secValueCache[product]['secValue'] = data['secValue']
    #         else:
    #             self.secValueCache[product]['secValue'] = data['secValue']
    #         if self.onSecValue not in self.updateHandlerList:
    #             self.updateHandlerList.append(self.onSecValue)
    #     retDict = {}
    #     retDict['retCode'] = RETCODE_SUCCESS
    #     return retDict

    # ---------------------------
    # def updateFuturesTodayInfo(self, data):
    #     if 'product' in data and 'margin' in data and 'todayProfit' in data:
    #         product = data['product']
    #         if product not in self.futuresToday:
    #             self.futuresToday[product] = {}
    #             self.futuresToday[product]['margin'] = data['margin']
    #             self.futuresToday[product]['todayProfit'] = data['todayProfit']
    #         else:
    #             self.futuresToday[product]['margin'] = data['margin']
    #             self.futuresToday[product]['todayProfit'] = data['todayProfit']
    #         if self.onFuturesTodayInfo not in self.updateHandlerList:
    #             self.updateHandlerList.append(self.onFuturesTodayInfo)
    #     retDict = {}
    #     retDict['retCode'] = RETCODE_SUCCESS
    #     return retDict

# ==================================
if __name__ == '__main__':
    fhLog = logging.getLogger("serverLog")
    fhLog.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    fileHandler = logging.handlers.TimedRotatingFileHandler('logs/log', 'midnight', 1, 50)
    fileHandler.suffix = "%Y%m%d"
    fileHandler.setFormatter(formatter)
    fhLog.addHandler(fileHandler)
    server = FhServer()
    # raw_input('Server Stopped, Please press ENTER to continue...')
    fhLog.info('server程序结束')
