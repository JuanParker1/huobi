"""
配资借贷账户测试方案 前7个函数
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

# from other_codes.otc_global.utils.rest_utils import api_key_get_hb, api_key_post_hb, http_get_request_hb  # request是可以把动作输入进去：get。pull'

# timeout in 5 seconds:
TIMEOUT = 5
ratelimit_remaining = 999
ratelimit_interval = 1000


# 各种请求,获取数据方式
def http_get_request(url, params, add_to_headers=None):
    global ratelimit_remaining
    global ratelimit_interval
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = urllib.parse.urlencode(params)
    try:
        if ratelimit_remaining <= 0:
            time.sleep(ratelimit_interval / 1000)
        response = requests.get(url, postdata, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            ratelimit_remaining = float(response.headers.get('ratelimit-remaining', ratelimit_remaining))
            ratelimit_interval = float(response.headers.get('ratelimit-interval', ratelimit_interval))
            return response.json()
        else:
            return {"status": "fail"}
    except Exception as e:
        print("httpGet failed, detail is:%s" % e)
        return {"status": "fail", "msg": "%s" % e}


def http_post_request(url, params, add_to_headers=None):
    global ratelimit_remaining
    global ratelimit_interval
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    try:
        if ratelimit_remaining <= 0:
            time.sleep(ratelimit_interval / 1000)
        response = requests.post(url, postdata, headers=headers, timeout=TIMEOUT, verify=False)
        if response.status_code == 200:
            ratelimit_remaining = float(response.headers.get('ratelimit-remaining', ratelimit_remaining))
            ratelimit_interval = float(response.headers.get('ratelimit-interval', ratelimit_interval))
            return response.json()
        else:
            return response.json()
    except Exception as e:
        print("httpPost failed, detail is:%s" % e)
        return {"status": "fail", "msg": "%s" % e}


def api_key_get(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({'AWSAccessKeyId': ACCESS_KEY,
                   'SignatureMethod': 'HmacSHA256',
                   'SignatureVersion': '2',
                   'Timestamp': timestamp})

    host_name = host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()

    params['Signature'] = createSign(params, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path
    return http_get_request(url, params)


def api_key_post(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {'AWSAccessKeyId': ACCESS_KEY,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Timestamp': timestamp}

    host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()
    params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
    return http_post_request(url, params)


def createSign(pParams, method, host_url, request_path, secret_key):
    sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = '\n'.join(payload)
    payload = payload.encode(encoding='UTF8')
    secret_key = secret_key.encode(encoding='UTF8')
    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature


def api_key_get_hb(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({'AccessKeyId': ACCESS_KEY,
                   'SignatureMethod': 'HmacSHA256',
                   'SignatureVersion': '2',
                   'Timestamp': timestamp})

    host_name = host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()

    params['Signature'] = createSign(params, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path
    return http_get_request(url, params)


def api_key_post_hb(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {'AccessKeyId': ACCESS_KEY,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Timestamp': timestamp}
    host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()
    params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
    return http_post_request(url, params)


def http_get_request_hb(url, params):
    postdata = urllib.parse.urlencode(params)
    try:
        response = requests.get(url, postdata, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "fail"}
    except Exception as e:
        print("httpGet failed, detail is:%s" % e)
        return {"status": "fail", "msg": "%s" % e}


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

    # 母子账户之间的转账 TODO
    def subuser_transfer(self, sub_uid, currency, amount, transfer_type):
        res = api_key_post_hb(
            self._url, '/v1/subuser/transfer',
            {
                "sub-uid": sub_uid,
                "currency": currency,
                "amount": amount,
                "type": transfer_type
            },
            self.api_key, self.secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            print('ERROR!', res)
        return res.get('data')

    def transfer_parent_to_sub(self, sub_uid, currency, amount):
        return self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-out')

    def transfer_sub_to_parent(self, sub_uid, currency, amount):
        return self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-in')

    # new
    # 下单函数 TODO
    def place_order(self, acc_id, amount):
        res = api_key_post_hb(
            self._url, '/v1/order/orders/place',
            {
                "account-id": acc_id,
                "amount": amount,
                "symbol": "ethusdt",
                "type": "buy-limit",
            },
            self.api_key, self.secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            print('下单 ERROR!', res)
        return res.get('data')  # .get('deductMode')

    def create_subuser(self):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/creation',
            {
                "userList": [
                    {
                        "userName": "testsubuser0001",
                        "note": "test-subuser"
                    },
                ]
            },
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:
            self.logger.error(res)
        return res.get('data').get('uid')  # .get('deductMode')

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

    # 1. 设置子用户手续费抵扣模式
    def set_subuser_deduct_mode(self, sub_uid=380841561):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/deduct-mode',
            {
                "subUids": sub_uid,
                "deductMode": 'sub'
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        return res.get('data')  # .get('deductMode')

    # 2.冻结/解冻子账户
    def lock_unlock_subuser(self, sub_uid=380841561, action='lock'):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/management',
            {
                "subUid": sub_uid,
                "action": action
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        # print(res.get('data'))
        # 看查询功能是否正常
        sub_state = self.get_subuser_state(sub_uid)

        # 看下单功能是否正常 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)
        return '子账户状态：{}，下单状态：{}'.format(sub_state, order)

    def get_subuser_acc_id(self, sub_uid=380841561):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/account-list',
            {
                "subUid": sub_uid,
            },
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:
            self.logger.error(res)
        # print(res.get('data'))
        return res.get('data').get('list')[2].get('accountIds')[0].get('accountId')

    # 3. 查询子账户用户状态
    def get_subuser_state(self, sub_uid=380841561):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/user-state',
            {
                "subUid": sub_uid,
            },
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:  # 状态码 显示 api 获取异常
            self.logger.error(res)
        return res.get('data').get('userState')

    # 4. 设置子账户交易权限
    def set_subuser_trade(self, sub_uid=380841561):
        # 设置关闭 isolated margin 的交易权限
        is_res = api_key_post_hb(
            self._url, '/v2/sub-user/tradable-market',
            {
                "subUids": sub_uid,
                "accountType": 'isolated-margin',  # cross-margin
                "activation": 'deactivated'
            },
            self.api_key, self.secret_key
        )
        if not is_res.get('ok'):
            self.logger.error(is_res)
            print('ERROR!', is_res)
        # 尝试进行下单动作来确认状态 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)
        if order:
            print('!!仍可交易！！')

        # 设置关闭 cross margin 的交易权限
        cr_res = api_key_post_hb(
            self._url, '/v2/sub-user/tradable-market',
            {
                "subUids": sub_uid,
                "accountType": 'cross-margin',  # cross-margin
                "activation": 'deactivated'
            },
            self.api_key, self.secret_key
        )
        if not cr_res.get('ok'):
            self.logger.error(cr_res)
            print('ERROR!', cr_res)
        # 尝试进行下单动作来确认状态 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)
        if order:
            print('!!仍可交易！！')
        return is_res.get('data')[0].get('activation'), cr_res.get('data')[0].get('activation')  #

    def get_access_key(self, uid):
        res = api_key_get_hb(
            self._url, '/v2/user/api-key',
            {
                "uid": uid,
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        # print(res.get('data'))
        return res.get('data')[0].get('accessKey')

    # 5. 修改子账户 API key
    def modify_subuser_api_key(self, sub_uid, sub_accessKey):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/api-key-modification',
            {
                "subUid": sub_uid,
                "accessKey": sub_accessKey,  # cross-margin
                "permission": 'readOnly'
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        # print(res.get('data'))

        # 测试账户是否能够进行交易 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)

        # 测试在不传入 ipAddress 这个参数的情况下是否会将原有设置的 ip 地址给删除掉
        if not res.get('data').get('ipAddresses'):
            ip_test = '不传入 ipAddress 参数会将原有设置的 ip 地址给删除掉'
        return '交易测试结果：{}, ip配置测试：{}'.format(order, ip_test)

    # 子账户之间的转账 TODO
    def transfer_sub_to_sub(self, sub_uid_from, sub_uid_to, currency, amount):
        acc_id_from = self.get_subuser_acc_id(sub_uid=sub_uid_from)
        acc_id_to = self.get_subuser_acc_id(sub_uid=sub_uid_to)
        res = api_key_post_hb(
            self._url, '/v1/account/transfer',
            {
                "from-user": sub_uid_from,
                "from-account-type": 'spot',
                "from-account": acc_id_from,
                "to-user": sub_uid_to,
                "to-account-type": 'spot',
                "to-account": acc_id_to,
                "currency": currency,
                "amount": amount
            },
            self.api_key, self.secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            print('ERROR!', res)
        return res.get('data')

    # 6. 设置子账户资产转出权限
    def set_subuser_transferable(self, sub_uid1, sub_uid2):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/transferability',
            {
                "subUids": sub_uid1,
                "accountType": 'spot',  # cross-margin
                "transferrable": 'false'
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)

        # 进行 子账户到母账户 的转账操作 TODO
        currency, amount = 'usdt', 0.0001
        sub2parent = self.transfer_sub_to_parent(sub_uid1, currency, amount)
        # 进行 子账户到子账户 的转账操作 TODO
        sub2sub = self.transfer_sub_to_sub(sub_uid1, sub_uid2, currency, amount)
        return sub2parent, sub2sub  # 转账结果

    # 7. 母子账户之间资产划转 TODO
    def check_4_sub_transfer(self, sub_uid, currency, amount):
        trans1 = self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-in')  # 子用户划转给母用户虚拟币
        trans2 = self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-out')  # 母用户划转给子用户虚拟币
        trans3 = self.subuser_transfer(sub_uid, currency, amount, 'master-point-transfer-in')  # 子用户划转给母用户点卡
        trans4 = self.subuser_transfer(sub_uid, currency, amount, 'master-point-transfer-out')  # 母用户划转给子用户点卡
        return trans1, trans2, trans3, trans4

    def test(self):
        # 获取子账户 uid
        sub_uid_list = self.get_all_sub_uid()
        while len(sub_uid_list) < 2:
            sub_uid_list.append(self.create_subuser())
        sub_uid1, sub_uid2 = sub_uid_list[0], sub_uid_list[1]
        # print(sub_uid1, sub_uid2)

        # 1. 设置子用户手续费抵扣模式
        re1 = self.set_subuser_deduct_mode(sub_uid1)
        print(f'test 1|设置子用户手续费抵扣模式| 子账户{re1[0].get("subUid")}的手续费抵扣模式: {re1[0].get("deductMode")}')

        # 2.冻结/解冻子账户
        re2_lock = self.lock_unlock_subuser(sub_uid1, action='lock')
        re2_unlock = self.lock_unlock_subuser(sub_uid1, action='unlock')
        print(f'test 2|冻结/解冻子账户| 冻结：{re2_lock}; 解冻：{re2_unlock}')

        # 3. 查询子账户用户状态
        sub_state = self.get_subuser_state(sub_uid1)
        print(f"test 3|查询子账户用户状态| 子账户{sub_uid1}的状态: {sub_state}")

        # 4. 设置子账户交易权限
        re4 = self.set_subuser_trade(sub_uid1)
        print(f"test 4|设置子账户交易权限| 关闭solated margin权限后是否可交易：{re4[0]}，关闭cross margin权限后是否可交易：{re4[1]}")

        # 5. 修改子账户 API key
        accesskey = self.get_access_key(sub_uid1)
        re5 = self.modify_subuser_api_key(sub_uid1, accesskey)
        print(f"test 5|修改子账户 API key| {re5}")

        # 6. 设置子账户资产转出权限
        sub2parent, sub2sub = self.set_subuser_transferable(sub_uid1, sub_uid2)
        print(f"test 6 |设置子账户资产转出权限| 设置权限关闭后，子账户转母账户 {sub2parent}，子账户转子账户 {sub2sub}")

        # 7. 母子账户之间资产划转
        t1, t2, t3, t4 = self.check_4_sub_transfer(sub_uid1, currency='usdt', amount=0.0001)
        print(f"test 7 |母子账户之间资产划转| 子用户划转给母用户虚拟币:{t1}, 母用户划转给子用户虚拟币:{t2},"
              f"子用户划转给母用户点卡:{t3}, 母用户划转给子用户点卡:{t4}")


if __name__ == '__main__':
    api = 'hrf5gdfghe-c2d03c8c-f4c4e8c7-cd08d'  # 'fb6e5a11-8ee79992-d927c71c-qz5c4v5b6n'
    secret = '24691826-9d56004b-4167f547-a1e5e'  # 'bb3c1e7b-a7f49452-05893315-d6170'

    p = ProWorker(api_key=api, secret_key=secret)
    p.test()
