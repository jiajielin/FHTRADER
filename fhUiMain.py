# coding=utf-8

"""
Time : 2016/7/15 15:16
Author : Jia Jielin
Company: fhhy.co
File : fhUiMain.py
Description:本

"""

# system module
from __future__ import division
import psutil

# third party module

# own module
from fhUiTrade import TradeTab
from fhUiProductManage import ProductManageTab
from fhUtils import *
from fhDb import DbUtils
from fhMainEngine import MainEngine
from fhUiBase import *
from fhUiOptional import *
from fhUiOptional import *
import qdarkstyle


# =============================
class MainWindow(QtGui.QMainWindow):
    def __init__(self, mainEngine, eventEngine, cache):
        super(MainWindow, self).__init__()

        self.mainEngine = mainEngine
        self.eventEngine = eventEngine
        self.cache = cache
        self.loginName = cache['loginName']
        self.encPwd = cache['encPwd']
        self.verifyFlag = cache['verifyFlag']
        self.isDefaultSetting = cache['isDefaultSetting']
        self.cache['productRatio'] = loadProductRatio()  # todo loadProductRatio()需重写
        self.dbUtils = DbUtils(self.eventEngine, isLog=True)
        self.cache['dbUtils'] = self.dbUtils

        productInfo = self.dbUtils.getProducts()
        self.productList = [productInfo[i][0] for i in range(0, len(productInfo))]
        self.productPerserving = {self.productList[i] : productInfo[i][1] for i in range(0, len(productInfo))}
        self.cache['productList'] = self.productList
        self.cache['productPerserving'] = self.productPerserving

        # 记录打开的Widget
        self.widgetDict = {}

        self.initUi()
        # if self.isDefaultSetting == False:
        #     self.loadWindowSettings()

    # ------------------------------
    def initUi(self):
        # 设置名称
        # self.setGeometry(200,200,1000,800)
        self.initSize()
        if self.verifyFlag == VERIFY_FUNDMANAGER or self.verifyFlag == VERIFY_TRADER or self.verifyFlag == VERIFY_INVESTMANAGER:
            self.setWindowTitle(unicode(VERIFY_COMMENT[self.verifyFlag]))
        # elif self.verifyFlag == VERIFY_TRADER:
        #     self.setWindowTitle(unicode(VERIFY_COMMENT[VERIFY_TRADER]))
        # elif self.verifyFlag == VERIFY_INVESTMANAGER:
        #     self.setWindowTitle(unicode(VERIFY_COMMENT[VERIFY_INVESTMANAGER]))
        else:
            self.setWindowTitle(u'欢迎使用FHTrader')
        self.initCentral()
        self.initMenu()
        self.initStatusBar()

    # ------------------------
    def initSize(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(screen.width() / 8, screen.height() / 8, 3 * screen.width() / 4, 3 * screen.height() / 4)

    # ---------------------------
    def initCentral(self):
        self.tabWidget = QtGui.QTabWidget()
        # 显示QTabWidget必须
        self.setCentralWidget(self.tabWidget)
        self.tabNum = 0
        # 权限控制
        if self.verifyFlag == VERIFY_ADMIN or self.verifyFlag == VERIFY_INVESTMANAGER or self.verifyFlag == VERIFY_FUNDMANAGER:  # 管理员、投资总监及基金经理权限
            self.tabWidget.addTab(ProductManageTab(self.mainEngine, self.eventEngine, self.cache), u"产品管理")
            self.tabWidget.addTab(TradeTab(self.mainEngine, self.eventEngine, self.cache, 0), u"证券交易")
            self.tabWidget.addTab(TradeTab(self.mainEngine, self.eventEngine, self.cache, 1), u"期货交易")
            self.tabWidget.setCurrentIndex(1)  # 默认证券交易放在最前
            self.optionalTab = OptionalTab(self.mainEngine, self.eventEngine, self.cache)
            self.tabWidget.addTab(self.optionalTab, u"自选股")
            self.optionalNum = 3
            # self.tabWidget.addTab(DataCentreTab(self.mainEngine, self.eventEngine, self.cache), u"数据中心")
            # self.tabWidget.addTab(ConfigTab(self.loginname, self.verifyFlag), u"系统管理")
            # 显示QTabWidget必须
            self.setCentralWidget(self.tabWidget)
            self.tabNum = self.tabWidget.count()

        elif self.verifyFlag == VERIFY_TRADER:  # 交易员权限控制
            self.tabWidget.addTab(ProductManageTab(self.mainEngine, self.eventEngine, self.cache), u"产品管理")
            self.tabWidget.addTab(TradeTab(self.mainEngine, self.eventEngine, self.cache, 2), u"下单任务")
            self.tabWidget.addTab(TradeTab(self.mainEngine, self.eventEngine, self.cache, 3), u"已撤销")
            self.tabWidget.setCurrentIndex(1)  # 默认下单任务放在最前
            self.optionalTab = OptionalTab(self.mainEngine, self.eventEngine, self.cache)
            self.tabWidget.addTab(self.optionalTab, u"自选股")
            self.optionalNum = 3
            # self.tabWidget.addTab(DataCentreTab(self.mainEngine, self.eventEngine, self.cache), u"数据中心")
            # self.tabWidget.addTab(ConfigTab(self.loginname, self.verifyFlag), u"系统管理")
            # 显示QTabWidget必须
            self.setCentralWidget(self.tabWidget)
            self.tabNum = self.tabWidget.count()
        # elif self.verifyFlag == VERIFY_DATAMANAGER:     # 数据管理员权限
        #     self.tabWidget.removeTab(1)
        else:  # 其他人员全删
            for i in range(0, self.tabNum):
                self.tabWidget.removeTab(self.tabNum-i-1)

        self.tabWidget.currentChanged.connect(self.tabChanged)

    # ----------------------------
    def initStatusBar(self):
        self.statusLabel = QtGui.QLabel()
        self.statusLabel.setAlignment(QtCore.Qt.AlignLeft)

        self.statusBar().addPermanentWidget(self.statusLabel)
        self.statusLabel.setText(self.getCpuMemory())

        self.sbCount = 0
        self.sbTrigger = 10  # 10秒刷新一次
        # self.eventEngine.register(EVENT_TIMER, self.updateSt)

    # ---------------------------------------------
    def tabChanged(self):
        if self.optionalNum == self.tabWidget.currentIndex():
            self.optionalTab.refresh()

    # -----------------------------------------------
    def updateStatusBar(self):
        """状态栏更新信息"""
        self.sbCount += 1
        if self.sbCount == self.sbTrigger:
            self.sbCount = 0
            self.statusLabel.setText(self.getCpuMemory)

    # ------------------------------
    def getCpuMemory(self):
        cpuPercent = psutil.cpu_percent()
        memoryPercent = psutil.virtual_memory().percent
        return u'CPU使用率：%d%%  内存使用率：%d%%' % (cpuPercent, memoryPercent)

    # ----------------------------------------
    def initMenu(self):
        # 设置菜单栏
        actionChoice = QtGui.QAction(u'连接Choice', self)
        actionChoice.triggered.connect(self.connectChoice)
        actionWind = QtGui.QAction(u'连接Wind', self)
        actionWind.triggered.connect(self.connectWind)
        actionTask = QtGui.QAction(u'开启任务监控',self)
        actionTask.triggered.connect(self.connectTask)
        actionCancelTask = QtGui.QAction(u'关闭任务监控',self)
        actionCancelTask.triggered.connect(self.cancelTask)
        actionExit = QtGui.QAction(u'退出', self)
        actionExit.triggered.connect(self.close)
        actionAbout = QtGui.QAction(u'关于', self)
        actionAbout.triggered.connect(self.openAboutWidget)

        menubar = self.menuBar()
        sysMenu = menubar.addMenu(u'系统')
        if 'Choice' in self.mainEngine.gatewayDict:
            sysMenu.addAction(actionChoice)
        if 'Wind' in self.mainEngine.gatewayDict:
            sysMenu.addAction(actionWind)
            self.connectWind()
        if 'Simu' in self.mainEngine.gatewayDict:
            sysMenu.addAction(actionTask)
            sysMenu.addAction(actionCancelTask)
            self.connectTask()
        sysMenu.addSeparator()
        sysMenu.addAction(actionExit)
        helpMenu = menubar.addMenu(u'帮助')
        helpMenu.addAction(actionAbout)

    # ----------------------------------------
    def loadWindowSettings(self):
        settings = QtCore.QSettings('fhhy.co', 'FHTrader')
        self.restoreState(settings.value('state').toByteArray())
        self.restoreGeometry(settings.value('geometry').toByteArrya())

    # -------------------------------
    def saveWindowSettings(self):
        """保存窗口设置"""
        settings = QtCore.QSettings('fhhy.co', 'FHTrader')
        settings.setValue('state', self.saveState())
        settings.setValue('geometry', self.saveGeometry())

    # --------------------------------
    def closeEvent(self, event):
        """关闭事件"""
        reply = QtGui.QMessageBox.question(self, u'退出',
                                           u'确认退出?', QtGui.QMessageBox.Yes |
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            for widget in self.widgetDict.values():
                widget.close()
            self.saveWindowSettings()

            self.mainEngine.exit()
            event.accept()
        else:
            event.ignore()

    # -------------------------------------
    def connectWind(self):
        """连接Wind接口"""
        if self.cache['dataGateway']:
            if self.cache['dataGateway'] != 'Wind':
                self.mainEngine.close(self.cache['dataGateway'])
                self.mainEngine.connect('Wind')
                self.cache['dataGateway'] = 'Wind'
            else:
                if self.mainEngine.isConnected('Wind'):
                    pass
                else:
                    self.mainEngine.connect('Wind')
        else:
            self.mainEngine.connect('Wind')
            self.cache['dataGateway'] = 'Wind'

    # -------------------------------------
    def connectChoice(self):
        """连接Wind接口"""
        if self.cache['dataGateway']:
            if self.cache['dataGateway'] != 'Choice':
                self.mainEngine.close(self.cache['dataGateway'])
                self.mainEngine.connect('Choice')
                self.cache['dataGateway'] = 'Choice'
            else:
                if self.mainEngine.isConnected('Choice'):
                    pass
                else:
                    self.mainEngine.connect('Choice')
        else:
            self.mainEngine.connect('Choice')
            self.cache['dataGateway'] = 'Choice'

    # ------------------------------------------
    def connectTask(self):
        """连接公司服务器接口"""
        self.mainEngine.login('Simu', self.loginName, self.encPwd)
        self.mainEngine.connect('Simu')

    # ---------------------------------------------
    def cancelTask(self):
        """连接公司服务器接口"""
        # self.mainEngine.logout('Simu', self.loginName, self.encPwd)
        self.mainEngine.disconnect('Simu')

    # ------------------------------------------
    def openAboutWidget(self):
        """"""
        try:
            self.widgetDict['aboutW'].show()
        except KeyError:
            self.widgetDict['aboutW'] = AboutWidget(self)
            self.widgetDict['aboutW'].show()


# =====================================
class AboutWidget(QtGui.QDialog):
    """显示关于信息"""

    def __init__(self, parent):
        """Constructor"""
        super(AboutWidget, self).__init__(parent)
        self.parent = parent
        self.initUi()

    # ----------------------------------------------------------------------
    def initUi(self):
        """"""
        self.setWindowTitle(u'关于')

        text = u"""
            福慧交易系统：FHTrader

            完成日期：

            作者：福慧恒裕金工组

            主页：福慧恒裕.cn

            版本：%s


            开发环境：

            操作系统：Windows 7 专业版 64位

            Python发行版：Python 2.7.6 (Anaconda 1.9.2 Win-32)

            图形库：PyQt4 4.11.3 Py2.7-x32
            """ % self.parent.cache['version']

        label = QtGui.QLabel()
        label.setText(text)
        label.setMinimumWidth(450)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(label)

        self.setLayout(vbox)


# ===============================
class LoginWidget(QtGui.QDialog):
    """登录界面，用于登录本公司系统，进入主页面前验证"""
    settingList = [SETTING_DEFAUlT,
                   SETTING_MYSELF]

    def __init__(self, cache, parent=None):
        super(LoginWidget, self).__init__()
        self.cache = cache
        self.initUi()

    # -----------------------
    def initUi(self):
        self.setWindowTitle(u'登录')
        # 设置组件
        labelUserId = QtGui.QLabel(u'用户')
        labelPassword = QtGui.QLabel(u'密码')
        labelSetting = QtGui.QLabel(u'界面')

        self.editUserId = QtGui.QLineEdit()
        self.editPassword = QtGui.QLineEdit()
        self.editPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.comboSetting = QtGui.QComboBox()
        self.comboSetting.addItems(self.settingList)

        self.editUserId.setMinimumWidth(220)

        buttonLogin = QtGui.QPushButton(u'登录')
        buttonCancel = QtGui.QPushButton(u'退出')
        buttonLogin.clicked.connect(self.login)
        buttonCancel.clicked.connect(self.close)

        # 设置布局
        buttonHBox = QtGui.QHBoxLayout()
        buttonHBox.addStretch()
        buttonHBox.addWidget(buttonLogin)
        buttonHBox.addWidget(buttonCancel)

        grid = QtGui.QGridLayout()
        grid.addWidget(labelUserId, 0, 0)
        grid.addWidget(labelPassword, 1, 0)
        grid.addWidget(labelSetting, 2, 0)
        grid.addWidget(self.editUserId, 0, 1)
        grid.addWidget(self.editPassword, 1, 1)
        grid.addWidget(self.comboSetting, 2, 1)

        grid.addLayout(buttonHBox, 3, 0, 1, 2)

        self.setLayout(grid)

        # self.login()

    # --------------------------------
    def login(self):
        """登录操作"""
        loginName = str(self.editUserId.text())
        password = str(self.editPassword.text())
        setting = self.comboSetting.currentIndex()
        if setting == 0:
            isDefaultSetting = True
        else:
            isDefaultSetting = False

        verifyFlag = self.userVerify(loginName, password)

        # 调试代码，调试完成后需注释掉
        # loginName = 'quli'
        # verifyFlag = VERIFY_FUNDMANAGER

        if verifyFlag == VERIFY_ADMIN or verifyFlag == VERIFY_FUNDMANAGER or verifyFlag == VERIFY_TRADER or verifyFlag == VERIFY_DATAMANAGER or verifyFlag == VERIFY_INVESTMANAGER:
            self.cache['loginName'] = loginName
            self.cache['verifyFlag'] = verifyFlag
            inc = CipherUtils(password, FhKey)
            encPwd = inc.encrypt()
            self.cache['encPwd'] = encPwd
            self.cache['isDefaultSetting'] = isDefaultSetting
            self.openMainWindow()
            self.close()
        elif verifyFlag == VERIFY_NOUSER:
            QtGui.QMessageBox.warning(self, u'信息提示', u'用户名或密码错误')
        elif verifyFlag == DB_DISCONNECT:
            QtGui.QMessageBox.warning(self, u'信息提示', u'数据库连接失败')
        else:
            QtGui.QMessageBox.warning(self, u'信息提示', u'未知错误')

    # ---------------------------------
    def userVerify(self, loginName, password):
        inc = CipherUtils(password, FhKey)
        encPwd = inc.encrypt()
        dbUtils = DbUtils()
        if dbUtils.isConnected():
            return dbUtils.getUserVerify(loginName, encPwd)
        else:
            QtGui.QMessageBox.warning(self, u'信息提示', u'数据库连接失败')

    # -------------------------------------
    def openMainWindow(self):
        mainEngine = MainEngine()
        self.mw = MainWindow(mainEngine, mainEngine.eventEngine, self.cache)
        if self.cache['isDefaultSetting'] == False:
            self.mw.setStyleSheet(qdarkstyle.load_stylesheet(pyside=False))

        self.mw.showMaximized()
