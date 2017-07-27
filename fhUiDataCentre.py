# coding=utf-8

"""
Time : 2016/8/3 10:18
Author : Jia Jielin
Company: fhhy.co
File : fhUiDataCentre.py
Description:

"""

# system module

# third party module


# own module
from fhUiBase import *


class DataCentreTab(QtGui.QWidget):
    """数据中心"""
    def __init__(self, mainEngine, eventEngine, cache, parent=None):
        super(DataCentreTab, self).__init__(parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.dbUtils = self.cache['dbUtils']
        self.user = self.cache['loginName']
        self.verifyFlag = self.cache['verifyFlag']
        if self.verifyFlag == VERIFY_FUNDMANAGER:
            self.productList = self.dbUtils.getProductsByManager(self.user)
        else:
            self.productList = self.cache['productList']
        # 配置标记，用于配置回撤比例
        if self.verifyFlag == VERIFY_FUNDMANAGER or self.verifyFlag == VERIFY_ADMIN or self.verifyFlag == VERIFY_INVESTMANAGER:
            self.configFlag = True
        else:
            self.configFlag = False

        self.initUi()

    # --------------------------
    def initUi(self):
        self.tree = QtGui.QTreeWidget()
        self.tree.setMaximumWidth(300)
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels([u''])
        self.rootHome = QtGui.QTreeWidgetItem(self.tree)
        self.rootHome.setText(0, unicode(HOME_PAGE))
        # 建立产品列表
        self.rootProductList = QtGui.QTreeWidgetItem(self.tree)
        self.rootProductList.setText(0, u'产品列表')

        self.productItem = [QtGui.QTreeWidgetItem(self.rootProductList) for product in self.productList]
        for i in range(0, len(self.productList)):
            self.productItem[i].setText(0, unicode(self.productList[i]))
        self.rootProductList.setExpanded(True)

        self.infoW = InfoWidget(self.mainEngine, self.eventEngine, self.cache, u'')

        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(self.tree)
        hLayout.addWidget(self.infoW)
        self.setLayout(hLayout)

        self.connect(self.tree, QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*, int)"), self.onDoubleClick)

    # --------------------------
    def onDoubleClick(self, item, i):
        if item.childCount() == 0:
            for product in self.productList:
                if item.text(i) == unicode(product):
                    self.infoW.changeInfo(product)
            if item.text(i) == unicode(HOME_PAGE):
                self.infoW.changeInfo(product=None)
            elif item.text(i) == u'数据维护':
                pass
                # self.infoW.changeInfo(product='refresh')
            else:
                self.infoW.changeInfo(product=None)


# =============================
class InfoWidget(QtGui.QGroupBox):
    """"""
    def __init__(self, mainEngine, eventEngine, cache, *args):
        super(InfoWidget, self).__init__(*args)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.initUi()

    # -----------------------
    def initUi(self):
        self.accountPage = AccountInfo(self.mainEngine, self.eventEngine, self.cache)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.accountPage)
        self.setLayout(self.layout)

    # ---------------------------------
    def changeInfo(self, product=None):
        if product:
            self.accountPage.changePage(product)
        else:
            pass


# ===================================
class AccountInfo(QtGui.QWidget):
    def __init__(self, mainEngine, eventEngine, cache):
        super(AccountInfo, self).__init__()
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.verifyFlag = self.cache['verifyFlag']
        self.product = ''
        self.subscribeID = -1
        self.dbUtils = self.cache['dbUtils']
        self.user = self.cache['loginName']

        self.retraceThreshold = self.getRetrace5d()
        self.retraceEditFlag = False

        self.initUi()

    # --------------------------------------
    def initUi(self):
        # 产品名对应label
        self.productLabel = QtGui.QLabel()
        font = QtGui.QFont()
        font.setBold(True)
        self.productLabel.setFont(font)

        # 分隔符label
        self.splitLabel1 = QtGui.QLabel('')
        # 股票账户对应label
        self.secLabel = QtGui.QLabel(u'股票账户')
        self.secUpdateLabel = QtGui.QLabel(u'                 最近更新:')
        self.secUpdateEdit = QtGui.QDateEdit()
        self.secUpdateEdit.setReadOnly(True)
        self.secUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
        if self.verifyFlag == VERIFY_FUNDMANAGER or self.verifyFlag == VERIFY_INVESTMANAGER:
            self.retraceLabel = QtGui.QLabel(u'回撤系数设置:')
            self.retraceRatio = QtGui.QDoubleSpinBox()
            self.retraceRatio.setDecimals(2)
            self.retraceRatio.setSingleStep(0.01)
            self.retraceRatio.setMinimum(0)
            self.retraceRatio.setMaximum(1)
            self.retraceRatio.setValue(self.retraceThreshold)
            self.retraceRatio.setEnabled(False)
            self.modButton = QtGui.QPushButton(u'修改')
            self.modButton.clicked.connect(self.saveRetrace)
        # 证券账户信息
        self.secAccountM = AccountMonitor(self.mainEngine, self.eventEngine, self.cache, 'sec')
        # 证券持仓信息
        self.secPositionM = PositionMonitor(self.mainEngine, self.eventEngine, self.cache, 'sec')

        # 分隔符label
        self.splitLabel2 = QtGui.QLabel('                                          ')
        # 期货账户对应label
        self.futuresLabel = QtGui.QLabel(u'期货账户')
        self.futuresUpdateLabel = QtGui.QLabel(u'                 最近更新:')
        self.futuresUpdateEdit = QtGui.QDateEdit()
        self.futuresUpdateEdit.setReadOnly(True)
        self.futuresUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
        # 期货账户信息
        self.futuresAccountM = AccountMonitor(self.mainEngine, self.eventEngine, self.cache, 'futures')
        # 证券持仓信息
        self.futuresPositionM = PositionMonitor(self.mainEngine, self.eventEngine, self.cache, 'futures')

        vLayout = QtGui.QVBoxLayout()
        vLayout.addWidget(self.productLabel)
        # vlabe.addWidget(self.splitLabel1)
        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(self.secLabel)
        hLayout.addWidget(self.secUpdateLabel)
        hLayout.addWidget(self.secUpdateEdit)
        if self.verifyFlag == VERIFY_FUNDMANAGER or self.verifyFlag == VERIFY_INVESTMANAGER:
            hLayout.addWidget(self.splitLabel2)
            hLayout.addWidget(self.retraceLabel)
            hLayout.addWidget(self.retraceRatio)
            hLayout.addWidget(self.modButton)
        hLayout.addStretch()
        vLayout.addLayout(hLayout)
        vLayout.addWidget(self.secAccountM)
        vLayout.addWidget(self.secPositionM)
        # vlabel.addWidget(self.splitLabel2)
        hLayoutF = QtGui.QHBoxLayout()
        hLayoutF.addWidget(self.futuresLabel)
        hLayoutF.addWidget(self.futuresUpdateLabel)
        hLayoutF.addWidget(self.futuresUpdateEdit)
        hLayoutF.addStretch()
        vLayout.addLayout(hLayoutF)
        vLayout.addWidget(self.futuresAccountM)
        vLayout.addWidget(self.futuresPositionM)

        self.setLayout(vLayout)

    # ------------------------------------
    def getRetrace5d(self):
        return self.dbUtils.getRetrace5d(self.user)

    # --------------------------
    def saveRetrace(self):
        if self.retraceEditFlag:
            self.retraceEditFlag = False
            retrace5d = self.retraceRatio.value()
            if self.dbUtils.saveRetrace5d(retrace5d, self.user):
                self.retraceThreshold = retrace5d
                self.secPositionM.retraceThreshold = self.retraceThreshold
                self.retraceRatio.setEnabled(False)
            self.modButton.setText(u'修改')
        else:
            self.retraceEditFlag = True
            self.modButton.setText(u'确认')
            self.retraceRatio.setEnabled(True)

    # -------------------------
    def changePage(self, product):
        if product:
            if product != 'refresh':
                self.productLabel.setText(unicode(product))
                secUpdateDate = self.getUpdateDate(product, 'sec')
                print 'secUpdateDate'
                print secUpdateDate
                futuresUpdateDate = self.getUpdateDate(product, 'futures')
                print 'futuresUpdateDate'
                print futuresUpdateDate
                if secUpdateDate:
                    self.secUpdateEdit.setDate(secUpdateDate)
                else:
                    self.secUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
                if futuresUpdateDate:
                    self.futuresUpdateEdit.setDate(futuresUpdateDate)
                else:
                    self.futuresUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
            else:
                self.productLabel.setText('')
                self.secUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
                self.futuresUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
        else:
            self.productLabel.setText('')
            self.secUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
            self.futuresUpdateEdit.setDate(QtCore.QDate(2010, 1, 1))
        if self.product != product and self.product:
            self.stopSubscribe()
        if product != 'refresh' and product:
            self.product = product
            self.startSubscirbe()

    # -----------------------------------
    def stopSubscribe(self):
        self.secAccountM.stopSubscribe()
        self.secPositionM.stopSubscribe()
        self.futuresAccountM.stopSubscribe()
        self.futuresPositionM.stopSubscribe()

    # ------------------------------------
    def startSubscirbe(self):
        self.secAccountM.subscribe(self.product)
        self.secPositionM.subscribe(self.product)
        self.futuresAccountM.subscribe(self.product)
        self.futuresPositionM.subscribe(self.product)

    # ---------------------------------------
    def getUpdateDate(self, product, objectClass='sec'):
        if objectClass == 'sec':
            return self.dbUtils.getUpdateDate(product, 'sec')
        elif objectClass == 'futures':
            return self.dbUtils.getUpdateDate(product, 'futures')
        else:
            return None


# ==============================================
class AccountMonitor(BasicMonitor):
    def __init__(self, mainEngine, eventEngine, cache, objectClass, product=None):
        super(AccountMonitor, self).__init__()
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.objectClass = objectClass
        self.product = product
        self.dbUtils = self.cache['dbUtils']

        self.cacheData = {}

        d = OrderedDict()
        if self.objectClass == 'sec':
            d['total'] = {'chinese': u'总资产', 'cellType': BasicCell}
            d['balance'] = {'chinese': u'资金余额', 'cellType': BasicCell}
            d['secValue'] = {'chinese': u'股票市值', 'cellType': BasicCell}
        elif self.objectClass == 'futures':
            # d['total'] = {'chinese': u'当前权益', 'cellType': BasicCell}
            d['balance'] = {'chinese': u'资金余额', 'cellType': BasicCell}
            # d['profit'] = {'chinese': u'盈亏', 'cellType': BasicCell}
            # d['profit'] = {'chinese': u'当日持仓盈亏', 'cellType': BasicCell}
            d['margin'] = {'chinese': u'持仓保证金占用', 'cellType': BasicCell}
            d['riskRatio'] = {'chinese': u'风险率', 'cellType': BasicCell}

        self.setHeaderDict(d)

        # 千分位表示字段
        self.finCountHeader = ['total', 'balance', 'secValue', 'margin']

        # 设置过滤器,objectClass并不在表格显示中
        self.addHeaderFilterDict('accountClass', self.objectClass)
        # 设置数据键，product并不在表格显示
        self.setDataKey('product')
        # 设置监控事件类型
        self.setEventType(EVENT_ACCOUNT)

        # 设置字体
        self.setFont(BASIC_FONT)

        # 初始化表格
        self.initTable()

        self.setMaximumHeight(65)

        # 注册监听事件
        self.registerEvent()

    # ---------------------------------------
    def subscribe(self, product):
        self.product = product
        if self.objectClass == 'sec':
            self.mainEngine.onAccount(product, 'Simu')

    # ---------------------------------------
    def stopSubscribe(self):
        # 删除数据
        num = self.rowCount()
        while num:
            num -= 1
            self.removeRow(num)
        if self.objectClass == 'sec':
            self.mainEngine.offAccount('Simu')
        self.dataDict = {}
        return 1

    # -----------------------------------
    def updateData(self, data):
        self.cacheData = {}
        for idata in data:
            inFilterFlag = True
            for i in range(0, len(self.headerFilterDict)):
                if self.headerFilterDict[i] in idata:
                    if idata[self.headerFilterDict[i]] not in self.headerFilter[self.headerFilterDict[i]]:
                        inFilterFlag = False
                        break
                else:
                    inFilterFlag = False
                    break
            if inFilterFlag:
                self.cacheData = idata
                break
        if self.cacheData:
            if self.rowCount():
                for key in self.cacheData:
                    if key in self.dataDict:
                        if key in self.finCountHeader:
                            content = safeUnicode(financialCount(self.cacheData[key]))
                        else:
                            content = safeUnicode(self.cacheData[key])
                        self.dataDict[key].setContent(content)
                if 'accountClass' in self.cacheData:
                    if self.cacheData['accountClass'] == 'futures':
                        if 'margin' in self.cacheData and 'balance' in self.cacheData and 'todayProfit' in self.cacheData:
                            if 'riskRatio' in self.dataDict:
                                try:
                                    a = self.cacheData['balance'] + self.cacheData['todayProfit'] + self.cacheData['margin']
                                    if a < 0.1:
                                        riskRatio = 0.0
                                    else:
                                        riskRatio = self.cacheData['margin'] / a
                                except:
                                    riskRatio = 0.0
                                self.dataDict['riskRatio'].setContent(safeUnicode(riskRatio))
                                color = QtGui.QColor()
                                if riskRatio < 0.8:
                                    color.setRed(0)
                                elif riskRatio < 0.85:
                                    color.setRed(128)
                                    color.setGreen(128)
                                elif riskRatio < 0.9:
                                    color.setRed(128)
                                else:
                                    color.setRed(255)
                                self.dataDict['riskRatio'].setTextColor(color)
            else:
                self.insertRow(0)
                d = {}
                for n, header in enumerate(self.headerList):
                    if header in self.cacheData:
                        if header in self.finCountHeader:
                            content = safeUnicode(financialCount(self.cacheData[header]))
                        else:
                            content = safeUnicode(self.cacheData[header])
                        cellType = self.headerDict[header]['cellType']
                        cell = cellType(content, self.mainEngine)

                        if self.font:
                            cell.setFont(self.font)
                        self.setItem(0, n, cell)
                        d[header] = cell
                    else:
                        content = safeUnicode('')
                        cellType = self.headerDict[header]['cellType']
                        cell = cellType(content, self.mainEngine)
                        if self.font:
                            cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置
                        self.setItem(0, n, cell)
                        d[header] = cell
                self.dataDict = d
        else:
            if self.rowCount():
                self.removeRow(0)
                self.dataDict = {}

# ===========================================
class PositionMonitor(BasicMonitor):
    signalTick = QtCore.pyqtSignal(type(Event()))
    def __init__(self, mainEngine, eventEngine, cache, objectClass, product=None):
        super(PositionMonitor, self).__init__()
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.objectClass = objectClass
        self.product = product
        self.dbUtils = self.cache['dbUtils']
        self.user = self.cache['loginName']
        self.verifyFlag = self.cache['verifyFlag']
        self.productDetails = {}
        #
        self.priceDict = {} # key:objectCode(dataKey), value:list[ {price, volume, direction, costPrice} ]

        self.priceHeader = ['price', 'high5', 'high', 'costPrice', 'direction', 'volume', 'profit']
        self.totalValue = 0

        self.req = FhSubscribeReq()
        self.req.fields = ''
        self.reqId = -1     # -1表示取消所有
        self.updateFlag = False  # 用于控制是否更新，在订阅时为True，在停止订阅时为False

        if self.objectClass == 'sec':
            self.high5 = {}
        else:
            self.margin = 0
            # 获取futures相关信息 key为objectCode
            self.futuresParameter = {}

        self.dataHeader = []

        d = OrderedDict()
        if objectClass == 'sec':
            d['objectCode'] = {'chinese': u'代码', 'cellType': BasicCell}
            d['objectName'] = {'chinese': u'名称', 'cellType': BasicCell}
            d['volume'] = {'chinese': u'持仓', 'cellType': BasicCell}
            # d['availableVolume'] = {'chinese': u'可卖数量', 'cellType': BasicCell}
            d['costPrice'] = {'chinese': u'成本价', 'cellType': BasicCell}
            d['price'] = {'chinese': u'现价', 'cellType': BasicCell}
            d['changeRatio'] = {'chinese': u'涨跌幅', 'cellType': BasicCell}
            d['profit'] = {'chinese': u'盈亏', 'cellType': BasicCell}
            if self.verifyFlag == VERIFY_FUNDMANAGER or self.verifyFlag == VERIFY_ADMIN or self.verifyFlag == VERIFY_INVESTMANAGER:
                d['retrace5d'] = {'chinese': u'五日回撤', 'cellType': BasicCell}
                d['sellSignal'] = {'chinese': u'卖出建议', 'cellType': BasicCell}
            d['remark'] = {'chinese': u'备注', 'cellType': BasicCell}
            # d[''] = {'chinese': u'', 'cellType': BasicCell}
        elif objectClass == 'futures':
            d['objectCode'] = {'chinese': u'合约', 'cellType': BasicCell}
            d['objectName'] = {'chinese': u'名称', 'cellType': BasicCell}
            d['volume'] = {'chinese': u'持仓数量', 'cellType': BasicCell}
            d['direction'] = {'chinese': u'买卖', 'cellType': BasicCell}
            d['costPrice'] = {'chinese': u'成本价', 'cellType': BasicCell}
            d['price'] = {'chinese': u'现价', 'cellType': BasicCell}
            d['changeRatio'] = {'chinese': u'涨跌幅', 'cellType': BasicCell}
            d['profit'] = {'chinese': u'盈亏', 'cellType': BasicCell}
            d['margin'] = {'chinese': u'保证金占用', 'cellType': BasicCell}

        self.setHeaderDict(d)
        # 千分位计数字段
        self.finCountHeader = ['volume', 'profit', 'margin']
        # 缓存数据
        self.cacheData = []
        self.high5 = {}

        # 设置监控事件类型
        self.setEventType(EVENT_POSITION)

        # 设置过滤器
        self.addHeaderFilterDict('objectClass', self.objectClass)

        # 设置从dataGateway提取字段字典
        self.setDataHeader('price')
        self.setDataHeader('changeRatio')
        self.setDataEvent(EVENT_TICK)

        if self.objectClass == 'sec':
            self.retraceThreshold = self.getRetrace5d()
        # 期货需用
        # self.margin = 0
        # self.todayProfit = 0
        self.riskRatio = 0.0

        # 设置数据键
        self.setDataKey('objectCode')

        # 设置字体
        self.setFont(BASIC_FONT)

        # 设置允许排列
        self.setSorting(True)

        # 初始化表格
        self.initTable()

        # 注册监听事件
        self.registerEvent()

    # -------------------------------------------------
    def getProductDetails(self, product=None):
        return self.dbUtils.getProductDetails(product)

    # -------------------------------------
    def getRetrace5d(self):
        return self.dbUtils.getRetrace5d(self.user)

    # ------------------------------
    def setDataHeader(self, header):
        self.dataHeader.append(header)

    # ----------------------------------------
    def setDataEvent(self, eventType):
        self.signalTick.connect(self.updateTick)
        self.eventEngine.register(eventType, self.signalTick.emit)

    # -----------------------------------
    def subscribe(self, product):
        self.updateFlag = True
        self.product = product
        self.productDetails = self.getProductDetails(self.product)
        if self.objectClass == 'sec':
            self.high5 = self.getHigh5()
            self.retraceThreshold = self.getRetrace5d()
            # 持仓信息推送
            self.mainEngine.onPosition(self.product, 'Simu')

    # ----------------------------------------
    def dataSubscribe(self):
        self.req.symbol = self.fitReq()
        # 订阅dataGateway实时信息
        self.reqId = self.mainEngine.subscribe(self.req, self.cache['dataGateway'])

    # ------------------------------
    def getHigh5(self):
        if self.product in self.productDetails:
            objectList = []
            for item in self.productDetails[self.product]:
                if item['objectClass'] == 'sec':
                    objectList.append(item['objectCode'])
            return self.mainEngine.getHigh5(objectList, self.cache['dataGateway'])
        return {}

    # --------------------------------------
    def fitReq(self):
        retStr = ''
        if self.product in self.productDetails:
            productList = self.productDetails[self.product]
            for item in productList:
                code = item['objectCode']
                retStr = retStr + code
                retStr = retStr + ','
        return retStr

    # --------------------------------
    def stopSubscribe(self):
        self.updateFlag = False
        # 删除数据
        num = self.rowCount()
        while num:
            num -= 1
            self.removeRow(num)
        if self.objectClass == 'sec':
            self.mainEngine.offPosition('Simu', self.product)
        self.stopDataSubscribe()
        self.dataDict = {}
        self.priceDict = {}
        self.high5 = {}
        self.reqId = -1
        self.cacheData = []
        return 1

    # -------------------------------------------
    def stopDataSubscribe(self):
        self.mainEngine.stopSubscribe(self.reqId, self.cache['dataGateway'])

    # --------------------------------------------
    def updateTick(self, event):
        """dataGateway更新数据用"""
        if self.updateFlag:
            data = event.dict_['data']
            self.updatePrice(data)

    # --------------------------------------------
    def updatePrice(self, data):
        """更新需要dataGateway实时得到的数据"""
        for i in range(0, len(data)):
            if self.dataKey in data[i]:
                code = unicode(data[i][self.dataKey])
                if code in self.dataDict:
                    dList = self.dataDict[code]
                    for d in dList:
                        for wHeader in self.dataHeader:
                            if wHeader in data[i] and wHeader in self.headerList:
                                content = safeUnicode(data[i][wHeader])
                                # print content
                                cell = d[wHeader]
                                cell.setContent(content)
                            if wHeader == 'price' and self.priceDict[code]:
                                for tem in self.priceDict[code]:
                                    if wHeader in tem and wHeader in data[i]:
                                        tem[wHeader] = data[i][wHeader]
                if code in self.priceDict:
                    if 'high' in data[i]:
                        dList = self.priceDict[code]
                        for d in dList:
                            d['high'] = data[i]['high']
        self.updateValue()

    # ------------------------------------------
    def updateValue(self):
        """
        更新：
        1.五日回撤
        2.盈亏
        3.买卖建议
        4.保证金占用（期货）
        5.更新总
        """
        for code in self.priceDict:
            dList = self.priceDict[code]
            # 为股票的情况
            if self.objectClass == 'sec':
                temTotalValue = 0
                if dList:
                    d = dList[0]
                    if code in self.high5:
                        d['high5'] = max([self.high5[code], d['high']])
                    else:
                        d['high5'] = max([d['high5'], d['high']])
                    d['profit'] = (d['price'] - d['costPrice']) * d['volume']
                    # temTotalValue += d['price'] * d['volume']
                    if code in self.dataDict:
                        dd = self.dataDict[code][0]
                        if 'profit' in dd:
                            content = safeUnicode(financialCount(d['profit']))
                            cell = dd['profit']
                            cell.setContent(content)
                        # 卖出建议
                        if d['high5'] <= 0.0:
                            tem = 0
                        else:
                            tem = 1.0 - d['price']/d['high5']
                        if 'retrace5d' in dd:
                            content = safeUnicode(tem)
                            cell = dd['retrace5d']
                            cell.setContent(content)
                        if tem >= self.retraceThreshold:
                            if 'sellSignal' in dd:
                                content = safeUnicode(SUGGEST_SELL)
                                cell = dd['sellSignal']
                                cell.setContent(content)
                                color = QtGui.QColor()
                                color.setRed(255)
                                cell.setTextColor(color)
                                if 'objectCode' in dd:
                                    cell = dd['objectCode']
                                    color = QtGui.QColor()
                                    color.setRed(255)
                                    # print cell.backgroundColor()
                                    cell.setBackgroundColor(color)
                        else:
                            if 'sellSignal' in dd:
                                content = safeUnicode(SUGGEST_HOLD)
                                cell = dd['sellSignal']
                                cell.setContent(content)
                                color = QtGui.QColor()
                                color.setRed(0)
                                cell.setTextColor(color)
                                if 'objectCode' in dd:
                                    cell = dd['objectCode']
                                    color = QtGui.QColor()
                                    color.setRgb(255,255,255,255)
                                    cell.setBackgroundColor(color)
                # if self.totalValue != temTotalValue:
                #     self.totalValue = temTotalValue
                #     self.mainEngine.saveSecValue(self.product, self.totalValue, 'Simu')
                    # self.dbUtils.saveSecValue(self.product, self.totalValue)
            # 为期货的情况
            else:
                temMargin = 0
                temTodayProfit = 0
                for d in dList:
                    if code in self.futuresParameter:
                        if self.futuresParameter[code]:
                            if d['direction'] == TRADE_BUY:
                                # temTodayProfit += (d['price'] - d['settlePrice']) * (d['volume'] - d['todayBuyVolume']) * self.futuresParameter[code]['weight'] + (d['price'] - d['todayBuyPrice']) * d['todayBuyVolume'] * self.futuresParameter[code]['weight']
                                d['profit'] = (d['price'] - d['costPrice']) * d['volume'] * self.futuresParameter[code]['weight']
                            else:
                                # temTodayProfit += (d['settlePrice'] - d['price']) * (d['volume'] - d['todayBuyVolume']) * self.futuresParameter[code]['weight'] + (d['todayBuyPrice'] - d['price']) * d['todayBuyVolume'] * self.futuresParameter[code]['weight']
                                d['profit'] = (d['price'] - d['costPrice']) * d['volume'] * self.futuresParameter[code]['weight']
                            d['margin'] = d['price'] * d['volume'] * self.futuresParameter[code]['marginRatio'] * self.futuresParameter[code]['weight']
                    if code in self.dataDict:
                        futuresL = self.dataDict[code]
                        for f in futuresL:
                            if str(f['direction'].text()) == safeUnicode(d['direction']):
                                if 'profit' in f:
                                    content = safeUnicode(d['profit'])
                                    cell = f['profit']
                                    cell.setContent(content)
                                if 'margin' in f:
                                    # temMargin += d['margin']
                                    if 'margin' in d:
                                        content = safeUnicode(d['margin'])
                                        cell = f['margin']
                                        cell.setContent(content)
                                    else:
                                        content = safeUnicode(0)
                                        cell = f['margin']
                                        cell.setContent(content)
                # if self.margin != temMargin or self.todayProfit != temTodayProfit:
                #     self.margin = temMargin
                #     self.todayProfit = temTodayProfit
                #     self.mainEngine.saveFuturesTodayInfo(self.product, self.margin, self.todayProfit, 'Simu')
                    # self.dbUtils.saveFuturesTodayInfo(self.product, self.margin, self.todayProfit)

    # -------------------------------------
    def updateData(self, data):
        if self.updateFlag:
            oldCache = self.cacheData
            self.cacheData = self.filterData(data)
            if self.dataKey:
                addList, updateList, deleteList = self.differentSet(self.cacheData, oldCache)
                for item in deleteList:
                    self.deleteRow(item)
                for item in updateList:
                    self.updateRow(item)
                for item in addList:
                    self.addRow(item)
                if addList:
                    if self.req != -1:
                        self.stopDataSubscribe()
                    self.dataSubscribe()

    # ----------------------------------------
    def filterData(self, data):
        """过滤数据"""
        retList = []
        if self.filterFlag:
            for item in data:
                inFilterFlag = True
                for i in range(0, len(self.headerFilterDict)):
                    if self.headerFilterDict[i] in item:
                        if item[self.headerFilterDict[i]] not in self.headerFilter[self.headerFilterDict[i]]:
                            inFilterFlag = False
                if inFilterFlag:
                    retList.append(item)
            return retList
        else:
            return data
    # --------------------------------------
    def differentSet(self, newData, oldData):
        addList = []
        updateList = []
        deleteList = []
        if oldData == []:
            addList = newData
            return addList, updateList, deleteList
        if newData == []:
            deleteList = oldData
            return addList, updateList, deleteList
        # 得到updateList,addList
        for newItem in newData:
            inOldFlag = False
            for oldItem in oldData:
                if self.dataKey in newItem:
                    if newItem[self.dataKey] == oldItem[self.dataKey]:
                        updateList.append(newItem)
                        inOldFlag = True
            if inOldFlag == False:
                addList.append(addList)
        # 得到 deleteList
        for oldItem in oldData:
            inUpdateFlag = False
            for updateItem in updateList:
                if updateItem[self.dataKey] == oldItem[self.dataKey]:
                    inUpdateFlag = True
                    break
            if inUpdateFlag == False:
                deleteList.append(oldItem)
        return addList, updateList, deleteList

    # ------------------------------------
    def addRow(self, item):
        inDict = False
        # item[self.dataKey]
        # print self.dataDict
        if item[self.dataKey] in self.dataDict:
            if self.objectClass == 'sec':
                inDict = True
            elif self.objectClass == 'futures':
                if 'direction' in item:
                    for k in self.dataDict[item[self.dataKey]]:
                        if safeUnicode(item['direction']) == str(k['direction'].text()):
                            inDict = True
                            break
        if inDict:
            self.updateRow(item)
        else:
            # 加入priceDict
            if item[self.dataKey] not in self.priceDict:
                self.priceDict[item[self.dataKey]] = []
                d = {}
                for pHeader in self.priceHeader:
                    if pHeader in item:
                        d[pHeader] = item[pHeader]
                    else:
                        if pHeader == 'direction':
                            d[pHeader] = TRADE_BUY
                        else:
                            d[pHeader] = 0
                self.priceDict[item[self.dataKey]].append(d)
            else:
                dList = self.priceDict[item[self.dataKey]]
                if len(dList) == 1:
                    d = dList[0]
                    if 'direction' in item:
                        if item['direction'] == d['direction']:
                            for pHeader in self.priceHeader:
                                if pHeader in item:
                                    d[pHeader] = item[pHeader]
                                else:
                                    if pHeader not in d:
                                        d[pHeader] = 0
                        else:
                            temd = {}
                            for pHeader in self.priceHeader:
                                if pHeader in item:
                                    temd[pHeader] = item[pHeader]
                                else:
                                    if pHeader not in temd:
                                        temd[pHeader] = 0
                            self.priceDict[item[self.dataKey]].append(temd)
                    else:
                        if d['direction'] == TRADE_BUY:
                            for pHeader in self.priceHeader:
                                if pHeader in item:
                                    d[pHeader] = item[pHeader]
                                else:
                                    if pHeader not in d:
                                        d[pHeader] = 0
                elif len(dList) == 2:
                    for d in dList:
                        if 'direction' in item:
                            if item['direction'] == d['direction']:
                                for pHeader in self.priceHeader:
                                    if pHeader in item:
                                        d[pHeader] = item[pHeader]
                                    else:
                                        if pHeader not in d:
                                            d[pHeader] = 0
                        else:
                            if d['direction'] == TRADE_BUY:
                                for pHeader in self.priceHeader:
                                    if pHeader in item:
                                        d[pHeader] = item[pHeader]
                                    else:
                                        if pHeader not in d:
                                            d[pHeader] = 0

            self.insertRow(0)
            d = {}
            for n, header in enumerate(self.headerList):
                if header in item:
                    if header in self.finCountHeader:
                        content = safeUnicode(financialCount(item[header]))
                    else:
                        content = safeUnicode(item[header])
                    # content = safeUnicode(item[header])
                    cellType = self.headerDict[header]['cellType']
                    cell = cellType(content, self.mainEngine)
                    if self.font:
                        cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置
                    self.setItem(0, n, cell)
                    d[header] = cell
                else:
                    content = safeUnicode('')
                    cellType = self.headerDict[header]['cellType']
                    cell = cellType(content, self.mainEngine)
                    if self.font:
                        cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置
                    self.setItem(0, n, cell)
                    d[header] = cell
            if item[self.dataKey] in self.dataDict:
                self.dataDict[item[self.dataKey]].append(d)
            else:
                self.dataDict[item[self.dataKey]] = []
                if self.objectClass == 'futures':
                    if item[self.dataKey] not in self.futuresParameter:
                        self.futuresParameter[item[self.dataKey]] = self.getFuturesParameter(item[self.dataKey])
                self.dataDict[item[self.dataKey]].append(d)

    # -----------------------------------
    def updateRow(self, item):
        # 先判断数据是否在 dataDict中
        if item[self.dataKey] in self.dataDict:

            # 更新priceDict
            if item[self.dataKey] not in self.priceDict:
                self.priceDict[item[self.dataKey]] = []
                d = {}
                for pHeader in self.priceHeader:
                    if pHeader in item:
                        d[pHeader] = item[pHeader]
                    else:
                        if pHeader == 'direction':
                            d[pHeader] = TRADE_BUY
                        else:
                            d[pHeader] = 0
                self.priceDict[item[self.dataKey]].append(d)
            else:
                dList = self.priceDict[item[self.dataKey]]
                for d in dList:
                    for pHeader in self.priceHeader:
                        if pHeader in item:
                            d[pHeader] = item[pHeader]
                        else:
                            if pHeader not in d:
                                if pHeader == 'direction':
                                    d[pHeader] = TRADE_BUY
                                else:
                                    d[pHeader] = 0

            dList = self.dataDict[item[self.dataKey]]
            inDict = False  # 由于有futures，需判断direction后判断现存Dict中
            if self.objectClass == 'futures':
                if 'direction' in item:
                    for k in dList:
                        if safeUnicode(item['direction']) == str(k['direction'].text()):
                            d = k
                            inDict = True
                            break
            elif self.objectClass == 'sec':
                d = dList[0]
                inDict = True
            if inDict:
                for header in self.headerList:
                    if header in item:
                        if header in self.finCountHeader:
                            content = safeUnicode(financialCount(item[header]))
                        else:
                            content = safeUnicode(item[header])
                        # content = safeUnicode(item[header])
                        cell = d[header]
                        cell.setContent(content)
            else:
                self.addRow(item)
        else:
            self.addRow(item)

    # ----------------------------------
    def deleteRow(self, item):
        inDict = False
        if item[self.dataKey] in self.dataDict:
            if self.objectClass == 'sec':
                inDict = True
                # print self.dataDict[item[self.dataKey]]
                deleteRow = self.row(self.dataDict[item[self.dataKey]][0][self.dataKey])
                self.dataDict.pop(item[self.dataKey])
                # 删除priceDict
                if item[self.dataKey] in self.priceDict:
                    self.priceDict.pop(item[self.dataKey])
            elif self.objectClass == 'futures':
                if 'direction' in item:
                    for k in self.dataDict[item[self.dataKey]]:
                        if safeUnicode(item['direction']) == str(k['direction'].text()):
                            inDict = True
                            deleteRow = self.row(k[self.dataKey])
                            self.dataDict[item[self.dataKey]].remove(k)
                            if self.dataDict[item[self.dataKey]]:
                                self.dataDict.pop(item[self.dataKey])
                            break
                    if item[self.dataKey] in self.priceDict:
                        dList = self.priceDict[item[self.dataKey]]
                        for d in dList:
                            if item['direction'] == d['direction']:
                                dList.remove(d)
                                break
                        if dList == []:
                            self.priceDict.pop(item[self.dataKey])
                            if item[self.dataKey] in self.futuresParameter:
                                self.futuresParameter.pop(item[self.dataKey])
        if inDict:
            self.removeRow(deleteRow)

    # ---------------------------------------
    def getFuturesParameter(self, code):
        return self.dbUtils.getFuturesParameter(code)

# ===========================================



