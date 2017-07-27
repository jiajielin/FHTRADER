# coding=utf-8

"""
Time : 2016/8/3 13:45
Author : Jia Jielin
Company: fhhy.co
File : fhFunc.py
Description:

"""

# system module
import decimal
# third party module
import json

# own module


MAX_NUMBER = 10000000000000
MAX_DECIMAL = 4


def safeUnicode(value):
    """检查接口数据潜在的错误，保证转化为的字符串正确"""
    if value == None:
        return unicode('')

    # 检查是数字接近0时会出现的浮点数上限
    if type(value) is int or type(value) is float:
        if value > MAX_NUMBER:
            value = 0

    # 检查防止小数点位过多
    if type(value) is float:
        d = decimal.Decimal(str(value))
        if abs(d.as_tuple().exponent) > MAX_DECIMAL:
            value = round(value, ndigits=MAX_DECIMAL)

    return unicode(value)


# -------------------------------
def loadDbSetting():
    """载入数据库配置"""
    try:
        f = file("setting.json")
        setting = json.load(f)
        f.close()
        host = setting['dbHost']
        port = setting['dbPort']
        user = setting['dbUser']
        password = setting['dbPwd']
        dbName = setting['dbName']
    except:
        host = 'localhost'
        port = 3306
        user = 'null'
        password = 'null'
        dbName = 'null'
    return host, port, user, password, dbName
