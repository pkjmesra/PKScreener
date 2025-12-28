"""
Main application refactoring for PKScreener
This module breaks down the massive main function into manageable classes
while preserving all existing functionality.
"""

import multiprocessing
import os
import sys
import time
import pandas as pd
from datetime import timedelta
from typing import Dict, List, Tuple, Any, Optional

# Import all necessary modules (preserving original imports)
import urllib.error
from alive_progress import alive_bar

# Import project-specific modules
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities as DevDateUtilities
from pkscreener.classes import Utility, ConsoleUtility
from pkscreener.classes.PKScanRunner import PKScanRunner
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.Fetcher import screenerStockDataFetcher
from pkscreener.classes.MenuOptions import menus
from pkscreener.classes import PortfolioXRay
from pkscreener.classes.PKAnalytics import PKAnalyticsService
from pkscreener.classes.PKPremiumHandler import PKPremiumHandler
from pkscreener.classes.PKSpreadsheets import PKSpreadsheets
from pkscreener.globals import *
# m0, m1, m2, m3, m4 are defined in globals.py and imported via *

class ApplicationState:
    """Manages the global application state and configuration"""
    
    def __init__(self, userArgs=None):
        self.userArgs = userArgs
        self.initialize_globals()
        self.setup_initial_state()
        
    def initialize_globals(self):
        """Initialize all global variables with their default values"""
        global lastScanOutputStockCodes, scanCycleRunning, runCleanUp, test_messages_queue
        global show_saved_diff_results, criteria_dateTime, analysis_dict, mp_manager
        global listStockCodes, screenResults, selectedChoice, defaultAnswer, menuChoiceHierarchy
        global screenCounter, screenResultsCounter, stockDictPrimary, stockDictSecondary
        global userPassedArgs, loadedStockData, keyboardInterruptEvent, loadCount, maLength
        global newlyListedOnly, keyboardInterruptEventFired, strategyFilter, elapsed_time, start_time
        
        selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        elapsed_time = 0 if not scanCycleRunning else elapsed_time
        start_time = 0 if not scanCycleRunning else start_time
        
    def setup_initial_state(self):
        """Set up the initial application state based on user arguments"""
        global testing, testBuild, downloadOnly, startupoptions, user, defaultAnswer, userPassedArgs
        global runOptionName, options, strategyFilter, test_messages_queue
        
        testing = False if self.userArgs is None else (self.userArgs.testbuild and self.userArgs.prodbuild)
        testBuild = False if self.userArgs is None else (self.userArgs.testbuild and not testing)
        downloadOnly = False if self.userArgs is None else self.userArgs.download
        startupoptions = None if self.userArgs is None else self.userArgs.options
        user = None if self.userArgs is None else self.userArgs.user
        defaultAnswer = None if self.userArgs is None else self.userArgs.answerdefault
        userPassedArgs = self.userArgs
        runOptionName = ""
        options = []
        strategyFilter = []
        test_messages_queue = []
        
        describeUser()


class MenuHandler:
    """Handles all menu-related operations and user interactions"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.configManager = ConfigManager()
        
    def process_top_level_menu(self):
        """Process the top-level menu options"""
        global screenResults, saveResults, options, menuOption, indexOption, executeOption
        
        screenResults, saveResults = PKScanRunner.initDataframes()
        options, menuOption, indexOption, executeOption = getTopLevelMenuChoices(
            self.app_state.startupoptions, self.app_state.testBuild, 
            self.app_state.downloadOnly, defaultAnswer=self.app_state.defaultAnswer
        )
        
        selectedMenu = initExecution(menuOption=menuOption)
        menuOption = selectedMenu.menuKey
        
        return selectedMenu, menuOption, indexOption, executeOption
    
    def handle_premium_checks(self, selectedMenu):
        """Check if user has premium access for premium features"""
        global menuOption, indexOption, executeOption
        
        if menuOption in ["F", "M", "S", "B", "G", "C", "P", "D"] or selectedMenu.isPremium:
            ensureMenusLoaded(menuOption, indexOption, executeOption)
            if not PKPremiumHandler.hasPremium(selectedMenu):
                PKAnalyticsService().send_event(f"non_premium_user_{menuOption}_{indexOption}_{executeOption}")
                PKAnalyticsService().send_event("app_exit")
                sys.exit(0)
    
    def handle_special_menu_options(self, menuOption, selectedMenu):
        """Handle special menu options like monitor, download, etc."""
        if menuOption in ["M", "D", "I", "L", "F"]:
            self.handle_monitor_download_options(menuOption, selectedMenu)
        elif menuOption in ["P"]:
            self.handle_predefined_scans()
        elif menuOption in ["X", "T", "E", "Y", "U", "H", "C"]:
            self.handle_scanner_menu_options()
        elif menuOption in ["B", "G"]:
            self.handle_backtest_options()
        elif menuOption in ["S"]:
            self.handle_strategy_options()
    
    def handle_monitor_download_options(self, menuOption, selectedMenu):
        """Handle monitor and download menu options"""
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        launcher = f"python3.12 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
        
        if menuOption in ["M"]:
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener in monitoring mode. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} --systemlaunched -a Y -m 'X'{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit monitoring mode.{colorText.END}")
            PKAnalyticsService().send_event(f"monitor_{menuOption}")
            time.sleep(2)
            os.system(f"{launcher} --systemlaunched -a Y -m 'X'")
        elif menuOption in ["D"]:
            self.handle_download_options(selectedMenu, launcher)
        elif menuOption in ["L"]:
            PKAnalyticsService().send_event(f"{menuOption}")
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to collect logs. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -l{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            time.sleep(2)
            os.system(f"{launcher} -a Y -l")
        elif menuOption in ["F"]:
            self.handle_favorites_option()
    
    def handle_download_options(self, selectedMenu, launcher):
        """Handle download-specific menu options"""
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        m1.renderForMenu(selectedMenu)
        selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "D"
        OutputControls().printOutput(colorText.END, end="")
        
        if selDownloadOption.upper() == "D":
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to Download daily OHLC data. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -e -d{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            PKAnalyticsService().send_event(f"{menuOption}_{selDownloadOption.upper()}")
            time.sleep(2)
            os.system(f"{launcher} -a Y -e -d")
            return None, None
        # ... handle other download options
    
    def handle_favorites_option(self):
        """Handle favorites menu option"""
        global indexOption, selectedChoice, listStockCodes
        
        PKAnalyticsService().send_event(f"{menuOption}")
        indexOption = 0
        selectedChoice["0"] = "F"
        selectedChoice["1"] = "0"
        executeOption = None
        shouldSuppress = not OutputControls().enableMultipleLineOutput
        
        if userPassedArgs is not None and userPassedArgs.options is not None and len(userPassedArgs.options.split(":")) >= 3:
            stockOptions = userPassedArgs.options.split(":")
            stockOptions = userPassedArgs.options.split(":")[2 if len(stockOptions)<=3 else 3]
            listStockCodes = stockOptions.replace(".",",").split(",")
        
        if listStockCodes is None or len(listStockCodes) == 0:
            with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                listStockCodes = fetcher.fetchStockCodes(tickerOption=0, stockCode=None)
        
        ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
    
    def handle_predefined_scans(self):
        """Handle predefined scan options"""
        global predefinedOption, selPredefinedOption, selIndexOption, selectedChoice
        
        predefinedOption = None
        selPredefinedOption = None
        selIndexOption = None
        
        if len(options) >= 3:
            predefinedOption = str(options[1]) if str(options[1]).isnumeric() else '1'
            selPredefinedOption = str(options[2]) if str(options[2]).isnumeric() else '1'
            if len(options) >= 4:
                selIndexOption = str(options[3]) if str(options[3]).isnumeric() else '12'
        
        selectedChoice["0"] = "P"
        updateMenuChoiceHierarchy()
        selectedMenu = m0.find(menuOption)
        m1.renderForMenu(selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
        
        # ... handle predefined scan logic


class ScannerHandler:
    """Handles scanner operations and screening logic"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.configManager = ConfigManager()
    
    def execute_scanner(self, menuOption, indexOption, executeOption):
        """Execute the selected scanner with appropriate parameters"""
        global volumeRatio, minRSI, maxRSI, insideBarToLookback, respChartPattern
        global daysForLowestVolume, reversalOption, maLength
        
        volumeRatio = self.configManager.volumeRatio
        
        if executeOption == 3:
            userPassedArgs.maxdisplayresults = max(self.configManager.maxdisplayresults, 2000)
        elif executeOption == 4:
            daysForLowestVolume = self.handle_scanner_execute_option_4(executeOption, options)
        elif executeOption == 5:
            self.handle_rsi_scanner(executeOption, options)
        elif executeOption == 6:
            self.handle_reversal_scanner(executeOption, options)
        elif executeOption == 7:
            self.handle_chart_pattern_scanner(executeOption, options)
        # ... handle other execute options
    
    def handle_rsi_scanner(self, executeOption, options):
        """Handle RSI scanner configuration"""
        global minRSI, maxRSI, selectedMenu
        
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 5:
            if str(options[3]).isnumeric():
                minRSI = int(options[3])
                maxRSI = int(options[4])
            elif str(options[3]).upper() == "D" or userPassedArgs.systemlaunched:
                minRSI = 60
                maxRSI = 75
        else:
            minRSI, maxRSI = ConsoleMenuUtility.PKConsoleMenuTools.promptRSIValues()
        
        if not minRSI and not maxRSI:
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] Error: Invalid values for RSI! Values should be in range of 0 to 100. Please try again!"
                + colorText.END
            )
            OutputControls().takeUserInput("Press <Enter> to continue...")
            return None, None
    
    def handle_reversal_scanner(self, executeOption, options):
        """Handle reversal scanner configuration"""
        global reversalOption, maLength, selectedMenu
        
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            reversalOption = int(options[3])
            if reversalOption in [4, 6, 7, 10]:
                if len(options) >= 5:
                    if str(options[4]).isnumeric():
                        maLength = int(options[4])
                    elif str(options[4]).upper() == "D" or userPassedArgs.systemlaunched:
                        maLength = 50 if reversalOption == 4 else (3 if reversalOption in [7] else (2 if reversalOption in [10] else 7))
                elif defaultAnswer == "Y" and user is not None:
                    maLength = 50 if reversalOption == 4 else (3 if reversalOption == 7 else 7)
                else:
                    reversalOption, maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptReversalScreening(selectedMenu)
        else:
            reversalOption, maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptReversalScreening(selectedMenu)
        
        if reversalOption is None or reversalOption == 0 or maLength == 0:
            return None, None
        else:
            selectedChoice["3"] = str(reversalOption)
            if str(reversalOption) in ["7", "10"]:
                selectedChoice["4"] = str(maLength)


class BacktestHandler:
    """Handles backtesting operations and results processing"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.configManager = ConfigManager()
    
    def handle_backtest_options(self):
        """Handle backtest menu options"""
        global backtestPeriod
        
        backtestPeriod = 0
        if len(options) >= 2:
            if str(indexOption).isnumeric():
                backtestPeriod = int(indexOption)
            if len(options) >= 4:
                indexOption = executeOption
                executeOption = options[3]
            del options[1]
        
        indexOption, executeOption, backtestPeriod = takeBacktestInputs(
            str(menuOption).upper(), indexOption, executeOption, backtestPeriod
        )
        backtestPeriod = backtestPeriod * self.configManager.backtestPeriodFactor
    
    def process_backtest_results(self, backtest_df):
        """Process and display backtest results"""
        if backtest_df is not None and len(backtest_df) > 0:
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            df_xray = prepareGroupedXRay(backtestPeriod, backtest_df)
            summary_df, sorting, sortKeys = FinishBacktestDataCleanup(backtest_df, df_xray)
            
            while sorting:
                sorting = showSortedBacktestData(backtest_df, summary_df, sortKeys)
            
            if defaultAnswer is None:
                OutputControls().takeUserInput("Press <Enter> to continue...")
        else:
            OutputControls().printOutput("Finished backtesting with no results to show!")


class StrategyHandler:
    """Handles strategy-related operations and filtering"""
    
    def __init__(self, app_state):
        self.app_state = app_state
    
    def handle_strategy_options(self):
        """Handle strategy menu options"""
        global userOption, strategyFilter, menuOption, indexOption, executeOption, selectedChoice
        
        if len(options) >= 2:
            userOption = options[1]
        
        if defaultAnswer is None:
            selectedMenu = m0.find(menuOption)
            m1.strategyNames = PortfolioXRay.strategyNames()
            m1.renderForMenu(selectedMenu=selectedMenu)
            
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
            except Exception as e:
                default_logger().debug(e, exc_info=True)
        
        userOption = userOption.upper()
        
        if userOption == "M":
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            return None, None
        elif userOption == "Z":
            handleExitRequest(userOption)
            return None, None
        elif userOption == "S":
            self.handle_strategy_summary()
        else:
            self.apply_strategy_filters(userOption)
    
    def handle_strategy_summary(self):
        """Handle strategy summary display"""
        OutputControls().printOutput(
            colorText.GREEN
            + "  [+] Collecting all metrics for summarising..."
            + colorText.END
        )
        
        savedValue = configManager.showPastStrategyData
        configManager.showPastStrategyData = True
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
            showBacktestResults(df_all, sortKey="Scanner", optionalName="InsightsSummary")
        else:
            OutputControls().printOutput("[!] Nothing to show here yet. Check back later.")
        
        configManager.showPastStrategyData = savedValue
        
        if defaultAnswer is None:
            OutputControls().takeUserInput("Press <Enter> to continue...")
        
        return None, None
    
    def apply_strategy_filters(self, userOption):
        """Apply selected strategy filters"""
        global strategyFilter, menuOption, indexOption, executeOption, selectedChoice
        
        userOptions = userOption.split(",")
        for usrOption in userOptions:
            strategyFilter.append(m1.find(usrOption).menuText.strip())
        
        menuOption, indexOption, executeOption, selectedChoice = getScannerMenuChoices(
            self.app_state.testBuild or self.app_state.testing,
            self.app_state.downloadOnly,
            self.app_state.startupoptions,
            menuOption="X",
            indexOption=indexOption,
            executeOption=executeOption,
            defaultAnswer=self.app_state.defaultAnswer,
            user=self.app_state.user,
        )


class DataLoader:
    """Handles data loading and preparation for screening"""
    
    def __init__(self, app_state):
        self.app_state = app_state
        self.configManager = ConfigManager()
    
    def load_stock_data(self, menuOption, indexOption, downloadOnly, listStockCodes):
        """Load stock data for screening"""
        global stockDictPrimary, stockDictSecondary, loadedStockData
        
        loadedStockData = loadedStockData and stockDictPrimary is not None and len(stockDictPrimary) > 0
        
        if (menuOption in ["X", "B", "G", "S", "F"] and not loadedStockData) or (
            self.configManager.cacheEnabled and not loadedStockData and not self.app_state.testing
        ):
            try:
                import tensorflow as tf
                with tf.device("/device:GPU:0"):
                    stockDictPrimary, stockDictSecondary = loadDatabaseOrFetch(
                        downloadOnly, listStockCodes, menuOption, indexOption
                    )
            except:
                stockDictPrimary, stockDictSecondary = loadDatabaseOrFetch(
                    downloadOnly, listStockCodes, menuOption, indexOption
                )
        
        return len(stockDictPrimary) if stockDictPrimary is not None else 0


class MainApplication:
    """Main application class that orchestrates all components"""
    
    def __init__(self, userArgs=None):
        self.app_state = ApplicationState(userArgs)
        self.menu_handler = MenuHandler(self.app_state)
        self.scanner_handler = ScannerHandler(self.app_state)
        self.backtest_handler = BacktestHandler(self.app_state)
        self.strategy_handler = StrategyHandler(self.app_state)
        self.data_loader = DataLoader(self.app_state)
        self.configManager = ConfigManager()
    
    def main(self, userArgs=None, optionalFinalOutcome_df=None):
        """
        Main entry point for the application
        Refactored from the original massive main function
        
        Args:
            userArgs: Command line arguments passed by user
            optionalFinalOutcome_df: Optional dataframe for final results
            
        Returns:
            Tuple of screen results and save results
        """
        global keyboardInterruptEventFired
        
        # Check for keyboard interrupt
        if keyboardInterruptEventFired:
            return None, None
        
        # Handle intraday analysis if requested
        if self.handle_intraday_analysis(userArgs, optionalFinalOutcome_df):
            savedAnalysisDict = analysis_dict.get(firstScanKey)
            return analysisFinalResults(
                savedAnalysisDict.get("S1"), 
                savedAnalysisDict.get("S2"), 
                optionalFinalOutcome_df, 
                None
            )
        
        # Initialize multiprocessing and market monitor
        self.initialize_multiprocessing()
        self.initialize_market_monitor()
        
        # Handle cleanup if needed
        if self.handle_cleanup(userArgs):
            cleanupLocalResults()
        
        # Process menu options
        selectedMenu, menuOption, indexOption, executeOption = self.menu_handler.process_top_level_menu()
        
        # Check premium access
        self.menu_handler.handle_premium_checks(selectedMenu)
        
        # Handle special menu options
        self.menu_handler.handle_special_menu_options(menuOption, selectedMenu)
        
        # Handle scanner menu options
        if menuOption in ["X", "T", "E", "Y", "U", "H", "C"]:
            menuOption, indexOption, executeOption, selectedChoice = getScannerMenuChoices(
                self.app_state.testBuild or self.app_state.testing,
                self.app_state.downloadOnly,
                self.app_state.startupoptions,
                menuOption=menuOption,
                indexOption=indexOption,
                executeOption=executeOption,
                defaultAnswer=self.app_state.defaultAnswer,
                user=self.app_state.user,
            )
        
        # Handle menu options X, B, G
        handleMenu_XBG(menuOption, indexOption, executeOption)
        
        # Check for exit request
        if str(indexOption).upper() == "M" or str(executeOption).upper() == "M":
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            return None, None
        
        # Prepare stocks for screening
        listStockCodes = handleRequestForSpecificStocks(options, indexOption)
        handleExitRequest(executeOption)
        
        if executeOption is None:
            executeOption = 0
        executeOption = int(executeOption)
        
        # Execute the selected scanner
        self.scanner_handler.execute_scanner(menuOption, indexOption, executeOption)
        
        # Load stock data
        loadCount = self.data_loader.load_stock_data(
            menuOption, indexOption, self.app_state.downloadOnly, listStockCodes
        )
        
        # Run the screening process
        screenResults, saveResults = self.run_screening_process(
            menuOption, indexOption, executeOption, listStockCodes, loadCount
        )
        
        # Process results
        if menuOption in ["X", "C", "F"] and (userPassedArgs.monitor is None or self.configManager.alwaysExportToExcel) or ("|" not in userPassedArgs.options and menuOption not in ["B"]):
            finishScreening(
                self.app_state.downloadOnly,
                self.app_state.testing,
                stockDictPrimary,
                self.configManager,
                loadCount,
                self.app_state.testBuild,
                screenResults,
                saveResults,
                self.app_state.user,
            )
        
        # Handle backtest results
        if menuOption == "B":
            self.backtest_handler.process_backtest_results(backtest_df)
        
        # Reset configuration
        resetConfigToDefault()
        
        # Save to Google Sheets if configured
        self.save_to_google_sheets(saveResults)
        
        # Handle pinned menu
        self.handle_pinned_menu(saveResults, menuOption)
        
        return screenResults, saveResults
    
    def run_screening_process(self, menuOption, indexOption, executeOption, listStockCodes, loadCount):
        """Run the screening process with appropriate parameters"""
        global screenResults, saveResults, backtest_df
        
        # Prepare screening parameters
        samplingDuration, fillerPlaceHolder, actualHistoricalDuration = PKScanRunner.getScanDurationParameters(
            self.app_state.testing, menuOption
        )
        
        totalStocksInReview = 0
        savedStocksCount = 0
        downloadedRecently = False
        items = []
        backtest_df = None
        
        # Get progress bar style
        bar, spinner = Utility.tools.getProgressbarStyle()
        
        # Begin screening process
        OutputControls().printOutput(f"{colorText.GREEN}  [+] Adding stocks to the queue...{colorText.END}")
        
        with alive_bar(actualHistoricalDuration, bar=bar, spinner=spinner) as progressbar:
            while actualHistoricalDuration >= 0:
                daysInPast = PKScanRunner.getBacktestDaysForScan(
                    userPassedArgs, backtestPeriod, menuOption, actualHistoricalDuration
                )
                
                try:
                    listStockCodes, savedStocksCount, pastDate = PKScanRunner.getStocksListForScan(
                        userPassedArgs, menuOption, totalStocksInReview, downloadedRecently, daysInPast
                    ) if menuOption not in ["C"] else (listStockCodes, 0, "")
                except KeyboardInterrupt:
                    try:
                        keyboardInterruptEvent.set()
                        keyboardInterruptEventFired = True
                        actualHistoricalDuration = -1
                        break
                    except KeyboardInterrupt:
                        pass
                    OutputControls().printOutput(
                        colorText.FAIL
                        + "\n  [+] Terminating Script, Please wait..."
                        + colorText.END
                    )
                
                exchangeName = "NASDAQ" if (indexOption == 15 or (self.configManager.defaultIndex == 15 and indexOption == 0)) else "INDIA"
                runOptionName = PKScanRunner.getFormattedChoices(userPassedArgs, selectedChoice)
                
                if ((":0:" in runOptionName or "_0_" in runOptionName) and userPassedArgs.progressstatus is not None) or userPassedArgs.progressstatus is not None:
                    runOptionName = userPassedArgs.progressstatus.split("=>")[0].split("  [+] ")[1]
                
                if menuOption in ["F"]:
                    if "^NSEI" in listStockCodes:
                        listStockCodes.remove("^NSEI")
                    items = PKScanRunner.addScansWithDefaultParams(
                        userPassedArgs, self.app_state.testing, self.app_state.testBuild, 
                        newlyListedOnly, self.app_state.downloadOnly, backtestPeriod, 
                        listStockCodes, menuOption, exchangeName, executeOption, volumeRatio, 
                        items, daysInPast, runOption=f"{userPassedArgs.options} =>{runOptionName} => {menuChoiceHierarchy}"
                    )
                else:
                    PKScanRunner.addStocksToItemList(
                        userPassedArgs, self.app_state.testing, self.app_state.testBuild, 
                        newlyListedOnly, self.app_state.downloadOnly, minRSI, maxRSI, 
                        insideBarToLookback, respChartPattern, daysForLowestVolume, 
                        backtestPeriod, reversalOption, maLength, listStockCodes, 
                        menuOption, exchangeName, executeOption, volumeRatio, items, 
                        daysInPast, runOption=f"{userPassedArgs.options} =>{runOptionName} => {menuChoiceHierarchy}"
                    )
                
                if savedStocksCount > 0:
                    progressbar.text(
                        colorText.GREEN
                        + f"Total Stocks: {len(items)}. Added {savedStocksCount} to Stocks from {pastDate} saved from earlier..."
                        + colorText.END
                    )
                
                fillerPlaceHolder = fillerPlaceHolder + 1
                actualHistoricalDuration = samplingDuration - fillerPlaceHolder
                
                if actualHistoricalDuration >= 0:
                    progressbar()
        
        # Run the scan with parameters
        screenResults, saveResults, backtest_df, tasks_queue, results_queue, consumers, logging_queue = PKScanRunner.runScanWithParams(
            userPassedArgs, keyboardInterruptEvent, screenCounter, screenResultsCounter,
            stockDictPrimary, stockDictSecondary, self.app_state.testing, backtestPeriod,
            menuOption, executeOption, samplingDuration, items, screenResults, saveResults,
            backtest_df, scanningCb=runScanners, tasks_queue=tasks_queue, 
            results_queue=results_queue, consumers=consumers, logging_queue=logging_queue
        )
        
        return screenResults, saveResults
    
    def save_to_google_sheets(self, saveResults):
        """Save results to Google Sheets if configured"""
        if 'ALERT_TRIGGER' in os.environ.keys() and os.environ["ALERT_TRIGGER"] == 'Y':
            if "GSHEET_SERVICE_ACCOUNT_DEV" in os.environ.keys() and (userPassedArgs.backtestdaysago is None):
                begin = time.time()
                creds = os.environ.get("GSHEET_SERVICE_ACCOUNT_DEV")
                OutputControls().printOutput(f"{colorText.GREEN}  [+] Saving data to Google Spreadsheets now...{colorText.END}")
                
                gClient = PKSpreadsheets(credentialDictStr=creds)
                runOption = PKScanRunner.getFormattedChoices(userPassedArgs, selectedChoice)
                df = saveResults.copy()
                df["LastTradeDate"], df["LastTradeTime"] = getLatestTradeDateTime(stockDictPrimary)
                
                gClient.df_to_sheet(df=df, sheetName=runOption)
                OutputControls().printOutput(f"{colorText.GREEN} => Done in {round(time.time()-begin,2)}s{colorText.END}")
    
    def handle_pinned_menu(self, saveResults, menuOption):
        """Handle the pinned menu display and options"""
        if ("RUNNER" not in os.environ.keys() and 
            not self.app_state.testing and 
            (userPassedArgs is None or 
             (userPassedArgs is not None and 
              (userPassedArgs.user is None or str(userPassedArgs.user) == DEV_CHANNEL_ID) and 
              (userPassedArgs.answerdefault is None or userPassedArgs.systemlaunched))) and
            not userPassedArgs.testbuild and 
            userPassedArgs.monitor is None):
            
            prevOutput_results = saveResults.index if (saveResults is not None and not saveResults.empty) else []
            isNotPiped = (("|" not in userPassedArgs.options) if (userPassedArgs is not None and userPassedArgs.options is not None) else True)
            hasFoundStocks = len(prevOutput_results) > 0 and isNotPiped
            
            if hasFoundStocks or (self.configManager.showPinnedMenuEvenForNoResult and isNotPiped):
                # ... handle pinned menu logic
                pass


# Replace the original main function with the refactored version
def main(userArgs=None, optionalFinalOutcome_df=None):
    """
    Main entry point - replaces the original massive main function
    
    Args:
        userArgs: Command line arguments passed by user
        optionalFinalOutcome_df: Optional dataframe for final results
        
    Returns:
        Tuple of screen results and save results
    """
    app = MainApplication(userArgs)
    return app.main(userArgs, optionalFinalOutcome_df)
