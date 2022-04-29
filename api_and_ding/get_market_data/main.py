import requests
# import ccxt
# exchange = ccxt.binance()
# markets = exchange.load_markets()
# print(markets)


period = '5m'
target = 'btcusdt'.upper()
contract_url = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit=1000".format(
    target, period
)  # &startTime={}&endTime={}
print(contract_url)
# resource.setrlimit(resource.RLIMIT_NOFILE, (the number you reset,resource.RLIM_INFINITY))


# s = requests.session()
# s.keep_alive = False
response = requests.get(contract_url, headers={'Connection': 'close'}, verify=False)
print(response.json())
response.close()

# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    pass




