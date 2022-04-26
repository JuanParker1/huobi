# -*- coding: utf-8 -*-
"""
 Created on 2022/4/20 15:29 2022
 @author  : shaokai
 @File    : test.py
 @Description:
"""

import numpy as np
import pandas as pd
from single_coin_anaylsis import *
from tabulate import tabulate


def get_indicators(data):
    # 波动率指标
    indicators = get_volatility(data)
    # 流动性指标
    indicators['liquid_amount'] = data['amount']
    indicators['liquid_volume'] = data['volume']
    # 合约溢价率： (U 本位永续合约 close - 现货 close)/现货 close
    # indicators['premium '] = np.divide(u_contract_data['close'] - data['close'], data['close'])
    return indicators

class ProWorker:
    def __init__(self, api_key, secret_key, url=None):
        if not url:
            self._url = 'https://api.huobi.pro'  # 现货
        else:
            self._url = url
        self._futures_url = 'https://api.hbdm.com'  # 期货，不同合约 是否是同一个入口？
        self.api_key = api_key
        self.secret_key = secret_key

    def get_contract_online_dt(self, url=None):
        if not self._url:
            self._url = 'https://api.huobi.pro'  #'https://api.hbdm.com'  #  现货
        else:
            self._url = url
        res = api_key_post_hb(
            self._url, '/v1/settings/common/symbols',
            {},  # "ts": transfer_type
            self.api_key, self.secret_key)
        if res.get('status') != 'ok':
            print('ERROR!', res)
        return res.get('data')


def get_contract_online_dt(api_key, secret_key, url=None):
    if not url:
        url = 'https://api.hbdm.com' #'https://api.huobi.pro'  # 现货

    res = api_key_post_hb(
        url, ' /v1/settings/common/symbols',
        {}, # "ts": transfer_type
        api_key, secret_key)
    if res.get('status') != 'ok':
        print('ERROR!', res)
    return res.get('data')

if __name__ == '__main__':
    # spot_data = pd.read_csv(r'C:\pythonProj\coin_analysis\spot_btcusdt_5min_None_to_None.csv', index_col=0)
    # # u_contract_data = pd.read_csv(r'C:\pythonProj\coin_analysis\u_contract_btcusdt_5min.csv', index_col=0)
    # spot_data.index = pd.to_datetime(spot_data.index)
    # # u_contract_data.index = pd.to_datetime(u_contract_data.index)
    # # print(spot_data)
    # print()
    # new_freq_data = adjust_frequence(spot_data, freq='10min')
    # indicators = get_indicators(new_freq_data)
    # print(indicators)
    # analyse = analyse_indicators(indicators)
    # print(analyse.info())
    # t = tabulate(analyse, headers='keys', tablefmt='psql')
    #
    # file_name = "result_report.txt"
    # f = open(file_name, "a")
    # # current_time = time.strftime('%Y_%m_%d %H_%M_%S', time.localtime(time.time()))
    # # f.write(current_time + '\n')
    # f.write(str(t) + '\n')
    # f.close()
    #
    # print(tabulate(analyse, headers='keys', tablefmt='psql'))

    # api = 'hrf5gdfghe-c2d03c8c-f4c4e8c7-cd08d'  # 'fb6e5a11-8ee79992-d927c71c-qz5c4v5b6n'
    # secret = '24691826-9d56004b-4167f547-a1e5e'

    # # p = ProWorker(api_key=api, secret_key=secret)
    # # r = p.get_contract_online_dt()
    # # print(r)
    # r = get_contract_online_dt(api, secret)
    # print(r)

    col_info = 'Introduction of the Indicators:\n' \
               '#1. open_close_vol = (open - close)/close, represents volatility. \n' \
               '#2. high_low_vol = (high - low)/low, represents volatility.\n' \
               '#3. liquid_amount = amount, represents liquidity.\n' \
               '#4. liquid_volume = volume, represents liquidity.\n' \
               '#5. premium = [contract(close) - spot(close)]/spot(close), represents the premium of futures over spot.\n'
    # print(col_info)

    class Solution:
        def maxSubArray(self, nums) -> int:
            ans = nums[0]
            for l in range(len(nums)):
                for r in range(l, len(nums)):
                    ans = max(ans, sum(nums[l:r]))
                    print(l, r, nums[l:r], sum(nums[l:r]))
            return ans
    a = Solution().maxSubArray([5,4,-1,7,8])