import pandas as pd

def backtest(data, strategy, periods=30):
    if data is None:
        print('No data received for backtesting!')
        return
    if strategy is None or strategy == '':
        print('No backtesting strategy name received!')
        return
    calcPeriods = [1,2,3,4,5,10,15,22,30]
    allStockBacktestData = []
    # Let's check the returns for the given strategy over a period ranging from 1 period to 30 periods.
    backTestedData = pd.DataFrame(columns=['Stock','1-Pd','2-Pd','3-Pd','4-Pd','5-Pd','10-Pd','15-Pd','22-Pd','30-Pd'])
    backTestedStock = {'Stock':'','1-Pd':'','2-Pd':'','3-Pd':'','4-Pd':'','5-Pd':'','10-Pd':'','15-Pd':'','22-Pd':'','30-Pd':''}
    backTestedStock['Stock'] = data.head(1)['Stock']
    for pd in calcPeriods:
        if pd <= periods:
            pct_change = (data[::-1]['Close'].pct_change(periods=-pd) * 100).iloc[-1]
            backTestedStock[f'{pd}-Pd'] = "%.1f%%" % pct_change
        else:
            break
    allStockBacktestData.append(backTestedStock)
    df = pd.DataFrame(allStockBacktestData, columns=backTestedData.columns)
    backTestedData = pd.concat([backTestedData, df])
    print(backTestedData)
    return backTestedData