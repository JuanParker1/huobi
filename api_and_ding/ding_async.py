import base64
import hashlib
import hmac
import json
import time
import urllib.parse

import aiohttp


class DingReporter:
    def __init__(self, config):
        self._uri = config['uri']
        self._secret = config['secret_key']

    def _sign(self):
        timestamp = str(round(time.time() * 1000))
        hmac_code = hmac.new(self._secret.encode(), '{}\n{}'.format(timestamp, self._secret).encode(),
                             digestmod=hashlib.sha256).digest()
        return timestamp, urllib.parse.quote_plus(base64.b64encode(hmac_code))

    async def send(self, text):
        data = {
            'msgtype': 'text',
            'text': {
                'content': text
            }
        }
        ts, signature = self._sign()
        headers = {'content-type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            try:
                await session.post('{}&timestamp={}&sign={}'.format(self._uri, ts, signature), data=json.dumps(data),
                                   headers=headers)
            except Exception as e:
                print(e)
                print('retry later')

    async def send_alert(self, text, mobile=['13226635604', '13612950214']):
        data = {
            'msgtype': 'text',
            'text': {
                'content': text
            },
            'at': {
                "atMobiles": mobile,
                "isAtAll": False
            }
        }
        ts, signature = self._sign()
        headers = {'content-type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            try:
                await session.post('{}&timestamp={}&sign={}'.format(self._uri, ts, signature), data=json.dumps(data),
                                   headers=headers)
            except Exception as e:
                print(e)
                print('retry later')
