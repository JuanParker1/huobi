# -*- coding: utf-8 -*-
"""
子母账户功能测试
完整修订版
"""
import logging
import time

from rest_utils import api_key_get_hb, api_key_post_hb  # request是可以把动作输入进去：get。pull'


class ProWorker:
    def __init__(self, api_key, secret_key, url=None):
        """
        在此不单独使用api key 和 secret key 进行查询, 而是默认把母账户的 access key 和 secret key 作为 api key 和 secret key
        :param api_key: the access key of master account
        :param secret_key: the secret key of master account
        :param url: the base url of the api service
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if not url:
            self._url = 'https://api.huobi.pro'  # 现货
        else:
            self._url = url
        self._futures_url = 'https://api.hbdm.com'  # 衍生品
        self.api_key = api_key
        self.secret_key = secret_key

        self.accid = self._get_account_id()
        self.logger.info('initialize pro worker, url: {}, api_key: {}, '
                         'secret_key: {}, accid: {}'.format(
            self._url, self.api_key, self.secret_key, self.accid))

    def _get_account_id(self, api_key=None, secret_key=None, account_type='spot', subtype='btcusdt'):
        if not api_key:
            api_key = self.api_key
        if not secret_key:
            secret_key = self.secret_key
        accid = None
        res = api_key_get_hb(
            self._url, '/v1/account/accounts', {}, api_key, secret_key)
        if res.get('status') == 'ok':
            for info in res.get('data'):
                if account_type != 'margin':
                    if info["type"] == account_type:
                        accid = str(info["id"])
                        break
                else:
                    if info['subtype'] == subtype:
                        accid = str(info["id"])
                        break
        else:
            raise Exception('you get wrong account id data')
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

    def get_balance(self, accid=None, api_key=None, secret_key=None):
        if not accid:
            accid = self.accid
        if not api_key:
            api_key = self.api_key
        if not secret_key:
            secret_key = self.secret_key
        res = api_key_get_hb(
            self._url, '/v1/account/accounts/{accid}/balance'.format(accid=accid),
            {}, api_key, secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
        return res.get('data')

    # new
    # 下单函数 TODO
    def place_order(self, acc_id, symbol, amount,
                    order_type='buy-limit', source='spot-api',
                    api_key=None, secret_key=None):
        if not api_key:
            api_key = self.api_key
        if not secret_key:
            secret_key = self.secret_key
        params = {
            "account-id": acc_id,
            "amount": amount,
            "symbol": symbol,
            "type": order_type,
            "source": source
        }
        res = api_key_post_hb(
            self._url,
            '/v1/order/orders/place',
            params,
            api_key,
            secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            raise ValueError('place {} {} {} order in {} error!'.format(symbol, amount, order_type, source[:-4]), res)
        return res.get('data')  # 这里返回的是 order id, 需要根据这个 order id取过去订单信息

    def get_order(self, order_id, api_key=None, secret_key=None):  # 获取 order id 的信息
        if not api_key:
            api_key = self.api_key
        if not secret_key:
            secret_key = self.secret_key
        params = {
            'order-id': order_id
        }
        res = api_key_get_hb(self._url, '/v1/order/orders/{}'.format(order_id), params, api_key, secret_key)
        if res.get('status') != 'ok':
            self.logger.error(res)
            raise ValueError('')
        r = res.get('data')
        return "{} {} {} at {} has filled {}".format(r['amount'], r['symbol'], r['type'], r['price'], r['field-amount'])

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
    def set_subuser_deduct_mode(self, sub_uid=380841561, deduct_mode='sub'):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/deduct-mode',
            {
                "subUids": sub_uid,
                "deductMode": deduct_mode
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        return res.get('data')  # .get('deductMode')

    # 2.冻结/解冻子账户
    def lock_unlock_subuser(self, sub_uid, action='lock'):
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
        time.sleep(1)
        # 返回当前账户状态
        sub_state = self.get_subuser_state(sub_uid)

        return 'status of sub account：{}'.format(sub_state)

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
        return "isolate-margin status: {}, cross-margin status: {}".format(
            is_res.get('data')[0].get('activation'), cr_res.get('data')[0].get('activation')
        )

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
    # 如果不填入ipAddress, 那就默认不修改
    def modify_subuser_api_key(self, sub_uid, sub_accessKey, permission='readOnly'):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/api-key-modification',
            {
                "subUid": sub_uid,
                "accessKey": sub_accessKey,  # cross-margin
                "permission": permission
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        return 'the current permission for {} {} is: {}'.format(sub_uid, sub_accessKey,
                                                                res.get('data').get('permission'))

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
    def set_subuser_transferable(self, sub_uid1):
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
        else:
            return 'sub account cannot transfer out now'

    # 7. 母子账户之间资产划转 TODO
    def check_4_sub_transfer(self, sub_uid, currency, amount):
        trans1 = self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-in')  # 子用户划转给母用户虚拟币
        trans2 = self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-out')  # 母用户划转给子用户虚拟币
        trans3 = self.subuser_transfer(sub_uid, currency, amount, 'master-point-transfer-in')  # 子用户划转给母用户点卡
        trans4 = self.subuser_transfer(sub_uid, currency, amount, 'master-point-transfer-out')  # 母用户划转给子用户点卡
        return trans1, trans2, trans3, trans4

    def margin_account_transfer(self, account_type, from_account, currency, amount: str, symbol=None, api_key=None,
                                secret_key=None):
        if not api_key:
            api_key = self.api_key
        if not secret_key:
            secret_key = self.secret_key

        if account_type not in {'margin', 'cross-margin'}:
            raise ValueError('account_type should be margin or cross-margin, please check')
        if from_account not in {'spot', 'margin'}:
            raise ValueError('from_account should be spot or margin, please check')
        if account_type == 'margin' and not symbol:
            raise ValueError('you should input symbol for margin transfer')
        # 现货账户与逐仓杠杆账户的资产互转
        if account_type == 'margin' and from_account == 'margin':
            path = '/v1/dw/transfer-out/margin'
            params = {
                'symbol': symbol,
                'currency': currency,
                'amount': amount
            }
        elif account_type == 'margin' and from_account == 'spot':
            path = '/v1/dw/transfer-in/margin'
            params = {
                'symbol': symbol,
                'currency': currency,
                'amount': amount
            }
        # 现货账户与全仓杠杆账户的资产互转
        elif account_type == 'cross-margin' and from_account == 'margin':
            path = '/v1/cross-margin/transfer-out'
            params = {
                'currency': currency,
                'amount': amount
            }
        else:
            path = '/v1/cross-margin/transfer-in'
            params = {
                'currency': currency,
                'amount': amount
            }

        res = api_key_post_hb(self._url, path, params, api_key, secret_key)
        if from_account == 'margin':
            to_account = 'spot'
        else:
            to_account = account_type
        try:
            if res.get('status') == 'ok':
                return 'transfer {} {} from {} to {} success'.format(amount, currency, from_account, to_account)
            else:
                raise ValueError(
                    'transfer {} {} from {} to {} fail, please check'.format(amount, currency, from_account, to_account)
                )
        except Exception as e:
            raise ValueError(e)

    def test_first_7_func(self, sub_account_info):
        """
        :param sub_account_info: it's a dict, contains uid, access_key and secret_key
        sub_account_info = {
            "uid": "",
            "api_key": "",
            "secret_key": ""
        }
        :return:
        """
        sub_uid = sub_account_info['uid']
        sub_api_key = sub_account_info['api_key']
        sub_secret_key = sub_account_info['secret_key']
        sub_account_id = self._get_account_id(sub_api_key, sub_secret_key)

        # 1. 设置子用户手续费抵扣模式
        re1 = self.set_subuser_deduct_mode(sub_uid)
        time.sleep(0.5)
        print(f'test 1|设置子用户手续费抵扣模式| 子账户{re1[0].get("subUid")}的手续费抵扣模式: {re1[0].get("deductMode")}')

        # 2.冻结/解冻子账户. 冻结账户会停用其所有 API 功能, 所以查询一下就好了
        re2_lock = self.lock_unlock_subuser(sub_uid, action='lock')
        try:
            query_test = self._get_account_id(api_key=sub_api_key, secret_key=sub_secret_key)
            print('after lock this account, it can still query. query account id is: {}'.format(query_test))
        except Exception as e:
            print('account has been successfully locked, the exception info is: {}'.format(e))
        time.sleep(1)
        re2_unlock = self.lock_unlock_subuser(sub_uid, action='unlock')
        # TODO: 解锁之后看看功能是否正常, 查询, 转账和交易是否能够正常进行
        try:
            query_test = self._get_account_id(api_key=sub_api_key, secret_key=sub_secret_key)
            print('account has been successfully unlocked, the query info is: {}'.format(query_test))
        except Exception as e:
            print("after unlock this account, it can't query. exception info is: {}".format(e))
        print(f'test 2|冻结/解冻子账户| 冻结：{re2_lock}; 解冻：{re2_unlock}')

        # 3. 查询子账户用户状态
        sub_state = self.get_subuser_state(sub_uid)
        print(f"test 3|查询子账户用户状态| 子账户{sub_uid}的状态: {sub_state}")

        # 4. 设置子账户交易权限
        re4 = self.set_subuser_trade(sub_uid)
        print(f"test 4|设置子账户交易权限| 关闭isolated margin权限后是否可交易：{re4[0]}，关闭cross margin权限后是否可交易：{re4[1]}")
        time.sleep(1)
        # 测试逐仓杠杆  从现货账户划转至逐仓杠杆账户
        transfer_to_isolate_margin = self.margin_account_transfer(
            account_type='margin', from_account='spot', currency='usdt', amount='20',
            symbol='xrpusdt', api_key=sub_api_key, secret_key=sub_secret_key
        )
        try:
            # buy-market 市价买入
            order_id_buy = self.place_order(
                acc_id=sub_account_id, symbol='xrpusdt', amount=20, order_type='buy-market',
                api_key=sub_api_key, secret_key=sub_secret_key, source='margin-api'
            )
            print(order_id_buy)
            time.sleep(1)
            # 获取 xrp 交易的 amount
            amount = self.get_balance(
                self._get_account_id(sub_api_key, sub_secret_key, account_type='margin', subtype='xrpusdt'),
                sub_api_key, sub_secret_key
            )
            for i in amount['list']:
                if i['currency'] == 'xrp' and i['type'] == 'trade':
                    amount = i['balance']
                    break
            # sell-market 市价卖出
            order_id_sell = self.place_order(
                acc_id=sub_account_id, symbol='xrpusdt', amount=amount, order_type='sell-market',
                api_key=sub_api_key, secret_key=sub_secret_key, source='margin-api'
            )
            time.sleep(1)
            # 获取 xrp 交易的 amount
            amount = self.get_balance(
                self._get_account_id(sub_api_key, sub_secret_key, account_type='margin', subtype='xrpusdt'),
                sub_api_key, sub_secret_key
            )
            for i in amount['list']:
                if i['currency'] == 'usdt' and i['type'] == 'trade':
                    amount = i['balance']
                    break
            # 将金额从逐仓杠杆账户划转回现货账户
            transfer_out_isolate_margin = self.margin_account_transfer(
                account_type='margin', from_account='margin', currency='usdt', amount=amount,
                symbol='xrpusdt', api_key=sub_api_key, secret_key=sub_secret_key
            )
            print(order_id_sell)
            print('isolated-margin account can still trade now, please check')
        except Exception as e:
            print('isolated-margin account cannot trade now')
            # 将金额从逐仓杠杆账户划转回现货账户
            transfer_to_cross_margin = self.margin_account_transfer(
                account_type='margin', from_account='margin', currency='usdt', amount='20',
                symbol='xrpusdt', api_key=sub_api_key, secret_key=sub_secret_key
            )

        # 测试全仓杠杆
        transfer_to_cross_margin = self.margin_account_transfer(
            account_type='cross-margin', from_account='spot', currency='usdt', amount='20',
            api_key=sub_api_key, secret_key=sub_secret_key
        )
        try:
            order_id_buy = self.place_order(
                acc_id=sub_account_id, symbol='xrpusdt', amount=20, order_type='buy-market',
                api_key=sub_api_key, secret_key=sub_secret_key, source='super-margin-api'
            )
            print(order_id_buy)
            time.sleep(1)
            amount = self.get_balance(
                self._get_account_id(sub_api_key, sub_secret_key, account_type='super-margin'),
                sub_api_key, sub_secret_key
            )
            for i in amount['list']:
                if i['currency'] == 'xrp' and i['type'] == 'trade':
                    amount = i['balance']
                    break
            order_id_sell = self.place_order(
                acc_id=sub_account_id, symbol='xrpusdt', amount=amount, order_type='sell-market',
                api_key=sub_api_key, secret_key=sub_secret_key, source='super-margin-api'
            )
            time.sleep(1)
            amount = self.get_balance(
                self._get_account_id(sub_api_key, sub_secret_key, account_type='super-margin'),
                sub_api_key, sub_secret_key
            )
            for i in amount['list']:
                if i['currency'] == 'usdt' and i['type'] == 'trade':
                    amount = i['balance']
                    break
            transfer_out_cross_margin = self.margin_account_transfer(
                account_type='cross-margin', from_account='margin', currency='usdt', amount=amount,
                symbol='xrpusdt', api_key=sub_api_key, secret_key=sub_secret_key
            )
            print(order_id_sell)
            print('cross-margin account can still trade now, please check')
        except Exception as e:
            print('cross-margin account cannot trade now')
            transfer_to_cross_margin = self.margin_account_transfer(
                account_type='cross-margin', from_account='margin', currency='usdt', amount='20',
                symbol='xrpusdt', api_key=sub_api_key, secret_key=sub_secret_key
            )

        # 5. 修改子账户 API key. 测试是否能够使用交易功能
        re5_readonly = self.modify_subuser_api_key(sub_uid, sub_api_key, permission='readOnly')
        print(re5_readonly)
        time.sleep(1)
        # 测试交易功能: 先买再卖
        try:
            order_id_sell = self.place_order(
                acc_id=sub_account_id, symbol='usdthusd', amount=11, order_type='sell-market',
                api_key=sub_api_key, secret_key=sub_secret_key
            )
            time.sleep(1)
            sell_order_info = self.get_order(order_id_sell, sub_api_key, sub_secret_key)
            print(sell_order_info)
            # TODO: 这里应该先 get_account_info 然后再进行交易, 把 HUSD 全给处理掉
            amount = self.get_balance(
                self._get_account_id(sub_api_key, sub_secret_key), sub_api_key, sub_secret_key
            )
            order_id_buy = self.place_order(
                acc_id=sub_account_id, symbol='usdthusd', amount=amount, order_type='buy-market',
                api_key=sub_api_key, secret_key=sub_secret_key
            )
            buy_order_info = self.get_order(order_id_buy, sub_api_key, sub_secret_key)
            print(buy_order_info)
        except Exception as e:
            print(
                'you have successfully set the permission of this api key as readOnly, exception info is: {}'.format(e))
        # 修改 为 readOnly,trade 再看是否能正常交易
        re5_read_trade = self.modify_subuser_api_key(sub_uid, sub_api_key, permission='readOnly,trade')
        print(re5_read_trade)
        time.sleep(1)
        try:
            order_id_sell = self.place_order(
                acc_id=sub_account_id, symbol='usdthusd', amount=11, order_type='sell-market',
                api_key=sub_api_key, secret_key=sub_secret_key
            )
            time.sleep(1)
            sell_order_info = self.get_order(order_id_sell, sub_api_key, sub_secret_key)
            print(sell_order_info)
            amount = self.get_balance(
                self._get_account_id(sub_api_key, sub_secret_key), sub_api_key, sub_secret_key
            )
            order_id_buy = self.place_order(
                acc_id=sub_account_id, symbol='usdthusd', amount=amount, order_type='buy-market',
                api_key=sub_api_key, secret_key=sub_secret_key
            )
            buy_order_info = self.get_order(order_id_buy, sub_api_key, sub_secret_key)
            print(buy_order_info)
            print('you have successfully set the permission of this api key as trade')
        except Exception as e:
            print("you can't trade after set the permission of this api key as trade, exception info is: {}".format(e))
        print(f"test 5|修改子账户 API key finished")

        # 6. 设置子账户资产转出权限
        sub2parent, sub2sub = self.set_subuser_transferable(sub_uid)
        print(f"test 6 |设置子账户资产转出权限| 设置权限关闭后，子账户转母账户 {sub2parent}，子账户转子账户 {sub2sub}")

        # 7. 母子账户之间资产划转
        t1, t2, t3, t4 = self.check_4_sub_transfer(sub_uid, currency='usdt', amount=0.0001)
        print(f"test 7 |母子账户之间资产划转| 子用户划转给母用户虚拟币:{t1}, 母用户划转给子用户虚拟币:{t2},"
              f"子用户划转给母用户点卡:{t3}, 母用户划转给子用户点卡:{t4}")

    # 8.子母账户获取用户UID
    def get_UID(self):
        uid = None
        res = api_key_get_hb(self._url, '/v2/user/uid', {}, self.api_key, self.secret_key)
        uid = res.get('data')
        if uid is None:
            raise Exception('fail to get account id')
        print('用户UID为：', uid)
        return uid

    # 9.子账户充币地址查询 TODO
    def get_sub_deposit_address(self, self_uid, currency):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/deposit-address',
            {
                'subUid': self_uid,
                'currency': currency,
            },
            self.api_key, self.secret_key
        )
        print('子账户充币地址为：', res.get('data'))
        return res.get('data')

    # 10.子用户充币记录查询 TODO
    def get_sub_deposit(self, self_uid, currency=None, starttime=None, endtime=None, sort=None, limit=None,
                        fromld=None):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/query-deposit',
            {
                'subUid': self_uid,
                'currency': currency,  # 省缺为所有币种
                'startTime': starttime,  # 省缺为endtime-30天
                'endTime': endtime,  # 省缺为当前时间
                'sort': sort,  # 省缺为desc由近及远
                'limit': limit,  # 单页最大返回条目数量 [1-500] （缺省值100）
                'fromId': fromld  # 起始充币订单ID
            },
            self.api_key, self.secret_key
        )
        print('子用户充币记录：', res.get('data'))
        return res.get('data')

    # 11.子用户余额汇总  TODO
    def get_sub_balance_summary(self):
        balance = None
        res = api_key_get_hb(self._url, '/v1/subuser/aggregate-balance', {}, self.api_key, self.secret_key)
        balance = res.get('data')
        if balance is None:
            raise Exception('fail to get account id')
        print('当前子账户余额汇总信息为：', balance)
        return balance

    # 12.子用户余额   TODO
    def get_sub_balance(self, self_uid):
        res = api_key_get_hb(
            self._url, '/v1/account/accounts/{sub_uid}'.format(sub_uid=self_uid),
            {}, self.api_key, self.secret_key)
        if res.get('status') != 'ok':
            self.logger.error(res)
        print('子用户{}的余额信息为'.format(self_uid), res.get('data'))
        return res.get('data')

    # 查找所有子账户
    def get_sub_uid(self):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/user-list',
            {}, self.api_key, self.secret_key)
        if res.get('status') != 'ok':
            self.logger.error(res)

        return res.get('data')

    # 创建子账户
    def create_sub(self):
        res = api_key_post_hb(self._url, '/v2/sub-user/creation',
                              {
                                  "userList": [
                                      {
                                          "userName": "testsublin",
                                          "note": "huobi"
                                      }
                                  ]
                              },
                              self.api_key, self.secret_key)
        return res.get('data')


if __name__ == '__main__':
    api = 'hrf5gdfghe-c2d03c8c-f4c4e8c7-cd08d'
    secret = '24691826-9d56004b-4167f547-a1e5e'
    test = ProWorker(api_key=api, secret_key=secret)
    # 1-7
    # q = test.test_first_7_func()
    # 8.获取UID
    # a = test.get_UID()
    # 9.获取充币地址
    # b= test.get_sub_deposit_address(self_uid=380855234,currency='usdt')
    # 10.获取充币记录
    # c=test.get_sub_deposit(self_uid=380841561)
    # 11.获取子用户余额汇总
    # d=test.get_sub_balance_summary()
    # 12.子用户余额查询
    # e=test.get_sub_balance(self_uid=380855234)

# 我的sub_uid=380855234
# [{'uid': 380841561, 'userState': 'locked'}, {'uid': 380849573, 'userState': 'normal'}, {'uid': 380855234, 'userState': 'normal'}]
