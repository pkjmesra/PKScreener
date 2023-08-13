"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import pandas as pd

from pkscreener.classes.ColorText import colorText


def backtest(
    stock, data, screenedDict=None, periods=30, sampleDays=365, backTestedData=None
):
    if stock == "" or data is None:
        print(f"No data/stock{(stock)} received for backtesting!")
        return
    if screenedDict is None or len(screenedDict) == 0:
        print(f"{(stock)}No backtesting strategy or screened dictionary received!")
        return
    calcPeriods = [1, 2, 3, 4, 5, 10, 15, 22, 30]
    allStockBacktestData = []
    # Take the data based on which the result set for a strategy may have been arrived at
    # The results must have been arrived at with data based on 400-sampleDays
    # but we also need the periods days to be able to calculate the next few days' returns
    # s1    d0
    # s1    d1
    # s1    d2  <----------------On this day the recommendation was made
    # s1    d3  ^
    #   ....    |
    # s1    dn  |----------------We need to make calculations upto 30 day period from d2
    futureRows = periods
    if sampleDays <= periods:
        f1 = 0
        t1 = sampleDays
    else:
        f1 = periods
        t1 = periods
    daysback_df = data.head(400 - sampleDays + f1)  # print(daysback_df)
    daysback_df = daysback_df.tail(
        t1 + 1
    )  # +1 to include the actual date on which the recommendation was made
    daysback_df = data.head(400 - sampleDays + futureRows)  # print(daysback_df)
    daysback_df = daysback_df.tail(
        futureRows + 1
    )  # +1 to include the actual date on which the recommendation was made
    previous_recent = daysback_df.head(
        1
    )  # This is the row which has the date for which the recommendation is valid
    previous_recent.reset_index(inplace=True)
    if len(previous_recent) <= 0:
        return backTestedData
    # Let's check the returns for the given strategy over a period ranging from 1 period to 30 periods.
    if backTestedData is None:
        backTestedData = pd.DataFrame(
            columns=[
                "Stock",
                "Base-Date",
                "Volume",
                "Trend",
                "MA-Signal",
                "1-Pd",
                "2-Pd",
                "3-Pd",
                "4-Pd",
                "5-Pd",
                "10-Pd",
                "15-Pd",
                "22-Pd",
                "30-Pd",
            ]
        )
    backTestedStock = {
        "Stock": "",
        "Base-Date": "",
        "Volume": "",
        "Trend": "",
        "MA-Signal": "",
        "1-Pd": "",
        "2-Pd": "",
        "3-Pd": "",
        "4-Pd": "",
        "5-Pd": "",
        "10-Pd": "",
        "15-Pd": "",
        "22-Pd": "",
        "30-Pd": "",
    }
    backTestedStock["Stock"] = stock
    backTestedStock["Base-Date"] = str(previous_recent.iloc[:, 0][0]).split(" ")[
        0
    ]  # Date or index column
    backTestedStock["Volume"] = screenedDict["Volume"]
    backTestedStock["Trend"] = screenedDict["Trend"]
    backTestedStock["MA-Signal"] = screenedDict["MA-Signal"]
    for prd in calcPeriods:
        if abs(prd) <= periods:
            try:
                rolling_pct = daysback_df["Close"].pct_change(periods=prd) * 100
                pct_change = rolling_pct.iloc[prd]
                backTestedStock[f"{abs(prd)}-Pd"] = (
                    (colorText.GREEN if pct_change >= 0 else colorText.FAIL)
                    + "%.2f%%" % pct_change
                    + colorText.END
                )
            except:
                continue
        else:
            del backTestedStock[f"{abs(prd)}-Pd"]
            try:
                backTestedData = backTestedData.drop(f"{abs(prd)}-Pd", axis=1)
            except:
                continue
    allStockBacktestData.append(backTestedStock)
    df = pd.DataFrame(allStockBacktestData, columns=backTestedData.columns)
    try:
        backTestedData = pd.concat([backTestedData, df])
    except:
        pass
    return backTestedData
