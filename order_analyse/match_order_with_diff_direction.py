import pandas as pd
import numpy as np
import datetime
import json

from api_and_ding.ding import DingReporter
from match_order import MatchOrder
from get_data_from_db import get_current_data_from_db


# 寻找 n数之和 = target, 允许误差在 5% 左右
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
    def __init__(self, neworders, interval):
        """
        Args:
            neworders: dataframe 以 quote_accept_time 为index
            interval: int       时间间隔 单位秒
        """
        self.neworders = neworders

        self.interval = interval
        self.tol = 0.05  # 5% 的容忍度

    def match_info(self, target, candidate):
        # 筛选出 side 正好相反，币种 、client_id 均匹配的数据
        candidate = candidate[(candidate['side'] != target['side']) &
                              (candidate['quote_coin'] == target['quote_coin']) &
                              (candidate['client_id'] == target['client_id'])]
        return candidate

    def match_amount_ratio_one2one(self, target, candidate):
        # 筛选出 base_amount 的误差在 tol 以内的数据，若存在不止一条数据，则选误差最小的那一条
        match_ind = []
        tol_rate_list = []
        for i in range(len(candidate)):
            amount_ratio = candidate.base_amount.iloc[i] / target['base_amount']
            if abs(1 - amount_ratio) <= self.tol:
                match_ind.append(i)
                tol_rate_list.append(abs(1 - amount_ratio))

        # 输出结果
        if len(tol_rate_list) == 0:
            return []
        elif len(match_ind) == 1:
            return candidate.iloc[match_ind, :]
        else:
            l = np.argmin(tol_rate_list)
            return candidate.iloc[[match_ind[l]], :]

    def match_amount_ratio_one2many(self, target, candidate, tol):
        # 筛选出 base_amount 的误差在 tol 以内的数据，若存在不止一条数据，则选误差最小的那一条
        candidate_list = candidate.base_amount.to_list()
        candidate_list.sort()

        results = []
        for i in range(2, len(candidate_list)):
            res = nSum(candidate_list, i, target=target['base_amount'], tol=tol)
            if res:
                results += res   # 如果不为空，则加入 list

        # print('target', target['base_amount'])
        # print('results: ', results)
        # 输出结果
        if len(results) == 0:
            return []
        elif len(results) == 1:
            many = candidate.index[candidate.base_amount.isin(results[0])]
            order_idx = many.to_list()
            return order_idx
        else:
            print('多条匹配上了，选择误差最小的一条')
            sum_res = [sum(r) for r in results]
            bias = abs(np.divide(sum_res, 494527.9232) - 1)
            idx = np.argmin(bias)
            many = candidate.index[candidate.base_amount.isin(results[idx])]
            order_idx = many.to_list()
            # print(many, order_idx)
            return order_idx

    def turn_pms_info_into_text(self, order_data):
        try:
            dt = datetime.datetime.fromtimestamp(order_data.name // 1000)
        except AttributeError:
            dt = datetime.datetime.fromtimestamp(order_data.index[0] // 1000)
            order_data = order_data.to_dict('index')[order_data.index[0]]
        text = '\n{}，{}/{} 的 {}交易,id为{}, 交易量: {:.6f} ' .format(
            dt, order_data['quote_coin'], order_data['base_coin'], order_data['side'],order_data['id'], order_data['base_amount'])
        return text

    def match(self, target, candidate, ding):
        if len(candidate) == 0:
            return 'NO', None

        candidate = self.match_info(target, candidate)  # 匹配  side、币种 、client_id 等数据
        if len(candidate) == 0:
            return 'NO', None
        # 筛选 base_amount 的误差在 5% 以内的数据，若存在不止一条数据，则选误差最小的那一条
        one2one = self.match_amount_ratio_one2one(target, candidate)
        if len(one2one) != 0:  # 可 一对一 匹配
            dt = datetime.datetime.fromtimestamp(target.name // 1000)
            content = "【锁价订单同向匹配】{}，{}/{} 的 {}交易,id为{}，交易量为{}，在误差 5% 情况下和以下 1 条交易相匹配：".format(
                dt, target['quote_coin'],target['base_coin'], target['side'], target['id'], target['base_amount'])
            content += self.turn_pms_info_into_text(one2one)
            ding.send_text(content)
            # print(content)
            return 'one2one', one2one.index[0]
        elif len(candidate) == 1:
            return 'NO', None
        else:  # 考虑多对一
            res = self.match_amount_ratio_one2many(target, candidate, tol=self.tol)
            if res:  # result 不为空
                dt = datetime.datetime.fromtimestamp(target.name // 1000)
                content = "【锁价订单同向匹配】{}，{}/{} 的 {}交易,id为{}，交易量为{}，在误差 5% 情况下和以下 {} 条交易相匹配：".format(
                    dt, target['quote_coin'], target['base_coin'], target['side'], target['id'], target['base_amount'],len(res))
                for j in res:
                    content += self.turn_pms_info_into_text(candidate.loc[j])
                ding.send_text(content)
                # print(content)
                return 'one2many', res
            else:
                return 'NO', None

    def update_many2one(self):
        one2many_idx = self.matched_data[self.matched_data['match'] == 'one2many'].index
        if len(one2many_idx) > 0:
            for i in one2many_idx:
                match_idx = self.matched_data['matched_timestamp'].loc[i]
                for idx in match_idx:
                    self.matched_data['match'].iloc[idx] = 'many2one'
                    self.matched_data['matched_timestamp'].iloc[idx] = i
        return self.matched_data

    def run(self, ding):
        self.matched_data = self.neworders[
            ['id', 'side', 'quote_coin', 'base_coin', 'client_id', 'base_amount', 'price']]
        self.matched_data[['match', 'matched_timestamp']] = np.nan

        # 开始逐条匹配
        idx_list = list(self.neworders.index)
        need_push = False
        for ts in idx_list:
            if self.matched_data['match'].loc[ts] == 'one2one':
                print('已经匹配好了')
                continue
            target = self.neworders.loc[ts]
            # 对 neworder 中的每一条数据，筛选出其 ts 往后 interval 秒 时间内，pms的所有数据
            candidate = self.cut_data(self.neworders, ts)

            is_match, match_idx = self.match(target, candidate, ding)
            self.matched_data['match'].loc[ts] = is_match
            self.matched_data['match'].loc[match_idx] = is_match
            self.matched_data['matched_timestamp'].loc[ts] = match_idx
            self.matched_data['matched_timestamp'].loc[match_idx] = ts
            if is_match !='NO':
                need_push = True

        self.update_many2one()
        return self.matched_data, need_push


if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf8') as fp:
        config = json.load(fp)
    ding = DingReporter(config['ding'])

    neworders = get_current_data_from_db(table1='neworders')
    period = 5 * 60  # 5 min
    # neworders.to_csv('neworders.csv')

    m = DiffDirectionMatch(neworders, interval=period)
    matched_data = m.run()
    print(matched_data[matched_data['match']!='NO'])
    # matched_data[matched_data['match'] != 'NO'].to_csv('matched.csv')

    content = f"共 {len(neworders)} 条数据，匹配上 {len(matched_data[matched_data['match']!='NO'])} 条"
    print(content)
