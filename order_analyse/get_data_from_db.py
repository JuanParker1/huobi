import pandas as pd
import psycopg2


def connect_db(tablename, sql=None):
    conn = psycopg2.connect(database='otcglobal', user='research',
                            password='hkresearch2019', host='10.157.21.20', port=5432)

    # sql语句
    if not sql:
        sql = "select * from {} where client_id = 24 order by create_time desc ".format(tablename)
    df = pd.read_sql(sql=sql, con=conn)
    return df

def get_current_data_from_db(table='neworders'):
    ts = {'neworders': 'quote_accept_time', 'pms_executions_spot': 'exec_place_time'}
    col = {'neworders': ['price', 'quote_amount', 'base_amount'],
           'pms_executions_spot': ['exec_price', 'exec_quote_amount', 'exec_base_amount']}
    data = connect_db(tablename=table)
    # 设 index，更改数据类型
    data = data.set_index(ts[table])
    data[col[table]] = data[col[table]].astype(float)
    return data

def get_recent_data(table, start_ts):
    """

    Args:
        table: 表格名称
        start_ts: 13位的timestamp，截取从这一时刻到当前运行时刻的数据

    Returns: 从 start_ts时刻到当前运行时刻的数据
    """
    # 'neworders' 和 'pms_executions_spot' 对应的列名不一样
    col = {'neworders': ['price', 'quote_amount', 'base_amount'],
           'pms_executions_spot': ['exec_price', 'exec_quote_amount', 'exec_base_amount']}
    ts = {'neworders': 'quote_accept_time', 'pms_executions_spot': 'exec_place_time'}

    # 截取 从 start_ts 到当前运行时刻的数据
    sql = "select * from {} where client_id = 24 and {} > {} order by create_time desc ".format(
            table, ts[table], start_ts)
    data = connect_db(table, sql)
    # 设 index，更改数据类型
    data = data.set_index(ts[table])
    data[col[table]] = data[col[table]].astype(float)
    return data

if __name__ == '__main__':
    # neworders = get_current_data_from_db(table='neworders')
    # pms_data = get_current_data_from_db(table='pms_executions_spot')
    get_recent_data('neworders', 1646882502777)