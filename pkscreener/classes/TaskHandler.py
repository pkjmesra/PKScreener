
import multiprocessing
import sys

import pandas as pd

import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes import ConfigManager
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger
from pkscreener.classes.ParallelProcessing import StockConsumer
from pkscreener.classes.PKMultiProcessorClient import PKMultiProcessorClient
from pkscreener.classes.TaskInputs import taskInputs

# usage: pkscreenercli.exe [-h] [-a ANSWERDEFAULT] [-c CRONINTERVAL] [-d] [-e] [-o OPTIONS] [-p] [-t] [-l] [-v]
# pkscreenercli.exe: error: unrecognized arguments: --multiprocessing-fork parent_pid=4620 pipe_handle=708
# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith("win"):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    print("Contact developer! Your platform does not support multiprocessing!")
    input("Exiting now...")
    sys.exit(0)

configManager = ConfigManager.tools()

class taskHandler:
    def __init__(self,executeOption=None,siblingsCount=1,configManager=None,stocks=[],
                 stockDict=None,containerName=None,containerTitle=None,dataCallbackHandler=None,progressCallbackHandler=None):
        self.executeOption = executeOption
        self.siblingsCount = siblingsCount
        self.stocks = stocks
        self.containerName = containerName
        self.containerTitle = containerTitle
        self.stockDict = stockDict
        self.screenCounter = multiprocessing.Value("i", 1)
        self.screenResultsCounter = multiprocessing.Value("i", 0)
        self.running = False
        self.dataCallbackHandler = dataCallbackHandler
        self.progressCallbackHandler = progressCallbackHandler
        self.keyboardInterruptEvent = multiprocessing.Manager().Event()
        self.configManager = configManager
        self.fetcher = Fetcher.tools(self.configManager)
        self.inputParams = self._taskInputsForScan()
        self.tasks_queue,self.results_queue,self.processCount = self._processorAndQueuePair(len(stocks))
        self.processors = self._processors()

    def tick(self):
        self.screenCounter = multiprocessing.Value("i", 1)
        self.screenResultsCounter = multiprocessing.Value("i", 0)
        self.screenResults,self.saveResults = self._initDataframes()
        self._startWorkers()
        self._populateTaskQueue()
        self._runScanner()

    def _processorAndQueuePair(self,minimumStockCount=0):
        tasks_queue = multiprocessing.JoinableQueue()
        results_queue = multiprocessing.Queue()
        processCount = min(minimumStockCount, multiprocessing.cpu_count()/self.siblingsCount)
        if processCount == 1:
            processCount = 2  # This is required for single core machine
        if configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
            processCount -= 1
        return tasks_queue, results_queue, int(processCount)

    def _taskInputsForScan(self):
        inputs = [taskInputs(executeOption=self.executeOption,stock=stock,stocksCount=len(self.stocks),configManager=self.configManager) 
                  for stock in self.stocks]
        inputParams = [input.inputParams() for input in inputs]
        return inputParams

    def _populateTaskQueue(self):
        for item in self.inputParams:
            self.tasks_queue.put(item)

    def _processors(self):
        processors = [
            PKMultiProcessorClient(
                StockConsumer().screenStocks,
                self.tasks_queue,
                self.results_queue,
                self.screenCounter,
                self.screenResultsCounter,
                self.stockDict,
                self.fetcher.proxyServer,
                self.keyboardInterruptEvent,
                default_logger(),
            )
            for _ in range(int(self.processCount))
        ]
        return processors

    def _startWorkers(self):
        if not self.running:
            self.running = True
            for worker in self.processors:
                worker.daemon = True
                worker.start()

    def stop(self):
        # Exit all processes. Without this, it threw error in next screening session
        for worker in self.processors:
            try:
                worker.terminate()
            except OSError as e:
                if e.winerror == 5:
                    continue
            except Exception:
                continue
        # Flush the queue so depending processes will end
        while True:
            try:
                _ = self.tasks_queue.get(False)
            except Exception:
                break
        self.running = False

    def _runScanner(self):
        try:
            numStocks = len(self.stocks)
            lstscreen = []
            while numStocks:
                result = self.results_queue.get()
                if result is not None:
                    lstscreen.insert(0,result[0])
                    # create extension
                    df_extendedscreen = pd.DataFrame(lstscreen, columns=self.screenResults.columns)
                    self.screenResults = pd.concat([df_extendedscreen, self.screenResults],
                                                   ignore_index=True) if len(self.screenResults) > 0 else df_extendedscreen
                    self.dataCallbackHandler(self.screenResults[["Stock","%Chng","Volume","LTP"]],self.containerName,self.containerTitle)
                numStocks -= 1
                self.progressCallbackHandler(f"[{colorText.GREEN}{len(self.stocks)-numStocks}{colorText.END}/{colorText.FAIL}{len(self.stocks)}{colorText.END} Done]. Found {colorText.GREEN}{len(self.screenResults)}{colorText.END} Stocks.",
                                             self.containerName)
        except KeyboardInterrupt:
            try:
                self.keyboardInterruptEvent.set()
                self.stop()
            except KeyboardInterrupt:
                self.stop()
                pass

    def _initDataframes(self):
        screenResults = pd.DataFrame(
            columns=[
                "Stock",
                "Consol.",
                "Breakout",
                "LTP",
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