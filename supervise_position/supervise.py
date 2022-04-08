"""
持仓监控
"""
import base64
import datetime
import hashlib
import hmac
import json
import logging
import time
import urllib

import requests
from decimal import *
from subuser_test.rest_utils import *
from api_and_ding.ding import DingReporter



class ProWorker:
    def __init__(self, api_key, secret_key, url=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        if not url:
            self._url = 'https://api.huobi.pro'  # 现货
        else:
            self._url = url
        self._futures_url = 'https://api.hbdm.com'  # 期货，不同合约 是否是同一个入口？
        self.api_key = api_key
        self.secret_key = secret_key
        self.accid = self._get_account_id()
        self.logger.info('initialize pro worker, url: {}, api_key: {}, '
                         'secret_key: {}, accid: {}'.format(
            self._url, self.api_key, self.secret_key, self.accid))

    def _get_account_id(self):
        accid = None
        res = api_key_get_hb(
            self._url, '/v1/account/accounts', {}, self.api_key, self.secret_key)
        if res.get('status') == 'ok':
            for info in res.get('data'):
                if info["type"] == "spot":
                    accid = str(info["id"])
                    break
        if accid is None:
            raise Exception('fail to get account id')
        return accid

    def get_all_sub_uid(self):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/user-list',
            {},
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:
            self.logger.error(res)
        # print(res.get('data'))
        uid_list = [i['uid'] for i in res.get('data')]
        return uid_list

    def get_aggregate_balance(self):
        res = api_key_get_hb(
            self._url, '/v1/subuser/aggregate-balance',
            {},
            self.api_key, self.secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            print('ERROR!', res)
        # print(res.get('data'))
        return res.get('data')

    def get_total_valuation(self):
        res = api_key_get_hb(
            self._url, '/v2/account/valuation',
            {},
            self.api_key, self.secret_key
        )
        if res.get('success') != True:
            self.logger.error(res)
            print('ERROR!', res)
        total_value = res.get('data').get('totalBalance')
        return total_value

    def test(self):
        # 获取子账户 uid
        sub_uid_list = self.get_all_sub_uid()
        sub_uid1, sub_uid2 = sub_uid_list[0], sub_uid_list[1]
        print(sub_uid1, sub_uid2)

        data = self.get_aggregate_balance()
        # print(data)
        data = [{
            "currency": "hbpoint",
            "balance": "10",
            "type": "point"
        },
        {
            "currency": "ada",
            "balance": "0",
            "type": "spot"
        },
        {
            "currency": "usdt",
            "balance": "8.08559165",
            "type": "spot"
        }]
        currency = [d.get('currency') for d in data if Decimal(d.get('balance'))>0]
        balance = [d.get('balance') for d in data if Decimal(d.get('balance'))>0]
        hold_info = dict(zip(currency, balance))
        return currency, hold_info


def get_forbid_coin(user_coins, permit_coins):
    forbid = [c for c in user_coins if c not in permit_coins]
    return forbid


def excess_limit(tier_coin):
    pass


if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf8') as fp:
        config = json.load(fp)
    api = config['user']['api']
    secret = config['user']['secret']
    permit_coins = config['permit_coins']

    p = ProWorker(api_key=api, secret_key=secret)
    currency, hold_info = p.test()
    print(currency)
    print(hold_info)

    forbid_coin = get_forbid_coin(currency, permit_coins)
    print(forbid_coin)

    ding = DingReporter(config['ding'])
    if len(forbid_coin) != 0:
        content = '账户内持仓了不允许持仓的币种: {}'.format(forbid_coin)
        print(content)
        ding.send_text(content)
    if not True:
        content = '账户内持仓了我们不允许持仓的币种: {}'.format(forbid_coin)
        print(content)
        ding.send_text(content)


