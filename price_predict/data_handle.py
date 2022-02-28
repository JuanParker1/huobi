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
        self.data['next_close'] = self.data['close'].shift(-1)
        self.data['next_open'] = self.data['open'].shift(-1)  # 第二天的开盘价
        self.data['d_open'] = self.data['next_open'] - self.data['open']
        # self.data['ret'] = np.log(self.data['open'] / self.data['open'].shift(1))
        self.data['next_ret'] = (self.data['next_close'] - self.data['next_open']) / self.data['next_open']  #self.data['ret'].shift(-1)  # 未来/下期 收益率
        self.data['log_next_ret'] = np.log(self.data['next_close'] / self.data['next_open'])
        return self.data

    def get_overlap(self):
        overlap_ind = pd.DataFrame(index=self.data.index)
        # 一、重叠研究（overlap studies）
        # 1.简单移动平均指标SMA
        # 参数说明：talib.SMA(a,b)
        # a:要计算平均数的序列；b:计算平均线的周期。表示计算a的b日移动平均
        close = self.data['close'].values
        overlap_ind['SMA'] = tb.SMA(close, 5)

        # 2.布林线BBANDS
        # 参数说明：talib.BBANDS(close, timeperiod, matype)
        # close:收盘价；timeperiod:周期；matype:平均方法(bolling线的middle线 = MA，用于设定哪种类型的MA)
        # MA_Type: 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3 (Default=SMA)
        overlap_ind['upper'], overlap_ind['middle'], overlap_ind['lower'] = tb.BBANDS(close, 5, matype=tb.MA_Type.EMA)

        # 3. DEMA 双移动平均线:DEMA = 2*EMA-EMA(EMA)
        # 参数说明：talib.DEMA(close, timeperiod = 30)
        overlap_ind['DEMA'] = tb.DEMA(close, timeperiod=30)

        # 4. MA
        # 参数说明：MA(close, timeperiod = 30, matype=0)
        # close:收盘价；timeperiod:周期；matype:计算平均线方法
        overlap_ind['MA'] = tb.MA(close, timeperiod=30, matype=0)

        # 5. EMA
        # 参数说明：EMA = talib.EMA(np.array(close), timeperiod=6)
        # close:收盘价；timeperiod:周期；matype:计算平均线方法
        overlap_ind['EMA'] = tb.EMA(np.array(close), timeperiod=6)

        # 6.KAMA：考夫曼的自适应移动平均线
        # 参数说明：KAMA = talib.KAMA(close, timeperiod = 30)
        overlap_ind['KAMA'] = tb.KAMA(close, timeperiod=30)

        # 7. MIDPRICE：阶段中点价格
        # talib.MIDPOINT(close, timeperiod)
        # 参数说明：close:收盘价；timeperiod:周期；
        overlap_ind['MIDPOINT'] = tb.MIDPOINT(close, timeperiod=14)

        # 8.SAR：抛物线指标
        # SAR(high, low, acceleration=0, maximum=0)
        # 参数说明：high：最高价；low:最低价；acceleration：加速因子；maximum：极点价
        overlap_ind['SAR'] = tb.SAR(self.data['high'].values, self.data['low'].values, acceleration=0, maximum=0)

        # 9.MIDPRICE：阶段中点价格（Midpoint Price over period）
        # talib.MIDPOINT(close, timeperiod=14)
        # 参数说明：close:收盘价；timeperiod:周期；
        overlap_ind['MIDPOINT'] = tb.MIDPOINT(close, timeperiod=14)

        # 10. T3:三重移动平均线
        # talib.T3(close, timeperiod=5, vfactor=0)
        # 参数说明：close:收盘价；timeperiod:周期；vfactor: va 系数，当va=0时，T3就是三重移动平均线；va=1时，就是DEMA
        overlap_ind['T3'] = tb.T3(close, timeperiod=5, vfactor=0)

        # 11.TEMA：三重指数移动平均线
        # talib.TEMA(close, timeperiod = 30)
        # 参数说明：close:收盘价；timeperiod:周期；
        overlap_ind['TEMA'] = tb.TEMA(close, timeperiod=30)

        # 12.SAREXT:SAR的抛物面扩展
        # talib.SAREXT(high_p, low_p, startvalue=0, offsetonreverse=0, accelerationinitlong=0, accelerationlong=0, accelerationmaxlong=0, accelerationinitshort=0, accelerationshort=0, accelerationmaxshort=0)
        overlap_ind['SAREXT'] = tb.SAREXT(self.data['high'].values, self.data['low'].values, startvalue=0, offsetonreverse=0,
                              accelerationinitlong=0, accelerationlong=0, accelerationmaxlong=0,
                              accelerationinitshort=0, accelerationshort=0, accelerationmaxshort=0)

        # 13.WMA：移动加权平均法
        # talib.WMA(close, timeperiod = 30)
        # 参数说明：close:收盘价；timeperiod:周期；
        overlap_ind['WMA'] = tb.WMA(close, timeperiod=30)
        return overlap_ind

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

    def get_cycle(self):
        cycle_data = pd.DataFrame(index=self.data.index)
        # 三、 周期指标
        # 1.HT_DCPERIOD：希尔伯特变换-主导周期
        # HT_DCPERIOD(close)
        # 参数说明：close:收盘价
        cycle_data['HT_DCPERIOD'] = tb.HT_DCPERIOD(self.data['close'])

        # 2.HT_DCPHASE：希尔伯特变换-主导循环阶段
        # HT_DCPHASE(close)
        # 参数说明：close:收盘价
        cycle_data['HT_DCPHASE'] = tb.HT_DCPHASE(self.data['close'])

        # 3.HT_PHASOR：希尔伯特变换-希尔伯特变换相量分量
        # inphase, quadrature = HT_PHASOR(close)
        # 参数说明：close:收盘价
        cycle_data['HT_PHASOR_inphase'], cycle_data['HT_PHASOR_quadrature'] = tb.HT_PHASOR(self.data['close'])

        # 4.HT_SINE：希尔伯特变换-正弦波
        # sine, leadsine = HT_SINE(close)
        # 参数说明：close:收盘价
        cycle_data['HT_SINE_sine'], cycle_data['HT_SINE_leadsine'] = tb.HT_SINE(self.data['close'])

        # 5.HT_TRENDMODE：希尔伯特变换-趋势与周期模式
        # integer = HT_TRENDMODE(close)
        # 参数说明：close:收盘价
        cycle_data['HT_TRENDMODE'] = tb.HT_TRENDMODE(self.data['close'])

        # 四、价格变化函数
        # 1. AVGPRICE：平均价格函数
        # real = AVGPRICE(open, high, low, close)
        cycle_data['AVGPRICE'] = tb.AVGPRICE(self.data['open'].values, self.data['high'].values, self.data['low'].values, self.data['close'])

        # 2. MEDPRICE:中位数价格
        # real = MEDPRICE(high, low)
        # 参数说明：high:最高价；low:最低价；
        cycle_data['MEDPRICE'] = tb.MEDPRICE(self.data['high'].values, self.data['low'].values)

        # 3. TYPPRICE ：代表性价格
        # real = TYPPRICE(high, low, close)
        # 参数说明：high:最高价；low:最低价；close：收盘价
        cycle_data['TYPPRICE'] = tb.TYPPRICE(self.data['high'].values, self.data['low'].values, self.data['close'])

        # 4. WCLPRICE ：加权收盘价
        # real = WCLPRICE(high, low, close)
        # 参数说明：high:最高价；low:最低价；close：收盘价
        cycle_data['WCLPRICE'] = tb.WCLPRICE(self.data['high'].values, self.data['low'].values, self.data['close'])

        return cycle_data

    def get_statistic(self):
        stat_data = pd.DataFrame(index=self.data.index)
        # 七、Statistic Functions 统计学指标
        # 1. BETA：β系数也称为贝塔系数
        # real = BETA(high, low, timeperiod=5)
        stat_data['BETA'] = tb.BETA(self.data['high'].values, self.data['low'].values, timeperiod=5)

        # 2. CORREL ：皮尔逊相关系数
        # real = CORREL(high, low, timeperiod=30)
        stat_data['CORREL'] = tb.CORREL(self.data['high'].values, self.data['low'].values, timeperiod=30)

        # 3.LINEARREG ：线性回归
        # real = LINEARREG(close, timeperiod=14)
        stat_data['LINEARREG'] = tb.LINEARREG(self.data['close'], timeperiod=14)

        # 4.LINEARREG_ANGLE ：线性回归的角度
        # real = LINEARREG_ANGLE(close, timeperiod=14)
        stat_data['LINEARREG_ANGLE'] = tb.LINEARREG_ANGLE(self.data['close'], timeperiod=14)

        # 5. LINEARREG_INTERCEPT ：线性回归截距
        # real = LINEARREG_INTERCEPT(close, timeperiod=14)
        stat_data['LINEARREG_INTERCEPT'] = tb.LINEARREG_INTERCEPT(self.data['close'], timeperiod=14)

        # 6.LINEARREG_SLOPE：线性回归斜率指标
        # real = LINEARREG_SLOPE(close, timeperiod=14)
        stat_data['LINEARREG_SLOPE'] = tb.LINEARREG_SLOPE(self.data['close'], timeperiod=14)

        # 7.STDDEV ：标准偏差
        # real = STDDEV(close, timeperiod=5, nbdev=1)
        stat_data['STDDEV'] = tb.STDDEV(self.data['close'], timeperiod=5, nbdev=1)

        # 8.TSF：时间序列预测
        # real = TSF(close, timeperiod=14)
        stat_data['TSF'] = tb.TSF(self.data['close'], timeperiod=14)

        # 9. VAR：方差
        # real = VAR(close, timeperiod=5, nbdev=1)
        stat_data['VAR'] = tb.VAR(self.data['close'], timeperiod=5, nbdev=1)
        return stat_data


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

    def data_analyse(self, target=['next_ret']):
        self.get_derivative_open()

        # 获取各种动量指标、波动率指标
        vol_data = self.get_volotility_factor()
        mom_data = self.get_momentum_indicators()
        vi_data = self.get_volume_indicators()
        overlap_data = self.get_overlap()
        stat_data = self.get_statistic()

        features = list(vol_data.columns) + list(mom_data.columns) + list(vi_data.columns) + list(overlap_data.columns) \
                   + list(stat_data.columns) + ['volume']
        corr_col = features + target
        self.data = pd.concat([vol_data, mom_data, vi_data, overlap_data, stat_data, self.data], axis=1)
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
    train_data = get_data.data_analyse(target=['next_ret', 'log_next_ret'])

    # target = 'next_ret'
    # feat_list = ['BOP', 'CCI', 'CMO', 'fastk', 'fastd', 'MINUS_DI', 'ATR', 'NATR', 'TRANGE', 'volume']
    # for i in feat_list:
    #     paint_relation(train_data.index, train_data[target], train_data[i], target, i)
