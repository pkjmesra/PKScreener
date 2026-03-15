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
import warnings

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
from pkscreener.classes import Utility, ConsoleUtility
from pkscreener.classes.ConfigManager import parser, tools

configManager = tools()
configManager.getConfig(parser)

# Backtests for a given stock with the data for the past x number of days.
# Before this gets called, the assumption is that the user must already
# have run some scanner from the available options. SampleDays is the
# sampling period for which we need to run the backtests. Generally, a
# 30 day period or a 180-day period should be more than enough.
def backtest(
    stock,
    data,
    saveDict=None,
    screenedDict=None,
    periods=30,
    sampleDays=configManager.backtestPeriod,
    backTestedData=None,
    sellSignal=False,
):
    if stock == "" or data is None:
        default_logger().debug(f"No data/stock {(stock)} received for backtesting!")
        return
    if screenedDict is None or len(screenedDict) == 0:
        default_logger().debug(f"{(stock)}No backtesting strategy or screened dictionary received!")
        return
    calcPeriods = configManager.periodsRange
    allStockBacktestData = []
    # Take the data based on which the result set for a strategy may have been arrived at
    # The results must have been arrived at with data based on configManager.backtestPeriod -sampleDays
    # but we also need the periods days to be able to calculate the next few days' returns
    # s1    d0
    # s1    d1
    # s1    d2  <----------------On this day the recommendation was made
    # s1    d3  ^
    #   ....    |
    # s1    dn  |----------------We need to make calculations upto 30 day period from d2
    previous_recent = data.head(
        1
    )  # This is the row which has the date for which the recommendation is valid
    if len(previous_recent) <= 0:
        return backTestedData
    data = data.head(max(calcPeriods) + 1)
    # Let's check the returns for the given strategy over a period ranging from 1 period to 30 periods.
    # columns=['Stock', 'Date', "volume", 'Trend', 'MA-Signal', 'LTP', '52Wk-H',
    #          '52Wk-L', '1-Pd', '2-Pd', '3-Pd', '4-Pd', '5-Pd', '10-Pd', '15-Pd',
    #          '22-Pd', '30-Pd', 'Consol.', 'Breakout', 'RSI', 'Pattern', 'CCI',
    #          'LTP1', 'Growth1', 'LTP2', 'Growth2', 'LTP3', 'Growth3', 'LTP4',
    #          'Growth4', 'LTP5', 'Growth5', 'LTP10', 'Growth10', 'LTP15', 'Growth15',
    #          'LTP22', 'Growth22', 'LTP30', 'Growth30']
    
    # incoming = list(saveDict.keys())
    # for prd in calcPeriods:
    #     colNames = [f"LTP{prd}",f"Growth{prd}",f"{prd}-Pd"]
    #     if colNames[0] not in incoming:
    #         for col in colNames:
    #             columns.remove(col)
    # if backTestedData is None:
    #     backTestedData = pd.DataFrame(columns=columns)
    # df = pd.DataFrame([screenedDict],columns=columns)
    # df[f"LTP{prd}"] = saveDict[f"LTP{prd}"]
    # df[f"Growth{prd}"] = saveDict[f"Growth{prd}"]
    columns=[
                "Stock",
                "Date",
                "volume",
                "Trend",
                "MA-Signal",
                "LTP",
                "52Wk-H",
                "52Wk-L"
            ]
    backTestedStock = {
        "Stock": "",
        "Date": "",
        "volume": "",
        "Trend": "",
        "MA-Signal": "",
        "LTP": "",
        "52Wk-H": "",
        "52Wk-L": ""
    }
    for prd in calcPeriods:
        columns.append(f"{prd}-Pd")
        backTestedStock[f"{prd}-Pd"] = ""
    if backTestedData is None:
        backTestedData = pd.DataFrame(columns=columns)
    backTestedStock["Stock"] = stock
    backTestedStock["Date"] = saveDict["Date"]
    backTestedStock["Consol."] = screenedDict["Consol."]
    backTestedStock["Breakout"] = screenedDict["Breakout"]
    backTestedStock["MA-Signal"] = screenedDict["MA-Signal"]
    backTestedStock["volume"] = screenedDict["volume"]
    backTestedStock["LTP"] = screenedDict["LTP"]
    backTestedStock["52Wk-H"] = screenedDict["52Wk-H"]
    backTestedStock["52Wk-L"] = screenedDict["52Wk-L"]
    backTestedStock["RSI"] = screenedDict["RSI"]
    backTestedStock["Trend"] = screenedDict["Trend"]
    backTestedStock["Pattern"] = screenedDict["Pattern"]
    backTestedStock["CCI"] = screenedDict["CCI"]
    for prd in calcPeriods:
        try:
            backTestedStock[f"{abs(prd)}-Pd"] = ""
            backTestedStock[f"LTP{prd}"] = ""
            backTestedStock[f"Growth{prd}"] = ""
            rolling_pct = data["close"].pct_change(periods=prd) * 100
            pct_change = rolling_pct.iloc[prd]
            if not sellSignal:
                colored_pct = colorText.GREEN if pct_change >= 0 else colorText.FAIL
            else:
                colored_pct = colorText.FAIL if pct_change >= 0 else colorText.GREEN
            backTestedStock[f"{abs(prd)}-Pd"] = (
                colored_pct + "%.2f%%" % pct_change + colorText.END
            )
        except Exception:# pragma: no cover
            pass
        # Let's capture the portfolio data, if available
        try:
            backTestedStock[f"LTP{prd}"] = saveDict[f"LTP{prd}"]
            backTestedStock[f"Growth{prd}"] = saveDict[f"Growth{prd}"]
        except Exception:# pragma: no cover
            pass
        # else:
        #     del backTestedStock[f"{abs(prd)}-Pd"]
        #     try:
        #         backTestedData = backTestedData.drop(f"{abs(prd)}-Pd", axis=1)
        #     except Exception:
        #         continue
    allStockBacktestData.append(backTestedStock)
    df = pd.DataFrame(allStockBacktestData)  # , columns=backTestedData.columns)
    try:
        backTestedData = pd.concat([backTestedData, df])
    except Exception:# pragma: no cover
        pass
    return backTestedData

# Prepares a backtest summary based on the color codes of individual days or stocks
# Based on that it calculates an overall success rate of a given strategy for which
# this backtest is run.
def backtestSummary(df):
    summary = {}
    overall = {}
    summaryList = []
    net_positives = 0
    net_negatives = 0
    if df is None:
        return
    df.drop_duplicates(inplace=True)
    df_grouped = df.groupby("Stock")
    for col in df.keys():
        if str(col).endswith("-Pd"):
            overall[col] = [0, 0]
    # iterate over each group of stock rows
    for stock_name, df_group in df_grouped:
        # for row_index, row in df_group.iterrows():
        group_positives = 0
        group_negatives = 0
        summary["Stock"] = stock_name
        for col in df_group.keys():
            if str(col).endswith("-Pd"):
                col_positives = (
                    df_group[col]
                    .astype(str)
                    .str.count(colorText.GREEN.replace("[", "\["))
                    .sum()
                )
                col_negatives = (
                    df_group[col]
                    .astype(str)
                    .str.count(colorText.FAIL.replace("[", "\["))
                    .sum()
                )
                group_positives += col_positives
                group_negatives += col_negatives
                overall[col] = [
                    overall[col][0] + col_positives,
                    overall[col][1] + col_negatives,
                ]
                overAllPeriodPrediction = (
                    col_positives * 100 / (col_positives + col_negatives)
                )
                if col_positives + col_negatives == 0:
                    summary[col] = "-"
                else:
                    summary[
                        col
                    ] = f"{ConsoleUtility.PKConsoleTools.formattedBacktestOutput(overAllPeriodPrediction)} of ({col_positives+col_negatives})"
        overAllRowPrediction = (
            group_positives * 100 / (group_positives + group_negatives)
        )
        if group_positives + group_negatives == 0:
            summary["Overall"] = "-"
        else:
            summary[
                "Overall"
            ] = f"{ConsoleUtility.PKConsoleTools.formattedBacktestOutput(overAllRowPrediction)} of ({group_positives+group_negatives})"
        summaryList.append(summary)
        summary = {}
        net_positives += group_positives
        net_negatives += group_negatives

    # Now prepare overall summary
    summary["Stock"] = "SUMMARY"
    for col in overall.keys():
        col_positives = overall[col][0]
        col_negatives = overall[col][1]
        if col_positives + col_negatives == 0:
            summary[col] = "-"
        else:
            summary[
                col
            ] = f"{ConsoleUtility.PKConsoleTools.formattedBacktestOutput((col_positives*100/(col_positives+col_negatives)))} of ({col_positives+col_negatives})"
    if net_positives + net_negatives == 0:
        summary["Overall"] = "-"
    else:
        summary[
            "Overall"
        ] = f"{ConsoleUtility.PKConsoleTools.formattedBacktestOutput(net_positives*100/(net_positives+net_negatives))} of ({net_positives+net_negatives})"
    summaryList.append(summary)
    summary_df = pd.DataFrame(summaryList, columns=summary.keys())
    return summary_df
