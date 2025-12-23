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
import multiprocessing

from PKDevTools.classes.Singleton import SingletonType, SingletonMixin
from PKDevTools.classes.log import default_logger

from PKNSETools.morningstartools.PKMorningstarDataFetcher import morningstarDataFetcher

import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
from pkscreener.classes import Fetcher
from pkscreener.classes.MenuOptions import menus


class PKGlobalStore(SingletonMixin, metaclass=SingletonType):
    """
    Singleton class that manages all global state for the PKScreener application.
    This centralizes all the global variables that were previously scattered in globals.py.
    
    Usage:
        store = PKGlobalStore()
        store.configManager.getConfig(...)
        store.userPassedArgs = args
    """
    
    def __init__(self):
        super(PKGlobalStore, self).__init__()
        self._initialize_config()
        self._initialize_fetchers()
        self._initialize_menus()
        self._initialize_scan_state()
        self._initialize_results_state()
        self._initialize_multiprocessing_state()
        self._initialize_notification_state()
    
    def _initialize_config(self):
        """Initialize configuration-related state."""
        self.configManager = ConfigManager.tools()
        self.configManager.getConfig(ConfigManager.parser)
        self.TEST_STKCODE = "SBIN"
        self.defaultAnswer = None
        
    def _initialize_fetchers(self):
        """Initialize data fetcher instances."""
        self.fetcher = Fetcher.screenerStockDataFetcher(self.configManager)
        self.mstarFetcher = morningstarDataFetcher(self.configManager)
        
    def _initialize_menus(self):
        """Initialize menu instances."""
        self.m0 = menus()
        self.m1 = menus()
        self.m2 = menus()
        self.m3 = menus()
        self.m4 = menus()
        self.selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        self.menuChoiceHierarchy = ""
        self.nValueForMenu = 0
        
    def _initialize_scan_state(self):
        """Initialize scan-related state."""
        self.keyboardInterruptEvent = None
        self.keyboardInterruptEventFired = False
        self.loadCount = 0
        self.loadedStockData = False
        self.maLength = None
        self.newlyListedOnly = False
        self.screenCounter = None
        self.screener = ScreeningStatistics(self.configManager, default_logger())
        self.userPassedArgs = None
        self.elapsed_time = 0
        self.start_time = 0
        self.scanCycleRunning = False
        self.strategyFilter = []
        self.listStockCodes = None
        self.lastScanOutputStockCodes = None
        self.runCleanUp = False
        
    def _initialize_results_state(self):
        """Initialize results-related state."""
        self.screenResults = None
        self.backtest_df = None
        self.screenResultsCounter = None
        self.stockDictPrimary = None
        self.stockDictSecondary = None
        self.analysis_dict = {}
        self.criteria_dateTime = None
        self.saved_screen_results = None
        self.show_saved_diff_results = False
        self.resultsContentsEncoded = None
        
    def _initialize_multiprocessing_state(self):
        """Initialize multiprocessing-related state."""
        self.tasks_queue = None
        self.results_queue = None
        self.consumers = None
        self.logging_queue = None
        self.mp_manager = None
        
    def _initialize_notification_state(self):
        """Initialize notification-related state."""
        self.test_messages_queue = None
        self.download_trials = 0
        self.media_group_dict = {}
        self.DEV_CHANNEL_ID = "-1001785195297"
    
    def reset_for_new_scan(self):
        """Reset state for a new scan cycle."""
        self.selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        self.elapsed_time = 0 if not self.scanCycleRunning else self.elapsed_time
        self.start_time = 0 if not self.scanCycleRunning else self.start_time
        self.strategyFilter = []
        self.test_messages_queue = []
        
    def reset_menu_choice_options(self):
        """Reset menu choice options and hierarchy."""
        self.media_group_dict = {}
        self.menuChoiceHierarchy = ""
        if self.userPassedArgs is not None:
            self.userPassedArgs.pipedtitle = ""
            
    def is_interrupted(self):
        """Check if keyboard interrupt was fired."""
        return self.keyboardInterruptEventFired
    
    def initialize_multiprocessing(self):
        """Initialize multiprocessing components if not already done."""
        self.screenCounter = multiprocessing.Value("i", 1)
        self.screenResultsCounter = multiprocessing.Value("i", 0)
        
        if self.mp_manager is None:
            self.mp_manager = multiprocessing.Manager()
            
        if self.keyboardInterruptEvent is None and not self.keyboardInterruptEventFired:
            self.keyboardInterruptEvent = self.mp_manager.Event()
            
        self.keyboardInterruptEventFired = False
        
        if self.stockDictPrimary is None or isinstance(self.stockDictPrimary, dict):
            self.stockDictPrimary = self.mp_manager.dict()
            self.stockDictSecondary = self.mp_manager.dict()
            self.loadCount = 0
            
    def get_mkt_monitor_dict(self):
        """Get a managed dictionary for market monitoring."""
        if self.mp_manager is None:
            self.mp_manager = multiprocessing.Manager()
        return self.mp_manager.dict()


# Module-level convenience function to get the singleton instance
def get_global_store():
    """Get the singleton PKGlobalStore instance."""
    return PKGlobalStore()
