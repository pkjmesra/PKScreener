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
import numpy as np
import pandas as pd

from tabulate import tabulate
from PKDevTools.classes.ColorText import colorText
from pkscreener.classes import Utility

def bestStrategiesFromSummaryForReport(reportName:None):
    dfs = []
    try:
        dfs = pd.read_html('https://pkjmesra.github.io/PKScreener/Backtest-Reports/{0}'.format(reportName.replace("_X_","_B_").replace("_G_","_B_")))
    except:
        pass
    insights = None
    strategy_percent = {}
    strategy = {}
    if len(dfs) > 0:
        df = dfs[0]
        if len(dfs) > 0:
            insights = df[df['ScanType'].astype(str).str.startswith("[SUM]")]
            insights = insights.replace(' %', '', regex=True)
            # insights = insights.replace('', np.nan, regex=True)
            # insights = insights.replace('-', np.nan, regex=True)
            periods = [1,2,3,4,5,10,15,22,30]
            for prd in periods:
                try:
                    insights[f'{prd}D-%'] = insights[f'{prd}D-%'].astype(float).fillna(0.0)
                    max_p = insights[f'{prd}D-%'].max()
                    strategy_percent[f'{prd}D'] = f"{colorText.GREEN if max_p > 0 else (colorText.FAIL if max_p < 0 else colorText.WARN)}{max_p} %{colorText.END}"
                    scanType = str(insights['ScanType'].iloc[insights[f'{prd}D-%'].idxmax()]).replace('[SUM]','').split('(')[0]
                    strategy[f'{prd}D'] = scanType
                except:
                    pass
            insights_list = [strategy,strategy_percent]
            insights= pd.DataFrame(insights_list)
    return insights

def xRaySummary(savedResults=None):
    saveResults = savedResults.copy()
    df_grouped = saveResults.groupby('ScanType')
    periods = [1,2,3,4,5,10,15,22,30]
    sum_list = []
    sum_dict = {}
    maxGrowth = -100
    for scanType, df_group in df_grouped:
        groupItems = len(df_group)
        sum_dict = {}
        sum_dict['ScanType'] = f'[SUM]{scanType}({groupItems})'
        sum_dict['Date'] = Utility.tools.currentDateTime().strftime("%Y-%m-%d")
        for prd in periods:
            if not f'{prd}D-%' in df_group.columns:
                continue
            prd_df = df_group[[f'{prd}D-%', f'{prd}D-10k']]
            prd_df.loc[:, f'{prd}D-10k'] = prd_df.loc[:, f'{prd}D-10k'].apply(
                lambda x: Utility.tools.removeAllColorStyles(x)
                )
            prd_df = prd_df.replace('-', np.nan, regex=True)
            prd_df = prd_df.replace('', np.nan, regex=True)
            prd_df.dropna(axis=0,how='all', inplace=True)
            prd_df[f'{prd}D-10k'] = prd_df[f'{prd}D-10k'].astype(float).fillna(0.0)
            gain = round((prd_df[f'{prd}D-10k'].sum() - 10000 * len(prd_df))*100/(10000 * len(prd_df)),2)
            sum_dict[f'{prd}D-%'] = gain
            sum_dict[f'{prd}D-10k'] = round(prd_df[f'{prd}D-10k'].sum()/len(prd_df),2)
        sum_list.append(sum_dict)
    df = pd.DataFrame(sum_list)
    df = formatGridOutput(df)
    saveResults = pd.concat([saveResults, df], axis=0)
    saveResults = saveResults.replace(np.nan, '-', regex=True)
    return saveResults

def performXRay(savedResults=None, args=None, calcForDate=None):
    if savedResults is not None and len(savedResults) > 0:
        backtestPeriods = 30 # Max backtest days
        if args is not None and args.backtestdaysago is not None:
            backtestPeriods = int(args.backtestdaysago)
        saveResults = savedResults.copy()
        for col in saveResults.columns:
            saveResults.loc[:, col] = saveResults.loc[:, col].apply(
            lambda x: Utility.tools.removeAllColorStyles(x)
            )
            
        saveResults['LTP'] = saveResults['LTP'].astype(float).fillna(0.0)
        saveResults['RSI'] = saveResults['RSI'].astype(float).fillna(0.0)
        saveResults.loc[:, 'Volume'] = saveResults.loc[:, 'Volume'].apply(
            lambda x: x.replace('x','')
            )
        if 'Consol.(30Prds)' not in saveResults.columns:
            saveResults.rename(columns={"Consol.": "Consol.(30Prds)","Trend": "Trend(30Prds)","Breakout": "Breakout(30Prds)"},inplace=True,)
        saveResults.loc[:, 'Consol.(30Prds)'] = saveResults.loc[:, 'Consol.(30Prds)'].apply(
                lambda x: x.replace('Range:','').replace('%','')
            )
        saveResults[['Breakout', 'Resistance']] = saveResults['Breakout(30Prds)'].str.split(' R: ', n=1, expand=True)
        saveResults.loc[:, 'Breakout'] = saveResults.loc[:, 'Breakout'].apply(
                lambda x: x.replace('BO: ','').replace(' ','')
            )
        saveResults['Volume'] = saveResults['Volume'].astype(float).fillna(0.0)
        saveResults['Consol.(30Prds)'] = saveResults['Consol.(30Prds)'].astype(float).fillna(0.0)
        saveResults['Breakout'] = saveResults['Breakout'].astype(float).fillna(0.0)
        saveResults['Resistance'] = saveResults['Resistance'].astype(float).fillna(0.0)
        saveResults['52Wk H'] = saveResults['52Wk H'].astype(float).fillna(0.0)
        saveResults['52Wk L'] = saveResults['52Wk L'].astype(float).fillna(0.0)
        saveResults['CCI'] = saveResults['CCI'].astype(float).fillna(0.0)

        days = 0
        df = None
        periods = [1,2,3,4,5,10,15,22,30]
        period = periods[days]
        targetDate = calcForDate if calcForDate is not None else saveResults['Date'].iloc[0]
        today = Utility.tools.currentDateTime()
        gap = Utility.tools.trading_days_between(Utility.tools.dateFromYmdString(targetDate).replace(tzinfo=today.tzinfo).date(),today.date())
        backtestPeriods = gap if gap > backtestPeriods else backtestPeriods
        while periods[days] <= backtestPeriods:
            period = periods[days]
            saveResults[f'LTP{period}'] = saveResults[f'LTP{period}'].astype(float).fillna(0.0)
            saveResults[f'Growth{period}'] = saveResults[f'Growth{period}'].astype(float).fillna(0.0)
            
            scanResults = []
            scanResults.append(getCalculatedValues(filterRSIAbove50(saveResults),period,'RSI>=50',args))
            scanResults.append(getCalculatedValues(filterRSI50To67(saveResults),period,'RSI<=67',args))
            scanResults.append(getCalculatedValues(filterRSI68OrAbove(saveResults),period,'RSI>=68',args))
            scanResults.append(getCalculatedValues(filterTrendStrongUp(saveResults),period,'[T]StrongUp',args))
            scanResults.append(getCalculatedValues(filterTrendWeakUp(saveResults),period,'[T]WeakUp',args))
            scanResults.append(getCalculatedValues(filterTrendUp(saveResults),period,'[T]TrendUp',args))
            scanResults.append(getCalculatedValues(filterTrendSideways(saveResults),period,'[T]Sideways',args))
            scanResults.append(getCalculatedValues(filterTrendDown(saveResults),period,'[T]TrendDown',args))
            scanResults.append(getCalculatedValues(filterMASignalBullish(saveResults),period,'[MA]Bull',args))
            scanResults.append(getCalculatedValues(filterMASignalBearish(saveResults),period,'[MA]Bear',args))
            scanResults.append(getCalculatedValues(filterMASignalBullCross(saveResults),period,'[MA]BullCross',args))
            scanResults.append(getCalculatedValues(filterMASignalBearCross(saveResults),period,'[MA]BearCross',args))
            scanResults.append(getCalculatedValues(filterMASignalSupport(saveResults),period,'[MA]Support',args))
            scanResults.append(getCalculatedValues(filterMASignalResist(saveResults),period,'[MA]Resist',args))
            scanResults.append(getCalculatedValues(filterVolumeLessThan25(saveResults),period,'Vol<2.5',args))
            scanResults.append(getCalculatedValues(filterVolumeMoreThan25(saveResults),period,'Vol>=2.5',args))
            scanResults.append(getCalculatedValues(filterConsolidating10Percent(saveResults),period,'Cons.<=10',args))
            scanResults.append(getCalculatedValues(filterConsolidatingMore10Percent(saveResults),period,'Cons.>10',args))
            scanResults.append(getCalculatedValues(filterLTPLessThanBreakout(saveResults),period,'[BO]LTP<BO',args))
            scanResults.append(getCalculatedValues(filterLTPMoreOREqualBreakout(saveResults),period,'[BO]LTP>=BO',args))
            scanResults.append(getCalculatedValues(filterLTPLessThanResistance(saveResults),period,'[BO]LTP<R',args))
            scanResults.append(getCalculatedValues(filterLTPMoreOREqualResistance(saveResults),period,'[BO]LTP>=R',args))
            scanResults.append(getCalculatedValues(filterLTPMoreOREqual52WkH(saveResults),period,'[52Wk]LTP>=H',args))
            scanResults.append(getCalculatedValues(filterLTPWithin90Percent52WkH(saveResults),period,'[52Wk]LTP>=.9*H',args))
            scanResults.append(getCalculatedValues(filterLTPLess90Percent52WkH(saveResults),period,'[52Wk]LTP<.9*H',args))
            scanResults.append(getCalculatedValues(filterLTPMore52WkL(saveResults),period,'[52Wk]LTP>L',args))
            scanResults.append(getCalculatedValues(filterLTPWithin90Percent52WkL(saveResults),period,'[52Wk]LTP>=1.1*L',args))
            scanResults.append(getCalculatedValues(filterLTPLess52WkL(saveResults),period,'[52Wk]LTP<=L',args))
            scanResults.append(getCalculatedValues(filterCCIBelowMinus100(saveResults),period,'[CCI]<=-100',args))
            scanResults.append(getCalculatedValues(filterCCIBelow0(saveResults),period,'[CCI]-100<C<0',args))
            scanResults.append(getCalculatedValues(filterCCI0To100(saveResults),period,'[CCI]0<=C<=100',args))
            scanResults.append(getCalculatedValues(filterCCI100To200(saveResults),period,'[CCI]100<C<=200',args))
            scanResults.append(getCalculatedValues(filterCCIAbove200(saveResults),period,'[CCI]>200',args))
            
            df_grouped = saveResults.groupby('Pattern')
            for pattern, df_group in df_grouped:
                if pattern is None or len(pattern) == 0:
                    pattern = 'No Pattern'
                scanResults.append(getCalculatedValues(df_group,period,f'[P]{pattern}',args))

            scanResults.append(getCalculatedValues(saveResults,period,'NoFilter',args))

            if df is None:
                df = pd.DataFrame(scanResults)
            else:
                df1 = pd.DataFrame(scanResults)
                df_target = df1[[col for col in df1.columns if ('D-%' in col or 'D-10k' in col)]]
                df = pd.concat([df, df_target], axis=1)
            days += 1
            if days >= len(periods):
                break

        df = df[[col for col in df.columns if ('ScanType' in col or 'D-%' in col or 'D-10k' in col)]]
        df = df.replace(999999999, np.nan, regex=True)
        df.dropna(axis=0,how='all', inplace=True)
        df = formatGridOutput(df)
        df.insert(1, 'Date', calcForDate if calcForDate is not None else saveResults['Date'].iloc[0])
        return df

def formatGridOutput(df):
    df = df.replace(np.nan, '-', regex=True)
    for col in df.columns:
        maxGrowth = df[col].max()
        if 'D-%' in col:
            df.loc[:, col] = df.loc[:, col].apply(
                        lambda x: x if (str(x) == '-') else (str(x).replace(str(x),(((colorText.BOLD + colorText.WHITE) if x==maxGrowth else colorText.GREEN) if float(x) >0 else (colorText.FAIL if float(x) <0 else colorText.WARN)) + str(float(x)) + " %" + colorText.END))
                    )
        if 'D-10k' in col:
            df.loc[:, col] = df.loc[:, col].apply(
                        lambda x: x if (str(x) == '-') else (str(x).replace(str(x),(((colorText.BOLD + colorText.WHITE) if x==maxGrowth else colorText.GREEN) if (float(x) >10000) else (colorText.FAIL if float(x) <10000 else colorText.WARN)) + str(x) + colorText.END))
                    )
    return df
    
def getCalculatedValues(df, period,key,args=None):
    ltpSum1ShareEach = round(df['LTP'].sum(),2)
    tdySum1ShareEach= round(df[f'LTP{period}'].sum(),2)
    growthSum1ShareEach= round(df[f'Growth{period}'].sum(),2)
    percentGrowth = round(100*growthSum1ShareEach/ltpSum1ShareEach,2)
    growth10k = round(10000*(1+0.01*percentGrowth),2)
    df = {'ScanType':key if tdySum1ShareEach != 0 else 999999999,
            f'{period}D-PFV':tdySum1ShareEach,
            f'{period}D-%':percentGrowth if tdySum1ShareEach != 0 else 999999999,
            f'{period}D-10k':growth10k if tdySum1ShareEach != 0 else 999999999,
            }
    # percentGrowth = colorText.GREEN if percentGrowth >=0 else colorText.FAIL + percentGrowth + colorText.END
    # growth10k = colorText.GREEN if percentGrowth >=0 else colorText.FAIL + growth10k + colorText.END
    # df_col = {'ScanType':key,
    #     f'{period}D-PFV':tdySum1ShareEach,
    #     f'{period}D-PFG':percentGrowth if tdySum1ShareEach != 0 else '-',
    #     f'{period}D-Go10k':growth10k if tdySum1ShareEach != 0 else '-',
    #     }
    return df #, df_col

def filterRSIAbove50(df):
    if df is None:
        return None
    return df[df['RSI'] > 50].fillna(0.0)

def filterRSI50To67(df):
    if df is None:
        return None
    return df[(df['RSI'] >= 50) & (df['RSI'] <= 67)].fillna(0.0)

def filterRSI68OrAbove(df):
    if df is None:
        return None
    return df[df['RSI'] >= 68].fillna(0.0)

def filterTrendStrongUp(df):
    if df is None:
        return None
    return df[df['Trend(30Prds)'] == 'Strong Up'].fillna(0.0)

def filterTrendWeakUp(df):
    if df is None:
        return None
    return df[df['Trend(30Prds)'] == 'Weak Up'].fillna(0.0)

def filterTrendUp(df):
    if df is None:
        return None
    return df[df['Trend(30Prds)'].astype(str).str.contains("Up")].fillna(0.0)

def filterTrendSideways(df):
    if df is None:
        return None
    return df[df['Trend(30Prds)'] == 'Sideways'].fillna(0.0)

def filterTrendDown(df):
    if df is None:
        return None
    return df[df['Trend(30Prds)'].astype(str).str.contains("Down")].fillna(0.0)

def filterMASignalBullish(df):
    if df is None:
        return None
    return df[df['MA-Signal'] == 'Bullish'].fillna(0.0)

def filterMASignalBearish(df):
    if df is None:
        return None
    return df[df['MA-Signal'] == 'Bearish'].fillna(0.0)

def filterMASignalBullCross(df):
    if df is None:
        return None
    return df[df['MA-Signal'].astype(str).str.contains("BullCross")].fillna(0.0)

def filterMASignalBearCross(df):
    if df is None:
        return None
    return df[df['MA-Signal'].astype(str).str.contains("BearCross")].fillna(0.0)

def filterMASignalSupport(df):
    if df is None:
        return None
    return df[df['MA-Signal'].astype(str).str.contains("Support")].fillna(0.0)

def filterMASignalResist(df):
    if df is None:
        return None
    return df[df['MA-Signal'].astype(str).str.contains("Resist")].fillna(0.0)

def filterVolumeLessThan25(df):
    if df is None:
        return None
    return df[df['Volume'] < 2.5].fillna(0.0)

def filterVolumeMoreThan25(df):
    if df is None:
        return None
    return df[df['Volume'] >= 2.5].fillna(0.0)

def filterConsolidating10Percent(df):
    if df is None:
        return None
    return df[df['Consol.(30Prds)'] <= 10].fillna(0.0)

def filterConsolidatingMore10Percent(df):
    if df is None:
        return None
    return df[df['Consol.(30Prds)'] > 10].fillna(0.0)

def filterLTPLessThanBreakout(df):
    if df is None:
        return None
    return df[df['LTP'] < df['Breakout']].fillna(0.0)

def filterLTPMoreOREqualBreakout(df):
    if df is None:
        return None
    return df[((df['Breakout'] > 0) & (df['LTP'] >= df['Breakout']))].fillna(0.0)

def filterLTPLessThanResistance(df):
    if df is None:
        return None
    return df[df['LTP'] < df['Resistance']].fillna(0.0)

def filterLTPMoreOREqualResistance(df):
    if df is None:
        return None
    return df[((df['Resistance'] > 0) & (df['LTP'] >= df['Resistance']))].fillna(0.0)

def filterLTPMoreOREqual52WkH(df):
    if df is None:
        return None
    return df[df['LTP'] >= df['52Wk H']].fillna(0.0)

def filterLTPWithin90Percent52WkH(df):
    if df is None:
        return None
    return df[(df['LTP'] >= 0.9*df['52Wk H']) & (df['LTP'] < df['52Wk H'])].fillna(0.0)

def filterLTPLess90Percent52WkH(df):
    if df is None:
        return None
    return df[df['LTP'] < 0.9*df['52Wk H']].fillna(0.0)

def filterLTPMore52WkL(df):
    if df is None:
        return None
    return df[((df['LTP'] > df['52Wk L']) & (df['LTP'] < 1.1*df['52Wk L']))].fillna(0.0)

def filterLTPWithin90Percent52WkL(df):
    if df is None:
        return None
    return df[(df['LTP'] >= 1.1*df['52Wk L']) & (df['LTP'] > df['52Wk L'])].fillna(0.0)

def filterLTPLess52WkL(df):
    if df is None:
        return None
    return df[df['LTP'] <= df['52Wk L']].fillna(0.0)

def filterCCIBelowMinus100(df):
    if df is None:
        return None
    return df[df['CCI'] <= -100].fillna(0.0)

def filterCCIBelow0(df):
    if df is None:
        return None
    return df[(df['CCI'] > -100) & (df['CCI'] < 0)].fillna(0.0)

def filterCCI0To100(df):
    if df is None:
        return None
    return df[(df['CCI'] >=0) & (df['CCI'] <=100)].fillna(0.0)

def filterCCI100To200(df):
    if df is None:
        return None
    return df[(df['CCI'] >100) & (df['CCI'] <=200)].fillna(0.0)

def filterCCIAbove200(df):
    if df is None:
        return None
    return df[(df['CCI'] >200)].fillna(0.0)