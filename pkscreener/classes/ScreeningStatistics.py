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

import math
import sys
import warnings
import datetime
import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd

from sys import float_info as sflt
import pkscreener.classes.Utility as Utility
from pkscreener import Imports
from pkscreener.classes.Pktalib import pktalib
from PKNSETools.morningstartools import Stock

if sys.version_info >= (3, 11):
    import advanced_ta as ata

# from sklearn.preprocessing import StandardScaler
if Imports["scipy"]:
    from scipy.stats import linregress

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.SuppressOutput import SuppressOutput
# from PKDevTools.classes.log import measure_time

# Exception for only downloading stock data and not screening
class DownloadDataOnly(Exception):
    pass


# Exception for stocks which are not newly listed when screening only for Newly Listed
class NotNewlyListed(Exception):
    pass


# Exception for stocks which are not stage two
class NotAStageTwoStock(Exception):
    pass

# Exception for LTP not being in the range as per config
class LTPNotInConfiguredRange(Exception):
    pass

# Exception for stocks which are low in volume as per configuration of 'minimumVolume'
class NotEnoughVolumeAsPerConfig(Exception):
    pass


# Exception for newly listed stocks with candle nos < daysToLookback
class StockDataNotAdequate(Exception):
    pass


# This Class contains methods for stock analysis and screening validation
class ScreeningStatistics:
    def __init__(self, configManager, default_logger) -> None:
        self.configManager = configManager
        self.default_logger = default_logger

    # Find stocks that have broken through 52 week high.
    def find52WeekHighBreakout(self, df):
        # https://chartink.com/screener/52-week-low-breakout
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["High"].iloc[0]
        last1Week = data.head(one_week)
        last2Week = data.head(2 * one_week)
        previousWeek = last2Week.tail(one_week)
        full52Week = data.head(50 * one_week)
        last1WeekHigh = last1Week["High"].max()
        previousWeekHigh = previousWeek["High"].max()
        full52WeekHigh = full52Week["High"].max()
        return (
            (recent >= full52WeekHigh)
            or (last1WeekHigh >= max(full52WeekHigh, last1WeekHigh))
            or (
                last1WeekHigh
                >= previousWeekHigh
                >= max(full52WeekHigh, previousWeekHigh)
            )
        )

    #@measure_time
    # Find stocks' 52 week high/low.
    def find52WeekHighLow(self, df, saveDict, screenDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        week_52 = one_week * 50  # Considering holidays etc as well of 10 days
        full52Week = data.head(week_52 + 1).tail(week_52+1)
        recentHigh = data.head(1)["High"].iloc[0]
        recentLow = data.head(1)["Low"].iloc[0]
        full52WeekHigh = full52Week["High"].max()
        full52WeekLow = full52Week["Low"].min()

        saveDict["52Wk H"] = "{:.2f}".format(full52WeekHigh)
        saveDict["52Wk L"] = "{:.2f}".format(full52WeekLow)
        if recentHigh >= full52WeekHigh:
            highColor = colorText.GREEN
        elif recentHigh >= 0.9 * full52WeekHigh:
            highColor = colorText.WARN
        else:
            highColor = colorText.FAIL
        if recentLow <= full52WeekLow:
            lowColor = colorText.FAIL
        elif recentLow <= 1.1 * full52WeekLow:
            lowColor = colorText.WARN
        else:
            lowColor = colorText.GREEN
        screenDict[
            "52Wk H"
        ] = f"{highColor}{str('{:.2f}'.format(full52WeekHigh))}{colorText.END}"
        screenDict[
            "52Wk L"
        ] = f"{lowColor}{str('{:.2f}'.format(full52WeekLow))}{colorText.END}"

    # Find stocks that have broken through 52 week low.
    def find52WeekLowBreakout(self, df):
        # https://chartink.com/screener/52-week-low-breakout
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["Low"].iloc[0]
        last1Week = data.head(one_week)
        last2Week = data.head(2 * one_week)
        previousWeek = last2Week.tail(one_week)
        full52Week = data.head(50 * one_week)
        last1WeekLow = last1Week["Low"].min()
        previousWeekLow = previousWeek["Low"].min()
        full52WeekLow = full52Week["Low"].min()
        return (
            (recent <= full52WeekLow)
            or (last1WeekLow <= min(full52WeekLow, last1WeekLow))
            or (last1WeekLow <= previousWeekLow <= min(full52WeekLow, previousWeekLow))
        )

        # Find stocks that have broken through 52 week low.

    def find10DaysLowBreakout(self, df):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["Low"].iloc[0]
        last1Week = data.head(one_week)
        last2Week = data.head(2 * one_week)
        previousWeek = last2Week.tail(one_week)
        last1WeekLow = last1Week["Low"].min()
        previousWeekLow = previousWeek["Low"].min()
        return (recent <= min(previousWeekLow, last1WeekLow)) and (
            last1WeekLow <= previousWeekLow
        )

        # Find stocks that have broken through 52 week low.

    def findAroonBullishCrossover(self, df):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        period = 14
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        aroondf = pktalib.Aroon(data["High"], data["Low"], period)
        recent = aroondf.tail(1)
        up = recent[f"AROONU_{period}"].iloc[0]
        down = recent[f"AROOND_{period}"].iloc[0]
        return up > down
    
    def non_zero_range(self, high: pd.Series, low: pd.Series) -> pd.Series:
        """Returns the difference of two series and adds epsilon to any zero values.  This occurs commonly in crypto data when 'high' = 'low'."""
        diff = high - low
        if diff.eq(0).any().any():
            diff += sflt.epsilon
        return diff
    
    # Find accurate breakout value
    def findBreakingoutNow(self, df, fullData, saveDict, screenDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        reversedData = fullData[::-1].copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        recentCandleHeight = self.getCandleBodyHeight(recent)
        if len(data) < 11 or recentCandleHeight <= 0:
            return False
        totalCandleHeight = 0
        candle = 0
        while candle < 10:
            candle += 1
            candleHeight = abs(self.getCandleBodyHeight(data[candle:]))
            totalCandleHeight += candleHeight

        reversedData.loc[:,'BBands-U'], reversedData.loc[:,'BBands-M'], reversedData.loc[:,'BBands-L'] = pktalib.BBANDS(reversedData["Close"], 20)
        reversedData = reversedData[::-1]
        recents = reversedData.head(6)
        ulr = self.non_zero_range(recents.loc[:,'BBands-U'], recents.loc[:,'BBands-L'])
        maxOfLast5Candles = ulr.tail(5).max()
        # bandwidth = 100 * ulr / recents.loc[:,'BBands-M']
        # percent = self.non_zero_range(recents.loc[:,'Close'], recents.loc[:,'BBands-L']) / ulr
        saveDict["bbands_ulr_ratio_max5"] = round(ulr.iloc[0]/maxOfLast5Candles,2) #percent.iloc[0]
        screenDict["bbands_ulr_ratio_max5"] = saveDict["bbands_ulr_ratio_max5"]
        # saveDict["bbands_bandwidth"] = bandwidth.iloc[0]
        # screenDict["bbands_bandwidth"] = saveDict["bbands_bandwidth"]
        # saveDict["bbands_ulr"] = ulr.iloc[0]
        # screenDict["bbands_ulr"] = saveDict["bbands_ulr"]

        return (
            recentCandleHeight > 0
            and totalCandleHeight > 0
            and (recentCandleHeight >= 3 * (float(totalCandleHeight / candle)))
        )

    #@measure_time
    # Find accurate breakout value
    def findBreakoutValue(
        self, df, screenDict, saveDict, daysToLookback, alreadyBrokenout=False
    ):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        data = data[1:]
        maxHigh = round(data.describe()["High"]["max"], 2)
        maxClose = round(data.describe()["Close"]["max"], 2)
        recentClose = round(recent["Close"].iloc[0], 2)
        if np.isnan(maxClose) or np.isnan(maxHigh):
            saveDict["Breakout"] = "BO: 0 R: 0"
            screenDict["Breakout"] = (
                colorText.BOLD + colorText.WARN + "BO: 0 R: 0" + colorText.END
            )
            # self.default_logger.info(
            #     f'For Stock:{saveDict["Stock"]}, the breakout is unknown because max-high ({maxHigh}) or max-close ({maxClose}) are not defined.'
            # )
            return False
        if maxHigh > maxClose:
            if (maxHigh - maxClose) <= (maxHigh * 2 / 100):
                saveDict["Breakout"] = "BO: " + str(maxClose) + " R: " + str(maxHigh)
                if recentClose >= maxClose:
                    screenDict["Breakout"] = (
                        colorText.BOLD
                        + colorText.GREEN
                        + "BO: "
                        + str(maxClose)
                        + colorText.END
                        + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                        + " R: "
                        + str(maxHigh)
                        + colorText.END
                    )
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, has a breakout because max-high ({maxHigh}) >= max-close ({maxClose})'
                    # )
                    return True and alreadyBrokenout and self.getCandleType(recent)
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, does not have a breakout yet because max-high ({maxHigh}) < max-close ({maxClose})'
                # )
                screenDict["Breakout"] = (
                    colorText.BOLD
                    + colorText.FAIL
                    + "BO: "
                    + str(maxClose)
                    + colorText.END
                    + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                    + " R: "
                    + str(maxHigh)
                    + colorText.END
                )
                return not alreadyBrokenout
            noOfHigherShadows = len(data[data.High > maxClose])
            if daysToLookback / noOfHigherShadows <= 3:
                saveDict["Breakout"] = "BO: " + str(maxHigh) + " R: 0"
                if recentClose >= maxHigh:
                    screenDict["Breakout"] = (
                        colorText.BOLD
                        + colorText.GREEN
                        + "BO: "
                        + str(maxHigh)
                        + " R: 0"
                        + colorText.END
                    )
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) >= max-high ({maxHigh})'
                    # )
                    return True and alreadyBrokenout and self.getCandleType(recent)
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, does not have a breakout yet because recent-close ({recentClose}) < max-high ({maxHigh})'
                # )
                screenDict["Breakout"] = (
                    colorText.BOLD
                    + colorText.FAIL
                    + "BO: "
                    + str(maxHigh)
                    + " R: 0"
                    + colorText.END
                )
                return not alreadyBrokenout
            saveDict["Breakout"] = "BO: " + str(maxClose) + " R: " + str(maxHigh)
            if recentClose >= maxClose:
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) >= max-close ({maxClose})'
                # )
                screenDict["Breakout"] = (
                    colorText.BOLD
                    + colorText.GREEN
                    + "BO: "
                    + str(maxClose)
                    + colorText.END
                    + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                    + " R: "
                    + str(maxHigh)
                    + colorText.END
                )
                return True and alreadyBrokenout and self.getCandleType(recent)
            # self.default_logger.info(
            #     f'Stock:{saveDict["Stock"]}, does not have a breakout yet because recent-close ({recentClose}) < max-high ({maxHigh})'
            # )
            screenDict["Breakout"] = (
                colorText.BOLD
                + colorText.FAIL
                + "BO: "
                + str(maxClose)
                + colorText.END
                + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                + " R: "
                + str(maxHigh)
                + colorText.END
            )
            return not alreadyBrokenout
        else:
            saveDict["Breakout"] = "BO: " + str(maxClose) + " R: 0"
            if recentClose >= maxClose:
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) >= max-close ({maxClose})'
                # )
                screenDict["Breakout"] = (
                    colorText.BOLD
                    + colorText.GREEN
                    + "BO: "
                    + str(maxClose)
                    + " R: 0"
                    + colorText.END
                )
                return True and alreadyBrokenout and self.getCandleType(recent)
            # self.default_logger.info(
            #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) < max-close ({maxClose})'
            # )
            screenDict["Breakout"] = (
                colorText.BOLD
                + colorText.FAIL
                + "BO: "
                + str(maxClose)
                + " R: 0"
                + colorText.END
            )
            return not alreadyBrokenout

    # Find stocks that are bullish intraday: RSI crosses 55, Macd Histogram positive, price above EMA 10
    def findBullishIntradayRSIMACD(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["RSI12"] = pktalib.RSI(data["Close"], 12)
        data["EMA10"] = pktalib.EMA(data["Close"], 10)
        data["EMA200"] = pktalib.EMA(data["Close"], 200)
        macd = pktalib.MACD(data["Close"], 10, 18, 9)[2].tail(1)
        recent = data.tail(1)
        cond1 = recent["RSI12"].iloc[0] > 55
        cond2 = cond1 and (macd.iloc[:1][0] > 0)
        cond3 = cond2 and (recent["Close"].iloc[0] > recent["EMA10"].iloc[0])
        cond4 = cond3 and (recent["Close"].iloc[0] > recent["EMA200"].iloc[0])
        return cond4
    
    def findNR4Day(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        # https://chartink.com/screener/nr4-daily-today
        if data.tail(1)["Volume"].iloc[0] <= 50000:
            return False
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["SMA10"] = pktalib.SMA(data["Close"], 10)
        data["SMA50"] = pktalib.SMA(data["Close"], 50)
        data["SMA200"] = pktalib.SMA(data["Close"], 200)
        recent = data.tail(5)
        recent = recent[::-1]
        cond1 = (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[1] - recent["Low"].iloc[1]
        )
        cond2 = cond1 and (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[2] - recent["Low"].iloc[2]
        )
        cond3 = cond2 and (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[3] - recent["Low"].iloc[3]
        )
        cond4 = cond3 and (recent["High"].iloc[0] - recent["Low"].iloc[0]) < (
            recent["High"].iloc[4] - recent["Low"].iloc[4]
        )
        cond5 = cond4 and (recent["SMA10"].iloc[0] > recent["SMA50"].iloc[0])
        cond6 = cond5 and (recent["SMA50"].iloc[0] > recent["SMA200"].iloc[0])
        return cond6

    # Find potential breakout stocks
    # This scanner filters stocks whose current close price + 5% is higher
    # than the highest High price in past 200 candles and the maximum high
    # in the previous 30 candles is lower than the highest high made in the
    # previous 200 candles, starting from the previous 30th candle. At the
    # same time the current candle volume is higher than 200 SMA of volume.
    def findPotentialBreakout(self, df, screenDict, saveDict, daysToLookback):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data.head(231)
        recent = data.head(1)
        recentVolume = recent["Volume"].iloc[0]
        recentClose = round(recent["Close"].iloc[0] * 1.05, 2)
        highestHigh200 = round(data.head(201).tail(200).describe()["High"]["max"], 2)
        highestHigh30 = round(data.head(31).tail(30).describe()["High"]["max"], 2)
        highestHigh200From30 = round(data.tail(200).describe()["High"]["max"], 2)
        data = data.head(200)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        vol = pktalib.SMA(data["Volume"],timeperiod=200)
        data["SMA200V"] = vol
        recent = data.tail(1)
        sma200v = recent["SMA200V"].iloc[0]
        if (
            np.isnan(recentClose)
            or np.isnan(highestHigh200)
            or np.isnan(highestHigh30)
            or np.isnan(highestHigh200From30)
            or np.isnan(recentVolume)
            or np.isnan(sma200v)
        ):
            return False
        if (
            (recentClose > highestHigh200)
            and (highestHigh30 < highestHigh200From30)
            and (recentVolume > sma200v)
        ):
            saveDict["Breakout"] = saveDict["Breakout"] + "(Potential)"
            screenDict["Breakout"] = screenDict["Breakout"] + (
                colorText.BOLD + colorText.GREEN + " (Potential)" + colorText.END
            )
            return True
        return False

    # Find stock reversing at given MA
    def findReversalMA(self, df, screenDict, saveDict, maLength, percentage=0.02):
        data = df.copy()
        maRange = [10, 20, 50, 200]
        results = []
        hasReversals = False
        data = data[::-1]
        saved = self.findCurrentSavedValue(screenDict,saveDict, "MA-Signal")
        for maLength in maRange:
            dataCopy = data
            if self.configManager.useEMA:
                maRev = pktalib.EMA(dataCopy["Close"], timeperiod=maLength)
            else:
                maRev = pktalib.MA(dataCopy["Close"], timeperiod=maLength)
            try:
                dataCopy.drop("maRev", axis=1, inplace=True, errors="ignore")
            except Exception:# pragma: no cover
                pass
            dataCopy.insert(len(dataCopy.columns), "maRev", maRev)
            dataCopy = dataCopy[::-1].head(3)
            if (
                dataCopy.equals(
                    dataCopy[
                        (
                            dataCopy.Close
                            >= (dataCopy.maRev - (dataCopy.maRev * percentage))
                        )
                        & (
                            dataCopy.Close
                            <= (dataCopy.maRev + (dataCopy.maRev * percentage))
                        )
                    ]
                )
                and dataCopy.head(1)["Close"].iloc[0]
                >= dataCopy.head(1)["maRev"].iloc[0]
            ):
                hasReversals = True
                results.append(str(maLength))
        if hasReversals:
            screenDict["MA-Signal"] = (
                saved[0] 
                + colorText.BOLD
                + colorText.GREEN
                + f"Reversal-[{','.join(results)}]MA"
                + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + f"Reversal-[{','.join(results)}]MA"
        return hasReversals

    def findCurrentSavedValue(self, screenDict, saveDict, key):
        existingScreen = screenDict.get(key)
        existingSave = saveDict.get(key)
        existingScreen = f"{existingScreen}, " if (existingScreen is not None and len(existingScreen) > 0) else ""
        existingSave = f"{existingSave}, " if (existingSave is not None and len(existingSave) > 0) else ""
        return existingScreen, existingSave

    # @measure_time
    def findBbandsSqueeze(self,fullData, screenDict, saveDict, filter=4):
        """
        The TTM Squeeze indicator measures the relationship between the 
        Bollinger Bands and Keltner's Channel. When the volatility increases, 
        so does the distance between the bands, and conversely, when the 
        volatility declines, the distance also decreases. The Squeeze indicator 
        finds sections of the Bollinger Bands study which fall inside the 
        Keltner's Channels.
        
        At the moment this squeeze happens, a price breakout from the upper 
        Bollinger Band would indicate the possibility of an uptrend in the 
        future. This is backed by the fact that once the price starts breaking 
        out of the bands, it would mean a relaxation of the squeeze and the 
        possibility of high market volatility and price movement in the future. 
        Similarly, a price breakout from the lower Bollinger Band after a squeeze 
        would indicate the possibility of a downtrend in the future and an 
        increased market volatility in the same direction. When the market 
        finishes a move, the indicator turns off, which corresponds to bands 
        having pushed well outside the range of Keltner's Channels.
        """
        if fullData is None or len(fullData) < 20:
            return False
        oldestRecordsFirst_df = fullData.head(30).copy()
        latestRecordsFirst_df = oldestRecordsFirst_df[::-1].tail(30)
        latestRecordsFirst_df = latestRecordsFirst_df.fillna(0)
        latestRecordsFirst_df = latestRecordsFirst_df.replace([np.inf, -np.inf], 0)
        # Bollinger bands
        latestRecordsFirst_df.loc[:,'BBands-U'], latestRecordsFirst_df.loc[:,'BBands-M'], latestRecordsFirst_df.loc[:,'BBands-L'] = pktalib.BBANDS(latestRecordsFirst_df["Close"], 20)
        # compute Keltner's channel
        latestRecordsFirst_df['low_kel'], latestRecordsFirst_df['upp_kel'] = pktalib.KeltnersChannel(latestRecordsFirst_df["High"], latestRecordsFirst_df["Low"],latestRecordsFirst_df["Close"],20)
        # squeeze indicator
        def in_squeeze(df):
            return df['low_kel'] < df['BBands-L'] < df['BBands-U'] < df['upp_kel']

        latestRecordsFirst_df['squeeze'] = latestRecordsFirst_df.apply(in_squeeze, axis=1)

        # Let's review just the previous 3 candles including today (at the end)
        latestRecordsFirst_df = latestRecordsFirst_df.tail(3)
        # stock is coming out of the squeeze
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        candle3Sqz = latestRecordsFirst_df.iloc[-3]["squeeze"]
        candle1Sqz = latestRecordsFirst_df.iloc[-1]["squeeze"]
        candle2Sqz = latestRecordsFirst_df.iloc[-2]["squeeze"]
        if candle3Sqz and not candle1Sqz:
            # 3rd candle from the most recent one was in squeeze but the most recent one is not.
            if filter not in [1,3,4]: # Buy/Sell/All
                return False
            # decide which action to take by comparing distances                
            distance_to_upper = abs(latestRecordsFirst_df['BBands-U'].values[-1] - latestRecordsFirst_df['Close'].values[-1])
            distance_to_lower = abs(latestRecordsFirst_df['BBands-L'].values[-1] - latestRecordsFirst_df['Close'].values[-1])
            
            action = False
            if distance_to_upper < distance_to_lower:
                if filter not in [1,4]: # Buy/All
                    return False
                action = True
            elif filter not in [3,4]: # Sell/All
                return False
            screenDict["Pattern"] = saved[0] + colorText.BOLD + (colorText.GREEN if action else colorText.FAIL) + f"BBands-SQZ-{'Buy' if action else 'Sell'}" + colorText.END
            saveDict["Pattern"] = saved[1] + f"TTM-SQZ-{'Buy' if action else 'Sell'}"
            return True
        elif candle3Sqz and candle2Sqz and candle1Sqz:
            # Last 3 candles in squeeze
            if filter not in [2,4]: # SqZ/All
                return False
            screenDict["Pattern"] = f'{saved[0]}{colorText.BOLD}{colorText.WARN}TTM-SQZ{colorText.END}'
            saveDict["Pattern"] = f'{saved[1]}TTM-SQZ'
            return True
        return False
        
    #@measure_time
    # Find out trend for days to lookback
    def findTrend(self, df, screenDict, saveDict, daysToLookback=None, stockName=""):
        if df is None or len(df) == 0:
            return "Unknown"
        data = df.copy()
        if daysToLookback is None:
            daysToLookback = self.configManager.daysToLookback
        data = data.head(daysToLookback)
        data = data[::-1]
        data = data.set_index(np.arange(len(data)))
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        saved = self.findCurrentSavedValue(screenDict,saveDict,"Trend")
        try:
            with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
                data["tops"] = data["Close"].iloc[
                    list(
                        pktalib.argrelextrema(
                            np.array(data["Close"]), np.greater_equal, order=1
                        )[0]
                    )
                ]
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)

            try:
                # if len(data) < daysToLookback:
                #     self.default_logger.debug(data)
                #     raise StockDataNotAdequate
                data = data.replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna()
                if len(data["tops"][data.tops > 0]) > 1:
                    slope = np.polyfit(
                        data.index[data.tops > 0], data["tops"][data.tops > 0], 1
                    )[0]
                else:
                    slope = 0
            except np.linalg.LinAlgError as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                screenDict["Trend"] = (
                    saved[0] + colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Unknown"
                return saveDict["Trend"]
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                slope, _ = 0, 0
            angle = np.rad2deg(np.arctan(slope))
            if angle == 0:
                screenDict["Trend"] = (
                    saved[0] + colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Unknown"
            elif angle <= 30 and angle >= -30:
                screenDict["Trend"] = (
                    saved[0] + colorText.BOLD + colorText.WARN + "Sideways" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Sideways"
            elif angle >= 30 and angle < 61:
                screenDict["Trend"] = (
                    saved[0] + colorText.BOLD + colorText.GREEN + "Weak Up" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Weak Up"
            elif angle >= 60:
                screenDict["Trend"] = (
                    saved[0] + colorText.BOLD + colorText.GREEN + "Strong Up" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Strong Up"
            elif angle <= -30 and angle > -61:
                screenDict["Trend"] = (
                    saved[0] + colorText.BOLD + colorText.FAIL + "Weak Down" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Weak Down"
            elif angle < -60:
                screenDict["Trend"] = (
                    saved[0] + colorText.BOLD + colorText.FAIL + "Strong Down" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Strong Down"
        except np.linalg.LinAlgError as e: # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            screenDict["Trend"] = (
                saved[0] + colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
            )
            saveDict["Trend"] = saved[1] + "Unknown"
        return saveDict["Trend"]

    # Find stocks approching to long term trendlines
    def findTrendlines(self, df, screenDict, saveDict, percentage=0.05):
        # period = int("".join(c for c in self.configManager.period if c.isdigit()))
        # if len(data) < period:
        #     return False
        data = df.copy()
        data = data[::-1]
        data["Number"] = np.arange(len(data)) + 1
        data_low = data.copy()
        points = 30

        """ Ignoring the Resitance for long-term purpose
        while len(data_high) > points:
            slope, intercept, r_value, p_value, std_err = linregress(x=data_high['Number'], y=data_high['High'])
            data_high = data_high.loc[data_high['High'] > slope * data_high['Number'] + intercept]
        slope, intercept, r_value, p_value, std_err = linregress(x=data_high['Number'], y=data_high['Close'])
        data['Resistance'] = slope * data['Number'] + intercept
        """

        while len(data_low) > points:
            try:
                slope, intercept, r_value, p_value, std_err = linregress(
                    x=data_low["Number"], y=data_low["Low"]
                )
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                continue
            data_low = data_low.loc[
                data_low["Low"] < slope * data_low["Number"] + intercept
            ]

        slope, intercept, r_value, p_value, std_err = linregress(
            x=data_low["Number"], y=data_low["Close"]
        )
        data["Support"] = slope * data["Number"] + intercept
        now = data.tail(1)

        limit_upper = now["Support"].iloc[0] + (now["Support"].iloc[0] * percentage)
        limit_lower = now["Support"].iloc[0] - (now["Support"].iloc[0] * percentage)
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        if limit_lower < now["Close"].iloc[0] < limit_upper and slope > 0.15:
            screenDict["Pattern"] = (
                saved[0] + colorText.BOLD + colorText.GREEN + "Trendline-Support" + colorText.END
            )
            saveDict["Pattern"] = saved[1] + "Trendline-Support"
            return True

        """ Plots for debugging
        import matplotlib.pyplot as plt
        fig, ax1 = plt.subplots(figsize=(15,10))
        color = 'tab:green'
        xdate = [x.date() for x in data.index]
        ax1.set_xlabel('Date', color=color)
        ax1.plot(xdate, data.Close, label="close", color=color)
        ax1.tick_params(axis='x', labelcolor=color)

        ax2 = ax1.twiny() # ax2 and ax1 will have common y axis and different x axis, twiny
        ax2.plot(data.Number, data.Resistance, label="Res")
        ax2.plot(data.Number, data.Support, label="Sup")

        plt.legend()
        plt.grid()
        plt.show()
        """
        return False

    # @measure_time
    def findUptrend(self, df, screenDict, saveDict, testing, stock,onlyMF=False,hostData=None):
        # shouldProceed = True
        isUptrend = False
        isDowntrend = False
        is50DMAUptrend = False
        is50DMADowntrend = False
        decision = ""
        dma50decision = ""
        fairValue = 0
        fairValueDiff = 0
        # if df is None or len(df) < 220 or testing:
        #     shouldProceed = False
        if df is not None:
            try:
                data = df.copy()
                data = data[::-1]
                today_sma = pktalib.SMA(data["Close"], timeperiod=50)
                sma_minus9 = pktalib.SMA(data.head(len(data)-9)["Close"], timeperiod=50)
                sma_minus14 = pktalib.SMA(data.head(len(data)-14)["Close"], timeperiod=50)
                sma_minus20 = pktalib.SMA(data.head(len(data)-20)["Close"], timeperiod=50)
                today_lma = pktalib.SMA(data["Close"], timeperiod=200)
                lma_minus20 = pktalib.SMA(data.head(len(data)-20)["Close"], timeperiod=200)
                lma_minus80 = pktalib.SMA(data.head(len(data)-80)["Close"], timeperiod=200)
                lma_minus100 = pktalib.SMA(data.head(len(data)-100)["Close"], timeperiod=200)
                today_lma = today_lma.iloc[len(today_lma)-1] if today_lma is not None else 0
                lma_minus20 = lma_minus20.iloc[len(lma_minus20)-1] if lma_minus20 is not None else 0
                lma_minus80 = lma_minus80.iloc[len(lma_minus80)-1] if lma_minus80 is not None else 0
                lma_minus100 = lma_minus100.iloc[len(lma_minus100)-1] if lma_minus100 is not None else 0
                today_sma = today_sma.iloc[len(today_sma)-1] if today_sma is not None else 0
                sma_minus9 = sma_minus9.iloc[len(sma_minus9)-1] if sma_minus9 is not None else 0
                sma_minus14 = sma_minus14.iloc[len(sma_minus14)-1] if sma_minus14 is not None else 0
                sma_minus20 = sma_minus20.iloc[len(sma_minus20)-1] if sma_minus20 is not None else 0
                isUptrend = (today_lma > lma_minus20) or (today_lma > lma_minus80) or (today_lma > lma_minus100)
                isDowntrend = (today_lma < lma_minus20) and (today_lma < lma_minus80) and (today_lma < lma_minus100)
                is50DMAUptrend = (today_sma > sma_minus9) or (today_sma > sma_minus14) or (today_sma > sma_minus20)
                is50DMADowntrend = (today_sma < sma_minus9) and (today_sma < sma_minus14) and (today_sma < sma_minus20)
            except Exception:  # pragma: no cover
                # self.default_logger.debug(e, exc_info=True)
                pass
        decision = 'T:▲' if isUptrend else ('T:▼' if isDowntrend else '')
        dma50decision = 't:▲' if is50DMAUptrend else ('t:▼' if is50DMADowntrend else '')
        mf_inst_ownershipChange = 0
        change_millions =""
        try:
            mf_inst_ownershipChange = self.getMutualFundStatus(stock,onlyMF=onlyMF,hostData=hostData,force=(hostData is None or hostData.empty or not ("MF" in hostData.columns or "FII" in hostData.columns)))
            roundOff = 2
            millions = round(mf_inst_ownershipChange/1000000,roundOff)
            while float(millions) == 0 and roundOff <=5:
                roundOff +=1
                millions = round(mf_inst_ownershipChange/1000000,roundOff)
            change_millions = f"({millions}M)"
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            pass
        try:
            #Let's get the fair value, either saved or fresh from service
            fairValue = self.getFairValue(stock,hostData,force=(hostData is None or hostData.empty or "FairValue" not in hostData.columns))
            if fairValue is not None and fairValue != 0:
                ltp = saveDict["LTP"]
                fairValueDiff = round(fairValue - ltp,0)
                saveDict["FairValue"] = str(fairValue)
                saveDict["FVDiff"] = fairValueDiff
                screenDict["FVDiff"] = fairValueDiff
                screenDict["FairValue"] = (colorText.GREEN if fairValue >= ltp else colorText.FAIL) + saveDict["FairValue"] + colorText.END
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            pass
        mf = ""
        mfs = ""
        if mf_inst_ownershipChange > 0:
            mf = f"MFI:▲ {change_millions}"
            mfs = colorText.GREEN + mf + colorText.END
        elif mf_inst_ownershipChange < 0:
            mf = f"MFI:▼ {change_millions}"
            mfs = colorText.FAIL + mf + colorText.END

        saved = self.findCurrentSavedValue(screenDict,saveDict,"Trend")
        decision_scr = (colorText.GREEN if isUptrend else (colorText.FAIL if isDowntrend else colorText.WARN)) + f"{decision}" + colorText.END
        dma50decision_scr = (colorText.GREEN if is50DMAUptrend else (colorText.FAIL if is50DMADowntrend else colorText.WARN)) + f"{dma50decision}" + colorText.END
        saveDict["Trend"] = f"{saved[1]} {decision} {dma50decision} {mf}"
        screenDict["Trend"] = f"{saved[0]} {decision_scr} {dma50decision_scr} {mfs}"
        saveDict["MFI"] = mf_inst_ownershipChange
        screenDict["MFI"] = mf_inst_ownershipChange
        return isUptrend, mf_inst_ownershipChange, fairValueDiff
    
    # Private method to find candle type
    # True = Bullish, False = Bearish
    def getCandleType(self, dailyData):
        return bool(dailyData["Close"].iloc[0] >= dailyData["Open"].iloc[0])

    def getCandleBodyHeight(self, dailyData):
        bodyHeight = dailyData["Close"].iloc[0] - dailyData["Open"].iloc[0]
        return bodyHeight

    def getFairValue(self, stock, hostData=None, force=False):
        if hostData is None or len(hostData) < 1:
            hostData = pd.DataFrame()
        # Let's look for fair values
        fairValue = 0
        if "FairValue" in hostData.columns and PKDateUtilities.currentDateTime().weekday() <= 4:
            try:
                fairValue = hostData[hostData.index[-1],"FairValue"]
            except (KeyError,IndexError):
                    pass
        else:
            if PKDateUtilities.currentDateTime().weekday() >= 5 or force:
                security = None
                # Refresh each saturday or sunday or when not found in saved data
                try:
                    security = Stock(stock)
                except ValueError: # pragma: no cover
                    # We did not find the stock? It's okay. Move on to the next one.
                    pass
                if security is not None:
                    fv = security.fairValue()
                    if fv is not None:
                        try:
                            fvResponseValue = fv["latestFairValue"]
                            if fvResponseValue is not None:
                                fairValue = float(fvResponseValue)
                        except: # pragma: no cover
                            pass
                            # self.default_logger.debug(f"{e}\nResponse:fv:\n{fv}", exc_info=True)
                    fairValue = round(float(fairValue),1)
                    try:
                        hostData.loc[hostData.index[-1],"FairValue"] = fairValue
                    except (KeyError,IndexError):
                        pass
        return fairValue

    def getMutualFundStatus(self, stock,onlyMF=False, hostData=None, force=False):
        if hostData is None or len(hostData) < 1:
            hostData = pd.DataFrame()
        
        netChangeMF = 0
        netChangeInst = 0
        latest_mfdate = None
        latest_instdate = None
        needsFreshUpdate = True
        lastDayLastMonth = PKDateUtilities.last_day_of_previous_month(PKDateUtilities.currentDateTime())
        if hostData is not None and len(hostData) > 0:
            if "MF" in hostData.columns or "FII" in hostData.columns:
                try:
                    netChangeMF = hostData[hostData.index[-1],"MF"]
                except (KeyError,IndexError):
                    pass
                try:
                    netChangeInst = hostData[hostData.index[-1],"FII"]
                except (KeyError,IndexError):
                    pass
                try:
                    latest_mfdate = hostData[hostData.index[-1],"MF_Date"]
                except (KeyError,IndexError):
                    pass
                try:
                    latest_instdate = hostData[hostData.index[-1],"FII_Date"]
                except (KeyError,IndexError):
                    pass
                if latest_mfdate is not None:
                    saved_mfdate = PKDateUtilities.dateFromYmdString(latest_mfdate.split("T")[0])
                else:
                    saved_mfdate = lastDayLastMonth - datetime.timedelta(1)
                if latest_instdate is not None:
                    saved_instdate = PKDateUtilities.dateFromYmdString(latest_instdate.split("T")[0])
                else:
                    saved_instdate = lastDayLastMonth - datetime.timedelta(1)
                today = PKDateUtilities.currentDateTime()
                needsFreshUpdate = (saved_mfdate.date() < lastDayLastMonth.date()) and (saved_instdate.date() < lastDayLastMonth.date())
            else:
                needsFreshUpdate = True

        if needsFreshUpdate and force:
            netChangeMF, netChangeInst, latest_mfdate, latest_instdate = self.getFreshMFIStatus(stock)
            if netChangeMF is not None:
                try:
                    hostData.loc[hostData.index[-1],"MF"] = netChangeMF
                except (KeyError,IndexError):
                    pass
            else:
                netChangeMF = 0
            if latest_mfdate is not None:
                try:
                    hostData.loc[hostData.index[-1],"MF_Date"] = latest_mfdate
                except (KeyError,IndexError):
                    pass
            if netChangeInst is not None:
                try:
                    hostData.loc[hostData.index[-1],"FII"] = netChangeInst
                except (KeyError,IndexError):
                    pass
            else:
                netChangeInst = 0
            if latest_instdate is not None:
                try:
                    hostData.loc[hostData.index[-1],"FII_Date"] = latest_instdate
                except (KeyError,IndexError):
                    pass
        lastDayLastMonth = lastDayLastMonth.strftime("%Y-%m-%dT00:00:00.000")
        if onlyMF:
            return netChangeMF
        if latest_instdate == latest_mfdate:
            return (netChangeMF + netChangeInst)
        elif latest_mfdate == lastDayLastMonth:
            return netChangeMF
        elif latest_instdate == lastDayLastMonth:
            return netChangeInst
        else:
            # find the latest date
            if latest_mfdate is not None:
                latest_mfdate = PKDateUtilities.dateFromYmdString(latest_mfdate.split("T")[0])
            if latest_instdate is not None:
                latest_instdate = PKDateUtilities.dateFromYmdString(latest_instdate.split("T")[0])
            return netChangeMF if ((latest_mfdate is not None) and latest_mfdate > (latest_instdate if latest_instdate is not None else (latest_mfdate - datetime.timedelta(1)))) else netChangeInst

    def getFreshMFIStatus(self, stock):
        changeStatusDataMF = None
        changeStatusDataInst = None
        netChangeMF = 0
        netChangeInst = 0
        latest_mfdate = None
        latest_instdate = None
        security = None
        try:
            security = Stock(stock)
        except ValueError:
            # We did not find the stock? It's okay. Move on to the next one.
            pass
        if security is not None:
            try:
                changeStatusRowsMF = security.mutualFundOwnership(top=5)
                changeStatusRowsInst = security.institutionOwnership(top=5)
                changeStatusDataMF = security.mutualFundFIIChangeData(changeStatusRowsMF)
                changeStatusDataInst = security.mutualFundFIIChangeData(changeStatusRowsInst)
            except Exception as e:
                self.default_logger.debug(e, exc_info=True)
                # TypeError or ConnectionError because we could not find the stock or MFI data isn't available?
                pass
            lastDayLastMonth = PKDateUtilities.last_day_of_previous_month(PKDateUtilities.currentDateTime())
            lastDayLastMonth = lastDayLastMonth.strftime("%Y-%m-%dT00:00:00.000")
            if changeStatusDataMF is not None and len(changeStatusDataMF) > 0:
                df_groupedMF = changeStatusDataMF.groupby("date", sort=False)
                for mfdate, df_groupMF in df_groupedMF:
                    netChangeMF = df_groupMF["changeAmount"].sum()
                    latest_mfdate = mfdate
                    break
            if changeStatusDataInst is not None and len(changeStatusDataInst) > 0:
                df_groupedInst = changeStatusDataInst.groupby("date", sort=False)
                for instdate, df_groupInst in df_groupedInst:
                    if (latest_mfdate is not None and latest_mfdate == instdate) or (latest_mfdate is None) or (instdate == lastDayLastMonth):
                        netChangeInst = df_groupInst["changeAmount"].sum()
                        latest_instdate = instdate
                    break
        return netChangeMF,netChangeInst,latest_mfdate,latest_instdate


    def getNiftyPrediction(self, df):
        import warnings

        warnings.filterwarnings("ignore")
        data = df.copy()
        model, pkl = Utility.tools.getNiftyModel()
        if model is None or pkl is None:
            return 0, "Unknown", "Unknown"
        with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
            data = data[pkl["columns"]]
            ### v2 Preprocessing
            data["High"] = data["High"].pct_change() * 100
            data["Low"] = data["Low"].pct_change() * 100
            data["Open"] = data["Open"].pct_change() * 100
            data["Close"] = data["Close"].pct_change() * 100
            data = data.iloc[-1]
            ###
            data = pkl["scaler"].transform([data])
            pred = model.predict(data)[0]
        if pred > 0.5:
            outText = "BEARISH"
            out = (
                colorText.BOLD
                + colorText.FAIL
                + outText
                + colorText.END
                + colorText.BOLD
            )
            sug = "Hold your Short position!"
        else:
            outText = "BULLISH"
            out = (
                colorText.BOLD
                + colorText.GREEN
                + outText
                + colorText.END
                + colorText.BOLD
            )
            sug = "Stay Bullish!"
        if not PKDateUtilities.isClosingHour():
            print(
                colorText.BOLD
                + colorText.WARN
                + "Note: The AI prediction should be executed After 3 PM or Near to Closing time as the Prediction Accuracy is based on the Closing price!"
                + colorText.END
            )
        predictionText = "Market may Open {} next day! {}".format(out, sug)
        strengthText = "Probability/Strength of Prediction = {}%".format(
            Utility.tools.getSigmoidConfidence(pred[0])
        )
        print(
            colorText.BOLD
            + colorText.BLUE
            + "\n"
            + "[+] Nifty AI Prediction -> "
            + colorText.END
            + colorText.BOLD
            + predictionText
            + colorText.END
        )
        print(
            colorText.BOLD
            + colorText.BLUE
            + "\n"
            + "[+] Nifty AI Prediction -> "
            + colorText.END
            + strengthText
        )

        return pred, predictionText.replace(out, outText), strengthText

    def monitorFiveEma(self, fetcher, result_df, last_signal, risk_reward=3):
        col_names = ["High", "Low", "Close", "5EMA"]
        data_list = ["nifty_buy", "banknifty_buy", "nifty_sell", "banknifty_sell"]

        data_tuple = fetcher.fetchFiveEmaData()
        for cnt in range(len(data_tuple)):
            d = data_tuple[cnt]
            d["5EMA"] = pktalib.EMA(d["Close"], timeperiod=5)
            d = d[col_names]
            d = d.dropna().round(2)

            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                if "sell" in data_list[cnt]:
                    streched = d[(d.Low > d["5EMA"]) & (d.Low - d["5EMA"] > 0.5)]
                    streched["SL"] = streched.High
                    validate = d[
                        (d.Low.shift(1) > d["5EMA"].shift(1))
                        & (d.Low.shift(1) - d["5EMA"].shift(1) > 0.5)
                    ]
                    old_index = validate.index
                else:
                    mask = (d.High < d["5EMA"]) & (d["5EMA"] - d.High > 0.5)  # Buy
                    streched = d[mask]
                    streched["SL"] = streched.Low
                    validate = d.loc[mask.shift(1).fillna(False)]
                    old_index = validate.index
            tgt = pd.DataFrame(
                (
                    validate.Close.reset_index(drop=True)
                    - (
                        (
                            streched.SL.reset_index(drop=True)
                            - validate.Close.reset_index(drop=True)
                        )
                        * risk_reward
                    )
                ),
                columns=["Target"],
            )
            validate = pd.concat(
                [
                    validate.reset_index(drop=True),
                    streched["SL"].reset_index(drop=True),
                    tgt,
                ],
                axis=1,
            )
            validate = validate.tail(len(old_index))
            validate = validate.set_index(old_index)
            if "sell" in data_list[cnt]:
                final = validate[validate.Close < validate["5EMA"]].tail(1)
            else:
                final = validate[validate.Close > validate["5EMA"]].tail(1)

            if data_list[cnt] not in last_signal:
                last_signal[data_list[cnt]] = final
            elif data_list[cnt] in last_signal:
                try:
                    condition = last_signal[data_list[cnt]][0]["SL"][0]
                except KeyError as e: # pragma: no cover
                    self.default_logger.debug(e, exc_info=True)
                    condition = last_signal[data_list[cnt]]["SL"][0]
                # if last_signal[data_list[cnt]] is not final:          # Debug - Shows all conditions
                if len(final["SL"]) > 0 and condition != final["SL"].iloc[0]:
                    # Do something with results
                    try:
                        result_df = pd.concat(
                            [
                                result_df,
                                pd.DataFrame(
                                    [
                                        [
                                            colorText.BLUE
                                            + str(final.index[0])
                                            + colorText.END,
                                            colorText.BOLD
                                            + colorText.WARN
                                            + data_list[cnt].split("_")[0].upper()
                                            + colorText.END,
                                            (
                                                colorText.BOLD
                                                + colorText.FAIL
                                                + data_list[cnt].split("_")[1].upper()
                                                + colorText.END
                                            )
                                            if "sell" in data_list[cnt]
                                            else (
                                                colorText.BOLD
                                                + colorText.GREEN
                                                + data_list[cnt].split("_")[1].upper()
                                                + colorText.END
                                            ),
                                            colorText.FAIL
                                            + str(final.SL[0])
                                            + colorText.END,
                                            colorText.GREEN
                                            + str(final.Target[0])
                                            + colorText.END,
                                            f"1:{risk_reward}",
                                        ]
                                    ],
                                    columns=result_df.columns,
                                ),
                            ],
                            axis=0,
                        )
                        result_df.reset_index(drop=True, inplace=True)
                    except Exception as e:  # pragma: no cover
                        self.default_logger.debug(e, exc_info=True)
                        pass
                    # Then update
                    last_signal[data_list[cnt]] = [final]
        if result_df is not None:
            result_df.drop_duplicates(keep="last", inplace=True)
            result_df.sort_values(by="Time", inplace=True)
        return result_df[::-1]

    # Preprocess the acquired data
    def preprocessData(self, df, daysToLookback=None):
        data = df.copy()
        self.default_logger.info(f"Preprocessing data:\n{data.head(1)}\n")
        if daysToLookback is None:
            daysToLookback = self.configManager.daysToLookback
        if self.configManager.useEMA:
            sma = pktalib.EMA(data["Close"], timeperiod=50)
            lma = pktalib.EMA(data["Close"], timeperiod=200)
            ssma = pktalib.EMA(data["Close"], timeperiod=9)
            data.insert(len(data.columns), "SMA", sma)
            data.insert(len(data.columns), "LMA", lma)
            data.insert(len(data.columns), "SSMA", ssma)
        else:
            sma = pktalib.SMA(data["Close"], timeperiod=50)
            lma = pktalib.SMA(data["Close"], timeperiod=200)
            ssma = pktalib.SMA(data["Close"], timeperiod=9)
            data.insert(len(data.columns), "SMA", sma)
            data.insert(len(data.columns), "LMA", lma)
            data.insert(len(data.columns), "SSMA", ssma)
        vol = pktalib.SMA(data["Volume"], timeperiod=20)
        rsi = pktalib.RSI(data["Close"], timeperiod=14)
        data.insert(len(data.columns), "VolMA", vol)
        data.insert(len(data.columns), "RSI", rsi)
        cci = pktalib.CCI(data["High"], data["Low"], data["Close"], timeperiod=14)
        data.insert(len(data.columns), "CCI", cci)
        # len(data["Close"])
        fastk, fastd = pktalib.STOCHRSI(
            data["Close"], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0
        )
        data.insert(len(data.columns), "FASTK", fastk)
        data.insert(len(data.columns), "FASTD", fastd)
        data = data[::-1]  # Reverse the dataframe
        # data = data.fillna(0)
        # data = data.replace([np.inf, -np.inf], 0)
        fullData = data
        trimmedData = data.head(daysToLookback)
        return (fullData, trimmedData)

    # Validate if the stock is bullish in the short term
    def validate15MinutePriceVolumeBreakout(self, df):
        # https://chartink.com/screener/15-min-price-volume-breakout
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["SMA20"] = pktalib.SMA(data["Close"], 20)
        data["SMA20V"] = pktalib.SMA(data["Volume"], 20)
        data = data[
            ::-1
        ]  # Reverse the dataframe so that it's the most recent date first
        recent = data.head(3)
        cond1 = recent["Close"].iloc[0] > recent["Close"].iloc[1]
        cond2 = cond1 and (recent["Close"].iloc[0] > recent["SMA20"].iloc[0])
        cond3 = cond2 and (recent["Close"].iloc[1] > recent["High"].iloc[2])
        cond4 = cond3 and (recent["Volume"].iloc[0] > recent["SMA20V"].iloc[0])
        cond5 = cond4 and (recent["Volume"].iloc[1] > recent["SMA20V"].iloc[0])
        return cond5

    def validateBullishForTomorrow(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        # https://chartink.com/screener/bullish-for-tomorrow
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macdLine = pktalib.MACD(data["Close"], 12, 26, 9)[0].tail(3)
        macdSignal = pktalib.MACD(data["Close"], 12, 26, 9)[1].tail(3)
        macdHist = pktalib.MACD(data["Close"], 12, 26, 9)[2].tail(3)

        return (
            (macdHist.iloc[:1].iloc[0] < macdHist.iloc[:2].iloc[1])
            and (macdHist.iloc[:3].iloc[2] > macdHist.iloc[:2].iloc[1])
            and (
                (macdLine.iloc[:3].iloc[2] - macdSignal.iloc[:3].iloc[2])
                - (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1])
                >= 0.4
            )
            and (
                (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1])
                - (macdLine.iloc[:1].iloc[0] - macdSignal.iloc[:1].iloc[0])
                <= 0.2
            )
            and (macdLine.iloc[:3].iloc[2] > macdSignal.iloc[:3].iloc[2])
            and (
                (macdLine.iloc[:3].iloc[2] - macdSignal.iloc[:3].iloc[2])
                - (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1])
                < 1
            )
        )

    #@measure_time
    # validate if CCI is within given range
    def validateCCI(self, df, screenDict, saveDict, minCCI, maxCCI):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        cci = int(data.head(1)["CCI"].iloc[0])
        saveDict["CCI"] = cci
        if (cci <= minCCI or cci >= maxCCI):
            if ("Up" in saveDict["Trend"]):
                screenDict["CCI"] = (
                    colorText.BOLD + colorText.GREEN + str(cci) + colorText.END
                )
            else:
                screenDict["CCI"] = (
                    colorText.BOLD + colorText.FAIL + str(cci) + colorText.END
                )
            return True
        screenDict["CCI"] = colorText.BOLD + colorText.FAIL + str(cci) + colorText.END
        return False

    # Find Conflucence
    def validateConfluence(self, stock, df, screenDict, saveDict, percentage=0.1,confFilter=3):
        data = df.copy()
        recent = data.head(2)
        is50DMAUpTrend = (recent["SMA"].iloc[0] > recent["SMA"].iloc[1])
        is50DMADownTrend = (recent["SMA"].iloc[0] < recent["SMA"].iloc[1])
        isGoldenCrossOver = (recent["SMA"].iloc[0] >= recent["LMA"].iloc[0]) and \
                            (recent["SMA"].iloc[1] <= recent["LMA"].iloc[1])
        isDeadCrossOver = (recent["SMA"].iloc[0] <= recent["LMA"].iloc[0]) and \
                            (recent["SMA"].iloc[1] >= recent["LMA"].iloc[1])
        is50DMA = (recent["SMA"].iloc[0] <= recent["Close"].iloc[0])
        is200DMA = (recent["LMA"].iloc[0] <= recent["Close"].iloc[0])
        difference = round((recent["SMA"].iloc[0] - recent["LMA"].iloc[0])
                / recent["Close"].iloc[0]
                * 100,
                2,
            )
        saveDict["ConfDMADifference"] = difference
        screenDict["ConfDMADifference"] = difference
        saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
        # difference = abs(difference)
        confText = f"{'GoldenCrossover' if isGoldenCrossOver else ('DeadCrossover' if isDeadCrossOver else ('Conf.Up' if is50DMAUpTrend else ('Conf.Down' if is50DMADownTrend else ('50DMA' if is50DMA else ('200DMA' if is200DMA else 'Unknown')))))}"
        if abs(recent["SMA"].iloc[0] - recent["LMA"].iloc[0]) <= (
            recent["SMA"].iloc[0] * percentage
        ):
            if recent["SMA"].iloc[0] >= recent["LMA"].iloc[0]:
                screenDict["MA-Signal"] = (
                    saved[0] 
                    + colorText.BOLD
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            else:
                screenDict["MA-Signal"] = (
                    saved[0] 
                    + colorText.BOLD
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            return confFilter == 3 or \
                (confFilter == 1 and (is50DMAUpTrend or (isGoldenCrossOver or 'Up' in confText))) or \
                (confFilter == 2 and (is50DMADownTrend or isDeadCrossOver or 'Down' in confText))
        # Maybe the difference is not within the range, but we'd still like to keep the stock in
        # the list if it's a golden crossover or dead crossover
        if isGoldenCrossOver or isDeadCrossOver:
            screenDict["MA-Signal"] = (
                    saved[0] 
                    + colorText.BOLD
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
            saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            return confFilter == 3 or \
                (confFilter == 1 and isGoldenCrossOver) or \
                (confFilter == 2 and isDeadCrossOver)
        return False

    #@measure_time
    # Validate if share prices are consolidating
    def validateConsolidation(self, df, screenDict, saveDict, percentage=10):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        hc = data.describe()["Close"]["max"]
        lc = data.describe()["Close"]["min"]
        if (hc - lc) <= (hc * percentage / 100) and (hc - lc != 0):
            screenDict["Consol."] = (
                colorText.BOLD
                + colorText.GREEN
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        else:
            screenDict["Consol."] = (
                colorText.BOLD
                + colorText.FAIL
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        saveDict["Consol."] = f'Range:{str(round((abs((hc-lc)/hc)*100),1))+"%"}'
        return round((abs((hc - lc) / hc) * 100), 1)

    # validate if the stock has been having higher highs, higher lows
    # and higher close with latest close > supertrend and 8-EMA.
    def validateHigherHighsHigherLowsHigherClose(self, df):
        data = df.copy()
        day0 = data
        day1 = data[1:]
        day2 = data[2:]
        day3 = data[3:]
        higherHighs = (
            (day0["High"].iloc[0] > day1["High"].iloc[0])
            and (day1["High"].iloc[0] > day2["High"].iloc[0])
            and (day2["High"].iloc[0] > day3["High"].iloc[0])
        )
        higherLows = (
            (day0["Low"].iloc[0] > day1["Low"].iloc[0])
            and (day1["Low"].iloc[0] > day2["Low"].iloc[0])
            and (day2["Low"].iloc[0] > day3["Low"].iloc[0])
        )
        higherClose = (
            (day0["Close"].iloc[0] > day1["Close"].iloc[0])
            and (day1["Close"].iloc[0] > day2["Close"].iloc[0])
            and (day2["Close"].iloc[0] > day3["Close"].iloc[0])
        )
        # higherRSI = (day0["RSI"].iloc[0] > day1["RSI"].iloc[0]) and \
        #                 (day1["RSI"].iloc[0] > day2["RSI"].iloc[0]) and \
        #                 (day2["RSI"].iloc[0] > day3["RSI"].iloc[0]) and \
        #                 day3["RSI"].iloc[0] >= 50 and day0["RSI"].iloc[0] >= 65
        reversedData = data[::-1].copy()
        reversedData["SUPERT"] = pktalib.supertrend(reversedData, 7, 3)["SUPERT_7_3.0"]
        reversedData["EMA8"] = pktalib.EMA(reversedData["Close"], timeperiod=9)
        higherClose = (
            higherClose
            and day0["Close"].iloc[0] > reversedData.tail(1)["SUPERT"].iloc[0]
            and day0["Close"].iloc[0] > reversedData.tail(1)["EMA8"].iloc[0]
        )
        return higherHighs and higherLows and higherClose

    #@measure_time
    # Validate 'Inside Bar' structure for recent days
    def validateInsideBar(
        self, df, screenDict, saveDict, chartPattern=1, daysToLookback=5
    ):
        data = df.copy()
        orgData = data
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        for i in range(daysToLookback, round(daysToLookback * 0.5) - 1, -1):
            if i == 2:
                return 0  # Exit if only last 2 candles are left
            if chartPattern == 1:
                if "Up" in saveDict["Trend"] and (
                    "Bull" in saveDict["MA-Signal"]
                    or "Support" in saveDict["MA-Signal"]
                ):
                    data = orgData.head(i)
                    refCandle = data.tail(1)
                    if (
                        (len(data.High[data.High > refCandle.High.item()]) == 0)
                        and (len(data.Low[data.Low < refCandle.Low.item()]) == 0)
                        and (len(data.Open[data.Open > refCandle.High.item()]) == 0)
                        and (len(data.Close[data.Close < refCandle.Low.item()]) == 0)
                    ):
                        screenDict["Pattern"] = (
                            saved[0]
                            + colorText.BOLD
                            + colorText.WARN
                            + ("Inside Bar (%d)" % i)
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Inside Bar (%d)" % i
                        return i
                else:
                    return 0
            else:
                if "Down" in saveDict["Trend"] and (
                    "Bear" in saveDict["MA-Signal"] or "Resist" in saveDict["MA-Signal"]
                ):
                    data = orgData.head(i)
                    refCandle = data.tail(1)
                    if (
                        (len(data.High[data.High > refCandle.High.item()]) == 0)
                        and (len(data.Low[data.Low < refCandle.Low.item()]) == 0)
                        and (len(data.Open[data.Open > refCandle.High.item()]) == 0)
                        and (len(data.Close[data.Close < refCandle.Low.item()]) == 0)
                    ):
                        screenDict["Pattern"] = (
                            saved[0]
                            + colorText.BOLD
                            + colorText.WARN
                            + ("Inside Bar (%d)" % i)
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Inside Bar (%d)" % i
                        return i
                else:
                    return 0
        return 0

    # Find IPO base
    def validateIpoBase(self, stock, df, screenDict, saveDict, percentage=0.3):
        data = df.copy()
        listingPrice = data[::-1].head(1)["Open"].iloc[0]
        currentPrice = data.head(1)["Close"].iloc[0]
        ATH = data.describe()["High"]["max"]
        if ATH > (listingPrice + (listingPrice * percentage)):
            return False
        away = round(((currentPrice - listingPrice) / listingPrice) * 100, 1)
        if (
            (listingPrice - (listingPrice * percentage))
            <= currentPrice
            <= (listingPrice + (listingPrice * percentage))
        ):
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            if away > 0:
                screenDict["Pattern"] = (
                    saved[0] 
                    + colorText.BOLD
                    + colorText.GREEN
                    + f"IPO Base ({away} %)"
                    + colorText.END
                )
            else:
                screenDict["Pattern"] = (
                    saved[0]
                    + colorText.BOLD
                    + colorText.GREEN
                    + "IPO Base "
                    + colorText.FAIL
                    + f"({away} %)"
                    + colorText.END
                )
            saveDict["Pattern"] = saved[1] + f"IPO Base ({away} %)"
            return True
        return False

    #@measure_time
    # Validate Lorentzian Classification signal
    def validateLorentzian(self, df, screenDict, saveDict, lookFor=3):
        data = df.copy()
        # lookFor: 1-Buy, 2-Sell, 3-Any
        data = data[::-1]  # Reverse the dataframe
        data = data.rename(
            columns={
                "Open": "open",
                "Close": "close",
                "High": "high",
                "Low": "low",
                "Volume": "volume",
            }
        )
        try:
            lc = ata.LorentzianClassification(data=data)
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            if lc.df.iloc[-1]["isNewBuySignal"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.BOLD + colorText.GREEN + "Lorentzian-Buy" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + "Lorentzian-Buy"
                if lookFor != 2: # Not Sell
                    return True
            elif lc.df.iloc[-1]["isNewSellSignal"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.BOLD + colorText.FAIL + "Lorentzian-Sell" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + "Lorentzian-Sell"
                if lookFor != 1: # Not Buy
                    return True
        except Exception:  # pragma: no cover
            # ValueError: operands could not be broadcast together with shapes (20,) (26,)
            # File "/opt/homebrew/lib/python3.11/site-packages/advanced_ta/LorentzianClassification/Classifier.py", line 186, in __init__
            # File "/opt/homebrew/lib/python3.11/site-packages/advanced_ta/LorentzianClassification/Classifier.py", line 395, in __classify
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/common.py", line 76, in new_method
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/arraylike.py", line 70, in __and__
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/series.py", line 5810, in _logical_method
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/array_ops.py", line 456, in logical_op
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/array_ops.py", line 364, in na_logical_op
            # self.default_logger.debug(e, exc_info=True)
            pass
        return False

    # validate if the stock has been having lower lows, lower highs
    def validateLowerHighsLowerLows(self, df):
        data = df.copy()
        day0 = data
        day1 = data[1:]
        day2 = data[2:]
        day3 = data[3:]
        lowerHighs = (
            (day0["High"].iloc[0] < day1["High"].iloc[0])
            and (day1["High"].iloc[0] < day2["High"].iloc[0])
            and (day2["High"].iloc[0] < day3["High"].iloc[0])
        )
        lowerLows = (
            (day0["Low"].iloc[0] < day1["Low"].iloc[0])
            and (day1["Low"].iloc[0] < day2["Low"].iloc[0])
            and (day2["Low"].iloc[0] < day3["Low"].iloc[0])
        )
        higherRSI = (
            (day0["RSI"].iloc[0] < day1["RSI"].iloc[0])
            and (day1["RSI"].iloc[0] < day2["RSI"].iloc[0])
            and (day2["RSI"].iloc[0] < day3["RSI"].iloc[0])
            and day0["RSI"].iloc[0] >= 50
        )
        return lowerHighs and lowerLows and higherRSI

    # Validate if recent volume is lowest of last 'N' Days
    def validateLowestVolume(self, df, daysForLowestVolume):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        if daysForLowestVolume is None:
            daysForLowestVolume = 30
        if len(data) < daysForLowestVolume:
            return False
        data = data.head(daysForLowestVolume)
        recent = data.head(1)
        if (recent["Volume"].iloc[0] <= data.describe()["Volume"]["min"]) and recent[
            "Volume"
        ][0] != np.nan:
            return True
        return False

    # Validate LTP within limits
    def validateLTP(self, df, screenDict, saveDict, minLTP=None, maxLTP=None):
        data = df.copy()
        ltpValid = False
        if minLTP is None:
            minLTP = self.configManager.minLTP
        if maxLTP is None:
            maxLTP = self.configManager.maxLTP
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)

        pct_change = (data[::-1]["Close"].pct_change() * 100).iloc[-1]
        pct_save = "%.1f%%" % pct_change
        if pct_change > 0.2:
            pct_change = colorText.GREEN + ("%.1f%%" % pct_change) + colorText.END
        elif pct_change < -0.2:
            pct_change = colorText.FAIL + ("%.1f%%" % pct_change) + colorText.END
        else:
            pct_change = colorText.WARN + ("%.1f%%" % pct_change) + colorText.END
        saveDict["%Chng"] = pct_save
        screenDict["%Chng"] = pct_change
        ltp = round(recent["Close"].iloc[0], 2)
        verifyStageTwo = True
        if len(data) > 250:
            yearlyLow = data.head(250).min()["Close"]
            yearlyHigh = data.head(250).max()["Close"]
            if ltp < (2 * yearlyLow) and ltp < (0.75 * yearlyHigh):
                verifyStageTwo = False
                screenDict["Stock"] = colorText.FAIL + saveDict["Stock"] + colorText.END
        if ltp >= minLTP and ltp <= maxLTP:
            ltpValid = True
            saveDict["LTP"] = round(ltp, 2)
            screenDict["LTP"] = colorText.GREEN + ("%.2f" % ltp) + colorText.END
            return ltpValid, verifyStageTwo
        screenDict["LTP"] = colorText.FAIL + ("%.2f" % ltp) + colorText.END
        saveDict["LTP"] = round(ltp, 2)
        return ltpValid, verifyStageTwo

    def validateLTPForPortfolioCalc(self, df, screenDict, saveDict,requestedPeriod=0):
        data = df.copy()
        periods = self.configManager.periodsRange
        if requestedPeriod > 0 and requestedPeriod not in periods:
            periods.append(requestedPeriod)
        previous_recent = data.head(1)
        previous_recent.reset_index(inplace=True)
        calc_date = str(previous_recent.iloc[:, 0][0]).split(" ")[0]
        for prd in periods:
            if len(data) >= prd + 1:
                prevLtp = data["Close"].iloc[0]
                ltpTdy = data["Close"].iloc[prd]
                if isinstance(prevLtp,pd.Series):
                    prevLtp = prevLtp[0]
                    ltpTdy = ltpTdy[0]
                screenDict[f"LTP{prd}"] = (
                    (colorText.GREEN if (ltpTdy >= prevLtp) else (colorText.FAIL))
                    + str("{:.2f}".format(ltpTdy))
                    + colorText.END
                )
                screenDict[f"Growth{prd}"] = (
                    (colorText.GREEN if (ltpTdy >= prevLtp) else (colorText.FAIL))
                    + str("{:.2f}".format(ltpTdy - prevLtp))
                    + colorText.END
                )
                saveDict[f"LTP{prd}"] = round(ltpTdy, 2)
                saveDict[f"Growth{prd}"] = round(ltpTdy - prevLtp, 2)
                if prd == 22 or (prd == requestedPeriod):
                    changePercent = round(((prevLtp-ltpTdy) if requestedPeriod ==0 else (ltpTdy - prevLtp))*100/ltpTdy, 2)
                    saveDict[f"{prd}-Pd %"] = f"{changePercent}%"
                    screenDict[f"{prd}-Pd %"] = (colorText.GREEN if changePercent >=0 else colorText.FAIL) + f"{changePercent}%" + colorText.END
                screenDict["Date"] = calc_date
                saveDict["Date"] = calc_date
            else:
                saveDict[f"LTP{prd}"] = np.nan
                saveDict[f"Growth{prd}"] = np.nan
                screenDict["Date"] = calc_date
                saveDict["Date"] = calc_date

    # Find stocks that are bearish intraday: Macd Histogram negative
    def validateMACDHistogramBelow0(self, df):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macd = pktalib.MACD(data["Close"], 12, 26, 9)[2].tail(1)
        return macd.iloc[:1][0] < 0

    #@measure_time
    # Find if stock gaining bullish momentum
    def validateMomentum(self, df, screenDict, saveDict):
        data = df.copy()
        try:
            data = data.head(3)
            if len(data) < 3:
                return False
            for row in data.iterrows():
                # All 3 candles should be Green and NOT Circuits
                yc = row[1]["Close"]
                yo = row[1]["Open"]
                if yc <= yo:
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because yesterday-close ({yc}) <= yesterday-open ({yo})'
                    )
                    return False
            openDesc = data.sort_values(by=["Open"], ascending=False)
            closeDesc = data.sort_values(by=["Close"], ascending=False)
            volDesc = data.sort_values(by=["Volume"], ascending=False)
            try:
                if (
                    data.equals(openDesc)
                    and data.equals(closeDesc)
                    and data.equals(volDesc)
                ):
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, open,close and volume equal from day before yesterday. A potential momentum-gainer!'
                    )
                    to = data["Open"].iloc[0]
                    yc = data["Close"].iloc[1]
                    yo = data["Open"].iloc[1]
                    dyc = data["Close"].iloc[2]
                    if (to >= yc) and (yo >= dyc):
                        self.default_logger.info(
                            f'Stock:{saveDict["Stock"]}, is a momentum-gainer because today-open ({to}) >= yesterday-close ({yc}) and yesterday-open({yo}) >= day-before-close({dyc})'
                        )
                        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                        screenDict["Pattern"] = (
                            saved[0]
                            + colorText.BOLD
                            + colorText.GREEN
                            + "Momentum Gainer"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Momentum Gainer"
                        return True
                    self.default_logger.info(
                        f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because either today-open ({to}) < yesterday-close ({yc}) or yesterday-open({yo}) < day-before-close({dyc})'
                    )
            except IndexError as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                # self.default_logger.debug(data)
                pass
            return False
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            return False

    #@measure_time
    # Validate Moving averages and look for buy/sell signals
    def validateMovingAverages(self, df, screenDict, saveDict, maRange=2.5):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
        if (
            recent["SMA"].iloc[0] > recent["LMA"].iloc[0]
            and recent["Close"].iloc[0] > recent["SMA"].iloc[0]
        ):
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.GREEN + "Bullish" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "Bullish"
        elif recent["SMA"].iloc[0] < recent["LMA"].iloc[0]:
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.FAIL + "Bearish" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "Bearish"
        elif recent["SMA"].iloc[0] == 0:
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.WARN + "Unknown" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "Unknown"
        else:
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.WARN + "Neutral" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "Neutral"

        smaDev = data["SMA"].iloc[0] * maRange / 100
        lmaDev = data["LMA"].iloc[0] * maRange / 100
        open, high, low, close, sma, lma = (
            data["Open"].iloc[0],
            data["High"].iloc[0],
            data["Low"].iloc[0],
            data["Close"].iloc[0],
            data["SMA"].iloc[0],
            data["LMA"].iloc[0],
        )
        maReversal = 0
        # Taking Support 50
        if close > sma and low <= (sma + smaDev):
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.GREEN + "50MA-Support" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "50MA-Support"
            maReversal = 1
        # Validating Resistance 50
        elif close < sma and high >= (sma - smaDev):
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.FAIL + "50MA-Resist" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "50MA-Resist"
            maReversal = -1
        # Taking Support 200
        elif close > lma and low <= (lma + lmaDev):
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.GREEN + "200MA-Support" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "200MA-Support"
            maReversal = 1
        # Validating Resistance 200
        elif close < lma and high >= (lma - lmaDev):
            screenDict["MA-Signal"] = (
                saved[0] + colorText.BOLD + colorText.FAIL + "200MA-Resist" + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + "200MA-Resist"
            maReversal = -1
        # For a Bullish Candle
        if self.getCandleType(data):
            # Crossing up 50
            if open < sma and close > sma:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.BOLD + colorText.GREEN + "BullCross-50MA" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "BullCross-50MA"
                maReversal = 1
            # Crossing up 200
            elif open < lma and close > lma:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.BOLD + colorText.GREEN + "BullCross-200MA" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "BullCross-200MA"
                maReversal = 1
        # For a Bearish Candle
        elif not self.getCandleType(data):
            # Crossing down 50
            if open > sma and close < sma:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.BOLD + colorText.FAIL + "BearCross-50MA" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "BearCross-50MA"
                maReversal = -1
            # Crossing up 200
            elif open > lma and close < lma:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.BOLD + colorText.FAIL + "BearCross-200MA" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "BearCross-200MA"
                maReversal = -1
        return maReversal

    # Find NRx range for Reversal
    def validateNarrowRange(self, df, screenDict, saveDict, nr=4):
        data = df.copy()
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        if PKDateUtilities.isTradingTime():
            rangeData = data.head(nr + 1)[1:]
            now_candle = data.head(1)
            rangeData["Range"] = abs(rangeData["Close"] - rangeData["Open"])
            recent = rangeData.head(1)
            if (
                len(recent) == 1
                and recent["Range"].iloc[0] == rangeData.describe()["Range"]["min"]
            ):
                if (
                    self.getCandleType(recent)
                    and now_candle["Close"].iloc[0] >= recent["Close"].iloc[0]
                ):
                    screenDict["Pattern"] = (
                        saved[0] + colorText.BOLD + colorText.GREEN + f"Buy-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = saved[1] + f"Buy-NR{nr}"
                    return True
                elif (
                    not self.getCandleType(recent)
                    and now_candle["Close"].iloc[0] <= recent["Close"].iloc[0]
                ):
                    screenDict["Pattern"] = (
                        saved[0] + colorText.BOLD + colorText.FAIL + f"Sell-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = saved[1] + f"Sell-NR{nr}"
                    return True
            return False
        else:
            rangeData = data.head(nr)
            rangeData["Range"] = abs(rangeData["Close"] - rangeData["Open"])
            recent = rangeData.head(1)
            if recent["Range"].iloc[0] == rangeData.describe()["Range"]["min"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.BOLD + colorText.GREEN + f"NR{nr}" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + f"NR{nr}"
                return True
            return False

    # Find if stock is newly listed
    def validateNewlyListed(self, df, daysToLookback):
        data = df.copy()
        daysToLookback = int(daysToLookback[:-1])
        recent = data.head(1)
        if len(data) < daysToLookback and (
            recent["Close"].iloc[0] != np.nan and recent["Close"].iloc[0] > 0
        ):
            return True
        return False

    # Validate if the stock prices are at least rising by 2% for the last 3 sessions
    def validatePriceRisingByAtLeast2Percent(self, df, screenDict, saveDict):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data.head(4)
        if len(data) < 4:
            return False
        day0 = data.iloc[0]["Close"].item()
        dayMinus1 = data.iloc[1]["Close"].item()
        dayMinus2 = data.iloc[2]["Close"].item()
        dayMinus3 = data.iloc[3]["Close"].item()
        percent3 = round((dayMinus2 - dayMinus3) * 100 / dayMinus3, 2)
        percent2 = round((dayMinus1 - dayMinus2) * 100 / dayMinus2, 2)
        percent1 = round((day0 - dayMinus1) * 100 / dayMinus1, 2)

        if percent1 >= 2 and percent2 >= 2 and percent3 >= 2:
            pct_change_text = (
                ("%.1f%%" % percent1)
                + (" (%.1f%%," % percent2)
                + (" %.1f%%)" % percent3)
            )
            saveDict["%Chng"] = pct_change_text
            screenDict["%Chng"] = colorText.GREEN + pct_change_text + colorText.END
            return True and self.getCandleType(data.head(1))
        return False

    #@measure_time
    # validate if RSI is within given range
    def validateRSI(self, df, screenDict, saveDict, minRSI, maxRSI):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        rsi = int(data.head(1)["RSI"].iloc[0])
        saveDict["RSI"] = rsi
        # https://chartink.com/screener/rsi-screening
        if rsi >= minRSI and rsi <= maxRSI:  # or (rsi <= 71 and rsi >= 67):
            screenDict["RSI"] = (
                colorText.BOLD + colorText.GREEN + str(rsi) + colorText.END
            )
            return True
        screenDict["RSI"] = colorText.BOLD + colorText.FAIL + str(rsi) + colorText.END
        return False

    # Validate if the stock is bullish in the short term
    def validateShortTermBullish(self, df, screenDict, saveDict):
        data = df.copy()
        # https://chartink.com/screener/short-term-bullish
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        fk = 0 if len(data) < 3 else np.round(data["FASTK"].iloc[2], 5)
        # Reverse the dataframe for ichimoku calculations with date in ascending order
        df_new = data[::-1]
        try:
            df_ichi = df_new.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
            )
            ichi = pktalib.ichimoku(df_ichi, 9, 26, 52, 26)
            if ichi is None:
                return False
            df_new = pd.concat([df_new, ichi], axis=1)
            # Reverse again to get the most recent date on top
            df_new = df_new[::-1]
            df_new = df_new.head(1)
            df_new["cloud_green"] = df_new["ISA_9"].iloc[0] > df_new["ISB_26"].iloc[0]
            df_new["cloud_red"] = df_new["ISB_26"].iloc[0] > df_new["ISA_9"].iloc[0]
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            pass
        aboveCloudTop = False
        # baseline > cloud top (cloud is bound by span a and span b) and close is > cloud top
        if df_new["cloud_green"].iloc[0]:
            aboveCloudTop = (
                df_new["IKS_26"].iloc[0] > df_new["ISA_9"].iloc[0]
                and recent["Close"].iloc[0] > df_new["ISA_9"].iloc[0]
            )
        elif df_new["cloud_red"].iloc[0]:
            aboveCloudTop = (
                df_new["IKS_26"].iloc[0] > df_new["ISB_26"].iloc[0]
                and recent["Close"].iloc[0] > df_new["ISB_26"].iloc[0]
            )

        # Latest Ichimoku baseline is < latest Ichimoku conversion line
        if aboveCloudTop and df_new["IKS_26"].iloc[0] < df_new["ITS_9"].iloc[0]:
            # StochRSI crossed 20 and RSI > 50
            if fk > 20 and recent["RSI"].iloc[0] > 50:
                # condition of crossing the StochRSI main signal line from bottom to top
                if (
                    data["FASTD"].iloc[100] < data["FASTK"].iloc[100]
                    and data["FASTD"].iloc[101] > data["FASTK"].iloc[101]
                ):
                    # close > 50 period SMA/EMA and 200 period SMA/EMA
                    if (
                        recent["SSMA"].iloc[0] > recent["SMA"].iloc[0]
                        and recent["Close"].iloc[0] > recent["SSMA"].iloc[0]
                        and recent["Close"].iloc[0] > recent["LMA"].iloc[0]
                    ):
                        saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                        screenDict["MA-Signal"] = (
                            saved[0] + colorText.BOLD + colorText.GREEN + "Bullish" + colorText.END
                        )
                        saveDict["MA-Signal"] = saved[1] + "Bullish"
                        return True
        return False

    # Validate VPC
    def validateVCP(
        self, df, screenDict, saveDict, stockName=None, window=3, percentageFromTop=3
    ):
        data = df.copy()
        try:
            percentageFromTop /= 100
            data.reset_index(inplace=True)
            data.rename(columns={"index": "Date"}, inplace=True)
            data["tops"] = (
                data["High"]
                .iloc[
                    list(
                        pktalib.argrelextrema(
                            np.array(data["High"]), np.greater_equal, order=window
                        )[0]
                    )
                ]
                .head(4)
            )
            data["bots"] = (
                data["Low"]
                .iloc[
                    list(
                        pktalib.argrelextrema(
                            np.array(data["Low"]), np.less_equal, order=window
                        )[0]
                    )
                ]
                .head(4)
            )
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)
            tops = data[data.tops > 0]
            # bots = data[data.bots > 0]
            highestTop = round(tops.describe()["High"]["max"], 1)
            filteredTops = tops[
                tops.tops > (highestTop - (highestTop * percentageFromTop))
            ]
            # print(tops)
            # print(filteredTops)
            # print(tops.sort_values(by=['tops'], ascending=False))
            # print(tops.describe())
            # print(f"Till {highestTop-(highestTop*percentageFromTop)}")
            if filteredTops.equals(tops):  # Tops are in the range
                lowPoints = []
                for i in range(len(tops) - 1):
                    endDate = tops.iloc[i]["Date"]
                    startDate = tops.iloc[i + 1]["Date"]
                    lowPoints.append(
                        data[
                            (data.Date >= startDate) & (data.Date <= endDate)
                        ].describe()["Low"]["min"]
                    )
                lowPointsOrg = lowPoints
                lowPoints.sort(reverse=True)
                lowPointsSorted = lowPoints
                ltp = data.head(1)["Close"].iloc[0]
                if (
                    lowPointsOrg == lowPointsSorted
                    and ltp < highestTop
                    and ltp > lowPoints[0]
                ):
                    saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                    screenDict["Pattern"] = (
                        saved[0] 
                        + colorText.BOLD
                        + colorText.GREEN
                        + f"VCP (BO: {highestTop})"
                        + colorText.END
                    )
                    saveDict["Pattern"] = saved[1] + f"VCP (BO: {highestTop})"
                    return True
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
        return False

    # Validate if volume of last day is higher than avg
    def validateVolume(
        self, df, screenDict, saveDict, volumeRatio=2.5, minVolume=100
    ):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        # Either the rolling volume of past 20 sessions or today's volume should be > min volume
        hasMinimumVolume = (
            recent["VolMA"].iloc[0] >= minVolume
            or recent["Volume"].iloc[0] >= minVolume
        )
        if recent["VolMA"].iloc[0] == 0:  # Handles Divide by 0 warning
            saveDict["Volume"] = 0  # "Unknown"
            screenDict["Volume"] = 0
            return False, hasMinimumVolume
        ratio = round(recent["Volume"].iloc[0] / recent["VolMA"].iloc[0], 2)
        saveDict["Volume"] = ratio
        if ratio >= volumeRatio and ratio != np.nan and (not math.isinf(ratio)):
            screenDict["Volume"] = ratio
            return True, hasMinimumVolume
        screenDict["Volume"] = ratio
        return False, hasMinimumVolume

    # Find if stock is validating volume spread analysis
    def validateVolumeSpreadAnalysis(self, df, screenDict, saveDict):
        try:
            data = df.copy()
            data = data.head(2)
            if len(data) < 2:
                return False
            try:
                # Check for previous RED candles
                # Current candle = 0th, Previous Candle = 1st for following logic
                if data.iloc[1]["Open"] >= data.iloc[1]["Close"]:
                    spread1 = abs(data.iloc[1]["Open"] - data.iloc[1]["Close"])
                    spread0 = abs(data.iloc[0]["Open"] - data.iloc[0]["Close"])
                    lower_wick_spread0 = (
                        max(data.iloc[0]["Open"], data.iloc[0]["Close"])
                        - data.iloc[0]["Low"]
                    )
                    vol1 = data.iloc[1]["Volume"]
                    vol0 = data.iloc[0]["Volume"]
                    saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                    if (
                        spread0 > spread1
                        and vol0 < vol1
                        and data.iloc[0]["Volume"] < data.iloc[0]["VolMA"]
                        and data.iloc[0]["Close"] <= data.iloc[1]["Open"]
                        and spread0 < lower_wick_spread0
                        and data.iloc[0]["Volume"] <= int(data.iloc[1]["Volume"] * 0.75)
                    ):
                        screenDict["Pattern"] = (
                            saved[0] 
                            + colorText.BOLD
                            + colorText.GREEN
                            + "Supply Drought"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Supply Drought"
                        return True
                    if (
                        spread0 < spread1
                        and vol0 > vol1
                        and data.iloc[0]["Volume"] > data.iloc[0]["VolMA"]
                        and data.iloc[0]["Close"] <= data.iloc[1]["Open"]
                    ):
                        screenDict["Pattern"] = (
                            saved[0] 
                            + colorText.BOLD
                            + colorText.GREEN
                            + "Demand Rise"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Demand Rise"
                        return True
            except IndexError as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
            return False
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            return False

    """
    # Find out trend for days to lookback
    def validateVCP(df, screenDict, saveDict, daysToLookback=ConfigManager.daysToLookback, stockName=None):
        // De-index date
        data = df.copy()
        data.reset_index(inplace=True)
        data.rename(columns={'index':'Date'}, inplace=True)
        data = data.head(daysToLookback)
        data = data[::-1]
        data = data.set_index(np.arange(len(data)))
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data['tops'] = data['Close'].iloc[list(pktalib.argrelextrema(np.array(data['Close']), np.greater_equal, order=3)[0])]
        data['bots'] = data['Close'].iloc[list(pktalib.argrelextrema(np.array(data['Close']), np.less_equal, order=3)[0])]
        try:
            try:
                top_slope,top_c = np.polyfit(data.index[data.tops > 0], data['tops'][data.tops > 0], 1)
                bot_slope,bot_c = np.polyfit(data.index[data.bots > 0], data['bots'][data.bots > 0], 1)
                topAngle = math.degrees(math.atan(top_slope))
                vcpAngle = math.degrees(math.atan(bot_slope) - math.atan(top_slope))

                # print(math.degrees(math.atan(top_slope)))
                # print(math.degrees(math.atan(bot_slope)))
                # print(vcpAngle)
                # print(topAngle)
                # print(data.max()['bots'])
                # print(data.max()['tops'])
                if (vcpAngle > 20 and vcpAngle < 70) and (topAngle > -10 and topAngle < 10) and (data['bots'].max() <= data['tops'].max()) and (len(data['bots'][data.bots > 0]) > 1):
                    print("---> GOOD VCP %s at %sRs" % (stockName, top_c))
                    import os
                    os.system("echo %s >> vcp_plots\VCP.txt" % stockName)

                    import matplotlib.pyplot as plt                
                    plt.scatter(data.index[data.tops > 0], data['tops'][data.tops > 0], c='g')
                    plt.scatter(data.index[data.bots > 0], data['bots'][data.bots > 0], c='r')
                    plt.plot(data.index, data['Close'])
                    plt.plot(data.index, top_slope*data.index+top_c,'g--')
                    plt.plot(data.index, bot_slope*data.index+bot_c,'r--')
                    if stockName != None:
                        plt.title(stockName)
                    # plt.show()
                    plt.savefig('vcp_plots\%s.png' % stockName)
                    plt.clf()
            except np.RankWarning:
                pass
        except np.linalg.LinAlgError:
            return False
    """
