import datetime
import json
import time

from analyse import compare_price
from api_and_ding.ding import DingReporter
from match_order import *
from get_data_from_db import get_current_data_from_db


class PushAnomalies():
    def __init__(self, config, new_ts):
        self.percentile = config['percentile']
        self.interval = config['interval']
        self.last_order_id = config['last_neworder_id']
        self.last_ts = config['last_timestamp']  # 上次运行时的 timestamp
        self.new_ts = new_ts  # 本次运行/ 最新一条 order 的 quote_accept_time

    def get_ratio_threshold(self, matched_data):
        threshold_down = matched_data.groupby('quote_coin')['d_amount_ratio'].apply(  # base_coin
            lambda x: np.percentile(x, 100 - self.percentile))
        threshold_up = matched_data.groupby('quote_coin')['d_amount_ratio'].apply(
            lambda x: np.percentile(x, self.percentile))
        # 转化为 字典形式
        threshold_down = threshold_down.to_dict()
        threshold_up = threshold_up.to_dict()
        return threshold_down, threshold_up

    def turn_order_info_into_text(self, order_dict):
        text = 'id: {},\nside: {}，\n锁 价: {:.6f}，\n对冲价: {:.6f}，\nbase_amount: {:.6f},\nexec_base_amount:{:.6f}，' \
               '\n绝对收益: {:4f}，\n相对收益: {:.6f}%，\n对冲时间差: {}s'.format(
                order_dict['id'], order_dict['side'], order_dict['price'], order_dict['exec_price'],
                order_dict['base_amount'], order_dict['exec_base_amount'], order_dict['d_amount'],
                order_dict['d_amount_ratio'] * 100, order_dict['d_time'] // 1000)
        return text

    def report_new_order_to_ding(self, ding, new_matched_data, time_up, threshold_down, threshold_up):
        """

        Args:
            ding: DingReporter类的实例
            new_matched_data: 最近一段时间的 锁价订单和对冲订单的匹配数据
            time_up: 对冲时间上限（超过认为是异常）
            threshold_down: 对冲收益下限（超过认为是异常）
            threshold_up: 对冲收益上限（超过认为是异常）

        Returns:
            是否有异常情况
        """
        last_dt = datetime.datetime.fromtimestamp(self.last_ts // 1000)
        new_dt = datetime.datetime.fromtimestamp(self.new_ts // 1000)

        if len(new_matched_data) == 0:
            content = '【锁价与对冲订单匹配】{}~{}时间段内，共有 {} 条新交易，匹配上 {} 条'.format(
                last_dt, new_dt, self.len_new_order, len(new_matched_data))
            print(content)
            ding.send_text(content)
            return False

        for i in range(len(new_matched_data)):
            dt = datetime.datetime.fromtimestamp(new_matched_data.index[i] // 1000)
            new_matched = new_matched_data.iloc[i].to_dict()
            # 损益在 5%以下的，95%以上的，对冲锁价时间差在95% 以上的都额外推送钉钉
            if new_matched['d_amount_ratio'] > threshold_up[new_matched['quote_coin']]:
                text = self.turn_order_info_into_text(new_matched)
                content = '【锁价与对冲订单异常推送】{}，{}/{} 交易对冲收益很高（{}%分位数以上）：\n{}'.format(
                    dt, new_matched['quote_coin'], new_matched['base_coin'], self.percentile, text)
                print(content)
                ding.send_text(content)
            if new_matched['d_amount_ratio'] < threshold_down[new_matched['quote_coin']]:
                text = self.turn_order_info_into_text(new_matched)
                content = '【锁价与对冲订单异常推送】{}，{}/{} 交易对冲收益很低（{}%分位数以下）：\n{}'.format(
                    dt, new_matched['quote_coin'], new_matched['base_coin'], 100 - self.percentile, text)
                print(content)
                ding.send_text(content)
            if new_matched['d_time'] > time_up:
                text = self.turn_order_info_into_text(new_matched)
                content = '【锁价与对冲订单异常推送】{}，{}/{} 交易对冲用时过长（{}s）：\n{}'.format(
                    dt, new_matched['quote_coin'], new_matched['base_coin'], new_matched['d_time'] // 1000, text)
                print(content)
                ding.send_text(content)
        # 推送总体情况
        content = '【锁价与对冲订单异常推送】{}~{}时间段内，共有 {} 条交易，匹配上 {} 条：\n平均绝对收益 {:.6f}，平均相对收益 {:.6f}%，平均对冲时间差 {}s'.format(
            last_dt, new_dt, self.len_new_order, len(new_matched_data), new_matched_data['d_amount'].mean(),
            new_matched_data['d_amount_ratio'].mean() * 100, new_matched_data['d_time'].mean() // 1000)
        print(content)
        ding.send_text(content)
        return True

    def get_matched_data(self, neworders, pms_data):
        m = MatchOrder(neworders, pms_data, self.interval)
        matched_data = m.match()
        matched_data = compare_price(matched_data)
        matched_data = matched_data.dropna()
        matched_data['d_time'] = matched_data['exec_place_time'] - matched_data.index

        # all_matched = neworders.copy()
        # all_matched[['exec_place_time', 'match']] = matched_data[['exec_place_time', 'match']]
        # all_matched = pd.merge(all_matched, pms_data, left_on='exec_place_time', right_index=True, how='left')
        # # all_matched = all_matched.dropna()
        # all_matched['d_time'] = all_matched['exec_place_time'] - all_matched.index
        # all_matched.to_csv('all_match_client24.csv')
        # all_matched = compare_price(all_matched)
        return matched_data

    def get_threshold(self, matched_data):
        time_up = np.percentile(matched_data['d_time'], self.percentile)
        threshold_down, threshold_up = self.get_ratio_threshold(matched_data)
        return time_up, threshold_down, threshold_up

    def update_config(self, config):
        config['last_neworder_id'] = int(self.new_order_id)  # 11701861,
        return config

    def run(self, neworders, pms_data, ding):
        """

        Args:
            neworders: 截至当前运行时刻的所有数据
            pms_data: 截至当前运行时刻的所有数据
            ding: DingReporter类的实例

        Returns:
            是否有异常情况
        """
        self.new_order_id = neworders['id'].iloc[0]

        if self.new_order_id != self.last_order_id:
            matched_data = self.get_matched_data(neworders, pms_data)
            time_up, threshold_down, threshold_up = self.get_threshold(matched_data)

            self.len_new_order = len(neworders[neworders.index > self.last_ts])
            new_matched_data = matched_data[matched_data.index > self.last_ts]  # index 为 quote_accept_time
            # new_matched_data.to_csv('new_matched_client24.csv')
            # if len()
            push_anomalies = self.report_new_order_to_ding(ding, new_matched_data, time_up, threshold_down, threshold_up)
        else:
            print('No New Order!')
            push_anomalies = False
        return push_anomalies

# "last_neworder_id": 2,
# "last_timestamp": 1646882502777,

if __name__ == "__main__":
    with open('config.json', 'r', encoding='utf8') as fp:
        config = json.load(fp)
    ding = DingReporter(config['ding'])

    # 全部数据
    all_neworders = get_current_data_from_db(table='neworders')
    all_pms_data = get_current_data_from_db(table='pms_executions_spot')

    # 记录获取完数据的时间点
    new_ts = time.time() * 1000

    r = PushAnomalies(config, new_ts)
    r.run(neworders, pms_data, ding)
    # 更新 config 中的 'last_neworder_id' 和 'last_timestamp'
    config = r.update_config(config)
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)