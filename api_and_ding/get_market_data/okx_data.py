# -*- coding: utf-8 -*-
"""
 Created on 2022/4/24
 @author  : shaokai
 @File    : okx_data.py
 @Description: 从 okx 获取数据
"""
import time
from datetime import datetime

import pandas as pd
import requests


def get_time_interval(interval='1m'):
    if interval == '1m':
        time_interval = 60
    elif interval == '5m':
        time_interval = 300
    elif interval == '15m':
        time_interval = 900
    elif interval == '30m':
        time_interval = 1800
    elif interval == '1H':
        time_interval = 3600
    elif interval == '4H':
        time_interval = 14400
    elif interval == '1D':
        time_interval = 86400
    else:
        raise ValueError(f'invalid interval:{interval}!')
    return time_interval


def OKX_kline(symbol='btcusdt', interval='1m', start_time=None, end_time=None,
              adjust_time=True, is_fr=False):
    """

    Args:
        symbol:  现货 BTC-USDT; 币本位 BTC-USD-SWAP; u本位 BTC-USDT-SWAP
        contract_type: spot, swap
        interval: k线数据的时间频率
        is_fr: 是否为资金费率数据

    Returns:
        dataframe
    """
    if interval[-1] == 'h' or interval[-1] == 'd':
        interval = interval.upper()
    elif 'min' in interval:
        interval = interval[:-2]


    limit = 100
    time_interval = get_time_interval(interval)  # 将 str类型时间间隔，转化为 int（单位为秒）

    # set specific end timestamp
    if not end_time:
        end_timestamp = int(datetime.timestamp(datetime.now()))
        end_timestamp -= end_timestamp % time_interval
    else:
        end_timestamp = int(end_time)
    # 设置初始时刻：默认为 获取limit个数据
    if not start_time:
        start_timestamp = end_timestamp - (limit - 1) * time_interval  # limit 为运行一次api最多可获取的数据条数
    else:
        start_timestamp = int(start_time)

    if not is_fr:
        result_data = pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    else:
        result_data = pd.DataFrame(columns=['fundingTime', 'realizedRate'])

    # 迭代次数
    iteration = (end_timestamp - start_timestamp) // (time_interval * limit) + 1
    for i in range(iteration):
        interval_time = end_timestamp - (limit - 1) * time_interval
        if interval_time < start_timestamp:
            interval_time = start_timestamp
        if start_timestamp > end_timestamp:
            break
        if is_fr:
            contract_url = "https://aws.okx.com/api/v5/public/funding-rate-history?instId={}&before={}&after={}&bar={}&limit=100".format(
                symbol, interval_time * 1000 - 1, end_timestamp * 1000, interval)  # 时间的始末都是开集,所以 -1使得初始时间能被包含进去
        else:
            contract_url = "https://aws.okx.com/api/v5/market/history-candles?instId={}&before={}&after={}&bar={}&limit=100".format(
                symbol, interval_time * 1000 - 1, end_timestamp * 1000, interval)
            print(contract_url)

        retry_time = 0
        while True:
            try:
                contract_response = requests.get(contract_url)
                break
            except Exception as e:
                print(e)
                print(symbol + ' fail to get data. Retry...')
                time.sleep(0.3)
                retry_time += 1
                if retry_time >= 10:
                    raise Exception('Please try later')
        contract_result = contract_response.json().get('data')
        print(contract_result)

        if not contract_result:
            pass
        else:
            try:
                contract_data = pd.DataFrame(contract_result)
            except Exception as e:
                print('Can not get desired data.')
                print(contract_result)
                print(e)
            else:
                if not is_fr:
                    contract_data.iloc[:, 0] = contract_data.iloc[:, 0].apply(lambda x: int(x) // 1000)
                    contract_data.columns = ['datetime', 'open', 'high', 'low', 'close', 'amount', 'volume']

                    result_data = result_data.append(contract_data)
                else:
                    contract_data = contract_data[['fundingTime', 'realizedRate']]
                    contract_data.iloc[:, 0] = contract_data.iloc[:, 0].apply(lambda x: int(x) // 1000)
                    contract_data['realizedRate'] = contract_data['realizedRate'].astype(
                        'float')  # decimal.Decimal(contract_data[j])
                    result_data = result_data.append(contract_data)

        end_timestamp = interval_time - time_interval
        time.sleep(0.3)

    if is_fr:
        result_data.rename(columns={'fundingTime': 'datetime', 'realizedRate': 'fundingRate'}, inplace=True)
        result_data['fundingRate'] = result_data['fundingRate'].astype('float')
    else:
        for j in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            result_data[j] = result_data[j].astype('float')

    result_data.sort_values('datetime', inplace=True)
    if adjust_time:
        result_data['datetime'] += 28800
        result_data['datetime'] = pd.to_datetime(result_data['datetime'], unit='s')

    result_data.set_index(['datetime'], inplace=True)

    return result_data


if __name__ == '__main__':
    from coin_analysis.exchange_data import *
    m = ExchangeData(coinpair='btcusdt', exchange='okx')
    spot, c_swap, u_swap = m.spot, m.c_contract, m.u_contract
    print(spot, c_swap, u_swap)



    start = int(time.mktime((2022, 4, 26, 0, 0, 0, 0, 0, 0)))
    period = '5min'  # '5m'

    result_data = OKX_kline(symbol=spot, interval=period, start_time=start, contract_type='')#, is_fr=True
    print(result_data.info())
    print(result_data)



    r = adjust_frequence(result_data, freq='10min')
    print(r)


    # get_okx_create_date(symbol='BTCUSDT', contract_type='Swap'), start_time=start
    # # get_binance_create_date()
    # d = get_huobi_creat_date(symbol='BTC-USDT')
    # print(d)
