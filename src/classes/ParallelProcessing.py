
'''
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi, Swar Patel
 *  Created             :   18/05/2021
 *  Description         :   Class for managing multiprocessing
'''

import multiprocessing
import pandas as pd
import numpy as np
import sys
import os
import pytz
import logging
from queue import Empty
from datetime import datetime
from classes import Imports
import classes.Fetcher as Fetcher
import classes.Screener as Screener
import classes.Utility as Utility
from classes.CandlePatterns import CandlePatterns
from classes.ColorText import colorText
from classes.SuppressOutput import SuppressOutput
from classes.log import default_logger, tracelog
import classes.Archiver as Archiver

if sys.platform.startswith('win'):
    import multiprocessing.popen_spawn_win32 as forking
else:
    import multiprocessing.popen_fork as forking

class StockConsumer(multiprocessing.Process):

    def __init__(self, task_queue, result_queue, screenCounter, screenResultsCounter, stockDict, proxyServer, keyboardInterruptEvent, default_logger):
        multiprocessing.Process.__init__(self)
        self.multiprocessingForWindows()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.screenCounter = screenCounter
        self.screenResultsCounter = screenResultsCounter
        self.stockDict = stockDict
        self.proxyServer = proxyServer
        self.keyboardInterruptEvent = keyboardInterruptEvent
        self.isTradingTime = Utility.tools.isTradingTime()
        self.default_logger = default_logger
        self.default_logger.info('StockConsumer initialized.')

    def run(self):
        # while True:
        try:
            while not self.keyboardInterruptEvent.is_set():
                try:
                    next_task = self.task_queue.get()
                except Empty as e:
                    self.default_logger.debug(e, exc_info=True)
                    continue
                if next_task is None:
                    self.default_logger.info('No next task in queue')
                    self.task_queue.task_done()
                    break
                answer = self.screenStocks(*(next_task))
                self.task_queue.task_done()
                self.default_logger.info(f'Task done. Result:{answer}')
                self.result_queue.put(answer)
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
            sys.exit(0)

    @tracelog
    def screenStocks(self, executeOption, reversalOption, maLength, daysForLowestVolume, minRSI, maxRSI, respChartPattern, insideBarToLookback, totalSymbols,
                     configManager, fetcher, screener, candlePatterns, stock, newlyListedOnly, downloadOnly, volumeRatio, testbuild=False, printCounter=False,backtestDuration=0, logLevel=logging.NOTSET):
        screenResults = pd.DataFrame(columns=[
            'Stock', 'Consol.', 'Breakout', 'MA-Signal', 'Volume', 'LTP','%Chng', 'RSI', 'Trend', 'Pattern', 'CCI'])
        screeningDictionary = {'Stock': "", 'Consol.': "",  'Breakout': "",
                               'MA-Signal': "", 'Volume': "", 'LTP': 0, '%Chng':0, 'RSI': 0, 'Trend': "", 'Pattern': "", 'CCI': 0}
        saveDictionary = {'Stock': "", 'Consol.': "", 'Breakout': "",
                          'MA-Signal': "", 'Volume': "", 'LTP': 0, '%Chng':0, 'RSI': 0, 'Trend': "", 'Pattern': "", 'CCI': 0}

        try:
            self.default_logger.level = logLevel
            screener.default_logger.level = logLevel
            self.default_logger.addHandlers(log_file_path=None, levelname=logLevel)
            screener.default_logger.addHandlers(log_file_path=None, levelname=logLevel)
            self.default_logger.info(f'Beginning the stock screening for stock:{stock}')
            period = configManager.period
            if volumeRatio <= 0:
                volumeRatio = configManager.volumeRatio
            # Data download adjustment for Newly Listed only feature
            if newlyListedOnly:
                if int(configManager.period[:-1]) > 250:
                    period = '250d'
                else:
                    period = configManager.period
            self.default_logger.info(f'For stock:{stock}, stock exists in stockdict:{self.stockDict.get(stock)}, cacheEnabled:{configManager.cacheEnabled}, isTradingTime:{self.isTradingTime}, downloadOnly:{downloadOnly}')
            if (self.stockDict.get(stock) is None) or (configManager.cacheEnabled is False) or self.isTradingTime or downloadOnly:
                data = fetcher.fetchStockData(stock,
                                              period,
                                              configManager.duration,
                                              self.proxyServer,
                                              self.screenResultsCounter,
                                              self.screenCounter,
                                              totalSymbols)
                self.default_logger.info(f'Fetcher fetched stock data:\n{data}')
                if configManager.cacheEnabled is True and not self.isTradingTime and (self.stockDict.get(stock) is None) or downloadOnly:
                    self.stockDict[stock] = data.to_dict('split')
                    self.default_logger.info(f'Stock data saved:\n{self.stockDict[stock]}')
                    if downloadOnly:
                        raise Screener.DownloadDataOnly
            else:
                if printCounter:
                    try:
                        print(colorText.BOLD + colorText.GREEN + ("[%d%%] Screened %d, Found %d. Fetching data & Analyzing %s..." % (
                            int((self.screenCounter.value / totalSymbols) * 100), self.screenCounter.value, self.screenResultsCounter.value, stock)) + colorText.END, end='')
                        print(colorText.BOLD + colorText.GREEN + "=> Done!" +
                              colorText.END, end='\r', flush=True)
                    except ZeroDivisionError as e:
                        self.default_logger.debug(e, exc_info=True)
                        pass
                    sys.stdout.write("\r\033[K")
                data = self.stockDict.get(stock)
                data = pd.DataFrame(
                    data['data'], columns=data['columns'], index=data['index'])
            if len(data) == 0:
                return None
            self.default_logger.info(f'Will pre-process data:\n{data.tail(10)}')
            if backtestDuration == 0:
                fullData, processedData = screener.preprocessData(
                    data, daysToLookback=configManager.daysToLookback)
            else:
                # data = Archiver.readData(f'RD_{Utility.tools.tradingDate()}_{stock}.pkl')
                fullData = Archiver.readData(f'FD_{Utility.tools.tradingDate()}_{stock}.pkl')
                processedData = Archiver.readData(f'PD_{Utility.tools.tradingDate()}_{stock}.pkl')
                if data is None or fullData is None or processedData is None:
                    inputData = (data if backtestDuration == 0 else data.head(400-backtestDuration))
                    fullData, processedData = screener.preprocessData(
                        inputData, daysToLookback=configManager.daysToLookback)
                    Archiver.saveData(data, f'RD_{Utility.tools.tradingDate()}_{stock}.pkl')
                    Archiver.saveData(fullData, f'FD_{Utility.tools.tradingDate()}_{stock}.pkl')
                    Archiver.saveData(processedData, f'PD_{Utility.tools.tradingDate()}_{stock}.pkl')
            self.default_logger.info(f'Finished pre-processing. processedData:\n{data}\nfullData:{fullData}\n')
            if newlyListedOnly:
                if not screener.validateNewlyListed(fullData, period):
                    raise Screener.NotNewlyListed

            with self.screenCounter.get_lock():
                self.screenCounter.value += 1
                self.default_logger.info(f'Processing {stock} in {self.screenCounter.value}th counter')
            if not processedData.empty:
                screeningDictionary['Stock'] = colorText.BOLD + \
                     colorText.BLUE + f'\x1B]8;;https://in.tradingview.com/chart?symbol=NSE%3A{stock}\x1B\\{stock}\x1B]8;;\x1B\\' + colorText.END
                saveDictionary['Stock'] = stock
                consolidationValue = screener.validateConsolidation(
                    processedData, screeningDictionary, saveDictionary, percentage=configManager.consolidationPercentage)
                isMaReversal = screener.validateMovingAverages(
                    processedData, screeningDictionary, saveDictionary, maRange=1.25)
                isShortTermBullish = screener.validateShortTermBullish(
                    fullData.copy(), screeningDictionary, saveDictionary)
                is15MinutePriceVolumeBreakout = screener.validate15MinutePriceVolumeBreakout(fullData.copy())
                isBullishIntradayRSIMACD = screener.findBullishIntradayRSIMACD(fullData.copy())
                isNR4Day = screener.findNR4Day(fullData.copy())
                isVolumeHigh = screener.validateVolume(
                    processedData, screeningDictionary, saveDictionary, volumeRatio= volumeRatio)
                isBreaking = screener.findBreakout(
                    processedData, screeningDictionary, saveDictionary, daysToLookback=configManager.daysToLookback)
                isLtpValid = screener.validateLTP(
                    fullData, screeningDictionary, saveDictionary, minLTP=configManager.minLTP, maxLTP=configManager.maxLTP)
                if executeOption == 4:
                    isLowestVolume = screener.validateLowestVolume(processedData, daysForLowestVolume)
                else:
                    isLowestVolume = False
                isValidRsi = screener.validateRSI(
                    processedData, screeningDictionary, saveDictionary, minRSI, maxRSI)
                try:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        currentTrend = screener.findTrend(
                            processedData,
                            screeningDictionary,
                            saveDictionary,
                            daysToLookback=configManager.daysToLookback,
                            stockName=stock)
                except np.RankWarning as e:
                    self.default_logger.debug(e, exc_info=True)
                    screeningDictionary['Trend'] = 'Unknown'
                    saveDictionary['Trend'] = 'Unknown'
                isValidCci = screener.validateCCI(
                    processedData, screeningDictionary, saveDictionary, minRSI, maxRSI)
                isCandlePattern=False
                try:
                    # Only 'doji' and 'inside' is internally implemented by pandas_ta.
                    # Otherwise, for the rest of the candle patterns, they also need
                    # TA-Lib. So if TA-Lib is not available, it will throw exception
                    # We can live with no-patterns if user has not installed ta-lib
                    # yet. If ta-lib is available, PKTalib will load it automatically.
                    isCandlePattern = candlePatterns.findPattern(
                    processedData, screeningDictionary, saveDictionary)
                except Exception as e:
                    self.default_logger.debug(e, exc_info=True)
                    screeningDictionary['Pattern'] = ''
                    saveDictionary['Pattern'] = ''
                isConfluence = False
                isInsideBar = False
                isIpoBase = False
                if newlyListedOnly:
                    isIpoBase = screener.validateIpoBase(stock, fullData, screeningDictionary, saveDictionary)
                if respChartPattern == 3 and executeOption == 7:
                    isConfluence = screener.validateConfluence(stock, processedData, screeningDictionary, saveDictionary, percentage=insideBarToLookback)
                else:
                    isInsideBar = screener.validateInsideBar(processedData, screeningDictionary, saveDictionary, chartPattern=respChartPattern, daysToLookback=insideBarToLookback)
                
                with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                    if maLength is not None and executeOption == 6 and reversalOption == 6:
                        isNR = screener.validateNarrowRange(processedData, screeningDictionary, saveDictionary, nr=maLength)
                    else:
                        isNR = screener.validateNarrowRange(processedData, screeningDictionary, saveDictionary)
                
                isMomentum = screener.validateMomentum(processedData, screeningDictionary, saveDictionary)
                isPriceRisingByAtLeast2Percent = screener.validatePriceRisingByAtLeast2Percent(processedData, screeningDictionary, saveDictionary)
                
                isVSA = False
                if not (executeOption == 7 and respChartPattern < 3):
                    isVSA = screener.validateVolumeSpreadAnalysis(processedData, screeningDictionary, saveDictionary)
                if maLength is not None and executeOption == 6 and reversalOption == 4:
                    isMaSupport = screener.findReversalMA(fullData, screeningDictionary, saveDictionary, maLength)

                isVCP = False
                if respChartPattern == 4:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        isVCP = screener.validateVCP(fullData, screeningDictionary, saveDictionary)

                isBuyingTrendline = False
                if executeOption == 7 and respChartPattern == 5:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        if Imports['scipy']:
                            isBuyingTrendline = screener.findTrendlines(fullData, screeningDictionary, saveDictionary)

                with self.screenResultsCounter.get_lock():
                    self.default_logger.info(f'Processing results for {stock} in {self.screenResultsCounter.value}th results counter')
                    if executeOption == 0:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if (executeOption == 1 or executeOption == 2) and isBreaking and isVolumeHigh and isLtpValid:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if (executeOption == 1 or executeOption == 3) and (consolidationValue <= configManager.consolidationPercentage and consolidationValue != 0) and isLtpValid:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 4 and isLtpValid and isLowestVolume:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 5 and isLtpValid and isValidRsi:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 6 and isLtpValid:
                        if reversalOption == 1:
                            if saveDictionary['Pattern'] in CandlePatterns.reversalPatternsBullish or isMaReversal > 0:
                                self.screenResultsCounter.value += 1
                                return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        elif reversalOption == 2:
                            if saveDictionary['Pattern'] in CandlePatterns.reversalPatternsBearish or isMaReversal < 0:
                                self.screenResultsCounter.value += 1
                                return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        elif reversalOption == 3 and isMomentum:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        elif reversalOption == 4 and isMaSupport:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        elif reversalOption == 5 and isVSA and saveDictionary['Pattern'] in CandlePatterns.reversalPatternsBullish:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        elif reversalOption == 6 and isNR:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 7 and isLtpValid:
                        if respChartPattern < 3 and isInsideBar:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        if isConfluence:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        if isIpoBase and newlyListedOnly and not respChartPattern < 3:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        if isVCP:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                        if isBuyingTrendline:
                            self.screenResultsCounter.value += 1
                            return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 8 and isLtpValid and isValidCci:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 9 and isVolumeHigh:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 10 and isPriceRisingByAtLeast2Percent:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 11 and isShortTermBullish:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 12 and is15MinutePriceVolumeBreakout:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 13 and isBullishIntradayRSIMACD:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    if executeOption == 14 and isNR4Day:
                        self.screenResultsCounter.value += 1
                        return screeningDictionary, saveDictionary, data, stock, backtestDuration 
                    
        except KeyboardInterrupt:
            # Capturing Ctr+C Here isn't a great idea
            pass
        except Fetcher.StockDataEmptyException as e:
            self.default_logger.debug(e, exc_info=True)
            pass
        except Screener.NotNewlyListed as e:
            self.default_logger.debug(e, exc_info=True)
            pass
        except Screener.DownloadDataOnly as e:
            self.default_logger.debug(e, exc_info=True)
            pass
        except KeyError as e:
            self.default_logger.debug(e, exc_info=True)
            pass
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
            if testbuild or printCounter:
                print(e)
                print(colorText.FAIL +
                      ("\n[+] Exception Occured while Screening %s! Skipping this stock.." % stock) + colorText.END)
        return None

    def multiprocessingForWindows(self):
        if sys.platform.startswith('win'):

            class _Popen(forking.Popen):
                def __init__(self, *args, **kw):
                    if hasattr(sys, 'frozen'):
                        os.putenv('_MEIPASS2', sys._MEIPASS)
                    try:
                        super(_Popen, self).__init__(*args, **kw)
                    finally:
                        if hasattr(sys, 'frozen'):
                            if hasattr(os, 'unsetenv'):
                                os.unsetenv('_MEIPASS2')
                            else:
                                os.putenv('_MEIPASS2', '')

            forking.Popen = _Popen
