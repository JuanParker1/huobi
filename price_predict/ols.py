import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import talib as tb

from sklearn.model_selection import train_test_split
import statsmodels.api as sm
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.graphics.api import qqplot

from data_handle import paint_relation

def max_min_normalize(data):
    scaler = MinMaxScaler(feature_range=(-1, 1))
    for col in data.columns:        # 这里不能进行统一进行缩放，因为fit_transform返回值是numpy类型
        data[col] = scaler.fit_transform(data[col].values.reshape(-1, 1))
    #data.to_csv(r"C:\pythonProj\price_predict\t_data_normalized.csv")
    return data


# 移动平均图
def draw_trend(timeSeries, size):
    f = plt.figure(facecolor='white')
    # 对size个数据进行移动平均
    rol_mean = timeSeries.rolling(window=size).mean()
    # 对size个数据进行加权移动平均
    rol_weighted_mean = timeSeries.ewm(span=size).mean()
    print(rol_weighted_mean)

    timeSeries.plot(color='blue', label='Original')
    rol_mean.plot(color='red', label='Rolling Mean')
    rol_weighted_mean.plot(color='black', label='Weighted Rolling Mean')
    plt.legend(loc='best')
    plt.title('Rolling Mean')
    plt.show()

def describe_period(data, startdt = datetime.datetime(2020, 3, 12, 0, 0), enddt = datetime.datetime(2020, 3, 13, 0, 0)):
    # 截取数据
    period_data = data.loc[data[(data.index > startdt) & (data.index < enddt)].index, :]

    target = 'next_ret'
    print(period_data[['BOP', 'next_ret']].corr())
    print('describe next_ret:\n', period_data[['BOP', 'next_ret']].describe())
    # print('describe BOP     :\n', period_data['BOP'].describe())
    paint_relation(pd.to_datetime(period_data.index), period_data['BOP'], period_data[target], 'BOP', target)


def build_linear_model(data_, target='d_open', feat_list=['ATR', 'd_volume', 'BOP'], train_size=0.6):
    X = data_[feat_list]  # ATR NATR TRANGE  # # BOP CCI CMO fastk fastd MINUS_DI 和 d_open 的相关性系数较强
    y = data_[target]  # d_open ret
    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, shuffle=False)  # 划分训练集和测试集
    train_ind = int(len(X) * train_size)
    X_train = X[:train_ind]
    X_test = X[train_ind:]
    y_train = y[:train_ind]
    y_test = y[train_ind:]

    # regr = linear_model.LinearRegression()
    # model = regr.fit(X_train, y_train)  # (x[:100000], y[:100000])
    # print('Mean squared error: %.4f' % mean_squared_error(y_test, regr.predict(X_test)))
    # print('R2 score: %.4f' % r2_score(y_test, regr.predict(X_test)))
    # print('score', regr.score(X_test, y_test))

    # X = sm.add_constant(x)
    model = sm.OLS(y_train, sm.add_constant(X_train)).fit()
    # 查看模型结果
    print(model.summary())
    # print('Mean squared error: %.4f' % mean_squared_error(y_test, model.predict(sm.add_constant(X_test))))
    return model, X_train, X_test, y_train, y_test

def draw_fit(y_pred, y):
    ## 预测值和实际值画图比较
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

    plt.figure(facecolor='w')  # 建一个画布，facecolor是背景色
    plt.plot(y.index, y, 'r-', linewidth=1.5, label='真实值')
    plt.plot(y_pred.index, y_pred, 'g-', linewidth=1, label='预测值')
    plt.legend(loc='upper left')  # 显示图例，设置图例的位置
    plt.title("线性回归预测真实值之间的关系", fontsize=20)
    plt.grid(visible=True)  # 加网格
    plt.show()

def draw_next_open(Y, y_pred_transf):
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

    plt.figure(facecolor='w')  # 建一个画布，facecolor是背景色
    plt.plot(Y.index, Y, 'r-', linewidth=1.5, label='真实值')
    plt.plot(y_pred_transf.index, y_pred_transf, 'g-', linewidth=1, label='预测值')
    plt.legend(loc='upper left')  # 显示图例，设置图例的位置
    plt.title("线性回归预测真实值之间的关系", fontsize=20)
    plt.grid(visible=True)  # 加网格
    plt.show()

def draw_next_open_fit_local(Y, y_pred_transf, startdt=datetime.datetime(2021,6,1,0,0), enddt=datetime.datetime(2021,6,1,0,30)):
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

    time_range = Y.index[(Y.index < enddt) & (Y.index > startdt)]
    time_range = pd.to_datetime(time_range)

    plt.figure(facecolor='w')  # 建一个画布，facecolor是背景色
    plt.plot(time_range, Y.loc[time_range], 'r-', linewidth=1.5, label='真实值')
    plt.plot(time_range, y_pred_transf.loc[time_range], 'g-', linewidth=1, label='预测值')
    plt.legend()  # 显示图例，设置图例的位置
    plt.title("线性回归预测真实值之间的关系", fontsize=20)
    plt.grid(visible=True)  # 加网格
    plt.show()

def back_to_nextopen(pred, open, now='next_ret'):
    if now=='d_open':
        Y = pred + open
        return Y
    elif now=='next_ret':
        Y = np.exp(pred) * open
        return Y
    elif now=='next_open':
        return pred
    else:
        raise NameError('Invalid "now" value: {}'.format(now))

def draw_scatter(y_test, y_pred):
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

    plt.figure(facecolor='w')  # 建一个画布，facecolor是背景色
    plt.scatter(y_test, y_pred)
    plt.legend(loc='upper left')  # 显示图例，设置图例的位置
    plt.title("预测值vs真实值", fontsize=20)
    plt.xlabel('真实值')
    plt.ylabel('预测值')
    plt.grid(visible=True)  # 加网格
    plt.show()

def draw_resid(model):
    resid = model.resid

    fig = plt.figure(figsize=(12, 8))
    # 直接画残差
    ax = fig.add_subplot(121)
    ax = model.resid.plot(ax=ax)  # 残差正态
    # 画 qq图
    ax = fig.add_subplot(122)
    fig = qqplot(resid, line='q', ax=ax, fit=True)
    plt.title('qq picture')
    plt.show()

def read_data(freq=1):
    if freq != 1:
        data = pd.read_csv(r"C:\pythonProj\data\price_pred\t_data_{}min.csv".format(freq), index_col='datetime')
    else:
        data = pd.read_csv(r"C:\pythonProj\data\price_pred\t_data.csv", index_col='datetime')
    # data['vol'] = tb.STDDEV(data['open'], timeperiod=5, nbdev=1)
    data = data.dropna()
    data.index = pd.to_datetime(data.index)
    return data

if __name__ == '__main__':
    freq = 5
    data = read_data(freq)

    # startdt = datetime.datetime(2020, 3, 9, 0, 0)  # 2020.3.12日， 2021年5月19日有暴跌行情
    # enddt = datetime.datetime(2020, 3, 15, 0, 0)
    startdt = datetime.datetime(2021, 5, 16, 0, 0)  # 2020.3.12日， 2021年5月19日有暴跌行情
    enddt = datetime.datetime(2021, 5, 22, 0, 0)
    # 截取数据
    data_ = data.loc[data[(data.index > startdt) & (data.index < enddt)].index, :]

    target = 'next_ret'  # 'next_open' 'd_open' 'ret' next_ret
    feat_list = ['BOP', 'd_volume']  # ['d_NATR', 'd_volume']  # ['BOP', 'fastk', 'd_volume']
    # ATR NATR TRANGE  # d_volume # BOP fastk fastd MINUS_DI 和 d_open 的相关性系数较强
    # ROC STOCHF_fastk MOM ADOSC WILLR  'STOCHF_fastk', 'ADOSC', 'd_NATR'

    # describe_period(data, startdt=datetime.datetime(2021, 5, 19, 12, 0), enddt=datetime.datetime(2021, 5, 20, 0, 0))
    # describe_period(data, startdt=datetime.datetime(2021, 5, 21, 0, 0), enddt=datetime.datetime(2021, 5, 21, 7, 0))

    # 模型建立
    train_size = 0.5
    model, X_train, X_test, y_train, y_test = build_linear_model(data_, target, feat_list, train_size)
    train_ind = int(len(data_) * train_size)

    # draw_resid(model)

    # 模型预测
    y_pred = model.predict(sm.add_constant(X_test))
    y = data_[target]

    Y = back_to_nextopen(y, data_['open'], now=target)  # y + data_['open']
    y_pred_transf = back_to_nextopen(y_pred, data_['open'].iloc[train_ind:], now=target)  # model.predict(sm.add_constant(X_test)) + data_['open'].iloc[train_ind:]

    # 画图 展示拟合结果
    draw_fit(y_pred, data_[target])
    draw_fit(y_pred_transf, data_['next_open'])

    # draw_next_open(Y[-20:], y_pred_transf[-20:])
    # draw_next_open_fit_local(Y, y_pred_transf, startdt=datetime.datetime(2020, 3, 12, 18, 10),
    #                          enddt=datetime.datetime(2020, 3, 12, 19, 50))
    # draw_next_open_fit_local(Y, y_pred_transf, startdt=datetime.datetime(2020, 3, 14, 10, 10),
    #                          enddt=datetime.datetime(2020, 3, 14, 15, 10))
    # draw_next_open_fit_local(Y, y_pred_transf, startdt=datetime.datetime(2020, 3, 13, 6, 30),
    #                          enddt=datetime.datetime(2020, 3, 13, 9, 0))
    draw_next_open_fit_local(Y, y_pred_transf, startdt=datetime.datetime(2021, 5, 19, 17, 0), enddt=datetime.datetime(2021, 5, 19, 19, 30))
    draw_next_open_fit_local(Y, y_pred_transf, startdt=datetime.datetime(2021, 5, 19, 20, 20), enddt=datetime.datetime(2021, 5, 19, 22, 0))
    draw_next_open_fit_local(Y, y_pred_transf, startdt=datetime.datetime(2021, 5, 20, 1, 10), enddt=datetime.datetime(2021, 5, 20, 5, 30))


    draw_scatter(y_test, y_pred)
    draw_scatter(data_['next_open'].iloc[train_ind:], y_pred_transf[:])
