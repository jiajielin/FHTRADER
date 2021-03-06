# coding=utf-8

"""
Time : 2016/9/13 9:13
Author : Jia Jielin
Company: fhhy.co
File : fhRetCode.py
Description:

"""

# system module

# third party module

# own module

# 发送类型
TYPE_UPDATE = 0
TYPE_LOGIN = 1
TYPE_LOGOUT = 2
TYPE_TASK_QUERY = 3
TYPE_TASK_ADD = 4
TYPE_TASK_MOD = 5
TYPE_REMARK_ADD = 6
TYPE_HALT_ON = 7
TYPE_HALT_OFF = 8
TYPE_ACCOUNT_QUERY = 10
TYPE_ACCOUNT_ALL = 11
TYPE_POSITION_QUERY = 12    # 查询持仓变化信息，当持仓变化时，返回True
TYPE_POSITION_ALL = 13
TPYE_UPDATE_SECVALUE = 14
TYPE_UPDATE_FUTURES_TODAY_INFO = 15
TYPE_CLOSE = 99


# 返回错误码
RETCODE_SUCCESS = 0
RETCODE_DATAPARSEERROR = -1
RETCODE_TYPEERROR = -2
RETCODE_DBDISCONNECT = -3
RETCODE_FORMATERROR = -4
RETCODE_ERROR = -5
RETCODE_AUTHORITYERROR = -6
RETCODE_DATAINCOMPLETE = -7
RETCODE_DBERROR = -8

RETCODE_TRADERWARNING = 1

# 返回类型内容
RETCODE_COMMENT = {}
RETCODE_COMMENT[RETCODE_SUCCESS] = '交易成功'
RETCODE_COMMENT[RETCODE_DATAPARSEERROR] = '接收数据解析错误'
RETCODE_COMMENT[RETCODE_TYPEERROR] = '发送类型错误'
RETCODE_COMMENT[RETCODE_FORMATERROR] = '返回格式错误'
RETCODE_COMMENT[RETCODE_ERROR] = '未知错误'
RETCODE_COMMENT[RETCODE_AUTHORITYERROR] = '权限错误'
RETCODE_COMMENT[RETCODE_DATAINCOMPLETE] = '数据不完整'
RETCODE_COMMENT[RETCODE_DBERROR] = '数据库错误'

RETCODE_COMMENT[RETCODE_TRADERWARNING] = '暂无登录交易员，已随机分配'

# 权限表