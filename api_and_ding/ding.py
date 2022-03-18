import base64
import hashlib
import hmac
import time
import urllib.parse

import requests
import json


class DingReporter:
    def __init__(self, config):
        self._url = config['url']
        self._secret = config['secret']

    def _sign(self):
        # 当前时刻
        timestamp = str(round(time.time() * 1000))
        # 获取 sign
        secret_enc = self._secret.encode('utf-8')
        string_to_sign_enc = '{}\n{}'.format(timestamp, self._secret).encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    def send_text(self, text):
        # 定义数据类型
        headers = {'content-type': 'application/json'}
        # 要发送的数据
        data = {
            'msgtype': 'text',
            'text': {'content': text}
        }
        ts, signature = self._sign()
        try:
            requests.post('{}&timestamp={}&sign={}'.format(self._url, ts, signature), data=json.dumps(data),
                                   headers=headers)
        except Exception as e:
            print(e)
            print('retry later')



if __name__ == "__main__":
    secret = 'SEC8847c2eb4980651aceb5dca50daa713373c7276440395ee81be6f8d11c655902' # 'SEC152f308b49c00490b59d498f50eb7ce3b9382dff7cb8c8b44cb6f072c435abe5'
    url = 'https://oapi.dingtalk.com/robot/send?access_token=2de56dc81131b65b3160fd6f2c958d51da2181a6c8857795db8936b01ea01284' # 'https://oapi.dingtalk.com/robot/send?access_token=800ce56822d8e4c3cc9eb241916c9c093a97409e54cb90833f909f9847a7e1f9'

    config = {'url': url, 'secret': secret}
    d = DingReporter(config)
    d.send_text('test')