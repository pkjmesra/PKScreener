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
import os
import sys
import numpy as np
import pandas as pd
from argparse import Namespace
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from pkscreener.classes import Utility
from PKDevTools.classes.log import default_logger
from pkscreener.classes.ConfigManager import parser, tools
from pkscreener.classes.Portfolio import Portfolio, PortfolioCollection
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes.PKScheduler import PKScheduler
from PKDevTools.classes.OutputControls import OutputControls

configManager = tools()
configManager.getConfig(parser)

def summariseAllStrategies(testing=False):
    reports = getSavedBacktestReportNames(testing=testing)
    df_all = None
    counter = 0
    for report in reports:
        counter += 1
        OutputControls().printOutput(f"Processing {counter} of {len(reports)}...")
        df = bestStrategiesFromSummaryForReport(
            f"PKScreener_{report}_Insights_DateSorted.html", summary=True,includeLargestDatasets=True
        )
        if df is not None:
            df.insert(loc=0, column="Scanner", value=report)
            if df_all is not None:
                df_all = pd.concat([df_all, df], axis=0)
            else:
                df_all = df
        # sys.stdout.write("\x1b[1A")
        OutputControls().moveCursorUpLines(1)
    if df_all is not None:
        df_all = df_all.replace(np.nan, "-", regex=True)
    return df_all

def getSavedBacktestReportNames(testing=False):
    indices = [1,5,8,11,12,14] if not testing else [1]
    scanSkipIndices = [21, 22] if not testing else [1,2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]
    indexWithSubindices = [6, 7] if not testing else [6]
    subIndices = {6: [1, 2, 3, 4, 5, 6, 7], 7: [1, 2, 3, 4, 5, 6, 7]} if not testing else {6: [7]}
    indexWithSubLevelindices = {6:[7],7:[6]}
    subLevelIndices = {7: [1, 2, 3], 6: [1, 2, 3]} if not testing else {7: [1]}
    reports = []
    for index in indices:
        scanTypeStartIndex = 1
        scanTypeEndIndex = 25
        reportName = f"B_{index}_"
        while scanTypeStartIndex <= scanTypeEndIndex:
            if scanTypeStartIndex not in scanSkipIndices:
                reportName = f"{reportName}{scanTypeStartIndex}"
                if scanTypeStartIndex in indexWithSubindices:
                    for subIndex in subIndices[scanTypeStartIndex]:
                        subReportName = f"{reportName}_{subIndex}"
                        if subIndex in indexWithSubLevelindices[scanTypeStartIndex]:
                            for subLevelIndex in subLevelIndices[subIndex]:
                                subLevelReportName = f"{subReportName}_{subLevelIndex}"
                                reports.append(subLevelReportName)
                        else:
                            reports.append(subReportName)
                else:
                    reports.append(reportName)
            reportName = f"B_{index}_"
            scanTypeStartIndex += 1
    return reports


def bestStrategiesFromSummaryForReport(reportName: None, summary=False,includeLargestDatasets=False):
    dfs = []
    insights = None
    if "PKDevTools_Default_Log_Level" not in os.environ.keys():
        if (("RUNNER" not in os.environ.keys())):
            return None
    if not configManager.showPastStrategyData:
        return None
    try:
        dfs = pd.read_html(
            "https://pkjmesra.github.io/PKScreener/Backtest-Reports/{0}".format(
                reportName.replace("_X_", "_B_").replace("_G_", "_B_").replace("_S_", "_B_")
            ),encoding="UTF-8", attrs = {'id': 'resultsTable'}
        )
    except Exception as e: # pragma: no cover
        pass
    if dfs is not None and len(dfs) > 0:
        df = dfs[0]
        if len(df) > 0:
            periods = configManager.periodsRange
            insights = cleanupInsightsSummary(df, periods)
            # insights = insights.replace('', np.nan, regex=True)
            # insights = insights.replace('-', np.nan, regex=True)
            dfs = []
            max_best_df = insights.copy()
            max_datasets_df = insights.copy()
            if includeLargestDatasets:
                addLargeDatasetInsights(dfs, max_datasets_df)
            
            insights_list = []
            dfs.append(max_best_df)
            getMaxBestInsight(summary, dfs, periods, insights_list)
            insights = pd.DataFrame(insights_list).drop_duplicates(ignore_index=True)
            insights.dropna(axis=0, how="all", inplace=True)
            insights = insights.replace(np.nan, "-", regex=True)
    return insights

def cleanupInsightsSummary(df, periods):
    df = df.replace(" %", "", regex=True)
    df = df.replace("-", np.nan, regex=True)
    for period in periods:
        df.rename(
                    columns={
                        f"{period}D-%": f"{period}Pd-%",
                        f"{period}D-10k": f"{period}Pd-10k",
                    },
                    inplace=True,
                )
        castToFloat(df, period)
    insights = df[df["ScanType"].astype(str).str.startswith("[SUM]")]
    return insights

def getMaxBestInsight(summary, dfs, periods, insights_list):
    for dfInsights in dfs:
        df = dfInsights.copy()
        df.reset_index(drop = True, inplace=True)
        strategy_percent = {}
        strategy = {}
        firstPeriod = True
        rowIndex = 0
        for prd in periods:
            rowIndex += 1
            try:
                max_p = df[f"{prd}Pd-%"].max()
                maxIndexPos = df[f"{prd}Pd-%"].idxmax()
                bestScanFilter = str(
                            df["ScanType"].iloc[maxIndexPos]).replace("[SUM]", "")
                resultPoints = bestScanFilter.split("(")[-1]
                strategy_percent[f"{prd}-Pd"] = f"{colorText.GREEN if max_p > 0 else (colorText.FAIL if max_p < 0 else colorText.WARN)}{max_p} %{colorText.END}{(' from ('+resultPoints) if (summary or firstPeriod) else ''}"
                scanType = (bestScanFilter.split("(")[0] if not summary else bestScanFilter)
                strategy[f"{prd}-Pd"] = scanType
            except KeyError:
                    max_p = df[rowIndex*2]
                    bestScanFilter = str(df[0]).replace("[SUM]", "")
                    resultPoints = bestScanFilter.split("(")[-1]
                    strategy_percent[f"{prd}-Pd"] = f"{colorText.GREEN if max_p > 0 else (colorText.FAIL if max_p < 0 else colorText.WARN)}{max_p} %{colorText.END}{(' from ('+resultPoints) if (summary or firstPeriod) else ''}"
                    scanType = (bestScanFilter.split("(")[0] if not summary else bestScanFilter)
                    strategy[f"{prd}-Pd"] = scanType
            except Exception:# pragma: no cover
                # default_logger().debug(e, exc_info=True)
                try:
                    max_p = df[f"{prd}Pd-%"]
                    bestScanFilter = str(df["ScanType"]).replace("[SUM]", "")
                    resultPoints = bestScanFilter.split("(")[-1]
                    strategy_percent[f"{prd}-Pd"] = f"{colorText.GREEN if max_p > 0 else (colorText.FAIL if max_p < 0 else colorText.WARN)}{max_p} %{colorText.END}{(' from ('+resultPoints) if (summary or firstPeriod) else ''}"
                    scanType = (bestScanFilter.split("(")[0] if not summary else bestScanFilter)
                    strategy[f"{prd}-Pd"] = scanType
                except Exception as e:# pragma: no cover
                    default_logger().debug(e, exc_info=True)
                    pass
                pass
            if summary:
                strategy[f"{prd}-Pd"] = strategy_percent[f"{prd}-Pd"].split("from")[0] + " " + strategy[f"{prd}-Pd"]
            firstPeriod = False
        insights_list.extend([strategy] if summary else [strategy, strategy_percent])

def addLargeDatasetInsights(dfs, max_datasets_df):
    max_datasets_df[["ScanTypeSplit", "DatasetSize"]] = max_datasets_df[
                    "ScanType"
                ].str.split("(", n=1, expand=True)
    max_datasets_df["DatasetSize"] = max_datasets_df["DatasetSize"].str.replace(")", "")
    try:
        max_datasets_df["DatasetSize"] = (max_datasets_df["DatasetSize"].astype(float).fillna(0.0))
    except Exception as e:# pragma: no cover
        default_logger().debug(e, exc_info=True)
        max_datasets_df.loc[:, "DatasetSize"] = max_datasets_df.loc[:, "DatasetSize"].apply(
                        lambda x: x.split("(")[-1]
                    )
        max_datasets_df["DatasetSize"] = (max_datasets_df["DatasetSize"].astype(float).fillna(0.0))
        pass
    max_size = max_datasets_df["DatasetSize"].max()
    max_datasets_df = max_datasets_df[(max_datasets_df["DatasetSize"] == max_size)].fillna(0.0)
    for i in range(0, len(max_datasets_df)):
        dfs.append(max_datasets_df.iloc[i])

def castToFloat(df, prd):
    if f"{prd}Pd-%" in df.columns:
        df[f"{prd}Pd-%"] = (df[f"{prd}Pd-%"].astype(float).fillna(0.0))


def xRaySummary(savedResults=None):
    if savedResults is None or not isinstance(savedResults, pd.DataFrame) or savedResults.empty:
        return savedResults
    saveResults = savedResults.copy()
    df_grouped = saveResults.groupby("ScanType")
    periods = configManager.periodsRange
    sum_list = []
    sum_dict = {}
    maxGrowth = -100
    for scanType, df_group in df_grouped:
        groupItems = len(df_group)
        sum_dict = {}
        sum_dict["ScanType"] = f"[SUM]{scanType.replace('(','[').replace(')',']')}  ({groupItems})"
        sum_dict["Date"] = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
        for prd in periods:
            if not f"{prd}Pd-%" in df_group.columns:
                continue
            prd_df = df_group[[f"{prd}Pd-%", f"{prd}Pd-10k"]]
            prd_df.loc[:, f"{prd}Pd-10k"] = prd_df.loc[:, f"{prd}Pd-10k"].apply(
                lambda x: Utility.tools.removeAllColorStyles(x)
            )
            prd_df = prd_df.replace("-", np.nan, regex=True)
            prd_df = prd_df.replace("", np.nan, regex=True)
            prd_df.dropna(axis=0, how="all", inplace=True)
            prd_df[f"{prd}Pd-10k"] = prd_df[f"{prd}Pd-10k"].astype(float).fillna(0.0)
            gain = round(
                (prd_df[f"{prd}Pd-10k"].sum() - 10000 * len(prd_df))
                * 100
                / (10000 * len(prd_df)),
                2,
            )
            sum_dict[f"{prd}Pd-%"] = gain
            sum_dict[f"{prd}Pd-10k"] = round(
                prd_df[f"{prd}Pd-10k"].sum() / len(prd_df), 2
            )
        sum_list.append(sum_dict)
    df = pd.DataFrame(sum_list)
    df = formatGridOutput(df, replacenan=False)
    saveResults = pd.concat([saveResults, df], axis=0)
    saveResults = saveResults.replace(np.nan, "-", regex=True)
    return saveResults


def performXRay(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        savedResults, userArgs, calcForDate, progressLabel = task.long_running_fn_args
    else:
        savedResults, userArgs, calcForDate, progressLabel = args[0],args[1],args[2],args[3]
    df = None
    if savedResults is not None and len(savedResults) > 0:
        backtestPeriods = getbacktestPeriod(userArgs)
        saveResults = cleanupData(savedResults)

        days = 0
        periods = configManager.periodsRange
        # period = periods[days]
        # requiredPeriods = []
        # If the calcForDate is more than the backtestPeriods, we should be able to 
        # still calculate the backtested returns for all 30 periods or periods more than
        # the requested backtestPeriods
        # backtestPeriods = getUpdatedBacktestPeriod(calcForDate, backtestPeriods, saveResults)
        # while periods[days] <= backtestPeriods:
        #     period = periods[days]
        #     requiredPeriods.append(period)
        #     days += 1
        #     if days >= len(periods):
        #         break
        df = getBacktestDataFromCleanedData(userArgs, saveResults, df, periods,progressLabel)
        if df is None:
            return None
        df = cleanFormattingForStatsData(calcForDate, saveResults, df)
        # OutputControls().printOutput(f"All portfolios:\n{PortfolioCollection().portfoliosAsDataframe}")
        # OutputControls().printOutput(f"All portfoliosSummary:\n{PortfolioCollection().ledgerSummaryAsDataframe}")
    if task is not None:
        if task.taskId > 0:
            task.progressStatusDict[task.taskId] = {'progress': 0, 'total': 1}
            task.resultsDict[task.taskId] = df
        else:
            task.result = df
    return df

def getUpdatedBacktestPeriod(calcForDate, backtestPeriods, saveResults):
    targetDate = (
            calcForDate if calcForDate is not None else saveResults["Date"].iloc[0]
        )
    today = PKDateUtilities.currentDateTime()
    gap = PKDateUtilities.trading_days_between(
            PKDateUtilities.dateFromYmdString(targetDate)
            .replace(tzinfo=today.tzinfo)
            .date(),
            today.date(),
        )
    backtestPeriods = gap if gap > backtestPeriods else backtestPeriods
    return backtestPeriods if backtestPeriods <= configManager.maxBacktestWindow else configManager.maxBacktestWindow

def cleanFormattingForStatsData(calcForDate, saveResults, df):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty \
        or saveResults is None or not isinstance(saveResults, pd.DataFrame) or saveResults.empty:
        return df
    df = df[
            [
                col
                for col in df.columns
                if ("ScanType" in col or "Pd-%" in col or "Pd-10k" in col)
            ]
        ]
    df = df.replace(999999999, np.nan, regex=True)
    df.dropna(axis=0, how="all", inplace=True)
    df = formatGridOutput(df)
    df.insert(
            1,
            "Date",
            calcForDate if calcForDate is not None else saveResults["Date"].iloc[0],
        )
    
    return df

def getBacktestDataFromCleanedData(args, saveResults, df, periods,progressLabel:str=None):
    '''
    Important
    ---------
    You should have called `cleanupData` before calling this.
    '''
    for period in periods:
        saveResults[f"LTP{period}"] = (
                    saveResults[f"LTP{period}"].astype(float).fillna(0.0)
                )
        saveResults[f"Growth{period}"] = (
                    saveResults[f"Growth{period}"].astype(float).fillna(0.0)
                )

    scanResults = statScanCalculations(args, saveResults, periods,progressLabel)

    if df is None:
        df = pd.DataFrame(scanResults)
    else:
        df1 = pd.DataFrame(scanResults)
        df_target = df1[
                    [col for col in df1.columns if ("Pd-%" in col or "Pd-10k" in col)]
                ]
        df = pd.concat([df, df_target], axis=1)
    return df

def statScanCalculationForNoFilter(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(saveResults, period, "NoFilter", userArgs,task)
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationForPatterns(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    df_grouped = saveResults.groupby("Pattern")
    for pattern, df_group in df_grouped:
        if pattern is None or len(pattern) == 0:
            pattern = "No Pattern"
        scanResults.append(
                    getCalculatedValues(df_group, period, f"[P]{pattern}", userArgs,task)
                )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def ensureColumnsExist(saveResults):
    columns = ['Stock', 'Date', 'Volume', 'Trend', 'MA-Signal', 'LTP', '52Wk-H',
               '52Wk-L', '1-Pd', '2-Pd', '3-Pd', '4-Pd', '5-Pd', '10-Pd', '15-Pd',
               '22-Pd', '30-Pd', 'Consol.', 'Breakout', 'RSI', 'Pattern', 'CCI',
               'LTP1', 'Growth1', 'LTP2', 'Growth2', 'LTP3', 'Growth3', 'LTP4',
               'Growth4', 'LTP5', 'Growth5', 'LTP10', 'Growth10', 'LTP15', 'Growth15',
               'LTP22', 'Growth22', 'LTP30', 'Growth30']
    if saveResults is None:
        saveResults = pd.DataFrame(columns=columns)
    else:
        for col in columns:
            if col not in saveResults.columns:
                saveResults[col] = ""
    return saveResults

def cleanupData(savedResults):
    saveResults = savedResults.copy()
    saveResults = ensureColumnsExist(saveResults)
    for col in saveResults.columns:
        saveResults.loc[:, col] = saveResults.loc[:, col].apply(
                lambda x: Utility.tools.removeAllColorStyles(x)
            )

    saveResults["LTP"] = saveResults["LTP"].astype(float).fillna(0.0)
    saveResults["RSI"] = saveResults["RSI"].astype(float).fillna(0.0)
    saveResults.loc[:, "Volume"] = saveResults.loc[:, "Volume"].apply(
            lambda x: x.replace("x", "")
        )
    if f"Trend({configManager.daysToLookback}Prds)" not in saveResults.columns:
        saveResults.rename(
                columns={
                    # "Consol.": f"Consol.({configManager.daysToLookback}Prds)",
                    "Trend": f"Trend({configManager.daysToLookback}Prds)",
                    "Breakout": f"Breakout({configManager.daysToLookback}Prds)",
                },
                inplace=True,
            )
    saveResults.loc[:, f"Consol."] = saveResults.loc[
            :, f"Consol."
        ].apply(lambda x: x.replace("Range:", "").replace("%", ""))
    try:
        saveResults = saveResults.loc[:,(saveResults!='').any(axis=0)]
    except ValueError:
        # The truth value of a Series is ambiguous.
        pass
    if f"Breakout({configManager.daysToLookback}Prds)" in savedResults.columns:
        saveResults[["Breakout", "Resistance"]] = saveResults[
                f"Breakout({configManager.daysToLookback}Prds)"
            ].astype(str).str.split(" R: ", n=1, expand=True)
        saveResults.loc[:, "Breakout"] = saveResults.loc[:, "Breakout"].apply(
                lambda x: x.replace("BO: ", "").replace(" ", "")
            )
        saveResults.loc[:, "Resistance"] = saveResults.loc[
                :, "Resistance"
            ].apply(lambda x: x.replace("(Potential)", "") if x is not None else x)
        saveResults["Breakout"] = saveResults["Breakout"].astype(float).fillna(0.0)
        saveResults["Resistance"] = saveResults["Resistance"].astype(float).fillna(0.0)
    saveResults["Volume"] = saveResults["Volume"].astype(float).fillna(0.0)
    saveResults[f"Consol."] = (
            saveResults[f"Consol."].astype(float).fillna(0.0)
        )
    saveResults["52Wk-H"] = saveResults["52Wk-H"].astype(float).fillna(0.0)
    saveResults["52Wk-L"] = saveResults["52Wk-L"].astype(float).fillna(0.0)
    saveResults["CCI"] = saveResults["CCI"].astype(float).fillna(0.0)
    return saveResults

def getbacktestPeriod(args):
    backtestPeriods = configManager.maxBacktestWindow  # Max backtest days
    if args is None or ((not isinstance(args,int)) and (not isinstance(args,Namespace))):
        return backtestPeriods
    if args is not None and args.backtestdaysago is not None:
        try:
            backtestPeriods = int(args.backtestdaysago)
        except Exception as e:# pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
    return backtestPeriods

def statScanCalculations(userArgs, saveResults, periods,progressLabel:str=None):
    scanResults = []
    tasksList = []
    if saveResults is not None and len(saveResults) >= 1:
        task1 = PKTask(f"[{len(saveResults)}] RSI Stats",long_running_fn=statScanCalculationForRSI)
        task2 = PKTask(f"[{len(saveResults)}] Trend Stats",long_running_fn=statScanCalculationForTrend)
        task3 = PKTask(f"[{len(saveResults)}] MA Stats",long_running_fn=statScanCalculationForMA)
        task4 = PKTask(f"[{len(saveResults)}] Volume Stats",long_running_fn=statScanCalculationForVol)
        task5 = PKTask(f"[{len(saveResults)}] Consolidation Stats",long_running_fn=statScanCalculationForConsol)
        task6 = PKTask(f"[{len(saveResults)}] Breakout Stats",long_running_fn=statScanCalculationForBO)
        task7 = PKTask(f"[{len(saveResults)}] 52Week Stats",long_running_fn=statScanCalculationFor52Wk)
        task8 = PKTask(f"[{len(saveResults)}] CCI Stats",long_running_fn=statScanCalculationForCCI)
        task9 = PKTask(f"[{len(saveResults)}] CCI Stats",long_running_fn=statScanCalculationForPatterns)
        task10 = PKTask(f"[{len(saveResults)}] NoFilter Stats",long_running_fn=statScanCalculationForNoFilter)
        tasksList=[task1,task2,task3,task4,task5,task6,task7,task8,task9,task10]
        for task in tasksList:
            task.long_running_fn_args = (userArgs, saveResults, periods, scanResults)
        if configManager.enablePortfolioCalculations:
            PKScheduler.scheduleTasks(tasksList,label=progressLabel,showProgressBars=True,timeout=600)
        else:
            for task in tasksList:
                task.long_running_fn(*(task,))
        for task in tasksList:
            if task.result is not None and len(task.result) > 0:
                scanResults.extend(task.result)
    return scanResults

def statScanCalculationForCCI(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterCCIBelowMinus100(saveResults), period, "[CCI]<=-100", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterCCIBelow0(saveResults), period, "[CCI]-100<C<0", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterCCI0To100(saveResults), period, "[CCI]0<=C<=100", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterCCI100To200(saveResults), period, "[CCI]100<C<=200", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterCCIAbove200(saveResults), period, "[CCI]>200", userArgs,task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationFor52Wk(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterLTPMoreOREqual52WkH(saveResults), period, "[52Wk]LTP>=H", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPWithin90Percent52WkH(saveResults),
                    period,
                    "[52Wk]LTP>=.9*H",
                    userArgs,
                    task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPLess90Percent52WkH(saveResults),
                    period,
                    "[52Wk]LTP<.9*H",
                    userArgs,
                    task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPMore52WkL(saveResults), period, "[52Wk]LTP>L", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPWithin90Percent52WkL(saveResults),
                    period,
                    "[52Wk]LTP>=1.1*L",
                    userArgs,
                    task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPLess52WkL(saveResults), period, "[52Wk]LTP<=L", userArgs,task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationForBO(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterLTPLessThanBreakout(saveResults), period, "[BO]LTP<BO", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPMoreOREqualBreakout(saveResults),
                    period,
                    "[BO]LTP>=BO",
                    userArgs,
                    task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPLessThanResistance(saveResults), period, "[BO]LTP<R", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterLTPMoreOREqualResistance(saveResults),
                    period,
                    "[BO]LTP>=R",
                    userArgs,
                    task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationForConsol(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterConsolidating10Percent(saveResults), period, "Cons.<=10", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterConsolidatingMore10Percent(saveResults),
                    period,
                    "Cons.>10",
                    userArgs,
                    task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationForVol(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterVolumeLessThan25(saveResults), period, "Vol<2.5", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterVolumeMoreThan25(saveResults), period, "Vol>=2.5", userArgs,task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationForMA(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterMASignalBullish(saveResults), period, "[MA]Bull", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterMASignalBearish(saveResults), period, "[MA]Bear", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterMASignalNeutral(saveResults), period, "[MA]Neutral", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterMASignalBullCross(saveResults), period, "[MA]BullCross", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterMASignalBearCross(saveResults), period, "[MA]BearCross", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterMASignalSupport(saveResults), period, "[MA]Support", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterMASignalResist(saveResults), period, "[MA]Resist", userArgs,task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationForTrend(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterTrendStrongUp(saveResults), period, "[T]StrongUp", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterTrendWeakUp(saveResults), period, "[T]WeakUp", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterTrendUp(saveResults), period, "[T]TrendUp", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterTrendStrongDown(saveResults), period, "[T]StrongDown", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterTrendWeakDown(saveResults), period, "[T]WeakDown", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterTrendSideways(saveResults), period, "[T]Sideways", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterTrendDown(saveResults), period, "[T]TrendDown", userArgs,task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults

def statScanCalculationForRSI(*args, **kwargs):
    task = None
    if isinstance(args[0], PKTask):
        task = args[0]
        userArgs, saveResults, period, scanResults = task.long_running_fn_args
    else:
        userArgs, saveResults, period, scanResults = args[0],args[1],args[2],args[3]
    scanResults.append(
                getCalculatedValues(
                    filterRSIAbove50(saveResults), period, "[RSI]>=50", userArgs, task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterRSI50To67(saveResults), period, "[RSI]50<=RSI<=67", userArgs,task
                )
            )
    scanResults.append(
                getCalculatedValues(
                    filterRSI68OrAbove(saveResults), period, "[RSI]>=68", userArgs,task
                )
            )
    if task is not None:
        if task.taskId > 0:
            task.resultsDict[task.taskId] = scanResults
            task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
        else:
            task.result = scanResults
    return scanResults


def formatGridOutput(df,replacenan=True):
    if replacenan:
        df = df.replace(np.nan, "-", regex=True)
    for col in df.columns:
        try:
            df[col] = df[col].astype(float).fillna(0)
        except ValueError as e: # pragma: no cover
            if len(str(e).split("-")) < 2:
                # We want to allow value "-" in column values
                # We don't want to allow '2024-12-03' or 'RSI >=50' or "Trends-50-to-60"
                pass
            else:
                continue
        except Exception as e:# pragma: no cover
            default_logger().debug(f"For column:{col}:\n{e}", exc_info=True)
            continue
        maxGrowth = df[col].max()
        if "Pd-%" in col:
            df.loc[:, col] = df.loc[:, col].astype(str).apply(
                lambda x: x
                if (str(x) == "-")
                else (
                    str(x).replace(
                        str(x),
                        (
                            (
                                (colorText.WHITE)
                                if x == maxGrowth
                                else colorText.GREEN
                            )
                            if float(x) > 0
                            else (colorText.FAIL if float(x) < 0 else colorText.WARN)
                        )
                        + str(float(x))
                        + " %"
                        + colorText.END,
                    )
                )
            )
        if "Pd-10k" in col:
            df.loc[:, col] = df.loc[:, col].astype(str).apply(
                lambda x: x
                if (str(x) == "-")
                else (
                    str(x).replace(
                        str(x),
                        (
                            (
                                (colorText.WHITE)
                                if x == maxGrowth
                                else colorText.GREEN
                            )
                            if (float(x) > 10000)
                            else (
                                colorText.FAIL if float(x) < 10000 else colorText.WARN
                            )
                        )
                        + str(x)
                        + colorText.END,
                    )
                )
            )
    df = df.replace(np.nan, "-", regex=True)
    df = df.replace(colorText.FAIL + "-100.0 %" + colorText.END, "-", regex=False)
    df = df.replace(colorText.WARN + "0.0 %" + colorText.END, "-", regex=False)
    df = df.replace(colorText.FAIL + "0.0" + colorText.END, "-", regex=False)
    return df


def getCalculatedValues(df, periods, key, userArgs=None, task=None):
    collated_df = None
    for period in periods:
        ltpSum1ShareEach = round(df["LTP"].sum(), 2)
        tdySum1ShareEach = round(df[f"LTP{period}"].sum(), 2)
        growthSum1ShareEach = round(df[f"Growth{period}"].sum(), 2)
        percentGrowth = 0
        if ltpSum1ShareEach > 0:
            percentGrowth = round(100 * growthSum1ShareEach / ltpSum1ShareEach, 2)
        growth10k = round(10000 * (1 + 0.01 * percentGrowth), 2)
        if configManager.enablePortfolioCalculations and userArgs.options.startswith("B"): # backtests
            portfolio = Portfolio(name=key)
            portfolio.updatePortfolioFromXRayDataFrame(df,configManager.periodsRange,task)
            PortfolioCollection().addPortfolio(portfolio)
        result_df = {
            "ScanType": key, #if tdySum1ShareEach != 0 else 999999999,
            f"{period}Pd-PFV": tdySum1ShareEach,
            f"{period}Pd-%": percentGrowth if tdySum1ShareEach != 0 else 999999999,
            f"{period}Pd-10k": growth10k if tdySum1ShareEach != 0 else 999999999,
        }
        if collated_df is None:
            collated_df = result_df
        collated_df = collated_df | result_df
    # percentGrowth = colorText.GREEN if percentGrowth >=0 else colorText.FAIL + percentGrowth + colorText.END
    # growth10k = colorText.GREEN if percentGrowth >=0 else colorText.FAIL + growth10k + colorText.END
    # df_col = {'ScanType':key,
    #     f'{period}Pd-PFV':tdySum1ShareEach,
    #     f'{period}Pd-PFG':percentGrowth if tdySum1ShareEach != 0 else '-',
    #     f'{period}Pd-Go10k':growth10k if tdySum1ShareEach != 0 else '-',
    #     }

    return collated_df  # , df_col


def filterRSIAbove50(df):
    if df is None:
        return None
    return df[df["RSI"] > 50].fillna(0.0)


def filterRSI50To67(df):
    if df is None:
        return None
    return df[(df["RSI"] >= 50) & (df["RSI"] <= 67)].fillna(0.0)


def filterRSI68OrAbove(df):
    if df is None:
        return None
    return df[df["RSI"] >= 68].fillna(0.0)


def filterTrendStrongUp(df):
    if df is None:
        return None
    return df[df[f"Trend({configManager.daysToLookback}Prds)"] == "Strong Up"].fillna(0.0)


def filterTrendWeakUp(df):
    if df is None:
        return None
    return df[df[f"Trend({configManager.daysToLookback}Prds)"] == "Weak Up"].fillna(0.0)


def filterTrendWeakDown(df):
    if df is None:
        return None
    return df[df[f"Trend({configManager.daysToLookback}Prds)"] == "Weak Down"].fillna(0.0)


def filterTrendStrongDown(df):
    if df is None:
        return None
    return df[df[f"Trend({configManager.daysToLookback}Prds)"] == "Strong Down"].fillna(0.0)


def filterTrendUp(df):
    if df is None:
        return None
    return df[df[f"Trend({configManager.daysToLookback}Prds)"].astype(str).str.endswith("Up")].fillna(0.0)


def filterTrendSideways(df):
    if df is None:
        return None
    return df[df[f"Trend({configManager.daysToLookback}Prds)"] == "Sideways"].fillna(0.0)


def filterTrendDown(df):
    if df is None:
        return None
    return df[df[f"Trend({configManager.daysToLookback}Prds)"].astype(str).str.endswith("Down")].fillna(0.0)


def filterMASignalBullish(df):
    if df is None:
        return None
    return df[df["MA-Signal"] == "Bullish"].fillna(0.0)


def filterMASignalBearish(df):
    if df is None:
        return None
    return df[df["MA-Signal"] == "Bearish"].fillna(0.0)


def filterMASignalNeutral(df):
    if df is None:
        return None
    return df[df["MA-Signal"] == "Neutral"].fillna(0.0)


def filterMASignalBullCross(df):
    if df is None:
        return None
    return df[df["MA-Signal"].astype(str).str.startswith("BullCross")].fillna(0.0)


def filterMASignalBearCross(df):
    if df is None:
        return None
    return df[df["MA-Signal"].astype(str).str.startswith("BearCross")].fillna(0.0)


def filterMASignalSupport(df):
    if df is None:
        return None
    return df[df["MA-Signal"].astype(str).str.endswith("Support")].fillna(0.0)


def filterMASignalResist(df):
    if df is None:
        return None
    return df[df["MA-Signal"].astype(str).str.endswith("Resist")].fillna(0.0)


def filterVolumeLessThan25(df):
    if df is None:
        return None
    return df[df["Volume"] < 2.5].fillna(0.0)


def filterVolumeMoreThan25(df):
    if df is None:
        return None
    return df[df["Volume"] >= 2.5].fillna(0.0)


def filterConsolidating10Percent(df):
    if df is None:
        return None
    return df[df[f"Consol."] <= 10].fillna(0.0)


def filterConsolidatingMore10Percent(df):
    if df is None:
        return None
    return df[df[f"Consol."] > 10].fillna(0.0)


def filterLTPLessThanBreakout(df):
    if df is None:
        return None
    return df[df["LTP"] < df["Breakout"]].fillna(0.0)


def filterLTPMoreOREqualBreakout(df):
    if df is None:
        return None
    return df[((df["Breakout"] > 0) & (df["LTP"] >= df["Breakout"]))].fillna(0.0)


def filterLTPLessThanResistance(df):
    if df is None:
        return None
    return df[df["LTP"] < df["Resistance"]].fillna(0.0)


def filterLTPMoreOREqualResistance(df):
    if df is None:
        return None
    return df[((df["Resistance"] > 0) & (df["LTP"] >= df["Resistance"]))].fillna(0.0)


def filterLTPMoreOREqual52WkH(df):
    if df is None:
        return None
    return df[df["LTP"] >= df["52Wk-H"]].fillna(0.0)


def filterLTPWithin90Percent52WkH(df):
    if df is None:
        return None
    return df[(df["LTP"] >= 0.9 * df["52Wk-H"]) & (df["LTP"] < df["52Wk-H"])].fillna(
        0.0
    )


def filterLTPLess90Percent52WkH(df):
    if df is None:
        return None
    return df[df["LTP"] < 0.9 * df["52Wk-H"]].fillna(0.0)


def filterLTPMore52WkL(df):
    if df is None:
        return None
    return df[((df["LTP"] > df["52Wk-L"]) & (df["LTP"] < 1.1 * df["52Wk-L"]))].fillna(
        0.0
    )


def filterLTPWithin90Percent52WkL(df):
    if df is None:
        return None
    return df[(df["LTP"] >= (1.1 * df["52Wk-L"])) & (df["LTP"] > df["52Wk-L"])].fillna(
        0.0
    )


def filterLTPLess52WkL(df):
    if df is None:
        return None
    return df[df["LTP"] <= df["52Wk-L"]].fillna(0.0)


def filterCCIBelowMinus100(df):
    if df is None:
        return None
    return df[df["CCI"] <= -100].fillna(0.0)


def filterCCIBelow0(df):
    if df is None:
        return None
    return df[(df["CCI"] > -100) & (df["CCI"] < 0)].fillna(0.0)


def filterCCI0To100(df):
    if df is None:
        return None
    return df[(df["CCI"] >= 0) & (df["CCI"] <= 100)].fillna(0.0)


def filterCCI100To200(df):
    if df is None:
        return None
    return df[(df["CCI"] > 100) & (df["CCI"] <= 200)].fillna(0.0)


def filterCCIAbove200(df):
    if df is None:
        return None
    return df[(df["CCI"] > 200)].fillna(0.0)

def returnNoFilter(df):
    return df

def filterPattern(df, pattern="[P]No Pattern"):
    if df is None:
        return None
    match_df = None
    df_grouped = df.groupby("Pattern")
    for foundPattern, df_group in df_grouped:
        if foundPattern is None or len(foundPattern) == 0:
            foundPattern = "No Pattern"
        if f"[P]{foundPattern}" == pattern:
            match_df = df_group
            break
    return match_df

def strategyDictionary():
    """
    Available Strategies:

    RSI
    ---
    `RSI>=50`, `50<=RSI<=67` and `RSI>=68`

    CCI
    ---
    `[CCI]<=-100`, `[CCI]-100<C<0`, `[CCI]0<=C<=100`, `[CCI]100<C<=200` and `[CCI]>200`

    52Wk-H/L
    --------
    `[52Wk]LTP>=H`, `[52Wk]LTP>=.9*H`, `[52Wk]LTP<.9*H`, `[52Wk]LTP>L`, `[52Wk]LTP>=1.1*L` and `[52Wk]LTP<=L`

    Breakout
    --------
    `[BO]LTP<BO`, `[BO]LTP>=BO`, `[BO]LTP<R` and `[BO]LTP>=R`

    Consolidation
    -------------
    `Cons.<=10` and Cons.>10

    Volume
    ------
    `Vol<2.5` and `Vol>=2.5`

    Moving Averages
    ---------------
    `[MA]Bull`, `[MA]Bear`, `[MA]Neutral`, `[MA]BullCross`, `[MA]BearCross`, `[MA]Support` and `[MA]Resist`

    Trends
    ------
    `[T]StrongUp`, `[T]WeakUp`, `[T]TrendUp`, `[T]StrongDown`, `[T]WeakDown`, `[T]Sideways` and `[T]TrendDown`

    NoFilter
    --------
    `NoFilter`

    Patterns
    --------
    `[P]{patern_name}`. For example, `[P]No Pattern`
    """
    strategies = {}
    # RSI
    strategies["[RSI]>=50"] = filterRSIAbove50
    strategies["[RSI]50<=RSI<=67"] = filterRSI50To67
    strategies["[RSI]>=68"] = filterRSI68OrAbove
    # CCI
    strategies["[CCI]<=-100"] = filterCCIBelowMinus100
    strategies["[CCI]-100<C<0"] = filterCCIBelow0
    strategies["[CCI]0<=C<=100"] = filterCCI0To100
    strategies["[CCI]100<C<=200"] = filterCCI100To200
    strategies["[CCI]>200"] = filterCCIAbove200
    # 52Wk-H/L
    strategies["[52Wk]LTP>=H"] = filterLTPMoreOREqual52WkH
    strategies["[52Wk]LTP>=.9*H"] = filterLTPWithin90Percent52WkH
    strategies["[52Wk]LTP<.9*H"] = filterLTPLess90Percent52WkH
    strategies["[52Wk]LTP>L"] = filterLTPMore52WkL
    strategies["[52Wk]LTP>=1.1*L"] = filterLTPWithin90Percent52WkL
    strategies["[52Wk]LTP<=L"] = filterLTPLess52WkL
    # Breakout
    strategies["[BO]LTP<BO"] = filterLTPLessThanBreakout
    strategies["[BO]LTP>=BO"] = filterLTPMoreOREqualBreakout
    strategies["[BO]LTP<R"] = filterLTPLessThanResistance
    strategies["[BO]LTP>=R"] = filterLTPMoreOREqualResistance
    # Consolidation
    strategies["Cons.<=10"] = filterConsolidating10Percent
    strategies["Cons.>10"] = filterConsolidatingMore10Percent
    # Volume
    strategies["Vol<2.5"] = filterVolumeLessThan25
    strategies["Vol>=2.5"] = filterVolumeMoreThan25
    # MA
    strategies["[MA]Bull"] = filterMASignalBullish
    strategies["[MA]Bear"] = filterMASignalBearish
    strategies["[MA]Neutral"] = filterMASignalNeutral
    strategies["[MA]BullCross"] = filterMASignalBullCross
    strategies["[MA]BearCross"] = filterMASignalBearCross
    strategies["[MA]Support"] = filterMASignalSupport
    strategies["[MA]Resist"] = filterMASignalResist
    # Trends
    strategies["[T]StrongUp"] = filterTrendStrongUp
    strategies["[T]WeakUp"] = filterTrendWeakUp
    strategies["[T]TrendUp"] = filterTrendUp
    strategies["[T]StrongDown"] = filterTrendStrongDown
    strategies["[T]WeakDown"] = filterTrendWeakDown
    strategies["[T]Sideways"] = filterTrendSideways
    strategies["[T]TrendDown"] = filterTrendDown
    # NoFilter
    strategies["NoFilter"] = returnNoFilter
    # Pattern
    strategies["[P]"] = filterPattern
    return strategies

def strategyForKey(key:str):
    strategies = strategyDictionary()
    if key in strategies.keys():
        return strategies[key]
    elif key.startswith("[P]"):
        return strategies["[P]"]

def strategyNames():
    return strategyDictionary().keys()