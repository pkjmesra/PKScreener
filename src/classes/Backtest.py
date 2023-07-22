import pandas as pd

def backtest(stock, data, strategy, periods=30,sampleDays=365, backTestedData = None):
    if stock == '' or data is None:
        print(f'No data/stock{(stock)} received for backtesting!')
        return
    if strategy is None or strategy == '':
        print(f'{(stock)}No backtesting strategy name received!')
        return
    calcPeriods = [1,2,3,4,5,10,15,22,30]
    allStockBacktestData = []
    daysback_df = data.head(400-sampleDays+periods)
    # print(daysback_df)
    daysback_df = daysback_df.tail(periods+1) 
    # print(daysback_df)
    previous_recent = daysback_df.head(1)
    previous_recent.reset_index(inplace=True)
    # print(previous_recent)
    if len(previous_recent) <= 0:
        return backTestedData
    # Let's check the returns for the given strategy over a period ranging from 1 period to 30 periods.
    if backTestedData is None:
        backTestedData = pd.DataFrame(columns=['Stock','Base-Date','1-Pd','2-Pd','3-Pd','4-Pd','5-Pd','10-Pd','15-Pd','22-Pd','30-Pd'])
    backTestedStock = {'Stock':'','Base-Date':'','1-Pd':'','2-Pd':'','3-Pd':'','4-Pd':'','5-Pd':'','10-Pd':'','15-Pd':'','22-Pd':'','30-Pd':''}
    backTestedStock['Stock'] = stock
    backTestedStock['Base-Date'] = previous_recent.iloc[:,0][0] # Date or index column
    for prd in calcPeriods:
        if abs(prd) <= periods:
            rolling_pct = (daysback_df['Close'].pct_change(periods=prd) * 100)
            # print(rolling_pct)
            pct_change = rolling_pct.iloc[prd]
            backTestedStock[f'{abs(prd)}-Pd'] = "%.2f%%" % pct_change
        else:
            del backTestedStock[f'{abs(prd)}-Pd']
            try:
                backTestedData = backTestedData.drop(f'{abs(prd)}-Pd', axis=1)
            except:
                pass
    allStockBacktestData.append(backTestedStock)
    df = pd.DataFrame(allStockBacktestData, columns=backTestedData.columns)
    backTestedData = pd.concat([backTestedData, df])
    # print(backTestedData)
    # input()
    return backTestedData