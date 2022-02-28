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
            data: 包含测试集和训练集的全部数据, index为交易时间
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
        print('\nMean squared error: %.8f' % mean_squared_error(self.y_test, model.predict(sm.add_constant(self.X_test))))

        # 模型预测
        self.y_pred = model.predict(sm.add_constant(self.X_test))
        return model

    def back_to_nextprice(self, series, this_price, now='next_ret'):
        if now == 'd_open':
            Y = series + this_price
            return Y
        elif now == 'next_ret':
            Y = np.exp(series) * this_price
            return Y
        elif now == 'next_ret_close':
            Y = np.exp(series) * this_price
            return Y
        elif now == 'next_open':
            return series
        elif now=='d_open_ratio':
            Y = series * self.nextopen + self.nextopen
            return Y
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

    def draw(self):
        # 画图 展示拟合结果
        self.draw_fit(self.y_pred, self.data[target])
        self.draw_fit(self.pred_nextclose, self.data['next_close']) # (self.pred_nextopen, self.data['next_open'])

        self.draw_fit_local(self.nextclose, self.pred_nextclose, startdt=self.pred_nextclose.index[20],
                            enddt=self.pred_nextclose.index[40])
        # self.draw_fit_local(self.nextopen, self.pred_nextopen, startdt=datetime.datetime(2021, 5, 19, 20, 20),
        #                     enddt=datetime.datetime(2021, 5, 19, 22, 0))
        # self.draw_fit_local(self.nextopen, self.pred_nextopen, startdt=datetime.datetime(2021, 5, 20, 1, 10),
        #                     enddt=datetime.datetime(2021, 5, 20, 5, 30))

        self.draw_scatter(self.y_test, self.y_pred)
        self.draw_scatter(self.data['next_close'].iloc[self.train_ind:], self.pred_nextclose)

    def get_performance(self):
        performance = pd.DataFrame(0.0, index=self.data.index[self.train_ind:], columns=['error_rate', 'direction'])
        performance['error_rate'] = (self.pred_nextclose - self.nextclose) / self.nextclose#(self.pred_nextopen - self.nextopen) / self.nextopen
        performance['direction'] = self.nextclose - self.data['close'].iloc[self.train_ind:]
        performance['pred_direction'] = self.pred_nextclose - self.data['close'].iloc[self.train_ind:]
        # 计算胜率
        win_num = performance[performance['pred_direction'] * performance['direction'] > 0].shape[0]
        win_ratio = win_num / (len(performance) - 1)
        print('胜率：', win_ratio)
        print('预测表现：', performance['error_rate'].mean())
        return win_ratio, performance['error_rate']

    def run(self, train_size=0.5):
        # self.describe_period(startdt=datetime.datetime(2021, 5, 19, 12, 0),
        #                 enddt=datetime.datetime(2021, 5, 20, 0, 0))

        # 模型建立
        self.split_train_test(train_size)
        model = self.build_linear_model_and_predict()
        rsquared = model.rsquared
        # self.draw_resid(model)

        # 还原为 未来一期收益率
        self.nextopen = self.data['next_open'].iloc[self.train_ind:]   # y + data_['open']
        # self.pred_nextopen = self.back_to_nextopen(self.y_pred, self.data['open'].iloc[self.train_ind:], now=self.target)
        self.nextclose = self.data['next_close'].iloc[self.train_ind:]
        self.pred_nextclose = self.back_to_nextprice(self.y_pred, self.data['close'].iloc[self.train_ind:], now=self.target)

        # 获取 预测表现
        win_ratio, error_rate = self.get_performance()

        # 画图 展示拟合结果
        self.draw()
        return win_ratio, error_rate, rsquared



def read_data(freq=1):
    if freq != 1:
        data = pd.read_csv(r"C:\pythonProj\data\price_pred\t_data_{}min.csv".format(freq), index_col='datetime')
    else:
        data = pd.read_csv(r"C:\pythonProj\data\price_pred\t_data.csv", index_col='datetime')
    # data['vol'] = tb.STDDEV(data['open'], timeperiod=5, nbdev=1)
    data = data.dropna()
    data.index = pd.to_datetime(data.index)
    return data

def rolling_ols(data, target = 'next_ret', feat_list = ['BOP'], window=6):
    first_date = data.index[0]; last_date = data.index[-1]
    date_num = (last_date - first_date).days
    print(f'{first_date} 和 {last_date} 相差 {date_num} 天')

    win_list, error_list, rsquared_list, startdt_list = [], [], [], []
    for i in range(int(date_num // 6)):
        startdt = first_date + datetime.timedelta(days=i * window)
        enddt = startdt + datetime.timedelta(days=window)
        # 截取数据
        data_period = data.loc[data[(data.index > startdt) & (data.index < enddt)].index, :]

        l = LinearModel(data_period, target, feat_list)
        win_ratio, error_rate, rsquared = l.run(train_size=0.5)
        startdt_list.append(startdt)
        rsquared_list.append(rsquared)
        win_list.append(win_ratio)
        error_list.append(error_rate.mean())

    perf_data = pd.DataFrame(data={'win_ratio': win_list, 'error_rate': error_list, 'rsquared': rsquared_list},
                             index=startdt_list)
    return perf_data

def draw_performance(perf_data=None):
    if len(perf_data)==0: # 没有传入数据，则默认读入数据
        perf_data = pd.read_csv('performance.csv')

    # 画图
    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

    plt.figure(figsize=(12, 10))
    plt.subplot(3, 1, 1)
    plt.hist(perf_data['win_ratio'], label=u'胜率', bins=20, facecolor='y', edgecolor='k')
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylabel(u'频数', fontsize=13)
    plt.legend(loc=0, fontsize=13)
    plt.grid(True)
    plt.subplot(3, 1, 2)
    plt.hist(perf_data['error_rate'], label=u'平均相对误差', bins=20, facecolor='r', edgecolor='k')
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylabel(u'频数', fontsize=13)
    plt.legend(loc=0, fontsize=13)
    plt.grid(True)
    plt.subplot(3, 1, 3)
    plt.hist(perf_data['rsquared'], label=u'回归R方', bins=20, facecolor='b', edgecolor='k')
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylabel(u'频数', fontsize=13)
    plt.legend(loc=0, fontsize=13)
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    freq = 1
    data = read_data(freq)

    # startdt = datetime.datetime(2020, 3, 9, 0, 0)  # 2020.3.12日， 2021年5月19日有暴跌行情
    # enddt = datetime.datetime(2020, 3, 15, 0, 0)
    # startdt = datetime.datetime(2021, 5, 16, 0, 0)  # 2020.3.12日， 2021年5月19日有暴跌行情
    # enddt = datetime.datetime(2021, 5, 22, 0, 0)
    # data_period = data.loc[data[(data.index > startdt) & (data.index < enddt)].index, :]

    # data['d_open_ratio'] = (data['next_close'] - data['next_open']) / data['next_open']
    # data['next_ret_close'] = np.log(data['next_close'] / data['next_open'])

    target = 'next_ret' #'d_open_ratio' # 'next_ret'  # 'log_next_ret' 'd_open' 'ret' next_ret
    feat_list = ['VAR', 'LINEARREG_SLOPE']   #'MINUS_DI', 'MACD_macd' ['d_NATR', 'd_volume']  # ['BOP', 'fastk', 'd_volume']

    l = LinearModel(data, target, feat_list)
    win_ratio, error_rate, rsquared = l.run(train_size=0.5)

    perf_dict = {'win_ratio': win_ratio, 'error_rate': error_rate.mean(), 'rsquared': rsquared}
    print(perf_dict)

    # draw_performance(perf_data)




