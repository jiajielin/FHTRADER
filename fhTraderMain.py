# coding=utf-8

"""
Name : 福慧交易系统（FHTrader）
Time : 2016/7/12 14:31
Author : Jia Jielin
Company: fhhy.co
File : fhTraderMain.py
Description:该文件包含FHTrader程序主函数，用于功能导入
Version: v0.1   2016/7/12-2016/12/18

"""

# system module
import sys
import json
import locale
from fhUiMain import *
from fhUiBase import BASIC_FONT


# ----------------------
def main():
    """主程序入口"""
    # 重载sys模块，设置默认字符串编码方式为utf-8
    reload(sys)
    sys.setdefaultencoding('utf8')

    # mycode = locale.getpreferredencoding()
    # code = QTextCodec.codecForName(mycode)
    # QTextCodec.setCodecForLocale(code)
    # QTextCodec.setCodecForTr(code)
    # QTextCodec.setCodecForCStrings(code)

    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('fhIcon.ico'))
    app.setFont(BASIC_FONT)

    # 缓存，缓存应保存信息会随着程序情况包括
    # loginname：    登录名
    # verifyFlag：   用户权限
    # isDefaultSetting： 界面默认设置
    # dbUtils：      数据库操作实例
    # proudctList：  产品列表，value应为产品列表，即数组，
    # productInfo：  产品中含股票及期货信息，key应为产品名称，value是一个字典，包含key：stock,futures，value
    # productPerserving：    股票对应每份的金额
    # version：      版本
    # dataGateway：  数据接口，不包括simuGateway，有Wind，Choice可选，只可选一个
    cache = dict()
    version = 'V0.1'
    cache['version'] = version
    cache['dataGateway'] = ''
    # 登录界面
    lw = LoginWidget(cache)

    # 初始化主引擎和主窗口对象 - 更改为登录界面后
    # mainEngine = MainEngine()
    # mw = MainWindow(mainEngine, mainEngine.eventEngine)
    # mw.showMaximized()
    lw.show()
    sys.exit(app.exec_())


# ---------------------------------

if __name__ == '__main__':
    main()
