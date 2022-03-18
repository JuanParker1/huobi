import datetime
import json

import psycopg2

from analyse import compare_price
from api_and_ding.ding import DingReporter
from match_order import *


def connect_db(tablename='neworders'):
    conn = psycopg2.connect(database='otcglobal', user='research',
                            password='hkresearch2019', host='10.157.21.20', port=5432)

    # sql语句
    sql = "select * from {} where client_id = 24 order by create_time desc ".format(tablename)
    df = pd.read_sql(sql=sql, con=conn)

    # 获得游标对象
    # cursor = conn.cursor()
    # cursor.execute(sql)
    # data = cursor.fetchmany(2)  # fetchmany(2)  # fetchone()  # fetchall()
    # print("database version : ", data)
    # conn.commit()  # 事物提交
    # conn.close()  # 关闭数据库连接
    return df


class ReportNewOrder():
    def __init__(self, config):
        self.percentile = config['percentile']
        self.interval = config['interval']
        self.last_order_id = config['last_neworder_id']
        self.last_ts = config['last_timestamp']  # 上次运行时的 timestamp
        self.new_ts = None  # 本次运行/ 最新一条 order 的 quote_accept_time

    @staticmethod
    def get_current_data_from_db():
        neworders = connect_db(tablename='neworders')
        pms_data = connect_db(tablename='pms_executions_spot')
        # 设 index，更改数据类型
        neworders = neworders.set_index('quote_accept_time')
        neworders[['price', 'quote_amount', 'base_amount']] = neworders[
            ['price', 'quote_amount', 'base_amount']].astype(
            float)
        pms_data = pms_data.set_index('exec_place_time')
        pms_data[['exec_price', 'exec_quote_amount', 'exec_base_amount']] = pms_data[['exec_price', 'exec_quote_amount',
                                                                                      'exec_base_amount']].astype(float)
        return neworders, pms_data

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

    def report_new_order_to_ding(self, new_matched_data, time_up, threshold_down, threshold_up):
        last_dt = datetime.datetime.fromtimestamp(self.last_ts // 1000)
        new_dt = datetime.datetime.fromtimestamp(self.new_ts // 1000)

        ding = DingReporter(config['ding'])
        if len(new_matched_data) == 0:
            print('new orders can not be matched!')
            content = '{}~{}时间段内，共有 {} 条新交易，匹配上 {} 条'.format(
                last_dt, new_dt, self.len_new_order, len(new_matched_data))
            print(content)
            ding.send_text(content)
            return None

        for i in range(len(new_matched_data)):
            dt = datetime.datetime.fromtimestamp(new_matched_data.index[i] // 1000)
            new_matched = new_matched_data.iloc[i].to_dict()
            # 损益在 5%以下的，95%以上的，对冲锁价时间差在95% 以上的都额外推送钉钉
            if new_matched['d_amount_ratio'] > threshold_up[new_matched['quote_coin']]:
                text = self.turn_order_info_into_text(new_matched)
                content = '{}，{}/{} 交易对冲收益很高（{}%分位数以上）：\n{}'.format(
                    dt, new_matched['quote_coin'], new_matched['base_coin'], config['percentile'], text)
                print(content)
                ding.send_text(content)
            if new_matched['d_amount_ratio'] < threshold_down[new_matched['quote_coin']]:
                text = self.turn_order_info_into_text(new_matched)
                content = '{}，{}/{} 交易对冲收益很低（{}%分位数以下）：\n{}'.format(
                    dt, new_matched['quote_coin'], new_matched['base_coin'], 100 - config['percentile'],text)
                print(content)
                ding.send_text(content)
            if new_matched['d_time'] > time_up:
                text = self.turn_order_info_into_text(new_matched)
                content = '{}，{}/{} 交易对冲用时过长（{}s）：\n{}'.format(
                    dt, new_matched['quote_coin'], new_matched['base_coin'], new_matched['d_time'] // 1000, text)
                print(content)
                ding.send_text(content)
        # 推送总体情况
        content = '{}~{}时间段内，共有 {} 条交易，匹配上 {} 条：\n平均绝对收益 {:.6f}，平均相对收益 {:.6f}%，平均对冲时间差 {}s'.format(
            last_dt, new_dt, self.len_new_order, len(new_matched_data), new_matched_data['d_amount'].mean(),
            new_matched_data['d_amount_ratio'].mean() * 100, new_matched_data['d_time'].mean() // 1000)
        print(content)
        ding.send_text(content)

    def get_matched_data(self, neworders, pms_data):
        m = MathchOrder(neworders, pms_data, self.interval)
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
        config['last_timestamp'] = int(self.new_ts)
        return config

    def run(self):
        neworders, pms_data = self.get_current_data_from_db()

        self.new_ts = neworders.index[0]
        self.new_order_id = neworders['id'].iloc[0]

        print(self.new_order_id, self.last_order_id)
        if self.new_order_id != self.last_order_id:
            matched_data = self.get_matched_data(neworders, pms_data)
            time_up, threshold_down, threshold_up = self.get_threshold(matched_data)

            self.len_new_order = len(neworders[neworders.index > self.last_ts])
            new_matched_data = matched_data[matched_data.index > self.last_ts]  # index 为 quote_accept_time
            # new_matched_data.to_csv('new_matched_client24.csv')
            self.report_new_order_to_ding(new_matched_data, time_up, threshold_down, threshold_up)
        else:
            print('No New Order!')


# config = {'interval': 600,
#           'percentile': 95,  #
#           'ding': {
#               'secret': 'SEC8847c2eb4980651aceb5dca50daa713373c7276440395ee81be6f8d11c655902',
#               'url': 'https://oapi.dingtalk.com/robot/send?access_token=2de56dc81131b65b3160fd6f2c958d51da2181a6c8857795db8936b01ea01284'
#           },
#           'last_neworder_id': 2,  # 11701861,
#           'last_timestamp': 1646882502777,
#           #'last_pms_id': 11079,  # 没用上
# }
#
# with open('config.json', 'w', encoding='utf-8') as f:
#     json.dump(config, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    with open('config.json', 'r', encoding='utf8') as fp:
        config = json.load(fp)
    r = ReportNewOrder(config)
    r.run()
    # 更新 config 中的 'last_neworder_id' 和 'last_timestamp'
    config = r.update_config(config)
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)