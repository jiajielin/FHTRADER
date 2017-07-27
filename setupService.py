# coding=utf-8

"""
Time : 2017/2/7 14:52
Author : Jia Jielin
Company: fhhy.co
File : setupService.py
Description:

"""

from distutils.core import setup
import py2exe

options = {"py2exe":{"compressed": 1,   # 压缩
                     "optimize": 2,
                     "bundle_files": 1  # 所有文件打包成一个exe文件
                     }}

setup(console=['fhService.py'],
      options=options,
      zipfile=None)

# 执行 python setupService.py py2exe