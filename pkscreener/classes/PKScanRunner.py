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
import time
import pandas as pd
import multiprocessing
from time import sleep
from halo import Halo

from PKDevTools.classes import Archiver
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKGitFolderDownloader import downloadFolder
from PKDevTools.classes.PKMultiProcessorClient import PKMultiProcessorClient
from PKDevTools.classes.multiprocessing_logging import LogQueueReader
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.FunctionTimeouts import exit_after

from pkscreener.classes.StockScreener import StockScreener
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes.ConfigManager import parser, tools
from PKDevTools.classes.OutputControls import OutputControls
from PKNSETools.PKIntraDay import Intra_Day
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.ScreeningStatistics as ScreeningStatistics
import pkscreener.classes.Utility as Utility

class PKScanRunner:
    configManager = tools()
    configManager.getConfig(parser)
    fetcher = Fetcher.screenerStockDataFetcher(configManager)
    candlePatterns = CandlePatterns()
    tasks_queue = None
    results_queue = None
    scr = None
    consumers = None

    def initDataframes():
        screenResults = pd.DataFrame(
            columns=[
                "Stock",
                "Consol.",
                "Breakout",
                "LTP",
                "52Wk-H",
                "52Wk-L",
                "%Chng",
                "Volume",
                "MA-Signal",
                "RSI",
                "RSIi",
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
                "52Wk-H",
                "52Wk-L",
                "%Chng",
                "Volume",
                "MA-Signal",
                "RSI",
                "RSIi",
                "Trend",
                "Pattern",
                "CCI",
            ]
        )
        return screenResults, saveResults

    def initQueues(minimumCount=0,userPassedArgs=None):
        tasks_queue = multiprocessing.JoinableQueue()
        results_queue = multiprocessing.Queue()
        logging_queue = multiprocessing.Queue()

        totalConsumers = 1 if (userPassedArgs is not None and userPassedArgs.singlethread) else min(minimumCount, multiprocessing.cpu_count())
        if totalConsumers == 1:
            totalConsumers = 2  # This is required for single core machine
        # if PKScanRunner.configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
        #     totalConsumers -= 1
        return tasks_queue, results_queue, totalConsumers, logging_queue

    def populateQueues(items, tasks_queue, exit=False,userPassedArgs=None):
        # default_logger().debug(f"Unfinished items in task_queue: {tasks_queue.qsize()}")
        for item in items:
            tasks_queue.put(item)
        mayBePiped = userPassedArgs is not None and (userPassedArgs.monitor is not None or "|" in userPassedArgs.options)
        if exit and not mayBePiped:
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

    def addScansWithDefaultParams(userArgs, testing, testBuild, newlyListedOnly, downloadOnly, backtestPeriod, listStockCodes, menuOption, exchangeName,executeOption, volumeRatio, items, daysInPast,runOption=""):
        import json
        defaultOptionsDict = {}
        filePath = os.path.join(Archiver.get_user_data_dir(),"defaults.json")
        if not os.path.exists(filePath):
            fileDownloaded = Utility.tools.downloadSavedDefaultsFromServer("defaults.json")
        if not os.path.exists(filePath):
            return items
        with open(filePath,"r") as f:
            defaultOptionsDict = json.loads(f.read())
        for scanOption in defaultOptionsDict.keys():
            items = PKScanRunner.addStocksToItemList(userArgs=userArgs,
                                                     testing=testing,
                                                     testBuild=testBuild,
                                                     newlyListedOnly=newlyListedOnly,
                                                     downloadOnly=downloadOnly,
                                                     minRSI=defaultOptionsDict[scanOption]["minRSI"],
                                                     maxRSI=defaultOptionsDict[scanOption]["maxRSI"],
                                                     insideBarToLookback=defaultOptionsDict[scanOption]["insideBarToLookback"],
                                                     respChartPattern=defaultOptionsDict[scanOption]["respChartPattern"],
                                                     daysForLowestVolume=defaultOptionsDict[scanOption]["daysForLowestVolume"],
                                                     backtestPeriod=backtestPeriod,
                                                     reversalOption=defaultOptionsDict[scanOption]["reversalOption"],
                                                     maLength=defaultOptionsDict[scanOption]["maLength"],
                                                     listStockCodes=listStockCodes,
                                                     menuOption=menuOption,
                                                     exchangeName=exchangeName,
                                                     executeOption=int(scanOption.split(":")[2]), 
                                                     volumeRatio=volumeRatio,
                                                     items=items,
                                                     daysInPast=daysInPast,
                                                     runOption=scanOption)
        return items
    
    def addStocksToItemList(userArgs, testing, testBuild, newlyListedOnly, downloadOnly, minRSI, maxRSI, insideBarToLookback, respChartPattern, daysForLowestVolume, backtestPeriod, reversalOption, maLength, listStockCodes, menuOption, exchangeName,executeOption, volumeRatio, items, daysInPast,runOption=""):
        moreItems = [
                        (
                            runOption,
                            menuOption,
                            exchangeName,
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
                            userArgs,
                            daysInPast,
                            (
                                backtestPeriod
                                if menuOption == "B"
                                else PKScanRunner.configManager.effectiveDaysToLookback
                            ),
                            default_logger().level,
                            (menuOption in ["B", "G", "X", "S","C", "F"])
                            or (userArgs.backtestdaysago is not None),
                            # assumption is that fetcher.fetchStockData would be
                            # mocked to avoid calling yf.download again and again
                            PKScanRunner.fetcher.fetchStockData() if testing else None,
                        )
                        for stock in listStockCodes
                    ]
        items.extend(moreItems)
        return items

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
            choiceOption = selectedChoice[choice]
            if len(choiceOption) > 0 and ("," not in choiceOption and "." not in choiceOption):
                if len(choices) > 0:
                    choices = f"{choices}_"
                choices = f"{choices}{choiceOption}"
        if choices.endswith("_"):
            choices = choices[:-1]
        choices = f"{choices}{'_i' if isIntraday else ''}"
        return f'{choices.strip()}{"_IA" if userArgs is not None and userArgs.runintradayanalysis else ""}'

    def refreshDatabase(consumers,stockDictPrimary,stockDictSecondary):
        for worker in consumers:
            worker.objectDictionaryPrimary = stockDictPrimary
            worker.objectDictionarySecondary = stockDictSecondary
            worker.refreshDatabase = True
    
    # @Halo(text='', spinner='dots')
    def runScanWithParams(userPassedArgs,keyboardInterruptEvent,screenCounter,screenResultsCounter,stockDictPrimary,stockDictSecondary,testing, backtestPeriod, menuOption, executeOption, samplingDuration, items,screenResults, saveResults, backtest_df,scanningCb,tasks_queue, results_queue, consumers,logging_queue):
        if tasks_queue is None or results_queue is None or consumers is None:
            try:
                import tensorflow as tf
                with tf.device("/device:GPU:0"):
                    tasks_queue, results_queue, consumers,logging_queue = PKScanRunner.prepareToRunScan(menuOption,keyboardInterruptEvent,screenCounter, screenResultsCounter, stockDictPrimary,stockDictSecondary, items,executeOption,userPassedArgs)
            except: # pragma: no cover
                tasks_queue, results_queue, consumers,logging_queue = PKScanRunner.prepareToRunScan(menuOption,keyboardInterruptEvent,screenCounter, screenResultsCounter, stockDictPrimary,stockDictSecondary, items,executeOption,userPassedArgs)
                pass
            try:
                if logging_queue is not None:
                    log_queue_reader = LogQueueReader(logging_queue)
                    log_queue_reader.start()
            except: # pragma: no cover
                pass

        # if executeOption == 29: # Intraday Bid/Ask, for which we need to fetch data from NSE instead of yahoo
        #     intradayFetcher = Intra_Day("SBINEQN") # This will initialise the cookies etc.
        #     for consumer in consumers:
        #         consumer.intradayNSEFetcher = intradayFetcher
        # else:
        #     # Restart the workers because the run method may have exited from a previous run
        #     PKScanRunner.startWorkers(consumers)
        PKScanRunner.tasks_queue = tasks_queue
        PKScanRunner.results_queue = results_queue
        PKScanRunner.consumers = consumers
        screenResults, saveResults, backtest_df = scanningCb(
                    menuOption,
                    items,
                    PKScanRunner.tasks_queue,
                    PKScanRunner.results_queue,
                    len(items),
                    backtestPeriod,
                    samplingDuration - 1,
                    PKScanRunner.consumers,
                    screenResults,
                    saveResults,
                    backtest_df,
                    testing=testing,
                )

        OutputControls().printOutput(colorText.END)
        if userPassedArgs is not None and not userPassedArgs.testalloptions and (userPassedArgs.monitor is None and "|" not in userPassedArgs.options) and not userPassedArgs.options.upper().startswith("C"):
            # Don't terminate the multiprocessing clients if we're 
            # going to pipe the results from an earlier run
            # or we're running in monitoring mode
            PKScanRunner.terminateAllWorkers(userPassedArgs,consumers, tasks_queue, testing)
        else:
            for worker in consumers:
                worker.paused = True
                worker._clear()
        return screenResults, saveResults,backtest_df,tasks_queue, results_queue, consumers, logging_queue

    @exit_after(180) # Should not remain stuck starting the multiprocessing clients beyond this time
    @Halo(text='  [+] Creating multiple processes for faster processing...', spinner='dots')
    def prepareToRunScan(menuOption,keyboardInterruptEvent, screenCounter, screenResultsCounter, stockDictPrimary,stockDictSecondary, items, executeOption,userPassedArgs):
        tasks_queue, results_queue, totalConsumers, logging_queue = PKScanRunner.initQueues(len(items),userPassedArgs)
        scr = ScreeningStatistics.ScreeningStatistics(PKScanRunner.configManager, default_logger())
        exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday=PKScanRunner.configManager.isIntradayConfig())
        sec_cache_file = cache_file if "intraday_" in cache_file else f"intraday_{cache_file}"
        # Get RS rating stock value of the index
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        nsei_df = screenerStockDataFetcher().fetchStockData(PKScanRunner.configManager.baseIndex,PKScanRunner.configManager.period,PKScanRunner.configManager.duration,None,0,0,0,exchangeSuffix="",printCounter=False)
        rs_score_index = -1
        PKScanRunner.configManager.getConfig(parser)
        if nsei_df is not None:
            rs_score_index = scr.calc_relative_strength(nsei_df[::-1])
        consumers = [
                    PKMultiProcessorClient(
                        StockScreener().screenStocks,
                        tasks_queue,
                        results_queue,
                        logging_queue,
                        screenCounter,
                        screenResultsCounter,
                        # stockDictPrimary,
                        # stockDictSecondary,
                        (stockDictPrimary if menuOption not in ["C"] else None),
                        (stockDictSecondary if menuOption not in ["C"] else None),
                        PKScanRunner.fetcher.proxyServer,
                        keyboardInterruptEvent,
                        default_logger(),
                        PKScanRunner.fetcher,
                        PKScanRunner.configManager,
                        PKScanRunner.candlePatterns,
                        scr,
                        # None,
                        # None
                        (cache_file if (exists and menuOption in ["C"]) else None),
                        (sec_cache_file if (exists and menuOption in ["C"]) else None),
                        rs_strange_index=rs_score_index
                    )
                    for _ in range(totalConsumers)
                ]
        # if executeOption == 29: # Intraday Bid/Ask, for which we need to fetch data from NSE instead of yahoo
        try:
            intradayFetcher = None
            intradayFetcher = Intra_Day("SBINEQN") # This will initialise the cookies etc.
        except: # pragma: no cover
            pass
        for consumer in consumers:
            consumer.intradayNSEFetcher = intradayFetcher
        PKScanRunner.startWorkers(consumers)
        return tasks_queue,results_queue,consumers,logging_queue

    @exit_after(120) # Should not remain stuck starting the multiprocessing clients beyond this time
    @Halo(text='', spinner='dots')
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
        OutputControls().printOutput(
            colorText.FAIL
            + f"[+] Using Period:{colorText.END}{colorText.GREEN}{PKScanRunner.configManager.period}{colorText.END}{colorText.FAIL} and Duration:{colorText.END}{colorText.GREEN}{PKScanRunner.configManager.duration}{colorText.END}{colorText.FAIL} for scan! You can change this in user config."
            + colorText.END
        )
        start_time = time.time()
        for worker in consumers:
            sys.stdout.write(f"{round(time.time() - start_time)}.")
            worker.daemon = True
            worker.start()
        OutputControls().printOutput(f"Started all workers in {round(time.time() - start_time,4)}s")
        if OutputControls().enableMultipleLineOutput:
            # sys.stdout.write("\x1b[1A") # Move cursor up to hide the starting times we printed above
            OutputControls().moveCursorUpLines(1)

    @Halo(text='', spinner='dots')
    def terminateAllWorkers(userPassedArgs,consumers, tasks_queue, testing=False):
        shouldSuppress = (userPassedArgs is None) or (userPassedArgs is not None and not userPassedArgs.log)
        with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
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
                    # try:
                        # while worker.is_alive():
                    worker.terminate()
                    default_logger().debug("Worker terminated!")
                    # except: # pragma: no cover
                    #     continue
                except OSError as e: # pragma: no cover
                    default_logger().debug(e, exc_info=True)
                    # if e.winerror == 5:
                    continue

            # Flush the queue so depending processes will end
            while True:
                try:
                    _ = tasks_queue.get(False)
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as e:  # pragma: no cover
                    # default_logger().debug(e, exc_info=True)
                    break
        PKScanRunner.tasks_queue = None
        PKScanRunner.results_queue = None
        PKScanRunner.scr = None
        PKScanRunner.consumers = None

    def shutdown(frame, signum):
        OutputControls().printOutput("Shutting down for test coverage")

    # @Halo(text='', spinner='dots')
    def runScan(userPassedArgs,testing,numStocks,iterations,items,numStocksPerIteration,tasks_queue,results_queue,originalNumberOfStocks,backtest_df, *otherArgs,resultsReceivedCb=None):
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
                        userPassedArgs
                    )
                else:
                    PKScanRunner.populateQueues(
                        items[
                            numStocksPerIteration
                            * queueCounter :
                        ],
                        tasks_queue,
                        True,
                        userPassedArgs
                    )
            numStocks -= 1
            result = results_queue.get()
            if result is not None:
                lastNonNoneResult = result
            
            if resultsReceivedCb is not None:
                shouldContinue, backtest_df = resultsReceivedCb(result, numStocks, backtest_df,*otherArgs)
            counter += 1
            # If it's being run under unit testing, let's wrap up if we find at least 1
            # stock or if we've already tried screening through 5% of the list.
            if (not shouldContinue) or (testing and counter >= int(numStocksPerIteration * 0.05)):
                if PKScanRunner.consumers is not None:
                    consumers = PKScanRunner.consumers
                    for worker in consumers:
                        worker.paused = True
                        worker._clear()
                break
            # Add to the queue when we're through 75% of the previously added items already
            if counter >= numStocksPerIteration: #int(numStocksPerIteration * 0.75):
                queueCounter += 1
                counter = 0
        
        return backtest_df, lastNonNoneResult
