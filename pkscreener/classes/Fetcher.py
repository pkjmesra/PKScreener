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
"""
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   28/04/2021
 *  Description         :   Class for handling networking for fetching stock codes and data
"""

import csv
import json
import os
import random
import sys
import urllib
import warnings
from datetime import timedelta
from io import StringIO
from bs4 import BeautifulSoup

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
import requests
import requests_cache
import yfinance as yf
from requests.exceptions import ConnectTimeout, ReadTimeout
from requests_cache import CachedSession
from urllib3.exceptions import ReadTimeoutError

from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger
from pkscreener.classes.SuppressOutput import SuppressOutput
from pkscreener.classes.PKHTMLScraper import FinancialsDownloader

requests.packages.urllib3.util.connection.HAS_IPV6 = False
session = CachedSession(
    "pkscreener_cache",
    expire_after=timedelta(hours=6),
    stale_if_error=True,
)

# Exception class if yfinance stock delisted


class StockDataEmptyException(Exception):
    pass


# This Class Handles Fetching of Stock Data over the internet

class tools:
    def __init__(self, configManager):
        self.configManager = configManager
        self._proxy = None
        pass
    
    @property
    def proxyServer(self):
        if self._proxy is None:
            self._proxy = self._getProxyServer()
        return self._proxy
    
    def _getProxyServer(self):
        # Get system wide proxy for networking
        try:
            proxy = urllib.request.getproxies()["http"]
            proxy = {"https": proxy}
        except KeyError as e:
            # default_logger().debug(e, exc_info=True)
            proxy = None
        return proxy

    def postURL(self, url, data=None, headers={}, trial=1):
        try:
            response = None
            requestor = session
            # We should try to switch to requests lib if cached_session 
            # begin to give some problem after we've tried for
            # 50% of the configured retrials.
            if trial >= int(self.configManager.maxNetworkRetryCount/2):
                requestor = requests
            response = requestor.post(
                            url,
                            proxies=self.proxyServer,
                            data = data,
                            headers=headers,
                            timeout=trial*self.configManager.generalTimeout,
                        )
        except (ConnectTimeout,ReadTimeoutError,ReadTimeout) as e:
            default_logger().debug(e, exc_info=True)
            if trial <= int(self.configManager.maxNetworkRetryCount):
                print(colorText.BOLD + colorText.FAIL + f"[+] Network Request timed-out. Going for {trial} of {self.configManager.maxNetworkRetryCount}th trial..." + colorText.END, end="")
                return self.postURL(url, data=data, headers=headers,trial=trial+1)
        except Exception as e:
            # Something went wrong with the CachedSession.
            default_logger().debug(e, exc_info=True)
            if trial <= int(self.configManager.maxNetworkRetryCount):
                if trial <= 1:
                    # Let's try and restart the cache
                    self.configManager.restartRequestsCache()
                elif trial > 1 and requests_cache.is_installed():
                    # REstarting didn't fix it. We need to disable the cache altogether.
                    requests_cache.clear()
                    requests_cache.uninstall_cache()
                print(colorText.BOLD + colorText.FAIL + f"[+] Network Request failed. Going for {trial} of {self.configManager.maxNetworkRetryCount}th trial..." + colorText.END, end="")
                return self.postURL(url, data=data, headers=headers,trial=trial+1)
        if trial > 1 and not requests_cache.is_installed():
            # Let's try and re-enable the caching behaviour before exiting.
            # Maybe there was something wrong with this request, but the next
            # request should have access to cache.
            self.configManager.restartRequestsCache()
        return response

    def fetchURL(self, url, stream=False, trial=1):
        try:
            response = None
            requestor = session
            # We should try to switch to requests lib if cached_session 
            # begin to give some problem after we've tried for
            # 50% of the configured retrials.
            if trial >= int(self.configManager.maxNetworkRetryCount/2):
                requestor = requests
            response = requestor.get(
                            url,
                            proxies=self.proxyServer,
                            stream = stream,
                            timeout=trial*self.configManager.generalTimeout,
                        ) 
        except (ConnectTimeout,ReadTimeoutError,ReadTimeout) as e:
            default_logger().debug(e, exc_info=True)
            if trial <= int(self.configManager.maxNetworkRetryCount):
                print(colorText.BOLD + colorText.FAIL + f"[+] Network Request timed-out. Going for {trial} of {self.configManager.maxNetworkRetryCount}th trial..." + colorText.END, end="")
                return self.fetchURL(url, stream=stream, trial=trial+1)
        except Exception as e:
            # Something went wrong with the CachedSession.
            default_logger().debug(e, exc_info=True)
            if trial <= int(self.configManager.maxNetworkRetryCount):
                if trial <= 1:
                    # Let's try and restart the cache
                    self.configManager.restartRequestsCache()
                elif trial > 1 and requests_cache.is_installed():
                    # REstarting didn't fix it. We need to disable the cache altogether.
                    requests_cache.clear()
                    requests_cache.uninstall_cache()
                print(colorText.BOLD + colorText.FAIL + f"[+] Network Request failed. Going for {trial} of {self.configManager.maxNetworkRetryCount}th trial..." + colorText.END, end="")
                return self.fetchURL(url, stream=stream, trial=trial+1)
        if trial > 1 and not requests_cache.is_installed():
            # Let's try and re-enable the caching behaviour before exiting.
            # Maybe there was something wrong with this request, but the next
            # request should have access to cache.
            self.configManager.restartRequestsCache()
        return response
                
    def fetchCodes(self, tickerOption):
        listStockCodes = []
        if tickerOption == 12:
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            res = self.fetchURL(url)
            if res is None or res.status_code != 200:
                return listStockCodes
            try:
                data = pd.read_csv(StringIO(res.text))
                return list(data["SYMBOL"].values)
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                return listStockCodes
            
        tickerMapping = {
            1: "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
            2: "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
            3: "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
            4: "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
            5: "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
            6: "https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
            7: "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
            8: "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
            9: "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
            10: "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
            11: "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
            14: "https://archives.nseindia.com/content/fo/fo_mktlots.csv",
        }

        url = tickerMapping.get(tickerOption)

        try:
            res = self.fetchURL(url)
            if res is None or res.status_code != 200:
                return listStockCodes
            cr = csv.reader(res.text.strip().split("\n"))

            if tickerOption == 14:
                for i in range(5):
                    next(cr)  # skipping first line
                for row in cr:
                    listStockCodes.append(row[1])
            else:
                next(cr)  # skipping first line
                for row in cr:
                    listStockCodes.append(row[2])
        except Exception as e:
            default_logger().debug(e, exc_info=True)

        return listStockCodes

    # Fetch all stock codes from NSE
    def fetchStockCodes(self, tickerOption, stockCode=None):
        listStockCodes = []
        if tickerOption == 0:
            stockCode = None
            while stockCode is None or stockCode == "":
                stockCode = str(
                    input(
                        colorText.BOLD
                        + colorText.BLUE
                        + "[+] Enter Stock Code(s) for screening (Multiple codes should be seperated by ,): "
                    )
                ).upper()
            stockCode = stockCode.replace(" ", "")
            listStockCodes = stockCode.split(",")
        else:
            print(colorText.BOLD + "[+] Getting Stock Codes From NSE... ", end="")
            listStockCodes = self.fetchCodes(tickerOption)
            if len(listStockCodes) > 10:
                print(
                    colorText.GREEN
                    + ("=> Done! Fetched %d stock codes." % len(listStockCodes))
                    + colorText.END
                )
                if self.configManager.shuffleEnabled:
                    random.shuffle(listStockCodes)
                    print(
                        colorText.BLUE
                        + "[+] Stock shuffling is active."
                        + colorText.END
                    )
                else:
                    print(
                        colorText.FAIL
                        + "[+] Stock shuffling is inactive."
                        + colorText.END
                    )
                if self.configManager.stageTwo:
                    print(
                        colorText.BLUE
                        + "[+] Screening only for the stocks in Stage-2! Edit User Config to change this."
                        + colorText.END
                    )
                else:
                    print(
                        colorText.FAIL
                        + "[+] Screening only for the stocks in all Stages! Edit User Config to change this."
                        + colorText.END
                    )

            else:
                input(
                    colorText.FAIL
                    + "=> Error getting stock codes from NSE! Press <Enter> to exit!"
                    + colorText.END
                )

        return listStockCodes

    # Fetch stock price data from Yahoo finance
    def fetchStockData(
        self,
        stockCode,
        period,
        duration,
        proxyServer,
        screenResultsCounter,
        screenCounter,
        totalSymbols,
        printCounter=False,
    ):
        with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
            data = yf.download(
                tickers=stockCode + ".NS",
                period=period,
                interval=duration,
                proxy=proxyServer,
                progress=False,
                timeout=self.configManager.longTimeout,
            )
        if printCounter:
            sys.stdout.write("\r\033[K")
            try:
                print(
                    colorText.BOLD
                    + colorText.GREEN
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
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                pass
            if len(data) == 0:
                print(
                    colorText.BOLD
                    + colorText.FAIL
                    + "=> Failed to fetch!"
                    + colorText.END,
                    end="\r",
                    flush=True,
                )
                raise StockDataEmptyException
                return None
            print(
                colorText.BOLD + colorText.GREEN + "=> Done!" + colorText.END,
                end="\r",
                flush=True,
            )
        return data

    # Get Daily Nifty 50 Index:
    def fetchLatestNiftyDaily(self, proxyServer=None):
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
        except FileNotFoundError as e:
            default_logger().debug(e, exc_info=True)
            print(
                colorText.BOLD
                + colorText.FAIL
                + f"[+] watchlist.xlsx not found in {os.getcwd()}"
                + colorText.END
            )
            createTemplate = True
        try:
            if not createTemplate:
                data = data["Stock Code"].values.tolist()
        except KeyError as e:
            default_logger().debug(e, exc_info=True)
            print(
                colorText.BOLD
                + colorText.FAIL
                + '[+] Bad Watchlist Format: First Column (A1) should have Header named "Stock Code"'
                + colorText.END
            )
            createTemplate = True
        if createTemplate:
            sample = {"Stock Code": ["SBIN", "INFY", "TATAMOTORS", "ITC"]}
            sample_data = pd.DataFrame(sample, columns=["Stock Code"])
            sample_data.to_excel("watchlist_template.xlsx", index=False, header=True)
            print(
                colorText.BOLD
                + colorText.BLUE
                + f"[+] watchlist_template.xlsx created in {os.getcwd()} as a referance template."
                + colorText.END
            )
            return None
        return data

    def fetchMorningstarTopDividendsYieldStocks(self):
        url = "https://lt.morningstar.com/api/rest.svc/g9vi2nsqjb/security/screener?page=1&pageSize=100&sortOrder=dividendYield%20desc&outputType=json&version=1&languageId=en&currencyId=BAS&universeIds=E0EXG%24XBOM%7CE0EXG%24XNSE&securityDataPoints=secId%2Cname%2CexchangeId%2CsectorId%2CindustryId%2CmarketCap%2CdividendYield%2CclosePrice%2CpriceCurrency%2CPEGRatio%2CpeRatio%2CquantitativeStarRating%2CequityStyleBox%2CgbrReturnM0%2CgbrReturnD1%2CgbrReturnW1%2CgbrReturnM1%2CgbrReturnM3%2CgbrReturnM6%2CgbrReturnM12%2CgbrReturnM36%2CgbrReturnM60%2CgbrReturnM120%2CrevenueGrowth3Y%2CdebtEquityRatio%2CnetMargin%2Croattm%2Croettm%2Cexchange&filters=&term="
        res = self.fetchURL(url)
        if res is None or res.status_code != 200:
            return None
        try:
            data = pd.read_json(StringIO(res.text))
            rows = data["rows"]
            output = pd.DataFrame()
            for row in rows:
                df_row = pd.DataFrame([row], columns=["name", "marketCap","exchangeId", "dividendYield", "closePrice","peRatio"])
                output = pd.concat([output, df_row], ignore_index=True)
            
            output.loc[:, "name"] = output.loc[:, "name"].apply(
                        lambda x: " ".join(x.split(" ")[:6])
                    )
            output.loc[:, "marketCap"] = output.loc[:, "marketCap"].apply(
                        lambda x: colorText.FAIL + str("{:.2f}".format(x/10000000)).replace("nan","-")+ colorText.END
                    )
            output.loc[:, "dividendYield"] = output.loc[:, "dividendYield"].apply(
                        lambda x: colorText.GREEN + str("{:.2f}".format(x))+ colorText.END
                    )
            output.loc[:, "closePrice"] = output.loc[:, "closePrice"].apply(
                        lambda x: colorText.FAIL + str("{:.2f}".format(x))+ colorText.END
                    )
            output.loc[:, "peRatio"] = output.loc[:, "peRatio"].apply(
                        lambda x: colorText.GREEN + str("{:.2f}".format(x)).replace("nan","-")+ colorText.END
                    )
            output.loc[:, "exchangeId"] = output.loc[:, "exchangeId"].apply(
                        lambda x: colorText.FAIL + ("BSE" if x == "EX$$$$XBOM" else "NSE") + colorText.END
                    )
            output.drop_duplicates(subset=['name'], keep='last',inplace=True)
            output.rename(
                columns={
                    "name": f"Stock",
                    "marketCap": f"Market Cap. (Cr)",
                    "exchangeId": f"Exchange",
                    "dividendYield": f"Dividend (%)",
                    "closePrice": f"LTP",
                    "peRatio": f"PE",
                },
                inplace=True,
            )
            output.set_index("Stock", inplace=True)
            return output
        except:
            pass
        return None

    def fetchMorningstarFundFavouriteStocks(self):
        getURL = "https://morningstar.in/tools/most-popular-stocks-in-mutual-fund.aspx"
        getRes = self.fetchURL(getURL)
        headers = getRes.headers
        headers['Cookie'] = getRes.headers['Set-Cookie']
        url = "https://morningstar.in/tools/most-popular-stocks-in-mutual-fund.aspx?tid=10"
        postData = 'ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24scriptMgr=ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24upnlSectorExposure%7Cctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24btnGo&__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwULLTExNTA0MjQxMzEPZBYCZg9kFgJmD2QWAgIDD2QWBgIHD2QWBAIBDxYCHgdWaXNpYmxlZ2QCFw8WAh8AaGQCCw8WAh8AaGQCDQ9kFgZmDxYCHgVjbGFzcwURbWRzLWJ1dHRvbiBhY3RpdmVkAgIPFgIeC18hSXRlbUNvdW50AgcWDgIBD2QWBGYPFQILUGVyZm9ybWFuY2ULUGVyZm9ybWFuY2VkAgEPFgIfAgIGFgwCAQ9kFgJmDxUFACMvdG9vbHMvbXV0dWFsLWZ1bmQtcGVyZm9ybWFuY2UuYXNweBBGdW5kIFBlcmZvcm1hbmNlBV9zZWxmEEZ1bmQgUGVyZm9ybWFuY2VkAgIPZBYCZg8VBQAsL3Rvb2xzL211dHVhbC1mdW5kLWNhdGVnb3J5LXBlcmZvcm1hbmNlLmFzcHgUQ2F0ZWdvcnkgUGVyZm9ybWFuY2UFX3NlbGYUQ2F0ZWdvcnkgUGVyZm9ybWFuY2VkAgMPZBYCZg8VBQAlL3Rvb2xzL211dHVhbC1mdW5kLXJpc2stbWVhc3VyZXMuYXNweBJGdW5kIFJpc2sgTWVhc3VyZXMFX3NlbGYSRnVuZCBSaXNrIE1lYXN1cmVzZAIED2QWAmYPFQUALi90b29scy9tdXR1YWwtZnVuZC1jYXRlZ29yeS1yaXNrLW1lYXN1cmVzLmFzcHgWQ2F0ZWdvcnkgUmlzayBNZWFzdXJlcwVfc2VsZhZDYXRlZ29yeSBSaXNrIE1lYXN1cmVzZAIFD2QWAmYPFQUAJi90b29scy90b3AtcGVyZm9ybWluZy1tdXR1YWwtZnVuZC5hc3B4FFRvcCBQZXJmb3JtaW5nIEZ1bmRzBV9zZWxmFFRvcCBQZXJmb3JtaW5nIEZ1bmRzZAIGD2QWAmYPFQUALi90b29scy9tdXR1YWwtZnVuZC1wZXJmb3JtYW5jZS1jb21wYXJpc29uLmFzcHgWUGVyZm9ybWFuY2UgQ29tcGFyaXNvbgVfc2VsZhZQZXJmb3JtYW5jZSBDb21wYXJpc29uZAICD2QWBGYPFQIJUG9ydGZvbGlvCVBvcnRmb2xpb2QCAQ8WAh8CAgYWDAIBD2QWAmYPFQUAKi90b29scy9tdXR1YWwtZnVuZC1kZXRhaWxlZC1wb3J0Zm9saW8uYXNweBJEZXRhaWxlZCBQb3J0Zm9saW8FX3NlbGYSRGV0YWlsZWQgUG9ydGZvbGlvZAICD2QWAmYPFQUAIi90b29scy9pbmRpYW4tc2VjdG9yLWV4cG9zdXJlLmFzcHgWSW5kaWFuIFNlY3RvciBFeHBvc3VyZQVfc2VsZhZJbmRpYW4gU2VjdG9yIEV4cG9zdXJlZAIDD2QWAmYPFQUAIS90b29scy9pbmRpYW4tY3JlZGl0LXF1YWxpdHkuYXNweBVJbmRpYW4gQ3JlZGl0IFF1YWxpdHkFX3NlbGYVSW5kaWFuIENyZWRpdCBRdWFsaXR5ZAIED2QWAmYPFQUALi90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHgMU3RvY2sgU2VhcmNoBV9zZWxmDFN0b2NrIFNlYXJjaGQCBQ9kFgJmDxUFCHNlbGVjdGVkLi90b29scy9tb3N0LXBvcHVsYXItc3RvY2tzLWluLW11dHVhbC1mdW5kLmFzcHgTTW9zdCBQb3B1bGFyIFN0b2NrcwVfc2VsZhNNb3N0IFBvcHVsYXIgU3RvY2tzZAIGD2QWAmYPFQUALy90b29scy9zZWN0b3Itc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4DVNlY3RvciBTZWFyY2gFX3NlbGYNU2VjdG9yIFNlYXJjaGQCAw9kFgRmDxUCCFJlc2VhcmNoCFJlc2VhcmNoZAIBDxYCHwICAhYEAgEPZBYCZg8VBQAWL2ZlYXR1cmVkLXJlcG9ydHMuYXNweA9NZWRhbGlzdCBSYXRpbmcGX2JsYW5rD01lZGFsaXN0IFJhdGluZ2QCAg9kFgJmDxUFACQvdG9vbHMvbXV0dWFsLWZ1bmQtc3Rhci1yYXRpbmdzLmFzcHgMU3RhciBSYXRpbmdzBV9zZWxmDFN0YXIgUmF0aW5nc2QCBA9kFgRmDxUCC0NhbGN1bGF0b3JzC0NhbGN1bGF0b3JzZAIBDxYCHwICAhYEAgEPZBYCZg8VBQAqL3Rvb2xzL211dHVhbC1mdW5kLXJldHVybnMtY2FsY3VsYXRvci5hc3B4ElJldHVybnMgQ2FsY3VsYXRvcgVfc2VsZhJSZXR1cm5zIENhbGN1bGF0b3JkAgIPZBYCZg8VBQAmL3Rvb2xzL211dHVhbC1mdW5kLXNpcC1jYWxjdWxhdG9yLmFzcHgOU0lQIENhbGN1bGF0b3IFX3NlbGYOU0lQIENhbGN1bGF0b3JkAgUPZBYEZg8VAgZMb29rdXAGTG9va3VwZAIBDxYCHwICBhYMAgEPZBYCZg8VBQAiL3Rvb2xzL211dHVhbC1mdW5kLWxhdGVzdC1uYXYuYXNweApMYXRlc3QgTkFWBV9zZWxmCkxhdGVzdCBOQVZkAgIPZBYCZg8VBQAWL2Z1bmRzL2ZhY3RzaGVldHMuYXNweA5GdW5kIEZhY3RzaGVldAZfYmxhbmsORnVuZCBGYWN0c2hlZXRkAgMPZBYCZg8VBQAjL3Rvb2xzL211dHVhbC1mdW5kLWluZm9ybWF0aW9uLmFzcHgQRnVuZCBJbmZvcm1hdGlvbgVfc2VsZhBGdW5kIEluZm9ybWF0aW9uZAIED2QWAmYPFQUANi90b29scy9tdXR1YWwtZnVuZC1hbWZpLWF2ZXJhZ2UtYXVtLWJ5LWZ1bmQtaG91c2UuYXNweA5BdmcgQVVNIGJ5IEFNQwVfc2VsZg5BdmcgQVVNIGJ5IEFNQ2QCBQ9kFgJmDxUFADUvdG9vbHMvbXV0dWFsLWZ1bmQtYW1maS1hdmVyYWdlLWF1bS1ieS1mdW5kLXdpc2UuYXNweA9BdmcgQVVNIGJ5IEZ1bmQFX3NlbGYPQXZnIEFVTSBieSBGdW5kZAIGD2QWAmYPFQUAJy90b29scy9tdXR1YWwtZnVuZC1uZm8taW5mb3JtYXRpb24uYXNweANORk8FX3NlbGYDTkZPZAIGD2QWBGYPFQIRUG9ydGZvbGlvIE1hbmFnZXIRUG9ydGZvbGlvIE1hbmFnZXJkAgEPFgIfAgIBFgICAQ9kFgJmDxUFABAvcG0vZGVmYXVsdC5hc3B4EVBvcnRmb2xpbyBNYW5hZ2VyBl9ibGFuaxFQb3J0Zm9saW8gTWFuYWdlcmQCBw9kFgRmDxUCCEFkdmFuY2VkCEFkdmFuY2VkZAIBDxYCHwICBBYIAgEPZBYCZg8VBQAaL3Rvb2xzL0VDRnVuZHNjcmVlbmVyLmFzcHgUTXV0dWFsIEZ1bmQgU2NyZWVuZXIGX2JsYW5rFE11dHVhbCBGdW5kIFNjcmVlbmVyZAICD2QWAmYPFQUAGS90b29scy9ldGYtcXVpY2tyYW5rLmFzcHgNRVRGIFF1aWNrcmFuawZfYmxhbmsNRVRGIFF1aWNrcmFua2QCAw9kFgJmDxUFAB8vdG9vbHMvZWNpbnZlc3RtZW50Y29tcGFyZS5hc3B4DEZ1bmQgQ29tcGFyZQZfYmxhbmsMRnVuZCBDb21wYXJlZAIED2QWAmYPFQUAGy90b29scy9lY3BvcnRmb2xpb3hyYXkuYXNweA1JbnN0YW50IFgtUmF5Bl9ibGFuaw1JbnN0YW50IFgtUmF5ZAIDD2QWBAIDDxYCHgVzdHlsZQUWZmxvYXQ6bGVmdDt3aWR0aDoxMDAlOxYCAgEPZBYCZg9kFgICAQ9kFgJmD2QWAgIRDxQrAAJkZGQCBQ8PFgIfAGhkZBgBBUtjdGwwMCRjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGNvbnRlbnRSZXNlYXJjaFRvb2xzJGN0bDAwJGxzdFBvcHVsYXJTdG9ja3MPZ2Spoj%2FnsQ6hGl0sA8GZ44fTCOJP4RxzR4TaOlJ8EmOPZw%3D%3D&__VIEWSTATEGENERATOR=BA27C21D&__EVENTVALIDATION=%2FwEdABKG1fCeNuDiu3yOlM58qZuIy0uYJYP1tw4rbCpvyc%2FgfoCSgu3wYE2RMXmCa14bD5glUe8feb14S1VenQlduIvvzaZA8XpuxQGSHP6360PH5LGPVBwPVcjF06QfM%2F4rdX5FobP5yY1mNjGyjkz5YY%2F3hIaanjP0X3aWj1Zl3gtmayHFK9h8SfYHpnL3Fdn91PL6phllOjnuMLEBUAXnCQ%2BT5J9%2Fi%2FPfGV%2FARoWyvyT3Gj8OdBTQ7cq5R36dNtedm0TMa%2BqPQtDAMSXpAkB%2FbMUMUh6jBTnoFSZjjU9VCjwlz9WcTtdhOQETLzbDd57Tq%2Bg4HKwgo%2FdJKw2IyLDEPQvKR7VvbnuaYjfDsPcS1IiYQk1b95yd6r1UcqNZ8aLybHL7DUnaRzeRRa%2BCzyqQUx%2BayWd4ZwQkMJvNDd%2BtgtaPwg%3D%3D&ctl00%24ctl00%24hdnEnvironemnt=prod&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl01%24navID=mnuHome&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl02%24navID=mnuPortfolio&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl03%24navID=mnuFunds&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl04%24navID=mnuEquities&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl05%24navID=mnuPersonalFinance&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl06%24navID=mnuTools&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl07%24navID=mnuArchives&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl08%24navID=mnuAdviser&ctl00%24ctl00%24ucHeader%24txtQuote%24txtAutoComplete=MF%2FStock%2FULIP&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24txtNumber=100&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24drpSort=ChangeInShares&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24hdnSelectedTool=10&__ASYNCPOST=true&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24btnGo=Go'
        res = self.postURL(url,postData,headers)
        if res is None or res.status_code != 200:
            return None
        try:
            json_text = res.text
            json_data = json_text #json.loads(json_text)
            result_soup = BeautifulSoup(json_data,'html.parser')
            fd = FinancialsDownloader()
            return fd._parse(result_soup)
        except:
            pass
        return None
    
    # https://www.morningstar.com/stocks/xnse/idea/ownership
    # https://api-global.morningstar.com/sal-service/v1/stock/ownership/v1/0P0000C2H4/OwnershipData/mutualfund/20/data?languageId=en&locale=en&clientId=MDC&component=sal-ownership&version=4.14.0
    # For each stock: https://api-global.morningstar.com/sal-service/v1/stock/header/v2/data/0P0000N0EO/securityInfo?showStarRating=&languageId=en&locale=en&clientId=RSIN_SAL&component=sal-quote&version=4.13.0&access_token=JrelGdhGkgqeSJhy7BufcEzwN0sb
    # Major ownership data: https://api-global.morningstar.com/sal-service/v1/stock/ownership/v1/0P0000C2H4/OwnershipData/institution/20/data?languageId=en&locale=en&clientId=MDC&component=sal-ownership&version=4.14.0
    # ESG risk score: https://api-global.morningstar.com/sal-service/v1/stock/esgRisk/0P0000C2H4/data?languageId=en&locale=en&clientId=MDC&component=sal-eqsv-risk-rating-assessment&version=4.14.0
    # https://www.morningstar.com/stocks/xnse/idea/sustainability
    def fetchMorningstarShareholdingPatternStocks(self):
        url = "https://morningstar.in/tools/most-popular-stocks-in-mutual-fund.aspx?tid=10"
        postData = 'ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24scriptMgr=ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24upnlSectorExposure%7Cctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24btnGo&__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwULLTExNTA0MjQxMzEPZBYCZg9kFgJmD2QWAgIDD2QWBgIHD2QWBAIBDxYCHgdWaXNpYmxlZ2QCFw8WAh8AaGQCCw8WAh8AaGQCDQ9kFgZmDxYCHgVjbGFzcwURbWRzLWJ1dHRvbiBhY3RpdmVkAgIPFgIeC18hSXRlbUNvdW50AgcWDgIBD2QWBGYPFQILUGVyZm9ybWFuY2ULUGVyZm9ybWFuY2VkAgEPFgIfAgIGFgwCAQ9kFgJmDxUFACMvdG9vbHMvbXV0dWFsLWZ1bmQtcGVyZm9ybWFuY2UuYXNweBBGdW5kIFBlcmZvcm1hbmNlBV9zZWxmEEZ1bmQgUGVyZm9ybWFuY2VkAgIPZBYCZg8VBQAsL3Rvb2xzL211dHVhbC1mdW5kLWNhdGVnb3J5LXBlcmZvcm1hbmNlLmFzcHgUQ2F0ZWdvcnkgUGVyZm9ybWFuY2UFX3NlbGYUQ2F0ZWdvcnkgUGVyZm9ybWFuY2VkAgMPZBYCZg8VBQAlL3Rvb2xzL211dHVhbC1mdW5kLXJpc2stbWVhc3VyZXMuYXNweBJGdW5kIFJpc2sgTWVhc3VyZXMFX3NlbGYSRnVuZCBSaXNrIE1lYXN1cmVzZAIED2QWAmYPFQUALi90b29scy9tdXR1YWwtZnVuZC1jYXRlZ29yeS1yaXNrLW1lYXN1cmVzLmFzcHgWQ2F0ZWdvcnkgUmlzayBNZWFzdXJlcwVfc2VsZhZDYXRlZ29yeSBSaXNrIE1lYXN1cmVzZAIFD2QWAmYPFQUAJi90b29scy90b3AtcGVyZm9ybWluZy1tdXR1YWwtZnVuZC5hc3B4FFRvcCBQZXJmb3JtaW5nIEZ1bmRzBV9zZWxmFFRvcCBQZXJmb3JtaW5nIEZ1bmRzZAIGD2QWAmYPFQUALi90b29scy9tdXR1YWwtZnVuZC1wZXJmb3JtYW5jZS1jb21wYXJpc29uLmFzcHgWUGVyZm9ybWFuY2UgQ29tcGFyaXNvbgVfc2VsZhZQZXJmb3JtYW5jZSBDb21wYXJpc29uZAICD2QWBGYPFQIJUG9ydGZvbGlvCVBvcnRmb2xpb2QCAQ8WAh8CAgYWDAIBD2QWAmYPFQUAKi90b29scy9tdXR1YWwtZnVuZC1kZXRhaWxlZC1wb3J0Zm9saW8uYXNweBJEZXRhaWxlZCBQb3J0Zm9saW8FX3NlbGYSRGV0YWlsZWQgUG9ydGZvbGlvZAICD2QWAmYPFQUAIi90b29scy9pbmRpYW4tc2VjdG9yLWV4cG9zdXJlLmFzcHgWSW5kaWFuIFNlY3RvciBFeHBvc3VyZQVfc2VsZhZJbmRpYW4gU2VjdG9yIEV4cG9zdXJlZAIDD2QWAmYPFQUAIS90b29scy9pbmRpYW4tY3JlZGl0LXF1YWxpdHkuYXNweBVJbmRpYW4gQ3JlZGl0IFF1YWxpdHkFX3NlbGYVSW5kaWFuIENyZWRpdCBRdWFsaXR5ZAIED2QWAmYPFQUALi90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHgMU3RvY2sgU2VhcmNoBV9zZWxmDFN0b2NrIFNlYXJjaGQCBQ9kFgJmDxUFCHNlbGVjdGVkLi90b29scy9tb3N0LXBvcHVsYXItc3RvY2tzLWluLW11dHVhbC1mdW5kLmFzcHgTTW9zdCBQb3B1bGFyIFN0b2NrcwVfc2VsZhNNb3N0IFBvcHVsYXIgU3RvY2tzZAIGD2QWAmYPFQUALy90b29scy9zZWN0b3Itc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4DVNlY3RvciBTZWFyY2gFX3NlbGYNU2VjdG9yIFNlYXJjaGQCAw9kFgRmDxUCCFJlc2VhcmNoCFJlc2VhcmNoZAIBDxYCHwICAhYEAgEPZBYCZg8VBQAWL2ZlYXR1cmVkLXJlcG9ydHMuYXNweA9NZWRhbGlzdCBSYXRpbmcGX2JsYW5rD01lZGFsaXN0IFJhdGluZ2QCAg9kFgJmDxUFACQvdG9vbHMvbXV0dWFsLWZ1bmQtc3Rhci1yYXRpbmdzLmFzcHgMU3RhciBSYXRpbmdzBV9zZWxmDFN0YXIgUmF0aW5nc2QCBA9kFgRmDxUCC0NhbGN1bGF0b3JzC0NhbGN1bGF0b3JzZAIBDxYCHwICAhYEAgEPZBYCZg8VBQAqL3Rvb2xzL211dHVhbC1mdW5kLXJldHVybnMtY2FsY3VsYXRvci5hc3B4ElJldHVybnMgQ2FsY3VsYXRvcgVfc2VsZhJSZXR1cm5zIENhbGN1bGF0b3JkAgIPZBYCZg8VBQAmL3Rvb2xzL211dHVhbC1mdW5kLXNpcC1jYWxjdWxhdG9yLmFzcHgOU0lQIENhbGN1bGF0b3IFX3NlbGYOU0lQIENhbGN1bGF0b3JkAgUPZBYEZg8VAgZMb29rdXAGTG9va3VwZAIBDxYCHwICBhYMAgEPZBYCZg8VBQAiL3Rvb2xzL211dHVhbC1mdW5kLWxhdGVzdC1uYXYuYXNweApMYXRlc3QgTkFWBV9zZWxmCkxhdGVzdCBOQVZkAgIPZBYCZg8VBQAWL2Z1bmRzL2ZhY3RzaGVldHMuYXNweA5GdW5kIEZhY3RzaGVldAZfYmxhbmsORnVuZCBGYWN0c2hlZXRkAgMPZBYCZg8VBQAjL3Rvb2xzL211dHVhbC1mdW5kLWluZm9ybWF0aW9uLmFzcHgQRnVuZCBJbmZvcm1hdGlvbgVfc2VsZhBGdW5kIEluZm9ybWF0aW9uZAIED2QWAmYPFQUANi90b29scy9tdXR1YWwtZnVuZC1hbWZpLWF2ZXJhZ2UtYXVtLWJ5LWZ1bmQtaG91c2UuYXNweA5BdmcgQVVNIGJ5IEFNQwVfc2VsZg5BdmcgQVVNIGJ5IEFNQ2QCBQ9kFgJmDxUFADUvdG9vbHMvbXV0dWFsLWZ1bmQtYW1maS1hdmVyYWdlLWF1bS1ieS1mdW5kLXdpc2UuYXNweA9BdmcgQVVNIGJ5IEZ1bmQFX3NlbGYPQXZnIEFVTSBieSBGdW5kZAIGD2QWAmYPFQUAJy90b29scy9tdXR1YWwtZnVuZC1uZm8taW5mb3JtYXRpb24uYXNweANORk8FX3NlbGYDTkZPZAIGD2QWBGYPFQIRUG9ydGZvbGlvIE1hbmFnZXIRUG9ydGZvbGlvIE1hbmFnZXJkAgEPFgIfAgIBFgICAQ9kFgJmDxUFABAvcG0vZGVmYXVsdC5hc3B4EVBvcnRmb2xpbyBNYW5hZ2VyBl9ibGFuaxFQb3J0Zm9saW8gTWFuYWdlcmQCBw9kFgRmDxUCCEFkdmFuY2VkCEFkdmFuY2VkZAIBDxYCHwICBBYIAgEPZBYCZg8VBQAaL3Rvb2xzL0VDRnVuZHNjcmVlbmVyLmFzcHgUTXV0dWFsIEZ1bmQgU2NyZWVuZXIGX2JsYW5rFE11dHVhbCBGdW5kIFNjcmVlbmVyZAICD2QWAmYPFQUAGS90b29scy9ldGYtcXVpY2tyYW5rLmFzcHgNRVRGIFF1aWNrcmFuawZfYmxhbmsNRVRGIFF1aWNrcmFua2QCAw9kFgJmDxUFAB8vdG9vbHMvZWNpbnZlc3RtZW50Y29tcGFyZS5hc3B4DEZ1bmQgQ29tcGFyZQZfYmxhbmsMRnVuZCBDb21wYXJlZAIED2QWAmYPFQUAGy90b29scy9lY3BvcnRmb2xpb3hyYXkuYXNweA1JbnN0YW50IFgtUmF5Bl9ibGFuaw1JbnN0YW50IFgtUmF5ZAIDD2QWBAIDDxYCHgVzdHlsZQUWZmxvYXQ6bGVmdDt3aWR0aDoxMDAlOxYCAgEPZBYCZg9kFgICAQ9kFgJmD2QWAgIRDxQrAAJkZGQCBQ8PFgIfAGhkZBgBBUtjdGwwMCRjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGNvbnRlbnRSZXNlYXJjaFRvb2xzJGN0bDAwJGxzdFBvcHVsYXJTdG9ja3MPZ2Spoj%2FnsQ6hGl0sA8GZ44fTCOJP4RxzR4TaOlJ8EmOPZw%3D%3D&__VIEWSTATEGENERATOR=BA27C21D&__EVENTVALIDATION=%2FwEdABKG1fCeNuDiu3yOlM58qZuIy0uYJYP1tw4rbCpvyc%2FgfoCSgu3wYE2RMXmCa14bD5glUe8feb14S1VenQlduIvvzaZA8XpuxQGSHP6360PH5LGPVBwPVcjF06QfM%2F4rdX5FobP5yY1mNjGyjkz5YY%2F3hIaanjP0X3aWj1Zl3gtmayHFK9h8SfYHpnL3Fdn91PL6phllOjnuMLEBUAXnCQ%2BT5J9%2Fi%2FPfGV%2FARoWyvyT3Gj8OdBTQ7cq5R36dNtedm0TMa%2BqPQtDAMSXpAkB%2FbMUMUh6jBTnoFSZjjU9VCjwlz9WcTtdhOQETLzbDd57Tq%2Bg4HKwgo%2FdJKw2IyLDEPQvKR7VvbnuaYjfDsPcS1IiYQk1b95yd6r1UcqNZ8aLybHL7DUnaRzeRRa%2BCzyqQUx%2BayWd4ZwQkMJvNDd%2BtgtaPwg%3D%3D&ctl00%24ctl00%24hdnEnvironemnt=prod&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl01%24navID=mnuHome&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl02%24navID=mnuPortfolio&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl03%24navID=mnuFunds&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl04%24navID=mnuEquities&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl05%24navID=mnuPersonalFinance&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl06%24navID=mnuTools&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl07%24navID=mnuArchives&ctl00%24ctl00%24navigation%24rptNavigationMenu%24ctl08%24navID=mnuAdviser&ctl00%24ctl00%24ucHeader%24txtQuote%24txtAutoComplete=MF%2FStock%2FULIP&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24txtNumber=100&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24drpSort=ChangeInShares&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24hdnSelectedTool=10&__ASYNCPOST=true&ctl00%24ctl00%24ContentPlaceHolder1%24contentResearchTools%24ctl00%24btnGo=Go'
        res = self.postURL(url,postData)
        if res is None or res.status_code != 200:
            return None
        return None

# from pkscreener.classes import ConfigManager
# configmgr = ConfigManager.tools()
# f = tools(configmgr)

# f.fetchMorningstarFundFavouriteStocks()
