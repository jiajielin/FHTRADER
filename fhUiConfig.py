# coding=utf-8

"""
Time : 2016/8/3 10:19
Author : Jia Jielin
Company: fhhy.co
File : fhUiConfig.py
Description:

"""

# system module

# third party module
from PyQt4 import QtGui


# own module


class ConfigTab(QtGui.QWidget):
    """"""

    def __init__(self, loginname, verifyFlag, parent=None):
        super(ConfigTab, self).__init__(parent)
        self.loginname = loginname
        self.verifyFlag = verifyFlag
        self.initUi()

    # --------------------------
    def initUi(self):
        productCfg = ProductCfgWidget(u'产品信息管理')
        staffCfg = StaffCfgWidget(u'人员信息信息')

        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(productCfg)
        mainLayout.addWidget(staffCfg)
        self.setLayout(mainLayout)

    # --------------------------
    def addAccount(self):
        pass

    # --------------------------
    def deleteAccount(self):
        pass

    # --------------------------
    def accountList(self):
        pass

    # --------------------------
    def addProduct(self):
        pass

    # --------------------------
    def deleteProduct(self):
        pass

    # --------------------------
    def producttList(self):
        pass

    # --------------------------
    def addEmployee(self):
        pass

    # --------------------------
    def deleteEmployee(self):
        pass

    # --------------------------
    def employeeList(self):
        pass


# =============================
class StaffCfgWidget(QtGui.QGroupBox):
    """"""

    def __init__(self, *args):
        super(StaffCfgWidget, self).__init__(*args)
        self.initUi()

    # -----------------------
    def initUi(self):
        pass


# =============================
class ProductCfgWidget(QtGui.QGroupBox):
    """"""

    def __init__(self, *args):
        super(ProductCfgWidget, self).__init__(*args)
        self.initUi()

    # -----------------------
    def initUi(self):
        # self.setWindowTitle(u'产品信息维护')
        pass
