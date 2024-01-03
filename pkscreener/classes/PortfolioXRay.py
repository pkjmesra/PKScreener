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
        # saveResults[['Breakout', 'Resistance']] = df['Breakout(30Prds)'].str.split(' R: ', n=1, expand=True)
        # saveResults.loc[:, 'Breakout'] = saveResults.loc[:, 'Breakout'].apply(
        #         lambda x: x.replace('BO: ','').replace(' ','')
        #     )
        saveResults['Volume'] = saveResults['Volume'].astype(float).fillna(0.0)
        saveResults['Consol.(30Prds)'] = saveResults['Consol.(30Prds)'].astype(float).fillna(0.0)
        
        ltpSum1ShareEach = round(saveResults['LTP'].sum(),2)
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
            scanResults.append(getCalculatedValues(filterTrendStrongUp(saveResults),period,'StrongUp',args))
            scanResults.append(getCalculatedValues(filterTrendWeakUp(saveResults),period,'WeakUp',args))
            scanResults.append(getCalculatedValues(filterTrendUp(saveResults),period,'TrendUp',args))
            scanResults.append(getCalculatedValues(filterTrendSideways(saveResults),period,'Sideways',args))
            scanResults.append(getCalculatedValues(filterTrendDown(saveResults),period,'TrendDown',args))
            scanResults.append(getCalculatedValues(filterMASignalBullish(saveResults),period,'MABull',args))
            scanResults.append(getCalculatedValues(filterMASignalBearish(saveResults),period,'MABear',args))
            scanResults.append(getCalculatedValues(filterMASignalBullCross(saveResults),period,'BullCross',args))
            scanResults.append(getCalculatedValues(filterMASignalBearCross(saveResults),period,'BearCross',args))
            scanResults.append(getCalculatedValues(filterMASignalSupport(saveResults),period,'MASupport',args))
            scanResults.append(getCalculatedValues(filterMASignalResist(saveResults),period,'MAResist',args))
            scanResults.append(getCalculatedValues(filterVolumeLessThan25(saveResults),period,'Vol<2.5',args))
            scanResults.append(getCalculatedValues(filterVolumeMoreThan25(saveResults),period,'Vol>=2.5',args))
            scanResults.append(getCalculatedValues(filterConsolidating10Percent(saveResults),period,'Cons.<=10',args))
            scanResults.append(getCalculatedValues(filterConsolidatingMore10Percent(saveResults),period,'Cons.>10',args))
            # scanResults.append(getCalculatedValues(filterLTPLessThanBreakout(saveResults),period,'LTP<BO',args))
            # scanResults.append(getCalculatedValues(filterLTPMoreOREqualBreakout(saveResults),period,'LTP>=BO',args))
            # scanResults.append(getCalculatedValues(filterLTPLessThanResistance(saveResults),period,'LTP<R',args))
            # scanResults.append(getCalculatedValues(filterLTPMoreOREqualResistance(saveResults),period,'LTP>=R',args))
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
        # maxValue = df.idxmax(axis=1)
        maxGrowth = -100
        df1 = df.copy()
        df1 = df1[[col for col in df1.columns if ('D-%' in col)]]
        for col in df1.columns:
            if 'D-%' in col:
                mx = df1[col].max()
                if maxGrowth < mx:
                    maxGrowth = mx

        # df = df.replace(np.nan, '-', regex=True)
        df = df.replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna()
        for col in df.columns:
            if 'D-%' in col:
                df.loc[:, col] = df.loc[:, col].apply(
                        lambda x: x if (str(x) == '-') else (str(x).replace(str(x),(((colorText.BOLD + colorText.WHITE) if x==maxGrowth else colorText.GREEN) if float(x) >0 else (colorText.FAIL if float(x) <0 else colorText.WARN)) + str(float(x)) + " %" + colorText.END))
                    )
            if 'D-10k' in col:
                df.loc[:, col] = df.loc[:, col].apply(
                        lambda x: x if (str(x) == '-') else (str(x).replace(str(x),((colorText.GREEN) if (float(x) >10000) else (colorText.FAIL if float(x) <10000 else colorText.WARN)) + str(x) + colorText.END))
                    )
        df.insert(1, 'Date', calcForDate if calcForDate is not None else saveResults['Date'].iloc[0])
        return df
    
def getCalculatedValues(df, period,key,args=None):
    ltpSum1ShareEach = round(df['LTP'].sum(),2)
    tdySum1ShareEach= round(df[f'LTP{period}'].sum(),2)
    growthSum1ShareEach= round(df[f'Growth{period}'].sum(),2)
    percentGrowth = round(100*growthSum1ShareEach/ltpSum1ShareEach,2)
    growth10k = round(10000*(1+0.01*percentGrowth),2)
    df = {'ScanType':key,
            f'{period}D-PFV':tdySum1ShareEach,
            f'{period}D-%':percentGrowth, #if tdySum1ShareEach != 0 else '-',
            f'{period}D-10k':growth10k, # if tdySum1ShareEach != 0 else '-',
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
    return df[df['LTP'] >= df['Breakout']].fillna(0.0)

def filterLTPLessThanResistance(df):
    if df is None:
        return None
    return df[df['LTP'] < df['Resistance']].fillna(0.0)

def filterLTPMoreOREqualResistance(df):
    if df is None:
        return None
    return df[df['LTP'] >= df['Resistance']].fillna(0.0)

