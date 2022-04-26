"""
单币种分析
"""
import numpy as np
import pandas as pd
from tabulate import tabulate
import time
import requests

from api_and_ding.get_market_data.okx_data import *
from other_codes.get_historical_data.huobi_data import Huobi_kline
from exchange_data import *


def get_contract_code(spot_code, exchange='huobi'):
    """ 获取现货交易对的永续合约代码

    Args:
        spot_code: 现货交易对代码

    Returns:
        币本位永续合约代码，U 本位永续合约代码
    """
    if exchange=='huobi':
        c_contract = spot_code[:-4].upper() + '-' + spot_code[-4:-1].upper()  # 币本位永续 XXX-USD
        u_contract = spot_code[:-4].upper() + '-' + spot_code[-4:].upper()  # U 本位永续 XXX-USDT
    elif exchange == 'okx':
        c_contract = spot_code[:-4].upper() + '-' + spot_code[-4:-1].upper()  # 币本位永续 XXX-USD
        u_contract = spot_code[:-4].upper() + '-' + spot_code[-4:].upper()
    return c_contract, u_contract

def get_coin_data(target='btcusdt', start_time=None, end_time=None, period='5min', exchange='huobi'):
    if exchange=='huobi':
        spot_data = Huobi_kline(symbol=target, period=period, start_time=start_time, end_time=end_time,
                                get_full_market_data=True, col_with_asset_name=False)
        # spot_data.to_csv(r'C:\pythonProj\coin_analysis\spot_{}_{}.csv'.format(target, period))
        try:
            c_contract, u_contract = get_contract_code(spot_code=target)
            c_contract_data = Huobi_kline(symbol=c_contract, period=period, start_time=start_time, end_time=end_time,
                                          get_full_market_data=True, col_with_asset_name=False)
            u_contract_data = Huobi_kline(symbol=u_contract, period=period, start_time=start_time, end_time=end_time,
                                          get_full_market_data=True, col_with_asset_name=False)
            # u_contract_data.to_csv(r'C:\pythonProj\coin_analysis\u_contract_{}_{}.csv'.format(target, period))
            # c_contract_data.to_csv(r'C:\pythonProj\coin_analysis\c_contract_{}_{}.csv'.format(target, period))
            return spot_data, c_contract_data, u_contract_data
        except KeyError:
            print('无相关合约')
            return spot_data, None, None
    elif exchange=='okx':
        spot_data = OKX_kline(target=target, contract_type='spot', interval=period, start_time=start_time,
                              end_time=end_time, is_fr=False)
        spot_data.to_csv(r'C:\pythonProj\coin_analysis\{}_spot_{}_{}.csv'.format(exchange, target, period))
        try:
            c_contract_data = OKX_kline(target=target[:-1], contract_type='swap', interval=period, start_time=start_time,
                                        end_time=end_time, is_fr=False)
            u_contract_data = OKX_kline(target=target, contract_type='swap', interval=period, start_time=start_time,
                                        end_time=end_time, is_fr=False)
            u_contract_data.to_csv(r'C:\pythonProj\coin_analysis\{}_u_contract_{}_{}.csv'.format(exchange, target, period))
            c_contract_data.to_csv(r'C:\pythonProj\coin_analysis\{}_c_contract_{}_{}.csv'.format(exchange, target, period))
            return spot_data, c_contract_data, u_contract_data
        except KeyError:
            print('无相关合约')
            return spot_data, None, None

def get_funding_rate(spot_code='btcusdt', start_time=None, end_time=None, exchange='huobi',  period='4hour'):
    """ 获取现货合约对于的 币本位、U本位永续合约的资金费率

    Args:
        target: 现货合约代码

    Returns:
        dataframe
    """
    c_contract, u_contract = get_contract_code(spot_code=spot_code)
    if exchange == 'huobi':
        try:
            c_contract_fr = Huobi_kline(symbol=c_contract, period=period, start_time=start_time, end_time=end_time,
                                        is_fr=True, col_with_asset_name=False)
            u_contract_fr = Huobi_kline(symbol=u_contract, period=period, start_time=start_time, end_time=end_time,
                                        is_fr=True, col_with_asset_name=False)
            # u_contract_data.to_csv(r'C:\pythonProj\coin_analysis\u_contract_{}_{}.csv'.format(target, period))
            # c_contract_data.to_csv(r'C:\pythonProj\coin_analysis\c_contract_{}_{}.csv'.format(target, period))
            print(c_contract_fr)
            print(u_contract_fr)
            c_contract_fr_close = c_contract_fr['close'].resample('8H').last()
            u_contract_fr_close = u_contract_fr['close'].resample('8H').last()
            funding_rate = pd.concat([c_contract_fr_close, u_contract_fr_close], axis=1,
                                     keys=['Coin-Margined Contract', 'USDT-Margined Contract'])
            return funding_rate
        except KeyError:
            print('为获取到相关合约')
            return None, None
    elif exchange == 'okx':
        try:
            c_contract_fr = OKX_kline(target=spot_code[:-1], interval='4H', start_time=start_time, end_time=end_time,
                                        is_fr=True)
            u_contract_fr = OKX_kline(target=spot_code, interval='4H', start_time=start_time, end_time=end_time,
                                        is_fr=True)
            # u_contract_data.to_csv(r'C:\pythonProj\coin_analysis\u_contract_{}_{}.csv'.format(target, period))
            # c_contract_data.to_csv(r'C:\pythonProj\coin_analysis\c_contract_{}_{}.csv'.format(target, period))
            print(c_contract_fr)
            print(u_contract_fr)
            c_contract_fr_close = c_contract_fr['close'].resample('8H').last()
            u_contract_fr_close = u_contract_fr['close'].resample('8H').last()
            funding_rate = pd.concat([c_contract_fr_close, u_contract_fr_close], axis=1,
                                     keys=['Coin-Margined Contract', 'USDT-Margined Contract'])
            return funding_rate
        except KeyError:
            print('为获取到相关合约')
            return None, None

class CoinAnalysis():
    def __init__(self, target='btcusdt', start_time=None, end_time=None, exchange='huobi', period='5min'):
        """

        Args:
            target:
            start_time:
            end_time:
            period:
        """
        c_contract, u_contract = get_contract_code(spot_code=target)
        if not start_time:
            c_date = get_create_timestamp(c_contract, exchange=exchange)
            u_date = get_create_timestamp(u_contract, exchange=exchange)
            start_time = max(int(c_date), int(u_date)) // 1000 + 86400  # 第二天
        if not end_time:
            end_time = int(time.time())
        # print(datetime.(start_time))
        spot_data, c_contract_data, u_contract_data = get_coin_data(target=target, start_time=start_time,
                                                                    end_time=end_time, period=period, exchange=exchange)

        # spot_data = pd.read_csv('spot_btcusdt_5min.csv', index_col=0)
        # c_contract_data = pd.read_csv('c_contract_btcusdt_5min.csv', index_col=0)
        # u_contract_data = pd.read_csv('u_contract_btcusdt_5min.csv', index_col=0)
        # spot_data.index = pd.to_datetime(spot_data.index)
        # c_contract_data.index = pd.to_datetime(c_contract_data.index)
        # u_contract_data.index = pd.to_datetime(u_contract_data.index)

        self.spot_data = spot_data
        self.c_contract_data = c_contract_data
        self.u_contract_data = u_contract_data
        self.start_time = start_time
        self.end_time = end_time
        self.target = target
        self.exchange = exchange

    # @staticmethod
    def adjust_frequence(self, data, freq='10min'):
        if freq == '5min':
            return data

        start = data.index[0]
        end = data.index[-1]

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

    def get_indicators(self, data, spot_data=[]):
        """ 获取指标数据 eg.流动性、波动率(、溢价率)

        Args:
            data: 现货数据 或 永续合约数据
            spot_data: 可选。若输入data为永续合约，则此处需要输入现货数据（以计算溢价率）

        Returns:
            dataframe
        """
        # 波动率指标
        indicators = self.get_volatility(data)
        # 流动性指标
        indicators['liquid_amount'] = data['amount']
        indicators['liquid_volume'] = data['volume']
        if len(spot_data)!=0:
            # 合约溢价率： (永续合约 close - 现货 close)/现货 close
            indicators['premium '] = np.divide(data['close'] - spot_data['close'], spot_data['close'])
        return indicators

    def analyse_indicators(self, indicators):
        analyse_data = indicators.describe(percentiles=[.05, .25, .5, .75, .95])
        analyse_data = analyse_data.drop('count', axis=0)
        return analyse_data

    def analyse_all_coin_data(self, period):
        u_contract_data = self.adjust_frequence(self.u_contract_data, freq=period)
        c_contract_data = self.adjust_frequence(self.c_contract_data, freq=period)
        new_freq_data = self.adjust_frequence(self.spot_data, freq=period)
        # 现货分析
        indicators = self.get_indicators(new_freq_data)
        spot_analyse_data = self.analyse_indicators(indicators)
        # 币本位
        indicators = self.get_indicators(c_contract_data, new_freq_data)
        c_analyse_data = self.analyse_indicators(indicators)
        # u本位
        indicators = self.get_indicators(u_contract_data, new_freq_data)
        u_analyse_data = self.analyse_indicators(indicators)
        return spot_analyse_data, c_analyse_data, u_analyse_data

    def describe_funding_rate(self):
        funding_rate = get_funding_rate(spot_code=self.target, start_time=self.start_time, end_time=self.end_time)
        # 近一周, 近一个月, 近三个月, 近半年, 近一年 的 总和
        fr_data = pd.DataFrame(0.0, columns=['Coin-Margined Contract', 'USDT-Margined Contract'],
                               index=['recent 1 week', 'recent 1 month', 'recent 3 month', 'recent 6 month',
                                      'recent 1 year'])

        fr_data.loc['recent 1 week', :] = funding_rate.resample('1W').sum().iloc[-1]
        fr_data.loc['recent 1 month', :] = funding_rate.resample('1M').sum().iloc[-1]
        fr_data.loc['recent 3 month', :] = funding_rate.resample('3M').sum().iloc[-1]
        fr_data.loc['recent 6 month', :] = funding_rate.resample('6M').sum().iloc[-1]
        fr_data.loc['recent 1 year', :] = funding_rate.resample('1Y').sum().iloc[-1]
        return fr_data

    def analyse(self, periods=['5min', '15min', '30min', '1hour', '4hour', '1day']):
        report_filename = "{}_report.txt".format(self.target)
        add_file_title(report_filename, self.exchange, self.target, self.start_time, self.end_time)

        fr_data = self.describe_funding_rate()
        add_table_to_txt(fr_data, data_name='Funding Rate', file_name=report_filename)

        for period in periods:
            f = open(report_filename, "a")
            f.write('\n' + f'{period} Analyse Result:' + '\n')
            f.close()

            spot_analyse_data, c_analyse_data, u_analyse_data = self.analyse_all_coin_data(period=period)
            add_table_to_txt(spot_analyse_data, period=period, data_name='Spot', file_name=report_filename)
            add_table_to_txt(c_analyse_data, period=period, data_name='Coin-Margined Contract', file_name=report_filename)
            add_table_to_txt(u_analyse_data, period=period, data_name='USDT-Margined Contract', file_name=report_filename)
        return spot_analyse_data, c_analyse_data, u_analyse_data


def get_create_timestamp(symbol, exchange='huobi'):
    if exchange=='huobi':
        creat_date = get_huobi_creat_date(symbol)
    elif exchange=='okx':
        creat_date = get_okx_create_date(symbol)
    return creat_date

def get_huobi_creat_date(symbol='BTC-USDT'):
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


def add_file_title(report_filename, exchange, target, start_time, end_time):
    # 主要信息：币种代码 & 分析的始末时间
    print(start_time, end_time)
    print(datetime.fromtimestamp(start_time))
    title = f'{target}: {datetime.fromtimestamp(start_time)} - {datetime.fromtimestamp(end_time)}'
    # 永续合约的上线时间
    c_contract, u_contract = get_contract_code(spot_code=target)
    c_creat_date = get_create_timestamp(c_contract, exchange)
    u_creat_date = get_create_timestamp(u_contract, exchange)
    contract_createdate = f'{c_contract}(Coin-M) listed @ {c_creat_date}; {u_contract}(USDT-M) listed @ {u_creat_date}'
    # 指标说明
    col_info = 'Introduction of the Indicators:\n' \
               '\t1. open_close_vol = (open - close)/close, represents volatility.\n' \
               '\t2. high_low_vol = (high - low)/low, represents volatility.\n' \
               '\t3. liquid_amount = amount, represents liquidity.\n' \
               '\t4. liquid_volume = volume, represents liquidity.\n' \
               '\t5. premium = [contract(close) - spot(close)]/spot(close), represents the premium of contract over spot.\n'
    f = open(report_filename, "a")
    f.write(title + '\n\n' + contract_createdate + '\n\n' + col_info)
    f.close()


def add_table_to_txt(df, data_name='spot', file_name="result_report.txt"):
    t = tabulate(df, headers='keys', tablefmt='psql')
    # 存入 txt
    f = open(file_name, "a")
    f.write(f'{data_name}:' + '\n')
    f.write(str(t) + '\n')
    f.close()


if __name__ == '__main__':
    m = MarketKline(coinpair='btcusdt', exchange='huobi')
    spot, c_swap, u_swap = m.get_coin_data(period='5min')
    funding_rate = m.get_funding_rate()
    print(spot, '\n', c_swap, '\n', u_swap)
    print(funding_rate)

    start_time = int(time.mktime((2022, 1, 1, 0, 0, 0, 0, 0, 0)))
    end_time = int(time.mktime((2022, 4, 20, 0, 0, 0, 0, 0, 0)))
    print(end_time, int(time.time()))
    target = 'btcusdt'  # 现货交易对代码

    c = CoinAnalysis(target=target, exchange='okx')  # start_time=start_time, end_time=end_time,
    c.analyse()
    c.describe_funding_rate()

    # d = get_create_date(symbol='BTC-USDT', exchange='huobi', )
    # print(d)