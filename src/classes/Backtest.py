import pandas as pd

def backtest(stock, data, strategy, periods=30, backTestedData = None):
    if stock == '' or data is None:
        print(f'No data/stock{(stock)} received for backtesting!')
        return
    if strategy is None or strategy == '':
        print(f'{(stock)}No backtesting strategy name received!')
        return
    calcPeriods = [-1,-2,-3,-4,-5,-10,-15,-22,-30]
    allStockBacktestData = []
    # Let's check the returns for the given strategy over a period ranging from 1 period to 30 periods.
    if backTestedData is None:
        backTestedData = pd.DataFrame(columns=['Stock','1-Pd','2-Pd','3-Pd','4-Pd','5-Pd','10-Pd','15-Pd','22-Pd','30-Pd'])
    backTestedStock = {'Stock':'','1-Pd':'','2-Pd':'','3-Pd':'','4-Pd':'','5-Pd':'','10-Pd':'','15-Pd':'','22-Pd':'','30-Pd':''}
    backTestedStock['Stock'] = stock
    for prd in calcPeriods:
        if abs(prd) <= periods:
            rolling_pct = (data['Close'].pct_change(periods=prd) * 100)
            pct_change = rolling_pct.iloc[0]
            backTestedStock[f'{abs(prd)}-Pd'] = "%.2f%%" % pct_change
        else:
            break
    allStockBacktestData.append(backTestedStock)
    df = pd.DataFrame(allStockBacktestData, columns=backTestedData.columns)
    backTestedData = pd.concat([backTestedData, df])
    # print(backTestedData)
    # input()
    return backTestedData