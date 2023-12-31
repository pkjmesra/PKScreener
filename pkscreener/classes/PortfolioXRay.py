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

from tabulate import tabulate
from PKDevTools.classes.ColorText import colorText


def performXRay(savedResults=None, args=0):
    if savedResults is not None:
        saveResults = savedResults.copy()
        saveResults['LTP'] = saveResults['LTP'].astype(float).fillna(0.0)
        saveResults['LTPTdy'] = saveResults['LTPTdy'].astype(float).fillna(0.0)
        saveResults['Growth'] = saveResults['Growth'].astype(float).fillna(0.0)
        saveResults['RSI'] = saveResults['RSI'].astype(float).fillna(0.0)
        saveResults.loc[:, 'Volume'] = saveResults.loc[:, 'Volume'].apply(
            lambda x: x.replace('x','')
            )
        saveResults.loc[:, 'Consol.(30Prds)'] = saveResults.loc[:, 'Consol.(30Prds)'].apply(
                lambda x: x.replace('Range:','').replace('%','')
            )
        saveResults['Volume'] = saveResults['Volume'].astype(float).fillna(0.0)
        saveResults['Consol.(30Prds)'] = saveResults['Consol.(30Prds)'].astype(float).fillna(0.0)
        
        ltpSum1ShareEach = round(saveResults['LTP'].sum(),2)
        tdySum1ShareEach= saveResults['LTPTdy'].sum()
        growthSum1ShareEach= round(saveResults['Growth'].sum(),2)
        percentGrowth = round(100*growthSum1ShareEach/ltpSum1ShareEach,2)
        growth10k = 10000*(1+0.01*percentGrowth)
        clr = colorText.GREEN if growthSum1ShareEach >=0 else colorText.FAIL
        print(f"[+] Total (1 share each bought on the date above)           : ₹ {ltpSum1ShareEach:7.2f}")
        print(f"[+] Total (portfolio value today for 1 share each)          : ₹ {clr}{tdySum1ShareEach:7.2f}{colorText.END}")
        print(f"[+] Total (portfolio value growth in {args.backtestdaysago} days                : ₹ {clr}{growthSum1ShareEach:7.2f}{colorText.END}")
        print(f"[+] Growth (@ {clr}{percentGrowth:5.2f} %{colorText.END}) of ₹ 10k, if you'd have invested)    : ₹ {clr}{growth10k:7.2f}{colorText.END}")
        scanResults = []

        scanResults.append(getCalculatedValues(filterRSIAbove50(saveResults),1,'RSI>=50'))
        scanResults.append(getCalculatedValues(filterRSI50To67(saveResults),1,'RSI<=67'))
        scanResults.append(getCalculatedValues(filterRSI68OrAbove(saveResults),1,'RSI>=68'))
        scanResults.append(getCalculatedValues(filterTrendStrongUp(saveResults),1,'StrngUp'))
        scanResults.append(getCalculatedValues(filterTrendWeakUp(saveResults),1,'WkUp'))
        scanResults.append(getCalculatedValues(filterTrendUp(saveResults),1,'TrndUp'))
        scanResults.append(getCalculatedValues(filterTrendSideways(saveResults),1,'Sideways'))
        scanResults.append(getCalculatedValues(filterTrendDown(saveResults),1,'TrndDown'))
        scanResults.append(getCalculatedValues(filterMASignalBullish(saveResults),1,'MABull'))
        scanResults.append(getCalculatedValues(filterMASignalBearish(saveResults),1,'MABear'))
        scanResults.append(getCalculatedValues(filterMASignalBullCross(saveResults),1,'BullCross'))
        scanResults.append(getCalculatedValues(filterMASignalBearCross(saveResults),1,'BearCross'))
        scanResults.append(getCalculatedValues(filterMASignalSupport(saveResults),1,'MASupprt'))
        scanResults.append(getCalculatedValues(filterMASignalResist(saveResults),1,'MARst'))
        scanResults.append(getCalculatedValues(filterVolumeLessThan25(saveResults),1,'Vol<2.5'))
        scanResults.append(getCalculatedValues(filterVolumeMoreThan25(saveResults),1,'Vol>=2.5'))
        scanResults.append(getCalculatedValues(filterConsolidating10Percent(saveResults),1,'Cons.<=10'))
        scanResults.append(getCalculatedValues(filterConsolidatingMore10Percent(saveResults),1,'Cons.>10'))
        df = pd.DataFrame(scanResults)
        print(tabulate(df, headers="keys", tablefmt="grid"))

def getCalculatedValues(df, period,key):
    ltpSum1ShareEach = round(df['LTP'].sum(),2)
    tdySum1ShareEach= round(df['LTPTdy'].sum(),2)
    growthSum1ShareEach= round(df['Growth'].sum(),2)
    percentGrowth = round(100*growthSum1ShareEach/ltpSum1ShareEach,2)
    growth10k = round(10000*(1+0.01*percentGrowth),2)
    return {'ScanType':key,
            f'{period}D-PFV':tdySum1ShareEach,
            f'{period}D-PFG':percentGrowth if tdySum1ShareEach != 0 else '-',
            f'{period}D-Go10k':growth10k if tdySum1ShareEach != 0 else '-',
            }
    
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