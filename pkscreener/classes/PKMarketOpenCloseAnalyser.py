#!/usr/bin/env python
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
import copy
import datetime
import shutil
import sys
import os
import numpy as np
import pandas as pd
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ConfigManager import parser, tools
from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes import Archiver
from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.PKPickler import PKPicklerDB
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.MarketHours import MarketHours
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.MarketHours import MarketHours

from halo import Halo

configManager = tools()

STD_ENCODING=sys.stdout.encoding if sys.stdout is not None else 'utf-8'

class PKDailyStockDataDB(SingletonMixin, metaclass=SingletonType):
    def __init__(self,fileName=None):
        super(PKDailyStockDataDB, self).__init__()
        self.pickler = PKPicklerDB(fileName=fileName)

    def searchCache(self, ticker:str=None, name:str=None):
        return self.pickler.searchCache(ticker=ticker, name=name)
    
    def saveCache(self, ticker:str=None, name:str=None, stockDict:dict=None):
        self.pickler.saveCache(ticker=ticker, name=name, stockDict=stockDict)

class PKIntradayStockDataDB(SingletonMixin, metaclass=SingletonType):
    def __init__(self,fileName=None):
        super(PKIntradayStockDataDB, self).__init__()
        self.pickler = PKPicklerDB(fileName=fileName)

    def searchCache(self, ticker:str=None, name:str=None):
        return self.pickler.searchCache(ticker=ticker, name=name)
    
    def saveCache(self, ticker:str=None, name:str=None, stockDict:dict=None):
        self.pickler.saveCache(ticker=ticker, name=name, stockDict=stockDict)


class PKMarketOpenCloseAnalyser:
    configManager = tools()
    configManager.getConfig(parser)
    updatedCandleData = None
    allDailyCandles = None
    allIntradayCandles = None
    
    def getStockDataForSimulation(sliceWindowDatetime=None,listStockCodes=[]):
        int_exists, int_cache_file, stockDictInt = PKMarketOpenCloseAnalyser.ensureIntradayStockDataExists(listStockCodes=listStockCodes)
        daily_exists, daily_cache_file, stockDict = PKMarketOpenCloseAnalyser.ensureDailyStockDataExists(listStockCodes=listStockCodes)
        updatedCandleData = PKMarketOpenCloseAnalyser.updatedCandleData
        allDailyCandles = PKMarketOpenCloseAnalyser.allDailyCandles
        if  ((int_exists or len(stockDictInt) > 0) and (daily_exists or len(stockDict) > 0)) and (updatedCandleData is None or allDailyCandles is None):
            allDailyCandles = PKMarketOpenCloseAnalyser.getLatestDailyCandleData(daily_cache_file,stockDict)
            morningIntradayCandle = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(int_cache_file,sliceWindowDatetime=sliceWindowDatetime,stockDictInt=stockDictInt)
            updatedCandleData = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(allDailyCandles,morningIntradayCandle)
            # PKMarketOpenCloseAnalyser.updatedCandleData = updatedCandleData
            # PKMarketOpenCloseAnalyser.allDailyCandles = allDailyCandles
            Utility.tools.saveStockData(updatedCandleData,PKMarketOpenCloseAnalyser.configManager,1,False,False, True)
        return updatedCandleData, allDailyCandles

    @Halo(text='  [+] Running final analysis...', spinner='dots')
    def runOpenCloseAnalysis(updatedCandleData,allDailyCandles,screen_df,save_df,runOptionName=None,filteredListOfStocks=[]):
        # stockListFromMorningTrade,morningIntraday_df = PKMarketOpenCloseAnalyser.simulateMorningTrade(updatedCandleData)
        # latest_daily_df = PKMarketOpenCloseAnalyser.runScanForStocksFromMorningTrade(stockListFromMorningTrade,allDailyCandles)
        try:
            shouldSuppress = not OutputControls().enableMultipleLineOutput
            with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                save_df, screen_df = PKMarketOpenCloseAnalyser.diffMorningCandleDataWithLatestDailyCandleData(screen_df,save_df, updatedCandleData, allDailyCandles,runOptionName=runOptionName,filteredListOfStocks=filteredListOfStocks)
        except: # pragma: no cover
            pass
        Utility.tools.saveStockData(allDailyCandles,PKMarketOpenCloseAnalyser.configManager,1,False,False, True)
        return save_df, screen_df

    @Halo(text='  [+] Getting intraday data...', spinner='dots')
    def ensureIntradayStockDataExists(listStockCodes=[]):
        # Ensure that the intraday_stock_data_<date>.pkl file exists
        exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=True)
        copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
        srcFileSize = os.stat(srcFilePath).st_size if os.path.exists(srcFilePath) else 0
        stockDict = None
        if exists and srcFileSize < 1024*1024*40:
             # File less than 30MB ? Must have been corrupted
            try:
                os.remove(srcFilePath)
                exists = False
            except: # pragma: no cover
                pass
        isTrading = PKDateUtilities.isTradingTime()
        if not exists or isTrading:
            savedPeriod = PKMarketOpenCloseAnalyser.configManager.period
            savedDuration = PKMarketOpenCloseAnalyser.configManager.duration
            PKMarketOpenCloseAnalyser.configManager.period = "1d"
            PKMarketOpenCloseAnalyser.configManager.duration = "1m"
            PKMarketOpenCloseAnalyser.configManager.setConfig(parser, default=True, showFileCreatedText=False)
            OutputControls().printOutput(f"  [+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_data_dir()} !")
            OutputControls().printOutput(f"  [+] {colorText.GREEN}Trying to download {cache_file}{colorText.END}. Please wait ...")
            if os.path.exists(copyFilePath) and not isTrading:
                copyFileSize = os.stat(copyFilePath).st_size if os.path.exists(copyFilePath) else 0
                if copyFileSize >= 1024*1024*40:
                    shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
                    PKMarketOpenCloseAnalyser.configManager.period = savedPeriod
                    PKMarketOpenCloseAnalyser.configManager.duration = savedDuration
                    PKMarketOpenCloseAnalyser.configManager.setConfig(parser, default=True, showFileCreatedText=False)
                    return True, cache_file, stockDict
            stockDict = Utility.tools.loadStockData(stockDict={},configManager=PKMarketOpenCloseAnalyser.configManager,downloadOnly=False,defaultAnswer='Y',retrial=False,forceLoad=False,stockCodes=listStockCodes,isIntraday=True)
            exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=True)
            PKMarketOpenCloseAnalyser.configManager.period = savedPeriod
            PKMarketOpenCloseAnalyser.configManager.duration = savedDuration
            PKMarketOpenCloseAnalyser.configManager.setConfig(parser, default=True, showFileCreatedText=False)
            if not exists and len(stockDict) <= 0:
                OutputControls().printOutput(f"  [+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_data_dir()}/ !")
                OutputControls().printOutput(f"  [+] Please run {colorText.FAIL}pkscreener{colorText.END}{colorText.GREEN} -a Y -e -d -i 1m{colorText.END} and then run this menu option again.")
                OutputControls().takeUserInput("Press any key to continue...")
        try:
            if os.path.exists(copyFilePath) and exists:
                shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
            if not os.path.exists(copyFilePath) and exists: # Let's make a copy of the original one
                shutil.copy(srcFilePath,copyFilePath)
        except: # pragma: no cover
            pass
        return exists, cache_file, stockDict

    @Halo(text='  [+] Getting daily data...', spinner='dots')
    def ensureDailyStockDataExists(listStockCodes=[]):
        # Ensure that the stock_data_<date>.pkl file exists
        exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=False)
        copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
        srcFileSize = os.stat(srcFilePath).st_size if os.path.exists(srcFilePath) else 0
        stockDict = None
        if exists and srcFileSize < 1024*1024*40:
             # File less than 30MB ? Must have been corrupted
            try:
                os.remove(srcFilePath)
                exists = False
            except: # pragma: no cover
                pass
        isTrading = PKDateUtilities.isTradingTime()
        if not exists or isTrading:
            savedPeriod = PKMarketOpenCloseAnalyser.configManager.period
            savedDuration = PKMarketOpenCloseAnalyser.configManager.duration
            PKMarketOpenCloseAnalyser.configManager.period = "1y"
            PKMarketOpenCloseAnalyser.configManager.duration = "1d"
            PKMarketOpenCloseAnalyser.configManager.setConfig(parser, default=True, showFileCreatedText=False)
            OutputControls().printOutput(f"  [+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_data_dir()} !")
        # We should download a fresh copy anyways because we may have altered the existing copy in
        # the previous run. -- !!!! Not required if we saved at the end of last operation !!!!
            OutputControls().printOutput(f"  [+] {colorText.GREEN}Trying to download {cache_file}{colorText.END}. Please wait ...")
            if os.path.exists(copyFilePath) and not isTrading:
                copyFileSize = os.stat(copyFilePath).st_size if os.path.exists(copyFilePath) else 0
                if copyFileSize >= 1024*1024*40:
                    shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
                    PKMarketOpenCloseAnalyser.configManager.period = savedPeriod
                    PKMarketOpenCloseAnalyser.configManager.duration = savedDuration
                    PKMarketOpenCloseAnalyser.configManager.setConfig(parser, default=True, showFileCreatedText=False)
                    return True, cache_file, stockDict
            stockDict = Utility.tools.loadStockData(stockDict={},configManager=PKMarketOpenCloseAnalyser.configManager,downloadOnly=False,defaultAnswer='Y',retrial=False,forceLoad=False,stockCodes=listStockCodes,isIntraday=False,forceRedownload=True)
            exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=False)
            PKMarketOpenCloseAnalyser.configManager.period = savedPeriod
            PKMarketOpenCloseAnalyser.configManager.duration = savedDuration
            PKMarketOpenCloseAnalyser.configManager.setConfig(parser, default=True, showFileCreatedText=False)
            if not exists and len(stockDict) <= 0:
                OutputControls().printOutput(f"  [+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_data_dir()}/ !")
                OutputControls().printOutput(f"  [+] Please run {colorText.FAIL}pkscreener{colorText.END}{colorText.GREEN} -a Y -e -d{colorText.END} and then run this menu option again.")
                OutputControls().takeUserInput("Press any key to continue...")
        try:
            if os.path.exists(copyFilePath) and exists:
                shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
            if not os.path.exists(copyFilePath) and exists: # Let's make a copy of the original one
                shutil.copy(srcFilePath,copyFilePath)
        except: # pragma: no cover
            pass
        return exists, cache_file, stockDict
    
    def simulateMorningTrade(updatedCandleData):
        # 1. For each stock, remove the latest daily data for today from stock_data_<date>.pkl
        # 2. For each stock, only take the configManager.morninganalysiscandlenumber data rows
        #    and combine them as one candle - open for the earliest candle and close for the last candle,
        #    low and high will be the lowest and highest for in-between candles. Volume should be combined
        #    for all.
        # 3. For each stock, replace the row from #1 above with the candle data from #2 above.
        # 4. Run scan and find stocks under each (selected) scan category as if the scan was
        #    running in the morning. 
        # 5. Compare the stock prices from #4 with the removed row from #1 and show the diff.
        stockListFromMorningTrade = []
        morningIntraday_df = None
        return stockListFromMorningTrade, morningIntraday_df
    
    def getLatestDailyCandleData(daily_cache_file,stockDict=None):
        allDailyCandles = None
        if stockDict is not None and len(stockDict) > 0:
            return stockDict
        dailyDB = PKDailyStockDataDB(fileName=daily_cache_file)
        allDailyCandles = dailyDB.pickler.pickler.unpickle(fileName=dailyDB.pickler.fileName)
        # latestDailyCandle = {}
        # stocks = list(allDailyCandles.keys())
        # for stock in stocks:
        #     try:
        #         df = pd.DataFrame(data=[allDailyCandles[stock]["data"][-1]],
        #                       columns=allDailyCandles[stock]["columns"],
        #                       index=[allDailyCandles[stock]["index"][-1]])
        #         latestDailyCandle[stock] = df.to_dict("split")
        #     except: # pragma: no cover
        #         continue
        return allDailyCandles
    
    @Halo(text='  [+] Simulating morning alert...', spinner='dots')
    def getIntradayCandleFromMorning(int_cache_file=None,candle1MinuteNumberSinceMarketStarted=0,sliceWindowDatetime=None,stockDictInt=None):
        if candle1MinuteNumberSinceMarketStarted <= 0:
            candle1MinuteNumberSinceMarketStarted = PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber
        morningIntradayCandle = None
        if stockDictInt is not None and len(stockDictInt) > 0:
            allDailyIntradayCandles = stockDictInt
        else:
            intradayDB = PKIntradayStockDataDB(fileName=int_cache_file)
            allDailyIntradayCandles = intradayDB.pickler.pickler.unpickle(fileName=intradayDB.pickler.fileName)
        PKMarketOpenCloseAnalyser.allIntradayCandles = allDailyIntradayCandles
        morningIntradayCandle = {}
        stocks = list(allDailyIntradayCandles.keys())
        numOfCandles = PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber
        duration = PKMarketOpenCloseAnalyser.configManager.morninganalysiscandleduration
        numOfCandles = numOfCandles * int(duration.replace("m",""))
        for stock in stocks:
            try:
                # Let's get the saved data from the DB. Then we need to only
                # get those candles which are earlier than 9:57AM which is
                # the time when the morning alerts collect data for generating alerts
                # We'd then combine the data from 9:15 to 9:57 as a single candle of 
                # OHLCV and replace the last daily candle with this one candle to
                # simulate the scan outcome from morning.
                df = pd.DataFrame(data=allDailyIntradayCandles[stock]["data"],
                                columns=allDailyIntradayCandles[stock]["columns"],
                                index=allDailyIntradayCandles[stock]["index"])
                if sliceWindowDatetime is None:
                    df = df.head(numOfCandles)
                try:
                    alertCandleTimestamp = sliceWindowDatetime if sliceWindowDatetime is not None else f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+candle1MinuteNumberSinceMarketStarted}:00+05:30'
                    df = df[df.index <=  pd.to_datetime(alertCandleTimestamp).to_datetime64()]
                except: # pragma: no cover
                    alertCandleTimestamp = sliceWindowDatetime if sliceWindowDatetime is not None else f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+candle1MinuteNumberSinceMarketStarted}:00+05:30'
                    df = df[df.index <=  pd.to_datetime(alertCandleTimestamp, utc=True)]
                    pass
                with pd.option_context('mode.chained_assignment', None):
                    df.dropna(axis=0, how="all", inplace=True)
                if df is not None and len(df) > 0:
                    combinedCandle = {"Open":PKMarketOpenCloseAnalyser.getMorningOpen(df), "High":max(df["High"]), 
                                    "Low":min(df["Low"]),"Close":PKMarketOpenCloseAnalyser.getMorningClose(df),
                                    "Adj Close":df["Adj Close"][-1],"Volume":sum(df["Volume"])}
                    tradingDate = df.index[-1] #PKDateUtilities.tradingDate()
                    timestamp = datetime.datetime.strptime(tradingDate.strftime("%Y-%m-%d %H:%M:%S"),"%Y-%m-%d %H:%M:%S")
                    df = pd.DataFrame([combinedCandle], columns=df.columns, index=[timestamp])
                    morningIntradayCandle[stock] = df.to_dict("split")
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                OutputControls().printOutput(f"{stock}:    {e}")
                continue
        return morningIntradayCandle

    def getMorningOpen(df):
        try:
            open = df["Open"][0]
        except KeyError: # pragma: no cover
            open = df["Open"][df.index.values[0]]
        index = 0
        while np.isnan(open) and index < len(df):
            try:
                open = df["Open"][index + 1]
            except KeyError: # pragma: no cover
                open = df["Open"][df.index.values[index + 1]]
            index += 1
        return open
    
    def getMorningClose(df):
        try:
            close = df["Close"][-1]
        except KeyError: # pragma: no cover
            close = df["Close"][df.index.values[-1]]
        index = len(df)
        while np.isnan(close) and index >= 0:
            try:
                close = df["Close"][index - 1]
            except KeyError: # pragma: no cover
                close = df["Close"][df.index.values[index - 1]]
            index -= 1
        return close
    
    @Halo(text='  [+] Updating candles...', spinner='dots')
    def combineDailyStockDataWithMorningSimulation(allDailyCandles,morningIntradayCandle):
        mutableAllDailyCandles = copy.deepcopy(allDailyCandles)
        stocks = list(mutableAllDailyCandles.keys())
        intradayStocks = list(morningIntradayCandle.keys())
        priceDict = {}
        listPriceDict = []
        for stock in stocks:
            try:
                priceDict = {}
                if stock in intradayStocks:
                    morningPrice = round(morningIntradayCandle[stock]["data"][0][3],2)
                    closePrice = round(mutableAllDailyCandles[stock]["data"][-1][3],2)
                    priceDict["Stock"] = stock
                    priceDict["Morning"] = morningPrice
                    priceDict["EoD"] = closePrice
                    listPriceDict.append(priceDict)
                    # We basically need to replace today's candle with a single candle that has data from market open to the time
                    # when we are taking as reference point in the morning. This is how it would have looked when running the scan 
                    # in the morning hours.
                    mutableAllDailyCandles[stock]["data"] = mutableAllDailyCandles[stock]["data"][:-1] + [morningIntradayCandle[stock]["data"][0]]
                    mutableAllDailyCandles[stock]["index"] = mutableAllDailyCandles[stock]["index"][:-1] + morningIntradayCandle[stock]["index"]
                else:
                    # We should ideally have all stocks from intraday and eod matching,
                    # but for whatever reason, if we don't have the stock, we should skip those
                    # stocks from analysis
                    del mutableAllDailyCandles[stock]
            except: # pragma: no cover
                del mutableAllDailyCandles[stock]
                if 'PKDevTools_Default_Log_Level' in os.environ.keys():
                    intradayChange = colorText.miniTabulator().tabulate(
                                        pd.DataFrame(listPriceDict),
                                        headers="keys",
                                        tablefmt=colorText.No_Pad_GridFormat,
                                        showindex=False
                                    ).encode("utf-8").decode(STD_ENCODING)
                    default_logger().debug(intradayChange)
                continue
        return mutableAllDailyCandles

    def runScanForStocksFromMorningTrade(stockListFromMorningTrade,dailyCandleData):
        latest_daily_df = None
        return latest_daily_df

    def diffMorningCandleDataWithLatestDailyCandleData(screen_df,save_df, updatedCandleData, allDailyCandles,runOptionName=None,filteredListOfStocks=[]):
        save_df.reset_index(inplace=True)
        screen_df.reset_index(inplace=True)
        save_df.drop(f"index", axis=1, inplace=True, errors="ignore")
        screen_df.drop(f"index", axis=1, inplace=True, errors="ignore")
        stocks = save_df["Stock"]
        filterStocks = []
        for stock in stocks:
            if stock in filteredListOfStocks:
                filterStocks.append(stock)
        stocks = filterStocks
        save_df = save_df[save_df['Stock'].isin(filteredListOfStocks)]
        df_screenResults = None
        for stk in filteredListOfStocks:
            df_screenResults_filter = screen_df[screen_df['Stock'].astype(str).str.contains(f"NSE%3A{stk}") == True]
            df_screenResults = pd.concat([df_screenResults, df_screenResults_filter], axis=0)
        screen_df = df_screenResults
        eodLTPs = []
        dayHighLTPs = []
        morningTimestamps = []
        morningAlertLTPs = []
        sellTimestamps = []
        dayHighTimestamps = []
        sellLTPs = []
        eodDiffs = []
        dayHighDiffs = []
        sqrOffDiffs = []
        index = 0
        ts = None
        row = None
        scrStats = ScreeningStatistics(PKMarketOpenCloseAnalyser.configManager, default_logger())
        tradingDate = PKDateUtilities.tradingDate()
        DEFAULT_ALERT_TIME = PKDateUtilities.currentDateTime().replace(year=tradingDate.year,month=tradingDate.month,day=tradingDate.day,hour=MarketHours().openHour,minute=MarketHours().openMinute+configManager.morninganalysiscandlenumber)
        morningAlertTime = DEFAULT_ALERT_TIME
        for stock in stocks:
            try:
                # Open, High, Low, Close, Adj Close, Volume. We need the 3rd index item: Close.
                dayHighLTP = allDailyCandles[stock]["data"][-1][1]
                endOfDayLTP = allDailyCandles[stock]["data"][-1][3]
                try:
                    savedMorningLTP = updatedCandleData[stock]["data"][-1][3]
                    morningTime = PKDateUtilities.utc_to_ist(updatedCandleData[stock]["index"][-1]).strftime("%H:%M")
                    morningAlertTime = updatedCandleData[stock]["index"][-1]
                except: # pragma: no cover
                    savedMorningLTP = round(save_df["LTP"][index],2)
                    morningTime = DEFAULT_ALERT_TIME.strftime("%H:%M")
                    morningAlertTime = DEFAULT_ALERT_TIME
                morningLTP = savedMorningLTP if pd.notna(savedMorningLTP) else round(save_df["LTP"][index],2)
                morningTimestamps.append(morningTime)
                morningCandles = PKMarketOpenCloseAnalyser.allIntradayCandles
                df = pd.DataFrame(data=morningCandles[stock]["data"],
                                columns=morningCandles[stock]["columns"],
                                index=morningCandles[stock]["index"])
                # try:
                #     # Let's only consider those candles that are after the alert issue-time in the mornings
                #     df = df[df.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 09:{15+PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber}:00+05:30').to_datetime64()]
                # except: # pragma: no cover
                #     df = df[df.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 09:{15+PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber}:00+05:30', utc=True)]
                #     pass
                ts, row = scrStats.findMACDCrossover(df=df,
                                           afterTimestamp=morningAlertTime,
                                           nthCrossover=1,
                                           upDirection=True)
                # saveDictionary = {}
                # screeningDictionary = {}
                # nextSellMinute = 1
                # foundNextSellCandle = False
                # index = None
                # while not foundNextSellCandle:
                #     try:
                #         # Let's only consider those candles that are right after the alert issue-time in the mornings
                #         index = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber+nextSellMinute}:00+05:30').to_datetime64()
                #         df = df[df.index <=  index]
                #     except: # pragma: no cover
                #         index = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber+nextSellMinute}:00+05:30', utc=True)
                #         df = df[df.index <=  index]
                #         pass
                #     foundNextSellCandle = scrStats.findATRTrailingStops(df=df,sensitivity=configManager.atrTrailingStopSensitivity, atr_period=configManager.atrTrailingStopPeriod,ema_period=configManager.atrTrailingStopEMAPeriod,buySellAll=2,saveDict=saveDictionary,screenDict=screeningDictionary)
                #     nextSellMinute += 1
                # if foundNextSellCandle:
                #     ts = df.tail(len(df)-index +1).head(1).index[-1]
                #     row = df[df.index == ts]
                highTS, highRow = scrStats.findIntradayHighCrossover(df=df)
                # buySell_df = scrStats.computeBuySellSignals(updatedCandleData[stock]["data"])
                # OutputControls().printOutput(buySell_df)
                dayHighLTP = dayHighLTP if pd.notna(dayHighLTP) else highRow["High"][-1]
                sellTimestamps.append(PKDateUtilities.utc_to_ist(ts).strftime("%H:%M"))
                dayHighTimestamps.append(PKDateUtilities.utc_to_ist(highTS).strftime("%H:%M"))
                sellLTPs.append(row["High"][-1])
                eodLTPs.append(round(endOfDayLTP,2))
                dayHighLTPs.append(round(dayHighLTP,2))
                eodDiffs.append(round(endOfDayLTP - morningLTP,2))
                dayHighDiffs.append(round(dayHighLTP - morningLTP,2))
                sqrOffDiffs.append(round(row["High"][-1] - morningLTP,2))
                morningAlertLTPs.append(str(int(round(morningLTP,0))))
                index += 1
            except: # pragma: no cover
                eodLTPs.append("0")
                eodDiffs.append("0")
                dayHighLTPs.append("0")
                dayHighDiffs.append("0")
                if len(morningAlertLTPs) < len(eodLTPs):
                    morningAlertLTPs.append("0")
                if len(morningTimestamps) < len(eodLTPs):
                    morningTimestamps.append("09:30")
                if len(sellTimestamps) < len(eodLTPs):
                    sellTimestamps.append("09:40")
                if len(sellLTPs) < len(eodLTPs):
                    sellLTPs.append("0")
                if len(sqrOffDiffs) < len(eodLTPs):
                    sqrOffDiffs.append("0")
                if len(dayHighTimestamps) < len(eodLTPs):
                    dayHighTimestamps.append("09:45")
                continue
        diffColumns = ["LTP@Alert", "AlertTime", "SqrOff", "SqrOffLTP", "SqrOffDiff","DayHighTime","DayHigh","DayHighDiff", "EoDLTP", "EoDDiff"]
        diffValues = [morningAlertLTPs, morningTimestamps, sellTimestamps, sellLTPs, sqrOffDiffs,dayHighTimestamps,dayHighLTPs, dayHighDiffs,eodLTPs, eodDiffs]
        for column in diffColumns:
            columnName = column
            save_df[columnName] = diffValues[diffColumns.index(columnName)]
            screen_df.loc[:, columnName] = save_df.loc[:, columnName].apply(
                lambda x: x if columnName in ["LTP@Alert","AlertTime", "SqrOff", "SqrOffLTP", "EoDLTP","DayHigh","DayHighTime"] else ((colorText.GREEN if float(x) >= 0 else colorText.FAIL) + str(x) + colorText.END)
            )

        columns = save_df.columns
        lastIndex = len(save_df)
        ltpSum = 0
        for col in columns:
            if col in ["Stock", "LTP@Alert", "Pattern", "LTP", "SqrOffLTP","SqrOffDiff","DayHigh","DayHighDiff", "EoDLTP", "EoDDiff", "%Chng"]:
                if col == "Stock":
                    save_df.loc[lastIndex,col] = "BASKET"
                elif col == "Pattern":
                    save_df.loc[lastIndex,col] = runOptionName if runOptionName is not None else ""
                elif col in ["LTP", "LTP@Alert", "SqrOffLTP","SqrOffDiff", "EoDLTP", "EoDDiff","DayHigh","DayHighDiff"]:
                    save_df.loc[lastIndex,col] = round(sum(save_df[col].dropna(inplace=False).astype(float)),2)
                elif col == "%Chng":
                    ltpSum = sum(save_df["LTP@Alert"].dropna(inplace=False).astype(float))
                    change_pct = sum(save_df["EoDDiff"].dropna(inplace=False).astype(float))*100/ltpSum
                    save_df.loc[lastIndex,col] = f"{round(change_pct,2)}%"
            else:
                save_df.loc[lastIndex,col] = ""
            screen_df.loc[lastIndex,col] = save_df.loc[lastIndex,col]
        eodDiff = save_df.loc[lastIndex,"EoDDiff"]
        sqrOffDiff = save_df.loc[lastIndex,"SqrOffDiff"]
        dayHighDiff = save_df.loc[lastIndex,"DayHighDiff"]
        save_df.loc[lastIndex,"EoDDiff"] = str(eodDiff) + f'({round(100*eodDiff/ltpSum,2) if ltpSum >0 else 0}%)'
        save_df.loc[lastIndex,"SqrOffDiff"] = str(sqrOffDiff) + f'({round(100*sqrOffDiff/ltpSum,2) if ltpSum >0 else 0}%)'
        save_df.loc[lastIndex,"DayHighDiff"] = str(dayHighDiff) + f'({round(100*dayHighDiff/ltpSum,2) if ltpSum >0 else 0}%)'
        screen_df.loc[lastIndex,"EoDDiff"] = (colorText.GREEN if eodDiff >= 0 else colorText.FAIL) + save_df.loc[lastIndex,"EoDDiff"] + colorText.END
        screen_df.loc[lastIndex,"SqrOffDiff"] = (colorText.GREEN if sqrOffDiff >= 0 else colorText.FAIL) + save_df.loc[lastIndex,"SqrOffDiff"] + colorText.END
        screen_df.loc[lastIndex,"DayHighDiff"] = (colorText.GREEN if dayHighDiff >= 0 else colorText.FAIL) + save_df.loc[lastIndex,"DayHighDiff"] + colorText.END
        save_df.set_index("Stock", inplace=True)
        screen_df.set_index("Stock", inplace=True)
        PKMarketOpenCloseAnalyser.allIntradayCandles = None
        screen_df.replace(np.nan, "", regex=True)
        save_df.replace(np.nan, "", regex=True)
        # Drop the unnecessary columns for this scanner type to make way for other columns to be fitted nicely on screen
        columnsToBeDropped = ["Breakout(22Prds)","index","EoDLTP","RS_Rating^NSEI","RVM(15)"]
        for col in columnsToBeDropped:
            if col in save_df.columns:
                save_df.drop(col, axis=1, inplace=True, errors="ignore")
            if col in screen_df.columns:
                screen_df.drop(col, axis=1, inplace=True, errors="ignore")
        return save_df, screen_df
