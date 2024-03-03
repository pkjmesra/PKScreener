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
import sys
import os
import pandas as pd
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ConfigManager import parser, tools
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes import Archiver
from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.PKPickler import PKPicklerDB
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
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
    def getStockDataForSimulation():
        int_exists, int_cache_file = PKMarketOpenCloseAnalyser.ensureIntradayStockDataExists()
        daily_exists, daily_cache_file = PKMarketOpenCloseAnalyser.ensureDailyStockDataExists()
        updatedCandleData = PKMarketOpenCloseAnalyser.updatedCandleData
        allDailyCandles = PKMarketOpenCloseAnalyser.allDailyCandles
        if  (int_exists and daily_exists) and (updatedCandleData is None or allDailyCandles is None):
            latestDailyCandle,allDailyCandles = PKMarketOpenCloseAnalyser.getLatestDailyCandleData(daily_cache_file)
            morningIntradayCandle = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(int_cache_file)
            updatedCandleData = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(latestDailyCandle,allDailyCandles,morningIntradayCandle)
        return updatedCandleData, allDailyCandles

    def runOpenCloseAnalysis(updatedCandleData,allDailyCandles,screen_df,save_df):
        # stockListFromMorningTrade,morningIntraday_df = PKMarketOpenCloseAnalyser.simulateMorningTrade(updatedCandleData)
        # latest_daily_df = PKMarketOpenCloseAnalyser.runScanForStocksFromMorningTrade(stockListFromMorningTrade,allDailyCandles)
        PKMarketOpenCloseAnalyser.diffMorningCandleDataWithLatestDailyCandleData(screen_df,save_df, allDailyCandles)

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
        # stocks = list(allDailyCandles.keys())
        # for stock in stocks:
        #     try:
        #         df = pd.DataFrame(data=[allDailyCandles[stock]["data"][-1]],
        #                       columns=allDailyCandles[stock]["columns"],
        #                       index=[allDailyCandles[stock]["index"][-1]])
        #         latestDailyCandle[stock] = df.to_dict("split")
        #     except:
        #         continue
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
                df = df.head(numOfCandles)
                df = df[df.index <=  f'{PKDateUtilities.tradingDate().strftime("%Y-%m-%d")} 09:57:00+05:30']
                if df is not None and len(df) > 0:
                    combinedCandle = {"Open":df["Open"][0], "High":max(df["High"]), 
                                    "Low":min(df["Low"]),"Close":df["Close"][-1],
                                    "Adj Close":df["Adj Close"][-1],"Volume":sum(df["Volume"])}
                    tradingDate = PKDateUtilities.tradingDate()
                    timestamp = datetime.datetime.strptime(tradingDate.strftime("%Y-%m-%d hh:mm:ss"),"%Y-%m-%d hh:mm:ss")
                    df = pd.DataFrame([combinedCandle], columns=df.columns, index=[timestamp])
                    morningIntradayCandle[stock] = df.to_dict("split")
            except Exception as e:
                print(f"{stock}:    {e}")
                continue
        return morningIntradayCandle

    def combineDailyStockDataWithMorningSimulation(latestDailyCandle,allDailyCandles,morningIntradayCandle):
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
                    mutableAllDailyCandles[stock]["data"] = mutableAllDailyCandles[stock]["data"][:-1] + [morningIntradayCandle[stock]["data"][0]]
                    mutableAllDailyCandles[stock]["index"] = mutableAllDailyCandles[stock]["index"][:-1] + morningIntradayCandle[stock]["index"]
                else:
                    # We should ideally have all stocks from intraday and eod matching,
                    # but for whatever reason, if we don't have the stock, we should skip those
                    # stocks from analysis
                    del mutableAllDailyCandles[stock]
            except:
                del mutableAllDailyCandles[stock]
                continue
            if 'PKDevTools_Default_Log_Level' in os.environ.keys():
                intradayChange = colorText.miniTabulator().tabulate(
                                    pd.DataFrame(listPriceDict),
                                    headers="keys",
                                    tablefmt=colorText.No_Pad_GridFormat,
                                    showindex=False
                                ).encode("utf-8").decode(STD_ENCODING)
                default_logger().debug(intradayChange)
        return mutableAllDailyCandles

    def runScanForStocksFromMorningTrade(stockListFromMorningTrade,dailyCandleData):
        latest_daily_df = None
        return latest_daily_df

    def diffMorningCandleDataWithLatestDailyCandleData(screen_df,save_df, allDailyCandles):
        stocks = save_df["Stock"]
        eodLTPs = []
        diff = []
        index = 0
        for stock in stocks:
            try:
                # Open, High, Low, Close, Adj Close, Volume. We need the 3rd index item: Close.
                endOfDayLTP = allDailyCandles[stock]["data"][-1][3]
                morningLTP = round(save_df["LTP"][index],2)
                eodLTPs.append(round(endOfDayLTP,2))
                diff.append(round(endOfDayLTP - morningLTP,2))
                index += 1
            except:
                eodLTPs.append("-")
                diff.append("-")
                continue
        save_df["EoDLTP"] = eodLTPs
        screen_df["EoDLTP"] = eodLTPs
        save_df["Diff"] = diff
        screen_df["Diff"] = diff
        columns = save_df.columns
        lastIndex = len(save_df)
        for col in columns:
            if col in ["Stock", "LTP", "%Chng", "EoDLTP", "Diff"]:
                if col == "Stock":
                    save_df.loc[lastIndex,col] = "PORTFOLIO"
                elif col in ["LTP","EoDLTP", "Diff"]:
                    save_df.loc[lastIndex,col] = round(sum(save_df[col].dropna(inplace=False).astype(float)),2)
                elif col == "%Chng":
                    change_pct = sum(save_df["Diff"].dropna(inplace=False).astype(float))*100/sum(save_df["LTP"].dropna(inplace=False).astype(float))
                    save_df.loc[lastIndex,col] = round(change_pct,2)
            else:
                save_df.loc[lastIndex,col] = ""
            screen_df.loc[lastIndex,col] = save_df.loc[lastIndex,col]
        save_df.set_index("Stock", inplace=True)
        screen_df.set_index("Stock", inplace=True)

