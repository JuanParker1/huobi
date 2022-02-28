import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd


def compare_price(match_data):
    # 计算 溢价率，胜率（盈利>0），胜率（盈利>=0）
    match_data['d_price'] = match_data.apply(lambda x: x['exec_price'] - x['price'] if (x['side'] == 'sell') else
                                             x['price'] - x['exec_price'], axis=1)
    match_data['d_price_ratio'] = match_data['d_price'] / match_data['price']
    return match_data


def describe_price(match_data, key='d_price_ratio'):
    # 描述性统计
    des_dict = {}
    des_dict['总'] = match_data[key].describe(percentiles=[0.5]).to_dict()
    des_dict['买入'] = match_data[match_data['side'] == 'buy'][key].describe(percentiles=[0.5]).to_dict()
    des_dict['卖出'] = match_data[match_data['side'] == 'sell'][key].describe(percentiles=[0.5]).to_dict()
    return des_dict


def analyse_win_ratio(match_data):
    # 胜率
    win_ratio = {'总': {}, '买入': {}, '卖出': {}}
    win_ratio['总']['胜率（盈利>0）'] = match_data[match_data['d_price']>0].shape[0] / len(match_data)
    win_ratio['总']['胜率（盈利>=0）'] = match_data[match_data['d_price']>=0].shape[0] / len(match_data)

    type_c = {'buy': '买入', 'sell': '卖出'}
    for i in ['buy', 'sell']:
        piece = match_data[match_data['side'] == i]
        win_ratio[type_c[i]]['胜率（盈利>0）'] = piece[piece['d_price']>0].shape[0] / len(piece)
        win_ratio[type_c[i]]['胜率（盈利>=0）'] = piece[piece['d_price']>=0].shape[0] / len(piece)
    return win_ratio


def draw_hist(match_data, client_id, key='d_price_ratio'):
    key_dict = {'d_price_ratio': '相对价差', 'd_price': '绝对价差'}

    mpl.rcParams['font.sans-serif'] = ['SimHei']  # 配置显示中文，否则乱码
    mpl.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号，如果是plt画图，则将mlp换成plt

    plt.figure(figsize=(12, 10))
    plt.subplot(2, 1, 1)
    plt.hist(match_data[match_data['side'] == 'buy'][key], label=u'买入'+key_dict[key], bins=30, facecolor='y',
             edgecolor='k')
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylabel(u'频数', fontsize=13)
    plt.legend(loc=0, fontsize=13)
    # plt.text(-0.0100, 1000, r"溢价率 = $\frac{exec price-quote price}{quote price}$", fontsize=20)
    plt.grid(True)
    plt.title(f"{key_dict[key]}分布情况（client_id={client_id})", fontsize=30)  # ('溢价率=实际交易价格-客户报价/客户报价')

    plt.subplot(2, 1, 2)
    plt.hist(match_data[match_data['side'] == 'sell'][key], label=u'卖出'+key_dict[key], bins=30, facecolor='r',
             edgecolor='k')
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylabel(u'频数', fontsize=13)
    plt.legend(loc=0, fontsize=13)
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    matched = pd.read_csv(r'C:\pythonProj\data\match_order\matched_data_60s.csv')
    matched = matched.dropna()

    matched = compare_price(matched)
    # draw_hist(matched)

    des_dict = {}
    win_ratio = {}
    key = 'd_price'  # d_price  d_price_ratio
    for client in [11, 18]:
        match_data = matched[matched['client_id'] == client]
        draw_hist(match_data, client, key)
        des_dict[client] = describe_price(match_data, key)
        win_ratio[client] = analyse_win_ratio(match_data)

    des_data = pd.concat([pd.DataFrame.from_dict(des_dict[11]), pd.DataFrame.from_dict(des_dict[18])],
                          keys=[11, 18], names=['client_id', '统计量'], axis=0)

    win_ratio_data = pd.concat([pd.DataFrame.from_dict(win_ratio[11]), pd.DataFrame.from_dict(win_ratio[18])],
                               keys=[11, 18], names=['client_id', 'win_ratio'], axis=0)
    des_data['卖出'] = round(des_data['卖出'], 6)
    print('describe \n', des_data, '\n', win_ratio_data)
