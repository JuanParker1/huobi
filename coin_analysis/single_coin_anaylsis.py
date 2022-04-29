"""
单币种分析
"""
import numpy as np
from tabulate import tabulate

from exchange_data import *


class CoinAnalysis():
    def __init__(self, target='btcusdt', start_time=None, end_time=None, exchange='huobi', period='5min'):
        m = ExchangeData(coinpair=target, exchange=exchange)
        if not end_time:
            end_time = int(time.time())

        if not start_time:
            c_date = m.get_swap_create_timestamp(m.c_contract)  # 10位的时间戳
            u_date = m.get_swap_create_timestamp(m.u_contract)
            if c_date is None and u_date is None:
                start_time = end_time - 86400 * 365  # 一年前的数据
            else:
                start_time = max(c_date, u_date) + 86400  # 第二天

        spot_data, c_contract_data, u_contract_data = m.get_coin_data(start_time=start_time, end_time=end_time,
                                                                      period=period)  # 'BTC-USDT-SWAP'

        funding_rate = m.get_funding_rate(start_time=start_time, end_time=end_time)
        # spot_data = pd.read_csv(r'C:\pythonProj\data\coin_analysis\{}_spot_{}_{}.csv'.format(exchange, m.spot, period), index_col=0)
        # u_contract_data = pd.read_csv('C:\pythonProj\data\coin_analysis\{}_c_contract_{}_{}.csv'.format(exchange, m.u_contract, period), index_col=0)
        # c_contract_data = pd.read_csv(r'C:\pythonProj\data\coin_analysis\{}_u_contract_{}_{}.csv'.format(exchange, m.c_contract, period), index_col=0)
        # spot_data.index = pd.to_datetime(spot_data.index)
        # c_contract_data.index = pd.to_datetime(c_contract_data.index)
        # u_contract_data.index = pd.to_datetime(u_contract_data.index)
        print(spot_data)
        print(c_contract_data)
        print('funding_rate', funding_rate)

        self.spot_data = spot_data
        self.c_contract_data = c_contract_data
        self.u_contract_data = u_contract_data
        self.funding_rate = funding_rate
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

        date_index = data['open'].resample(freq).first().index  # pd.date_range(start, end, freq=freq)
        new_freq_data = pd.DataFrame(0, columns=data.columns, index=date_index)
        # open = data['open'].resample(freq).first()
        # new_freq_data = pd.DataFrame(open, columns='open', index=open.index)

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
        if len(spot_data) != 0:
            # 合约溢价率： (永续合约 close - 现货 close)/现货 close
            indicators['premium '] = np.divide(data['close'] - spot_data['close'], spot_data['close'])
        indicators = indicators[indicators.columns].astype(float)
        return indicators

    def analyse_indicators(self, indicators):
        analyse_data = indicators.describe(percentiles=[.05, .25, .5, .75, .95])
        analyse_data = analyse_data.drop('count', axis=0)
        print('--' * 30)
        print(analyse_data)
        return analyse_data

    def analyse_all_coin_data(self, period):
        # 现货分析
        new_freq_data = self.adjust_frequence(self.spot_data, freq=period)
        indicators = self.get_indicators(new_freq_data)
        spot_analyse_data = self.analyse_indicators(indicators)
        # 币本位
        c_contract_data = self.adjust_frequence(self.c_contract_data, freq=period)
        indicators = self.get_indicators(c_contract_data, new_freq_data)
        c_analyse_data = self.analyse_indicators(indicators)

        if self.u_contract_data is not None:
            u_contract_data = self.adjust_frequence(self.u_contract_data, freq=period)
            # u本位
            indicators = self.get_indicators(u_contract_data, new_freq_data)
            u_analyse_data = self.analyse_indicators(indicators)
        else:
            u_analyse_data = None
        return spot_analyse_data, c_analyse_data, u_analyse_data

    def describe_funding_rate(self):
        # 近一周, 近一个月, 近三个月, 近半年, 近一年 的 总和
        if self.exchange != 'ftx':
            fr_data = pd.DataFrame(
                0.0, columns=['Coin-Margined Contract', 'USDT-Margined Contract'],
                index=['recent 1 week', 'recent 1 month', 'recent 3 month', 'recent 6 month', 'recent 1 year'])
            fr_data.loc['recent 1 week', :] = self.funding_rate.resample('1W').sum().iloc[-1]
            fr_data.loc['recent 1 month', :] = self.funding_rate.resample('1M').sum().iloc[-1]
            fr_data.loc['recent 3 month', :] = self.funding_rate.resample('3M').sum().iloc[-1]
            fr_data.loc['recent 6 month', :] = self.funding_rate.resample('6M').sum().iloc[-1]
            fr_data.loc['recent 1 year', :] = self.funding_rate.resample('1Y').sum().iloc[-1]
        else:
            fr_data = pd.DataFrame(
                0.0, columns=['Perpetual Contract'],
                index=['recent 1 week', 'recent 1 month', 'recent 3 month', 'recent 6 month', 'recent 1 year'])

            fr_data.loc['recent 1 week', :] = self.funding_rate.resample('1W').sum().iloc[-1, 0]
            fr_data.loc['recent 1 month', :] = self.funding_rate.resample('1M').sum().iloc[-1, 0]
            fr_data.loc['recent 3 month', :] = self.funding_rate.resample('3M').sum().iloc[-1, 0]
            fr_data.loc['recent 6 month', :] = self.funding_rate.resample('6M').sum().iloc[-1, 0]
            fr_data.loc['recent 1 year', :] = self.funding_rate.resample('1Y').sum().iloc[-1, 0]
        return fr_data

    def analyse_and_save_to_txt(self, report_filename='report.txt',
                                periods=['5min', '15min', '30min', '1hour', '4hour', '1day']):
        fr_data = self.describe_funding_rate()

        f = open(report_filename, "a")
        f.write(
            '\n' + f'## {self.exchange.title()} Exchange\n Time Range: from {datetime.fromtimestamp(self.start_time)} '
                   f'to {datetime.fromtimestamp(self.end_time)}' + '\n')
        f.close()

        add_table_to_txt(fr_data, data_name='Funding Rate', file_name=report_filename)

        for period in periods:
            f = open(report_filename, "a")
            f.write('\n' + f'{period} Analyse Result:' + '\n')
            f.close()

            spot_analyse_data, c_analyse_data, u_analyse_data = self.analyse_all_coin_data(period=period)
            add_table_to_txt(spot_analyse_data, data_name='Spot', file_name=report_filename)
            if u_analyse_data is not None:
                add_table_to_txt(c_analyse_data, data_name='Coin-Margined Contract', file_name=report_filename)
                add_table_to_txt(u_analyse_data, data_name='USDT-Margined Contract', file_name=report_filename)
            else:
                add_table_to_txt(c_analyse_data, data_name='Perpetual Contract', file_name=report_filename)
        return spot_analyse_data, c_analyse_data, u_analyse_data

    def test(self, periods=['5min', '15min', '30min', '1hour', '4hour', '1day']):
        fr_data = self.describe_funding_rate()
        print(fr_data)
        for period in periods[1:]:
            spot_analyse_data, c_analyse_data, u_analyse_data = self.analyse_all_coin_data(period=period)
            # print(spot_analyse_data, '\n', c_analyse_data, '\n', u_analyse_data)
        return spot_analyse_data, c_analyse_data, u_analyse_data


def get_list_date_of_exchanges(exchanges=['huobi', 'okx']):
    # 永续合约的上线时间
    list_date = pd.DataFrame(index=exchanges, columns=['Coin-Margined Contract', 'USDT-Margined Contract'])
    for exchange in exchanges:
        m = ExchangeData(coinpair='btcusdt', exchange=exchange)
        c_ts = m.get_swap_create_timestamp(m.c_contract)  # 13位的时间戳
        u_ts = m.get_swap_create_timestamp(m.u_contract)
        if c_ts is not None:
            c_creat_date = datetime.fromtimestamp(c_ts)
            u_creat_date = datetime.fromtimestamp(u_ts)
            list_date.loc[exchange, 'Coin-Margined Contract'] = c_creat_date
            list_date.loc[exchange, 'USDT-Margined Contract'] = u_creat_date
        else:
            list_date.loc[exchange, 'Coin-Margined Contract'] = 'NaN'
            list_date.loc[exchange, 'USDT-Margined Contract'] = 'NaN'
    return list_date


def add_file_title(report_filename, target):
    # 主要信息：币种代码 & 分析的始末时间
    title = f'# Analysis of {target.upper()}'

    # 指标说明
    col_info = 'Introduction of the Indicators:\n' \
               '\t1. open_close_vol = (open - close)/close, represents volatility.\n' \
               '\t2. high_low_vol = (high - low)/low, represents volatility.\n' \
               '\t3. liquid_amount = amount, represents liquidity.\n' \
               '\t4. liquid_volume = volume, represents liquidity.\n' \
               '\t5. premium = [contract(close) - spot(close)]/spot(close), represents the premium of contract over spot.'
    f = open(report_filename, "a")
    f.write(title + '\n\n' + col_info + '\n\n')
    f.close()


def add_table_to_txt(df, data_name='spot', file_name="result_report.txt"):
    t = tabulate(df, headers='keys', tablefmt='psql')
    # 存入 txt
    f = open(file_name, "a")
    f.write(f'{data_name}:' + '\n')
    f.write(str(t) + '\n')
    f.close()


if __name__ == '__main__':
    start_time = int(time.mktime((2022, 4, 15, 0, 0, 0, 0, 0, 0)))
    end_time = int(time.mktime((2022, 4, 26, 0, 0, 0, 0, 0, 0)))
    target = 'btcusdt'  # 现货交易对代码
    exchanges = ['huobi', 'binance', 'okx', 'ftx']

    # 报告的头文件：主要为指标说明
    report_filename = "{}_report.txt".format(target)
    add_file_title(report_filename, target)

    list_date = get_list_date_of_exchanges(exchanges=exchanges)
    add_table_to_txt(list_date, data_name='List Date', file_name=report_filename)

    for exchange in exchanges[3:]:
        c = CoinAnalysis(target=target, exchange=exchange, start_time=start_time, end_time=end_time)  # ,
        c.analyse_and_save_to_txt(report_filename=report_filename)

    # c = CoinAnalysis(target=target, exchange='ftx', start_time=start_time, end_time=end_time)  # ,
    # a, b, d = c.test()
