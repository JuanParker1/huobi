import ccxt

# print(ccxt.exchanges)
#
# hb = ccxt.huobipro({
#     'apiKey': 'fb6e5a11-8ee79992-d927c71c-qz5c4v5b6n',
#     'secret': 'bb3c1e7b-a7f49452-05893315-d6170'
# })  # huobipro huobi
# print(hb.has)
# pair = 'ETH/BTC'
# limit = 5
# data = hb.fetch_order_book(pair, limit)
# print(data)
# bids = data['bids'][0]
# # asks = data['asks'][0]
#
# print(type(158069153))
#
# binance = ccxt.binance({
#     'apiKey': 'tJho9jXPC0bqYC3IdD2zWQ3FLC87w6rVDHvCQehWXj4q2h7IVWYyty35zDoA4O4P',
#     'secret': '6jBtXmaMgppsfr63zFWCehrOB9pdeQ3cvVraUFOlRrRqxu0C7hpaJAEO74RdWnir'
# })
# print(binance.has)
#
# symbol = 'BTC/USDT'
# order_book = binance.fetch_order_book(symbol, limit=5)
# print(order_book)
import numpy as np
import time
import datetime
from api_and_ding.ding import DingReporter

import json


with open(r'C:\pythonProj\order_analyse\config.json', 'r', encoding='utf8') as fp:
    config = json.load(fp)
ding = DingReporter(config['ding'])

while True:
    # 近期数据
    start_ts = config['last_timestamp']
    ding.send_text('{} - {} 时间段内无新订单'.format(str(datetime.datetime.fromtimestamp(start_ts//1000)),
                                            str(datetime.datetime.fromtimestamp(time.time()))))
    break


# "last_neworder_id": 5,
# "last_timestamp": 1646883273378