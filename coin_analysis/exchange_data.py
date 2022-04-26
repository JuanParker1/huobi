# -*- coding: utf-8 -*-
"""
 Created on 2022/4/26
 @author  : shaokai
 @File    : exchange_data.py
 @Description:
"""
import time
from datetime import datetime

import pandas as pd
import requests
from api_and_ding.get_market_data.okx_data import *
from api_and_ding.get_market_data.huobi_data import Huobi_kline

def get_time_interval(period='1m'):
    if period == '1m':
        time_interval = 60
    elif period == '5m':
        time_interval = 300
    elif period == '15m':
        time_interval = 900
    elif period == '30m':
        time_interval = 1800
    elif period == '1H':
        time_interval = 3600
    elif period == '4H':
        time_interval = 14400
    elif period == '1D':
        time_interval = 86400
    else:
        raise ValueError(f'invalid interval:{period}!')
    return time_interval

class MarketKline():
    def __init__(self, coinpair='btcusdt', exchange='huobi'):
        """

        Args:
            coinpair: 现货交易对 eg. btcusdt
            exchange:
        """
        self.coinpair = coinpair
        self.exchange = exchange
        self.spot, self.c_contract, self.u_contract = self.get_contract_code()

    def get_contract_code(self):
        """ 获取现货交易对的永续合约代码

        Returns:
            现货交易对代码, 币本位永续合约代码，U 本位永续合约代码
        """
        if self.exchange == 'huobi':
            spot = self.coinpair.lower()
            c_contract = self.coinpair[:-4].upper() + '-' + self.coinpair[-4:-1].upper()  # 币本位永续 XXX-USD
            u_contract = self.coinpair[:-4].upper() + '-' + self.coinpair[-4:].upper()  # U 本位永续 XXX-USDT
        elif self.exchange == 'okx':
            spot = self.coinpair[:-4].upper() + '-' + self.coinpair[-4:].upper()
            c_contract = self.coinpair[:-4].upper() + '-' + self.coinpair[-4:-1].upper() + '-SWAP'  # 币本位永续 XXX-USD-SWAP
            u_contract = self.coinpair[:-4].upper() + '-' + self.coinpair[-4:].upper() + '-SWAP' # U 本位永续 XXX-USDT-SWAP
        return spot, c_contract, u_contract

    def get_swap_create_timestamp(self, swap_code):
        """
        Returns:
            10位的时间戳数据（int型）
        """
        if self.exchange == 'huobi':
            creat_date = get_huobi_creat_timestamp(swap_code)
        elif self.exchange == 'okx':
            creat_date = get_okx_create_timestamp(swap_code)
        return creat_date

    def get_coin_data(self, period, start_time=None, end_time=None):
        if self.exchange == 'huobi':
            spot_data = Huobi_kline(symbol=self.spot, period=period, start_time=start_time, end_time=end_time,
                                    get_full_market_data=True, col_with_asset_name=False)
            spot_data.to_csv(r'C:\pythonProj\data\coin_analysis\{}_spot_{}_{}.csv'.format(self.exchange, self.spot, period))
            try:
                c_contract_data = Huobi_kline(symbol=self.c_contract, period=period, start_time=start_time,
                                              end_time=end_time,
                                              get_full_market_data=True, col_with_asset_name=False)
                u_contract_data = Huobi_kline(symbol=self.u_contract, period=period, start_time=start_time,
                                              end_time=end_time,
                                              get_full_market_data=True, col_with_asset_name=False)
                # u_contract_data.to_csv(r'C:\pythonProj\data\coin_analysis\u_contract_{}_{}.csv'.format(target, period))
                # c_contract_data.to_csv(r'C:\pythonProj\data\coin_analysis\c_contract_{}_{}.csv'.format(target, period))
                return spot_data, c_contract_data, u_contract_data
            except KeyError:
                print('无相关合约')
                return spot_data, None, None
        elif self.exchange == 'okx':
            spot_data = OKX_kline(symbol=self.spot, contract_type='spot', interval=period, start_time=start_time,
                                  end_time=end_time, is_fr=False)
            spot_data.to_csv(r'C:\pythonProj\data\coin_analysis\{}_spot_{}_{}.csv'.format(self.exchange, self.spot, period))
            try:
                c_contract_data = OKX_kline(symbol=self.c_contract, contract_type='swap', interval=period,
                                            start_time=start_time,
                                            end_time=end_time, is_fr=False)
                u_contract_data = OKX_kline(symbol=self.u_contract, contract_type='swap', interval=period, start_time=start_time,
                                            end_time=end_time, is_fr=False)
                u_contract_data.to_csv(
                    r'C:\pythonProj\data\coin_analysis\{}_u_contract_{}_{}.csv'.format(self.exchange, self.c_contract, period))
                c_contract_data.to_csv(
                    r'C:\pythonProj\data\coin_analysis\{}_c_contract_{}_{}.csv'.format(self.exchange, self.u_contract, period))
                return spot_data, c_contract_data, u_contract_data
            except KeyError:
                print('无相关合约')
                return spot_data, None, None

    def get_funding_rate(self, start_time=None, end_time=None, period='4hour'):
        """ 获取 币本位、U本位永续合约的资金费率

        Args:
            target: 现货合约代码

        Returns:
            dataframe
        """
        if self.exchange == 'huobi':
            try:
                c_contract_fr = Huobi_kline(symbol=self.c_contract, period=period, start_time=start_time, end_time=end_time,
                                            is_fr=True, col_with_asset_name=False)
                u_contract_fr = Huobi_kline(symbol=self.u_contract, period=period, start_time=start_time, end_time=end_time,
                                            is_fr=True, col_with_asset_name=False)
                # u_contract_data.to_csv(r'C:\pythonProj\data\coin_analysis\u_contract_{}_{}.csv'.format(target, period))
                # c_contract_data.to_csv(r'C:\pythonProj\data\coin_analysis\c_contract_{}_{}.csv'.format(target, period))
                c_contract_fr_close = c_contract_fr['close'].resample('8H').last()
                u_contract_fr_close = u_contract_fr['close'].resample('8H').last()
                funding_rate = pd.concat([c_contract_fr_close, u_contract_fr_close], axis=1,
                                         keys=['Coin-Margined Contract', 'USDT-Margined Contract'])
                return funding_rate
            except KeyError:
                print('为获取到相关合约')
                return None
        elif self.exchange == 'okx':
            try:
                c_contract_fr = OKX_kline(symbol=self.c_contract, interval='4H', start_time=start_time,
                                          end_time=end_time, is_fr=True)
                u_contract_fr = OKX_kline(symbol=self.u_contract, interval='4H', start_time=start_time, end_time=end_time,
                                          is_fr=True)
                # u_contract_data.to_csv(r'C:\pythonProj\data\coin_analysis\u_contract_{}_{}.csv'.format(target, period))
                # c_contract_data.to_csv(r'C:\pythonProj\data\coin_analysis\c_contract_{}_{}.csv'.format(target, period))
                funding_rate = pd.concat([c_contract_fr, u_contract_fr], axis=1)
                funding_rate.columns = ['Coin-Margined Contract', 'USDT-Margined Contract']
                return funding_rate
            except KeyError:
                print('未获取到相关合约')
                return None


def get_huobi_creat_timestamp(symbol='BTC-USDT'):
    futures_url = 'https://api.hbdm.com'
    if symbol[-4:] == 'USDT':
        curl = '/linear-swap-api/v1/swap_contract_info'
    elif symbol[-3:] == 'USD':
        curl = '/swap-api/v1/swap_contract_info'

    contract_url = futures_url + curl + '?contract_code={}'.format(symbol)
    res = requests.get(contract_url)
    create_date = res.json().get('data')[0].get('create_date')
    create_ts = int(time.mktime((int(create_date[:4]), int(create_date[4:6]), int(create_date[-2:]), 0, 0, 0, 0, 0, 0)))
    return create_ts

def get_okx_create_timestamp(symbol='BTC-USDT-SWAP'):
    url = 'https://aws.okx.com/api/v5/public/instruments'
    contract_url = url + '?instId={}&instType={}'.format(symbol, 'SWAP')
    response = requests.get(contract_url)
    create_date = response.json().get('data')[0].get('listTime')
    return int(create_date) // 1000


def get_binance_create_date():
    ''
    url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
    # symbol = target[:-3].upper() + '-' + target[-3:].upper() + '-' + contract_type.upper()
    contract_url = url  # + '?instId={}&instType={}'.format(symbol, contract_type.upper())
    response = requests.get(contract_url)
    create_date = response.json().get('symbols')[0].get('onboardDate')
    print(datetime.fromtimestamp(int(create_date) // 1000))
    return create_date


if __name__ == '__main__':
    m = MarketKline(coinpair='btcusdt', exchange='huobi')
    spot, c_swap, u_swap = m.get_coin_data(period='5min')
    funding_rate = m.get_funding_rate()
    print(spot, '\n', c_swap, '\n', u_swap)
    print(funding_rate)

    # start = int(time.time()) - 800 * 86400
    # period = '4H'  # '5m'
    # target = 'BTCUSDT'
    #
    # result_data = OKX_kline(symbol=target, interval=period, contract_type='SWAP', is_fr=True)
    # print(result_data)
