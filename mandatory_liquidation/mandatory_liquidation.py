"""
强平模拟

滚动模拟 6/3 个月，看在不同持仓分布及市场情况下，现有强平策略是否会造成损失。

Class & Function
    Class：
        Coin  进行币种层次的操作，如：更新每个币种 每一期的价值；对单个币进行强平
        Tier  进行tier层次的操作，如：更新整个tier的每期价值；对整个tier进行强平
        Trade 进行账户层次的操作，如：更新整个账户的煤气价值；计算risk rate并判断需要对哪个tier进行强平

    Function:
        monitor 强平模拟器，调用上述的类进行滚动强平模拟
"""
import time

import numpy as np
import pandas as pd

from other_codes.get_historical_data.huobi_data import Huobi_kline
from paint import paint_result


coins = ['btcusdt', 'ethusdt', 'trxusdt', 'shibusdt', 'solusdt', 'dotusdt',
        'filusdt', 'dogeusdt', 'adausdt', 'linkusdt', 'sandusdt', 'ltcusdt',
        'avaxusdt', 'eosusdt', 'bchusdt', 'uniusdt', 'sushiusdt', 'aaveusdt',
        'etcusdt', 'crousdt', 'axsusdt', 'zecusdt', 'xlmusdt', 'bsvusdt',
        'dashusdt', '1inchusdt', 'xmrusdt', 'compusdt',
        'iotausdt', 'sklusdt', 'paxusdt', 'wbtcusdt']


def get_trade_data(target='btcusdt', start_time=None, end_time=None, period='5min'):
    tradedata = Huobi_kline(symbol=target, period=period, start_time=start_time, end_time=end_time,
                            get_full_market_data=True, col_with_asset_name=False)
    print(tradedata)
    tradedata.to_csv('C:/pythonProj/data/mandatory_liquidation/origin_data/{}_{}_{}_to_{}.csv'.format(target, period,
                                                                                                      start_time,
                                                                                                      end_time))
    return tradedata


def download_all_coin_data():
    # 生成 timestamp
    start_time = int(time.mktime((2021, 5, 12, 0, 0, 0, 0, 0, 0)))
    end_time = int(time.mktime((2022, 3, 12, 0, 0, 0, 0, 0, 0)))
    for i in range(len(coins) - 12, 10, -1):  # 10, len(coins)): # 若从前往后，是第十个
        coin = coins[i]
        print('\n......', coin)
        get_trade_data(target=coin, start_time=start_time, end_time=end_time, period='5min')


def get_four_tiers():
    """
    Returns: 四个 tier (字典形式，含字段 { coin, percent, slippage})
    """
    tier_perc = [.4, .3, .2, .1]
    slippage_list = [.0003, .0006, .0008, .001]

    tier1, tier2, tier3, tier4 = {}, {}, {}, {}
    tier1['coins'] = coins[:2]
    tier2['coins'] = coins[2:13]
    tier3['coins'] = coins[13:23]
    tier4['coins'] = coins[-9:]

    tier1['percent'], tier1['slippage'] = tier_perc[0], slippage_list[0]
    tier2['percent'], tier2['slippage'] = tier_perc[1], slippage_list[1]
    tier3['percent'], tier3['slippage'] = tier_perc[2], slippage_list[2]
    tier4['percent'], tier4['slippage'] = tier_perc[3], slippage_list[3]
    return tier1, tier2, tier3, tier4


def get_random_proportion(num):
    r = np.random.normal(loc=0, scale=1.0, size=num)
    # 保证正态分布随机数的最小值 > 0
    if r.min() < 0:
        r = r + abs(r.min()) + 1
    # 使和为 1
    proportion = r / sum(r)
    return proportion


def load_all_coin_data_to_dict():
    coins_data = {}
    for coin in coins:
        data = pd.read_csv(
            'C:/pythonProj/data/mandatory_liquidation/origin_data/{}_5min_1620748800_to_1647014400.csv'.format(
                coin), index_col=0)
        data.index = pd.to_datetime(data.index)
        coins_data[coin] = data.to_dict('index')
    return coins_data


def select_coin_data(coins_data, tier_coin):
    select_coins = {}
    for coin in tier_coin:
        select_coins[coin] = coins_data[coin]
    return select_coins


class Coin():
    def __init__(self, name, slippage):
        self.name = name
        self.datetime = None
        self.slippage = slippage  # 滑点
        self.commission = .0003  # 佣金

        self.cash = None  # 买入时 由于持仓数取两位小数 而剩余的；或卖出的
        self.hold_pos = None
        # self.short_pos = None
        self.value = None
        self.short_loss = 0

    def __str__(self):
        param_list = ['datetime', 'name', 'hold_pos', 'cash', 'value', 'short_loss']
        value = [(name, getattr(self, name)) for name in param_list]
        f_string = ''
        for i, (item, count) in enumerate(value):
            f_string += (f'#{i + 1}: {item.title():<10s} = {count}\n')
        return f_string

    def place_order(self, datetime, trade_dict, allocation):
        self.datetime = datetime
        self.open = trade_dict.get('open')
        self.close = trade_dict.get('close')
        self.avg_price = (self.open + self.close) / 2

        self.hold_pos = allocation / self.avg_price
        # 持仓数（币数） 两位小数
        self.hold_pos = np.floor(self.hold_pos * 100) / 100  # 取两位小数（向下取，否则可能会超出 allocation）
        self.cash = allocation - self.hold_pos * self.avg_price
        if self.cash < 0:
            raise ValueError('cash can not be negative.')
        self.value = self.hold_pos * self.avg_price + self.cash  # 下单的时候 value 是 avg_price 计算

    def short_order(self, datetime, trade_dict):
        self.datetime = datetime
        self.open = trade_dict.get('open')
        self.close = trade_dict.get('close')
        self.amount = trade_dict.get('amount')

        self.avg_price = (self.open + self.close) / 2

        # 不进行平仓操作时，二者不变
        if self.hold_pos >= self.amount * .05:
            self.short_pos = self.amount * .05
        else:
            self.short_pos = self.hold_pos

        self.hold_pos -= self.short_pos
        self.cash += self.short_pos * self.avg_price * (1 - self.slippage) * (1 - self.commission)
        last_value = self.value
        self.value = self.close * self.hold_pos + self.cash  # 平仓时，资产价值用 close 计算（期末的）
        self.short_loss = self.short_pos * self.avg_price * (1 - (1 - self.slippage) * (1 - self.commission))

    def update(self, datetime, trade_dict):
        self.datetime = datetime
        self.open = trade_dict.get('open')
        self.close = trade_dict.get('close')

        self.avg_price = (self.open + self.close) / 2

        # 不进行平仓操作时，二者不变
        # self.cash = self.cash
        # self.hold_pos = self.hold_pos
        self.value = self.open * self.hold_pos + self.cash  # 不平仓时，资产价值用open计算
        self.short_loss = 0  # 每一期重新算一个 short loss

    def gather_info(self):
        if self.hold_pos > 0:
            param_list = ['hold_pos', 'open', 'cash', 'value', 'short_loss']
            value = [(para, round(getattr(self, para), 2)) for para in param_list]
            info_dict = dict(value)
        else:
            info_dict = {'hold_pos': self.hold_pos, 'cash': self.cash, 'value': self.value}  # 持仓为 0
        return info_dict


class Tier():
    def __init__(self, name, tier, allocation, coins_data, period='5min'):
        """

        Args:
            tier: 字典形式，含字段 {coin, slippage}
            allocation: 本 tier 的资金配比
        """
        self.name = name
        self.period = period
        self.tier_coin = tier.get('coins')  # list
        self.slippage = tier.get('slippage')  # list
        self.value = allocation

        self.coin_object = None
        self.hold_pos = None
        self.cash = None  # 平仓后得到的 usdt

        self.short_pos = None
        self.short_loss = 0
        self.is_empty = False  # 是否无持仓
        self.short = False  # 是否触及到平仓线

        # 获取该 tier 内全部 coins 的数据
        self.tier_tradedata = select_coin_data(coins_data, self.tier_coin)

    def __str__(self):
        param_list = ['hold_pos', 'cash', 'value', 'short_loss']
        value = [(name, getattr(self, name)) for name in param_list]
        f_string = ''
        for i, (item, count) in enumerate(value):
            f_string += (f'#{i + 1}: '
                         f'{item.title():<10s} = '
                         f'{count}\n')
        return f_string

    def fetch_tradeinfo(self, datetime):
        tier_tradeinfo = {}
        tier_open = []
        for coin in self.tier_coin:
            # data = pd.read_csv('C:/pythonProj/data/mandatory_liquidation/{}_{}_1620748800_to_1647014400.csv'.format(
            #     coin, self.period), index_col=0)
            # data.index = pd.to_datetime(data.index)
            # tier_tradeinfo[coin] = data.to_dict('index')[datetime]
            tier_tradeinfo[coin] = self.tier_tradedata[coin][datetime]
            tier_open.append(tier_tradeinfo[coin].get('open'))
        return tier_tradeinfo, tier_open

    def place_order(self, datetime, pos_percent):
        """更新 初始资产配置后的 hold_pos, cash

        Args:
            datetime: 日期
            pos_percent: 当前 tier 中各币种的投资比例
        """
        trade_dict = self.fetch_tradeinfo(datetime)[0]
        self.hold_pos = []
        self.cash = 0
        self.coin_object = []
        for i in range(len(self.tier_coin)):
            coinname = self.tier_coin[i]
            c = Coin(coinname, self.slippage)
            c.place_order(datetime, trade_dict[coinname], pos_percent[i] * self.value)
            self.coin_object.append(c)
            self.hold_pos.append(c.hold_pos)
            self.cash += c.cash

    def short_tier(self, datetime):
        trade_dict = self.fetch_tradeinfo(datetime)[0]
        # 每一期算一个 流量的 cash，value，short_loss
        self.hold_pos = []
        self.cash = 0
        self.value = 0
        self.short_loss = 0
        for i in range(len(self.tier_coin)):
            coin = self.coin_object[i]
            if coin.hold_pos > 0:  # 只要有持仓，就进行平仓（否则无操作
                coin.short_order(datetime, trade_dict[coin.name])
                self.short_loss += coin.short_loss
            self.cash += coin.cash
            self.value += coin.value
            self.hold_pos.append(coin.hold_pos)
        if self.value == self.cash:
            self.is_empty = True  # 是否无持仓

    def update(self, datetime):
        self.short_loss = 0  # 每期重新算一个 损益
        # 更新 cash 和 value
        trade_dict = self.fetch_tradeinfo(datetime)[0]
        self.value = 0
        self.cash = 0
        for coin in self.coin_object:
            coin.update(datetime, trade_dict[coin.name])  # 更新每个币种的 价值
            self.value += coin.value
            self.cash += coin.cash

    # 每期都需要更新 总资产
    def calc_total_value(self, datetime):
        # openprice_list = self.fetch_tradeinfo(datetime)[1]
        # self.value = np.dot(np.array(openprice_list), np.array(self.hold_pos).T) + self.cash
        self.short_loss = 0
        trade_dict = self.fetch_tradeinfo(datetime)[0]
        self.value = 0
        for coin in self.coin_object:
            coin.update(datetime, trade_dict[coin.name])  # 更新每个币种的 价值
            self.value += coin.value
        return self.value

    def gather_info(self):
        param_list = ['hold_pos', 'cash', 'value', 'short_loss', 'short', 'is_empty']
        value = [(self.name + '_' + para, getattr(self, para)) for para in param_list]
        info_dict = dict(value)
        for coin in self.coin_object:
            info_dict[coin.name] = coin.gather_info()
        return info_dict


# risk rate 是总体算的
class Trade():
    def __init__(self, coins_data, liquidation_lines=[1.1, 1.075, 1.05, 1.025, 1], client_asset=500e4, loan=1000e4,
                 interest=40e4):
        """

        Args:
            client_asset: 客户的资金
            lend_asset: 配资借贷借给客户的资金
            interest: 借贷的利息额
        """
        self.loan_with_interest = loan + interest  # 算 risk rate 做分母
        self.liquidation_lines = liquidation_lines  # 4个tier 对应 5 条线

        init_asset = client_asset + loan
        tier1, tier2, tier3, tier4 = get_four_tiers()
        self.Tier1 = Tier('tier1', tier1, tier1['percent'] * init_asset, coins_data)
        self.Tier2 = Tier('tier2', tier2, tier2['percent'] * init_asset, coins_data)
        self.Tier3 = Tier('tier3', tier3, tier3['percent'] * init_asset, coins_data)
        self.Tier4 = Tier('tier4', tier4, tier4['percent'] * init_asset, coins_data)
        self.tiers = [self.Tier1, self.Tier2, self.Tier3, self.Tier4]

        # self.hold_pos = None
        self.cash = None
        self.value = init_asset  # 账户总资产
        self.short_loss = 0
        self.risk_rate = self.value / self.loan_with_interest
        self.short = None

    def calc_risk_rate(self):
        # 账户内资产 = sum(open * 持仓量 ) + 现金
        # risk rate= 账户内资产（open计算）/(借贷资产+生成利息)
        self.value = self.Tier1.value + self.Tier2.value + self.Tier3.value + self.Tier4.value
        self.risk_rate = self.value / self.loan_with_interest
        return self.risk_rate

    def get_cash(self):
        self.cash = 0
        for tier in self.tiers:
            self.cash += tier.cash

    def get_shortloss(self):
        self.short_loss = 0
        for tier in self.tiers:
            self.short_loss += tier.short_loss

    def get_value(self):
        self.value = self.Tier1.value + self.Tier2.value + self.Tier3.value + self.Tier4.value
        return self.value

    def gather_info(self):
        param_list = ['risk_rate', 'value', 'cash', 'short_loss']
        value = [(para, getattr(self, para)) for para in param_list]
        info_dict = dict(value)
        for tier in self.tiers:
            tier_info = tier.gather_info()
            info_dict.update(tier_info)
            # info_dict['tier'+str(i+1)] = tier.gather_info()
        return info_dict

    def trade(self, datetime_list):
        # 初始时刻，下单 配置资产
        for tier in self.tiers:
            prop = get_random_proportion(len(tier.tier_coin))
            tier.place_order(datetime_list[0], prop)

        # 每日计算risk rate
        info = {}
        for dt in datetime_list[1:]:
            # 先更新 每个 tier 的总资产
            for tier in self.tiers:
                tier.update(dt)  # 函数里会 update 每个币种的价值
            self.calc_risk_rate()

            # 若 触碰到/曾经触碰到强平线 + 对应tier仍有持仓，则将对应 tier 平仓
            # print(dt)
            if (self.liquidation_lines[0] >= self.risk_rate > self.liquidation_lines[1] or self.Tier1.short) and \
                    not self.Tier1.is_empty:
                self.Tier1.short_tier(dt)
                self.Tier1.short = True
                # print(dt, 'risk rate: {}, short tier 1 , daily loss: {}'.format(self.risk_rate, self.Tier2.short_loss))
            if (self.liquidation_lines[1] >= self.risk_rate > self.liquidation_lines[2] or self.Tier2.short) and \
                    not self.Tier2.is_empty:
                self.Tier2.short_tier(dt)
                self.Tier2.short = True
                # print(dt, 'risk rate: {}, short tier 2 , daily loss: {}'.format(self.risk_rate, self.Tier2.short_loss))
            if (self.liquidation_lines[2] >= self.risk_rate > self.liquidation_lines[3] or self.Tier3.short) and \
                    not self.Tier3.is_empty:
                self.Tier3.short_tier(dt)
                self.Tier3.short = True
                # print(dt, 'risk rate: {}, short tier 3 , daily loss: {}'.format(self.risk_rate, self.Tier2.short_loss))
            if (self.liquidation_lines[3] >= self.risk_rate > self.liquidation_lines[4] or self.Tier4.short) and \
                    not self.Tier4.is_empty:
                self.Tier4.short_tier(dt)
                self.Tier4.short = True
                # print(dt, 'risk rate: {}, short tier 4 , daily loss: {}'.format(self.risk_rate, self.Tier2.short_loss))

            self.get_shortloss()
            self.get_cash()
            info[dt] = self.gather_info()  # 函数里，会先获取每个 coin 的信息，再获取每个 tier 的信息，再到整个汇总输出
        return info


def calc_tiers_short_loss(trade_df):
    # 计算每个 tier 的 平仓损益，开始平仓时间，结束平仓时间，开始平仓risk rate，结束平仓risk rate
    tier_dict = {}
    total_shortloss = 0
    for i in range(1, 5):
        pr = 'tier' + str(i)
        trade_df['pre_short'] = trade_df[pr + '_short'].shift(1)
        trade_df['pre_empty'] = trade_df[pr + '_is_empty'].shift(1)
        short_start = trade_df.apply(lambda x: 1 if x['pre_short'] == False and x[pr + '_short'] == True else None,
                                     axis=1)
        short_end = trade_df.apply(lambda x: 1 if x['pre_empty'] == False and x[pr + '_is_empty'] == True else None,
                                   axis=1)
        shortloss = trade_df[pr + '_short_loss'].sum()
        try:
            short_start = short_start.dropna().index[0]
            short_end = short_end.dropna().index[0]
            tier_dict[pr] = {'平仓损益': shortloss, '开始平仓时间': short_start, '结束平仓时间': short_end, '开始平仓risk rate':
                trade_df['risk_rate'].loc[short_start], '结束平仓risk rate': trade_df['risk_rate'].loc[short_end]}
        except IndexError:
            short_start, short_end = '', ''  # 即，该tier没有平仓
            tier_dict[pr] = {'平仓损益': shortloss, '开始平仓时间': short_start, '结束平仓时间': short_end, '开始平仓risk rate':
                '', '结束平仓risk rate': ''}

        total_shortloss += shortloss
    # 计算总的平仓损益，期末总资产，'期末risk rate
    tier_dict['总'] = {'平仓损益': total_shortloss, '期末总资产': trade_df['value'].iloc[-1],
                      '期末risk rate': trade_df['risk_rate'].iloc[-1]}

    # tiers_info = {'tier1': {}, 'tier2': {}, 'tier3': {}, 'tier4': {}, '总': {}}
    # for t in ['tier1', 'tier2', 'tier3', 'tier4', '总']:
    #     tiers_info[t][1] = tier_dict[t]
    #     tiers_info[t][2] = tier_dict[t]
    #
    # writer = pd.ExcelWriter('C:/pythonProj/data/mandatory_liquidation/results/simulation_test.xlsx')
    # for t in ['tier1', 'tier2', 'tier3', 'tier4', '总']:
    #     df = pd.DataFrame.from_dict(tiers_info[t], 'index')
    #     df.index.name = t
    #     df.to_excel(writer, sheet_name=t)
    # writer.save()
    return tier_dict


def get_total_value_and_short_loss(trade_df):
    # 计算每个 tier 的 平仓损益，开始平仓时间，结束平仓时间，开始平仓risk rate，结束平仓risk rate
    total_shortloss = 0
    for i in range(1, 5):
        pr = 'tier' + str(i)
        shortloss = trade_df[pr + '_short_loss'].sum()
        total_shortloss += shortloss
    # 计算总的平仓损益，期末总资产，'期末risk rate
    total_dict = {'total short loss': total_shortloss, 'final value': trade_df['value'].iloc[-1],
                  'final risk rate': trade_df['risk_rate'].iloc[-1]}
    return total_dict


def monitor(iterate=None, duration=3):
    """ 强平模拟器，以六个月为周期进行强平模拟，并在每个周期随机生成持仓分布进行迭代

    Args:
        iterate: 循环迭代的次数，默认 None，即不循环
        duration: 模拟周期长度 单位：月
    """
    months = ['2021-5-12 00:00', '2021-6-12 00:00', '2021-7-12 00:00', '2021-8-12 00:00', '2021-9-12 00:00',
              '2021-10-12 00:00', '2021-11-12 00:00', '2021-12-12 00:00', '2022-1-12 00:00', '2022-2-12 00:00',
              '2022-3-12 00:00']
    start_dates = months[:-duration]
    end_dates = months[duration:]
    coins_data = load_all_coin_data_to_dict()
    for n in range(len(start_dates)):
        start_dt = start_dates[n]
        end_dt = end_dates[n]
        print(start_dt, end_dt)
        # 如果不迭代：存入此次的数据，并可视化
        if not iterate:
            t = Trade(coins_data)
            trade_dt = pd.date_range(start_dt, end_dt, freq='5MIN')
            trade_info = t.trade(trade_dt)
            # 存入数据 + 可视化
            trade_df = pd.DataFrame.from_dict(trade_info, orient='index')
            trade_df.to_csv('C:/pythonProj/data/mandatory_liquidation/results/liquidation_{}_to_{}.csv'.format(
                start_dt.split(' ', 1)[0], end_dt.split(' ', 1)[0]))
            paint_result(trade_df, start_dt.split(' ', 1)[0], end_dt.split(' ', 1)[0],
                         path='C:/pythonProj/data/mandatory_liquidation/results')
        # 若迭代，则统计每次模拟的期末总资产、risk rate
        else:
            tiers_info = {}
            for i in range(iterate):  # 循环30次，随机性
                t = Trade(coins_data)
                trade_dt = pd.date_range(start_dt, end_dt, freq='5MIN')
                trade_info = t.trade(trade_dt)
                # 统计 资产总价值
                # trade_df = pd.DataFrame.from_dict(trade_info, orient='index')
                # total_dict = get_total_value_and_short_loss(trade_df)  # calc_tiers_short_loss(trade_df)# 每个 tier，以及总值
                final_trade = trade_info[trade_dt[-1]]
                if final_trade['tier1_short'] == False and final_trade['tier2_short'] == False and \
                        final_trade['tier3_short'] == False and final_trade['tier4_short'] == False:
                    short = False
                else:
                    short = ''
                    for j in range(1, 5):
                        if final_trade[f'tier{str(j)}_short'] == True:
                            short += f'tier{str(j)} '
                total_dict = {'final value': final_trade['value'],
                              'final risk rate': final_trade['risk_rate'],
                              'short': short}
                print(i, end=' ')
                tiers_info[i] = total_dict

            df = pd.DataFrame.from_dict(tiers_info, 'index')
            df.to_csv('C:/pythonProj/data/mandatory_liquidation/results/simulation_{}_to_{}.csv'.format(
                start_dt.split(' ', 1)[0], end_dt.split(' ', 1)[0]))
            print(df)
            print('期末资产价值的均值为 {:,.0f}，标准差为 {:,.0f}'.format(df['final value'].mean(), df['final value'].std()))
            print('期末 risk rate 的均值为{:.4f}，表明期末资金超出本息 {:.2%}'.format(df['final risk rate'].mean(),
                                                                     df['final risk rate'].mean() - 1))
            print(
                '强平概率为 {:.2%}（{}/{}）'.format(1 - len(df[df['short'] == False]) / iterate, len(df[df['short'] == False]),
                                             iterate))


if __name__ == "__main__":
    monitor()
