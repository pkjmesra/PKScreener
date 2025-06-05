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

#!/usr/bin/env python
# =============================
# AssetsManager.py
# Purpose: Manage asset data, caching, downloads, and Excel export for stock screening
# =============================

import glob
import os
import pickle
import shutil
import tempfile
import pandas as pd
import numpy as np
from halo import Halo
from alive_progress import alive_bar
from yfinance import shared

# --- PKDevTools and pkscreener imports for logging, utilities, and color output ---
from PKDevTools.classes.log import default_logger
from PKDevTools.classes import Archiver
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.MarketHours import MarketHours
from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.SuppressOutput import SuppressOutput

import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes import Utility, ImageUtility
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.PKScheduler import PKScheduler

# =============================
# PKAssetsManager: Main class for asset management
# =============================
class PKAssetsManager:
    # --- Initialize fetcher and configManager as class attributes ---
    fetcher = Fetcher.screenerStockDataFetcher()
    configManager = ConfigManager.tools()
    configManager.getConfig(ConfigManager.parser)

    # =============================
    # Helper: Create Excel hyperlink for stock names
    # =============================
    def make_hyperlink(value):
        url = "https://in.tradingview.com/chart?symbol=NSE:{}"
        return '=HYPERLINK("%s", "%s")' % (url.format(ImageUtility.PKImageTools.stockNameFromDecoratedName(value)), value)

    # =============================
    # Save screened results to Excel (with fallback to Desktop/temp)
    # =============================
    def promptSaveResults(sheetName,df_save, defaultAnswer=None,pastDate=None,screenResults=None):
        """
        Tries to save the dataframe output into an excel file.
        It will first try to save to the current-working-directory/results/
        If it fails to save, it will then try to save to Desktop and then eventually into
a temporary directory.
        """
        data = df_save.copy()
        try:
            # --- Clean up data: fill NaN, replace inf, remove color styles ---
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)
            data = ImageUtility.PKImageTools.removeAllColorStyles(data)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e,exc_info=True)
            pass
        try:
            # --- Add hyperlinks to stock column ---
            data.reset_index(inplace=True)
            with pd.option_context('mode.chained_assignment', None):
                data["Stock"] = data['Stock'].apply(PKAssetsManager.make_hyperlink)
            data.set_index("Stock", inplace=True)
        except: 
            pass
        df = data
        isSaved = False
        try:
            # --- Prompt user to review legends and/or save results ---
            if defaultAnswer is None:
                responseLegends = str(
                        OutputControls().takeUserInput(
                            colorText.WARN
                            + f"[>] Do you want to review legends used in the report above? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): ",defaultInput="N"
                        ) or "N"
                    ).upper()
                if "Y" in responseLegends:
                    OutputControls().printOutput(ImageUtility.PKImageTools.getLegendHelpText(table=None).replace("***:",colorText.END+":").replace("***"," " +colorText.FAIL))
                if not PKAssetsManager.configManager.alwaysExportToExcel:
                    response = str(
                        input(
                            colorText.WARN
                            + f"[>] Do you want to save the results in excel file? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): "
                        ) or "N"
                    ).upper()
                else:
                    response = "Y"
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            response = "Y"
        if response is not None and response.upper() != "N":
            # --- Build filename with date/time and sheet name ---
            pastDateString = f"{pastDate}_to_" if pastDate is not None else ""
            filename = (
                f"PKS_{sheetName.strip()}_"
                + pastDateString
                + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
                + ".xlsx"
            )
            desktop = os.path.expanduser("~/Desktop")
           
            desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
            filePath = ""
            try:
                # --- Try saving to user reports directory ---
                filePath = os.path.join(Archiver.get_user_reports_dir(), filename)
                writer = pd.ExcelWriter(filePath, engine='xlsxwriter') 
                df.to_excel(writer, sheet_name=sheetName[-31:]) 
                writer.close()
                df.to_csv(filePath.replace(".xlsx",".csv"))
                isSaved = True
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput(
                    colorText.FAIL
                    + (
                        "  [+] Error saving file at %s"
                        % filePath
                    )
                    + colorText.END
                )
                try:
                    # --- Fallback: Try saving to Desktop ---
                    filePath = os.path.join(desktop, filename)
                    writer = pd.ExcelWriter(filePath, engine='xlsxwriter') 
                    df.to_excel(writer, sheet_name=sheetName)
                    writer.close()
                    isSaved = True
                except KeyboardInterrupt: # pragma: no cover
                    raise KeyboardInterrupt
                except Exception as ex:  # pragma: no cover
                    default_logger().debug(ex, exc_info=True)
                    OutputControls().printOutput(
                        colorText.FAIL
                        + (
                            "  [+] Error saving file at %s"
                            % filePath
                        )
                        + colorText.END
                    )
                    try:
                        # --- Fallback: Try saving to temp directory ---
                        filePath = os.path.join(tempfile.gettempdir(), filename)
                        writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                        df.to_excel(writer, sheet_name=sheetName)
                        writer.close()
                        isSaved = True
                    except Exception as ex:  # pragma: no cover
                        pass
            OutputControls().printOutput(
                (colorText.GREEN if isSaved else colorText.FAIL)
                + (("  [+] Results saved to %s" % filePath) if isSaved else "  [+] Failed saving results into Excel file!")
                + colorText.END
            )
            return filePath
        return None

    # =============================
    # Check if after-market stock data exists in cache
    # =============================
    def afterMarketStockDataExists(intraday=False, forceLoad=False):
        curr = PKDateUtilities.currentDateTime()
        openTime = curr.replace(hour=MarketHours().openHour, minute=MarketHours().openMinute)
        cache_date = PKDateUtilities.previousTradingDate(PKDateUtilities.nextTradingDate(curr)) #curr  # for monday to friday
        weekday = curr.weekday()
        isTrading = PKDateUtilities.isTradingTime()
        if (forceLoad and isTrading) or isTrading:
           
            cache_date = PKDateUtilities.previousTradingDate(curr) #curr - datetime.timedelta(1)
       
        if curr < openTime:
            cache_date = PKDateUtilities.previousTradingDate(curr) # curr - datetime.timedelta(1)
        if weekday == 0 and curr < openTime:  # for monday before market open
            cache_date = PKDateUtilities.previousTradingDate(curr) #curr - datetime.timedelta(3)
        if weekday == 5 or weekday == 6:  # for saturday and sunday
            cache_date = PKDateUtilities.previousTradingDate(curr) # curr - datetime.timedelta(days=weekday - 4)
        cache_date = cache_date.strftime("%d%m%y")
        pattern = f"{'intraday_' if intraday else ''}stock_data_"
        cache_file = pattern + str(cache_date) + ".pkl"
        exists = False
        for f in glob.glob(f"{pattern}*.pkl", root_dir=Archiver.get_user_data_dir()):
            if f.endswith(cache_file):
                exists = True
                break
        return exists, cache_file

    # =============================
    # Save stock data to pickle file (with downloadOnly and forceSave options)
    # =============================
    @Halo(text='', spinner='dots')
    def saveStockData(stockDict, configManager, loadCount, intraday=False, downloadOnly=False, forceSave=False):
        exists, fileName = PKAssetsManager.afterMarketStockDataExists(
            configManager.isIntradayConfig() or intraday
        )
        outputFolder = Archiver.get_user_data_dir()
        if downloadOnly:
            outputFolder = outputFolder.replace(f"results{os.sep}Data","actions-data-download")
            if not os.path.isdir(outputFolder):
                try:
                    os.makedirs(os.path.dirname(f"{outputFolder}{os.sep}"), exist_ok=True)
                except: # pragma: no cover
                    pass
            configManager.deleteFileWithPattern(rootDir=outputFolder)
        cache_file = os.path.join(outputFolder, fileName)
        if not os.path.exists(cache_file) or forceSave or (loadCount >= 0 and len(stockDict) > (loadCount + 1)):
            try:
                # --- Save stockDict to pickle file ---
                with open(cache_file, "wb") as f:
                    pickle.dump(stockDict.copy(), f, protocol=pickle.HIGHEST_PROTOCOL)
                    OutputControls().printOutput(colorText.GREEN + "=> Done." + colorText.END)
                if downloadOnly:
                    # --- Print all relevant files for downloadOnly mode ---
                    rootDirs = [Archiver.get_user_data_dir(),Archiver.get_user_indices_dir(),outputFolder]
                    patterns = ["*.csv","*.pkl"]
                    for dir in rootDirs:
                        for pattern in patterns:
                            for f in glob.glob(pattern, root_dir=dir, recursive=True):
                                OutputControls().printOutput(colorText.GREEN + f"=> {f}" + colorText.END)
                                if "RUNNER" in os.environ.keys():
                                    Committer.execOSCommand(f"git add {f} -f >/dev/null 2>&1")

            except pickle.PicklingError as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput(
                    colorText.FAIL
                    + "=> Error while Caching Stock Data."
                    + colorText.END
                )
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
        else:
            OutputControls().printOutput(
                colorText.GREEN + "=> Already Cached." + colorText.END
            )
            if downloadOnly:
                OutputControls().printOutput(colorText.GREEN + f"=> {cache_file}" + colorText.END)
        return cache_file

    # =============================
    # Check for yfinance rate limit errors
    # =============================
    def had_rate_limit_errors():
        """Checks if any stored errors are YFRateLimitError."""
        err = ",".join(list(shared._ERRORS.values()))
        hitRateLimit = "YFRateLimitError" in err or "Too Many Requests" in err or "429" in err
        if hitRateLimit:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] We hit a rate limit error in the previous request(s)!"
                + colorText.END
            )
        return hitRateLimit
    
    # =============================
    # Download latest data for a batch of stocks (with retries)
    # =============================
    @Halo(text='  [+] Downloading fresh data from Data Providers...', spinner='dots')
    def downloadLatestData(stockDict, configManager, stockCodes=[], exchangeSuffix=".NS", downloadOnly=False, numStocksPerIteration=0):
        """
        Improved batch download for yfinance 0.2.61+ (inspired by test_download.py)
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import yfinance as yf
        from yfinance import shared
        
        def download_single_stock(stock_code, period, interval, exchange_suffix):
            ticker_symbol = f"{stock_code}{exchange_suffix}"
            try:
                if ticker_symbol in shared._ERRORS:
                    del shared._ERRORS[ticker_symbol]
                ticker = yf.Ticker(ticker_symbol)
                data = ticker.history(
                    period=period,
                    interval=interval,
                    auto_adjust=True,
                    timeout=15,
                    rounding=True
                )
                if data.empty:
                    return stock_code, None
                data_dict = data.to_dict("split")
                return stock_code, data_dict
            except Exception as e:
                default_logger().debug(f"Error downloading {stock_code}: {str(e)}")
                return stock_code, None

        batch_size = 100  # Always use 100 stocks per batch
        max_workers = 5
        max_retries = 1
        all_stockDict = stockDict.copy() if stockDict else {}
        leftOutStocks = stockCodes.copy()
        period = configManager.period
        interval = configManager.duration

        for attempt in range(max_retries + 1):
            if not leftOutStocks:
                break
            current_batch_size = batch_size
            failed = []
            print(f"[Batch Download] Attempt {attempt+1}/{max_retries+1}: {len(leftOutStocks)} stocks, batch size {current_batch_size}")
            for i in range(0, len(leftOutStocks), current_batch_size):
                batch = leftOutStocks[i:i+current_batch_size]
                batch_success = 0
                batch_failed = 0
                batch_start_time = time.time()
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_stock = {
                        executor.submit(download_single_stock, stock_code, period, interval, exchangeSuffix): stock_code
                        for stock_code in batch
                    }
                    for future in as_completed(future_to_stock, timeout=120):
                        stock_code = future_to_stock[future]
                        try:
                            result_stock, result_data = future.result()
                            if result_data is not None:
                                all_stockDict[result_stock] = result_data
                                batch_success += 1
                            else:
                                failed.append(result_stock)
                                batch_failed += 1
                        except Exception as e:
                            default_logger().debug(f"Future failed for {stock_code}: {str(e)}")
                            failed.append(stock_code)
                            batch_failed += 1
                batch_end_time = time.time()
                OutputControls().printOutput(
                    colorText.GREEN + f"Batch: Downloaded {batch_success}, Failed {batch_failed} (Time: {batch_end_time - batch_start_time:.2f}s)" + colorText.END
                )
                time.sleep(1.5 if current_batch_size > 10 else 1.0)
            leftOutStocks = failed
            if leftOutStocks and attempt < max_retries:
                OutputControls().printOutput(colorText.WARN + f"Retrying {len(leftOutStocks)} failed stocks..." + colorText.END)
                time.sleep(1.0)
        OutputControls().printOutput(colorText.GREEN + f"[Batch Download] Finished: {len(all_stockDict)} downloaded, {len(leftOutStocks)} failed." + colorText.END)
        return all_stockDict, leftOutStocks

    # =============================
    # Load stock data (from cache, server, or download as needed)
    # =============================
    def loadStockData(
        stockDict,
        configManager,
        downloadOnly=False,
        defaultAnswer=None,
        retrial=False,
        forceLoad=False,
        stockCodes=[],
        exchangeSuffix=".NS",
        isIntraday = False,
        forceRedownload=False,
        userDownloadOption=None
    ):
        isIntraday = isIntraday or configManager.isIntradayConfig()
        exists, cache_file = PKAssetsManager.afterMarketStockDataExists(
            isIntraday, forceLoad=forceLoad
        )
        initialLoadCount = len(stockDict)
        leftOutStocks = None
        recentDownloadFromOriginAttempted = False
        isTrading = PKDateUtilities.isTradingTime() and (PKDateUtilities.wasTradedOn() or not PKDateUtilities.isTodayHoliday()[0])
        if userDownloadOption is not None and "B" in userDownloadOption: # Backtests
            isTrading = False
        # Check if NSEI data is requested
        if configManager.baseIndex not in stockCodes:
            stockCodes.insert(0,configManager.baseIndex)
        
        if (stockCodes is not None and len(stockCodes) > 0) and (isTrading or downloadOnly):
            recentDownloadFromOriginAttempted = True
            stockDict, leftOutStocks = PKAssetsManager.downloadLatestData(stockDict,configManager,stockCodes,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(stockCodes) if stockCodes is not None else 0)
            if len(leftOutStocks) > int(len(stockCodes)*0.05) and not PKAssetsManager.had_rate_limit_errors():
                
                stockDict, _ = PKAssetsManager.downloadLatestData(stockDict,configManager,leftOutStocks,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(leftOutStocks) if leftOutStocks is not None else 0)
            # return stockDict
        if downloadOnly or isTrading:
            # We don't want to download from local stale pkl file or stale file at server
            return stockDict
        
        default_logger().debug(
            f"Stock data cache file:{cache_file} exists ->{str(exists)}"
        )
        stockDataLoaded = False
        
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
      
        if os.path.exists(srcFilePath) and not forceRedownload:
            stockDict, stockDataLoaded = PKAssetsManager.loadDataFromLocalPickle(stockDict,configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading)
        if (
            not stockDataLoaded
            and ("1d" if isIntraday else ConfigManager.default_period)
            == configManager.period
            and ("1m" if isIntraday else ConfigManager.default_duration)
            == configManager.duration
        ) or forceRedownload:
            stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(stockDict,configManager, downloadOnly, defaultAnswer, retrial, forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, cache_file, isTrading)
        if not stockDataLoaded:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] Cache unavailable on pkscreener server, Continuing.."
                + colorText.END
            )
        if not stockDataLoaded and not recentDownloadFromOriginAttempted and not PKAssetsManager.had_rate_limit_errors():
            stockDict, _ = PKAssetsManager.downloadLatestData(stockDict,configManager,stockCodes,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(stockCodes) if stockCodes is not None else 0)
        # See if we need to save stock data
        stockDataLoaded = stockDataLoaded or (len(stockDict) > 0 and (len(stockDict) != initialLoadCount))
        leftOutStocks = list(set(stockCodes)-set(list(stockDict.keys())))
        if len(leftOutStocks) > int(len(stockCodes)*0.05) and not PKAssetsManager.had_rate_limit_errors():
            # More than 5 % of stocks are still remaining
            stockDict, _ = PKAssetsManager.downloadLatestData(stockDict,configManager,leftOutStocks,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(leftOutStocks) if leftOutStocks is not None else 0)
        if stockDataLoaded and downloadOnly:
            PKAssetsManager.saveStockData(stockDict,configManager,initialLoadCount,isIntraday,downloadOnly, forceSave=stockDataLoaded)
        return stockDict

    # =============================
    # Load data from local pickle cache
    # =============================
    @Halo(text='  [+] Loading data from local cache...', spinner='dots')
    def loadDataFromLocalPickle(stockDict, configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading):
        stockDataLoaded = False
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)

        try:
            # --- Attempt to load pickle file ---
            with open(srcFilePath, "rb") as f:
                stockData = pickle.load(f)
            if not stockData:
                return stockDict, stockDataLoaded
            if not downloadOnly:
                OutputControls().printOutput(
                    colorText.GREEN
                    + f"\n  [+] Automatically Using [{len(stockData)}] Tickers' Cached Stock Data"
                    + (" due to After-Market hours" if not PKDateUtilities.isTradingTime() else "")
                    + colorText.END
                )
            multiIndex = stockData.keys()
            if isinstance(multiIndex, pd.MultiIndex):
                listStockCodes = sorted(set(multiIndex.get_level_values(0)))
            else:
                listStockCodes = list(stockData.keys())
            if exchangeSuffix and any(exchangeSuffix in code for code in listStockCodes):
                listStockCodes = [x.replace(exchangeSuffix, "") for x in listStockCodes]
            for stock in listStockCodes:
                df_or_dict = stockData.get(stock)
                df_or_dict = df_or_dict.to_dict("split") if isinstance(df_or_dict, pd.DataFrame) else df_or_dict
                existingPreLoadedData = stockDict.get(stock)
                if existingPreLoadedData:
                    if isTrading:
                        for col in ["MF", "FII", "MF_Date", "FII_Date", "FairValue"]:
                            existingPreLoadedData[col] = df_or_dict.get(col)
                        stockDict[stock] = existingPreLoadedData
                    else:
                        stockDict[stock] = {**existingPreLoadedData, **df_or_dict}
                elif not isTrading:
                    stockDict[stock] = df_or_dict
            stockDataLoaded = True
        except (pickle.UnpicklingError, EOFError) as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL + "  [+] Error while Reading Stock Cache." + colorText.END
            )
            if PKAssetsManager.promptFileExists(defaultAnswer=defaultAnswer) == "Y":
                configManager.deleteFileWithPattern()
        except KeyboardInterrupt:
            raise
        return stockDict, stockDataLoaded

    # =============================
    # Download saved defaults from server (for cache file)
    # =============================
    @Halo(text='', spinner='dots')
    def downloadSavedDefaultsFromServer(cache_file):
        fileDownloaded = False
        resp = Utility.tools.tryFetchFromServer(cache_file)
        if resp is not None:
            default_logger().debug(
                    f"Stock data cache file:{cache_file} request status ->{resp.status_code}"
                )
        if resp is not None and resp.status_code == 200:
            contentLength = resp.headers.get("content-length")
            serverBytes = int(contentLength) if contentLength is not None else 0
            KB = 1024
            MB = KB * 1024
            chunksize = MB if serverBytes >= MB else (KB if serverBytes >= KB else 1)
            filesize = int( serverBytes / chunksize)
            if filesize > 40: 
                try:
                    with open(os.path.join(Archiver.get_user_data_dir(), cache_file),"w+",) as f: # .split(os.sep)[-1]
                        f.write(resp.text)
                    fileDownloaded = True
                except: # pragma: no cover
                    pass
        return fileDownloaded

    # =============================
    # Download and load saved data from server (with progress bar)
    # =============================
    def downloadSavedDataFromServer(stockDict, configManager, downloadOnly, defaultAnswer, retrial, forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, cache_file, isTrading):
        stockDataLoaded = False
        resp = Utility.tools.tryFetchFromServer(cache_file)
        if resp is not None:
            default_logger().debug(
                    f"Stock data cache file:{cache_file} request status ->{resp.status_code}"
                )
        if resp is not None and resp.status_code == 200:
            contentLength = resp.headers.get("content-length")
            serverBytes = int(contentLength) if contentLength is not None else 0
            KB = 1024
            MB = KB * 1024
            chunksize = MB if serverBytes >= MB else (KB if serverBytes >= KB else 1)
            filesize = int( serverBytes / chunksize)
            if filesize > 40 and chunksize == MB: 
                bar, spinner = Utility.tools.getProgressbarStyle()
                try:
                    f = open(
                            os.path.join(Archiver.get_user_data_dir(), cache_file),
                            "w+b",
                        )  # .split(os.sep)[-1]
                    dl = 0
                    with alive_bar(
                            filesize, bar=bar, spinner=spinner, manual=True
                        ) as progressbar:
                        for data in resp.iter_content(chunk_size=chunksize):
                            dl += 1
                            f.write(data)
                            progressbar(dl / filesize)
                            if dl >= filesize:
                                progressbar(1.0)
                    f.close()
                    with open(
                            os.path.join(Archiver.get_user_data_dir(), cache_file),
                            "rb",
                        ) as f:
                        stockData = pickle.load(f)
                    if len(stockData) > 0:
                        multiIndex = stockData.keys()
                        if isinstance(multiIndex, pd.MultiIndex):
                                
                            listStockCodes = multiIndex.get_level_values(0)
                            listStockCodes = sorted(list(filter(None,list(set(listStockCodes)))))
                            if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                                listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                        else:
                            listStockCodes = list(stockData.keys())
                            if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                                listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                        for stock in listStockCodes:
                            df_or_dict = stockData.get(stock)
                            df_or_dict = df_or_dict.to_dict("split") if isinstance(df_or_dict,pd.DataFrame) else df_or_dict
                                
                            try:
                                existingPreLoadedData = stockDict.get(stock)
                                if existingPreLoadedData is not None:
                                    if isTrading:
                                           
                                        cols = ["MF", "FII","MF_Date","FII_Date","FairValue"]
                                        for col in cols:
                                            existingPreLoadedData[col] = df_or_dict.get(col)
                                        stockDict[stock] = existingPreLoadedData
                                    else:
                                        stockDict[stock] = df_or_dict | existingPreLoadedData
                                else:
                                    if not isTrading:
                                        stockDict[stock] = df_or_dict
                            except: 
                                    
                                continue
                        stockDataLoaded = True
                        
                        OutputControls().moveCursorUpLines(1)
                except KeyboardInterrupt: # pragma: no cover
                    raise KeyboardInterrupt
                except Exception as e:  # pragma: no cover
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    OutputControls().printOutput("[!] Download Error - " + str(e))
            else:
                default_logger().debug(
                        f"Stock data cache file:{cache_file} on server has length ->{filesize} {'Mb' if chunksize >= MB else ('Kb' if chunksize >= KB else 'bytes')}"
                    )
            if not retrial and not stockDataLoaded:
                # Don't try for more than once.
                stockDict = PKAssetsManager.loadStockData(
                        stockDict,
                        configManager,
                        downloadOnly,
                        defaultAnswer,
                        retrial=True,
                        forceLoad=forceLoad,
                        stockCodes=stockCodes,
                        exchangeSuffix=exchangeSuffix,
                        isIntraday = isIntraday,
                        forceRedownload=forceRedownload
                    )
                
        return stockDict,stockDataLoaded

    # =============================
    # Prompt user if file exists (Y/N)
    # =============================
    def promptFileExists(cache_file="stock_data_*.pkl", defaultAnswer=None):
        try:
            if defaultAnswer is None:
                response = str(
                    input(
                        colorText.WARN
                        + "[>] "
                        + cache_file
                        + " already exists. Do you want to replace this? [Y/N] (Default: Y): "
                ) or "Y").upper()
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        return "Y" if response != "N" else "N"

# =============================
# End of PKAssetsManager
# =============================

# =============================
# Notes & Observations
# =============================
# - All logic and structure are preserved as in the original script.
# - Comments have been added to clarify the purpose of each major section and function.
# - No renaming or reordering was performed.
# - Minor whitespace and comment formatting for clarity.
# - No bugs or edge cases were fixed inline; see below for any observations.
#
# Notes & Observations:
# 1. The script uses a lot of try/except/pass blocks. This can hide errors; consider logging or handling exceptions more specifically.
# 2. The fallback logic for saving files is robust, but if all locations fail, the user only gets a generic error.
# 3. The use of 'or' in input() calls (e.g., input(...) or "Y") is good for defaulting, but if input is interrupted, it may not always behave as expected.
# 4. The script assumes certain directory structures and permissions; if these change, file operations may fail.
# 5. The use of global class attributes (e.g., fetcher, configManager) is preserved, but could be refactored for better encapsulation in the future.
# 6. The script is careful not to overwrite files unless the user agrees, which is good for safety.
# 7. The batch download logic is efficient and uses ThreadPoolExecutor, but the max_workers and batch_size are hardcoded.
# 8. The script is compatible with Python 3.x and avoids advanced features for maximum compatibility.
#
# End of Notes & Observations
