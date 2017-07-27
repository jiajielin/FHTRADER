# coding=utf-8

"""
Time : 2016/9/19 9:57
Author : Jia Jielin
Company: fhhy.co
File : fhStopServer.py
Description:

"""

# system module
import socket
import json
import getpass
# third party module
# own module
from fhRetCode import *
from fhConstant import *
from fhUtils import *

if __name__ == '__main__':
    print u'停止服务脚本'
    print u''
    try:
        f = file("setting.json")
        setting = json.load(f)
        f.close()
        host = setting['host']
        port = setting['port']
        bufSize = setting['bufSize']
        initFlag = True
        print u'加载配置文件成功'
    except:
        host = 'localhost'
        port = 3333
        bufSize = 1024
        print u'加载配置文件失败'

    continueNum = 1
    connectFlag = False
    while(continueNum):
        # user = raw_input('user:')
        # pwd = getpass.getpass("password:")
        user = 'admin'
        pwd = 'admin123'
        inc = CipherUtils(pwd, FhKey)
        encPwd = inc.encrypt()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.connect((host, port))
            connectFlag = True
        except:
            print u'未能连接到相应server，请检查server是否开启或配置文件是否正确'
            break

        if connectFlag:

            loginDict = {}
            loginDict['user'] = user
            loginDict['transType'] = TYPE_LOGIN
            loginDict['transData'] = {}
            loginDict['transData']['user'] = user
            loginDict['transData']['encPwd'] = encPwd
            loginStr = repr(loginDict)

            sock.send(loginStr)

            szBuf = sock.recv(bufSize)

            sock.close()
            parseFlag = False
            try:
                szDict = eval(szBuf)
                parseFlag = True
            except:
                print u'返回数据解析错误'

            if parseFlag:
                try:
                    retCode = szDict['retCode']

                    if retCode != RETCODE_SUCCESS:
                        print u'返回错误，错误码：'+str(retCode)
                        continueNum -= 1
                        continue
                    try:
                        verifyFlag = szDict['data']['verifyFlag']
                        if verifyFlag != VERIFY_NOUSER:
                            break
                        else:
                            continueNum -= 1
                            print u'用户名或密码不正确'
                            continue
                    except:
                        print u'返回数据解析错误，无verifyFlag'
                        continueNum -= 1
                        continue

                except:
                    parseFlag = False
                    continueNum -= 1
                    print u'返回数据解析错误，无retCode'

    if connectFlag and connectFlag:
        stopDict = {}
        stopDict['user'] = user
        stopDict['transType'] = TYPE_CLOSE
        stopDict['transData'] = {}
        stopStr = repr(stopDict)
        if parseFlag:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.send(stopStr)
            sock.close()
    # if continueNum == 0:
    #     print u'错误次数过多，请稍后重试'
    # raw_input('Please press ENTER to continue...')

