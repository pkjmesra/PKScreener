#!/usr/bin/python3
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
import random
import warnings
warnings.simplefilter("ignore", UserWarning, append=True)
os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import logging
import multiprocessing
import sys
import time
import urllib
import warnings
from datetime import datetime, UTC, timedelta
from time import sleep

import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
from alive_progress import alive_bar
from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes import Archiver
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured,
    send_document,
    send_message,
    send_photo,
    send_media_group
)
from PKNSETools.morningstartools.PKMorningstarDataFetcher import morningstarDataFetcher
from PKNSETools.Nasdaq.PKNasdaqIndex import PKNasdaqIndexFetcher
from tabulate import tabulate
from halo import Halo

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.ScreeningStatistics as ScreeningStatistics
from pkscreener.classes import Utility, ConsoleUtility, ConsoleMenuUtility, ImageUtility
from pkscreener.classes.Utility import STD_ENCODING
from pkscreener.classes import VERSION, PortfolioXRay
from pkscreener.classes.Backtest import backtest, backtestSummary
from pkscreener.classes.PKSpreadsheets import PKSpreadsheets
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.Environment import PKEnvironment
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes import AssetsManager
from PKDevTools.classes.FunctionTimeouts import exit_after
from pkscreener.classes.MenuOptions import (
    level0MenuDict,
    level1_X_MenuDict,
    level1_P_MenuDict,
    level2_X_MenuDict,
    level2_P_MenuDict,
    level3_X_ChartPattern_MenuDict,
    level3_X_PopularStocks_MenuDict,
    level3_X_PotentialProfitable_MenuDict,
    PRICE_CROSS_SMA_EMA_DIRECTION_MENUDICT,
    PRICE_CROSS_SMA_EMA_TYPE_MENUDICT,
    PRICE_CROSS_PIVOT_POINT_TYPE_MENUDICT,
    level3_X_Reversal_MenuDict,
    level4_X_Lorenzian_MenuDict,
    level4_X_ChartPattern_Confluence_MenuDict,
    level4_X_ChartPattern_BBands_SQZ_MenuDict,
    level4_X_ChartPattern_MASignalMenuDict,
    level1_index_options_sectoral,
    menus,
    MAX_SUPPORTED_MENU_OPTION,
    MAX_MENU_OPTION,
    PIPED_SCANNERS,
    PREDEFINED_SCAN_MENU_KEYS,
    PREDEFINED_SCAN_MENU_TEXTS,
    INDICES_MAP,
    CANDLESTICK_DICT
)
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes.Portfolio import PortfolioCollection
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes.PKScheduler import PKScheduler
from pkscreener.classes.PKScanRunner import PKScanRunner
from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser
from pkscreener.classes.PKPremiumHandler import PKPremiumHandler
from pkscreener.classes.AssetsManager import PKAssetsManager
from pkscreener.classes.PKAnalytics import PKAnalyticsService
from pkscreener.classes.MenuManager import MenuManager, ScanExecutor, ResultProcessor, TelegramNotifier, DataManager, BacktestManager
from pkscreener.globals import getTopLevelMenuChoices, ensureMenusLoaded, initExecution, getScannerMenuChoices, handleSecondaryMenuChoices, handleExitRequest, handleScannerExecuteOption4, selectedChoice
if __name__ == '__main__':
    multiprocessing.freeze_support()

# Constants
np.seterr(divide="ignore", invalid="ignore")
TEST_STKCODE = "SBIN"


class PKScreenerMain:
    """
    Main application class for PKScreener that orchestrates the entire screening process.
    Coordinates between all manager classes and handles the main execution flow.
    """

    def __init__(self):
        """Initialize the PKScreener application with all manager classes."""
        self.config_manager = ConfigManager.tools()
        self.config_manager.getConfig(ConfigManager.parser)
        self.user_passed_args = None
        self.default_answer = None
        
        # Initialize manager classes
        self.menu_manager = MenuManager(self.config_manager, self.user_passed_args)
        self.scan_executor = ScanExecutor(self.config_manager, self.user_passed_args)
        self.result_processor = ResultProcessor(self.config_manager, self.user_passed_args)
        self.telegram_notifier = TelegramNotifier()
        self.data_manager = DataManager(self.config_manager, self.user_passed_args)
        self.backtest_manager = BacktestManager(self.config_manager, self.user_passed_args)
        
        # Share state between managers
        self.menu_manager.list_stock_codes = self.data_manager.list_stock_codes
        self.scan_executor.selected_choice = self.menu_manager.selected_choice
        self.scan_executor.criteria_date_time = self.result_processor.criteria_date_time
        self.result_processor.selected_choice = self.menu_manager.selected_choice
        self.result_processor.menu_choice_hierarchy = self.menu_manager.menu_choice_hierarchy
        self.data_manager.selected_choice = self.menu_manager.selected_choice
        self.data_manager.default_answer = self.default_answer
        self.backtest_manager.selected_choice = self.menu_manager.selected_choice
        self.backtest_manager.menu_choice_hierarchy = self.menu_manager.menu_choice_hierarchy
        self.backtest_manager.elapsed_time = self.scan_executor.elapsed_time
        self.backtest_manager.default_answer = self.default_answer

    def runScanning(self, userArgs=None, menuOption=None, indexOption=None, 
                    executeOption=None, testing=False, downloadOnly=False,
                    optionalFinalOutcome_df=None):
        """
        Execute scanning with pre-processed menu options.
        
        This method is called by globals.py when menu processing has already been done.
        It skips menu navigation and goes directly to scanning.
        
        Args:
            userArgs: User arguments passed to the application
            menuOption: Pre-processed menu option (X, C, etc.)
            indexOption: Pre-processed index option
            executeOption: Pre-processed execute option
            testing: Whether in test mode
            downloadOnly: Whether download-only mode
            optionalFinalOutcome_df: Optional final outcome dataframe
            
        Returns:
            tuple: Screen results and save results dataframes
        """
        from pkscreener.globals import selectedChoice
        
        # Initialize state variables
        self.user_passed_args = userArgs
        self.default_answer = None if userArgs is None else userArgs.answerdefault
        
        # Update references with actual user args
        self.menu_manager.user_passed_args = self.user_passed_args
        self.scan_executor.user_passed_args = self.user_passed_args
        self.result_processor.user_passed_args = self.user_passed_args
        self.telegram_notifier.user_passed_args = self.user_passed_args
        self.data_manager.user_passed_args = self.user_passed_args
        self.backtest_manager.user_passed_args = self.user_passed_args
        
        # Initialize screening counters
        self.scan_executor.screen_counter = multiprocessing.Value("i", 1)
        self.scan_executor.screen_results_counter = multiprocessing.Value("i", 0)
        
        # Initialize multiprocessing manager
        if self.scan_executor.mp_manager is None:
            self.scan_executor.mp_manager = multiprocessing.Manager()
            
        # Setup keyboard interrupt handling
        if self.scan_executor.keyboard_interrupt_event is None and not self.scan_executor.keyboard_interrupt_event_fired:
            self.scan_executor.keyboard_interrupt_event = self.scan_executor.mp_manager.Event()
            mkt_monitor_dict = self.scan_executor.mp_manager.dict()
            self.startMarketMonitor(mkt_monitor_dict, self.scan_executor.keyboard_interrupt_event)
            
        self.scan_executor.keyboard_interrupt_event_fired = False
        
        # Initialize stock data dictionaries
        if self.data_manager.stock_dict_primary is None or isinstance(self.data_manager.stock_dict_primary, dict):
            self.data_manager.stock_dict_primary = self.scan_executor.mp_manager.dict()
            self.data_manager.stock_dict_secondary = self.scan_executor.mp_manager.dict()
            self.data_manager.load_count = 0
            
        # Handle cleanup if needed
        if not self.data_manager.run_clean_up and self.user_passed_args is not None and not self.user_passed_args.systemlaunched:
            self.data_manager.cleanup_local_results()
            
        # Initialize results dataframes
        self.scan_executor.screen_results, self.scan_executor.save_results = PKScanRunner.initDataframes()
        
        # Use pre-processed selectedChoice
        self.menu_manager.selected_choice = selectedChoice.copy()
        
        # Update menu choice hierarchy
        self.menu_manager.update_menu_choice_hierarchy()
        
        # Prepare stocks for screening using pre-processed options
        options = []
        if self.user_passed_args and self.user_passed_args.options:
            options = self.user_passed_args.options.split(":")
        
        self.data_manager.list_stock_codes = self.data_manager.handle_request_for_specific_stocks(options, indexOption)
        self.data_manager.list_stock_codes = self.data_manager.prepare_stocks_for_screening(
            testing, downloadOnly, self.data_manager.list_stock_codes, indexOption
        )
        
        if executeOption is None:
            executeOption = 0
        try:
            executeOption = int(executeOption)
        except:
            executeOption = 0
        
        # Process execute options (RSI, chart patterns, etc.)
        volumeRatio = self.config_manager.volumeRatio
        reversalOption = None
        respChartPattern = None
        
        # Load or fetch stock data
        if not self.data_manager.loaded_stock_data:
            try:
                import tensorflow as tf
                with tf.device("/device:GPU:0"):
                    self.data_manager.stock_dict_primary, self.data_manager.stock_dict_secondary = self.data_manager.load_database_or_fetch(
                        downloadOnly, self.data_manager.list_stock_codes, menuOption, indexOption
                    )
            except:
                self.data_manager.stock_dict_primary, self.data_manager.stock_dict_secondary = self.data_manager.load_database_or_fetch(
                    downloadOnly, self.data_manager.list_stock_codes, menuOption, indexOption
                )
                
        self.data_manager.load_count = len(self.data_manager.stock_dict_primary) if self.data_manager.stock_dict_primary is not None else 0
        
        # Run the scanning process
        if menuOption in ["X", "B", "G", "C", "F"]:
            self.scan_executor.screen_results, self.scan_executor.save_results, self.scan_executor.backtest_df = self.scan_executor.run_scanners(
                menuOption, [], self.scan_executor.tasks_queue, self.scan_executor.results_queue,
                len(self.data_manager.list_stock_codes), 0, 1, self.scan_executor.consumers,
                self.scan_executor.screen_results, self.scan_executor.save_results, self.scan_executor.backtest_df, testing
            )
            
            # Process and display results
            if not downloadOnly and menuOption in ["X", "G", "C", "F"]:
                if self.scan_executor.screen_results is not None and len(self.scan_executor.screen_results) > 0:
                    self.scan_executor.screen_results, self.scan_executor.save_results = self.result_processor.label_data_for_printing(
                        self.scan_executor.screen_results, self.scan_executor.save_results, volumeRatio, executeOption, reversalOption or respChartPattern, menuOption
                    )
                    
                # Remove unknown values if configured
                if not self.menu_manager.newlyListedOnly and not self.config_manager.showunknowntrends and self.scan_executor.screen_results is not None and len(self.scan_executor.screen_results) > 0 and not self.user_passed_args.runintradayanalysis:
                    self.scan_executor.screen_results, self.scan_executor.save_results = self.result_processor.remove_unknowns(
                        self.scan_executor.screen_results, self.scan_executor.save_results
                    )
                    
        # Finish screening process
        self.finishScreening(
            downloadOnly, testing, self.data_manager.stock_dict_primary, self.data_manager.load_count,
            testing, self.scan_executor.screen_results, self.scan_executor.save_results, 
            None if userArgs is None else userArgs.user
        )
        
        # Reset configuration to default
        self.resetConfigToDefault()
        
        return self.scan_executor.screen_results, self.scan_executor.save_results

    def main(self, userArgs=None, optionalFinalOutcome_df=None):
        """
        Main entry point for the PKScreener application.
        
        This method orchestrates the entire screening process by coordinating between
        all manager classes. It handles menu navigation, scanning execution, result
        processing, and notifications while maintaining all existing functionality.
        
        Args:
            userArgs: User arguments passed to the application
            optionalFinalOutcome_df: Optional final outcome dataframe for intraday analysis
            
        Returns:
            tuple: Screen results and save results dataframes
        """
        # Initialize state variables
        self.user_passed_args = userArgs
        self.default_answer = None if userArgs is None else userArgs.answerdefault
        
        # Update references with actual user args
        self.menu_manager.user_passed_args = self.user_passed_args
        self.scan_executor.user_passed_args = self.user_passed_args
        self.result_processor.user_passed_args = self.user_passed_args
        self.telegram_notifier.user_passed_args = self.user_passed_args
        self.data_manager.user_passed_args = self.user_passed_args
        self.backtest_manager.user_passed_args = self.user_passed_args
        
        # Set initial state
        testing = False if userArgs is None else (userArgs.testbuild and userArgs.prodbuild)
        testBuild = False if userArgs is None else (userArgs.testbuild and not testing)
        downloadOnly = False if userArgs is None else userArgs.download
        startupoptions = None if userArgs is None else userArgs.options
        user = None if userArgs is None else userArgs.user
        self.default_answer = None if userArgs is None else userArgs.answerdefault
        
        # Initialize screening counters
        self.scan_executor.screen_counter = multiprocessing.Value("i", 1)
        self.scan_executor.screen_results_counter = multiprocessing.Value("i", 0)
        
        # Initialize multiprocessing manager
        if self.scan_executor.mp_manager is None:
            self.scan_executor.mp_manager = multiprocessing.Manager()
            
        # Setup keyboard interrupt handling
        if self.scan_executor.keyboard_interrupt_event is None and not self.scan_executor.keyboard_interrupt_event_fired:
            self.scan_executor.keyboard_interrupt_event = self.scan_executor.mp_manager.Event()
            mkt_monitor_dict = self.scan_executor.mp_manager.dict()
            self.startMarketMonitor(mkt_monitor_dict, self.scan_executor.keyboard_interrupt_event)
            
        self.scan_executor.keyboard_interrupt_event_fired = False
        
        # Initialize stock data dictionaries
        if self.data_manager.stock_dict_primary is None or isinstance(self.data_manager.stock_dict_primary, dict):
            self.data_manager.stock_dict_primary = self.scan_executor.mp_manager.dict()
            self.data_manager.stock_dict_secondary = self.scan_executor.mp_manager.dict()
            self.data_manager.load_count = 0
            
        # Handle cleanup if needed
        if not self.data_manager.run_clean_up and self.user_passed_args is not None and not self.user_passed_args.systemlaunched:
            self.data_manager.cleanup_local_results()
            
        # Log user arguments if enabled
        if self.user_passed_args.log:
            default_logger().debug(f"User Passed args: {self.user_passed_args}")
            
        # Initialize results dataframes
        self.scan_executor.screen_results, self.scan_executor.save_results = PKScanRunner.initDataframes()
        
        # Get top level menu choices
        options, menuOption, indexOption, executeOption = getTopLevelMenuChoices(
            startupoptions, testBuild, downloadOnly, defaultAnswer_param=self.default_answer
        )
        
        # Execute main menu navigation and processing
        selectedMenu = initExecution(menuOption=menuOption)
        menuOption = selectedMenu.menuKey
        
        # Handle premium feature checks
        if menuOption in ["F", "M", "S", "B", "G", "C", "P", "D"] or selectedMenu.isPremium:
            ensureMenusLoaded(menuOption, indexOption, executeOption)
            if not PKPremiumHandler.hasPremium(selectedMenu):
                PKAnalyticsService().send_event(f"non_premium_user_{menuOption}_{indexOption}_{executeOption}")
                PKAnalyticsService().send_event("app_exit")
                sys.exit(0)
                
        # Handle special menu options
        if menuOption in ["M", "D", "I", "L", "F"]:
            self.handle_special_menu_options(menuOption)
            return None, None
            
        # Process scanner menu choices
        if menuOption in ["X", "C"]:
            menuOption, indexOption, executeOption, self.menu_manager.selected_choice = getScannerMenuChoices(
                testBuild or testing, downloadOnly, startupoptions, menuOption=menuOption,
                indexOption=indexOption, executeOption=executeOption,
                defaultAnswer_param=self.default_answer, user=user
            )
            if indexOption is None:
                return None, None
                
        # Handle secondary menu options (T, E, Y, U, H)
        if menuOption in ["T", "E", "Y", "U", "H"]:
            handleSecondaryMenuChoices(menuOption, testBuild or testing, defaultAnswer_param=self.default_answer, user=user)
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            return None, None
                
        # Handle backtest options
        elif menuOption in ["B", "G"]:
            indexOption, executeOption, backtestPeriod = self.backtest_manager.takeBacktestInputs(
                str(menuOption).upper(), indexOption, executeOption, 0
            )
            backtestPeriod = backtestPeriod * self.config_manager.backtestPeriodFactor
            
        # Handle strategy screening
        elif menuOption in ["S"]:
            strategyFilter = self.handle_strategy_screening(options)
            if strategyFilter:
                menuOption, indexOption, executeOption, self.menu_manager.selected_choice = getScannerMenuChoices(
                    testBuild or testing, downloadOnly, startupoptions, menuOption="X",
                    indexOption=indexOption, executeOption=executeOption,
                    defaultAnswer_param=self.default_answer, user=user
                )
                
        # Update menu choice hierarchy
        self.menu_manager.update_menu_choice_hierarchy()
        
        # Prepare stocks for screening
        self.data_manager.list_stock_codes = self.data_manager.handle_request_for_specific_stocks(options, indexOption)
        self.data_manager.list_stock_codes = self.data_manager.prepare_stocks_for_screening(
            testing, downloadOnly, self.data_manager.list_stock_codes, indexOption
        )
        
        # Handle exit requests
        handleExitRequest(executeOption)
        
        # Process execute options
        volumeRatio = self.config_manager.volumeRatio
        reversalOption = None
        respChartPattern = None
        daysForLowestVolume = 30
        maLength = None
        
        if executeOption == 3:
            self.user_passed_args.maxdisplayresults = max(self.config_manager.maxdisplayresults, 2000)
        elif executeOption == 4:
            daysForLowestVolume = handleScannerExecuteOption4(executeOption, options)
        elif executeOption == 5:
            minRSI, maxRSI = ConsoleMenuUtility.PKConsoleMenuTools.promptRSIValues()
        elif executeOption == 6:
            reversalOption, maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptReversalScreening(
                self.menu_manager.m2.find(str(executeOption))
            )
        elif executeOption == 7:
            respChartPattern, insideBarToLookback = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatterns(
                self.menu_manager.m2.find(str(executeOption))
            )
            if respChartPattern in [3, 6, 9]:
                maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptChartPatternSubMenu(
                    self.menu_manager.m2.find(str(executeOption)), respChartPattern
                )
        # ... handle other execute options
        
        # Load or fetch stock data
        if not self.data_manager.loaded_stock_data:
            try:
                import tensorflow as tf
                with tf.device("/device:GPU:0"):
                    self.data_manager.stock_dict_primary, self.data_manager.stock_dict_secondary = self.data_manager.load_database_or_fetch(
                        downloadOnly, self.data_manager.list_stock_codes, menuOption, indexOption
                    )
            except:
                self.data_manager.stock_dict_primary, self.data_manager.stock_dict_secondary = self.data_manager.load_database_or_fetch(
                    downloadOnly, self.data_manager.list_stock_codes, menuOption, indexOption
                )
                
        self.data_manager.load_count = len(self.data_manager.stock_dict_primary) if self.data_manager.stock_dict_primary is not None else 0
        
        # Run the scanning process
        if menuOption in ["X", "B", "G", "C", "F"]:
            self.scan_executor.screen_results, self.scan_executor.save_results, self.scan_executor.backtest_df = self.scan_executor.run_scanners(
                menuOption, [], self.scan_executor.tasks_queue, self.scan_executor.results_queue,
                len(self.data_manager.list_stock_codes), 0, 1, self.scan_executor.consumers,
                self.scan_executor.screen_results, self.scan_executor.save_results, self.scan_executor.backtest_df, testing
            )
            
            # Process and display results
            if not downloadOnly and menuOption in ["X", "G", "C", "F"]:
                if menuOption == "G":
                    self.user_passed_args.backtestdaysago = 0  # backtestPeriod would be set appropriately
                    
                if self.scan_executor.screen_results is not None and len(self.scan_executor.screen_results) > 0:
                    self.scan_executor.screen_results, self.scan_executor.save_results = self.result_processor.labelDataForPrinting(
                        self.scan_executor.screen_results, self.scan_executor.save_results, volumeRatio, executeOption, reversalOption or respChartPattern, menuOption
                    )
                    
                # Remove unknown values if configured
                if not self.menu_manager.newlyListedOnly and not self.config_manager.showunknowntrends and self.scan_executor.screen_results is not None and len(self.scan_executor.screen_results) > 0 and not self.user_passed_args.runintradayanalysis:
                    self.scan_executor.screen_results, self.scan_executor.save_results = self.result_processor.removeUnknowns(
                        self.scan_executor.screen_results, self.scan_executor.save_results
                    )
                    
                # Handle backtest results
                if menuOption == "B":
                    if self.scan_executor.backtest_df is not None and len(self.scan_executor.backtest_df) > 0:
                        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                        df_xray = self.backtest_manager.prepareGroupedXRay(0, self.scan_executor.backtest_df)
                        summary_df, sorting, sortKeys = self.backtest_manager.finishBacktestDataCleanup(self.scan_executor.backtest_df, df_xray)
                        while sorting:
                            sorting = self.backtest_manager.showSortedBacktestData(self.scan_executor.backtest_df, summary_df, sortKeys)
                            
        # Finish screening process
        self.finishScreening(
            downloadOnly, testing, self.data_manager.stock_dict_primary, self.data_manager.load_count,
            testBuild, self.scan_executor.screen_results, self.scan_executor.save_results, user
        )
        
        # Reset configuration to default
        self.resetConfigToDefault()
        
        # Handle Google Sheets integration if enabled
        self.handle_google_sheets_integration()
        
        # Handle pinned menu options
        self.handle_pinned_menu_options(testing)
        
        # Handle intraday analysis if requested
        if self.user_passed_args is not None and self.user_passed_args.runintradayanalysis:
            return self.result_processor.analysisFinalResults(
                self.scan_executor.screen_results, self.scan_executor.save_results, optionalFinalOutcome_df, 
                PKScanRunner.getFormattedChoices(self.user_passed_args, self.menu_manager.selected_choice)
            )
        else:
            return self.scan_executor.screen_results, self.scan_executor.save_results

    def handle_special_menu_options(self, menu_option):
        """
        Handle special menu options that require external execution.
        
        Args:
            menu_option: Selected menu option
        """
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        launcher = f"python3.12 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
        
        if menu_option == "M":
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener in monitoring mode. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} --systemlaunched -a Y -m 'X'{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit monitoring mode.{colorText.END}")
            PKAnalyticsService().send_event(f"monitor_{menu_option}")
            sleep(2)
            os.system(f"{launcher} --systemlaunched -a Y -m 'X'")
        elif menu_option == "D":
            self.handle_download_menu_option(launcher)
        elif menu_option == "L":
            PKAnalyticsService().send_event(f"{menu_option}")
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to collect logs. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -l{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            sleep(2)
            os.system(f"{launcher} -a Y -l")
        elif menu_option == "F":
            PKAnalyticsService().send_event(f"{menu_option}")
            indexOption = 0
            self.menu_manager.selected_choice["0"] = "F"
            self.menu_manager.selected_choice["1"] = "0"
            executeOption = None
            
            if self.user_passed_args is not None and self.user_passed_args.options is not None and len(self.user_passed_args.options.split(":")) >= 3:
                optionParts = self.user_passed_args.options.split(":")
                stockOptions = optionParts[2 if len(optionParts) <= 3 else 3]
                self.data_manager.list_stock_codes = stockOptions.replace(".",",").split(",")
                
            if self.data_manager.list_stock_codes is None or len(self.data_manager.list_stock_codes) == 0:
                shouldSuppress = not OutputControls().enableMultipleLineOutput
                with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                    self.data_manager.list_stock_codes = self.data_manager.fetcher.fetchStockCodes(tickerOption=0, stockCode=None)
                    
            ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)

    def handle_download_menu_option(self, launcher):
        """
        Handle the download menu option with its sub-options.
        
        Args:
            launcher: Launcher command for external execution
        """
        selectedMenu = self.menu_manager.m0.find("D")
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        self.menu_manager.m1.renderForMenu(selectedMenu)
        selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "D"
        OutputControls().printOutput(colorText.END, end="")
        
        if selDownloadOption.upper() == "D":
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to Download daily OHLC data. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -e -d{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
            sleep(2)
            os.system(f"{launcher} -a Y -e -d")
        elif selDownloadOption.upper() == "I":
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to Download intraday OHLC data. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -e -d -i 1m{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
            sleep(2)
            os.system(f"{launcher} -a Y -e -d -i 1m")
        elif selDownloadOption.upper() == "N":
            self.handle_nasdaq_download_option(selectedMenu, selDownloadOption)
        elif selDownloadOption.upper() == "S":
            self.handle_sector_download_option(selectedMenu, selDownloadOption)

    def handle_nasdaq_download_option(self, selectedMenu, selDownloadOption):
        """
        Handle NASDAQ download option.
        
        Args:
            selectedMenu: Selected menu object
            selDownloadOption: Selected download option
        """
        selectedMenu = self.menu_manager.m1.find(selDownloadOption.upper())
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        self.menu_manager.m2.renderForMenu(selectedMenu)
        PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
        selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "12"
        OutputControls().printOutput(colorText.END, end="")
        
        filePrefix = "Download"
        if selDownloadOption.upper() in INDICES_MAP.keys():
            filePrefix = INDICES_MAP.get(selDownloadOption.upper()).replace(" ","")
            
        filename = (
            f"PKS_Data_{filePrefix}_"
            + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
            + ".csv"
        )
        filePath = os.path.join(Archiver.get_user_indices_dir(), filename)
        PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
        
        if selDownloadOption.upper() == "15":
            nasdaq = PKNasdaqIndexFetcher(self.config_manager)
            _, nasdaq_df = nasdaq.fetchNasdaqIndexConstituents()
            try:
                nasdaq_df.to_csv(filePath)
            except Exception as e:
                OutputControls().printOutput(f"{colorText.FAIL}We encountered an error. Please try again!{colorText.END}\n{colorText.WARN}{e}{colorText.END}")
                pass
            OutputControls().printOutput(f"{colorText.GREEN}{filePrefix} Saved at: {filePath}{colorText.END}")
            input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")
        elif selDownloadOption.upper() == "M":
            PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
        else:
            fileContents = self.data_manager.fetcher.fetchFileFromHostServer(filePath=filePath, tickerOption=int(selDownloadOption), fileContents="")
            if len(fileContents) > 0:
                OutputControls().printOutput(f"{colorText.GREEN}{filePrefix} Saved at: {filePath}{colorText.END}")
            else:
                OutputControls().printOutput(f"{colorText.FAIL}We encountered an error. Please try again!{colorText.END}")
            input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")

    def handle_sector_download_option(self, selectedMenu, selDownloadOption):
        """
        Handle sector download option.
        
        Args:
            selectedMenu: Selected menu object
            selDownloadOption: Selected download option
        """
        selectedMenu = self.menu_manager.m1.find(selDownloadOption.upper())
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        self.menu_manager.m2.renderForMenu(selectedMenu, skip=["15"])
        selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "12"
        OutputControls().printOutput(colorText.END, end="")
        
        filePrefix = "Download"
        if selDownloadOption.upper() in INDICES_MAP.keys():
            filePrefix = INDICES_MAP.get(selDownloadOption.upper()).replace(" ","")
            
        filename = (
            f"PKS_Data_{filePrefix}_"
            + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
            + ".csv"
        )
        PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
        filePath = os.path.join(Archiver.get_user_reports_dir(), filename)
        
        if selDownloadOption.upper() == "M":
            return
        else:
            indexOption = int(selDownloadOption)
            if indexOption > 0 and indexOption <= 14:
                PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
                shouldSuppress = not OutputControls().enableMultipleLineOutput
                with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                    self.data_manager.list_stock_codes = self.data_manager.fetcher.fetchStockCodes(indexOption, stockCode=None)
                    
                OutputControls().printOutput(f"{colorText.GREEN}Please be patient. It might take a while...{colorText.END}")
                from pkscreener.classes.PKDataService import PKDataService
                dataSvc = PKDataService()
                stockDictList, leftOutStocks = dataSvc.getSymbolsAndSectorInfo(self.config_manager, stockCodes=self.data_manager.list_stock_codes)
                
                if len(stockDictList) > 0:
                    sector_df = pd.DataFrame(stockDictList)
                    sector_df.to_csv(filePath)
                    OutputControls().printOutput(f"{colorText.GREEN}Sector/Industry info for {filePrefix}, saved at: {filePath}{colorText.END}")
                else:
                    OutputControls().printOutput(f"{colorText.FAIL}We encountered an error. Please try again!{colorText.END}")
                    
                input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")

    def handle_strategy_screening(self, options):
        """
        Handle strategy screening menu option.
        
        Args:
            options: Options list
            
        Returns:
            list: Strategy filter list
        """
        strategyFilter = []
        
        if len(options) >= 2:
            userOption = options[1]
            
        if self.default_answer is None:
            selectedMenu = self.menu_manager.m0.find("S")
            self.menu_manager.m1.strategyNames = PortfolioXRay.strategyNames()
            self.menu_manager.m1.renderForMenu(selectedMenu=selectedMenu)
            
            try:
                userOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ")
                OutputControls().printOutput(colorText.END, end="")
                
                if userOption == "":
                    userOption = "37"  # NoFilter
                elif userOption == "38":
                    userOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Enter Exact Pattern name:")
                    OutputControls().printOutput(colorText.END, end="")
                    
                    if userOption == "":
                        userOption = "37"  # NoFilter
                    else:
                        strategyFilter.append(f"[P]{userOption}")
                        userOption = "38"
            except EOFError:
                userOption = "37"  # NoFilter
                pass
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                pass
                
        userOption = userOption.upper()
        
        if userOption == "M":
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            return None
        elif userOption == "Z":
            handleExitRequest(userOption)
            return None
        elif userOption == "S":
            OutputControls().printOutput(
                colorText.GREEN
                + "  [+] Collecting all metrics for summarising..."
                + colorText.END
            )
            
            # Enable showing/saving past strategy data
            savedValue = self.config_manager.showPastStrategyData
            self.config_manager.showPastStrategyData = True
            df_all = PortfolioXRay.summariseAllStrategies()
            
            if df_all is not None and len(df_all) > 0:
                OutputControls().printOutput(
                    colorText.miniTabulator().tabulate(
                        df_all,
                        headers="keys",
                        tablefmt=colorText.No_Pad_GridFormat,
                        showindex=False,
                        maxcolwidths=Utility.tools.getMaxColumnWidths(df_all)
                    ).encode("utf-8").decode(STD_ENCODING)
                )
                self.backtest_manager.showBacktestResults(df_all, sortKey="Scanner", optionalName="InsightsSummary")
            else:
                OutputControls().printOutput("[!] Nothing to show here yet. Check back later.")
                
            # Reinstate whatever was the earlier saved value
            self.config_manager.showPastStrategyData = savedValue
            
            if self.default_answer is None:
                OutputControls().takeUserInput("Press <Enter> to continue...")
                
            return None
        else:
            userOptions = userOption.split(",")
            for usrOption in userOptions:
                strategyFilter.append(self.menu_manager.m1.find(usrOption).menuText.strip())
                
        return strategyFilter

    def finishScreening(self, downloadOnly, testing, stockDictPrimary, loadCount, 
                       testBuild, screenResults, saveResults, user=None):
        """
        Finalize the screening process by saving data and notifying results.
        
        Args:
            downloadOnly (bool): Whether only downloading data without screening
            testing (bool): Whether running in test mode
            stockDictPrimary (dict): Primary stock data dictionary
            loadCount (int): Number of stocks loaded
            testBuild (bool): Whether running test build
            screenResults: Screen results data
            saveResults: Results to save
            user: User identifier for notifications
        """
        if "RUNNER" not in os.environ.keys() or downloadOnly:
            self.data_manager.saveDownloadedData(downloadOnly, testing, stockDictPrimary, loadCount)
        
        if not testBuild and not downloadOnly and not testing and \
           ((self.user_passed_args is not None and "|" not in self.user_passed_args.options) or self.user_passed_args is None):
            self.result_processor.saveNotifyResultsFile(
                screenResults, saveResults, self.default_answer, 
                self.menu_manager.menu_choice_hierarchy, user=user
            )
        
        if ("RUNNER" in os.environ.keys() and not downloadOnly) or self.user_passed_args.log:
            self.telegram_notifier.sendMessageToTelegramChannel(mediagroup=True, user=self.user_passed_args.user)

    def resetConfigToDefault(self, force=False):
        """
        Reset configuration to default values.
        
        Args:
            force (bool): Whether to force reset
        """
        if self.user_passed_args is not None and self.user_passed_args.monitor is None:
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                if self.user_passed_args is None or (self.user_passed_args is not None and self.user_passed_args.options is not None and "|" not in self.user_passed_args.options and not self.user_passed_args.runintradayanalysis and self.user_passed_args.pipedtitle is None):
                    del os.environ['PKDevTools_Default_Log_Level']
                    
        self.config_manager.logsEnabled = False
        
        if force:
            self.config_manager.logsEnabled = False
            
        self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)

    def handle_google_sheets_integration(self):
        """Handle Google Sheets integration if enabled."""
        try:
            creds = None
            # Write into sheet only if it's the regular scan alert trigger in the morning and evening
            if 'ALERT_TRIGGER' in os.environ.keys() and os.environ["ALERT_TRIGGER"] == 'Y':
                if "GSHEET_SERVICE_ACCOUNT_DEV" in os.environ.keys() and (self.user_passed_args.backtestdaysago is None):
                    begin = time.time()
                    creds = os.environ.get("GSHEET_SERVICE_ACCOUNT_DEV")
                    OutputControls().printOutput(f"{colorText.GREEN}  [+] Saving data to Google Spreadsheets now...{colorText.END}")
                    gClient = PKSpreadsheets(credentialDictStr=creds)
                    runOption = PKScanRunner.getFormattedChoices(self.user_passed_args, self.menu_manager.selected_choice)
                    df = self.scan_executor.saveResults.copy()
                    df["LastTradeDate"], df["LastTradeTime"] = self.data_manager.getLatestTradeDateTime(self.data_manager.stock_dict_primary)
                    gClient.df_to_sheet(df=df, sheetName=runOption)
                    OutputControls().printOutput(f"{colorText.GREEN} => Done in {round(time.time()-begin,2)}s{colorText.END}")
        except:
            pass

    def handle_pinned_menu_options(self,testing):
        """Handle pinned menu options for monitoring and quick access."""
        if ("RUNNER" not in os.environ.keys() and 
            not testing and 
            (self.user_passed_args is None or 
                (self.user_passed_args is not None and 
                    (self.user_passed_args.user is None or 
                        str(self.user_passed_args.user) == self.telegram_notifier.DEV_CHANNEL_ID) and 
                    (self.user_passed_args.answerdefault is None or self.user_passed_args.systemlaunched))) and
                    not self.user_passed_args.testbuild and 
                    self.user_passed_args.monitor is None):
            
            prevOutput_results = self.scan_executor.saveResults.index if (self.scan_executor.saveResults is not None and not self.scan_executor.saveResults.empty) else []
            isNotPiped = (("|" not in self.user_passed_args.options) if (self.user_passed_args is not None and self.user_passed_args.options is not None) else True)
            hasFoundStocks = len(prevOutput_results) > 0 and isNotPiped
            
            if hasFoundStocks or (self.config_manager.showPinnedMenuEvenForNoResult and isNotPiped):
                monitorOption = self.user_passed_args.systemlaunched if (self.user_passed_args is not None and isinstance(self.user_passed_args.systemlaunched, str) and self.user_passed_args.systemlaunched is not None) else (self.user_passed_args.options if (self.user_passed_args is not None and self.user_passed_args.options is not None) else "")
                
                if len(monitorOption) == 0:
                    for choice in self.menu_manager.selected_choice.keys():
                        monitorOption = (f"{monitorOption}:" if len(monitorOption) > 0 else '') + f"{self.menu_manager.selected_choice[choice]}"
                        
                self.menu_manager.m0.renderPinnedMenu(substitutes=[monitorOption, len(prevOutput_results), monitorOption, monitorOption, monitorOption], skip=(["1","2","4","5"] if self.menu_manager.selected_choice["0"] in ["F"] else []))
                pinOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or 'M'
                OutputControls().printOutput(colorText.END, end="")
                
                self.menu_manager.ensureMenusLoaded(self.menu_manager.selected_choice["0"], self.menu_manager.selected_choice["1"], self.menu_manager.selected_choice["2"])
                
                if not PKPremiumHandler.hasPremium(self.menu_manager.m0.find(str(pinOption).upper())):
                    PKAnalyticsService().send_event(f"non_premium_user_pin_{self.menu_manager.selected_choice['0']}_{self.menu_manager.selected_choice['1']}_{self.menu_manager.selected_choice['2']}_{pinOption}")
                    PKAnalyticsService().send_event("app_exit")
                    sys.exit(0)
                    
                if pinOption in ["1", "2"]:
                    self.handle_pinned_monitoring_options(pinOption, monitorOption, prevOutput_results)
                elif pinOption in ["3"]:
                    self.handle_time_window_navigation()
                elif pinOption in ["4"]:
                    self.handle_pinned_option_saving(monitorOption)
                elif pinOption in ["5"]:
                    self.handle_restart_with_previous_results(prevOutput_results)
                    
                self.result_processor.show_saved_diff_results = False

    def handle_pinned_monitoring_options(self, pinOption, monitorOption, prevOutput_results):
        """
        Handle pinned monitoring options.
        
        Args:
            pinOption: Pinned option selected
            monitorOption: Monitor option string
            prevOutput_results: Previous results
        """
        if pinOption in ["2"]:
            monitorOption = "X:0:0"
            prevOutput_results = ",".join(prevOutput_results)
            monitorOption = f"{monitorOption}:{prevOutput_results}"
            
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        launcher = f"python3.12 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
        monitorOption = f'"{monitorOption}"'
        scannerOptionQuoted = monitorOption.replace("'", '"')
        
        OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener with pinned scan option. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} --systemlaunched -a Y -m {scannerOptionQuoted}{colorText.END}")
        sleep(2)
        os.system(f"{launcher} --systemlaunched -a Y -m {scannerOptionQuoted}")

    def handle_time_window_navigation(self):
        """Handle time window navigation for intraday analysis."""
        from pkscreener.classes.keys import getKeyBoardArrowInput
        
        message = f"\n  [+] {colorText.FAIL}Please use {colorText.END}{colorText.GREEN}Left / Right arrow keys{colorText.END} to slide through the {colorText.WARN}time-window by every 1 minute.{colorText.END}\n  [+] Use {colorText.GREEN}Up / Down arrow keys{colorText.END} to jump {colorText.GREEN}forward / backwards{colorText.END} by {colorText.WARN}{self.config_manager.duration}{colorText.END}\n  [+] {colorText.FAIL}Press any oher key to cancel.{colorText.END}"
        currentTime = PKDateUtilities.currentDateTime()
        requestTime = PKDateUtilities.currentDateTime()
        
        OutputControls().printOutput(message)
        direction = getKeyBoardArrowInput(message=None)
        numRequestsInASecond = 0
        
        while (direction is not None and direction not in ["RETURN", "CANCEL"]):
            requestTimeDiff = PKDateUtilities.currentDateTime() - requestTime
            
            if requestTimeDiff.total_seconds() <= 0.4:
                numRequestsInASecond += 1
            else:
                numRequestsInASecond = 0
                
            if numRequestsInASecond >= 10:
                numRequestsInASecond = 0
                fastMultiplier = 60
            else:
                fastMultiplier = 1
                
            candleFrequency = self.config_manager.candleDurationFrequency
            candleDuration = self.config_manager.candleDurationInt
            multiplier = fastMultiplier * (60 if candleFrequency == "h" else (24*60 if candleFrequency == "d" else (24*60*5 if candleFrequency == "wk" else (24*60*5*20 if candleFrequency == "mo" else 1))))
            
            if direction in ["LEFT", "DOWN"]:
                prevTime = currentTime - timedelta(minutes=(candleDuration*multiplier if direction == "DOWN" else 1*fastMultiplier))
                minPastDate = PKDateUtilities.currentDateTime() - timedelta(days=364)
                
                if prevTime <= minPastDate:
                    prevTime = minPastDate
                    
                currentTime = prevTime
                prevTime_comps = prevTime.strftime("%Y-%m-%d %H:%M:%S").split(" ")
                dateComp = prevTime_comps[0]
                timeComp = prevTime_comps[1].split(":")
                prevTime = f"{colorText.FAIL}{dateComp}{colorText.END} {prevTime_comps[1]}" if direction == "DOWN" else f"{dateComp} {colorText.FAIL}{timeComp[0]}:{timeComp[1]}{colorText.END}:{timeComp[2]}"
                
                OutputControls().moveCursorUpLines(lines=5)
                OutputControls().printOutput(message)
                OutputControls().printOutput(f"  [+] {colorText.WARN}Go back to: {colorText.END}{colorText.GREEN}{prevTime}{colorText.END}{colorText.WARN} ? Press <Enter> to confirm.{colorText.END}")
            elif direction in ["RIGHT", "UP"]:
                prevTime = currentTime + timedelta(minutes=(candleDuration*multiplier if direction == "UP" else 1*fastMultiplier))
                
                if prevTime > PKDateUtilities.currentDateTime():
                    prevTime = PKDateUtilities.currentDateTime()
                    
                currentTime = prevTime
                prevTime_comps = prevTime.strftime("%Y-%m-%d %H:%M:%S").split(" ")
                dateComp = prevTime_comps[0]
                timeComp = prevTime_comps[1].split(":")
                prevTime = f"{colorText.FAIL}{dateComp}{colorText.END} {prevTime_comps[1]}" if direction == "UP" else f"{dateComp} {colorText.FAIL}{timeComp[0]}:{timeComp[1]}{colorText.END}:{timeComp[2]}"
                
                OutputControls().moveCursorUpLines(lines=5)
                OutputControls().printOutput(message)
                OutputControls().printOutput(f"  [+] {colorText.WARN}Go forward to: {colorText.END}{colorText.GREEN}{prevTime}{colorText.END}{colorText.WARN} ? Press <Enter> to confirm.{colorText.END}")
                
            requestTime = PKDateUtilities.currentDateTime()
            direction = getKeyBoardArrowInput(message=None)
            
        if direction is not None and direction == "RETURN":
            # We need to take the data until "currentTime" from intraday data
            if self.user_passed_args is not None and self.user_passed_args.progressstatus is not None:
                runOptionName = self.user_passed_args.progressstatus.split("=>")[0].split("  [+] ")[1].strip()
                
                if runOptionName.startswith("P"):
                    self.user_passed_args.options = runOptionName.replace("_", ":")
                    
            self.user_passed_args.stocklist = ','.join(self.scan_executor.screen_results.index)
            tradingDaysInThePast = PKDateUtilities.trading_days_between(currentTime, PKDateUtilities.tradingDate())
            
            if tradingDaysInThePast > 0:
                self.user_passed_args.backtestdaysago = tradingDaysInThePast
            elif tradingDaysInThePast < 0:
                self.user_passed_args.backtestdaysago = None
            elif tradingDaysInThePast == 0:
                self.user_passed_args.slicewindow = f"'{currentTime}'"
                
            ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
            OutputControls().printOutput(f"{colorText.WARN}Launching into the selected time-window!{colorText.END}{colorText.GREEN} Brace yourself for the time-travel!{colorText.END}")
            sleep(5)
            
            # Restart the main method with new parameters
            return self.main(userArgs=self.user_passed_args, optionalFinalOutcome_df=None)

    def handle_pinned_option_saving(self, monitorOption):
        """
        Handle saving pinned options for monitoring.
        
        Args:
            monitorOption: Monitor option to save
        """
        prevMonitorOption = f"{self.config_manager.myMonitorOptions}~" if len(self.config_manager.myMonitorOptions) > 0 else ""
        self.config_manager.myMonitorOptions = f"{prevMonitorOption}{monitorOption}"
        self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        
        OutputControls().printOutput(f"[+] {colorText.GREEN} Your monitoring options have been updated:{colorText.END}\n     {colorText.WARN}{self.config_manager.myMonitorOptions}{colorText.END}\n[+] {colorText.GREEN}You can run it using the option menu {colorText.END}{colorText.FAIL}-m{colorText.END} {colorText.GREEN}or using the main launch option {colorText.END}{colorText.FAIL}M >{colorText.END}")
        sleep(4)

    def handle_restart_with_previous_results(self, prevOutput_results):
        """
        Handle restarting with previous results.
        
        Args:
            prevOutput_results: Previous results to use
        """
        if len(self.scan_executor.save_results) > 0:
            self.data_manager.last_scan_output_stock_codes = list(self.scan_executor.save_results.index)
            self.user_passed_args.options = None
            menuOption = None
            executeOption = 0
            
            # Restart the main method with previous results
            return self.main(userArgs=self.user_passed_args, optionalFinalOutcome_df=None)

    def startMarketMonitor(self, mp_dict, keyboardevent):
        """
        Start monitoring the market status in a separate process.
        
        Args:
            mp_dict: Multiprocessing dictionary
            keyboardevent: Keyboard interrupt event
        """
        if not 'pytest' in sys.modules:
            from PKDevTools.classes.NSEMarketStatus import NSEMarketStatus
            NSEMarketStatus(mp_dict, keyboardevent).startMarketMonitor()

# Global functions for backward compatibility
def startMarketMonitor(mp_dict, keyboardevent):
    """Start market monitor - maintained for backward compatibility."""
    screener = PKScreenerMain()
    screener.startMarketMonitor(mp_dict, keyboardevent)
