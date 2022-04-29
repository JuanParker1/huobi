# -*- coding: utf-8 -*-
"""
 Created on 2022/4/24
 @author  : shaokai
 @File    : test.py
 @Description:
"""
import pandas as pd

if __name__ == '__main__':
    from ftx_data import *
    import re
    # print(re.findall('^b', 'abtc'))

    import re

    reg = re.compile(r"\d+([a-zA-Z])")
    match = reg.search("1day").group(0)
    print(match)


    # from urllib.request import urlopen
    #
    # # urlopen('https://www.howsmyssl.com/a/check').read()
    #
    # import ssl
    # # print(ssl._create_unverified_context())
    # urlopen('https://www.howsmyssl.com/a/check', context=ssl._create_unverified_context()).read()
