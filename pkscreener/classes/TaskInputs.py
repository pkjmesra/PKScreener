import logging

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.Screener as Screener
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes.log import default_logger

candlePatternsLocal = CandlePatterns()
configManagerLocal = ConfigManager.tools()
fetcherLocal = Fetcher.tools(configManagerLocal)
screenerLocal = Screener.tools(configManagerLocal, default_logger())

class taskInputs:
    def __init__(self, executeOption,
                    reversalOption= None,
                    maLength= None,
                    daysForLowestVolume= 30,
                    minRSI= 0,
                    maxRSI= 100,
                    respChartPattern= None,
                    insideBarToLookback= 7,
                    stocksCount= 0,
                    configManager= configManagerLocal,
                    fetcher= fetcherLocal,
                    screener= screenerLocal,
                    candlePatterns= candlePatternsLocal,
                    stock= None,
                    newlyListedOnly= False,
                    downloadOnly= False,
                    volumeRatio= configManagerLocal.volumeRatio,
                    testBuild= False,
                    printCounter= False,
                    backtestDuration= 0,
                    backtestPeriodToLookback= 30,
                    loggingLevel= logging.NOTSET,
                    monitoring=True):
        self.executeOption = executeOption
        self.reversalOption = reversalOption
        self.maLength = maLength
        self.daysForLowestVolume = daysForLowestVolume
        self.minRSI = minRSI
        self.maxRSI = maxRSI
        self.respChartPattern = respChartPattern
        self.insideBarToLookback = insideBarToLookback
        self.stocksCount = stocksCount
        self.configManager = configManager
        self.cacheEnabled = configManager.cacheEnabled
        self.fetcher = fetcher
        self.screener = screener
        self.candlePatterns = candlePatterns
        self.stock = stock
        self.newlyListedOnly = newlyListedOnly
        self.downloadOnly = downloadOnly
        self.volumeRatio = volumeRatio
        self.testBuild = testBuild
        self.printCounter = printCounter
        self.backtestDuration = backtestDuration
        self.backtestPeriodToLookback = backtestPeriodToLookback
        self.loggingLevel = loggingLevel
        self.monitoring = monitoring

    def inputParams(self):
        return (self.executeOption,
            self.reversalOption,
            self.maLength,
            self.daysForLowestVolume,
            self.minRSI,
            self.maxRSI,
            self.respChartPattern,
            self.insideBarToLookback,
            self.stocksCount,
            self.configManager,
            self.cacheEnabled,
            self.fetcher,
            self.screener,
            self.candlePatterns,
            self.stock,
            self.newlyListedOnly,
            self.downloadOnly,
            self.volumeRatio,
            self.testBuild,
            self.printCounter,
            self.backtestDuration,
            self.backtestPeriodToLookback,
            self.loggingLevel,
            self.monitoring,
            )
