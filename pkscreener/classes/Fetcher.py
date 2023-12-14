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
from html import escape
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
                        lambda x: " ".join(x.split(" ")[:6]).replace("Ordinary Shares","").replace("Shs Dematerialised","")
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
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass
        return None

    def prepareASPNETFormDataForPost(self, soup):
        # soup = BeautifulSoup(page.content,features="lxml")
        viewstate = soup.select_one("#__VIEWSTATE")["value"]
        viewstategenerator = soup.select_one("#__VIEWSTATEGENERATOR")["value"]
        eventtarget = soup.select_one("#__EVENTTARGET")["value"]
        eventargument = soup.select_one("#__EVENTARGUMENT")["value"]
        eventValidator = soup.select_one("#__EVENTVALIDATION")["value"]
        data = {
                r'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$scriptMgr': r'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$upnlSectorExposure|ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$btnGo',
                r'__EVENTTARGET': eventtarget,
                r'__EVENTARGUMENT': eventargument,                
                r'___VIEWSTATE': viewstate,
                r'__VIEWSTATEGENERATOR': viewstategenerator,
                r'__EVENTVALIDATION': eventValidator,
                r'__ASYNCPOST': r'true',
                r'ctl00$ctl00$hdnEnvironemnt': 'prod',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl01$navID': 'mnuHome',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl02$navID': 'mnuPortfolio',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl03$navID': 'mnuFunds',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl04$navID': 'mnuEquities',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl05$navID': 'mnuPersonalFinance',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl06$navID': 'mnuTools',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl07$navID': 'mnuArchives',
                r'ctl00$ctl00$navigation$rptNavigationMenu$ctl08$navID': 'mnuAdviser',
                r'ctl00$ctl00$ucHeader$txtQuote$txtAutoComplete': 'MF/Stock/ULIP',
                r'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$txtNumber': '100',
                r'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$drpSort': 'NoOfFunds',
                r'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$hdnSelectedTool': '10',
                r'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$btnGo': 'Go',
            }
        return urllib.parse.urlencode(data)
        
    def fetchMorningstarFundFavouriteStocks(self, sortby="ChangeInShares"):
        getURL = "https://morningstar.in/tools/most-popular-stocks-in-mutual-fund.aspx"
        getRes = self.fetchURL(getURL)
        headers = {
            'authority': 'www.morningstar.in',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': 'ASP.NET_SessionId=oykrok0d3kmfpn5sq3453v05; ',
            'dnt': '1',
            'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjE1MjY4MjUiLCJhcCI6IjEzODYwMjM4ODEiLCJpZCI6Ijc3ZWVhNzI1YmNjZTQwNDUiLCJ0ciI6IjkyYzI4ZTgyNjYzODBkMDM3Zjk2MmQwMTVlNTU2NTAwIiwidGkiOjE3MDIyNDA1NDM2NDUsInRrIjoiMzU4OTQifX0=',
            'origin': 'https://www.morningstar.in',
            'referer': 'https://www.morningstar.in/tools/most-popular-stocks-in-mutual-fund.aspx',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'traceparent': '00-92c28e8266380d037f962d015e556500-77eea725bcce4045-01',
            'tracestate': '35894@nr=0-1-1526825-1386023881-77eea725bcce4045----1702240543645',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-microsoftajax': 'Delta=true',
            'x-newrelic-id': 'VQMFV15RDRABV1ZVAAEBUlUG',
            'x-requested-with': 'XMLHttpRequest',
        }
        headers['cookie'] = getRes.headers['Set-Cookie']

        data = {
            'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$scriptMgr': 'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$upnlSectorExposure|ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$btnGo',
            'ctl00$ctl00$hdnEnvironemnt': 'prod',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl01$navID': 'mnuHome',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl02$navID': 'mnuPortfolio',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl03$navID': 'mnuFunds',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl04$navID': 'mnuEquities',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl05$navID': 'mnuPersonalFinance',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl06$navID': 'mnuTools',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl07$navID': 'mnuArchives',
            'ctl00$ctl00$navigation$rptNavigationMenu$ctl08$navID': 'mnuAdviser',
            'ctl00$ctl00$ucHeader$txtQuote$txtAutoComplete': 'MF/Stock/ULIP',
            'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$txtNumber': '100',
            'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$drpSort': 'NoOfFunds' if sortby is None else sortby,
            'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$hdnSelectedTool': '10',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '/wEPDwULLTExNTA0MjQxMzEPZBYCZg9kFgJmD2QWAgIDD2QWBgIHD2QWBAIBDxYCHgdWaXNpYmxlZ2QCFw8WAh8AaGQCCw8WAh8AaGQCDQ9kFgZmDxYCHgVjbGFzcwURbWRzLWJ1dHRvbiBhY3RpdmVkAgIPFgIeC18hSXRlbUNvdW50AgcWDgIBD2QWBGYPFQILUGVyZm9ybWFuY2ULUGVyZm9ybWFuY2VkAgEPFgIfAgIGFgwCAQ9kFgJmDxUFACMvdG9vbHMvbXV0dWFsLWZ1bmQtcGVyZm9ybWFuY2UuYXNweBBGdW5kIFBlcmZvcm1hbmNlBV9zZWxmEEZ1bmQgUGVyZm9ybWFuY2VkAgIPZBYCZg8VBQAsL3Rvb2xzL211dHVhbC1mdW5kLWNhdGVnb3J5LXBlcmZvcm1hbmNlLmFzcHgUQ2F0ZWdvcnkgUGVyZm9ybWFuY2UFX3NlbGYUQ2F0ZWdvcnkgUGVyZm9ybWFuY2VkAgMPZBYCZg8VBQAlL3Rvb2xzL211dHVhbC1mdW5kLXJpc2stbWVhc3VyZXMuYXNweBJGdW5kIFJpc2sgTWVhc3VyZXMFX3NlbGYSRnVuZCBSaXNrIE1lYXN1cmVzZAIED2QWAmYPFQUALi90b29scy9tdXR1YWwtZnVuZC1jYXRlZ29yeS1yaXNrLW1lYXN1cmVzLmFzcHgWQ2F0ZWdvcnkgUmlzayBNZWFzdXJlcwVfc2VsZhZDYXRlZ29yeSBSaXNrIE1lYXN1cmVzZAIFD2QWAmYPFQUAJi90b29scy90b3AtcGVyZm9ybWluZy1tdXR1YWwtZnVuZC5hc3B4FFRvcCBQZXJmb3JtaW5nIEZ1bmRzBV9zZWxmFFRvcCBQZXJmb3JtaW5nIEZ1bmRzZAIGD2QWAmYPFQUALi90b29scy9tdXR1YWwtZnVuZC1wZXJmb3JtYW5jZS1jb21wYXJpc29uLmFzcHgWUGVyZm9ybWFuY2UgQ29tcGFyaXNvbgVfc2VsZhZQZXJmb3JtYW5jZSBDb21wYXJpc29uZAICD2QWBGYPFQIJUG9ydGZvbGlvCVBvcnRmb2xpb2QCAQ8WAh8CAgYWDAIBD2QWAmYPFQUAKi90b29scy9tdXR1YWwtZnVuZC1kZXRhaWxlZC1wb3J0Zm9saW8uYXNweBJEZXRhaWxlZCBQb3J0Zm9saW8FX3NlbGYSRGV0YWlsZWQgUG9ydGZvbGlvZAICD2QWAmYPFQUAIi90b29scy9pbmRpYW4tc2VjdG9yLWV4cG9zdXJlLmFzcHgWSW5kaWFuIFNlY3RvciBFeHBvc3VyZQVfc2VsZhZJbmRpYW4gU2VjdG9yIEV4cG9zdXJlZAIDD2QWAmYPFQUAIS90b29scy9pbmRpYW4tY3JlZGl0LXF1YWxpdHkuYXNweBVJbmRpYW4gQ3JlZGl0IFF1YWxpdHkFX3NlbGYVSW5kaWFuIENyZWRpdCBRdWFsaXR5ZAIED2QWAmYPFQUALi90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHgMU3RvY2sgU2VhcmNoBV9zZWxmDFN0b2NrIFNlYXJjaGQCBQ9kFgJmDxUFCHNlbGVjdGVkLi90b29scy9tb3N0LXBvcHVsYXItc3RvY2tzLWluLW11dHVhbC1mdW5kLmFzcHgTTW9zdCBQb3B1bGFyIFN0b2NrcwVfc2VsZhNNb3N0IFBvcHVsYXIgU3RvY2tzZAIGD2QWAmYPFQUALy90b29scy9zZWN0b3Itc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4DVNlY3RvciBTZWFyY2gFX3NlbGYNU2VjdG9yIFNlYXJjaGQCAw9kFgRmDxUCCFJlc2VhcmNoCFJlc2VhcmNoZAIBDxYCHwICAhYEAgEPZBYCZg8VBQAWL2ZlYXR1cmVkLXJlcG9ydHMuYXNweA9NZWRhbGlzdCBSYXRpbmcGX2JsYW5rD01lZGFsaXN0IFJhdGluZ2QCAg9kFgJmDxUFACQvdG9vbHMvbXV0dWFsLWZ1bmQtc3Rhci1yYXRpbmdzLmFzcHgMU3RhciBSYXRpbmdzBV9zZWxmDFN0YXIgUmF0aW5nc2QCBA9kFgRmDxUCC0NhbGN1bGF0b3JzC0NhbGN1bGF0b3JzZAIBDxYCHwICAhYEAgEPZBYCZg8VBQAqL3Rvb2xzL211dHVhbC1mdW5kLXJldHVybnMtY2FsY3VsYXRvci5hc3B4ElJldHVybnMgQ2FsY3VsYXRvcgVfc2VsZhJSZXR1cm5zIENhbGN1bGF0b3JkAgIPZBYCZg8VBQAmL3Rvb2xzL211dHVhbC1mdW5kLXNpcC1jYWxjdWxhdG9yLmFzcHgOU0lQIENhbGN1bGF0b3IFX3NlbGYOU0lQIENhbGN1bGF0b3JkAgUPZBYEZg8VAgZMb29rdXAGTG9va3VwZAIBDxYCHwICBhYMAgEPZBYCZg8VBQAiL3Rvb2xzL211dHVhbC1mdW5kLWxhdGVzdC1uYXYuYXNweApMYXRlc3QgTkFWBV9zZWxmCkxhdGVzdCBOQVZkAgIPZBYCZg8VBQAWL2Z1bmRzL2ZhY3RzaGVldHMuYXNweA5GdW5kIEZhY3RzaGVldAZfYmxhbmsORnVuZCBGYWN0c2hlZXRkAgMPZBYCZg8VBQAjL3Rvb2xzL211dHVhbC1mdW5kLWluZm9ybWF0aW9uLmFzcHgQRnVuZCBJbmZvcm1hdGlvbgVfc2VsZhBGdW5kIEluZm9ybWF0aW9uZAIED2QWAmYPFQUANi90b29scy9tdXR1YWwtZnVuZC1hbWZpLWF2ZXJhZ2UtYXVtLWJ5LWZ1bmQtaG91c2UuYXNweA5BdmcgQVVNIGJ5IEFNQwVfc2VsZg5BdmcgQVVNIGJ5IEFNQ2QCBQ9kFgJmDxUFADUvdG9vbHMvbXV0dWFsLWZ1bmQtYW1maS1hdmVyYWdlLWF1bS1ieS1mdW5kLXdpc2UuYXNweA9BdmcgQVVNIGJ5IEZ1bmQFX3NlbGYPQXZnIEFVTSBieSBGdW5kZAIGD2QWAmYPFQUAJy90b29scy9tdXR1YWwtZnVuZC1uZm8taW5mb3JtYXRpb24uYXNweANORk8FX3NlbGYDTkZPZAIGD2QWBGYPFQIRUG9ydGZvbGlvIE1hbmFnZXIRUG9ydGZvbGlvIE1hbmFnZXJkAgEPFgIfAgIBFgICAQ9kFgJmDxUFABAvcG0vZGVmYXVsdC5hc3B4EVBvcnRmb2xpbyBNYW5hZ2VyBl9ibGFuaxFQb3J0Zm9saW8gTWFuYWdlcmQCBw9kFgRmDxUCCEFkdmFuY2VkCEFkdmFuY2VkZAIBDxYCHwICBBYIAgEPZBYCZg8VBQAaL3Rvb2xzL0VDRnVuZHNjcmVlbmVyLmFzcHgUTXV0dWFsIEZ1bmQgU2NyZWVuZXIGX2JsYW5rFE11dHVhbCBGdW5kIFNjcmVlbmVyZAICD2QWAmYPFQUAGS90b29scy9ldGYtcXVpY2tyYW5rLmFzcHgNRVRGIFF1aWNrcmFuawZfYmxhbmsNRVRGIFF1aWNrcmFua2QCAw9kFgJmDxUFAB8vdG9vbHMvZWNpbnZlc3RtZW50Y29tcGFyZS5hc3B4DEZ1bmQgQ29tcGFyZQZfYmxhbmsMRnVuZCBDb21wYXJlZAIED2QWAmYPFQUAGy90b29scy9lY3BvcnRmb2xpb3hyYXkuYXNweA1JbnN0YW50IFgtUmF5Bl9ibGFuaw1JbnN0YW50IFgtUmF5ZAIDD2QWBAIDDxYCHgVzdHlsZQUWZmxvYXQ6bGVmdDt3aWR0aDoxMDAlOxYCAgEPZBYCZg9kFgICAQ9kFgJmD2QWBgIRDxQrAAIPFgQeC18hRGF0YUJvdW5kZx8CAmRkZBYCZg9kFsgBAgEPZBYCZg8VDAIxLkMvc3RvY2tzLzBwMDAwMGJnOHIvYnNlLWljaWNpLWJhbmstbHRkLW9yZGluYXJ5LXNoYXJlcy9vdmVydmlldy5hc3B4HklDSUNJIEJhbmsgTHRkIE9yZGluYXJ5IFNoYXJlcx5JQ0lDSSBCYW5rIEx0ZCBPcmRpbmFyeSBTaGFyZXMKMTY5NTkxMjQ4MDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJHOFIDNTU1AzU1NQY1LjY1NDEMMTU1MjM2MC4zNDgzCjE2Nzg4OTU2NDkIMTcwMTY4MzFkAgIPZBYCZg8VDAIyLjIvc3RvY2tzLzBwMDAwMGFyczcvYnNlLWhkZmMtYmFuay1sdGQvb3ZlcnZpZXcuYXNweA1IREZDIEJhbmsgTHRkDUhERkMgQmFuayBMdGQKMTMxMDg3OTE0NzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEFSUzcDNTQ1AzU0NQY3LjA0OTcMMTkzNTU0Mi42MDE3CjEyOTg1MTU1MjgIMTIzNjM2MTlkAgMPZBYCZg8VDAIzLjAvc3RvY2tzLzBwMDAwMGNmZzkvYnNlLWluZm9zeXMtbHRkL292ZXJ2aWV3LmFzcHgLSW5mb3N5cyBMdGQLSW5mb3N5cyBMdGQJNjgxMjgwMTkzPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ0ZHOQM0NjkDNDY5BjMuMzk1Ngs5MzIyODEuMjcyMQk2ODI5ODU2NzEILTE3MDU0NzhkAgQPZBYCZg8VDAI0Lk8vc3RvY2tzLzBwMDAwMGJoeTYvYnNlLXJlbGlhbmNlLWluZHVzdHJpZXMtbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4KlJlbGlhbmNlIEluZHVzdHJpZXMgTHRkIFNocyBEZW1hdGVyaWFsaXNlZCpSZWxpYW5jZSBJbmR1c3RyaWVzIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQJNDM5MzQ4MzAwPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQkhZNgM0NjcDNDY3BjMuNjYxMwwxMDA1MjI4LjgwNzUJNDMyOTAyNTEzBzY0NDU3ODdkAgUPZBYCZg8VDAI1LjIvc3RvY2tzLzBwMDAwMGNtOGMvYnNlLWF4aXMtYmFuay1sdGQvb3ZlcnZpZXcuYXNweA1BeGlzIEJhbmsgTHRkDUF4aXMgQmFuayBMdGQJNjMzOTc5NzY0PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ004QwM0NDMDNDQzBjIuMjY3Mgs2MjI0NzYuMzMyMQk2MjU1OTY3MzYHODM4MzAyOGQCBg9kFgJmDxUMAjYuSC9zdG9ja3MvMHAwMDAwY2Nrai9ic2Utc3RhdGUtYmFuay1vZi1pbmRpYS1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweCNTdGF0ZSBCYW5rIG9mIEluZGlhIE9yZGluYXJ5IFNoYXJlcyNTdGF0ZSBCYW5rIG9mIEluZGlhIE9yZGluYXJ5IFNoYXJlcwoxMDQwMjI2NDc0PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ0NLSgM0NDEDNDQxBjIuMTQyNws1ODgyODIuMjM5OAoxMDQwMzk4MjMyBy0xNzE3NThkAgcPZBYCZg8VDAI3Lkkvc3RvY2tzLzBwMDAwMGF1YmQvYnNlLWxhcnNlbi10b3Vicm8tbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4KkxhcnNlbiAmYW1wOyBUb3Vicm8gTHRkIFNocyBEZW1hdGVyaWFsaXNlZCpMYXJzZW4gJmFtcDsgVG91YnJvIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQJMjI3MjE1MzMxPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQVVCRAM0MzYDNDM2BjIuNDI0MAs2NjU1MTcuNDY0NgkyMjQzNDI0MDAHMjg3MjkzMWQCCA9kFgJmDxUMAjguNi9zdG9ja3MvMHAwMDAwYXo2bS9ic2UtYmhhcnRpLWFpcnRlbC1sdGQvb3ZlcnZpZXcuYXNweBFCaGFydGkgQWlydGVsIEx0ZBFCaGFydGkgQWlydGVsIEx0ZAk2MzcwNTA3ODI8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBWjZNAzQwNgM0MDYGMi4xMjE2CzU4MjUwOS4zODIxCTYzMzM5NTc3MAczNjU1MDEyZAIJD2QWAmYPFQwCOS5ML3N0b2Nrcy8wcDAwMDBiczdhL2JzZS1tYXJ1dGktc3V6dWtpLWluZGlhLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweCdNYXJ1dGkgU3V6dWtpIEluZGlhIEx0ZCBPcmRpbmFyeSBTaGFyZXMnTWFydXRpIFN1enVraSBJbmRpYSBMdGQgT3JkaW5hcnkgU2hhcmVzCDM2ODA3Mjg1PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQlM3QQMzOTcDMzk3BjEuMzkzMgszODI1MTAuODA4NggzNjU3MTkxMwYyMzUzNzJkAgoPZBYCZg8VDAMxMC5XL3N0b2Nrcy8wcDAwMDBhdzN2L2JzZS1zdW4tcGhhcm1hY2V1dGljYWxzLWluZHVzdHJpZXMtbHRkLW9yZGluYXJ5LXNoYXJlcy9vdmVydmlldy5hc3B4MlN1biBQaGFybWFjZXV0aWNhbHMgSW5kdXN0cmllcyBMdGQgT3JkaW5hcnkgU2hhcmVzMlN1biBQaGFybWFjZXV0aWNhbHMgSW5kdXN0cmllcyBMdGQgT3JkaW5hcnkgU2hhcmVzCTMxNDU0MDYwMTwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEFXM1YDMzg4AzM4OAYxLjI0NzELMzQyNDExLjAyODIJMzEzNDUxODk3BzEwODg3MDRkAgsPZBYCZg8VDAMxMS5AL3N0b2Nrcy8wcDAwMDBieXJ4L2JzZS1udHBjLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweBtOVFBDIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQbTlRQQyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCjE5MDk5MTI3OTg8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCWVJYAzM2MwMzNjMGMS42NDAzCzQ1MDM2NC43MTI4CjE4NzIxMDgzNjkIMzc4MDQ0MjlkAgwPZBYCZg8VDAMxMi4/L3N0b2Nrcy8wcDAwMDBicDd4L2JzZS1pdGMtbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4GklUQyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkGklUQyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCjExNjQ3MjQwMzI8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCUDdYAzM1OQMzNTkGMS44MTc1CzQ5ODk5OS4zOTI2CjExNjM4MDYwMDQGOTE4MDI4ZAIND2QWAmYPFQwDMTMuVS9zdG9ja3MvMHAwMDAwYXh0OS9ic2UtdGF0YS1jb25zdWx0YW5jeS1zZXJ2aWNlcy1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgwVGF0YSBDb25zdWx0YW5jeSBTZXJ2aWNlcyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkMFRhdGEgQ29uc3VsdGFuY3kgU2VydmljZXMgTHRkIFNocyBEZW1hdGVyaWFsaXNlZAkxMjgwMjQxMzk8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBWFQ5AzM1NwMzNTcGMS41NzA4CzQzMTI3MC4zMDAxCTEyNjQwOTQyOAcxNjE0NzExZAIOD2QWAmYPFQwDMTQuOS9zdG9ja3MvMHAwMDAwYnh5cC9ic2UtdWx0cmF0ZWNoLWNlbWVudC1sdGQvb3ZlcnZpZXcuYXNweBRVbHRyYVRlY2ggQ2VtZW50IEx0ZBRVbHRyYVRlY2ggQ2VtZW50IEx0ZAgyNjA1ODcwNTwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJYWVADMzQ3AzM0NwYwLjc5OTQLMjE5NDg4LjQ2MDEIMjU4MzQ1OTEGMjI0MTE0ZAIPD2QWAmYPFQwDMTUuSy9zdG9ja3MvMHAwMDAwYzlmMi9ic2UtaGluZHVzdGFuLXVuaWxldmVyLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweCZIaW5kdXN0YW4gVW5pbGV2ZXIgTHRkIE9yZGluYXJ5IFNoYXJlcyZIaW5kdXN0YW4gVW5pbGV2ZXIgTHRkIE9yZGluYXJ5IFNoYXJlcwkxMTI1Mzg4NzQ8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDOUYyAzMzNQMzMzUGMS4wMTgyCzI3OTU0Ni41NzAxCTExMTkxNzgwNgY2MjEwNjhkAhAPZBYCZg8VDAMxNi5GL3N0b2Nrcy8wcDAwMDBhajRwL2JzZS10ZWNoLW1haGluZHJhLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweCFUZWNoIE1haGluZHJhIEx0ZCBPcmRpbmFyeSBTaGFyZXMhVGVjaCBNYWhpbmRyYSBMdGQgT3JkaW5hcnkgU2hhcmVzCTEzMTk4NDg2NzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEFKNFADMzIwAzMyMAYwLjU0NDcLMTQ5NTU4LjY1NzUJMTIyODExMjAwBzkxNzM2NjdkAhEPZBYCZg8VDAMxNy5ML3N0b2Nrcy8wcDAwMDBjYmE5L2JzZS1rb3Rhay1tYWhpbmRyYS1iYW5rLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweCdLb3RhayBNYWhpbmRyYSBCYW5rIEx0ZCBPcmRpbmFyeSBTaGFyZXMnS290YWsgTWFoaW5kcmEgQmFuayBMdGQgT3JkaW5hcnkgU2hhcmVzCTIwMjQ2MjkwMDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMENCQTkDMzE2AzMxNgYxLjI4MjYLMzUyMTU2Ljk3NDcJMTkwODQ0NzgyCDExNjE4MTE4ZAISD2QWAmYPFQwDMTguOi9zdG9ja3MvMHAwMDAwYXNycS9ic2UtbWFoaW5kcmEtbWFoaW5kcmEtbHRkL292ZXJ2aWV3LmFzcHgbTWFoaW5kcmEgJmFtcDsgTWFoaW5kcmEgTHRkG01haGluZHJhICZhbXA7IE1haGluZHJhIEx0ZAkxNjY5MTY0ODE8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBU1JRAzMxNgMzMTYGMC44ODY4CzI0MzQ2Ni4yNTQ3CTE2NjcxNjk1OQYxOTk1MjJkAhMPZBYCZg8VDAMxOS42L3N0b2Nrcy8wcDAwMDBiaGcyL2JzZS1pbmR1c2luZC1iYW5rLWx0ZC9vdmVydmlldy5hc3B4EUluZHVzSW5kIEJhbmsgTHRkEUluZHVzSW5kIEJhbmsgTHRkCTExNzY2OTM0NjwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJIRzIDMzExAzMxMQYwLjYxNzcLMTY5NTk1LjE5MzkJMTE3MDQwNTgyBjYyODc2NGQCFA9kFgJmDxUMAzIwLkQvc3RvY2tzLzBwMDAwMGFqMmEvYnNlLXRhdGEtbW90b3JzLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweB9UYXRhIE1vdG9ycyBMdGQgT3JkaW5hcnkgU2hhcmVzH1RhdGEgTW90b3JzIEx0ZCBPcmRpbmFyeSBTaGFyZXMJMzMwODI0OTU5PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQUoyQQMzMDIDMzAyBjAuNzU3NQsyMDc5NjcuODYzOQkzMjQ1MDgwMTAHNjMxNjk0OWQCFQ9kFgJmDxUMAzIxLjYvc3RvY2tzLzBwMDAwMGJlajIvYnNlLWJhamFqLWZpbmFuY2UtbHRkL292ZXJ2aWV3LmFzcHgRQmFqYWogRmluYW5jZSBMdGQRQmFqYWogRmluYW5jZSBMdGQINTQ4MzM1NTQ8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCRUoyAzI5OAMyOTgGMS40OTY0CzQxMDg0Mi4zODQyCDU1MDE4Mjc3By0xODQ3MjNkAhYPZBYCZg8VDAMyMi5ML3N0b2Nrcy8wcDAwMDBia3FtL2JzZS1oY2wtdGVjaG5vbG9naWVzLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweCdIQ0wgVGVjaG5vbG9naWVzIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQnSENMIFRlY2hub2xvZ2llcyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCTIyNTIwNjQ4NTwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJLUU0DMjk0AzI5NAYxLjA0NjcLMjg3MzgxLjI0NDQJMjIyNDg3NjI4BzI3MTg4NTdkAhcPZBYCZg8VDAMyMy5BL3N0b2Nrcy8wcDAwMDBjZWRmL2JzZS10aXRhbi1jby1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHgcVGl0YW4gQ28gTHRkIE9yZGluYXJ5IFNoYXJlcxxUaXRhbiBDbyBMdGQgT3JkaW5hcnkgU2hhcmVzCDQ4ODgwNTQ2PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ0VERgMyNzgDMjc4BjAuNTY3OAsxNTU5MDQuNDk3Nwg0NzIyMTc1MgcxNjU4Nzk0ZAIYD2QWAmYPFQwDMjQuOy9zdG9ja3MvMHAwMDAwY21saS9ic2UtYmhhcmF0LWVsZWN0cm9uaWNzLWx0ZC9vdmVydmlldy5hc3B4FkJoYXJhdCBFbGVjdHJvbmljcyBMdGQWQmhhcmF0IEVsZWN0cm9uaWNzIEx0ZAoxMzc5NTQ5OTQ2PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ01MSQMyNjcDMjY3BjAuNjY5NQsxODM4MjcuMzAyOQoxMzYyODU2NDQ0CDE2NjkzNTAyZAIZD2QWAmYPFQwDMjUuRi9zdG9ja3MvMHAwMDAwYzk0ci9ic2UtdGF0YS1zdGVlbC1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHghVGF0YSBTdGVlbCBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkIVRhdGEgU3RlZWwgTHRkIFNocyBEZW1hdGVyaWFsaXNlZAoxMTU2NzU4MDk0PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQzk0UgMyNjYDMjY2BjAuNTAwMwsxMzczNjUuMDI0NQoxMTQ2MDgwODUzCDEwNjc3MjQxZAIaD2QWAmYPFQwDMjYuNC9zdG9ja3MvMHAwMDAxOGU3Zy9ic2UtbHRpbWluZHRyZWUtbHRkL292ZXJ2aWV3LmFzcHgPTFRJTWluZHRyZWUgTHRkD0xUSU1pbmR0cmVlIEx0ZAgyMTY0ODg1MjwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMThFN0cDMjY2AzI2NgYwLjM5OTALMTA5NTUxLjg1ODYIMjE0MzU2MTUGMjEzMjM3ZAIbD2QWAmYPFQwDMjcuTy9zdG9ja3MvMHAwMDAwYnhiNi9ic2UtaGluZGFsY28taW5kdXN0cmllcy1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgqSGluZGFsY28gSW5kdXN0cmllcyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkKkhpbmRhbGNvIEluZHVzdHJpZXMgTHRkIFNocyBEZW1hdGVyaWFsaXNlZAkyNzU4MDY2MDY8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCWEI2AzI1NwMyNTcGMC40NjE2CzEyNjczMy4xNTQ4CTI1NjQ5MDIxNwgxOTMxNjM4OWQCHA9kFgJmDxUMAzI4Lkcvc3RvY2tzLzBwMDAwMWJwdnMvYnNlLXNiaS1saWZlLWluc3VyYW5jZS1jb21wYW55LWxpbWl0ZWQvb3ZlcnZpZXcuYXNweCJTQkkgTGlmZSBJbnN1cmFuY2UgQ29tcGFueSBMaW1pdGVkIlNCSSBMaWZlIEluc3VyYW5jZSBDb21wYW55IExpbWl0ZWQJMTEwOTE0MjMxPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAxQlBWUwMyNDMDMjQzBjAuNTUyNgsxNTE3MTQuMDQ5MQkxMDg1MTQ0OTAHMjM5OTc0MWQCHQ9kFgJmDxUMAzI5LkEvc3RvY2tzLzBwMDAwMGJpMnIvYnNlLWNpcGxhLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweBxDaXBsYSBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkHENpcGxhIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQJMTM0MTk5NTYyPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQkkyUgMyNDMDMjQzBjAuNTg2NQsxNjEwMzkuNDI1NgkxMzAwMDEyNjYHNDE5ODI5NmQCHg9kFgJmDxUMAzMwLmAvc3RvY2tzLzBwMDAwMGJkdWQvYnNlLWNob2xhbWFuZGFsYW0taW52ZXN0bWVudC1hbmQtZmluYW5jZS1jby1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHg7Q2hvbGFtYW5kYWxhbSBJbnZlc3RtZW50IGFuZCBGaW5hbmNlIENvIEx0ZCBPcmRpbmFyeSBTaGFyZXM7Q2hvbGFtYW5kYWxhbSBJbnZlc3RtZW50IGFuZCBGaW5hbmNlIENvIEx0ZCBPcmRpbmFyeSBTaGFyZXMJMTM1OTE5OTAyPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQkRVRAMyMzkDMjM5BjAuNTYzMAsxNTQ1ODEuNzA0NwkxMzYyNDcwOTMHLTMyNzE5MWQCHw9kFgJmDxUMAzMxLkgvc3RvY2tzLzBwMDAwMGFvbTIvYnNlLW5lc3RsZS1pbmRpYS1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgjTmVzdGxlIEluZGlhIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQjTmVzdGxlIEluZGlhIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQHNDcyOTgxMjwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEFPTTIDMjM3AzIzNwYwLjQxNzULMTE0NjI5LjIwMDYHNDczNjM5MAUtNjU3OGQCIA9kFgJmDxUMAzMyLjMvc3RvY2tzLzBwMDAwMGhqOXMvYnNlLWJhamFqLWF1dG8tbHRkL292ZXJ2aWV3LmFzcHgOQmFqYWogQXV0byBMdGQOQmFqYWogQXV0byBMdGQIMTQ4NzMxMTA8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBISjlTAzIzNgMyMzYGMC4yODc5Cjc5MDM2LjQ1OTcIMTMyMjcyMzYHMTY0NTg3NGQCIQ9kFgJmDxUMAzMzLkMvc3RvY2tzLzBwMDAwMGNsZnMvYnNlLWJhbmstb2YtYmFyb2RhLW9yZGluYXJ5LXNoYXJlcy9vdmVydmlldy5hc3B4HkJhbmsgb2YgQmFyb2RhIE9yZGluYXJ5IFNoYXJlcx5CYW5rIG9mIEJhcm9kYSBPcmRpbmFyeSBTaGFyZXMJNDkzNzg0MzUyPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ0xGUwMyMjEDMjIxBjAuMzUyOQo5Njg3OS43NzAzCTQ3OTcyMzQyOQgxNDA2MDkyM2QCIg9kFgJmDxUMAzM0Lkkvc3RvY2tzLzBwMDAwMGJtd3IvYnNlLXRoZS1mZWRlcmFsLWJhbmstbHRkLW9yZGluYXJ5LXNoYXJlcy9vdmVydmlldy5hc3B4JFRoZSBGZWRlcmFsIEJhbmsgTHRkIE9yZGluYXJ5IFNoYXJlcyRUaGUgRmVkZXJhbCBCYW5rIEx0ZCBPcmRpbmFyeSBTaGFyZXMJODUwMjg1NDc5PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQk1XUgMyMTkDMjE5BjAuNDM1NgsxMTk1OTIuNTk2Nwk4NTQ2NDg4MzgILTQzNjMzNTlkAiMPZBYCZg8VDAMzNS5DL3N0b2Nrcy8wcDAwMDBjaTJwL2JzZS1jb2ZvcmdlLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweB5Db2ZvcmdlIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQeQ29mb3JnZSBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCDI2NDYwNjM0PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ0kyUAMyMTcDMjE3BjAuNDgwNAsxMzE4ODYuNDE1MwgyNTkxNTA5MwY1NDU1NDFkAiQPZBYCZg8VDAMzNi42L3N0b2Nrcy8wcDAwMDBjZDY3L2JzZS1oZXJvLW1vdG9jb3JwLWx0ZC9vdmVydmlldy5hc3B4EUhlcm8gTW90b0NvcnAgTHRkEUhlcm8gTW90b0NvcnAgTHRkCDI2OTMyMTE1PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ0Q2NwMyMTcDMjE3BjAuMzAyOQo4MzE3NS44MDc0CDI1MjQ0NzMxBzE2ODczODRkAiUPZBYCZg8VDAMzNy4zL3N0b2Nrcy8wcDAwMDBycTk2L2JzZS1jb2FsLWluZGlhLWx0ZC9vdmVydmlldy5hc3B4DkNvYWwgSW5kaWEgTHRkDkNvYWwgSW5kaWEgTHRkCTY2MjYxNTE0MDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMFJROTYDMjE0AzIxNAYwLjc1ODQLMjA4MjMwLjAxMDMJNjcxNjM5MzUwCC05MDI0MjEwZAImD2QWAmYPFQwDMzguLy9zdG9ja3MvMHAwMDAxbXpyaC9ic2Utem9tYXRvLWx0ZC9vdmVydmlldy5hc3B4ClpvbWF0byBMdGQKWm9tYXRvIEx0ZAk5NDA0MzQ3Njc8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDFNWlJIAzIxMgMyMTIGMC4zNjAwCjk4ODM5LjcwNzgJOTA5ODkyOTQ4CDMwNTQxODE5ZAInD2QWAmYPFQwDMzkuSC9zdG9ja3MvMHAwMDAwY2x6My9ic2UtdHZzLW1vdG9yLWNvLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweCNUVlMgTW90b3IgQ28gTHRkIFNocyBEZW1hdGVyaWFsaXNlZCNUVlMgTW90b3IgQ28gTHRkIFNocyBEZW1hdGVyaWFsaXNlZAg4OTQ3ODEyMzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMENMWjMDMjEyAzIxMgYwLjUxODQLMTQyMzQxLjc5ODEIODkyODA3NzMGMTk3MzUwZAIoD2QWAmYPFQwDNDAuPC9zdG9ja3MvMHAwMDAxNnpxeS9ic2UtaW50ZXJnbG9iZS1hdmlhdGlvbi1sdGQvb3ZlcnZpZXcuYXNweBdJbnRlckdsb2JlIEF2aWF0aW9uIEx0ZBdJbnRlckdsb2JlIEF2aWF0aW9uIEx0ZAg0NTgzOTExNzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMTZaUVkDMjEwAzIxMAYwLjQwOTcLMTEyNDgyLjMxMjMINDIxNDE1ODIHMzY5NzUzNWQCKQ9kFgJmDxUMAzQxLkovc3RvY2tzLzBwMDAwMGFoZWMvYnNlLXVuaXRlZC1zcGlyaXRzLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweCVVbml0ZWQgU3Bpcml0cyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkJVVuaXRlZCBTcGlyaXRzIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQINzQxMDMwMDg8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBSEVDAzIwNQMyMDUGMC4yNzg2Cjc2NDg5LjEzMzUINzI1NDM4NzQHMTU1OTEzNGQCKg9kFgJmDxUMAzQyLlEvc3RvY2tzLzBwMDAwMGdnbG0vYnNlLXBvd2VyLWdyaWQtY29ycC1vZi1pbmRpYS1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHgsUG93ZXIgR3JpZCBDb3JwIE9mIEluZGlhIEx0ZCBPcmRpbmFyeSBTaGFyZXMsUG93ZXIgR3JpZCBDb3JwIE9mIEluZGlhIEx0ZCBPcmRpbmFyeSBTaGFyZXMJOTI1NTQ0NTk2PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwR0dMTQMyMDUDMjA1BjAuNjgxNQsxODcwOTguODQwNwk4ODY5MDUxNjMIMzg2Mzk0MzNkAisPZBYCZg8VDAM0My4/L3N0b2Nrcy8wcDAwMDFyYjVlL2JzZS1qaW8tZmluYW5jaWFsLXNlcnZpY2VzLWx0ZC9vdmVydmlldy5hc3B4GkppbyBGaW5hbmNpYWwgU2VydmljZXMgTHRkGkppbyBGaW5hbmNpYWwgU2VydmljZXMgTHRkCTI5ODM5MTI4NzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMVJCNUUDMTk2AzE5NgYwLjIzODAKNjUzNDcuNzAwNAkyOTI0NDI4MzMHNTk0ODQ1NGQCLA9kFgJmDxUMAzQ0Lj8vc3RvY2tzLzBwMDAwMGFtdHIvYnNlLWRyLXJlZGR5cy1sYWJvcmF0b3JpZXMtbHRkL292ZXJ2aWV3LmFzcHgfRHIgUmVkZHkmIzM5O3MgTGFib3JhdG9yaWVzIEx0ZB9EciBSZWRkeSYjMzk7cyBMYWJvcmF0b3JpZXMgTHRkCDE0ODU5MzAzPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQU1UUgMxOTUDMTk1BjAuMjkwNQo3OTc1Ny44NzkzCDE0MzE1OTMxBjU0MzM3MmQCLQ9kFgJmDxUMAzQ1LkUvc3RvY2tzLzBwMDAwMGF4aWUvYnNlLWFzaWFuLXBhaW50cy1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHggQXNpYW4gUGFpbnRzIEx0ZCBPcmRpbmFyeSBTaGFyZXMgQXNpYW4gUGFpbnRzIEx0ZCBPcmRpbmFyeSBTaGFyZXMIMzUxMjA5NzE8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBWElFAzE5MQMxOTEGMC4zODMyCzEwNTIxNy42MzA4CDMzNjQ1MTk4BzE0NzU3NzNkAi4PZBYCZg8VDAM0Ni5LL3N0b2Nrcy8wcDAwMDFib290L2JzZS1pY2ljaS1sb21iYXJkLWdlbmVyYWwtaW5zdXJhbmNlLWNvLWx0ZC9vdmVydmlldy5hc3B4JklDSUNJIExvbWJhcmQgR2VuZXJhbCBJbnN1cmFuY2UgQ28gTHRkJklDSUNJIExvbWJhcmQgR2VuZXJhbCBJbnN1cmFuY2UgQ28gTHRkCDc1OTE2MTI3PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAxQk9PVAMxODkDMTg5BjAuMzc5OQsxMDQyOTMuNjE5MQg3NTg4NTQyMwUzMDcwNGQCLw9kFgJmDxUMAzQ3LlQvc3RvY2tzLzBwMDAwMGI3eW4vYnNlLWFwb2xsby1ob3NwaXRhbHMtZW50ZXJwcmlzZS1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHgvQXBvbGxvIEhvc3BpdGFscyBFbnRlcnByaXNlIEx0ZCBPcmRpbmFyeSBTaGFyZXMvQXBvbGxvIEhvc3BpdGFscyBFbnRlcnByaXNlIEx0ZCBPcmRpbmFyeSBTaGFyZXMIMTk3MzI5Nzc8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCN1lOAzE4OAMxODgGMC4zNDY0Cjk1MTEwLjk3MDMIMTg3OTU3NzkGOTM3MTk4ZAIwD2QWAmYPFQwDNDguRi9zdG9ja3MvMHAwMDAwYW9yMy9ic2UtcGktaW5kdXN0cmllcy1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHghUEkgSW5kdXN0cmllcyBMdGQgT3JkaW5hcnkgU2hhcmVzIVBJIEluZHVzdHJpZXMgTHRkIE9yZGluYXJ5IFNoYXJlcwgyNTY2MDYzNjwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEFPUjMDMTg3AzE4NwYwLjMxNzkKODcyNzguMjM0NggyNjA4NTQ3NwctNDI0ODQxZAIxD2QWAmYPFQwDNDkuOy9zdG9ja3MvMHAwMDAwY20zbi9ic2UtZGl2aXMtbGFib3JhdG9yaWVzLWx0ZC9vdmVydmlldy5hc3B4G0RpdmkmIzM5O3MgTGFib3JhdG9yaWVzIEx0ZBtEaXZpJiMzOTtzIExhYm9yYXRvcmllcyBMdGQIMzY0OTM4OTQ8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDTTNOAzE4NgMxODYGMC40NTA0CzEyMzY1NC4wNzY0CDM2MTI2MDMzBjM2Nzg2MWQCMg9kFgJmDxUMAzUwLi4vc3RvY2tzLzBwMDAwMGI1eGovYnNlLXRyZW50LWx0ZC9vdmVydmlldy5hc3B4CVRyZW50IEx0ZAlUcmVudCBMdGQIMzI1Mzk2Njk8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCNVhKAzE4NAMxODQGMC4yNTU0CjcwMTEzLjI5MTUIMzE3NTExODMGNzg4NDg2ZAIzD2QWAmYPFQwDNTEuPS9zdG9ja3MvMHAwMDAwYmJvcy9ic2UtYnJpdGFubmlhLWluZHVzdHJpZXMtbHRkL292ZXJ2aWV3LmFzcHgYQnJpdGFubmlhIEluZHVzdHJpZXMgTHRkGEJyaXRhbm5pYSBJbmR1c3RyaWVzIEx0ZAgxMzUwNjU1ODwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJCT1MDMTgyAzE4MgYwLjIxNzgKNTk3ODYuNzA4NQgxMzYxMDYxMActMTA0MDUyZAI0D2QWAmYPFQwDNTIuOi9zdG9ja3MvMHAwMDAwYjE2by9ic2UtZ3Jhc2ltLWluZHVzdHJpZXMtbHRkL292ZXJ2aWV3LmFzcHgVR3Jhc2ltIEluZHVzdHJpZXMgTHRkFUdyYXNpbSBJbmR1c3RyaWVzIEx0ZAgzNjY0NTU0MTwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEIxNk8DMTc4AzE3OAYwLjI1MTgKNjkxMzkuMTM1OAgzNjMyNTU1MQYzMTk5OTBkAjUPZBYCZg8VDAM1My45L3N0b2Nrcy8wcDAwMDBib2wxL2JzZS1pbmRpYW4taG90ZWxzLWNvLWx0ZC9vdmVydmlldy5hc3B4FEluZGlhbiBIb3RlbHMgQ28gTHRkFEluZGlhbiBIb3RlbHMgQ28gTHRkCTI1MzQ4MzY4MDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJPTDEDMTc4AzE3OAYwLjM1NDAKOTcxODUuNjU2OAkyNTQ0MTQxNzEHLTkzMDQ5MWQCNg9kFgJmDxUMAzU0LlEvc3RvY2tzLzBwMDAwMGJweTkvYnNlLWJoYXJhdC1wZXRyb2xldW0tY29ycC1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgsQmhhcmF0IFBldHJvbGV1bSBDb3JwIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQsQmhhcmF0IFBldHJvbGV1bSBDb3JwIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQJMjIwNDkxNjk1PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQlBZOQMxNzcDMTc3BjAuMjgwNQo3NzAwNi4yNTMyCTIxMTEyMTUzMAc5MzcwMTY1ZAI3D2QWAmYPFQwDNTUuOy9zdG9ja3MvMHAwMDAwYzd3Yy9ic2UtcG93ZXItZmluYW5jZS1jb3JwLWx0ZC9vdmVydmlldy5hc3B4FlBvd2VyIEZpbmFuY2UgQ29ycCBMdGQWUG93ZXIgRmluYW5jZSBDb3JwIEx0ZAk0MDE2MjczNjE8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDN1dDAzE3NQMxNzUGMC4zNjA3Cjk5MDQxLjg3NjAJMzk0NjI4NzA4BzY5OTg2NTNkAjgPZBYCZg8VDAM1Ni5fL3N0b2Nrcy8wcDAwMDBidnA1L2JzZS1zYW12YXJkaGFuYS1tb3RoZXJzb24taW50ZXJuYXRpb25hbC1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHg6U2FtdmFyZGhhbmEgTW90aGVyc29uIEludGVybmF0aW9uYWwgTHRkIFNocyBEZW1hdGVyaWFsaXNlZDpTYW12YXJkaGFuYSBNb3RoZXJzb24gSW50ZXJuYXRpb25hbCBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCTgyMTI3NTk3ODwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJWUDUDMTc1AzE3NQYwLjI3NTAKNzU1MTYuMzMxMgk4MDMwNDU1MzUIMTgyMzA0NDNkAjkPZBYCZg8VDAM1Ny5GL3N0b2Nrcy8wcDAwMDBwdDVnL2JzZS1iYWphai1maW5zZXJ2LWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweCFCYWphaiBGaW5zZXJ2IEx0ZCBPcmRpbmFyeSBTaGFyZXMhQmFqYWogRmluc2VydiBMdGQgT3JkaW5hcnkgU2hhcmVzCDYwNDE5NzU3PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwUFQ1RwMxNzEDMTcxBjAuMzQ1Mwo5NDgxMi4yMjU1CDU5MjA3NTU1BzEyMTIyMDJkAjoPZBYCZg8VDAM1OC5NL3N0b2Nrcy8wcDAwMDBhcTk2L2JzZS1vaWwtbmF0dXJhbC1nYXMtY29ycC1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHguT2lsICZhbXA7IE5hdHVyYWwgR2FzIENvcnAgTHRkIE9yZGluYXJ5IFNoYXJlcy5PaWwgJmFtcDsgTmF0dXJhbCBHYXMgQ29ycCBMdGQgT3JkaW5hcnkgU2hhcmVzCjEwMTQ0NTQ0NDY8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBUTk2AzE2OQMxNjkGMC42ODc4CzE4ODgzOC43NjQyCjEwMzU3Njc0ODkJLTIxMzEzMDQzZAI7D2QWAmYPFQwDNTkuPC9zdG9ja3MvMHAwMDAwYmg1bS9ic2UtZGxmLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweBdETEYgTHRkIE9yZGluYXJ5IFNoYXJlcxdETEYgTHRkIE9yZGluYXJ5IFNoYXJlcwkxMDEwNTY3OTg8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCSDVNAzE2OAMxNjgGMC4yMDc0CjU2OTQ1LjUwOTUIOTc3MjcyOTgHMzMyOTUwMGQCPA9kFgJmDxUMAzYwLjYvc3RvY2tzLzBwMDAwMGJ1MDkvYnNlLWVpY2hlci1tb3RvcnMtbHRkL292ZXJ2aWV3LmFzcHgRRWljaGVyIE1vdG9ycyBMdGQRRWljaGVyIE1vdG9ycyBMdGQIMTU1NjIxMTI8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCVTA5AzE2OAMxNjgGMC4xODY4CjUxMjg2LjQ5MTAIMTU2ODg1ODEHLTEyNjQ2OWQCPQ9kFgJmDxUMAzYxLkIvc3RvY2tzLzBwMDAwMGMyMGIvYnNlLWFiYi1pbmRpYS1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHgdQUJCIEluZGlhIEx0ZCBPcmRpbmFyeSBTaGFyZXMdQUJCIEluZGlhIEx0ZCBPcmRpbmFyeSBTaGFyZXMIMTAyNTIyNTU8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDMjBCAzE2OAMxNjgGMC4xNTM0CjQyMTI5LjU5ODIIMTA0NDczMjgHLTE5NTA3M2QCPg9kFgJmDxUMAzYyLkgvc3RvY2tzLzBwMDAwMGNrY3kvYnNlLWJoYXJhdC1mb3JnZS1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgjQmhhcmF0IEZvcmdlIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQjQmhhcmF0IEZvcmdlIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQIOTM0OTk1NDk8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDS0NZAzE2OAMxNjgGMC4zNDcxCjk1MzA4LjczODIIOTIzMzg3NDkHMTE2MDgwMGQCPw9kFgJmDxUMAzYzLiwvc3RvY2tzLzBwMDAwMGQ2ZjkvYnNlLXJlYy1sdGQvb3ZlcnZpZXcuYXNweAdSRUMgTHRkB1JFQyBMdGQJMjM2NjcxODk1PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwRDZGOQMxNjgDMTY4BjAuMjQ3OQo2ODA2Ni41OTI4CTIyOTgzMjE5NQc2ODM5NzAwZAJAD2QWAmYPFQwDNjQuQS9zdG9ja3MvMHAwMDAwYW51Zi9ic2Utd2lwcm8tbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4HFdpcHJvIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQcV2lwcm8gTHRkIFNocyBEZW1hdGVyaWFsaXNlZAkxNDU2ODcxOTg8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBTlVGAzE2OAMxNjgGMC4yMDI2CjU1NjI3LjUyMTYJMTQ0MTY5MDE5BzE1MTgxNzlkAkEPZBYCZg8VDAM2NS5UL3N0b2Nrcy8wcDAwMDBhZ212L2JzZS1nb2RyZWotY29uc3VtZXItcHJvZHVjdHMtbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4L0dvZHJlaiBDb25zdW1lciBQcm9kdWN0cyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkL0dvZHJlaiBDb25zdW1lciBQcm9kdWN0cyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCDQ3Nzg2Nzg2PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQUdNVgMxNjYDMTY2BjAuMTcyNgo0NzM5Ny4zMzY4CDQ3OTMzMTA0By0xNDYzMThkAkIPZBYCZg8VDAM2Ni5OL3N0b2Nrcy8wcDAwMDFkMmlsL2JzZS1oaW5kdXN0YW4tYWVyb25hdXRpY3MtbHRkLW9yZGluYXJ5LXNoYXJlcy9vdmVydmlldy5hc3B4KUhpbmR1c3RhbiBBZXJvbmF1dGljcyBMdGQgT3JkaW5hcnkgU2hhcmVzKUhpbmR1c3RhbiBBZXJvbmF1dGljcyBMdGQgT3JkaW5hcnkgU2hhcmVzCDQ4MDI5Mjk5PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAxRDJJTAMxNjYDMTY2BjAuMzE4OQo4NzU1OS44MTU4CDQ2OTIwODM3BzExMDg0NjJkAkMPZBYCZg8VDAM2Ny5LL3N0b2Nrcy8wcDAwMDBucXk4L2JzZS1wZXJzaXN0ZW50LXN5c3RlbXMtbHRkLW9yZGluYXJ5LXNoYXJlcy9vdmVydmlldy5hc3B4JlBlcnNpc3RlbnQgU3lzdGVtcyBMdGQgT3JkaW5hcnkgU2hhcmVzJlBlcnNpc3RlbnQgU3lzdGVtcyBMdGQgT3JkaW5hcnkgU2hhcmVzCDE4OTExMDEwPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwTlFZOAMxNjYDMTY2BjAuNDI0MwsxMTY0OTUuNjA2NAgxODM5MjMyMgY1MTg2ODhkAkQPZBYCZg8VDAM2OC5OL3N0b2Nrcy8wcDAwMDBhdG1vL2JzZS1qaW5kYWwtc3RlZWwtcG93ZXItbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4L0ppbmRhbCBTdGVlbCAmYW1wOyBQb3dlciBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkL0ppbmRhbCBTdGVlbCAmYW1wOyBQb3dlciBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCTExOTI2NDUyMjwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEFUTU8DMTY1AzE2NQYwLjI3NTMKNzU1ODkuODcwMAkxMTg0MzUyNDkGODI5MjczZAJFD2QWAmYPFQwDNjkuOi9zdG9ja3MvMHAwMDAxOXp0Ni9ic2UtYXZlbnVlLXN1cGVybWFydHMtbHRkL292ZXJ2aWV3LmFzcHgVQXZlbnVlIFN1cGVybWFydHMgTHRkFUF2ZW51ZSBTdXBlcm1hcnRzIEx0ZAg0Njg3MjQ4MTwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMTlaVDYDMTY0AzE2NAYwLjYyMDMLMTcwMzA2LjQ2MzkINDc0NTU4NTUHLTU4MzM3NGQCRg9kFgJmDxUMAzcwLj8vc3RvY2tzLzBwMDAwMGFveXQvYnNlLXRhdGEtY29uc3VtZXItcHJvZHVjdHMtbHRkL292ZXJ2aWV3LmFzcHgaVGF0YSBDb25zdW1lciBQcm9kdWN0cyBMdGQaVGF0YSBDb25zdW1lciBQcm9kdWN0cyBMdGQINTY4Nzk3NDY8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBT1lUAzE2NAMxNjQGMC4xODY2CjUxMjIwLjIxNjQINTYyODIxODUGNTk3NTYxZAJHD2QWAmYPFQwDNzEuSC9zdG9ja3MvMHAwMDAxYzhnYi9ic2UtaGRmYy1saWZlLWluc3VyYW5jZS1jb21wYW55LWxpbWl0ZWQvb3ZlcnZpZXcuYXNweCNIREZDIExpZmUgSW5zdXJhbmNlIENvbXBhbnkgTGltaXRlZCNIREZDIExpZmUgSW5zdXJhbmNlIENvbXBhbnkgTGltaXRlZAkxMDQxMjUyMDI8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDFDOEdCAzE2MwMxNjMGMC4yMzQ1CjY0Mzg1LjgzNDUIOTg5NTIzNjMHNTE3MjgzOWQCSA9kFgJmDxUMAzcyLk4vc3RvY2tzLzBwMDAwMTgwdTIvYnNlLWNyb21wdG9uLWdyZWF2ZXMtY29uc3VtZXItZWxlY3RyaWNhbHMtbHRkL292ZXJ2aWV3LmFzcHgpQ3JvbXB0b24gR3JlYXZlcyBDb25zdW1lciBFbGVjdHJpY2FscyBMdGQpQ3JvbXB0b24gR3JlYXZlcyBDb25zdW1lciBFbGVjdHJpY2FscyBMdGQJMjI2MDIzNDg2PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAxODBVMgMxNjMDMTYzBjAuMjMyMgo2MzczOC42MjQ3CTIyMzU0Nzg3MwcyNDc1NjEzZAJJD2QWAmYPFQwDNzMuQy9zdG9ja3MvMHAwMDAwYjFrdi9ic2UtbXBoYXNpcy1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgeTXBoYXNpcyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkHk1waGFzaXMgTHRkIFNocyBEZW1hdGVyaWFsaXNlZAgyNDQ4ODk3OTwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEIxS1YDMTYwAzE2MAYwLjE4OTQKNTE5OTkuOTQ2OAgyMzg2MDg3NAY2MjgxMDVkAkoPZBYCZg8VDAM3NC41L3N0b2Nrcy8wcDAwMDBicXd4L2JzZS1nYWlsLShpbmRpYSktbHRkL292ZXJ2aWV3LmFzcHgQR0FJTCAoSW5kaWEpIEx0ZBBHQUlMIChJbmRpYSkgTHRkCTU3MzMyNTgwNDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJRV1gDMTU4AzE1OAYwLjI0OTUKNjg1MTQuNTE3MQk1NTY4OTQwMDUIMTY0MzE3OTlkAksPZBYCZg8VDAM3NS43L3N0b2Nrcy8wcDAwMDBiMjY5L2JzZS1hbWJ1amEtY2VtZW50cy1sdGQvb3ZlcnZpZXcuYXNweBJBbWJ1amEgQ2VtZW50cyBMdGQSQW1idWphIENlbWVudHMgTHRkCTEzMjIwMTg4MzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEIyNjkDMTU3AzE1NwYwLjIwNDQKNTYxMTMuMDk0MQkxMjg0NTQ3NzEHMzc0NzExMmQCTA9kFgJmDxUMAzc2Lkkvc3RvY2tzLzBwMDAwMGNqNWEvYnNlLWN1bW1pbnMtaW5kaWEtbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4JEN1bW1pbnMgSW5kaWEgTHRkIFNocyBEZW1hdGVyaWFsaXNlZCRDdW1taW5zIEluZGlhIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQINDkxMTYwMzQ8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDSjVBAzE1NgMxNTYGMC4yOTk5CjgyMzQ1LjQ5MjAINDc4ODM3NzQHMTIzMjI2MGQCTQ9kFgJmDxUMAzc3Lksvc3RvY2tzLzBwMDAwMGIzeGgvYnNlLXNocmlyYW0tZmluYW5jZS1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgmU2hyaXJhbSBGaW5hbmNlIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQmU2hyaXJhbSBGaW5hbmNlIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQINDA5NzA5OTA8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBCM1hIAzE1NAMxNTQGMC4yODA1Cjc3MDE5LjIzOTUIMzgyNDE1NTkHMjcyOTQzMWQCTg9kFgJmDxUMAzc4Ljsvc3RvY2tzLzBwMDAwMGNlenovYnNlLXp5ZHVzLWxpZmVzY2llbmNlcy1sdGQvb3ZlcnZpZXcuYXNweBZaeWR1cyBMaWZlc2NpZW5jZXMgTHRkFlp5ZHVzIExpZmVzY2llbmNlcyBMdGQINjY4ODMyMDg8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDRVpaAzE1NAMxNTQGMC4xMzk3CjM4MzYwLjg2ODIINjI2NzQyMDgHNDIwOTAwMGQCTw9kFgJmDxUMAzc5LlYvc3RvY2tzLzBwMDAwMGJ2c2gvYnNlLXplZS1lbnRlcnRhaW5tZW50LWVudGVycHJpc2VzLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweDFaZWUgRW50ZXJ0YWlubWVudCBFbnRlcnByaXNlcyBMdGQgT3JkaW5hcnkgU2hhcmVzMVplZSBFbnRlcnRhaW5tZW50IEVudGVycHJpc2VzIEx0ZCBPcmRpbmFyeSBTaGFyZXMJMjk5MTE1NzA2PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQlZTSAMxNTIDMTUyBjAuMjgyNAo3NzUzMC43NzgyCTI4OTYyMjc0MAc5NDkyOTY2ZAJQD2QWAmYPFQwDODAuQy9zdG9ja3MvMHAwMDAwY2xsbS9ic2Utc2llbWVucy1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHgeU2llbWVucyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkHlNpZW1lbnMgTHRkIFNocyBEZW1hdGVyaWFsaXNlZAgxMTU2MjczMDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMENMTE0DMTUyAzE1MgYwLjE0MDMKMzg1MTQuODc2NQgxMDg2NTcwNAY2OTcwMjZkAlEPZBYCZg8VDAM4MS5TL3N0b2Nrcy8wcDAwMDBheG4xL2JzZS10b3JyZW50LXBoYXJtYWNldXRpY2Fscy1sdGQtc2hzLWRlbWF0ZXJpYWxpc2VkL292ZXJ2aWV3LmFzcHguVG9ycmVudCBQaGFybWFjZXV0aWNhbHMgTHRkIFNocyBEZW1hdGVyaWFsaXNlZC5Ub3JyZW50IFBoYXJtYWNldXRpY2FscyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCDE1OTcwNjQ0PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQVhOMQMxNTEDMTUxBjAuMTExOQozMDczMS42NTYyCDE3NDkwNjA3CC0xNTE5OTYzZAJSD2QWAmYPFQwDODIuNi9zdG9ja3MvMHAwMDAxaGEzdi9ic2UtcG9seWNhYi1pbmRpYS1sdGQvb3ZlcnZpZXcuYXNweBFQb2x5Y2FiIEluZGlhIEx0ZBFQb2x5Y2FiIEluZGlhIEx0ZAgxMDIzNjQ1MTwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMUhBM1YDMTQ3AzE0NwYwLjE4MzUKNTAzODQuODI2Nwc5MzI1Mjg4BjkxMTE2M2QCUw9kFgJmDxUMAzgzLkcvc3RvY2tzLzBwMDAwMGFsNzcvYnNlLWRhYnVyLWluZGlhLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweCJEYWJ1ciBJbmRpYSBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkIkRhYnVyIEluZGlhIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQIODU0MzExNjg8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBTDc3AzE0NQMxNDUGMC4xNjQ2CjQ1MTg0LjU0NzMINzI3NjY2MDgIMTI2NjQ1NjBkAlQPZBYCZg8VDAM4NC5DL3N0b2Nrcy8wcDAwMDBibGJvL2JzZS1jYW5hcmEtYmFuay1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweB5DYW5hcmEgQmFuayBTaHMgRGVtYXRlcmlhbGlzZWQeQ2FuYXJhIEJhbmsgU2hzIERlbWF0ZXJpYWxpc2VkCDkzMzU5NTkxPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQkxCTwMxNDUDMTQ1BjAuMTMwNwozNTg4Mi43NDYyCDg5ODQ2ODgyBzM1MTI3MDlkAlUPZBYCZg8VDAM4NS5FL3N0b2Nrcy8wcDAwMDBieW9tL2JzZS1qc3ctc3RlZWwtbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4IEpTVyBTdGVlbCBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkIEpTVyBTdGVlbCBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCDYyMDQyODIyPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQllPTQMxNDUDMTQ1BjAuMTY2NAo0NTY3OS42OTQ0CDYxMjQyNTc4BjgwMDI0NGQCVg9kFgJmDxUMAzg2Ljkvc3RvY2tzLzBwMDAwMGNqdmkvYnNlLWF1cm9iaW5kby1waGFybWEtbHRkL292ZXJ2aWV3LmFzcHgUQXVyb2JpbmRvIFBoYXJtYSBMdGQUQXVyb2JpbmRvIFBoYXJtYSBMdGQINzUxNzYwNTY8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBDSlZJAzE0NAMxNDQGMC4yMzI2CjYzODYyLjA2NTEINjcxNDA1OTEHODAzNTQ2NWQCVw9kFgJmDxUMAzg3Lkkvc3RvY2tzLzBwMDAwMGF4OTgvYnNlLWFzaG9rLWxleWxhbmQtbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4JEFzaG9rIExleWxhbmQgTHRkIFNocyBEZW1hdGVyaWFsaXNlZCRBc2hvayBMZXlsYW5kIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQJMjkwMTAyMDMxPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQVg5OAMxNDQDMTQ0BjAuMTc3Mgo0ODY1MC4xMDU3CTI4NTA5ODM0MQc1MDAzNjkwZAJYD2QWAmYPFQwDODguVC9zdG9ja3MvMHAwMDAxOHM0ei9ic2UtaWNpY2ktcHJ1ZGVudGlhbC1saWZlLWluc3VyYW5jZS1jb21wYW55LWxpbWl0ZWQvb3ZlcnZpZXcuYXNweC9JQ0lDSSBQcnVkZW50aWFsIExpZmUgSW5zdXJhbmNlIENvbXBhbnkgTGltaXRlZC9JQ0lDSSBQcnVkZW50aWFsIExpZmUgSW5zdXJhbmNlIENvbXBhbnkgTGltaXRlZAg3MDIyODQzODwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMThTNFoDMTQyAzE0MgYwLjEzNDQKMzY4ODcuNTEwNAg2NDgzMDQwNAc1Mzk4MDM0ZAJZD2QWAmYPFQwDODkuQy9zdG9ja3MvMHAwMDAxYm1sdC9ic2UtZGl4b24tdGVjaG5vbG9naWVzLShpbmRpYSktbHRkL292ZXJ2aWV3LmFzcHgeRGl4b24gVGVjaG5vbG9naWVzIChJbmRpYSkgTHRkHkRpeG9uIFRlY2hub2xvZ2llcyAoSW5kaWEpIEx0ZAgxMDI4MDgyMzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMUJNTFQDMTQyAzE0MgYwLjE5MTAKNTI0NDguNjQ2OQc5MTg5OTY5BzEwOTA4NTRkAloPZBYCZg8VDAM5MC4+L3N0b2Nrcy8wcDAwMDBhdTZvL2JzZS1sdXBpbi1sdGQtb3JkaW5hcnktc2hhcmVzL292ZXJ2aWV3LmFzcHgZTHVwaW4gTHRkIE9yZGluYXJ5IFNoYXJlcxlMdXBpbiBMdGQgT3JkaW5hcnkgU2hhcmVzCDc4MTc1MzI5PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQVU2TwMxNDEDMTQxBjAuMzIxMgo4ODE5My41MDA1CDc2NDI4MTAyBzE3NDcyMjdkAlsPZBYCZg8VDAM5MS5XL3N0b2Nrcy8wcDAwMDFqZm5qL2JzZS1zYmktY2FyZHMtYW5kLXBheW1lbnQtc2VydmljZXMtbHRkLW9yZGluYXJ5LXNoYXJlcy9vdmVydmlldy5hc3B4MlNCSSBDYXJkcyBhbmQgUGF5bWVudCBTZXJ2aWNlcyBMdGQgT3JkaW5hcnkgU2hhcmVzMlNCSSBDYXJkcyBhbmQgUGF5bWVudCBTZXJ2aWNlcyBMdGQgT3JkaW5hcnkgU2hhcmVzCTExMjUxMzQ1MDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMUpGTkoDMTQxAzE0MQYwLjMwNTgKODM5NTEuOTIwOAkxMDg2NTMzOTgHMzg2MDA1MmQCXA9kFgJmDxUMAzkyLjUvc3RvY2tzLzBwMDAwMGJnc2gvYnNlLWFiYm90dC1pbmRpYS1sdGQvb3ZlcnZpZXcuYXNweBBBYmJvdHQgSW5kaWEgTHRkEEFiYm90dCBJbmRpYSBMdGQHMTU1NjkwODwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJHU0gDMTM4AzEzOAYwLjEyNzEKMzQ4OTYuMTAzNQcxNTUzMDExBDM4OTdkAl0PZBYCZg8VDAM5My47L3N0b2Nrcy8wcDAwMDE3N2hjL2JzZS1hbGtlbS1sYWJvcmF0b3JpZXMtbHRkL292ZXJ2aWV3LmFzcHgWQWxrZW0gTGFib3JhdG9yaWVzIEx0ZBZBbGtlbSBMYWJvcmF0b3JpZXMgTHRkCDE2MDU3NTA4PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAxNzdIQwMxMzgDMTM4BjAuMjE3Nwo1OTc2My42NjgwCDE1NDUzODI0BjYwMzY4NGQCXg9kFgJmDxUMAzk0LjYvc3RvY2tzLzBwMDAwMGFoaXEvYnNlLWhhdmVsbHMtaW5kaWEtbHRkL292ZXJ2aWV3LmFzcHgRSGF2ZWxscyBJbmRpYSBMdGQRSGF2ZWxscyBJbmRpYSBMdGQIMjM0MDYwNTE8L3Rvb2xzL3N0b2NrLXNlYXJjaC1tdXR1YWwtZnVuZC1wb3J0Zm9saW8uYXNweD9pZD0wUDAwMDBBSElRAzEzNwMxMzcGMC4xMDYyCjI5MTY3LjQ1NzEIMjE5OTE1MzEHMTQxNDUyMGQCXw9kFgJmDxUMAzk1Lj8vc3RvY2tzLzBwMDAwMGNkcjkvYnNlLW1heC1maW5hbmNpYWwtc2VydmljZXMtbHRkL292ZXJ2aWV3LmFzcHgaTWF4IEZpbmFuY2lhbCBTZXJ2aWNlcyBMdGQaTWF4IEZpbmFuY2lhbCBTZXJ2aWNlcyBMdGQJMTA1NzcwMDU4PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQ0RSOQMxMzYDMTM2BjAuMzUyMQo5NjY4NC40MDg5CTEwNDM3NDU0OAcxMzk1NTEwZAJgD2QWAmYPFQwDOTYuOi9zdG9ja3MvMHAwMDAwYng3MS9ic2UtaW5mby1lZGdlLShpbmRpYSktbHRkL292ZXJ2aWV3LmFzcHgVSW5mbyBFZGdlIChJbmRpYSkgTHRkFUluZm8gRWRnZSAoSW5kaWEpIEx0ZAgxNTQ2OTM5MzwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEJYNzEDMTM2AzEzNgYwLjIzMDEKNjMxODAuODU4MAgxNDc0MzczOQY3MjU2NTRkAmEPZBYCZg8VDAM5Ny5UL3N0b2Nrcy8wcDAwMDBhajloL2JzZS1oaW5kdXN0YW4tcGV0cm9sZXVtLWNvcnAtbHRkLXNocy1kZW1hdGVyaWFsaXNlZC9vdmVydmlldy5hc3B4L0hpbmR1c3RhbiBQZXRyb2xldW0gQ29ycCBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkL0hpbmR1c3RhbiBQZXRyb2xldW0gQ29ycCBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCTIxMTYzNTk0MDwvdG9vbHMvc3RvY2stc2VhcmNoLW11dHVhbC1mdW5kLXBvcnRmb2xpby5hc3B4P2lkPTBQMDAwMEFKOUgDMTM1AzEzNQYwLjE5MDkKNTI0MjIuMjM4MQkxOTkzMDQxNDgIMTIzMzE3OTJkAmIPZBYCZg8VDAM5OC5JL3N0b2Nrcy8wcDAwMDBkNHF4L2JzZS1waG9lbml4LW1pbGxzLWx0ZC1zaHMtZGVtYXRlcmlhbGlzZWQvb3ZlcnZpZXcuYXNweCRQaG9lbml4IE1pbGxzIEx0ZCBTaHMgRGVtYXRlcmlhbGlzZWQkUGhvZW5peCBNaWxscyBMdGQgU2hzIERlbWF0ZXJpYWxpc2VkCDMwODY3OTQ3PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwRDRRWAMxMzQDMTM0BjAuMjA0MQo1NjAzNi4xMjk0CDMwMzMwNDY3BjUzNzQ4MGQCYw9kFgJmDxUMAzk5Ljsvc3RvY2tzLzBwMDAwMG45aWIvYnNlLWp1YmlsYW50LWZvb2R3b3Jrcy1sdGQvb3ZlcnZpZXcuYXNweBZKdWJpbGFudCBGb29kd29ya3MgTHRkFkp1YmlsYW50IEZvb2R3b3JrcyBMdGQJMTA0MTQ3OTg1PC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwTjlJQgMxMzMDMTMzBjAuMTkwMAo1MjE3Mi45NTAwCDk5NzU5NjY0BzQzODgzMjFkAmQPZBYCZg8VDAQxMDAuSC9zdG9ja3MvMHAwMDAwYzNxNi9ic2UtcGFnZS1pbmR1c3RyaWVzLWx0ZC1vcmRpbmFyeS1zaGFyZXMvb3ZlcnZpZXcuYXNweCNQYWdlIEluZHVzdHJpZXMgTHRkIE9yZGluYXJ5IFNoYXJlcyNQYWdlIEluZHVzdHJpZXMgTHRkIE9yZGluYXJ5IFNoYXJlcwcxODg1MDcxPC90b29scy9zdG9jay1zZWFyY2gtbXV0dWFsLWZ1bmQtcG9ydGZvbGlvLmFzcHg/aWQ9MFAwMDAwQzNRNgMxMzIDMTMyBjAuMjU5Ngo3MTI4Ni42MTE4BzE4NDY3MjMFMzgzNDhkAhMPDxYCHgRUZXh0BUZOb3RlOiBTdG9jayBuYW1lIHByZWZpeGVkIHdpdGggKiBkb2VzIG5vdCBoYXZlIGFkZGl0aW9uYWwgaW5mb3JtYXRpb24uZGQCFQ8PFgIfBQUoVG90YWwgbnVtYmVyIG9mIHN0b2NrcyBjb25zaWRlcmVkIDogMTUyMGRkAgUPDxYCHwBoZGQYAQVLY3RsMDAkY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRjb250ZW50UmVzZWFyY2hUb29scyRjdGwwMCRsc3RQb3B1bGFyU3RvY2tzDxQrAA5kZGRkZGRkPCsAZAACZGRkZGYC/////w9k+BhIt2Y0ikLOP+l+GaBrxwRYu42ztdN+TQpfMcNQTiw=',
            '__VIEWSTATEGENERATOR': 'BA27C21D',
            '__EVENTVALIDATION': '/wEdAAqMIty/lARO94JhHT7dKiEbzGvqj0LQwDEl6QJAf2zFDFIeowU56BUmY41PVQo8Jc/VnE7XYTkBEy82w3ee06voOBysIKP3SSsNiMiwxD0Lyke1b257mmI3w7D3EtSImELLS5glg/W3DitsKm/Jz+B+5J9/i/PfGV/ARoWyvyT3Gj8OdBTQ7cq5R36dNtedm0RNW/ecneq9VHKjWfGi8mxyFlMCqSAo1EuNwDx086iKYmuIXPQPnVETgrnTq12rlTg=',
            '__ASYNCPOST': 'true',
            'ctl00$ctl00$ContentPlaceHolder1$contentResearchTools$ctl00$btnGo': 'Go',
        }

        res = requests.post('https://www.morningstar.in/tools/most-popular-stocks-in-mutual-fund.aspx', headers=headers, data=data)
        if res is None or res.status_code != 200:
            return None
        try:
            json_text = res.content
            json_data = json_text #json.loads(json_text)
            result_soup = BeautifulSoup(json_data,'html.parser')
            t = result_soup.find_all('table')[2]
            df = pd.read_html(StringIO(str(t)))
            output = pd.concat([df[0], df[1]], ignore_index=True)
            output.drop_duplicates(subset=['Name'], keep='last',inplace=True)
            output = output.dropna()
            output = output.drop('Unnamed: 0', axis=1)
            output.loc[:, "Name"] = output.loc[:, "Name"].apply(
                        lambda x: " ".join(x.split(" ")[:6]).replace("Ordinary Shares","").replace("Shs Dematerialised","")
                    )
            output.loc[:, "No Of  Shares"] = output.loc[:, "No Of  Shares"].apply(
                        lambda x: colorText.FAIL + str("{:.2f}".format(x/1000000)).replace("nan","-")+ "M" + colorText.END
                    )
            output.loc[:, "Market Value  (Mil)"] = output.loc[:, "Market Value  (Mil)"].apply(
                        lambda x: colorText.FAIL + str("{:.2f}".format(x)).replace("nan","-")+ "M" + colorText.END
                    )
            output.loc[:, "Weighting  %"] = output.loc[:, "Weighting  %"].apply(
                        lambda x: colorText.FAIL + str("{:.2f}".format(x)).replace("nan","-") + colorText.END
                    )
            output.loc[:, "No Of  Funds"] = output.loc[:, "No Of  Funds"].apply(
                        lambda x: colorText.FAIL + str("{:.2f}".format(x)).replace("nan","-") + colorText.END
                    )
            output.loc[:, "Prev No  Of Shares"] = output.loc[:, "Prev No  Of Shares"].apply(
                        lambda x: colorText.FAIL + str("{:.2f}".format(x/1000000)).replace("nan","-")+ "M" + colorText.END
                    )
            output.loc[:, "Change  In Shares"] = output.loc[:, "Change  In Shares"].apply(
                        lambda x: (colorText.GREEN if x > 0 else colorText.FAIL)+ str("{:.2f}".format(x/1000000)).replace("nan","-")+ "M" + colorText.END
                    )
            output.rename(
                columns={
                    "Name": f"Stock",
                },
                inplace=True,
            )
            output.set_index("Stock", inplace=True)
            return output
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass
        return None
    
    # https://www.morningstar.com/stocks/xnse/idea/ownership
    # https://api-global.morningstar.com/sal-service/v1/stock/ownership/v1/0P0000C2H4/OwnershipData/mutualfund/20/data?languageId=en&locale=en&clientId=MDC&component=sal-ownership&version=4.14.0
    # For each stock: https://api-global.morningstar.com/sal-service/v1/stock/header/v2/data/0P0000N0EO/securityInfo?showStarRating=&languageId=en&locale=en&clientId=RSIN_SAL&component=sal-quote&version=4.13.0&access_token=JrelGdhGkgqeSJhy7BufcEzwN0sb
    # Get accessToken from <meta> from https://morningstar.in/stocks/0p0000vp2q/bse-alliance-integrated-metaliks-ltd/overview.aspx
    # Major ownership data: https://api-global.morningstar.com/sal-service/v1/stock/ownership/v1/0P0000C2H4/OwnershipData/institution/20/data?languageId=en&locale=en&clientId=MDC&component=sal-ownership&version=4.14.0
    # ESG risk score: https://api-global.morningstar.com/sal-service/v1/stock/esgRisk/0P0000C2H4/data?languageId=en&locale=en&clientId=MDC&component=sal-eqsv-risk-rating-assessment&version=4.14.0
    # https://www.morningstar.com/stocks/xnse/idea/sustainability
    # curl 'https://17iqhzwxzw-dsn.algolia.net/1/indexes/companies/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.4.0)%3B%20Browser%20(lite)&x-algolia-api-key=be7c37718f927d0137a88a11b69ae419&x-algolia-application-id=17IQHZWXZW' \
    # -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' \
    # -H 'content-type: application/x-www-form-urlencoded' \
    # --data-raw '{"query":"531889","highlightPostTag":" ","highlightPreTag":" ","restrictHighlightAndSnippetArrays":true}' \
    # --compressed
    # https://simplywall.st/stocks/in/tech/bse-530343/genus-power-infrastructures-shares
    # https://lt.morningstar.com/api/rest.svc/g9vi2nsqjb/security/screener?languageId=en&currencyId=BAS&universeIds=E0EXG%24XBOM%7CE0EXG%24XNSE&outputType=json&filterDataPoints=sectorId%7CindustryId&filters=%7B%7D
    def fetchMorningstarStocksPerformanceForExchange(self):
        url = "https://lt.morningstar.com/api/rest.svc/g9vi2nsqjb/security/screener?page=1&pageSize=2500&sortOrder=name%20asc&outputType=json&version=1&languageId=en&currencyId=BAS&universeIds=E0EXG%24XBOM%7CE0EXG%24XNSE&securityDataPoints=secId%2Cname%2CexchangeId%2CsectorId%2CindustryId%2CmarketCap%2CdividendYield%2CclosePrice%2CpriceCurrency%2CPEGRatio%2CpeRatio%2CquantitativeStarRating%2CequityStyleBox%2CgbrReturnM0%2CgbrReturnD1%2CgbrReturnW1%2CgbrReturnM1%2CgbrReturnM3%2CgbrReturnM6%2CgbrReturnM12%2CgbrReturnM36%2CgbrReturnM60%2CgbrReturnM120%2CrevenueGrowth3Y%2CdebtEquityRatio%2CnetMargin%2Croattm%2Croettm%2Cexchange&filters=&term="
        res = self.fetchURL(url)
        if res is None or res.status_code != 200:
            return None
        try:
            data = pd.read_json(StringIO(res.text))
            rows = data["rows"]
            output = pd.DataFrame()
            for row in rows:
                df_row = pd.DataFrame([row]), #columns=["name", "marketCap","exchangeId", "dividendYield", "closePrice","peRatio"])
                output = pd.concat([output, df_row[0]], ignore_index=True)
            output.drop_duplicates(subset=['name'], keep='first',inplace=True)
            output = output[["name","exchangeId","sectorId","industryId","closePrice","gbrReturnM0","gbrReturnD1","gbrReturnW1","gbrReturnM1","gbrReturnM3","gbrReturnM6","gbrReturnM12","gbrReturnM36","gbrReturnM60","gbrReturnM120","marketCap","dividendYield","peRatio","quantitativeStarRating","equityStyleBox","revenueGrowth3Y","debtEquityRatio","netMargin","roattm","roettm","PEGRatio"]]
            output.rename(
                columns={
                    "name": f"Stock",
                    # "marketCap": f"Market Cap. (Cr)",
                    # "exchangeId": f"Exchange",
                    # "dividendYield": f"Dividend (%)",
                    # "closePrice": f"LTP",
                    # "peRatio": f"PE",
                },
                inplace=True,
            )
            output.set_index("Stock", inplace=True)
            return output
        except Exception as e:
            pass
        return None

# from pkscreener.classes import ConfigManager
# configmgr = ConfigManager.tools()
# f = tools(configmgr)
# # f.fetchMorningstarStocksPerformanceForExchange()
# f.fetchMorningstarFundFavouriteStocks()
