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
# Keep module imports prior to classes
import os
import random
import warnings
warnings.simplefilter("ignore", UserWarning,append=True)
os.environ["PYTHONWARNINGS"]="ignore::UserWarning"
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
from PKDevTools.classes.log import default_logger #, tracelog
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
from pkscreener.classes import Utility,ConsoleUtility, ConsoleMenuUtility, ImageUtility
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

# Import modular components for refactored functionality
from pkscreener.classes.CoreFunctions import (
    get_review_date as _get_review_date,
    get_max_allowed_results_count as _get_max_allowed_results_count,
    get_iterations_and_stock_counts as _get_iterations_and_stock_counts,
    process_single_result as _process_single_result,
    update_backtest_results as _update_backtest_results,
)
from pkscreener.classes.OutputFunctions import (
    show_option_error_message as _show_option_error_message,
    cleanup_local_results as _cleanup_local_results,
    describe_user as _describe_user,
    toggle_user_config as _toggle_user_config,
    reset_config_to_default as _reset_config_to_default,
    get_backtest_report_filename as _get_backtest_report_filename,
    save_screen_results_encoded as _save_screen_results_encoded,
    read_screen_results_decoded as _read_screen_results_decoded,
    remove_unknowns as _remove_unknowns,
    removed_unused_columns as _removed_unused_columns,
)
from pkscreener.classes.MenuNavigation import update_menu_choice_hierarchy_impl
from pkscreener.classes.MainLogic import (handle_secondary_menu_choices_impl,
    MenuOptionHandler, GlobalStateProxy, create_menu_handler, 
    handle_mdilf_menus, handle_predefined_menu, handle_backtest_menu, handle_strategy_menu
)
from pkscreener.classes.ExecuteOptionHandlers import (
    handle_execute_option_3, handle_execute_option_4, handle_execute_option_5,
    handle_execute_option_6, handle_execute_option_7, handle_execute_option_8,
    handle_execute_option_9, handle_execute_option_12, handle_execute_option_21,
    handle_execute_option_22, handle_execute_option_30, handle_execute_option_31,
    handle_execute_option_33, handle_execute_option_34, handle_execute_option_40,
    handle_execute_option_41, handle_execute_option_42_43
)
from pkscreener.classes.NotificationService import (
    send_message_to_telegram_channel_impl,
    handle_alert_subscriptions_impl,
    send_test_status_impl
)
from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
from pkscreener.classes.BacktestUtils import (
    show_backtest_results_impl, 
    tabulate_backtest_results_impl,
    finish_backtest_data_cleanup_impl,
    prepare_grouped_xray_impl,
    show_sorted_backtest_data_impl
)
from pkscreener.classes.DataLoader import save_downloaded_data_impl

if __name__ == '__main__':
    multiprocessing.freeze_support()
# import dataframe_image as dfi
# import df2img
# Try Fixing bug with this symbol
TEST_STKCODE = "SBIN"
# Constants
np.seterr(divide="ignore", invalid="ignore")

# Variabls
configManager = ConfigManager.tools()
configManager.getConfig(ConfigManager.parser)
defaultAnswer = None
fetcher = Fetcher.screenerStockDataFetcher(configManager)
mstarFetcher = morningstarDataFetcher(configManager)
keyboardInterruptEvent = None
keyboardInterruptEventFired=False
loadCount = 0
loadedStockData = False
m0 = menus()
m1 = menus()
m2 = menus()
m3 = menus()
m4 = menus()
maLength = None
nValueForMenu = 0
menuChoiceHierarchy = ""
newlyListedOnly = False
screenCounter = None
screener = ScreeningStatistics.ScreeningStatistics(configManager, default_logger())
screenResults = None
backtest_df = None
screenResultsCounter = None
selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
stockDictPrimary = None
stockDictSecondary = None
userPassedArgs = None
elapsed_time = 0
start_time = 0
scanCycleRunning = False
test_messages_queue = None
strategyFilter=[]
listStockCodes = None
lastScanOutputStockCodes = None
tasks_queue = None
results_queue = None
consumers = None
logging_queue = None
mp_manager = None
analysis_dict = {}
download_trials = 0
media_group_dict = {}
DEV_CHANNEL_ID="-1001785195297"
criteria_dateTime = None
saved_screen_results = None
show_saved_diff_results = False
resultsContentsEncoded = None
runCleanUp = False

def startMarketMonitor(mp_dict,keyboardevent):
    if not 'pytest' in sys.modules:
        from PKDevTools.classes.NSEMarketStatus import NSEMarketStatus
        NSEMarketStatus(mp_dict,keyboardevent).startMarketMonitor()

def finishScreening(
    downloadOnly,
    testing,
    stockDictPrimary,
    configManager,
    loadCount,
    testBuild,
    screenResults,
    saveResults,
    user=None,
):
    global defaultAnswer, menuChoiceHierarchy, userPassedArgs, selectedChoice
    if "RUNNER" not in os.environ.keys() or downloadOnly:
        # There's no need to prompt the user to save xls report or to save data locally.
        # This scan must have been triggered by github workflow by a user or scheduled job
        saveDownloadedData(downloadOnly, testing, stockDictPrimary, configManager, loadCount)
    if not testBuild and not downloadOnly and not testing and ((userPassedArgs is not None and "|" not in userPassedArgs.options) or userPassedArgs is None):
        saveNotifyResultsFile(
            screenResults, saveResults, defaultAnswer, menuChoiceHierarchy, user=user
        )
    if ("RUNNER" in os.environ.keys() and not downloadOnly) or userPassedArgs.log:
        sendMessageToTelegramChannel(mediagroup=True,user=userPassedArgs.user)

def getDownloadChoices(defaultAnswer=None):
    global userPassedArgs
    argsIntraday = userPassedArgs is not None and userPassedArgs.intraday is not None
    intradayConfig = configManager.isIntradayConfig()
    intraday = intradayConfig or argsIntraday
    exists, cache_file = AssetsManager.PKAssetsManager.afterMarketStockDataExists(intraday)
    if exists:
        shouldReplace = AssetsManager.PKAssetsManager.promptFileExists(
            cache_file=cache_file, defaultAnswer=defaultAnswer
        )
        if shouldReplace == "N":
            OutputControls().printOutput(
                cache_file
                + colorText.END
                + " already exists. Exiting as user chose not to replace it!"
            )
            PKAnalyticsService().send_event("app_exit")
            sys.exit(0)
        else:
            pattern = f"{'intraday_' if intraday else ''}stock_data_*.pkl"
            configManager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(),pattern=pattern)
    return "X", 12, 0, {"0": "X", "1": "12", "2": "0"}


def getHistoricalDays(numStocks, testing):
    # Generally it takes 40-50 stocks to be processed every second.
    # We would like the backtest to finish withn 10 minutes (600 seconds).
    # days = numStocks/40 per second
    return (
        2 if testing else configManager.backtestPeriod
    )  # if numStocks <= 2000 else 120 # (5 if iterations < 5 else (100 if iterations > 100 else iterations))


def getScannerMenuChoices(
    testBuild=False,
    downloadOnly=False,
    startupoptions=None,
    menuOption=None,
    indexOption=None,
    executeOption=None,
    defaultAnswer=None,
    user=None,
):
    global selectedChoice
    executeOption = executeOption
    menuOption = menuOption
    indexOption = indexOption
    try:
        if menuOption is None:
            selectedMenu = initExecution(menuOption=menuOption)
            menuOption = selectedMenu.menuKey
        if menuOption in ["H", "U", "T", "E", "Y"]:
            handleSecondaryMenuChoices(
                menuOption, testBuild, defaultAnswer=defaultAnswer, user=user
            )
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        elif menuOption in ["X","C"]:
            indexOption, executeOption = initPostLevel0Execution(
                menuOption=menuOption,
                indexOption=indexOption,
                executeOption=executeOption,
            )
            indexOption, executeOption = initPostLevel1Execution(
                indexOption=indexOption, executeOption=executeOption
            )
    except KeyboardInterrupt: # pragma: no cover
        OutputControls().takeUserInput(
            colorText.FAIL
            + "  [+] Press <Enter> to Exit!"
            + colorText.END
        )
        PKAnalyticsService().send_event("app_exit")
        sys.exit(0)
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
    return menuOption, indexOption, executeOption, selectedChoice


def getSummaryCorrectnessOfStrategy(resultdf, summaryRequired=True):
    summarydf = None
    detaildf = None
    try:
        if resultdf is None or len(resultdf) == 0:
            return None, None
        results = resultdf.copy()
        if summaryRequired:
            _, reportNameSummary = getBacktestReportFilename(optionalName="Summary")
            dfs = pd.read_html(
                "https://pkjmesra.github.io/PKScreener/Backtest-Reports/{0}".format(
                    reportNameSummary.replace("_X_", "_B_").replace("_G_", "_B_").replace("_S_", "_B_")
                ),encoding="UTF-8", attrs = {'id': 'resultsTable'}
            )
        _, reportNameDetail = getBacktestReportFilename()
        dfd = pd.read_html(
            "https://pkjmesra.github.io/PKScreener/Backtest-Reports/{0}".format(
                reportNameDetail.replace("_X_", "_B_").replace("_G_", "_B_").replace("_S_", "_B_")
            ),encoding="UTF-8", attrs = {'id': 'resultsTable'}
        )

        if summaryRequired and dfs is not None and len(dfs) > 0:
            df = dfs[0]
            summarydf = df[df["Stock"] == "SUMMARY"]
            for col in summarydf.columns:
                summarydf.loc[:, col] = summarydf.loc[:, col].apply(
                    lambda x: ConsoleUtility.PKConsoleTools.getFormattedBacktestSummary(
                        x, columnName=col
                    )
                )
            summarydf = summarydf.replace(np.nan, "", regex=True)
        if dfd is not None and len(dfd) > 0:
            df = dfd[0]
            results.reset_index(inplace=True)
            detaildf = df[df["Stock"].isin(results["Stock"])]
            for col in detaildf.columns:
                detaildf.loc[:, col] = detaildf.loc[:, col].apply(
                    lambda x: ConsoleUtility.PKConsoleTools.getFormattedBacktestSummary(
                        x, pnlStats=True, columnName=col
                    )
                )
            detaildf = detaildf.replace(np.nan, "", regex=True)
            detaildf.loc[:, "volume"] = detaildf.loc[:, "volume"].apply(
                lambda x: Utility.tools.formatRatio(x, configManager.volumeRatio)
            )
            detaildf.sort_values(
                ["Stock", "Date"], ascending=[True, False], inplace=True
            )
            detaildf.rename(
                columns={
                    "LTP": "LTP on Date",
                },
                inplace=True,
            )
    except urllib.error.HTTPError as e: # pragma: no cover
        if "HTTP Error 404" in str(e):
            pass
        else:
            default_logger().debug(e, exc_info=True)
    except Exception as e:# pragma: no cover
        default_logger().debug(e, exc_info=True)
        pass
    return summarydf, detaildf


def getTestBuildChoices(indexOption=None, executeOption=None, menuOption=None):
    if menuOption is not None:
        return (
            str(menuOption),
            indexOption if indexOption is not None else 1,
            executeOption if executeOption is not None else 0,
            {
                "0": str(menuOption),
                "1": (str(indexOption) if indexOption is not None else 1),
                "2": (str(executeOption) if executeOption is not None else 0),
            },
        )
    return "X", 1, 0, {"0": "X", "1": "1", "2": "0"}


def getTopLevelMenuChoices(startupoptions, testBuild, downloadOnly, defaultAnswer=None):
    global selectedChoice, userPassedArgs, lastScanOutputStockCodes
    executeOption = None
    menuOption = None
    indexOption = None
    options = []
    if startupoptions is not None:
        options = startupoptions.split(":")
        menuOption = options[0] if len(options) >= 1 else None
        indexOption = options[1] if len(options) >= 2 else None
        executeOption = options[2] if len(options) >= 3 else None
    if testBuild:
        menuOption, indexOption, executeOption, selectedChoice = getTestBuildChoices(
            indexOption=indexOption,
            executeOption=executeOption,
            menuOption=menuOption,
        )
    elif downloadOnly:
        menuOption, indexOption, executeOption, selectedChoice = getDownloadChoices(
            defaultAnswer=defaultAnswer
        )
        intraday = userPassedArgs.intraday or configManager.isIntradayConfig()
        filePrefix = "INTRADAY_" if intraday else ""
        _, cache_file_name = AssetsManager.PKAssetsManager.afterMarketStockDataExists(intraday)
        Utility.tools.set_github_output(f"{filePrefix}DOWNLOAD_CACHE_FILE_NAME",cache_file_name)
    indexOption = 0 if lastScanOutputStockCodes is not None else indexOption
    return options, menuOption, indexOption, executeOption


def handleScannerExecuteOption4(executeOption, options):
    try:
        # m2.find(str(executeOption))
        if len(options) >= 4:
            if str(options[3]).upper() == "D":
                # Use a default value
                daysForLowestVolume = 5
            else:
                daysForLowestVolume = int(options[3])
        else:
            daysForLowestVolume = int(
                input(
                    colorText.WARN
                    + "\n  [+] The Volume should be lowest since last how many candles? (Default = 5)"
                ) or "5"
            )
    except ValueError as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(colorText.END)
        OutputControls().printOutput(
            colorText.FAIL
            + "  [+] Error: Non-numeric value entered! Please try again!"
            + colorText.END
        )
        OutputControls().takeUserInput("Press <Enter> to continue...")
        return
    OutputControls().printOutput(colorText.END)
    global nValueForMenu 
    nValueForMenu = daysForLowestVolume
    return daysForLowestVolume


def handleSecondaryMenuChoices(
    menuOption, testing=False, defaultAnswer=None, user=None
):
    """Handle secondary menu choices - delegates to MainLogic module"""
    global userPassedArgs, resultsContentsEncoded
    return handle_secondary_menu_choices_impl(
        menuOption, m0, m1, m2, configManager, userPassedArgs, resultsContentsEncoded,
        testing, defaultAnswer, user,
        showSendConfigInfo, showSendHelpInfo, toggleUserConfig, sendMessageToTelegramChannel
    )

def showSendConfigInfo(defaultAnswer=None, user=None):
    configData = configManager.showConfigFile(defaultAnswer=('Y' if user is not None else defaultAnswer))
    if user is not None:
        sendMessageToTelegramChannel(message=ImageUtility.PKImageTools.removeAllColorStyles(configData), user=user)
    if defaultAnswer is None:
        input("Press any key to continue...")

def showSendHelpInfo(defaultAnswer=None, user=None):
    helpData = ConsoleUtility.PKConsoleTools.showDevInfo(defaultAnswer=('Y' if user is not None else defaultAnswer))
    if user is not None:
        sendMessageToTelegramChannel(message=ImageUtility.PKImageTools.removeAllColorStyles(helpData), user=user)
    if defaultAnswer is None:
        input("Press any key to continue...")

def ensureMenusLoaded(menuOption=None,indexOption=None,executeOption=None):
    try:
        if len(m0.menuDict.keys()) == 0:
            m0.renderForMenu(asList=True)
        if len(m1.menuDict.keys()) == 0:
            m1.renderForMenu(selectedMenu=m0.find(menuOption),asList=True)
        if len(m2.menuDict.keys()) == 0:
            m2.renderForMenu(selectedMenu=m1.find(indexOption),asList=True)
        if len(m3.menuDict.keys()) == 0:
            m3.renderForMenu(selectedMenu=m2.find(executeOption),asList=True)
    except Exception as e:
        default_logger().debug(f"Error loading menus: {e}")

def initExecution(menuOption=None):
    global selectedChoice, userPassedArgs
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None):
        OutputControls().printOutput(
        colorText.FAIL
        + "  [+] You chose: "
        + f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]"
        + colorText.END
    )
    m0.renderForMenu(selectedMenu=None,asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    try:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)}{colorText.END} ]\n" if needsCalc else ""
        if menuOption is None:
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                from PKDevTools.classes import Archiver
                log_file_path = os.path.join(Archiver.get_user_data_dir(), "pkscreener-logs.txt")
                OutputControls().printOutput(colorText.FAIL + "\n      [+] Logs will be written to:"+colorText.END)
                OutputControls().printOutput(colorText.GREEN + f"      [+] {log_file_path}"+colorText.END)
                OutputControls().printOutput(colorText.FAIL + "      [+] If you need to share,run through the menus that are causing problems. At the end, open this folder, zip the log file to share at https://github.com/pkjmesra/PKScreener/issues .\n" + colorText.END)
            # In non-interactive mode (bot/systemlaunched), default to X (Scanners) not P (Piped Scanners)
            # to avoid infinite loops where P triggers another P selection
            defaultMenuOption = "X" if (userPassedArgs is not None and (userPassedArgs.systemlaunched or userPassedArgs.answerdefault is not None or userPassedArgs.telegram)) else "P"
            menuOption = OutputControls().takeUserInput(colorText.FAIL + f"{pastDate}  [+] Select option: ", defaultInput=defaultMenuOption)
            OutputControls().printOutput(colorText.END, end="")
        if menuOption == "" or menuOption is None:
            menuOption = "X"
        menuOption = menuOption.upper()
        selectedMenu = m0.find(menuOption)
        if selectedMenu is not None:
            if selectedMenu.menuKey == "Z":
                OutputControls().takeUserInput(
                    colorText.FAIL
                    + "  [+] Press <Enter> to Exit!"
                    + colorText.END
                )
                PKAnalyticsService().send_event("app_exit")
                sys.exit(0)
            elif selectedMenu.menuKey in ["B", "C", "G", "H", "U", "T", "S", "E", "X", "Y", "M", "D", "I", "L","F"]:
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                selectedChoice["0"] = selectedMenu.menuKey
                return selectedMenu
            elif selectedMenu.menuKey in ["P"]:
                return selectedMenu
    except KeyboardInterrupt: # pragma: no cover
        raise KeyboardInterrupt
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        showOptionErrorMessage()
        return initExecution()

    showOptionErrorMessage()
    return initExecution()


def initPostLevel0Execution(
    menuOption=None, indexOption=None, executeOption=None, skip=[], retrial=False
):
    global newlyListedOnly, selectedChoice, userPassedArgs
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    if menuOption is None:
        OutputControls().printOutput('You must choose an option from the previous menu! Defaulting to "X"...')
        menuOption = "X"
    OutputControls().printOutput(
        colorText.FAIL
        + "  [+] You chose: "
        + level0MenuDict[menuOption].strip() 
        + (f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]" if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None) else "")
        + colorText.END
    )
    if indexOption is None:
        selectedMenu = m0.find(menuOption)
        m1.renderForMenu(selectedMenu=selectedMenu, skip=skip,asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    try:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)}{colorText.END} ]\n" if needsCalc else ""
        if indexOption is None:
            indexOption = OutputControls().takeUserInput(
                colorText.FAIL + f"{pastDate}  [+] Select option: "
            )
            OutputControls().printOutput(colorText.END, end="")
        if (str(indexOption).isnumeric() and int(indexOption) > 1 and str(executeOption).isnumeric() and int(str(executeOption)) <= MAX_SUPPORTED_MENU_OPTION) or \
            str(indexOption).upper() in ["S", "E", "W"]:
            ensureMenusLoaded(menuOption,indexOption,executeOption)
            if not PKPremiumHandler.hasPremium(m1.find(str(indexOption).upper())):
                PKAnalyticsService().send_event(f"non_premium_user_{menuOption}_{indexOption}_{executeOption}")
                return None, None
        if indexOption == "" or indexOption is None:
            indexOption = int(configManager.defaultIndex)
        # elif indexOption == 'W' or indexOption == 'w' or indexOption == 'N' or indexOption == 'n' or indexOption == 'E' or indexOption == 'e':
        elif not str(indexOption).isnumeric():
            indexOption = indexOption.upper()
            if indexOption in ["M", "E", "N", "Z"]:
                return indexOption, 0
        else:
            indexOption = int(indexOption)
            if indexOption < 0 or indexOption > 15:
                raise ValueError
            elif indexOption == 13:
                configManager.period = "2y"
                configManager.getConfig(ConfigManager.parser)
                newlyListedOnly = True
                indexOption = 12
        if indexOption == 15:
            from pkscreener.classes.MarketStatus import MarketStatus
            MarketStatus().exchange = "^IXIC"
        selectedChoice["1"] = str(indexOption)
    except KeyboardInterrupt: # pragma: no cover
        raise KeyboardInterrupt
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(
            colorText.FAIL
            + "\n  [+] Please enter a valid numeric option & Try Again!"
            + colorText.END
        )
        if not retrial:
            sleep(2)
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            return initPostLevel0Execution(retrial=True)
    return indexOption, executeOption


def initPostLevel1Execution(indexOption, executeOption=None, skip=[], retrial=False):
    global selectedChoice, userPassedArgs, listStockCodes
    listStockCodes = [] if listStockCodes is None or len(listStockCodes) == 0 else listStockCodes
    if executeOption is None:
        if indexOption is not None and indexOption != "W":
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] You chose: "
                + level0MenuDict[selectedChoice["0"]].strip()
                + " > "
                + level1_X_MenuDict[selectedChoice["1"]].strip()
                + (f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]" if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None) else "")
                + colorText.END
            )
            selectedMenu = m1.find(indexOption)
            m2.renderForMenu(selectedMenu=selectedMenu, skip=skip,asList=(userPassedArgs is not None and userPassedArgs.options is not None))
            stockIndexCode = str(len(level1_index_options_sectoral.keys()))
            if indexOption == "S":
                ensureMenusLoaded("X",indexOption,executeOption)
                if not PKPremiumHandler.hasPremium(selectedMenu):
                    PKAnalyticsService().send_event(f"non_premium_user_X_{indexOption}_{executeOption}")
                    PKAnalyticsService().send_event("app_exit")
                    sys.exit(0)
                indexKeys = level1_index_options_sectoral.keys()
                stockIndexCode = OutputControls().takeUserInput(
                    colorText.FAIL + "  [+] Select option: "
                ) or str(len(indexKeys))
                OutputControls().printOutput(colorText.END, end="")
                
                if stockIndexCode == str(len(indexKeys)):
                    for indexCode in indexKeys:
                        if indexCode != str(len(indexKeys)):
                            listStockCodes.append(level1_index_options_sectoral[str(indexCode)].split("(")[1].split(")")[0])
                else:
                    listStockCodes = [level1_index_options_sectoral[str(stockIndexCode)].split("(")[1].split(")")[0]]
                selectedMenu.menuKey = "0" # Reset because user must have selected specific index menu with single stock
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                m2.renderForMenu(selectedMenu=selectedMenu, skip=skip,asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    try:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)}{colorText.END} ]\n" if needsCalc else ""
        if indexOption is not None and indexOption != "W":
            if executeOption is None:
                executeOption = OutputControls().takeUserInput(
                    colorText.FAIL + f"{pastDate}  [+] Select option: "
                ) or "9"
                OutputControls().printOutput(colorText.END, end="")
            ensureMenusLoaded("X",indexOption,executeOption)
            if not PKPremiumHandler.hasPremium(m2.find(str(executeOption))):
                PKAnalyticsService().send_event(f"non_premium_user_X_{indexOption}_{executeOption}")
                return None, None
            if executeOption == "":
                executeOption = 1
            if not str(executeOption).isnumeric():
                executeOption = executeOption.upper()
            else:
                executeOption = int(executeOption)
                if executeOption < 0 or executeOption > MAX_MENU_OPTION: # or (executeOption > MAX_SUPPORTED_MENU_OPTION and executeOption < MAX_MENU_OPTION):
                    raise ValueError
        else:
            executeOption = 0
        selectedChoice["2"] = str(executeOption)
    except KeyboardInterrupt: # pragma: no cover
        raise KeyboardInterrupt
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(
            colorText.FAIL
            + "\n  [+] Please enter a valid numeric option & Try Again!"
            + colorText.END
        )
        if not retrial:
            sleep(2)
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            return initPostLevel1Execution(indexOption, executeOption, retrial=True)
    return indexOption, executeOption

def labelDataForPrinting(screenResults, saveResults, configManager, volumeRatio, executeOption, reversalOption, menuOption):
    """Label data for printing - delegates to ResultsLabeler module"""
    global menuChoiceHierarchy, userPassedArgs
    return label_data_for_printing_impl(
        screen_results=screenResults,
        save_results=saveResults,
        config_manager=configManager,
        volume_ratio=volumeRatio,
        execute_option=executeOption,
        reversal_option=reversalOption,
        menu_option=menuOption,
        menu_choice_hierarchy=menuChoiceHierarchy,
        user_passed_args=userPassedArgs
    )

def isInterrupted():
    global keyboardInterruptEventFired
    return keyboardInterruptEventFired

def resetUserMenuChoiceOptions():
    global menuChoiceHierarchy, userPassedArgs, media_group_dict
    media_group_dict = {}
    menuChoiceHierarchy = ""
    userPassedArgs.pipedtitle = ""

@Halo(text='', spinner='dots')
def refreshStockData(startupoptions=None):
    global consumers,stockDictPrimary, loadedStockData, listStockCodes, stockDictSecondary, menuChoiceHierarchy
    menuChoiceHierarchy = ""
    options = startupoptions.replace("|","").split(" ")[0].replace(":i","")
    loadedStockData = False
    options, menuOption, indexOption, executeOption = getTopLevelMenuChoices(
        options, False, False, defaultAnswer='Y'
    )
    if indexOption == 0:
        listStockCodes = handleRequestForSpecificStocks(options,indexOption=indexOption)
    listStockCodes = prepareStocksForScreening(testing=False, downloadOnly=False, listStockCodes=listStockCodes,indexOption=indexOption)
    try:
        import tensorflow as tf
        with tf.device("/device:GPU:0"):
            stockDictPrimary,stockDictSecondary = loadDatabaseOrFetch(downloadOnly=False, listStockCodes=listStockCodes, menuOption=menuOption,indexOption=indexOption)
    except: # pragma: no cover
        stockDictPrimary,stockDictSecondary = loadDatabaseOrFetch(downloadOnly=False, listStockCodes=listStockCodes, menuOption=menuOption,indexOption=indexOption)
        pass
    PKScanRunner.refreshDatabase(consumers,stockDictPrimary,stockDictSecondary)

def closeWorkersAndExit():
    global consumers, tasks_queue,userPassedArgs
    if consumers is not None:
        PKScanRunner.terminateAllWorkers(userPassedArgs=userPassedArgs,consumers=consumers, tasks_queue=tasks_queue, testing=userPassedArgs.testbuild)

def main(userArgs=None,optionalFinalOutcome_df=None):
    global lastScanOutputStockCodes,scanCycleRunning,runCleanUp,test_messages_queue,show_saved_diff_results, criteria_dateTime, analysis_dict, mp_manager, listStockCodes, screenResults, selectedChoice, defaultAnswer, menuChoiceHierarchy, screenCounter, screenResultsCounter, stockDictPrimary, stockDictSecondary, userPassedArgs, loadedStockData, keyboardInterruptEvent, loadCount, maLength, newlyListedOnly, keyboardInterruptEventFired,strategyFilter, elapsed_time, start_time
    selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
    elapsed_time = 0 if not scanCycleRunning else elapsed_time
    start_time = 0 if not scanCycleRunning else start_time
    testing = False if userArgs is None else (userArgs.testbuild and userArgs.prodbuild)
    testBuild = False if userArgs is None else (userArgs.testbuild and not testing)
    downloadOnly = False if userArgs is None else userArgs.download
    startupoptions = None if userArgs is None else userArgs.options
    user = None if userArgs is None else userArgs.user
    defaultAnswer = None if userArgs is None else userArgs.answerdefault
    userPassedArgs = userArgs
    runOptionName = ""
    options = []
    strategyFilter=[]
    test_messages_queue = []
    describeUser()
    if keyboardInterruptEventFired:
        return None, None
    
    if userPassedArgs is not None and userPassedArgs.runintradayanalysis and "C:" in startupoptions and "|" in startupoptions:
        firstScanKey = startupoptions.split(">|")[0]
        if firstScanKey.startswith("X:12:") and firstScanKey in analysis_dict.keys():
            savedAnalysisDict = analysis_dict.get(firstScanKey)
            return analysisFinalResults(savedAnalysisDict.get("S1"),savedAnalysisDict.get("S2"),optionalFinalOutcome_df,None)

    screenCounter = multiprocessing.Value("i", 1)
    screenResultsCounter = multiprocessing.Value("i", 0)
    if mp_manager is None:
        mp_manager = multiprocessing.Manager()
        
    if keyboardInterruptEvent is None and not keyboardInterruptEventFired:
        keyboardInterruptEvent = mp_manager.Event()
        mkt_monitor_dict = mp_manager.dict()
        # Let's start monitoring the market monitor
        startMarketMonitor(mkt_monitor_dict,keyboardInterruptEvent)
        
    keyboardInterruptEventFired = False
    if stockDictPrimary is None or isinstance(stockDictPrimary,dict):
        stockDictPrimary = mp_manager.dict()
        stockDictSecondary = mp_manager.dict()
        loadCount = 0
    endOfdayCandles = None
    minRSI = 0
    maxRSI = 100
    insideBarToLookback = 7
    respChartPattern = None
    daysForLowestVolume = 30
    backtestPeriod = 0
    reversalOption = None
    listStockCodes = None if lastScanOutputStockCodes is None else lastScanOutputStockCodes
    lastScanOutputStockCodes = None
    if not runCleanUp and userPassedArgs is not None and not userPassedArgs.systemlaunched:
        cleanupLocalResults()
    if userPassedArgs.log:
        default_logger().debug(f"User Passed args: {userPassedArgs}")
    screenResults, saveResults = PKScanRunner.initDataframes()
    options, menuOption, indexOption, executeOption = getTopLevelMenuChoices(
        startupoptions, testBuild, downloadOnly, defaultAnswer=defaultAnswer
    )
    # Print Level 1 menu options
    selectedMenu = initExecution(menuOption=menuOption)
    menuOption = selectedMenu.menuKey
    if menuOption in ["F", "M", "S", "B", "G", "C", "P", "D"] or selectedMenu.isPremium:
        ensureMenusLoaded(menuOption,indexOption,executeOption)
        if not PKPremiumHandler.hasPremium(selectedMenu):
            PKAnalyticsService().send_event(f"non_premium_user_{menuOption}_{indexOption}_{executeOption}")
            PKAnalyticsService().send_event("app_exit")
            sys.exit(0)
    if menuOption in ["M", "D", "I", "L", "F"]:
        # Delegate to MainLogic module for M, D, I, L, F menu handling
        should_return_early, listStockCodes, _idx, _exec = handle_mdilf_menus(
            menuOption, m0, m1, m2, configManager, fetcher, userPassedArgs, selectedChoice, listStockCodes
        )
        if menuOption == "F":
            indexOption = 0
            executeOption = None
        if should_return_early:
            return None, None
    if menuOption in ["P"]:
        # Delegate to MainLogic for P menu handling
        should_return, new_menu, listStockCodes = handle_predefined_menu(
            options, m0, m1, m2, configManager, userPassedArgs, selectedChoice,
            listStockCodes, defaultAnswer, resultsContentsEncoded,
            updateMenuChoiceHierarchy, addOrRunPipedMenus
        )
        if should_return:
            if new_menu is None:
                # If pipedmenus exists and we're returning early, run the piped menus
                if userPassedArgs.pipedmenus is not None:
                    return addOrRunPipedMenus()
                return None, None
        if new_menu == "X":
            menuOption = "X"
            selectedMenu = m0.find(menuOption)
    if menuOption in ["X", "T", "E", "Y", "U", "H", "C"]:
        # Print Level 2 menu options
        menuOption, indexOption, executeOption, selectedChoice = getScannerMenuChoices(
            testBuild or testing,
            downloadOnly,
            startupoptions,
            menuOption=menuOption,
            indexOption=indexOption,
            executeOption=executeOption,
            defaultAnswer=defaultAnswer,
            user=user,
        )
        if indexOption is None:
            return None, None
        
        if menuOption in ["H", "U", "T", "E", "Y"]:
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            return None, None
    elif menuOption in ["B", "G"]:
        indexOption, executeOption, backtestPeriod = handle_backtest_menu(
            options, menuOption, indexOption, executeOption, configManager, takeBacktestInputs
        )
    elif menuOption in ["S"]:
        # Delegate to MainLogic for S menu handling
        should_return, new_menu, indexOption, executeOption, sc = handle_strategy_menu(
            options, m0, m1, defaultAnswer, strategyFilter, getScannerMenuChoices,
            testBuild, testing, downloadOnly, startupoptions, indexOption, executeOption, user
        )
        if should_return:
            if new_menu is None:
                return None, None
        if new_menu == "X":
            menuOption = "X"
            selectedChoice = sc

    else:
        if menuOption not in ["F"]:
            OutputControls().printOutput("Not implemented yet! Try selecting a different option.")
            sleep(3)
            return None, None

    handleMenu_XBG(menuOption, indexOption, executeOption)
    if str(indexOption).upper() == "M" or str(executeOption).upper() == "M":
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        # Go back to the caller. It will show the console menu again.
        return None, None
    listStockCodes = handleRequestForSpecificStocks(options, indexOption)
    handleExitRequest(executeOption)
    if executeOption is None:
        executeOption = 0
    executeOption = int(executeOption)
    volumeRatio = configManager.volumeRatio
    if executeOption == 3:
        userPassedArgs.maxdisplayresults = max(configManager.maxdisplayresults,2000) # force evaluate all stocks before getting the top results
    if executeOption == 4:
        daysForLowestVolume = handleScannerExecuteOption4(executeOption, options)
    if executeOption == 5:
        minRSI, maxRSI = handle_execute_option_5(options, userPassedArgs, m2)
        if minRSI is None:
            return None, None
    if executeOption == 6:
        reversalOption, maLength = handle_execute_option_6(options, userPassedArgs, defaultAnswer, user, m2, selectedChoice)
        if reversalOption is None:
            return None, None
    if executeOption == 7:
        respChartPattern, insideBarToLookback, maLength = handle_execute_option_7(
            options, userPassedArgs, defaultAnswer, user, m0, m2, selectedChoice, configManager
        )
        if respChartPattern is None:
            return None, None
    if executeOption == 8:
        minRSI, maxRSI = handle_execute_option_8(options, userPassedArgs)
        if minRSI is None:
            return None, None
    if executeOption == 9:
        volumeRatio = handle_execute_option_9(options, configManager)
        if volumeRatio is None:
            return None, None
    if executeOption == 12:
        global nValueForMenu
        nValueForMenu = handle_execute_option_12(userPassedArgs, configManager)
    if executeOption == 21:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            popOption = int(options[3])
            if popOption >= 0 and popOption <= 9:
                pass
        else:
            popOption = ConsoleMenuUtility.PKConsoleMenuTools.promptSubMenuOptions(selectedMenu)
        if popOption is None or popOption == 0:
            return None, None
        else:
            selectedChoice["3"] = str(popOption)
        if popOption in [1,2,4]:
            updateMenuChoiceHierarchy()
            screenResults = getMFIStats(popOption)
            if menuOption in ["X"]:
                printNotifySaveScreenedResults(
                    screenResults,
                    screenResults,
                    selectedChoice,
                    menuChoiceHierarchy,
                    False,
                    None,
                    executeOption,
                    menuOption
                )
                finishScreening(downloadOnly=downloadOnly,testing=testing,stockDictPrimary=stockDictPrimary,configManager=configManager,loadCount=0,testBuild=testBuild,screenResults=screenResults,saveResults=saveResults,user=userPassedArgs.user)
                if defaultAnswer is None:
                    OutputControls().takeUserInput("Press <Enter> to continue...")
                return None, None
            else:
                listStockCodes = ",".join(list(screenResults.index))
        else:
            userPassedArgs.maxdisplayresults = max(configManager.maxdisplayresults,2000) # force evaluate all stocks before getting the top results
            reversalOption = popOption
    if executeOption == 22:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            popOption = int(options[3])
            if popOption >= 0 and popOption <= 3:
                pass
        else:
            popOption = ConsoleMenuUtility.PKConsoleMenuTools.promptSubMenuOptions(selectedMenu)
        if popOption is None or popOption == 0:
            return None, None
        else:
            selectedChoice["3"] = str(popOption)
        updateMenuChoiceHierarchy()
        screenResults = getPerformanceStats()
        if menuOption in ["X"]:
            printNotifySaveScreenedResults(
                screenResults,
                screenResults,
                selectedChoice,
                menuChoiceHierarchy,
                False,
                None,
                executeOption,
                menuOption
            )
            if defaultAnswer is None:
                OutputControls().takeUserInput("Press <Enter> to continue...")
            return None, None
        else:
            listStockCodes = ",".join(list(screenResults.index))
    if executeOption == 26:
        dividend_df, bonus_df, stockSplit_df = mstarFetcher.getCorporateActions()
        ca_dfs = [dividend_df, bonus_df, stockSplit_df]
        listStockCodes = []
        for df in ca_dfs:
            df = df[
                df["Stock"].astype(str).str.contains("BSE:") == False
            ]
            listStockCodes.extend(list(df["Stock"]))
    if executeOption == 29 and not PKDateUtilities.isTradingTime():
        message = "\n[👉🏻] Bid/Ask build up report can only be generated during trading hours."
        OutputControls().printOutput(
            colorText.FAIL
            + message
            + colorText.END
        )
        if defaultAnswer is None:
            OutputControls().takeUserInput("Press <Enter> to continue...")
        if userPassedArgs is not None and userPassedArgs.user is not None:
            sendMessageToTelegramChannel(message=message, user=userPassedArgs.user)
        return None, None
    
    if executeOption == 30 or executeOption == 32:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            if str(options[3]).isnumeric():
                maLength = int(options[3])
            elif str(options[3]).upper() == "D":
                maLength = 1
            else:
                maLength = 1
        elif len(options) >= 3:
            maLength = 1 # By default buy option
        else:
            maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptSubMenuOptions(selectedMenu)
        if maLength == 0:
            return None, None
        else:
            selectedChoice["3"] = str(maLength)

    if executeOption == 30:
        handle_execute_option_30(userPassedArgs, configManager, screener)
    if executeOption == 31:  # DEEL Momentum
        maLength = handle_execute_option_31(userPassedArgs)
    if executeOption == 33:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            if str(options[3]).isnumeric():
                maLength = int(options[3])
            elif str(options[3]).upper() == "D":
                maLength = 2
            else:
                maLength = 2
        elif len(options) >= 3:
            maLength = 2 # By default Bullish PDO/PDC
        else:
            maLength = ConsoleMenuUtility.PKConsoleMenuTools.promptSubMenuOptions(selectedMenu, defaultOption="2")
        if maLength == 0:
            return None, None
        else:
            selectedChoice["3"] = str(maLength)
        if maLength == 3:
            userPassedArgs.maxdisplayresults = max(configManager.maxdisplayresults,2000)
            
    if executeOption == 34:
        handle_execute_option_34(userPassedArgs, configManager)
    if executeOption == 40:
        result = handle_execute_option_40(options, m2, m3, m4, userPassedArgs, selectedChoice)
        if result[0] is None:
            return None, None
        respChartPattern, reversalOption, insideBarToLookback = result
    if executeOption == 41:
        result = handle_execute_option_41(options, m2, m3, m4, userPassedArgs, selectedChoice)
        if result[0] is None:
            return None, None
        respChartPattern, reversalOption = result

    if executeOption == 42:  # Super Gainer
        maLength = handle_execute_option_42_43(executeOption, userPassedArgs)
    if executeOption == 43:  # Super Losers
        maLength = handle_execute_option_42_43(executeOption, userPassedArgs)
    
    if executeOption == MAX_MENU_OPTION:
        ConsoleUtility.PKConsoleTools.getLastScreenedResults(defaultAnswer)
        return None, None
    if executeOption > MAX_SUPPORTED_MENU_OPTION and executeOption < MAX_MENU_OPTION:
        OutputControls().printOutput(
            colorText.FAIL
            + F"\n  [+] Error: Option {MAX_SUPPORTED_MENU_OPTION} to {MAX_MENU_OPTION} Not implemented yet! Press <Enter> to continue."
            + colorText.END
        )
        OutputControls().takeUserInput("Press <Enter> to continue...")
        return None, None
    
    if str(indexOption).isnumeric() and int(indexOption) > 1 and executeOption <= MAX_SUPPORTED_MENU_OPTION:
        ensureMenusLoaded(menuOption,indexOption,executeOption)
        if not PKPremiumHandler.hasPremium(m2.find(str(executeOption).upper())):
            PKAnalyticsService().send_event(f"non_premium_user_{menuOption}_{indexOption}_{executeOption}")
            PKAnalyticsService().send_event("app_exit")
            sys.exit(0)
    if (
        not str(indexOption).isnumeric() and str(indexOption).upper() in ["W", "E", "M", "N", "Z", "S"]
    ) or (
        str(indexOption).isnumeric()
        and (int(indexOption) >= 0 and int(indexOption) < 16)
    ):
        configManager.getConfig(ConfigManager.parser)
        try:
            if str(indexOption).upper() in ["W", "E", "S"]:
                if not PKPremiumHandler.hasPremium(m1.find(str(indexOption).upper())):
                    PKAnalyticsService().send_event(f"non_premium_user_{menuOption}_{indexOption}_{executeOption}")
                    PKAnalyticsService().send_event("app_exit")
                    sys.exit(0)
            if indexOption == "W":
                listStockCodes = fetcher.fetchWatchlist()
                if listStockCodes is None:
                    input(
                        colorText.FAIL
                        + f"  [+] Please create the watchlist.xlsx file in {os.getcwd()} and Restart the Program!"
                        + colorText.END
                    )
                    PKAnalyticsService().send_event("app_exit")
                    sys.exit(0)
            elif indexOption == "N":
                import pandas as pd
                os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
                import tensorflow as tf
                tf.get_logger().setLevel('ERROR')
                if stockDictPrimary is None or (len(stockDictPrimary.keys()) == 0):
                    stockDictPrimary,stockDictSecondary = loadDatabaseOrFetch(downloadOnly=False, listStockCodes=["NIFTY 50"], menuOption=menuOption,indexOption=indexOption)
                hostData = stockDictPrimary.get("NIFTY 50") if (stockDictPrimary is not None and len(stockDictPrimary) > 0) else None
                if hostData is None:
                    messageToUser = "Nifty AI prediction NOT available right now! No data available. Please try again later."
                    OutputControls().printOutput(messageToUser)
                    sendMessageToTelegramChannel(message=messageToUser,user=user)
                    if defaultAnswer is None:
                        input("\nPress <Enter> to Continue...\n")
                    return None, None
                columns = hostData["columns"]
                data = pd.DataFrame(
                        hostData["data"], columns=columns, index=hostData["index"]
                    )
                data.reset_index(inplace=True)
                if "Datetime" in data.columns and "Date" not in data.columns:
                    data.rename(columns={"Datetime": "Date"}, inplace=True)
                else:
                    data.rename(columns={"index": "Date"}, inplace=True)
                data.set_index("Date", inplace=True)
                data.index = pd.to_datetime(data.index)
                prediction, pText, sText = screener.getNiftyPrediction(df=data)
                warningText = "\nNifty AI prediction works best if you request after market is closed. It may not be accurate while market is still open!" if "open" in Utility.marketStatus() else ""
                try:
                    todayHoliday, todayOccassion = PKDateUtilities.isHoliday(PKDateUtilities.currentDateTime())
                    nextWeekday = PKDateUtilities.nextWeekday()
                    tomorrowHoliday,tomorrowOccassion = PKDateUtilities.isHoliday(nextWeekday)
                    if todayHoliday:
                        warningText = f"{warningText}\n\nMarket is closed today due to {todayOccassion}."
                    if tomorrowHoliday:
                        warningText = f"{warningText}\n\nMarket will be closed on {nextWeekday.strftime('%Y-%m-%d')} due to {tomorrowOccassion}."
                except: # pragma: no cover
                    pass
                messageToUser = "Nifty AI prediction NOT available right now! Please try again later. Please let @itsonlypk know about this!"
                if prediction != 0:
                    messageToUser = f"{ImageUtility.PKImageTools.removeAllColorStyles(Utility.marketStatus())}\nNifty AI prediction for the Next Day: {pText}. {sText}.{warningText}"
                else:
                    OutputControls().printOutput(messageToUser)
                sendMessageToTelegramChannel(message=messageToUser,user=user)
                if defaultAnswer is None:
                    input("\nPress <Enter> to Continue...\n")
                return None, None
            elif str(indexOption) == "M":
                return None, None
            elif indexOption == "Z":
                OutputControls().takeUserInput(
                    colorText.FAIL
                    + "  [+] Press <Enter> to Exit!"
                    + colorText.END
                )
                PKAnalyticsService().send_event("app_exit")
                sys.exit(0)
            elif indexOption == "E":
                return handleMonitorFiveEMA()
            else:
                if userPassedArgs.slicewindow is not None:
                    if userPassedArgs.options.startswith("X:12:"):
                        analysis_dict = {}
                        shouldSuppress = not OutputControls().enableMultipleLineOutput
                        with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                            listStockCodes = fetcher.fetchStockCodes(tickerOption=12, stockCode=None)
                        currentTime = userPassedArgs.slicewindow.replace("'","")
                        stockDictPrimary,endOfdayCandles = PKMarketOpenCloseAnalyser.getStockDataForSimulation(sliceWindowDatetime=currentTime,listStockCodes=listStockCodes)
                        if stockDictPrimary is None:
                            OutputControls().printOutput(f"{colorText.FAIL}Cannot continue. Failed to download latest data!{colorText.END}")
                            sleep(3)
                            return None, None
                        listStockCodes = stockDictPrimary.keys()
                    loadedStockData = True
                    show_saved_diff_results = True
                    
                if str(menuOption).upper() == "C":
                    stockDictPrimary,endOfdayCandles = PKMarketOpenCloseAnalyser.getStockDataForSimulation()
                    if stockDictPrimary is None or endOfdayCandles is None or len(stockDictPrimary) < 1 or len(endOfdayCandles) < 1:
                        OutputControls().printOutput(f"Cannot proceed! Stock data is unavailable. Please check the error logs/messages !")
                        return None, None
                    if indexOption > 0:
                        listStockCodes = sorted(list(filter(None,list(set(stockDictPrimary.keys())))))
                if str(indexOption) not in ["S"]:
                    listStockCodes = prepareStocksForScreening(testing, downloadOnly, listStockCodes, indexOption)
        except urllib.error.URLError as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + "\n\n  [+] Oops! It looks like you don't have an Internet connectivity at the moment!"
                + colorText.END
            )
            OutputControls().takeUserInput("Press <Enter> to continue...")
            ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True,forceTop=True)
            return None, None
        if userPassedArgs.options is None or len(userPassedArgs.options) == 0:
            userPassedArgs.options = ""
            for choice in selectedChoice.keys():
                userPassedArgs.options = (f"{userPassedArgs.options}:" if len(userPassedArgs.options) > 0  else '') + f"{selectedChoice[choice]}"
        if userPassedArgs.pipedmenus is not None:
            return addOrRunPipedMenus()
        
        loadedStockData = loadedStockData and stockDictPrimary is not None and len(stockDictPrimary) > 0
        if (menuOption in ["X", "B", "G", "S", "F"] and not loadedStockData) or (
            # not downloadOnly
            # and not PKDateUtilities.isTradingTime()
            # and 
            configManager.cacheEnabled
            and not loadedStockData
            and not testing
        ):
            try:
                import tensorflow as tf
                with tf.device("/device:GPU:0"):
                    stockDictPrimary,stockDictSecondary = loadDatabaseOrFetch(downloadOnly, listStockCodes, menuOption, indexOption)
            except: # pragma: no cover
                stockDictPrimary,stockDictSecondary = loadDatabaseOrFetch(downloadOnly, listStockCodes, menuOption, indexOption)
                pass
        loadCount = len(stockDictPrimary) if stockDictPrimary is not None else 0
        # Let's use screening only for the stocks for which we could get the data.
        savedOrDownloadedKeys = listStockCodes if (userArgs.options is not None and "," in userArgs.options) else list(stockDictPrimary.keys())
        missingStocks = set(listStockCodes) - set([ x.replace("-BE","").replace("-BZ","") for x in savedOrDownloadedKeys ])
        # print(missingStocks)
        # default_logger().debug(missingStocks)
        OutputControls().printOutput(f"{colorText.GREEN}  [+] Adding {len(savedOrDownloadedKeys)-len(missingStocks)} stocks out of {len(savedOrDownloadedKeys)} to the queue...{colorText.END}")
        listStockCodes = list(set(savedOrDownloadedKeys)-set(missingStocks)) if not downloadOnly else savedOrDownloadedKeys
        if downloadOnly:
            OutputControls().printOutput(
                colorText.WARN
                + "  [+] Starting download.. Press Ctrl+C to stop!"
            )
            if not configManager.isIntradayConfig():
                fetcher.saveAllNSEIndices()
        if menuOption.upper() in ["B", "G"]:
            OutputControls().printOutput(
                    colorText.WARN
                    + f"  [+] A total of {configManager.backtestPeriod} trading periods' historical data will be considered for backtesting. You can change this in User Config."
                )
        samplingDuration, fillerPlaceHolder, actualHistoricalDuration = PKScanRunner.getScanDurationParameters(testing, menuOption)
        totalStocksInReview = 0
        savedStocksCount = 0
        downloadedRecently = False
        items = []
        backtest_df = None
        bar, spinner = Utility.tools.getProgressbarStyle()
        # Lets begin from y days ago, evaluate from that date if the selected strategy had yielded any result
        # and then keep coming to the next day (x-1) until we get to today (actualHistoricalDuration = 0)
        OutputControls().printOutput(f"{colorText.GREEN}  [+] Adding stocks to the queue...{colorText.END}")
        with alive_bar(actualHistoricalDuration, bar=bar, spinner=spinner) as progressbar:
            while actualHistoricalDuration >= 0:
                daysInPast = PKScanRunner.getBacktestDaysForScan(userPassedArgs, backtestPeriod, menuOption, actualHistoricalDuration)
                try:
                    listStockCodes, savedStocksCount, pastDate = PKScanRunner.getStocksListForScan(userPassedArgs, menuOption, totalStocksInReview, downloadedRecently, daysInPast) if menuOption not in ["C"] else (listStockCodes, 0, "")
                except KeyboardInterrupt: # pragma: no cover
                    try:
                        keyboardInterruptEvent.set()
                        keyboardInterruptEventFired = True
                        actualHistoricalDuration = -1
                        break
                    except KeyboardInterrupt: # pragma: no cover
                        pass
                    OutputControls().printOutput(
                        colorText.FAIL
                        + "\n  [+] Terminating Script, Please wait..."
                        + colorText.END
                    )
                except Exception:
                    pass
                exchangeName = "NASDAQ" if (indexOption == 15 or (configManager.defaultIndex == 15 and indexOption == 0)) else "INDIA"
                runOptionName = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
                if ((":0:" in runOptionName or "_0_" in runOptionName) and userPassedArgs.progressstatus is not None) or userPassedArgs.progressstatus is not None:
                    runOptionName = userPassedArgs.progressstatus.split("=>")[0].split("  [+] ")[1]
                if menuOption in ["F"]:
                    if "^NSEI" in listStockCodes:
                        listStockCodes.remove("^NSEI")
                    items = PKScanRunner.addScansWithDefaultParams(userPassedArgs, testing, testBuild, newlyListedOnly, downloadOnly, backtestPeriod, listStockCodes, menuOption,exchangeName,executeOption, volumeRatio, items, daysInPast,runOption=f"{userPassedArgs.options} =>{runOptionName} => {menuChoiceHierarchy}")
                else:
                    PKScanRunner.addStocksToItemList(userPassedArgs, testing, testBuild, newlyListedOnly, downloadOnly, minRSI, maxRSI, insideBarToLookback, respChartPattern, daysForLowestVolume, backtestPeriod, reversalOption, maLength, listStockCodes, menuOption,exchangeName,executeOption, volumeRatio, items, daysInPast,runOption=f"{userPassedArgs.options} =>{runOptionName} => {menuChoiceHierarchy}")
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
        OutputControls().moveCursorUpLines(1 if userPassedArgs.monitor else 2)    #sys.stdout.write(f"\x1b[1A") # Replace the download progress bar and start writing on the same line
        if not keyboardInterruptEventFired:
            global tasks_queue, results_queue, consumers, logging_queue
            screenResults, saveResults, backtest_df, tasks_queue, results_queue, consumers,logging_queue = PKScanRunner.runScanWithParams(userPassedArgs,keyboardInterruptEvent,screenCounter,screenResultsCounter,stockDictPrimary,stockDictSecondary,testing, backtestPeriod, menuOption,executeOption, samplingDuration, items,screenResults, saveResults, backtest_df,scanningCb=runScanners,tasks_queue=tasks_queue, results_queue=results_queue, consumers=consumers,logging_queue=logging_queue)
            if userPassedArgs is not None and not userPassedArgs.testalloptions and (userPassedArgs.monitor is None and "|" not in userPassedArgs.options and not userPassedArgs.options.upper().startswith("C")):
                tasks_queue = None
                results_queue = None
                consumers = None
            if menuOption in ["C"]:
                runOptionName = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
                if ((":0:" in runOptionName or "_0_" in runOptionName) and userPassedArgs.progressstatus is not None) or userPassedArgs.progressstatus is not None:
                    runOptionName = userPassedArgs.progressstatus.split("=>")[0].split("  [+] ")[1]
                if saveResults is not None and not saveResults.empty:
                    saveResults, screenResults = PKMarketOpenCloseAnalyser.runOpenCloseAnalysis(stockDictPrimary,endOfdayCandles,screenResults, saveResults,runOptionName=runOptionName,filteredListOfStocks=listStockCodes)
            if downloadOnly and menuOption in ["X"]:
                screener.getFreshMFIStatus(stock="LatestCheckedOnDate")
                screener.getFairValue(stock="LatestCheckedOnDate", force=True)
            if not downloadOnly and menuOption in ["X", "G", "C", "F"]:
                if menuOption == "G":
                    userPassedArgs.backtestdaysago = backtestPeriod
                if screenResults is not None and len(screenResults) > 0:
                    screenResults, saveResults = labelDataForPrinting(
                        screenResults, saveResults, configManager, volumeRatio, executeOption, reversalOption or respChartPattern, menuOption
                    )
                    # ticker_list = list(saveResults.index)
                    # marketCaps = fetcher.fetchAdditionalTickerInfo(ticker_list)
                    # saveResults["MCapWt%"] = 0
                    # numShares = []
                    # for ticker in ticker_list:
                    #     try:
                    #         mCap = marketCaps.get(f"{ticker}.NS")
                    #         mCap = round(mCap.get("marketCap"),0)
                    #     except:
                    #         mCap = 0
                    #         pass
                    #     saveResults.loc[ticker, 'MCapWt%'] = mCap
                    # # Let's get the weighted no. of shares
                    # marketCapSum = sum(saveResults["MCapWt%"])
                    # for ticker in ticker_list:
                    #     try:
                    #         saveResults.loc[ticker, 'MCapWt%'] = int(round(saveResults.loc[ticker, 'MCapWt%']/marketCapSum,2)*100)
                    #     except:
                    #         saveResults.loc[ticker, 'MCapWt%'] = 0
                    #         pass
                    #     numShares.append(saveResults.loc[ticker, 'MCapWt%'])
                    # screenResults["MCapWt%"] = numShares
                if not newlyListedOnly and not configManager.showunknowntrends and screenResults is not None and len(screenResults) > 0 and not userPassedArgs.runintradayanalysis:
                    screenResults, saveResults = removeUnknowns(screenResults, saveResults)
                    OutputControls().printOutput(colorText.FAIL + f"  [+] Configuration to remove unknown cell values resulted into removing all rows!" + colorText.END)
                if len(strategyFilter) > 0 and saveResults is not None and len(saveResults) > 0:
                    # We'd need to apply additional filters for selected strategy
                    df_screenResults = None
                    cleanedUpSaveResults = PortfolioXRay.cleanupData(saveResults)
                    for strFilter in strategyFilter:
                        cleanedUpSaveResults = PortfolioXRay.strategyForKey(strFilter)(cleanedUpSaveResults)
                        saveResults = saveResults[saveResults.index.isin(cleanedUpSaveResults.index.values)]
                    for stk in saveResults.index.values:
                        df_screenResults_filter = screenResults[screenResults.index.astype(str).str.contains(f"NSE%3A{stk}") == True]
                        df_screenResults = pd.concat([df_screenResults, df_screenResults_filter], axis=0)
                    if df_screenResults is None or len(df_screenResults) == 0:
                        OutputControls().printOutput(colorText.FAIL + f"  [+] Of the {len(screenResults) if screenResults is not None else 0} stocks, no results matching the selected strategies!" + colorText.END)
                    screenResults = df_screenResults
                if executeOption == 26:
                    removedUnusedColumns(screenResults, saveResults, ["Date"],userArgs=userPassedArgs)
                    screen_copy = screenResults.copy()
                    screen_copy.reset_index(inplace=True)
                    dividend_df = pd.merge(screen_copy, dividend_df, on='Stock')
                    bonus_df = pd.merge(screen_copy, bonus_df, on='Stock')
                    stockSplit_df = pd.merge(screen_copy, stockSplit_df, on='Stock')
                    corp_dfs = [dividend_df, bonus_df, stockSplit_df]
                    shareable_strings = []
                    shouldSend = False
                    corp_columns = ["Div.Date","Ratio","Record","Split","OldFV","NewFV"]
                    caption_df = None
                    caption_results = ""
                    for corp_df in corp_dfs:
                        if corp_df is None:
                            continue
                        tab_results = ""
                        if corp_df is not None and not corp_df.empty:
                            corp_df.set_index("Stock", inplace=True)
                            corp_df = corp_df[~corp_df.index.duplicated(keep='first')]
                            tab_results = colorText.miniTabulator().tabulate(
                                corp_df,
                                headers="keys",
                                tablefmt=colorText.No_Pad_GridFormat,
                                # showindex = False,
                                maxcolwidths=Utility.tools.getMaxColumnWidths(dividend_df)
                            ).encode("utf-8").decode(STD_ENCODING)
                            
                            if corp_columns[0] in corp_df.columns:
                                caption_df = corp_df[[corp_columns[0]]]
                            elif corp_columns[1] in corp_df.columns:
                                caption_df = corp_df[[corp_columns[1],corp_columns[2]]]
                            elif corp_columns[3] in corp_df.columns:
                                caption_df = corp_df[[corp_columns[3],corp_columns[4],corp_columns[5]]]
                                with pd.option_context('mode.chained_assignment', None):
                                    caption_df["FV"] = caption_df[corp_columns[4]].astype(str) + ":" + caption_df[corp_columns[5]].astype(str)
                                    caption_df = caption_df[[corp_columns[3],"FV"]]
                            if caption_df is not None:
                                # caption_df.reset_index(inplace=True)
                                caption_df = caption_df.head(3)
                                caption_results = caption_results + "\n" + colorText.miniTabulator().tabulate(
                                    caption_df,
                                    headers="keys",
                                    tablefmt=colorText.No_Pad_GridFormat,
                                    maxcolwidths=None
                                    ).encode("utf-8").decode(STD_ENCODING).replace("-K-----S-----C-----R","-K-----S----C---R").replace("%  ","% ").replace("=K=====S=====C=====R","=K=====S====C===R").replace("Vol  |","Vol|").replace("Hgh  |","Hgh|").replace("EoD  |","EoD|").replace("x  ","x")
                            shouldSend = True
                        shareable_strings.append(tab_results)
                        OutputControls().printOutput(tab_results)
                    if shouldSend:
                        caption_results = ImageUtility.PKImageTools.removeAllColorStyles(caption_results.replace("-E-----N-----E-----R","-E-----N----E---R").replace("=E=====N=====E=====R","=E=====N====E===R"))
                        caption = f"Stocks with dividends/bonus/splits. Samples:<pre>{caption_results}</pre>" #<i>Author is <u><b>NOT</b> a SEBI registered financial advisor</u> and MUST NOT be deemed as one.</i>"
                        png_file = f"PKS_X_12_26_{PKDateUtilities.currentDateTime().strftime('%Y-%m-%d_%H:%M:%S')}"
                        png_ext = ".png"
                        sendQuickScanResult(
                            menuChoiceHierarchy,
                            user,
                            shareable_strings[0],
                            ImageUtility.PKImageTools.removeAllColorStyles(shareable_strings[0]),
                            caption,
                            png_file,
                            png_ext,
                            addendum=shareable_strings[1],
                            addendumLabel="NSE Stocks giving bonus:",
                            backtestSummary=shareable_strings[2],
                            backtestDetail="",
                            summaryLabel = "NSE Stocks with corporate action type stock split:",
                            detailLabel = None,
                            forceSend=False
                            )
                        media_group_dict["ATTACHMENTS"] = [{"FILEPATH":png_file+png_ext,"CAPTION":caption.replace('&','n')}]
                        media_group_dict["CAPTION"] = "Stocks with dividends/bonus/splits."
                        
                elif "|" not in userPassedArgs.options:
                    try:
                        printNotifySaveScreenedResults(
                            screenResults,
                            saveResults,
                            selectedChoice,
                            menuChoiceHierarchy,
                            testing,
                            user=user,
                            executeOption=executeOption,
                            menuOption=menuOption
                        )
                    except Exception as e: # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        if userPassedArgs.log:
                            import traceback
                            traceback.print_exc()
                        pass
        if (menuOption in ["X","C","F"] and (userPassedArgs.monitor is None or configManager.alwaysExportToExcel)) or ("|" not in userPassedArgs.options and menuOption not in ["B"]):
            finishScreening(
                downloadOnly,
                testing,
                stockDictPrimary,
                configManager,
                loadCount,
                testBuild,
                screenResults,
                saveResults,
                user,
            )

        if menuOption == "B":
            if backtest_df is not None and len(backtest_df) > 0:
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                # Let's do the portfolio calculation first
                df_xray = prepareGroupedXRay(backtestPeriod, backtest_df)
                summary_df, sorting, sortKeys = FinishBacktestDataCleanup(backtest_df, df_xray)
                while sorting:
                    sorting = showSortedBacktestData(backtest_df, summary_df, sortKeys)
                if defaultAnswer is None:
                    OutputControls().takeUserInput("Press <Enter> to continue...")
            else:
                OutputControls().printOutput("Finished backtesting with no results to show!")
        elif menuOption == "G":
            if defaultAnswer is None:
                OutputControls().takeUserInput("Press <Enter> to continue...")
    newlyListedOnly = False
    # Change the config back to usual
    resetConfigToDefault()
    try:
        creds = None
        # Write into sheet only if it's the reglar scan alert trigger in the morning and evening
        if 'ALERT_TRIGGER' in os.environ.keys() and os.environ["ALERT_TRIGGER"] == 'Y':
            if "GSHEET_SERVICE_ACCOUNT_DEV" in os.environ.keys() and (userPassedArgs.backtestdaysago is None):# or userPassedArgs.log:
                begin = time.time()
                creds = os.environ.get("GSHEET_SERVICE_ACCOUNT_DEV")
                OutputControls().printOutput(f"{colorText.GREEN}  [+] Saving data to Google Spreadsheets now...{colorText.END}")
                gClient = PKSpreadsheets(credentialDictStr=creds)
                runOption = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
                df = saveResults.copy()
                df["LastTradeDate"], df["LastTradeTime"] = getLatestTradeDateTime(stockDictPrimary)
                gClient.df_to_sheet(df=df,sheetName=runOption)
                OutputControls().printOutput(f"{colorText.GREEN} => Done in {round(time.time()-begin,2)}s{colorText.END}")
    except: # pragma: no cover
        pass
    if ("RUNNER" not in os.environ.keys() and 
        not testing and 
        #menuOption not in ["F"] and
        (userPassedArgs is None or 
            (userPassedArgs is not None and 
                (userPassedArgs.user is None or 
                    str(userPassedArgs.user) == DEV_CHANNEL_ID) and 
                (userPassedArgs.answerdefault is None or userPassedArgs.systemlaunched))) and
                    not userPassedArgs.testbuild and 
                    userPassedArgs.monitor is None):
        prevOutput_results = saveResults.index if (saveResults is not None and not saveResults.empty) else []
        isNotPiped = (("|" not in userPassedArgs.options) if (userPassedArgs is not None and userPassedArgs.options is not None) else True)
        hasFoundStocks = len(prevOutput_results) > 0 and isNotPiped
        if hasFoundStocks or (configManager.showPinnedMenuEvenForNoResult and isNotPiped):
            monitorOption = userPassedArgs.systemlaunched if (userPassedArgs is not None and isinstance(userPassedArgs.systemlaunched,str) and userPassedArgs.systemlaunched is not None) else (userPassedArgs.options if (userPassedArgs is not None and userPassedArgs.options is not None) else "")
            if len(monitorOption) == 0:
                for choice in selectedChoice.keys():
                    monitorOption = (f"{monitorOption}:" if len(monitorOption) > 0  else '') + f"{selectedChoice[choice]}"
            m0.renderPinnedMenu(substitutes=[monitorOption,len(prevOutput_results),monitorOption,monitorOption,monitorOption],skip=(["1","2","4","5"] if menuOption in ["F"] else []))
            pinOption = OutputControls().takeUserInput(
                    colorText.FAIL + "  [+] Select option: "
                ) or 'M'
            OutputControls().printOutput(colorText.END, end="")
            ensureMenusLoaded(menuOption,indexOption,executeOption)
            if not PKPremiumHandler.hasPremium(m0.find(str(pinOption).upper())):
                PKAnalyticsService().send_event(f"non_premium_user_pin_{menuOption}_{indexOption}_{executeOption}_{pinOption}")
                PKAnalyticsService().send_event("app_exit")
                sys.exit(0)
            if pinOption in ["1","2"]:
                if pinOption in ["2"]:
                    monitorOption = "X:0:0"
                    prevOutput_results = ",".join(prevOutput_results)
                    monitorOption = f"{monitorOption}:{prevOutput_results}"
                launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
                launcher = f"python3.12 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
                monitorOption = f'"{monitorOption}"'
                scannerOptionQuoted = monitorOption.replace("'",'"')
                OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener with pinned scan option. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} --systemlaunched -a Y -m {scannerOptionQuoted}{colorText.END}")
                sleep(2)
                os.system(f"{launcher} --systemlaunched -a Y -m {scannerOptionQuoted}")
            elif pinOption in ["3"]:
                from pkscreener.classes.keys import getKeyBoardArrowInput
                message = f"\n  [+] {colorText.FAIL}Please use {colorText.END}{colorText.GREEN}Left / Right arrow keys{colorText.END} to slide through the {colorText.WARN}time-window by every 1 minute.{colorText.END}\n  [+] Use {colorText.GREEN}Up / Down arrow keys{colorText.END} to jump {colorText.GREEN}forward / backwards{colorText.END} by {colorText.WARN}{configManager.duration}{colorText.END}\n  [+] {colorText.FAIL}Press any oher key to cancel.{colorText.END}"
                currentTime = PKDateUtilities.currentDateTime()
                requestTime = PKDateUtilities.currentDateTime()
                OutputControls().printOutput(message)
                direction = getKeyBoardArrowInput(message=None)
                numRequestsInASecond = 0
                while (direction is not None and direction not in ["RETURN","CANCEL"]):
                    requestTimeDiff = PKDateUtilities.currentDateTime() - requestTime
                    if requestTimeDiff.total_seconds() <= 0.4:
                        numRequestsInASecond += 1 # Track the number of requests in a second
                    else:
                        numRequestsInASecond = 0
                    if numRequestsInASecond >= 10:
                        numRequestsInASecond = 0
                        fastMultiplier = 60 # Let the clock move faster if the user really wants to go faster
                    else:
                        fastMultiplier = 1
                    candleFrequency = configManager.candleDurationFrequency
                    candleDuration = configManager.candleDurationInt
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
                    elif direction in ["RIGHT","UP"]:
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
                    if userPassedArgs is not None and userPassedArgs.progressstatus is not None:
                        runOptionName = userPassedArgs.progressstatus.split("=>")[0].split("  [+] ")[1].strip()
                        if runOptionName.startswith("P"):
                            userPassedArgs.options = runOptionName.replace("_",":")
                    userPassedArgs.stocklist = ','.join(screenResults.index)
                    tradingDaysInThePast = PKDateUtilities.trading_days_between(currentTime,PKDateUtilities.tradingDate())
                    if tradingDaysInThePast > 0:
                        userPassedArgs.backtestdaysago = tradingDaysInThePast
                    elif tradingDaysInThePast < 0:
                        userPassedArgs.backtestdaysago = None
                    elif tradingDaysInThePast == 0:
                        userPassedArgs.slicewindow = f"'{currentTime}'"
                    ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True,forceTop=True)
                    OutputControls().printOutput(f"{colorText.WARN}Launching into the selected time-window!{colorText.END}{colorText.GREEN} Brace yourself for the time-travel!{colorText.END}")
                    sleep(5)
                    return main(userArgs=userPassedArgs, optionalFinalOutcome_df=optionalFinalOutcome_df)
            elif pinOption in ["4"]:
                prevMonitorOption = f"{configManager.myMonitorOptions}~" if len(configManager.myMonitorOptions) > 0 else ""
                configManager.myMonitorOptions = f"{prevMonitorOption}{monitorOption}"
                configManager.setConfig(ConfigManager.parser,default=True,showFileCreatedText=False)
                OutputControls().printOutput(f"[+] {colorText.GREEN} Your monitoring options have been updated:{colorText.END}\n     {colorText.WARN}{configManager.myMonitorOptions}{colorText.END}\n[+] {colorText.GREEN}You can run it using the option menu {colorText.END}{colorText.FAIL}-m{colorText.END} {colorText.GREEN}or using the main launch option {colorText.END}{colorText.FAIL}M >{colorText.END}")
                sleep(4)
            elif pinOption in ["5"]:
                if len(saveResults) > 0:
                    lastScanOutputStockCodes = list(saveResults.index)
                    userPassedArgs.options = None
                    menuOption = None
                    executeOption = 0
                    return main(userArgs=userPassedArgs,optionalFinalOutcome_df=optionalFinalOutcome_df)
            show_saved_diff_results = False
            return None, None

    if userPassedArgs is not None:
        existingTitle = f"{userPassedArgs.pipedtitle}|" if userPassedArgs.pipedtitle is not None else ""
        choiceSegments = menuChoiceHierarchy.split(">")
        choiceSegments = f"{choiceSegments[-2]} > {choiceSegments[-1]}" if len(choiceSegments)>=4 else f"{choiceSegments[-1]}"
        userPassedArgs.pipedtitle = f'{existingTitle}{choiceSegments}[{len(saveResults)}]'
        if userPassedArgs.runintradayanalysis:
            return analysisFinalResults(screenResults,saveResults,optionalFinalOutcome_df,runOptionName)
        else:
            return screenResults, saveResults

@Halo(text='', spinner='dots')
def getPerformanceStats():
    return mstarFetcher.fetchMorningstarStocksPerformanceForExchange()

@Halo(text='', spinner='dots')
def getMFIStats(popOption):
    if popOption == 4:
        screenResults = mstarFetcher.fetchMorningstarTopDividendsYieldStocks()
    elif popOption in [1,2]:
        screenResults = mstarFetcher.fetchMorningstarFundFavouriteStocks(
                    "NoOfFunds" if popOption == 2 else "ChangeInShares"
                )
    return screenResults

@Halo(text='', spinner='dots')
def analysisFinalResults(screenResults,saveResults,optionalFinalOutcome_df,runOptionName=None):
    global analysis_dict, userPassedArgs
    if screenResults is not None:
        analysis_df = screenResults.copy()
    else:
        analysis_df = pd.DataFrame()
    index_columns = ["Stock","%Chng","volume","Pattern","MA-Signal","Trend(22Prds)","Trend","LTP","LTP@Alert","AlertTime","SqrOff","SqrOffLTP","SqrOffDiff","EoDDiff","DayHighTime","DayHigh","DayHighDiff"]
    final_index_columns = []
    firstScanKey = userPassedArgs.options.split(">|")[0]
    for column in index_columns:
        if column in analysis_df.columns:
            final_index_columns.append(column)
    analysis_df = analysis_df[final_index_columns]
    analysis_df.reset_index(inplace=True)
    if analysis_df is not None and 'index' in analysis_df.columns:
        analysis_df.drop('index', axis=1, inplace=True, errors="ignore")            
    if firstScanKey.startswith("C:"):
        analysis_df["Stock"] = saveResults.index.values
        if analysis_df is not None and "LTP@Alert" in analysis_df.columns:
            if optionalFinalOutcome_df is None:
                optionalFinalOutcome_df = analysis_df
            else:
                optionalFinalOutcome_df = pd.concat([optionalFinalOutcome_df, analysis_df], axis=0)
        else:
            if analysis_df is not None:
                analysis_df.loc[len(analysis_df),"Stock"] = "BASKET"
                analysis_df.loc[len(analysis_df),"Pattern"] = runOptionName if runOptionName is not None else ""
            else:
                analysis_df = pd.DataFrame()
                analysis_df.loc[0,"Stock"] = "BASKET"
                analysis_df.loc[0,"Pattern"] = runOptionName if runOptionName is not None else ""
            optionalFinalOutcome_df = pd.concat([optionalFinalOutcome_df, analysis_df], axis=0)
        showBacktestResults(analysis_df,optionalName="Intraday_Backtest_Result",choices=runOptionName)
    if firstScanKey.startswith("X:12:"):
        analysis_dict[firstScanKey] = {"S1": screenResults, "S2": saveResults}
    return optionalFinalOutcome_df, saveResults

@exit_after(10)
def tryLoadDataOnBackgroundThread():
    global stockDictPrimary,stockDictSecondary, configManager, defaultAnswer, userPassedArgs, loadedStockData
    if stockDictPrimary is None:
        stockDictPrimary = {}
        stockDictSecondary = {}
        loadedStockData = False
    configManager.getConfig(parser=ConfigManager.parser)
    defaultAnswer = "Y"
    userPassedArgs = None
    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
        listStockCodes = fetcher.fetchStockCodes(int(configManager.defaultIndex), stockCode=None)
    loadDatabaseOrFetch(downloadOnly=True,listStockCodes=listStockCodes,menuOption="X",indexOption=int(configManager.defaultIndex))            

def loadDatabaseOrFetch(downloadOnly, listStockCodes, menuOption, indexOption): 
    global stockDictPrimary,stockDictSecondary, configManager, defaultAnswer, userPassedArgs, loadedStockData
    if menuOption not in ["C"]:
        stockDictPrimary = AssetsManager.PKAssetsManager.loadStockData(
                    stockDictPrimary,
                    configManager,
                    downloadOnly=downloadOnly,
                    defaultAnswer=defaultAnswer,
                    forceLoad=(menuOption in ["X", "B", "G", "S", "F"]),
                    stockCodes = listStockCodes,
                    exchangeSuffix = "" if (indexOption == 15 or (configManager.defaultIndex == 15 and indexOption == 0)) else ".NS",
                    userDownloadOption = menuOption
            )
    if menuOption not in ["C"] and (userPassedArgs is not None and (userPassedArgs.monitor is not None or \
                                    ("|" in userPassedArgs.options and ':i' in userPassedArgs.options) or \
                                    (":33:3:" in userPassedArgs.options or \
                                     ":32:" in userPassedArgs.options or \
                                        ":38:" in userPassedArgs.options))) :#not configManager.isIntradayConfig() and configManager.calculatersiintraday:
        prevDuration = configManager.duration
        prevPeriod = configManager.period
        candleDuration = (userPassedArgs.intraday if (userPassedArgs is not None and userPassedArgs.intraday is not None) else ("1m" if configManager.duration.endswith("d") else configManager.duration))
        configManager.toggleConfig(candleDuration=candleDuration,clearCache=False)
        if userPassedArgs is not None and ":33:3:" in userPassedArgs.options:
            exists, cache_file = AssetsManager.PKAssetsManager.afterMarketStockDataExists(True, forceLoad=(menuOption in ["X", "B", "G", "S", "F"]))
            cache_file = os.path.join(Archiver.get_user_data_dir(),cache_file)
            cacheFileSize = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
            if cacheFileSize < 1024*1024*100: # 1m data for 5d is at least 450MB
                configManager.deleteFileWithPattern(pattern="*intraday_stock_data_*.pkl",rootDir=Archiver.get_user_data_dir())
            configManager.duration = "1m"
            configManager.period = "5d"
            configManager.setConfig(ConfigManager.parser,default=True,showFileCreatedText=False)
        # We also need to load the intraday data to be able to calculate intraday RSI
        stockDictSecondary = AssetsManager.PKAssetsManager.loadStockData(
                        stockDictSecondary,
                        configManager,
                        downloadOnly=downloadOnly,
                        defaultAnswer=defaultAnswer,
                        forceLoad=(menuOption in ["X", "B", "G", "S", "F"]),
                        stockCodes = listStockCodes,
                        isIntraday=True,
                        exchangeSuffix = "" if (indexOption == 15 or (configManager.defaultIndex == 15 and indexOption == 0)) else ".NS",
                        userDownloadOption = menuOption
                )
        configManager.duration = prevDuration
        configManager.period = prevPeriod
        configManager.setConfig(ConfigManager.parser,default=True,showFileCreatedText=False)
    loadedStockData = True
    Utility.tools.loadLargeDeals()
    return stockDictPrimary, stockDictSecondary

def getLatestTradeDateTime(stockDictPrimary):
    stocks = list(stockDictPrimary.keys())
    stock = stocks[0]
    try:
        lastTradeDate = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
        lastTradeTime_ist = PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
        df = pd.DataFrame(data=stockDictPrimary[stock]["data"],
                        columns=stockDictPrimary[stock]["columns"],
                        index=stockDictPrimary[stock]["index"])
        ts = df.index[-1]
        lastTraded = pd.to_datetime(ts, unit='s', utc=True) #.tz_convert("Asia/Kolkata")
        lastTradeDate = lastTraded.strftime("%Y-%m-%d")
        lastTradeTime = lastTraded.strftime("%H:%M:%S")
        if lastTradeTime == "00:00:00":
            lastTradeTime = lastTradeTime_ist
    except: # pragma: no cover
        pass
    return lastTradeDate, lastTradeTime

def FinishBacktestDataCleanup(backtest_df, df_xray):
    """Finish backtest data cleanup - delegates to BacktestUtils module"""
    global defaultAnswer
    return finish_backtest_data_cleanup_impl(
        backtest_df=backtest_df,
        df_xray=df_xray,
        default_answer=defaultAnswer,
        config_manager=configManager,
        show_backtest_cb=showBacktestResults,
        backtest_summary_cb=backtestSummary
    )

def addOrRunPipedMenus():
    global userPassedArgs
    # User must have selected menu "P" earlier
    savedPipes = f"{userPassedArgs.pipedmenus}:>|" if len(userPassedArgs.pipedmenus) > 0 else ""
    userPassedArgs.pipedmenus = f"{savedPipes}{userPassedArgs.options}:D:D:D:"
    userPassedArgs.pipedmenus = userPassedArgs.pipedmenus.replace("::",":D:")
    userPassedArgs.pipedmenus = f"{userPassedArgs.pipedmenus}{('i '+configManager.duration) if configManager.isIntradayConfig() else ''}"
    updateMenuChoiceHierarchy()
    OutputControls().printOutput(
            colorText.GREEN
            + f"  [+] {len(userPassedArgs.pipedmenus.split('|'))} Scanners piped so far: {colorText.END}{colorText.WARN+userPassedArgs.pipedmenus+colorText.END}\n{colorText.GREEN}  [+] Do you want to add any more scanners into the pipe?"
            + colorText.END
        )
    shouldAddMoreIntoPipe = 'n'
    if userPassedArgs is None or (userPassedArgs is not None and userPassedArgs.answerdefault is None):
        shouldAddMoreIntoPipe = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select [Y/N] (Default:N): " + colorText.END) or 'n'
    if shouldAddMoreIntoPipe.lower() != 'y':
        OutputControls().printOutput(
            colorText.GREEN
            + f"  [+] Would you also like to run morning vs day close intraday analysis for this selection ?"
            + colorText.END
        )
        shouldRunIntradayAnalysis = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select [Y/N] (Default:N): " + colorText.END) or 'n'
        shouldRunIntradayAnalysis = shouldRunIntradayAnalysis.lower() == 'y'
        if shouldRunIntradayAnalysis:
            analysisOptions = userPassedArgs.pipedmenus.split("|")
            analysisOptions[-1] = analysisOptions[-1].replace("X:","C:")
            userPassedArgs.pipedmenus = "|".join(analysisOptions)
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        launcher = f"python3.12 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
        monitorOption = f'"{userPassedArgs.pipedmenus}"'
        scannerOptionQuoted = monitorOption.replace("'",'"').replace(":>",":D:D:D:>").replace("::",":")
        requestingUser = f" -u {userPassedArgs.user}" if userPassedArgs.user is not None else ""
        enableLog = f" -l" if userPassedArgs.log else ""
        enableTelegramMode = f" --telegram" if userPassedArgs is not None and userPassedArgs.telegram else ""
        backtestParam = f" --backtestdaysago {userPassedArgs.backtestdaysago}" if userPassedArgs.backtestdaysago else ""
        runIntradayAnalysisParam = f" --runintradayanalysis" if shouldRunIntradayAnalysis else ""
        stockListParam = f" --stocklist {userPassedArgs.stocklist}" if userPassedArgs.stocklist else ""
        slicewindowParam = f" --slicewindow {userPassedArgs.slicewindow}" if userPassedArgs.slicewindow else ""
        fnameParam = f" --fname {resultsContentsEncoded}" if resultsContentsEncoded else ""
        OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener with piped scanners. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -e -o {scannerOptionQuoted}{requestingUser}{enableLog}{backtestParam}{runIntradayAnalysisParam}{enableTelegramMode}{stockListParam}{slicewindowParam}{fnameParam}{colorText.END}")
        sleep(2)
        os.system(f"{launcher} --systemlaunched -a Y -e -o {scannerOptionQuoted}{requestingUser}{enableLog}{backtestParam}{runIntradayAnalysisParam}{enableTelegramMode}{stockListParam}{slicewindowParam}{fnameParam}")
        userPassedArgs.pipedmenus = None
        OutputControls().printOutput(
                colorText.GREEN
                + f"  [+] Finished running all piped scanners!"
                + colorText.END
            )
        if defaultAnswer is None:
            OutputControls().takeUserInput("Press <Enter> to continue...")
        ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True,forceTop=True)
        return None, None
    else:
        userPassedArgs.options = None
        return None, None

def describeUser():
    if not configManager.enableUsageAnalytics:
        return
    service = PKAnalyticsService()
    func_args = None
    task = PKTask("Usage Analytics",
                    long_running_fn=service.collectMetrics,
                    long_running_fn_args=func_args)
    task.total = 1
    try:
        # On Github CI, we may run out of memory because of saving results in
        # shared multiprocessing dict.
        PKScheduler.scheduleTasks([task],"Starting up...", showProgressBars=False,submitTaskAsArgs=False,timeout=600)
    except Exception as e: # pragma: no cover
        pass

@Halo(text='', spinner='dots')
def prepareGroupedXRay(backtestPeriod, backtest_df):
    """Prepare grouped X-Ray - delegates to BacktestUtils module"""
    global userPassedArgs
    return prepare_grouped_xray_impl(
        backtest_period=backtestPeriod,
        backtest_df=backtest_df,
        user_passed_args=userPassedArgs,
        remove_unused_columns_cb=removedUnusedColumns
    )

def showSortedBacktestData(backtest_df, summary_df, sortKeys):
    """Show sorted backtest data - delegates to BacktestUtils module"""
    global defaultAnswer
    return show_sorted_backtest_data_impl(
        backtest_df=backtest_df,
        summary_df=summary_df,
        sort_keys=sortKeys,
        default_answer=defaultAnswer,
        show_backtest_cb=showBacktestResults
    )

def resetConfigToDefault(force=False):
    global userPassedArgs
    # isIntraday = userPassedArgs is not None and userPassedArgs.intraday is not None
    # if configManager.isIntradayConfig() or isIntraday:
    #     configManager.toggleConfig(candleDuration="1d", clearCache=False)
    if userPassedArgs is not None and userPassedArgs.monitor is None:
        if "PKDevTools_Default_Log_Level" in os.environ.keys():
            if userPassedArgs is None or (userPassedArgs is not None and userPassedArgs.options is not None and "|" not in userPassedArgs.options and not userPassedArgs.runintradayanalysis and userPassedArgs.pipedtitle is None):
                del os.environ['PKDevTools_Default_Log_Level']
        configManager.logsEnabled = False
    if force:
        configManager.logsEnabled = False
    configManager.setConfig(ConfigManager.parser,default=True,showFileCreatedText=False)

def prepareStocksForScreening(testing, downloadOnly, listStockCodes, indexOption):
    if not downloadOnly:
        updateMenuChoiceHierarchy()
    indexOption = int(indexOption)
    if listStockCodes is None or len(listStockCodes) == 0:
        if indexOption >= 0 and indexOption <= 14:
            shouldSuppress = not OutputControls().enableMultipleLineOutput
            with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                listStockCodes = fetcher.fetchStockCodes(
                                indexOption, stockCode=None
                            )
        elif indexOption == 15:
            OutputControls().printOutput("  [+] Getting Stock Codes From NASDAQ... ", end="")
            nasdaq = PKNasdaqIndexFetcher(configManager)
            listStockCodes,_ = nasdaq.fetchNasdaqIndexConstituents()
            if len(listStockCodes) > 10:
                OutputControls().printOutput(
                    colorText.GREEN
                    + ("=> Done! Fetched %d stock codes." % len(listStockCodes))
                    + colorText.END
                )
                if configManager.shuffleEnabled:
                    random.shuffle(listStockCodes)
                    OutputControls().printOutput(
                        colorText.BLUE
                        + "  [+] Stock shuffling is active."
                        + colorText.END
                    )
            else:
                OutputControls().printOutput(
                    colorText.FAIL
                    + ("=> Failed! Could not fetch stock codes from NASDAQ!")
                    + colorText.END
                )
        if (listStockCodes is None or len(listStockCodes) == 0) and testing:
            listStockCodes = [TEST_STKCODE if indexOption < 15 else "AMD"]
    if indexOption == 0:
        selectedChoice["3"] = ".".join(listStockCodes)
    if testing:
        listStockCodes = [random.choice(listStockCodes)]
    return listStockCodes

def handleMonitorFiveEMA():
    result_df = pd.DataFrame(
                    columns=["Time", "Stock/Index", "Action", "SL", "Target", "R:R"]
                )
    last_signal = {}
    first_scan = True
    result_df = screener.monitorFiveEma(  # Dummy scan to avoid blank table on 1st scan
                    fetcher=fetcher,
                    result_df=result_df,
                    last_signal=last_signal,
                )
    try:
        while True:
            ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
            last_result_len = len(result_df)
            try:
                result_df = screener.monitorFiveEma(
                                fetcher=fetcher,
                                result_df=result_df,
                                last_signal=last_signal,
                            )
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput(
                                colorText.FAIL
                                + "  [+] There was an exception while monitoring 5-EMA"
                                + "\n  [+] If this continues to happen, please try and run with -l"
                                + "\n  [+] and collect all the logs, zip it and submit it to the developer."
                                + "\n  [+] For example:"
                                + colorText.END
                                + colorText.WARN
                                + "pkscreener -l\n"
                                + colorText.END
                            )
            OutputControls().printOutput(
                            colorText.WARN
                            + "  [+] 5-EMA : Live Intraday Scanner \t"
                            + colorText.END
                            + colorText.FAIL
                            + f'Last Scanned: {datetime.now().strftime("%H:%M:%S")}\n'
                            + colorText.END
                        )
            if result_df is not None and len(result_df) > 0:
                OutputControls().printOutput(
                                colorText.miniTabulator().tabulate(
                                    result_df,
                                    headers="keys",
                                    tablefmt=colorText.No_Pad_GridFormat,
                                    maxcolwidths=Utility.tools.getMaxColumnWidths(result_df)
                                ).encode("utf-8").decode(STD_ENCODING)
                            )
            OutputControls().printOutput("\nPress Ctrl+C to exit.")
            if result_df is not None and len(result_df) != last_result_len and not first_scan:
                Utility.tools.alertSound(beeps=5)
            sleep(60)
            first_scan = False
    except KeyboardInterrupt: # pragma: no cover
        input("\nPress <Enter> to Continue...\n")
        return

def handleRequestForSpecificStocks(options, indexOption):
    global listStockCodes
    listStockCodes = [] if listStockCodes is None or len(listStockCodes) ==0 else listStockCodes
    strOptions = ""
    if isinstance(options, list):
        strOptions = ":".join(options).split(">")[0]
    else:
        strOptions = options.split(">")[0]
    
    if indexOption == 0:
        if len(strOptions) >= 4:
            strOptions = strOptions.replace(":D:",":").replace(">","")
            providedOptions = strOptions.split(":")
            for option in providedOptions:
                if not "".join(str(option).split(".")).isdecimal() and len(option.strip()) > 1:
                    listStockCodes = str(option.strip()).split(",")
                    break
    return listStockCodes

def handleExitRequest(executeOption):
    if executeOption == "Z":
        OutputControls().takeUserInput(
            colorText.FAIL
            + "  [+] Press <Enter> to Exit!"
            + colorText.END
        )
        PKAnalyticsService().send_event("app_exit")
        sys.exit(0)

def handleMenu_XBG(menuOption, indexOption, executeOption):
    if menuOption in ["X", "B", "G", "C"]:
        selMenu = m0.find(menuOption)
        m1.renderForMenu(selMenu, asList=True)
        if indexOption is not None:
            selMenu = m1.find(indexOption)
            m2.renderForMenu(selMenu, asList=True)
            if executeOption is not None:
                selMenu = m2.find(executeOption)
                m3.renderForMenu(selMenu, asList=True)


def updateMenuChoiceHierarchy():
    """Update menu choice hierarchy - delegates to MenuNavigation module"""
    global userPassedArgs, selectedChoice, menuChoiceHierarchy, nValueForMenu
    menuChoiceHierarchy = update_menu_choice_hierarchy_impl(
        userPassedArgs, selectedChoice, configManager, nValueForMenu,
        level0MenuDict, level1_X_MenuDict, level1_P_MenuDict,
        level2_X_MenuDict, level2_P_MenuDict,
        level3_X_Reversal_MenuDict, level3_X_ChartPattern_MenuDict,
        level3_X_PopularStocks_MenuDict, level3_X_PotentialProfitable_MenuDict,
        level4_X_Lorenzian_MenuDict, level4_X_ChartPattern_Confluence_MenuDict,
        level4_X_ChartPattern_BBands_SQZ_MenuDict, level4_X_ChartPattern_MASignalMenuDict,
        PRICE_CROSS_SMA_EMA_DIRECTION_MENUDICT, PRICE_CROSS_SMA_EMA_TYPE_MENUDICT,
        PRICE_CROSS_PIVOT_POINT_TYPE_MENUDICT, CANDLESTICK_DICT
    )
    return menuChoiceHierarchy

def saveScreenResultsEncoded(encodedText:None):
    import uuid
    uuidFileName = str(uuid.uuid4())
    os.makedirs(os.path.dirname(os.path.join(Archiver.get_user_outputs_dir(),f"DeleteThis{os.sep}")), exist_ok=True)
    toBeDeletedFolder = os.path.join(Archiver.get_user_outputs_dir(),"DeleteThis")
    fileName = os.path.join(toBeDeletedFolder, uuidFileName)
    try:
        with open(fileName, 'w', encoding="utf-8") as f:
            f.write(encodedText)
    except: # pragma: no cover
        pass
    return f'{uuidFileName}~{PKDateUtilities.currentDateTime().strftime("%Y-%m-%d %H:%M:%S.%f%z").replace(" ","~")}'

def readScreenResultsDecoded(fileName=None):
    os.makedirs(os.path.dirname(os.path.join(Archiver.get_user_outputs_dir(),f"DeleteThis{os.sep}")), exist_ok=True)
    toBeDeletedFolder = os.path.join(Archiver.get_user_outputs_dir(),"DeleteThis")
    filePath = os.path.join(toBeDeletedFolder, fileName)
    contents = None
    try:
        with open(filePath, 'r', encoding="utf-8") as f:
            contents = f.read()
    except: # pragma: no cover
        pass
    return contents

def findPipedScannerOptionFromStdScanOptions(df_scr, df_sr,menuOption="X"):
    if menuOption not in ["F"] or "ScanOption" not in df_sr.columns:
        return df_scr, df_sr
    df_grouped_sr = df_sr.groupby("Stock")
    df_grouped_scr = df_scr.groupby("Stock")
    signalDictScr = {}
    signalDict = {}
    grp_scr = {}
    grp_sr = {}
    _,scanDescriptions = menus.allMenus()
    for stock_name, df_group in df_grouped_scr:
        items = []
        for item in list(df_group["MA-Signal"]):
            items.extend(item.replace("'","").replace("\"","").replace(" ","").split(","))
        maSignalsScr = sorted(list(filter(None,list(set(items)))))
        stockName = ImageUtility.PKImageTools.stockNameFromDecoratedName(stock_name)
        signalDictScr[stockName] = maSignalsScr
        grp_scr[stockName] = df_group

    for stock_name, df_group in df_grouped_sr:
        items = []
        grp_sr[stock_name] = df_group
        saveResults = df_group
        screenResults = grp_scr[stock_name]
        for item in list(saveResults["MA-Signal"]):
            items.extend(item.replace("'","").replace("\"","").replace(" ","").split(","))
        maSignals = sorted(list(filter(None,list(set(items)))))
        signalDict[stock_name] = maSignals
        from pkscreener.classes.MenuOptions import PREDEFINED_PIPED_MENU_OPTIONS
        predefinedKeys = PREDEFINED_PIPED_MENU_OPTIONS.keys()
        matchingKeys = []
        resultScanOptions = list(saveResults["ScanOption"])
        for key in predefinedKeys:
            predefinedScanOptions = PREDEFINED_PIPED_MENU_OPTIONS[key]
            hasMatchingKeyCount = 0
            resultIndices = []
            resultIndex = 0
            for scanOption in resultScanOptions:
                for predefinedScanOption in predefinedScanOptions:
                    if f"{scanOption}:" in predefinedScanOption:
                        hasMatchingKeyCount += 1
                        resultIndices.append(resultIndex)
                resultIndex += 1
            if hasMatchingKeyCount == len(predefinedScanOptions):
                matchingKeys.append(key)
                for index in resultIndices:
                    try:
                        with pd.option_context('mode.chained_assignment', None):
                            saveResults["ScanOption"].iloc[index] = f'{saveResults["ScanOption"].iloc[index]}, {key}'
                            screenResults["ScanOption"].iloc[index] = f'{screenResults["ScanOption"].iloc[index]}, {key}'
                    except: # pragma: no cover
                        pass
        items = []
        for item in list(screenResults["ScanOption"]):
            items.extend(item.replace("'","").replace("\"","").replace(" ","").split(","))
        items = sorted(list(filter(None,list(set(items)))))
        try:
            with pd.option_context('mode.chained_assignment', None):
                saveResults["ScanOption"].iloc[0] = "\n".join(items)
                screenResults["ScanOption"].iloc[0] = "\n".join(items)
                saveResults["MA-Signal"].iloc[0] = " ,".join(maSignals)
                screenResults["MA-Signal"].iloc[0] = " ,".join(signalDictScr[stock_name])
                descs = []
                for item in items:
                    if item in scanDescriptions.keys():
                        descs.append(scanDescriptions[item])
                    elif str(item).startswith("P"):
                        descs.append(PREDEFINED_SCAN_MENU_TEXTS[int(str(item).split("_")[-1])-1])
                screenResults["ScanDescription"] = "\n".join(descs)
                saveResults["ScanDescription"] = "\n".join(descs)
                saveResults.reset_index(inplace=True)
                screenResults.reset_index(inplace=True)
                saveResults = saveResults.drop(saveResults.index.to_list()[1:], axis=0)
                screenResults = screenResults.drop(screenResults.index.to_list()[1:], axis=0)
                saveResults.set_index("Stock", inplace=True)
                screenResults.set_index("Stock", inplace=True)
                # Reorder the columns so that the column max-size can be effectve.
                # For some reason, last column is not wrapped if it's large
                columns = ["ScanOption"]
                indexOfColumn = list(screenResults.columns).index("ScanOption")
                columns.extend(list(screenResults.columns[:-(len(list(screenResults.columns))-indexOfColumn)]))
                columns.extend(list(screenResults.columns[-(len(list(screenResults.columns))-indexOfColumn)+1:]))
                screenResults = screenResults[columns]
                saveResults = saveResults[columns]
                grp_scr[stock_name] = screenResults
                grp_sr[stock_name] = saveResults
        except: # pragma: no cover
            pass
    df_scr = pd.concat([x for x in grp_scr.values()], axis=0)
    df_sr = pd.concat([x for x in grp_sr.values()], axis=0)
    return df_scr, df_sr

def printNotifySaveScreenedResults(
    screenResults, saveResults, selectedChoice, menuChoiceHierarchy, testing, user=None,executeOption=None,menuOption=None
):
    global scanCycleRunning,userPassedArgs, elapsed_time, media_group_dict, saved_screen_results, resultsContentsEncoded,criteria_dateTime
    diff_from_prev_scan = None
    onlyInCurrent_df = None
    common_df  = None
    addedList = []
    printableColumns = []
    lastReportDateTime = "Unknown"
    if userPassedArgs.monitor is not None:
        return
    screenResults, saveResults = findPipedScannerOptionFromStdScanOptions(screenResults, saveResults,menuOption)
    if userPassedArgs.stocklist is not None and saved_screen_results is not None and show_saved_diff_results:
        diff_from_prev_scan = pd.concat([saved_screen_results, screenResults])
        diff_from_prev_scan = diff_from_prev_scan.reset_index()
        df_gpby = diff_from_prev_scan.groupby([diff_from_prev_scan.columns[0]])
        # get index of unique records
        idx = [x[0] for x in df_gpby.groups.values() if len(x) == 1]
        diff_from_prev_scan = diff_from_prev_scan.reindex(idx)
        diff_from_prev_scan = diff_from_prev_scan.set_index(["Stock"])
        if resultsContentsEncoded is not None:
            fnames = resultsContentsEncoded.split("~")
            lastReportDateTime = f"{fnames[1]} {fnames[2]}"
            resultsContentsDecoded = readScreenResultsDecoded(fnames[0])
            toBeDeletedFolder = os.path.join(Archiver.get_user_outputs_dir(),"DeleteThis")
            try:
                os.remove(os.path.join(toBeDeletedFolder, fnames[0]))
            except: # pragma: no cover
                pass
    if userPassedArgs.stocklist is not None:
        passedList = userPassedArgs.stocklist.split(",")
        onlyInCurrent_df = screenResults[~screenResults.index.isin(passedList)]
        common_df = screenResults[screenResults.index.isin(passedList)]
        addedList = list(set(passedList) - set(common_df.index))
    
    MAX_ALLOWED = (configManager.maxdisplayresults if userPassedArgs.maxdisplayresults is None else (int(userPassedArgs.maxdisplayresults) if not testing else 1))
    tabulated_backtest_summary = ""
    tabulated_backtest_detail = ""
    recordDate = PKDateUtilities.tradingDate().strftime('%Y-%m-%d') if (userPassedArgs.backtestdaysago is None) else (PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago)))
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    if screenResults is not None and len(screenResults) > 0 and menuOption not in ["F"]:
        screenResults = screenResults[~screenResults.index.duplicated(keep='first')]
        saveResults = saveResults[~saveResults.index.duplicated(keep='first')]
        if "Stock" in screenResults.columns:
            screenResults.drop_duplicates(keep="first", inplace=True)
        if "Stock" in saveResults.columns:
            saveResults.drop_duplicates(keep="first", inplace=True)

    runOptionName = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
    if ((":0:" in runOptionName or "_0_" in runOptionName) and userPassedArgs.progressstatus is not None) or userPassedArgs.progressstatus is not None:
        runOptionName = userPassedArgs.progressstatus.split("=>")[0].split("  [+] ")[1].strip()
    indexName = ""
    if runOptionName.startswith("P"):
        indexName = f" for {INDICES_MAP[runOptionName.split('_')[-1]]}" if runOptionName is not None and len(runOptionName.split('_')) >= 4 and str(runOptionName.split('_')[-1]).isnumeric() and int(str(runOptionName.split('_')[-1])) <= int(list(INDICES_MAP.keys())[-2]) else ""
    userPassedArgs.pipedtitle = f"{userPassedArgs.pipedtitle}{indexName}" if userPassedArgs.pipedtitle is not None else ""
    reportTitle = f"{userPassedArgs.pipedtitle}|" if userPassedArgs is not None and userPassedArgs.pipedtitle is not None else ""
    reportTitle = f"{runOptionName} | {reportTitle}" if runOptionName is not None else reportTitle
    
    OutputControls().printOutput(
        colorText.FAIL
        + f"  [+] You chose: {reportTitle}{menuChoiceHierarchy}[{len(screenResults) if screenResults is not None and not screenResults.empty else 0}]"
        + (f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]" if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None) else "")
        + colorText.END
        , enableMultipleLineOutput=True
    )
    pngName = f'PKS_{"IA_" if userPassedArgs is not None and userPassedArgs.runintradayanalysis else ""}{runOptionName}_{PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")}'
    pngExtension = ".png"
    eligible = is_token_telegram_configured()
    targetDateG10k = prepareGrowthOf10kResults(saveResults, selectedChoice, menuChoiceHierarchy, testing, user, pngName, pngExtension, eligible)
    if saveResults is not None and "Date" in saveResults.columns and len(saveResults) > 0:
        recordDate = saveResults["Date"].iloc[0].replace("/","-")
    summaryReturns = removedUnusedColumns(screenResults, saveResults, ["Date","Breakout","Resistance"],userArgs=userPassedArgs)

    tabulated_results = ""
    console_results = ""
    if screenResults is not None and len(screenResults) > 0:
        try:
            screenResults = screenResults.loc[:,(screenResults!='-').any(axis=0)] # .all for at least 1 contianing -
            saveResults = saveResults.loc[:,(saveResults!='-').any(axis=0)]
        except ValueError:
            # The truth value of a Series is ambiguous.
            pass
        tabulated_results = colorText.miniTabulator().tabulate(
            screenResults, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
            maxcolwidths=Utility.tools.getMaxColumnWidths(screenResults)
        ).encode("utf-8").decode(STD_ENCODING)
        copyScreenResults = screenResults.copy()
        hiddenColumns = configManager.alwaysHiddenDisplayColumns.split(",")
        try:
            if userPassedArgs.runintradayanalysis or ("VCP" in menuChoiceHierarchy) or ("Patterns" in menuChoiceHierarchy) or ("Reversal" in menuChoiceHierarchy):
                hiddenColumns.remove("Pattern")
            if executeOption in [33]:
                hiddenColumns.remove("52Wk-L")
            if executeOption in [30,5] or "RSI" in menuChoiceHierarchy:
                hiddenColumns.remove("RSI")
                hiddenColumns.remove("CCI")
        except: # pragma: no cover
            pass
        for col in screenResults.columns:
            if col in hiddenColumns:
                copyScreenResults.drop(col, axis=1, inplace=True, errors="ignore")
        saved_screen_results = screenResults
        try:
            console_results = colorText.miniTabulator().tabulate(
                                    copyScreenResults, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
                                    maxcolwidths=Utility.tools.getMaxColumnWidths(copyScreenResults)
                                ).encode("utf-8").decode(STD_ENCODING)
            console_results = console_results
            printableColumns = copyScreenResults.columns
        except: # pragma: no cover
            console_results = tabulated_results
            printableColumns = screenResults.columns
        resultsContentsEncoded = saveScreenResultsEncoded(encodedText=console_results)
    if userPassedArgs.stocklist is None:
        OutputControls().printOutput(f"{console_results}\n", enableMultipleLineOutput=True)
    else:
        if diff_from_prev_scan is not None:
            # diff_from_prev_scan = diff_from_prev_scan[printableColumns]
            saved_screen_results = copyScreenResults
            # tabulated_diff_from_prev = colorText.miniTabulator().tabulate(
            #     diff_from_prev_scan, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
            #     maxcolwidths=Utility.tools.getMaxColumnWidths(diff_from_prev_scan)
            # ).encode("utf-8").decode(STD_ENCODING)
            # OutputControls().printOutput(f"{colorText.WARN}\n  [+] Diff. from previous scan:\n\n{colorText.END}{tabulated_diff_from_prev}\n\n", enableMultipleLineOutput=True)
        if userPassedArgs.fname is not None:
            fnames = userPassedArgs.fname.split("~")
            lastReportDateTime = f"{fnames[1]} {fnames[2]}"
            resultsContentsDecoded = readScreenResultsDecoded(fnames[0])
            toBeDeletedFolder = os.path.join(Archiver.get_user_outputs_dir(),"DeleteThis")
            try:
                os.remove(os.path.join(toBeDeletedFolder, fnames[0]))
            except: # pragma: no cover
                pass
        if onlyInCurrent_df is not None and not onlyInCurrent_df.empty and len(onlyInCurrent_df) > 0:
            onlyInCurrent_df = onlyInCurrent_df[printableColumns]
            tabulated_onlyInCurrent_df = colorText.miniTabulator().tabulate(
                onlyInCurrent_df, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
                maxcolwidths=Utility.tools.getMaxColumnWidths(onlyInCurrent_df)
            ).encode("utf-8").decode(STD_ENCODING)
            OutputControls().printOutput(f"\n  [+] {colorText.WARN}These were not found in the previous results at {colorText.END}{colorText.FAIL}{lastReportDateTime}{colorText.END}{colorText.WARN} (these are only in the current results at {colorText.END}{colorText.GREEN}{criteria_dateTime}{colorText.END}{colorText.WARN}):\n{colorText.END}{tabulated_onlyInCurrent_df}\n", enableMultipleLineOutput=True)
        if common_df is not None and not common_df.empty and len(common_df) > 0:
            common_df = common_df[printableColumns]
            tabulated_common_df = colorText.miniTabulator().tabulate(
                common_df, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
                maxcolwidths=Utility.tools.getMaxColumnWidths(common_df)
            ).encode("utf-8").decode(STD_ENCODING)
            OutputControls().printOutput(f"\n  [+] {colorText.WARN}These were common between the previous results at {colorText.END}{colorText.FAIL}{lastReportDateTime}{colorText.END}{colorText.WARN} and the current results at {colorText.END}{colorText.GREEN}{criteria_dateTime}{colorText.END}{colorText.WARN}):\n{colorText.END}{tabulated_common_df}\n", enableMultipleLineOutput=True)
        if len(addedList) > 0:
            if resultsContentsDecoded is not None:
                reportLines = resultsContentsDecoded.splitlines(keepends=True)
                filteredReportLines = reportLines[:3]
                shouldKeep = False
                for line in reportLines[3:]:
                    if line.startswith("|"):
                        item = line.split("|")[1].strip()
                        if len(item) > 0:
                            shouldKeep = item in addedList
                    if shouldKeep:
                        filteredReportLines.append(line)
                resultsContentsDecoded = "".join(filteredReportLines)
                OutputControls().printOutput(f"\n  [+] {colorText.WARN}These may have been newly added in the previous results at {colorText.END}{colorText.FAIL}{lastReportDateTime}{colorText.END}{colorText.WARN} and were not found in the current results at {colorText.END}{colorText.GREEN}{criteria_dateTime}{colorText.END}{colorText.WARN}):\n{colorText.END}{resultsContentsDecoded}\n", enableMultipleLineOutput=True)
        else:
            OutputControls().printOutput(f"\n  [+] {colorText.WARN}No new stock may have been added in the previous results at {colorText.END}{colorText.FAIL}{lastReportDateTime}{colorText.END}", enableMultipleLineOutput=True)
    
    criteria_dateTime = None
    _, reportNameInsights = getBacktestReportFilename(
        sortKey="Date", optionalName="Insights"
    )
    strategy_df = PortfolioXRay.bestStrategiesFromSummaryForReport(reportNameInsights,includeLargestDatasets=True)
    addendumLabel = (
        "  [+] Strategies that have best results in the past for this scan option (calculated with 1 stock each with matching strategy in the result):"
    )
    tabulated_strategy = ""
    if strategy_df is not None and len(strategy_df) > 0:
        tabulated_strategy = colorText.miniTabulator().tabulate(
            strategy_df,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            showindex=False,
            maxcolwidths=Utility.tools.getMaxColumnWidths(strategy_df)
        ).encode("utf-8").decode(STD_ENCODING)
        OutputControls().printOutput(addendumLabel)
        OutputControls().printOutput(tabulated_strategy)
    if screenResults is not None and len(screenResults) >= 1:
        choiceSegments = menuChoiceHierarchy.split(">")
        choiceSegments = f"{choiceSegments[-2]} > {choiceSegments[-1]}" if len(choiceSegments)>=4 else f"{choiceSegments[-1]}"
        pipedTitle = f"{userPassedArgs.pipedtitle}|" if userPassedArgs.pipedtitle is not None else ""
        pipedTitle = f'| Piped Results: {pipedTitle}{choiceSegments}[{len(saveResults)}]' if len(pipedTitle) > 0 else ""
        pipedTitle = pipedTitle.replace("[","<b>[").replace("]","]</b>")
        title = f'<b>{reportTitle}{choiceSegments}</b>{"" if selectedChoice["0"] != "G" else " for Date:"+ targetDateG10k}'
        if (
            ("RUNNER" in os.environ.keys() and os.environ["RUNNER"] != "LOCAL_RUN_SCANNER")
            or "PKDevTools_Default_Log_Level" in os.environ.keys()
        ):
            if eligible:
                # There's no need to save data locally.
                # This scan must have been triggered by github workflow by a user or scheduled job
                # Let's just send the image result to telegram
                screenResultsTrimmed = screenResults.copy()
                saveResultsTrimmed = saveResults.copy()
                # No point sending a photo with more than MAX_ALLOWED stocks.
                warn_text = (
                    f" but showing only {MAX_ALLOWED}. "
                    if (len(saveResults) > MAX_ALLOWED)
                    else ""
                )
                caption = f"{title}"
                elapsed_text = f"<i>({len(saveResults)}{'+' if (len(saveResults) > MAX_ALLOWED) else ''} stocks found in {str(int(elapsed_time))} sec. Queue Wait Time:{int(PKDateUtilities.currentDateTimestamp()-userPassedArgs.triggertimestamp-int(elapsed_time))}s){warn_text}</i>"
                backtestExtension = "_backtest.png"
                if len(screenResultsTrimmed) > MAX_ALLOWED:
                    screenResultsTrimmed = screenResultsTrimmed.head(MAX_ALLOWED)
                    saveResultsTrimmed = saveResultsTrimmed.head(MAX_ALLOWED)
                    if saveResultsTrimmed is not None and len(saveResultsTrimmed) > 0:
                        tabulated_results = colorText.miniTabulator().tabulate(
                            screenResultsTrimmed,
                            headers="keys",
                            tablefmt=colorText.No_Pad_GridFormat,
                            maxcolwidths=Utility.tools.getMaxColumnWidths(screenResultsTrimmed)
                        ).encode("utf-8").decode(STD_ENCODING)
                markdown_results = ""
                if saveResultsTrimmed is not None and len(saveResultsTrimmed) > 0:
                    markdown_results = colorText.miniTabulator().tabulate(
                        saveResultsTrimmed,
                        headers="keys",
                        tablefmt=colorText.No_Pad_GridFormat,
                        maxcolwidths=Utility.tools.getMaxColumnWidths(saveResultsTrimmed)
                    ).encode("utf-8").decode(STD_ENCODING)
                    try:
                        if "EoDDiff" in saveResultsTrimmed.columns:
                            caption = f"<b>Intraday Analysis</b>:{caption}"
                            caption_df = saveResultsTrimmed[['LTP','DayHighDiff','EoDDiff']].tail(configManager.telegramSampleNumberRows)
                            for col in caption_df.columns:
                                caption_df.loc[:, col] = caption_df.loc[:, col].apply(
                                    lambda x: str(int(round(float(x),0))) if "%" not in str(x) else str(x)
                                )
                            with pd.option_context('mode.chained_assignment', None):
                                caption_df.rename(columns={"DayHighDiff": "Hgh","EoDDiff":"EoD"}, inplace=True)
                        else:
                            caption_df = saveResultsTrimmed[['LTP','%Chng',"volume"]].head(configManager.telegramSampleNumberRows)
                            caption_df.loc[:, "LTP"] = caption_df.loc[:, "LTP"].apply(
                                lambda x: str(int(round(float(x),0)))
                            )
                            caption_df.loc[:, "%Chng"] = caption_df.loc[:, "%Chng"].apply(
                                lambda x: f'{int(round(float(x.split(" ")[0].replace("%","")),0))}%'
                            )
                            caption_df.loc[:, "volume"] = caption_df.loc[:, "volume"].apply(
                                lambda x: f'{int(round(float(x.replace("x","")),0))}x' if (len(x.replace("x","").strip()) > 0 and not pd.isna(float(x.replace("x","")))) else ''
                            )
                            caption_df.rename(columns={"%Chng": "Ch%","volume":"Vol"}, inplace=True)
                    except: # pragma: no cover
                        cols = [list(saveResultsTrimmed.columns)[0]]
                        cols.extend(list(saveResultsTrimmed.columns[5:]))
                        caption_df = saveResultsTrimmed[cols].head(2)
                    with pd.option_context('mode.chained_assignment', None):
                        for col in caption_df.columns:
                            caption_df[col] = caption_df[col].astype(str)
                    caption_results = colorText.miniTabulator().tabulate(
                        caption_df,
                        headers="keys",
                        tablefmt=colorText.No_Pad_GridFormat,
                        maxcolwidths=[None,None,4,3]
                    ).encode("utf-8").decode(STD_ENCODING).replace("-K-----S-----C-----R","-K-----S----C---R").replace("%  ","% ").replace("=K=====S=====C=====R","=K=====S====C===R").replace("Vol  |","Vol|").replace("Hgh  |","Hgh|").replace("EoD  |","EoD|").replace("x  ","x")
                    caption_results = ImageUtility.PKImageTools.removeAllColorStyles(caption_results.replace("-E-----N-----E-----R","-E-----N----E---R").replace("=E=====N=====E=====R","=E=====N====E===R"))
                    suggestion_text = "Try @nse_pkscreener_bot for more scans! <i><b><u>You agree that you have read</u></b>:https://pkjmesra.github.io/PKScreener/Disclaimer.txt</i> <b>and accept TOS</b>: https://pkjmesra.github.io/PKScreener/tos.txt <b>STOP using and exit from channel/group, if you do not</b>"
                    finalCaption = f"{caption}.Feel free to share on social media.open attached image for more. Samples:<pre>{caption_results}</pre>{elapsed_text} {suggestion_text}"
                if not testing:
                    if PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]:
                        kite_file_path, kite_caption = sendKiteBasketOrderReviewDetails(saveResultsTrimmed,runOptionName,caption,user)
                    else:
                        kite_file_path, kite_caption = "Dummy.html", "Dummy"
                    sendQuickScanResult(
                        f"{reportTitle}{menuChoiceHierarchy}",
                        user,
                        tabulated_results,
                        markdown_results,
                        finalCaption,
                        pngName,
                        pngExtension,
                        addendum=tabulated_strategy,
                        addendumLabel=addendumLabel,
                    )
                    png_filepath = pngName+pngExtension
                    if not userPassedArgs.runintradayanalysis or (userPassedArgs.runintradayanalysis and "Intraday Analysis" in finalCaption):
                        media_group_dict["ATTACHMENTS"] = [{"FILEPATH":kite_file_path,"CAPTION":kite_caption.replace('&','n')},
                                                        {"FILEPATH":png_filepath,"CAPTION":finalCaption.replace('&','n')}]
                        media_group_dict["CAPTION"] = caption
                    # Let's send the backtest results now only if the user requested 1-on-1 for scan.
                    if user is not None:
                        # Now let's try and send backtest results
                        (
                            tabulated_backtest_summary,
                            tabulated_backtest_detail,
                        ) = tabulateBacktestResults(
                            saveResultsTrimmed, maxAllowed=MAX_ALLOWED, force=True
                        )
                        try:
                            # import traceback
                            if tabulated_backtest_summary is not None:
                                ImageUtility.PKImageTools.tableToImage(
                                    "",
                                    "",
                                    pngName + backtestExtension,
                                    menuChoiceHierarchy,
                                    backtestSummary=tabulated_backtest_summary,
                                    backtestDetail=tabulated_backtest_detail,
                                )
                                caption = f"Backtest data for stocks listed in <b>{title}</b> scan results. See more past backtest data at https://pkjmesra.github.io/PKScreener/BacktestReports.html"
                                sendMessageToTelegramChannel(
                                    message=None,
                                    document_filePath=pngName + backtestExtension,
                                    caption=caption,
                                    user=user,
                                )
                                os.remove(pngName + backtestExtension)
                        except Exception as e:  # pragma: no cover
                            default_logger().debug(e, exc_info=True)
                            pass
                            # OutputControls().printOutput(e)
                            # traceback.print_exc()
                    else:
                        tabulateBacktestResults(saveResults)
            else:
                tabulateBacktestResults(saveResults)
        else:
            tabulateBacktestResults(saveResults)
            needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
            pastDate = PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)
            pastDate = pastDate if criteria_dateTime is None else criteria_dateTime
            OutputControls().printOutput(
                colorText.GREEN
                + f"  [+] Found {len(screenResults) if screenResults is not None else 0} {'Scan Options' if menuOption in 'F' else 'Stocks'} in {str('{:.2f}'.format(elapsed_time))} sec for {pastDate}. Showing only {'Scan Options' if menuOption in 'F' else 'stocks'} that met the filter criteria in the filters section of user configuration{(' with portfolio returns:' + summaryReturns) if (len(summaryReturns) > 0) else ''}"
                + colorText.END
            )
    elif user is not None and not str(user).startswith("-"):
        sendMessageToTelegramChannel(
            message=f"No scan results found for {menuChoiceHierarchy}", user=user
        )
    if not testing:
        runOptionName = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
        if ((":0:" in runOptionName or "_0_" in runOptionName) and userPassedArgs.progressstatus is not None) or userPassedArgs.progressstatus is not None:
            runOptionName = userPassedArgs.progressstatus.split("=>")[0].split("  [+] ")[1].strip()
        ConsoleUtility.PKConsoleTools.setLastScreenedResults(screenResults, saveResults, f"{runOptionName}_{recordDate if recordDate is not None else ''}")
    scanCycleRunning = False

def sendKiteBasketOrderReviewDetails(saveResultsTrimmed,runOptionName,caption,user):
    kite_file_path = os.path.join(Archiver.get_user_data_dir(), f"{runOptionName}_Kite_Basket.html")
    kite_caption=f"Review Kite(Zerodha) Basket order for {runOptionName}  - {caption}"
    global userPassedArgs
    if PKDateUtilities.isTradingTime() or userPassedArgs.log: # Only during market hours
        # Also share the kite_basket html/json file.
        try:
            with pd.option_context('mode.chained_assignment', None):
                kite_basket_df = pd.DataFrame(columns=["product","exchange","tradingsymbol","quantity","transaction_type","order_type","price"], index=saveResultsTrimmed.index)
                price = (saveResultsTrimmed["LTP"].astype(float)*0.995).round(1) if "LTP" in saveResultsTrimmed.columns else 0
                kite_basket_df.loc[:,"price"] = price
                kite_basket_df["quantity"] = 1
                kite_basket_df["product"] = "MIS"
                kite_basket_df["exchange"] = "NSE"
                kite_basket_df["transaction_type"] = "SELL" if "sell" in caption.lower() or "bear" in caption.lower() else "BUY"
                kite_basket_df["order_type"] = "LIMIT"
                kite_basket_df.reset_index(inplace=True)
                kite_basket_df.reset_index(inplace=True, drop=True)
                kite_basket_df["tradingsymbol"] = kite_basket_df["Stock"]
                kite_basket_df.drop("Stock", axis=1, inplace=True, errors="ignore")
                kite_basket_df.to_json(kite_file_path,orient='records',lines=False)
                lines = ""
                with open(kite_file_path, "r") as f:
                    lines = f.read()
                lines = lines.replace("\"","&quot;").replace("\n","\n,")
                style = ".center { margin: 0;position: absolute;top: 50%;left: 50%;-ms-transform: translate(-50%, -50%);transform: translate(-50%, -50%);}"
                htmlContent = f'<html><style>{style}</style><span><form method="post" action="https://kite.zerodha.com/connect/basket" target="_blank"><input type="hidden" name="api_key" value="gcac8p9oowmserd0"><input type="hidden" name="data" value="{lines}"><div class="center"><input type="submit" value="Review Basket Order on Kite" style="width:250px;height:200px;padding: 0.5rem 1rem; font-weight: 700;"></div></form></span></html>'
                with open(kite_file_path, "w") as f:
                    f.write(htmlContent)
                # sendMessageToTelegramChannel(
                #     message=None,
                #     document_filePath=kite_file_path,
                #     caption=kite_caption,
                #     user=user,
                # )
                # os.remove(kite_file_path)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
    return kite_file_path, kite_caption

@Halo(text='', spinner='dots')
def prepareGrowthOf10kResults(saveResults, selectedChoice, menuChoiceHierarchy, testing, user, pngName, pngExtension, eligible):
    targetDateG10k = None
    if selectedChoice["0"] == "G" or \
        (userPassedArgs.backtestdaysago is not None and 
         int(userPassedArgs.backtestdaysago) > 0 and 
         "RUNNER" not in os.environ.keys() and
         configManager.enablePortfolioCalculations):
        if saveResults is not None and len(saveResults) > 0:
            df = PortfolioXRay.performXRay(saveResults, userPassedArgs,None, None)
            targetDateG10k = saveResults["Date"].iloc[0]
            if df is not None and len(df) > 0:
                titleLabelG10k = f"For {userPassedArgs.backtestdaysago}-Period(s) from {targetDateG10k}, portfolio calculations in terms of Growth of 10k:"
                g10kStyledTable = colorText.miniTabulator().tabulate(
                    df,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                    showindex=False,
                    maxcolwidths=Utility.tools.getMaxColumnWidths(df)
                ).encode("utf-8").decode(STD_ENCODING)
                # Show only if the configuration dicttates showing strategy data
                if configManager.showPastStrategyData:
                    OutputControls().printOutput(f"\n\n{titleLabelG10k}\n")
                    OutputControls().printOutput(g10kStyledTable)
                g10kUnStyledTable = ImageUtility.PKImageTools.removeAllColorStyles(g10kStyledTable)
                if not testing and eligible:
                    sendQuickScanResult(
                        menuChoiceHierarchy,
                        user,
                        g10kStyledTable,
                        g10kUnStyledTable,
                        titleLabelG10k,
                        pngName,
                        pngExtension,
                        forceSend=True
                    )
        elif user is not None and eligible and not str(user).startswith("-"):
            sendMessageToTelegramChannel(
                message=f"No scan results found for {menuChoiceHierarchy}", user=user
            )
            
    return targetDateG10k


def removedUnusedColumns(screenResults, saveResults, dropAdditionalColumns=[], userArgs=None):
    periods = configManager.periodsRange
    if userArgs is not None and userArgs.backtestdaysago is not None and int(userArgs.backtestdaysago) < 22:
        dropAdditionalColumns.append("22-Pd")
    summaryReturns = "" #("w.r.t. " + saveResults["Date"].iloc[0]) if "Date" in saveResults.columns else ""
    for period in periods:
        if saveResults is not None:
            # if f"LTP{period}" in saveResults.columns and "MCapWt%" in saveResults.columns:
            #     pdLTP = saveResults[f"LTP{period}"].replace("", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            #     mktWeight = saveResults["MCapWt%"].replace("", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            #     ltp = saveResults[f"LTP"].replace("", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            #     pdReturn = round(100*(sum(pdLTP * mktWeight)-sum(ltp * mktWeight))/sum(ltp * mktWeight),1)
            #               #round((sum(saveResults[f"LTP{period}"]) - sum(saveResults['LTP']))*100/sum(saveResults['LTP']),1)
            #     if pdReturn > -500:
            #         summaryReturns = f"{period}-Pd({pdReturn} %), {summaryReturns}"
            with pd.option_context('mode.chained_assignment', None):
                saveResults.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
                saveResults.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
            # saveResults.drop(f"MCapWt%", axis=1, inplace=True, errors="ignore")
            # screenResults.drop(f"MCapWt%", axis=1, inplace=True, errors="ignore")
            if len(dropAdditionalColumns) > 0:
                for col in dropAdditionalColumns:
                    if col in saveResults.columns:
                        saveResults.drop(col, axis=1, inplace=True, errors="ignore")
        if screenResults is not None:
            with pd.option_context('mode.chained_assignment', None):
                screenResults.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
                screenResults.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
                if len(dropAdditionalColumns) > 0:
                    for col in dropAdditionalColumns:
                        if col in screenResults.columns:
                            screenResults.drop(col, axis=1, inplace=True, errors="ignore")
    return summaryReturns


def tabulateBacktestResults(saveResults, maxAllowed=0, force=False):
    """Tabulate backtest results - delegates to BacktestUtils module"""
    return tabulate_backtest_results_impl(
        save_results=saveResults,
        max_allowed=maxAllowed,
        force=force,
        config_manager=configManager,
        get_summary_cb=getSummaryCorrectnessOfStrategy
    )


def sendQuickScanResult(
    menuChoiceHierarchy,
    user,
    tabulated_results,
    markdown_results,
    caption,
    pngName,
    pngExtension,
    addendum=None,
    addendumLabel=None,
    backtestSummary="",
    backtestDetail="",
    summaryLabel = None,
    detailLabel = None,
    legendPrefixText = "",
    forceSend=False
):
    if "PKDevTools_Default_Log_Level" not in os.environ.keys():
        if (("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
            return
    try:
        if not is_token_telegram_configured():
            return
        ImageUtility.PKImageTools.tableToImage(
            markdown_results,
            tabulated_results,
            pngName + pngExtension,
            menuChoiceHierarchy,
            backtestSummary=backtestSummary,
            backtestDetail=backtestDetail,
            addendum=addendum,
            addendumLabel=addendumLabel,
            summaryLabel = summaryLabel,
            detailLabel = detailLabel,
            legendPrefixText = legendPrefixText
        )
        if forceSend:
            sendMessageToTelegramChannel(
                message=None,
                document_filePath=pngName + pngExtension,
                caption=caption,
                user=user,
            )
            os.remove(pngName + pngExtension)
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        pass


def reformatTable(summaryText, headerDict, colored_text, sorting=True):
    if sorting:
        tableText = "<!DOCTYPE html><html><head><script type='application/javascript' src='https://pkjmesra.github.io/pkjmesra/pkscreener/classes/tableSorting.js' ></script><style type='text/css'>body, table {background-color: black; color: white;} table, th, td {border: 1px solid white;} th {cursor: pointer; color:white; text-decoration:underline;} .r {color:red;font-weight:bold;} .br {border-color:green;border-width:medium;} .w {color:white;font-weight:bold;} .g {color:lightgreen;font-weight:bold;} .y {color:yellow;} .bg {background-color:darkslategrey;} .bb {background-color:black;} input#searchReports { width: 220px; } table thead tr th { background-color: black; position: sticky; z-index: 100; top: 0; } </style></head><body><span style='color:white;' >"
        colored_text = colored_text.replace(
            "<table", f"{tableText}{summaryText}<br /><input type='text' id='searchReports' onkeyup='searchReportsByAny()' placeholder='Search for stock/scan reports..' title='Type in a name/ID'><table")
        colored_text = colored_text.replace("<table ", "<table id='resultsTable' ")
        colored_text = colored_text.replace('<tr style="text-align: right;">','<tr style="text-align: right;" class="header">')
        for key in headerDict.keys():
            if key > 0:
                colored_text = colored_text.replace(
                    headerDict[key], f"<th>{headerDict[key][4:]}"
                )
            else:
                colored_text = colored_text.replace(
                    headerDict[key], f"<th>Stock{headerDict[key][4:]}"
                )
    else:
        colored_text = colored_text.replace('<table border="1" class="dataframe">', "")
        colored_text = colored_text.replace("<tbody>", "")
        colored_text = colored_text.replace("<tr>", "")
        colored_text = colored_text.replace("</tr>", "")
        colored_text = colored_text.replace("</tbody>", "")
        colored_text = colored_text.replace("</table>", "")
    colored_text = colored_text.replace(colorText.BOLD, "")
    colored_text = colored_text.replace(f"{colorText.GREEN}", "<span class='g'>")
    colored_text = colored_text.replace(f"{colorText.FAIL}", "<span class='r'>")
    colored_text = colored_text.replace(f"{colorText.WARN}", "<span class='y'>")
    colored_text = colored_text.replace(f"{colorText.WHITE}", "<span class='w'>")
    colored_text = colored_text.replace("<td><span class='w'>","<td class='br'><span class='w'>")
    colored_text = colored_text.replace(colorText.END, "</span>")
    colored_text = colored_text.replace("\n", "")
    if sorting:
        colored_text = colored_text.replace("</table>", "</table></span></body></html>")
    return colored_text


def removeUnknowns(screenResults, saveResults):
    for col in screenResults.keys():
        screenResults = screenResults[
            screenResults[col].astype(str).str.contains("Unknown") == False
        ]
    for col in saveResults.keys():
        saveResults = saveResults[
            saveResults[col].astype(str).str.contains("Unknown") == False
        ]
    return screenResults, saveResults

# def apply_df_style(x):
#     red = 'color: red'
#     noColor = '' 
#     green = 'color: green'
#     #compare columns
#     mask_green_bid = x['BidQty'] > x['AskQty']
#     mask_red_bid = x['BidQty'] <= x['AskQty']
#     mask_green_vwap = x['VWAP'] >= x['LTP']
#     #DataFrame with same index and columns names as original filled empty strings
#     df1 =  pd.DataFrame(noColor, index=x.index, columns=x.columns)
#     #modify values of df1 column by boolean mask
#     df1.loc[mask_green_bid, 'BidQty'] = green
#     df1.loc[mask_red_bid, 'AskQty'] = red
#     df1.loc[mask_green_vwap, 'VWAP'] = green
#     return df1

def runScanners(
    menuOption,
    items,
    tasks_queue,
    results_queue,
    numStocks,
    backtestPeriod,
    iterations,
    consumers,
    screenResults,
    saveResults,
    backtest_df,
    testing=False,
):
    global scanCycleRunning,selectedChoice, userPassedArgs, elapsed_time, start_time,userPassedArgs,criteria_dateTime
    result = None
    backtest_df = None
    reviewDate = getReviewDate(userPassedArgs) if criteria_dateTime is None else criteria_dateTime
    max_allowed = getMaxAllowedResultsCount(iterations, testing)
    try:
        originalNumberOfStocks = numStocks
        iterations, numStocksPerIteration = getIterationsAndStockCounts(numStocks, iterations)
        OutputControls().printOutput(
            colorText.GREEN
            + f"  [+] For {reviewDate}, total {'Scanners' if menuOption in ['F'] else 'Stocks'} under review: {numStocks} over {iterations} iterations..."
            + colorText.END
        )
        if not userPassedArgs.download:
            OutputControls().printOutput(colorText.WARN
                + f"  [+] Starting {'Stock' if menuOption not in ['C'] else 'Intraday'} {'Screening' if menuOption=='X' else ('Analysis' if menuOption == 'C' else 'Look-up' if menuOption in ['F'] else 'Backtesting.')}. Press Ctrl+C to stop!"
                + colorText.END
            )
            if userPassedArgs.progressstatus is not None:
                OutputControls().printOutput(f"{colorText.GREEN}{userPassedArgs.progressstatus}{colorText.END}")
        else:
            OutputControls().printOutput(
                colorText.FAIL
                + f"  [+] Download ONLY mode (OHLCV for period:{configManager.period}, candle-duration:{configManager.duration} )! Stocks will not be screened!"
                + colorText.END
            )
        bar, spinner = Utility.tools.getProgressbarStyle()
        # OutputControls().moveCursorUpLines(1)
        with alive_bar(numStocks, bar=bar, spinner=spinner) as progressbar:
            lstscreen = []
            lstsave = []
            result = None
            backtest_df = None
            start_time = time.time() if not scanCycleRunning else start_time
            scanCycleRunning = True
            def processResultsCallback(resultItem, processedCount,result_df, *otherArgs):
                global userPassedArgs
                (menuOption, backtestPeriod, result, lstscreen, lstsave) = otherArgs
                numStocks = processedCount
                result = resultItem
                backtest_df = processResults(menuOption, backtestPeriod, result, lstscreen, lstsave, result_df)
                progressbar()
                progressbar.text(
                    colorText.GREEN
                    + f"{'Remaining' if userPassedArgs.download else ('Found' if menuOption in ['X','F'] else 'Analysed')} {len(lstscreen) if not userPassedArgs.download else processedCount} {'Stocks' if menuOption in ['X'] else 'Records'}"
                    + colorText.END
                )
                if result is not None:
                    if not userPassedArgs.monitor and len(lstscreen) > 0 and userPassedArgs is not None and userPassedArgs.options.split(":")[2] in ["29"]:
                        scr_df = pd.DataFrame(lstscreen)
                        existingColumns = ["Stock","%Chng","LTP","volume"]
                        newColumns = ["BidQty","AskQty","LwrCP","UprCP","VWAP","DayVola","Del(%)"]
                        existingColumns.extend(newColumns)
                        scr_df = scr_df[existingColumns]
                        scr_df.sort_values(by=["volume","BidQty"], ascending=False, inplace=True)
                        tabulated_results = colorText.miniTabulator().tb.tabulate(
                                scr_df,
                                headers="keys",
                                showindex=False,
                                tablefmt=colorText.No_Pad_GridFormat,
                                maxcolwidths=Utility.tools.getMaxColumnWidths(scr_df)
                            )
                        tableLength = 2*len(lstscreen)+5
                        OutputControls().printOutput('\n'+tabulated_results)
                        # Move the cursor up, back to the top because we want the progress bar to keep showing at the top
                        # sys.stdout.write(f"\x1b[{tableLength}A")  # cursor up one line
                        OutputControls().moveCursorUpLines(tableLength)
                if keyboardInterruptEventFired:
                    return False, backtest_df
                return not ((testing and len(lstscreen) >= 1) or len(lstscreen) >= max_allowed), backtest_df
            otherArgs = (menuOption, backtestPeriod, result, lstscreen, lstsave)
            backtest_df, result =PKScanRunner.runScan(userPassedArgs,testing,numStocks,iterations,items,numStocksPerIteration,tasks_queue,results_queue,originalNumberOfStocks,backtest_df,*otherArgs,resultsReceivedCb=processResultsCallback)

        # OutputControls().printOutput(f"\x1b[{3 if OutputControls().enableMultipleLineOutput else 1}A")
        # if len(lstscreen) == 0 and userPassedArgs is not None and userPassedArgs.monitor is None:
        #     OutputControls().printOutput("\x1b[2K") # Delete the progress bar line
        OutputControls().moveCursorUpLines(3 if OutputControls().enableMultipleLineOutput else 1)
        elapsed_time = time.time() - start_time
        if menuOption in ["X", "G", "C", "F"]:
            # create extension
            screenResults = pd.DataFrame(lstscreen)
            saveResults = pd.DataFrame(lstsave)

    except KeyboardInterrupt: # pragma: no cover
        try:
            global keyboardInterruptEventFired
            keyboardInterruptEvent.set()
            keyboardInterruptEventFired = True
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] Terminating Script, Please wait..."
                + colorText.END
            )
            PKScanRunner.terminateAllWorkers(userPassedArgs=userPassedArgs,consumers=consumers, tasks_queue=tasks_queue,testing=testing)
            logging.shutdown()
        except KeyboardInterrupt: # pragma: no cover
            pass
    except Exception as e: # pragma: no cover
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(
            colorText.FAIL
            + f"\nException:\n{e}\n  [+] Terminating Script, Please wait..."
            + colorText.END
        )
        PKScanRunner.terminateAllWorkers(userPassedArgs=userPassedArgs,consumers=consumers, tasks_queue=tasks_queue,testing=testing)
        logging.shutdown()

    if result is not None and len(result) >=1 and criteria_dateTime is None:
        if userPassedArgs is not None and userPassedArgs.backtestdaysago is not None:
            criteria_dateTime = result[2].copy().index[-1-int(userPassedArgs.backtestdaysago)]
        else:
            criteria_dateTime = result[2].copy().index[-1] if userPassedArgs.slicewindow is None else datetime.strptime(userPassedArgs.slicewindow.replace("'",""),"%Y-%m-%d %H:%M:%S.%f%z")
        localtz = datetime.now(UTC).astimezone().tzinfo
        exchangeTz = PKDateUtilities.currentDateTime().astimezone().tzinfo
        if localtz != exchangeTz:
            criteria_dateTime = PKDateUtilities.utc_to_ist(criteria_dateTime,localTz=localtz)
    if result is not None and len(result) >=1 and "Date" not in saveResults.columns:
        temp_df = result[2].copy()
        temp_df.reset_index(inplace=True)
        temp_df = temp_df.tail(1)
        temp_df.rename(columns={"index": "Date"}, inplace=True)
        targetDate = (
            temp_df["Date"].iloc[0]
            if "Date" in temp_df.columns
            else str(temp_df.iloc[:, 0][0])
        )
        saveResults["Date"] = str(targetDate).split(" ")[0]
    return screenResults, saveResults, backtest_df

        
def processResults(menuOption, backtestPeriod, result, lstscreen, lstsave, backtest_df):
    if result is not None:
        lstscreen.append(result[0])
        lstsave.append(result[1])
        sampleDays = result[4]
        if menuOption == "B":
            backtest_df = updateBacktestResults(
                            backtestPeriod,
                            start_time,
                            result,
                            sampleDays,
                            backtest_df,
                        )
            
    return backtest_df

def getReviewDate(userPassedArgs=None):
    """Get review date - delegates to CoreFunctions module"""
    return _get_review_date(userPassedArgs, criteria_dateTime)

def getMaxAllowedResultsCount(iterations, testing):
    """Get max allowed results count - delegates to CoreFunctions module"""
    return _get_max_allowed_results_count(iterations, testing, configManager, userPassedArgs)

def getIterationsAndStockCounts(numStocks, iterations):
    """Get iterations and stock counts - delegates to CoreFunctions module"""
    return _get_iterations_and_stock_counts(numStocks, iterations)


def updateBacktestResults(
    backtestPeriod, start_time, result, sampleDays, backtest_df
):
    global elapsed_time
    sellSignal = (
        str(selectedChoice["2"]) in ["6", "7"] and str(selectedChoice["3"]) in ["2"]
    ) or selectedChoice["2"] in ["15", "16", "19", "25"]
    backtest_df = backtest(
        result[3],
        result[2],
        result[1],
        result[0],
        backtestPeriod,
        sampleDays,
        backtest_df,
        sellSignal,
    )
    elapsed_time = time.time() - start_time
    return backtest_df


def saveDownloadedData(downloadOnly, testing, stockDictPrimary, configManager, loadCount):
    """Save downloaded stock data - delegates to DataLoader module"""
    global userPassedArgs, keyboardInterruptEventFired
    save_downloaded_data_impl(
        download_only=downloadOnly,
        testing=testing,
        stock_dict_primary=stockDictPrimary,
        config_manager=configManager,
        load_count=loadCount,
        user_passed_args=userPassedArgs,
        keyboard_interrupt_fired=keyboardInterruptEventFired,
        send_message_cb=sendMessageToTelegramChannel,
        dev_channel_id=DEV_CHANNEL_ID
    )


def saveNotifyResultsFile(
    screenResults, saveResults, defaultAnswer, menuChoiceHierarchy, user=None
):
    global userPassedArgs, elapsed_time, selectedChoice, media_group_dict,criteria_dateTime
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    if ">|" in userPassedArgs.options and not configManager.alwaysExportToExcel:
        # Let the final results be there. We're mid-way through the screening of some
        # piped scan. Do not save the intermediate results.
        return
    caption = f'<b>{menuChoiceHierarchy.split(">")[-1]}</b>'
    if screenResults is not None and len(screenResults) >= 1:
        choices = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
        if userPassedArgs.progressstatus is not None:
            choices = userPassedArgs.progressstatus.split("=>")[0].split("  [+] ")[1]
        choices = f'{choices.strip()}{"_IA" if userPassedArgs is not None and userPassedArgs.runintradayanalysis else ""}'
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0) if needsCalc else None
        filename = PKAssetsManager.promptSaveResults(choices,
            saveResults, defaultAnswer=defaultAnswer,pastDate=pastDate,screenResults=screenResults)
        # User triggered telegram bot request
        # Group user Ids are < 0, individual ones are > 0
        # if filename is not None and user is not None and int(str(user)) > 0:
        #     sendMessageToTelegramChannel(
        #         document_filePath=filename, caption=menuChoiceHierarchy, user=user
        #     )
        if filename is not None:
            if "ATTACHMENTS" not in media_group_dict.keys():
                media_group_dict["ATTACHMENTS"] = []
            caption = media_group_dict["CAPTION"] if "CAPTION" in media_group_dict.keys() else menuChoiceHierarchy
            media_group_dict["ATTACHMENTS"].append({"FILEPATH":filename,"CAPTION":caption.replace('&','n')})

        OutputControls().printOutput(
            colorText.WARN
            + f"  [+] Notes:\n  [+] 1.Trend calculation is based on 'daysToLookBack'. See configuration.\n  [+] 2.Reduce the console font size to fit all columns on screen.\n  [+] Standard data columns were hidden: {configManager.alwaysHiddenDisplayColumns}. If you want, you can change this in pkscreener.ini"
            + colorText.END
        )
    if userPassedArgs.monitor is None:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0) if criteria_dateTime is None else criteria_dateTime
        if userPassedArgs.triggertimestamp is None:
            userPassedArgs.triggertimestamp = int(PKDateUtilities.currentDateTimestamp())
        OutputControls().printOutput(
            colorText.GREEN
            + f"  [+] Screening Completed. Found {len(screenResults) if screenResults is not None else 0} results in {round(elapsed_time,2)} sec. for {colorText.END}{colorText.FAIL}{pastDate}{colorText.END}{colorText.GREEN}. Queue Wait Time:{int(PKDateUtilities.currentDateTimestamp()-userPassedArgs.triggertimestamp-round(elapsed_time,2))}s! Press Enter to Continue.."
            + colorText.END
            , enableMultipleLineOutput=True
        )
        if defaultAnswer is None:
            OutputControls().takeUserInput("Press <Enter> to continue...")

def sendGlobalMarketBarometer(userArgs=None):
    from pkscreener.classes import Barometer
    suggestion_text = "Feel free to share on social media.Try @nse_pkscreener_bot for more scans! <i><b><u>You agree that you have read</u></b>:https://pkjmesra.github.io/PKScreener/Disclaimer.txt</i> <b>and accept TOS</b>: https://pkjmesra.github.io/PKScreener/tos.txt <b>STOP using and exit from channel/group, if you do not.</b>"
    caption = f"Global Market Barometer with India market Performance (top) and Valuation (bottom).{suggestion_text}"
    gmbPath = Barometer.getGlobalMarketBarometerValuation()
    try:
        if gmbPath is not None:
            Channel_Id, _, _, _ = PKEnvironment().secrets
            user = userArgs.user if userArgs is not None else (int(f"-{Channel_Id}") if Channel_Id is not None and len(str(Channel_Id)) > 0 else None)
            gmbFileSize = os.stat(gmbPath).st_size if os.path.exists(gmbPath) else 0
            OutputControls().printOutput(f"Barometer report created with size {gmbFileSize} @ {gmbPath}")
            sendMessageToTelegramChannel(
                message=None,
                photo_filePath=gmbPath,
                caption=caption,
                user=user,
            )
            os.remove(gmbPath)
        else:
            PKAnalyticsService().send_event("app_exit")
            sys.exit(0)
    except Exception as e: # pragma: no cover
        default_logger().debug(e,exc_info=True)
        pass

def sendMessageToTelegramChannel(
    message=None, photo_filePath=None, document_filePath=None, caption=None, user=None, mediagroup=False
):
    """Send message to Telegram channel - delegates to NotificationService module"""
    global userPassedArgs, test_messages_queue, media_group_dict, menuChoiceHierarchy
    test_messages_queue, media_group_dict = send_message_to_telegram_channel_impl(
        message=message,
        photo_file_path=photo_filePath,
        document_file_path=document_filePath,
        caption=caption,
        user=user,
        mediagroup=mediagroup,
        user_passed_args=userPassedArgs,
        test_messages_queue=test_messages_queue,
        media_group_dict=media_group_dict,
        menu_choice_hierarchy=menuChoiceHierarchy
    )


def handleAlertSubscriptions(user, message):
    """Handle alert subscriptions - delegates to NotificationService module"""
    handle_alert_subscriptions_impl(user, message)

            
def sendTestStatus(screenResults, label, user=None):
    msg = "<b>SUCCESS</b>" if (screenResults is not None and len(screenResults) >= 1) else "<b>FAIL</b>"
    sendMessageToTelegramChannel(
        message=f"{msg}: Found {len(screenResults) if screenResults is not None else 0} Stocks for {label}", user=user
    )


def showBacktestResults(backtest_df:pd.DataFrame, sortKey="Stock", optionalName="backtest_result", choices=None):
    """Show backtest results - delegates to BacktestUtils module"""
    global menuChoiceHierarchy, selectedChoice, userPassedArgs, elapsed_time
    show_backtest_results_impl(
        backtest_df=backtest_df,
        sort_key=sortKey,
        optional_name=optionalName,
        choices=choices,
        menu_choice_hierarchy=menuChoiceHierarchy,
        selected_choice=selectedChoice,
        user_passed_args=userPassedArgs,
        elapsed_time=elapsed_time,
        config_manager=configManager,
        reformat_table_cb=reformatTable,
        get_report_filename_cb=getBacktestReportFilename,
        scan_output_directory_cb=scanOutputDirectory
    )

def scanOutputDirectory(backtest=False):
    dirName = 'actions-data-scan' if not backtest else "Backtest-Reports"
    outputFolder = os.path.join(os.getcwd(),dirName)
    if not os.path.isdir(outputFolder):
        OutputControls().printOutput("Creating actions-data-scan directory now...")
        os.makedirs(os.path.dirname(os.path.join(os.getcwd(),f"{dirName}{os.sep}")), exist_ok=True)
    return outputFolder

def getBacktestReportFilename(sortKey="Stock", optionalName="backtest_result",choices=None):
    global userPassedArgs,selectedChoice
    if choices is None:
        choices = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice).strip()
    filename = f"PKScreener_{choices.strip()}_{optionalName.strip()}_{sortKey.strip() if sortKey is not None else 'Default'}Sorted.html"
    return choices.strip(), filename.strip()

def showOptionErrorMessage():
    """Show option error message - delegates to OutputFunctions module"""
    _show_option_error_message()

def takeBacktestInputs(
    menuOption=None, indexOption=None, executeOption=None, backtestPeriod=0
):
    g10k = '"Growth of 10k"'
    OutputControls().printOutput(
        colorText.GREEN
        + f"  [+] For {g10k if menuOption == 'G' else 'backtesting'}, you can choose from (1,2,3,4,5,10,15,22,30) or any other custom periods (< 1y)."
    )
    try:
        if backtestPeriod == 0:
            backtestPeriod = int(
                input(
                    colorText.FAIL
                    + f"  [+] Enter {g10k if menuOption == 'G' else 'backtesting'} period (Default is {15 if menuOption == 'G' else 30} [days]): "
                )
            )
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
    if backtestPeriod == 0:
        backtestPeriod = 3 if menuOption == "G" else 30
    indexOption, executeOption = initPostLevel0Execution(
        menuOption=menuOption,
        indexOption=indexOption,
        executeOption=executeOption,
        skip=["N", "E"],
    )
    indexOption, executeOption = initPostLevel1Execution(
        indexOption=indexOption,
        executeOption=executeOption,
        skip=[
            "0",
            "29",
            "42",
        ],
    )
    return indexOption, executeOption, backtestPeriod

def toggleUserConfig():
    configManager.toggleConfig(
        candleDuration="1d" if configManager.isIntradayConfig() else "1m"
    )
    OutputControls().printOutput(
        colorText.GREEN
        + "\nConfiguration toggled to duration: "
        + str(configManager.duration)
        + " and period: "
        + str(configManager.period)
        + colorText.END
    )
    input("\nPress <Enter> to Continue...\n")


def userReportName(userMenuOptions):
    global userPassedArgs
    choices = ""
    for choice in userMenuOptions:
        if len(userMenuOptions[choice]) > 0:
            if len(choices) > 0:
                choices = f"{choices}_"
            choices = f"{choices}{userMenuOptions[choice]}"
    if choices.endswith("_"):
        choices = choices[:-1]
    choices = f"{choices}{'_i' if userPassedArgs.intraday else ''}"
    return choices

def cleanupLocalResults():
    global userPassedArgs, runCleanUp
    runCleanUp = True
    # No need to ask and show prompts if launched by system
    if userPassedArgs.answerdefault is not None or userPassedArgs.systemlaunched or userPassedArgs.testbuild:
        return
    from PKDevTools.classes.NSEMarketStatus import NSEMarketStatus
    if not NSEMarketStatus().shouldFetchNextBell()[0]:
        return
    launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
    shouldPrompt = (launcher.endswith(".py\"") or launcher.endswith(".py")) and (userPassedArgs is None or userPassedArgs.answerdefault is None)
    response = "N"
    if shouldPrompt:
        response = OutputControls().takeUserInput(f"  [+] {colorText.WARN}Clean up local non-essential system generated data?{colorText.END}{colorText.FAIL}[Default: {response}]{colorText.END}\n    (User generated reports won't be deleted.)        :") or response
    if "y" in response.lower():
        dirs = [Archiver.get_user_data_dir(), Archiver.get_user_cookies_dir(), 
                Archiver.get_user_temp_dir(), Archiver.get_user_indices_dir()]
        for dir in dirs:
            configManager.deleteFileWithPattern(rootDir=dir, pattern="*")
        response = OutputControls().takeUserInput(f"\n  [+] {colorText.WARN}Clean up local user generated reports as well?{colorText.END} {colorText.FAIL}[Default: N]{colorText.END} :") or "n"
        if "y" in response.lower():
            configManager.deleteFileWithPattern(rootDir=Archiver.get_user_reports_dir(), pattern="*.*")
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
