import time
import datetime
from api_and_ding.ding import DingReporter

from push_anomalies import *
from match_order_with_diff_direction import *
from get_data_from_db import *


with open('config.json', 'r', encoding='utf8') as fp:
    config = json.load(fp)
ding = DingReporter(config['ding'])
config['last_timestamp'] = (time.time() - config['sleep']) * 1000  # 当前运行时刻往前挪 sleep 秒

while True:
    # 近期数据
    start_ts = config['last_timestamp']
    neworders = get_recent_data(table='neworders', start_ts=start_ts)
    pms_data = get_recent_data(table='pms_executions_spot', start_ts=start_ts)
    if len(neworders) == 0:
        ding.send_text('{} - {} 时间段内无新订单'.format(datetime.datetime.fromtimestamp(start_ts//1000),
                                                 datetime.datetime.fromtimestamp(time.time())))
        config['sleep'] = 30 * 60  # 改为半小时运行一次
        time.sleep(config['sleep'])
        continue
    # 全部数据
    all_neworders = get_current_data_from_db(table='neworders')
    all_pms_data = get_current_data_from_db(table='pms_executions_spot')
    # 记录获取完数据的时间点
    new_ts = time.time() * 1000

    r = PushAnomalies(config, new_ts)
    push_anomalies = r.run(all_neworders, all_pms_data, ding) # 返回是否有异常情况

    m = DiffDirectionMatch(neworders, interval=config['interval'])
    matched_data, need_push = m.run(ding)  # 返回匹配上的数据 & 是否有匹配上的数据（即是否推送）
    print(matched_data[matched_data['match'] != 'NO'])
    # print(f"共 {len(neworders)} 条数据，匹配上 {len(matched_data[matched_data['match'] != 'NO'])} 条")

    # 更新 config 中的 'last_neworder_id', 'last_timestamp'
    config['last_timestamp'] = new_ts
    config = r.update_config(config)
    if not push_anomalies and not need_push:
        ding.send_text('{} - {} 时间段内无新订单'.format(datetime.datetime.fromtimestamp(start_ts//1000),
                                                 datetime.datetime.fromtimestamp(config['last_timestamp'])))
        config['sleep'] = 30 * 60  # 改为半小时运行一次
    else:
        config['sleep'] = 5 * 60  # 改为5 min 运行一次
    print('本次循环结束')
    time.sleep(config['sleep'])


with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=4)