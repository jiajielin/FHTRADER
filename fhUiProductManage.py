# coding=utf-8

"""
Time : 2016/8/3 10:18
Author : Jia Jielin
Company: fhhy.co
File : fhUiProductManage.py
Description:

"""

# system module
from collections import OrderedDict
# third party module
from PyQt4 import QtGui, QtCore
# own module
from fhConstant import *
from fhUtils import *


class ProductManageTab(QtGui.QWidget):
    """产品管理界面"""

    def __init__(self, mainEngine, eventEngine, cache, parent=None):
        super(ProductManageTab, self).__init__(parent)
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
        self.productEndedList = self.getEndedList()
        self.initUi()

    # --------------------------
    def initUi(self):
        # self.setWindowTitle(title)
        # self.view = setModel(self.treeModel)
        self.tree = QtGui.QTreeWidget()
        self.tree.setMaximumWidth(300)
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels([u''])

        self.rootHome = QtGui.QTreeWidgetItem(self.tree)
        self.rootHome.setText(0, unicode(HOME_PAGE))

        self.rootOption = QtGui.QTreeWidgetItem(self.tree)
        self.rootOption.setText(0, u'产品操作')

        self.optionAdd = QtGui.QTreeWidgetItem(self.rootOption)
        self.optionAdd.setText(0, u'新建产品')
        # self.optionDelete = QtGui.QTreeWidgetItem(self.rootOption)
        # self.optionDelete.setText(0, u'删除产品')

        self.rootActive = QtGui.QTreeWidgetItem(self.tree)
        self.rootActive.setText(0, unicode(PRODUCT_ON))

        self.productActive = [QtGui.QTreeWidgetItem(self.rootActive) for product in self.productList]
        for i in range(0, len(self.productList)):
            self.productActive[i].setText(0, unicode(self.productList[i]))
        self.rootActive.setExpanded(True)

        self.rootEnd = QtGui.QTreeWidgetItem(self.tree)
        self.rootEnd.setText(0, unicode(PRODUCT_OFF))
        self.productEnded = [QtGui.QTreeWidgetItem(self.rootEnd) for product in self.productEndedList]
        for i in range(0, len(self.productEndedList)):
            self.productEnded[i].setText(0, unicode(self.productEndedList[i]))

        # print self.tree.findItems(u'新建产品',QtCore.Qt.MatchRecursive)[0].text(0)

        # self.tree.insertTopLevelItems(0, [self.rootActive, self.rootEnd, self.rootOption, self.rootHome])
        # self.tree.insertTopLevelItems(0, [self.rootActive, self.rootEnd, self.rootOption])
        # self.tree.insertTopLevelItem(0, [self.rootHome])

        # 建立双击信号连接
        self.connect(self.tree, QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*, int)"), self.onClick)

        self.infoW = InfoWidget(u'产品中心', self.mainEngine, self.eventEngine, self.cache)
        # self.productPage = ProductInfo(self.mainEngine, self.eventEngine, self.cache, option=None, product=None)

        hLayout = QtGui.QHBoxLayout()
        hLayout.addWidget(self.tree)
        hLayout.addWidget(self.infoW)
        self.setLayout(hLayout)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

    # --------------------------
    def getEndedList(self):
        productEndedInfo = self.dbUtils.getProducts(state=PRODUCT_OFF)
        productEndedList = [productEndedInfo[i][0] for i in range(0, len(productEndedInfo))]
        return productEndedList

    # -------------------------------
    def onClick(self, item, i):
        if item.childCount() == 0:
            for product in self.productList:
                if item.text(0) == unicode(product):
                    self.infoW.changeInfo(PRODUCT_VIEW, product)
            for product in self.productEndedList:
                if item.text(0) == unicode(product):
                    self.infoW.changeInfo(PRODUCT_VIEW, product)
            if item.text(0) == unicode(HOME_PAGE):
                self.infoW.changeInfo(option=None, product=None)
            elif item.text(0) == u'新建产品':
                self.infoW.changeInfo(option=PRODUCT_ADD, product=None)
            elif item.text(0) == u'删除产品':
                pass
            else:
                pass


# =============================================
class InfoWidget(QtGui.QGroupBox):
    """显示信息页面"""

    def __init__(self, name, mainEngine, eventEngine, cache):
        super(InfoWidget, self).__init__(name)
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.initUi()

    # -----------------------------------
    def initUi(self):
        self.productPage = ProductInfo(self.mainEngine, self.eventEngine, self.cache)
        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.productPage)
        self.setLayout(self.layout)
        self.changeInfo()

    # ------------------------------------
    def changeInfo(self, option=None, product=None):
        if option == None:
            self.productPage.setHidden(True)
        else:
            self.productPage.setHidden(False)
            self.productPage.changePage(option, product)


# ======================================
class ProductInfo(QtGui.QWidget):
    def __init__(self, mainEngine, eventEngine, cache, option=None, product=None):
        super(ProductInfo, self).__init__()
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.dbUtils = self.cache['dbUtils']
        self.option = option  # PRODUCT_VIEW 查看，PRODUCT_ADD,新增，PRODUCT_MOD,修改，None 无操作首页
        self.product = product

        self.fieldsAll = ['product', 'fundmanager', 'trader', 'startdate', 'finishdate', 'fundscale', 'remaindate',
                          'secratio', 'futuresratio', 'perserving', 'seccompany', 'futurescompany', 'state']
        self.mapAll = {}
        self.mapAll['product'] = u'产品名称'
        self.mapAll['fundmanager'] = u'基金经理'
        self.mapAll['trader'] = u'交易员    '
        self.mapAll['startdate'] = u'开始时间'
        self.mapAll['finishdate'] = u'结束时间'
        self.mapAll['fundscale'] = u'产品规模'
        self.mapAll['remaindate'] = u'距离结束'
        self.mapAll['futuresratio'] = u'期货比例'
        self.mapAll['perserving'] = u'每份金额'
        self.mapAll['secratio'] = u'证券比例'
        self.mapAll['seccompany'] = u'券商       '
        self.mapAll['futurescompany'] = u'期货公司'
        self.mapAll['state'] = u'状态       '

        self.stateType = OrderedDict()
        self.stateType[PRODUCT_ON] = unicode(PRODUCT_ON)
        self.stateType[PRODUCT_OFF] = unicode(PRODUCT_OFF)

        self.fieldsSec = ['secposition', 'secpositionall']

        self.mapSec = {}
        self.mapSec['secposition'] = u'股票仓位'
        self.mapSec['secpositionall'] = u'总仓位    '

        self.fieldsFutures = ['long', 'short', 'margin', 'futurespos']
        self.mapFutures = {}
        self.mapFutures['long'] = u'多   '
        self.mapFutures['short'] = u'空   '
        self.mapFutures['short'] = u'空   '
        self.mapFutures['margin'] = u'占用保证金'
        self.mapFutures['futurespos'] = u'占期货仓位'

        self.initUi()

    # -------------------------
    def initUi(self):
        # 标签显示
        labelAll = {}
        for field in self.fieldsAll:
            labelAll[field] = QtGui.QLabel(self.mapAll[field] + u':')

        labelSecName = QtGui.QLabel(u'股票信息 :')
        labelSec = {}
        for field in self.fieldsSec:
            labelSec[field] = QtGui.QLabel(self.mapSec[field].ljust(5) + u':')

        labelFuturesName = QtGui.QLabel(u'期货信息 :')
        labelFutures = {}
        for field in self.fieldsFutures:
            labelFutures[field] = QtGui.QLabel(self.mapFutures[field].ljust(5) + u':')

        # 产品编辑设置
        self.editAll = {}
        self.editAll[self.fieldsAll[0]] = QtGui.QLineEdit()  # 产品名称
        self.editAll[self.fieldsAll[1]] = QtGui.QLineEdit()  # 基金经理
        self.editAll[self.fieldsAll[2]] = QtGui.QLineEdit()  # 交易员
        self.editAll[self.fieldsAll[3]] = QtGui.QDateEdit()  # 开始时间
        self.editAll[self.fieldsAll[4]] = QtGui.QDateEdit()  # 结束时间

        self.editAll[self.fieldsAll[5]] = QtGui.QDoubleSpinBox()  # 产品规模
        self.editAll[self.fieldsAll[5]].setDecimals(0)  # 设置小数点位
        self.editAll[self.fieldsAll[5]].setMaximum(10000000000)  # 最大值
        # self.editAll[self.fieldsAll[5]].valueChanged.connect(self.getScaleChn)
        self.editAll[self.fieldsAll[5]].setSuffix(u' 万元')

        self.editAll[self.fieldsAll[6]] = QtGui.QSpinBox()  # 距离结束
        self.editAll[self.fieldsAll[6]].setMaximum(100000)

        self.editAll[self.fieldsAll[7]] = QtGui.QDoubleSpinBox()  # 证券比例
        self.editAll[self.fieldsAll[7]].setDecimals(4)  # 设置小数点位
        self.editAll[self.fieldsAll[7]].setMaximum(1)  # 设置最大值
        self.editAll[self.fieldsAll[7]].setToolTip(u'证券账户分配金额/产品总金额')

        self.editAll[self.fieldsAll[8]] = QtGui.QDoubleSpinBox()  # 期货比例
        self.editAll[self.fieldsAll[8]].setDecimals(4)  # 设置小数点位
        self.editAll[self.fieldsAll[8]].setMaximum(1)  # 设置最大值
        self.editAll[self.fieldsAll[8]].setToolTip(u'期货账户分配金额/产品总金额')

        self.editAll[self.fieldsAll[9]] = QtGui.QDoubleSpinBox()  # 每份金额
        self.editAll[self.fieldsAll[9]].setDecimals(0)  # 设置小数点位
        self.editAll[self.fieldsAll[9]].setMaximum(10000000000)  # 最大值
        # self.editAll[self.fieldsAll[9]].valueChanged.connect(self.getPerChn)
        self.editAll[self.fieldsAll[9]].setSuffix(u' 万元')

        self.editAll[self.fieldsAll[10]] = QtGui.QLineEdit()  # 券商
        self.editAll[self.fieldsAll[11]] = QtGui.QLineEdit()  # 期货公司

        self.editAll[self.fieldsAll[12]] = QtGui.QComboBox()
        self.editAll[self.fieldsAll[12]].addItems(self.stateType.values())
        # for editItem in self.editAll:
        #     self.editAll[editItem].resize(200, 50)

        for field in self.fieldsAll:
            self.editAll[field].setMaximumWidth(150)
        # self.editAll[self.fieldsAll[3]].dateChanged.connect(self.updateRemain)
        self.editAll[self.fieldsAll[4]].dateChanged.connect(self.updateRemain)

        # 证券部分编辑器设置
        self.editSec = {}
        for field in self.fieldsSec:
            self.editSec[field] = QtGui.QDoubleSpinBox()
            self.editSec[field].setReadOnly(True)
        self.editSec['secposition'].setToolTip(u'股票市值/股票账户总资产')
        self.editSec['secpositionall'].setToolTip(u'股票市值/(股票市值+期货保证金占用)')

        # 期货部分编辑器设置
        self.editFutures = {}
        self.editFutures[self.fieldsFutures[0]] = QtGui.QSpinBox()  # 多
        self.editFutures[self.fieldsFutures[1]] = QtGui.QSpinBox()  # 空
        self.editFutures[self.fieldsFutures[2]] = QtGui.QDoubleSpinBox()  # 占用保证金 setMaximum
        self.editFutures[self.fieldsFutures[2]].setMaximum(1000000000)
        self.editFutures[self.fieldsFutures[2]].setDecimals(3)  # 设置小数点位
        self.editFutures[self.fieldsFutures[3]] = QtGui.QDoubleSpinBox()  # 占期货仓位
        self.editFutures[self.fieldsFutures[3]].setToolTip(u'期货保证金占用/期货账户总资产')
        self.editFutures[self.fieldsFutures[3]].setDecimals(4)  # 设置小数点位
        for field in self.fieldsFutures:
            self.editFutures[field].setReadOnly(True)

        self.buttonAction = QtGui.QPushButton()
        if self.option == PRODUCT_VIEW:
            self.buttonAction.setText(u'修改产品信息')
            self.buttonAction.clicked.connect(self.modifyProduct)
        elif self.option == PRODUCT_ADD:
            self.buttonAction.setText(u'添加产品')
            self.buttonAction.clicked.connect(self.addProduct)
        elif self.option == PRODUCT_MOD:
            self.buttonAction.setText(u'确认修改信息')
            self.buttonAction.clicked.connect(self.modifyProduct)

        # 布局
        # 产品信息布局
        layoutAll = QtGui.QGridLayout()
        layoutAllList = {}
        for field in self.fieldsAll:
            layoutAllList[field] = QtGui.QHBoxLayout()
            layoutAllList[field].addWidget(labelAll[field])
            layoutAllList[field].addWidget(self.editAll[field])
            layoutAllList[field].addStretch(10)
        # 增加汉字显示
        # self.labelScale = QtGui.QLabel()
        # self.labelScale.setAlignment(QtCore.Qt.AlignLeft)
        # layoutAllList['fundscale'].addWidget(self.labelScale)
        # layoutAllList['fundscale'].addStretch(10)
        # self.labelPer = QtGui.QLabel()
        # self.labelScale.setAlignment(QtCore.Qt.AlignLeft)
        # layoutAllList['perserving'].addWidget(self.labelPer)
        # layoutAllList['perserving'].addStretch(10)
        layoutAll.addLayout(layoutAllList[self.fieldsAll[0]], 0, 0)
        for i in range(1, len(self.fieldsAll)):
            layoutAll.addLayout(layoutAllList[self.fieldsAll[i]], (i - 1) / 4 + 1, (i - 1) % 4)

        # 股票信息布局
        layoutSec = QtGui.QGridLayout()
        layoutSecList = {}
        for field in self.fieldsSec:
            layoutSecList[field] = QtGui.QHBoxLayout()
            layoutSecList[field].addWidget(labelSec[field])
            layoutSecList[field].addWidget(self.editSec[field])
            layoutSecList[field].addStretch(10)
        layoutSec.addWidget(labelSecName, 0, 0)
        for i in range(0, len(self.fieldsSec)):
            layoutSec.addLayout(layoutSecList[self.fieldsSec[i]], i / 4 + 1, i % 4)

        # 期货信息布局
        layoutFutures = QtGui.QGridLayout()
        layoutFuturesList = {}
        for field in self.fieldsFutures:
            layoutFuturesList[field] = QtGui.QHBoxLayout()
            layoutFuturesList[field].addWidget(labelFutures[field])
            layoutFuturesList[field].addWidget(self.editFutures[field])
            layoutFuturesList[field].addStretch(10)
        layoutFutures.addWidget(labelFuturesName, 0, 0)
        for i in range(0, len(self.fieldsFutures)):
            layoutFutures.addLayout(layoutFuturesList[self.fieldsFutures[i]], i / 4 + 1, i % 4)

        self.button = QtGui.QPushButton(u'修改产品信息')
        self.button.setMaximumSize(100, 50)
        # self.button.setGeometry(-100, -100, 80, 40)

        layoutAll.setSpacing(10)
        layoutSec.setSpacing(10)
        layoutFutures.setSpacing(10)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(layoutAll)
        layout.addLayout(layoutSec)
        layout.addLayout(layoutFutures)
        layout.setSpacing(50)

        layoutButton = QtGui.QVBoxLayout()
        layoutButton.addLayout(layout)
        layoutButton.addWidget(self.button)
        layoutButton.setSpacing(100)
        # layout.addWidget(self.button)
        layoutButton.addStretch()
        self.setLayout(layoutButton)
        self.button.clicked.connect(self.onClick)

        self.changePage(self.option, self.product)

    # --------------------------------------
    def changePage(self, option, product):
        self.option = option
        self.product = product
        if self.option == None:
            pass
        elif self.option == PRODUCT_ADD:
            for i in range(0, len(self.fieldsAll) - 1):
                self.editAll[self.fieldsAll[i]].setReadOnly(False)
            self.editAll[self.fieldsAll[10]].setEnabled(True)
            self.button.setText(u'添加产品')
        elif self.option == PRODUCT_MOD:
            for i in range(1, len(self.fieldsAll) - 1):
                self.editAll[self.fieldsAll[i]].setReadOnly(False)
            self.editAll[self.fieldsAll[10]].setEnabled(True)
            self.button.setText(u'确认修改信息')
        elif self.option == PRODUCT_VIEW:
            for i in range(0, len(self.fieldsAll) - 1):
                self.editAll[self.fieldsAll[i]].setReadOnly(True)
            self.editAll[self.fieldsAll[10]].setEnabled(False)
            self.button.setText(u'修改产品信息')
        else:
            for i in range(0, len(self.fieldsAll) - 1):
                self.editAll[self.fieldsAll[i]].setReadOnly(True)
            self.editAll[self.fieldsAll[10]].setEnabled(False)

        self.showData()

    # -------------------------------
    def onClick(self):
        if self.option == PRODUCT_ADD:
            if self.addProduct():
                self.changePage(PRODUCT_VIEW, self.product)
        elif self.option == PRODUCT_MOD:
            self.modifyProduct()
            self.changePage(PRODUCT_VIEW, self.product)
        elif self.option == PRODUCT_VIEW:
            self.changePage(PRODUCT_MOD, self.product)
        else:
            pass

    # ----------------------------
    def modifyProduct(self):
        if self.option == PRODUCT_VIEW:
            for field in self.fieldsAll:
                self.editAll[field].setReadOnly(False)
            self.buttonAction.setText(u'确认修改信息')
            self.option = PRODUCT_MOD
        elif self.option == PRODUCT_MOD:
            productBuffer = {}
            productBuffer[0] = str(self.editAll[self.fieldsAll[0]].text())  # 产品名称
            productBuffer[1] = str(self.editAll[self.fieldsAll[1]].text())  # 基金经理
            productBuffer[2] = str(self.editAll[self.fieldsAll[2]].text())  # 交易员
            productBuffer[3] = str(self.editAll[self.fieldsAll[3]].date().toString(QtCore.Qt.ISODate))  # 开始时间
            productBuffer[4] = str(self.editAll[self.fieldsAll[4]].date().toString(QtCore.Qt.ISODate))  # 结束时间
            productBuffer[5] = str(10000*self.editAll[self.fieldsAll[5]].value())  # 产品规模
            productBuffer[6] = str(self.editAll[self.fieldsAll[7]].value())  # 证券比例
            productBuffer[7] = str(self.editAll[self.fieldsAll[8]].value())  # 期货比例
            productBuffer[8] = str(10000*self.editAll[self.fieldsAll[9]].value())  # 每份金额
            productBuffer[9] = str(self.editAll[self.fieldsAll[10]].text())  # 券商
            productBuffer[10] = str(self.editAll[self.fieldsAll[11]].text())  # 期货公司
            productBuffer[11] = str(self.editAll[self.fieldsAll[12]].currentText())  # 每份金额

            try:
                if (float(productBuffer[6]) + float(productBuffer[7])) >= 1.0001 or (float(productBuffer[6]) + float(productBuffer[7])) <= 0.9999:
                    QtGui.QMessageBox.warning(self, u'提示', u'证券期货比例错误，请重新设置，修改失败')
                    return 0
            except:
                QtGui.QMessageBox.warning(self, u'提示', u'证券期货比例错误，请重新设置，修改失败')
                return 0

            if self.dbUtils.updateProduct(productBuffer):
                QtGui.QMessageBox.warning(self, u'提示', u'修改成功')
                return 1
            else:
                QtGui.QMessageBox.warning(self, u'提示', u'修改失败')
                return 0
        else:
            pass

    # ------------------------------
    def addProduct(self):
        if self.option == PRODUCT_VIEW:
            for field in self.fieldsAll:
                self.editAll[field].setReadOnly(False)
            self.buttonAction.setText(u'确认修改信息')
            self.option = PRODUCT_MOD
        elif self.option == PRODUCT_ADD:
            productBuffer = {}
            productBuffer[0] = str(self.editAll[self.fieldsAll[0]].text())  # 产品名称
            productBuffer[1] = str(self.editAll[self.fieldsAll[1]].text())  # 基金经理
            productBuffer[2] = str(self.editAll[self.fieldsAll[2]].text())  # 交易员
            productBuffer[3] = str(self.editAll[self.fieldsAll[3]].date().toString(QtCore.Qt.ISODate))  # 开始时间
            productBuffer[4] = str(self.editAll[self.fieldsAll[4]].date().toString(QtCore.Qt.ISODate))  # 结束时间
            productBuffer[5] = str(10000*self.editAll[self.fieldsAll[5]].value())  # 产品规模
            # productBuffer[6] = ''
            productBuffer[6] = str(self.editAll[self.fieldsAll[7]].value())  # 证券比例
            productBuffer[7] = str(self.editAll[self.fieldsAll[8]].value())  # 期货比例
            productBuffer[8] = str(10000*self.editAll[self.fieldsAll[9]].value())  # 每份金额
            productBuffer[9] = str(self.editAll[self.fieldsAll[10]].text())  # 券商
            productBuffer[10] = str(self.editAll[self.fieldsAll[11]].text())  # 期货公司
            productBuffer[11] = str(self.editAll[self.fieldsAll[12]].currentText())  # 运作状态
            productAccount = {}
            productAccount['product'] = str(self.editAll[self.fieldsAll[0]].text())
            productAccount['total'] = 10000.0 * self.editAll[self.fieldsAll[5]].value()
            productAccount['secRatio'] = self.editAll[self.fieldsAll[7]].value()
            productAccount['futuresRatio'] = self.editAll[self.fieldsAll[8]].value()
            try:
                secRatio = float(productBuffer[6])
                futuresRatio = float(productBuffer[7])
                if (secRatio + futuresRatio) >= 1.0001 or (secRatio + futuresRatio) <= 0.9999:
                    QtGui.QMessageBox.warning(self, u'提示', u'证券期货比例错误，请重新设置，新建失败')
                    return 0
            except:
                QtGui.QMessageBox.warning(self, u'提示', u'证券期货比例获取失败，请重新设置，新建失败')
                return 0
            if self.dbUtils.saveProduct(productBuffer):
                if self.dbUtils.addAccount(productAccount):
                    QtGui.QMessageBox.warning(self, u'提示', u'新建成功')
                else:
                    QtGui.QMessageBox.warning(self, u'提示', u'新建数据成功，创建账户信息失败，请手工创建')
                return 1
            else:
                QtGui.QMessageBox.warning(self, u'提示', u'新建失败')
                return 0
        else:
            pass

    # ------------------------------
    def deleteProduct(self):
        if self.product:
            return self.dbUtils.deleteProduct(self.product)
        return 0

    # ------------------------
    def showData(self):
        if self.product != None:
            if self.option == PRODUCT_ADD:
                self.editAll[self.fieldsAll[0]].setText('')  # 产品名称
                self.editAll[self.fieldsAll[1]].setText('')  # 基金经理
                self.editAll[self.fieldsAll[2]].setText('')  # 交易员
                self.editAll[self.fieldsAll[3]].setDate(QtCore.QDate(2001, 1, 1))  # 开始时间
                self.editAll[self.fieldsAll[4]].setDate(QtCore.QDate(2099, 1, 1))  # 结束时间

                self.editAll[self.fieldsAll[5]].setValue(0)  # 产品规模

                self.editAll[self.fieldsAll[6]].setValue(self.editAll[self.fieldsAll[
                    4]].date().toJulianDay() - QtCore.QDate.currentDate().toJulianDay())  # 距离结束

                self.editAll[self.fieldsAll[7]].setValue(0.00)  # 证券比例

                self.editAll[self.fieldsAll[8]].setValue(0.00)  # 期货比例

                self.editAll[self.fieldsAll[9]].setValue(0)  # 每份金额位

                self.editAll[self.fieldsAll[10]].setText('')    # 证券公司
                self.editAll[self.fieldsAll[11]].setText('')    # 期货公司

            elif self.option == PRODUCT_VIEW:
                productInfo = self.dbUtils.getProductInfo(self.product)
                accountInfo = self.dbUtils.getAccountInfo(self.product)
                futuresInfo = self.dbUtils.getFuturesPositionInfo(self.product)

                # info = {}
                # for i in range(0, len(self.fieldsAll)):
                #     info[self.fieldsAll[i]] = productInfo[i]
                self.editAll[self.fieldsAll[0]].setText(unicode(productInfo[0]))  # 产品名称
                self.editAll[self.fieldsAll[1]].setText(unicode(productInfo[1]))  # 基金经理
                self.editAll[self.fieldsAll[2]].setText(unicode(productInfo[2]))  # 交易员
                self.editAll[self.fieldsAll[3]].setDate(productInfo[3])  # 开始时间
                self.editAll[self.fieldsAll[4]].setDate(productInfo[4])  # 结束时间
                self.editAll[self.fieldsAll[5]].setValue(productInfo[5]/10000)  # 产品规模
                self.editAll[self.fieldsAll[6]].setValue(self.editAll[self.fieldsAll[
                    4]].date().toJulianDay() - QtCore.QDate.currentDate().toJulianDay())  # 距离结束
                self.editAll[self.fieldsAll[7]].setValue(productInfo[6])  # 证券比例
                self.editAll[self.fieldsAll[8]].setValue(productInfo[7])  # 期货比例
                self.editAll[self.fieldsAll[9]].setValue(productInfo[8]/10000)  # 每份金额位
                self.editAll[self.fieldsAll[10]].setText(unicode(productInfo[9]))    # 证券公司
                self.editAll[self.fieldsAll[11]].setText(unicode(productInfo[10]))    # 期货公司
                for i in range(0, len(self.stateType.values())):
                    if self.stateType.values()[i] == productInfo[11]:
                        self.editAll[self.fieldsAll[12]].setCurrentIndex(i)

                for i in range(0, len(self.editSec)):
                    self.editSec[self.fieldsSec[i]].setValue(0.0)

                for i in range(0, len(self.editFutures)):
                    self.editFutures[self.fieldsFutures[i]].setValue(0.0)

                if 'sec' in accountInfo:
                    if 'secValue' in accountInfo['sec'] and 'total' in accountInfo['sec']:
                        secValue = accountInfo['sec']['secValue']
                        total = accountInfo['sec']['total']
                        if total > 0.0:
                            ratio = secValue / total
                            self.editSec[self.fieldsSec[0]].setValue(ratio)
                        if 'futures' in accountInfo:
                            if 'margin' in accountInfo['futures']:
                                margin = accountInfo['futures']['margin']
                                if secValue + margin > 0.0:
                                    ratio = secValue / (secValue + margin)
                                    self.editSec[self.fieldsSec[1]].setValue(ratio)

                # 期货部分编辑器
                if TRADE_BUY in futuresInfo:
                    self.editFutures[self.fieldsFutures[0]].setValue(futuresInfo[TRADE_BUY])
                if TRADE_SELL in futuresInfo:
                    self.editFutures[self.fieldsFutures[1]].setValue(futuresInfo[TRADE_SELL])
                if 'futures' in accountInfo:
                    if 'margin' in accountInfo['futures']:
                        margin = accountInfo['futures']['margin']
                        self.editFutures[self.fieldsFutures[2]].setValue(margin)
                        if 'total' in accountInfo['futures']:
                            total = accountInfo['futures']['total']
                            if total != 0.0:
                                ratio = margin / total
                                self.editFutures[self.fieldsFutures[3]].setValue(ratio)

        else:
            self.editAll[self.fieldsAll[0]].setText('')  # 产品名称
            self.editAll[self.fieldsAll[1]].setText('')  # 基金经理
            self.editAll[self.fieldsAll[2]].setText('')  # 交易员
            self.editAll[self.fieldsAll[3]].setDate(QtCore.QDate(2001, 1, 1))  # 开始时间
            self.editAll[self.fieldsAll[4]].setDate(QtCore.QDate(2099, 1, 1))  # 结束时间

            self.editAll[self.fieldsAll[5]].setValue(0)  # 产品规模

            self.editAll[self.fieldsAll[6]].setValue(
                self.editAll[self.fieldsAll[4]].date().toJulianDay() - QtCore.QDate.currentDate().toJulianDay())  # 距离结束

            self.editAll[self.fieldsAll[7]].setValue(0.00)  # 证券比例
            self.editAll[self.fieldsAll[8]].setValue(0.00)  # 期货比例
            self.editAll[self.fieldsAll[9]].setValue(0)  # 每份金额位
            self.editAll[self.fieldsAll[10]].setText('')    # 证券公司
            self.editAll[self.fieldsAll[11]].setText('')    # 期货公司

    # ----------------------
    def updateRemain(self):
        self.editAll[self.fieldsAll[6]].setValue(
            self.editAll[self.fieldsAll[4]].date().toJulianDay() - QtCore.QDate.currentDate().toJulianDay())

    # ------------------------
    # def getScaleChn(self):
    #     self.labelScale.setText(NumUtils().toRmb(self.editAll[self.fieldsAll[5]].value()))
    #     # self.editAll[self.fieldsAll[5]].setToolTip(NumUtils().toRmb(self.editAll[self.fieldsAll[5]].value()))

    # -----------------------
    # def getPerChn(self):
    #     self.labelPer.setText(NumUtils().toRmb(self.editAll[self.fieldsAll[9]].value()))
    #     # self.editAll[self.fieldsAll[9]].setToolTip(NumUtils().toRmb(self.editAll[self.fieldsAll[9]].value()))
