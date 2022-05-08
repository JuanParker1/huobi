import ccxt

print(ccxt.exchanges)

hb = ccxt.huobipro({
    'apiKey': 'fb6e5a11-8ee79992-d927c71c-qz5c4v5b6n',
    'secret': 'bb3c1e7b-a7f49452-05893315-d6170'
})  # huobipro huobi
print(hb.has)
pair = 'ETH/BTC'
limit = 5
data = hb.fetch_order_book(pair, limit)
print(data)
bids = data['bids'][0]
# asks = data['asks'][0]

print(type(158069153))

binance = ccxt.binance({
    'apiKey': 'tJho9jXPC0bqYC3IdD2zWQ3FLC87w6rVDHvCQehWXj4q2h7IVWYyty35zDoA4O4P',
    'secret': '6jBtXmaMgppsfr63zFWCehrOB9pdeQ3cvVraUFOlRrRqxu0C7hpaJAEO74RdWnir'
})
print(binance.has)

symbol = 'BTC/USDT'
order_book = binance.fetch_order_book(symbol, limit=5)
print(order_book)
