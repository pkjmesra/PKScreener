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
import pandas as pd
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ConfigManager import parser, tools
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes import Archiver
from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.PKPickler import PKPicklerDB

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

    def runOpenCloseAnalysis():
        int_exists, int_cache_file = PKMarketOpenCloseAnalyser.ensureIntradayStockDataExists()
        daily_exists, daily_cache_file = PKMarketOpenCloseAnalyser.ensureDailyStockDataExists()
        if  int_exists and daily_exists:
            latestDailyCandle,allDailyCandles = PKMarketOpenCloseAnalyser.getLatestDailyCandleData(daily_cache_file)
            morningIntradayCandle = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(int_cache_file)
            updatedCandleData = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(latestDailyCandle,morningIntradayCandle)
            stockListFromMorningTrade,morningIntraday_df = PKMarketOpenCloseAnalyser.simulateMorningTrade(updatedCandleData)
            latest_daily_df = PKMarketOpenCloseAnalyser.runScanForStocksFromMorningTrade(stockListFromMorningTrade,allDailyCandles)
            PKMarketOpenCloseAnalyser.diffMorningCandleDataWithLatestDailyCandleData(latest_daily_df,morningIntraday_df)

    def ensureIntradayStockDataExists():
        # Ensure that the intraday_stock_data_<date>.pkl file exists
        exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=True)
        if not exists:
            print(f"[+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_outputs_dir()} !")
            print(f"[+] Please run {colorText.FAIL}pkscreener{colorText.END}{colorText.GREEN} -a Y -e -d -i 1m{colorText.END} and then run this menu option again.")
            input("Press any key to continue...")
        return exists, cache_file

    def ensureDailyStockDataExists():
        # Ensure that the stock_data_<date>.pkl file exists
        exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=False)
        if not exists:
            print(f"[+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_outputs_dir()} !")
            print(f"[+] Please run {colorText.FAIL}pkscreener{colorText.END}{colorText.GREEN} -a Y -e -d{colorText.END} and then run this menu option again.")
            input("Press any key to continue...")
        return exists, cache_file
    
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
    
    def getLatestDailyCandleData(daily_cache_file):
        latestDailyCandle,allDailyCandles = None, None
        dailyDB = PKDailyStockDataDB(fileName=daily_cache_file)
        allDailyCandles = dailyDB.pickler.pickler.unpickle(fileName=dailyDB.pickler.fileName)
        latestDailyCandle = {}
        stocks = list(allDailyCandles.keys())
        for stock in stocks:
            df = pd.DataFrame(data=[allDailyCandles[stock]["data"][-1]],
                              columns=allDailyCandles[stock]["columns"],
                              index=[allDailyCandles[stock]["index"][-1]])
            latestDailyCandle[stock] = df.to_dict("split")
        return latestDailyCandle,allDailyCandles
    
    def getIntradayCandleFromMorning(int_cache_file):
        morningIntradayCandle = None
        intradayDB = PKIntradayStockDataDB(fileName=int_cache_file)
        allDailyIntradayCandles = intradayDB.pickler.pickler.unpickle(fileName=intradayDB.pickler.fileName)
        morningIntradayCandle = {}
        stocks = list(allDailyIntradayCandles.keys())
        numOfCandles = PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber
        duration = PKMarketOpenCloseAnalyser.configManager.morninganalysiscandleduration
        numOfCandles = numOfCandles * int(duration.replace("m",""))
        for stock in stocks:
            df = pd.DataFrame(data=allDailyIntradayCandles[stock]["data"],
                              columns=allDailyIntradayCandles[stock]["columns"],
                              index=allDailyIntradayCandles[stock]["index"])
            df = df.head(numOfCandles)
            combinedCandle = {"Open":df["Open"][0], "High":max(df["High"]), 
                              "Low":min(df["Low"]),"Close":df["Close"][-1],
                              "Adj Close":df["Adj Close"][-1],"Volume":sum(df["Volume"])}
            df = pd.DataFrame([combinedCandle], columns=df.columns)
            morningIntradayCandle[stock] = df.to_dict("split")
        return morningIntradayCandle
    
    def combineDailyStockDataWithMorningSimulation(latestDailyCandle,morningIntradayCandle):
        return
    
    def runScanForStocksFromMorningTrade(stockListFromMorningTrade,dailyCandleData):
        latest_daily_df = None
        return latest_daily_df

    def diffMorningCandleDataWithLatestDailyCandleData(latest_daily_df,morningIntraday_df):
        return
    
    

    
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
import datetime
import pandas as pd
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ConfigManager import parser, tools
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes import Archiver
from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.PKPickler import PKPicklerDB
from PKDevTools.classes.PKDateUtilities import PKDateUtilities

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

    def getStockDataForSimulation():
        int_exists, int_cache_file = PKMarketOpenCloseAnalyser.ensureIntradayStockDataExists()
        daily_exists, daily_cache_file = PKMarketOpenCloseAnalyser.ensureDailyStockDataExists()
        updatedCandleData = None
        if  int_exists and daily_exists:
            latestDailyCandle,allDailyCandles = PKMarketOpenCloseAnalyser.getLatestDailyCandleData(daily_cache_file)
            morningIntradayCandle = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(int_cache_file)
            updatedCandleData = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(latestDailyCandle,allDailyCandles,morningIntradayCandle)
        return updatedCandleData

    def runOpenCloseAnalysis(updatedCandleData,allDailyCandles):
        stockListFromMorningTrade,morningIntraday_df = PKMarketOpenCloseAnalyser.simulateMorningTrade(updatedCandleData)
        latest_daily_df = PKMarketOpenCloseAnalyser.runScanForStocksFromMorningTrade(stockListFromMorningTrade,allDailyCandles)
        PKMarketOpenCloseAnalyser.diffMorningCandleDataWithLatestDailyCandleData(latest_daily_df,morningIntraday_df)

    def ensureIntradayStockDataExists():
        # Ensure that the intraday_stock_data_<date>.pkl file exists
        exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=True)
        if not exists:
            print(f"[+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_outputs_dir()} !")
            print(f"[+] Please run {colorText.FAIL}pkscreener{colorText.END}{colorText.GREEN} -a Y -e -d -i 1m{colorText.END} and then run this menu option again.")
            input("Press any key to continue...")
        return exists, cache_file

    def ensureDailyStockDataExists():
        # Ensure that the stock_data_<date>.pkl file exists
        exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=False)
        if not exists:
            print(f"[+] {colorText.FAIL}{cache_file}{colorText.END} not found under {Archiver.get_user_outputs_dir()} !")
            print(f"[+] Please run {colorText.FAIL}pkscreener{colorText.END}{colorText.GREEN} -a Y -e -d{colorText.END} and then run this menu option again.")
            input("Press any key to continue...")
        return exists, cache_file
    
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
    
    def getLatestDailyCandleData(daily_cache_file):
        latestDailyCandle,allDailyCandles = None, None
        dailyDB = PKDailyStockDataDB(fileName=daily_cache_file)
        allDailyCandles = dailyDB.pickler.pickler.unpickle(fileName=dailyDB.pickler.fileName)
        latestDailyCandle = {}
        stocks = list(allDailyCandles.keys())
        for stock in stocks:
            df = pd.DataFrame(data=[allDailyCandles[stock]["data"][-1]],
                              columns=allDailyCandles[stock]["columns"],
                              index=[allDailyCandles[stock]["index"][-1]])
            latestDailyCandle[stock] = df.to_dict("split")
        return latestDailyCandle,allDailyCandles
    
    def getIntradayCandleFromMorning(int_cache_file):
        morningIntradayCandle = None
        intradayDB = PKIntradayStockDataDB(fileName=int_cache_file)
        allDailyIntradayCandles = intradayDB.pickler.pickler.unpickle(fileName=intradayDB.pickler.fileName)
        morningIntradayCandle = {}
        stocks = list(allDailyIntradayCandles.keys())
        numOfCandles = PKMarketOpenCloseAnalyser.configManager.morninganalysiscandlenumber
        duration = PKMarketOpenCloseAnalyser.configManager.morninganalysiscandleduration
        numOfCandles = numOfCandles * int(duration.replace("m",""))
        for stock in stocks:
            df = pd.DataFrame(data=allDailyIntradayCandles[stock]["data"],
                              columns=allDailyIntradayCandles[stock]["columns"],
                              index=allDailyIntradayCandles[stock]["index"])
            df = df.head(numOfCandles)
            df = df[df.index <=  f'{PKDateUtilities.tradingDate().strftime("%Y-%m-%d")} 09:59:00+05:30']
            if df is not None and len(df) > 0:
                combinedCandle = {"Open":df["Open"][0], "High":max(df["High"]), 
                                "Low":min(df["Low"]),"Close":df["Close"][-1],
                                "Adj Close":df["Adj Close"][-1],"Volume":sum(df["Volume"])}
                tradingDate = PKDateUtilities.tradingDate()
                timestamp = datetime.datetime.strptime(tradingDate.strftime("%Y-%m-%d hh:mm:ss"),"%Y-%m-%d hh:mm:ss")
                df = pd.DataFrame([combinedCandle], columns=df.columns, index=[timestamp])
                morningIntradayCandle[stock] = df.to_dict("split")
        return morningIntradayCandle

    def combineDailyStockDataWithMorningSimulation(latestDailyCandle,allDailyCandles,morningIntradayCandle):
        stocks = list(allDailyCandles.keys())
        intradayStocks = list(morningIntradayCandle.keys())
        for stock in stocks:
            if stock in intradayStocks:
                allDailyCandles[stock]["data"] = allDailyCandles[stock]["data"][:-1] + [morningIntradayCandle[stock]["data"][0]]
                allDailyCandles[stock]["index"] = allDailyCandles[stock]["index"][:-1] + morningIntradayCandle[stock]["index"]
        return allDailyCandles

    def runScanForStocksFromMorningTrade(stockListFromMorningTrade,dailyCandleData):
        latest_daily_df = None
        return latest_daily_df

    def diffMorningCandleDataWithLatestDailyCandleData(latest_daily_df,morningIntraday_df):
        return
