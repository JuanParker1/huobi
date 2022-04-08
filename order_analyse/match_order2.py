import pandas as pd
import numpy as np
import datetime

from api_and_ding.ding import DingReporter
from match_order import MatchOrder
from get_data_from_db import get_current_data_from_db



def nSum(nums, n: int, target, tol=0.05):
    res = []
    if len(nums) < n:
        return res
    if n == 2:
        left, right = 0, len(nums) - 1
        while left < right:
            if target*(1+tol) > nums[left] + nums[right] > target*(1-tol):
                res.append([nums[left], nums[right]])
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif nums[left] + nums[right] < target*(1+tol):
                left += 1
            else:
                right -= 1
        return res
    else:
        for i in range(len(nums) - n + 1):
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            min_sum = sum(nums[i:i + n])
            if min_sum > target*(1+tol):
                break
            max_sum = nums[i] + sum(nums[-n + 1:])
            if max_sum < target*(1-tol):
                continue
            sub_res = nSum(nums[i + 1:], n - 1, target - nums[i], tol)
            for j in range(len(sub_res)):
                res.append([nums[i]] + sub_res[j])
        return res


class DiffDirectionMatch(MatchOrder):
    def __init__(self, neworders, pms_data, interval):
        """
        Args:
            neworders: dataframe 以 quote_accept_time 为index
            pms_data: dataframe 以 exec_place_time 为index
            interval: int       时间间隔 单位秒
        """
        pms_data['quote_coin'] = pms_data['symbol'].apply(lambda x: x.split("_")[0].upper())
        pms_data['base_coin'] = pms_data['symbol'].apply(lambda x: x.split("_")[1].upper())

        self.neworders = neworders
        self.pms_data = pms_data

        self.interval = interval
        self.tol = 0.05  # 5% 的容忍度

    def match_info(self, target, candidate):
        # 筛选出 side 正好相反，币种 、client_id 均匹配的数据
        candidate = candidate[(candidate['side'] != target['side']) &
                              (candidate['quote_coin'] == target['quote_coin']) &
                              (candidate['base_coin'] == target['base_coin']) &
                              (candidate['client_id'] == target['client_id'])]
        return candidate

    def match_amount_ratio_one2many(self, target, candidate, tol):
        # 筛选出 base_amount 的误差在 tol 以内的数据，若存在不止一条数据，则选误差最小的那一条
        candidate_list = candidate.exec_base_amount.to_list()
        candidate_list.sort()

        results = []
        for i in range(2, len(candidate_list)):
            res = nSum(candidate_list, i, target=target['base_amount'], tol=tol)
            if res:
                results += res   # 如果不为空，则加入 list

        print('target', target['base_amount'])
        print('results: ', results)
        # 输出结果
        if len(results) == 0:
            return []
        elif len(results) == 1:
            many = candidate.index[candidate.exec_base_amount.isin(results[0])]
            order_idx = many.to_list()
            return order_idx
        else:
            print('多条匹配上了，选择误差最小的一条')
            sum_res = [sum(r) for r in results]
            bias = abs(np.divide(sum_res, 494527.9232) - 1)
            idx = np.argmin(bias)
            many = candidate.index[candidate.exec_base_amount.isin(results[idx])]
            order_idx = many.to_list()
            print(many, order_idx)
            a==a
            return order_idx

    def turn_pms_info_into_text(self, order_data):
        print(order_data)
        try:
            dt = datetime.datetime.fromtimestamp(order_data.name // 1000)
        except AttributeError:
            dt = datetime.datetime.fromtimestamp(order_data.index[0] // 1000)
            order_data = order_data.to_dict('index')[order_data.index[0]]
            print(dt)
            print(dt, order_data['quote_coin'], order_data['base_coin'], order_data['side'], order_data['exec_base_amount'])
        text = '\n\t{}，{}/{} 的 {}交易, exec_base_amount:{:.6f} ' .format(
                dt, order_data['quote_coin'], order_data['base_coin'], order_data['side'], order_data['exec_base_amount'])
        return text

    def match_one2many(self):
        self.matched_data = pd.DataFrame(index=self.neworders.index, columns=
                        ['id', 'side', 'quote_coin', 'base_coin', 'client_id', 'base_amount', 'price',
                        'exec_place_time', 'exec_price', 'exec_base_amount', 'exec_algo', 'match'])
        self.matched_data[['id','side', 'quote_coin', 'base_coin', 'client_id', 'base_amount', 'price']] = \
            self.neworders[['id','side','quote_coin', 'base_coin', 'client_id', 'base_amount', 'price']]
        # 开始逐条匹配
        for i in range(len(self.neworders)):
            target = self.neworders[['side', 'quote_coin', 'base_coin', 'client_id', 'base_amount']].iloc[i, :]
            accept_time = self.neworders.index[i]
            # 对 neworder 中的每一条数据，筛选出其 accept_time 往后 interval 秒 时间内，pms的所有数据
            candidate = self.cut_pms(accept_time)
            if len(candidate) == 0:
                self.matched_data['match'].iloc[i] = 'NO'
                continue
            # 匹配  side、币种 (quote_coin) 、client_id 等数据
            candidate = self.match_info(target, candidate)
            if len(candidate) == 0:
                self.matched_data['match'].iloc[i] = 'NO'
                continue
            # 筛选出二者 base_amount 的误差在 5% 以内的数据，若存在不止一条数据，则选误差最小的那一条
            one2one = self.match_amount_ratio(target, candidate)
            if len(one2one) != 0:  # 可 一对一 匹配
                self.matched_data['match'].iloc[i] = 'one2one'
                self.update_matched_data(i, one2one)
                dt = datetime.datetime.fromtimestamp(target.name // 1000)
                content = "{}，{}/{} 的 {}交易，交易量为{}，在误差 5% 情况下和以下 1 条对冲交易相匹配：".format(dt, target['quote_coin'],
                                            target['base_coin'], target['side'], target['base_amount'])
                content += self.turn_pms_info_into_text(one2one)
                # ding.send_text(content)
                print(content)
                a==a
            elif len(candidate) == 1:
                self.matched_data['match'].iloc[i] = 'NO'
            else:  # 考虑多对一
                res = self.match_amount_ratio_one2many(target, candidate, tol=self.tol)
                print('\none2many result', res)
                if res:   # result 不为空
                    self.matched_data['match'].iloc[i] = 'one2many'
                    dt = datetime.datetime.fromtimestamp(target.name // 1000)
                    content = "{}，{}/{} 的 {}交易，交易量为{}，在误差 5% 情况下和以下 {} 条对冲交易相匹配：".format(dt, target['quote_coin'],
                                target['base_coin'], target['side'], target['base_amount'], len(res))
                    for j in res:
                        content += self.turn_pms_info_into_text(candidate.loc[j])
                    # ding.send_text(content)
                    print(content)
                else:
                    self.matched_data['match'].iloc[i] = 'NO'
        return self.matched_data


if __name__ == '__main__':
    ding = {
        "secret": "SEC8847c2eb4980651aceb5dca50daa713373c7276440395ee81be6f8d11c655902",
        "url": "https://oapi.dingtalk.com/robot/send?access_token=2de56dc81131b65b3160fd6f2c958d51da2181a6c8857795db8936b01ea01284"
    }

    ding = DingReporter(ding)

    neworders, pms_data = get_current_data_from_db()
    period = 5 * 60  # 5 min

    # neworders.to_csv('neworders.csv')
    # pms_data.to_csv('pms_data.csv')

    m = DiffDirectionMatch(neworders, pms_data, interval=period)
    matched_data = m.match_one2many()
    print(matched_data[matched_data['match']!='NO'])

    # all_matched = neworders.copy()
    # all_matched[['exec_place_time', 'match']] = one2one[['exec_place_time', 'match']]
    # all_matched = pd.merge(all_matched, pms_data, left_on='exec_place_time', right_index=True, how='left')

    contant = f"共 {len(neworders)} 条数据，匹配上 {len(matched_data[matched_data['match']!='NO'])} 条"
    print(contant)






    # if len(results) != 0:
    #     content = '账户内持仓了不允许持仓的币种: {}'.format(forbid_coin)
    #     ding.send_text(content)
    #     print(content)