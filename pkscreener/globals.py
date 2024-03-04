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
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured,
    send_document,
    send_message,
)
from PKNSETools.morningstartools.PKMorningstarDataFetcher import morningstarDataFetcher
from tabulate import tabulate

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.ScreeningStatistics as ScreeningStatistics
import pkscreener.classes.Utility as Utility
from pkscreener.classes.Utility import STD_ENCODING
from pkscreener.classes import VERSION, PortfolioXRay
from pkscreener.classes.Backtest import backtest, backtestSummary

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
    menus,
)
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes.Portfolio import PortfolioCollection
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes.PKScheduler import PKScheduler
from pkscreener.classes.PKScanRunner import PKScanRunner
from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser

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
menuChoiceHierarchy = ""
newlyListedOnly = False
screenCounter = None
screener = ScreeningStatistics.ScreeningStatistics(configManager, default_logger())
screenResults = None
backtest_df = None
screenResultsCounter = None
selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
stockDict = None
userPassedArgs = None
elapsed_time = 0
start_time = 0
test_messages_queue = []
strategyFilter=[]

def finishScreening(
    downloadOnly,
    testing,
    stockDict,
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
    saveDownloadedData(downloadOnly, testing, stockDict, configManager, loadCount)
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
            print(
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

        if summaryRequired and len(dfs) > 0:
            df = dfs[0]
            summarydf = df[df["Stock"] == "SUMMARY"]
            for col in summarydf.columns:
                summarydf.loc[:, col] = summarydf.loc[:, col].apply(
                    lambda x: Utility.tools.getFormattedBacktestSummary(
                        x, columnName=col
                    )
                )
            summarydf = summarydf.replace(np.nan, "", regex=True)
        if len(dfd) > 0:
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
                    + "\n[+] The Volume should be lowest since last how many candles? "
                )
            )
    except ValueError as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        print(colorText.END)
        print(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Error: Non-numeric value entered! Please try again!"
            + colorText.END
        )
        input("Press <Enter> to continue...")
        return
    print(colorText.END)
    return daysForLowestVolume


def handleSecondaryMenuChoices(
    menuOption, testing=False, defaultAnswer=None, user=None
):
    if menuOption == "H":
        showSendHelpInfo(defaultAnswer, user)
    elif menuOption == "U":
        OTAUpdater.checkForUpdate(VERSION, skipDownload=testing)
        if defaultAnswer is None:
            input("Press <Enter> to continue...")
    elif menuOption == "T":
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
    global selectedChoice
    Utility.tools.clearScreen()

    m0.renderForMenu(selectedMenu=None)
    try:
        if menuOption is None:
            menuOption = input(colorText.BOLD + colorText.FAIL + "[+] Select option: ")
            print(colorText.END, end="")
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
            elif selectedMenu.menuKey in ["B", "C", "G", "H", "U", "T", "S", "E", "X", "Y"]:
                Utility.tools.clearScreen()
                selectedChoice["0"] = selectedMenu.menuKey
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
    global newlyListedOnly, selectedChoice
    Utility.tools.clearScreen()
    if menuOption is None:
        print('You must choose an option from the previous menu! Defaulting to "X"...')
        menuOption = "X"
    print(
        colorText.BOLD
        + colorText.FAIL
        + "[+] You chose: "
        + level0MenuDict[menuOption].strip()
        + colorText.END
    )
    if indexOption is None:
        selectedMenu = m0.find(menuOption)
        m1.renderForMenu(selectedMenu=selectedMenu, skip=skip)
    try:
        if indexOption is None:
            indexOption = input(
                colorText.BOLD + colorText.FAIL + "[+] Select option: "
            )
            print(colorText.END, end="")
        if indexOption == "" or indexOption is None:
            indexOption = 12
        # elif indexOption == 'W' or indexOption == 'w' or indexOption == 'N' or indexOption == 'n' or indexOption == 'E' or indexOption == 'e':
        elif not str(indexOption).isnumeric():
            indexOption = indexOption.upper()
            if indexOption in ["M", "E", "N", "Z"]:
                return indexOption, 0
        else:
            indexOption = int(indexOption)
            if indexOption < 0 or indexOption > 14:
                raise ValueError
            elif indexOption == 13:
                newlyListedOnly = True
                indexOption = 12
        selectedChoice["1"] = str(indexOption)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
        print(
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
    global selectedChoice
    if executeOption is None:
        if indexOption is not None and indexOption != "W":
            Utility.tools.clearScreen()
            print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] You chose: "
                + level0MenuDict[selectedChoice["0"]].strip()
                + " > "
                + level1_X_MenuDict[selectedChoice["1"]].strip()
                + colorText.END
            )
            selectedMenu = m1.find(indexOption)
            m2.renderForMenu(selectedMenu=selectedMenu, skip=skip)
    try:
        if indexOption is not None and indexOption != "W":
            if executeOption is None:
                executeOption = input(
                    colorText.BOLD + colorText.FAIL + "[+] Select option: "
                )
                print(colorText.END, end="")
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
        print(
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
    try:
        sortKey = ["Volume"]
        ascending = [False]
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
            sortKey = ["bbands_ulr_ratio_max5"]
            ascending = [False]
        screenResults.sort_values(by=sortKey, ascending=ascending, inplace=True)
        saveResults.sort_values(by=sortKey, ascending=ascending, inplace=True)
        columnsToBeDeleted = ["MFI","FVDiff","ConfDMADifference","bbands_ulr_ratio_max5"]
        for column in columnsToBeDeleted:
            if column in saveResults.columns:
                saveResults.drop(column, axis=1, inplace=True, errors="ignore")
                screenResults.drop(column, axis=1, inplace=True, errors="ignore")
        screenResults.set_index("Stock", inplace=True)
        saveResults.set_index("Stock", inplace=True)
        screenResults['Volume'] = screenResults['Volume'].astype(str)
        saveResults['Volume'] = saveResults['Volume'].astype(str)
        screenResults.loc[:, "Volume"] = screenResults.loc[:, "Volume"].apply(
            lambda x: Utility.tools.formatRatio(float(x), volumeRatio)
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


# @tracelog
def main(userArgs=None):
    global screenResults, selectedChoice, defaultAnswer, menuChoiceHierarchy, screenCounter, screenResultsCounter, stockDict, userPassedArgs, loadedStockData, keyboardInterruptEvent, loadCount, maLength, newlyListedOnly, keyboardInterruptEventFired,strategyFilter, elapsed_time, start_time
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
    screenCounter = multiprocessing.Value("i", 1)
    screenResultsCounter = multiprocessing.Value("i", 0)
    keyboardInterruptEvent = multiprocessing.Manager().Event()
    keyboardInterruptEventFired = False
    if stockDict is None:
        stockDict = multiprocessing.Manager().dict()
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
    screenResults, saveResults = PKScanRunner.initDataframes()
    options, menuOption, indexOption, executeOption = getTopLevelMenuChoices(
        startupoptions, testBuild, downloadOnly, defaultAnswer=defaultAnswer
    )
    # Print Level 1 menu options
    selectedMenu = initExecution(menuOption=menuOption)
    menuOption = selectedMenu.menuKey
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
            return
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
                print(colorText.END, end="")
                if userOption == "":
                    userOption = "37" # NoFilter
            except EOFError:  # pragma: no cover
                userOption = "37"  # NoFilter
                pass
            except Exception as e:# pragma: no cover
                default_logger().debug(e, exc_info=True)
                pass
        userOption = userOption.upper()
        if userOption == "M":
                # Go back to the caller. It will show the console menu again.
                return
        elif userOption == "Z":
            handleExitRequest(userOption)
            return
        
        if userOption == "S":
            print(
                colorText.GREEN
                + "[+] Collecting all metrics for summarising..."
                + colorText.END
            )
            df_all = PortfolioXRay.summariseAllStrategies()
            if df_all is not None and len(df_all) > 0:
                print(
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
                print("[!] Nothing to show here yet. Check back later.")
            if defaultAnswer is None:
                input("Press <Enter> to continue...")
            return
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
        print("Not implemented yet! Try selecting a different option.")
        sleep(3)
        return

    handleMenu_XBG(menuOption, indexOption, executeOption)
    if indexOption == "M" or executeOption == "M":
        # Go back to the caller. It will show the console menu again.
        return
    listStockCodes = handleRequestForSpecificStocks(options, indexOption)
    handleExitRequest(executeOption)
    if executeOption is None:
        executeOption = 0
    executeOption = int(executeOption)
    volumeRatio = configManager.volumeRatio
    if executeOption == 3:
        userPassedArgs.maxdisplayresults = 2000 # force evaluate all stocks before getting the top results
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
                minRSI = 30
                maxRSI = 70
        else:
            minRSI, maxRSI = Utility.tools.promptRSIValues()
        if not minRSI and not maxRSI:
            print(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Error: Invalid values for RSI! Values should be in range of 0 to 100. Please try again!"
                + colorText.END
            )
            input("PRess <Enter> to continue...")
            return
    if executeOption == 6:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            reversalOption = int(options[3])
            if reversalOption in [4, 6, 7]:
                if len(options) >= 5:
                    if str(options[4]).isnumeric():
                        maLength = int(options[4])
                    elif str(options[4]).upper() == "D":
                        maLength = 50 if reversalOption == 4 else (3 if reversalOption == 7 else 7)
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
            return
        else:
            selectedChoice["3"] = str(reversalOption)
            if str(reversalOption) == "7":
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
            elif respChartPattern in [0, 4, 5, 6]:
                insideBarToLookback = 0
                if respChartPattern == 6:
                    if len(options) >= 5:
                        if str(options[4]).isnumeric():
                            maLength = int(options[4])
                        elif str(options[4]).upper() == "D":
                            maLength = 1 # Bollinger Bands Squeeze-Buy
                    elif defaultAnswer == "Y" and user is not None:
                        # bot mode
                        maLength = 4 # Bollinger Bands Squeeze- Any/All
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
            if maLength == 0:
                maLength = Utility.tools.promptChartPatternSubMenu(selectedMenu, respChartPattern)
        if (
            respChartPattern is None
            or insideBarToLookback is None
            or respChartPattern == 0
            or maLength == 0
        ):
            return
        else:
            selectedChoice["3"] = str(respChartPattern)
            selectedChoice["4"] = str(maLength)
    if executeOption == 8:
        if len(options) >= 5:
            if str(options[3]).isnumeric():
                minRSI = int(options[3])
                maxRSI = int(options[4])
            elif str(options[3]).upper() == "D":
                minRSI = -100
                maxRSI = 150
        else:
            minRSI, maxRSI = Utility.tools.promptCCIValues()
        if not minRSI and not maxRSI:
            print(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Error: Invalid values for CCI! Values should be in range of -300 to 500. Please try again!"
                + colorText.END
            )
            input("Press <Enter> to continue...")
            return
    if executeOption == 9:
        if len(options) >= 4:
            if str(options[3]).isnumeric():
                volumeRatio = float(options[3])
            elif str(options[3]).upper() == "D":
                volumeRatio = configManager.volumeRatio
        else:
            volumeRatio = Utility.tools.promptVolumeMultiplier()
        if volumeRatio <= 0:
            print(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Error: Invalid values for Volume Ratio! Value should be a positive number. Please try again!"
                + colorText.END
            )
            input("Press <Enter> to continue...")
            return
        else:
            configManager.volumeRatio = float(volumeRatio)
    if executeOption == 12:
        configManager.toggleConfig(candleDuration="15m")
    if executeOption == 21:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            popOption = int(options[3])
            if popOption >= 0 and popOption <= 9:
                pass
        else:
            popOption = Utility.tools.promptSubMenuOptions(selectedMenu)
        if popOption is None or popOption == 0:
            return
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
                return
            else:
                listStockCodes = ",".join(list(screenResults.index))
        else:
            userPassedArgs.maxdisplayresults = 2000 # force evaluate all stocks before getting the top results
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
            return
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
            return
        else:
            listStockCodes = ",".join(list(screenResults.index))
    if executeOption == 42:
        Utility.tools.getLastScreenedResults(defaultAnswer)
        return
    if executeOption >= 26 and executeOption <= 41:
        print(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] Error: Option 25 to 41 Not implemented yet! Press <Enter> to continue."
            + colorText.END
        )
        input("Press <Enter> to continue...")
        return
    if (
        not str(indexOption).isnumeric() and indexOption in ["W", "E", "M", "N", "Z"]
    ) or (
        str(indexOption).isnumeric()
        and (int(indexOption) >= 0 and int(indexOption) < 15)
    ):
        configManager.getConfig(ConfigManager.parser)
        try:
            if indexOption == "W":
                listStockCodes = fetcher.fetchWatchlist()
                if listStockCodes is None:
                    input(
                        colorText.BOLD
                        + colorText.FAIL
                        + f"[+] Create the watchlist.xlsx file in {os.getcwd()} and Restart the Program!"
                        + colorText.END
                    )
                    sys.exit(0)
            elif indexOption == "N":
                os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
                prediction, pText, sText = screener.getNiftyPrediction(
                    df=fetcher.fetchLatestNiftyDaily(proxyServer=fetcher.proxyServer)
                )
                warningText = "\nNifty AI prediction works best if you request after market is closed. It may not be accurate while market is still open!" if "Open" in Utility.marketStatus() else ""
                sendMessageToTelegramChannel(
                    message=f"{Utility.tools.removeAllColorStyles(Utility.marketStatus())}\nNifty AI prediction for the Next Day: {pText}. {sText}.{warningText}",
                    user=user,
                )
                if defaultAnswer is None:
                    input("\nPress <Enter> to Continue...\n")
                return
            elif indexOption == "M":
                return
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
                    stockDict,endOfdayCandles = PKMarketOpenCloseAnalyser.getStockDataForSimulation()
                    if stockDict is None or endOfdayCandles is None:
                        print(f"Cannot proceed! Stock data is unavailable. Please check the error logs/messages !")
                        return
                    listStockCodes = sorted(list(filter(None,list(set(stockDict.keys())))))
                listStockCodes = prepareStocksForScreening(testing, downloadOnly, listStockCodes, indexOption)
        except urllib.error.URLError as e:
            default_logger().debug(e, exc_info=True)
            print(
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

        if (menuOption in ["X", "B", "G", "S"] and not loadedStockData) or (
            # not downloadOnly
            # and not PKDateUtilities.isTradingTime()
            # and 
            configManager.cacheEnabled
            and not loadedStockData
            and not testing
        ):
            if menuOption not in ["C"]:
                Utility.tools.loadStockData(
                    stockDict,
                    configManager,
                    downloadOnly=downloadOnly,
                    defaultAnswer=defaultAnswer,
                    forceLoad=(menuOption in ["X", "B", "G", "S"]),
                    stockCodes = listStockCodes
            )
            loadedStockData = True
        loadCount = len(stockDict)

        if downloadOnly:
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Starting download.. Press Ctrl+C to stop!"
            )
        if menuOption.upper() in ["B", "G"]:
            print(
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
        print(f"{colorText.GREEN}[+] Adding stocks to the queue...{colorText.END}")
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
                    print(
                        colorText.BOLD
                        + colorText.FAIL
                        + "\n[+] Terminating Script, Please wait..."
                        + colorText.END
                    )
                except Exception:
                    pass
                PKScanRunner.addStocksToItemList(userPassedArgs, testing, testBuild, newlyListedOnly, downloadOnly, minRSI, maxRSI, insideBarToLookback, respChartPattern, daysForLowestVolume, backtestPeriod, reversalOption, maLength, listStockCodes, menuOption, executeOption, volumeRatio, items, daysInPast)
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
        sys.stdout.write(f"\x1b[1A")
        if not keyboardInterruptEventFired:
            screenResults, saveResults, backtest_df, scr = PKScanRunner.PrepareAndRunScan(keyboardInterruptEvent,screenCounter,screenResultsCounter,stockDict,testing, backtestPeriod, menuOption, samplingDuration, items,screenResults, saveResults, backtest_df,scanningCb=runScanners)
            if menuOption in ["C"]:
                PKMarketOpenCloseAnalyser.runOpenCloseAnalysis(stockDict,endOfdayCandles,screenResults, saveResults)
            if downloadOnly and menuOption in ["X"]:
                scr.getFreshMFIStatus(stock="LatestCheckedOnDate")
                scr.getFairValue(stock="LatestCheckedOnDate", force=True)
            if not downloadOnly and menuOption in ["X", "G", "C"]:
                if menuOption == "G":
                    userPassedArgs.backtestdaysago = backtestPeriod
                if len(screenResults) > 0:
                    screenResults, saveResults = labelDataForPrinting(
                        screenResults, saveResults, configManager, volumeRatio, executeOption, reversalOption or respChartPattern
                    )
                if not newlyListedOnly and not configManager.showunknowntrends and len(screenResults) > 0:
                    screenResults, saveResults = removeUnknowns(screenResults, saveResults)
                    print(colorText.FAIL + f"[+] Configuration to remove unknown cell values resulted into removing all rows!" + colorText.END)
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
                    if len(df_screenResults) == 0:
                        print(colorText.FAIL + f"[+] Of the {len(screenResults)} stocks, no results matching the selected strategies!" + colorText.END)
                    screenResults = df_screenResults
                printNotifySaveScreenedResults(
                    screenResults,
                    saveResults,
                    selectedChoice,
                    menuChoiceHierarchy,
                    testing,
                    user=user,
                )
        if menuOption in ["X","C"]:
            finishScreening(
                downloadOnly,
                testing,
                stockDict,
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
            print("Finished backtesting with no results to show!")
        elif menuOption == "G":
            if defaultAnswer is None:
                input("Press <Enter> to continue...")
        newlyListedOnly = False
    
    # Change the config back to usual
    resetConfigToDefault()

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
            PKScheduler.scheduleTasks(tasksList=tasksList, label=f"Portfolio Calculations Report Export(Total={len(tasksList)})")
        else:
            for task in tasksList:
                task.long_running_fn(*(task,))
        for task in tasksList:
            if task.result is not None:
                showBacktestResults(task.result, sortKey=None, optionalName=task.taskName)
    
    return summary_df,sorting,sortKeys

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
        PKScheduler.scheduleTasks(tasksList,f"Portfolio X-Ray for ({len(df_grouped)})", showProgressBars=False)
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
    print(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] Would you like to sort the results?"
                    + colorText.END
                )
    print(
                    colorText.BOLD
                    + colorText.GREEN
                    + "[+] Press :\n [+] s, v, t, m : sort by Stocks, Volume, Trend, MA-Signal\n [+] d : sort by date\n [+] 1,2,3...30 : sort by period\n [+] n : Exit sorting\n"
                    + colorText.END
                )
    if defaultAnswer is None:
        choice = input(
                        colorText.BOLD + colorText.FAIL + "[+] Select option:"
                    )
        print(colorText.END, end="")
        if choice.upper() in sortKeys.keys():
            Utility.tools.clearScreen()
            showBacktestResults(backtest_df, sortKeys[choice.upper()])
            showBacktestResults(summary_df, optionalName="Summary")
        else:
            sorting = False
    else:
        print("Finished backtesting!")
        sorting = False
    return sorting

def resetConfigToDefault():
    isIntraday = userPassedArgs.intraday is not None
    if configManager.isIntradayConfig() or isIntraday:
        configManager.toggleConfig(candleDuration="1d", clearCache=False)

def prepareStocksForScreening(testing, downloadOnly, listStockCodes, indexOption):
    if not downloadOnly:
        updateMenuChoiceHierarchy()
    if listStockCodes is None or len(listStockCodes) == 0:
        listStockCodes = fetcher.fetchStockCodes(
                        indexOption, stockCode=None
                    )
        if (listStockCodes is None or len(listStockCodes) == 0) and testing:
            listStockCodes = [TEST_STKCODE]
    if indexOption == 0:
        selectedChoice["3"] = ".".join(listStockCodes)
    if testing:
        import random
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
                print(
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
            print(
                            colorText.BOLD
                            + colorText.WARN
                            + "[+] 5-EMA : Live Intraday Scanner \t"
                            + colorText.END
                            + colorText.FAIL
                            + f'Last Scanned: {datetime.now().strftime("%H:%M:%S")}\n'
                            + colorText.END
                        )
            if result_df is not None and len(result_df) > 0:
                print(
                                colorText.miniTabulator().tabulate(
                                    result_df,
                                    headers="keys",
                                    tablefmt=colorText.No_Pad_GridFormat,
                                    maxcolwidths=Utility.tools.getMaxColumnWidths(result_df)
                                ).encode("utf-8").decode(STD_ENCODING)
                            )
            print("\nPress Ctrl+C to exit.")
            if len(result_df) != last_result_len and not first_scan:
                Utility.tools.alertSound(beeps=5)
            sleep(60)
            first_scan = False
    except KeyboardInterrupt:
        input("\nPress <Enter> to Continue...\n")
        return

def handleRequestForSpecificStocks(options, indexOption):
    listStockCodes = []
    if indexOption == 0:
        if len(options) >= 4:
            listStockCodes = str(options[3]).split(",")
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
    if menuOption in ["X", "B", "G","C"]:
        selMenu = m0.find(menuOption)
        m1.renderForMenu(selMenu, asList=True)
        if indexOption is not None:
            selMenu = m1.find(indexOption)
            m2.renderForMenu(selMenu, asList=True)
            if executeOption is not None:
                selMenu = m2.find(executeOption)
                m3.renderForMenu(selMenu, asList=True)


def updateMenuChoiceHierarchy():
    global selectedChoice, menuChoiceHierarchy
    menuChoiceHierarchy = f'{level0MenuDict[selectedChoice["0"]].strip()}>{level1_X_MenuDict[selectedChoice["1"]].strip()}>{level2_X_MenuDict[selectedChoice["2"]].strip()}'
    if selectedChoice["2"] == "6":
        menuChoiceHierarchy = (
            menuChoiceHierarchy
            + f'>{level3_X_Reversal_MenuDict[selectedChoice["3"]].strip()}'
        )
        if len(selectedChoice) >= 5 and selectedChoice["3"] == "7":
            menuChoiceHierarchy = (
            menuChoiceHierarchy
            + f'>{level4_X_Lorenzian_MenuDict[selectedChoice["4"]].strip()}'
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
    elif selectedChoice["2"] == "21":
        menuChoiceHierarchy = (
            menuChoiceHierarchy
            + f'>{level3_X_PopularStocks_MenuDict[selectedChoice["3"]].strip()}'
        )
    print(
        colorText.BOLD
        + colorText.FAIL
        + "[+] You chose: "
        + menuChoiceHierarchy
        + colorText.END
    )
    default_logger().info(menuChoiceHierarchy)

def printNotifySaveScreenedResults(
    screenResults, saveResults, selectedChoice, menuChoiceHierarchy, testing, user=None
):
    global userPassedArgs, elapsed_time
    MAX_ALLOWED = (100 if userPassedArgs.maxdisplayresults is None else min(int(userPassedArgs.maxdisplayresults),100)) if not testing else 1
    tabulated_backtest_summary = ""
    tabulated_backtest_detail = ""
    recordDate = PKDateUtilities.tradingDate().strftime('%Y-%m-%d') if (userPassedArgs.backtestdaysago is None) else (PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago)))
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    Utility.tools.clearScreen()
    print(
        colorText.BOLD
        + colorText.FAIL
        + f"[+] You chose: {menuChoiceHierarchy}"
        + colorText.END
    )
    pngName = f'PKS_{PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)}_{PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")}'
    pngExtension = ".png"
    eligible = is_token_telegram_configured()
    targetDateG10k = prepareGrowthOf10kResults(saveResults, selectedChoice, menuChoiceHierarchy, testing, user, pngName, pngExtension, eligible)
    if saveResults is not None and "Date" in saveResults.columns and len(saveResults) > 0:
        recordDate = saveResults["Date"].iloc[0].replace("/","-")
    removedUnusedColumns(screenResults, saveResults, ["Date","Breakout","Resistance"],userArgs=userPassedArgs)

    tabulated_results = ""
    if screenResults is not None and len(screenResults) > 0:
        tabulated_results = colorText.miniTabulator().tabulate(
            screenResults, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
            maxcolwidths=Utility.tools.getMaxColumnWidths(screenResults)
        ).encode("utf-8").decode(STD_ENCODING)
    print(tabulated_results)
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
        print(addendumLabel)
        print(tabulated_strategy)
    if screenResults is not None and len(screenResults) >= 1:
        choiceSegments = menuChoiceHierarchy.split(">")
        choiceSegments = f"{choiceSegments[-2]} > {choiceSegments[-1]}" if len(choiceSegments)>=4 else f"{choiceSegments[-1]}"
        title = f'<b>{choiceSegments}</b> {"" if selectedChoice["0"] != "G" else "for Date:"+ targetDateG10k}'
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
                    f" but only including top {MAX_ALLOWED} results here. "
                    if (len(saveResults) > MAX_ALLOWED)
                    else ""
                )
                caption = f"<b>({len(saveResults)}{'+' if (len(saveResults) > MAX_ALLOWED) else ''}</b> stocks found in {str('{:.2f}'.format(elapsed_time))} sec){warn_text}. {title}"
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
                if not testing:
                    sendQuickScanResult(
                        menuChoiceHierarchy,
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
                                photo_filePath=pngName + backtestExtension,
                                caption=caption,
                                user=user,
                            )
                            os.remove(pngName + backtestExtension)
                        except Exception as e:  # pragma: no cover
                            default_logger().debug(e, exc_info=True)
                            pass
                            # print(e)
                            # traceback.print_exc()
                    else:
                        tabulateBacktestResults(saveResults)
            else:
                tabulateBacktestResults(saveResults)
        else:
            tabulateBacktestResults(saveResults)
            print(
                colorText.BOLD
                + colorText.GREEN
                + f"[+] Found {len(screenResults)} Stocks in {str('{:.2f}'.format(elapsed_time))} sec."
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
         "RUNNER" not in os.environ.keys()):
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
                    print(f"\n\n{titleLabelG10k}\n")
                    print(g10kStyledTable)
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
        dropAdditionalColumns.append("22-Pd %")
    for period in periods:
        if saveResults is not None:
            saveResults.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
            saveResults.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
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


def tabulateBacktestResults(saveResults, maxAllowed=0, force=False):
    if ("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and not force) or not configManager.showPastStrategyData:
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
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
        print(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] For chosen scan, summary of correctness from past: [Example, 70% of (100) under 1-Pd, means out of 100 stocks that were in the scan result in the past, 70% of them gained next day.)"
            + colorText.END
        )
        print(tabulated_backtest_summary)
    if tabulated_backtest_detail != "":
        print(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] 1 to 30 period gain/loss % on respective date for matching stocks from earlier predictions:[Example, 5% under 1-Pd, means the stock price actually gained 5% the next day from given date.]"
            + colorText.END
        )
        print(tabulated_backtest_detail)
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
):
    if (("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            return
    try:
        Utility.tools.tableToImage(
            markdown_results,
            tabulated_results,
            pngName + pngExtension,
            menuChoiceHierarchy,
            backtestSummary="",
            backtestDetail="",
            addendum=addendum,
            addendumLabel=addendumLabel,
        )
        sendMessageToTelegramChannel(
            message=None,
            photo_filePath=pngName + pngExtension,
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
    global selectedChoice, userPassedArgs, elapsed_time, start_time
    result = None
    backtest_df = None
    reviewDate = getReviewDate(userPassedArgs)
    max_allowed = getMaxAllowedResultsCount(iterations, testing)
    try:
        originalNumberOfStocks = numStocks
        iterations, numStocksPerIteration = getIterationsAndStockCounts(numStocks, iterations)
        print(
            colorText.BOLD
            + colorText.GREEN
            + f"[+] For {reviewDate}, total Stocks under review: {numStocks} over {iterations} iterations..."
            + colorText.END
        )
        if not userPassedArgs.download:
            print(colorText.WARN
                + f"[+] Starting Stock {'Screening' if menuOption=='X' else 'Backtesting.'}. Press Ctrl+C to stop!"
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
                (menuOption, backtestPeriod, result, lstscreen, lstsave) = otherArgs
                numStocks = processedCount
                result = resultItem
                backtest_df = processResults(menuOption, backtestPeriod, result, lstscreen, lstsave, result_df)
                progressbar()
                progressbar.text(
                    colorText.BOLD
                    + colorText.GREEN
                    + f"{'Found' if menuOption in ['X'] else 'Analysed'} {len(lstscreen)} {'Stocks' if menuOption in ['X'] else 'Records'}"
                    + colorText.END
                )
                if keyboardInterruptEventFired:
                    return False, backtest_df
                return not ((testing and len(lstscreen) >= 1) or len(lstscreen) >= max_allowed), backtest_df
            otherArgs = (menuOption, backtestPeriod, result, lstscreen, lstsave)
            backtest_df, result =PKScanRunner.runScan(testing,numStocks,iterations,items,numStocksPerIteration,tasks_queue,results_queue,originalNumberOfStocks,backtest_df,*otherArgs,resultsReceivedCb=processResultsCallback)

        print(f"\x1b[3A")
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
            print(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Terminating Script, Please wait..."
                + colorText.END
            )
            PKScanRunner.terminateAllWorkers(consumers=consumers, tasks_queue=tasks_queue,testing=testing)
            logging.shutdown()
        except KeyboardInterrupt:
            pass
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        print(
            colorText.BOLD
            + colorText.FAIL
            + f"\nException:\n{e}\n[+] Terminating Script, Please wait..."
            + colorText.END
        )
        PKScanRunner.terminateAllWorkers(consumers=consumers, tasks_queue=tasks_queue,testing=testing)
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
    return iterations * (100 if userPassedArgs.maxdisplayresults is None else int(userPassedArgs.maxdisplayresults)) if not testing else 1

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


def saveDownloadedData(downloadOnly, testing, stockDict, configManager, loadCount):
    global userPassedArgs, keyboardInterruptEventFired
    argsIntraday = userPassedArgs is not None and userPassedArgs.intraday is not None
    intradayConfig = configManager.isIntradayConfig()
    intraday = intradayConfig or argsIntraday
    if not keyboardInterruptEventFired and (downloadOnly or (
        configManager.cacheEnabled and not PKDateUtilities.isTradingTime() and not testing
    )):
        print(
            colorText.BOLD
            + colorText.GREEN
            + "[+] Caching Stock Data for future use, Please Wait... "
            + colorText.END,
            end="",
        )
        Utility.tools.saveStockData(stockDict, configManager, loadCount, intraday)
        if downloadOnly:
            Utility.tools.saveStockData(stockDict, configManager, loadCount, intraday, downloadOnly=downloadOnly)
    else:
        print(colorText.BOLD + colorText.GREEN + "[+] Skipped Saving!" + colorText.END)


def saveNotifyResultsFile(
    screenResults, saveResults, defaultAnswer, menuChoiceHierarchy, user=None
):
    global userPassedArgs, elapsed_time
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    caption = f'<b>{menuChoiceHierarchy.split(">")[-1]}</b>'
    if screenResults is not None and len(screenResults) >= 1:
        filename = Utility.tools.promptSaveResults(
            saveResults, defaultAnswer=defaultAnswer
        )
        # if filename is not None:
        #     sendMessageToTelegramChannel(
        #         document_filePath=filename, caption=caption, user=user
        #     )
        print(
            colorText.BOLD
            + colorText.WARN
            + "[+] Note: Trend calculation is based on number of days 'daysToLookBack' to scan as per your configuration."
            + colorText.END
        )
        try:
            if filename is not None:
                os.remove(filename)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
    print(
        colorText.BOLD
        + colorText.GREEN
        + f"[+] Screening Completed. Found {len(screenResults)} results in {round(elapsed_time,2)} sec.! Press Enter to Continue.."
        + colorText.END
    )
    if defaultAnswer is None:
        input("Press <Enter> to continue...")


def sendMessageToTelegramChannel(
    message=None, photo_filePath=None, document_filePath=None, caption=None, user=None
):
    global userPassedArgs, test_messages_queue
    test_messages_queue.append(f"message:{message}\ncaption:{caption}\nuser:{user}\ndocument:{document_filePath}")
    if len(test_messages_queue) >10:
        test_messages_queue.pop(0)
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    if user is not None and caption is not None:
        caption = f"{caption.replace('&','n')}."
    if message is not None:
        try:
            message = message.replace("&", "n")
            send_message(message, userID=user)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
    else:
        message = ""
    if photo_filePath is not None:
        try:
            if caption is not None:
                caption = f"{caption.replace('&','n')}"
            send_document(photo_filePath, caption, userID=user)
            # Breather for the telegram API to be able to send the heavy photo
            sleep(2)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
    if document_filePath is not None:
        try:
            if caption is not None:
                caption = f"{caption.replace('&','n')}"
            send_document(document_filePath, caption, userID=user)
            # Breather for the telegram API to be able to send the document
            sleep(1)
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
    if user is not None:
        # Send an update to dev channel
        send_message(
            "Responded back to userId:{0} with {1}.{2}".format(user, caption, message),
            userID="-1001785195297",
        )


def sendTestStatus(screenResults, label, user=None):
    msg = "<b>SUCCESS</b>" if len(screenResults) >= 1 else "<b>FAIL</b>"
    sendMessageToTelegramChannel(
        message=f"{msg}: Found {len(screenResults)} Stocks for {label}", user=user
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
    print(colorText.FAIL + summaryText + colorText.END + "\n")
    print(tabulated_text + "\n")
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
        print("Creating actions-data-scan directory now...")
        os.makedirs(os.path.dirname(os.path.join(os.getcwd(),f"{dirName}{os.sep}")), exist_ok=True)
    return outputFolder

def getBacktestReportFilename(sortKey="Stock", optionalName="backtest_result"):
    global userPassedArgs,selectedChoice
    choices = PKScanRunner.getFormattedChoices(userPassedArgs,selectedChoice)
    filename = f"PKScreener_{choices}_{optionalName}_{sortKey if sortKey is not None else 'Default'}Sorted.html"
    return choices, filename

def showOptionErrorMessage():
    print(
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
    print(
        colorText.BOLD
        + colorText.GREEN
        + f"[+] For {g10k if menuOption == 'G' else 'backtesting'}, you can choose from (1,2,3,4,5,10,15,22,30) or any other custom periods (< 450)."
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
            "26",
            "27",
            "28",
            "29",
            "42",
        ],
    )
    return indexOption, executeOption, backtestPeriod

def toggleUserConfig():
    configManager.toggleConfig(
        candleDuration="1d" if configManager.isIntradayConfig() else "1m"
    )
    print(
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
