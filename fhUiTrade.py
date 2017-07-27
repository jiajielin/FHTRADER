# coding=utf-8

"""
Time : 2016/8/3 9:11
Author : Jia Jielin
Company: fhhy.co
File : fhUiTrade.py
Description:

"""

# system module
import winsound
# third party module
# own module
from fhUiBase import *
from fhGateway import *
from fhUtils import *
import datetime


class TradeTab(QtGui.QMainWindow):
    """该类用于显示交易主界面相关信息，根据tabFlag，分为证券，期货界面"""

    # 初始化函数，tabFlag：0,证券 1,期货 2,综合，交易员用到
    def __init__(self, mainEngine, eventEngine, cache, tabFlag, parent=None):
        """
        tabFlag：0，证券交易；1，期货交易；2，任务；3，已撤销；
        """
        super(TradeTab, self).__init__(parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.dbUtils = self.cache['dbUtils']
        self.loginName = self.cache['loginName']
        self.verifyFlag = self.cache['verifyFlag']
        self.tabFlag = tabFlag
        self.productList = self.cache['productList']

        self.initUi()

    # ---------------------
    def initUi(self):
        # 如果为证券或期货区分页面
        if self.tabFlag == 0 or self.tabFlag == 1:
            # self.productMonitorList, dockProduct = self.createDock(ProductMonitorTab, u'产品行情',
            #                                                        QtCore.Qt.RightDockWidgetArea)
            # 任务列表模块
            widgetTaskM, dockTaskM = self.createTaskDock(TaskMonitor, u'任务', QtCore.Qt.RightDockWidgetArea, filterFlag=1)
            # self.setCentralWidget(widgetTaskM)
            if self.tabFlag == 0:
                # 指标画图
                self.widgetTrendD, self.dockTrendD = self.createDrawDock(TrendDraw, u'指标', QtCore.Qt.RightDockWidgetArea)
                # 叠加显示 任务和指标
                self.tabifyDockWidget(dockTaskM, self.dockTrendD)
                dockTaskM.raise_()

            # 创建买卖模块，tabFlag标记证券或期货，sellFlag标记买入或卖出
            widgetTradingBuyW, dockTradingBuyW = self.createTradeDock(TradingWidget, u'买入', QtCore.Qt.LeftDockWidgetArea
                                                                      , self.tabFlag, 0)  # 0为买入
            widgetTradingSellW, dockTradingSellW = self.createTradeDock(TradingWidget, u'卖出', QtCore.Qt.LeftDockWidgetArea
                                                                        , self.tabFlag, 1)  # 1为卖出

            # 日志显示模块
            widgetLogM, dockLogM = self.createLogDock(LogMonitor, u'日志', QtCore.Qt.LeftDockWidgetArea, leftFlag=True)

            # 叠加买卖模块
            self.tabifyDockWidget(dockTradingBuyW, dockTradingSellW)
            # 叠加最先显示设置，目前不需要
            dockTradingBuyW.raise_()
        elif self.tabFlag == 2:
            widgetLogM, dockLogM = self.createLogDock(LogMonitor, u'日志', QtCore.Qt.RightDockWidgetArea, leftFlag=False)
            widgetTaskSecM, dockTaskSecM = self.createTaskDock(TaskMonitor, u'证券', QtCore.Qt.LeftDockWidgetArea, optionFlag=0, buttonFlag=0, filterFlag=2, warningFlag=True)
            widgetTaskFuturesM, dockTasFutureskM = self.createTaskDock(TaskMonitor, u'期货', QtCore.Qt.LeftDockWidgetArea, optionFlag=1, buttonFlag=2, filterFlag=2, warningFlag=True)
        elif self.tabFlag == 3:
            # widgetLogM, dockLogM = self.createLogDock(LogMonitor, u'日志', QtCore.Qt.RightDockWidgetArea)
            widgetTaskSecM, dockTaskSecM = self.createTaskDock(TaskMonitor, u'证券', QtCore.Qt.LeftDockWidgetArea, optionFlag=0, buttonFlag=1, filterFlag=4)
            widgetTaskFuturesM, dockTasFutureskM = self.createTaskDock(TaskMonitor, u'期货', QtCore.Qt.RightDockWidgetArea, optionFlag=1, buttonFlag=1, filterFlag=4)

    # ----------------------------------
    def createLogDock(self, widgetClass, widgetName, widgetArea, leftFlag):
        widget = widgetClass(self.mainEngine, self.eventEngine, leftFlag)
        dock = QtGui.QDockWidget(widgetName)
        dock.setObjectName(widgetName)
        dock.setWidget(widget)
        dock.setFeatures(dock.DockWidgetFloatable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock

    # ----------------------------------------------
    def createDrawDock(self, widgetClass, widgetName, widgetArea):
        widget = widgetClass(self.mainEngine, self.eventEngine, self.cache)
        dock = QtGui.QDockWidget(widgetName)
        dock.setObjectName(widgetName)
        dock.setWidget(widget)
        dock.setFeatures(dock.DockWidgetFloatable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock

    # ----------------------------------------------
    def createTaskDock(self, widgetClass, widgetName, widgetArea, optionFlag=-1, buttonFlag=1, filterFlag=0, warningFlag=False):
        if optionFlag == -1:
            widget = widgetClass(self.mainEngine, self.eventEngine, self.cache, self.tabFlag, buttonFlag, filterFlag, warningFlag)
        else:
            widget = widgetClass(self.mainEngine, self.eventEngine, self.cache, optionFlag, buttonFlag, filterFlag, warningFlag)
        dock = QtGui.QDockWidget(widgetName)
        dock.setObjectName(widgetName)
        dock.setWidget(widget)
        dock.setFeatures(dock.DockWidgetFloatable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock

    # -----------------------------------
    def createTradeDock(self, widgetClass, widgetName, widgetArea, tabFlag, sellFlag):
        widget = widgetClass(self.mainEngine, self.eventEngine, self.cache, tabFlag, sellFlag)
        dock = QtGui.QDockWidget(widgetName)
        dock.setObjectName(widgetName)
        dock.setWidget(widget)
        dock.setFeatures(dock.DockWidgetFloatable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock

    # ------------------------------------------
    def selectProduct(self):    # 已删除
        for i in range(0, self.widgetList.productNum):
            if self.widgetList.productCbs[i].isChecked():
                if self.productList[i] not in self.selectedProducts:
                    self.selectedProducts.append(self.productList[i])
                    self.productMonitorList.addProductTab(self.productList[i])
            else:
                if self.productList[i] in self.selectedProducts:
                    self.selectedProducts.remove(self.productList[i])
                    self.productMonitorList.deleteProductTab(self.productList[i])


# =============================
class LogMonitor(BasicMonitor):
    """日志监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, leftFlag=True, parent=None):
        """Constructor"""
        super(LogMonitor, self).__init__(mainEngine, eventEngine, parent)

        d = OrderedDict()
        d['logTime'] = {'chinese': u'时间', 'cellType': BasicCell}
        d['logContent'] = {'chinese': u'内容', 'cellType': BasicCell}
        d['gatewayName'] = {'chinese': u'接口', 'cellType': BasicCell}
        self.setHeaderDict(d)

        self.setEventType(EVENT_LOG)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.registerEvent()
        if leftFlag:
            self.setMaximumWidth(TRADE_LEFT_MAX)
            self.setMinimumWidth(TRADE_LEFT_MIN)
        else:
            self.setMaximumWidth(LOG_RIGHT_MAX)
            self.setMinimumWidth(LOG_RIGHT_MIN)


class TaskMonitor(BasicTreeMonitor):
    """任务监控"""

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine, cache, tabFlag, buttonFlag=1, filterFlag=0, warningFlag=False, parent=None):
        """
        tabFlag：证券期货海选标志，0，证券；1，期货
        buttonFlag：按键标志，0，无按键；1，一个按键（刷新）；2，两个按键（状态切换、刷新）
        filterFlag：状态筛选标志，0，全选（‘已成交’，‘未成交’，‘已撤销’）；1，只选‘已成交、未成交’；2，只选‘未成交’；3，只选‘已成交’；4，只选‘已撤销’
        cache：cache中verifyFlag用于区分权限，若fundManager：左键目录与filterFlag
        """
        super(TaskMonitor, self).__init__(buttonFlag, mainEngine, eventEngine, warningFlag, parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.tabFlag = tabFlag
        self.verifyFlag = self.cache['verifyFlag']
        self.isDefaultSetting = self.cache['isDefaultSetting']
        self.warningFlag = warningFlag

        d = OrderedDict()
        if self.tabFlag:
            d['taskNo'] = {'chinese': u'序号', 'editable': False}
            d['state'] = {'chinese': u'状态', 'editable': False}  # 未读、已读、已完成、已撤销、已撤销且部分完成
            d['product'] = {'chinese': u'产品', 'editable': True}
            d['objectCode'] = {'chinese': u'代码', 'editable': False}
            d['objectName'] = {'chinese': u'名称', 'editable': False}
            d['buySell'] = {'chinese': u'买卖', 'editable': False}
            d['direction'] = {'chinese': u'开平', 'editable': False}     # 期货独有
            d['taskPrice'] = {'chinese': u'价格', 'editable': False}
            d['taskVolume'] = {'chinese': u'数量', 'editable': False}
            # d['price'] = {'chinese': u'当前价格', 'editable': False}
            d['fundManager'] = {'chinese': u'基金经理', 'editable': False}
            d['trader'] = {'chinese': u'交易员', 'editable': False}
            d['transPrice'] = {'chinese': u'交易价格', 'editable': False}
            d['transVolume'] = {'chinese': u'交易数量', 'editable': False}
            d['taskTime'] = {'chinese': u'下发时间', 'editable': False}
            d['finishTime'] = {'chinese': u'完成时间', 'editable': False}
            # d['remark'] = {'chinese': u'备注', 'editable': True}
        else:
            d['taskNo'] = {'chinese': u'序号', 'editable': False}
            d['state'] = {'chinese': u'状态', 'editable': True}  # 未读、已读、已完成、已撤销、已撤销且部分完成
            d['product'] = {'chinese': u'产品', 'editable': False}
            d['objectCode'] = {'chinese': u'代码', 'editable': False}
            d['objectName'] = {'chinese': u'名称', 'editable': False}
            d['buySell'] = {'chinese': u'买卖', 'editable': False}
            d['taskPrice'] = {'chinese': u'价格', 'editable': False}
            d['taskVolume'] = {'chinese': u'数量', 'editable': False}
            # d['price'] = {'chinese': u'当前价格', 'editable': False}
            d['fundManager'] = {'chinese': u'基金经理', 'editable': False}
            d['trader'] = {'chinese': u'交易员', 'editable': False}
            d['transPrice'] = {'chinese': u'交易价格', 'editable': False}
            d['transVolume'] = {'chinese': u'交易数量', 'editable': False}
            d['taskTime'] = {'chinese': u'下发时间', 'editable': False}
            d['finishTime'] = {'chinese': u'完成时间', 'editable': False}
            # d['remark'] = {'chinese': u'备注', 'editable': True}
        mainHeader = 'taskNo'
        subHeader = 'subNo'
        self.setHeaderDict(d, mainHeader, subHeader)

        # 设置千分位显示字段
        if self.tabFlag:
            self.setFinCountHeader('taskVolume')
            self.setFinCountHeader('transVolume')
        else:
            self.setFinCountHeader('taskVolume', -1)
            self.setFinCountHeader('transVolume', -1)

        self.setEventType(EVENT_TASK)
        self.setFont(BASIC_FONT)
        self.initTable()
        self.setSorting(True)

        # 筛选字段设置
        # 期货现货筛选
        if self.tabFlag:
            self.setHeaderFilterDict('objectClass', ['futures'])
        else:
            self.setHeaderFilterDict('objectClass', ['sec'])
        # 状态筛选
        if filterFlag == 0:
            # 筛选项为全状态，目前暂无该要求
            self.setHeaderFilterDict('state', [STATUS_NOTTRADED, STATUS_ALLTRADED, STATUS_CANCELLED])
        elif filterFlag == 1:
            # 筛选项为未完成、已完成，基金经理需看
            # self.bgColorFlag = True
            # if self.isDefaultSetting == False:
            #     self.addBgColor.setGreen(64)
            #     self.defaultBgColor.setRgb(0, 0, 0)
            self.setHeaderFilterDict('state', [STATUS_NOTTRADED, STATUS_ALLTRADED])
        elif filterFlag == 2:
            # 筛选项为未完成， 供trader看
            self.setHeaderFilterDict('state', [STATUS_NOTTRADED])
        elif filterFlag == 3:
            # 筛选项为已完成，目前暂无该要求
            self.setHeaderFilterDict('state', [STATUS_ALLTRADED])
        elif filterFlag == 4:
            # 筛选项为已撤销，供trader看
            self.bgColorFlag = True
            if self.isDefaultSetting == False:
                self.addBgColor.setGreen(64)
                self.defaultBgColor.setRgb(0, 0, 0)
            self.setHeaderFilterDict('state', [STATUS_CANCELLED])

        self.registerEvent()
        self.gatewayName = 'Simu'
        self.haltFlag = False   # 表示当前离线状态，False表示离线，True在线
        if self.verifyFlag == VERIFY_ADMIN or self.verifyFlag == VERIFY_FUNDMANAGER or self.verifyFlag == VERIFY_INVESTMANAGER:
            menuHandlerDict = {}
            menuNameList = [u'撤销任务']
            menuHandlerDict[u'撤销任务'] = self.cancelTask
            # menuHandlerDict[u'撤销取消状态'] = self.revokeCancel
            # menuHandlerDict[u'添加备注'] = self.addRemark
            self.setMenuItems(menuNameList, menuHandlerDict)
        elif self.verifyFlag == VERIFY_TRADER:
            menuHandlerDict = {}
            menuNameList = [u'完成任务']
            menuHandlerDict[u'完成任务'] = self.traded
            # menuHandlerDict[u'部分完成'] = self.partTraded
            # menuHandlerDict[u'未下单'] = self.notTraded
            # menuHandlerDict[u'添加备注'] = self.addRemark
            self.setMenuItems(menuNameList, menuHandlerDict)

    # --------------------------------
    def getAllTask(self):
        self.mainEngine.getAllTask(self.gatewayName)

    # ---------------------------------
    def halt(self):
        if self.haltFlag:
            self.haltButton.setText(u'挂起')
            self.haltFlag = False
            self.mainEngine.halt('off', self.gatewayName)
        else:
            self.haltButton.setText(u'在线')
            self.haltFlag = True
            self.mainEngine.halt('on', self.gatewayName)

    # ----------------------------------
    def refresh(self):
        super(TaskMonitor, self).refresh()
        self.getAllTask()

    # ---------------------------------
    def cancelTask(self):
        curItem = self.tree.currentItem()
        if curItem:
            data = []
            if curItem.childCount():
                taskNo = str(curItem.text(0))
                subNo = ''
            else:
                subNo = str(curItem.text(0))
                taskNo = str(curItem.parent().text(0))
            temData = {}
            temData['taskNo'] = taskNo
            temData['subNo'] = subNo
            data.append(temData)
            self.modifyState(OPTION_CANCEL, data)

    # ---------------------------------
    def addRemark(self):
        # curItem = self.tree.currentItem()
        self.editor = QtGui.QDialog()
        self.editor.line = QtGui.QLineEdit()
        curItem = self.tree.currentItem()
        remark = curItem.text(self.headerDict.keys().index('remark'))
        showRemark = ''
        if remark:
            remarkSplit = remark.split('\n')
            for userRemark in remarkSplit:
                temSplit = userRemark.split(':')
                if temSplit[0] == self.cache['loginName']:
                    if temSplit[1]:
                        showRemark = temSplit[1]
                    break
        self.editor.line.setText(showRemark)
        self.editor.okButton = QtGui.QPushButton(u'确定', self.editor)
        self.editor.okButton.clicked.connect(self.getRemark)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.editor.line)
        layout.addWidget(self.editor.okButton)
        layout.addStretch()
        self.editor.setLayout(layout)
        self.editor.setModal(True)
        self.editor.show()

    # --------------------------------------------
    def getRemark(self):
        text = str(self.editor.line.text())
        curItem = self.tree.currentItem()
        if curItem:
            if curItem.childCount():
                taskNo = curItem.text(0)
                subNo = ''
            else:
                subNo = curItem.text(0)
                taskNo = curItem.parent().text(0)

            self.editor.close()
            if text:
                self.mainEngine.addRemark(text, taskNo, subNo,  self.gatewayName)

    # ----------------------------------
    def traded(self):
        curItem = self.tree.currentItem()
        if curItem:
            self.priceEditor = QtGui.QDialog()
            label = QtGui.QLabel(u'价格')
            self.priceEditor.line = QtGui.QDoubleSpinBox()
            self.priceEditor.line.setMaximum(10000000)
            self.priceEditor.line.setSingleStep(0.01)
            showPrice = 0
            taskPrice = curItem.text(self.headerDict.keys().index('taskPrice'))
            if taskPrice:
                try:
                    showPrice = float(taskPrice)
                except:
                    showPrice = 0
            self.priceEditor.line.setValue(showPrice)
            self.priceEditor.okButton = QtGui.QPushButton(u'确定')
            self.priceEditor.okButton.clicked.connect(self.getTraded)
            # self.priceEditor.okButton.clicked.connect(self.priceEditor.close)
            layout = QtGui.QHBoxLayout()
            layout.addWidget(label)
            layout.addWidget(self.priceEditor.line)
            layout.addWidget(self.priceEditor.okButton)
            layout.addStretch()
            self.priceEditor.setLayout(layout)
            self.priceEditor.setModal(True)
            self.priceEditor.show()

    # --------------------------
    def getTraded(self):
        data = []   # 记录要素，用于交易
        transPrice = self.priceEditor.line.value()
        curItem = self.tree.currentItem()
        if curItem:
            if curItem.childCount():
                taskNo = str(curItem.text(0))
                for i in range(0, curItem.childCount()):
                    item = curItem.child(i)
                    subNo = str(item.text(0))
                    temData = {}
                    temData['taskNo'] = taskNo
                    temData['subNo'] = subNo
                    temData['trasnPrice'] = transPrice
                    data.append(temData)
            else:
                subNo = str(curItem.text(0))
                taskNo = str(curItem.parent().text(0))
                temData = {}
                temData['taskNo'] = taskNo
                temData['subNo'] = subNo
                temData['transPrice'] = transPrice
                data.append(temData)
            self.modifyState(OPTION_TRADED, data)
            self.priceEditor.close()

    # -----------------------------------
    # def partTraded(self):
    #     curItem = self.tree.currentItem()
    #     if curItem:
    #         if curItem.childCount:
    #             self.transEditor = QtGui.QDialog()
    #             labelPrice = QtGui.QLabel(u'交易价格：')
    #             labelVolume = QtGui.QLabel(u'交易数量：')
    #             self.transEditor.linePrice = QtGui.QDoubleSpinBox()
    #             self.transEditor.lineVolume = QtGui.QSpinBox()
    #             self.transEditor.lineVolume.setMaximum(1000000000)
    #             showPrice = 0
    #             showVolume = 0
    #             taskPrice = curItem.text(self.headerDict.keys().index('taskPrice'))
    #             taskVolume = curItem.text(self.headerDict.keys().index('taskVolume'))
    #             if taskPrice:
    #                 try:
    #                     showPrice = float(taskPrice)
    #                 except:
    #                     pass
    #             if taskVolume:
    #                 try:
    #                     showVolume = int(taskVolume)
    #                 except:
    #                     pass
    #             self.transEditor.linePrice.setValue(showPrice)
    #             self.transEditor.lineVolume.setValue(showVolume)
    #             self.transEditor.okButton = QtGui.QPushButton(u'确定')
    #             self.transEditor.okButton.clicked.connect(self.getPartTraded)
    #             layout = QtGui.QGridLayout()
    #             layout.addWidget(labelPrice, 0, 0)
    #             layout.addWidget(labelVolume, 1, 0)
    #             layout.addWidget(self.transEditor.linePrice, 0, 1)
    #             layout.addWidget(self.transEditor.lineVolume, 1, 1)
    #             layout.addWidget(self.transEditor.okButton, 2, 1)
    #             self.transEditor.setLayout(layout)
    #             self.transEditor.setModal(True)
    #             self.transEditor.show()

    # -----------------------------------
    # def getPartTraded(self):
    #     data = []   # 记录要素，用于交易
    #     transPrice = self.transEditor.linePrice.value()
    #     transVolume = self.transEditor.lineVolume.value()
    #     curItem = self.tree.currentItem()
    #     if curItem:
    #         if curItem.childCount():
    #             pass
    #         else:
    #             subNo = str(curItem.text(0))
    #             taskNo = str(curItem.parent().text(0))
    #             temData = {}
    #             temData['taskNo'] = taskNo
    #             temData['subNo'] = subNo
    #             temData['transPrice'] = transPrice
    #             temData['transVolume'] = transVolume
    #             data.append(temData)
    #         self.modifyState(OPTION_PARTTRADED, data)

    # -----------------------------------
    # def notTraded(self):
    #     curItem = self.tree.currentItem()
    #     if curItem:
    #         if curItem.childCount():
    #             taskNo = str(curItem.text(0))
    #             subNo = ''
    #         else:
    #             subNo = str(curItem.text(0))
    #             taskNo = str(curItem.parent().text(0))
    #         data = {}
    #         data['taskNo'] = taskNo
    #         data['subNo'] = subNo
    #         self.modifyState(OPTION_NOTTRADED, data)

    # -----------------------------------
    def modifyState(self, option, data):
        self.mainEngine.sendOption(option, data, self.gatewayName)


# ===============================================
class TradingWidget(QtGui.QFrame):
    """交易部分"""

    buysell = [u'买入', u'卖出']
    priceType = OrderedDict()
    priceType['0'] = u'限价'
    priceType['1'] = u'市价'
    direction = OrderedDict()
    direction['0'] = u'开仓'
    direction['1'] = u'平仓'
    dictRatio, ratioList = loadProductRatio()  # 目前该函数未连接数据库，返回的是自设值，需判断是否需要连库

    # gatewayList = ['']

    # ------------------------------------
    def __init__(self, mainEngine, eventEngine, cache, tabFlag, sellFlag, parent=None):
        super(TradingWidget, self).__init__()
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.loginName = self.cache['loginName']
        self.tabFlag = tabFlag
        self.sellFlag = sellFlag
        self.selectedProducts = []
        self.selectedRatio = 0.0
        self.user = self.cache['loginName']
        self.productPerserving = self.cache['productPerserving']
        self.dbUtils = self.cache['dbUtils']
        self.verifyFlag = self.cache['verifyFlag']
        self.productRatioList = self.dbUtils.getProductsRatioByManager(self.user)
        self.productList = []
        # 为期货的筛选
        if self.tabFlag == 1:
            for item in self.productRatioList:
                if item['futuresRatio'] > 0.0:
                    self.productList.append(item['product'])
        # 为股票的筛选
        elif self.tabFlag == 0:
            self.optionalControlFlag = self.dbUtils.getOptionalControlFlag()
            for item in self.productRatioList:
                if item['secRatio'] > 0.0:
                    self.productList.append(item['product'])

        self.symbol = ''

        # # 添加交易接口
        # self.gatewayList.extend(mainEngine.gatewayDict.keys())
        # 交易接口确定，暂时未用到

        self.initUi()

    # --------------------------------
    def initUi(self):

        self.setWindowTitle(u'交易')
        self.setMaximumWidth(TRADE_LEFT_MAX)
        self.setMinimumWidth(TRADE_LEFT_MIN)
        self.setMaximumHeight(280+20*len(self.productList))

        self.setFrameShape(self.Box)  # 设置边框
        self.setLineWidth(1)

        if self.tabFlag == 0:
            self.initUiSec()
        elif self.tabFlag == 1:
            self.initUiFutures()

    # ------------------
    def initUiSec(self):
        # 左边字段显示
        labelProduct = QtGui.QLabel(u'产品')
        labelID = QtGui.QLabel(u'代码')
        labelName = QtGui.QLabel(u'名称')
        labelRatio = QtGui.QLabel(u'交易比例')
        labelPrice = QtGui.QLabel(u'价格')
        labelVolume = QtGui.QLabel(u'数量')
        # labelPriceType = QtGui.QLabel(u'价格类型')

        # 右边控件，产品选择
        self.productNum = len(self.productList)
        if self.productNum == 0:
            labelNull = QtGui.QLabel(u'无产品信息')
        else:
            self.productCbs = [QtGui.QCheckBox(unicode(self.productList[i]), self) for i in range(0, self.productNum)]
            gridProduct = QtGui.QGridLayout()
            for i in range(0, self.productNum):
                self.productCbs[i].setFocusPolicy(QtCore.Qt.NoFocus)
                gridProduct.addWidget(self.productCbs[i], i / 2, i % 2)
                self.connect(self.productCbs[i], QtCore.SIGNAL('stateChanged(int)'), self.selectProduct)
            self.productAll = QtGui.QCheckBox(u'全选', self)
            gridProduct.addWidget(self.productAll, self.productNum / 2, self.productNum % 2)
            self.connect(self.productAll, QtCore.SIGNAL('stateChanged(int)'), self.selectAll)

        # 获取股票secId，secName，secLetter
        secList = self.getSecList([])

        # 代码输入
        self.lineID = QtGui.QLineEdit()
        secIdList = QtCore.QStringList()  # 设置股票代码匹配集

        # lineID关联下拉列表
        for i in range(0, len(secList)):
            secIdList << secList[i][0] + ' ' + unicode(secList[i][1])
        idCompleter = QtGui.QCompleter(secIdList)
        self.lineID.setCompleter(idCompleter)

        # # demo
        # secIdList = QtCore.QStringList()
        # for i in range(0, 2):
        #     secIdList << secList[i][0] + ' ' + unicode(secList[i][1])
        # idCompleter = QtGui.QCompleter(secIdList)
        # self.lineID.setCompleter(idCompleter)

        # 股票名称
        self.lineName = QtGui.QLineEdit()
        secNameList = QtCore.QStringList()  # 设置股票首字母匹配集

        # lineName关联下拉列表
        for i in range(0, len(secList)):
            secNameList << secList[i][2] + ' ' + unicode(secList[i][1])
        nameCompleter = QtGui.QCompleter(secNameList)
        self.lineName.setCompleter(nameCompleter)

        # 交易比例
        self.ratioRbs = [QtGui.QRadioButton(self.dictRatio[i]) for i in range(0, len(self.dictRatio))]

        gridRatio = QtGui.QGridLayout()
        for i in range(0, len(self.dictRatio)):
            gridRatio.addWidget(self.ratioRbs[i], i / 3, i % 3)
            self.ratioRbs[i].clicked.connect(self.selectRatio)
        self.ratioRbs[len(self.ratioRbs)-1].setHidden(True)

        # 价格
        self.sprinPrice = QtGui.QDoubleSpinBox()
        self.sprinPrice.setDecimals(3)  # 设置小数点位数
        self.sprinPrice.setSingleStep(0.01)  # 设置步长
        self.sprinPrice.setMinimum(0)  # 设置最小值，实际输入时需修改为90%
        self.sprinPrice.setMaximum(10000)  # 设置最大值，实际输入时需修改为110%

        # 数量
        self.spinVolume = QtGui.QSpinBox()
        self.spinVolume.setMinimum(0)  # 设置最小值

        self.spinVolume.setSingleStep(100)  # 设置步长，为100股
        self.spinVolume.setMaximum(100000000)  # 设置最大值

        # 价格类型
        # self.comboPriceType = QtGui.QComboBox()
        # self.comboPriceType.addItems(self.priceType.values())

        grid = QtGui.QGridLayout()
        grid.addWidget(labelProduct, 0, 0)
        grid.addWidget(labelID, 1, 0)
        grid.addWidget(labelName, 2, 0)
        grid.addWidget(labelRatio, 4, 0)
        grid.addWidget(labelPrice, 3, 0)
        grid.addWidget(labelVolume, 5, 0)
        # grid.addWidget(labelPriceType, 6, 0)
        if self.productNum == 0:
            grid.addWidget(labelNull, 0, 1)
        else:
            grid.addLayout(gridProduct, 0, 1)
        grid.addWidget(self.lineID, 1, 1)
        grid.addWidget(self.lineName, 2, 1)
        grid.addLayout(gridRatio, 4, 1)
        grid.addWidget(self.sprinPrice, 3, 1)
        grid.addWidget(self.spinVolume, 5, 1)
        # grid.addWidget(self.comboPriceType, 6, 1)

        # 下发按钮
        buttonSendOrder = QtGui.QPushButton(self.buysell[self.sellFlag])

        # 整合布局

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(buttonSendOrder)
        vbox.addStretch()

        self.setLayout(vbox)

        # 关联更新
        self.lineID.editingFinished.connect(self.getSecIdName)  # lineID结束编辑事件关联
        self.lineName.editingFinished.connect(self.getSecNameId)  # lineName结束编辑事件关联
        buttonSendOrder.clicked.connect(self.sendOrder)  # 下单按钮点击事件关联
        self.spinVolume.valueChanged.connect(self.stdValueState)

    # ---------------------------------------------
    def initUiFutures(self):
        # 左边部分
        labelProduct = QtGui.QLabel(u'产品')
        labelID = QtGui.QLabel(u'代码')
        labelName = QtGui.QLabel(u'名称')
        labelDirection = QtGui.QLabel(u'开平')

        labelPrice = QtGui.QLabel(u'价格')
        labelVolume = QtGui.QLabel(u'数量')
        # labelPriceType = QtGui.QLabel(u'价格类型')

        self.productNum = len(self.productList)
        if self.productNum == 0:
            labelNull = QtGui.QLabel(u'无产品信息')
        else:
            self.productCbs = [QtGui.QCheckBox(unicode(self.productList[i]), self) for i in range(0, self.productNum)]
            gridProduct = QtGui.QGridLayout()
            for i in range(0, self.productNum):
                self.productCbs[i].setFocusPolicy(QtCore.Qt.NoFocus)
                gridProduct.addWidget(self.productCbs[i], i / 2, i % 2)
                self.connect(self.productCbs[i], QtCore.SIGNAL('stateChanged(int)'), self.selectProduct)
            self.productAll = QtGui.QCheckBox(u'全选', self)
            gridProduct.addWidget(self.productAll, self.productNum / 2, self.productNum % 2)
            self.connect(self.productAll, QtCore.SIGNAL('stateChanged(int)'), self.selectAll)

        # 代码
        self.lineID = QtGui.QLineEdit()


         # 获取股票secId，secName，secLetter
        futuresList = self.getFuturesList([])

        # 代码输入
        self.lineID = QtGui.QLineEdit()
        futuresCodeList = QtCore.QStringList()  # 设置股票代码匹配集

        # lineID关联下拉列表
        for i in range(0, len(futuresList)):
            futuresCodeList << futuresList[i][0] + ' ' + unicode(futuresList[i][1])
        idCompleter = QtGui.QCompleter(futuresCodeList)
        self.lineID.setCompleter(idCompleter)


        # 名称
        self.lineName = QtGui.QLineEdit()
        futuresNameList = QtCore.QStringList()  # 设置股票首字母匹配集
        # lineName关联下拉列表
        for i in range(0, len(futuresList)):
            futuresNameList << futuresList[i][2] + ' ' + unicode(futuresList[i][1])
        nameCompleter = QtGui.QCompleter(futuresNameList)
        self.lineName.setCompleter(nameCompleter)


        # 委托类型
        self.comboDirection = QtGui.QComboBox()
        self.comboDirection.addItems(self.direction.values())

        # 价格
        self.sprinPrice = QtGui.QDoubleSpinBox()
        self.sprinPrice.setDecimals(4)  # 设置小数点位数
        self.sprinPrice.setMinimum(0)  # 设置最小值，实际输入时需修改为90%
        self.sprinPrice.setMaximum(10000)  # 设置最大值，实际输入时需修改为110%
        # 数量
        self.spinVolume = QtGui.QSpinBox()
        self.spinVolume.setMinimum(0)  # 设置最小值，实际输入时需修改为90%
        self.spinVolume.setMaximum(1000000)  # 设置最大值，实际输入时需修改为110%
        # 价格类型
        # self.comboPriceType = QtGui.QComboBox()
        # self.comboPriceType.addItems(self.priceType.values())

        grid = QtGui.QGridLayout()
        grid.addWidget(labelProduct, 0, 0)
        grid.addWidget(labelID, 1, 0)
        grid.addWidget(labelName, 2, 0)
        grid.addWidget(labelDirection, 3, 0)
        grid.addWidget(labelPrice, 4, 0)
        grid.addWidget(labelVolume, 5, 0)
        # grid.addWidget(labelPriceType, 6, 0)
        if self.productNum == 0:
            grid.addWidget(labelNull, 0, 1)
        else:
            grid.addLayout(gridProduct, 0, 1)
        grid.addWidget(self.lineID, 1, 1)
        grid.addWidget(self.lineName, 2, 1)
        grid.addWidget(self.comboDirection, 3, 1)
        grid.addWidget(self.sprinPrice, 4, 1)
        grid.addWidget(self.spinVolume, 5, 1)
        # grid.addWidget(self.comboPriceType, 6, 1)

        # 买卖按钮
        self.buttonSendOrder = QtGui.QPushButton(self.buysell[self.sellFlag] + self.comboDirection.currentText())

        self.comboDirection.currentIndexChanged.connect(self.buttonTextChange)

        # 整合布局

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(self.buttonSendOrder)
        vbox.addStretch()

        self.setLayout(vbox)

        self.lineID.editingFinished.connect(self.getFuturesCodeName)  # lineID结束编辑事件关联
        self.lineName.editingFinished.connect(self.getFuturesNameCode)  # lineName结束编辑事件关联
        self.buttonSendOrder.clicked.connect(self.sendOrder)

    # -------------------------------------------
    def buttonTextChange(self):
        self.buttonSendOrder.setText(self.buysell[self.sellFlag] + self.comboDirection.currentText())

    # ---------------------------------------------
    def selectAll(self):
        if self.productAll.isChecked():
            for i in range(0, self.productNum):
                self.productCbs[i].setChecked(True)

        else:
            for i in range(0, self.productNum):
                self.productCbs[i].setChecked(False)

    # ------------------------------------------
    def stdValueState(self):
        if self.spinVolume.value():
            self.ratioRbs[len(self.ratioRbs)-1].setChecked(True)
            self.selectedRatio = 0.0

    # --------------------------------------------
    def selectProduct(self):
        for i in range(0, self.productNum):
            if self.productCbs[i].isChecked():
                if self.productList[i] not in self.selectedProducts:
                    self.selectedProducts.append(self.productList[i])
            else:
                if self.productList[i] in self.selectedProducts:
                    self.selectedProducts.remove(self.productList[i])

    # -------------------------
    def selectRatio(self):
        for i in range(0, len(self.ratioList)):
            if self.ratioRbs[i].isChecked():
                self.selectedRatio = self.ratioList[i]
                self.spinVolume.setValue(0)

    # -----------------------------------------------
    def getSecList(self, segment):
        return self.dbUtils.getSecList(segment)

    # -----------------------------------------------
    def getFuturesList(self, segment):
        return self.dbUtils.getFuturesList(segment)

    # --------------------------------------------------
    def getSecIdName(self):
        if len(str(self.lineID.text())) >= 6:
            secIdTemp = str(self.lineID.text())[0:6]
            ret = self.dbUtils.getSecIdName(secIdTemp)
            if len(ret):
                # firstLetter = str(self.lineID.text())[0]
                # if firstLetter == '0' or firstLetter == '3' or firstLetter == '6':
                #     self.sprinPrice.setDecimals(2)
                #     self.sprinPrice.setSingleStep(0.01)
                # else:
                #     self.sprinPrice.setDecimals(3)
                #     self.sprinPrice.setSingleStep(0.001)
                self.lineID.setText(ret[0])
                self.lineName.setText(unicode(ret[1]))

                self.updatePrice(1)
        else:
            self.updatePrice()

    # -----------------------------------------------------
    def getFuturesCodeName(self):
        code = str(self.lineID.text())
        if len(code) > 2:
            codeSplit = code.split(' ')
            futuresCodeTemp = codeSplit[0]
            ret = self.dbUtils.getFuturesCodeName(futuresCodeTemp)
            if len(ret):
                self.lineID.setText(ret[0])
                self.lineName.setText(unicode(ret[1]))
                self.updateFuturesPrice()
        else:
            self.updateFuturesPrice()

    # -----------------------------------------------------
    def getSecNameId(self):
        if len(str(self.lineName.text())) >= 4:
            secNameTemp = str(self.lineName.text()).split(' ')[0]
            ret = self.dbUtils.getSecIdName(secNameTemp, option=1)
            if len(ret):
                self.lineID.setText(ret[0])
                self.lineName.setText(unicode(ret[1]))
                self.updatePrice()
        else:
            self.updatePrice()

    # --------------------------------------------------
    def getFuturesNameCode(self):
        if len(str(self.lineName.text())) >= 4:
            futuresNameTemp = str(self.lineName.text()).split(' ')
            ret = self.dbUtils.getFuturesCodeName(futuresNameTemp, option=1)
            if len(ret):
                self.lineID.setText(ret[0])
                self.lineName.setText(unicode(ret[1]))
                self.updateFuturesPrice()
        else:
            self.updateFuturesPrice()

    # --------------------------------------------------
    def updatePrice(self, flag=0):
        if self.dbUtils.isSecId(str(self.lineID.text())):
            secId = str(self.lineID.text())
            firstLetter = secId[0]
            if firstLetter == '0' or firstLetter == '3' or firstLetter == '6':
                self.sprinPrice.setDecimals(2)
                self.sprinPrice.setSingleStep(0.01)
            else:
                self.sprinPrice.setDecimals(3)
                self.sprinPrice.setSingleStep(0.001)
            gatewayName = self.cache['dataGateway']
            self.sprinPrice.setValue(0)
            req = FhSubscribeReq()
            req.symbol = secId
            req.exchange = ''
            data = self.mainEngine.getPrice(req, gatewayName)
            if flag:
                self.updateTrendDraw(secId)
            self.sprinPrice.setValue(data)

        else:
            self.sprinPrice.setValue(0)

    # -------------------------------------------------
    def updateTrendDraw(self, secId):
        # print 'updateTrendDraw:', secId
        self.parent().parent().widgetTrendD.drawing(secId)

    # -----------------------------------------------------
    def updateFuturesPrice(self):
        if self.dbUtils.isFuturesCode(str(self.lineID.text())):
            futuresCode = str(self.lineID.text())
            gatewayName = self.cache['dataGateway']
            self.sprinPrice.setValue(0)
            req = FhSubscribeReq()
            req.symbol = futuresCode
            req.exchange = ''
            data = self.mainEngine.getPrice(req, gatewayName)
            self.sprinPrice.setValue(data)
        else:
            self.sprinPrice.setValue(0)

    # -------------------------------------------------
    def sendOrder(self):
        """发单"""
        if self.productNum == 0:
            QtGui.QMessageBox.warning(self, u'信息提示', u'无产品信息，无法下单')
            return
        checkFlag = self.selfCheck()
        if checkFlag == False:
            QtGui.QMessageBox.warning(self, u'信息提示', u'输入要素不全,请重新输入')
            return
        info = ''
        objectCode = str(self.lineID.text())
        if self.tabFlag:    # 期货
            data = []
            if self.dbUtils.isFuturesCode(objectCode):
                for product in self.selectedProducts:
                    szDict = {}
                    szDict['product'] = product
                    szDict['fundManager'] = self.loginName
                    szDict['objectCode'] = objectCode
                    szDict['objectClass'] = 'futures'
                    szDict['objectName'] = str(self.lineName.text())
                    szDict['taskPrice'] = self.sprinPrice.value()
                    szDict['taskVolume'] = self.spinVolume.value()
                    szDict['offset'] = 0.0
                    szDict['direction'] = str(self.comboDirection.currentText())
                    if self.sellFlag:
                        szDict['buySell'] = TRADE_SELL
                    else:
                        szDict['buySell'] = TRADE_BUY
                    data.append(szDict)
                    info = info + '产品：%s: \n代码：%s   价格：%f   数量：%d手   买卖：%s   开平：%s\n\n'  \
                                  % (szDict['product'], szDict['objectCode'], szDict['taskPrice'], szDict['taskVolume'], szDict['buySell'], szDict['direction'])
            else:
                QtGui.QMessageBox.warning(self, u'信息提示', u'输入合约代码不正确')
                return
        else:   # 证券
            data = []
            isSecFlag = self.dbUtils.isSecId(objectCode)
            # if self.dbUtils.isSecId(objectCode):
            if self.sellFlag:
                volumeList = self.dbUtils.getProductVolume(self.selectedProducts, objectCode)
            for product in self.selectedProducts:
                szDict = {}
                szDict['product'] = product
                szDict['fundManager'] = self.loginName
                szDict['objectCode'] = objectCode
                szDict['objectClass'] = 'sec'
                szDict['objectName'] = str(self.lineName.text())
                szDict['taskPrice'] = self.sprinPrice.value()
                szDict['offset'] = 0.0
                if self.sellFlag:
                    if self.selectedRatio < 0.01:
                        volume = self.spinVolume.value()
                        szDict['taskVolume'] = volume
                    else:
                        volume = self.selectedRatio
                    szDict['buySell'] = TRADE_SELL
                    szDict['taskVolume'] = volume
                    data.append(szDict)
                    info = info + '产品：%s: \n代码：%s   价格：%.2f   数量/比例：%f 股   买卖：%s\n\n'  \
                                    % (szDict['product'], szDict['objectCode'], szDict['taskPrice'], szDict['taskVolume'],
                                     szDict['buySell'])
                else:
                    szDict['buySell'] = TRADE_BUY
                    if self.selectedRatio < 0.01:
                        volume = self.spinVolume.value()
                        szDict['taskVolume'] = volume
                    else:
                        szDict['taskVolume'] = 100*int(self.productPerserving[product] * self.selectedRatio/(100 * self.sprinPrice.value()))
                    data.append(szDict)
                    if self.productPerserving[product] == 0:
                        ratio = 0
                    else:
                        ratio = szDict['taskPrice']*szDict['taskVolume']/self.productPerserving[product]
                    optionalStockList = self.dbUtils.getOptionalStockList()
                    if optionalStockList and self.optionalControlFlag:
                        if szDict['objectCode'] in optionalStockList:
                            info = info + '产品：%s: \n代码：%s   价格：%.2f   数量：%d股   买卖：%s   金额：%.2f   占每份比例%.4f：\n\n'  \
                                          % (szDict['product'], szDict['objectCode'], szDict['taskPrice'], szDict['taskVolume'],
                                             szDict['buySell'], szDict['taskPrice']*szDict['taskVolume'], ratio)
                        else:
                            info = info + '买入股票不在自选股票池中，无法下单'
                            QtGui.QMessageBox.warning(self, u'信息提示', unicode(info))
                            for i in range(0, self.productNum):
                                self.productCbs[i].setChecked(False)
                            self.productAll.setChecked(False)
                            self.lineID.setText('')
                            self.lineName.setText('')
                            self.sprinPrice.setValue(0)
                            self.spinVolume.setValue(0)
                            self.ratioRbs[len(self.ratioRbs)-1].setChecked(True)
                            return
                    else:
                        info = info + '产品：%s: \n代码：%s   价格：%.2f   数量：%d股   买卖：%s   金额：%.2f   占每份比例%.4f：\n\n'  \
                                      % (szDict['product'], szDict['objectCode'], szDict['taskPrice'], szDict['taskVolume'],
                                         szDict['buySell'], szDict['taskPrice']*szDict['taskVolume'], ratio)

        reply = QtGui.QMessageBox.question(self, u'信息确认',unicode(info), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.mainEngine.sendOrder(data, 'Simu')
            # 期货
            if self.tabFlag:
                for i in range(0, self.productNum):
                    self.productCbs[i].setChecked(False)
                self.productAll.setChecked(False)
                self.lineID.setText('')
                self.lineName.setText('')
                self.sprinPrice.setValue(0)
                self.spinVolume.setValue(0)
                self.comboDirection.setCurrentIndex(0)
            # 证券
            else:
                for i in range(0, self.productNum):
                    self.productCbs[i].setChecked(False)
                self.productAll.setChecked(False)
                self.lineID.setText('')
                self.lineName.setText('')
                self.sprinPrice.setValue(0)
                self.spinVolume.setValue(0)
                self.ratioRbs[len(self.ratioRbs)-1].setChecked(True)

    # --------------------------------
    def selfCheck(self):
        if self.selectedProducts == []:
            return False
        if str(self.lineID.text()) == '':
            return False
        if self.sprinPrice.value() == 0.0:
            return False
        if self.tabFlag == 0:
            if self.selectedRatio == 0.0 and self.spinVolume.value() == 0:
                return False
        else:
            if self.spinVolume.value() == 0:
                return False
        return True

    # ---------------------------------
    def getAllCode(self, code):
        self.dbUtils.getFuturesParameter()


# ===============================================
class TrendDraw(BasicDrawTwin):
    """"""
    def __init__(self, mainEngine, eventEngine, cache,parent=None):
        super(TrendDraw, self).__init__(parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.runningFlag = False
        self.cache = cache
        self.code = None
        self.dbUtils = self.cache['dbUtils']
        self.setTitle('Trend Oscillation Index')

    # -----------------------------
    def drawing(self, secId):
        if not self.runningFlag:
            # print 'self.code:', self.code

            if self.code != secId:
                # print 'secId:', secId
                self.code = secId
                self.runningFlag = True
                sThread = Thread(target=self.onDraw)
                sThread.start()

    # ---------------------------------
    def onDraw(self):
        data = []
        try:
            data = self.getData(self.code)
        except:
            print u'获取数据异常'

        if data:
            self.resetData()
            try:
                self.parent().parent().dockTrendD.raise_()
            except:
                pass

            self.setData(data['datetime'], data['close'], data['RankC'])
            self.setLabel('', self.code, 'RankC')
            self.drawTwin()

        self.runningFlag = False

    # -----------------------------
    def getData(self, code):
        """从数据库获取数据"""
        return self.dbUtils.getTrendData(code)
