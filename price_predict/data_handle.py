import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

import talib as tb

from other_codes.get_historical_data.huobi_data import Huobi_kline


# 用 huobi api 获取数据 TODO 报错
def huobi_data(target='btcusdt', period='1min'):
    start_time = int(datetime.timestamp(datetime(2020, 1, 1)))
    kline = Huobi_kline(symbol=target, period=period, start_time=start_time, get_full_market_data=True)
    filename = target + '_' + period + '.csv'
    kline.to_csv(filename)
    print(kline)


class GetData():
    def __init__(self, file_path=r"C:\pythonProj\data\price_pred\btc_data_200101_220208.csv", freq=1):
        """
        Args:
            file_path: 文件路径
            freq: 数据频率，默认为 1min频
        """
        # 获取原始 1min频率 数据
        data = self.get_initial_data(file_path)
        # 转换频率
        if freq != 1:
            self.data = self.change_frequence(data, freq)
        else:
            self.data = data
        self.freq = freq
        self.path = os.path.split(file_path)[0]  # 获取数据存储的根目录

    # 获取原始 1min频率 数据，设置时间为index
    def get_initial_data(self, file_path):
        data = pd.read_csv(file_path)
        data = data.set_index('datetime')
        data.index = pd.to_datetime((data.index))
        return data

    def save_final_data(self):
        if self.freq == 1:
            save_path = os.path.join(self.path, 't_data.csv')
        else:
            save_path = os.path.join(self.path, 't_data_{}min.csv'.format(self.freq))
        self.data.to_csv(save_path)

    # 转换数据频率
    def change_frequence(self, data, freq=5):
        open = data['open'].resample(f'{freq}min').apply(lambda x: x.iloc[0])
        close = data['close'].resample(f'{freq}min').apply(lambda x: x.iloc[-1])
        high = data['high'].resample(f'{freq}min').max()
        low = data['low'].resample(f'{freq}min').min()
        volume = data['volume'].resample(f'{freq}min').sum()
        new_freq_data = pd.concat([open, close, high, low, volume], keys=['open', 'close', 'high', 'low', 'volume'], axis=1)
        return new_freq_data


    def get_derivative_open(self):
        self.data['next_open'] = self.data['open'].shift(-1)  # 第二天的开盘价
        self.data['d_open'] = self.data['next_open'] - self.data['open']
        self.data['ret'] = np.log(self.data['open'] / self.data['open'].shift(1))
        self.data['next_ret'] = self.data['ret'].shift(-1)  # 未来/下期 收益率
        return self.data

    def get_volotility_factor(self):
        # 真实波动率 ATR(high, low, close, timeperiod=14)
        re = tb.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        # 归一化波动幅度均值 NATR(high, low, close, timeperiod=5)
        re2 = tb.NATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        # 真实范围函数 TRANGE(high, low, close), columns=
        re3 = tb.TRANGE(self.data['high'], self.data['low'], self.data['close'])
        vol_data = pd.concat([re, re2, re3], axis=1, keys=['ATR', 'NATR', 'TRANGE'])
        return vol_data

    def get_momentum_indicators(self):
        # 1. ADX：平均趋向指数
        ADX = tb.ADX(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        # 2. ADXR：平均趋向指数的趋向指数
        ADXR = tb.ADXR(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        # 3. APO ：价格震荡指数
        APO = tb.APO(self.data['close'], fastperiod=12, slowperiod=26, matype=0)
        # 4. AROON ：阿隆指标
        AROON_aroondown, AROON_aroonup = tb.AROON(self.data['high'], self.data['low'], timeperiod=14)
        # 5.AROONOSC ：阿隆振荡
        AROONOSC = tb.AROONOSC(self.data['high'], self.data['low'], timeperiod=14)
        # 6. BOP ：均势指标
        BOP = tb.BOP(self.data['open'], self.data['high'], self.data['low'], self.data['close'])
        # 7. CCI ：顺势指标
        CCI = tb.CCI(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        # 8. CMO ：钱德动量摆动指标
        CMO = tb.CMO(self.data['close'], timeperiod=14)
        # 9. DX ：动向指标或趋向指标
        DX = tb.DX(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        # 10. MACD:平滑异同移动平均线
        MACD_macd, MACD_macdsignal, MACD_macdhist = tb.MACD(self.data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        # 11. MACDEXT :MACD延伸
        MACDEXT_macd, MACDEXT_macdsignal, MACDEXT_macdhist = tb.MACDEXT(self.data['close'], fastperiod=12, fastmatype=0,
                                                            slowperiod=26, slowmatype=0, signalperiod=9, signalmatype=0)
        # 12. MFI ：资金流量指标
        MFI = tb.MFI(self.data['high'], self.data['low'], self.data['close'], self.data['volume'], timeperiod=14)
        # 13. MINUS_DI：DMI 中的DI指标 负方向指标
        MINUS_DI = tb.MINUS_DI(self.data['high'], self.data['low'], self.data['close'], timeperiod=14)
        # 14. MINUS_DM：上升动向值
        MINUS_DM = tb.MINUS_DM(self.data['high'], self.data['low'], timeperiod=14)
        # 15.
        fastk, fastd = tb.STOCHRSI(self.data['close'], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)

        mom_data = pd.concat([ADX, ADXR, APO, AROON_aroondown, AROON_aroonup, AROONOSC, BOP, CCI, CMO, DX, MACD_macd,
                              MACDEXT_macd, MFI, MINUS_DI, MINUS_DM, fastk, fastd], axis=1,
                             keys=['ADX', 'ADXR', 'APO', 'AROON_aroondown', 'AROON_aroonup', 'AROONOSC', 'BOP',
                                   'CCI', 'CMO', 'DX', 'MACD_macd', 'MACDEXT_macd', 'MFI', 'MINUS_DI',
                                   'MINUS_DM', 'fastk', 'fastd'])
        return mom_data

    def get_volume_indicators(self):
        # 1. AD:量价指标
        # 参数说明：high:最高价；low:最低价；close:收盘价,volume:成交量
        AD = tb.AD(self.data['high'], self.data['low'], self.data['close'], self.data['volume'])
        # 2.ADOSC:震荡指标
        # 参数说明：high:最高价；low:最低价；close:收盘价,volume:成交量; fastperiod:快周期； slowperiod：慢周期
        ADOSC = tb.ADOSC(self.data['high'], self.data['low'], self.data['close'], self.data['volume'], fastperiod=3, slowperiod=10)
        # 3.OBV：能量潮
        # 参数说明：close:收盘价,volume:成交量
        OBV = tb.OBV(self.data['close'], self.data['volume'])
        vi_data = pd.concat([AD, ADOSC, OBV], axis=1, keys=['AD', 'ADOSC', 'OBV'])
        return vi_data

    def data_analyse(self, target='next_ret'):
        self.get_derivative_open()

        # 获取各种动量指标、波动率指标
        vol_data = self.get_volotility_factor()
        mom_data = self.get_momentum_indicators()
        # vi_data = self.get_volume_indicators()

        features = list(vol_data.columns) + list(mom_data.columns)
        corr_col = features + [target]
        self.data = pd.concat([vol_data, mom_data, self.data], axis=1)
        print('correlation: \n', self.data[corr_col].corr())
        self.save_final_data()
        return self.data


def paint_relation(indx, data1, data2, label1='data1', label2='data2'):
    """
    绘制折线图，看两数据之间的相关性

    Args:
        indx: 图片 x轴
        data1: 数据 1
        data2: 数据 2
        label1: 数据 1 的标签
        label2: 数据 2 的标签
    """
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
    fig, ax1 = plt.subplots()

    # 双轴
    ax1.plot(indx, data1, 'r-', label=label1)
    ax1.set_ylabel(label1)
    ax2 = ax1.twinx()
    ax2.plot(indx, data2, 'b-', label=label2)
    ax2.set_ylabel(label2)

    # 图例
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    plt.legend(handles1 + handles2, labels1 + labels2, loc='upper right')
    plt.show()
    plt.close()


if __name__ == '__main__':
    # 获取数据
    get_data = GetData(file_path=r"C:\pythonProj\data\price_pred\btc_data_200101_220208.csv", freq=1)
    train_data = get_data.data_analyse(target='next_ret')

    target = 'next_ret'
    feat_list = ['BOP', 'CCI', 'CMO', 'fastk', 'fastd', 'MINUS_DI', 'ATR', 'NATR', 'TRANGE', 'volume']
    for i in feat_list:
        paint_relation(train_data.index, train_data[target], train_data[i], target, i)
