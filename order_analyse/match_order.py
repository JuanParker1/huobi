import pandas as pd
import numpy as np
from get_data_from_db import *

class MatchOrder():
    def __init__(self, neworders, pms_data, interval=30):
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
        self.tol = 0.01  # 1% 的容忍度

    def cut_data(self, data, starttime):
        # 筛选出其 starttime 往后 interval 秒 这段时间范围内，pms 的所有数据
        period_data = data[(data.index > starttime) & (data.index < starttime + self.interval * 1000)]
        return period_data

    def match_info(self, target, candidate):
        # 筛选出 side、币种 、client_id 均匹配的数据
        candidate = candidate[(candidate['side'] == target['side']) & #(candidate['symbol'] == (target['quote_coin']).lower() + '_' + ( target['base_coin']).lower()) &
                              (candidate['quote_coin'] == target['quote_coin']) &  # 放松 qoute coin
                              (candidate['client_id'] == target['client_id'])]
        # print('side:', target['side'], 'symbol:', (target['quote_coin']).lower() + '_' + (target['base_coin']).lower(),
        #       'client_id:', target['client_id'])
        # print(candidate)
        return candidate

    def match_amount_ratio(self, target, candidate):
        # 筛选出 base_amount 的误差在 tol 以内的数据，若存在不止一条数据，则选误差最小的那一条
        match_ind = []
        tol_rate_list = []
        for i in range(len(candidate)):
            amount_ratio = candidate.exec_base_amount.iloc[i] / target['base_amount']
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

    def update_matched_data(self, idx, candidate):
        self.matched_data['exec_place_time'].iloc[idx] = candidate.index.values[0]  # candidate['exec_place_time']
        self.matched_data['exec_price'].iloc[idx] = candidate['exec_price'].values[0]
        self.matched_data['exec_base_amount'].iloc[idx] = candidate['exec_base_amount'].values[0]
        self.matched_data['exec_algo'].iloc[idx] = candidate['exec_algo'].values[0]

    def match(self):
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
            candidate = self.cut_data(self.pms_data, accept_time)
            if len(candidate) == 0:
                self.matched_data['match'].iloc[i] = 'NO'
                continue
            # 匹配  side、币种 (quote_coin) 、client_id 等数据
            candidate = self.match_info(target, candidate)
            if len(candidate) == 0:
                self.matched_data['match'].iloc[i] = 'NO'
                continue
            # 筛选出二者 base_amount 的误差在 1% 以内的数据，若存在不止一条数据，则选误差最小的那一条
            candidate = self.match_amount_ratio(target, candidate)
            if len(candidate) == 0:
                self.matched_data['match'].iloc[i] = 'NO'
                continue

            # 看 base_coin 是否对得上
            if candidate['base_coin'].values[0] == target['base_coin']:
                self.matched_data['match'].iloc[i] = 'YES'
            else:
                self.matched_data['match'].iloc[i] = 'ALMOST'
            self.update_matched_data(i, candidate)
            # print(self.matched_data.iloc[i])
        return self.matched_data





if __name__ == "__main__":
    neworders = get_current_data_from_db(table='neworders')
    pms_data = get_current_data_from_db(table='pms_executions_spot')

    interval = 600
    m = MatchOrder(neworders, pms_data, interval)
    matched_data = m.match()

    print(matched_data)
    all_matched = neworders.copy()
    all_matched[['exec_place_time', 'match']] = matched_data[['exec_place_time', 'match']]
    all_matched = pd.merge(all_matched, pms_data, left_on='exec_place_time', right_index=True, how='left')

    # all_matched.to_csv(r'C:\pythonProj\data\match_order\matched_data_all_{}s.csv'.format(interval))
    # matched_data.to_csv(r'C:\pythonProj\data\match_order\matched_data_{}s.csv'.format(interval))
    print(f"在 {interval}s 时间间隔下，共 {len(neworders)} 条数据，匹配上 {len(matched_data['exec_place_time'].dropna())} 条"\
          f"（其中 base coin 也匹配的有 {len(matched_data[matched_data['match']=='YES'])} 条）")

