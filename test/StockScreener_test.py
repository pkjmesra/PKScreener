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
import pytest
import logging
import pandas as pd
from unittest.mock import MagicMock, patch

from pkscreener.classes.StockScreener import StockScreener

@pytest.fixture
def stock_consumer():
    return StockScreener()

@pytest.mark.skip(reason="API has changed")
def test_screenStocks(stock_consumer):
    hostRef = MagicMock()
    hostRef.configManager.period = '1d'
    hostRef.configManager.duration = '1d'
    hostRef.configManager.volumeRatio = 1
    hostRef.configManager.consolidationPercentage = 10
    hostRef.proxyServer = None
    hostRef.processingResultsCounter.value = 0
    hostRef.processingCounter.value = 0
    hostRef.objectDictionary.get.return_value = None
    hostRef.fetcher.fetchStockData.return_value = pd.DataFrame(data=[1, 2, 3], columns=['A'], index=[0, 1, 2])
    hostRef.objectDictionary.__getitem__.return_value = None
    hostRef.processingResultsCounter.get_lock.return_value = MagicMock()
    hostRef.processingResultsCounter.get_lock.return_value.__enter__.return_value = None
    hostRef.processingResultsCounter.get_lock.return_value.__exit__.return_value = None
    hostRef.processingCounter.get_lock.return_value = MagicMock()
    hostRef.processingCounter.get_lock.return_value.__enter__.return_value = None
    hostRef.processingCounter.get_lock.return_value.__exit__.return_value = None
    hostRef.screener.preprocessData = MagicMock(return_value=(pd.DataFrame(data=[1, 2, 3], columns=['A'], index=[0, 1, 2]), pd.DataFrame(data=[1, 2, 3], columns=['A'], index=[0, 1, 2])))
    stock_consumer.setupLoggers = MagicMock()
    stock_consumer.initResultDictionaries = MagicMock(return_value=({}, {}))
    stock_consumer.initResultDictionaries.return_value = ({}, {})
    hostRef.screener.processingResultsCounter = MagicMock()
    for bool_value in [True,False]:
        hostRef.screener.validateNewlyListed = MagicMock(return_value=bool_value)
        hostRef.screener.validateLTP = MagicMock(return_value=(bool_value, bool_value))
        hostRef.screener.validateVolume = MagicMock(return_value=(bool_value, bool_value))
        hostRef.screener.validateRSI = MagicMock(return_value=bool_value)
        hostRef.screener.validateLowestVolume = MagicMock(return_value=bool_value)
        hostRef.screener.validateIpoBase = MagicMock(return_value=bool_value)
        hostRef.screener.validateConfluence = MagicMock(return_value=bool_value)
        hostRef.screener.validateMovingAverages = MagicMock(return_value=(1,1,0))
        hostRef.screener.validateInsideBar = MagicMock(return_value=1)
        hostRef.screener.validateMomentum = MagicMock(return_value=bool_value)
        hostRef.screener.validateCCI = MagicMock(return_value=bool_value)
        hostRef.screener.findTrend = MagicMock(return_value=bool_value)
        hostRef.screener.findUptrend = MagicMock(return_value=(bool_value, 0,0))
        hostRef.screener.findPotentialBreakout = MagicMock(return_value=bool_value)
        hostRef.screener.findBreakoutValue = MagicMock(return_value=bool_value)
        hostRef.screener.validateConsolidation = MagicMock(return_value=3)
        hostRef.candlePatterns.findPattern = MagicMock(return_value=bool_value)
        hostRef.screener.validateNarrowRange = MagicMock(return_value=bool_value)
        hostRef.screener.validatePriceRisingByAtLeast2Percent = MagicMock(return_value=bool_value)
        hostRef.screener.validateShortTermBullish = MagicMock(return_value=bool_value)
        hostRef.screener.validate15MinutePriceVolumeBreakout = MagicMock(return_value=bool_value)
        hostRef.screener.findBullishIntradayRSIMACD = MagicMock(return_value=bool_value)
        hostRef.screener.findNR4Day = MagicMock(return_value=bool_value)
        hostRef.screener.find52WeekLowBreakout = MagicMock(return_value=bool_value)
        hostRef.screener.find10DaysLowBreakout = MagicMock(return_value=bool_value)
        hostRef.screener.find52WeekHighBreakout = MagicMock(return_value=bool_value)
        hostRef.screener.findAroonBullishCrossover = MagicMock(return_value=bool_value)
        hostRef.screener.validateMACDHistogramBelow0 = MagicMock(return_value=bool_value)
        hostRef.screener.validateBullishForTomorrow = MagicMock(return_value=bool_value)    
        hostRef.screener.findBreakingoutNow = MagicMock(return_value=bool_value)
        hostRef.screener.validateHigherHighsHigherLowsHigherClose = MagicMock(return_value=bool_value)
        hostRef.screener.validateLowerHighsLowerLows = MagicMock(return_value=bool_value)

        hostRef.screener.processingResultsCounter.value = 0
        executeOptions=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,23,24,25]
        menuOption = "X"
        exchangeName = "INDIA"
        userArgs = None
        newlyListedOnly = False
        respChartPattern = 3
        foundValues = 0
        for executeOption in executeOptions:
            result = stock_consumer.screenStocks(
                runOption = "X:0:1:SBIN, =>SomeOption => someotherOption",
                menuOption = menuOption,
                exchangeName = exchangeName,
                executeOption=executeOption,
                reversalOption=6,
                maLength=10,
                daysForLowestVolume=5,
                minRSI=30,
                maxRSI=70,
                respChartPattern=respChartPattern,
                insideBarToLookback=5,
                totalSymbols=100,
                shouldCache=True,
                stock='AAPL',
                newlyListedOnly=newlyListedOnly,
                downloadOnly=False,
                volumeRatio=1,
                testbuild=False,
                userArgs=userArgs,
                backtestDuration=0,
                backtestPeriodToLookback=30,
                logLevel=logging.NOTSET,
                portfolio=False,
                hostRef=hostRef
            )
            called_values = {1:hostRef.screener.findPotentialBreakout.called,
                        2:hostRef.screener.findBreakoutValue.called,
                        3:hostRef.screener.validateConsolidation.called,
                        4:hostRef.screener.validateLowestVolume.called,
                        5:hostRef.screener.validateRSI.called,
                        6:hostRef.screener.validateNarrowRange.called,
                        7:hostRef.screener.validateConfluence.called,
                        8:hostRef.screener.validateCCI.called,
                        9:hostRef.screener.validateVolume.called,
                        10:hostRef.screener.validatePriceRisingByAtLeast2Percent.called,
                        11:hostRef.screener.validateShortTermBullish.called,
                        12:hostRef.screener.validate15MinutePriceVolumeBreakout.called,
                        13:hostRef.screener.findBullishIntradayRSIMACD.called,
                        14:hostRef.screener.findNR4Day.called,
                        15:hostRef.screener.find52WeekLowBreakout.called,
                        16:hostRef.screener.find10DaysLowBreakout.called,
                        17:hostRef.screener.find52WeekHighBreakout.called,
                        18:hostRef.screener.findAroonBullishCrossover.called,
                        19:hostRef.screener.validateMACDHistogramBelow0.called,
                        20:hostRef.screener.validateBullishForTomorrow.called,
                        23:hostRef.screener.findBreakingoutNow.called,
                        24:hostRef.screener.validateHigherHighsHigherLowsHigherClose.called,
                        25:hostRef.screener.validateLowerHighsLowerLows.called
                    }

            if bool_value:
                assert result[0] == {'Stock': '\x1b[97m\x1b]8;;https://in.tradingview.com/chart?symbol=NSE%3AAAPL\x1b\\AAPL\x1b]8;;\x1b\\\x1b[0m'}
                assert result[1] == {'Stock': 'AAPL'}
                df = pd.DataFrame(data=[1, 2, 3], columns=['A'], index=[0, 1, 2])
                df.index.name = "Date"
                pd.testing.assert_frame_equal(result[2],df)
                assert result[3] == 'AAPL'
                assert result[4] == 0
                
                foundValues += 1
                assert stock_consumer.setupLoggers.called == False
                assert hostRef.screener.validateNewlyListed.called == newlyListedOnly
                assert stock_consumer.initResultDictionaries.called
                assert hostRef.screener.validateLTP.called
                assert hostRef.screener.validateVolume.called
                assert hostRef.screener.validateRSI.called
                assert hostRef.screener.preprocessData.called
                assert hostRef.screener.validateIpoBase.called == newlyListedOnly
                assert hostRef.screener.validateMovingAverages.called
                assert hostRef.screener.validateInsideBar.called == (executeOption == 7 and respChartPattern < 3)
                assert hostRef.screener.validateCCI.called
                assert hostRef.screener.findTrend.called
                assert hostRef.screener.findBreakoutValue.called
                assert hostRef.screener.validateConsolidation.called
                assert hostRef.candlePatterns.findPattern.called
                assert hostRef.processingResultsCounter.value == foundValues
                assert called_values[executeOption]
            else:
                assert result is None
