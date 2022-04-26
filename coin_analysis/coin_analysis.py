# -*- coding: utf-8 -*-
"""
 Created on 2022/4/21
 @author  : shaokai
 @File    : coin_analysis.py.py
 @Description: 单币种分析
"""


import numpy as np
import pandas as pd
from tabulate import tabulate
import time

from other_codes.get_historical_data.huobi_data import Huobi_kline
from subuser_test.rest_utils import *


def get_contract_code(spot_code):
    """ 获取现货交易对的永续合约代码

    Args:
        spot_code: 现货交易对代码

    Returns:
        币本位永续合约代码，U 本位永续合约代码
    """
    c_contract = spot_code[:-4].upper() + '-' + spot_code[-4:].upper()  # 币本位永续 XXX-USD
    u_contract = spot_code[:-4].upper() + '-' + spot_code[-4:-1].upper()  # U 本位永续 XXX-USDT
    return c_contract, u_contract


def get_coin_data(target='btcusdt', start_time=None, end_time=None, period='5min'):
    spot_data = Huobi_kline(symbol=target, period=period, start_time=start_time, end_time=end_time,
                            get_full_market_data=True, col_with_asset_name=False)
    print(spot_data)
    spot_data.to_csv(r'C:\pythonProj\coin_analysis\spot_{}_{}.csv'.format(target, period))
    try:
        c_contract = target[:-4].upper() + '-' + target[-4:].upper()  # 币本位永续 XXX-USD
        u_contract = target[:-4].upper() + '-' + target[-4:-1].upper()  # U 本位永续 XXX-USDT
        print(c_contract, u_contract)
        c_contract_data = Huobi_kline(symbol=c_contract, period=period, start_time=start_time, end_time=end_time,
                                get_full_market_data=True, col_with_asset_name=False)
        u_contract_data = Huobi_kline(symbol=u_contract, period=period, start_time=start_time, end_time=end_time,
                                      get_full_market_data=True, col_with_asset_name=False)
        u_contract_data.to_csv(r'C:\pythonProj\coin_analysis\u_contract_{}_{}.csv'.format(target, period))
        c_contract_data.to_csv(r'C:\pythonProj\coin_analysis\c_contract_{}_{}.csv'.format(target, period))
        return spot_data, c_contract_data, u_contract_data
    except KeyError:
        print('无相关合约')
        return spot_data, None, None

class CoinAnalysis():
    def __init__(self, target='btcusdt', start_time=None, end_time=None, period='5min'):
        # spot_data, c_contract_data, u_contract_data = get_coin_data(target=target, start_time=start_time,
        #                                                             end_time=end_time, period=period)
        spot_data = pd.read_csv('spot_btcusdt_5min.csv', index_col=0)
        c_contract_data = pd.read_csv('c_contract_btcusdt_5min.csv', index_col=0)
        u_contract_data = pd.read_csv('u_contract_btcusdt_5min.csv', index_col=0)
        spot_data.index = pd.to_datetime(spot_data.index)
        c_contract_data = pd.to_datetime(c_contract_data.index)
        u_contract_data = pd.to_datetime(u_contract_data.index)

        self.spot_data = spot_data
        self.c_contract_data = c_contract_data
        self.u_contract_data = u_contract_data
        self.start_time = start_time
        self.end_time = end_time
        self.target = target

    # @staticmethod
    def adjust_frequence(self, data, freq='10min'):
        if freq == '5min':
            return data

        start = data.index[0], end = data.index[-1]

        if freq[-3:] == 'min':
            freq = freq.upper()
        elif freq[-4:] == 'hour':
            freq = freq[:-4] + 'H'
        elif freq[-3:] == 'day':
            freq = freq[:-3] + 'D'
        date_index = pd.date_range(start, end, freq=freq)
        new_freq_data = pd.DataFrame(0.0, columns=data.columns, index=date_index)

        # 求出新 K 线数据
        new_freq_data['open'] = data['open'].resample(freq).first()
        new_freq_data['close'] = data['close'].resample(freq).last()
        new_freq_data['high'] = data['high'].resample(freq).max()
        new_freq_data['low'] = data['low'].resample(freq).min()
        new_freq_data['volume'] = data['volume'].resample(freq).sum()
        new_freq_data['amount'] = data['amount'].resample(freq).sum()
        return new_freq_data

    def get_volatility(self, data):
        vol_data = pd.DataFrame(0.0, columns=['open_close_vol', 'high_low_vol'], index=data.index)
        vol_data['open_close_vol'] = np.divide(data['open'] - data['close'], data['close'])
        vol_data['high_low_vol'] = np.divide(data['high'] - data['low'], data['low'])
        return vol_data

    def get_indicators(self, data, u_contract_data=[]):
        # 波动率指标
        indicators = self.get_volatility(data)
        # 流动性指标
        indicators['liquid_amount'] = data['amount']
        indicators['liquid_volume'] = data['volume']
        if len(u_contract_data)!=0:
            # 合约溢价率： (U 本位永续合约 close - 现货 close)/现货 close
            indicators['premium '] = np.divide(u_contract_data['close'] - data['close'], data['close'])
        return indicators

    def analyse_indicators(self, indicators):
        analyse_data = indicators.describe()
        analyse_data = analyse_data.drop('count', axis=0)
        return analyse_data

    def analyse_all(self, period):
        u_contract_data = self.adjust_frequence(self.u_contract_data, freq=period)
        c_contract_data = self.adjust_frequence(self.c_contract_data, freq=period)
        new_freq_data = self.adjust_frequence(self.spot_data, freq=period)
        # 现货分析
        indicators = self.get_indicators(new_freq_data, u_contract_data)
        spot_analyse_data = self.analyse_indicators(indicators)
        # 币本位
        indicators = self.get_indicators(c_contract_data)
        c_analyse_data = self.analyse_indicators(indicators)
        # u本位
        indicators = self.get_indicators(u_contract_data)
        u_analyse_data = self.analyse_indicators(indicators)
        return spot_analyse_data, c_analyse_data, u_analyse_data

    def analyse(self, periods=['5min', '15min', '30min', '1hour', '4hour', '1day']):
        report_filename = "{}_report.txt".format(self.target)

        title = f'{self.target}: {datetime.datetime.fromtimestamp(self.start_time)} - {datetime.datetime.fromtimestamp(self.end_time)}'
        f = open(report_filename, "a")
        f.write(title +'\n')
        f.close()
        for period in periods:
            spot_analyse_data, c_analyse_data, u_analyse_data = self.analyse_all(period=period)
            add_to_txt(spot_analyse_data, period=period, data_name='spot', file_name=report_filename)
            add_to_txt(c_analyse_data, period=period, data_name='coin-margined contract', file_name=report_filename)
            add_to_txt(u_analyse_data, period=period, data_name='USDT-margined contract', file_name=report_filename)
        return spot_analyse_data, c_analyse_data, u_analyse_data


def add_to_txt(df, period, data_name='spot', file_name="result_report.txt"):
    t = tabulate(df, headers='keys', tablefmt='psql')
    # 存入 txt
    f = open(file_name, "a")
    f.write(f'{data_name}:' + '\n')
    f.write(str(t) + '\n')
    f.close()

class ProWorker:
    def __init__(self, api_key, secret_key, url=None):
        if not url:
            self._url = 'https://api.huobi.pro'  # 现货
        else:
            self._url = url
        self._futures_url = 'https://api.hbdm.com'  # 期货，不同合约 是否是同一个入口？
        self.api_key = api_key
        self.secret_key = secret_key

    def get_creat_date(self, symbol):
        if symbol[-4:] == 'USDT':
            curl = '/linear-swap-api/v1/swap_contract_info'
        elif symbol[-3:] == 'USD':
            curl = '/swap-api/v1/swap_contract_info'

        res = api_key_get_hb(
            self._futures_url, curl, {'contract_code': symbol}, self.api_key, self.secret_key)
        # if res.get('status') != 'ok':
        #     self.logger.error(res)
        return res.get('data')[0].get('create_date')

if __name__ == '__main__':
    start_time = int(time.mktime((2022, 1, 1, 0, 0, 0, 0, 0, 0)))
    end_time = int(time.mktime((2022, 4, 20, 0, 0, 0, 0, 0, 0)))

    c = CoinAnalysis(target='btcusdt', start_time=start_time, end_time=end_time)
    c.analyse()
    # target = 'btcusdt'
    # report_filename = "{}_report.txt".format(target)
    # print(f'{target}: {datetime.datetime.fromtimestamp(start_time)} - {datetime.datetime.fromtimestamp(end_time)}')
    # f = open(report_filename, "a")
    # f.write(f'{target}: {datetime.datetime.fromtimestamp(start_time)} - {datetime.datetime.fromtimestamp(end_time)}\n')
    # f.close()



    # for period in ['5min', '15min', '30min', '1hour', '4hour', '1day']:
    #     f = open(report_filename, "a")
    #     f.write('\n' + f'{period} analyse result:' + '\n')
    #     f.close()
    #
    #
    #     spot_analyse_data, c_analyse_data, u_analyse_data = analyse(target=target, period=period)
    #     add_to_txt(spot_analyse_data, period=period, data_name='spot', file_name=report_filename)
    #     add_to_txt(c_analyse_data, period=period, data_name='coin-margined contract', file_name=report_filename)
    #     add_to_txt(u_analyse_data, period=period, data_name='USDT-margined contract', file_name=report_filename)
    #     f.close()
    api = 'hrf5gdfghe-c2d03c8c-f4c4e8c7-cd08d'  # 'fb6e5a11-8ee79992-d927c71c-qz5c4v5b6n'
    secret = '24691826-9d56004b-4167f547-a1e5e'

    c_contract, u_contract = get_contract_code(spot_code=target)
    p = ProWorker(api, secret)
    creat_date = p.get_creat_date(c_contract)
    print(c_contract, creat_date)
    creat_date = p.get_creat_date(u_contract)
    print(c_contract, creat_date)