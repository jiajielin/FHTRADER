# coding=utf-8

"""
Time : 2017/5/8 10:38
Author : Jia Jielin
Company: fhhy.co
File : fhUiOptional.py
Description:

"""


from fhUiBase import *
from fhGateway import *
from fhUtils import *


class OptionalTab(QtGui.QWidget):
    """自选股"""
    def __init__(self, mainEngine, eventEngine, cache, parent=None):
        super(OptionalTab, self).__init__(parent)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.dbUtils = self.cache['dbUtils']
        self.loginName = self.cache['loginName']
        self.verifyFlag = self.cache['verifyFlag']
        # 判断是修改备注还是添加自选股，若修改备注，则代码和名称栏不可编辑
        self.remarkFlag = False

        self.initUi()

    # --------------------------
    def initUi(self):
        self.labelSecId = QtGui.QLabel(u'代码')
        self.labelName = QtGui.QLabel(u'            名称')
        self.labelRemark = QtGui.QLabel(u'            备注')

        self.lineSecId = QtGui.QLineEdit()
        self.lineSecId.setMaximumWidth(150)
        # 关联列表
        secList = self.getSecList()
        secIdList = QtCore.QStringList()    # 设置股票代码匹配集
        for i in range(0, len(secList)):
            secIdList << secList[i][0] + '' + unicode(secList[i][1])
        idCompleter = QtGui.QCompleter(secIdList)
        self.lineSecId.setCompleter(idCompleter)
        self.lineSecId.editingFinished.connect(self.getSecIdName)


        self.lineName = QtGui.QLineEdit()
        self.lineName.setMaximumWidth(150)
        self.lineRemark = QtGui.QLineEdit()
        self.lineRemark.setMaximumWidth(200)

        self.addButton = QtGui.QPushButton()
        self.addButton.setText(u'添加')
        self.addButton.clicked.connect(self.addOptional)

        self.optionalPage = OptionalMonitor(self.mainEngine, self.eventEngine, self.cache, self)
        self.refreshButton = QtGui.QPushButton()
        self.refreshButton.setText(u'刷新')
        self.refreshButton.setMaximumWidth(100)
        self.refreshButton.clicked.connect(self.refresh)

        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(self.labelSecId)
        hLayout.addWidget(self.lineSecId)
        hLayout.addWidget(self.labelName)
        hLayout.addWidget(self.lineName)
        hLayout.addWidget(self.labelRemark)
        hLayout.addWidget(self.lineRemark)
        hLayout.addWidget(self.addButton)
        hLayout.addStretch()
        vLayout = QtGui.QVBoxLayout()
        vLayout.addLayout(hLayout)
        vLayout.addWidget(self.optionalPage)
        vLayout.addWidget(self.refreshButton)

        # vLayout.addStretch()
        self.setLayout(vLayout)
        # self.show()

    # ---------------------------------
    def refresh(self):
        self.optionalPage.refresh()

    # -------------------------------
    def addOptional(self):
        if self.remarkFlag:
            code = self.lineSecId.text()
            name = self.lineName.text()
            remark = self.lineRemark.text()
            ret = self.dbUtils.updataOptionalRemark(code, name, remark, self.loginName)
            if ret == 0:
                QtGui.QMessageBox.warning(self, u'提示', u'修改成功')
            elif ret == -1:
                QtGui.QMessageBox.warning(self, u'提示', u'修改失败')
            elif ret == -2:
                QtGui.QMessageBox.warning(self, u'提示', u'添加失败')
            elif ret == 1:
                QtGui.QMessageBox.warning(self, u'提示', u'添加成功')
            elif ret == 3:
                QtGui.QMessageBox.warning(self, u'提示', u'备注过长，操作失败')
            else:
                QtGui.QMessageBox.warning(self, u'提示', u'操作失败')
        else:
            code = self.lineSecId.text()
            name = self.lineName.text()
            remark = self.lineRemark.text()
            # 添加 0，成功；-1，失败；2，有重复；3，remark长度超标
            ret = self.dbUtils.addOptional(code, name, remark, self.loginName)
            if ret == 0:
                QtGui.QMessageBox.warning(self, u'提示', u'添加成功')
            elif ret == -1:
                QtGui.QMessageBox.warning(self, u'提示', u'添加失败')
            elif ret == 2:
                QtGui.QMessageBox.warning(self, u'提示', u'重复添加')
            elif ret == 3:
                QtGui.QMessageBox.warning(self, u'提示', u'备注过长，添加失败')
            else:
                pass
        self.refresh()
        self.remarkFlag = False

    # -----------------------------------------
    def getSecList(self, segment=[]):
        return self.dbUtils.getSecList(segment)

    # --------------------------------------------------
    def getSecIdName(self):
        if len(str(self.lineSecId.text())) >= 6:
            secIdTemp = str(self.lineSecId.text())[0:6]
            ret = self.dbUtils.getSecIdName(secIdTemp)
            if len(ret):
                self.lineSecId.setText(ret[0])
                self.lineName.setText(unicode(ret[1]))
        else:
            self.lineName.setText(unicode(''))


# ====================================================
class OptionalMonitor(BasicMonitor):
    def __init__(self, mainEngine, eventEngine, cache, parent):
        super(OptionalMonitor, self).__init__()
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.dbUtils = self.cache['dbUtils']
        self.loginName = self.cache['loginName']
        self.parent = parent

        d = OrderedDict()
        d['secId'] = {'chinese': u'代码', 'cellType': BasicCell}
        d['secName'] = {'chinese': u'名称', 'cellType': BasicCell}
        d['updateTime'] = {'chinese': u'更新时间', 'cellType': BasicCell}
        d['lastReferrer'] = {'chinese': u'最新推荐人', 'cellType': BasicCell}
        d['firstTime'] = {'chinese': u'入选时间', 'cellType': BasicCell}
        d['firstReferrer'] = {'chinese': u'最初推荐人', 'cellType': BasicCell}
        d['remark'] = {'chinese': u'备注', 'cellType': BasicCell}

        self.setHeaderDict(d)
        # 设置监控事件类型
        self.setEventType(EVENT_OPTIONAL)
        # 设置字体
        self.setFont(BASIC_FONT)
        # 初始化表格
        self.initTable()

        # 注册监控事件
        self.setEventType(EVENT_OPTIONAL)
        self.registerEvent()

        self.setSorting(True)
        self.setDataKey('secId')

        menuHandlerDict = {}
        menuNameList = [u'更新时间', u'修改备注', u'删除']
        menuHandlerDict[u'更新时间'] = self.updateOptional
        menuHandlerDict[u'修改备注'] = self.modifyRemark
        menuHandlerDict[u'删除'] = self.deleteOptional
        self.setMenuItems(menuNameList, menuHandlerDict)

    # ----------------------------------------
    def refresh(self):
        self.deleteItem([])
        event = Event(type_=EVENT_OPTIONAL_REQ)
        self.eventEngine.put(event)

    # ------------------------------------------
    def updateOptional(self):
        curItem = self.currentItem()
        if curItem:
            row = curItem.row()
            code = self.item(row, self.headerDict.keys().index('secId')).text()
            info = '是否更新代码 %s 的时间' % code
            reply = QtGui.QMessageBox.question(self, u'确认', unicode(info), QtGui.QMessageBox.Yes |QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                if self.dbUtils.updateOptional(code, self.loginName):
                    self.refresh()

    # ---------------------------------------------
    def modifyRemark(self):
        curItem = self.currentItem()
        if curItem:
            row = curItem.row()
            code = self.item(row, self.headerDict.keys().index('secId')).text()
            name = self.item(row, self.headerDict.keys().index('secName')).text()

            self.parent.lineSecId.setText(code)
            self.parent.lineName.setText(name)
            self.parent.remarkFlag = True

    # -------------------------------------------
    def deleteOptional(self):
        curItem = self.currentItem()
        if curItem:
            row = curItem.row()
            code = self.item(row, self.headerDict.keys().index('secId')).text()
            info = '是否删除代码 %s' % code
            reply = QtGui.QMessageBox.question(self, u'确认', unicode(info), QtGui.QMessageBox.Yes |QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                self.dbUtils.deleteOptional(code)
        self.refresh()

