import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def paint_result(data, startdt, enddt, path='C:/pythonProj/mandatory_liquidation'):
    data['hold_value'] = data['value'] - data['cash']
    data.index = pd.to_datetime(data.index)
    # data['short_tier1'] = data.apply(lambda x:1 if x['tier1_short']=True and x.shift(1)['tier1_short']=False else -1 )

    plt.figure(figsize=(10, 8))
    gs = gridspec.GridSpec(7, 1)  # 通过gridspec.GridSpec()创建区域

    ax1 = plt.subplot(gs[:3, 0])
    ax1.plot(data.index, data.risk_rate, label='risk rate')
    ax1.legend(loc=1)
    ax1.grid(color='gray')
    ax1.set_title(f'Risk Rate from {startdt} to {enddt}')

    ax2 = plt.subplot(gs[-3:, 0])
    ax2.plot(data.index, data.value, label='total value')
    ax2.stackplot(data.index, data.cash, data.hold_value, baseline='zero', labels=['cash', 'holding value'], colors=['r', 'c'])
    ax2.legend(loc=1)
    ax2.grid(color='gray')
    ax2.set_title(f'Total Value from {startdt} to {enddt}')

    plt.savefig(os.path.join(path, f'result_{startdt}_to_{enddt}.png'))
    print('picture saved +1')


def paint():
    path = 'C:/pythonProj/data/mandatory_liquidation/results'  # 'C:/pythonProj/mandatory_liquidation'    #

    for root, dirs, files in os.walk(path):
        for filename in files:
            if '.csv' in filename:
                daterange = filename.split('_', 1)[1].split('.', 1)[0]
                startdt, enddt = daterange.split('_', 2)[0], daterange.split('_', 2)[2]
                data = pd.read_csv(os.path.join(path, filename), index_col=0)  # index 为时间日期
                print(startdt, enddt)
                data = data[['risk_rate', 'cash', 'value']]
                # print(data)
                paint_result(data, startdt, enddt)


if __name__ == '__main__':
    paint()
