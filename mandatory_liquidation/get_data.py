import time
import pandas as pd

from api_and_ding.get_market_data.huobi_data import Huobi_kline


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


def download_all_coin_data(coins):
    # 生成 timestamp
    start_time = int(time.mktime((2021, 5, 12, 0, 0, 0, 0, 0, 0)))
    end_time = int(time.mktime((2022, 3, 12, 0, 0, 0, 0, 0, 0)))
    for i in range(len(coins) - 12, 10, -1):  # 10, len(coins)): # 若从前往后，是第十个
        coin = coins[i]
        print('\n......', coin)
        get_trade_data(target=coin, start_time=start_time, end_time=end_time, period='5min')


def load_all_coin_data_to_dict(coins):
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

if __name__ == "__main__":
    download_all_coin_data(coins)