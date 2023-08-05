#!/usr/bin/python3

# Keep module imports prior to classes
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import sys
import logging
# import dataframe_image as dfi
# import df2img

import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes import VERSION
from pkscreener.classes.log import default_logger, tracelog
import pkscreener.classes.Screener as Screener
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes.MenuOptions import menu, menus, level0MenuDict, level1_X_MenuDict, level2_X_MenuDict, level3_X_Reversal_MenuDict, level3_X_ChartPattern_MenuDict
from pkscreener.classes.ParallelProcessing import StockConsumer
from pkscreener.classes.Utility import level3ReversalMenuDict, level3ChartPatternMenuDict
# import classes.Archiver as Archiver

from alive_progress import alive_bar
import urllib
import numpy as np
import pandas as pd
from datetime import datetime
import pkscreener.classes.PortfolioTracker as tracker
from pkscreener.classes.Backtest import backtest
from time import sleep
from tabulate import tabulate
from pkscreener.Telegram import send_message, send_photo, send_document, is_token_telegram_configured
import multiprocessing
multiprocessing.freeze_support()

# Try Fixing bug with this symbol
TEST_STKCODE = "SBIN"

# Constants
np.seterr(divide='ignore', invalid='ignore')

# Global Variabls
menuChoiceHierarchy = ''
defaultAnswer = None
screenCounter = None
screenResults = None
screenResultsCounter = None
stockDict = None
keyboardInterruptEvent = None
loadedStockData = False
loadCount = 0
maLength = None
newlyListedOnly = False

configManager = ConfigManager.tools()
fetcher = Fetcher.tools(configManager)
screener = Screener.tools(configManager, default_logger())
candlePatterns = CandlePatterns()

selectedChoice = {'0':'', '1':'','2':'','3':'','4':''}
m0 = menus()
m1 = menus()
m2 = menus()

def initExecution(menuOption=None):
    global selectedChoice
    Utility.tools.clearScreen()
    
    m0.renderForMenu(selectedMenu=None)
    try:
        if menuOption == None:
            menuOption = input(
                colorText.BOLD + colorText.FAIL + '[+] Select option: ')
            print(colorText.END, end='')
        if menuOption == '':
            menuOption = 'X'
        menuOption = menuOption.upper()
        selectedMenu = m0.find(menuOption)
        if selectedMenu is not None:
            if selectedMenu.menuKey == 'Z':
                input(colorText.BOLD + colorText.FAIL +
                    "[+] Press any key to Exit!" + colorText.END)
                sys.exit(0)
            elif selectedMenu.menuKey in ['B','H','U','T','S','E','X','Y']:
                Utility.tools.clearScreen()
                selectedChoice['0'] = selectedMenu.menuKey
                return selectedMenu
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        showOptionErrorMessage()
        return initExecution()
    
    showOptionErrorMessage()
    return initExecution()

def showOptionErrorMessage():
    print(colorText.BOLD + colorText.FAIL +
              '\n[+] Please enter a valid option & try Again!' + colorText.END)
    sleep(2)
    Utility.tools.clearScreen()

def toggleUserConfig():
    configManager.toggleConfig()
    print(colorText.BOLD + colorText.GREEN +
    '\nConfiguration toggled to duration: ' + str(configManager.duration) + ' and period: ' + str(configManager.period) + colorText.END)
    input('\nPress any key to Continue...\n')

# Manage Execution flow
def initPostLevel0Execution(menuOption=None, tickerOption=None, executeOption=None, skip=[]):
    global newlyListedOnly, selectedChoice
    Utility.tools.clearScreen()
    if menuOption is None:
        print('You must choose an option from the previous menu! Defaulting to "X"...')
        menuOption = 'X'
    print(colorText.BOLD + colorText.FAIL + '[+] You chose: ' + level0MenuDict[selectedChoice['0']].strip() + ' > ' + colorText.END)
    if tickerOption is None:
        selectedMenu = m0.find(menuOption)
        m1.renderForMenu(selectedMenu=selectedMenu, skip=skip)
    try:
        if tickerOption is None:
            tickerOption = input(
                colorText.BOLD + colorText.FAIL + '[+] Select option: ')
            print(colorText.END, end='')
        if tickerOption == '' or tickerOption is None:
            tickerOption = 12
        # elif tickerOption == 'W' or tickerOption == 'w' or tickerOption == 'N' or tickerOption == 'n' or tickerOption == 'E' or tickerOption == 'e':
        elif not str(tickerOption).isnumeric():
            tickerOption = tickerOption.upper()
            if tickerOption in ['M','E','N','Z']:
                return tickerOption, 0
        else:
            tickerOption = int(tickerOption)
            if(tickerOption < 0 or tickerOption > 14):
                raise ValueError
            elif tickerOption == 13:
                newlyListedOnly = True
                tickerOption = 12
        selectedChoice['1'] = str(tickerOption)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        print(colorText.BOLD + colorText.FAIL +
              '\n[+] Please enter a valid numeric option & Try Again!' + colorText.END)
        sleep(2)
        Utility.tools.clearScreen()
        return initPostLevel0Execution()
    return tickerOption, executeOption

def initPostLevel1Execution(tickerOption, executeOption=None, skip=[]):
    global selectedChoice
    if executeOption is None:
        if tickerOption is not None and tickerOption != 'W':
            Utility.tools.clearScreen()
            print(colorText.BOLD + colorText.FAIL + '[+] You chose: ' + level0MenuDict[selectedChoice['0']].strip() + ' > ' + level1_X_MenuDict[selectedChoice['1']].strip() + colorText.END)
            selectedMenu = m1.find(tickerOption)
            m2.renderForMenu(selectedMenu=selectedMenu,skip=skip)
    try:
        if tickerOption is not None and tickerOption != 'W':
            if executeOption is None:
                executeOption = input(
                    colorText.BOLD + colorText.FAIL + '[+] Select option: ')
                print(colorText.END, end='')
            if executeOption == '':
                executeOption = 1
            if not str(executeOption).isnumeric():
                executeOption = executeOption.upper()
            else:
                executeOption = int(executeOption)
                if(executeOption < 0 or executeOption > 44):
                    raise ValueError
        else:
            executeOption = 0
        selectedChoice['2'] = str(executeOption)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        print(colorText.BOLD + colorText.FAIL +
              '\n[+] Please enter a valid numeric option & Try Again!' + colorText.END)
        sleep(2)
        Utility.tools.clearScreen()
        return initPostLevel1Execution()
    return tickerOption, executeOption

def initDataframes():
    screenResults = pd.DataFrame(columns=[
                                 'Stock', 'Consol.', 'Breakout', 'LTP','%Chng', 'Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern', 'CCI'])
    saveResults = pd.DataFrame(columns=[
                               'Stock', 'Consol.', 'Breakout', 'LTP','%Chng','Volume', 'MA-Signal', 'RSI', 'Trend', 'Pattern', 'CCI'])
    return screenResults, saveResults

def getTestBuildChoices(tickerOption=None, executeOption=None, menuOption=None):
    if menuOption is not None and tickerOption is not None and executeOption is not None:
        return menuOption, tickerOption, executeOption, {'0':'X','1':str(tickerOption),'2':str(executeOption)}
    return 'X', 1, 0, {'0':'X','1':'1','2':'0'}

def getDownloadChoices():
    exists, cache_file = Utility.tools.afterMarketStockDataExists()
    if exists:
        shouldReplace = Utility.tools.promptFileExists(cache_file=cache_file, defaultAnswer=defaultAnswer)
        if shouldReplace == 'N':
            print(cache_file + colorText.END + ' already exists. Exiting as user chose not to replace it!')
            sys.exit(0)
        else:
            configManager.deleteFileWithPattern()
    return 'X', 12, 2, {'0':'X','1':'12','2':'2'}
    
def handleSecondaryMenuChoices(menuOption, testing=False,defaultAnswer=None,user=None):
    if menuOption == 'H':
        helpData = Utility.tools.showDevInfo(defaultAnswer=defaultAnswer)
        if user is not None:
            sendMessageToTelegramChannel(message=Utility.tools.removeAllColorStyles(helpData),user=user)
            return
    elif menuOption == 'U':
        OTAUpdater.checkForUpdate(getProxyServer(), VERSION, skipDownload=testing)
    elif menuOption == 'T':
        toggleUserConfig()
    elif menuOption == 'E':
        configManager.setConfig(ConfigManager.parser)
    elif menuOption == 'Y':
        configData = configManager.showConfigFile(defaultAnswer=defaultAnswer)
        if user is not None:
            sendMessageToTelegramChannel(message=Utility.tools.removeAllColorStyles(configData),user=user)
            return
    # main()
    return

def getTopLevelMenuChoices(startupoptions, testBuild, downloadOnly):
    global selectedChoice
    executeOption = None
    menuOption = None
    tickerOption = None
    options =[]
    if startupoptions is not None:
        options = startupoptions.split(':')
        menuOption = options[0] if len(options) >= 1 else None
        tickerOption = options[1] if len(options) >= 2 else None
        executeOption = options[2] if len(options) >= 3 else None
    if testBuild:
        menuOption, tickerOption, executeOption, selectedChoice = getTestBuildChoices(tickerOption=tickerOption, executeOption=executeOption, menuOption=menuOption)
    elif downloadOnly:
        menuOption, tickerOption, executeOption, selectedChoice = getDownloadChoices()
    return options, menuOption, tickerOption, executeOption

def getScannerMenuChoices(testBuild=False,downloadOnly=False,startupoptions=None, menuOption=None, tickerOption=None, executeOption=None,defaultAnswer=None,user=None):
    global selectedChoice
    executeOption = executeOption
    menuOption = menuOption
    tickerOption = tickerOption
    try:
        if menuOption is None:
            selectedMenu = initExecution(menuOption=menuOption)
            menuOption = selectedMenu.menuKey
        if menuOption in ['H','U','T','E','Y']:
            handleSecondaryMenuChoices(menuOption, testBuild,defaultAnswer=defaultAnswer,user=user)
        elif menuOption == 'X':
            tickerOption, executeOption = initPostLevel0Execution(menuOption=menuOption,tickerOption=tickerOption, executeOption=executeOption)
            tickerOption, executeOption = initPostLevel1Execution(tickerOption=tickerOption, executeOption=executeOption)
    except KeyboardInterrupt:
        input(colorText.BOLD + colorText.FAIL +
            "[+] Press any key to Exit!" + colorText.END)
        sys.exit(0)
    return menuOption, tickerOption, executeOption, selectedChoice

def handleScannerExecuteOption4(executeOption,options):
    try:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            daysForLowestVolume = int(options[3])
        else:
            daysForLowestVolume = int(input(colorText.BOLD + colorText.WARN +
                                        '\n[+] The Volume should be lowest since last how many candles? '))
    except ValueError as e:
        default_logger().debug(e, exc_info=True)
        print(colorText.END)
        print(colorText.BOLD + colorText.FAIL +
                '[+] Error: Non-numeric value entered! Screening aborted.' + colorText.END)
        input('')
        main()
        return
    print(colorText.END)
    return daysForLowestVolume

# Main function
@tracelog
def main(testing=False, testBuild=False, downloadOnly=False, startupoptions=None, defaultConsoleAnswer=None, user=None):
    global screenResults, selectedChoice, defaultAnswer, menuChoiceHierarchy, screenCounter, screenResultsCounter, stockDict, loadedStockData, keyboardInterruptEvent, loadCount, maLength, newlyListedOnly
    defaultAnswer = defaultConsoleAnswer
    options = []
    screenCounter = multiprocessing.Value('i', 1)
    screenResultsCounter = multiprocessing.Value('i', 0)
    keyboardInterruptEvent = multiprocessing.Manager().Event()

    if stockDict is None:
        stockDict = multiprocessing.Manager().dict()
        loadCount = 0

    minRSI = 0
    maxRSI = 100
    insideBarToLookback = 7
    respChartPattern = 1
    daysForLowestVolume = 30
    backtestPeriod= 0
    reversalOption = None
    listStockCodes = None
    screenResults, saveResults = initDataframes()
    options, menuOption, tickerOption, executeOption = getTopLevelMenuChoices(startupoptions, testBuild, downloadOnly) 
    # Print Level 1 menu options
    selectedMenu = initExecution(menuOption=menuOption)
    menuOption = selectedMenu.menuKey
    if menuOption in ['X','T','E','Y','U','H']:
        # Print Level 2 menu options
        menuOption, tickerOption, executeOption, selectedChoice = getScannerMenuChoices(
            testBuild or testing,downloadOnly,startupoptions, menuOption=menuOption, 
            tickerOption=tickerOption, executeOption=executeOption,defaultAnswer=defaultAnswer,user=user)
        if menuOption in ['H','U','T','E','Y']:
            return
    elif menuOption == 'B':
        # Backtests
        tickerOption, executeOption, backtestPeriod = takeBacktestInputs(menuOption,tickerOption, executeOption)
    else:
        print('Work in progress! Try selecting a different option.')
        sleep(3)
        main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
        return

    if tickerOption == 'M' or executeOption == 'M':
        main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
        return
    if tickerOption == 0:
        if len(options) >= 4:
            listStockCodes = str(options[3]).split(',')
    if executeOption == 'Z':
        input(colorText.BOLD + colorText.FAIL +
              "[+] Press any key to Exit!" + colorText.END)
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
            minRSI = int(options[3])
            maxRSI = int(options[4])
        else:
            minRSI, maxRSI = Utility.tools.promptRSIValues()
        if (not minRSI and not maxRSI):
            print(colorText.BOLD + colorText.FAIL +
                  '\n[+] Error: Invalid values for RSI! Values should be in range of 0 to 100. Screening aborted.' + colorText.END)
            input('')
            main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
            return
    if executeOption == 6:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            reversalOption = int(options[3])
            if reversalOption == 4 or reversalOption == 6:
                if len(options) >= 5:
                    maLength = int(options[4])
                else:
                    reversalOption, maLength = Utility.tools.promptReversalScreening(selectedMenu)
        else:
            reversalOption, maLength = Utility.tools.promptReversalScreening(selectedMenu)
        if reversalOption is None or reversalOption == 0:
            main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
            return
        else:
            selectedChoice['3'] = str(reversalOption)
    if executeOption == 7:
        selectedMenu = m2.find(str(executeOption))
        if len(options) >= 4:
            respChartPattern = int(options[3])
            selectedChoice['3'] = options[3]
            if respChartPattern in [1,2,3]:
                if len(options) >= 5:
                    insideBarToLookback = int(options[4])
                else:
                    respChartPattern, insideBarToLookback = Utility.tools.promptChartPatterns(selectedMenu)
            elif respChartPattern in [0,4,5]:
                insideBarToLookback = 0
            else:
                respChartPattern, insideBarToLookback = Utility.tools.promptChartPatterns(selectedMenu)
        if respChartPattern is None or insideBarToLookback is None:
            main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
            return
        else:
            selectedChoice['3'] = str(respChartPattern)
    if executeOption == 8:
        if len(options) >= 5:
            minRSI = int(options[3])
            maxRSI = int(options[4])
        else:
            minRSI, maxRSI = Utility.tools.promptCCIValues()
        if (not minRSI and not maxRSI):
            print(colorText.BOLD + colorText.FAIL +
                  '\n[+] Error: Invalid values for CCI! Values should be in range of -300 to 500. Screening aborted.' + colorText.END)
            input('')
            main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
            return
    if executeOption == 9:
        if len(options) >= 4:
            volumeRatio = float(options[3])
        else:
            volumeRatio = Utility.tools.promptVolumeMultiplier()
        if (volumeRatio <= 0):
            print(colorText.BOLD + colorText.FAIL +
                  '\n[+] Error: Invalid values for Volume Ratio! Value should be a positive number. Screening aborted.' + colorText.END)
            input('')
            main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
            return
        else:
            configManager.volumeRatio = float(volumeRatio)
    if executeOption == 42:
        Utility.tools.getLastScreenedResults()
        main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
        return
    if executeOption >= 15 and executeOption <= 39:
        print(colorText.BOLD + colorText.FAIL + '\n[+] Error: Option 15 to 39 Not implemented yet! Press any key to continue.' + colorText.END) 
        input('')
        main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
             startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
             user=user)
        return
    if (not str(tickerOption).isnumeric() and tickerOption in ['W','E','M','N','Z']) or (str(tickerOption).isnumeric() and (int(tickerOption) >= 0 and int(tickerOption) < 15)):
        configManager.getConfig(ConfigManager.parser)
        try:
            if tickerOption == 'W':
                listStockCodes = fetcher.fetchWatchlist()
                if listStockCodes is None:
                    input(colorText.BOLD + colorText.FAIL +
                          f'[+] Create the watchlist.xlsx file in {os.getcwd()} and Restart the Program!' + colorText.END)
                    sys.exit(0)
            elif tickerOption == 'N':
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
                prediction, pText, sText = screener.getNiftyPrediction(
                    data=fetcher.fetchLatestNiftyDaily(proxyServer=proxyServer), 
                    proxyServer=proxyServer
                )
                sendMessageToTelegramChannel(message=f'Nifty AI prediction for the next day: {pText}. {sText}',user=user)
                if defaultAnswer is None:
                    input('\nPress any key to Continue...\n')
                return
            elif tickerOption == 'M':
                main(testing=testing, testBuild=testBuild, downloadOnly=downloadOnly,
                    startupoptions=startupoptions,defaultConsoleAnswer=defaultConsoleAnswer,
                    user=user)
                return
            elif tickerOption == 'Z':
                input(colorText.BOLD + colorText.FAIL + "[+] Press any key to Exit!" + colorText.END)
                sys.exit(0)
            elif tickerOption == 'E':
                result_df = pd.DataFrame(columns=['Time','Stock/Index','Action','SL','Target','R:R'])
                last_signal = {}
                first_scan = True
                result_df = screener.monitorFiveEma(        # Dummy scan to avoid blank table on 1st scan
                        proxyServer=proxyServer,
                        fetcher=fetcher,
                        result_df=result_df,
                        last_signal=last_signal
                    )
                try:
                    while True:
                        Utility.tools.clearScreen()
                        last_result_len = len(result_df)
                        result_df = screener.monitorFiveEma(
                            proxyServer=proxyServer,
                            fetcher=fetcher,
                            result_df=result_df,
                            last_signal=last_signal
                        )
                        print(colorText.BOLD + colorText.WARN + '[+] 5-EMA : Live Intraday Scanner \t' + colorText.END + colorText.FAIL + f'Last Scanned: {datetime.now().strftime("%H:%M:%S")}\n' + colorText.END)
                        print(tabulate(result_df, headers='keys', tablefmt='psql'))
                        print('\nPress Ctrl+C to exit.')
                        if len(result_df) != last_result_len and not first_scan:
                            Utility.tools.alertSound(beeps=5)
                        sleep(60)
                        first_scan = False
                except KeyboardInterrupt:
                    input('\nPress any key to Continue...\n')
                    return
            else:
                if not downloadOnly:
                    menuChoiceHierarchy = f'{level0MenuDict[selectedChoice["0"]].strip()}>{level1_X_MenuDict[selectedChoice["1"]].strip()}>{level2_X_MenuDict[selectedChoice["2"]].strip()}'
                    if selectedChoice['2'] == '6':
                        menuChoiceHierarchy = menuChoiceHierarchy + f'>{level3ReversalMenuDict[selectedChoice["3"]].strip()}'
                    elif selectedChoice['2'] == '7':
                        menuChoiceHierarchy = menuChoiceHierarchy + f'>{level3ChartPatternMenuDict[selectedChoice["3"]].strip()}'
                    print(colorText.BOLD + colorText.FAIL + '[+] You chose: ' + menuChoiceHierarchy + colorText.END)
                    default_logger().info(menuChoiceHierarchy)
                if listStockCodes is None or len(listStockCodes) == 0:
                    if not testing:
                        listStockCodes = fetcher.fetchStockCodes(tickerOption, proxyServer=proxyServer, stockCode=None)
                    else:
                        listStockCodes = [TEST_STKCODE]
                if tickerOption == 0:
                    selectedChoice['3']='.'.join(listStockCodes)
                if testing:
                    import random
                    listStockCodes = [random.choice(listStockCodes)]

        except urllib.error.URLError as e:
            default_logger().debug(e, exc_info=True)
            print(colorText.BOLD + colorText.FAIL +
                  "\n\n[+] Oops! It looks like you don't have an Internet connectivity at the moment! Press any key to exit!" + colorText.END)
            input('')
            sys.exit(0)

        if menuOption =='X' and not downloadOnly and not Utility.tools.isTradingTime() and configManager.cacheEnabled and not loadedStockData and not testing:
            dfsd = None #Archiver.readData(f'SD_{Utility.tools.tradingDate()}_{selectedChoice["0"]}_{selectedChoice["1"]}_{selectedChoice["2"]}_{selectedChoice["3"]}.pkl')
            dfsc = None #Archiver.readData(f'SC_{Utility.tools.tradingDate()}_{selectedChoice["0"]}_{selectedChoice["1"]}_{selectedChoice["2"]}_{selectedChoice["3"]}.pkl')
            if dfsc is not None and dfsd is not None:
                print(colorText.BOLD + colorText.WARN +
                      '[+] Found local results already saved in cache for selected option!\n')
                printNotifySaveScreenedResults(dfsc,dfsd,selectedChoice,menuChoiceHierarchy,testing,user=user)
                finishScreening(downloadOnly, testing, stockDict, configManager, 
                        len(screenResults), testBuild, screenResults, saveResults,user)
                return
            else:
                print(colorText.BOLD + colorText.WARN +
                      '[+] No local results cache for selected option! Will screen afresh...\n')
            Utility.tools.loadStockData(stockDict, configManager, proxyServer, downloadOnly=downloadOnly, defaultAnswer=defaultAnswer)
            loadedStockData = True
        loadCount = len(stockDict)

        if not downloadOnly:
            print(colorText.BOLD + colorText.WARN +
                f"[+] Starting Stock {'Screening' if menuOption=='X' else 'Backtesting.'}. Press Ctrl+C to stop!\n")
        else:
            print(colorText.BOLD + colorText.WARN +
                "[+] Starting download.. Press Ctrl+C to stop!\n")

        iterations = getIterationCount(len(listStockCodes)) if menuOption.upper() == 'B' else 1
        sampleDays = ((iterations + backtestPeriod + 1) if menuOption == 'B' else 2)
        iteration = 1 if menuOption == 'B' else 2
        backtest_df = None
        if menuOption.upper() == 'B':
            print(colorText.BOLD + colorText.WARN +
                f"[+] A total of {iterations} iterations are planned.\n")
        items = []
        historicalDays = sampleDays - iteration
        while historicalDays >= 0:
            moreItems = [(executeOption, reversalOption, maLength, daysForLowestVolume, minRSI, maxRSI, respChartPattern, insideBarToLookback, len(listStockCodes),
                    configManager, fetcher, screener, candlePatterns, stock, newlyListedOnly, downloadOnly, volumeRatio, testBuild, testBuild,historicalDays, default_logger().level)
                    for stock in listStockCodes]
            items.extend(moreItems)
            iteration = iteration + 1
            historicalDays = sampleDays - iteration
        tasks_queue, results_queue, totalConsumers = initQueues()
        consumers = [StockConsumer(tasks_queue, results_queue, screenCounter, screenResultsCounter, stockDict, proxyServer, keyboardInterruptEvent, default_logger())
                    for _ in range(totalConsumers)]
        startWorkers(consumers)
        if testing or testBuild:
            screenResults, saveResults = runTests(items,tasks_queue,results_queue,screenResults,saveResults)
        else:
            screenResults, saveResults,backtest_df = runScanners(menuOption,items,tasks_queue,results_queue,
                                                    listStockCodes,backtestPeriod,sampleDays-1, consumers,screenResults,
                                                    saveResults,backtest_df)
        
        print(colorText.END)
        terminateAllWorkers(consumers, tasks_queue)
        if not downloadOnly and menuOption=='X':
            screenResults, saveResults = labelDataForPrinting(screenResults,saveResults,configManager, volumeRatio)
            screenResults, saveResults = removeUnknowns(screenResults, saveResults)
            # Archiver.saveData(saveResults, f'SD_{Utility.tools.tradingDate()}_{selectedChoice["0"]}_{selectedChoice["1"]}_{selectedChoice["2"]}_{selectedChoice["3"]}.pkl')
            # Archiver.saveData(screenResults, f'SC_{Utility.tools.tradingDate()}_{selectedChoice["0"]}_{selectedChoice["1"]}_{selectedChoice["2"]}_{selectedChoice["3"]}.pkl')
            printNotifySaveScreenedResults(screenResults,saveResults,selectedChoice,menuChoiceHierarchy,testing,user=user)
        if menuOption=='X':
            finishScreening(downloadOnly, testing, stockDict, configManager, 
                        loadCount, testBuild, screenResults, saveResults,user)

        if menuOption == 'B' and backtest_df is not None and len(backtest_df) > 0:
                backtest_df.set_index('Stock', inplace=True)
                showBacktestResults(backtest_df)
                sorting = False if defaultAnswer == 'Y' else True
                sortKeys ={'S':'Stock','D': 'Base-Date','1':'1-Pd','2':'2-Pd','3':'3-Pd','4':'4-Pd',
                           '5':'5-Pd','10':'10-Pd','15':'15-Pd','22':'22-Pd','30':'30-Pd','T':'Trend',
                           'V':'Volume','M':'MA-Signal'}
                while sorting:
                    print(colorText.BOLD + colorText.FAIL +
                        f"[+] Would you like to sort the results?" + colorText.END)
                    print(colorText.BOLD + colorText.GREEN + "[+] Press :\n [+] s, v, t, m : sort by Stocks, Volume, Trend, MA-Signal\n [+] d : sort by date\n [+] 1,2,3...30 : sort by period\n [+] n : Exit sorting\n" + colorText.END)
                    if defaultAnswer != 'Y':
                        choice = input(colorText.BOLD + colorText.FAIL + "[+] Select option:")
                        print(colorText.END, end='')
                        if choice.upper() in sortKeys.keys():
                            showBacktestResults(backtest_df, sortKeys[choice.upper()])
                        else:
                            sorting = False
                    else:
                        print('Finished backtesting!')
                        sorting = False
                if defaultAnswer != 'Y':
                    input('Press any key to return to the main menu...')
        elif menuOption == 'B':
            print('Finished backtesting with no results to show!')
        newlyListedOnly = False

def color_negative_red(val):
    color = 'red' if str(val).startswith('-') else 'green'
    return 'color: %s' % color

def showBacktestResults(backtest_df, sortKey='Base-Date'):
    Utility.tools.clearScreen()
    pd.set_option("display.max_rows", 300)
    # pd.set_option("display.max_columns", 20)
    backtest_df = backtest_df.drop_duplicates()
    backtest_df.sort_values(by=[sortKey], ascending=False, inplace=True)
    tabulated_text = tabulate(backtest_df, headers='keys', tablefmt='grid')
    print(tabulated_text)
    print('\n')
    filename = 'PKScreener-backtest_result_' + \
                Utility.tools.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")+".html"
    with open(filename, 'a') as f:
        f.write(tabulated_text)
    configManager.deleteFileWithPattern(pattern='PKScreener-backtest_result_*.html', excludeFile=filename)

def getIterationCount(numStocks):
    # Generally it takes 50-60 seconds for one full run of backtest for a batch of 1900
    # stocks. We would like the backtest to finish with 3-5 minutes.
    # iterations = (1900/numStocks) * 3.5
    return 240 #(5 if iterations < 5 else (100 if iterations > 100 else iterations))

def runScanners(menuOption,items,tasks_queue,results_queue,listStockCodes,backtestPeriod,iterations,consumers,screenResults,saveResults,backtest_df):
    populateQueues(items,tasks_queue)
    try:
        numStocks = len(listStockCodes) * iterations
        dumpFreq = 1
        print(colorText.END+colorText.BOLD)
        bar, spinner = Utility.tools.getProgressbarStyle()
        with alive_bar(numStocks, bar=bar, spinner=spinner) as progressbar:
            lstscreen = []
            lstsave = []
            lstFullData = []
            stocks = []
            while numStocks:
                result = results_queue.get()
                if result is not None:
                    lstscreen.append(result[0])
                    lstsave.append(result[1])
                    lstFullData.append(result[2])
                    stocks.append(result[3])
                    sampleDays = result[4]
                    # Backtest for results
                    if menuOption == 'B':
                        backtest_df = backtest(result[3], result[2],result[0],backtestPeriod,sampleDays,backtest_df)
                        if screenResultsCounter.value >= 50*dumpFreq:
                            # Dump results on the screen and into a file every 50 results
                            showBacktestResults(backtest_df)
                            dumpFreq = dumpFreq + 1
                numStocks -= 1
                progressbar.text(colorText.BOLD + colorText.GREEN +
                                    f'Found {screenResultsCounter.value} Stocks' + colorText.END)
                progressbar()
                # default_logger().flush()
        
        if menuOption == 'X':
            # create extension
            df_extendedscreen = pd.DataFrame(lstscreen, columns=screenResults.columns)
            df_extendedsave = pd.DataFrame(lstsave, columns=saveResults.columns)
            screenResults = pd.concat([screenResults, df_extendedscreen])
            saveResults = pd.concat([saveResults, df_extendedsave])
    except KeyboardInterrupt:
        try:
            keyboardInterruptEvent.set()
        except KeyboardInterrupt:
            pass
        print(colorText.BOLD + colorText.FAIL +
                "\n[+] Terminating Script, Please wait..." + colorText.END)
        for worker in consumers:
            worker.terminate()
        logging.shutdown()
    return screenResults, saveResults,backtest_df

def takeBacktestInputs(menuOption=None,tickerOption=None,executeOption=None,backtestPeriod=0):
    print(colorText.BOLD + colorText.GREEN +
                                      "[+] For backtesting, you can choose from (1,2,3,4,5,10,15,22,30) periods.")
    backtestPeriod = 0
    try:
        backtestPeriod = int(input(colorText.BOLD + colorText.FAIL +
                                    "[+] Enter backtesting period (Default is 30 [days]): "))
    except:
        pass
    if backtestPeriod == 0:
        backtestPeriod = 30
    tickerOption, executeOption = initPostLevel0Execution(menuOption=menuOption,
                                                            tickerOption=tickerOption,
                                                            executeOption=executeOption,
                                                            skip=['N', 'E'])
    tickerOption, executeOption = initPostLevel1Execution(tickerOption=tickerOption,
                                                            skip=['0','15','16','17','18','19','20','21','22','23','24','25','26','42'])
    return tickerOption, executeOption, backtestPeriod

def populateQueues(items,tasks_queue):
    for item in items:
        tasks_queue.put(item)
    # Append exit signal for each process indicated by None
    for _ in range(multiprocessing.cpu_count()):
        tasks_queue.put(None)

def runTests(items,tasks_queue,results_queue,screenResults,saveResults):
    testCounter = 0
    for item in items:
        testCounter = testCounter + 1
        tasks_queue.put(item)
        result = results_queue.get()
        lstscreen = []
        lstsave = []
        lstFullData = []
        stocks = []
        default_logger().info(f'Fetched results:\n{result}')
        if result is not None:
            lstscreen.append(result[0])
            lstsave.append(result[1])
            lstFullData.append(result[2])
            stocks.append(result[3])
            df_extendedscreen = pd.DataFrame(lstscreen, columns=screenResults.columns)
            df_extendedsave = pd.DataFrame(lstsave, columns=saveResults.columns)
            screenResults = pd.concat([screenResults, df_extendedscreen])
            saveResults = pd.concat([saveResults, df_extendedsave])
        if len(screenResults) >= 2 or testCounter >= 5:
            break
    # backtest(lstFullData[0],'Momentum',30)
    # input()
    return screenResults, saveResults

def startWorkers(consumers):
    for worker in consumers:
        worker.daemon = True
        worker.start()

def initQueues():
    tasks_queue = multiprocessing.JoinableQueue()
    results_queue = multiprocessing.Queue()

    totalConsumers = multiprocessing.cpu_count()
    if totalConsumers == 1:
        totalConsumers = 2      # This is required for single core machine
    if configManager.cacheEnabled is True and multiprocessing.cpu_count() > 2:
        totalConsumers -= 1
    return tasks_queue, results_queue, totalConsumers

def terminateAllWorkers(consumers, tasks_queue):
    # Exit all processes. Without this, it threw error in next screening session
    for worker in consumers:
        try:
            worker.terminate()
        except OSError as e:
            default_logger().debug(e, exc_info=True)
            if e.winerror == 5:
                pass

    # Flush the queue so depending processes will end
    from queue import Empty
    while True:
        try:
            _ = tasks_queue.get(False)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            break

def finishScreening(downloadOnly, testing, stockDict, configManager, loadCount, testBuild, screenResults, saveResults,user=None):
    global defaultAnswer, menuChoiceHierarchy
    saveDownloadedData(downloadOnly, testing, stockDict, configManager, loadCount)
    if not testBuild and not downloadOnly and not testing:
        saveNotifyResultsFile(screenResults, saveResults, defaultAnswer,menuChoiceHierarchy,user=user)
    # elif testing:
    #     sendTestStatus(screenResults, menuChoiceHierarchy,user=user)
    
def labelDataForPrinting(screenResults,saveResults,configManager,volumeRatio):
    # Publish to gSheet with https://github.com/burnash/gspread 
    try:
        screenResults.sort_values(by=['Volume'], ascending=False, inplace=True)
        saveResults.sort_values(by=['Volume'], ascending=False, inplace=True)
        screenResults.set_index('Stock', inplace=True)
        saveResults.set_index('Stock', inplace=True)
        screenResults.loc[:,'Volume'] = screenResults.loc[:,'Volume'].apply(lambda x: Utility.tools.formatRatio(x, volumeRatio))
        saveResults.loc[:,'Volume'] = saveResults.loc[:,'Volume'].apply(lambda x: str(x)+"x")
        screenResults.rename(
            columns={
                'Trend': f'Trend({configManager.daysToLookback}Prds)',
                'Breakout': f'Breakout ({configManager.daysToLookback}Prds)',
                'Consol.': f'Consol.({configManager.daysToLookback}Prds)',
            },
            inplace=True
        )
        saveResults.rename(
            columns={
                'Trend': f'Trend({configManager.daysToLookback}Prds)',
                'Breakout': f'Breakout ({configManager.daysToLookback}Prds)',
                'Consol.': f'Consol.({configManager.daysToLookback}Prds)',
            },
            inplace=True
        )
    except:
        pass
    return screenResults, saveResults

def printNotifySaveScreenedResults(screenResults,saveResults,selectedChoice,menuChoiceHierarchy,testing,user=None):
    Utility.tools.clearScreen()
    print(colorText.BOLD + colorText.FAIL + f'[+] You chose: {menuChoiceHierarchy}\n' + colorText.END)
    tabulated_results = tabulate(screenResults, headers='keys', tablefmt='grid')
    print(tabulated_results)
    caption = f'<b>{menuChoiceHierarchy.split(">")[-1]}</b>'
    if len(screenResults) >= 1:
        if not testing:
            if len(screenResults) <= 100:
                # No point sending a photo with more than 100 stocks.
                caption = f'<b>({len(saveResults)}</b> stocks found).{caption}'
                markdown_results = tabulate(saveResults, headers='keys', tablefmt='grid')
                pngName = f'PKS_{"_".join(selectedChoice.values())}{Utility.tools.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")+".png"}'
                if is_token_telegram_configured():
                    Utility.tools.tableToImage(markdown_results,tabulated_results,pngName,menuChoiceHierarchy)
                    sendMessageToTelegramChannel(message=None, photo_filePath=pngName, caption=caption, user=user)
                    try:
                        os.remove(pngName)
                    except Exception as e:
                        default_logger().debug(e, exc_info=True)
                        pass
            print(colorText.BOLD + colorText.GREEN +
                    f"[+] Found {len(screenResults)} Stocks." + colorText.END)
            Utility.tools.setLastScreenedResults(screenResults)
    elif user is not None:
        sendMessageToTelegramChannel(message=f'No scan results found for {menuChoiceHierarchy}', user=user)

def saveDownloadedData(downloadOnly, testing, stockDict, configManager, loadCount):
    if downloadOnly or (configManager.cacheEnabled and not Utility.tools.isTradingTime() and not testing):
        print(colorText.BOLD + colorText.GREEN +
                "[+] Caching Stock Data for future use, Please Wait... " + colorText.END, end='')
        Utility.tools.saveStockData(stockDict, configManager, loadCount)
    else:
        print(colorText.BOLD + colorText.GREEN +
                "[+] Skipped Saving!" + colorText.END, end='')

def saveNotifyResultsFile(screenResults, saveResults, defaultAnswer, menuChoiceHierarchy,user=None):
    caption = f'<b>{menuChoiceHierarchy.split(">")[-1]}</b>'
    if len(screenResults) >= 1:
        filename = Utility.tools.promptSaveResults(saveResults, defaultAnswer = defaultAnswer)
        if filename is not None:
            sendMessageToTelegramChannel(document_filePath=filename, caption=caption,user=user)
        print(colorText.BOLD + colorText.WARN +
            "[+] Note: Trend calculation is based on number of days recent to screen as per your configuration." + colorText.END)
        try:
            if filename is not None:
                os.remove(filename)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass
    print(colorText.BOLD + colorText.GREEN +
        "[+] Screening Completed! Press Enter to Continue.." + colorText.END)
    if defaultAnswer is None:
        input('')

def sendTestStatus(screenResults, label,user=None):
    msg = '<b>SUCCESS</b>' if len(screenResults) >= 1 else '<b>FAIL</b>'
    sendMessageToTelegramChannel(message=f'{msg}: Found {len(screenResults)} Stocks for {label}',user=user)

def removeUnknowns(screenResults, saveResults):
    for col in screenResults.keys():
        screenResults = screenResults[screenResults[col].astype(str).str.contains('Unknown') == False]
    for col in saveResults.keys():
        saveResults = saveResults[saveResults[col].astype(str).str.contains('Unknown') == False]
    return screenResults, saveResults

def sendMessageToTelegramChannel(message=None,photo_filePath=None,document_filePath=None, caption=None, user=None):
    if message is not None:
        try:
            send_message(message,userID=user)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass
    if photo_filePath is not None:
        try:
            send_document(photo_filePath, caption,userID=user)
            # Breather for the telegram API to be able to send the heavy photo
            sleep(2)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass
    if document_filePath is not None:
        try:
            send_document(document_filePath, caption,userID=user)
            # Breather for the telegram API to be able to send the document
            sleep(1)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass

def getProxyServer():
    # Get system wide proxy for networking
    try:
        proxyServer = urllib.request.getproxies()['http']
    except KeyError as e:
        default_logger().debug(e, exc_info=True)
        proxyServer = ""
    return proxyServer

proxyServer = getProxyServer()
