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
from subuser_test.rest_utils import *



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

    def test(self):
        # 获取子账户 uid
        sub_uid_list = self.get_all_sub_uid()
        sub_uid1, sub_uid2 = sub_uid_list[0], sub_uid_list[1]
        print(sub_uid1, sub_uid2)

        balance = self.get_aggregate_balance()
        print(balance)
        currency = [d.get('currency') for d in balance]

def have_forbid_coin(user_coins, permit_coins):
    pass

def excess_limit(tier_coin = []):
    pass


if __name__ == '__main__':
    api = 'hrf5gdfghe-c2d03c8c-f4c4e8c7-cd08d'  # 'fb6e5a11-8ee79992-d927c71c-qz5c4v5b6n'
    secret = '24691826-9d56004b-4167f547-a1e5e'  # 'bb3c1e7b-a7f49452-05893315-d6170'

    permit_coins = ['usdt', 'usdc', 'husd', 'fil', 'ltc', 'xrp', 'bch', 'bsv', 'trx', 'link',
                    'pax', 'etc', 'bnb', 'ada', 'doge', 'xlm', 'xmr', 'eos', 'neo', 'comp',
                    'dash', 'zec', 'btg', 'sol', 'avax', 'cake', 'axs', 'qnt', 'shib', 'perp',
                    'nexo', 'sand', 'skl', 'dydx', 'cream', 'btc', 'eth', 'dai', 'moita',
                    '1inch', 'slp', 'sushi', 'dot', 'uni', 'wbtc', 'aave', 'cro']

    p = ProWorker(api_key=api, secret_key=secret)
    p.test()
