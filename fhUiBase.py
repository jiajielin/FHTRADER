# coding=utf-8

"""
Time : 2016/8/3 11:24
Author : Jia Jielin
Company: fhhy.co
File : fhUiBase.py
Description:

"""

# system module
from collections import OrderedDict
import winsound
import json
from PyQt4 import QtGui, QtCore

# own module
from fhGateway import *
from fhFunc import safeUnicode

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figureCanvas
from matplotlib.pyplot import gcf


def loadFont():
    """载入字体设置"""
    try:
        f = file('setting.json')
        setting = json.load(f)
        f.close()
        family = setting['fontFamily']
        size = setting['fontSize']
        font = QtGui.QFont(family, size)
    except:
        font = QtGui.QFont(u'微软雅黑', 12)
    return font

# -------------------------
BASIC_FONT = loadFont()

def loadProductRatio():
    dictRatio = [u'1',u'1/2', u'1/3', u'1/4', u'1/5', u'1/10', u'0']
    ratioList = [1, 0.5, 0.33, 0.25, 0.2, 0.1, 0.0]
    return dictRatio, ratioList

# ----------------------------------
def financialCount(num, percentFlag=0):
    """当输入为int,float时，改为千分位计数
    同时对于是否百分号显示做改动:
    percentFlag==0:非百分号显示
    percentFlag==1:全部数据百分号显示
    percentFlag==-1:只对绝对值小于等于1的数字百分号显示"""
    makePercent = False
    if type(num) == int or type(num) == long:
        if percentFlag == 1:
            num *= 100
            makePercent = True
        if percentFlag == -1:
            if abs(num) <= 1:
                num *= 100
                makePercent = True

        unsignNum = abs(num)
        nstr = str(unsignNum)
        n = len(nstr)
        nList = []
        while n > 3:
            nList.append(3)
            n -= 3
        nList.append(n)
        nList.reverse()
        retStr = ''
        counter = 0
        for i in range(0, (len(nList) - 1)):
            retStr += nstr[counter:(counter + nList[i])]
            retStr += ','
            counter += nList[i]
        retStr += nstr[counter:]
        if num < 0:
            retStr = '-' + retStr
        if makePercent:
            retStr = retStr + '%'
        return retStr
    elif type(num) == float:
        if percentFlag == 1:
            num *= 100
            makePercent = True
        if percentFlag == -1:
            if abs(num) <= 1:
                num *= 100
                makePercent = True
        unsignNum = abs(num)
        try:
            if (unsignNum - int(unsignNum)) == 0:
                unsignNum = int(unsignNum)
        except:
            pass
        nstr = str(unsignNum)
        nSplit = nstr.split('.')
        flag = 1    # 1表示只处理整数，0表示处理整数和小数部分
        if len(nSplit) == 1:
            flag = 1
        elif len(nSplit) == 2:
            if nSplit[1]:
                flag = 0
        else:
            if makePercent:
                return num/100
            return num
        if flag:
            n = len(nSplit[0])
            nList = []
            while n > 3:
                nList.append(3)
                n -= 3
            nList.append(n)
            nList.reverse()
            retStr = ''
            counter = 0
            for i in range(0, (len(nList) - 1)):
                retStr += nSplit[0][counter:(counter + nList[i])]
                retStr += ','
                counter += nList[i]
            retStr += nSplit[0][counter:]
            if num < 0:
                retStr = '-' + retStr
            if makePercent:
                retStr = retStr + '%'
            return retStr
        else:
            n = len(nSplit[0])
            nList = []
            while n > 3:
                nList.append(3)
                n -= 3
            nList.append(n)
            nList.reverse()
            retStr = ''
            counter = 0
            for i in range(0, (len(nList) - 1)):
                retStr += nSplit[0][counter:(counter + nList[i])]
                retStr += ','
                counter += nList[i]
            retStr += nSplit[0][counter:]
            # 加小数部分
            retStr += '.'
            m = len(nSplit[1])
            mList = []
            while m > 3:
                mList.append(3)
                m -= 3
            mList.append(m)
            counter = 0
            for i in range(0, (len(mList) - 1)):
                retStr += nSplit[1][counter:(counter + mList[i])]
                retStr += ','
                counter += mList[i]
            retStr += nSplit[1][counter:]
            if num < 0:
                retStr = '-' + retStr
            if makePercent:
                retStr = retStr + '%'
            return retStr
    else:
        return num

# --------------------------------------
class BasicTreeMonitor(QtGui.QWidget):
    """
    树形监控，至多两层
    更新数据事件：
    通过初始化传入更新事件，分为两类，一类是未完成的更新事件，一类是已完成的更新事件，
    每次未完成更新状态时发送更改状态请求及全量更新，届时会将
    """
    signal = QtCore.pyqtSignal(type(Event()))

    # -----------------------------------
    def __init__(self, buttonFlag=2, mainEngine=None, eventEngine=None, warningFlag=False,parent=None):
        super(BasicTreeMonitor, self).__init__()
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.buttonFlag = buttonFlag    # 0，无button；1，有刷新button；2，有刷新、挂起button

        # 保存表头标签用
        self.headerDict = OrderedDict()
        self.headerList = []
        self.mainHeader = ''    # 主字段，字符串类型，为headerList[0]，在task中，为主任务序号
        self.subHeader = ''     # 子字段，字符串类型，需自己定义，在task中，为任务子序号
        self.colNum = 0         # 记录列长

        # 保存相关数据用
        self.dataDict = {}  # 数据存储字段，按mainHeader->subHeader->数据索引，结构为{mainHeader0:{subHeader0:{},subHeader1:{} }, mainHeader1:{subHeader0:{}}} 说明：subHeader的value字典中无subHeader字段,用mainHeader字段记录其中的subHeader值

        # 监控事件类型
        self.eventType = ''

        # 字体
        self.font = None

        self.finCountHeader = {}

        # 新增item背景色提醒
        self.addBgColor = QtGui.QColor()
        self.addBgColor.setGreen(255)

        # 默认背景色
        self.defaultBgColor = QtGui.QColor()
        self.defaultBgColor.setRgb(255,255,255)


        # 新增背景色开启Flag
        self.bgColorFlag = False

        # 默认不允许表头排序，需要的组件可以开启
        self.sorting = False

        # 设置表头筛选项，用于相同内容的分别显示，主要是针对交易状态or证券期货，每个值为过滤属性
        self.headerFilterDict = []
        # 过滤器内容，key为过滤属性，value为相关字段，为list，在value中的值方予以显示
        self.headerFilter = {}
        self.filterFlag = False
        self.gatewayName = ''


        # 菜单名称列表
        self.menuNameList = []
        self.menuHandlerDict = {}

        # 用于标记是否展开，用于刷新更新数据时不改变展开状态，True允许展开，False不允许
        self.expandFlag = True

        # 提示音相关
        self.warningFlag = warningFlag
        self.playFlag = False
        if self.warningFlag:
            self.warningTimer = Thread(target=self.onPlayTiemr)

        self.initUi()
        if self.warningFlag:
            self.warningTimer.start()

    # ------------------------------
    def initUi(self):
        # 操作按键
        self.tree = QtGui.QTreeWidget()
        # 当为2，增加挂起、刷新button
        if self.buttonFlag == 2:
            self.haltButton = QtGui.QPushButton(u'在线')
            self.haltButton.clicked.connect(self.halt)
            self.refreshButton = QtGui.QPushButton(u'刷新')
            self.refreshButton.clicked.connect(self.refresh)

            hLayout = QtGui.QHBoxLayout()
            vLayout = QtGui.QVBoxLayout()
            hLayout.addWidget(self.haltButton)
            hLayout.addWidget(self.refreshButton)
            hLayout.addStretch()
            vLayout.addWidget(self.tree)
            vLayout.addLayout(hLayout)
            self.setLayout(vLayout)
        # 当为1，增加刷新button
        elif self.buttonFlag == 1:
            # self.haltButton = QtGui.QPushButton(u'挂起')
            # self.haltButton.clicked.connect(self.halt)
            self.refreshButton = QtGui.QPushButton(u'刷新')
            self.refreshButton.clicked.connect(self.refresh)

            vLayout = QtGui.QVBoxLayout()
            # hLayout.addWidget(self.haltButton)
            vLayout.addWidget(self.tree)
            hLayout = QtGui.QHBoxLayout()
            hLayout.addWidget(self.refreshButton)
            hLayout.addStretch()
            vLayout.addLayout(hLayout)
            # vLayout.addWidget(self.refreshButton)
            # vLayout.addStretch()
            self.setLayout(vLayout)
        else:
            vLayout = QtGui.QVBoxLayout()
            vLayout.addWidget(self.tree)
            self.setLayout(vLayout)

        # 初始化右键菜单
        self.initMenu()

    # -------------------------------------------
    def halt(self):
        pass

    # ---------------------------------------------
    def refresh(self):
        self.expandFlag = False
        if self.bgColorFlag:
            topCount = self.tree.topLevelItemCount()
            for i in range(0, topCount):
                topItem = self.tree.topLevelItem(i)
                num = topItem.childCount()
                for j in range(0, num):
                    item = topItem.child(j)
                    if item.backgroundColor(0) == self.addBgColor:
                        for k in range(0, self.colNum):
                            item.setBackgroundColor(k, self.defaultBgColor)

    # ---------------------------------------
    def setHeaderDict(self, headerDict, mainHeader, subHeader):
        """设置表头信息"""
        self.headerDict = headerDict
        self.headerList = headerDict.keys()
        self.mainHeader = mainHeader
        self.subHeader = subHeader
        self.colNum = len(self.headerDict)

    # ---------------------------------------
    def setHeaderFilterDict(self, header, filter):
        self.headerFilterDict.append(header)
        self.headerFilter[header] = filter
        self.filterFlag = True

    # ------------------------------------------
    def setEventType(self, eventType):
        """设置监控的事件类型"""
        self.eventType = eventType

    # ----------------------------
    def setFont(self, font):
        """设置字体"""
        self.font = font

    # ------------------------------
    def setFinCountHeader(self, header, flag=0):
        self.finCountHeader[header] = flag

    # ------------------------------
    def initTable(self):
        # 设置表格列数
        col = len(self.headerDict)
        self.tree.setColumnCount(col)

        # 设置列表头
        labels = [d['chinese'] for d in self.headerDict.values()]
        self.tree.setHeaderLabels(labels)

        # 设置为不可编辑
        self.tree.setEditTriggers(self.tree.NoEditTriggers)   # 需重做，规定可编辑项

        # 设置为行交替颜色
        self.tree.setAlternatingRowColors(True)

        # 设置允许排列
        self.tree.setSortingEnabled(self.sorting)

    # ------------------------------
    def registerEvent(self):
        self.signal.connect(self.updateEvent)
        self.eventEngine.register(self.eventType, self.signal.emit)

    # ------------------------------
    def updateEvent(self, event):
        data = event.dict_['data']
        self.updateData(data)

    # ------------------------------
    def updateData(self, data):
        """
        数据更新至表格中
        data格式：【{}，{}】
        """
        for k in range(0, len(data)):
            inFilter = True
            if self.filterFlag:
                # 通过headerFilterDict和headerFilter筛选数据，对于不在过滤器中的数据，再进行判断，如果已经加入数据中，删除之
                for i in range(0, len(self.headerFilterDict)):
                    if self.headerFilterDict[i] in data[k]:
                        if data[k][self.headerFilterDict[i]] not in self.headerFilter[self.headerFilterDict[i]]:
                            # 如果不在过滤器中，且在保存在dataDict中，则删除
                            if data[k][self.mainHeader] in self.dataDict:
                                if data[k][self.subHeader] in self.dataDict[data[k][self.mainHeader]]:
                                    # 如果子任务在dataDict中，则删除子任务，包括删除对应节点
                                    # 删除对应节点
                                    itemList = self.tree.findItems(data[k][self.mainHeader], QtCore.Qt.MatchRecursive)
                                    if itemList != []:
                                        itemRoot = itemList[0]
                                        # 如果是子任务
                                        if data[k][self.subHeader] != '':
                                            for j in range(0, itemRoot.childCount()):
                                                if itemRoot.child(j).text(0) == data[k][self.subHeader]:
                                                    itemRoot.takeChild(j)   # 删除子任务节点
                                                    self.dataDict[data[k][self.mainHeader]].pop(data[k][self.subHeader])    # 删除存储数据
                                                    break
                                            # 如果总任务名下已无数据，或只有subNo为''的数据，则删除总任务
                                            if len(self.dataDict[data[k][self.mainHeader]]) == 0:
                                                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(itemRoot)) # 删除总任务节点
                                                self.dataDict.pop(data[k][self.mainHeader]) # 删除存储数据
                                            elif len(self.dataDict[data[k][self.mainHeader]]) == 1 and  ('' in self.dataDict[data[k][self.mainHeader]]):
                                                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(itemRoot)) # 删除总任务节点
                                                self.dataDict.pop(data[k][self.mainHeader]) # 删除存储数据
                                        # # 如果是总任务
                                        # else:
                                        #     self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(itemRoot)) # 删除总任务节点
                                        #     self.dataDict.pop(data[k][self.mainHeader]) # 删除存储数据
                            # 当筛选字段不在筛选字典中时，则inFilter为False，不再进行更新
                            inFilter = False
                    else:
                        # 当跟新数据中无筛选字段时，inFilter为False舍弃该数据，不再进行更新
                        inFilter = False
            # 当筛选字段在过滤字典中时，进行更新操作
            if inFilter:
                # 排序判断
                if self.sorting:
                    self.tree.setSortingEnabled(False)
                key = data[k][self.mainHeader]
                # 当key值不在现有字典中时，增量更新，添加树结构
                if key not in self.dataDict:
                    d = {}
                    tempRoot = QtGui.QTreeWidgetItem(self.tree)
                    subKey = ''
                    if self.subHeader in data[k]:
                        subKey = data[k][self.subHeader]
                    d[subKey] = {}
                    # 如果是主任务
                    if subKey == '' or subKey == None:
                        for n, header in enumerate(self.headerList):
                            if header in data[k]:
                                content = safeUnicode(data[k][header])
                                tempRoot.setText(n, content)
                                d[subKey][header] = content
                            else:
                                tempRoot.setText(n, '')
                                d[subKey][header] = ''
                        self.dataDict[key] = d
                    # 如果是子任务
                    else:
                        # 在dataDict中添加主任务数据
                        d[''] = {}
                        # 设置根节点数据
                        content = safeUnicode(key)
                        tempRoot.setText(0, content)
                        d[''][self.mainHeader] = content

                        tempChild = QtGui.QTreeWidgetItem(tempRoot)
                        if self.bgColorFlag:
                            for col in range(0, self.colNum):
                                tempChild.setBackgroundColor(col, self.addBgColor)
                        # 用subKey填充第mainHeadr和subHeader共同占用的cell，并记录subHeader值
                        content = safeUnicode(subKey)
                        tempChild.setText(0, content)
                        d[subKey][self.subHeader] = content
                        for n, header in enumerate(self.headerList):
                            if n > 0:
                                if header in data[k]:
                                    if header in self.finCountHeader:
                                        content = safeUnicode(financialCount(data[k][header], self.finCountHeader[header]))
                                    else:
                                        content = safeUnicode(data[k][header])
                                    tempChild.setText(n, content)
                                    d[subKey][header] = content
                                else:
                                    tempChild.setText(n, safeUnicode(''))
                                    d[subKey][header] = ''
                        # 将数据传递给dataDict
                        self.dataDict[key] = d
                    tempRoot.setExpanded(True)
                    self.playFlag = True
                # 当key值在现有字典中时，存量更新，更新数值
                else:
                    subKey = data[k][self.subHeader]
                    itemList = self.tree.findItems(key, QtCore.Qt.MatchRecursive)
                    # 如果itemList不为空，则其中值为所需主任务item，
                    if itemList != []:
                        item = itemList[0]
                        if self.expandFlag:
                            item.setExpanded(True)
                    else:
                        continue
                    # 如果是更新主任务信息
                    if subKey == '' or subKey == None:
                        d = self.dataDict[key]
                        if subKey not in self.dataDict[key]:
                            d[subKey] = {}
                        for n, header in enumerate(self.headerList):
                            if header in data[k]:
                                content = safeUnicode(data[k][header])
                                item.setText(n, content)
                                d[subKey][header] = content
                        self.dataDict[key] = d
                    # 如果是更新子任务信息
                    else:
                        # 如果子任务不在显示中，需新增
                        if subKey not in self.dataDict[key]:
                            d = {}
                            # 设置子节点，并记录subHeader值
                            tempChild = QtGui.QTreeWidgetItem(item)
                            if self.bgColorFlag:
                                for col in range(0, self.colNum):
                                    tempChild.setBackgroundColor(col, self.addBgColor)
                            content = safeUnicode(subKey)
                            tempChild.setText(0, content)
                            d[self.subHeader] = content
                            for n, header in enumerate(self.headerList):
                                if n > 0:
                                    if header in data[k]:
                                        if header in self.finCountHeader:
                                            content = safeUnicode(financialCount(data[k][header], self.finCountHeader[header]))
                                        else:
                                            content = safeUnicode(data[k][header])
                                        tempChild.setText(n, content)
                                        d[header] = content
                            self.dataDict[key][subKey] = d
                            item.setExpanded(True)
                        # 如果子任务在显示中，只更新
                        else:
                            subDict = self.dataDict[key][subKey]
                            # 查找通过key与subKey查找匹配的item
                            itemRoot = item
                            item = None
                            for j in range(0, itemRoot.childCount()):
                                if itemRoot.child(j).text(0) == subKey:
                                    item = itemRoot.child(j)
                                    break
                            if item == None:
                                continue
                            content = safeUnicode(data[k][self.subHeader])
                            item.setText(0, content)
                            subDict[self.subHeader] = content
                            for n, header in enumerate(self.headerList):
                                if n > 0:
                                    if header in data[k]:
                                        if header in self.finCountHeader:
                                            content = safeUnicode(financialCount(data[k][header], self.finCountHeader[header]))
                                        else:
                                            content = safeUnicode(data[k][header])
                                        item.setText(n, content)
                                        subDict[header] = content

                self.tree.setSortingEnabled(self.sorting)
                self.expandFlag = True
                for i in range(0, len(self.headerDict)):
                    self.tree.resizeColumnToContents(i)

    # ----------------------------------------------
    def resizeColumns(self):
        self.horizontalHeader().resizeSections(QtGui.QHeaderView.ResizeToContents)  # todo 无对应函数

    # ------------------------------
    def setSorting(self, sorting):
        self.sorting = sorting

    # ------------------------------
    def initMenu(self):
        """初始化右键菜单"""
        self.tree.menu = QtGui.QMenu(self)
        self.actionList = [QtGui.QAction(content, self.tree) for content in self.menuNameList]
        for n, action in enumerate(self.actionList):
            if self.menuNameList[n] in self.menuHandlerDict:
                action.triggered.connect(self.menuHandlerDict[self.menuNameList[n]])
                self.tree.menu.addAction(action)

    # ------------------------------
    def setMenuItems(self, menuNameList, menuHandlerDict):
        self.menuNameList = menuNameList
        self.menuHandlerDict = menuHandlerDict
        self.actionList = [QtGui.QAction(content, self.tree) for content in self.menuNameList]
        for n, action in enumerate(self.actionList):
            if self.menuNameList[n] in self.menuHandlerDict:
                action.triggered.connect(self.menuHandlerDict[self.menuNameList[n]])
                self.tree.menu.addAction(action)

    # ---------------------------------
    def contextMenuEvent(self, event):
        """右键点击事件"""
        curItem = self.tree.currentItem()
        if curItem:
            if curItem.childCount() == 0:
                self.tree.menu.popup(QtGui.QCursor.pos())

    # -----------------------------------
    def onPlayTiemr(self):
        while 1:
            if self.playFlag:
                try:
                    winsound.PlaySound('warning', winsound.SND_ALIAS)
                except:
                    pass

                self.playFlag = False
            sleep(1)

    # ------------------------------------
    def __del__(self):
        if self.warningFlag:
            self.warningTimer.join()
        super(BasicTreeMonitor, self).__del__()


# ============================================
class BasicMonitor(QtGui.QTableWidget):
    """
    基础监控
    """
    signal = QtCore.pyqtSignal(type(Event()))

    # -----------------------------------
    def __init__(self, mainEngine=None, eventEngine=None, parent=None):
        super(BasicMonitor, self).__init__(parent)

        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        # 保存表头标签用
        self.headerDict = OrderedDict()  # 有序字典，key是英文名，value是对应的配置字典
        self.headerList = []  # 对应self.headerDict.keys()

        # 设置表头筛选项，用于相同内容的分别显示，主要是针对各个产品
        self.headerFilterDict = []
        self.headerFilter = {}
        self.filterFlag = False

        # 保存相关数据用
        self.dataDict = {}  # 字典，key是字段对应的数据，value是保存相关单元格的字典
        self.dataKey = ''  # 字典键对应的数据字段

        # 监控事件类型
        self.eventType = ''

        # 字体
        self.font = None

        # 最大行数，为0时，不限制
        self.maxRowCount = 1500

        # 保存数据对象到单元格
        self.saveData = False

        # 默认不允许根据表头进行排序，需要的组件可以开启
        self.sorting = False

        # 菜单名称列表
        self.menuNameList = []
        self.menuHandlerDict = {}

        # 初始化右键菜单
        self.initMenu()

    # -----------------------------
    def setHeaderDict(self, headerDict):
        """设置表头有序字典"""
        self.headerDict = headerDict
        self.headerList = headerDict.keys()

    # ------------------------------
    def addHeaderFilterDict(self, header, filter):
        self.headerFilterDict.append(header)
        self.headerFilter[header] = filter
        self.filterFlag = True

    # ------------------------------
    def setDataKey(self, dataKey):
        """设置数据字典的键"""
        self.dataKey = dataKey

    # -----------------------------
    def setEventType(self, eventType):
        """设置监控的事件类型"""
        self.eventType = eventType

    # --------------------------------
    def setFont(self, font):
        """设置字体"""
        self.font = font

    # ---------------------------------
    def initTable(self):
        # 设置表格列数
        col = len(self.headerDict)
        self.setColumnCount(col)

        # 设置列表头
        labels = [d['chinese'] for d in self.headerDict.values()]
        self.setHorizontalHeaderLabels(labels)

        # 关闭左边垂直表头
        self.verticalHeader().setVisible(False)

        # 设置为不可编辑
        self.setEditTriggers(self.NoEditTriggers)

        # 设置为行交替颜色
        self.setAlternatingRowColors(True)

        # 设置允许排列
        self.setSortingEnabled(self.sorting)

    # -----------------------------
    def registerEvent(self):
        self.signal.connect(self.updateEvent)
        self.eventEngine.register(self.eventType, self.signal.emit)

    # ------------------------------------
    def updateEvent(self, event):
        data = event.dict_['data']
        self.updateData(data)

    # ------------------------------------
    def updateData(self, data):
        """数据更新至表格中"""
        inFilterFlag = True
        if self.filterFlag:
            for i in range(0, len(self.headerFilterDict)):
                if self.headerFilterDict[i] in data:
                    if data[self.headerFilterDict[i]] not in self.headerFilter[self.headerFilterDict[i]]:
                        inFilterFlag = False
                        break
                else:
                    inFilterFlag = False
                    break

        if inFilterFlag:
            # 如果允许排序，则插入数据前需关闭，否则插入新的数据会变乱
            if self.sorting:
                self.setSortingEnabled(False)

            # 如果设置了dataKey，则采用存量更新模式
            if self.dataKey:
                key = data.__getattribute__(self.dataKey)
                # 如果键在数据字典中不存在，则先插入新的一行，并创建对应单元格
                if key not in self.dataDict:
                    self.insertRow(0)
                    d = {}
                    for n, header in enumerate(self.headerList):
                        content = safeUnicode(data.__getattribute__(header))
                        cellType = self.headerDict[header]['cellType']
                        cell = cellType(content, self.mainEngine)

                        if self.font:
                            cell.setFont(self.font)  # 如果设置了特殊字体，则进行单元格设置

                        if self.saveData:  # 如果设置了保存数据对象，则进行对象保存
                            cell.data = data

                        self.setItem(0, n, cell)
                        d[header] = cell
                    self.dataDict[key] = d
                # 否则如果已经存在，则直接更新相关单元格
                else:
                    d = self.dataDict[key]
                    for header in self.headerList:
                        if header in dir(data):
                            content = safeUnicode(data.__getattribute__(header))
                            cell = d[header]
                            cell.setContent(content)

                            if self.saveData:  # 如果设置了保存数据对象，则进行对象保存
                                cell.data = data

            # 否则采用增量更新模式
            else:
                self.insertRow(0)
                for n, header in enumerate(self.headerList):
                    content = safeUnicode(data.__getattribute__(header))
                    cellType = self.headerDict[header]['cellType']
                    cell = cellType(content, self.mainEngine)

                    if self.font:
                        cell.setFont(self.font)

                    if self.saveData:
                        cell.data = data

                    self.setItem(0, n, cell)

            # 调整列宽
            self.resizeColumns()

            # 重新打开排序
            if self.sorting:
                self.setSortingEnabled(True)
        if self.maxRowCount:
            n = self.rowCount()
            while n >= self.maxRowCount:
                self.removeRow(n)
                n -= 1

    # ----------------------------------
    def deleteItem(self, item=[]):
        if item:
            row = item.row()
            itemKey = self.item(row, self.headerDict.keys().index(self.dataKey))
            self.dataDict.pop(itemKey)
            self.removeRow(row)
        else:
            n = self.rowCount()
            while n:
                n -= 1
                self.removeRow(n)
            self.dataDict = {}

    # ---------------------------------------
    def resizeColumns(self):
        self.horizontalHeader().resizeSections(QtGui.QHeaderView.ResizeToContents)

    # ----------------------------
    def setSorting(self, sorting):
        self.sorting = sorting

    # --------------------------------
    def initMenu(self):
        """初始化右键菜单"""
        self.menu = QtGui.QMenu(self)
        self.actionList = [QtGui.QAction(content, self) for content in self.menuNameList]
        for n, action in enumerate(self.actionList):
            if self.menuNameList[n] in self.menuHandlerDict:
                action.triggered.connect(self.menuHandlerDict[self.menuNameList[n]])
                self.menu.addAction(action)

    # ------------------------------
    def setMenuItems(self, menuNameList, menuHandlerDict):
        self.menuNameList = menuNameList
        self.menuHandlerDict = menuHandlerDict
        self.actionList = [QtGui.QAction(content, self) for content in self.menuNameList]
        for n, action in enumerate(self.actionList):
            if self.menuNameList[n] in self.menuHandlerDict:
                action.triggered.connect(self.menuHandlerDict[self.menuNameList[n]])
                self.menu.addAction(action)


    # ---------------------------------
    def contextMenuEvent(self, event):
        """右键点击事件"""
        curItem = self.currentItem()
        if curItem:
            self.menu.popup(QtGui.QCursor.pos())


# ================================================
class BasicTreeCell(QtGui.QTreeWidgetItem):
    """基础的单元格"""

    # ------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BasicTreeCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)

    # --------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if text == '0' or text == '0.0':
            self.setText('')
        else:
            self.setText(text)


# ===============================================
class BasicCell(QtGui.QTableWidgetItem):
    """基础的单元格"""

    # ------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(BasicCell, self).__init__()
        self.data = None
        if text:
            self.setContent(text)

    # --------------------------------------------
    def setContent(self, text):
        """设置内容"""
        # if text == '0' or text == '0.0':
        #     self.setText('')
        # else:
        #     self.setText(text)
        self.setText(text)


# ==============================================
class NameCell(QtGui.QTableWidgetItem):
    """用来显示中文的单元格"""

    # --------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(NameCell, self).__init__()

        self.mainEngine = mainEngine
        self.data = None

        if text:
            self.setContent(text)

    # -----------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if self.mainEngine:
            # 首先尝试正常获取合约对象
            contract = self.mainEngine.getContract(text)

            # 如果能读取合约信息
            if contract:
                self.setText(contract.name)


# ====================================================
class Edit(QtGui.QDialog):
    def __init__(self):
        super(Edit, self).__init__()
        self.label = QtGui.QLineEdit()


# =================================================
class BasicDrawTwin(QtGui.QWidget):
    """"""
    def __init__(self, parent=None):
        super(BasicDrawTwin, self).__init__(parent)
        self.figure = gcf()
        self.canvas = figureCanvas(self.figure)
        self.canvas.draw()
        self.xdata = []
        self.ydata1 = []
        self.ydata2 = []
        self.title = 'BasicDraw'
        self.xlabel = 'x'
        self.ylabel1 = 'y1'
        self.ylabel2 = 'y2'
        self.color1 = 'blue'
        self.color2 = 'red'
        self.ax1 = None
        self.ax2 = None
        self.line1 = None    # 记录画图，在第一次调用时会由plot赋值
        self.line2 = None    # 记录画图，在第一次调用时会由plot赋值
        self.firstDrawFlag = True
        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.canvas)

    # -----------------------------------
    def setData(self, xdata, ydata1, ydata2):
        if len(xdata) != len(ydata1):
            print u'画图数据长度不匹配'
            return
        if len(xdata) != len(ydata2):
            print u'画图数据长度不匹配'
            return
        self.xdata = xdata
        self.ydata1 = ydata1
        self.ydata2 = ydata2

    # ---------------------------------------
    def setTitle(self, title):
        self.title = title

    # ------------------------------------------
    def setLabel(self, xlabel, ylabel1, ylabel2):
        self.xlabel = xlabel
        self.ylabel1 = ylabel1
        self.ylabel2 = ylabel2

    # -------------------------------------------
    def setColor(self, color1, color2):
        self.color1 = color1
        self.color2 = color2

    # -----------------------------------------------
    def resetData(self):
        self.xdata = []
        self.ydata1 = []
        self.ydata2 = []

    # -----------------------------------------------
    def drawTwin(self):
        if self.firstDrawFlag:
            self.firstDrawFlag = False
            self.ax1 = self.figure.add_subplot(111)
            self.line1, = self.ax1.plot(self.xdata, self.ydata1, self.color1)
            self.ax1.set_ylabel(self.ylabel1)
            min1 = min(self.ydata1)
            max1 = max(self.ydata1)
            bias1 = 0.1 * (max1 - min1)
            min1 -= bias1
            max1 += bias1
            self.ax1.set_ylim([min1, max1])
            self.ax1.set_title(self.title)

            self.ax2 = self.ax1.twinx()
            self.line2, = self.ax2.plot(self.xdata, self.ydata1, self.color2)
            self.ax2.set_ylabel(self.ylabel2)

            min2 = min(self.ydata2)
            max2 = max(self.ydata2)
            bias2 = 0.1 * (max2 - min2)
            min2 -= bias2
            max2 += bias2
            self.ax2.set_ylim([min2, max2])

            self.ax2.set_xlabel(self.xlabel)
            self.drawTwin()
        else:
            self.line1.set_xdata(self.xdata)
            self.line1.set_ydata(self.ydata1)
            self.line2.set_ydata(self.ydata2)

            min1 = min(self.ydata1)
            max1 = max(self.ydata1)
            bias1 = 0.1 * (max1 - min1)
            min1 -= bias1
            max1 += bias1
            self.ax1.set_ylim([min1, max1])

            min2 = min(self.ydata2)
            max2 = max(self.ydata2)
            bias2 = 0.1 * (max2 - min2)
            min2 -= bias2
            max2 += bias2
            self.ax2.set_ylim([min2, max2])
        # plt.legend([self.ylabel1, self.ylabel2])
        self.ax1.legend([self.ylabel1],loc=1)
        self.ax2.legend([self.ylabel2], loc=2)

        self.canvas.draw_idle()




