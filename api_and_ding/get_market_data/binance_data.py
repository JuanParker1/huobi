import requests
import pandas as pd
import time
from datetime import datetime


def Binance_kline(target='BTCUSDT', contract_type=None, interval='1m',
                  start_time=None, end_time=None,
                  get_full_market_data=False, adjust_time=True,
                  col_with_asset_name=True, is_fr=False, get_adj=False):
    if is_fr:
        result_data = pd.DataFrame(columns=['datetime', 'bnfr{}_close'.format(target)])
        get_full_market_data = False
    else:
        if contract_type:
            if get_full_market_data:
                result_data = pd.DataFrame(columns=['datetime', 'bn{}{}_open'.format(target, contract_type[:3]),
                                                    'bn{}{}_high'.format(target, contract_type[:3]),
                                                    'bn{}{}_low'.format(target, contract_type[:3]),
                                                    'bn{}{}_close'.format(target, contract_type[:3]),
                                                    'bn{}{}_volume'.format(target, contract_type[:3])])
            else:
                result_data = pd.DataFrame(columns=['datetime', 'bn{}{}_close'.format(target, contract_type[:3])])
        else:
            result_data = pd.DataFrame(columns=['datetime', 'bn{}_close'.format(target)])

    time_interval = 60
    if interval == '1m':
        time_interval = 60
    elif interval == '5m':
        time_interval = 300
    elif interval == '15m':
        time_interval = 900
    elif interval == '30m':
        time_interval = 1800
    elif interval == '1h':
        time_interval = 3600
    elif interval == '4h':
        time_interval = 14400
    elif interval == '1d':
        time_interval = 86400

    # set specific end timestamp
    if not end_time:
        end_timestamp = int(datetime.timestamp(datetime.now()))
        end_timestamp -= end_timestamp % time_interval
    else:
        end_timestamp = end_time

    if not start_time:
        start_timestamp = end_timestamp - 999 * time_interval
    else:
        start_timestamp = start_time

    iteration = (end_timestamp - start_timestamp)//(time_interval*1000) + 1

    for i in range(iteration):
        interval_time = end_timestamp - 999 * time_interval
        if interval_time < start_timestamp:
            interval_time = start_timestamp
        if start_timestamp > end_timestamp:
            break

        if is_fr:
            if target[-1] == 'T':
                contract_url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol={}&startTime={}&endTime={}&limit=1000".format(
                    target, interval_time*1000, end_timestamp*1000)
            else:
                contract_url = "https://dapi.binance.com/dapi/v1/fundingRate?symbol={}&startTime={}&endTime={}&limit=1000".format(
                    target+'_PERP', interval_time * 1000, end_timestamp * 1000)
        else:
            if not contract_type:
                contract_url = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&startTime={}&endTime={}&limit=1000".format(target, interval, interval_time*1000, end_timestamp*1000)
            else:
                if target[-1] == 'T':
                    contract_url = "https://fapi.binance.com/fapi/v1/continuousKlines?pair={}&contractType={}&interval={}&startTime={}&endTime={}&limit=1000".format(target, contract_type, interval, interval_time*1000, end_timestamp*1000)
                else:
                    contract_url = "https://dapi.binance.com/dapi/v1/continuousKlines?pair={}&contractType={}&interval={}&startTime={}&endTime={}&limit=1000".format(target, contract_type, interval, interval_time*1000, end_timestamp*1000)
        retry_time = 0
        while True:
            try:
                contract_response = requests.get(contract_url)
                break
            except Exception as e:
                print(e)
                print(target+' fail to get data. Retry...')
                time.sleep(0.3)
                retry_time += 1
                if retry_time >= 10:
                    raise Exception('Please try later')
        contract_result = contract_response.json()
        if not contract_result:
            pass
        else:
            if get_full_market_data:
                try:
                    contract_data = pd.DataFrame(contract_result).iloc[:, [0, 1, 2, 3, 4, 5, 7]]
                except Exception as e:
                    print('Can not get desired data.')
                    print(contract_result)
                    print(e)
                else:
                    if contract_type:
                        open_name = 'bn{}{}_open'.format(target, contract_type[:3])
                        high_name = 'bn{}{}_high'.format(target, contract_type[:3])
                        low_name = 'bn{}{}_low'.format(target, contract_type[:3])
                        close_name = 'bn{}{}_close'.format(target, contract_type[:3])
                        volume_name = 'bn{}{}_volume'.format(target, contract_type[:3])
                        amount_name = 'bn{}{}_amount'.format(target, contract_type[:3])
                    else:
                        open_name = 'bn{}_open'.format(target)
                        high_name = 'bn{}_high'.format(target)
                        low_name = 'bn{}_low'.format(target)
                        close_name = 'bn{}_close'.format(target)
                        volume_name = 'bn{}_volume'.format(target)
                        amount_name = 'bn{}_amount'.format(target)
                    contract_data.iloc[:, 0] = contract_data.iloc[:, 0].apply(lambda x: x//1000)
                    contract_data.columns = ['datetime', open_name, high_name, low_name, close_name, volume_name, amount_name]
                    for j in [open_name, high_name, low_name, close_name, volume_name, amount_name]:
                        contract_data[j] = contract_data[j].astype('float')
                    result_data = result_data.append(contract_data)
            else:
                if is_fr:
                    try:
                        contract_data = pd.DataFrame(contract_result).iloc[:, [1, 2]]
                    except Exception as e:
                        print('Can not get desired data.')
                        print(contract_result)
                        print(e)
                    else:
                        close_name = 'bnfr{}_close'.format(target)
                        contract_data = contract_data[['fundingTime', 'fundingRate']]
                        contract_data.iloc[:, 0] = contract_data.iloc[:, 0].apply(lambda x: x//1000)
                        contract_data.rename(columns={'fundingTime': 'datetime', 'fundingRate': close_name}, inplace=True)
                        contract_data[close_name] = contract_data[close_name].astype('float')
                        result_data = result_data.append(contract_data)
                else:
                    try:
                        contract_data = pd.DataFrame(contract_result).iloc[:, [0, 4]]
                    except Exception as e:
                        print('Can not get desired data.')
                        print(contract_result)
                        print(e)
                    else:
                        if contract_type:
                            close_name = 'bn{}{}_close'.format(target, contract_type[:3])
                        else:
                            close_name = 'bn{}_close'.format(target)
                        contract_data.iloc[:, 0] = contract_data.iloc[:, 0].apply(lambda x: x//1000)
                        contract_data.columns = ['datetime', close_name]
                        contract_data[close_name] = contract_data[close_name].astype('float')
                        result_data = result_data.append(contract_data)
        end_timestamp = interval_time - time_interval
        time.sleep(0.3)

    result_data.sort_values('datetime', inplace=True)
    if adjust_time:
        result_data['datetime'] += 28800
        result_data['datetime'] = pd.to_datetime(result_data['datetime'], unit='s')

    result_data.set_index(['datetime'], inplace=True)
    
    if col_with_asset_name:
        return result_data
    else:
        rename_dict = {}
        for i in result_data.columns:
            rename_dict[i] = i.split("_")[-1]
        result_data.rename(columns=rename_dict, inplace=True)
        if get_adj:
            result_data['adj_close'] = result_data['close']
        return result_data


if __name__ == "__main__":
    start_time = int(time.time()) - 71 * 86400
    period = '5m'
    target = 'btcusd'.upper()

    result_data = Binance_kline(target=target, interval=period, contract_type='PERPETUAL', start_time=start_time,
                                get_full_market_data=True, col_with_asset_name=False, is_fr=True)
    # bn_spot_5min_data.to_csv('~/PycharmProjects/ljw_basis_strategy/Data/Binance_data/bn_btc_spot_1hour_data.csv')
    # bn_cq_5min_data = Binance_kline(target=target, interval=period, contract_type='CURRENT_QUARTER', start_time=start_time,
    #                                 get_full_market_data=True, col_with_asset_name=False)
    # bn_cq_5min_data.to_csv('~/PycharmProjects/ljw_basis_strategy/Data/Binance_data/bn_btc_cq_1hour_data.csv')
    # bn_nq_5min_data = Binance_kline(target=target, interval=period, contract_type='NEXT_QUARTER', start_time=start_time,
    #                                 get_full_market_data=True, col_with_asset_name=False)
    # bn_nq_5min_data.to_csv('~/PycharmProjects/ljw_basis_strategy/Data/Binance_data/bn_btc_nq_1hour_data.csv')

    result_data = pd.DataFrame(result_data)
    print(result_data)
    print(result_data.shape)
    # print("daily avg amount for woo in binance is {}".format(result_data['amount'].mean()))
    # print("daily avg volume for woo in binance is {}".format(result_data['volume'].mean()))
    # print(result_data)
    # result_data.to_csv('../data/woo_binance_spot.csv')
    # bn_fr_test = Binance_kline(target=target, interval=period, start_time=start_time)
    # print(bn_fr_test)


