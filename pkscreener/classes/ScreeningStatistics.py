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
import os
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd

from sys import float_info as sflt
import pkscreener.classes.Utility as Utility
from pkscreener import Imports
from pkscreener.classes.Pktalib import pktalib
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes import Archiver
from PKNSETools.morningstartools import Stock

if sys.version_info >= (3, 11):
    import advanced_ta as ata

# from sklearn.preprocessing import StandardScaler
if Imports["scipy"]:
    from scipy.stats import linregress

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.MarketHours import MarketHours
# from PKDevTools.classes.log import measure_time

# Exception for only downloading stock data and not screening
class DownloadDataOnly(Exception):
    pass

class EligibilityConditionNotMet(Exception):
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
    def __init__(self, configManager=None, default_logger=None,shouldLog=False) -> None:
        self.configManager = configManager
        self.default_logger = default_logger
        self.shouldLog = shouldLog

    def calc_relative_strength(self,df:pd.DataFrame):
        if df is None or len(df) <= 1:
            return -1
        closeColumn = 'Adj Close'
        if closeColumn not in df.columns:
            closeColumn = 'Close'

        with pd.option_context('mode.chained_assignment', None):
            df.sort_index(inplace=True)
            ## relative gain and losses
            df['close_shift'] = df[closeColumn].shift(1)
            ## Gains (true) and Losses (False)
            df['gains'] = df.apply(lambda x: x[closeColumn] if x[closeColumn] >= x['close_shift'] else 0, axis=1)
            df['loss'] = df.apply(lambda x: x[closeColumn] if x[closeColumn] <= x['close_shift'] else 0, axis=1)

        avg_gain = df['gains'].mean()
        avg_losses = df['loss'].mean()

        return avg_gain / avg_losses

    #Calculating signals
    def computeBuySellSignals(self,df,ema_period=200,retry=True):
        try:
            if Imports["vectorbt"]:
                from vectorbt.indicators import MA as vbt
                if df is not None:
                    ema = vbt.run(df["Close"], 1, short_name='EMA', ewm=True)
                    df["Above"] = ema.ma_crossed_above(df["ATRTrailingStop"])
                    df["Below"] = ema.ma_crossed_below(df["ATRTrailingStop"])
            else:
                OutputControls().printOutput(f"{colorText.FAIL}The main module needed for best Buy/Sell result calculation is missing. Falling back on an alternative, but it is not very reliable.{colorText.END}")
                if df is not None:
                    ema = pktalib.EMA(df["Close"], ema_period) if ema_period > 1 else df["Close"]#short_name='EMA', ewm=True)        
                    df["Above"] = ema > df["ATRTrailingStop"]
                    df["Below"] = ema < df["ATRTrailingStop"]
        except (OSError,FileNotFoundError) as e: # pragma: no cover
            OutputControls().printOutput(f"{colorText.FAIL}Some dependencies are missing. Try and run this option again.{colorText.END}")
            # OSError:RALLIS: [Errno 2] No such file or directory: '/tmp/_MEIzoTV6A/vectorbt/templates/light.json'
            # if "No such file or directory" in str(e):
            try:
                import os
                outputFolder = None
                try:
                    outputFolder = os.sep.join(e.filename.split(os.sep)[:-1])
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e: # pragma: no cover
                    outputFolder = os.sep.join(str(e).split("\n")[0].split(": ")[1].replace("'","").split(os.sep)[:-1])
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                pass
            self.downloadSaveTemplateJsons(outputFolder)
            if retry:
                return self.computeBuySellSignals(df,ema_period=ema_period,retry=False)
            return None
        except ImportError as e: # pragma: no cover
            OutputControls().printOutput(f"{colorText.FAIL}The main module needed for best Buy/Sell result calculation is missing. Falling back on an alternative, but it is not very reliable.{colorText.END}")
            if df is not None:
                ema = pktalib.EMA(df["Close"], ema_period) if ema_period > 1 else df["Close"]#short_name='EMA', ewm=True)        
                df["Above"] = ema > df["ATRTrailingStop"]
                df["Below"] = ema < df["ATRTrailingStop"]
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            pass
                
        if df is not None:
            df["Buy"] = (df["Close"] > df["ATRTrailingStop"]) & (df["Above"]==True)
            df["Sell"] = (df["Close"] < df["ATRTrailingStop"]) & (df["Below"]==True)

        return df

    # Example of combining UTBot Alerts with RSI and ADX
    def custom_strategy(self,dataframe):
        dataframe = self.findBuySellSignalsFromATRTrailing(dataframe, key_value=2, atr_period=7, ema_period=100)
        
        # Calculate RSI and ADX
        rsi = pktalib.RSI(dataframe['Close'])
        adx = pktalib.ADX(dataframe['High'], dataframe['Low'], dataframe['Close'])
        
        # Define conditions based on UTBot Alerts and additional indicators
        # ... (your custom conditions here)
        
        return dataframe

    def downloadSaveTemplateJsons(self, outputFolderPath=None):
        from PKDevTools.classes.Fetcher import fetcher
        import os
        if outputFolderPath is None:
            dirName = 'templates'
            outputFolder = os.path.join(os.getcwd(),dirName)
        else:
            outputFolder = outputFolderPath
        outputFolder = f"{outputFolder}{os.sep}" if not outputFolder.endswith(f"{os.sep}") else outputFolder
        if not os.path.isdir(outputFolder):
            os.makedirs(outputFolder, exist_ok=True)
        json1 = "https://raw.githubusercontent.com/polakowo/vectorbt/master/vectorbt/templates/dark.json"
        json2 = "https://raw.githubusercontent.com/polakowo/vectorbt/master/vectorbt/templates/light.json"
        json3 = "https://raw.githubusercontent.com/polakowo/vectorbt/master/vectorbt/templates/seaborn.json"
        fileURLs = [json1,json2,json3]
        fileFetcher = fetcher()
        from PKDevTools.classes.Utils import random_user_agent
        for url in fileURLs:
            try:
                path = os.path.join(outputFolder,url.split("/")[-1])
                if not os.path.exists(path):
                    # if self.shouldLog:
                    #     self.default_logger.debug(f"Fetching {url} to keep at {path}")
                    resp = fileFetcher.fetchURL(url=url,trial=3,timeout=5,headers={'user-agent': f'{random_user_agent()}'})
                    if resp is not None and resp.status_code == 200:
                        with open(path, "w") as f:
                            f.write(resp.text)
                # else:
                #     if self.shouldLog:
                #         self.default_logger.debug(f"Already exists: {path}")
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                # if self.shouldLog:
                #     self.default_logger.debug(e, exc_info=True)
                continue

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
        full52Week = data.head(50 * one_week)
        full52WeekHigh = full52Week["High"].max()
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return recent >= full52WeekHigh

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

        saveDict["52Wk-H"] = "{:.2f}".format(full52WeekHigh)
        saveDict["52Wk-L"] = "{:.2f}".format(full52WeekLow)
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
            "52Wk-H"
        ] = f"{highColor}{str('{:.2f}'.format(full52WeekHigh))}{colorText.END}"
        screenDict[
            "52Wk-L"
        ] = f"{lowColor}{str('{:.2f}'.format(full52WeekLow))}{colorText.END}"
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))

    # Find stocks that have broken through 10 days low.
    def find10DaysLowBreakout(self, df):
        if df is None or len(df) == 0:
            return False
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
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return (recent <= min(previousWeekLow, last1WeekLow)) and (
            last1WeekLow <= previousWeekLow
        )

    # Find stocks that have broken through 52 week low.
    def find52WeekLowBreakout(self, df):
        if df is None or len(df) == 0:
            return False
        # https://chartink.com/screener/52-week-low-breakout
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["Low"].iloc[0]
        # last1Week = data.head(one_week)
        # last2Week = data.head(2 * one_week)
        # previousWeek = last2Week.tail(one_week)
        full52Week = data.head(50 * one_week)
        # last1WeekLow = last1Week["Low"].min()
        # previousWeekLow = previousWeek["Low"].min()
        full52WeekLow = full52Week["Low"].min()
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return recent <= full52WeekLow

    # Find stocks that have broken through Aroon bullish crossover.
    def findAroonBullishCrossover(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        period = 14
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        aroondf = pktalib.Aroon(data["High"], data["Low"], period)
        recent = aroondf.tail(1)
        up = recent[f"AROONU_{period}"].iloc[0]
        down = recent[f"AROOND_{period}"].iloc[0]
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return up > down
    
    # Find ATR cross stocks
    def findATRCross(self, df,saveDict, screenDict):
        #https://chartink.com/screener/stock-crossing-atr
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        recentCandleHeight = self.getCandleBodyHeight(recent)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        atr = pktalib.ATR(data["High"],data["Low"],data["Close"], 14)
        atrCross = recentCandleHeight >= atr.tail(1).iloc[0]
        bullishRSI = recent["RSI"].iloc[0] >= 55 or recent["RSIi"].iloc[0] >= 55
        smav7 = pktalib.SMA(data["Volume"],timeperiod=7).tail(1).iloc[0]
        atrCrossCondition = atrCross and bullishRSI and (smav7 < recent["Volume"].iloc[0])
        saveDict["ATR"] = round(atr.tail(1).iloc[0],1)
        screenDict["ATR"] = saveDict["ATR"] #(colorText.GREEN if atrCrossCondition else colorText.FAIL) + str(atr.tail(1).iloc[0]) + colorText.END
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return atrCrossCondition
    
    def findATRTrailingStops(self,df,sensitivity=1, atr_period=10, ema_period=1,buySellAll=1,saveDict=None,screenDict=None):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first

        SENSITIVITY = sensitivity
        # Compute ATR And nLoss variable
        data["xATR"] = pktalib.ATR(data["High"], data["Low"], data["Close"], timeperiod=atr_period)
        data["nLoss"] = SENSITIVITY * data["xATR"]
        
        #Drop all rows that have nan, X first depending on the ATR preiod for the moving average
        data = data.dropna()
        data = data.reset_index()
        # Filling ATRTrailingStop Variable
        data["ATRTrailingStop"] = [0.0] + [np.nan for i in range(len(data) - 1)]
        
        for i in range(1, len(data)):
            data.loc[i, "ATRTrailingStop"] = self.xATRTrailingStop_func(
                data.loc[i, "Close"],
                data.loc[i - 1, "Close"],
                data.loc[i - 1, "ATRTrailingStop"],
                data.loc[i, "nLoss"],
            )
        data = self.computeBuySellSignals(data,ema_period=ema_period)
        if data is None:
            return False
        recent = data.tail(1)
        buy = recent["Buy"].iloc[0]
        sell = recent["Sell"].iloc[0]
        saveDict["B/S"] = "Buy" if buy else ("Sell" if sell else "NA")
        screenDict["B/S"] = ((colorText.GREEN + "Buy") if buy else ((colorText.FAIL+ "Sell") if sell else (colorText.WARN + "NA"))) + colorText.END
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return buy if buySellAll==1 else (sell if buySellAll == 2 else (True if buySellAll == 3 else False))


    # def identify_demand_zone(self,data, cmp):
    #     demand_zones = []
    #     drop_base_rally_zone = False
    #     rally_base_rally_zone = False
        
    #     # Additional variables to track base candle prices for proximal line calculation
    #     base_candle_prices = []
        
    #     for i in range(len(data) - 2):
    #         if data['Candle Type'][i] == 'Drop Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count <= 4:  # Maximum of 4 base candles for weekly or monthly timeframe, else 3 for daily
    #                 if j < len(data) and data['Candle Type'][j] == 'Rally Candle':
    #                     if data['Close'][j] > data['Low'][i] + 0.6 * data['Candle Range'][i] and data['High'][i] <= cmp:
    #                         # Check for one more rally candle or green base candle
    #                         k = j + 1
    #                         while k < len(data):
    #                             if data['Candle Type'][k] == 'Rally Candle' or (data['Candle Type'][k] == 'Base Candle' and data['Close'][k] > data['Open'][k]):
    #                                 demand_zones.append((i, j, 'Drop Base Rally', base_count))
    #                                 drop_base_rally_zone = True
    #                                 break
    #                             k += 1
    #         elif data['Candle Type'][i] == 'Rally Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count >= 1:  # At least one base candle required
    #                 if j < len(data) and data['Candle Type'][j] == 'Rally Candle':
    #                     if data['Close'][j] > data['Close'][i] and data['High'][i] <= cmp:  # New condition: close of 2nd rally candle > 1st rally candle
    #                         # Check for one more rally candle or green base candle
    #                         k = j + 1
    #                         while k < len(data):
    #                             if data['Candle Type'][k] == 'Rally Candle' or (data['Candle Type'][k] == 'Base Candle' and data['Close'][k] > data['Open'][k]):
    #                                 demand_zones.append((i, j, 'Rally Base Rally', base_count))
    #                                 rally_base_rally_zone = True
    #                                 break
    #                             k += 1
                            
    #         # Collect base candle prices for proximal line calculation
    #         if data['Candle Type'][i] == 'Base Candle':
    #             base_candle_prices.append(data['Close'][i])

    #     # Calculate proximal line price (highest price among base candles)
    #     proximal_line_price = max(base_candle_prices) if base_candle_prices else None

    #     return demand_zones, drop_base_rally_zone, rally_base_rally_zone, proximal_line_price

    # def identify_supply_zone(self,data, cmp):
    #     supply_zones = []
    #     rally_base_drop_zone = False
    #     drop_base_drop_zone = False
        
    #     # Additional variables to track base candle prices for proximal line calculation
    #     base_candle_prices = []
        
    #     for i in range(len(data) - 2):
    #         if data['Candle Type'][i] == 'Drop Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count <= 4:  # Maximum of 4 base candles for weekly or monthly timeframe, else 3 for daily
    #                 if j < len(data) and data['Candle Type'][j] == 'Drop Candle':
    #                     if data['Close'][i] < data['Low'][j] and data['Low'][i] >= cmp:  # New condition: close of drop candle < low of base candle
    #                         # New logic: Look for one more drop candle or red base candle
    #                         k = j + 1
    #                         while k < len(data) and (data['Candle Type'][k] == 'Drop Candle' or data['Close'][k] < data['Open'][k]):
    #                             k += 1
    #                         if k < len(data) and (data['Candle Type'][k] == 'Drop Candle' or data['Close'][k] < data['Open'][k]):
    #                             supply_zones.append((i, j, 'Drop Base Drop', base_count))
    #                             drop_base_drop_zone = True
    #         elif data['Candle Type'][i] == 'Rally Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count >= 1:  # At least one base candle required
    #                 if j < len(data) and data['Candle Type'][j] == 'Drop Candle':
    #                     if data['Close'][j] < data['Open'][j] and data['Low'][i] >= cmp:  # Modified condition: close of drop candle < open of drop candle
    #                         supply_zones.append((i, j, 'Rally Base Drop', base_count))
    #                         rally_base_drop_zone = True
                            
    #         # Collect base candle prices for proximal line calculation
    #         if data['Candle Type'][i] == 'Base Candle':
    #             base_candle_prices.append(data['Close'][i])

    #     # Calculate proximal line price (lowest price among base candles)
    #     proximal_line_price = min(base_candle_prices) if base_candle_prices else None

    #     return supply_zones, rally_base_drop_zone, drop_base_drop_zone, proximal_line_price

    # def calculate_demand_proximal_lines(self,data, demand_zones):
    #     proximal_line_prices = []
    #     for start, end, _, _ in demand_zones:
    #         base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), ['Open', 'Close']]
    #         max_price = base_candle_prices.max(axis=1).max()  # Get the maximum price among all base candles' open and close prices
    #         proximal_line_prices.append(max_price)
    #     return proximal_line_prices

    # def calculate_supply_proximal_lines(self,data, supply_zones):
    #     proximal_line_prices = []
    #     for start, end, _, _ in supply_zones:
    #         base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), ['Open', 'Close']]
    #         min_price = base_candle_prices.min(axis=1).min()  # Get the minimum price among all base candles' open and close prices
    #         proximal_line_prices.append(min_price)
    #     return proximal_line_prices
        
    # def calculate_demand_distal_lines(self,data, demand_zones):
    #     distal_line_prices = []
    #     for start, end, pattern, _ in demand_zones:
    #         if pattern == 'Drop Base Rally':
    #             # Logic for Drop Base Rally pattern: Take the lowest price among all components of the zone
    #             lowest_price = min(data['Low'][start:end + 1])  # Get the lowest price within the zone
    #             distal_line_prices.append(lowest_price)
    #         elif pattern == 'Rally Base Rally':
    #             # Logic for Rally Base Rally pattern: Take the lowest of only all base candle and followed rally candle
    #             base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), 'Low']
    #             rally_candle_prices = data.loc[(data['Candle Type'] == 'Rally Candle') & (data.index >= data.index[end]) & (data.index < data.index[end+1]), 'Low']
    #             all_prices = pd.concat([base_candle_prices, rally_candle_prices])
    #             lowest_price = all_prices.min() if not all_prices.empty else None
    #             distal_line_prices.append(lowest_price)
    #     return distal_line_prices

    # def calculate_supply_distal_lines(self,data, supply_zones):
    #     distal_line_prices = []
    #     for start, end, pattern, _ in supply_zones:
    #         if pattern == 'Rally Base Drop':
    #             # Logic for Rally Base Drop pattern: Take the highest price among all components of the zone
    #             highest_price = max(data['High'][start:end + 1])  # Get the highest price within the zone
    #             distal_line_prices.append(highest_price)
    #         elif pattern == 'Drop Base Drop':
    #             # Logic for Drop Base Drop pattern: Take the highest of only all base candles and followed drop candle
    #             base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), 'High']
    #             drop_candle_prices = data.loc[(data['Candle Type'] == 'Drop Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), 'High']
    #             all_prices = pd.concat([base_candle_prices, drop_candle_prices])
    #             highest_price = all_prices.max() if not all_prices.empty else None
    #             distal_line_prices.append(highest_price)
    #     return distal_line_prices

    # def is_zone_tested(self,data, start_index, end_index, proximal_line_price):
    #     """
    #     Check if the proximal line price has been tested by future prices.
        
    #     Args:
    #     - data: DataFrame containing stock data
    #     - start_index: Start index of the demand/supply zone
    #     - end_index: End index of the demand/supply zone
    #     - proximal_line_price: Proximal line price
        
    #     Returns:
    #     - True if the proximal line price is tested, False otherwise
    #     """
    #     for i in range(end_index + 1, len(data)):
    #         if data['Low'][i] <= proximal_line_price <= data['High'][i]:
    #             return True
    #     return False

    # def calculate_zone_range(self,proximal_line, distal_line):
    #     """
    #     Calculate the range of a zone given its proximal and distal lines.
        
    #     Args:
    #     - proximal_line: Proximal line price
    #     - distal_line: Distal line price
        
    #     Returns:
    #     - Range of the zone
    #     """
    #     if proximal_line is not None and distal_line is not None:
    #         return abs(proximal_line - distal_line)
    #     else:
    #         return None

    # def calculate_demand_zone_ranges(self,demand_zones, demand_proximal_lines, demand_distal_lines):
    #     """
    #     Calculate the range of each demand zone.
        
    #     Args:
    #     - demand_zones: List of demand zone tuples (start, end, pattern, base_count)
    #     - demand_proximal_lines: List of proximal line prices for demand zones
    #     - demand_distal_lines: List of distal line prices for demand zones
        
    #     Returns:
    #     - List of ranges corresponding to each demand zone
    #     """
    #     demand_zone_ranges = []
    #     for i, (start, end, _, _) in enumerate(demand_zones):
    #         range_of_zone = self.calculate_zone_range(demand_proximal_lines[i], demand_distal_lines[i])
    #         demand_zone_ranges.append(range_of_zone)
    #     return demand_zone_ranges

    # def calculate_supply_zone_ranges(self,supply_zones, supply_proximal_lines, supply_distal_lines):
    #     """
    #     Calculate the range of each supply zone.
        
    #     Args:
    #     - supply_zones: List of supply zone tuples (start, end, pattern, base_count)
    #     - supply_proximal_lines: List of proximal line prices for supply zones
    #     - supply_distal_lines: List of distal line prices for supply zones
        
    #     Returns:
    #     - List of ranges corresponding to each supply zone
    #     """
    #     supply_zone_ranges = []
    #     for i, (start, end, _, _) in enumerate(supply_zones):
    #         range_of_zone = self.calculate_zone_range(supply_proximal_lines[i], supply_distal_lines[i])
    #         supply_zone_ranges.append(range_of_zone)
    #     return supply_zone_ranges

    # def filter_stocks_by_distance(self,data,symbol_list, threshold_percent, timeframe):
    #     filtered_stocks = []
    #     for symbol in symbol_list:
    #         if data is not None:
    #             cmp = data.iloc[-1]['Close']  # Current market price
    #             demand_zones, _, _, demand_proximal_line = self.identify_demand_zone(data, cmp)  # Pass cmp argument here
    #             supply_zones, _, _, supply_proximal_line = self.identify_supply_zone(data, cmp)  # Pass cmp argument here
                
    #             # Check if either demand or supply zones exist for the stock
    #             if demand_zones or supply_zones:
    #                 filtered_stocks.append(symbol)

    #     return filtered_stocks
    
    # def findDemandSupplyZones(self,data,threshold_percent=1):        
    #     # Initialize count for filtered stocks
    #     count_filtered_stocks = 0

    #     # Analyze demand and supply zones for each stock and save results in a file
    #     with open("demand_supply_zones.txt", "w") as file:
    #         for symbol in data["Stock"]:
    #             if data is not None:
    #                 cmp = data.iloc[-1]['Close']  # Current market price
    #                 demand_zones, _, _, demand_proximal_line = self.identify_demand_zone(data, cmp)
    #                 supply_zones, _, _, supply_proximal_line = self.identify_supply_zone(data, cmp)

    #                 # Step 1: Calculate proximal lines for demand and supply zones
    #                 demand_proximal_lines = self.calculate_demand_proximal_lines(data, demand_zones)
    #                 supply_proximal_lines = self.calculate_supply_proximal_lines(data, supply_zones)
                    
    #                 # Step 2: Calculate distal lines for demand zones and supply zones
    #                 demand_distal_lines = self.calculate_demand_distal_lines(data, demand_zones)
    #                 supply_distal_lines = self.calculate_supply_distal_lines(data, supply_zones)

    #                 # Calculate range of demand and supply zones
    #                 demand_zone_ranges = self.calculate_demand_zone_ranges(demand_zones, demand_proximal_lines, demand_distal_lines)
    #                 supply_zone_ranges = self.calculate_supply_zone_ranges(supply_zones, supply_proximal_lines, supply_distal_lines)
                    
    #                 file.write(f"\n\nAnalysis for {symbol} ({timeframe}):")
                    
    #                 # Demand Zones
    #                 file.write("\n\nDemand Zones:")
    #                 if demand_zones:  # Check if demand_zones is not empty
    #                     for i, (start, end, pattern, base_count) in enumerate(demand_zones):
    #                         dist_from_cmp = abs((cmp - demand_proximal_lines[i]) / cmp) * 100
    #                         file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                         file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                         file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                         if demand_proximal_lines:
    #                             file.write(f"\nProximal Line Price: {demand_proximal_lines[i]:.2f}")
    #                         if demand_distal_lines:  # Include distal line price if available
    #                             file.write(f"\nDistal Line Price: {demand_distal_lines[i]:.2f}")
    #                         # Include zone range
    #                             file.write(f"\nZone Range: {demand_zone_ranges[i]:.2f}")       
    #                         # Check if proximal line is tested
    #                         tested = self.is_zone_tested(data, start, end, demand_proximal_lines[i])
    #                         if tested:
    #                             file.write("\nZone is Tested")
    #                         else:
    #                             file.write("\nFresh Zone")
    #                 else:
    #                     file.write("\nNo demand zone patterns found.")

    #                 # Supply Zones
    #                 file.write("\n\nSupply Zones:")
    #                 if supply_zones:  # Check if supply_zones is not empty
    #                     for i, (start, end, pattern, base_count) in enumerate(supply_zones):
    #                         dist_from_cmp = abs((cmp - supply_proximal_lines[i]) / cmp) * 100
    #                         file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                         file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                         file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                         if supply_proximal_lines:
    #                             file.write(f"\nProximal Line Price: {supply_proximal_lines[i]:.2f}")
    #                         if supply_distal_lines:  # Include distal line price if available
    #                             file.write(f"\nDistal Line Price: {supply_distal_lines[i]:.2f}")
    #                         # Include zone range
    #                             file.write(f"\nZone Range: {supply_zone_ranges[i]:.2f}")
    #                         # Check if proximal line is tested
    #                         tested = is_zone_tested(data, start, end, supply_proximal_lines[i])
    #                         if tested:
    #                             file.write("\nZone is Tested")
    #                         else:
    #                             file.write("\nFresh Zone")
    #                 else:
    #                     file.write("\nNo supply zone patterns found.")

    #                 # Check if the stock has either demand or supply zone within the threshold
    #                 has_demand_or_supply_within_threshold = any(
    #                     abs((cmp - price) / cmp) * 100 <= threshold_percent
    #                     for price in demand_proximal_lines + supply_proximal_lines
    #                 )
                    
    #                 # If the stock has demand or supply zone within the threshold, increment the count
    #                 if has_demand_or_supply_within_threshold:
    #                     count_filtered_stocks += 1

    #     # Filter stocks based on the percentage threshold and save the results in another file
    #     filtered_stocks = self.filter_stocks_by_distance(stock_symbols, threshold_percent, timeframe)

    #     with open("filtered_stocks_data.txt", "w") as file:
    #         file.write(f"Number of stocks Filtered: {count_filtered_stocks}\n\n")
    #         file.write("Filtered Stock Data:\n\n")
            
    #         for symbol in filtered_stocks:
    #             if data is not None:
    #                 cmp = data.iloc[-1]['Close']  # Current market price
    #                 demand_zones, _, _, demand_proximal_line = self.identify_demand_zone(data, cmp)
    #                 supply_zones, _, _, supply_proximal_line = self.identify_supply_zone(data, cmp)

    #                 # Step 1: Calculate proximal lines for demand and supply zones
    #                 demand_proximal_lines = self.calculate_demand_proximal_lines(data, demand_zones)
    #                 supply_proximal_lines = self.calculate_supply_proximal_lines(data, supply_zones)
                    
    #                 # Step 2: Calculate distal lines for demand zones and supply zones
    #                 demand_distal_lines = self.calculate_demand_distal_lines(data, demand_zones)
    #                 supply_distal_lines = self.calculate_supply_distal_lines(data, supply_zones)
                    
    #                 # Calculate range of demand and supply zones
    #                 demand_zone_ranges = self.calculate_demand_zone_ranges(demand_zones, demand_proximal_lines, demand_distal_lines)
    #                 supply_zone_ranges = self.calculate_supply_zone_ranges(supply_zones, supply_proximal_lines, supply_distal_lines)
                                    
    #                 # Check if the stock has either demand or supply zone within the threshold
    #                 has_demand_or_supply_within_threshold = any(
    #                     abs((cmp - price) / cmp) * 100 <= threshold_percent
    #                     for price in demand_proximal_lines + supply_proximal_lines
    #                 )
                    
    #                 # If the stock has demand or supply zone within the threshold, write its analysis
    #                 if has_demand_or_supply_within_threshold:
    #                     file.write(f"Analysis for {symbol} ({timeframe}):\n")
                        
    #                     # Demand Zones
    #                     file.write("\n\nDemand Zones:")
    #                     if demand_zones:  # Check if demand_zones is not empty
    #                         for i, (start, end, pattern, base_count) in enumerate(demand_zones):
    #                             dist_from_cmp = abs((cmp - demand_proximal_lines[i]) / cmp) * 100
    #                             if abs(dist_from_cmp) <= threshold_percent:  # Check if dist_from_cmp is within threshold
    #                                 file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                                 file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                                 file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                                 if demand_proximal_lines:
    #                                     file.write(f"\nProximal Line Price: {demand_proximal_lines[i]:.2f}")
    #                                 if demand_distal_lines:  # Include distal line price if available
    #                                     file.write(f"\nDistal Line Price: {demand_distal_lines[i]:.2f}")
    #                                 # Include zone range
    #                                     file.write(f"\nZone Range: {demand_zone_ranges[i]:.2f}")
    #                                 # Check if proximal line is tested
    #                                 tested = is_zone_tested(data, start, end, demand_proximal_lines[i])
    #                                 if tested:
    #                                     file.write("\nZone is Tested")
    #                                 else:
    #                                     file.write("\nFresh Zone")
    #                     else:
    #                         file.write("\nNo demand zone patterns found.")

    #                     # Supply Zones
    #                     file.write("\n\nSupply Zones:")
    #                     if supply_zones:  # Check if supply_zones is not empty
    #                         for i, (start, end, pattern, base_count) in enumerate(supply_zones):
    #                             dist_from_cmp = abs((cmp - supply_proximal_lines[i]) / cmp) * 100
    #                             if abs(dist_from_cmp) <= threshold_percent:  # Check if dist_from_cmp is within threshold
    #                                 file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                                 file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                                 file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                                 if supply_proximal_lines:
    #                                     file.write(f"\nProximal Line Price: {supply_proximal_lines[i]:.2f}")
    #                                 if supply_distal_lines:  # Include distal line price if available
    #                                     file.write(f"\nDistal Line Price: {supply_distal_lines[i]:.2f}")
    #                                 # Include zone range
    #                                     file.write(f"\nZone Range: {supply_zone_ranges[i]:.2f}")
    #                                 # Check if proximal line is tested
    #                                 tested = self.is_zone_tested(data, start, end, supply_proximal_lines[i])
    #                                 if tested:
    #                                     file.write("\nZone is Tested")
    #                                 else:
    #                                     file.write("\nFresh Zone")
    #                     else:
    #                         file.write("\nNo supply zone patterns found.")

    #                     file.write("\n\n")
                    
    #     print("Analysis completed and results saved.")

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
            screenDict["Pattern"] = saved[0] + (colorText.GREEN if action else colorText.FAIL) + f"BBands-SQZ-{'Buy' if action else 'Sell'}" + colorText.END
            saveDict["Pattern"] = saved[1] + f"TTM-SQZ-{'Buy' if action else 'Sell'}"
            return True
        elif candle3Sqz and candle2Sqz and candle1Sqz:
            # Last 3 candles in squeeze
            if filter not in [2,4]: # SqZ/All
                return False
            screenDict["Pattern"] = f'{saved[0]}{colorText.WARN}TTM-SQZ{colorText.END}'
            saveDict["Pattern"] = f'{saved[1]}TTM-SQZ'
            return True
        return False

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
        if df is None or len(df) == 0:
            return False
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
                colorText.WARN + "BO: 0 R: 0" + colorText.END
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
                        colorText.GREEN
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
                    colorText.FAIL
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
                        colorText.GREEN
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
                    colorText.FAIL
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
                    colorText.GREEN
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
                colorText.FAIL
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
                    colorText.GREEN
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
                colorText.FAIL
                + "BO: "
                + str(maxClose)
                + " R: 0"
                + colorText.END
            )
            return not alreadyBrokenout

    def findBullishAVWAP(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        reversedData = data[::-1]  # Reverse the dataframe so that its the oldest date first
        # Find the anchor point. Find the candle where there's a major dip.
        majorLow = reversedData["Low"].min()
        lowRow = reversedData[reversedData["Low"] == majorLow]
        anchored_date = lowRow.index[0]
        avwap = pktalib.AVWAP(df=reversedData,anchored_date=anchored_date)
        recentOpen = reversedData["Open"].tail(1).head(1).iloc[0]
        recentClose = reversedData["Close"].tail(1).head(1).iloc[0]
        recentLow = reversedData["Low"].tail(1).head(1).iloc[0]
        recentAVWAP = reversedData["anchored_VWAP"].tail(1).head(1).iloc[0]
        recentVol = reversedData["Volume"].tail(1).head(1).iloc[0]
        prevVol = reversedData["Volume"].tail(2).head(1).iloc[0]
        avwap.replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna(inplace=True)
        reversedData = reversedData.tail(len(avwap))
        diffFromAVWAP = (abs(recentClose-recentAVWAP)/recentAVWAP) * 100
        x = reversedData.index
        y = avwap.astype(float)
        # Create a sequance of integers from 0 to x.size to use in np.polyfit() call
        x_seq = np.arange(x.size)
        # call numpy polyfit() method with x_seq, y 
        fit = np.polyfit(x_seq, y, 1)
        fit_fn = np.poly1d(fit)
        slope = fit[0]
        # print('Slope = ', fit[0], ", ","Intercept = ", fit[1])
        # print(fit_fn)
        isBullishAVWAP = (slope <= 1 and # AVWAP is flat
                recentOpen == recentLow and recentLow !=0 and # Open = Low candle
                recentClose > recentAVWAP and recentAVWAP != 0 and # price near AVWAP
                recentVol > (self.configManager.volumeRatio)*prevVol and prevVol != 0 and # volumes spiked
                diffFromAVWAP <= self.configManager.anchoredAVWAPPercentage)

        if isBullishAVWAP:
            saveDict["AVWAP"] = round(recentAVWAP,2)
            screenDict["AVWAP"] = round(recentAVWAP,2)
            saveDict["Anchor"] = str(anchored_date).split(" ")[0]
            screenDict["Anchor"] = str(anchored_date).split(" ")[0]
        return isBullishAVWAP

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
    
    def findBuySellSignalsFromATRTrailing(self,df, key_value=1, atr_period=10, ema_period=200,buySellAll=1,saveDict=None,screenDict=None):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first

        # Calculate ATR and xATRTrailingStop
        xATR = np.array(pktalib.ATR(data['High'], data['Low'], data['Close'], timeperiod=atr_period))
        nLoss = key_value * xATR
        src = data['Close']
        # Initialize arrays
        xATRTrailingStop = np.zeros(len(data))
        xATRTrailingStop[0] = src[0] - nLoss[0]

        # Calculate xATRTrailingStop using vectorized operations
        mask_1 = (src > np.roll(xATRTrailingStop, 1)) & (np.roll(src, 1) > np.roll(xATRTrailingStop, 1))
        mask_2 = (src < np.roll(xATRTrailingStop, 1)) & (np.roll(src, 1) < np.roll(xATRTrailingStop, 1))
        mask_3 = src > np.roll(xATRTrailingStop, 1)

        xATRTrailingStop = np.where(mask_1, np.maximum(np.roll(xATRTrailingStop, 1), src - nLoss), xATRTrailingStop)
        xATRTrailingStop = np.where(mask_2, np.minimum(np.roll(xATRTrailingStop, 1), src + nLoss), xATRTrailingStop)
        xATRTrailingStop = np.where(mask_3, src - nLoss, xATRTrailingStop)

        mask_buy = (np.roll(src, 1) < xATRTrailingStop) & (src > np.roll(xATRTrailingStop, 1))
        mask_sell = (np.roll(src, 1) > xATRTrailingStop) & (src < np.roll(xATRTrailingStop, 1))

        pos = np.zeros(len(data))
        pos = np.where(mask_buy, 1, pos)
        pos = np.where(mask_sell, -1, pos)
        pos[~((pos == 1) | (pos == -1))] = 0

        ema = np.array(pktalib.EMA(data['Close'], timeperiod=ema_period))

        buy_condition_utbot = (xATRTrailingStop > ema) & (pos > 0) & (src > ema)
        sell_condition_utbot = (xATRTrailingStop < ema) & (pos < 0) & (src < ema)

        # The resulting trend array holds values of 1 (buy), -1 (sell), or 0 (neutral).
        trend = np.where(buy_condition_utbot, 1, np.where(sell_condition_utbot, -1, 0))
        trend_arr = np.array(trend)
        data.insert(len(data.columns), "trend", trend_arr)
        trend = trend[0]
        saveDict["B/S"] = "Buy" if trend == 1 else ("Sell" if trend == -1 else "NA")
        screenDict["B/S"] = (colorText.GREEN + "Buy") if trend == 1 else ((colorText.FAIL+ "Sell") if trend == -1 else (colorText.WARN + "NA")) + colorText.END
        return buySellAll == trend

    # 1. Cup Formation (Bowl)
    # During the cup formation phase, the price experiences a prolonged downtrend or consolidation, 
    # creating a rounded or U-shaped bottom. This phase represents a period of price stabilization, 
    # where investors who bought at higher levels are selling to cut their losses, and new buyers 
    # cautiously enter the market as they see potential value at these lower price levels. The 
    # psychology during this phase includes:
        # Capitulation and Despair:
        # The initial phase of the cup is marked by capitulation, where panicked investors sell off 
        # their holdings due to fear and negative sentiment.
    # Value Perception:
        # As the price stabilizes and gradually starts to rise, some investors perceive value in the 
        # stock at these lower levels, leading to accumulation of shares.
    
    # 2. Handle Formation
    # The handle formation phase follows the cup’s rounded bottom, characterized by a short-term 
    # decline in price. This decline typically ranges from 10% to 20% and is often referred to as 
    # the “handle” of the pattern. During this phase, the psychology involves:
    # Consolidation and Profit-Taking:
        # After the cup’s advance, some investors decide to take profits, leading to a brief pullback 
        # in price. This retracement is seen as a normal part of the market cycle.
    # Temporary Skepticism:
        # The pullback in price could make some investors skeptical about the stock’s future prospects, 
        # creating a cautious sentiment.
    
    # 3. Breakout and Upside Potential
    # The psychology behind the breakout from the handle involves the culmination of buying pressure 
    # exceeding selling pressure. This breakout is signaled when the price breaks above the resistance 
    # level formed by the cup’s rim. Investors who missed the earlier opportunity or who had been 
    # waiting for confirmation now step in, leading to renewed buying interest. The psychology during 
    # this phase includes:
    # Confirmation of Strength:
        # The breakout above the resistance level validates the bullish sentiment and confirms that the 
        # consolidation phase is ending. This attracts traders looking for confirmation before committing 
        # capital.
    # Fear of Missing Out (FOMO):
        # As the price starts to rise and gain momentum, FOMO can kick in, driving more investors to buy 
        # in at fear of missing out on potential gains.
    # Recovery and Optimism:
        # The price’s ability to surpass previous highs reinforces optimism, encouraging further buying 
        # from both existing and new investors.
    def findCupAndHandlePattern(self, df, stockName):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first

        df_point = pd.DataFrame(columns=['StockName', 'DateK', 'DateA', 'DateB', 'DateC', 'DateD', 'Gamma'])

        data = data.reset_index()
        data['Date'] = data['Date'].apply(lambda x : x.strftime('%Y-%m-%d'))
        data['Close_ch'] = data['Close'].shift(+1)
        data['rpv'] = ((data['Close'] / data['Close_ch']) - 1) * data['Volume']
        data['SMA50_Volume'] = data.Volume.rolling(50).mean()
        data['SMA50_rpv'] = data.rpv.rolling(50).mean()

        T = 0
        i = 1
        t = 51
        foundStockWithCupNHandle = False
        while t < len(data)-T:
            dat = data.loc[t:]
            Dk = dat.loc[t]['Date']
            Pk = dat.loc[t]['Close']   
            # search for region K to A
            k = 25
            while k > 15:
                #print('Searching SETUP with width = ', k)
                datA = dat.loc[:t+k] # Dk = t
                # first find absolute maxima point A
                Da_index = datA[datA['Close'] == max(datA['Close'])]['Date'].index[0]
                Da_value = datA[datA['Close'] == max(datA['Close'])]['Date'].values[0]
                Pa_index = datA[datA['Close'] == max(datA['Close'])]['Close'].index[0]
                Pa_value = datA[datA['Close'] == max(datA['Close'])]['Close'].values[0]
                uprv1 = abs(datA.loc[t:Da_index].loc[datA['rpv'] > 0, :]['rpv'].mean())
                dprv1 = abs(datA.loc[t:Da_index].loc[datA['rpv'] <= 0, :]['rpv'].mean())
                if (dprv1 == 'NaN') | (dprv1 == 0):
                    dprv1 = datA['SMA50_rpv'].mean()   
                alpha1 = uprv1/dprv1
                #delta = Pa_index/t 
                delta = Pa_value/Pk
                if (delta > 1) & (alpha1 > 1):
                    #print('Okay good setup! Lets move on now')
                    a = 40
                    while a > 10:
                        #print('Lets search for LEFT SIDE CUP with width = ', a)
                        datB = dat.loc[Da_index:Da_index+a]
                        Db_index = datB[datB['Close'] == min(datB['Close'])]['Date'].index[0]
                        Db_value = datB[datB['Close'] == min(datB['Close'])]['Date'].values[0]
                        Pb_index = datB[datB['Close'] == min(datB['Close'])]['Close'].index[0]
                        Pb_value = datB[datB['Close'] == min(datB['Close'])]['Close'].values[0]
                        avg_vol = datB['Volume'].mean()
                        avg_ma_vol = data['SMA50_Volume'].mean()
                        if (Pb_value < Pa_value) & (avg_vol < avg_ma_vol):
                            #print("Voila! You found the bottom, it's all uphill from here")
                            b = a
                            while b > round(a/3):
                                #print("Let's search for RIGHT SIDE CUP with width = ", b)
                                datC = dat.loc[Db_index:Db_index+b+1]
                                Dc_index = datC[datC['Close'] == max(datC['Close'])]['Date'].index[0]
                                Dc_value = datC[datC['Close'] == max(datC['Close'])]['Date'].values[0]
                                Pc_index = datC[datC['Close'] == max(datC['Close'])]['Close'].index[0]
                                Pc_value = datC[datC['Close'] == max(datC['Close'])]['Close'].values[0]
                                uprv2 = abs(datC.loc[datC['rpv'] > 0, :]['rpv'].mean())
                                dprv2 = abs(datC.loc[datC['rpv'] <= 0, :]['rpv'].mean())
                                if (dprv2 == 'NaN') | (dprv2 == 0):
                                    dprv2 = datC['SMA50_rpv'].mean()      
                                alpha2 = uprv2/dprv2
                                if (Pc_value > Pb_value) & (alpha2 > 1):
                                    #print("Almost there... be patient now! :D")
                                    # search for region C to D
                                    c = b/2
                                    while c > round(b/4):
                                        #print("Let's search for the handle now with width = ", c)
                                        #print(t, " ", k, " ", a, " ", b, " ", c)
                                        datD = dat.loc[Dc_index:Dc_index+c+1]
                                        Dd_index = datD[datD['Close'] == min(datD['Close'])]['Date'].index[0]
                                        Dd_value = datD[datD['Close'] == min(datD['Close'])]['Date'].values[0]
                                        Pd_index = datD[datD['Close'] == min(datD['Close'])]['Close'].index[0]
                                        Pd_value = datD[datD['Close'] == min(datD['Close'])]['Close'].values[0]
                                        uprv3 = abs(datD.loc[datD['rpv'] > 0, :]['rpv'].mean())
                                        dprv3 = abs(datD.loc[datD['rpv'] <= 0, :]['rpv'].mean())
                                        if (dprv3 == 'NaN') | (dprv3 == 0):
                                            dprv3 = datD['SMA50_rpv'].mean()      
                                        beta = uprv2/dprv3
                                        if (Pd_value <= Pc_value) & (Pd_value > 0.8 * Pc_value + 0.2 * Pb_value) & (beta > 1):
                                            if (Pc_value <= Pa_value) & (Pd_value > Pb_value):
                                                foundStockWithCupNHandle = True
                                                gamma = math.log(alpha2) + math.log(beta) + delta
                                                df_point.loc[len(df_point)] = [stockName, Dk, Da_value, Db_value, Dc_value, Dd_value, gamma]
                                                #print("Hurrah! Got "+str(i)+" hits!")
                                                k = 15
                                                a = 10
                                                b = round(a/3)
                                                c = round(b/4)
                                                i = i+1
                                                t = t+15
                                                break
                                        c = c-1
                                b = b-1
                        a = a-1
                k = k-1
            t = t + 1
        return foundStockWithCupNHandle, df_point

    def findCurrentSavedValue(self, screenDict, saveDict, key):
        existingScreen = screenDict.get(key)
        existingSave = saveDict.get(key)
        existingScreen = f"{existingScreen}, " if (existingScreen is not None and len(existingScreen) > 0) else ""
        existingSave = f"{existingSave}, " if (existingSave is not None and len(existingSave) > 0) else ""
        return existingScreen, existingSave

    def findHigherBullishOpens(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(2)
        if len(recent) < 2:
            return False
        return recent["Open"].iloc[0] > recent["High"].iloc[1]

    # Find stocks that opened higher than the previous high
    def findHigherOpens(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(2)
        if len(recent) < 2:
            return False
        return recent["Open"].iloc[0] > recent["Close"].iloc[1]

    # Find DEEL Momentum
    def findHighMomentum(self, df):
        #https://chartink.com/screener/deel-momentum-rsi-14-mfi-14-cci-14
        if df is None or len(df) < 2:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        mfis = pktalib.MFI(data["High"],data["Low"],data["Close"],data["Volume"], 14)
        ccis = pktalib.CCI(data["High"],data["Low"],data["Close"], 14)
        sma7 = pktalib.SMA(data["Close"], 7).tail(2)
        sma20 = pktalib.SMA(data["Close"], 20).tail(2)
        recent = data.tail(2)
        percentChange = round((recent["Close"].iloc[1] - recent["Close"].iloc[0]) *100/recent["Close"].iloc[0],1)
        rsi = recent["RSI"].iloc[1]
        mfi = mfis.tail(1).iloc[0]
        cci = ccis.tail(1).iloc[0]
        hasDeelMomentum = percentChange >= 1 and ((rsi>= 68 and mfi >= 68 and cci >= 110) or (rsi>= 50 and mfi >= 50 and recent["Close"].iloc[1] >= sma7.iloc[1] and recent["Close"].iloc[1] >= sma20.iloc[1]))
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return hasDeelMomentum

    def findIntradayHighCrossover(self, df, afterTimestamp=None):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        diff_df = None
        try:
            # Let's only consider those candles that are after the alert issue-time in the mornings + 2 candles (for buy/sell)
            diff_df = data[data.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30').to_datetime64()]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30').to_datetime64()
        except: # pragma: no cover
            diff_df = data[data.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30', utc=True)]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30', utc=True)
            pass
        dayHighAfterAlert = diff_df["High"].max()
        highRow = diff_df[diff_df["High"] >= dayHighAfterAlert]
        if highRow is not None and len(highRow) > 0:
            highRow = highRow.tail(1)
        return highRow.index[-1], highRow

    def findIntradayOpenSetup(self,df,df_intraday,saveDict,screenDict,buySellAll=1):
        if df is None or len(df) == 0 or df_intraday is None or len(df_intraday) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        previousDay = data.head(1)
        prevDayHigh = previousDay["High"].iloc[0]
        prevDayLow = previousDay["Low"].iloc[0]
        candleDurations = [1,5,10,15,30]
        int_df = None
        hasIntradaySetup = False
        for candle1MinuteNumberSinceMarketStarted in candleDurations:
            try:
                int_df = df_intraday[df_intraday.index <=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+candle1MinuteNumberSinceMarketStarted}:00+05:30').to_datetime64()]
            except: # pragma: no cover
                int_df = df_intraday[df_intraday.index <=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+candle1MinuteNumberSinceMarketStarted}:00+05:30', utc=True)]
                pass
            if int_df is not None and len(int_df) > 0:
                combinedCandle = {"Open":self.getMorningOpen(int_df), "High":max(int_df["High"]), 
                                "Low":min(int_df["Low"]),"Close":self.getMorningClose(int_df),
                                "Adj Close":int_df["Adj Close"][-1],"Volume":sum(int_df["Volume"])}
                openPrice = combinedCandle["Open"]
                lowPrice = combinedCandle["Low"]
                closePrice = combinedCandle["Close"]
                highPrice = combinedCandle["High"]
                if buySellAll == 1 or buySellAll == 3:
                    hasIntradaySetup = openPrice == lowPrice and openPrice < prevDayHigh and closePrice > prevDayHigh
                elif buySellAll == 2 or buySellAll == 3:
                    hasIntradaySetup = openPrice == highPrice and openPrice > prevDayLow and closePrice < prevDayLow
                if hasIntradaySetup:
                    saveDict["B/S"] = f"{'Buy' if buySellAll == 1 else ('Sell' if buySellAll == 2 else 'All')}-{candle1MinuteNumberSinceMarketStarted}m"
                    screenDict["B/S"] = (colorText.GREEN if buySellAll == 1 else (colorText.FAIL if buySellAll == 2 else colorText.WARN)) + f"{'Buy' if buySellAll == 1 else ('Sell' if buySellAll == 2 else 'All')}-{candle1MinuteNumberSinceMarketStarted}m" + colorText.END
                    break
        return hasIntradaySetup

    def findIntradayShortSellWithPSARVolumeSMA(self, df,df_intraday):
        if df is None or len(df) == 0 or df_intraday is None or len(df_intraday) == 0:
            return False
        data = df.copy()
        data_int = df_intraday.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data_int = pd.DataFrame(data_int)['Close'].resample('30T', offset='15min').ohlc()
        # data_int = data_int[::-1]  # Reverse the dataframe so that its the oldest date first
        if len(data_int) < 5: # we need TMA for period 5
            return False
        data.loc[:,'PSAR'] = pktalib.psar(data["High"],data["Low"],acceleration=0.08)
        data_int.loc[:,'TMA5'] = pktalib.TriMA(data_int["close"],length=5)
        recent = data.tail(4)
        recent = recent[::-1]
        recent_i = data_int[::-1]
        recent_i = recent_i.head(2)
        # recent_i = recent_i[::-1]
        if len(recent) < 4 or len(recent_i) < 2:
            return False
        # daily PSAR crossed above recent 30m TMA
        cond1 = recent["PSAR"].iloc[0] >= recent_i["TMA5"].iloc[0] and \
                recent["PSAR"].iloc[1] <= recent_i["TMA5"].iloc[1]
        # Daily volume > 1400k
        cond2 = cond1 and (recent["Volume"].iloc[0] > 1400000)
        # Daily close above 50
        cond4 = cond2 and recent["Close"].iloc[0] > 50
        return cond4

    def findIPOLifetimeFirstDayBullishBreak(self, df):
        if df is None or len(df) == 0 or len(df) >= 220:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data.dropna(axis=0, how="all", inplace=True) # Maybe there was no trade done at these times?
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        return data["High"].iloc[0] >= data["High"].max()

    def findMACDCrossover(self, df, afterTimestamp=None, nthCrossover=1, upDirection=True, minRSI=60):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data.dropna(axis=0, how="all", inplace=True) # Maybe there was no trade done at these times?
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macdLine, macdSignal, macdHist = pktalib.MACD(data["Close"], 12, 26, 9)
        # rsi_df = pktalib.RSI(data["Close"], 14)
        line_df = pd.DataFrame(macdLine)
        signal_df = pd.DataFrame(macdSignal)
        vol_df = data["Volume"]
        diff_df = pd.concat([line_df, signal_df, signal_df-line_df,vol_df], axis=1)
        diff_df.columns = ["line","signal","diff","vol"]
        diff_df = diff_df[diff_df["vol"] > 0] # We're not going to do anything with a candle where there was no trade.
        # brokerSqrOfftime = None
        try:
            # Let's only consider those candles that are after the alert issue-time in the mornings + 2 candles (for buy/sell)
            diff_df = diff_df[diff_df.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30').to_datetime64()]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30').to_datetime64()
        except: # pragma: no cover
            diff_df = diff_df[diff_df.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30', utc=True)]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30', utc=True)
            pass
        index = len(diff_df)
        crossOver = 0
        
        # Loop until we've found the nth crossover for MACD or we've reached the last point in time
        while (crossOver < nthCrossover and index > 0):
            try:
                if diff_df["diff"][index-1] < 0: # Signal line has not crossed yet and is below the zero line
                    while((diff_df["diff"][index-1] < 0 and index >=0)): # and diff_df.index <= brokerSqrOfftime): # or diff_df["rsi"][index-1] <= minRSI):
                        # Loop while Signal line has not crossed yet and is below the zero line and we've not reached the last point
                        index -= 1
                else:
                    while((diff_df["diff"][index-1] >= 0 and index >=0)): # and diff_df.index <= brokerSqrOfftime): # or diff_df["rsi"][index-1] <= minRSI):
                        # Loop until signal line has not crossed yet and is above the zero line
                        index -= 1
            except: # pragma: no cover
                continue
            crossOver += 1
        ts = diff_df.tail(len(diff_df)-index +1).head(1).index[-1]
        return ts, data[data.index == ts] #df.head(len(df) -index +1).tail(1)

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

    def findPerfectShortSellsFutures(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data.loc[:,'BBands-U'], data.loc[:,'BBands-M'], data.loc[:,'BBands-L'] = pktalib.BBANDS(data["Close"], 20)
        recent = data.tail(4)
        recent = recent[::-1]
        if len(recent) < 4:
            return False
        # 1 day ago high > 2 days ago high
        cond1 = recent["High"].iloc[1] > recent["High"].iloc[2]
        # 1 day ago close < 2 days ago high
        cond2 = cond1 and (recent["Close"].iloc[1] < recent["High"].iloc[2])
        # 1 day ago volume > 3 days ago volume
        cond3 = cond2 and (recent["Volume"].iloc[1] > recent["Volume"].iloc[3])
        # daily high < 1 day ago high
        cond4 = cond3 and (recent["High"].iloc[0] < recent["High"].iloc[1])
        # daily close crossed below daily lower bollinger band(20,2)
        cond5 = cond4 and (recent["Close"].iloc[0] <= recent["BBands-L"].iloc[0] and \
                           recent["Close"].iloc[1] >= recent["BBands-L"].iloc[1])
        return cond5
    
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
        highestHigh8From30 = round(data.head(39).tail(8).describe()["High"]["max"], 2)
        data = data.head(200)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        vol200 = pktalib.SMA(data["Volume"],timeperiod=200)
        data["SMA200V"] = vol200
        vol50 = pktalib.SMA(data["Volume"],timeperiod=50)
        data["SMA50V"] = vol50
        recent = data.tail(1)
        sma200v = recent["SMA200V"].iloc[0]
        sma50v = recent["SMA50V"].iloc[0]
        if (
            np.isnan(recentClose)
            or np.isnan(highestHigh200)
            or np.isnan(highestHigh30)
            or np.isnan(highestHigh200From30)
            or np.isnan(highestHigh8From30)
            or np.isnan(recentVolume)
            or np.isnan(sma200v)
            or np.isnan(sma50v)
        ):
            return False
        if (
            (recentClose > highestHigh200)
            and (((highestHigh30 < highestHigh200From30) and (recentVolume > sma200v)) or \
                 ((highestHigh30 < highestHigh8From30) and (recentVolume > sma50v))
                )
        ):
            saveDict["Breakout"] = saveDict["Breakout"] + "(Potential)"
            screenDict["Breakout"] = screenDict["Breakout"] + (
                colorText.GREEN + " (Potential)" + colorText.END
            )
            return True
        return False

    def findPriceActionCross(self, df, ma, daysToConsider=1, baseMAOrPrice=None, isEMA=False,maDirectionFromBelow=True):
        ma_val = pktalib.EMA(df["Close"],int(ma)) if isEMA else pktalib.SMA(df["Close"],int(ma))
        ma = ma_val.tail(daysToConsider).head(1).iloc[0]
        ma_prev = ma_val.tail(daysToConsider+1).head(1).iloc[0]
        base = baseMAOrPrice.tail(daysToConsider).head(1).iloc[0]
        base_prev = baseMAOrPrice.tail(daysToConsider+1).head(1).iloc[0]
        percentageDiff = round(100*(base-ma)/ma,1)
        if maDirectionFromBelow: # base crosses ma line from below
            return (ma <= base and ma_prev >= base_prev), percentageDiff
        else: # base crosses ma line from above
            return (ma >= base and ma_prev <= base_prev), percentageDiff
        
    def findProbableShortSellsFutures(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        recent = data.tail(4)
        recent = recent[::-1]
        if len(recent) < 4:
            return False
        # 1 day ago high > 2 days ago high
        cond1 = recent["High"].iloc[1] > recent["High"].iloc[2]
        # daily close < 1 day ago high
        cond2 = cond1 and (recent["Close"].iloc[0] < recent["High"].iloc[1])
        # Daily volume > 3 days ago volume
        cond3 = cond2 and (recent["Volume"].iloc[0] > recent["Volume"].iloc[3])
        # daily high < 1 day ago high
        cond4 = cond3 and (recent["High"].iloc[0] < recent["High"].iloc[1])
        return cond4
    
    # Find stocks with reversing PSAR and RSI
    def findPSARReversalWithRSI(self, df, screenDict, saveDict,minRSI=50):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data[::-1]
        psar = pktalib.psar(data["High"],data["Low"])
        if len(psar) < 3:
            return False
        psar = psar.tail(3)
        data = data.tail(3)
        # dayMinus2Psar = psar.iloc[0]
        dayMinus1Psar = psar.iloc[1]
        dayPSAR = psar.iloc[2]
        # dayMinus2Close = data["Close"].iloc[0]
        dayMinus1Close = data["Close"].iloc[1]
        dayClose = data["Close"].iloc[2]
        # dayMinus2RSI = data["RSI"].iloc[0]
        dayMinus1RSI = data["RSI"].iloc[1]
        dayRSI = data["RSI"].iloc[2]
        
        hasReversal= (((dayMinus1Psar >= dayMinus1Close) and \
                    (dayClose >= dayPSAR)) and \
                    (dayMinus1RSI <= minRSI) and \
                    (dayRSI >= dayMinus1RSI))
        if hasReversal:
            saved = self.findCurrentSavedValue(screenDict,saveDict, "Pattern")
            screenDict["Pattern"] = (
                saved[0] 
                + colorText.GREEN
                + f"PSAR-RSI-Rev"
                + colorText.END
            )
            saveDict["Pattern"] = saved[1] + f"PSAR-RSI-Rev"
                # (((dayMinus2Psar >= dayMinus2Close) and \
                # ((dayMinus1Close >= dayMinus1Psar) and \
                # (dayClose >= dayPSAR))) and \
                # (dayMinus2RSI >= minRSI) and \
                # (dayMinus1RSI >= dayMinus2RSI) and \
                # (dayRSI >= dayMinus1RSI)) or \
        return hasReversal

    # Find stock reversing at given MA
    def findReversalMA(self, df, screenDict, saveDict, maLength, percentage=0.02):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        maRange = [9, 10, 20, 50, 200] if maLength in [9,10,20,50,100] else [9,10,20,50,100,maLength]
        results = []
        hasReversals = False
        data = data[::-1]
        saved = self.findCurrentSavedValue(screenDict,saveDict, "MA-Signal")
        for maLength in maRange:
            dataCopy = data
            if self.configManager.useEMA or maLength == 9:
                maRev = pktalib.EMA(dataCopy["Close"], timeperiod=maLength)
            else:
                maRev = pktalib.MA(dataCopy["Close"], timeperiod=maLength)
            try:
                dataCopy.drop("maRev", axis=1, inplace=True, errors="ignore")
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception:# pragma: no cover
                pass
            dataCopy.insert(len(dataCopy.columns), "maRev", maRev)
            dataCopy = dataCopy[::-1].head(4)
            bullishMAReversal = dataCopy["maRev"].iloc[0] >= dataCopy["maRev"].iloc[1] and \
                dataCopy["maRev"].iloc[1] >= dataCopy["maRev"].iloc[2] and \
                    dataCopy["maRev"].iloc[2] < dataCopy["maRev"].iloc[3]
            bullishClose = dataCopy.head(1)["Close"].iloc[0] >= dataCopy.head(1)["maRev"].iloc[0]
            bearishMAReversal = dataCopy["maRev"].iloc[0] <= dataCopy["maRev"].iloc[1] and \
                dataCopy["maRev"].iloc[1] <= dataCopy["maRev"].iloc[2] and \
                    dataCopy["maRev"].iloc[2] > dataCopy["maRev"].iloc[3]
            isRecentCloseWithinPercentRange = dataCopy.equals(dataCopy[(dataCopy.Close >= (dataCopy.maRev - (dataCopy.maRev * percentage))) & (dataCopy.Close <= (dataCopy.maRev + (dataCopy.maRev * percentage)))])
            if (isRecentCloseWithinPercentRange and bullishClose and bullishMAReversal) or \
                (isRecentCloseWithinPercentRange and not bullishClose and bearishMAReversal):
                hasReversals = True
                results.append(str(maLength))
        if hasReversals:
            screenDict["MA-Signal"] = (
                saved[0] 
                + (colorText.GREEN if bullishMAReversal else (colorText.FAIL if bearishMAReversal else colorText.WARN))
                + f"Reversal-[{','.join(results)}]{'EMA' if (maLength == 9 or self.configManager.useEMA) else 'MA'}"
                + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + f"Reversal-[{','.join(results)}]{'EMA' if (maLength == 9 or self.configManager.useEMA) else 'MA'}"
        return hasReversals
    
    # Find stocks with rising RSI from lower levels
    def findRisingRSI(self, df, rsiKey="RSI"):
        if df is None or len(df) == 0:
            return False
        if rsiKey not in df.columns:
            return False
        data = df.copy()
        data = data[::-1]
        data = data.tail(3)
        if len(data) < 3:
            return False
        dayMinus2RSI = data["RSI"].iloc[0]
        dayMinus1RSI = data["RSI"].iloc[1]
        dayRSI = data["RSI"].iloc[2]
        returnValue = (dayMinus2RSI <= 35 and dayMinus1RSI > dayMinus2RSI and dayRSI > dayMinus1RSI) or \
                (dayMinus1RSI <= 35 and dayRSI > dayMinus1RSI)
        if rsiKey == "RSI":
            returnValue = self.findRisingRSI(df, rsiKey="RSIi") or returnValue
        return returnValue

    # Find stock showing RSI crossing with RSI 9 SMA
    def findRSICrossingMA(self, df, screenDict, saveDict,lookFor=1, maLength=9, rsiKey="RSI"):
        if df is None or len(df) == 0:
            return False
        if rsiKey not in df.columns:
            return False
        data = df.copy()
        data = data[::-1]
        maRsi = pktalib.MA(data[rsiKey], timeperiod=maLength)
        data = data[::-1].head(3)
        maRsi = maRsi[::-1].head(3)
        saved = self.findCurrentSavedValue(screenDict,saveDict,"Trend")
        if lookFor in [1,3] and maRsi.iloc[0] <= data[rsiKey].iloc[0] and maRsi.iloc[1] > data[rsiKey].iloc[1]:
            screenDict['MA-Signal'] = saved[0] + colorText.GREEN + f'RSI-MA-Buy' + colorText.END
            saveDict['MA-Signal'] = saved[1] + f'RSI-MA-Buy'
            return True if (rsiKey == "RSIi") else (self.findRSICrossingMA(df, screenDict, saveDict,lookFor=lookFor, maLength=maLength, rsiKey="RSIi") or True)
        elif lookFor in [2,3] and maRsi.iloc[0] >= data[rsiKey].iloc[0] and maRsi.iloc[1] < data[rsiKey].iloc[1]:
            screenDict['MA-Signal'] = saved[0] + colorText.FAIL + f'RSI-MA-Sell' + colorText.END
            saveDict['MA-Signal'] = saved[1] + f'RSI-MA-Sell'
            return True if (rsiKey == "RSIi") else (self.findRSICrossingMA(df, screenDict, saveDict,lookFor=lookFor, maLength=maLength, rsiKey="RSIi") or True)
        return False if (rsiKey == "RSIi") else (self.findRSICrossingMA(df, screenDict, saveDict,lookFor=lookFor, maLength=maLength, rsiKey="RSIi"))
    
    def findRSRating(self, stock_rs_value=-1, index_rs_value=-1,df=None,screenDict={}, saveDict={}):
        if stock_rs_value <= 0:
            stock_rs_value = self.calc_relative_strength(df=df)
        rs_rating = round(100 * ( stock_rs_value / index_rs_value ),2)
        screenDict[f"RS_Rating{self.configManager.baseIndex}"] = rs_rating
        saveDict[f"RS_Rating{self.configManager.baseIndex}"] = rs_rating
        return rs_rating
    
    # Relative volatality measure
    def findRVM(self, df=None,screenDict={}, saveDict={}):
        if df is None or len(df) == 0 or len(df) < 144:
            return 0
        # RVM over the lookback period of 15 periods
        rvm = pktalib.RVM(df["High"],df["Low"],df["Close"],15)
        screenDict["RVM(15)"] = rvm
        saveDict["RVM(15)"] = rvm
        return rvm

    def findShortSellCandidatesForVolumeSMA(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data.loc[:,'SMAV10'] = pktalib.SMA(data["Volume"], 10)
        recent = data.tail(4)
        recent = recent[::-1]
        if len(recent) < 4:
            return False
        # daily close < 1 day ago close * .97
        cond1 = recent["Close"].iloc[0] < recent["Close"].iloc[1] * 0.97
        # Daily volume > 100k
        cond2 = cond1 and (recent["Volume"].iloc[0] > 100000)
        # Daily volume * Daily Close > 1000k
        cond3 = cond2 and (recent["Volume"].iloc[0] * recent["Close"].iloc[0] > 1000000)
        # Daily close above 8
        cond4 = cond3 and recent["Close"].iloc[0] > 8
        cond5 = cond4 and (recent["Volume"].iloc[0] > recent["SMAV10"].iloc[0] * 0.75)
        return cond5
    
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
                    saved[0] + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Unknown"
                return saveDict["Trend"]
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                slope, _ = 0, 0
            angle = np.rad2deg(np.arctan(slope))
            if angle == 0:
                screenDict["Trend"] = (
                    saved[0] + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Unknown"
            elif angle <= 30 and angle >= -30:
                screenDict["Trend"] = (
                    saved[0] + colorText.WARN + "Sideways" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Sideways"
            elif angle >= 30 and angle < 61:
                screenDict["Trend"] = (
                    saved[0] + colorText.GREEN + "Weak Up" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Weak Up"
            elif angle >= 60:
                screenDict["Trend"] = (
                    saved[0] + colorText.GREEN + "Strong Up" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Strong Up"
            elif angle <= -30 and angle > -61:
                screenDict["Trend"] = (
                    saved[0] + colorText.FAIL + "Weak Down" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Weak Down"
            elif angle < -60:
                screenDict["Trend"] = (
                    saved[0] + colorText.FAIL + "Strong Down" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Strong Down"
        except np.linalg.LinAlgError as e: # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            screenDict["Trend"] = (
                saved[0] + colorText.WARN + "Unknown" + colorText.END
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
            except KeyboardInterrupt:
                raise KeyboardInterrupt
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
                saved[0] + colorText.GREEN + "Trendline-Support" + colorText.END
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
    def findUptrend(self, df, screenDict, saveDict, testing, stock,onlyMF=False,hostData=None,exchangeName="INDIA",refreshMFAndFV=True,downloadOnly=False):
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
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception:  # pragma: no cover
                # self.default_logger.debug(e, exc_info=True)
                pass
        decision = f'T:{colorText.UPARROW}' if isUptrend else (f'T:{colorText.DOWNARROW}' if isDowntrend else '')
        dma50decision = f't:{colorText.UPARROW}' if is50DMAUptrend else (f't:{colorText.DOWNARROW}' if is50DMADowntrend else '')
        mf_inst_ownershipChange = 0
        change_millions =""
        mf = ""
        mfs = ""
        if refreshMFAndFV:
            try:
                mf_inst_ownershipChange = self.getMutualFundStatus(stock,onlyMF=onlyMF,hostData=hostData,force=(hostData is None or hostData.empty or not ("MF" in hostData.columns or "FII" in hostData.columns)) and downloadOnly,exchangeName=exchangeName)
                if isinstance(mf_inst_ownershipChange, pd.Series):
                    mf_inst_ownershipChange = 0
                roundOff = 2
                millions = round(mf_inst_ownershipChange/1000000,roundOff)
                while float(millions) == 0 and roundOff <=5:
                    roundOff +=1
                    millions = round(mf_inst_ownershipChange/1000000,roundOff)
                change_millions = f"({millions}M)"
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
            try:
                #Let's get the fair value, either saved or fresh from service
                fairValue = self.getFairValue(stock,hostData,force=(hostData is None or hostData.empty or "FairValue" not in hostData.columns) and downloadOnly,exchangeName=exchangeName)
                if fairValue is not None and fairValue != 0:
                    ltp = saveDict["LTP"]
                    fairValueDiff = round(fairValue - ltp,0)
                    saveDict["FairValue"] = str(fairValue)
                    saveDict["FVDiff"] = fairValueDiff
                    screenDict["FVDiff"] = fairValueDiff
                    screenDict["FairValue"] = (colorText.GREEN if fairValue >= ltp else colorText.FAIL) + saveDict["FairValue"] + colorText.END
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
            
            if mf_inst_ownershipChange > 0:
                mf = f"MFI:{colorText.UPARROW} {change_millions}"
                mfs = colorText.GREEN + mf + colorText.END
            elif mf_inst_ownershipChange < 0:
                mf = f"MFI:{colorText.DOWNARROW} {change_millions}"
                mfs = colorText.FAIL + mf + colorText.END

        # Let's get the large deals for the stock
        try:
            dealsInfo = ""
            symbolKeys = ["Ⓑ","Ⓛ","Ⓢ"]
            largeDealsData, filePath, modifiedDateTime = Archiver.findFileInAppResultsDirectory(directory=Archiver.get_user_data_dir(), fileName="large_deals.json")
            dealsFileSize = os.stat(filePath).st_size if os.path.exists(filePath) else 0
            if dealsFileSize > 0 and len(largeDealsData) > 0:
                import json
                countKeys = ["BULK_DEALS","BLOCK_DEALS","SHORT_DEALS"]
                dataKeys = ["BULK_DEALS_DATA","BLOCK_DEALS_DATA","SHORT_DEALS_DATA"]
                jsonDeals = json.loads(largeDealsData)
                index = 0
                for countKey in countKeys:
                    if countKey in jsonDeals.keys() and int(jsonDeals[countKey]) > 0 and dataKeys[index] in jsonDeals.keys() and len(jsonDeals[dataKeys[index]]) > 0:
                        for deal in jsonDeals[dataKeys[index]]:
                            if stock.upper() == deal["symbol"]:
                                buySellInfo = "" if deal["buySell"] is None else (f"({'B' if deal['buySell'] == 'BUY' else 'S'})")
                                qty = int(deal["qty"])
                                qtyInfo = f"({int(qty/1000000)}M)" if qty >= 1000000 else (f"({int(qty/1000)}K)" if qty >= 1000 else f"({qty})")
                                dealsInfo = f"{dealsInfo} {buySellInfo}{qtyInfo}{symbolKeys[index]}"
                    index += 1
        except: # pragma: no cover
            pass

        saved = self.findCurrentSavedValue(screenDict,saveDict,"Trend")
        decision_scr = (colorText.GREEN if isUptrend else (colorText.FAIL if isDowntrend else colorText.WARN)) + f"{decision}" + colorText.END
        dma50decision_scr = (colorText.GREEN if is50DMAUptrend else (colorText.FAIL if is50DMADowntrend else colorText.WARN)) + f"{dma50decision}" + colorText.END
        saveDict["Trend"] = f"{saved[1]} {decision} {dma50decision} {mf}{dealsInfo}"
        for symbol in symbolKeys:
            dealParts = dealsInfo.split(" ")
            dealPartsRefined = []
            for dealPart in dealParts:
                dealPart = dealPart.replace(symbol,(colorText.GREEN+symbol+colorText.END) if ("(B)" in dealPart) else ((colorText.FAIL+symbol+colorText.END) if ("(S)" in dealPart) else symbol))
                dealPartsRefined.append(dealPart)
            dealsInfo = " ".join(dealPartsRefined).strip()
        screenDict["Trend"] = f"{saved[0]} {decision_scr} {dma50decision_scr} {mfs}{dealsInfo}"
        saveDict["MFI"] = mf_inst_ownershipChange
        screenDict["MFI"] = mf_inst_ownershipChange
        return isUptrend, mf_inst_ownershipChange, fairValueDiff

    def getCandleBodyHeight(self, dailyData):
        bodyHeight = dailyData["Close"].iloc[0] - dailyData["Open"].iloc[0]
        return bodyHeight

    # Private method to find candle type
    # True = Bullish, False = Bearish
    def getCandleType(self, dailyData):
        return bool(dailyData["Close"].iloc[0] >= dailyData["Open"].iloc[0])

    def getFairValue(self, stock, hostData=None, force=False,exchangeName="INDIA"):
        if hostData is None or len(hostData) < 1:
            hostData = pd.DataFrame()
        # Let's look for fair values
        fairValue = 0
        if "FairValue" in hostData.columns and PKDateUtilities.currentDateTime().weekday() <= 4:
            try:
                fairValue = hostData.loc[hostData.index[-1],"FairValue"]
            except (KeyError,IndexError):
                    pass
        else:
            if PKDateUtilities.currentDateTime().weekday() >= 5 or force:
                security = None
                # Refresh each saturday or sunday or when not found in saved data
                try:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        security = Stock(stock,exchange=exchangeName)
                except ValueError: # pragma: no cover
                    # We did not find the stock? It's okay. Move on to the next one.
                    pass
                except (TimeoutError, ConnectionError) as e:
                    self.default_logger.debug(e, exc_info=True)
                    pass
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e: # pragma: no cover
                    self.default_logger.debug(e, exc_info=True)
                    pass
                if security is not None:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        fv = security.fairValue()
                    if fv is not None:
                        try:
                            fvResponseValue = fv["latestFairValue"]
                            if fvResponseValue is not None:
                                fairValue = float(fvResponseValue)
                        except: # pragma: no cover # pragma: no cover
                            pass
                            # self.default_logger.debug(f"{e}\nResponse:fv:\n{fv}", exc_info=True)
                    fairValue = round(float(fairValue),1)
                    try:
                        hostData.loc[hostData.index[-1],"FairValue"] = fairValue
                    except (KeyError,IndexError):
                        pass
        return fairValue

    def getFreshMFIStatus(self, stock,exchangeName="INDIA"):
        changeStatusDataMF = None
        changeStatusDataInst = None
        netChangeMF = 0
        netChangeInst = 0
        latest_mfdate = None
        latest_instdate = None
        security = None
        try:
            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                security = Stock(stock,exchange=exchangeName)
        except ValueError:
            # We did not find the stock? It's okay. Move on to the next one.
            pass
        except (TimeoutError, ConnectionError) as e:
            self.default_logger.debug(e, exc_info=True)
            pass
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            pass
        if security is not None:
            try:
                with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                    changeStatusRowsMF = security.mutualFundOwnership(top=5)
                    changeStatusRowsInst = security.institutionOwnership(top=5)
                    changeStatusDataMF = security.mutualFundFIIChangeData(changeStatusRowsMF)
                    changeStatusDataInst = security.mutualFundFIIChangeData(changeStatusRowsInst)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
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

    def getMorningClose(self,df):
        close = df["Close"][-1]
        index = len(df)
        while close is np.nan and index >= 0:
            close = df["Close"][index - 1]
            index -= 1
        return close

    def getMorningOpen(self,df):
        open = df["Open"][0]
        index = 0
        while open is np.nan and index < len(df):
            open = df["Open"][index + 1]
            index += 1
        return open

    def getMutualFundStatus(self, stock,onlyMF=False, hostData=None, force=False,exchangeName="INDIA"):
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
                    netChangeMF = hostData.loc[hostData.index[-1],"MF"]
                except (KeyError,IndexError):
                    pass
                try:
                    netChangeInst = hostData.loc[hostData.index[-1],"FII"]
                except (KeyError,IndexError):
                    pass
                try:
                    latest_mfdate = hostData.loc[hostData.index[-1],"MF_Date"]
                    if isinstance(latest_mfdate, float):
                        latest_mfdate = datetime.datetime.fromtimestamp(latest_mfdate).strftime('%Y-%m-%d')
                except (KeyError,IndexError):
                    pass
                try:
                    latest_instdate = hostData.loc[hostData.index[-1],"FII_Date"]
                    if isinstance(latest_instdate, float):
                        latest_instdate = datetime.datetime.fromtimestamp(latest_instdate).strftime('%Y-%m-%d')
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
            netChangeMF, netChangeInst, latest_mfdate, latest_instdate = self.getFreshMFIStatus(stock,exchangeName=exchangeName)
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
            with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
                pred = model.predict(data)[0]
        if pred > 0.5:
            outText = "BEARISH"
            out = (
                colorText.FAIL
                + outText
                + colorText.END
            )
            sug = "Hold your Short position!"
        else:
            outText = "BULLISH"
            out = (
                colorText.GREEN
                + outText
                + colorText.END
            )
            sug = "Stay Bullish!"
        if PKDateUtilities.isClosingHour():
            OutputControls().printOutput(
                colorText.WARN
                + "Note: The AI prediction should be executed After 3 PM or Near to Closing time as the Prediction Accuracy is based on the Closing price!"
                + colorText.END
            )
        predictionText = "Market may Open {} next day! {}".format(out, sug)
        strengthText = "Probability/Strength of Prediction = {}%".format(
            Utility.tools.getSigmoidConfidence(pred[0])
        )
        OutputControls().printOutput(
            colorText.BLUE
            + "\n"
            + "  [+] Nifty AI Prediction -> "
            + colorText.END
            + predictionText
            + colorText.END
        )
        OutputControls().printOutput(
            colorText.BLUE
            + "\n"
            + "  [+] Nifty AI Prediction -> "
            + colorText.END
            + strengthText
        )

        return pred, predictionText.replace(out, outText), strengthText

    def getTopsAndBottoms(self, df, window=3, numTopsBottoms=6):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data.reset_index(inplace=True)
        data.rename(columns={"index": "Date"}, inplace=True)
        data = data[data["High"]>0]
        data = data[data["Low"]>0]
        data["tops"] = (data["High"].iloc[list(pktalib.argrelextrema(np.array(data["High"]), np.greater_equal, order=window)[0])].head(numTopsBottoms))
        data["bots"] = (data["Low"].iloc[list(pktalib.argrelextrema(np.array(data["Low"]), np.less_equal, order=window)[0])].head(numTopsBottoms))
        tops = data[data.tops > 0]
        bots = data[data.bots > 0]
        return tops, bots

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
                except (KeyError,IndexError) as e: # pragma: no cover
                    try:
                        condition = last_signal[data_list[cnt]]["SL"][0]
                    except (KeyError,IndexError) as e: # pragma: no cover
                        condition = None
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
                                            colorText.WARN
                                            + data_list[cnt].split("_")[0].upper()
                                            + colorText.END,
                                            (
                                                colorText.FAIL
                                                + data_list[cnt].split("_")[1].upper()
                                                + colorText.END
                                            )
                                            if "sell" in data_list[cnt]
                                            else (
                                                colorText.GREEN
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
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except Exception as e:  # pragma: no cover
                        self.default_logger.debug(e, exc_info=True)
                        pass
                    # Then update
                    last_signal[data_list[cnt]] = [final]
        if result_df is not None:
            result_df.drop_duplicates(keep="last", inplace=True)
            result_df.sort_values(by="Time", inplace=True)
        return result_df[::-1]

    def non_zero_range(self, high: pd.Series, low: pd.Series) -> pd.Series:
        """Returns the difference of two series and adds epsilon to any zero values.  This occurs commonly in crypto data when 'high' = 'low'."""
        diff = high - low
        if diff.eq(0).any().any():
            diff += sflt.epsilon
        return diff
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_long_min.value) & # trend strength confirmation
                        (dataframe['adx'] < self.adx_long_max.value) & # trend strength confirmation
                        (dataframe['trend_l'] > 0) &
                        (dataframe['volume'] > dataframe['volume_mean']) &
                        (dataframe['volume'] > 0)

            ),
            'enter_long'] = 1

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_short_min.value) & # trend strength confirmation
                        (dataframe['adx'] < self.adx_short_max.value) & # trend strength confirmation
                        (dataframe['trend_s'] < 0) &
                        (dataframe['volume'] > dataframe['volume_mean_s']) # volume weighted indicator
            ),
            'enter_short'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:

        conditions_long = []
        conditions_short = []
        dataframe.loc[:, 'exit_tag'] = ''

        exit_long = (
                # (dataframe['close'] < dataframe['low'].shift(self.sell_shift.value)) &
                (dataframe['close'] < dataframe['ema_l']) &
                (dataframe['volume'] > dataframe['volume_mean_exit'])
        )

        exit_short = (
                # (dataframe['close'] > dataframe['high'].shift(self.sell_shift_short.value)) &
                (dataframe['close'] > dataframe['ema_s']) &
                (dataframe['volume'] > dataframe['volume_mean_exit_s'])
        )


        conditions_short.append(exit_short)
        dataframe.loc[exit_short, 'exit_tag'] += 'exit_short'


        conditions_long.append(exit_long)
        dataframe.loc[exit_long, 'exit_tag'] += 'exit_long'


        if conditions_long:
            dataframe.loc[
                pd.reduce(lambda x, y: x | y, conditions_long),
                'exit_long'] = 1

        if conditions_short:
            dataframe.loc[
                pd.reduce(lambda x, y: x | y, conditions_short),
                'exit_short'] = 1
            
        return dataframe

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        if not self.dp:
            # Don't do anything if DataProvider is not available.
            return dataframe
        L_optimize_trend_alert  = self.findBuySellSignalsFromATRTrailing(dataframe=dataframe, key_value= self.key_value_l.value, atr_period= self.atr_period_l.value, ema_period=self.ema_period_l.value)
        # Long position?
        dataframe['trend_l'] = L_optimize_trend_alert['trend']
        S_optimize_trend_alert  = self.findBuySellSignalsFromATRTrailing(dataframe=dataframe, key_value= self.key_value_s.value, atr_period= self.atr_period_s.value, ema_period=self.ema_period_s.value)
        # Short position?
        dataframe['trend_s'] = S_optimize_trend_alert['trend']

        # ADX
        dataframe['adx'] = pktalib.ADX(dataframe)
        
        # RSI
        # dataframe['rsi'] = ta.RSI(dataframe)

        # EMA
        dataframe['ema_l'] = pktalib.EMA(dataframe['close'], timeperiod=self.ema_period_l_exit.value)
        dataframe['ema_s'] = pktalib.EMA(dataframe['close'], timeperiod=self.ema_period_s_exit.value)


        # Volume Weighted
        dataframe['volume_mean'] = dataframe['volume'].rolling(self.volume_check.value).mean().shift(1)
        dataframe['volume_mean_exit'] = dataframe['volume'].rolling(self.volume_check_exit.value).mean().shift(1)

        dataframe['volume_mean_s'] = dataframe['volume'].rolling(self.volume_check_s.value).mean().shift(1)
        dataframe['volume_mean_exit_s'] = dataframe['volume'].rolling(self.volume_check_exit_s.value).mean().shift(1)
        return dataframe
    
    # Preprocess the acquired data
    def preprocessData(self, df, daysToLookback=None):
        assert isinstance(df, pd.DataFrame)
        data = df.copy()
        try:
            data = data.replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna(how="all")
            # self.default_logger.info(f"Preprocessing data:\n{data.head(1)}\n")
            if daysToLookback is None:
                daysToLookback = self.configManager.daysToLookback
            if self.configManager.useEMA:
                sma = pktalib.EMA(data["Close"], timeperiod=50)
                lma = pktalib.EMA(data["Close"], timeperiod=200)
                ssma = pktalib.EMA(data["Close"], timeperiod=9)
                ssma20 = pktalib.EMA(data["Close"], timeperiod=20)
                data.insert(len(data.columns), "SMA", sma)
                data.insert(len(data.columns), "LMA", lma)
                data.insert(len(data.columns), "SSMA", ssma)
                data.insert(len(data.columns), "SSMA20", ssma20)
            else:
                sma = pktalib.SMA(data["Close"], timeperiod=50)
                lma = pktalib.SMA(data["Close"], timeperiod=200)
                ssma = pktalib.SMA(data["Close"], timeperiod=9)
                ssma20 = pktalib.SMA(data["Close"], timeperiod=20)
                data.insert(len(data.columns), "SMA", sma)
                data.insert(len(data.columns), "LMA", lma)
                data.insert(len(data.columns), "SSMA", ssma)
                data.insert(len(data.columns), "SSMA20", ssma20)
            vol = pktalib.SMA(data["Volume"], timeperiod=20)
            rsi = pktalib.RSI(data["Close"], timeperiod=14)
            data.insert(len(data.columns), "VolMA", vol)
            data.insert(len(data.columns), "RSI", rsi)
            cci = pktalib.CCI(data["High"], data["Low"], data["Close"], timeperiod=14)
            data.insert(len(data.columns), "CCI", cci)
            try:
                fastk, fastd = pktalib.STOCHRSI(
                    data["Close"], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0
                )
                data.insert(len(data.columns), "FASTK", fastk)
                data.insert(len(data.columns), "FASTD", fastd)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
        data = data[::-1]  # Reverse the dataframe
        # data = data.fillna(0)
        # data = data.replace([np.inf, -np.inf], 0)
        fullData = data
        trimmedData = data.head(daysToLookback)
        return (fullData, trimmedData)
    
    # Validate if the stock is bullish in the short term
    def validate15MinutePriceVolumeBreakout(self, df):
        if df is None or len(df) == 0:
            return False
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
        if len(recent) < 3:
            return False
        # Price at least 1% higher than previous close
        cond1 = recent["Close"].iloc[0] > 1.01*recent["Close"].iloc[1]
        # Volume at least 5% higher than previous volume
        cond6 = recent["Volume"].iloc[0] > 1.05*recent["Volume"].iloc[1]
        cond2 = cond1 and cond6 and (recent["Close"].iloc[0] > recent["SMA20"].iloc[0])
        cond3 = cond2 and (recent["Close"].iloc[1] > recent["High"].iloc[2])
        cond4 = cond3 and (recent["Volume"].iloc[0] > 1.05*recent["SMA20V"].iloc[0])
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
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        cci = int(data.head(1)["CCI"].iloc[0])
        saveDict["CCI"] = cci
        if (cci >= minCCI and cci <= maxCCI) and "Trend" in saveDict.keys():
            if ("Up" in saveDict["Trend"]):
                screenDict["CCI"] = (
                    (colorText.BOLD if ("Strong" in saveDict["Trend"]) else "") + colorText.GREEN + str(cci) + colorText.END
                )
            else:
                screenDict["CCI"] = (
                    (colorText.BOLD if ("Strong" in saveDict["Trend"]) else "") + colorText.FAIL + str(cci) + colorText.END
                )
            return True
        screenDict["CCI"] = colorText.FAIL + str(cci) + colorText.END
        return False

    # Find Conflucence
    def validateConfluence(self, stock, df, full_df, screenDict, saveDict, percentage=0.1,confFilter=3):
        if df is None or len(df) == 0:
            return False
        data = df.copy() if confFilter < 4 else full_df.copy()
        recent = data.head(2)
        if len(recent) < 2:
            return False
        key1 = "SMA"
        key2 = "LMA"
        key3 = "50DMA"
        key4 = "200DMA"
        saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
        if confFilter == 4:
            maxRecentDays = int(self.configManager.superConfluenceMaxReviewDays)
            recentCurrentDay = 1
            isSuperConfluence = False
            ema_8 = 0
            ema_21 = 0
            ema_55 = 0
            reversedData = data[::-1]  # Reverse the dataframe so that it's oldest data first
            emas = self.configManager.superConfluenceEMAPeriods.split(",")
            if len(emas) < 2:
                emas = [8,21,]
            ema8CrossedEMA21 = False
            ema8CrossedEMA55 = False
            ema21CrossedEMA55 = False
            emasCrossedSMA200 = False
            silverCross = False
            while recentCurrentDay <= maxRecentDays:
                # 8 ema>21 ema > 55 ema >200 sma each OF THE ema AND THE 200 sma SEPARATED BY LESS THAN 1%(ideally 0.1% TO 0.5%) DURING CONFLUENCE
                if len(emas) >= 1:
                    ema_8 = pktalib.EMA(reversedData["Close"],int(emas[0])).tail(recentCurrentDay).head(1).iloc[0]
                    ema_8_prev = pktalib.EMA(reversedData["Close"],int(emas[0])).tail(recentCurrentDay+1).head(1).iloc[0]
                if len(emas) >= 2:
                    ema_21 = pktalib.EMA(reversedData["Close"],int(emas[1])).tail(recentCurrentDay).head(1).iloc[0]
                    ema_21_prev = pktalib.EMA(reversedData["Close"],int(emas[1])).tail(recentCurrentDay+1).head(1).iloc[0]
                if len(emas) >= 3:
                    ema_55 = pktalib.EMA(reversedData["Close"],int(emas[2])).tail(recentCurrentDay).head(1).iloc[0]
                    ema_55_prev = pktalib.EMA(reversedData["Close"],int(emas[2])).tail(recentCurrentDay+1).head(1).iloc[0]
                
                ema8CrossedEMA21 = (ema_8 >= ema_21 and ema_8_prev <= ema_21_prev) or ema8CrossedEMA21
                ema8CrossedEMA55 = (ema_8 >= ema_55 and ema_8_prev <= ema_55_prev) or ema8CrossedEMA55
                ema21CrossedEMA55 = (ema_21 >= ema_55 and ema_21_prev <= ema_55_prev) or ema21CrossedEMA55
                
                sma_200 = pktalib.SMA(reversedData["Close"],200).tail(recentCurrentDay).head(1).iloc[0]
                # ema9 = pktalib.EMA(reversedData["Close"],9).tail(recentCurrentDay).head(1).iloc[0]
                # smaRange = sma_200 * percentage
                superConfluenceEnforce200SMA = self.configManager.superConfluenceEnforce200SMA
                # ema_min = min(ema_8, ema_21, ema_55)
                ema55_percentage = abs(ema_55 - sma_200) / ema_55
                emasCrossedSMA200 = ((ema55_percentage <= percentage)) or emasCrossedSMA200 # (sma_200 <= ema_min and sma_200 <= ema_55)
                if not superConfluenceEnforce200SMA:
                    emasCrossedSMA200 = True
                superbConfluence = sum([ema8CrossedEMA21, emasCrossedSMA200]) >= 2 # ema8CrossedEMA55, ema21CrossedEMA55
                if superbConfluence:
                    indexDate = PKDateUtilities.dateFromYmdString(str(data.index[recentCurrentDay-1]).split(" ")[0])
                    dayDate = f"{indexDate.day}/{indexDate.month}"
                    screenDict["MA-Signal"] = (
                        saved[0] 
                        + (colorText.GREEN)
                        + f"SuperGoldenConf.({dayDate})"
                        + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"SuperGoldenConf(-{dayDate})"
                    screenDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{colorText.GREEN if (ema_8>=ema_21 and ema_8>=ema_55) else (colorText.WARN if (ema_8>=ema_21 or ema_8>=ema_55) else colorText.FAIL)}{round(ema_8,1)}{colorText.END},{colorText.GREEN if ema_21>=ema_55 else colorText.FAIL}{round(ema_21,1)}{colorText.END},{round(ema_55,1)}, {colorText.GREEN if sma_200<= ema_55 and emasCrossedSMA200 else (colorText.WARN if sma_200<= ema_55 else colorText.FAIL)}{round(sma_200,1)} ({round(ema55_percentage*100,1)}%){colorText.END}"
                    saveDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{round(ema_8,1)},{round(ema_21,1)},{round(ema_55,1)}, {round(sma_200,1)} ({round(ema55_percentage*100,1)}%)"
                    saveDict[f"SuperConfSort"] = int(f"{indexDate.year:04}{indexDate.month:02}{indexDate.day:02}") #0 if ema_8>=ema_21 and ema_8>=ema_55 and ema_21>=ema_55 and sma_200<=ema_55 else (1 if (ema_8>=ema_21 or ema_8>=ema_55) else (2 if sma_200<=ema_55 else 3))
                    screenDict[f"SuperConfSort"] = saveDict[f"SuperConfSort"]
                    return superbConfluence
                elif ema8CrossedEMA21 and ema8CrossedEMA55 and ema21CrossedEMA55:
                    indexDate = PKDateUtilities.dateFromYmdString(str(data.index[recentCurrentDay-1]).split(" ")[0])
                    dayDate = f"{indexDate.day}/{indexDate.month}"
                    screenDict["MA-Signal"] = (
                        saved[0] 
                        + (colorText.WHITE)
                        + f"SilverCrossConf.({dayDate})"
                        + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"SilverCrossConf.({dayDate})"
                    screenDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{colorText.GREEN if (ema_8>=ema_21 and ema_8>=ema_55) else (colorText.WARN if (ema_8>=ema_21 or ema_8>=ema_55) else colorText.FAIL)}{round(ema_8,1)}{colorText.END},{colorText.GREEN if ema_21>=ema_55 else colorText.FAIL}{round(ema_21,1)}{colorText.END},{round(ema_55,1)}, {colorText.GREEN if sma_200<= ema_55 and emasCrossedSMA200 else (colorText.WARN if sma_200<= ema_55 else colorText.FAIL)}{round(sma_200,1)} ({round(ema55_percentage*100,1)}%){colorText.END}"
                    saveDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{round(ema_8,1)},{round(ema_21,1)},{round(ema_55,1)}, {round(sma_200,1)} ({round(ema55_percentage*100,1)}%)"
                    saveDict[f"SuperConfSort"] = int(f"{indexDate.year:04}{indexDate.month:02}{indexDate.day:02}") #0 if ema_8>=ema_21 and ema_8>=ema_55 and ema_21>=ema_55 and sma_200<=ema_55 else (1 if (ema_8>=ema_21 or ema_8>=ema_55) else (2 if sma_200<=ema_55 else 3))
                    screenDict[f"SuperConfSort"] = saveDict[f"SuperConfSort"]
                    silverCross = True
                
                recentCurrentDay += 1
            
            if silverCross:
                return True
        is20DMACrossover50DMA = (recent["SSMA20"].iloc[0] >= recent["SMA"].iloc[0]) and \
                            (recent["SSMA20"].iloc[1] <= recent["SMA"].iloc[1])
        is50DMACrossover200DMA = (recent["SMA"].iloc[0] >= recent["LMA"].iloc[0]) and \
                            (recent["SMA"].iloc[1] <= recent["LMA"].iloc[1])
        isGoldenCrossOver = is20DMACrossover50DMA or is50DMACrossover200DMA
        is50DMACrossover200DMADown = (recent["SMA"].iloc[0] <= recent["LMA"].iloc[0]) and \
                            (recent["SMA"].iloc[1] >= recent["LMA"].iloc[1])
        is20DMACrossover50DMADown = (recent["SSMA20"].iloc[0] <= recent["SMA"].iloc[0]) and \
                            (recent["SSMA20"].iloc[1] >= recent["SMA"].iloc[1])
        isDeadCrossOver = is20DMACrossover50DMADown or is50DMACrossover200DMADown
        deadxOverText = f'DeadCrossover{"(20)" if is20DMACrossover50DMADown else ("(50)" if is50DMACrossover200DMADown else "")}'
        goldenxOverText = f'GoldenCrossover{"(20)" if is20DMACrossover50DMA else ("(50)" if is50DMACrossover200DMA else "")}'
        if is20DMACrossover50DMA or is20DMACrossover50DMADown:
            key1 = "SSMA20"
            key2 = "SMA"
            key3 = "20DMA"
            key4 = "50DMA"
        is50DMAUpTrend = (recent[key1].iloc[0] > recent[key2].iloc[1])
        is50DMADownTrend = (recent[key1].iloc[0] < recent[key1].iloc[1])
        is50DMA = (recent[key1].iloc[0] <= recent["Close"].iloc[0])
        is200DMA = (recent[key2].iloc[0] <= recent["Close"].iloc[0])
        difference = round((recent[key1].iloc[0] - recent[key2].iloc[0])
                / recent["Close"].iloc[0]
                * 100,
                2,
            )
        saveDict["ConfDMADifference"] = difference
        screenDict["ConfDMADifference"] = difference
        # difference = abs(difference)
        confText = f"{goldenxOverText if isGoldenCrossOver else (deadxOverText if isDeadCrossOver else ('Conf.Up' if is50DMAUpTrend else ('Conf.Down' if is50DMADownTrend else (key3 if is50DMA else (key4 if is200DMA else 'Unknown')))))}"
        if abs(recent[key1].iloc[0] - recent[key2].iloc[0]) <= (
            recent[key1].iloc[0] * percentage
        ):
            if recent[key1].iloc[0] >= recent[key2].iloc[0]:
                screenDict["MA-Signal"] = (
                    saved[0] 
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            else:
                screenDict["MA-Signal"] = (
                    saved[0] 
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            return confFilter == 3 or \
                (confFilter == 1 and not isDeadCrossOver and (is50DMAUpTrend or (isGoldenCrossOver or 'Up' in confText))) or \
                (confFilter == 2 and not isGoldenCrossOver and (is50DMADownTrend or isDeadCrossOver or 'Down' in confText))
        # Maybe the difference is not within the range, but we'd still like to keep the stock in
        # the list if it's a golden crossover or dead crossover
        if isGoldenCrossOver or isDeadCrossOver:
            screenDict["MA-Signal"] = (
                    saved[0] 
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
            saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            return confFilter == 3 or \
                (confFilter == 1 and isGoldenCrossOver) or \
                (confFilter == 2 and isDeadCrossOver)
        return False

    def findPotentialProfitableEntriesBullishTodayForPDOPDC(self, df, saveDict, screenDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        reversedData = data[::-1]  # Reverse the dataframe
        recentClose = reversedData["Close"].tail(1).head(1).iloc[0]
        yesterdayClose = reversedData["Close"].tail(2).head(1).iloc[0]
        recentOpen = reversedData["Open"].tail(1).head(1).iloc[0]
        yesterdayOpen = reversedData["Open"].tail(2).head(1).iloc[0]
        recentVol = reversedData["Volume"].tail(1).head(1).iloc[0]
        # Daily open > 1 day ago open &
        # Daily Close > 1 day ago close &
        # Volume > 1000000
        return recentOpen > yesterdayOpen and recentClose > yesterdayClose and recentVol >= 1000000
    
    # - 200 MA is rising for at least 3 months.
    # - 50 MA is above 200MA
    # - Current price is above 20Osma and preferably above 50 to 100
    # - Current price is at least above 100 % from 52week low
    # - The stock should have made a 52 week high at least once every 4 to 6 month
    def findPotentialProfitableEntriesFrequentHighsBullishMAs(self, df, full_df, saveDict, screenDict):
        if df is None or len(df) == 0 or full_df is None or len(full_df) == 0:
            return False
        data = full_df.copy()
        one_week = 5
        if len(data) < 45 * one_week:
            return False
        reversedData = data[::-1]  # Reverse the dataframe
        lma_200 = reversedData["LMA"]
        sma_50 = reversedData["SMA"]
        full52Week = reversedData.tail(50 * one_week)
        full52WeekLow = full52Week["Low"].min()
        #200 MA is rising for at least 3 months
        today = 1
        while today <= one_week * 12: # last 3 months
            if lma_200.tail(today).head(1).iloc[0] < lma_200.tail(today + 1).head(1).iloc[0]:
                return False
            today += 1
        # 50 MA is above 200MA
        if sma_50.tail(1).head(1).iloc[0] <= lma_200.tail(1).head(1).iloc[0]:
            return False
        # Current price is above 20Osma and preferably above 50 to 100
        recentClose = reversedData["Close"].tail(1).head(1).iloc[0]
        if recentClose < lma_200.tail(1).head(1).iloc[0] or recentClose < 50 or recentClose > 100:
            return False
        # Current price is at least above 100 % from 52week low
        if recentClose <= 2*full52WeekLow:
            return False
        # The stock should have made a 52 week high at least once every 4 to 6 month
        highAsc = reversedData.sort_values(by=["High"], ascending=True)
        highs = highAsc.tail(13)
        dateDiffs = highs.index.to_series().diff().dt.days
        index = 0
        while index < 12:
            if abs(dateDiffs.tail(12).iloc[index]) >= 120: # max 6 months = 120 days
                return False
            index += 1
        return True

    # - Stock must be trading above 2% on day
    # - stock must be trading above previous day high 
    # - stock must be above daily 50ma
    # - stock must be above 200ma on 5min TF
    def findPotentialProfitableEntriesForFnOTradesAbove50MAAbove200MA5Min(self, df_5min, full_df, saveDict, screenDict):
        if df_5min is None or len(df_5min) == 0 or full_df is None or len(full_df) == 0:
            return False
        data = full_df.copy()
        reversedData = data[::-1]  # Reverse the dataframe
        recentClose = reversedData["Close"].tail(1).head(1).iloc[0]
        prevClose = reversedData["Close"].tail(2).head(1).iloc[0]
        tradingAbove2Percent = (recentClose-prevClose)*100/prevClose > 2
        if tradingAbove2Percent:
            prevHigh = reversedData["High"].tail(2).head(1).iloc[0]
            tradingAbovePrevHighAnd50MA = (recentClose > prevHigh) and (recentClose > reversedData["SMA"].tail(1).head(1).iloc[0])
            # return tradingAbovePrevHighAnd50MA
            # resampling 1-min data to 5 min for 200MA requires at least 5d data to
            # be downloaded which is pretty huge (~460MB). So skipping this for now.
            if tradingAbovePrevHighAnd50MA:
                ohlc_dict = {
                    'Open':'first',
                    'High':'max',
                    'Low':'min',
                    'Close':'last',
                    'Adj Close': 'last',
                    'Volume':'sum'
                }
                data_5min = df_5min.copy()
                reversedData_5min = data_5min[::-1]  # Reverse the dataframe
                reversedData_5min = reversedData_5min.resample(f'5T', offset='15min').agg(ohlc_dict)
                reversedData_5min.dropna(inplace=True)
                sma200_5min = pktalib.SMA(reversedData_5min["Close"],timeperiod=200)
                return recentClose > sma200_5min.tail(1).head(1).iloc[0]
        return False

    #@measure_time
    # Validate if share prices are consolidating
    def validateConsolidation(self, df, screenDict, saveDict, percentage=10):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        hc = data.describe()["Close"]["max"]
        lc = data.describe()["Close"]["min"]
        if (hc - lc) <= (hc * percentage / 100) and (hc - lc != 0):
            screenDict["Consol."] = (
                colorText.GREEN
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        else:
            screenDict["Consol."] = (
                colorText.FAIL
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        saveDict["Consol."] = f'Range:{str(round((abs((hc-lc)/hc)*100),1))+"%"}'
        return round((abs((hc - lc) / hc) * 100), 1)

    def validateConsolidationContraction(self, df,legsToCheck=2,stockName=None):
        if df is None or len(df) == 0:
            return False,[],0
        data = df.copy()
        # We can use window =3 because we need at least 3 candles to get the next top or bottom
        # but to better identify the pattern, we'd use window = 5
        tops, bots = self.getTopsAndBottoms(df=data,window=5,numTopsBottoms=3*(legsToCheck if legsToCheck > 0 else 3))
        # bots = bots.tail(3*legsToCheck-1)
        consolidationPercentages = []
        # dfc.assign(topbots=dfc["tops","bots"].sum(1)).drop("tops","bots", 1)
        dfc = pd.concat([tops,bots],axis=0)
        dfc.sort_index(inplace=True)
        dfc = dfc.assign(topbots=dfc[["tops","bots"]].sum(1))
        if np.isnan(dfc["tops"].iloc[0]): # For a leg to form, we need two tops and one bottom \_/\_/\_/
            dfc = dfc.tail(len(dfc)-1)
        indexLength = len(dfc)
        toBeDroppedIndices = []
        index = 0
        while index < indexLength-1:
            top = dfc["tops"].iloc[index]
            top_next = dfc["tops"].iloc[index+1]
            bot = dfc["bots"].iloc[index]
            bot_next = dfc["bots"].iloc[index+1]
            if not np.isnan(top) and not np.isnan(top_next):
                if top >= top_next:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index+1])].index
                else:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index])].index
                toBeDroppedIndices.append(indexVal)
            if not np.isnan(bot) and not np.isnan(bot_next):
                if bot <= bot_next:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index+1])].index
                else:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index])].index
                toBeDroppedIndices.append(indexVal)
            index += 1

        for indexVal in toBeDroppedIndices:
            dfc.drop(indexVal,axis=0, inplace=True, errors="ignore")
        index = 0
        indexLength = len(dfc)
        relativeLegsTocheck = (legsToCheck if legsToCheck >= 3 else 3)
        while index < indexLength-3:
            top1 = dfc["tops"].iloc[index]
            top2 = dfc["tops"].iloc[index+2]
            top = max(top1,top2)
            bot = dfc["bots"].iloc[index+1]
            if bot != 0 and not np.isnan(top) and not np.isnan(bot):
                legConsolidation = int(round((top-bot)*100/bot,0))
            else:
                legConsolidation = 0
            consolidationPercentages.append(legConsolidation)
            if len(consolidationPercentages) >= relativeLegsTocheck:
                break
            index += 2
        # Check for consolidation/tightening.
        # Every next leg should be tighter than the previous one
        consolidationPercentages = list(reversed(consolidationPercentages))
        devScore = 0
        if self.configManager.enableAdditionalVCPFilters:
            if len(consolidationPercentages) >= 2:
                index = 0
                while (index+1) < legsToCheck:
                    # prev one < new one.
                    if len(consolidationPercentages) >= index+2 and consolidationPercentages[index] <= consolidationPercentages[index+1]:
                        return False, consolidationPercentages[:relativeLegsTocheck], devScore
                    if index < relativeLegsTocheck and len(consolidationPercentages) >= index+2:
                        devScore += 2-(consolidationPercentages[index]/consolidationPercentages[index+1])
                    index += 1
        
        # Return the first requested number of legs in the order of leg1, leg2, leg3 etc.
        conditionMet = len(consolidationPercentages[:relativeLegsTocheck]) >= legsToCheck
        return conditionMet, consolidationPercentages[:relativeLegsTocheck], devScore

    # validate if the stock has been having higher highs, higher lows
    # and higher close with latest close > supertrend and 8-EMA.
    def validateHigherHighsHigherLowsHigherClose(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        day0 = data
        day1 = data[1:]
        day2 = data[2:]
        day3 = data[3:]
        if len(day1) < 1 or len(day2) < 1 or len(day3) < 1:
            return False
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
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        orgData = data
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        for i in range(int(daysToLookback), int(round(daysToLookback * 0.5)) - 1, -1):
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
        if df is None or len(df) == 0:
            return False
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
                    + colorText.GREEN
                    + f"IPO Base ({away} %)"
                    + colorText.END
                )
            else:
                screenDict["Pattern"] = (
                    saved[0]
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
    def validateLorentzian(self, df, screenDict, saveDict, lookFor=3,stock=None):
        if df is None or len(df) == 0:
            return False
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
            with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
                lc = ata.LorentzianClassification(data=data,
                features=[
                    ata.LorentzianClassification.Feature("RSI", 14, 2),  # f1
                    ata.LorentzianClassification.Feature("WT", 10, 11),  # f2
                    ata.LorentzianClassification.Feature("CCI", 20, 2),  # f3
                    ata.LorentzianClassification.Feature("ADX", 20, 2),  # f4
                    ata.LorentzianClassification.Feature("RSI", 9, 2),   # f5
                    pktalib.MFI(data['high'], data['low'], data['close'], data['volume'], 14) #f6
                ],
                settings=ata.LorentzianClassification.Settings(
                    source=data['close'],
                    neighborsCount=8,
                    maxBarsBack=2000,
                    useDynamicExits=False
                ),
                filterSettings=ata.LorentzianClassification.FilterSettings(
                    useVolatilityFilter=True,
                    useRegimeFilter=True,
                    useAdxFilter=False,
                    regimeThreshold=-0.1,
                    adxThreshold=20,
                    kernelFilter = ata.LorentzianClassification.KernelFilter(
                        useKernelSmoothing = False,
                        lookbackWindow = 8,
                        relativeWeight = 8.0,
                        regressionLevel = 25,
                        crossoverLag = 2,
                    )
                ))
            # if stock is not None:
            #     lc.dump(f'{stock}_result.csv')
            #     lc.plot(f'{stock}_result.jpg')
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            if lc.df.iloc[-1]["isNewBuySignal"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.GREEN + "Lorentzian-Buy" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + "Lorentzian-Buy"
                if lookFor != 2: # Not Sell
                    return True
            elif lc.df.iloc[-1]["isNewSellSignal"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.FAIL + "Lorentzian-Sell" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + "Lorentzian-Sell"
                if lookFor != 1: # Not Buy
                    return True
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            # ValueError: operands could not be broadcast together with shapes (20,) (26,)
            # File "/opt/homebrew/lib/python3.11/site-packages/advanced_ta/LorentzianClassification/Classifier.py", line 186, in __init__
            # File "/opt/homebrew/lib/python3.11/site-packages/advanced_ta/LorentzianClassification/Classifier.py", line 395, in __classify
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/common.py", line 76, in new_method
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/arraylike.py", line 70, in __and__
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/series.py", line 5810, in _logical_method
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/array_ops.py", line 456, in logical_op
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/array_ops.py", line 364, in na_logical_op
            self.default_logger.debug(e, exc_info=True)
            pass
        return False

    # validate if the stock has been having lower lows, lower highs
    def validateLowerHighsLowerLows(self, df):
        if df is None or len(df) == 0:
            return False
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
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        if daysForLowestVolume is None:
            daysForLowestVolume = 30
        if len(data) < daysForLowestVolume:
            return False
        data = data.head(daysForLowestVolume)
        recent = data.head(1)
        if len(recent) < 1:
            return False
        if (recent["Volume"].iloc[0] <= data.describe()["Volume"]["min"]) and recent[
            "Volume"
        ][0] != np.nan:
            return True
        return False

    # Validate LTP within limits
    def validateLTP(self, df, screenDict, saveDict, minLTP=None, maxLTP=None,minChange=0):
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
        if pct_change == np.inf or pct_change == -np.inf:
            pct_change = 0
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
            yearlyLow = data.head(250)["Close"].min()
            yearlyHigh = data.head(250)["Close"].max()
            if ltp < (2 * yearlyLow) and ltp < (0.75 * yearlyHigh):
                verifyStageTwo = False
                screenDict["Stock"] = colorText.FAIL + saveDict["Stock"] + colorText.END
        if ltp >= minLTP and ltp <= maxLTP:
            ltpValid = True
            if minChange != 0:
                # User has supplied some filter for percentage change
                ltpValid = float(str(pct_save).replace("%","")) >= minChange
            saveDict["LTP"] = round(ltp, 2)
            screenDict["LTP"] = (colorText.GREEN if ltpValid else colorText.FAIL) + ("%.2f" % ltp) + colorText.END
            try:
                dateTimePart = str(recent.index[0]).split(" ")
                if len(dateTimePart) == 1:
                    indexDate = PKDateUtilities.dateFromYmdString(dateTimePart[0])
                    dayDate = f"{indexDate.day}/{indexDate.month}"
                elif len(dateTimePart) == 2:
                    today = PKDateUtilities.currentDateTime()
                    try:
                        indexDate = datetime.datetime.strptime(str(recent.index[0]),"%Y-%m-%d %H:%M:%S").replace(tzinfo=today.tzinfo)
                    except: # pragma: no cover
                        indexDate = datetime.datetime.strptime(str(recent.index[0]),"%Y-%m-%d %H:%M:%S%z").replace(tzinfo=today.tzinfo)
                        pass
                    dayDate = f"{indexDate.day}/{indexDate.month} {indexDate.hour}:{indexDate.minute}" if indexDate.hour > 0 else f"{indexDate.day}/{indexDate.month} {today.hour}:{today.minute}"
                    screenDict["Time"] = f"{colorText.WHITE}{dayDate}{colorText.END}"
                    saveDict["Time"] = str(dayDate)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
            
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
                    saveDict[f"{prd}-Pd"] = f"{changePercent}%" if not pd.isna(changePercent) else '-'
                    screenDict[f"{prd}-Pd"] = ((colorText.GREEN if changePercent >=0 else colorText.FAIL) + f"{changePercent}%" + colorText.END) if not pd.isna(changePercent) else '-'
                    if (prd == requestedPeriod):
                        maxLTPPotential = max(data["High"].head(prd))
                        screenDict[f"MaxLTP"] = (
                            (colorText.GREEN if (maxLTPPotential >= prevLtp) else (colorText.FAIL))
                            + str("{:.2f}".format(maxLTPPotential))
                            + colorText.END
                        )
                        screenDict[f"Pot.Grw"] = (
                            (colorText.GREEN if (maxLTPPotential >= prevLtp) else (colorText.FAIL))
                            + str("{:.2f}%".format((maxLTPPotential - prevLtp)*100/prevLtp))
                            + colorText.END
                        )
                        saveDict[f"MaxLTP"] = round(maxLTPPotential, 2)
                        saveDict[f"Pot.Grw"] = f"{round((maxLTPPotential - prevLtp)*100/prevLtp, 2)}%"
                screenDict["Date"] = calc_date
                saveDict["Date"] = calc_date
            else:
                saveDict[f"LTP{prd}"] = np.nan
                saveDict[f"Growth{prd}"] = np.nan
                screenDict["Date"] = calc_date
                saveDict["Date"] = calc_date

    # Find stocks that are bearish intraday: Macd Histogram negative
    def validateMACDHistogramBelow0(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macd = pktalib.MACD(data["Close"], 12, 26, 9)[2].tail(1)
        return macd.iloc[:1][0] < 0

    #@measure_time
    # Find if stock gaining bullish momentum
    def validateMomentum(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
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
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because yesterday-close ({yc}) <= yesterday-open ({yo})'
                    # )
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
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, open,close and volume equal from day before yesterday. A potential momentum-gainer!'
                    # )
                    to = data["Open"].iloc[0]
                    yc = data["Close"].iloc[1]
                    yo = data["Open"].iloc[1]
                    dyc = data["Close"].iloc[2]
                    if (to >= yc) and (yo >= dyc):
                        # self.default_logger.info(
                        #     f'Stock:{saveDict["Stock"]}, is a momentum-gainer because today-open ({to}) >= yesterday-close ({yc}) and yesterday-open({yo}) >= day-before-close({dyc})'
                        # )
                        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                        screenDict["Pattern"] = (
                            saved[0]
                            + colorText.GREEN
                            + "Momentum Gainer"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Momentum Gainer"
                        return True
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because either today-open ({to}) < yesterday-close ({yc}) or yesterday-open({yo}) < day-before-close({dyc})'
                    # )
            except IndexError as e: # pragma: no cover
                # self.default_logger.debug(e, exc_info=True)
                # self.default_logger.debug(data)
                pass
            return False
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            return False

    #@measure_time
    # Validate Moving averages and look for buy/sell signals
    def validateMovingAverages(self, df, screenDict, saveDict, maRange=2.5,maLength=0,filters={}):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        maSignals = []
        if str(maLength) in ["0","2","3"]:
            saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
            if (
                recent["SMA"].iloc[0] > recent["LMA"].iloc[0]
                and recent["Close"].iloc[0] > recent["SMA"].iloc[0]
            ):
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.GREEN + "Bullish" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Bullish"
                maSignals.append("3")
            elif recent["SMA"].iloc[0] < recent["LMA"].iloc[0]:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.FAIL + "Bearish" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Bearish"
                maSignals.append("2")
            elif recent["SMA"].iloc[0] == 0:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Unknown"
            else:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.WARN + "Neutral" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Neutral"
        reversedData = data[::-1]  # Reverse the dataframe
        ema_20 = pktalib.EMA(reversedData["Close"],20).tail(1).iloc[0]
        vwap = pktalib.VWAP(reversedData["High"],reversedData["Low"],reversedData["Close"],reversedData["Volume"]).tail(1).iloc[0]
        smaDev = data["SMA"].iloc[0] * maRange / 100
        lmaDev = data["LMA"].iloc[0] * maRange / 100
        emaDev = ema_20 * maRange / 100
        vwapDev = vwap * maRange / 100
        open, high, low, close, sma, lma = (
            data["Open"].iloc[0],
            data["High"].iloc[0],
            data["Low"].iloc[0],
            data["Close"].iloc[0],
            data["SMA"].iloc[0],
            data["LMA"].iloc[0],
        )
        mas = [sma,lma,ema_20,vwap] #if maLength==0 else [sma,lma,ema_20]
        maDevs = [smaDev, lmaDev, emaDev, vwapDev] #if maLength==0 else [smaDev, lmaDev, emaDev]
        maTexts = ["50MA","200MA","20EMA","VWAP"] #if maLength==0 else ["50MA","200MA","20EMA"]
        maReversal = 0
        index = 0
        bullishCandle = self.getCandleType(data)
        if str(maLength) not in ["2","3"]:
            for ma in mas:
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                # Taking Support
                if close > ma and low <= (ma + maDevs[index]) and str(maLength) in ["0","1"]:
                    screenDict["MA-Signal"] = (
                        saved[0] + colorText.GREEN + f"{maTexts[index]}-Support" + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"{maTexts[index]}-Support"
                    maReversal = 1
                    maSignals.append("1")
                # Validating Resistance
                elif close < ma and high >= (ma - maDevs[index]) and str(maLength) in ["0","6"]:
                    screenDict["MA-Signal"] = (
                        saved[0] + colorText.FAIL + f"{maTexts[index]}-Resist" + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"{maTexts[index]}-Resist"
                    maReversal = -1
                    maSignals.append("6")
                    
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                # For a Bullish Candle
                if bullishCandle:
                    # Crossing up
                    if open < ma and close > ma:
                        if (str(maLength) in ["0","5"]) or (str(maLength) in ["7"] and index == maTexts.index("VWAP")):
                            screenDict["MA-Signal"] = (
                                saved[0] + colorText.GREEN + f"BullCross-{maTexts[index]}" + colorText.END
                            )
                            saveDict["MA-Signal"] = saved[1] + f"BullCross-{maTexts[index]}"
                            maReversal = 1
                            maSignals.append(str(maLength))
                # For a Bearish Candle
                elif not bullishCandle:
                    # Crossing down
                    if open > sma and close < sma and str(maLength) in ["0","4"]:
                        screenDict["MA-Signal"] = (
                            saved[0] + colorText.FAIL + f"BearCross-{maTexts[index]}" + colorText.END
                        )
                        saveDict["MA-Signal"] = saved[1] + f"BearCross-{maTexts[index]}"
                        maReversal = -1
                        maSignals.append("4")
                index += 1
        returnValue = maReversal
        if maLength != 0:
            hasRespectiveMAInList = str(maLength) in maSignals
            hasVWAP = "BullCross-VWAP" in saveDict["MA-Signal"]
            returnValue = (hasVWAP and hasRespectiveMAInList) if maLength == 7 else hasRespectiveMAInList
        savedMASignals = saveDict["MA-Signal"]
        return returnValue, savedMASignals.count("Bull") + savedMASignals.count("Support"), savedMASignals.count("Bear") + savedMASignals.count("Resist")

    # Find NRx range for Reversal
    def validateNarrowRange(self, df, screenDict, saveDict, nr=4):
        if df is None or len(df) == 0:
            return False
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
                        saved[0] + colorText.GREEN + f"Buy-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = saved[1] + f"Buy-NR{nr}"
                    return True
                elif (
                    not self.getCandleType(recent)
                    and now_candle["Close"].iloc[0] <= recent["Close"].iloc[0]
                ):
                    screenDict["Pattern"] = (
                        saved[0] + colorText.FAIL + f"Sell-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = saved[1] + f"Sell-NR{nr}"
                    return True
            return False
        else:
            rangeData = data.head(nr)
            rangeData.loc[:,'Range'] = abs(rangeData["Close"] - rangeData["Open"])
            recent = rangeData.head(1)
            if recent["Range"].iloc[0] == rangeData.describe()["Range"]["min"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.GREEN + f"NR{nr}" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + f"NR{nr}"
                return True
            return False

    # Find if stock is newly listed
    def validateNewlyListed(self, df, daysToLookback):
        if df is None or len(df) == 0 or len(df) > 220:
            return False
        data = df.copy()
        if str(daysToLookback).endswith("y"):
            daysToLookback = '220d'
        daysToLookback = int(daysToLookback[:-1])
        recent = data.head(1)
        if len(recent) < 1:
            return False
        if len(data) < daysToLookback and (
            recent["Close"].iloc[0] != np.nan and recent["Close"].iloc[0] > 0
        ):
            return True
        return False

    def validatePriceActionCrosses(self, full_df, screenDict, saveDict,mas=[], isEMA=False, maDirectionFromBelow=True):
        if full_df is None or len(full_df) == 0:
            return False
        data = full_df.copy()
        reversedData = data[::-1]  # Reverse the dataframe so that it's oldest data first
        hasAtleastOneMACross = False
        for ma in mas:
            if len(reversedData) <= int(ma):
                continue
            hasCrossed, percentageDiff = self.findPriceActionCross(df=reversedData,ma=ma,daysToConsider=1,baseMAOrPrice=reversedData["Close"].tail(2),isEMA=isEMA,maDirectionFromBelow=maDirectionFromBelow)
            if hasCrossed:
                if not hasAtleastOneMACross:
                    hasAtleastOneMACross = True
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                maText = f"{ma}-{'EMA' if isEMA else 'SMA'}-Cross-{'FromBelow' if maDirectionFromBelow else 'FromAbove'}"
                saveDict["MA-Signal"] = saved[1] + maText + f"({percentageDiff}%)"
                screenDict["MA-Signal"] = saved[0] + f"{colorText.GREEN}{maText}{colorText.END}{colorText.FAIL if abs(percentageDiff) > 1 else colorText.WARN}({percentageDiff}%){colorText.END}"
        return hasAtleastOneMACross

    def validatePriceActionCrossesForPivotPoint(self, df, screenDict, saveDict, pivotPoint="1", crossDirectionFromBelow=True):
        if df is None or len(df) == 0:
            return False
        hasPriceCross = False
        data = df.copy()
        pp_map = {"1":"PP","2":"S1","3":"S2","4":"S3","5":"R1","6":"R2","7":"R3"}
        if pivotPoint is not None and pivotPoint != "0" and str(pivotPoint).isnumeric():
            ppToCheck = pp_map[str(pivotPoint)]
            ppsr_df = pktalib.get_ppsr_df(data["High"],data["Low"],data["Close"],ppToCheck)
            if ppsr_df is None:
                return False
            if crossDirectionFromBelow:
                hasPriceCross = (ppsr_df["Close"].iloc[0] > ppsr_df[ppToCheck].iloc[0] and 
                             ppsr_df["Close"].iloc[1] <= ppsr_df[ppToCheck].iloc[1])
            else:
                hasPriceCross = (ppsr_df["Close"].iloc[0] < ppsr_df[ppToCheck].iloc[0] and 
                             ppsr_df["Close"].iloc[1] >= ppsr_df[ppToCheck].iloc[1])
            if hasPriceCross:
                percentageDiff = round(100*(ppsr_df["Close"].iloc[0]-ppsr_df[ppToCheck].iloc[0])/ppsr_df[ppToCheck].iloc[0],1)
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                maText = f"Cross-{'FromBelow' if crossDirectionFromBelow else 'FromAbove'}({ppToCheck}:{ppsr_df[ppToCheck].iloc[0]})"
                saveDict["MA-Signal"] = saved[1] + maText + f"({percentageDiff}%)"
                screenDict["MA-Signal"] = saved[0] + f"{colorText.GREEN}{maText}{colorText.END}{colorText.FAIL if abs(percentageDiff) > 1 else colorText.WARN}({percentageDiff}%){colorText.END}"
        return hasPriceCross

    # Validate if the stock prices are at least rising by 2% for the last 3 sessions
    def validatePriceRisingByAtLeast2Percent(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
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
    def validateRSI(self, df, screenDict, saveDict, minRSI, maxRSI,rsiKey="RSI"):
        if df is None or len(df) == 0:
            return False
        if rsiKey not in df.columns:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        rsi = int(data.head(1)[rsiKey].iloc[0])
        saveDict[rsiKey] = rsi
        # https://chartink.com/screener/rsi-screening
        if rsi> 0 and rsi >= minRSI and rsi <= maxRSI:  # or (rsi <= 71 and rsi >= 67):
            screenDict[rsiKey] = (
                colorText.GREEN + str(rsi) + colorText.END
            )
            return True if (rsiKey == "RSIi") else (self.validateRSI(df, screenDict, saveDict, minRSI, maxRSI,rsiKey="RSIi") or True)
        screenDict[rsiKey] = colorText.FAIL + str(rsi) + colorText.END
        # If either daily or intraday RSI comes within range?
        return False if (rsiKey == "RSIi") else (self.validateRSI(df, screenDict, saveDict, minRSI, maxRSI,rsiKey="RSIi"))

    # Validate if the stock is bullish in the short term
    def validateShortTermBullish(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
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
        except KeyboardInterrupt:
            raise KeyboardInterrupt
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
                            saved[0] + colorText.GREEN + "Bullish" + colorText.END
                        )
                        saveDict["MA-Signal"] = saved[1] + "Bullish"
                        return True
        return False
    
    # Validate VCP
    def validateVCP(
        self, df, screenDict, saveDict, stockName=None, window=3, percentageFromTop=3
    ):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        try:
            if self.configManager.enableAdditionalVCPEMAFilters:
                reversedData = data[::-1] 
                ema = pktalib.EMA(reversedData["Close"], timeperiod=50)
                sema20 = pktalib.EMA(reversedData["Close"], timeperiod=20)
                if not (data["Close"].iloc[0] >= ema.tail(1).iloc[0] and data["Close"].iloc[0] >= sema20.tail(1).iloc[0]):
                    return False
            percentageFromTop /= 100
            data.reset_index(inplace=True)
            data.rename(columns={"index": "Date"}, inplace=True)
            data["tops"] = (data["High"].iloc[list(pktalib.argrelextrema(np.array(data["High"]), np.greater_equal, order=window)[0])].head(4))
            data["bots"] = (data["Low"].iloc[list(pktalib.argrelextrema(np.array(data["Low"]), np.less_equal, order=window)[0])].head(4))
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)
            tops = data[data.tops > 0]
            # bots = data[data.bots > 0]
            highestTop = round(tops.describe()["High"]["max"], 1)
            allTimeHigh = max(data["High"])
            withinATHRange = data["Close"].iloc[0] >= (allTimeHigh-allTimeHigh * float(self.configManager.vcpRangePercentageFromTop)/100)
            if not withinATHRange and self.configManager.enableAdditionalVCPFilters:
                # Last close is not within all time high range
                return False
            filteredTops = tops[
                tops.tops > (highestTop - (highestTop * percentageFromTop))
            ]
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
                if data.empty or len(lowPoints) < 1:
                    return False
                ltp = data.head(1)["Close"].iloc[0]
                if (
                    lowPointsOrg == lowPointsSorted
                    and ltp < highestTop
                    and ltp > lowPoints[0]
                ):
                    saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                    isTightening, consolidations, deviationScore = self.validateConsolidationContraction(df=df.copy(),legsToCheck=(int(self.configManager.vcpLegsToCheckForConsolidation) if self.configManager.enableAdditionalVCPFilters else 0),stockName=stockName)
                    consolidations = [f"{str(x)}%" for x in consolidations]
                    if isTightening:
                        screenDict["Pattern"] = (
                            saved[0] 
                            + colorText.GREEN
                            + f"VCP (BO: {highestTop}, Cons.:{','.join(consolidations)})"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + f"VCP (BO: {highestTop}, Cons.:{','.join(consolidations)})"
                        screenDict["deviationScore"] = deviationScore
                        saveDict["deviationScore"] = deviationScore
                        return True
                    return False
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
        return False

    # Validate VCP as per Mark Minervini
    # https://chartink.com/screener/volatility-compression
    def validateVCPMarkMinervini(self, df:pd.DataFrame, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        ohlc_dict = {
            'Open':'first',
            'High':'max',
            'Low':'min',
            'Close':'last',
            'Volume':'sum'
        }
        # final_df = df.resample('W-FRI', closed='left').agg(ohlc_dict).shift('1d')
        weeklyData = data.resample('W').agg(ohlc_dict)
        reversedData = data[::-1]  # Reverse the dataframe
        recent_close = data["Close"].head(1).iloc[0]
        w_ema_13 = pktalib.EMA(weeklyData["Close"],timeperiod=13).tail(1).iloc[0]
        w_ema_26 = pktalib.EMA(weeklyData["Close"],timeperiod=26).tail(1).iloc[0]
        w_sma_50 = pktalib.SMA(weeklyData["Close"],timeperiod=50).tail(1).iloc[0]
        w_sma_40 = pktalib.SMA(weeklyData["Close"],timeperiod=40).tail(1).iloc[0]
        w_sma_40_5w_ago = pktalib.SMA(weeklyData.head(len(weeklyData)-5)["Close"],timeperiod=40).tail(1).iloc[0]
        w_min_50 = min(1.3*weeklyData.tail(50)["Low"])
        w_max_50 = max(0.75*weeklyData.tail(50)["High"])
        w_ema_26_20w_ago = pktalib.EMA(weeklyData.head(len(weeklyData)-20)["Close"],timeperiod=26).tail(1).iloc[0]
        recent_ema_13_20d_ago = pktalib.EMA(reversedData.head(len(reversedData)-20)["Close"],timeperiod=13).tail(1).iloc[0]
        w_sma_40_5w_ago = pktalib.SMA(weeklyData.head(len(weeklyData)-5)["Close"],timeperiod=40).tail(1).iloc[0]
        w_sma_40_10w_ago = pktalib.SMA(weeklyData.head(len(weeklyData)-10)["Close"],timeperiod=40).tail(1).iloc[0]
        recent_sma_50 = pktalib.SMA(reversedData["Close"],timeperiod=50).tail(1).iloc[0]
        w_wma_8 = pktalib.WMA(weeklyData["Close"],timeperiod=8).tail(1).iloc[0]
        w_sma_8 = pktalib.SMA(weeklyData["Close"],timeperiod=8).tail(1).iloc[0]
        numPreviousCandles = 20
        pullbackData = data.head(numPreviousCandles)
        pullbackData.loc[:,'PullBack'] = pullbackData["Close"].lt(pullbackData["Open"]) #.shift(periods=1)) #& data["Low"].lt(data["Low"].shift(periods=1))
        shrinkedVolData = pullbackData[pullbackData["PullBack"] == True].head(numPreviousCandles)
        recentLargestVolume = max(pullbackData[pullbackData["PullBack"] == False].head(3)["Volume"])
        # pullbackData.loc[:,'PBVolRatio'] = pullbackData["Volume"]/recentLargestVolume
        volInPreviousPullbacksShrinked = False
        if not shrinkedVolData.empty:
            index = 0
            while index < len(shrinkedVolData):
                volInPreviousPullbacksShrinked = shrinkedVolData["Volume"].iloc[index] < self.configManager.vcpVolumeContractionRatio * recentLargestVolume
                if not volInPreviousPullbacksShrinked:
                    break
                index += 1
        recentVolumeHasAboveAvgVol = recentLargestVolume >= self.configManager.volumeRatio * data["VolMA"].iloc[0]
        isVCP = w_ema_13 > w_ema_26 and \
                w_ema_26 > w_sma_50 and \
                w_sma_40 > w_sma_40_5w_ago and \
                recent_close >= w_min_50 and \
                recent_close >= w_max_50 and \
                recent_ema_13_20d_ago > w_ema_26_20w_ago and \
                w_sma_40_5w_ago > w_sma_40_10w_ago and \
                recent_close > recent_sma_50 and \
                (w_wma_8 - w_sma_8)*6/29 < 0.5 and \
                volInPreviousPullbacksShrinked and \
                recentVolumeHasAboveAvgVol and \
                recent_close > 10
        if isVCP:
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            screenDict["Pattern"] = (
                saved[0] 
                + colorText.GREEN
                + f"VCP(Minervini)"
                + colorText.END
            )
            saveDict["Pattern"] = saved[1] + f"VCP(Minervini)"
        return isVCP

    # Validate if volume of last day is higher than avg
    def validateVolume(
        self, df, screenDict, saveDict, volumeRatio=2.5, minVolume=100
    ):
        if df is None or len(df) == 0:
            return False, False
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
            if df is None or len(df) == 0:
                return False
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
                            + colorText.GREEN
                            + "Demand Rise"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Demand Rise"
                        return True
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except IndexError as e: # pragma: no cover
                # self.default_logger.debug(e, exc_info=True)
                pass
            return False
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            return False

    # Function to compute ATRTrailingStop
    def xATRTrailingStop_func(self,close, prev_close, prev_atr, nloss):
        if close > prev_atr and prev_close > prev_atr:
            return max(prev_atr, close - nloss)
        elif close < prev_atr and prev_close < prev_atr:
            return min(prev_atr, close + nloss)
        elif close > prev_atr:
            return close - nloss
        else:
            return close + nloss
