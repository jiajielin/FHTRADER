# coding=utf-8

"""
Time : 2016/11/15 9:04
Author : Jia Jielin
Company: fhhy.co
File : setup.py
Description:
涉及matplotlib打包，参考 http://www.py2exe.org/index.cgi/MatPlotLib
"""


from distutils.core import setup
import py2exe
import sys
import matplotlib
import matplotlib.backends.backend_tkagg
import FileDialog
import numpy
import os

# sys.path.append(r'D:\Program Files\Microsoft Visual Studio 11.0\VC\redist\x86\Microsoft.VC110.CRT')
sys.argv.append('py2exe')

paths = set()
np_path = numpy.__path__[0]
for dirpath, _, filenames in os.walk(np_path):
    for item in filenames:
        if item.endswith('.dll'):
            paths.add(dirpath)
sys.path.append(*list(paths))

options = {"py2exe": {"includes": ["sip",
                                   "matplotlib.backends.backend_tkagg",
                                   "FileDialog"],
                      "compressed": 1,
                      "optimize": 2,
                      "ascii": 0,
                      # "excludes": ["Tkinter"],
                      "dll_excludes": ["MSVCP90.dll"]
                      }
           }
data_files = matplotlib.get_py2exe_datafiles()

windows=[{'script': 'fhTraderMain.py', 'icon_resources':[(1, 'fhIcon.ico')]}]
setup(windows=windows,
      options=options,
      data_files=data_files)

# print '--------'
# print data_files
# print type(data_files)

#