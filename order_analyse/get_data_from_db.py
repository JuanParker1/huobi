import pandas as pd
import psycopg2


def connect_db(tablename):
    conn = psycopg2.connect(database='otcglobal', user='research',
                            password='hkresearch2019', host='10.157.21.20', port=5432)

    # sql语句
    sql = "select * from {} where client_id in (18, 24) order by create_time desc ".format(tablename)
    df = pd.read_sql(sql=sql, con=conn)
    return df

def get_current_data_from_db(table1='neworders', table2='pms_executions_spot'):
    neworders = connect_db(tablename=table1)
    pms_data = connect_db(tablename=table2)
    # 设 index，更改数据类型
    neworders = neworders.set_index('quote_accept_time')
    neworders[['price', 'quote_amount', 'base_amount']] = neworders[
        ['price', 'quote_amount', 'base_amount']].astype(float)
    pms_data = pms_data.set_index('exec_place_time')
    pms_data[['exec_price', 'exec_quote_amount', 'exec_base_amount']] = pms_data[['exec_price', 'exec_quote_amount',
                                                                                  'exec_base_amount']].astype(float)
    return neworders, pms_data

if __name__ == '__main__':
    a,b = get_current_data_from_db()
    print(a, b)
