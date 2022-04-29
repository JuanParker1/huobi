# -*- coding: utf-8 -*-
"""
 Created on 2022/4/27
 @author  : shaokai
 @File    : ftx_kline_test.py
 @Description:
"""
import os
import sys

argvs = sys.argv
from datetime import datetime, timedelta, timezone
import json
import pytz
import pandas as pd

# For FtxClient ----------------------------------------
import time
import urllib.parse
from typing import Optional, Dict, Any, List

from requests import Request, Session, Response
import hmac

# ------------------------------------------------------


##########################################################################################################
#
#  Global settings
#
##########################################################################################################

# get yesterday's date in UTC
#  ****Assuming this script will be executed at midnight (0:00)!!****
dt = datetime.utcnow() - timedelta(days=1)
# timezone setting
jst = pytz.timezone('Asia/Tokyo')

# Market and interval
prefix = 'BTC-MOVE-'
market = prefix + dt.strftime('%m%d')
print(f'market is {market}')
# interval = float(sys.argv[1]) if len(sys.argv) >= 2 else 1 # unit: min
interval = 1  # unit: min
# Make sure interval is either 0.4/1/5/15/60/240/1440. See get_klines() comment.
if interval not in [0.4, 1, 5, 15, 60, 240, 1440]:
    print(f'Kline interval {interval} has to be either 0.4/1/5/15/60/240/1440.')
    sys.exit(0)
elif interval >= 1:
    interval = int(interval)
    print(f'Kline interval is {interval} min.')
else:
    print(f'Kline interval is {int(interval * 60)} sec.')


##########################################################################################################
#
#  FtxClient class
#    from https://github.com/ftexchange/ftx/blob/master/rest/client.py
#
##########################################################################################################

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

    def get_klines(self, market_name: str, resolution: int = 3600, limit: int = 1440,
                   start_time: int = None, end_time: int = None):
        # resolution: window length in seconds: 15, 60, 300, 900, 3600, 14400, 86400
        # limit: max number to fetch, optional, max 5000
        return self._get(f'markets/{market_name}/candles', {'resolution': resolution,
                                                            'limit': limit,
                                                            'start_time': start_time,
                                                            'end_time': end_time})

    def get_trades(self, market_name: str, limit: int = 1440, start_time: int = None, end_time: int = None):
        # resolution: window length in seconds: 15, 60, 300, 900, 3600, 14400, 86400
        # limit: max number to fetch, optional, max 5000
        return self._get(f'markets/{market_name}/trades', {'limit': limit,
                                                           'start_time': start_time,
                                                           'end_time': end_time})


# --------------------------------------------------------------------------------------------------------

# connect to FTX
dir_path = os.getcwd()
ftx_key = {'access': 'TtCuDaRMhZlE_nH_qSnQYWiKF2asdLknFNWXsu2Z',
           'secret': 'n7eSUAR_GtmAxVXgaUiYpEJO6CtGlMTzQlC1QqqU'}
client = FtxClient(api_key=ftx_key['access'],
                   api_secret=ftx_key['secret'])


##########################################################################################################
#
#  Fetch OHLCV function
#
##########################################################################################################

# Get candle stick data from FTX
def FTX_klines(market, interval, limit=2880, start_time=None, end_time=None):
    # make sure limtit is below 5000
    if limit > 5000:
        print(f'Max klines is 5000 per request. Getting 5000 klines instead of {limit}.')
        limit = 5000

    for _ in range(10):
        try:
            temp_dict = client.get_klines(market_name=market, resolution=int(interval * 60),
                                          limit=limit, start_time=start_time, end_time=end_time)
            # print(temp_dict)
        except Exception as e:
            print(e)
            print("Failed to get historical kline. Retrying....")
            time.sleep(2)
        else:
            if len(temp_dict) > 0:
                break
            else:
                time.sleep(1)
    else:  # when all the retries failed
        print("(get_historical_klines_simple) Failed 10 times to get historical kline data.")
        # sys.exit(0)

    # convert to data frame
    df = pd.DataFrame.from_dict(temp_dict)
    df.columns = ['Date UTC', 'TimeStamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype('float64')
    df['Date JST'] = [datetime.fromtimestamp(i / 1000, jst).strftime('%Y-%m-%d %H:%M:%S.%d')[:-3] for i in
                      df['TimeStamp']]  # use JST to convert time
    # change df column order to OHLCV
    df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'TimeStamp', 'Date UTC', 'Date JST']]
    return df


def main():
    first_date = datetime(2019, 9, 23, 0, 0, 0)  # the first day of FTX MOVE contract
    # first_date = datetime(2020, 12, 23, 0, 0, 0)
    last_date = datetime.utcnow()
    delta = timedelta(days=1)

    curr_date = first_date
    while curr_date < last_date:
        sdate = curr_date - delta
        edate = curr_date + delta
        sts = int(time.mktime(sdate.timetuple()) * 1000.0 + sdate.microsecond / 1000.0)
        ets = int(time.mktime(edate.timetuple()) * 1000.0 + sdate.microsecond / 1000.0)
        market = curr_date.strftime('BTC-MOVE-%Y%m%d')
        # if market == 'BTC-MOVE-20201231':
        #    market = 'BTC-MOVE-1231'
        if curr_date.year == 2021:
            market = curr_date.strftime('BTC-MOVE-%m%d')
        print(f'market is {market}')
        df = FTX_klines(market, interval=interval,
                                   limit=2880, start_time=sts, end_time=ets)
        df.to_csv(f'{dir_path}/data/FTX_OHLCV_{curr_date.year}_BTC-MOVE-{curr_date.strftime("%m%d")}_{interval}min.csv')

        curr_date += delta


if __name__ == "__main__":
    main()
