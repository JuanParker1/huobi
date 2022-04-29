# -*- coding: utf-8 -*-
"""
 Created on 2022/4/27
 @author  : shaokai
 @File    : ftx_data.py
 @Description:
"""
import sys

argvs = sys.argv
from datetime import datetime, timedelta
import pandas as pd

import time
import urllib.parse
from typing import Optional, Dict, Any, List

from requests import Request, Session, Response
import hmac


class FtxClient:
    _ENDPOINT = 'https://ftx.com/api/'

    def __init__(self, api_key=None, api_secret=None, subaccount_name=None) -> None:
        self._session = Session()
        self._api_key = api_key
        self._api_secret = api_secret
        self._subaccount_name = subaccount_name

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('GET', path, params=params)

    def _post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('POST', path, json=params)

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request('DELETE', path, json=params)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self._ENDPOINT + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def _sign_request(self, request: Request) -> None:
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self._api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self._api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self._subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self._subaccount_name)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    def get_all_futures(self) -> List[dict]:
        return self._get('futures')

    def get_future(self, future_name: str = None) -> dict:
        return self._get(f'futures/{future_name}')

    def get_markets(self) -> List[dict]:
        return self._get('markets')

    def get_klines(self, market: str, resolution: int = 3600, limit: int = 1000,
                   start_time: int = None, end_time: int = None)-> List[dict]:
        """ 获取历史数据

        Args:
            market:
            resolution: 窗口时长（秒）。 选项：15, 60, 300, 900, 3600, 14400, 86400
            limit: max number to fetch, optional, max 5000
            start_time: 10位时间戳 , optional
            end_time:
        """
        return self._get(f'markets/{market}/candles', {'resolution': resolution,
                                                       'limit': limit,
                                                       'start_time': start_time,
                                                       'end_time': end_time})

    def get_trades(self, market_name: str, limit: int = 1440, start_time: int = None, end_time: int = None):
        return self._get(f'markets/{market_name}/trades', {'limit': limit,
                                                           'start_time': start_time,
                                                           'end_time': end_time})

    def get_future(self, future_name: str = None) -> dict:
        return self._get(f'futures/{future_name}')

    def get_markets(self) -> List[dict]:
        return self._get('markets')

    def get_orderbook(self, market: str, depth: int = None) -> dict:
        return self._get(f'markets/{market}/orderbook', {'depth': depth})

    def get_trades(self, market: str, start_time: float = None, end_time: float = None) -> dict:
        return self._get(f'markets/{market}/trades', {'start_time': start_time, 'end_time': end_time})

    def get_single_market(self, market: str = None) -> Dict:
        return self._get(f'markets/{market}')

    def get_market_info(self, market: str = None) -> dict:
        return self._get('spot_margin/market_info', {'market': market})

    def get_funding_rates(self, future: str = None, start_time: float = None, end_time: float = None) -> List[dict]:
        return self._get('funding_rates', {
            'future': future,
            'start_time': start_time,
            'end_time': end_time
        })

    def get_all_funding_rates(self) -> List[dict]:
        return self._get('funding_rates')

    def get_latency_stats(self, days: int = 1, subaccount_nickname: str = None) -> Dict:
        return self._get('stats/latency_stats', {'days': days, 'subaccount_nickname': subaccount_nickname})


def get_time_interval(interval='1m'):
    if interval == '1min':
        time_interval = 60
    elif interval == '5min':
        time_interval = 300
    elif interval == '15min':
        time_interval = 900
    elif interval == '1hour':
        time_interval = 3600
    elif interval == '4hour':
        time_interval = 14400
    elif interval == '1day':
        time_interval = 86400
    else:
        raise ValueError(f"invalid interval: {interval}. You can only chose interval from "
                         f"['1min', '5min', '15min', '1hour', '4hour', '1day']")
    return time_interval


def FTX_kline(symbol='btcusdt', interval='1m', start_time=None, end_time=None,
              adjust_time=True, is_fr=False):
    """

    Args:
        symbol:  现货 BTCUSDT;
        interval: k线数据的时间频率, 可选：'1min', '5min', '15min', '1hour', '4hour', '1day'
        is_fr: 是否为资金费率数据

    Returns:
        dataframe
    """
    ftx_key = {'access': 'TtCuDaRMhZlE_nH_qSnQYWiKF2asdLknFNWXsu2Z',
               'secret': 'n7eSUAR_GtmAxVXgaUiYpEJO6CtGlMTzQlC1QqqU'}
    limit = 5000
    time_interval = get_time_interval(interval)  # 将 str类型时间间隔，转化为 int（单位为秒）
    print('time_interval', time_interval)

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
        result_data = pd.DataFrame(columns=['startTime', 'time', 'open', 'high', 'low', 'close', 'volume'])
    else:
        result_data = pd.DataFrame(columns=['future', 'rate'])

    # 迭代次数
    iteration = (end_timestamp - start_timestamp) // (time_interval * limit) + 1
    for i in range(iteration):
        interval_time = end_timestamp - (limit - 1) * time_interval
        if interval_time < start_timestamp:
            interval_time = start_timestamp
        if start_timestamp > end_timestamp:
            break

        retry_time = 0
        while True:
            try:
                f = FtxClient(api_key=ftx_key['access'], api_secret=ftx_key['secret'])
                if is_fr:
                    contract_result = f.get_funding_rates(future=symbol, start_time=interval_time,
                                                 end_time=end_timestamp)  # 时间的始末都是开集,所以 -1使得初始时间能被包含进去
                else:
                    contract_result = f.get_klines(market=symbol, start_time=interval_time,
                                                   end_time=end_timestamp, resolution=time_interval)

                break
            except Exception as e:
                print(e)
                print(symbol + ' fail to get data. Retry...')
                time.sleep(0.3)
                retry_time += 1
                if retry_time >= 10:
                    raise Exception('Please try later')
        # contract_result = contract_response.json().get('data')
        print(contract_result)

        if not contract_result:
            pass
        else:
            try:
                contract_data = pd.DataFrame.from_dict(contract_result)
            except Exception as e:
                print('Can not get desired data.')
                print(contract_result)
                print(e)
            else:
                if not is_fr:
                    contract_data.iloc[:, 1] = contract_data.iloc[:, 1].apply(
                        lambda x: int(x) // 1000)  # 第二列为 timestamp
                    # contract_data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']
                    result_data = pd.concat([result_data, contract_data])

                else:
                    contract_data['rate'] = contract_data['rate'].astype('float')
                    result_data = pd.concat([result_data, contract_data])

        end_timestamp = interval_time - time_interval
        time.sleep(0.3)

    if is_fr:
        result_data.rename(columns={'time': 'datetime', 'rate': 'fundingRate'}, inplace=True)
        result_data['fundingRate'] = result_data['fundingRate'].astype('float')
        result_data['datetime'] = pd.to_datetime(result_data['datetime'])
        result_data.drop(columns='future', inplace=True)

    else:
        for j in ['open', 'high', 'low', 'close', 'volume']:  # , 'amount'
            result_data[j] = result_data[j].astype('float')
        result_data.rename(columns={'time': 'datetime'}, inplace=True)
        result_data.drop(columns='startTime', inplace=True)
        # 交易量 amount, 和交易额 volume
        result_data['amount'] = result_data['volume'] / \
                                ((result_data['open'] + result_data['open'] + result_data['open'])/3)

    result_data.sort_values('datetime', inplace=True)
    if adjust_time:
        if not is_fr:
            result_data['datetime'] += 28800
            result_data['datetime'] = pd.to_datetime(result_data['datetime'], unit='s')
        else:
            result_data['datetime'] = result_data['datetime'] + timedelta(hours=8)

    result_data.set_index(['datetime'], inplace=True)

    return result_data


if __name__ == "__main__":
    # main()
    coin = 'BTC'
    target = [coin + '/USDT', coin + '-PERP']
    ftx_key = {'access': 'TtCuDaRMhZlE_nH_qSnQYWiKF2asdLknFNWXsu2Z',
               'secret': 'n7eSUAR_GtmAxVXgaUiYpEJO6CtGlMTzQlC1QqqU'}
    f = FtxClient(api_key=ftx_key['access'], api_secret=ftx_key['secret'])
    r = f.get_future(target[1])
    r = pd.DataFrame.from_dict(r)
    print(r.columns)
    print(r)
    # print(r.iloc[0,:])

    # result = FTX_kline(symbol=target[1], interval='5min', start_time=None, end_time=None,
    #                    adjust_time=True, is_fr=False)
    # print(result)



    # 打印 btc 的market
    # result = f.get_markets()
    # df = pd.DataFrame.from_dict(result)
    # name = df.name.tolist()
    # print(name)
    # import re
    # all = [c for c in name if re.findall("^BTC", c)]
    # for a in all:
    #     print(a)
