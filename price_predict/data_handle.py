# This is a sample Python script.
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import talib as tb

from other_codes.get_historical_data.huobi_data import Huobi_kline


def huobi_data(target='DOGE-USD', period='1min'):
    start_time = int(datetime.timestamp(datetime(2020, 1, 1)))
    kline = Huobi_kline(symbol=target, period=period, start_time=start_time, get_full_market_data=True)
    filename = target + '_' + period + '.csv'
    kline.to_csv(filename)
    print(kline)

def change_frequence(data, freq=5):
    # new_freq_data = pd.DataFrame(0, columns=data.columns)
    open = data['open'].resample(f'{freq}min').apply(lambda x: x.iloc[0])
    close = data['close'].resample(f'{freq}min').apply(lambda x: x.iloc[-1])
    high = data['high'].resample(f'{freq}min').max()
    low = data['low'].resample(f'{freq}min').min()
    volume = data['volume'].resample(f'{freq}min').sum()
    new_freq_data = pd.concat([open, close, high, low, volume], keys=['open', 'close', 'high', 'low', 'volume'], axis=1)
    print(new_freq_data)
    return new_freq_data

def get_volotility_factor(data, factor=''):
    # 真实波动率 ATR(high, low, close, timeperiod=14)
    re = tb.ATR(data['high'], data['low'], data['close'], timeperiod=14)
    # 归一化波动幅度均值 NATR(high, low, close, timeperiod=5)
    re2 = tb.NATR(data['high'], data['low'], data['close'], timeperiod=14)
    # 真实范围函数 TRANGE(high, low, close), columns=
    re3 = tb.TRANGE(data['high'], data['low'], data['close'])
    vol_data = pd.concat([re, re2, re3], axis=1, keys=['ATR', 'NATR', 'TRANGE'])
    print(vol_data)
    return vol_data


def get_momentum_indicators(data):
    # 1. ADX：平均趋向指数
    ADX = tb.ADX(data['high'], data['low'], data['close'], timeperiod=14)
    # 2. ADXR：平均趋向指数的趋向指数
    ADXR = tb.ADXR(data['high'], data['low'], data['close'], timeperiod=14)
    # 3. APO ：价格震荡指数
    APO = tb.APO(data['close'], fastperiod=12, slowperiod=26, matype=0)
    # 4. AROON ：阿隆指标
    AROON_aroondown, AROON_aroonup = tb.AROON(data['high'], data['low'], timeperiod=14)
    # 5.AROONOSC ：阿隆振荡
    AROONOSC = tb.AROONOSC(data['high'], data['low'], timeperiod=14)
    # 6. BOP ：均势指标
    BOP = tb.BOP(data['open'], data['high'], data['low'], data['close'])
    # 7. CCI ：顺势指标
    CCI = tb.CCI(data['high'], data['low'], data['close'], timeperiod=14)
    # 8. CMO ：钱德动量摆动指标
    CMO = tb.CMO(data['close'], timeperiod=14)
    # 9. DX ：动向指标或趋向指标
    DX = tb.DX(data['high'], data['low'], data['close'], timeperiod=14)
    # 10. MACD:平滑异同移动平均线
    MACD_macd, MACD_macdsignal, MACD_macdhist = tb.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    # 11. MACDEXT :MACD延伸
    MACDEXT_macd, MACDEXT_macdsignal, MACDEXT_macdhist = tb.MACDEXT(data['close'], fastperiod=12, fastmatype=0,
                                                                    slowperiod=26, slowmatype=0, signalperiod=9,
                                                                   signalmatype=0)
    # 12. MFI ：资金流量指标
    MFI = tb.MFI(data['high'], data['low'], data['close'], data['volume'], timeperiod=14)
    # 13. MINUS_DI：DMI 中的DI指标 负方向指标
    MINUS_DI = tb.MINUS_DI(data['high'], data['low'], data['close'], timeperiod=14)
    # 14. MINUS_DM：上升动向值
    MINUS_DM = tb.MINUS_DM(data['high'], data['low'], timeperiod=14)
    # 15.
    fastk, fastd = tb.STOCHRSI(data['close'], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)

    mom_data = pd.concat([ADX, ADXR, APO, AROON_aroondown, AROON_aroonup, AROONOSC, BOP, CCI, CMO, DX, MACD_macd,
                          MACDEXT_macd, MFI, MINUS_DI, MINUS_DM, fastk, fastd], axis=1, keys=['ADX', 'ADXR', 'APO',
                          'AROON_aroondown', 'AROON_aroonup', 'AROONOSC', 'BOP', 'CCI', 'CMO', 'DX', 'MACD_macd',
                          'MACDEXT_macd', 'MFI', 'MINUS_DI', 'MINUS_DM', 'fastk', 'fastd'])
    return mom_data

def get_volume_indicators(data):
    # 三、 量价指标
    # 1. AD:量价指标
    # 参数说明：high:最高价；low:最低价；close:收盘价,volume:成交量
    AD = tb.AD(data['high'], data['low'], data['close'], data['volume'])
    # 2.ADOSC:震荡指标
    # 参数说明：high:最高价；low:最低价；close:收盘价,volume:成交量; fastperiod:快周期； slowperiod：慢周期
    ADOSC = tb.ADOSC(data['high'], data['low'], data['close'], data['volume'], fastperiod=3, slowperiod=10)
    # 3.OBV：能量潮
    # 参数说明：close:收盘价,volume:成交量
    OBV = tb.OBV(data['close'], data['volume'])
    vi_data = pd.concat([AD, ADOSC, OBV], axis=1, keys=['AD', 'ADOSC', 'OBV'])
    return vi_data

def get_cycle_indicators(data):
    # 三、 周期指标
    # 1.HT_DCPERIOD：希尔伯特变换-主导周期
    # 参数说明：close:收盘价
    HT_DCPERIOD = tb.HT_DCPERIOD(data['close'])
    # 2.HT_DCPHASE：希尔伯特变换-主导循环阶段
    # 参数说明：close:收盘价
    HT_DCPHASE = tb.HT_DCPHASE(data['close'])
    # 3.HT_PHASOR：希尔伯特变换-希尔伯特变换相量分量
    # 参数说明：close:收盘价
    HT_PHASOR_inphase, HT_PHASOR_quadrature = tb.HT_PHASOR(data['close'])
    # 4.HT_SINE：希尔伯特变换-正弦波
    # 参数说明：close:收盘价
    HT_SINE_sine, HT_SINE_leadsine = tb.HT_SINE(data['close'])
    # 5.HT_TRENDMODE：希尔伯特变换-趋势与周期模式
    # 参数说明：close:收盘价
    HT_TRENDMODE = tb.HT_TRENDMODE(data['close'])

    cycle_data = pd.concat([HT_DCPERIOD, HT_DCPHASE, HT_PHASOR_inphase, HT_PHASOR_quadrature, HT_SINE_sine, HT_SINE_leadsine,
                            HT_TRENDMODE], axis=1, keys=['HT_1', 'HT_2', 'HT_3', 'HT_4',
                            'HT_5', 'HT_6', 'HT_7'])
    # 'HT_DCPERIOD', 'HT_DCPHASE', 'HT_PHASOR_inphase', 'HT_PHASOR_quadrature', 'HT_SINE_sine', 'HT_SINE_leadsine', 'HT_TRENDMODE'
    return cycle_data

def get_volatility_rate(data):
    # 六、波动率指标
    # 1.MOM： 上升动向值
    # 参数说明：close：收盘价；timeperiod：时间周期
    MOM = tb.MOM(data['close'], timeperiod=10)
    # 2.PLUS_DI
    # 参数说明：high:最高价；low:最低价；close：收盘价；timeperiod：时间周期
    PLUS_DI = tb.PLUS_DI(data['high'], data['low'], data['close'], timeperiod=14)
    # 3.PLUS_DM
    # 参数说明：high:最高价；low:最低价；close：收盘价；timeperiod：时间周期
    PLUS_DM = tb.PLUS_DM(data['high'], data['low'], timeperiod=14)
    # 4. PPO： 价格震荡百分比指数
    # 参数说明：close：收盘价；timeperiod：时间周期，fastperiod:快周期； slowperiod：慢周期
    PPO = tb.PPO(data['close'], fastperiod=12, slowperiod=26, matype=0)
    # 5.ROC：变动率指标
    # 参数说明：close：收盘价；timeperiod：时间周期
    ROC = tb.ROC(data['close'], timeperiod=10)
    # 6. ROCP：变动百分比
    # 参数说明：close：收盘价；timeperiod：时间周期
    ROCP = tb.ROCP(data['close'], timeperiod=10)
    # 7.ROCR ：变动百分率
    # 参数说明：close：收盘价；timeperiod：时间周期
    ROCR = tb.ROCR(data['close'], timeperiod=10)
    # 8. ROCR100 ：变动百分率（*100）
    # 参数说明：close：收盘价；timeperiod：时间周期
    ROCR100 = tb.ROCR100(data['close'], timeperiod=10)
    # 9. RSI：相对强弱指数
    # 参数说明：close：收盘价；timeperiod：时间周期
    RSI = tb.RSI(data['close'], timeperiod=14)
    # 10.STOCH ：随机指标,俗称KD
    # 参数说明：high:最高价；low:最低价；close：收盘价；fastk_period：N参数, slowk_period：M1参数, slowk_matype：M1类型, slowd_period:M2参数, slowd_matype：M2类型
    STOCH_slowk, STOCH_slowd = tb.STOCH(data['high'], data['low'], data['close'], fastk_period=5,
                                           slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    # 11. STOCHF ：快速随机指标
    STOCHF_fastk, STOCHF_fastd = tb.STOCHF(data['high'], data['low'], data['close'], fastk_period=5,
                                              fastd_period=3, fastd_matype=0)
    # 12.TRIX：1-day Rate-Of-Change (ROC) of a Triple Smooth EMA
    TRIX = tb.TRIX(data['close'], timeperiod=30)
    # 13.ULTOSC：终极波动指标
    ULTOSC = tb.ULTOSC(data['high'], data['low'], data['close'], timeperiod1=7, timeperiod2=14, timeperiod3=28)
    # 14.WILLR ：威廉指标
    WILLR = tb.WILLR(data['high'], data['low'], data['close'], timeperiod=14)

    vol_rate_data = pd.concat([MOM, PLUS_DI, PLUS_DM, PPO, ROC, ROCP, ROCR, ROCR100, RSI, STOCH_slowk, STOCH_slowd,
                          STOCHF_fastk, STOCHF_fastd, TRIX, ULTOSC, WILLR], axis=1, keys=['MOM', 'PLUS_DI', 'PLUS_DM',
                        'PPO', 'ROC', 'ROCP', 'ROCR', 'ROCR100', 'RSI', 'STOCH_slowk', 'STOCH_slowd','STOCHF_fastk',
                        'STOCHF_fastd', 'TRIX', 'ULTOSC', 'WILLR'])
    return vol_rate_data


def get_derivative_open(data):
    data['next_open'] = data['open'].shift(-1)  # 第二天的开盘价
    data['d_open'] = data['next_open'] - data['open']
    data['ret'] = np.log(data['open'] / data['open'].shift(1))
    data['next_ret'] = data['ret'].shift(-1)   # 未来/下期 收益率
    return data

def paint_relation(indx, data1, data2, label1='data1', label2='data2'):
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



if __name__ == '__main__':
    # huobi_data(target='btcusdt', period='1min')  # ) # 'BTC-USDT' btcusdt
    data = pd.read_csv(r"C:\pythonProj\data\price_pred\btc_data_200101_220208.csv")
    data = data.set_index('datetime')
    data.index = pd.to_datetime((data.index))
    # 转换频率
    freq = 5
    if freq != 1:
        data = change_frequence(data, freq)
    data = get_derivative_open(data)
    print(data[['open', 'ret', 'next_ret']])

    # 获取各种动量指标、波动率指标
    vol_data = get_volotility_factor(data)
    mom_data = get_momentum_indicators(data)
    # vi_data = get_volume_indicators(data)
    # cycle_data = get_cycle_indicators(data)
    # vol_rate_data = get_volatility_rate(data)
    # # print(pd.concat([vi_data, data], axis=1).corr())
    # print(pd.concat([cycle_data, data], axis=1).corr())
    # print(pd.concat([vol_rate_data, data], axis=1).corr())
    # a == a

    data['d_volume'] = data['volume'].diff()
    # data['e_ATR'] = np.exp(data['ATR'])    , cycle_data, vi_data, vol_rate_data
    train_data = pd.concat([vol_data, mom_data, data], axis=1)
    train_data['d_ATR'] = train_data['ATR'].diff()
    train_data['d_NATR'] = train_data['NATR'].diff()
    train_data['d_TRANGE'] = train_data['TRANGE'].diff()
    if freq == 1:
        # 存入
        train_data.to_csv(r'C:\pythonProj\data\price_pred\t_data.csv')#, index=False)
    else:
        train_data.to_csv(r'C:\pythonProj\data\price_pred\t_data_{}min.csv'.format(freq))#, index=False)
    corr_data = train_data[['BOP', 'CCI', 'CMO', 'fastk', 'fastd', 'MINUS_DI',  # 'ATR', 'NATR', 'TRANGE',
                            'd_open', 'next_open', 'next_ret']].corr()  # BOP CCI CMO fastk fastd 和 d_open 的相关性系数较强
    print(corr_data)
    print(train_data[['ATR', 'NATR', 'TRANGE','d_ATR', 'd_NATR', 'd_TRANGE', 'volume','d_volume','d_open', 'next_open', 'next_ret']].corr())
    # corr_data.to_csv(r'C:\pythonProj\price_predict\corr_data.csv')
    a == a

    target = 'next_ret'
    feat_list = ['BOP', 'CCI', 'CMO', 'fastk', 'fastd', 'MINUS_DI','ATR', 'NATR', 'TRANGE','d_ATR', 'd_NATR', 'd_TRANGE', 'volume','d_volume']
    # print(pd.concat([vol_data, train_data], axis=1).corr())
    # paint_relation(range(len(train_data)), train_data[target], train_data['volume'], target, 'volume')
    for i in feat_list:
        paint_relation(train_data.index, train_data[target], train_data[i], target, i)
    print(tb.get_function_groups()['Momentum Indicators'])
