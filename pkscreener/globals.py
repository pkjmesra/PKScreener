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
from PKDevTools.classes import Archiver
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger, tracelog
from PKDevTools.classes.PKMultiProcessorClient import PKMultiProcessorClient
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured,
    send_document,
    send_message,
)
from PKNSETools.morningstartools.PKMorningstarDataFetcher import morningstarDataFetcher
from tabulate import tabulate

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.Screener as Screener
import pkscreener.classes.Utility as Utility
from pkscreener.classes import VERSION, PortfolioXRay
from pkscreener.classes.Backtest import backtest, backtestSummary
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes.MenuOptions import (
    level0MenuDict,
    level1_X_MenuDict,
    level2_X_MenuDict,
    level3_X_ChartPattern_MenuDict,
    level3_X_PopularStocks_MenuDict,
    level3_X_Reversal_MenuDict,
    menus,
)
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes.ParallelProcessing import StockConsumer

multiprocessing.freeze_support()
# import dataframe_image as dfi
# import df2img
# Try Fixing bug with this symbol
TEST_STKCODE = "SBIN"
# Constants
np.seterr(divide="ignore", invalid="ignore")

# Variabls
candlePatterns = CandlePatterns()
configManager = ConfigManager.tools()
configManager.getConfig(ConfigManager.parser)
defaultAnswer = None
fetcher = Fetcher.screenerStockDataFetcher(configManager)
mstarFetcher = morningstarDataFetcher(configManager)
keyboardInterruptEvent = None
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
screener = Screener.tools(configManager, default_logger())
screenResults = None
screenResultsCounter = None
selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
stockDict = None
userPassedArgs = None
elapsed_time = 0


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
    # if not userPassedArgs.exit:
    #     userPassedArgs.options = "{0}:{1}:".format(selectedChoice["0"],selectedChoice["1"])
    #     main(userArgs=userPassedArgs)
    # elif testing:
    #     sendTestStatus(screenResults, menuChoiceHierarchy,user=user)


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
            pattern = f"{'intraday_' if intraday else ''}stock_data_"
            configManager.deleteFileWithPattern(pattern)
    return "X", 12, 0, {"0": "X", "1": "12", "2": "0"}


def getHistoricalDays(numStocks, testing):
    # Generally it takes 40-50 stocks to be processed every second.
    # We would like the backtest to finish withn 10 minutes (600 seconds).
    # days = numStocks/40 per second
    return (
        10 if testing else configManager.backtestPeriod
    )  # if numStocks <= 2000 else 120 # (5 if iterations < 5 else (100 if iterations > 100 else iterations))


def getScannerMenuChoices(
    testBuild=False,
    downloadOnly=False,
    startupoptions=None,
    menuOption=None,
    tickerOption=None,
    executeOption=None,
    defaultAnswer=None,
    user=None,
):
    global selectedChoice
    executeOption = executeOption
    menuOption = menuOption
    tickerOption = tickerOption
    try:
        if menuOption is None:
            selectedMenu = initExecution(menuOption=menuOption)
            menuOption = selectedMenu.menuKey
        if menuOption in ["H", "U", "T", "E", "Y"]:
            handleSecondaryMenuChoices(
                menuOption, testBuild, defaultAnswer=defaultAnswer, user=user
            )
        elif menuOption == "X":
            tickerOption, executeOption = initPostLevel0Execution(
                menuOption=menuOption,
                tickerOption=tickerOption,
                executeOption=executeOption,
            )
            tickerOption, executeOption = initPostLevel1Execution(
                tickerOption=tickerOption, executeOption=executeOption
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
    return menuOption, tickerOption, executeOption, selectedChoice


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
                    reportNameSummary.replace("_X_", "_B_")
                )
            )
        _, reportNameDetail = getBacktestReportFilename()
        dfd = pd.read_html(
            "https://pkjmesra.github.io/PKScreener/Backtest-Reports/{0}".format(
                reportNameDetail.replace("_X_", "_B_")
            )
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
    except:
        pass
    return summarydf, detaildf


def getTestBuildChoices(tickerOption=None, executeOption=None, menuOption=None):
    if menuOption is not None:
        return (
            str(menuOption),
            tickerOption if tickerOption is not None else 1,
            executeOption if executeOption is not None else 0,
            {
                "0": str(menuOption),
                "1": (str(tickerOption) if tickerOption is not None else 1),
                "2": (str(executeOption) if executeOption is not None else 0),
            },
        )
    return "X", 1, 0, {"0": "X", "1": "1", "2": "0"}


def getTopLevelMenuChoices(startupoptions, testBuild, downloadOnly, defaultAnswer=None):
    global selectedChoice, userPassedArgs
    executeOption = None
    menuOption = None
    tickerOption = None
    options = []
    if startupoptions is not None:
        options = startupoptions.split(":")
        menuOption = options[0] if len(options) >= 1 else None
        tickerOption = options[1] if len(options) >= 2 else None
        executeOption = options[2] if len(options) >= 3 else None
    if testBuild:
        menuOption, tickerOption, executeOption, selectedChoice = getTestBuildChoices(
            tickerOption=tickerOption,
            executeOption=executeOption,
            menuOption=menuOption,
        )
    elif downloadOnly:
        menuOption, tickerOption, executeOption, selectedChoice = getDownloadChoices(
            defaultAnswer=defaultAnswer
        )
        intraday = userPassedArgs.intraday or configManager.isIntradayConfig()
        filePrefix = "INTRADAY_" if intraday else ""
        _, cache_file_name = Utility.tools.afterMarketStockDataExists(intraday)
        Utility.tools.set_github_output(f"{filePrefix}DOWNLOAD_CACHE_FILE_NAME",cache_file_name)
    return options, menuOption, tickerOption, executeOption


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
        helpData = Utility.tools.showDevInfo(defaultAnswer=defaultAnswer)
        if user is not None:
            sendMessageToTelegramChannel(
                message=Utility.tools.removeAllColorStyles(helpData), user=user
            )
    elif menuOption == "U":
        OTAUpdater.checkForUpdate(VERSION, skipDownload=testing)
        if defaultAnswer is None:
            input("Press <Enter> to continue...")
    elif menuOption == "T":
        toggleUserConfig()
    elif menuOption == "E":
        configManager.setConfig(ConfigManager.parser)
    elif menuOption == "Y":
        configData = configManager.showConfigFile(defaultAnswer=defaultAnswer)
        if user is not None:
            sendMessageToTelegramChannel(
                message=Utility.tools.removeAllColorStyles(configData), user=user
            )
    return


def initDataframes():
    screenResults = pd.DataFrame(
        columns=[
            "Stock",
            "Consol.",
            "Breakout",
            "LTP",
            "52Wk H",
            "52Wk L",
            "%Chng",
            "Volume",
            "MA-Signal",
            "RSI",
            "Trend",
            "Pattern",
            "CCI",
        ]
    )
    saveResults = pd.DataFrame(
        columns=[
            "Stock",
            "Consol.",
            "Breakout",
            "LTP",
            "52Wk H",
            "52Wk L",
            "%Chng",
            "Volume",
            "MA-Signal",
            "RSI",
            "Trend",
            "Pattern",
            "CCI",
        ]
    )
    return screenResults, saveResults


def initExecution(menuOption=None):
    global selectedChoice
    Utility.tools.clearScreen()

    m0.renderForMenu(selectedMenu=None)
    try:
        if menuOption is None:
            menuOption = input(colorText.BOLD + colorText.FAIL + "[+] Select option: ")
            print(colorText.END, end="")
        if menuOption == "":
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
            elif selectedMenu.menuKey in ["B", "G", "H", "U", "T", "S", "E", "X", "Y"]:
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
    menuOption=None, tickerOption=None, executeOption=None, skip=[], retrial=False
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
        + " > "
        + colorText.END
    )
    if tickerOption is None:
        selectedMenu = m0.find(menuOption)
        m1.renderForMenu(selectedMenu=selectedMenu, skip=skip)
    try:
        if tickerOption is None:
            tickerOption = input(
                colorText.BOLD + colorText.FAIL + "[+] Select option: "
            )
            print(colorText.END, end="")
        if tickerOption == "" or tickerOption is None:
            tickerOption = 12
        # elif tickerOption == 'W' or tickerOption == 'w' or tickerOption == 'N' or tickerOption == 'n' or tickerOption == 'E' or tickerOption == 'e':
        elif not str(tickerOption).isnumeric():
            tickerOption = tickerOption.upper()
            if tickerOption in ["M", "E", "N", "Z"]:
                return tickerOption, 0
        else:
            tickerOption = int(tickerOption)
            if tickerOption < 0 or tickerOption > 14:
                raise ValueError
            elif tickerOption == 13:
                newlyListedOnly = True
                tickerOption = 12
        selectedChoice["1"] = str(tickerOption)
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
    return tickerOption, executeOption


def initPostLevel1Execution(tickerOption, executeOption=None, skip=[], retrial=False):
    global selectedChoice
    if executeOption is None:
        if tickerOption is not None and tickerOption != "W":
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
            selectedMenu = m1.find(tickerOption)
            m2.renderForMenu(selectedMenu=selectedMenu, skip=skip)
    try:
        if tickerOption is not None and tickerOption != "W":
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
            return initPostLevel1Execution(tickerOption, executeOption, retrial=True)
    return tickerOption, executeOption


def initQueues(minimumCount=0):
    tasks_queue = multiprocessing.JoinableQueue()
    results_queue = multiprocessing.Queue()

    totalConsumers = min(minimumCount, multiprocessing.cpu_count())
    if totalConsumers == 1:
        totalConsumers = 2  # This is required for single core machine
    if configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
        totalConsumers -= 1
    return tasks_queue, results_queue, totalConsumers


def labelDataForPrinting(screenResults, saveResults, configManager, volumeRatio):
    # Publish to gSheet with https://github.com/burnash/gspread
    try:
        screenResults.sort_values(by=["Volume"], ascending=False, inplace=True)
        saveResults.sort_values(by=["Volume"], ascending=False, inplace=True)
        screenResults.set_index("Stock", inplace=True)
        saveResults.set_index("Stock", inplace=True)
        screenResults.loc[:, "Volume"] = screenResults.loc[:, "Volume"].apply(
            lambda x: Utility.tools.formatRatio(x, volumeRatio)
        )
        saveResults.loc[:, "Volume"] = saveResults.loc[:, "Volume"].apply(
            lambda x: str(x) + "x"
        )
        screenResults.rename(
            columns={
                "Trend": f"Trend({configManager.daysToLookback}Prds)",
                "Breakout": f"Breakout({configManager.daysToLookback}Prds)",
                "Consol.": f"Consol.({configManager.daysToLookback}Prds)",
            },
            inplace=True,
        )
        saveResults.rename(
            columns={
                "Trend": f"Trend({configManager.daysToLookback}Prds)",
                "Breakout": f"Breakout({configManager.daysToLookback}Prds)",
                "Consol.": f"Consol.({configManager.daysToLookback}Prds)",
            },
            inplace=True,
        )
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
    return screenResults, saveResults


@tracelog
def main(userArgs=None):
    global screenResults, selectedChoice, defaultAnswer, menuChoiceHierarchy, screenCounter, screenResultsCounter, stockDict, userPassedArgs, loadedStockData, keyboardInterruptEvent, loadCount, maLength, newlyListedOnly
    selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
    testing = False if userArgs is None else (userArgs.testbuild and userArgs.prodbuild)
    testBuild = False if userArgs is None else (userArgs.testbuild and not testing)
    downloadOnly = False if userArgs is None else userArgs.download
    startupoptions = None if userArgs is None else userArgs.options
    user = None if userArgs is None else userArgs.user
    defaultAnswer = None if userArgs is None else userArgs.answerdefault
    userPassedArgs = userArgs
    options = []
    screenCounter = multiprocessing.Value("i", 1)
    screenResultsCounter = multiprocessing.Value("i", 0)
    keyboardInterruptEvent = multiprocessing.Manager().Event()

    if stockDict is None:
        stockDict = multiprocessing.Manager().dict()
        loadCount = 0

    minRSI = 0
    maxRSI = 100
    insideBarToLookback = 7
    respChartPattern = None
    daysForLowestVolume = 30
    backtestPeriod = 0
    reversalOption = None
    listStockCodes = None
    screenResults, saveResults = initDataframes()
    options, menuOption, tickerOption, executeOption = getTopLevelMenuChoices(
        startupoptions, testBuild, downloadOnly, defaultAnswer=defaultAnswer
    )
    # Print Level 1 menu options
    selectedMenu = initExecution(menuOption=menuOption)
    menuOption = selectedMenu.menuKey
    if menuOption in ["X", "T", "E", "Y", "U", "H"]:
        # Print Level 2 menu options
        menuOption, tickerOption, executeOption, selectedChoice = getScannerMenuChoices(
            testBuild or testing,
            downloadOnly,
            startupoptions,
            menuOption=menuOption,
            tickerOption=tickerOption,
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
            if str(tickerOption).isnumeric():
                backtestPeriod = int(tickerOption)
            if len(options) >= 4:
                tickerOption = executeOption
                executeOption = options[3]
            del options[1]  # Let's delete the backtestperiod from the provided options
        tickerOption, executeOption, backtestPeriod = takeBacktestInputs(
            str(menuOption).upper(), tickerOption, executeOption, backtestPeriod
        )
    elif menuOption in ["S"]:
        print(
            colorText.GREEN
            + "[+] Collecting all metrics for summarising..."
            + colorText.END
        )
        df_all = PortfolioXRay.summariseAllStrategies()
        if df_all is not None:
            print(
                colorText.miniTabulator().tabulate(
                    df_all,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                    showindex=False,
                )
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
        print("Not implemented yet! Try selecting a different option.")
        sleep(3)
        return

    if menuOption in ["X", "B", "G"]:
        selMenu = m0.find(menuOption)
        m1.renderForMenu(selMenu, asList=True)
        if tickerOption is not None:
            selMenu = m1.find(tickerOption)
            m2.renderForMenu(selMenu, asList=True)
            if executeOption is not None:
                selMenu = m2.find(executeOption)
                m3.renderForMenu(selMenu, asList=True)
    if tickerOption == "M" or executeOption == "M":
        # Go back to the caller. It will show the console menu again.
        return
    if tickerOption == 0:
        if len(options) >= 4:
            listStockCodes = str(options[3]).split(",")
    if executeOption == "Z":
        input(
            colorText.BOLD
            + colorText.FAIL
            + "[+] Press <Enter> to Exit!"
            + colorText.END
        )
        sys.exit(0)
    if executeOption is None:
        executeOption = 0
    executeOption = int(executeOption)
    volumeRatio = configManager.volumeRatio
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
            if reversalOption == 4 or reversalOption == 6:
                if len(options) >= 5:
                    if str(options[4]).isnumeric():
                        maLength = int(options[4])
                    elif str(options[4]).upper() == "D":
                        maLength = 50 if reversalOption == 4 else 7
                elif defaultAnswer == "Y" and user is not None:
                    # bot mode
                    maLength = 50 if reversalOption == 4 else 7
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
    if executeOption == 7:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            respChartPattern = int(options[3])
            selectedChoice["3"] = options[3]
            if respChartPattern in [1, 2, 3]:
                if len(options) >= 5:
                    if str(options[4]).isnumeric():
                        insideBarToLookback = int(options[4])
                    elif str(options[4]).upper() == "D":
                        insideBarToLookback = 7 if respChartPattern in [1, 2] else 0.02
                elif defaultAnswer == "Y" and user is not None:
                    # bot mode
                    insideBarToLookback = 7 if respChartPattern in [1, 2] else 0.02
                else:
                    (
                        respChartPattern,
                        insideBarToLookback,
                    ) = Utility.tools.promptChartPatterns(selectedMenu)
            elif respChartPattern in [0, 4, 5, 6]:
                insideBarToLookback = 0
            else:
                (
                    respChartPattern,
                    insideBarToLookback,
                ) = Utility.tools.promptChartPatterns(selectedMenu)
        else:
            respChartPattern, insideBarToLookback = Utility.tools.promptChartPatterns(
                selectedMenu
            )
        if (
            respChartPattern is None
            or insideBarToLookback is None
            or respChartPattern == 0
        ):
            return
        else:
            selectedChoice["3"] = str(respChartPattern)
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
            if popOption >= 0 and popOption <= 3:
                pass
        else:
            popOption = Utility.tools.promptPopularStocks(selectedMenu)
        if popOption is None or popOption == 0:
            return
        else:
            selectedChoice["3"] = str(popOption)
        updateMenuChoiceHierarchy()
        if popOption == 3:
            screenResults = mstarFetcher.fetchMorningstarTopDividendsYieldStocks()
        elif popOption > 0 and popOption <= 2:
            screenResults = mstarFetcher.fetchMorningstarFundFavouriteStocks(
                "NoOfFunds" if popOption == 2 else "ChangeInShares"
            )
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
    if executeOption == 22:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            popOption = int(options[3])
            if popOption >= 0 and popOption <= 3:
                pass
        else:
            popOption = Utility.tools.promptPopularStocks(selectedMenu)
        if popOption is None or popOption == 0:
            return
        else:
            selectedChoice["3"] = str(popOption)
        updateMenuChoiceHierarchy()
        screenResults = mstarFetcher.fetchMorningstarStocksPerformanceForExchange()
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
    if executeOption == 42:
        Utility.tools.getLastScreenedResults()
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
        not str(tickerOption).isnumeric() and tickerOption in ["W", "E", "M", "N", "Z"]
    ) or (
        str(tickerOption).isnumeric()
        and (int(tickerOption) >= 0 and int(tickerOption) < 15)
    ):
        configManager.getConfig(ConfigManager.parser)
        try:
            if tickerOption == "W":
                listStockCodes = fetcher.fetchWatchlist()
                if listStockCodes is None:
                    input(
                        colorText.BOLD
                        + colorText.FAIL
                        + f"[+] Create the watchlist.xlsx file in {os.getcwd()} and Restart the Program!"
                        + colorText.END
                    )
                    sys.exit(0)
            elif tickerOption == "N":
                os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
                prediction, pText, sText = screener.getNiftyPrediction(
                    data=fetcher.fetchLatestNiftyDaily(proxyServer=fetcher.proxyServer)
                )
                sendMessageToTelegramChannel(
                    message=f"Nifty AI prediction for the next day: {pText}. {sText}.",
                    user=user,
                )
                if defaultAnswer is None:
                    input("\nPress <Enter> to Continue...\n")
                return
            elif tickerOption == "M":
                return
            elif tickerOption == "Z":
                input(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] Press <Enter> to Exit!"
                    + colorText.END
                )
                sys.exit(0)
            elif tickerOption == "E":
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
                        print(
                            colorText.miniTabulator().tabulate(
                                result_df,
                                headers="keys",
                                tablefmt=colorText.No_Pad_GridFormat,
                            )
                        )
                        print("\nPress Ctrl+C to exit.")
                        if len(result_df) != last_result_len and not first_scan:
                            Utility.tools.alertSound(beeps=5)
                        sleep(60)
                        first_scan = False
                except KeyboardInterrupt:
                    input("\nPress <Enter> to Continue...\n")
                    return
            else:
                if not downloadOnly:
                    updateMenuChoiceHierarchy()
                if listStockCodes is None or len(listStockCodes) == 0:
                    listStockCodes = fetcher.fetchStockCodes(
                        tickerOption, stockCode=None
                    )
                    if (listStockCodes is None or len(listStockCodes) == 0) and testing:
                        listStockCodes = [TEST_STKCODE]
                if tickerOption == 0:
                    selectedChoice["3"] = ".".join(listStockCodes)
                if testing:
                    import random
                    listStockCodes = [random.choice(listStockCodes)]
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

        if (menuOption in ["B", "G"] and not loadedStockData) or (
            not downloadOnly
            and not Utility.tools.isTradingTime()
            and configManager.cacheEnabled
            and not loadedStockData
            and not testing
        ):
            Utility.tools.loadStockData(
                stockDict,
                configManager,
                downloadOnly=downloadOnly,
                defaultAnswer=defaultAnswer,
                forceLoad=(menuOption in ["B", "G"]),
            )
            loadedStockData = True
        loadCount = len(stockDict)

        if not downloadOnly:
            print(
                colorText.BOLD
                + colorText.WARN
                + f"[+] Starting Stock {'Screening' if menuOption=='X' else 'Backtesting.'}. Press Ctrl+C to stop!"
            )
        else:
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Starting download.. Press Ctrl+C to stop!"
            )

        suggestedHistoricalDuration = (
            getHistoricalDays(len(listStockCodes), testing)
            if menuOption.upper() in ["B"]
            else 1
        )
        # Number of days from past, including the backtest duration chosen by the user
        # that we will need to consider to evaluate the data. If the user choses 10-period
        # backtesting, we will need to have the past 6-months or whatever is returned by
        # x = getHistoricalDays and 10 days of recent data. So total rows to consider
        # will be x + 10 days.
        samplingDuration = (
            (suggestedHistoricalDuration + 1) if menuOption in ["B"] else 2
        )
        fillerPlaceHolder = 1 if menuOption in ["B"] else 2
        backtest_df = None
        if menuOption.upper() in ["B", "G"]:
            print(
                colorText.BOLD
                + colorText.WARN
                + f"[+] A total of {configManager.backtestPeriod} trading periods' historical data will be considered for backtesting. You can change this in User Config."
            )
        items = []
        actualHistoricalDuration = samplingDuration - fillerPlaceHolder
        # Lets begin from y days ago, evaluate from that date if the selected strategy had yielded any result
        # and then keep coming to the next day (x-1) until we get to today (actualHistoricalDuration = 0)
        while actualHistoricalDuration >= 0:
            moreItems = [
                (
                    executeOption,
                    reversalOption,
                    maLength,
                    daysForLowestVolume,
                    minRSI,
                    maxRSI,
                    respChartPattern,
                    insideBarToLookback,
                    len(listStockCodes),
                    configManager.cacheEnabled,
                    stock,
                    newlyListedOnly,
                    downloadOnly,
                    volumeRatio,
                    testBuild,
                    userArgs.log,
                    (
                        actualHistoricalDuration
                        if (menuOption == "B")
                        else (
                            (backtestPeriod)
                            if (menuOption == "G")
                            else (
                                0
                                if (userPassedArgs.backtestdaysago is None)
                                else (int(userPassedArgs.backtestdaysago))
                            )
                        )
                    ),
                    (
                        backtestPeriod
                        if menuOption == "B"
                        else configManager.daysToLookback
                    ),
                    default_logger().level,
                    (menuOption in ["B", "G"])
                    or (userPassedArgs.backtestdaysago is not None),
                )
                for stock in listStockCodes
            ]
            items.extend(moreItems)
            fillerPlaceHolder = fillerPlaceHolder + 1
            actualHistoricalDuration = samplingDuration - fillerPlaceHolder

        tasks_queue, results_queue, totalConsumers = initQueues(len(items))
        cp = CandlePatterns()
        cm = configManager
        f = Fetcher.screenerStockDataFetcher(configManager)
        scr = Screener.tools(configManager, default_logger())
        consumers = [
            PKMultiProcessorClient(
                StockConsumer().screenStocks,
                tasks_queue,
                results_queue,
                screenCounter,
                screenResultsCounter,
                stockDict,
                fetcher.proxyServer,
                keyboardInterruptEvent,
                default_logger(),
                f,
                cm,
                cp,
                scr,
            )
            for _ in range(totalConsumers)
        ]
        startWorkers(consumers)
        screenResults, saveResults, backtest_df = runScanners(
            menuOption,
            items,
            tasks_queue,
            results_queue,
            listStockCodes,
            backtestPeriod,
            samplingDuration - 1,
            consumers,
            screenResults,
            saveResults,
            backtest_df,
            testing=testing,
        )

        print(colorText.END)
        terminateAllWorkers(consumers, tasks_queue, testing)
        if not downloadOnly and menuOption in ["X", "G"]:
            if menuOption == "G":
                userPassedArgs.backtestdaysago = backtestPeriod
            screenResults, saveResults = labelDataForPrinting(
                screenResults, saveResults, configManager, volumeRatio
            )
            if not newlyListedOnly and not configManager.showunknowntrends:
                screenResults, saveResults = removeUnknowns(screenResults, saveResults)
            printNotifySaveScreenedResults(
                screenResults,
                saveResults,
                selectedChoice,
                menuChoiceHierarchy,
                testing,
                user=user,
            )
        if menuOption == "X":
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
            df_grouped = backtest_df.groupby("Date")
            userPassedArgs.backtestdaysago = backtestPeriod
            df_xray = None
            for calcForDate, df_group in df_grouped:
                p_df = PortfolioXRay.performXRay(
                    df_group, userPassedArgs, calcForDate=calcForDate
                )
                if df_xray is not None:
                    df_xray = pd.concat([df_xray, p_df], axis=0)
                else:
                    df_xray = p_df
            # Let's drop the columns no longer required for backtest report
            removedUnusedColumns(
                None, backtest_df, ["Consol.", "Breakout", "RSI", "Pattern", "CCI"]
            )
            df_xray = df_xray.replace(np.nan, "", regex=True)
            df_xray = PortfolioXRay.xRaySummary(df_xray)
            df_xray.loc[:, "Date"] = df_xray.loc[:, "Date"].apply(
                lambda x: x.replace("-", "/")
            )
            showBacktestResults(df_xray, sortKey="Date", optionalName="Insights")
            summary_df = backtestSummary(backtest_df)
            backtest_df.loc[:, "Date"] = backtest_df.loc[:, "Date"].apply(
                lambda x: x.replace("-", "/")
            )
            showBacktestResults(backtest_df)
            showBacktestResults(summary_df, optionalName="Summary")
            sorting = False if defaultAnswer == "Y" else True
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
            while sorting:
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
                if defaultAnswer != "Y":
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
            if defaultAnswer != "Y":
                input("Press <Enter> to continue...")
        elif menuOption == "B":
            print("Finished backtesting with no results to show!")
        elif menuOption == "G":
            if defaultAnswer != "Y":
                input("Press <Enter> to continue...")
        newlyListedOnly = False
    if configManager.isIntradayConfig():
        isIntraday = userPassedArgs.intraday is not None
        configManager.toggleConfig(
            candleDuration="1m" if isIntraday else "1d", clearCache=False
        )


def updateMenuChoiceHierarchy():
    global selectedChoice, menuChoiceHierarchy
    menuChoiceHierarchy = f'{level0MenuDict[selectedChoice["0"]].strip()}>{level1_X_MenuDict[selectedChoice["1"]].strip()}>{level2_X_MenuDict[selectedChoice["2"]].strip()}'
    if selectedChoice["2"] == "6":
        menuChoiceHierarchy = (
            menuChoiceHierarchy
            + f'>{level3_X_Reversal_MenuDict[selectedChoice["3"]].strip()}'
        )
    elif selectedChoice["2"] == "7":
        menuChoiceHierarchy = (
            menuChoiceHierarchy
            + f'>{level3_X_ChartPattern_MenuDict[selectedChoice["3"]].strip()}'
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


def populateQueues(items, tasks_queue, exit=False):
    for item in items:
        tasks_queue.put(item)
    if exit:
        # Append exit signal for each process indicated by None
        for _ in range(multiprocessing.cpu_count()):
            tasks_queue.put(None)


def printNotifySaveScreenedResults(
    screenResults, saveResults, selectedChoice, menuChoiceHierarchy, testing, user=None
):
    global userPassedArgs, elapsed_time
    MAX_ALLOWED = 100 if not testing else 1
    tabulated_backtest_summary = ""
    tabulated_backtest_detail = ""
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    Utility.tools.clearScreen()
    print(
        colorText.BOLD
        + colorText.FAIL
        + f"[+] You chose: {menuChoiceHierarchy}"
        + colorText.END
    )
    pngName = f'PKS_{getFormattedChoices()}_{Utility.tools.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")}'
    pngExtension = ".png"
    if selectedChoice["0"] == "G" or userPassedArgs.backtestdaysago is not None:
        if saveResults is not None and len(saveResults) > 0:
            df = PortfolioXRay.performXRay(saveResults, userPassedArgs)
            targetDateG10k = saveResults["Date"].iloc[0]
            titleLabelG10k = f"For {userPassedArgs.backtestdaysago}-Period(s) from {targetDateG10k}, portfolio calculations in terms of Growth of 10k:"
            print(f"\n\n{titleLabelG10k}\n")
            g10kStyledTable = colorText.miniTabulator().tabulate(
                df,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
            )
            print(g10kStyledTable)
            g10kUnStyledTable = Utility.tools.removeAllColorStyles(g10kStyledTable)
            if not testing:
                sendQuickScanResult(
                    menuChoiceHierarchy,
                    user,
                    g10kStyledTable,
                    g10kUnStyledTable,
                    titleLabelG10k,
                    pngName,
                    pngExtension,
                )
        elif user is not None:
            sendMessageToTelegramChannel(
                message=f"No scan results found for {menuChoiceHierarchy}", user=user
            )
    removedUnusedColumns(screenResults, saveResults, ["Date"])

    tabulated_results = colorText.miniTabulator().tabulate(
        screenResults, headers="keys", tablefmt=colorText.No_Pad_GridFormat
    )
    print(tabulated_results)
    _, reportNameInsights = getBacktestReportFilename(
        sortKey="Date", optionalName="Insights"
    )
    strategy_df = PortfolioXRay.bestStrategiesFromSummaryForReport(reportNameInsights)
    addendumLabel = (
        "[+] Strategy that has best results in the past for this scan option:"
    )
    tabulated_strategy = ""
    if strategy_df is not None:
        tabulated_strategy = colorText.miniTabulator().tabulate(
            strategy_df,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            showindex=False,
        )
        print(addendumLabel)
        print(tabulated_strategy)
    if screenResults is not None and len(screenResults) >= 1:
        title = f'<b>{menuChoiceHierarchy.split(">")[-1]}</b> {"" if selectedChoice["0"] != "G" else "for Date:"+ targetDateG10k}'
        if (
            "RUNNER" in os.environ.keys()
            or "PKDevTools_Default_Log_Level" in os.environ.keys()
        ):
            eligible = is_token_telegram_configured()
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
                caption = f"<b>({len(saveResults)}</b> stocks found in {str('{:.2f}'.format(elapsed_time))} sec){warn_text}. {title}"
                backtestExtension = "_backtest.png"
                if len(screenResultsTrimmed) > MAX_ALLOWED:
                    screenResultsTrimmed = screenResultsTrimmed.head(MAX_ALLOWED)
                    saveResultsTrimmed = saveResultsTrimmed.head(MAX_ALLOWED)
                    tabulated_results = colorText.miniTabulator().tabulate(
                        screenResultsTrimmed,
                        headers="keys",
                        tablefmt=colorText.No_Pad_GridFormat,
                    )
                markdown_results = colorText.miniTabulator().tabulate(
                    saveResultsTrimmed,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                )
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
                            saveResultsTrimmed, maxAllowed=MAX_ALLOWED
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
            Utility.tools.setLastScreenedResults(screenResults)
    elif user is not None:
        sendMessageToTelegramChannel(
            message=f"No scan results found for {menuChoiceHierarchy}", user=user
        )


def removedUnusedColumns(screenResults, saveResults, dropAdditionalColumns=[]):
    periods = [1, 2, 3, 4, 5, 10, 15, 22, 30]
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


def tabulateBacktestResults(saveResults, maxAllowed=0):
    tabulated_backtest_summary = ""
    tabulated_backtest_detail = ""
    summarydf, detaildf = getSummaryCorrectnessOfStrategy(saveResults)
    if summarydf is not None and len(summarydf) > 0:
        tabulated_backtest_summary = colorText.miniTabulator().tabulate(
            summarydf,
            headers="keys",
            tablefmt=colorText.No_Pad_GridFormat,
            showindex=False,
        )
    if detaildf is not None and len(detaildf) > 0:
        if maxAllowed != 0 and len(detaildf) > 2 * maxAllowed:
            detaildf = detaildf.head(2 * maxAllowed)
            tabulated_backtest_detail = colorText.miniTabulator().tabulate(
                detaildf,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
            )
        else:
            tabulated_backtest_detail = colorText.miniTabulator().tabulate(
                detaildf,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
            )
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
        tableText = "<!DOCTYPE html><html><head><script type='application/javascript' src='https://pkjmesra.github.io/PKScreener/pkscreener/classes/tableSorting.js' ></script><style type='text/css'>body, table {background-color: black; color: white;} table, th, td {border: 1px solid white;} th {cursor: pointer; color:white; text-decoration:underline;} .r {color:red;font-weight:bold;} .w {color:white;font-weight:bold;} .g {color:lightgreen;font-weight:bold;} .y {color:yellow;}</style></head><body><span style='color:white;' >"
        colored_text = colored_text.replace(
            "<table", f"{tableText}{summaryText}<br /><table"
        )
        colored_text = colored_text.replace("<table ", "<table id='resultsTable' ")
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
    colored_text = colored_text.replace(f"<td>{colorText.GREEN}", "<td class='g'>")
    colored_text = colored_text.replace(f"<td>{colorText.FAIL}", "<td class='r'>")
    colored_text = colored_text.replace(f"<td>{colorText.WARN}", "<td class='y'>")
    colored_text = colored_text.replace(f"<td>{colorText.WHITE}", "<td class='w'>")
    colored_text = colored_text.replace(colorText.END, "")
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
    listStockCodes,
    backtestPeriod,
    iterations,
    consumers,
    screenResults,
    saveResults,
    backtest_df,
    testing=False,
):
    global selectedChoice, userPassedArgs, elapsed_time
    choices = userReportName(selectedChoice)
    try:
        numStocks = len(listStockCodes) * int(iterations)
        queueCounter = 0
        dumpFreq = 1
        print(colorText.END + colorText.BOLD)
        bar, spinner = Utility.tools.getProgressbarStyle()
        counter = 0
        start_time = time.time()
        with alive_bar(numStocks, bar=bar, spinner=spinner) as progressbar:
            lstscreen = []
            lstsave = []
            while numStocks:
                if counter == 0 and queueCounter < int(iterations) and numStocks > 0:
                    populateQueues(
                        items[
                            len(listStockCodes)
                            * queueCounter : len(listStockCodes)
                            * (queueCounter + 1)
                        ],
                        tasks_queue,
                        queueCounter + 1 == int(iterations),
                    )
                counter += 1
                result = results_queue.get()
                if result is not None:
                    lstscreen.append(result[0])
                    lstsave.append(result[1])
                    sampleDays = result[4]
                    if menuOption == "B":
                        backtest_df = updateBacktestResults(
                            backtestPeriod,
                            choices,
                            dumpFreq,
                            start_time,
                            result,
                            sampleDays,
                            backtest_df,
                        )

                numStocks -= 1
                progressbar.text(
                    colorText.BOLD
                    + colorText.GREEN
                    + f"Found {screenResultsCounter.value} Stocks"
                    + colorText.END
                )
                progressbar()
                # If it's being run under unit testing, let's wrap up if we find at least 1
                # stock or if we've already tried screening through 5% of the list.
                if testing and (
                    len(lstscreen) >= 1 or counter >= int(len(listStockCodes) * 0.05)
                ):
                    break
                if counter >= len(listStockCodes):
                    queueCounter += 1
                    counter = 0
        elapsed_time = time.time() - start_time
        if menuOption in ["X", "G"]:
            # create extension
            screenResults = pd.DataFrame(lstscreen)
            saveResults = pd.DataFrame(lstsave)

    except KeyboardInterrupt:
        try:
            keyboardInterruptEvent.set()
        except KeyboardInterrupt:
            pass
        print(
            colorText.BOLD
            + colorText.FAIL
            + "\n[+] Terminating Script, Please wait..."
            + colorText.END
        )
        for worker in consumers:
            worker.terminate()
        logging.shutdown()
    return screenResults, saveResults, backtest_df


def updateBacktestResults(
    backtestPeriod, choices, dumpFreq, start_time, result, sampleDays, backtest_df
):
    global elapsed_time
    sellSignal = (
        str(selectedChoice["2"]) in ["6", "7"] and str(selectedChoice["3"]) in ["2"]
    ) or selectedChoice["2"] in ["15", "16", "19"]
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
    # if  screenResultsCounter.value >= 50 * (4 if userPassedArgs.prodbuild else 1) * dumpFreq:
    #     # Dump results on the screen and into a file every 50 results
    #     showBacktestResults(backtest_df)
    #     summary_df = backtestSummary(backtest_df)
    #     # summary_df.set_index("Stock", inplace=True)
    #     showBacktestResults(summary_df,optionalName="Summary")
    #     dumpFreq = dumpFreq + 1
    # Commit intermittently if its been running for over x hours
    # if userPassedArgs.prodbuild and elapsed_time >= dumpFreq * 3600:
    #     Committer.commitTempOutcomes(choices)
    return backtest_df


def saveDownloadedData(downloadOnly, testing, stockDict, configManager, loadCount):
    global userPassedArgs
    argsIntraday = userPassedArgs is not None and userPassedArgs.intraday is not None
    intradayConfig = configManager.isIntradayConfig()
    intraday = intradayConfig or argsIntraday
    if downloadOnly or (
        configManager.cacheEnabled and not Utility.tools.isTradingTime() and not testing
    ):
        print(
            colorText.BOLD
            + colorText.GREEN
            + "[+] Caching Stock Data for future use, Please Wait... "
            + colorText.END,
            end="",
        )
        Utility.tools.saveStockData(stockDict, configManager, loadCount, intraday)
    else:
        print(
            colorText.BOLD + colorText.GREEN + "[+] Skipped Saving!" + colorText.END,
            end="",
        )


def saveNotifyResultsFile(
    screenResults, saveResults, defaultAnswer, menuChoiceHierarchy, user=None
):
    global userPassedArgs
    if user is None and userPassedArgs.user is not None:
        user = userPassedArgs.user
    caption = f'<b>{menuChoiceHierarchy.split(">")[-1]}</b>'
    if len(screenResults) >= 1:
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
        + "[+] Screening Completed! Press Enter to Continue.."
        + colorText.END
    )
    if defaultAnswer is None:
        input("Press <Enter> to continue...")


def sendMessageToTelegramChannel(
    message=None, photo_filePath=None, document_filePath=None, caption=None, user=None
):
    global userPassedArgs
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
    global menuChoiceHierarchy, selectedChoice, userPassedArgs
    pd.set_option("display.max_rows", 800)
    # pd.set_option("display.max_columns", 20)
    if backtest_df is None:
        return
    backtest_df.drop_duplicates()
    summaryText = f"As of {Utility.tools.currentDateTime().strftime('%d-%m-%y %H:%M:%S IST')}\n{menuChoiceHierarchy.replace('Backtests','Growth of 10K' if optionalName=='Insights' else 'Backtests')}"
    lastSummaryRow = None
    if optionalName != "Summary":
        backtest_df.sort_values(by=[sortKey], ascending=False, inplace=True)
    else:
        lastRow = backtest_df.iloc[-1, :]
        if lastRow.iloc[0] == "SUMMARY":
            lastSummaryRow = pd.DataFrame(lastRow).transpose()
            lastSummaryRow.set_index("Stock", inplace=True)
            lastSummaryRow = lastSummaryRow.iloc[:, lastSummaryRow.columns != "Stock"]
        summaryText = f"{summaryText}\nOverall Summary of (correctness of) Strategy Prediction Positive outcomes:"
    tabulated_text = colorText.miniTabulator().tabulate(
        backtest_df,
        headers="keys",
        tablefmt=colorText.No_Pad_GridFormat,
        showindex=False,
    )
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
    colored_text = reformatTable(summaryText, headerDict, colored_text, sorting=True)
    # Delete any pre-existing backtesting report for the same parameters
    filename = os.path.join(Archiver.get_user_outputs_dir(), filename)
    try:
        os.remove(filename)
    except Exception:
        pass
    finally:
        with open(filename, "w") as f:
            f.write(colored_text)

    if lastSummaryRow is not None:
        oneline_text = lastSummaryRow.to_html(header=False, index=False)
        oneline_text = reformatTable(
            summaryText, headerDict, oneline_text, sorting=False
        )
        onelineSummaryFile = f"PKScreener_{choices}_OneLine_{optionalName}.html"
        onelineSummaryFile = os.path.join(
            Archiver.get_user_outputs_dir(), onelineSummaryFile
        )
        try:
            os.remove(onelineSummaryFile)
        except Exception:
            pass
        finally:
            with open(onelineSummaryFile, "w") as f:
                f.write(oneline_text)


def getBacktestReportFilename(sortKey="Stock", optionalName="backtest_result"):
    choices = getFormattedChoices()
    filename = f"PKScreener_{choices}_{optionalName}_{sortKey}Sorted.html"
    return choices, filename


def getFormattedChoices():
    global selectedChoice, userPassedArgs
    isIntraday = configManager.isIntradayConfig() or (
        userPassedArgs.intraday is not None
    )
    choices = ""
    for choice in selectedChoice:
        if len(selectedChoice[choice]) > 0:
            if len(choices) > 0:
                choices = f"{choices}_"
            choices = f"{choices}{selectedChoice[choice]}"
    if choices.endswith("_"):
        choices = choices[:-1]
    choices = f"{choices}{'_i' if isIntraday else ''}"
    return choices


def showOptionErrorMessage():
    print(
        colorText.BOLD
        + colorText.FAIL
        + "\n[+] Please enter a valid option & try Again!"
        + colorText.END
    )
    sleep(2)
    Utility.tools.clearScreen()


def shutdown(frame, signum):
    # your app's shutdown or whatever
    print("Shutting down for test coverage")


def startWorkers(consumers):
    try:
        from pytest_cov.embed import cleanup_on_signal, cleanup_on_sigterm
    except ImportError:
        pass
    else:
        if sys.platform.startswith("win"):
            import signal

            cleanup_on_signal(signal.SIGBREAK)
        else:
            cleanup_on_sigterm()
    print(
        colorText.BOLD
        + colorText.FAIL
        + f"[+] Using Period:{configManager.period} and Duration:{configManager.duration} for scan! You can change this in user config."
        + colorText.END
    )
    for worker in consumers:
        worker.daemon = True
        worker.start()


def takeBacktestInputs(
    menuOption=None, tickerOption=None, executeOption=None, backtestPeriod=0
):
    g10k = '"Growth of 10k"'
    print(
        colorText.BOLD
        + colorText.GREEN
        + f"[+] For {g10k if menuOption == 'G' else 'backtesting'}, you can choose from (1,2,3,4,5,10,15,22,30) periods."
    )
    try:
        if backtestPeriod == 0:
            backtestPeriod = int(
                input(
                    colorText.BOLD
                    + colorText.FAIL
                    + f"[+] Enter {g10k if menuOption == 'G' else 'backtesting'} period (Default is {3 if menuOption == 'G' else 30} [days]): "
                )
            )
    except Exception as e:  # pragma: no cover
        default_logger().debug(e, exc_info=True)
    if backtestPeriod == 0:
        backtestPeriod = 3 if menuOption == "G" else 30
    tickerOption, executeOption = initPostLevel0Execution(
        menuOption=menuOption,
        tickerOption=tickerOption,
        executeOption=executeOption,
        skip=["N", "E"],
    )
    tickerOption, executeOption = initPostLevel1Execution(
        tickerOption=tickerOption,
        executeOption=executeOption,
        skip=[
            "0",
            "26",
            "27",
            "28",
            "29" "42",
        ],
    )
    return tickerOption, executeOption, backtestPeriod


def terminateAllWorkers(consumers, tasks_queue, testing):
    # Exit all processes. Without this, it threw error in next screening session
    for worker in consumers:
        try:
            if testing:
                if sys.platform.startswith("win"):
                    import signal

                    signal.signal(signal.SIGBREAK, shutdown)
                    sleep(1)
                # worker.join()  # necessary so that the Process exists before the test suite exits (thus coverage is collected)
            # else:
            worker.terminate()
        except OSError as e:
            default_logger().debug(e, exc_info=True)
            if e.winerror == 5:
                continue

    # Flush the queue so depending processes will end
    while True:
        try:
            _ = tasks_queue.get(False)
        except Exception as e:  # pragma: no cover
            break


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
