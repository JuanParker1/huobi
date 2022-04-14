import time
import json
import urllib.parse
import hmac
import hashlib
import requests
import base64

# from other_codes.dingding_bot_and_async.ding import DingReporter
from api_and_ding.ding import DingReporter


def gen_timestamp():
    return int(time.time())


def gen_headers(time_stamp, key, sig):
    headers = {
        'Api-Timestamp': str(time_stamp),
        'Api-Key': key,
        'Api-Signature': sig,
        'Content-Type': 'application/json'
    }
    return headers


def gen_sign(secret, verb, path, timestamp, data=None):
    if data is None:
        data_str = ''
    else:
        assert isinstance(data, dict)
        # server并不要求data_str按key排序，只需此处用来签名的data_str和所发送请求中的data相同即可，是否排序请按实际情况选择
        data_str = json.dumps(data)
    message = verb + path + str(timestamp) + data_str
    print("\nmessage:", message)
    signature = hmac.new(base64.b64decode(secret), bytes(message, 'utf8'), digestmod=hashlib.sha256)
    signature = base64.b64encode(signature.digest()).decode()
    # print('signature:', signature)
    return signature


def test_get(api_key, api_secret):
    verb = 'GET'
    url = 'https://camtest.huobiapps.com/api/v1'  # 'https://www.camprod.org/api/v1'
    path = '/quote/single-tick?contract=index/eth.usdt'
    timestamp = gen_timestamp()
    sig = gen_sign(api_secret, verb, path, timestamp)
    headers = gen_headers(timestamp, api_key, sig)
    resp = requests.get(url + path, headers=headers)
    return resp.json()


def test_post(api_key, api_secret):
    verb = 'POST'
    url = 'https://camtest.huobiapps.com/api/v1'  # 'https://www.camprod.org/api/v1'
    path = '/otc-assets/broker/loan/collateral-valuation-haircut-setting'
    timestamp = gen_timestamp()
    post_data = {
        "underlying": "btc",
        "week_section": [0, 0, 0, 0, 0, 0, 1],
        "start_time": "00:00",
        "end_time": "23:59",
        "timezone": "+08:00",
        "discount_rate": "0.5",
    }
    sig = gen_sign(api_secret, verb, path, timestamp, post_data)
    headers = gen_headers(timestamp, api_key, sig)
    resp = requests.post(url + path, headers=headers, data=json.dumps(post_data).encode('utf-8'))
    return resp.json()


def get_single_tick(api_key, api_secret):
    verb = 'GET'
    url = 'https://camtest.huobiapps.com/api/v1'

    path = '/quote/batch-ticks?contracts=index/eth.usdt,huobip/btc.usdt'
    # path = '/otc-assets/broker/loan/summary-lit'

    '''↓↓↓借贷订单报警查询'''
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) - 1 * 86400))
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) + 7 * 86400))
    start_time = start_time.split(" ")
    start_time = "{}T{}.000Z".format(start_time[0], start_time[1])
    end_time = end_time.split(" ")
    end_time = "{}T{}.000Z".format(end_time[0], end_time[1])
    status = 'trigger'

    # path = "/riskcontrol/history/otc-loan/ltv/list?"
    # path += "begin={}&end={}&status={}".format(start_time, end_time, status)
    '''↑↑↑借贷订单报警查询'''

    '''↓↓↓订单信息实时查询'''
    # path = "/otc-assets/broker/loan/batch-records?type=loan_id&val="
    # path += ",".join(['211119845', '211119844', '211123477'])
    '''↑↑↑订单信息实时查询'''

    timestamp = gen_timestamp()
    sig = gen_sign(api_secret, verb, path, timestamp)
    headers = gen_headers(timestamp, api_key, sig)
    resp = requests.get(url + path, headers=headers)
    return resp.json()



if __name__ == "__main__":
    # 填入你的api_key
    api_key = 'llqcgQLvjrkrEXBijdrJkVJlicHSdwNwXjMrMiCnBYTB'
    # 填入你的api_secret
    api_secret = 'BRS3DdEyJxr+LSqz9GvGARElbCS+yoOeqQV6BkvjbxE='
    # res = get_single_tick(api_key, api_secret)
    # print(res)

    rs_get = test_get(api_key, api_secret)
    print(rs_get)
    # rs_post = test_post(api_key, api_secret)
    # print(rs_post)

    # secret = 'SEC8847c2eb4980651aceb5dca50daa713373c7276440395ee81be6f8d11c655902'
    # url = 'https://oapi.dingtalk.com/robot/send?access_token=2de56dc81131b65b3160fd6f2c958d51da2181a6c8857795db8936b01ea01284'
    #
    # config = {'url': url, 'secret': secret}  # config = {'uri': url, 'secret_key': secret}
    # d = DingReporter(config)
    # print('CAM API testing:\n'+str(json.dumps(rs_get, indent=2)))
    # d.send_text('CAM API testing:\n' + str(json.dumps(rs_get, indent=2)))
    # d.send(rs_get)


