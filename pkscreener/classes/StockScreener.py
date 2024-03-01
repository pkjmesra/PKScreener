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
import logging
import sys
import time
import warnings

import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
# from PKDevTools.classes.log import tracelog
# from PKDevTools.classes.PKTimer import PKTimer
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.Fetcher import StockDataEmptyException
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.PKDateUtilities import PKDateUtilities

import pkscreener.classes.ScreeningStatistics as ScreeningStatistics
from pkscreener import Imports
from pkscreener.classes.CandlePatterns import CandlePatterns


class StockScreener:
    def __init__(self):
        self.isTradingTime = PKDateUtilities.isTradingTime()
        self.configManager = None

    # @tracelog
    def screenStocks(
        self,
        menuOption,
        executeOption,
        reversalOption,
        maLength,
        daysForLowestVolume,
        minRSI,
        maxRSI,
        respChartPattern,
        insideBarToLookback,
        totalSymbols,
        shouldCache,
        stock,
        newlyListedOnly,
        downloadOnly,
        volumeRatio,
        testbuild=False,
        printCounter=False,
        backtestDuration=0,
        backtestPeriodToLookback=30,
        logLevel=logging.NOTSET,
        portfolio=False,
        testData = None,
        hostRef=None,
    ):
        assert (
            hostRef is not None
        ), "hostRef argument must not be None. It should b an instance of PKMultiProcessorClient"
        configManager = hostRef.configManager
        self.configManager = configManager
        screeningDictionary, saveDictionary = self.initResultDictionaries()
        fullData = None
        processedData = None
        fetcher = hostRef.fetcher
        screener = hostRef.screener
        candlePatterns = hostRef.candlePatterns
        userArgsLog = printCounter
        start_time = time.time()
        try:
            with hostRef.processingCounter.get_lock():
                hostRef.processingCounter.value += 1

            volumeRatio, period = self.determineBasicConfigs(stock, newlyListedOnly, volumeRatio, logLevel, hostRef, configManager, screener, userArgsLog)
            # hostRef.default_logger.info(
            #     f"For stock:{stock}, stock exists in objectDictionary:{hostRef.objectDictionary.get(stock)}, cacheEnabled:{configManager.cacheEnabled}, isTradingTime:{self.isTradingTime}, downloadOnly:{downloadOnly}"
            # )
            data = self.getRelevantDataForStock(totalSymbols, shouldCache, stock, downloadOnly, printCounter, backtestDuration, hostRef, configManager, fetcher, period, testData)
            if len(data) == 0 or len(data) < backtestDuration:
                return None
            # hostRef.default_logger.info(f"Will pre-process data:\n{data.tail(10)}")
            fullData, processedData, data = self.getCleanedDataForDuration(backtestDuration, portfolio, screeningDictionary, saveDictionary, configManager, screener, data)
            def returnLegibleData():
                if backtestDuration == 0 or menuOption not in ["B"]:
                    return None
                elif (backtestDuration > 0 and backtestDuration <= configManager.maxBacktestWindow):
                    screener.validateMovingAverages(
                        processedData, screeningDictionary, saveDictionary, maRange=1.25
                    )
                    screener.findTrend(
                        processedData,
                        screeningDictionary,
                        saveDictionary,
                        daysToLookback=configManager.daysToLookback,
                        stockName=stock,
                    )
                    screener.find52WeekHighLow(
                            fullData, saveDictionary, screeningDictionary
                        )
                    return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )
            if newlyListedOnly:
                if not screener.validateNewlyListed(fullData, period):
                    raise ScreeningStatistics.NotNewlyListed

            if processedData.empty:
                return returnLegibleData()
            
            with SuppressOutput(suppress_stderr=(logLevel==logging.NOTSET), suppress_stdout=(not (printCounter or testbuild))):
                self.updateStock(stock, screeningDictionary, saveDictionary)
                
                self.performBasicLTPChecks(executeOption, screeningDictionary, saveDictionary, fullData, configManager, screener)
                hasMinVolumeRatio = self.performBasicVolumeChecks(executeOption, volumeRatio, screeningDictionary, saveDictionary, processedData, configManager, screener)
                
                isConfluence = False
                isInsideBar = 0
                isMaReversal = 0
                isIpoBase = False
                isMaSupport = False
                isLorentzian = False
                isVCP = False
                isVSA = False
                isNR = False
                isValidRsi = False
                isBuyingTrendline = False
                isMomentum = False
                mfiStake = 0
                fairValueDiff = 0
                consolidationValue = 0
                isBreaking = False
                isValidCci = False
                isVSA = False
                isCandlePattern = False
                isLowestVolume = False
                hasBbandsSqz = False

                isValidityCheckMet = self.performValidityCheckForExecuteOptions(executeOption,screener,fullData,screeningDictionary,saveDictionary,processedData)
                if not isValidityCheckMet:
                    return returnLegibleData()
                isShortTermBullish = (executeOption == 11 and isValidityCheckMet)
                if newlyListedOnly:
                    isIpoBase = screener.validateIpoBase(
                        stock, fullData, screeningDictionary, saveDictionary
                    )
                if executeOption in [1,2]:
                    isBreaking = screener.findBreakoutValue(
                        processedData,
                        screeningDictionary,
                        saveDictionary,
                        daysToLookback=configManager.daysToLookback,
                        alreadyBrokenout=(executeOption == 2),
                    )
                    if executeOption == 1:
                        isPotentialBreaking = screener.findPotentialBreakout(
                            fullData,
                            screeningDictionary,
                            saveDictionary,
                            daysToLookback=configManager.daysToLookback,
                        )
                        if not (isBreaking or isPotentialBreaking) or not hasMinVolumeRatio:
                            return returnLegibleData()
                    elif executeOption == 2:
                        if not (isBreaking) or not hasMinVolumeRatio:
                            return returnLegibleData()
                elif executeOption == 3:
                    consolidationValue = screener.validateConsolidation(
                        processedData,
                        screeningDictionary,
                        saveDictionary,
                        percentage=configManager.consolidationPercentage,
                    )
                    if ((consolidationValue == 0 or consolidationValue > configManager.consolidationPercentage)):
                        return returnLegibleData()
                elif executeOption == 4:
                    isLowestVolume = screener.validateLowestVolume(
                        processedData, daysForLowestVolume
                    )
                    if not isLowestVolume:
                        return returnLegibleData()
                elif executeOption == 5:
                    isValidRsi = screener.validateRSI(
                        processedData, screeningDictionary, saveDictionary, minRSI, maxRSI
                    )
                    if not isValidRsi:
                        return returnLegibleData()
                elif executeOption == 6:
                    if reversalOption == 6:
                        isNR = screener.validateNarrowRange(
                            processedData,
                            screeningDictionary,
                            saveDictionary,
                            nr=maLength if maLength is not None else 4,
                        )
                        if not isNR:
                            return returnLegibleData()
                    elif reversalOption == 5:
                        isVSA = screener.validateVolumeSpreadAnalysis(
                            processedData, screeningDictionary, saveDictionary
                        )
                        if not isVSA:
                            return returnLegibleData()
                    elif reversalOption == 4 and maLength is not None:
                        isMaSupport = screener.findReversalMA(
                            fullData, screeningDictionary, saveDictionary, maLength
                        )
                        if not isMaSupport:
                            return returnLegibleData()
                    elif reversalOption == 7:
                        if sys.version_info >= (3, 11):
                            isLorentzian = screener.validateLorentzian(
                                fullData,
                                screeningDictionary,
                                saveDictionary,
                                lookFor=maLength, # 1 =Buy, 2 =Sell, 3 = Any
                            )
                            if not isLorentzian:
                                return returnLegibleData()
                elif executeOption == 7:
                    if respChartPattern == 3:
                        isConfluence = screener.validateConfluence(
                            stock,
                            processedData,
                            screeningDictionary,
                            saveDictionary,
                            percentage=insideBarToLookback,
                            confFilter=(maLength if maLength > 0 else 3) # 1 = Conf up, 2 = Conf Down, 3 = all
                        )
                        if not isConfluence:
                            return returnLegibleData()
                    elif respChartPattern == 4:
                        isVCP = screener.validateVCP(
                            fullData, screeningDictionary, saveDictionary
                        )
                        if not isVCP:
                            return returnLegibleData()
                    elif respChartPattern == 5:
                        if Imports["scipy"]:
                            isBuyingTrendline = screener.findTrendlines(
                                fullData, screeningDictionary, saveDictionary
                            )
                            if not isBuyingTrendline:
                                return returnLegibleData()
                    elif respChartPattern == 6:
                        hasBbandsSqz = screener.findBbandsSqueeze(fullData, screeningDictionary, saveDictionary, filter=(maLength if maLength > 0 else 4))
                        if not hasBbandsSqz:
                            return returnLegibleData()
                        
                elif executeOption == 10:
                    isPriceRisingByAtLeast2Percent = (
                        screener.validatePriceRisingByAtLeast2Percent(
                            processedData, screeningDictionary, saveDictionary
                        )
                    )
                    if not isPriceRisingByAtLeast2Percent:
                        return returnLegibleData()
                # Must-run, but only at the end
                try:
                    # Only 'doji' and 'inside' is internally implemented by pandas_ta.
                    # Otherwise, for the rest of the candle patterns, they also need
                    # TA-Lib. So if TA-Lib is not available, it will throw exception
                    # We can live with no-patterns if user has not installed ta-lib
                    # yet. If ta-lib is available, PKTalib will load it automatically.
                    isCandlePattern = candlePatterns.findPattern(
                        processedData, screeningDictionary, saveDictionary
                    )
                except Exception as e:  # pragma: no cover
                    hostRef.default_logger.debug(e, exc_info=True)
                    screeningDictionary["Pattern"] = ""
                    saveDictionary["Pattern"] = ""

                try:
                    currentTrend = screener.findTrend(
                        processedData,
                        screeningDictionary,
                        saveDictionary,
                        daysToLookback=configManager.daysToLookback,
                        stockName=stock,
                    )
                    if backtestDuration == 0:
                        if executeOption == 21 and reversalOption in [3,5,6,7,8,9]:
                            # Find general trend
                            _,mfiStake,fairValueDiff = screener.findUptrend(
                                fullData,
                                screeningDictionary,
                                saveDictionary,
                                testbuild,
                                stock,
                                onlyMF=(executeOption == 21 and reversalOption in [5,6]),
                                hostData=data
                            )
                            hostRef.objectDictionary[stock] = data.to_dict("split")
                except np.RankWarning as e: # pragma: no cover 
                    hostRef.default_logger.debug(e, exc_info=True)
                    screeningDictionary["Trend"] = "Unknown"
                    saveDictionary["Trend"] = "Unknown"
                # CCI also uses "Trend" value from findTrend above.
                # So it must only be called after findTrend
                if executeOption == 8:
                    isValidCci = screener.validateCCI(
                        processedData, screeningDictionary, saveDictionary, minRSI, maxRSI
                    )
                    if not isValidCci:
                        return returnLegibleData()

                if not (isConfluence or isShortTermBullish or isMaSupport):
                    isMaReversal = screener.validateMovingAverages(
                        processedData, screeningDictionary, saveDictionary, maRange=1.25
                    )
                if executeOption == 6:
                    if reversalOption == 1 and not (str(saveDictionary["Pattern"]).split(",")[0]
                                                                    in CandlePatterns.reversalPatternsBullish
                                                                    or isMaReversal > 0):
                        return returnLegibleData()
                    elif reversalOption == 2 and not (str(saveDictionary["Pattern"]).split(",")[0]
                                                                    in CandlePatterns.reversalPatternsBearish
                                                                    or isMaReversal < 0):
                        return returnLegibleData()
                # validateInsideBar needs "Trend" to be already defined
                # ValidateInsideBar also needs "MA-Signal" to be setup
                if executeOption == 7 and respChartPattern < 3:
                    isInsideBar = screener.validateInsideBar(
                                processedData,
                                screeningDictionary,
                                saveDictionary,
                                chartPattern=respChartPattern,
                                daysToLookback=insideBarToLookback,
                            )
                    if isInsideBar ==0:
                        return returnLegibleData()

                if not (isLorentzian or (isInsideBar !=0) or isBuyingTrendline or isIpoBase or isNR or isVCP or isVSA):
                    isMomentum = screener.validateMomentum(
                        processedData, screeningDictionary, saveDictionary
                    )
                    if executeOption == 6 and reversalOption ==3 and not isMomentum:
                        return returnLegibleData()

                with hostRef.processingResultsCounter.get_lock():
                    hostRef.default_logger.debug(f"ExecuteOption:{executeOption}:{reversalOption}:{respChartPattern}:{maLength}. Elapsed: {time.time() - start_time}")
                    if (
                        (executeOption == 0)
                        or ((
                            (
                                (executeOption == 1 and (isBreaking or isPotentialBreaking))
                                or (executeOption == 2 and isBreaking)
                            )
                            and hasMinVolumeRatio
                        ))
                        or ((
                            (executeOption == 3)
                            and (
                                consolidationValue <= configManager.consolidationPercentage
                                and consolidationValue != 0
                            )
                        ))
                        or (executeOption == 4 and isLowestVolume)
                        or (executeOption == 5 and isValidRsi)
                        or ((executeOption == 6) and ((reversalOption == 1 and (
                                                                    str(saveDictionary["Pattern"]).split(",")[0]
                                                                    in CandlePatterns.reversalPatternsBullish
                                                                    or isMaReversal > 0
                                                                ))
                                                                or (reversalOption == 2 and (
                                                                    str(saveDictionary["Pattern"]).split(",")[0]
                                                                    in CandlePatterns.reversalPatternsBearish
                                                                    or isMaReversal < 0
                                                                ))
                                                                or (reversalOption == 3 and isMomentum)
                                                                or (reversalOption == 4 and isMaSupport)
                                                                or ((
                                                                    reversalOption == 5
                                                                    and isVSA
                                                                    and saveDictionary["Pattern"]
                                                                    in CandlePatterns.reversalPatternsBullish
                                                                ))
                                                                or (reversalOption == 6 and isNR)
                                                                or (reversalOption == 7 and isLorentzian)
                                                                ))
                        or ((executeOption == 7) and ((respChartPattern < 3 and isInsideBar > 0) 
                                                                  or (isConfluence)
                                                                  or (isIpoBase and newlyListedOnly and not respChartPattern < 3)
                                                                  or (isVCP)
                                                                  or (isBuyingTrendline))
                                                                  or (respChartPattern == 6 and hasBbandsSqz))
                        or (executeOption == 8 and isValidCci)
                        or (executeOption == 9 and hasMinVolumeRatio)
                        or (executeOption == 10 and isPriceRisingByAtLeast2Percent)
                        or (executeOption == 11 and isShortTermBullish)
                        or (executeOption in [12,13,14,15,16,17,18,19,20,23,24,25] and isValidityCheckMet)
                        or (executeOption == 21 and (mfiStake > 0 and reversalOption in [3,5]))
                        or (executeOption == 21 and (mfiStake < 0 and reversalOption in [6,7]))
                        or (executeOption == 21 and (fairValueDiff > 0 and reversalOption in [8]))
                        or (executeOption == 21 and (fairValueDiff < 0 and reversalOption in [9]))
                    ):
                        # Now screen for common ones to improve performance
                        if not (executeOption == 6 and reversalOption == 7):
                            if sys.version_info >= (3, 11):
                                with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                                    screener.validateLorentzian(
                                        fullData,
                                        screeningDictionary,
                                        saveDictionary,
                                        lookFor=maLength, # 1 =Buy, 2 =Sell, 3 = Any
                                    )
                        if not (executeOption in [1,2]):
                            screener.findBreakoutValue(
                                processedData,
                                screeningDictionary,
                                saveDictionary,
                                daysToLookback=configManager.daysToLookback,
                                alreadyBrokenout=(executeOption == 2),
                            )
                        if executeOption != 3:
                            screener.validateConsolidation(
                                processedData,
                                screeningDictionary,
                                saveDictionary,
                                percentage=configManager.consolidationPercentage,
                            )
                        if executeOption != 5:
                            screener.validateRSI(
                                processedData, screeningDictionary, saveDictionary, minRSI, maxRSI
                            )
                        screener.find52WeekHighLow(
                            fullData, saveDictionary, screeningDictionary
                        )
                        if executeOption != 8:
                            screener.validateCCI(
                                processedData, screeningDictionary, saveDictionary, minRSI, maxRSI
                            )
                        if executeOption != 21 and backtestDuration == 0:
                            # We don't need to have MFI or fair value data for backtesting because those
                            # are anyways only available for days in the past.
                            # For executeOption 21, we'd have already got the mfiStake and fairValueDiff
                            # Find general trend, MFI data and fairvalue only after the stocks are already screened
                            screener.findUptrend(
                                fullData,
                                screeningDictionary,
                                saveDictionary,
                                testbuild,
                                stock,
                                onlyMF=(executeOption == 21 and reversalOption in [5,6]),
                                hostData=data
                            )
                            hostRef.objectDictionary[stock] = data.to_dict("split")

                        hostRef.processingResultsCounter.value += 1
                        return (
                            screeningDictionary,
                            saveDictionary,
                            data,
                            stock,
                            backtestDuration,
                        )

        except KeyboardInterrupt: # pragma: no cover
            # Capturing Ctr+C Here isn't a great idea
            pass
        except StockDataEmptyException as e: # pragma: no cover
            hostRef.default_logger.debug(e, exc_info=True)
            pass
        except ScreeningStatistics.NotNewlyListed as e: # pragma: no cover
            hostRef.default_logger.debug(e, exc_info=True)
            pass
        except ScreeningStatistics.NotAStageTwoStock as e: # pragma: no cover
            # hostRef.default_logger.debug(e, exc_info=True)
            pass
        except ScreeningStatistics.NotEnoughVolumeAsPerConfig as e: # pragma: no cover 
            pass
        except ScreeningStatistics.DownloadDataOnly as e: # pragma: no cover
            # hostRef.default_logger.debug(e, exc_info=True)
            try:
                data = hostRef.objectDictionary.get(stock)
                if data is not None:
                    data = pd.DataFrame(data["data"], columns=data["columns"], index=data["index"])
                    screener.getMutualFundStatus(stock, hostData=data, force=True)
                    hostRef.objectDictionary[stock] = data.to_dict("split")
            except Exception as ex:
                hostRef.default_logger.debug(f"MFIStatus: {stock}:\n{ex}", exc_info=True)
                pass
            try:
                screener.getFairValue(stock,hostData=data, force=True)
                hostRef.objectDictionary[stock] = data.to_dict("split")
            except Exception as ex:
                hostRef.default_logger.debug(f"FairValue: {stock}:\n{ex}", exc_info=True)
                pass
            pass
        except ScreeningStatistics.LTPNotInConfiguredRange as e: # pragma: no cover
            # hostRef.default_logger.debug(e, exc_info=True)
            pass
        except KeyError as e: # pragma: no cover
            hostRef.default_logger.debug(e, exc_info=True)
            pass
        except OSError as e: # pragma: no cover
            pass
        except Exception as e:  # pragma: no cover
            hostRef.default_logger.debug(e, exc_info=True)
            if testbuild or printCounter:
                print(e)
                print(
                    colorText.FAIL
                    + (
                        "\n[+] Exception Occured while Screening %s! Skipping this stock.."
                        % stock
                    )
                    + colorText.END
                )
        return None

    def performValidityCheckForExecuteOptions(self,executeOption,screener,fullData,screeningDictionary,saveDictionary,processedData):
        isValid = True
        if executeOption not in [11,12,13,14,15,16,1,18,19,20,23,24,25]:
            return True
        if executeOption == 11:
            isValid = screener.validateShortTermBullish(
                fullData, screeningDictionary, saveDictionary
            )
        if executeOption == 12:
            isValid = (
                screener.validate15MinutePriceVolumeBreakout(fullData)
            )
        if executeOption == 13:
            isValid = screener.findBullishIntradayRSIMACD(
                fullData
            )
        if executeOption == 14:
            isValid = screener.findNR4Day(fullData)
        if executeOption == 15:
            isValid = screener.find52WeekLowBreakout(fullData)
        if executeOption == 16:
            isValid = screener.find10DaysLowBreakout(fullData)
        if executeOption == 17:
            isValid = screener.find52WeekHighBreakout(fullData)
        if executeOption == 18:
            isValid = screener.findAroonBullishCrossover(fullData)
        if executeOption == 19:
            isValid = screener.validateMACDHistogramBelow0(fullData)
        if executeOption == 20:
            isValid = screener.validateBullishForTomorrow(fullData)
        if executeOption == 23:
            isValid = screener.findBreakingoutNow(processedData, fullData, saveDictionary, screeningDictionary)
        if executeOption == 24:
            isValid = (
                screener.validateHigherHighsHigherLowsHigherClose(fullData)
            )
        if executeOption == 25:
            isValid = screener.validateLowerHighsLowerLows(processedData)
        return isValid        
                    
    def performBasicVolumeChecks(self, executeOption, volumeRatio, screeningDictionary, saveDictionary, processedData, configManager, screener):
        minVolume = configManager.minVolume / (
                    100 if configManager.isIntradayConfig() else 1
                )
        hasMinVolumeRatio, hasMinVolQty = screener.validateVolume(
                    processedData,
                    screeningDictionary,
                    saveDictionary,
                    volumeRatio=volumeRatio,
                    minVolume=minVolume,
                )
        if (not hasMinVolQty and executeOption > 0) or (executeOption == 9 and not hasMinVolumeRatio):
            raise ScreeningStatistics.NotEnoughVolumeAsPerConfig
        return hasMinVolumeRatio

    def performBasicLTPChecks(self, executeOption, screeningDictionary, saveDictionary, fullData, configManager, screener):
        isLtpValid, verifyStageTwo = screener.validateLTP(
                    fullData,
                    screeningDictionary,
                    saveDictionary,
                    minLTP=configManager.minLTP,
                    maxLTP=configManager.maxLTP,
                )
        if not isLtpValid:
            raise ScreeningStatistics.LTPNotInConfiguredRange
        if configManager.stageTwo and not verifyStageTwo and executeOption > 0:
            raise ScreeningStatistics.NotAStageTwoStock

    def updateStock(self, stock, screeningDictionary, saveDictionary):
        screeningDictionary["Stock"] = (
                    colorText.WHITE
                    + (
                        f"\x1B]8;;https://in.tradingview.com/chart?symbol=NSE%3A{stock}\x1B\\{stock}\x1B]8;;\x1B\\"
                    )
                    + colorText.END
                )
        saveDictionary["Stock"] = stock

    def getCleanedDataForDuration(self, backtestDuration, portfolio, screeningDictionary, saveDictionary, configManager, screener, data):
        fullData = None
        processedData = None
        if backtestDuration == 0:
            fullData, processedData = screener.preprocessData(
                    data, daysToLookback=configManager.effectiveDaysToLookback
                )
            if portfolio:
                data = data[::-1]
                screener.validateLTPForPortfolioCalc(
                        data, screeningDictionary, saveDictionary,requestedPeriod=backtestDuration
                    )
                data = data[::-1]
        else:
            if data is None or fullData is None or processedData is None:
                    # data will have the oldest date at the top and the most recent
                    # date will be at the bottom
                    # We want to have the nth day treated as today when pre-processing where n = backtestDuration row from the bottom
                inputData = data.head(len(data) - backtestDuration)
                    # imputData will have the last row as the date for which the entire calculation
                    # and prediction is being done
                data = data.tail(
                        backtestDuration + 1
                    )  # .head(backtestPeriodToLookback+1)
                    # Let's get today's data
                if portfolio:
                    screener.validateLTPForPortfolioCalc(
                            data, screeningDictionary, saveDictionary,requestedPeriod=backtestDuration
                        )
                    # data has the last row from inputData at the top.
                fullData, processedData = screener.preprocessData(
                        inputData, daysToLookback=configManager.daysToLookback
                    )
                
        return fullData,processedData,data

    def getRelevantDataForStock(self, totalSymbols, shouldCache, stock, downloadOnly, printCounter, backtestDuration, hostRef, configManager, fetcher, period, testData=None):
        hostData = hostRef.objectDictionary.get(stock)
        data = None
        if (
                not shouldCache
                or downloadOnly
                or self.isTradingTime
                or hostData is None
            ):
            start = None
            if (period == '1d' or configManager.duration[-1] == "m") and backtestDuration > 0:
                start = PKDateUtilities.nthPastTradingDateStringFromFutureDate(backtestDuration)
                end = start
            if testData is not None:
                data = testData
            else:
                data = fetcher.fetchStockData(
                        stock,
                        period,
                        configManager.duration,
                        hostRef.proxyServer,
                        hostRef.processingResultsCounter,
                        hostRef.processingCounter,
                        totalSymbols,
                        start=start,
                        end=start
                    )
                if hostData is not None and data is not None:
                    # During the market trading hours, we don't want to go for MFI/FV value fetching
                    # So let's copy the old saved ones.
                    try:
                        data["MF"] = hostData["MF"]
                        data["MF_Date"] = hostData["MF_Date"]
                    except KeyError:
                        pass
                    try:
                        data["FII"] = hostData["FII"]
                        data["FII_Date"] = hostData["FII_Date"]
                    except KeyError:
                        pass
                    try:
                        data["FairValue"] = hostData["FairValue"]
                    except KeyError:
                        pass
            if (
                    (shouldCache and not self.isTradingTime and (hostData is None))
                    or downloadOnly
                ) or (
                    shouldCache and hostData is None
                ):  # and backtestDuration == 0 # save only if we're NOT backtesting
                if start is None and data is not None:
                    hostRef.objectDictionary[stock] = data.to_dict("split")
                if downloadOnly:
                    with hostRef.processingResultsCounter.get_lock():
                        hostRef.processingResultsCounter.value += 1
                    raise ScreeningStatistics.DownloadDataOnly
                else:
                    hostData = hostRef.objectDictionary.get(stock)
        else:
            self.printProcessingCounter(totalSymbols, stock, printCounter, hostRef)
            data = hostData
            data = pd.DataFrame(
                    data["data"], columns=data["columns"], index=data["index"]
                )
            
        return data

    def determineBasicConfigs(self, stock, newlyListedOnly, volumeRatio, logLevel, hostRef, configManager, screener, userArgsLog):
        if userArgsLog:
            self.setupLoggers(hostRef, screener, logLevel, stock)
        period = configManager.period
        if volumeRatio <= 0:
            volumeRatio = configManager.volumeRatio
            # Data download adjustment for Newly Listed only feature
        if newlyListedOnly:
            if int(configManager.period[:-1]) > 250:
                period = "250d"
            else:
                period = configManager.period
        return volumeRatio,period

    def printProcessingCounter(self, totalSymbols, stock, printCounter, hostRef):
        if printCounter:
            try:
                print(
                            colorText.BOLD
                            + colorText.GREEN
                            + (
                                "[%d%%] Screened %d, Found %d. Fetching data & Analyzing %s..."
                                % (
                                    int(
                                        (hostRef.processingCounter.value / totalSymbols)
                                        * 100
                                    ),
                                    hostRef.processingCounter.value,
                                    hostRef.processingResultsCounter.value,
                                    stock,
                                )
                            )
                            + colorText.END,
                            end="",
                        )
                print(
                            colorText.BOLD
                            + colorText.GREEN
                            + "=> Done!"
                            + colorText.END,
                            end="\r",
                            flush=True,
                        )
            except ZeroDivisionError as e:
                hostRef.default_logger.debug(e, exc_info=True)
                pass
            sys.stdout.write("\r\033[K")
    
    def setupLoggers(self, hostRef, screener, logLevel, stock):
        # Set the loglevels for both the caller and screener
        # Also add handlers that are specific to this sub-process which
        # will co ntinue with the screening. Each sub-process would have
        # its own logger but going into the same file/console > to that
        # of the parent logger.
        if hostRef.default_logger.level > 0:
            return
        hostRef.default_logger.level = logLevel
        screener.default_logger.level = logLevel
        hostRef.default_logger.addHandlers(log_file_path=None, levelname=logLevel)
        screener.default_logger.addHandlers(log_file_path=None, levelname=logLevel)
        hostRef.default_logger.info(f"Beginning the stock screening for stock:{stock}")

    def initResultDictionaries(self):
        periods = self.configManager.periodsRange
        columns = [
            "Stock",
            "LTP",
            "%Chng",
            "52Wk H",
            "52Wk L",
            "RSI",
            "Volume",
            "22-Pd %",
            "Consol.",
            "Breakout",
            "MA-Signal",
            "Trend",
            "Pattern",
            "CCI",
            "FairValue"
        ]
        screeningDictionary = {
            "Stock": "",
            "LTP": 0,
            "%Chng": 0,
            "52Wk H": 0,
            "52Wk L": 0,
            "RSI": 0,
            "Volume": "",
            "22-Pd %": "",
            "Consol.": "Range:0%",
            "Breakout": "BO: 0 R: 0",
            "MA-Signal": "",
            "Trend": "",
            "Pattern": "",
            "CCI": 0,
            "FairValue": "-"
        }
        saveDictionary = {
            "Stock": "",
            "LTP": 0,
            "%Chng": 0,
            "52Wk H": 0,
            "52Wk L": 0,
            "RSI": 0,
            "Volume": "",
            "22-Pd %": "",
            "Consol.": "Range:0%",
            "Breakout": "BO: 0 R: 0",
            "MA-Signal": "",
            "Trend": "",
            "Pattern": "",
            "CCI": 0,
            "FairValue": "-"
        }
        for prd in periods:
            columns.append(f"LTP{prd}")
            columns.append(f"Growth{prd}")
            screeningDictionary[f"LTP{prd}"] = np.nan
            saveDictionary[f"LTP{prd}"] = np.nan
            screeningDictionary[f"Growth{prd}"] = np.nan
            saveDictionary[f"Growth{prd}"] = np.nan

        screenResults = pd.DataFrame(columns=columns)

        return screeningDictionary, saveDictionary
