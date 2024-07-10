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
from datetime import datetime
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
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured,
    send_document,
    send_message,
    send_photo
)
from PKNSETools.morningstartools.PKMorningstarDataFetcher import morningstarDataFetcher
from PKNSETools.Nasdaq.PKNasdaqIndex import PKNasdaqIndexFetcher
from tabulate import tabulate

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.ScreeningStatistics as ScreeningStatistics
import pkscreener.classes.Utility as Utility
from pkscreener.classes.Utility import STD_ENCODING
from pkscreener.classes import VERSION, PortfolioXRay
from pkscreener.classes.Backtest import backtest, backtestSummary
from pkscreener.classes.PKSpreadsheets import PKSpreadsheets
from PKDevTools.classes.OutputControls import OutputControls
from pkscreener.classes.MenuOptions import (
    level0MenuDict,
    level1_X_MenuDict,
    level2_X_MenuDict,
    level3_X_ChartPattern_MenuDict,
    level3_X_PopularStocks_MenuDict,
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
    PREDEFINED_SCAN_MENU_KEYS
)
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes.Portfolio import PortfolioCollection
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes.PKScheduler import PKScheduler
from pkscreener.classes.PKScanRunner import PKScanRunner
from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser

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
test_messages_queue = []
strategyFilter=[]
listStockCodes = None
tasks_queue = None
results_queue = None
consumers = None
logging_queue = None
mp_manager = None
download_trials = 0

def startMarketMonitor(mp_dict,keyboardevent):
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
    if "RUNNER" in os.environ.keys():
        # There's no need to prompt the user to save xls report or to save data locally.
        # This scan must have been triggered by github workflow by a user or scheduled job
        return
    global defaultAnswer, menuChoiceHierarchy, userPassedArgs, selectedChoice
    saveDownloadedData(downloadOnly, testing, stockDictPrimary, configManager, loadCount)
    if not testBuild and not downloadOnly and not testing:
        saveNotifyResultsFile(
            screenResults, saveResults, defaultAnswer, menuChoiceHierarchy, user=user
        )


def getDownloadChoices(defaultAnswer=None):
    global userPassedArgs
    argsIntraday = userPassedArgs is not None and userPassedArgs.intraday is not None
    intradayConfig = configManager.isIntradayConfig()
    intraday = intradayConfig or argsIntraday
    exists, cache_file = Utility.tools.afterMarketStockDataExists(intraday)
    if exists:
        shouldReplace = Utility.tools.promptFileExists(
            cache_file=cache_file, defaultAnswer=defaultAnswer
        )
        if shouldReplace == "N":
            OutputControls().printOutput(
                cache_file
                + colorText.END
                + " already exists. Exiting as user chose not to replace it!"
            )
            sys.exit(0)
        else:
            pattern = f"{'intraday_' if intraday else ''}stock_data_*.pkl"
            configManager.deleteFileWithPattern(pattern)
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
            Utility.tools.clearScreen(forceTop=True)
        elif menuOption in ["X","C"]:
            indexOption, executeOption = initPostLevel0Execution(
                menuOption=menuOption,
                indexOption=indexOption,
                executeOption=executeOption,
            )
            indexOption, executeOption = initPostLevel1Execution(
                indexOption=indexOption, executeOption=executeOption
            )
    except KeyboardInterrupt:
        input(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Press <Enter> to Exit!"
            + colorText.END
        )
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
                    lambda x: Utility.tools.getFormattedBacktestSummary(
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
                    lambda x: Utility.tools.getFormattedBacktestSummary(
                        x, pnlStats=True, columnName=col
                    )
                )
            detaildf = detaildf.replace(np.nan, "", regex=True)
            detaildf.loc[:, "Volume"] = detaildf.loc[:, "Volume"].apply(
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
    except urllib.error.HTTPError as e:
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
    global selectedChoice, userPassedArgs
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
        _, cache_file_name = Utility.tools.afterMarketStockDataExists(intraday)
        Utility.tools.set_github_output(f"{filePrefix}DOWNLOAD_CACHE_FILE_NAME",cache_file_name)
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
                    colorText.BOLD
                    + colorText.WARN
                    + "\n[+] The Volume should be lowest since last how many candles? (Default = 5)"
                ) or "5"
            )
    except ValueError as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(colorText.END)
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Error: Non-numeric value entered! Please try again!"
            + colorText.END
        )
        input("Press <Enter> to continue...")
        return
    OutputControls().printOutput(colorText.END)
    global nValueForMenu 
    nValueForMenu = daysForLowestVolume
    return daysForLowestVolume


def handleSecondaryMenuChoices(
    menuOption, testing=False, defaultAnswer=None, user=None
):
    global userPassedArgs
    if menuOption == "H":
        showSendHelpInfo(defaultAnswer, user)
    elif menuOption == "U":
        OTAUpdater.checkForUpdate(VERSION, skipDownload=testing)
        if defaultAnswer is None:
            input("Press <Enter> to continue...")
    elif menuOption == "T":
        if userPassedArgs is None or userPassedArgs.options is None:
            selectedMenu = m0.find(menuOption)
            m1.renderForMenu(selectedMenu=selectedMenu)
            periodOption = input(
                    colorText.BOLD + colorText.FAIL + "[+] Select option: "
                ) or ('L' if configManager.period == '1y' else 'S')
            OutputControls().printOutput(colorText.END, end="")
            if periodOption is None or periodOption.upper() not in ["L","S","B"]:
                return
            Utility.tools.clearScreen(forceTop=True)
            if periodOption.upper() in ["L","S"]:
                selectedMenu = m1.find(periodOption)
                m2.renderForMenu(selectedMenu=selectedMenu)
                durationOption = input(
                        colorText.BOLD + colorText.FAIL + "[+] Select option: "
                    ) or "1"
                OutputControls().printOutput(colorText.END, end="")
                if durationOption is None or durationOption.upper() not in ["1","2","3","4","5"]:
                    return
                Utility.tools.clearScreen(forceTop=True)
                if durationOption.upper() in ["1","2","3","4"]:
                    selectedMenu = m2.find(durationOption)
                    periodDurations = selectedMenu.menuText.split("(")[1].split(")")[0].split(", ")
                    configManager.period = periodDurations[0]
                    configManager.duration = periodDurations[1]
                    configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
                elif durationOption.upper() in ["5"]:
                    configManager.setConfig(ConfigManager.parser, default=False, showFileCreatedText=True)
                return
            elif periodOption.upper() in ["B"]:
                backtestDaysAgo = input(
                    colorText.BOLD + colorText.FAIL + "[+] Enter no. of days/candles in the past as starting candle for which you'd like to run the scans (e.g. 10 for 10 candles ago or 0 for today):"
                ) or ('22' if configManager.period == '1y' else '15')
                OutputControls().printOutput(colorText.END, end="")
                launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
                requestingUser = f" -u {userPassedArgs.user}" if userPassedArgs.user is not None else ""
                enableLog = f" -l" if userPassedArgs.log else ""
                launcher = f"python3.11 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
                OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener in quick backtest mode. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} --backtestdaysago {int(backtestDaysAgo)}{requestingUser}{enableLog}{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit quick backtest mode.{colorText.END}")
                sleep(2)
                os.system(f"{launcher} --systemlaunched -a Y -e --backtestdaysago {int(backtestDaysAgo)}{requestingUser}{enableLog}")
                sys.exit(0)
        elif userPassedArgs is not None and userPassedArgs.options is not None:
            options = userPassedArgs.options.split(":")
            selectedMenu = m0.find(options[0])
            m1.renderForMenu(selectedMenu=selectedMenu, asList=True)
            selectedMenu = m1.find(options[1])
            m2.renderForMenu(selectedMenu=selectedMenu)
            if options[2] in ["1","2","3","4"]:
                selectedMenu = m2.find(options[2])
                periodDurations = selectedMenu.menuText.split("(")[1].split(")")[0].split(", ")
                configManager.period = periodDurations[0]
                configManager.duration = periodDurations[1]
                configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
            else:
                toggleUserConfig()
        else:
            toggleUserConfig()
    elif menuOption == "E":
        configManager.setConfig(ConfigManager.parser)
    elif menuOption == "Y":
        showSendConfigInfo(defaultAnswer, user)
    return

def showSendConfigInfo(defaultAnswer=None, user=None):
    configData = configManager.showConfigFile(defaultAnswer=('Y' if user is not None else defaultAnswer))
    if user is not None:
        sendMessageToTelegramChannel(message=Utility.tools.removeAllColorStyles(configData), user=user)

def showSendHelpInfo(defaultAnswer=None, user=None):
    helpData = Utility.tools.showDevInfo(defaultAnswer=('Y' if user is not None else defaultAnswer))
    if user is not None:
        sendMessageToTelegramChannel(message=Utility.tools.removeAllColorStyles(helpData), user=user)

def initExecution(menuOption=None):
    global selectedChoice, userPassedArgs
    Utility.tools.clearScreen()
    if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None):
        OutputControls().printOutput(
        colorText.BOLD
        + colorText.FAIL
        + "[+] You chose: "
        + f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]"
        + colorText.END
    )
    m0.renderForMenu(selectedMenu=None)
    try:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = f"[+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)}{colorText.END} ]\n" if needsCalc else ""
        if menuOption is None:
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                from PKDevTools.classes import Archiver
                log_file_path = os.path.join(Archiver.get_user_outputs_dir(), "pkscreener-logs.txt")
                OutputControls().printOutput(colorText.FAIL + "\n    [+] Logs will be written to:"+colorText.END)
                OutputControls().printOutput(colorText.GREEN + f"    [+] {log_file_path}"+colorText.END)
                OutputControls().printOutput(colorText.FAIL + "    [+] If you need to share,run through the menus that are causing problems. At the end, open this folder, zip the log file to share at https://github.com/pkjmesra/PKScreener/issues .\n" + colorText.END)
            menuOption = input(colorText.BOLD + colorText.FAIL + f"{pastDate}[+] Select option: ")
            OutputControls().printOutput(colorText.END, end="")
        if menuOption == "" or menuOption is None:
            menuOption = "X"
        menuOption = menuOption.upper()
        selectedMenu = m0.find(menuOption)
        if selectedMenu is not None:
            if selectedMenu.menuKey == "Z":
                input(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] Press <Enter> to Exit!"
                    + colorText.END
                )
                sys.exit(0)
            elif selectedMenu.menuKey in ["B", "C", "G", "H", "U", "T", "S", "E", "X", "Y", "M", "D", "I", "L"]:
                Utility.tools.clearScreen(forceTop=True)
                selectedChoice["0"] = selectedMenu.menuKey
                return selectedMenu
            elif selectedMenu.menuKey in ["P"]:
                return selectedMenu
    except KeyboardInterrupt:
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
    Utility.tools.clearScreen()
    if menuOption is None:
        OutputControls().printOutput('You must choose an option from the previous menu! Defaulting to "X"...')
        menuOption = "X"
    OutputControls().printOutput(
        colorText.BOLD
        + colorText.FAIL
        + "[+] You chose: "
        + level0MenuDict[menuOption].strip() 
        + (f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]" if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None) else "")
        + colorText.END
    )
    if indexOption is None:
        selectedMenu = m0.find(menuOption)
        m1.renderForMenu(selectedMenu=selectedMenu, skip=skip)
    try:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = f"[+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)}{colorText.END} ]\n" if needsCalc else ""
        if indexOption is None:
            indexOption = input(
                colorText.BOLD + colorText.FAIL + f"{pastDate}[+] Select option: "
            )
            OutputControls().printOutput(colorText.END, end="")
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
                newlyListedOnly = True
                indexOption = 12
        if indexOption == 15:
            from pkscreener.classes.MarketStatus import MarketStatus
            MarketStatus().exchange = "^IXIC"
        selectedChoice["1"] = str(indexOption)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] Please enter a valid numeric option & Try Again!"
            + colorText.END
        )
        if not retrial:
            sleep(2)
            Utility.tools.clearScreen()
            return initPostLevel0Execution(retrial=True)
    return indexOption, executeOption


def initPostLevel1Execution(indexOption, executeOption=None, skip=[], retrial=False):
    global selectedChoice, userPassedArgs, listStockCodes
    if executeOption is None:
        if indexOption is not None and indexOption != "W":
            Utility.tools.clearScreen()
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.FAIL
                + "[+] You chose: "
                + level0MenuDict[selectedChoice["0"]].strip()
                + " > "
                + level1_X_MenuDict[selectedChoice["1"]].strip()
                + (f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]" if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None) else "")
                + colorText.END
            )
            selectedMenu = m1.find(indexOption)
            m2.renderForMenu(selectedMenu=selectedMenu, skip=skip)
            stockIndexCode = "2"
            if indexOption == "S":
                stockIndexCode = input(
                    colorText.BOLD + colorText.FAIL + "[+] Select option: "
                ) or "2"
                OutputControls().printOutput(colorText.END, end="")
                listStockCodes = [level1_index_options_sectoral[str(stockIndexCode)].split("(")[1].split(")")[0]]
                selectedMenu.menuKey = "0" # Reset because user must have selected specific index menu with single stock
                Utility.tools.clearScreen()
                m2.renderForMenu(selectedMenu=selectedMenu, skip=skip)
    try:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = f"[+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)}{colorText.END} ]\n" if needsCalc else ""
        if indexOption is not None and indexOption != "W":
            if executeOption is None:
                executeOption = input(
                    colorText.BOLD + colorText.FAIL + f"{pastDate}[+] Select option: "
                ) or "9"
                OutputControls().printOutput(colorText.END, end="")
            if executeOption == "":
                executeOption = 1
            if not str(executeOption).isnumeric():
                executeOption = executeOption.upper()
            else:
                executeOption = int(executeOption)
                if executeOption < 0 or executeOption > 44:
                    raise ValueError
        else:
            executeOption = 0
        selectedChoice["2"] = str(executeOption)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] Please enter a valid numeric option & Try Again!"
            + colorText.END
        )
        if not retrial:
            sleep(2)
            Utility.tools.clearScreen()
            return initPostLevel1Execution(indexOption, executeOption, retrial=True)
    return indexOption, executeOption

def labelDataForPrinting(screenResults, saveResults, configManager, volumeRatio,executeOption, reversalOption):
    # Publish to gSheet with https://github.com/burnash/gspread
    global menuChoiceHierarchy, userPassedArgs
    try:
        isTrading = PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]
        if "RUNNER" not in os.environ.keys() and (isTrading or userPassedArgs.monitor or ("RSIi" in saveResults.columns)) and configManager.calculatersiintraday:
            screenResults['RSI'] = screenResults['RSI'].astype(str) + "/" + screenResults['RSIi'].astype(str)
            saveResults['RSI'] = saveResults['RSI'].astype(str) + "/" + saveResults['RSIi'].astype(str)
            screenResults.rename(columns={"RSI": "RSI/i"},inplace=True)
            saveResults.rename(columns={"RSI": "RSI/i"},inplace=True)
        sortKey = ["Volume"] if "RSI" not in menuChoiceHierarchy else ("RSIi" if (isTrading or "RSIi" in saveResults.columns) else "RSI")
        ascending = [False if "RSI" not in menuChoiceHierarchy else True]
        if executeOption == 21:
            if reversalOption in [3,5,6,7]:
                sortKey = ["MFI"]
                ascending = [reversalOption in [6,7]]
            elif reversalOption in [8,9]:
                sortKey = ["FVDiff"]
                ascending = [reversalOption in [9]]
        elif executeOption == 7:
            if reversalOption in [3]:
                sortKey = ["Volume","MA-Signal"]
                ascending = [False, False]
        elif executeOption == 23:
            sortKey = ["bbands_ulr_ratio_max5"] if "bbands_ulr_ratio_max5" in screenResults.columns else ["Volume"]
            ascending = [False]
        elif executeOption == 27: # ATR Cross
            sortKey = ["ATR"] if "ATR" in screenResults.columns else ["Volume"]
            ascending = [False]
        elif executeOption == 31: # DEEL Momentum
            sortKey = ["Volume"]
            ascending = [False]
        try:
            try:
                screenResults[sortKey] = screenResults[sortKey].replace("", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            except:
                pass
            try:
                saveResults[sortKey] = saveResults[sortKey].replace("", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
            except:
                pass
            screenResults.sort_values(by=sortKey, ascending=ascending, inplace=True)
            saveResults.sort_values(by=sortKey, ascending=ascending, inplace=True)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass
        columnsToBeDeleted = ["MFI","FVDiff","ConfDMADifference","bbands_ulr_ratio_max5", "RSIi"]
        if userPassedArgs is not None and userPassedArgs.options is not None and userPassedArgs.options.upper().startswith("C"):
            columnsToBeDeleted.append("FairValue")
        if executeOption == 27 and "ATR" in screenResults.columns: # ATR Cross
            columnsToBeDeleted.append("Consol.")
            screenResults['ATR'] = screenResults['ATR'].astype(str)
            screenResults['ATR'] = colorText.GREEN + screenResults['ATR'] + colorText.END
        for column in columnsToBeDeleted:
            if column in saveResults.columns:
                saveResults.drop(column, axis=1, inplace=True, errors="ignore")
                screenResults.drop(column, axis=1, inplace=True, errors="ignore")
        if "Stock" in screenResults.columns:
            screenResults.set_index("Stock", inplace=True)
        if "Stock" in saveResults.columns:
            saveResults.set_index("Stock", inplace=True)
        screenResults['Volume'] = screenResults['Volume'].astype(str)
        saveResults['Volume'] = saveResults['Volume'].astype(str)
        screenResults.loc[:, "Volume"] = screenResults.loc[:, "Volume"].apply(
            lambda x: Utility.tools.formatRatio(float(Utility.tools.removeAllColorStyles(x)), volumeRatio) if len(str(x).strip()) > 0 else ''
        )
        saveResults.loc[:, "Volume"] = saveResults.loc[:, "Volume"].apply(
            lambda x: str(x) + "x"
        )
        screenResults.rename(
            columns={
                "Trend": f"Trend({configManager.daysToLookback}Prds)",
                "Breakout": f"Breakout({configManager.daysToLookback}Prds)",
                # "Consol.": f"Consol.({configManager.daysToLookback}Prds)",
            },
            inplace=True,
        )
        saveResults.rename(
            columns={
                "Trend": f"Trend({configManager.daysToLookback}Prds)",
                "Breakout": f"Breakout({configManager.daysToLookback}Prds)",
                # "Consol.": f"Consol.({configManager.daysToLookback}Prds)",
            },
            inplace=True,
        )
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
    return screenResults, saveResults

def isInterrupted():
    global keyboardInterruptEventFired
    return keyboardInterruptEventFired

def refreshStockData(startupoptions=None):
    global consumers,stockDictPrimary, loadedStockData, listStockCodes, stockDictSecondary
    options = startupoptions.replace("|","").split(" ")[0].replace(":i","")
    loadedStockData = False
    options, menuOption, indexOption, executeOption = getTopLevelMenuChoices(
        options, False, False, defaultAnswer='Y'
    )
    if indexOption == 0:
        listStockCodes = handleRequestForSpecificStocks(options,indexOption=indexOption)
    listStockCodes = prepareStocksForScreening(testing=False, downloadOnly=False, listStockCodes=listStockCodes,indexOption=indexOption)
    stockDictPrimary,stockDictSecondary = loadDatabaseOrFetch(downloadOnly=False, listStockCodes=listStockCodes, menuOption=menuOption,indexOption=indexOption)
    PKScanRunner.refreshDatabase(consumers,stockDictPrimary,stockDictSecondary)

def closeWorkersAndExit():
    global consumers, tasks_queue,userPassedArgs
    if consumers is not None:
        PKScanRunner.terminateAllWorkers(userPassedArgs=userPassedArgs,consumers=consumers, tasks_queue=tasks_queue, testing=userPassedArgs.testbuild)
    
# @tracelog
def main(userArgs=None,optionalFinalOutcome_df=None):
    global mp_manager, listStockCodes, screenResults, selectedChoice, defaultAnswer, menuChoiceHierarchy, screenCounter, screenResultsCounter, stockDictPrimary, stockDictSecondary, userPassedArgs, loadedStockData, keyboardInterruptEvent, loadCount, maLength, newlyListedOnly, keyboardInterruptEventFired,strategyFilter, elapsed_time, start_time
    selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
    elapsed_time = 0
    start_time = 0
    testing = False if userArgs is None else (userArgs.testbuild and userArgs.prodbuild)
    testBuild = False if userArgs is None else (userArgs.testbuild and not testing)
    downloadOnly = False if userArgs is None else userArgs.download
    startupoptions = None if userArgs is None else userArgs.options
    user = None if userArgs is None else userArgs.user
    defaultAnswer = None if userArgs is None else userArgs.answerdefault
    userPassedArgs = userArgs
    options = []
    strategyFilter=[]
    if keyboardInterruptEventFired:
        return None, None
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
    if stockDictPrimary is None:
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
    listStockCodes = None
    if userPassedArgs.log:
        default_logger().debug(f"User Passed args: {userPassedArgs}")
    screenResults, saveResults = PKScanRunner.initDataframes()
    options, menuOption, indexOption, executeOption = getTopLevelMenuChoices(
        startupoptions, testBuild, downloadOnly, defaultAnswer=defaultAnswer
    )
    # Print Level 1 menu options
    selectedMenu = initExecution(menuOption=menuOption)
    menuOption = selectedMenu.menuKey
    if menuOption in ["M", "D", "I", "L"]:
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        launcher = f"python3.11 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
        if menuOption in ["M"]:
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener in monitoring mode. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -m 'X'{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit monitoring mode.{colorText.END}")
            sleep(2)
            os.system(f"{launcher} -a Y -m 'X'")
        elif menuOption in ["D"]:
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to Download daily OHLC data. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -e -d{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            sleep(2)
            os.system(f"{launcher} -a Y -e -d")
        elif menuOption in ["I"]:
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to Download intraday OHLC data. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -e -d -i 1m{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            sleep(2)
            os.system(f"{launcher} -a Y -e -d -i 1m")
        elif menuOption in ["L"]:
            OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener to collect logs. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -l{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}")
            sleep(2)
            os.system(f"{launcher} -a Y -l")
        sys.exit(0)
    if menuOption in ["P"]:
        predefinedOption = None
        selPredefinedOption = None
        if len(options) >= 3:
            predefinedOption = str(options[1])
            selPredefinedOption = str(options[2])
        updateMenuChoiceHierarchy()
        selectedMenu = m0.find(menuOption)
        m1.renderForMenu(selectedMenu)
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = f"[+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)}{colorText.END} ]\n" if needsCalc else ""
        if predefinedOption is None:
            predefinedOption = input(colorText.BOLD + colorText.FAIL + f"{pastDate}[+] Select option: ") or "1"
        OutputControls().printOutput(colorText.END, end="")
        if predefinedOption not in ["1","2","3"]:
            return None, None
        if predefinedOption == "1":
            updateMenuChoiceHierarchy()
            selectedMenu = m1.find(predefinedOption)
            m2.renderForMenu(selectedMenu=selectedMenu)
            if selPredefinedOption is None:
                selPredefinedOption = input(colorText.BOLD + colorText.FAIL + f"{pastDate}[+] Select option: ") or "1"
            OutputControls().printOutput(colorText.END, end="")
            if selPredefinedOption in PREDEFINED_SCAN_MENU_KEYS:
                scannerOption = PIPED_SCANNERS[selPredefinedOption]
                updateMenuChoiceHierarchy()
                if userPassedArgs.pipedmenus is not None:
                    chosenOptions = scannerOption.split("-o ")[1]
                    userPassedArgs.options = chosenOptions.replace("'","")
                    return addOrRunPipedMenus()
                launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
                launcher = f"python3.11 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
                scannerOptionQuoted = scannerOption.replace("'",'"')
                requestingUser = f" -u {userPassedArgs.user}" if userPassedArgs.user is not None else ""
                enableLog = f" -l" if userPassedArgs.log else ""
                backtestParam = f" --backtestdaysago {userPassedArgs.backtestdaysago}" if userPassedArgs.backtestdaysago else ""
                OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener with piped scanners. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} {scannerOptionQuoted}{requestingUser}{enableLog}{backtestParam}{colorText.END}")
                sleep(2)
                os.system(f"{launcher} {scannerOptionQuoted}{requestingUser}{enableLog}{backtestParam}")
                OutputControls().printOutput(
                        colorText.GREEN
                        + f"[+] Finished running all piped scanners!"
                        + colorText.END
                    )
                if defaultAnswer is None:
                    input("Press <Enter> to exit...")
                sys.exit(0)
            else:
                return None, None
        elif predefinedOption == "2":
            # User chose custom
            menuOption = "X" # Let's have the user choose various scan options
            selectedMenu = m0.find(menuOption)
            selectedChoice["0"] = selectedMenu.menuKey
            if userPassedArgs.pipedmenus is None:
                userPassedArgs.pipedmenus = ""
        elif predefinedOption == "3":
            if userPassedArgs.pipedmenus is not None:
                return addOrRunPipedMenus()
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

        if menuOption in ["H", "U", "T", "E", "Y"]:
            Utility.tools.clearScreen(forceTop=True)
            return None, None
    elif menuOption in ["B", "G"]:
        # Backtests
        backtestPeriod = 0
        if len(options) >= 2:
            if str(indexOption).isnumeric():
                backtestPeriod = int(indexOption)
            if len(options) >= 4:
                indexOption = executeOption
                executeOption = options[3]
            del options[1]  # Let's delete the backtestperiod from the provided options
        indexOption, executeOption, backtestPeriod = takeBacktestInputs(
            str(menuOption).upper(), indexOption, executeOption, backtestPeriod
        )
        backtestPeriod = backtestPeriod * configManager.backtestPeriodFactor
    elif menuOption in ["S"]:
        if len(options) >= 2:
            userOption = options[1]
        if defaultAnswer is None:
            selectedMenu = m0.find(menuOption)
            m1.strategyNames = PortfolioXRay.strategyNames()
            m1.renderForMenu(selectedMenu=selectedMenu)
            try:
                userOption = input(
                            colorText.BOLD + colorText.FAIL + "[+] Select option: "
                        )
                OutputControls().printOutput(colorText.END, end="")
                if userOption == "":
                    userOption = "37" # NoFilter
                elif userOption == "38":
                    userOption = input(
                            colorText.BOLD + colorText.FAIL + "[+] Enter Exact Pattern name:"
                        )
                    OutputControls().printOutput(colorText.END, end="")
                    if userOption == "":
                        userOption = "37" # NoFilter
                    else:
                        strategyFilter.append(f"[P]{userOption}")
                        userOption = "38"
            except EOFError:  # pragma: no cover
                userOption = "37"  # NoFilter
                pass
            except Exception as e:# pragma: no cover
                default_logger().debug(e, exc_info=True)
                pass
        userOption = userOption.upper()
        if userOption == "M":
            Utility.tools.clearScreen(forceTop=True)
            # Go back to the caller. It will show the console menu again.
            return None, None
        elif userOption == "Z":
            handleExitRequest(userOption)
            return None, None
        
        if userOption == "S":
            OutputControls().printOutput(
                colorText.GREEN
                + "[+] Collecting all metrics for summarising..."
                + colorText.END
            )
            # Enable showing/saving past strategy data
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
                showBacktestResults(
                    df_all, sortKey="Scanner", optionalName="InsightsSummary"
                )
            else:
                OutputControls().printOutput("[!] Nothing to show here yet. Check back later.")
            # reinstate whatever was the earlier saved value
            configManager.showPastStrategyData = savedValue
            if defaultAnswer is None:
                input("Press <Enter> to continue...")
            return None, None
        else:
            userOptions = userOption.split(",")
            for usrOption in userOptions:
                strategyFilter.append(m1.find(usrOption).menuText.strip())
            menuOption, indexOption, executeOption, selectedChoice = getScannerMenuChoices(
            testBuild or testing,
            downloadOnly,
            startupoptions,
            menuOption="X",
            indexOption=indexOption,
            executeOption=executeOption,
            defaultAnswer=defaultAnswer,
            user=user,
        )

    else:
        OutputControls().printOutput("Not implemented yet! Try selecting a different option.")
        sleep(3)
        return None, None

    handleMenu_XBG(menuOption, indexOption, executeOption)
    if indexOption == "M" or executeOption == "M":
        Utility.tools.clearScreen(forceTop=True)
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
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 5:
            if str(options[3]).isnumeric():
                minRSI = int(options[3])
                maxRSI = int(options[4])
            elif str(options[3]).upper() == "D":
                # Use a default value
                minRSI = 60
                maxRSI = 75
        else:
            minRSI, maxRSI = Utility.tools.promptRSIValues()
        if not minRSI and not maxRSI:
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Error: Invalid values for RSI! Values should be in range of 0 to 100. Please try again!"
                + colorText.END
            )
            input("PRess <Enter> to continue...")
            return None, None
    if executeOption == 6:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            reversalOption = int(options[3])
            if reversalOption in [4, 6, 7, 10]:
                if len(options) >= 5:
                    if str(options[4]).isnumeric():
                        maLength = int(options[4])
                    elif str(options[4]).upper() == "D":
                        maLength = 50 if reversalOption == 4 else (3 if reversalOption in [7] else (2 if reversalOption in [10] else 7))
                elif defaultAnswer == "Y" and user is not None:
                    # bot mode
                    maLength = 50 if reversalOption == 4 else (3 if reversalOption == 7 else 7)
                else:
                    reversalOption, maLength = Utility.tools.promptReversalScreening(
                        selectedMenu
                    )
        else:
            reversalOption, maLength = Utility.tools.promptReversalScreening(
                selectedMenu
            )
        if reversalOption is None or reversalOption == 0 or maLength == 0:
            return None, None
        else:
            selectedChoice["3"] = str(reversalOption)
            if str(reversalOption) in ["7", "10"]:
                selectedChoice["4"] = str(maLength)
    if executeOption == 7:
        selectedMenu = m2.find(str(executeOption))
        maLength = 0
        if len(options) >= 4:
            respChartPattern = int(options[3])
            selectedChoice["3"] = options[3]
            if respChartPattern in [1, 2, 3]:
                if len(options) >= 5:
                    if "".join(str(options[4]).split(".")).isdecimal():
                        insideBarToLookback = float(options[4])
                    elif str(options[4]).upper() == "D":
                        insideBarToLookback = 7 if respChartPattern in [1, 2] else 0.02
                    if len(options) >= 6:
                        if str(options[5]).isnumeric():
                            maLength = int(options[5])
                        elif str(options[5]).upper() == "D":
                            maLength = 1 # Conf. up
                elif defaultAnswer == "Y" and user is not None:
                    # bot mode
                    insideBarToLookback = 7 if respChartPattern in [1, 2] else 0.02
                    maLength = 1 if respChartPattern in [3] else 0
                else:
                    (
                        respChartPattern,
                        insideBarToLookback,
                    ) = Utility.tools.promptChartPatterns(selectedMenu)
                if maLength == 0:
                    maLength = Utility.tools.promptChartPatternSubMenu(selectedMenu, respChartPattern)
            elif respChartPattern in [0, 4, 5, 6, 7, 8, 9]:
                insideBarToLookback = 0
                if respChartPattern == 6 or respChartPattern == 9:
                    if len(options) >= 5:
                        if str(options[4]).isnumeric():
                            maLength = int(options[4])
                        elif str(options[4]).upper() == "D":
                            maLength = 1 if respChartPattern == 6 else 6 # Bollinger Bands Squeeze-Buy or MA-Support
                    elif defaultAnswer == "Y" and user is not None:
                        # bot mode
                        maLength = 4 if respChartPattern == 6 else 6 # Bollinger Bands Squeeze- Any/All or MA-Support
                    else:
                        maLength = Utility.tools.promptChartPatternSubMenu(selectedMenu,respChartPattern)
            else:
                (
                    respChartPattern,
                    insideBarToLookback,
                ) = Utility.tools.promptChartPatterns(selectedMenu)
        else:
            respChartPattern, insideBarToLookback = Utility.tools.promptChartPatterns(
                selectedMenu
            )
            if maLength == 0 and respChartPattern in [1, 2, 3, 6, 9]:
                maLength = Utility.tools.promptChartPatternSubMenu(selectedMenu, respChartPattern)
        if (
            respChartPattern is None
            or insideBarToLookback is None
            or respChartPattern == 0
            or (maLength == 0 and respChartPattern in [1, 2, 3, 6, 9])
        ):
            return None, None
        else:
            userPassedArgs.maxdisplayresults = max(configManager.maxdisplayresults,2000) if respChartPattern in [3,4,5,8,9] else min(configManager.maxdisplayresults,userPassedArgs.maxdisplayresults)
            selectedChoice["3"] = str(respChartPattern)
            selectedChoice["4"] = str(insideBarToLookback) if (respChartPattern in [1, 2, 3] and (userPassedArgs is not None and userPassedArgs.pipedmenus is not None)) else str(maLength)
            selectedChoice["5"] = str(maLength) if (respChartPattern in [1, 2, 3] and (userPassedArgs is not None and userPassedArgs.pipedmenus is not None)) else ""
    if executeOption == 8:
        if len(options) >= 5:
            if "".join(str(options[3]).split(".")).isdecimal():
                minRSI = int(options[3])
            if "".join(str(options[4]).split(".")).isdecimal():
                maxRSI = int(options[4])
            if str(options[3]).upper() == "D":
                minRSI = -150
                maxRSI = 250
        else:
            minRSI, maxRSI = Utility.tools.promptCCIValues()
        if not minRSI and not maxRSI:
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Error: Invalid values for CCI! Values should be in range of -300 to 500. Please try again!"
                + colorText.END
            )
            input("Press <Enter> to continue...")
            return None, None
    if executeOption == 9:
        if len(options) >= 4:
            if str(options[3]).isnumeric():
                volumeRatio = float(options[3])
            elif str(options[3]).upper() == "D":
                volumeRatio = configManager.volumeRatio
        else:
            volumeRatio = Utility.tools.promptVolumeMultiplier()
        if volumeRatio <= 0:
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Error: Invalid values for Volume Ratio! Value should be a positive number. Please try again!"
                + colorText.END
            )
            input("Press <Enter> to continue...")
            return None, None
        else:
            configManager.volumeRatio = float(volumeRatio)
    if executeOption == 12:
        candleDuration = userPassedArgs.intraday if (userPassedArgs is not None and userPassedArgs.intraday is not None) else ("15m")
        configManager.toggleConfig(candleDuration=candleDuration)
        global nValueForMenu 
        nValueForMenu = candleDuration
    if executeOption == 21:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            popOption = int(options[3])
            if popOption >= 0 and popOption <= 9:
                pass
        else:
            popOption = Utility.tools.promptSubMenuOptions(selectedMenu)
        if popOption is None or popOption == 0:
            return None, None
        else:
            selectedChoice["3"] = str(popOption)
        if popOption in [1,2,4]:
            updateMenuChoiceHierarchy()
            if popOption == 4:
                screenResults = mstarFetcher.fetchMorningstarTopDividendsYieldStocks()
            elif popOption in [1,2]:
                screenResults = mstarFetcher.fetchMorningstarFundFavouriteStocks(
                    "NoOfFunds" if popOption == 2 else "ChangeInShares"
                )
            if menuOption in ["X"]:
                printNotifySaveScreenedResults(
                    screenResults,
                    screenResults,
                    selectedChoice,
                    menuChoiceHierarchy,
                    False,
                    None,
                )
                if defaultAnswer is None:
                    input("Press <Enter> to continue...")
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
            popOption = Utility.tools.promptSubMenuOptions(selectedMenu)
        if popOption is None or popOption == 0:
            return None, None
        else:
            selectedChoice["3"] = str(popOption)
        updateMenuChoiceHierarchy()
        screenResults = mstarFetcher.fetchMorningstarStocksPerformanceForExchange()
        if menuOption in ["X"]:
            printNotifySaveScreenedResults(
                screenResults,
                screenResults,
                selectedChoice,
                menuChoiceHierarchy,
                False,
                None,
            )
            if defaultAnswer is None:
                input("Press <Enter> to continue...")
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
            colorText.BOLD
            + colorText.FAIL
            + message
            + colorText.END
        )
        if defaultAnswer is None:
            input("Press <Enter> to continue...")
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
            maLength = Utility.tools.promptSubMenuOptions(selectedMenu)
        if maLength == 0:
            return None, None
        else:
            selectedChoice["3"] = str(maLength)
    if executeOption == 30:
        if userPassedArgs.options is None:
            Utility.tools.clearScreen(forceTop=True)
            atrSensitivity = input(colorText.WARN + f"Enter the ATR Trailing Stop Sensitivity (Multiplier) value (Optimal:1, Current={configManager.atrTrailingStopSensitivity}):") or configManager.atrTrailingStopSensitivity
            configManager.atrTrailingStopSensitivity = atrSensitivity
            atrPeriod = input(colorText.WARN + f"Enter the ATR Period value (Optimal:10, Current={configManager.atrTrailingStopPeriod}):") or configManager.atrTrailingStopPeriod
            configManager.atrTrailingStopPeriod = atrPeriod
            atrEma = input(colorText.WARN + f"Enter the ATR EMA period (Optimal:200, Current={configManager.atrTrailingStopEMAPeriod}):") or configManager.atrTrailingStopEMAPeriod
            configManager.atrTrailingStopEMAPeriod = atrEma
            configManager.setConfig(ConfigManager.parser,default=True,showFileCreatedText=False)
        # Ensure we have the template JSONs from vectorBt
        screener.shouldLog = userPassedArgs.log
        screener.computeBuySellSignals(None)

    if executeOption == 42:
        Utility.tools.getLastScreenedResults(defaultAnswer)
        return None, None
    if executeOption >= MAX_SUPPORTED_MENU_OPTION and executeOption <= MAX_MENU_OPTION:
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.FAIL
            + F"\n[+] Error: Option {MAX_SUPPORTED_MENU_OPTION} to {MAX_MENU_OPTION} Not implemented yet! Press <Enter> to continue."
            + colorText.END
        )
        input("Press <Enter> to continue...")
        return None, None
    if (
        not str(indexOption).isnumeric() and indexOption in ["W", "E", "M", "N", "Z", "S"]
    ) or (
        str(indexOption).isnumeric()
        and (int(indexOption) >= 0 and int(indexOption) < 16)
    ):
        configManager.getConfig(ConfigManager.parser)
        try:
            if indexOption == "W":
                listStockCodes = fetcher.fetchWatchlist()
                if listStockCodes is None:
                    input(
                        colorText.BOLD
                        + colorText.FAIL
                        + f"[+] Please create the watchlist.xlsx file in {os.getcwd()} and Restart the Program!"
                        + colorText.END
                    )
                    sys.exit(0)
            elif indexOption == "N":
                os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
                prediction, pText, sText = screener.getNiftyPrediction(
                    df=fetcher.fetchLatestNiftyDaily(proxyServer=fetcher.proxyServer)
                )
                warningText = "\nNifty AI prediction works best if you request after market is closed. It may not be accurate while market is still open!" if "Open" in Utility.marketStatus() else ""
                try:
                    todayHoliday, todayOccassion = PKDateUtilities.isHoliday(PKDateUtilities.currentDateTime())
                    nextWeekday = PKDateUtilities.nextWeekday()
                    tomorrowHoliday,tomorrowOccassion = PKDateUtilities.isHoliday(nextWeekday)
                    if todayHoliday:
                        warningText = f"{warningText}\n\nMarket is closed today due to {todayOccassion}."
                    if tomorrowHoliday:
                        warningText = f"{warningText}\n\nMarket will be closed on {nextWeekday.strftime('%Y-%m-%d')} due to {tomorrowOccassion}."
                except:
                    pass
                sendMessageToTelegramChannel(
                    message=f"{Utility.tools.removeAllColorStyles(Utility.marketStatus())}\nNifty AI prediction for the Next Day: {pText}. {sText}.{warningText}",
                    user=user,
                )
                if defaultAnswer is None:
                    input("\nPress <Enter> to Continue...\n")
                return None, None
            elif indexOption == "M":
                return None, None
            elif indexOption == "Z":
                input(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] Press <Enter> to Exit!"
                    + colorText.END
                )
                sys.exit(0)
            elif indexOption == "E":
                return handleMonitorFiveEMA()
            else:
                if str(menuOption).upper() == "C":
                    stockDictPrimary,endOfdayCandles = PKMarketOpenCloseAnalyser.getStockDataForSimulation()
                    if stockDictPrimary is None or endOfdayCandles is None:
                        OutputControls().printOutput(f"Cannot proceed! Stock data is unavailable. Please check the error logs/messages !")
                        return None, None
                    if indexOption > 0:
                        listStockCodes = sorted(list(filter(None,list(set(stockDictPrimary.keys())))))
                if str(indexOption) not in ["S"]:
                    listStockCodes = prepareStocksForScreening(testing, downloadOnly, listStockCodes, indexOption)
        except urllib.error.URLError as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.FAIL
                + "\n\n[+] Oops! It looks like you don't have an Internet connectivity at the moment!"
                + colorText.END
            )
            input("Exiting now...")
            sys.exit(0)
        if userPassedArgs.options is None or len(userPassedArgs.options) == 0:
            userPassedArgs.options = ""
            for choice in selectedChoice.keys():
                userPassedArgs.options = (f"{userPassedArgs.options}:" if len(userPassedArgs.options) > 0  else '') + f"{selectedChoice[choice]}"
        if userPassedArgs.pipedmenus is not None:
            return addOrRunPipedMenus()

        if (menuOption in ["X", "B", "G", "S"] and not loadedStockData) or (
            # not downloadOnly
            # and not PKDateUtilities.isTradingTime()
            # and 
            configManager.cacheEnabled
            and not loadedStockData
            and not testing
        ):
            stockDictPrimary,stockDictSecondary = loadDatabaseOrFetch(downloadOnly, listStockCodes, menuOption, indexOption)
            
        loadCount = len(stockDictPrimary) if stockDictPrimary is not None else 0

        if downloadOnly:
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.WARN
                + "[+] Starting download.. Press Ctrl+C to stop!"
            )
            if not configManager.isIntradayConfig():
                fetcher.saveAllNSEIndices()
        if menuOption.upper() in ["B", "G"]:
            OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + f"[+] A total of {configManager.backtestPeriod} trading periods' historical data will be considered for backtesting. You can change this in User Config."
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
        OutputControls().printOutput(f"{colorText.GREEN}[+] Adding stocks to the queue...{colorText.END}")
        with alive_bar(actualHistoricalDuration, bar=bar, spinner=spinner) as progressbar:
            while actualHistoricalDuration >= 0:
                daysInPast = PKScanRunner.getBacktestDaysForScan(userPassedArgs, backtestPeriod, menuOption, actualHistoricalDuration)
                try:
                    listStockCodes, savedStocksCount, pastDate = PKScanRunner.getStocksListForScan(userPassedArgs, menuOption, totalStocksInReview, downloadedRecently, daysInPast) if menuOption not in ["C"] else (listStockCodes, 0, "")
                except KeyboardInterrupt:
                    try:
                        keyboardInterruptEvent.set()
                        keyboardInterruptEventFired = True
                        actualHistoricalDuration = -1
                        break
                    except KeyboardInterrupt:
                        pass
                    OutputControls().printOutput(
                        colorText.BOLD
                        + colorText.FAIL
                        + "\n[+] Terminating Script, Please wait..."
                        + colorText.END
                    )
                except Exception:
                    pass
                exchangeName = "NASDAQ" if (indexOption == 15 or (configManager.defaultIndex == 15 and indexOption == 0)) else "INDIA"
                PKScanRunner.addStocksToItemList(userPassedArgs, testing, testBuild, newlyListedOnly, downloadOnly, minRSI, maxRSI, insideBarToLookback, respChartPattern, daysForLowestVolume, backtestPeriod, reversalOption, maLength, listStockCodes, menuOption,exchangeName,executeOption, volumeRatio, items, daysInPast)
                if savedStocksCount > 0:
                    progressbar.text(
                        colorText.BOLD
                        + colorText.GREEN
                        + f"Total Stocks: {len(items)}. Added {savedStocksCount} to Stocks from {pastDate} saved from earlier..."
                        + colorText.END
                    )
                fillerPlaceHolder = fillerPlaceHolder + 1
                actualHistoricalDuration = samplingDuration - fillerPlaceHolder
                if actualHistoricalDuration >= 0:
                    progressbar()
        sys.stdout.write(f"\x1b[1A") # Replace the download progress bar and start writing on the same line
        if not keyboardInterruptEventFired:
            global tasks_queue, results_queue, consumers, logging_queue
            screenResults, saveResults, backtest_df, tasks_queue, results_queue, consumers,logging_queue = PKScanRunner.runScanWithParams(userPassedArgs,keyboardInterruptEvent,screenCounter,screenResultsCounter,stockDictPrimary,stockDictSecondary,testing, backtestPeriod, menuOption,executeOption, samplingDuration, items,screenResults, saveResults, backtest_df,scanningCb=runScanners,tasks_queue=tasks_queue, results_queue=results_queue, consumers=consumers,logging_queue=logging_queue)
            if userPassedArgs is not None and (userPassedArgs.monitor is None and "|" not in userPassedArgs.options and not userPassedArgs.options.upper().startswith("C")):
                tasks_queue = None
                results_queue = None
                consumers = None
            if menuOption in ["C"]:
                runOptionName = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
                PKMarketOpenCloseAnalyser.runOpenCloseAnalysis(stockDictPrimary,endOfdayCandles,screenResults, saveResults,runOptionName=runOptionName,filteredListOfStocks=listStockCodes)
            if downloadOnly and menuOption in ["X"]:
                screener.getFreshMFIStatus(stock="LatestCheckedOnDate")
                screener.getFairValue(stock="LatestCheckedOnDate", force=True)
            if not downloadOnly and menuOption in ["X", "G", "C"]:
                if menuOption == "G":
                    userPassedArgs.backtestdaysago = backtestPeriod
                if screenResults is not None and len(screenResults) > 0:
                    screenResults, saveResults = labelDataForPrinting(
                        screenResults, saveResults, configManager, volumeRatio, executeOption, reversalOption or respChartPattern
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
                if not newlyListedOnly and not configManager.showunknowntrends and screenResults is not None and len(screenResults) > 0:
                    screenResults, saveResults = removeUnknowns(screenResults, saveResults)
                    OutputControls().printOutput(colorText.FAIL + f"[+] Configuration to remove unknown cell values resulted into removing all rows!" + colorText.END)
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
                        OutputControls().printOutput(colorText.FAIL + f"[+] Of the {len(screenResults) if screenResults is not None else 0} stocks, no results matching the selected strategies!" + colorText.END)
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
                            shouldSend = True
                        shareable_strings.append(tab_results)
                        OutputControls().printOutput(tab_results)
                    if shouldSend:
                        sendQuickScanResult(
                            menuChoiceHierarchy,
                            user,
                            shareable_strings[0],
                            Utility.tools.removeAllColorStyles(shareable_strings[0]),
                            "NSE Stocks with dividends/bonus/splits soon",
                            f"PKS_X_12_26_{PKDateUtilities.currentDateTime().strftime('%Y-%m-%d_%H:%M:%S')}",
                            ".png",
                            addendum=shareable_strings[1],
                            addendumLabel="NSE Stocks giving bonus:",
                            backtestSummary=shareable_strings[2],
                            backtestDetail="",
                            summaryLabel = "NSE Stocks with corporate action type stock split:",
                            detailLabel = None,
                            )
                elif "|" not in userPassedArgs.options:
                    try:
                        printNotifySaveScreenedResults(
                            screenResults,
                            saveResults,
                            selectedChoice,
                            menuChoiceHierarchy,
                            testing,
                            user=user,
                        )
                    except Exception as e:
                        default_logger().debug(e, exc_info=True)
                        if userPassedArgs.log:
                            import traceback
                            traceback.print_exc()
                        pass
        if menuOption in ["X","C"] and userPassedArgs.monitor is None:
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

        if menuOption == "B" and backtest_df is not None and len(backtest_df) > 0:
            Utility.tools.clearScreen()
            # Let's do the portfolio calculation first
            df_xray = prepareGroupedXRay(backtestPeriod, backtest_df)
            summary_df, sorting, sortKeys = FinishBacktestDataCleanup(backtest_df, df_xray)
            while sorting:
                sorting = showSortedBacktestData(backtest_df, summary_df, sortKeys)
            if defaultAnswer is None:
                input("Press <Enter> to continue...")
        elif menuOption == "B":
            OutputControls().printOutput("Finished backtesting with no results to show!")
        elif menuOption == "G":
            if defaultAnswer is None:
                input("Press <Enter> to continue...")
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
                OutputControls().printOutput(f"{colorText.GREEN}[+] Saving data to Google Spreadsheets now...{colorText.END}")
                gClient = PKSpreadsheets(credentialDictStr=creds)
                runOption = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
                df = saveResults.copy()
                df["LastTradeDate"], df["LastTradeTime"] = getLatestTradeDateTime(stockDictPrimary)
                gClient.df_to_sheet(df=df,sheetName=runOption)
                OutputControls().printOutput(f"{colorText.GREEN} => Done in {round(time.time()-begin,2)}s{colorText.END}")
    except:
        pass
    if "RUNNER" not in os.environ.keys() and not testing and (userPassedArgs is None or (userPassedArgs is not None and userPassedArgs.user is None and (userPassedArgs.answerdefault is None or userPassedArgs.systemlaunched))):
        prevOutput_results = saveResults.index if (saveResults is not None and not saveResults.empty) else []
        isNotPiped = (("|" not in userPassedArgs.options) if (userPassedArgs is not None and userPassedArgs.options is not None) else True)
        hasFoundStocks = len(prevOutput_results) > 0 and isNotPiped
        if hasFoundStocks or (configManager.showPinnedMenuEvenForNoResult and isNotPiped):
            monitorOption = userPassedArgs.systemlaunched if (userPassedArgs is not None and isinstance(userPassedArgs.systemlaunched,str) and userPassedArgs.systemlaunched is not None) else (userPassedArgs.options if (userPassedArgs is not None and userPassedArgs.options is not None) else "")
            if len(monitorOption) == 0:
                for choice in selectedChoice.keys():
                    monitorOption = (f"{monitorOption}:" if len(monitorOption) > 0  else '') + f"{selectedChoice[choice]}"
            m0.renderPinnedMenu(substitutes=[monitorOption,len(prevOutput_results)])
            pinOption = input(
                    colorText.BOLD + colorText.FAIL + "[+] Select option: "
                ) or 'M'
            OutputControls().printOutput(colorText.END, end="")
            if pinOption in ["1","2"]:
                if pinOption in ["2"]:
                    monitorOption = "X:0:0"
                    prevOutput_results = ",".join(prevOutput_results)
                    monitorOption = f"{monitorOption}:{prevOutput_results}"
                launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
                launcher = f"python3.11 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
                monitorOption = f'"{monitorOption}"'
                scannerOptionQuoted = monitorOption.replace("'",'"')
                OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener with pinned scan option. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -m {scannerOptionQuoted}{colorText.END}")
                sleep(2)
                os.system(f"{launcher} -a Y -m {scannerOptionQuoted}")

    if userPassedArgs is not None:
        if userPassedArgs.runintradayanalysis:
            analysis_df = screenResults.copy()
            analysis_df.reset_index(inplace=True)
            if 'index' in analysis_df.columns:
                analysis_df.drop('index', axis=1, inplace=True, errors="ignore")
            if optionalFinalOutcome_df is None:
                optionalFinalOutcome_df = analysis_df
            else:
                optionalFinalOutcome_df = pd.concat([optionalFinalOutcome_df, analysis_df], axis=0)
            return optionalFinalOutcome_df, saveResults
        else:
            existingTitle = f"{userPassedArgs.pipedtitle}|" if userPassedArgs.pipedtitle is not None else ""
            choiceSegments = menuChoiceHierarchy.split(">")
            choiceSegments = f"{choiceSegments[-2]} > {choiceSegments[-1]}" if len(choiceSegments)>=4 else f"{choiceSegments[-1]}"
            userPassedArgs.pipedtitle = f'{existingTitle}{choiceSegments}[{len(saveResults)}]'
            return screenResults, saveResults

def loadDatabaseOrFetch(downloadOnly, listStockCodes, menuOption, indexOption):
    global stockDictPrimary,stockDictSecondary, configManager, defaultAnswer, userPassedArgs, loadedStockData
    if menuOption not in ["C"]:
        stockDictPrimary = Utility.tools.loadStockData(
                    stockDictPrimary,
                    configManager,
                    downloadOnly=downloadOnly,
                    defaultAnswer=defaultAnswer,
                    forceLoad=(menuOption in ["X", "B", "G", "S"]),
                    stockCodes = listStockCodes,
                    exchangeSuffix = "" if (indexOption == 15 or (configManager.defaultIndex == 15 and indexOption == 0)) else ".NS"
            )
    if menuOption not in ["C"] and (userPassedArgs.monitor is not None or "|" in userPassedArgs.options) :#not configManager.isIntradayConfig() and configManager.calculatersiintraday:
        candleDuration = (userPassedArgs.intraday if (userPassedArgs is not None and userPassedArgs.intraday is not None) else "1m")
        configManager.toggleConfig(candleDuration=candleDuration,clearCache=False)
        # We also need to load the intraday data to be able to calculate intraday RSI
        stockDictSecondary = Utility.tools.loadStockData(
                        stockDictSecondary,
                        configManager,
                        downloadOnly=downloadOnly,
                        defaultAnswer=defaultAnswer,
                        forceLoad=(menuOption in ["X", "B", "G", "S"]),
                        stockCodes = listStockCodes,
                        isIntraday=True,
                        exchangeSuffix = "" if (indexOption == 15 or (configManager.defaultIndex == 15 and indexOption == 0)) else ".NS"
                )
        resetConfigToDefault()
    loadedStockData = True
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
    except:
        pass
    return lastTradeDate, lastTradeTime

def FinishBacktestDataCleanup(backtest_df, df_xray):
    showBacktestResults(df_xray, sortKey="Date", optionalName="Insights")
    summary_df = backtestSummary(backtest_df)
    backtest_df.loc[:, "Date"] = backtest_df.loc[:, "Date"].apply(
                lambda x: x.replace("-", "/")
            )
    showBacktestResults(backtest_df)
    showBacktestResults(summary_df, optionalName="Summary")
    sorting = False if defaultAnswer is not None else True
    sortKeys = {
                "S": "Stock",
                "D": "Date",
                "1": "1-Pd",
                "2": "2-Pd",
                "3": "3-Pd",
                "4": "4-Pd",
                "5": "5-Pd",
                "10": "10-Pd",
                "15": "15-Pd",
                "22": "22-Pd",
                "30": "30-Pd",
                "T": "Trend",
                "V": "Volume",
                "M": "MA-Signal",
            }
    if configManager.enablePortfolioCalculations:
        if 'RUNNER' not in os.environ.keys():
            task1 = PKTask("PortfolioLedger",long_running_fn=PortfolioCollection().getPortfoliosAsDataframe)
            task2 = PKTask("PortfolioLedgerSnapshots",long_running_fn=PortfolioCollection().getLedgerSummaryAsDataframe)
            tasksList = [task1,task2]
            PKScheduler.scheduleTasks(tasksList=tasksList, label=f"Portfolio Calculations Report Export(Total={len(tasksList)})",timeout=600)
        else:
            for task in tasksList:
                task.long_running_fn(*(task,))
        for task in tasksList:
            if task.result is not None:
                showBacktestResults(task.result, sortKey=None, optionalName=task.taskName)
    
    return summary_df,sorting,sortKeys

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
            + f"[+] {len(userPassedArgs.pipedmenus.split('|'))} Scanners piped so far: {colorText.END}{colorText.WARN+userPassedArgs.pipedmenus+colorText.END}\n{colorText.GREEN}[+] Do you want to add any more scanners into the pipe?"
            + colorText.END
        )
    shouldAddMoreIntoPipe = 'n'
    if userPassedArgs is None or (userPassedArgs is not None and userPassedArgs.answerdefault is None):
        shouldAddMoreIntoPipe = input(colorText.FAIL + "[+] Select [Y/N] (Default:N): " + colorText.END) or 'n'
    if shouldAddMoreIntoPipe.lower() != 'y':
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        launcher = f"python3.11 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
        monitorOption = f'"{userPassedArgs.pipedmenus}"'
        scannerOptionQuoted = monitorOption.replace("'",'"').replace(":>",":D:D:D:>").replace("::",":")
        requestingUser = f" -u {userPassedArgs.user}" if userPassedArgs.user is not None else ""
        enableLog = f" -l" if userPassedArgs.log else ""
        backtestParam = f" --backtestdaysago {userPassedArgs.backtestdaysago}" if userPassedArgs.backtestdaysago else ""
        OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener with piped scanners. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} -a Y -e -o {scannerOptionQuoted}{requestingUser}{enableLog}{backtestParam}{colorText.END}")
        sleep(2)
        os.system(f"{launcher} --systemlaunched -a Y -e -o {scannerOptionQuoted}{requestingUser}{enableLog}{backtestParam}")
        userPassedArgs.pipedmenus = None
        OutputControls().printOutput(
                colorText.GREEN
                + f"[+] Finished running all piped scanners!"
                + colorText.END
            )
        if defaultAnswer is None:
            input("Press <Enter> to exit...")
        sys.exit(0)
    else:
        userPassedArgs.options = None
        return None, None
    
def prepareGroupedXRay(backtestPeriod, backtest_df):
    df_grouped = backtest_df.groupby("Date")
    userPassedArgs.backtestdaysago = backtestPeriod
    df_xray = None
    groupCounter = 0
    tasksList=[]
    for calcForDate, df_group in df_grouped:
        groupCounter += 1
        func_args = (df_group, userPassedArgs, calcForDate,f"Portfolio X-Ray | {calcForDate} | {groupCounter} of {len(df_grouped)}")
        task = PKTask(f"Portfolio X-Ray | {calcForDate} | {groupCounter} of {len(df_grouped)}",
                      long_running_fn=PortfolioXRay.performXRay,
                      long_running_fn_args=func_args)
        task.total = len(df_grouped)
        tasksList.append(task)
    if 'RUNNER' not in os.environ.keys():
        # if configManager.enablePortfolioCalculations:
        # On Github CI, we may run out of memory because of saving results in
        # shared multiprocessing dict.
        PKScheduler.scheduleTasks(tasksList,f"Portfolio X-Ray for ({len(df_grouped)})", showProgressBars=False,timeout=600)
    else:
        # On Github CI, let's run synchronously.
        for task in tasksList:
            task.long_running_fn(*(task,))
    for task in tasksList:
        p_df = task.result
        if p_df is not None:
            if df_xray is not None:
                df_xray = pd.concat([df_xray, p_df.copy()], axis=0)
            else:
                df_xray = p_df.copy()
            # Let's drop the columns no longer required for backtest report

    removedUnusedColumns(None, backtest_df, ["Consol.", "Breakout", "RSI", "Pattern", "CCI"], userArgs=userPassedArgs)
    df_xray = df_xray.replace(np.nan, "", regex=True)
    df_xray = PortfolioXRay.xRaySummary(df_xray)
    df_xray.loc[:, "Date"] = df_xray.loc[:, "Date"].apply(
                lambda x: x.replace("-", "/")
            )
    
    return df_xray

def showSortedBacktestData(backtest_df, summary_df, sortKeys):
    OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] Would you like to sort the results?"
                    + colorText.END
                )
    OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.GREEN
                    + "[+] Press :\n [+] s, v, t, m : sort by Stocks, Volume, Trend, MA-Signal\n [+] d : sort by date\n [+] 1,2,3...30 : sort by period\n [+] n : Exit sorting\n"
                    + colorText.END
                )
    if defaultAnswer is None:
        choice = input(
                        colorText.BOLD + colorText.FAIL + "[+] Select option:"
                    )
        OutputControls().printOutput(colorText.END, end="")
        if choice.upper() in sortKeys.keys():
            Utility.tools.clearScreen()
            showBacktestResults(backtest_df, sortKeys[choice.upper()])
            showBacktestResults(summary_df, optionalName="Summary")
        else:
            sorting = False
    else:
        OutputControls().printOutput("Finished backtesting!")
        sorting = False
    return sorting

def resetConfigToDefault():
    global userPassedArgs
    isIntraday = userPassedArgs is not None and userPassedArgs.intraday is not None
    if configManager.isIntradayConfig() or isIntraday:
        configManager.toggleConfig(candleDuration="1d", clearCache=False)
    if userPassedArgs is not None and userPassedArgs.monitor is None:
        if "PKDevTools_Default_Log_Level" in os.environ.keys():
            if userPassedArgs is None or (userPassedArgs is not None and userPassedArgs.options is not None and "|" not in userPassedArgs.options):
                del os.environ['PKDevTools_Default_Log_Level']
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
            OutputControls().printOutput(colorText.BOLD + "[+] Getting Stock Codes From NASDAQ... ", end="")
            nasdaq = PKNasdaqIndexFetcher(configManager)
            listStockCodes = nasdaq.fetchNasdaqIndexConstituents()
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
                        + "[+] Stock shuffling is active."
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
            Utility.tools.clearScreen()
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
                                colorText.BOLD
                                + colorText.FAIL
                                + "[+] There was an exception while monitoring 5-EMA"
                                + "\n[+] If this continues to happen, please try and run with -l"
                                + "\n[+] and collect all the logs, zip it and submit it to the developer."
                                + "\n[+] For example:"
                                + colorText.END
                                + colorText.WARN
                                + "pkscreener -l\n"
                                + colorText.END
                            )
            OutputControls().printOutput(
                            colorText.BOLD
                            + colorText.WARN
                            + "[+] 5-EMA : Live Intraday Scanner \t"
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
    except KeyboardInterrupt:
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
        input(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Press <Enter> to Exit!"
            + colorText.END
        )
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
    global userPassedArgs, selectedChoice, menuChoiceHierarchy
    try:
        menuChoiceHierarchy = f'{level0MenuDict[selectedChoice["0"]].strip()}>{level1_X_MenuDict[selectedChoice["1"]].strip()}>{level2_X_MenuDict[selectedChoice["2"]].strip()}'
        if selectedChoice["2"] == "6":
            menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level3_X_Reversal_MenuDict[selectedChoice["3"]].strip()}'
            )
            if len(selectedChoice) >= 5 and selectedChoice["3"] in ["7","10"]:
                menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level4_X_Lorenzian_MenuDict[selectedChoice["4"]].strip()}'
            )
        elif selectedChoice["2"] in ["30"]:
            if len(selectedChoice) >= 3:
                menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level4_X_Lorenzian_MenuDict[selectedChoice["3"]].strip()}'
            )
        elif selectedChoice["2"] == "7":
            menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level3_X_ChartPattern_MenuDict[selectedChoice["3"]].strip()}'
            )
            if len(selectedChoice) >= 5 and selectedChoice["3"] == "3":
                menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level4_X_ChartPattern_Confluence_MenuDict[selectedChoice["4"]].strip()}'
            )
            elif len(selectedChoice) >= 5 and selectedChoice["3"] == "6":
                menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level4_X_ChartPattern_BBands_SQZ_MenuDict[selectedChoice["4"]].strip()}'
            )
            elif len(selectedChoice) >= 5 and selectedChoice["3"] == "9":
                menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level4_X_ChartPattern_MASignalMenuDict[selectedChoice["4"]].strip()}'
            )
        elif selectedChoice["2"] == "21":
            menuChoiceHierarchy = (
                menuChoiceHierarchy
                + f'>{level3_X_PopularStocks_MenuDict[selectedChoice["3"]].strip()}'
            )
        intraday = "(Intraday)" if ("Intraday" not in menuChoiceHierarchy and (userPassedArgs is not None and userPassedArgs.intraday) or configManager.isIntradayConfig()) else ""
        menuChoiceHierarchy = f"{menuChoiceHierarchy}{intraday}"
        global nValueForMenu
        menuChoiceHierarchy = menuChoiceHierarchy.replace("N-",f"{nValueForMenu}-")
    except:
        pass
    Utility.tools.clearScreen(forceTop=True)
    needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
    pastDate = f"[ {PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)} ]" if needsCalc else ""
    OutputControls().printOutput(
        colorText.BOLD
        + colorText.FAIL
        + "[+] You chose: "
        + menuChoiceHierarchy
        + (f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}] {pastDate}" if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None) else "")
        + colorText.END
    )
    default_logger().info(menuChoiceHierarchy)
    return menuChoiceHierarchy

def printNotifySaveScreenedResults(
    screenResults, saveResults, selectedChoice, menuChoiceHierarchy, testing, user=None
):
    global userPassedArgs, elapsed_time
    if userPassedArgs.monitor is not None:
        return
    MAX_ALLOWED = (configManager.maxdisplayresults if userPassedArgs.maxdisplayresults is None else (int(userPassedArgs.maxdisplayresults) if not testing else 1))
    tabulated_backtest_summary = ""
    tabulated_backtest_detail = ""
    recordDate = PKDateUtilities.tradingDate().strftime('%Y-%m-%d') if (userPassedArgs.backtestdaysago is None) else (PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago)))
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    Utility.tools.clearScreen(forceTop=True)
    if screenResults is not None and len(screenResults) > 0:
        screenResults = screenResults[~screenResults.index.duplicated(keep='first')]
        saveResults = saveResults[~saveResults.index.duplicated(keep='first')]
        if "Stock" in screenResults.columns:
            screenResults.drop_duplicates(keep="first", inplace=True)
        if "Stock" in saveResults.columns:
            saveResults.drop_duplicates(keep="first", inplace=True)
    
    reportTitle = f"{userPassedArgs.pipedtitle}|" if userPassedArgs is not None and userPassedArgs.pipedtitle is not None else ""
    OutputControls().printOutput(
        colorText.BOLD
        + colorText.FAIL
        + f"[+] You chose: {reportTitle}{menuChoiceHierarchy}[{len(screenResults) if screenResults is not None and not screenResults.empty else 0}]"
        + (f" (Piped Scan Mode) [{userPassedArgs.pipedmenus}]" if (userPassedArgs is not None and userPassedArgs.pipedmenus is not None) else "")
        + colorText.END
        , enableMultipleLineOutput=True
    )
    pngName = f'PKS_{PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)}_{PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")}'
    pngExtension = ".png"
    eligible = is_token_telegram_configured()
    targetDateG10k = prepareGrowthOf10kResults(saveResults, selectedChoice, menuChoiceHierarchy, testing, user, pngName, pngExtension, eligible)
    if saveResults is not None and "Date" in saveResults.columns and len(saveResults) > 0:
        recordDate = saveResults["Date"].iloc[0].replace("/","-")
    summaryReturns = removedUnusedColumns(screenResults, saveResults, ["Date","Breakout","Resistance"],userArgs=userPassedArgs)

    tabulated_results = ""
    console_results = ""
    if screenResults is not None and len(screenResults) > 0:
        tabulated_results = colorText.miniTabulator().tabulate(
            screenResults, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
            maxcolwidths=Utility.tools.getMaxColumnWidths(screenResults)
        ).encode("utf-8").decode(STD_ENCODING)
        copyScreenResults = screenResults.copy()
        hiddenColumns = configManager.alwaysHiddenDisplayColumns.split(",")
        for col in screenResults.columns:
            if col in hiddenColumns:
                copyScreenResults.drop(col, axis=1, inplace=True, errors="ignore")
        try:
            console_results = colorText.miniTabulator().tabulate(
                                    copyScreenResults, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
                                    maxcolwidths=Utility.tools.getMaxColumnWidths(copyScreenResults)
                                ).encode("utf-8").decode(STD_ENCODING)
        except:
            console_results = tabulated_results
    OutputControls().printOutput(f"{console_results}\n", enableMultipleLineOutput=True)
    _, reportNameInsights = getBacktestReportFilename(
        sortKey="Date", optionalName="Insights"
    )
    strategy_df = PortfolioXRay.bestStrategiesFromSummaryForReport(reportNameInsights,includeLargestDatasets=True)
    addendumLabel = (
        "[+] Strategies that have best results in the past for this scan option (calculated with 1 stock each with matching strategy in the result):"
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
                        caption_df = saveResultsTrimmed[['LTP','%Chng','Volume']].head(5)
                        caption_df.loc[:, "LTP"] = caption_df.loc[:, "LTP"].apply(
                            lambda x: str(int(round(float(x),0)))
                        )
                        caption_df.loc[:, "%Chng"] = caption_df.loc[:, "%Chng"].apply(
                            lambda x: f'{int(round(float(x.split(" ")[0].replace("%","")),0))}%'
                        )
                        caption_df.loc[:, "Volume"] = caption_df.loc[:, "Volume"].apply(
                            lambda x: f'{int(round(float(x.replace("x","")),0))}x' if (len(x.replace("x","").strip()) > 0 and not pd.isna(float(x.replace("x","")))) else ''
                        )
                        caption_df.rename(columns={"%Chng": "Ch%","Volume":"Vol"}, inplace=True)
                    except:
                        cols = [list(saveResultsTrimmed.columns)[0]]
                        cols.extend(list(saveResultsTrimmed.columns[5:]))
                        caption_df = saveResultsTrimmed[cols].head(2)
                    for col in caption_df.columns:
                        caption_df[col] = caption_df[col].astype(str)
                    caption_results = colorText.miniTabulator().tabulate(
                        caption_df,
                        headers="keys",
                        tablefmt=colorText.No_Pad_GridFormat,
                        maxcolwidths=[None,None,4,3]
                    ).encode("utf-8").decode(STD_ENCODING).replace("-K-----S-----C-----R","-K-----S----C---R").replace("%  ","% ").replace("=K=====S=====C=====R","=K=====S====C===R").replace("Vol  |","Vol|").replace("x  ","x")
                    caption_results = Utility.tools.removeAllColorStyles(caption_results.replace("-E-----N-----E-----R","-E-----N----E---R").replace("=E=====N=====E=====R","=E=====N====E===R"))
                    caption = f"{caption}.Open attached image for more. Samples:<pre>{caption_results}</pre>{elapsed_text}{pipedTitle}" #<i>Author is <u><b>NOT</b> a SEBI registered financial advisor</u> and MUST NOT be deemed as one.</i>"
                if not testing: # and not userPassedArgs.runintradayanalysis:
                    sendQuickScanResult(
                        f"{reportTitle}{menuChoiceHierarchy}",
                        user,
                        tabulated_results,
                        markdown_results,
                        caption,
                        pngName,
                        pngExtension,
                        addendum=tabulated_strategy,
                        addendumLabel=addendumLabel,
                    )
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
                                Utility.tools.tableToImage(
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
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.GREEN
                + f"[+] Found {len(screenResults) if screenResults is not None else 0} Stocks in {str('{:.2f}'.format(elapsed_time))} sec for {pastDate}. Showing only stocks that met the filter criteria in the filters section of user configuration{(' with portfolio returns:' + summaryReturns) if (len(summaryReturns) > 0) else ''}"
                + colorText.END
            )
    elif user is not None:
        sendMessageToTelegramChannel(
            message=f"No scan results found for {menuChoiceHierarchy}", user=user
        )
    if not testing:
        Utility.tools.setLastScreenedResults(screenResults, saveResults, f"{PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)}_{recordDate if recordDate is not None else ''}")

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
                g10kUnStyledTable = Utility.tools.removeAllColorStyles(g10kStyledTable)
                if not testing and eligible:
                    sendQuickScanResult(
                        menuChoiceHierarchy,
                        user,
                        g10kStyledTable,
                        g10kUnStyledTable,
                        titleLabelG10k,
                        pngName,
                        pngExtension,
                    )
        elif user is not None and eligible:
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
            saveResults.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
            saveResults.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
            # saveResults.drop(f"MCapWt%", axis=1, inplace=True, errors="ignore")
            # screenResults.drop(f"MCapWt%", axis=1, inplace=True, errors="ignore")
            if len(dropAdditionalColumns) > 0:
                for col in dropAdditionalColumns:
                    if col in saveResults.columns:
                        saveResults.drop(col, axis=1, inplace=True, errors="ignore")
        if screenResults is not None:
            screenResults.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
            screenResults.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
            if len(dropAdditionalColumns) > 0:
                for col in dropAdditionalColumns:
                    if col in screenResults.columns:
                        screenResults.drop(col, axis=1, inplace=True, errors="ignore")
    return summaryReturns


def tabulateBacktestResults(saveResults, maxAllowed=0, force=False):
    if "PKDevTools_Default_Log_Level" not in os.environ.keys():
        if ("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and not force):
            return None, None
    if not configManager.showPastStrategyData:
        return None, None
    tabulated_backtest_summary = ""
    tabulated_backtest_detail = ""
    summarydf, detaildf = getSummaryCorrectnessOfStrategy(saveResults)
    if summarydf is not None and len(summarydf) > 0:
        tabulated_backtest_summary = colorText.miniTabulator().tabulate(
            summarydf,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            showindex=False,
            maxcolwidths=Utility.tools.getMaxColumnWidths(summarydf)
        ).encode("utf-8").decode(STD_ENCODING)
    if detaildf is not None and len(detaildf) > 0:
        if maxAllowed != 0 and len(detaildf) > 2 * maxAllowed:
            detaildf = detaildf.head(2 * maxAllowed)
        tabulated_backtest_detail = colorText.miniTabulator().tabulate(
            detaildf,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            showindex=False,
            maxcolwidths=Utility.tools.getMaxColumnWidths(detaildf)
        ).encode("utf-8").decode(STD_ENCODING)
    if tabulated_backtest_summary != "":
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] For chosen scan, summary of correctness from past: [Example, 70% of (100) under 1-Pd, means out of 100 stocks that were in the scan result in the past, 70% of them gained next day.)"
            + colorText.END
        )
        OutputControls().printOutput(tabulated_backtest_summary)
    if tabulated_backtest_detail != "":
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] 1 to 30 period gain/loss % on respective date for matching stocks from earlier predictions:[Example, 5% under 1-Pd, means the stock price actually gained 5% the next day from given date.]"
            + colorText.END
        )
        OutputControls().printOutput(tabulated_backtest_detail)
    return tabulated_backtest_summary, tabulated_backtest_detail


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
    legendPrefixText = ""
):
    if "PKDevTools_Default_Log_Level" not in os.environ.keys():
        if (("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
            return
    try:
        Utility.tools.tableToImage(
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
        tableText = "<!DOCTYPE html><html><head><script type='application/javascript' src='https://pkjmesra.github.io/PKScreener/pkscreener/classes/tableSorting.js' ></script><style type='text/css'>body, table {background-color: black; color: white;} table, th, td {border: 1px solid white;} th {cursor: pointer; color:white; text-decoration:underline;} .r {color:red;font-weight:bold;} .br {border-color:green;border-width:medium;} .w {color:white;font-weight:bold;} .g {color:lightgreen;font-weight:bold;} .y {color:yellow;} .bg {background-color:darkslategrey;} .bb {background-color:black;} input#searchReports { width: 220px; } table thead tr th { background-color: black; position: sticky; z-index: 100; top: 0; } </style></head><body><span style='color:white;' >"
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
    global selectedChoice, userPassedArgs, elapsed_time, start_time,userPassedArgs
    result = None
    backtest_df = None
    reviewDate = getReviewDate(userPassedArgs)
    max_allowed = getMaxAllowedResultsCount(iterations, testing)
    try:
        originalNumberOfStocks = numStocks
        iterations, numStocksPerIteration = getIterationsAndStockCounts(numStocks, iterations)
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.GREEN
            + f"[+] For {reviewDate}, total Stocks under review: {numStocks} over {iterations} iterations..."
            + colorText.END
        )
        if not userPassedArgs.download:
            OutputControls().printOutput(colorText.WARN
                + f"[+] Starting {'Stock' if menuOption not in ['C'] else 'Intraday'} {'Screening' if menuOption=='X' else ('Analysis' if menuOption == 'C' else 'Backtesting.')}. Press Ctrl+C to stop!"
                + colorText.END
            )
        else:
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.FAIL
                + f"[+] Download ONLY mode (OHLCV for period:{configManager.period}, candle-duration:{configManager.duration} )! Stocks will not be screened!"
                + colorText.END
            )
        bar, spinner = Utility.tools.getProgressbarStyle()
        with alive_bar(numStocks, bar=bar, spinner=spinner) as progressbar:
            lstscreen = []
            lstsave = []
            result = None
            backtest_df = None
            start_time = time.time()
            def processResultsCallback(resultItem, processedCount,result_df, *otherArgs):
                global userPassedArgs
                (menuOption, backtestPeriod, result, lstscreen, lstsave) = otherArgs
                numStocks = processedCount
                result = resultItem
                backtest_df = processResults(menuOption, backtestPeriod, result, lstscreen, lstsave, result_df)
                progressbar()
                progressbar.text(
                    colorText.BOLD
                    + colorText.GREEN
                    + f"{'Remaining' if userPassedArgs.download else ('Found' if menuOption in ['X'] else 'Analysed')} {len(lstscreen) if not userPassedArgs.download else processedCount} {'Stocks' if menuOption in ['X'] else 'Records'}"
                    + colorText.END
                )
                if result is not None:
                    if not userPassedArgs.monitor and len(lstscreen) > 0 and userPassedArgs is not None and userPassedArgs.options.split(":")[2] in ["29"]:
                        scr_df = pd.DataFrame(lstscreen)
                        existingColumns = ["Stock","%Chng","LTP","Volume"]
                        newColumns = ["BidQty","AskQty","LwrCP","UprCP","VWAP","DayVola","Del(%)"]
                        existingColumns.extend(newColumns)
                        scr_df = scr_df[existingColumns]
                        scr_df.sort_values(by=["Volume","BidQty"], ascending=False, inplace=True)
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
                        sys.stdout.write(f"\x1b[{tableLength}A")  # cursor up one line
                if keyboardInterruptEventFired:
                    return False, backtest_df
                return not ((testing and len(lstscreen) >= 1) or len(lstscreen) >= max_allowed), backtest_df
            otherArgs = (menuOption, backtestPeriod, result, lstscreen, lstsave)
            backtest_df, result =PKScanRunner.runScan(userPassedArgs,testing,numStocks,iterations,items,numStocksPerIteration,tasks_queue,results_queue,originalNumberOfStocks,backtest_df,*otherArgs,resultsReceivedCb=processResultsCallback)

        OutputControls().printOutput(f"\x1b[{3 if OutputControls().enableMultipleLineOutput else 1}A")
        if len(lstscreen) == 0 and userPassedArgs is not None and userPassedArgs.monitor is None:
            OutputControls().printOutput("\x1b[2K") # Delete the progress bar line
        elapsed_time = time.time() - start_time
        if menuOption in ["X", "G", "C"]:
            # create extension
            screenResults = pd.DataFrame(lstscreen)
            saveResults = pd.DataFrame(lstsave)

    except KeyboardInterrupt:
        try:
            global keyboardInterruptEventFired
            keyboardInterruptEvent.set()
            keyboardInterruptEventFired = True
            OutputControls().printOutput(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Terminating Script, Please wait..."
                + colorText.END
            )
            PKScanRunner.terminateAllWorkers(userPassedArgs=userPassedArgs,consumers=consumers, tasks_queue=tasks_queue,testing=testing)
            logging.shutdown()
        except KeyboardInterrupt:
            pass
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.FAIL
            + f"\nException:\n{e}\n[+] Terminating Script, Please wait..."
            + colorText.END
        )
        PKScanRunner.terminateAllWorkers(userPassedArgs=userPassedArgs,consumers=consumers, tasks_queue=tasks_queue,testing=testing)
        logging.shutdown()

    if result is not None and len(result) >=3 and "Date" not in saveResults.columns:
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
    reviewDate = PKDateUtilities.tradingDate().strftime('%Y-%m-%d')
    if userPassedArgs is not None and userPassedArgs.backtestdaysago is not None:
        reviewDate = PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago))
    return reviewDate

def getMaxAllowedResultsCount(iterations, testing):
    return iterations * (configManager.maxdisplayresults if userPassedArgs.maxdisplayresults is None else int(userPassedArgs.maxdisplayresults)) if not testing else 1

def getIterationsAndStockCounts(numStocks, iterations):
    if numStocks <= 2500:
        return 1,numStocks
    originalIterations = iterations
        # If we put in more into the queue, it might cause the warnings from multiprocessing resource_tracker
        # about semaphore leakages etc. This is, caused due to overallocating RAM.
    idealNumStocksMaxPerIteration = 100
    iterations = int(numStocks*iterations/idealNumStocksMaxPerIteration) + 1
    numStocksPerIteration = int(numStocks/int(iterations))
    if numStocksPerIteration < 10:
        numStocksPerIteration = numStocks if (iterations == 1 or numStocks<= iterations) else int(numStocks/int(iterations))
        iterations = originalIterations
    if numStocksPerIteration > 500:
        numStocksPerIteration = 500
        iterations = int(numStocks/numStocksPerIteration) + 1
    return iterations,numStocksPerIteration


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
    global userPassedArgs, keyboardInterruptEventFired, download_trials
    argsIntraday = userPassedArgs is not None and userPassedArgs.intraday is not None
    intradayConfig = configManager.isIntradayConfig()
    intraday = intradayConfig or argsIntraday
    if not keyboardInterruptEventFired and (downloadOnly or (
        configManager.cacheEnabled and not PKDateUtilities.isTradingTime() and not testing
    )):
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.GREEN
            + "[+] Caching Stock Data for future use, Please Wait... "
            + colorText.END,
            end="",
        )
        Utility.tools.saveStockData(stockDictPrimary, configManager, loadCount, intraday)
        if downloadOnly:
            cache_file = Utility.tools.saveStockData(stockDictPrimary, configManager, loadCount, intraday, downloadOnly=downloadOnly)
            cacheFileSize = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
            if cacheFileSize < 1024*1024*40:
                try:
                    from PKDevTools.classes import Archiver
                    log_file_path = os.path.join(Archiver.get_user_outputs_dir(), "pkscreener-logs.txt")
                    message=f"{cache_file} has size: {cacheFileSize}! Something is wrong!"
                    if os.path.exists(log_file_path):
                        sendMessageToTelegramChannel(caption=message,document_filePath=log_file_path, user="-1001785195297")
                    else:
                        sendMessageToTelegramChannel(message=message,user="-1001785195297")
                except:
                    pass
                # Let's try again with logging
                if download_trials < 1:
                    download_trials += 1
                    launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
                    launcher = f"python3.11 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
                    os.system(f"{launcher} -a Y -e -l -d {'-i 1m' if configManager.isIntradayConfig() else ''}")
    else:
        OutputControls().printOutput(colorText.BOLD + colorText.GREEN + "[+] Skipped Saving!" + colorText.END)


def saveNotifyResultsFile(
    screenResults, saveResults, defaultAnswer, menuChoiceHierarchy, user=None
):
    global userPassedArgs, elapsed_time, selectedChoice
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    caption = f'<b>{menuChoiceHierarchy.split(">")[-1]}</b>'
    if screenResults is not None and len(screenResults) >= 1:
        choices = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0) if needsCalc else None
        filename = Utility.tools.promptSaveResults(choices,
            saveResults, defaultAnswer=defaultAnswer,pastDate=pastDate)
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.WARN
            + f"[+] Notes:\n[+] 1.Trend calculation is based on 'daysToLookBack'. See configuration.\n[+] 2.Reduce the console font size to fit all columns on screen.\n[+] Standard data columns were hidden: {configManager.alwaysHiddenDisplayColumns}. If you want, you can change this in pkscreener.ini"
            + colorText.END
        )
    if userPassedArgs.monitor is None:
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago) if needsCalc else 0)
        OutputControls().printOutput(
            colorText.BOLD
            + colorText.GREEN
            + f"[+] Screening Completed. Found {len(screenResults) if screenResults is not None else 0} results in {round(elapsed_time,2)} sec. for {pastDate}. Queue Wait Time:{int(PKDateUtilities.currentDateTimestamp()-userPassedArgs.triggertimestamp-round(elapsed_time,2))}s! Press Enter to Continue.."
            + colorText.END
            , enableMultipleLineOutput=True
        )
        if defaultAnswer is None:
            input("Press <Enter> to continue...")

def sendGlobalMarketBarometer(userArgs=None):
    from pkscreener.classes import Barometer
    caption = "Global Market Barometer with India market Performance (top) and Valuation (bottom)"
    gmbPath = Barometer.getGlobalMarketBarometerValuation()
    try:
        if gmbPath is not None:
            sendMessageToTelegramChannel(
                message=None,
                photo_filePath=gmbPath,
                caption=caption,
                user=(userArgs.user if userArgs is not None else None),
            )
            os.remove(gmbPath)
    except:
        pass

def sendMessageToTelegramChannel(
    message=None, photo_filePath=None, document_filePath=None, caption=None, user=None
):
    global userPassedArgs, test_messages_queue
    if test_messages_queue is not None:
        test_messages_queue.append(f"message:{message}\ncaption:{caption}\nuser:{user}\ndocument:{document_filePath}")
        if len(test_messages_queue) >10:
            test_messages_queue.pop(0)
    if user is None and userPassedArgs is not None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    if user is not None and caption is not None:
        caption = f"{caption.replace('&','n')}."
    if message is not None:
        try:
            message = message.replace("&", "n").replace("<","*")
            send_message(message, userID=user)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
    else:
        message = ""
    if photo_filePath is not None:
        try:
            if caption is not None:
                caption = f"{caption.replace('&','n')}"
            send_photo(photo_filePath, (caption if len(caption) <=1024 else ""), userID=user)
            # Breather for the telegram API to be able to send the heavy photo
            sleep(2)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
    if document_filePath is not None:
        try:
            if caption is not None:
                caption = f"{caption.replace('&','n')}"
            send_document(document_filePath, (caption if len(caption) <=1024 else ""), userID=user)
            # Breather for the telegram API to be able to send the document
            sleep(2)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
    if user is not None:
        channel_userID="-1001785195297"
        if user != channel_userID:
            # Send an update to dev channel
            send_message(
                "Responded back to userId:{0} with {1}.{2}".format(user, caption, message),
                userID="-1001785195297",
            )


def sendTestStatus(screenResults, label, user=None):
    msg = "<b>SUCCESS</b>" if (screenResults is not None and len(screenResults) >= 1) else "<b>FAIL</b>"
    sendMessageToTelegramChannel(
        message=f"{msg}: Found {len(screenResults) if screenResults is not None else 0} Stocks for {label}", user=user
    )


def showBacktestResults(backtest_df, sortKey="Stock", optionalName="backtest_result"):
    global menuChoiceHierarchy, selectedChoice, userPassedArgs, elapsed_time
    pd.set_option("display.max_rows", 800)
    # pd.set_option("display.max_columns", 20)
    if backtest_df is None or backtest_df.empty or len(backtest_df) < 1:
        return
    backtest_df.drop_duplicates(inplace=True)
    summaryText = f"Auto-generated in {round(elapsed_time,2)} sec. as of {PKDateUtilities.currentDateTime().strftime('%d-%m-%y %H:%M:%S IST')}\n{menuChoiceHierarchy.replace('Backtests','Growth of 10K' if optionalName=='Insights' else 'Backtests')}"
    lastSummaryRow = None
    if "Summary" not in optionalName:
        if sortKey is not None and len(sortKey) > 0:
            backtest_df.sort_values(by=[sortKey], ascending=False, inplace=True)
    else:
        lastRow = backtest_df.iloc[-1, :]
        if lastRow.iloc[0] == "SUMMARY":
            lastSummaryRow = pd.DataFrame(lastRow).transpose()
            lastSummaryRow.set_index("Stock", inplace=True)
            lastSummaryRow = lastSummaryRow.iloc[:, lastSummaryRow.columns != "Stock"]
        if "Insights" in optionalName:
            summaryText = f"{summaryText}\nActual returns at a portfolio level with 1-stock each based on selected scan-parameters:"
        else:
            summaryText = f"{summaryText}\nOverall Summary of (correctness of) Strategy Prediction Positive outcomes:"
    tabulated_text = ""
    if backtest_df is not None and len(backtest_df) > 0:
        tabulated_text = colorText.miniTabulator().tabulate(
            backtest_df,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            showindex=False,
            maxcolwidths=Utility.tools.getMaxColumnWidths(backtest_df)
        ).encode("utf-8").decode(STD_ENCODING)
    OutputControls().printOutput(colorText.FAIL + summaryText + colorText.END + "\n")
    OutputControls().printOutput(tabulated_text + "\n")
    choices, filename = getBacktestReportFilename(sortKey, optionalName)
    headerDict = {0: "<th></th>"}
    index = 1
    for col in backtest_df.columns:
        if col != "Stock":
            headerDict[index] = f"<th>{col}</th>"
            index += 1

    colored_text = backtest_df.to_html(index=False)
    summaryText = summaryText.replace("\n", "<br />")
    if "Summary" in optionalName:
       summaryText = f"{summaryText}<br /><input type='checkbox' id='chkActualNumbers' name='chkActualNumbers' value='0'><label for='chkActualNumbers'>Sort by actual numbers (Stocks + Date combinations of results. Higher the count, better the prediction reliability)</label><br>"
    colored_text = reformatTable(summaryText, headerDict, colored_text, sorting=True)
    # Delete any pre-existing backtesting report for the same parameters
    filename = os.path.join(scanOutputDirectory(True), filename)
    try:
        os.remove(filename)
    except Exception:# pragma: no cover
        pass
    finally:
        colored_text = colored_text.encode('utf-8').decode(STD_ENCODING)
        with open(filename, "w") as f:
            f.write(colored_text)
        Committer.execOSCommand(f"git add {filename} -f >/dev/null 2>&1")

    if lastSummaryRow is not None:
        oneline_text = lastSummaryRow.to_html(header=False, index=False)
        oneline_text = reformatTable(
            summaryText, headerDict, oneline_text, sorting=False
        )
        onelineSummaryFile = f"PKScreener_{choices}_OneLine_{optionalName}.html"
        onelineSummaryFile = os.path.join(
            scanOutputDirectory(True), onelineSummaryFile
        )
        try:
            os.remove(onelineSummaryFile)
        except Exception:# pragma: no cover
            pass
        finally:
            oneline_text = f"{oneline_text}<td class='w'>{PKDateUtilities.currentDateTime().strftime('%Y/%m/%d')}</td><td class='w'>{round(elapsed_time,2)}</td>"
            with open(onelineSummaryFile, "w") as f:
                f.write(oneline_text)
            Committer.execOSCommand(f"git add {onelineSummaryFile} -f >/dev/null 2>&1")

def scanOutputDirectory(backtest=False):
    dirName = 'actions-data-scan' if not backtest else "Backtest-Reports"
    outputFolder = os.path.join(os.getcwd(),dirName)
    if not os.path.isdir(outputFolder):
        OutputControls().printOutput("Creating actions-data-scan directory now...")
        os.makedirs(os.path.dirname(os.path.join(os.getcwd(),f"{dirName}{os.sep}")), exist_ok=True)
    return outputFolder

def getBacktestReportFilename(sortKey="Stock", optionalName="backtest_result"):
    global userPassedArgs,selectedChoice
    choices = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
    filename = f"PKScreener_{choices}_{optionalName}_{sortKey if sortKey is not None else 'Default'}Sorted.html"
    return choices, filename

def showOptionErrorMessage():
    OutputControls().printOutput(
        colorText.BOLD
        + colorText.FAIL
        + "\n[+] Please enter a valid option & try Again!"
        + colorText.END
    )
    sleep(2)
    Utility.tools.clearScreen()

def takeBacktestInputs(
    menuOption=None, indexOption=None, executeOption=None, backtestPeriod=0
):
    g10k = '"Growth of 10k"'
    OutputControls().printOutput(
        colorText.BOLD
        + colorText.GREEN
        + f"[+] For {g10k if menuOption == 'G' else 'backtesting'}, you can choose from (1,2,3,4,5,10,15,22,30) or any other custom periods (< 1y)."
    )
    try:
        if backtestPeriod == 0:
            backtestPeriod = int(
                input(
                    colorText.BOLD
                    + colorText.FAIL
                    + f"[+] Enter {g10k if menuOption == 'G' else 'backtesting'} period (Default is {15 if menuOption == 'G' else 30} [days]): "
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
        colorText.BOLD
        + colorText.GREEN
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
