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
# import yfinance as yf
# from yfinance import shared
# from yfinance.const import USER_AGENTS
from PKDevTools.classes.Utils import USER_AGENTS
import random
# from yfinance.version import version as yfVersion
# if yfVersion == "0.2.28":
#     from yfinance.data import TickerData as YfData
#     class YFPricesMissingError(Exception):
#         pass
#     class YFInvalidPeriodError(Exception):
#         pass
#     class YFRateLimitError(Exception):
#         pass
# else:
#     from yfinance.data import YfData
#     from yfinance.exceptions import YFPricesMissingError, YFInvalidPeriodError, YFRateLimitError
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
# This Class Handles Fetching of Stock Data over the internet

from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
   pass

# https://help.yahooinc.com/dsp-api/docs/rate-limits
# Define multiple rate limits
TRY_FACTOR = 1
yf_limiter = Limiter(
    RequestRate(60*TRY_FACTOR, Duration.MINUTE),      # Max 60 requests per minute
    RequestRate(360*TRY_FACTOR, Duration.HOUR),       # Max 360 requests per hour
    RequestRate(8000*TRY_FACTOR, Duration.DAY)        # Max 8000 requests per day
)
# yf_session = CachedLimiterSession(
#    limiter=yf_limiter,
#    bucket_class=MemoryQueueBucket,
#    backend=SQLiteCache(db_path=os.path.join(Archiver.get_user_data_dir(),"yfinance.cache")),
# )
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
        info = None #yf.Tickers(ticker).tickers[ticker].fast_info
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

    # Fetch stock price data from Yahoo finance
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
        """
        if isinstance(stockCode,list):
            if len(exchangeSuffix) > 0:
                stockCode = [(f"{x}{exchangeSuffix}" if (not x.endswith(exchangeSuffix) and not x.startswith("^")) else x) for x in stockCode]
        elif isinstance(stockCode,str):
            if len(exchangeSuffix) > 0:
                stockCode = f"{stockCode}{exchangeSuffix}" if (not stockCode.endswith(exchangeSuffix) and not stockCode.startswith("^")) else stockCode
        if (period in ["1d","5d","1mo","3mo","5mo"] or duration[-1] in ["m","h"]):
            # Since this is intraday data, we'd just need to start from the last trading session
            # if start is None:
            #     start = PKDateUtilities.tradingDate().strftime("%Y-%m-%d")
            # if end is None:
            #     end = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
            # if start == end:
                # If we send start and end dates for intraday, it comes back with empty dataframe
            start = None
            end = None
            # if duration == "1m" and period == "1d":
            #     period = "5d" # Download 1m data for the last 5 days
        """
        data = None
        """
        with SuppressOutput(suppress_stdout=(not printCounter), suppress_stderr=(not printCounter)):
            try:
                if yfVersion == "0.2.28":
                    YfData.user_agent_headers = {
                        'User-Agent': random.choice(USER_AGENTS)}
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
                    timeout=self.configManager.generalTimeout/4,
                    start=start,
                    end=end,
                    auto_adjust=True,
                    threads=len(stockCode) if not isinstance(stockCode,str) else True,
                    session=yf_session
                )
                if isinstance(stockCode,str):
                    if (data is None or data.empty):
                        for ticker in shared._ERRORS:
                            err = shared._ERRORS.get(ticker)
                            # Maybe this stock is recently listed. Let's try and fetch for the last month
                            if "YFInvalidPeriodError" in err: #and "Period \'1mo\' is invalid" not in err:
                                recommendedPeriod = period
                                if isinstance(err,YFInvalidPeriodError):
                                    recommendedPeriod = err.valid_ranges[-1]
                                else:
                                    recommendedPeriod = str(err).split("[")[1].split("]")[0].split(",")[-1].strip()
                                recommendedPeriod = recommendedPeriod.replace("'","").replace("\"","")
                                # default_logger().debug(f"Sending request again for {ticker} with period:{recommendedPeriod}")
                                data = self.fetchStockData(stockCode=ticker,period=period,duration=duration,printCounter=printCounter, start=start,end=end,proxyServer=proxyServer,)
                                return data
                            elif "YFRateLimitError" in err:
                                if attempt <= 2:
                                    default_logger().debug(f"YFRateLimitError Hit! Going for attempt : {attempt+1}")
                                    # sleep(attempt*1) # Exponential backoff
                                    # return self.fetchStockData(stockCode=stockCode,period=period,duration=duration,printCounter=printCounter, start=start,end=end,screenResultsCounter=screenResultsCounter,screenCounter=screenCounter,totalSymbols=totalSymbols,exchangeSuffix=exchangeSuffix,attempt=attempt+1)
                    else:
                        multiIndex = data.keys()
                        if isinstance(multiIndex, pd.MultiIndex):
                            # If we requested for multiple stocks from yfinance
                            # we'd have received a multiindex dataframe
                            listStockCodes = multiIndex.get_level_values(0)
                            data = data.get(listStockCodes[0])
                # else:
                #     if (data is None or data.empty):
                #         if len(shared._ERRORS) > 0:
                #             default_logger().debug(shared._ERRORS)
                #         for ticker in shared._ERRORS:
                #             err = shared._ERRORS.get(ticker)
                #             if "YFRateLimitError" in err:
                #                 if attempt <= 2:
                #                     default_logger().debug(f"YFRateLimitError Hit! Going for attempt : {attempt+1}")
                                    # sleep(attempt*2) # Exponential backoff
                                    # return self.fetchStockData(stockCode=stockCode,period=period,duration=duration,printCounter=printCounter, start=start,end=end,screenResultsCounter=screenResultsCounter,screenCounter=screenCounter,totalSymbols=totalSymbols,exchangeSuffix=exchangeSuffix,attempt=attempt+1)
            except (KeyError,YFPricesMissingError) as e: # pragma: no cover
                default_logger().debug(e,exc_info=True)
                pass
            except YFRateLimitError as e:
                default_logger().debug(f"YFRateLimitError Hit! \n{e}")
                # if attempt <= 2:
                #     default_logger().debug(f"YFRateLimitError Hit! Going for attempt : {attempt+1}")
                    # sleep(attempt*2) # Exponential backoff
                    # return self.fetchStockData(stockCode=stockCode,period=period,duration=duration,printCounter=printCounter, start=start,end=end,screenResultsCounter=screenResultsCounter,screenCounter=screenCounter,totalSymbols=totalSymbols,exchangeSuffix=exchangeSuffix,attempt=attempt+1)
                pass
            except (YFInvalidPeriodError,Exception) as e: # pragma: no cover
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
            except ZeroDivisionError as e: # pragma: no cover
                default_logger().debug(e, exc_info=True)
                pass
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
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
        """
        return data

    # Get Daily Nifty 50 Index:
    def fetchLatestNiftyDaily(self, proxyServer=None):
        return None
        data = yf.download(
            tickers="^NSEI",
            period="5d",
            interval="1d",
            proxy=proxyServer,
            progress=False,
            timeout=self.configManager.longTimeout,
        )
        return data

    # Get Data for Five EMA strategy
    def fetchFiveEmaData(self, proxyServer=None):
        return None
        nifty_sell = yf.download(
            tickers="^NSEI",
            period="5d",
            interval="5m",
            proxy=proxyServer,
            progress=False,
            timeout=self.configManager.longTimeout,
        )
        banknifty_sell = yf.download(
            tickers="^NSEBANK",
            period="5d",
            interval="5m",
            proxy=proxyServer,
            progress=False,
            timeout=self.configManager.longTimeout,
        )
        nifty_buy = yf.download(
            tickers="^NSEI",
            period="5d",
            interval="15m",
            proxy=proxyServer,
            progress=False,
            timeout=self.configManager.longTimeout,
        )
        banknifty_buy = yf.download(
            tickers="^NSEBANK",
            period="5d",
            interval="15m",
            proxy=proxyServer,
            progress=False,
            timeout=self.configManager.longTimeout,
        )
        return nifty_buy, banknifty_buy, nifty_sell, banknifty_sell

    # Load stockCodes from the watchlist.xlsx
    def fetchWatchlist(self):
        createTemplate = False
        data = pd.DataFrame()
        try:
            data = pd.read_excel("watchlist.xlsx")
        except FileNotFoundError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + f"  [+] watchlist.xlsx not found in {os.getcwd()}"
                + colorText.END
            )
            createTemplate = True
        try:
            if not createTemplate:
                data = data["Stock Code"].values.tolist()
        except KeyError as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + '  [+] Bad Watchlist Format: First Column (A1) should have Header named "Stock Code"'
                + colorText.END
            )
            createTemplate = True
        if createTemplate:
            sample = {"Stock Code": ["SBIN", "INFY", "TATAMOTORS", "ITC"]}
            sample_data = pd.DataFrame(sample, columns=["Stock Code"])
            sample_data.to_excel("watchlist_template.xlsx", index=False, header=True)
            OutputControls().printOutput(
                colorText.BLUE
                + f"  [+] watchlist_template.xlsx created in {os.getcwd()} as a referance template."
                + colorText.END
            )
            return None
        return data
