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

from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.log import default_logger

from PKNSETools.morningstartools.PKMorningstarDataFetcher import morningstarDataFetcher

import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
from pkscreener.classes import Fetcher
from pkscreener.classes.MenuOptions import menus

class PKGlobalStore(SingletonMixin, metaclass=SingletonType):
    
    def __init__(self):
        super(PKGlobalStore, self).__init__()
        self.configManager = ConfigManager.tools()
        self.configManager.getConfig(ConfigManager.parser)
        # Try Fixing bug with this symbol
        self.TEST_STKCODE = "SBIN"
        self.defaultAnswer = None
        self.fetcher = Fetcher.screenerStockDataFetcher(self.configManager)
        self.mstarFetcher = morningstarDataFetcher(self.configManager)
        self.keyboardInterruptEvent = None
        self.keyboardInterruptEventFired=False
        self.loadCount = 0
        self.loadedStockData = False
        self.m0 = menus()
        self.m1 = menus()
        self.m2 = menus()
        self.m3 = menus()
        self.m4 = menus()
        self.maLength = None
        self.nValueForMenu = 0
        self.menuChoiceHierarchy = ""
        self.newlyListedOnly = False
        self.screenCounter = None
        self.screener = ScreeningStatistics.ScreeningStatistics(self.configManager, default_logger())
        self.screenResults = None
        self.backtest_df = None
        self.screenResultsCounter = None
        self.selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        self.stockDictPrimary = None
        self.stockDictSecondary = None
        self.userPassedArgs = None
        self.elapsed_time = 0
        self.start_time = 0
        self.scanCycleRunning = False
        self.test_messages_queue = None
        self.strategyFilter=[]
        self.listStockCodes = None
        self.lastScanOutputStockCodes = None
        self.tasks_queue = None
        self.results_queue = None
        self.consumers = None
        self.logging_queue = None
        self.mp_manager = None
        self.analysis_dict = {}
        self.download_trials = 0
        self.media_group_dict = {}
        self.DEV_CHANNEL_ID="-1001785195297"
        self.criteria_dateTime = None
        self.saved_screen_results = None
        self.show_saved_diff_results = False
        self.resultsContentsEncoded = None
        self.runCleanUp = False
