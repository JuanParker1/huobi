# -*- coding: utf-8 -*-
"""
 Created on 2022/4/24
 @author  : shaokai
 @File    : test.py
 @Description:
"""
import time
import decimal
from datetime import datetime
import pandas as pd


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
    return time_interval

# def get_default_timestamp(start_time, end_time):


def OKX_kline(target='btcusdt', contract_type='swap',
                  interval='1m', start_time=None, end_time=None,
                  adjust_time=True,
                  col_with_asset_name=True, is_fr=False, get_adj=False):


    symbol = target[:-3].upper() + '-' + target[-3:].upper() + '-' + contract_type.upper()
    limit = 100
    # url = 'https://aws.okx.com/api/v5/market/mark-price-candles'
    # para = {'instId': symbol, 'after':end_time, 'before':start_time, 'bar':interval,'limit':100}

    time_interval = get_time_interval(interval)  # 将 str类型时间间隔，转化为 int（单位为秒）

    # set specific end timestamp
    if not end_time:
        end_timestamp = int(datetime.timestamp(datetime.now()))
        end_timestamp -= end_timestamp % time_interval
    else:
        end_timestamp = end_time
    # 设置初始时刻：默认为 获取limit个数据
    if not start_time:
        start_timestamp = end_timestamp - (limit-1) * time_interval  # limit 为运行一次api最多可获取的数据条数
    else:
        start_timestamp = start_time

    if not is_fr:
        result_data = pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    else:
        result_data = pd.DataFrame(columns=['fundingTime', 'realizedRate'])

    # 迭代次数
    iteration = (end_timestamp - start_timestamp) // (time_interval * limit) + 1
    for i in range(iteration):
        interval_time = end_timestamp - (limit-1) * time_interval
        if interval_time < start_timestamp:
            interval_time = start_timestamp
        if start_timestamp > end_timestamp:
            break
        if is_fr:
            contract_url = "https://aws.okx.com/api/v5/public/funding-rate-history?instId={}&before={}&after={}&bar={}&limit=100".format(
                symbol, interval_time * 1000, end_timestamp * 1000, interval)
        else:
            contract_url = "https://aws.okx.com/api/v5/market/history-candles?instId={}&before={}&after={}&bar={}&limit=100".format(
                symbol, interval_time * 1000, end_timestamp * 1000, interval)
        print(i, datetime.fromtimestamp(interval_time), datetime.fromtimestamp(end_timestamp))

        retry_time = 0
        while True:
            try:
                contract_response = requests.get(contract_url)
                break
            except Exception as e:
                print(e)
                print(target + ' fail to get data. Retry...')
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
                    contract_data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']
                    for j in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                        contract_data[j] = contract_data[j].astype('float')
                    print(len(contract_data))
                    result_data = result_data.append(contract_data)
                else:
                    contract_data = contract_data[['fundingTime', 'realizedRate']]
                    contract_data.iloc[:, 0] = contract_data.iloc[:, 0].apply(lambda x: int(x) // 1000)
                    contract_data['realizedRate'] = contract_data['realizedRate'].astype('float')  # decimal.Decimal(contract_data[j])  #
                    print(len(contract_data))
                    result_data = result_data.append(contract_data)

        end_timestamp = interval_time - time_interval
        time.sleep(0.3)

    if is_fr:
        result_data.rename(columns={'fundingTime': 'datetime', 'realizedRate': 'fundingRate'}, inplace=True)

    result_data.sort_values('datetime', inplace=True)
    if adjust_time:
        result_data['datetime'] += 28800
        result_data['datetime'] = pd.to_datetime(result_data['datetime'], unit='s')

    result_data.set_index(['datetime'], inplace=True)

    if col_with_asset_name:
        return result_data
    else:
        rename_dict = {}
        for i in result_data.columns:
            rename_dict[i] = i.split("_")[-1]
        result_data.rename(columns=rename_dict, inplace=True)
        if get_adj:
            result_data['adj_close'] = result_data['close']
        return result_data

if __name__ == '__main__':
    import requests

    # symbol = 'BTC-USDT-SWAP'  # 'BTC-USDT' # 'BTC-USD-SWAP'
    # interval = '1m'

    # print(time.time())
    # end   = 1650791160000 #int(time.time())
    # start = 1650791040000 #end - 60 * 1000 * 20
    # print(datetime.datetime.fromtimestamp(start//1000))
    # print(datetime.datetime.fromtimestamp(end // 1000))

    # contract_url = "https://aws.okx.com/api/v5/market/mark-price-candles?instId={}&before={}&after={}&bar={}&limit=100".format(
    #     symbol, start,  end, interval)
    # # contract_url = "https://aws.okx.com/api/v5/market/mark-price-candles?instId={}&bar={}&limit=100".format(
    # #     symbol,interval)
    # print(contract_url)
    # url = 'https://www.okex.me/api/general/v3/time'
    # response = requests.get(contract_url)
    # print(response.json())

    # start_time = int(time.time()) - 80 * 86400
    # period = '4H'  # '5m'
    # target = 'BTCUSD'
    #
    # result_data = OKX_kline(target=target, interval=period, contract_type='SWAP', start_time=start_time,
    #                         col_with_asset_name=False)
    # print(result_data)
    a = '20h'
    print(a.upper())