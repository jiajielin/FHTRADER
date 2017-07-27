# coding=utf-8

"""
Time : 2016/7/18 17:15
Author : Jia Jielin
Company: fhhy.co
File : fhUtils.py
Description : 本文档用于编写一些通用的函数和类

"""

# system module
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex



def getSymbolExchange(id, objectclass=0):
    """objectclass:0,证券 1,期货"""
    idSplit = id.split('.')
    if len(idSplit) == 2:
        if idSplit[1] == '':
            if objectclass == 0:
                if id[0] == '0':
                    return id + 'SZ'
                elif id[0] == '3':
                    return id + 'SZ'
                elif id[0] == '6':
                    return id + 'SH'
                else:
                    return id
            elif objectclass == 1:
                return id + 'CFE'
            else:
                return id
        else:
            return id
    elif len(idSplit) == 1:
        if objectclass == 0:
            if id[0] == '0':
                return id + '.SZ'
            elif id[0] == '3':
                return id + '.SZ'
            elif id[0] == '6':
                return id + '.SH'
            else:
                return id
        elif objectclass == 1:
            return id + '.CFE'
        else:
            return id


# -------------------------
FhKey = "fuhuihengyu12345"


class CipherUtils:
    """
    该类用于加解密，加密后输出为转换为16进制的对应字符串，解密输入亦应为16进制的对应字符串
    encrypt：会把输入按长度16分段，每段进行加密，然后组成密文。对于长度不足16的，补'\0'
    decrypt：会判断输入长度是否为16的倍数，若不是，则无法解密，若是，则按16为一段进行解密，然后组成明文，并删除后端的'\0'
    """

    def __init__(self, text, key):
        self.__key = key
        self.__text = text
        self.__textLength = len(text)
        self.__error = 0
        self.__mode = AES.MODE_CBC
        self.__isEncrypted = False
        self.__isDecrypted = False
        if self.__textLength == 0 or (len(key) != 16):
            self.__error = 1
        else:
            self.__cryptor = AES.new(self.__key, self.__mode, self.__key)
            self.__cipherText = ""
            self.__plainText = ""

        if (self.__textLength % 16) == 0:
            self.__block = divmod(self.__textLength, 16)[0]
            self.__enText = self.__text
            self.__deText = a2b_hex(self.__text)
            self.__canDecrypted = True
        else:
            self.__block = divmod(self.__textLength, 16)[0] + 1
            self.__enText = self.__text + ('\0' * (16 - (self.__textLength % 16)))
            self.__canDecrypted = False
            self.__deText = ""

    # -------------------------------
    def encrypt(self):
        if self.__error == 1:
            return self.__error
        if self.__isEncrypted:
            return self.__cipherText
        for i in range(self.__block):
            self.__cipherText = self.__cipherText + self.__cryptor.encrypt(self.__enText[16 * i:(16 * i + 16)])
        self.__isEncrypted = True
        return b2a_hex(self.__cipherText)

    # -------------------
    def decrypt(self):
        if self.__error == 1:
            return self.__error
        if self.__canDecrypted == False:
            return 1
        if self.__isDecrypted:
            return self.__plainText
        for i in range(self.__block):
            self.__plainText = self.__plainText + self.__cryptor.decrypt(self.__deText[16 * i:(16 * i + 16)])
        self.__isDecrypted = True
        return self.__plainText.rstrip('\0')


# ====================
class NumUtils:
    """数字类，目前只用数字转人民币读法
    toRmb: 转为人民币读法，输入为int、double、float、string均可，但未有对string的合法性校验
    """
    cdict = {}
    gdict = {}
    xdict = {}

    # -----------------------
    def __init__(self):
        self.cdict = {1: u'', 2: u'十', 3: u'百', 4: u'千'}
        self.xdict = {1: u'元', 2: u'万', 3: u'亿', 4: u'兆'}  # 数字标识符
        self.gdict = {0: u'零', 1: u'一', 2: u'二', 3: u'三', 4: u'四', 5: u'五', 6: u'六', 7: u'七', 8: u'八', 9: u'九'}

    # -------------------------------
    def toRmb(self, data):
        try:
            sdata = str(data)
            return self.cwchange(sdata)
        except:
            return 'Null'

    # -----------------------------------
    def csplit(self, cdata):  # 拆分函数，将整数字符串拆分成[亿，万，仟]的list
        g = len(cdata) % 4
        csdata = []
        lx = len(cdata) - 1
        if g > 0:
            csdata.append(cdata[0:g])
        k = g
        while k <= lx:
            csdata.append(cdata[k:k + 4])
            k += 4
        return csdata

    # ------------------------------------------
    def cschange(self, cki):  # 对[亿，万，仟]的list中每个字符串分组进行大写化再合并
        lenki = len(cki)
        i = 0
        lk = lenki
        chk = u''
        for i in range(lenki):
            if int(cki[i]) == 0:
                if i < lenki - 1:
                    if int(cki[i + 1]) != 0:
                        chk = chk + self.gdict[int(cki[i])]
            else:
                chk = chk + self.gdict[int(cki[i])] + self.cdict[lk]
            lk -= 1
        return chk

    # -------------------------------------------------
    def cwchange(self, data):
        cdata = str(data).split('.')
        if len(cdata) == 1:
            cki = cdata[0]
            ckj = '00'
        else:
            if cdata[1]:
                cki = cdata[0]
                ckj = cdata[1]
            else:
                cki = cdata[0]
                ckj = '00'
        i = 0
        chk = u''
        cski = self.csplit(cki)  # 分解字符数组[亿，万，仟]三组List:['0000','0000','0000']
        ikl = len(cski)  # 获取拆分后的List长度
        # 大写合并
        for i in range(ikl):
            if self.cschange(cski[i]) == '':  # 有可能一个字符串全是0的情况
                chk = chk + self.cschange(cski[i])  # 此时不需要将数字标识符引入
            else:
                chk = chk + self.cschange(cski[i]) + self.xdict[ikl - i]  # 合并：前字符串大写+当前字符串大写+标识符
        # 处理小数部分
        lenkj = len(ckj)
        if lenkj == 1:  # 若小数只有1位
            if int(ckj[0]) == 0:
                chk = chk + u'整'
            else:
                chk = chk + self.gdict[int(ckj[0])] + u'角整'
        else:  # 若小数有两位的四种情况
            if int(ckj[0]) == 0 and int(ckj[1]) != 0:
                chk = chk + u'零' + self.gdict[int(ckj[1])] + u'分'
            elif int(ckj[0]) == 0 and int(ckj[1]) == 0:
                chk = chk + u'整'
            elif int(ckj[0]) != 0 and int(ckj[1]) != 0:
                chk = chk + self.gdict[int(ckj[0])] + u'角' + self.gdict[int(ckj[1])] + u'分'
            else:
                chk = chk + self.gdict[int(ckj[0])] + u'角整'
        return chk


# ===========================
if __name__ == '__main__':
    inc = CipherUtils('admin123', FhKey)
    enc = inc.encrypt()
    print enc
    dec = CipherUtils(enc, FhKey)
    print dec.decrypt()
    pt = NumUtils()
    print pt.toRmb(190101000)
