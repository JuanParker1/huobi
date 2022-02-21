import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib as mpl
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, r2_score
from statsmodels.graphics.api import qqplot
from data_handle import paint_relation


class LinearModel():
    def __init__(self, data, target='next_ret', feat_list=['BOP', 'd_volume']):
        """
        Args:
            data: 包含测试集和训练集的全部数据
            target: 被解释变量
            feat_list: 解释变量
        """
        self.data = data
        self.target = target
        self.feat_list = feat_list

    def split_train_test(self, train_size=0.5):
        X = self.data[self.feat_list]
        y = self.data[self.target]
        # 划分训练集 和 测试集
        self.train_size = train_size
        self.train_ind = int(len(X) * train_size)
        self.X_train = X[:self.train_ind]
        self.X_test = X[self.train_ind:]
        self.y_train = y[:self.train_ind]
        self.y_test = y[self.train_ind:]

    def build_linear_model_and_predict(self):
        model = sm.OLS(self.y_train, sm.add_constant(self.X_train)).fit()
        # 查看模型结果
        print(model.summary())
        print('\nMean squared error: %.4f' % mean_squared_error(self.y_test, model.predict(sm.add_constant(self.X_test))))

        # 模型预测
        self.y_pred = model.predict(sm.add_constant(self.X_test))
        return model

    def back_to_nextopen(self, series, open, now='next_ret'):
        if now == 'd_open':
            Y = series + open
            return Y
        elif now == 'next_ret':
            Y = np.exp(series) * open
            return Y
        elif now == 'next_open':
            return series
        else:
            raise NameError('Invalid "now" value: {}'.format(now))

    def describe_period(self, startdt = datetime.datetime(2020, 3, 12, 0, 0), enddt = datetime.datetime(2020, 3, 13, 0, 0)):
        # 截取数据
        period_data = self.data.loc[self.data[(self.data.index > startdt) & (self.data.index < enddt)].index, :]

        corr_list = self.feat_list + [self.target]
        print(period_data[corr_list].corr())
        print('describe:\n', period_data[corr_list].describe())
        paint_relation(pd.to_datetime(period_data.index), period_data['BOP'], period_data[target], 'BOP', target)

    def draw_fit(self, origin, predict, how='origin'):
        # how='origin' 或 'next_open'
        mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
        mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

        y = self.data[target]
        plt.figure(facecolor='w')  # 建一个画布，facecolor是背景色
        plt.plot(origin.index, origin, 'r-', linewidth=1.5, label='真实值')
        plt.plot(predict.index, predict, 'g-', linewidth=1, label='预测值')
        plt.legend()
        if how == 'origin':
            plt.title("预测值和真实值之间的关系", fontsize=20)
        elif how == 'next_open':
            plt.title("还原后开盘价的预测值和真实值之间的关系", fontsize=20)
        else:
            raise NameError('invalid parameter: how')
        plt.grid(visible=True)  # 加网格
        plt.show()
        plt.close()

    def draw_fit_local(self, origin, predict, startdt=datetime.datetime(2021,6,1,0,0), enddt=datetime.datetime(2021,6,1,0,30)):
        mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
        mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

        time_range = origin.index[(origin.index < enddt) & (origin.index > startdt)]
        time_range = pd.to_datetime(time_range)

        plt.figure(facecolor='w')  # 建一个画布，facecolor是背景色
        plt.plot(time_range, origin.loc[time_range], 'r-', linewidth=1.5, label='真实值')
        plt.plot(time_range, predict.loc[time_range], 'g-', linewidth=1, label='预测值')
        plt.legend()  # 显示图例，设置图例的位置
        plt.title("线性回归预测真实值之间的关系", fontsize=20)
        plt.grid(visible=True)  # 加网格
        plt.show()
        plt.close()

    def draw_scatter(self, origin, predict):
        mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
        mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

        plt.figure(facecolor='w')  # 建一个画布，facecolor是背景色
        plt.scatter(origin, predict)
        plt.legend()  # 显示图例，设置图例的位置
        plt.title("预测值vs真实值", fontsize=20)
        plt.xlabel('真实值')
        plt.ylabel('预测值')
        plt.grid(visible=True)  # 加网格
        plt.show()
        plt.close()

    def draw_resid(self, model):
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
        plt.close()

    def run(self, train_size=0.5):
        self.describe_period(startdt=datetime.datetime(2021, 5, 19, 12, 0),
                        enddt=datetime.datetime(2021, 5, 20, 0, 0))

        # 模型建立
        self.split_train_test(train_size)
        model = self.build_linear_model_and_predict()
        self.draw_resid(model)

        # 还原为 未来一期收益率
        nextopen = self.back_to_nextopen(self.data[target], self.data['open'], now=target)  # y + data_['open']
        self.pred_nextopen = self.back_to_nextopen(self.y_pred, self.data['open'].iloc[self.train_ind:], now=target)

        # 画图 展示拟合结果
        self.draw_fit(self.y_pred, self.data[target])
        self.draw_fit(self.pred_nextopen, self.data['next_open'])

        self.draw_fit_local(nextopen, self.pred_nextopen, startdt=datetime.datetime(2021, 5, 19, 17, 0),
                                 enddt=datetime.datetime(2021, 5, 19, 19, 30))
        self.draw_fit_local(nextopen, self.pred_nextopen, startdt=datetime.datetime(2021, 5, 19, 20, 20),
                                 enddt=datetime.datetime(2021, 5, 19, 22, 0))
        self.draw_fit_local(nextopen, self.pred_nextopen, startdt=datetime.datetime(2021, 5, 20, 1, 10),
                                 enddt=datetime.datetime(2021, 5, 20, 5, 30))

        self.draw_scatter(self.y_test, self.y_pred)
        self.draw_scatter(self.data['next_open'].iloc[self.train_ind:], self.pred_nextopen)


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
    data_period = data.loc[data[(data.index > startdt) & (data.index < enddt)].index, :]

    target = 'next_ret'  # 'next_open' 'd_open' 'ret' next_ret
    feat_list = ['BOP', 'd_volume']  # ['d_NATR', 'd_volume']  # ['BOP', 'fastk', 'd_volume']

    l = LinearModel(data_period, target, feat_list)
    l.run(train_size=0.5)