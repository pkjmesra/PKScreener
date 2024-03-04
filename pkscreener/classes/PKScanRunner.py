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
import pandas as pd
import multiprocessing
from time import sleep

from PKDevTools.classes import Archiver
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKGitFolderDownloader import downloadFolder
from PKDevTools.classes.PKMultiProcessorClient import PKMultiProcessorClient

from pkscreener.classes.StockScreener import StockScreener
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes.ConfigManager import parser, tools

import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.ScreeningStatistics as ScreeningStatistics

class PKScanRunner:
    configManager = tools()
    configManager.getConfig(parser)
    fetcher = Fetcher.screenerStockDataFetcher(configManager)
    candlePatterns = CandlePatterns()

    def initDataframes():
        screenResults = pd.DataFrame(
            columns=[
                "Stock",
                "Consol.",
                "Breakout",
                "LTP",
                "52Wk H",
                "52Wk L",
                "%Chng",
                "Volume",
                "MA-Signal",
                "RSI",
                "Trend",
                "Pattern",
                "CCI",
            ]
        )
        saveResults = pd.DataFrame(
            columns=[
                "Stock",
                "Consol.",
                "Breakout",
                "LTP",
                "52Wk H",
                "52Wk L",
                "%Chng",
                "Volume",
                "MA-Signal",
                "RSI",
                "Trend",
                "Pattern",
                "CCI",
            ]
        )
        return screenResults, saveResults

    def initQueues(minimumCount=0):
        tasks_queue = multiprocessing.JoinableQueue()
        results_queue = multiprocessing.Queue()

        totalConsumers = min(minimumCount, multiprocessing.cpu_count())
        if totalConsumers == 1:
            totalConsumers = 2  # This is required for single core machine
        if PKScanRunner.configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
            totalConsumers -= 1
        return tasks_queue, results_queue, totalConsumers

    def populateQueues(items, tasks_queue, exit=False):
        for item in items:
            tasks_queue.put(item)
        if exit:
            # Append exit signal for each process indicated by None
            for _ in range(multiprocessing.cpu_count()):
                tasks_queue.put(None)


    def getScanDurationParameters(testing, menuOption):
        # Number of days from past, including the backtest duration chosen by the user
        # that we will need to consider to evaluate the data. If the user choses 10-period
        # backtesting, we will need to have the past 6-months or whatever is returned by
        # x = getHistoricalDays and 10 days of recent data. So total rows to consider
        # will be x + 10 days.
        samplingDuration = (3 if testing else PKScanRunner.configManager.backtestPeriod+1) if menuOption.upper() in ["B"] else 2
        fillerPlaceHolder = 1 if menuOption in ["B"] else 2
        actualHistoricalDuration = (samplingDuration - fillerPlaceHolder)
        return samplingDuration,fillerPlaceHolder,actualHistoricalDuration

    def addStocksToItemList(userArgs, testing, testBuild, newlyListedOnly, downloadOnly, minRSI, maxRSI, insideBarToLookback, respChartPattern, daysForLowestVolume, backtestPeriod, reversalOption, maLength, listStockCodes, menuOption, executeOption, volumeRatio, items, daysInPast):
        moreItems = [
                        (
                            menuOption,
                            executeOption,
                            reversalOption,
                            maLength,
                            daysForLowestVolume,
                            minRSI,
                            maxRSI,
                            respChartPattern,
                            insideBarToLookback,
                            len(listStockCodes),
                            PKScanRunner.configManager.cacheEnabled,
                            stock,
                            newlyListedOnly,
                            downloadOnly,
                            volumeRatio,
                            testBuild,
                            userArgs.log,
                            daysInPast,
                            (
                                backtestPeriod
                                if menuOption == "B"
                                else PKScanRunner.configManager.effectiveDaysToLookback
                            ),
                            default_logger().level,
                            (menuOption in ["B", "G", "X", "S","C"])
                            or (userArgs.backtestdaysago is not None),
                            # assumption is that fetcher.fetchStockData would be
                            # mocked to avoid calling yf.download again and again
                            PKScanRunner.fetcher.fetchStockData() if testing else None,
                        )
                        for stock in listStockCodes
                    ]
        items.extend(moreItems)

    def getStocksListForScan(userArgs, menuOption, totalStocksInReview, downloadedRecently, daysInPast):
        savedStocksCount = 0
        pastDate, savedListResp = PKScanRunner.downloadSavedResults(daysInPast,downloadedRecently=downloadedRecently)
        downloadedRecently = True
        if savedListResp is not None and len(savedListResp) > 0:
            savedListStockCodes = savedListResp
            savedStocksCount = len(savedListStockCodes)
            if savedStocksCount > 0:
                listStockCodes = savedListStockCodes
                totalStocksInReview += savedStocksCount
            else:
                if menuOption in ["B"] and not userArgs.forceBacktestsForZeroResultDays:
                                    # We have a zero length result saved in repo.
                                    # Likely we didn't have any stock in the result output. So why run the scan again?
                    listStockCodes = savedListStockCodes
                totalStocksInReview += len(listStockCodes)
        else:
            totalStocksInReview += len(listStockCodes)
        return listStockCodes,savedStocksCount,pastDate

    def getBacktestDaysForScan(userArgs, backtestPeriod, menuOption, actualHistoricalDuration):
        daysInPast = (
                                actualHistoricalDuration
                                if (menuOption == "B")
                                else (
                                    (backtestPeriod)
                                    if (menuOption == "G")
                                    else (
                                        0
                                        if (userArgs.backtestdaysago is None)
                                        else (int(userArgs.backtestdaysago))
                                    )
                                )
                            )
                
        return daysInPast
    
    def downloadSavedResults(daysInPast,downloadedRecently=False):
        pastDate = PKDateUtilities.nthPastTradingDateStringFromFutureDate(daysInPast)
        filePrefix = PKScanRunner.getFormattedChoices().replace("B","X").replace("G","X").replace("S","X")
        # url = f"https://raw.github.com/pkjmesra/PKScreener/actions-data-download/actions-data-scan/{filePrefix}_{pastDate}.txt"
        # savedListResp = fetcher.fetchURL(url)
        localPath = Archiver.get_user_outputs_dir()
        downloadedPath = os.path.join(localPath,"PKScreener","actions-data-scan")
        if not downloadedRecently:
            downloadedPath = downloadFolder(localPath=localPath,
                                            repoPath="pkjmesra/PKScreener",
                                            branchName="actions-data-download",
                                            folderName="actions-data-scan")
        items = []
        savedList = []
        fileName = os.path.join(downloadedPath,f"{filePrefix}_{pastDate}.txt")
        if os.path.isfile(fileName):
            #File already exists.
            with open(fileName, 'r') as fe:
                stocks = fe.read()
                items = stocks.replace("\n","").replace("\"","").split(",")
                savedList = sorted(list(filter(None,list(set(items)))))
        return pastDate,savedList
    
    def getFormattedChoices(userArgs, selectedChoice):
        isIntraday = PKScanRunner.configManager.isIntradayConfig() or (
            userArgs.intraday is not None
        )
        choices = ""
        for choice in selectedChoice:
            if len(selectedChoice[choice]) > 0:
                if len(choices) > 0:
                    choices = f"{choices}_"
                choices = f"{choices}{selectedChoice[choice]}"
        if choices.endswith("_"):
            choices = choices[:-1]
        choices = f"{choices}{'_i' if isIntraday else ''}"
        return choices

    def PrepareAndRunScan(keyboardInterruptEvent,screenCounter,screenResultsCounter,stockDict,testing, backtestPeriod, menuOption, samplingDuration, items,screenResults, saveResults, backtest_df,scanningCb):
        tasks_queue, results_queue, totalConsumers = PKScanRunner.initQueues(len(items))
        scr = ScreeningStatistics.ScreeningStatistics(PKScanRunner.configManager, default_logger())
        consumers = [
                    PKMultiProcessorClient(
                        StockScreener().screenStocks,
                        tasks_queue,
                        results_queue,
                        screenCounter,
                        screenResultsCounter,
                        stockDict,
                        PKScanRunner.fetcher.proxyServer,
                        keyboardInterruptEvent,
                        default_logger(),
                        PKScanRunner.fetcher,
                        PKScanRunner.configManager,
                        PKScanRunner.candlePatterns,
                        scr,
                    )
                    for _ in range(totalConsumers)
                ]
        PKScanRunner.startWorkers(consumers)
        screenResults, saveResults, backtest_df = scanningCb(
                    menuOption,
                    items,
                    tasks_queue,
                    results_queue,
                    len(items),
                    backtestPeriod,
                    samplingDuration - 1,
                    consumers,
                    screenResults,
                    saveResults,
                    backtest_df,
                    testing=testing,
                )

        print(colorText.END)
        PKScanRunner.terminateAllWorkers(consumers, tasks_queue, testing)
        return screenResults, saveResults,backtest_df,scr
    
    def startWorkers(consumers):
        try:
            from pytest_cov.embed import cleanup_on_signal, cleanup_on_sigterm
        except ImportError:
            pass
        else:
            if sys.platform.startswith("win"):
                import signal

                cleanup_on_signal(signal.SIGBREAK)
            else:
                cleanup_on_sigterm()
        print(
            colorText.BOLD
            + colorText.FAIL
            + f"[+] Using Period:{PKScanRunner.configManager.period} and Duration:{PKScanRunner.configManager.duration} for scan! You can change this in user config."
            + colorText.END
        )
        for worker in consumers:
            worker.daemon = True
            worker.start()

    def terminateAllWorkers(consumers, tasks_queue, testing):
        # Exit all processes. Without this, it threw error in next screening session
        for worker in consumers:
            try:
                if testing: # pragma: no cover
                    if sys.platform.startswith("win"):
                        import signal

                        signal.signal(signal.SIGBREAK, PKScanRunner.shutdown)
                        sleep(1)
                    # worker.join()  # necessary so that the Process exists before the test suite exits (thus coverage is collected)
                # else:
                worker.terminate()
            except OSError as e: # pragma: no cover
                default_logger().debug(e, exc_info=True)
                # if e.winerror == 5:
                continue

        # Flush the queue so depending processes will end
        while True:
            try:
                _ = tasks_queue.get(False)
            except Exception as e:  # pragma: no cover
                # default_logger().debug(e, exc_info=True)
                break

    def shutdown(frame, signum):
        print("Shutting down for test coverage")

    def runScan(testing,numStocks,iterations,items,numStocksPerIteration,tasks_queue,results_queue,originalNumberOfStocks,backtest_df, *otherArgs,resultsReceivedCb=None):
        queueCounter = 0
        counter = 0
        shouldContinue = True
        lastNonNoneResult = None
        while numStocks:
            if counter == 0 and numStocks > 0:
                if queueCounter < int(iterations):
                    PKScanRunner.populateQueues(
                        items[
                            numStocksPerIteration
                            * queueCounter : numStocksPerIteration
                            * (queueCounter + 1)
                        ],
                        tasks_queue,
                        (queueCounter + 1 == int(iterations)) and ((queueCounter + 1)*int(iterations) == originalNumberOfStocks),
                    )
                else:
                    PKScanRunner.populateQueues(
                        items[
                            numStocksPerIteration
                            * queueCounter :
                        ],
                        tasks_queue,
                        True,
                    )
            result = results_queue.get()
            if result is not None:
                lastNonNoneResult = result
            numStocks -= 1
            if resultsReceivedCb is not None:
                shouldContinue, backtest_df = resultsReceivedCb(result, numStocks, backtest_df,*otherArgs)
            counter += 1
            # If it's being run under unit testing, let's wrap up if we find at least 1
            # stock or if we've already tried screening through 5% of the list.
            if (not shouldContinue) or (testing and counter >= int(numStocksPerIteration * 0.05)):
                break
            # Add to the queue when we're through 75% of the previously added items already
            if counter >= numStocksPerIteration: #int(numStocksPerIteration * 0.75):
                queueCounter += 1
                counter = 0
        return backtest_df, lastNonNoneResult
