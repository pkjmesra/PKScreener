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
import glob
import os
import pickle
import shutil
import tempfile
import pandas as pd
import numpy as np
from halo import Halo
from alive_progress import alive_bar
# from yfinance import shared

from PKDevTools.classes.log import default_logger
from PKDevTools.classes import Archiver
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.MarketHours import MarketHours
from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.PKBackupRestore import start_backup

import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes import Utility, ImageUtility
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.PKScheduler import PKScheduler

class PKAssetsManager:
    fetcher = Fetcher.screenerStockDataFetcher()
    configManager = ConfigManager.tools()
    configManager.getConfig(ConfigManager.parser)

    def make_hyperlink(value):
        url = "https://in.tradingview.com/chart?symbol=NSE:{}"
        return '=HYPERLINK("%s", "%s")' % (url.format(ImageUtility.PKImageTools.stockNameFromDecoratedName(value)), value)

    # Save screened results to excel
    def promptSaveResults(sheetName,df_save, defaultAnswer=None,pastDate=None,screenResults=None):
        """
        Tries to save the dataframe output into an excel file.

        It will first try to save to the current-working-directory/results/

        If it fails to save, it will then try to save to Desktop and then eventually into
        a temporary directory.
        """
        data = df_save.copy()
        try:
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)
            data = ImageUtility.PKImageTools.removeAllColorStyles(data)
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            default_logger().debug(e,exc_info=True)
            pass
        try:
            data.reset_index(inplace=True)
            with pd.option_context('mode.chained_assignment', None):
                data["Stock"] = data['Stock'].apply(PKAssetsManager.make_hyperlink)
            data.set_index("Stock", inplace=True)
        except: # pragma: no cover
            pass
        df = data
        isSaved = False
        try:
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
            pastDateString = f"{pastDate}_to_" if pastDate is not None else ""
            filename = (
                f"PKS_{sheetName.strip()}_"
                + pastDateString
                + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
                + ".xlsx"
            )
            desktop = os.path.expanduser("~/Desktop")
            # # the above is valid on Windows (after 7) but if you want it in os normalized form:
            desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
            filePath = ""
            try:
                filePath = os.path.join(Archiver.get_user_reports_dir(), filename)
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                # Convert the dataframe to an XlsxWriter Excel object.
                df.to_excel(writer, sheet_name=sheetName[-31:]) # sheetname cannot be beyond 31 character
                # Close the Pandas Excel writer and output the Excel file.
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
                    filePath = os.path.join(desktop, filename)
                    # Create a Pandas Excel writer using XlsxWriter as the engine.
                    writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                    # Convert the dataframe to an XlsxWriter Excel object.
                    df.to_excel(writer, sheet_name=sheetName)
                    # Close the Pandas Excel writer and output the Excel file.
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
                        filePath = os.path.join(tempfile.gettempdir(), filename)
                        # Create a Pandas Excel writer using XlsxWriter as the engine.
                        writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                        # Convert the dataframe to an XlsxWriter Excel object.
                        df.to_excel(writer, sheet_name=sheetName)
                        # Close the Pandas Excel writer and output the Excel file.
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

    def afterMarketStockDataExists(intraday=False, forceLoad=False):
        exists, cache_file = Archiver.afterMarketStockDataExists(intraday=intraday,
                                                                 forceLoad=forceLoad,
                                                                 date_suffix=True)
        return exists, cache_file

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
                with open(cache_file, "wb") as f:
                    pickle.dump(stockDict.copy(), f, protocol=pickle.HIGHEST_PROTOCOL)
                    OutputControls().printOutput(colorText.GREEN + "=> Done." + colorText.END)
                if downloadOnly:
                    # if "RUNNER" not in os.environ.keys():
                        # copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{fileName}")
                        # cacheFileSize = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
                        # if os.path.exists(cache_file) and cacheFileSize >= 1024*1024*40:
                        #     shutil.copy(cache_file,copyFilePath) # copy is the saved source of truth

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

    def had_rate_limit_errors():
        return False
        """Checks if any stored errors are YFRateLimitError."""
        err = "" #",".join(list(shared._ERRORS.values()))
        hitRateLimit = "YFRateLimitError" in err or "Too Many Requests" in err or "429" in err
        if hitRateLimit:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] We hit a rate limit error in the previous request(s)!"
                + colorText.END
            )
        return hitRateLimit
    
    @Halo(text='  [+] Downloading fresh data from Data Providers...', spinner='dots')
    def downloadLatestData(stockDict,configManager,stockCodes=[],exchangeSuffix=".NS",downloadOnly=False,numStocksPerIteration=0):
        """
        shared._ERRORS.clear()  # Clear previous errors
        # if numStocksPerIteration == 0:
        # maxParallelProcesses = 17
        numStocksPerIteration = 100 #(int(len(stockCodes)/int(len(stockCodes)/maxParallelProcesses)) if len(stockCodes) >= maxParallelProcesses else len(stockCodes)) + 1
        queueCounter = 0
        iterations = int(len(stockCodes)/numStocksPerIteration) + 1
        tasksList = []
        while queueCounter < iterations:
            stocks = []
            if queueCounter < iterations:
                stocks = stockCodes[numStocksPerIteration* queueCounter : numStocksPerIteration* (queueCounter + 1)]
            else:
                stocks = ["DUMMYStock"]#stockCodes[numStocksPerIteration* queueCounter :]
            fn_args = (stocks, configManager.period, configManager.duration,exchangeSuffix)
            task = PKTask(f"DataDownload-{queueCounter}",long_running_fn=PKAssetsManager.fetcher.fetchStockDataWithArgs,long_running_fn_args=fn_args)
            task.userData = stocks
            if len(stocks) > 0:
                tasksList.append(task)
            queueCounter += 1
        """
        processedStocks = []
        """
        if len(tasksList) > 0:
            # Suppress any multiprocessing errors/warnings
            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                PKScheduler.scheduleTasks(tasksList=tasksList, 
                                        label=f"Downloading latest data [{configManager.period},{configManager.duration}] (Total={len(stockCodes)} records in {len(tasksList)} batches){'Be Patient!' if len(stockCodes)> 2000 else ''}",
                                        timeout=(5+2.5*configManager.longTimeout*(4 if downloadOnly else 1)), # 5 sec additional time for multiprocessing setup
                                        minAcceptableCompletionPercentage=(100 if downloadOnly else 100),
                                        showProgressBars=configManager.logsEnabled)
            for task in tasksList:
                if task.result is not None and isinstance(task.result,pd.DataFrame) and not task.result.empty:
                    for stock in task.userData:
                        taskResult = task.result.get(f"{stock}{exchangeSuffix}")
                        if taskResult is not None and isinstance(taskResult,pd.DataFrame) and not taskResult.empty:
                            stockDict[stock] = taskResult.to_dict("split")
                            processedStocks.append(stock)
        """
        leftOutStocks = list(set(stockCodes)-set(processedStocks))
        default_logger().debug(f"Attempted fresh download of {len(stockCodes)} stocks and downloaded {len(processedStocks)} stocks. {len(leftOutStocks)} stocks remaining.")
        return stockDict, leftOutStocks

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
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
        isTrading = PKDateUtilities.isTradingTime() and (PKDateUtilities.wasTradedOn() or not PKDateUtilities.isTodayHoliday()[0])
        if isTrading or not os.path.exists(srcFilePath):
            try:
                from pkbrokers.kite.examples.externals import kite_fetch_save_pickle
                if kite_fetch_save_pickle():
                    default_logger().info("pkl file update succeeded!")
            except Exception as e:
                default_logger().error(f"Error downloading latest file:{e}")
            isTrading = False
        if userDownloadOption is not None and "B" in userDownloadOption: # Backtests
            isTrading = False
        # Check if NSEI data is requested
        if configManager.baseIndex not in stockCodes:
            stockCodes.insert(0,configManager.baseIndex)
        # stockCodes is not None mandates that we start our work based on the downloaded data from yesterday
        if (stockCodes is not None and len(stockCodes) > 0) and (isTrading or downloadOnly):
            recentDownloadFromOriginAttempted = True
            stockDict, leftOutStocks = PKAssetsManager.downloadLatestData(stockDict,configManager,stockCodes,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(stockCodes) if stockCodes is not None else 0)
            if len(leftOutStocks) > int(len(stockCodes)*0.05) and not PKAssetsManager.had_rate_limit_errors():
                # During live market hours, we may not really get additional data if we didn't
                # get it the first time
                # More than 5 % of stocks are still remaining
                stockDict, _ = PKAssetsManager.downloadLatestData(stockDict,configManager,leftOutStocks,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly,numStocksPerIteration=len(leftOutStocks) if leftOutStocks is not None else 0)
            # return stockDict
        if downloadOnly or isTrading:
            # We don't want to download from local stale pkl file or stale file at server
            # start_backup()
            return stockDict
        
        default_logger().debug(
            f"Stock data cache file:{cache_file} exists ->{str(exists)}"
        )
        stockDataLoaded = False
        # copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
        # if os.path.exists(copyFilePath):
        #     shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
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
        # start_backup()
        return stockDict

    @Halo(text='  [+] Loading data from local cache...', spinner='dots')
    def loadDataFromLocalPickle(stockDict, configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading):
        stockDataLoaded = False
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)

        try:
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
            if filesize > 40: #Something definitely went wrong. It should be upward of 40bytes
                try:
                    with open(os.path.join(Archiver.get_user_data_dir(), cache_file),"w+",) as f: # .split(os.sep)[-1]
                        f.write(resp.text)
                    fileDownloaded = True
                except: # pragma: no cover
                    pass
        return fileDownloaded

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
            if filesize > 20 and chunksize == MB: # Saved data can't be in KBs. Something definitely went wrong. It should be upward of 40MB
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
                                # If we requested for multiple stocks from yfinance
                                # we'd have received a multiindex dataframe
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
                                # This will keep all the latest security data we downloaded
                                # just now and also copy the additional data like, MF/FII,FairValue
                                # etc. data, from yesterday's saved data.
                            try:
                                existingPreLoadedData = stockDict.get(stock)
                                if existingPreLoadedData is not None:
                                    if isTrading:
                                            # Only copy the MF/FII/FairValue data and leave the stock prices as is.
                                        cols = ["MF", "FII","MF_Date","FII_Date","FairValue"]
                                        for col in cols:
                                            existingPreLoadedData[col] = df_or_dict.get(col)
                                        stockDict[stock] = existingPreLoadedData
                                    else:
                                        stockDict[stock] = df_or_dict | existingPreLoadedData
                                else:
                                    if not isTrading:
                                        stockDict[stock] = df_or_dict
                            except: # pragma: no cover
                                    # Probably, the "stock" got removed from the latest download
                                    # and so, was not found in stockDict
                                continue
                        stockDataLoaded = True
                        # copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
                        # srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
                        # if os.path.exists(copyFilePath) and os.path.exists(srcFilePath):
                        #     shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
                        # if not os.path.exists(copyFilePath) and os.path.exists(srcFilePath): # Let's make a copy of the original one
                        #     shutil.copy(srcFilePath,copyFilePath)
                        # Remove the progress bar now!
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

    # Save screened results to excel
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
