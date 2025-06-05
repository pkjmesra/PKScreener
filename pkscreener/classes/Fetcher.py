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
import warnings
import logging
from time import sleep
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
import yfinance as yf
from yfinance import exceptions as yf_exceptions  # <-- Updated import
from PKDevTools.classes.Utils import USER_AGENTS
import random
from yfinance import __version__ as yfVersion  # <-- Updated version import

from concurrent.futures import ThreadPoolExecutor
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.Fetcher import StockDataEmptyException
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKNSETools.PKNSEStockDataFetcher import nseStockDataFetcher
from pkscreener.classes.PKTask import PKTask
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes import Archiver

class screenerStockDataFetcher(nseStockDataFetcher):
    _tickersInfoDict={}
    def fetchStockDataWithArgs(self, *args):
        task = None
        if isinstance(args[0], PKTask):
            task = args[0]
            stockCode,period,duration,exchangeSuffix = task.long_running_fn_args
        else:
            stockCode,period,duration,exchangeSuffix = args[0],args[1],args[2],args[3]
        result = self.fetchStockData(stockCode,period,duration,None,0,0,0,exchangeSuffix=exchangeSuffix,printCounter=False)
        if task is not None:
            if task.taskId >= 0:
                task.progressStatusDict[task.taskId] = {'progress': 0, 'total': 1}
                task.resultsDict[task.taskId] = result
                task.progressStatusDict[task.taskId] = {'progress': 1, 'total': 1}
            task.result = result
        return result

    def get_stats(self,ticker):
        info = yf.Ticker(ticker).fast_info
        screenerStockDataFetcher._tickersInfoDict[ticker] = {"marketCap":info.market_cap if info is not None else 0}

    def fetchAdditionalTickerInfo(self,ticker_list,exchangeSuffix=".NS"):
        if not isinstance(ticker_list,list):
            raise TypeError("ticker_list must be a list")
        if len(exchangeSuffix) > 0:
            ticker_list = [(f"{x}{exchangeSuffix}" if not x.endswith(exchangeSuffix) else x) for x in ticker_list]
        screenerStockDataFetcher._tickersInfoDict = {}
        with ThreadPoolExecutor() as executor:
            executor.map(self.get_stats, ticker_list)
        return screenerStockDataFetcher._tickersInfoDict

    def fetchStockData(
        self,
        stockCode,
        period,
        duration,
        proxyServer=None,
        screenResultsCounter=0,
        screenCounter=0,
        totalSymbols=0,
        printCounter=False,
        start=None, 
        end=None,
        exchangeSuffix=".NS",
        attempt = 0
    ):
        if isinstance(stockCode,list):
            if len(exchangeSuffix) > 0:
                stockCode = [(f"{x}{exchangeSuffix}" if (not x.endswith(exchangeSuffix) and not x.startswith("^")) else x) for x in stockCode]
        elif isinstance(stockCode,str):
            if len(exchangeSuffix) > 0:
                stockCode = f"{stockCode}{exchangeSuffix}" if (not stockCode.endswith(exchangeSuffix) and not stockCode.startswith("^")) else stockCode
        if (period in ["1d","5d","1mo","3mo","5mo"] or duration[-1] in ["m","h"]):
            start = None
            end = None

        data = None
        with SuppressOutput(suppress_stdout=(not printCounter), suppress_stderr=(not printCounter)):
            try:
                # Set user-agent header if needed (yfinance now uses requests.Session)
                headers = {'User-Agent': random.choice(USER_AGENTS)}

                if "PKDevTools_Default_Log_Level" in os.environ.keys():
                    from yfinance import utils
                    yflogger = utils.get_yf_logger()
                    yflogger.setLevel(int(os.environ.get("PKDevTools_Default_Log_Level"),logging.DEBUG))
                    yf.enable_debug_mode()

                data = yf.download(
                    tickers=stockCode,
                    period=period,
                    interval=duration,
                    proxy=proxyServer,
                    progress=False,
                    rounding = True,
                    group_by='ticker',
                    timeout=getattr(self.configManager, "generalTimeout", 10)/4,
                    start=start,
                    end=end,
                    auto_adjust=True,
                    threads=len(stockCode) if not isinstance(stockCode,str) else True,
                )
                # Error handling for empty data
                if isinstance(stockCode,str):
                    if (data is None or data.empty):
                        # Try a fallback for invalid period
                        if attempt < 2:
                            default_logger().debug(f"Empty data for {stockCode}, attempt {attempt+1}")
                            sleep(1)
                            return self.fetchStockData(
                                stockCode=stockCode,
                                period=period,
                                duration=duration,
                                printCounter=printCounter,
                                start=start,
                                end=end,
                                proxyServer=proxyServer,
                                screenResultsCounter=screenResultsCounter,
                                screenCounter=screenCounter,
                                totalSymbols=totalSymbols,
                                exchangeSuffix=exchangeSuffix,
                                attempt=attempt+1
                            )
                    else:
                        multiIndex = data.keys()
                        if isinstance(multiIndex, pd.MultiIndex):
                            listStockCodes = multiIndex.get_level_values(0)
                            data = data.get(listStockCodes[0])
            except (KeyError, yf_exceptions.YFPricesMissingError) as e:
                default_logger().debug(e,exc_info=True)
                pass
            except yf_exceptions.YFRateLimitError as e:
                default_logger().debug(f"YFRateLimitError Hit! \n{e}")
                if attempt < 2:
                    sleep(2 ** attempt)
                    return self.fetchStockData(
                        stockCode=stockCode,
                        period=period,
                        duration=duration,
                        printCounter=printCounter,
                        start=start,
                        end=end,
                        proxyServer=proxyServer,
                        screenResultsCounter=screenResultsCounter,
                        screenCounter=screenCounter,
                        totalSymbols=totalSymbols,
                        exchangeSuffix=exchangeSuffix,
                        attempt=attempt+1
                    )
                pass
            except (yf_exceptions.YFInvalidPeriodError, Exception) as e:
                default_logger().debug(e,exc_info=True)

        if printCounter and type(screenCounter) != int:
            sys.stdout.write("\r\033[K")
            try:
                OutputControls().printOutput(
                    colorText.GREEN
                    + (
                        "[%d%%] Screened %d, Found %d. Fetching data & Analyzing %s..."
                        % (
                            int((screenCounter.value / totalSymbols) * 100),
                            screenCounter.value,
                            screenResultsCounter.value,
                            stockCode,
                        )
                    )
                    + colorText.END,
                    end="",
                )
            except ZeroDivisionError as e:
                default_logger().debug(e, exc_info=True)
                pass
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                pass
        if (data is None or len(data) == 0) and printCounter:
            OutputControls().printOutput(
                colorText.FAIL
                + "=> Failed to fetch!"
                + colorText.END,
                end="\r",
                flush=True,
            )
            raise StockDataEmptyException
        if printCounter:
            OutputControls().printOutput(
                colorText.GREEN + "=> Done!" + colorText.END,
                end="\r",
                flush=True,
            )
        return data
