import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from other_codes.get_historical_data.huobi_data import Huobi_kline


def compare_price(match_data):
    # 计算 溢价率，胜率（盈利>0），胜率（盈利>=0）
    match_data['d_amount'] = match_data.apply(
        lambda x: x['exec_base_amount'] - x['base_amount'] if (x['side'] == 'sell') else
        x['base_amount'] - x['exec_base_amount'], axis=1)
    match_data['d_amount_ratio'] = match_data['d_amount'] / match_data['base_amount']
    return match_data


def describe_price(match_data, key='d_price_ratio'):
    # 描述性统计
    des_dict = {}
    des_dict['总'] = match_data[key].describe(percentiles=[0.5]).to_dict()
    des_dict['买入'] = match_data[match_data['side'] == 'buy'][key].describe(percentiles=[0.5]).to_dict()
    des_dict['卖出'] = match_data[match_data['side'] == 'sell'][key].describe(percentiles=[0.5]).to_dict()
    return des_dict


def get_win_ratio(match_data):
    # 胜率
    win_ratio = {'总': {}, '买入': {}, '卖出': {}}
    win_ratio['总']['胜率（盈利>0）'] = match_data[match_data['d_amount'] > 0].shape[0] / len(match_data)
    win_ratio['总']['胜率（盈利>=0）'] = match_data[match_data['d_amount'] >= 0].shape[0] / len(match_data)

    type_c = {'buy': '买入', 'sell': '卖出'}
    for i in ['buy', 'sell']:
        piece = match_data[match_data['side'] == i]
        win_ratio[type_c[i]]['胜率（盈利>0）'] = piece[piece['d_amount'] > 0].shape[0] / len(piece)
        win_ratio[type_c[i]]['胜率（盈利>=0）'] = piece[piece['d_amount'] >= 0].shape[0] / len(piece)
    return win_ratio


def get_exp_return(match_data):
    exp_return = {}
    exp_return['总'] = {'绝对收益': match_data.d_amount.mean(), '相对收益': match_data.d_amount_ratio.mean()}
    exp_return['买入'] = {'绝对收益': match_data[match_data['side'] == 'buy'].d_amount.mean(),
                        '相对收益': match_data[match_data['side'] == 'buy'].d_amount_ratio.mean()}
    exp_return['卖出'] = {'绝对收益': match_data[match_data['side'] == 'sell'].d_amount.mean(),
                        '相对收益': match_data[match_data['side'] == 'sell'].d_amount_ratio.mean()}
    return exp_return


def draw_hist(match_data, client_id, key='d_price_ratio'):
    key_dict = {'d_amount_ratio': '相对收益', 'd_amount': '绝对收益'}

    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

    plt.figure(figsize=(12, 10))
    plt.subplot(2, 1, 1)
    plt.hist(match_data[match_data['side'] == 'buy'][key], label=u'买入' + key_dict[key], bins=30, facecolor='y',
             edgecolor='k')
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylabel(u'频数', fontsize=13)
    plt.legend(loc=0, fontsize=13)
    # plt.text(-0.0100, 1000, r"溢价率 = $\frac{exec price-quote price}{quote price}$", fontsize=20)
    plt.grid(True)
    plt.title(f"{key_dict[key]}分布情况（client_id={client_id})", fontsize=30)  # ('溢价率=实际交易价格-客户报价/客户报价')

    plt.subplot(2, 1, 2)
    plt.hist(match_data[match_data['side'] == 'sell'][key], label=u'卖出' + key_dict[key], bins=30, facecolor='r',
             edgecolor='k')
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylabel(u'频数', fontsize=13)
    plt.legend(loc=0, fontsize=13)
    plt.grid(True)

    plt.show()


def analyse_return(matched):
    des_dict, des_ratio_dict = {}, {}
    win_ratio = {}
    exp_ret = {}
    # key = 'd_amount_ratio'  # d_amount  d_amount_ratio
    for client in [11, 18]:
        match_data = matched[matched['client_id'] == client]
        # draw_hist(match_data, client, 'd_amount')
        # draw_hist(match_data, client, 'd_amount_ratio')
        des_dict[client] = describe_price(match_data, 'd_amount')
        des_ratio_dict[client] = describe_price(match_data, 'd_amount_ratio')
        win_ratio[client] = get_win_ratio(match_data)
        exp_ret[client] = get_exp_return(match_data)

    des_data = pd.concat([pd.DataFrame.from_dict(des_dict[11]), pd.DataFrame.from_dict(des_dict[18])],
                         keys=[11, 18], names=['client_id', '统计量'], axis=0)
    des_ratio_data = pd.concat([pd.DataFrame.from_dict(des_ratio_dict[11]), pd.DataFrame.from_dict(des_ratio_dict[18])],
                               keys=[11, 18], names=['client_id', '统计量'], axis=0)
    win_ratio_data = pd.concat([pd.DataFrame.from_dict(win_ratio[11]), pd.DataFrame.from_dict(win_ratio[18])],
                               keys=[11, 18], names=['client_id', 'win_ratio'], axis=0)
    exp_ret_data = pd.concat([pd.DataFrame.from_dict(exp_ret[11]), pd.DataFrame.from_dict(exp_ret[18])],
                             keys=[11, 18], names=['client_id', '期望'], axis=0)
    exec_type = analyse_exec_type()
    # print('describe \n', des_ratio_data, '\n', des_data, '\n', win_ratio_data, '\n', exec_type)

    writer = pd.ExcelWriter(r'C:\pythonProj\data\match_order\analyse.xlsx')
    des_ratio_data.to_excel(writer, sheet_name='des_ratio_data')
    des_data.to_excel(writer, sheet_name='des_data')
    win_ratio_data.to_excel(writer, sheet_name='win_ratio_data')
    exec_type.to_excel(writer, sheet_name='exec_type')
    exp_ret_data.to_excel(writer, sheet_name='exp_ret_data')
    # for s in sheet_list:
    #     df.to_excel(writer, sheet_name=s)
    writer.save()
    writer.close()

    return des_data, win_ratio_data, exp_ret_data


def get_huobi_data(target='btcusdt', start_time=None, end_time=None, period='1min'):
    kline = Huobi_kline(symbol=target, period=period, start_time=start_time, end_time=end_time,
                        get_full_market_data=True)
    filename = target + '_' + period + '.csv'
    kline.to_csv(r'C:\pythonProj\data\match_order\{}'.format(filename))


def cut_data(trade_data, end_time, forward_hou=12):
    # 筛选出其 end_time 往前 forward_hour 这段时间范围内的所有数据
    period_data = trade_data[(trade_data.index >= end_time - forward_hour * 3600 * 1000) &
                             (trade_data.index <= end_time)]
    return period_data


def cal_volatility(matched, trade_data, symbol='btc', forward_hour=12):
    matched['{}_vol_{}h_ahead'.format(symbol, forward_hour)] = np.nan
    for i in range(len(matched)):
        current_time = matched.index[i]
        vol_trade_data = cut_data(trade_data, end_time=current_time, forward_hour=forward_hour)
        vol = np.log(vol_trade_data.close.shift() / vol_trade_data.close).std() * np.sqrt(365 * 24 * 60)  # log收益率的std 转化为年化波动率
        matched['{}_vol_{}h_ahead'.format(symbol, forward_hour)].iloc[i] = vol

    return matched #['vol_{}h_ahead'.format(forward_hour)]

def analyse_volatility(matched, forward_hour):
    # twap 代表是现货交易, 用 otchedge 代表是用合约交易
    vol_dict = {'盈利订单': {}, '亏损订单': {}}
    type_o = {'盈利订单': 1, '亏损订单': -1}
    for i in ['盈利订单', '亏损订单']:
        match_data = matched[matched['d_amount'] * type_o[i] > 0]

        vol_temp = {'总': {}, '线上服务': {}, '线下服务': {}}
        vol_temp['总'][f'BTC现货{forward_hour}h波动率'] = match_data['btc_vol_{}h_ahead'.format(forward_hour)].mean()
        vol_temp['总'][f'ETH现货{forward_hour}h波动率'] = match_data['eth_vol_{}h_ahead'.format(forward_hour)].mean()

        # for client in [11, 18]:
        #     piece = match_data[match_data['client_id'] == client]
        type_c = {11:'线上服务', 18:'线下服务'}
        for client in [11, 18]:
            piece = match_data[match_data['client_id'] == client]
            vol_temp[type_c[client]][f'BTC现货{forward_hour}h波动率'] = piece['btc_vol_{}h_ahead'.format(forward_hour)].mean()
            vol_temp[type_c[client]][f'ETH现货{forward_hour}h波动率'] = piece['eth_vol_{}h_ahead'.format(forward_hour)].mean()
        vol_dict[i] = vol_temp

    vol_data = pd.concat([pd.DataFrame.from_dict(vol_dict['盈利订单']), pd.DataFrame.from_dict(vol_dict['亏损订单'])],
                         keys=['盈利订单', '亏损订单'], names=['', '波动率'], axis=0)
    return vol_data

def analyse_d_time(matched):
    vol_dict = {'盈利订单': {}, '亏损订单': {}}
    type_c = {'盈利订单': 1, '亏损订单': -1}
    for i in ['盈利订单', '亏损订单']:
        match_data = matched[matched['d_amount'] * type_c[i] > 0]

        vol_temp = {'总': {}, 11: {}, 18: {}}
        vol_temp['总']['对冲锁价时间差'] = match_data['d_time'].mean()

        vol_temp[11]['对冲锁价时间差'] = match_data[match_data['client_id'] == 11]['d_time'].mean()
        vol_temp[18]['对冲锁价时间差'] = match_data[match_data['client_id'] == 18]['d_time'].mean()

        vol_dict[i] = vol_temp

    vol_data = pd.concat([pd.DataFrame.from_dict(vol_dict['盈利订单']), pd.DataFrame.from_dict(vol_dict['亏损订单'])],
                          keys=['盈利订单', '亏损订单'], names=['client_id', '均值'], axis=0)
    return vol_data

def get_trade_data(symbol='btcusdt', period=1):
    trade_data = pd.read_csv(r'C:\pythonProj\data\match_order\{}_{}min.csv'.format(symbol, period))  # 文件名 记得改回来
    trade_data.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    trade_data['datetime'] = pd.to_datetime(trade_data['datetime'])
    # 转换为 毫秒的 timestamp
    trade_data['datetime'] = trade_data['datetime'].apply(datetime.datetime.timestamp) * 1000
    trade_data = trade_data.set_index('datetime')
    return trade_data

def get_exec_type(data):
    # twap 代表是现货交易, 用 otchedge 代表是用合约交易
    exec_type = {'总': {}, '盈利订单': {}, '亏损订单': {}}
    exec_type['总']['现货交易'] = len(data[data['exec_algo'] == 'twap']) / len(data)
    exec_type['总']['合约交易'] = len(data[data['exec_algo'] == 'otchedge']) / len(data)
    exec_type['总']['alameda'] = len(data[data['exec_algo'] == 'alameda']) / len(data)

    type_c = {'盈利订单': 1, '亏损订单': -1}
    for i in ['盈利订单', '亏损订单']:
        piece = data[data['d_amount'] * type_c[i] > 0]
        exec_type[i]['现货交易'] = piece[piece['exec_algo'] == 'twap'].shape[0] / len(piece)
        exec_type[i]['合约交易'] = piece[piece['exec_algo'] == 'otchedge'].shape[0] / len(piece)
        exec_type[i]['alameda'] = piece[piece['exec_algo'] == 'alameda'].shape[0] / len(piece)
    return exec_type

def analyse_exec_type_():
    type_dict = {}
    for client in [11, 18]:
        match_data = matched[matched['client_id'] == client]
        type_dict[client] = get_exec_type(match_data)

    exec_type = pd.concat([pd.DataFrame.from_dict(type_dict[11]), pd.DataFrame.from_dict(type_dict[18])],
                          keys=[11, 18], names=['client_id', '比例'], axis=0)
    return exec_type

def analyse_exec_type():
    type_dict = {'盈利订单': {}, '亏损订单': {}}
    type_o = {'盈利订单': 1, '亏损订单': -1}
    for i in ['盈利订单', '亏损订单']:
        match_data = matched[matched['d_amount'] * type_o[i] > 0]

        type_temp = {'总': {}, '线上服务': {}, '线下服务': {}}
        type_temp['总']['现货交易'] = len(match_data[match_data['exec_algo'] == 'twap']) / len(match_data)
        type_temp['总']['合约交易'] = len(match_data[match_data['exec_algo'] == 'otchedge']) / len(match_data)
        type_temp['总']['alameda'] = len(match_data[match_data['exec_algo'] == 'alameda']) / len(match_data)
        # for client in [11, 18]:
        #     piece = match_data[match_data['client_id'] == client]
        type_c = {11: '线上服务', 18: '线下服务'}
        for client in [11, 18]:
            piece = match_data[match_data['client_id'] == client]
            type_temp[type_c[client]]['现货交易'] = piece[piece['exec_algo'] == 'twap'].shape[0] / len(piece)
            type_temp[type_c[client]]['合约交易'] = piece[piece['exec_algo'] == 'otchedge'].shape[0] / len(piece)
            type_temp[type_c[client]]['alameda'] = piece[piece['exec_algo'] == 'alameda'].shape[0] / len(piece)
        type_dict[i] = type_temp

    exec_type = pd.concat([pd.DataFrame.from_dict(type_dict['盈利订单']), pd.DataFrame.from_dict(type_dict['亏损订单'])],
                         keys=['盈利订单', '亏损订单'], names=['client_id', '比例'], axis=0)
    # print(exec_type)
    return exec_type

if __name__ == "__main__":
    matched = pd.read_csv(r'C:\pythonProj\data\match_order\matched_data_600s.csv', index_col=0)
    matched = matched.dropna()
    matched['d_time'] = matched['exec_place_time'] - matched.index  # ['quote_accept_time']

    # # #
    matched = compare_price(matched)
    # analyse_return(matched)


    # quote_accept_time 设为index
    # start_ts = matched.index.min() // 1000 - forward_hour * 3600  # 向下取整
    # end_ts = matched.index.max() // 1000 + 1  # 向上取整
    #
    # get_huobi_data(target='btcusdt', start_time=start_ts, end_time=end_ts, period='1min')  # btcusdt ethusdt
    # get_huobi_data(target='btcusdt', start_time=start_ts, end_time=end_ts, period='1min')  # btcusdt ethusdt


    # eth_data = get_trade_data('ethusdt', 1)
    # btc_data = get_trade_data('btcusdt', 1)
    # for forward_hour in [1, 12]:
    #     matched = cal_volatility(matched, eth_data, 'eth', forward_hour)
    #     matched = cal_volatility(matched, btc_data, 'btc', forward_hour)
    # matched[['client_id', 'side', 'd_time', 'btc_vol_1h_ahead', 'eth_vol_1h_ahead', 'btc_vol_12h_ahead', 'eth_vol_12h_ahead',
    #          'd_amount', 'd_amount_ratio']].to_csv(r'C:\pythonProj\data\match_order\vol.csv')
    vol_all = pd.read_csv(r'C:\pythonProj\data\match_order\vol.csv')
    # # 若只分析卖出对冲
    # vol_all = vol_all[vol_all['side'] == 'buy']
    vol_all.corr()[['d_amount', 'd_amount_ratio']].to_csv(r'C:\pythonProj\data\match_order\corr.csv')

    vol_data_list = []
    forward_hour_list = [1, 12]
    for forward_hour in forward_hour_list:
        vol_data = analyse_volatility(vol_all, forward_hour)  # matched
        vol_data_list.append(vol_data)

    # t_data = analyse_d_time(matched)
    writer = pd.ExcelWriter(r'C:\pythonProj\data\match_order\vol_analyse.xlsx')
    for i in range(len(forward_hour_list)):
        vol_data_list[i].to_excel(writer, sheet_name='vol{}h_data'.format(forward_hour_list[i]))
    # t_data.to_excel(writer, sheet_name='d_time_data')
    writer.save()
    writer.close()