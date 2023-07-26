'''
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   28/04/2021
 *  Description         :   Class for managing misc and utility methods
'''
import math
import numpy as np

from decimal import DivisionByZero
from genericpath import isfile
import os
import glob
import sys
import platform
import datetime
import pytz
import pickle
import requests
import time
import joblib
from classes import Imports
from classes.log import default_logger

if Imports['keras']:
    import keras
import warnings
from PIL import Image, ImageDraw, ImageFont, ImageColor
import pandas as pd
from alive_progress import alive_bar
from tabulate import tabulate
from time import sleep
from classes.ColorText import colorText
from classes import VERSION
from classes.Changelog import changelog
import classes.ConfigManager as ConfigManager
from classes.MenuOptions import menus, menu, MenuRenderStyle

artText = '''
    $$$$$$      $$   $$      $$$$$                                                        
    $$    $$    $$  $$      $$   $$                         $$$$       $$$$                  $$$$         
    $$    $$    $$$$$        $$$       $$$$$     $$ $$     $$  $$     $$  $$     $$$$$      $$  $$     $$ $$ 
    $$$$$$      $$  $$         $$$     $$        $$$ $     $$$$$$     $$$$$$     $$  $$     $$$$$$     $$$ $ 
    $$          $$   $$     $$   $$    $$        $$        $$         $$         $$  $$     $$         $$    
    $$          $$   $$      $$$$$     $$$$$     $$        $$$$$      $$$$$      $$  $$     $$$$$      $$    
'''
art = colorText.GREEN + artText + colorText.END

lastScreened = 'last_screened_results.pkl'

# Class for managing misc and utility methods

level3ReversalMenuDict = {'1': 'Buy Signals (Bullish Reversal)',
                          '2':'Sell Signals (Bearish Reversal)',
                          '3': 'Momentum Gainers (Rising Bullish Momentum)',
                          '4': 'Reversal at Moving Average (Bullish Reversal)',
                          '5': 'Volume Spread Analysis (Bullish VSA Reversal)',
                          '6': 'Narrow Range (NRx) Reversal',
                          '0': 'Cancel'
                          }
level3ChartPatternMenuDict = {'1': 'Bullish Inside Bar (Flag) Pattern',
                              '2':'Bearish Inside Bar (Flag) Pattern',
                              '3': 'The Confluence (50 & 200 MA/EMA)',
                              '4': 'VCP (Experimental)',
                              '5': 'Buying at Trendline (Ideal for Swing/Mid/Long term)',
                              '6': 'Narrow Range (NRx) Reversal',
                              '0': 'Cancel'
                              }
class tools:

    def clearScreen():
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
        print(art)

    # Print about developers and repository
    def showDevInfo():
        print('\n'+changelog)
        print(colorText.BOLD + colorText.WARN +
              "\n[+] Developer: PK (PKScreener)" + colorText.END)
        print(colorText.BOLD + colorText.WARN +
              ("[+] Version: %s" % VERSION) + colorText.END)
        print(colorText.BOLD +
              "[+] Home Page: https://github.com/pkjmesra/PKScreener" + colorText.END)
        print(colorText.BOLD + colorText.FAIL +
              "[+] Read/Post Issues here: https://github.com/pkjmesra/PKScreener/issues" + colorText.END)
        print(colorText.BOLD + colorText.GREEN +
              "[+] Join Community Discussions: https://github.com/pkjmesra/PKScreener/discussions" + colorText.END)
        print(colorText.BOLD + colorText.BLUE +
              "[+] Download latest software from https://github.com/pkjmesra/PKScreener/releases/latest" + colorText.END)
        input(colorText.BOLD + colorText.FAIL +
                    "[+] Press any key to continue!" + colorText.END)

    # Save last screened result to pickle file
    def setLastScreenedResults(df):
        try:
            df.sort_values(by=['Stock'], ascending=True, inplace=True)
            df.to_pickle(lastScreened)
        except IOError as e:
            default_logger().debug(e, exc_info=True)
            input(colorText.BOLD + colorText.FAIL +
                  '[+] Failed to save recently screened result table on disk! Skipping..' + colorText.END)

    # Load last screened result to pickle file
    def getLastScreenedResults():
        try:
            df = pd.read_pickle(lastScreened)
            print(colorText.BOLD + colorText.GREEN +
                  '\n[+] Showing recently screened results..\n' + colorText.END)
            print(tabulate(df, headers='keys', tablefmt='psql'))
            print(colorText.BOLD + colorText.WARN +
                  "[+] Note: Trend calculation is based on number of recent days to screen as per your configuration." + colorText.END)
            input(colorText.BOLD + colorText.GREEN +
                  '[+] Press any key to continue..' + colorText.END)
        except FileNotFoundError as e:
            default_logger().debug(e, exc_info=True)
            print(colorText.BOLD + colorText.FAIL +
                  '[+] Failed to load recently screened result table from disk! Skipping..' + colorText.END)

    def formatRatio(ratio, volumeRatio):
        if(ratio >= volumeRatio and ratio != np.nan and (not math.isinf(ratio)) and (ratio != 20)):
            return colorText.BOLD + colorText.GREEN + str(ratio) + "x" + colorText.END
        return colorText.BOLD + colorText.FAIL + str(ratio) + "x" + colorText.END
    
    def getCellColor(cellStyledValue=''):
        otherStyles = [colorText.HEAD, colorText.END, colorText.BOLD, colorText.UNDR]
        mainStyles = [colorText.BLUE, colorText.GREEN, colorText.WARN, colorText.FAIL]
        colorsDict = {colorText.BLUE:'blue', colorText.GREEN:'green',colorText.WARN:'yellow',colorText.FAIL:'red'}
        cleanedUpStyledValue = cellStyledValue
        cellFillColor = 'white'
        for style in otherStyles:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(style,'')
        for style in mainStyles:
            if style in cleanedUpStyledValue:
                cleanedUpStyledValue = cleanedUpStyledValue.replace(style,'')
                cellFillColor = colorsDict[style]
                break
        return cellFillColor, cleanedUpStyledValue

    def tableToImage(table, styledTable, filename,label):
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        # First 4 lines are headers. Last 1 line is bottom grid line
        bgColor = 'white'
        artColor = 'green'
        menuColor = 'red'
        gridColor = 'black'
        repoText = 'https://GitHub.com/pkjmesra/pkscreener/'
        screenLines = styledTable.splitlines()
        unstyledLines = table.splitlines()
        artfont = ImageFont.truetype("courbd.ttf", 30)
        font = ImageFont.truetype("courbd.ttf", 60)
        arttext_width, arttext_height = artfont.getsize_multiline(artText)
        label_width, label_height = font.getsize_multiline(label)
        text_width, text_height = font.getsize_multiline(table)
        im = Image.new("RGB", (text_width + 15, arttext_height + text_height + label_height + 15),bgColor)
        draw = ImageDraw.Draw(im)
        # artwork
        draw.text((7, 7), artText, font=artfont, fill=artColor)
        # selected menu options
        draw.text((7, 8 + arttext_height), label, font=font, fill=menuColor)
        lineNumber = 0
        colPixelRunValue = 7
        rowPixelRunValue = 9 + arttext_height + label_height
        separator = '|'
        sep_width, sep_height = font.getsize_multiline(separator)
        for line in screenLines:
            line_width, line_height = font.getsize_multiline(line)
            # Print the header columns and bottom grid line
            if lineNumber == 0 or (lineNumber % 2) == 0 or lineNumber == len(screenLines)-1:
                draw.text((colPixelRunValue, rowPixelRunValue),line , font=font, fill=gridColor)
                rowPixelRunValue = rowPixelRunValue + line_height + 1
            elif lineNumber == 1:
                draw.text((colPixelRunValue, rowPixelRunValue),line , font=font, fill=gridColor)
                rowPixelRunValue = rowPixelRunValue + line_height + 1
            else:
                valueScreenCols = line.split(separator)
                columnNumber = 0
                del valueScreenCols[0]
                del valueScreenCols[-1]
                for val in valueScreenCols:
                    unstyledLine = unstyledLines[lineNumber]
                    style, cleanValue = tools.getCellColor(val)
                    if columnNumber == 0:
                        cleanValue = unstyledLine.split(separator)[1]
                        style = gridColor
                    if bgColor == 'white' and style == 'yellow':
                        # Yellow on a white background is difficult to read
                        style = 'blue'
                    elif bgColor == 'black' and style == 'blue':
                        # blue on a black background is difficult to read
                        style = 'yellow'
                    col_width, col_height = font.getsize_multiline(cleanValue)
                    draw.text((colPixelRunValue, rowPixelRunValue),separator, font=font, fill=gridColor)
                    colPixelRunValue = colPixelRunValue + sep_width
                    draw.text((colPixelRunValue, rowPixelRunValue),cleanValue, font=font, fill=style)
                    colPixelRunValue = colPixelRunValue + col_width
                    columnNumber = columnNumber + 1
                # Close the row with the separator
                draw.text((colPixelRunValue, rowPixelRunValue),separator, font=font, fill=gridColor)
                colPixelRunValue = 7
                rowPixelRunValue = rowPixelRunValue + line_height + 1
            lineNumber = lineNumber + 1
        draw.text((colPixelRunValue, rowPixelRunValue), repoText, font=font, fill=menuColor)
        im.save(filename, format='png', bitmap_format='png')
        # im.show()

    def tradingDate(simulate=False, day=None):
        curr = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        if simulate:
            return curr.replace(day=day)
        else:
            if tools.isTradingWeekday() and tools.ispreMarketTime():
                # Monday to Friday but before 9:15AM.So the date should be yesterday
                return (curr - datetime.timedelta(days=1)).date()
            if tools.isTradingTime() or tools.ispostMarketTime():
                # Monday to Friday but after 9:15AM or after 15:30.So the date should be today
                return curr.date()
            if not tools.isTradingWeekday():
                # Weekends .So the date should be last Friday
                return (curr - datetime.timedelta(days=(curr.weekday()-4))).date()
            
    def currentDateTime(simulate=False, day=None, hour=None, minute=None):
        curr = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        if simulate:
            return curr.replace(day=day, hour=hour, minute=minute)
        else:
            return curr

    def isTradingTime():
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=9, minute=15)
        closeTime = curr.replace(hour=15, minute=30)
        return ((openTime <= curr <= closeTime) and tools.isTradingWeekday())

    def isTradingWeekday():
        curr = tools.currentDateTime()
        return (0 <= curr.weekday() <= 4)
    
    def ispreMarketTime():
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=9, minute=15)
        return ((openTime > curr) and tools.isTradingWeekday())
    
    def ispostMarketTime():
        curr = tools.currentDateTime()
        closeTime = curr.replace(hour=15, minute=30)
        return ((closeTime < curr) and tools.isTradingWeekday())
    
    def isClosingHour():
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=15, minute=00)
        closeTime = curr.replace(hour=15, minute=30)
        return ((openTime <= curr <= closeTime) and tools.isTradingWeekday())

    def secondsAfterCloseTime():
        curr = tools.currentDateTime() #(simulate=True,day=7,hour=8,minute=14)
        closeTime = curr.replace(hour=15, minute=30)
        return (curr - closeTime).total_seconds()

    def secondsBeforeOpenTime():
        curr = tools.currentDateTime() #(simulate=True,day=7,hour=8,minute=14)
        openTime = curr.replace(hour=9, minute=15)
        return (curr - openTime).total_seconds()

    def nextRunAtDateTime(bufferSeconds=3600, cronWaitSeconds=300):
        curr = tools.currentDateTime() #(simulate=True,day=7,hour=8,minute=14)
        nextRun = curr + datetime.timedelta(seconds=cronWaitSeconds)
        if (0 <= curr.weekday() <= 4):
            daysToAdd = 0
        else:
            daysToAdd = 7 - curr.weekday()
        if tools.isTradingTime():
            nextRun = curr + datetime.timedelta(seconds=cronWaitSeconds)
        else:
            # Same day after closing time
            secondsAfterClosingTime = tools.secondsAfterCloseTime()
            if secondsAfterClosingTime > 0:
                if secondsAfterClosingTime <= bufferSeconds:
                    nextRun = curr + datetime.timedelta(days=daysToAdd, seconds=1.5*cronWaitSeconds + bufferSeconds - secondsAfterClosingTime)
                elif secondsAfterClosingTime > (bufferSeconds+1.5*cronWaitSeconds):
                    # Same day, upto 11:59:59pm
                    curr = curr + datetime.timedelta(days=3 if curr.weekday() == 4 else 1)
                    nextRun = curr.replace(hour=9, minute=15) - datetime.timedelta(days=daysToAdd, seconds=1.5*cronWaitSeconds + bufferSeconds)
            elif secondsAfterClosingTime < 0:
                # Next day
                nextRun = curr.replace(hour=9, minute=15) - datetime.timedelta(days=daysToAdd, seconds=1.5*cronWaitSeconds + bufferSeconds)
        return nextRun

    def afterMarketStockDataExists():
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=9, minute=15)
        cache_date = curr.today()  # for monday to friday
        weekday = curr.today().weekday()
        if curr < openTime:  # for monday to friday before 9:15
            cache_date = curr.today() - datetime.timedelta(1)
        if weekday == 0 and curr < openTime:  # for monday before 9:15
            cache_date = curr.today() - datetime.timedelta(3)
        if weekday == 5 or weekday == 6:  # for saturday and sunday
            cache_date = curr.today() - datetime.timedelta(days=weekday - 4)
        cache_date = cache_date.strftime("%d%m%y")
        cache_file = "stock_data_" + str(cache_date) + ".pkl"
        exists = False
        for f in glob.glob('stock_data*.pkl'):
            if f.endswith(cache_file):
                exists = True
                break
        return exists, cache_file

    def saveStockData(stockDict, configManager, loadCount):
        exists, cache_file = tools.afterMarketStockDataExists()
        if exists:
            configManager.deleteStockData(excludeFile=cache_file)

        if not os.path.exists(cache_file) or len(stockDict) > (loadCount+1):
            with open(cache_file, 'wb') as f:
                try:
                    pickle.dump(stockDict.copy(), f)
                    print(colorText.BOLD + colorText.GREEN +
                          "=> Done." + colorText.END)
                except pickle.PicklingError as e:
                    default_logger().debug(e, exc_info=True)
                    print(colorText.BOLD + colorText.FAIL +
                          "=> Error while Caching Stock Data." + colorText.END)
        else:
            print(colorText.BOLD + colorText.GREEN +
                  "=> Already Cached." + colorText.END)

    def loadStockData(stockDict, configManager, proxyServer=None, downloadOnly=False, defaultAnswer=None,retrial=False):
        exists, cache_file = tools.afterMarketStockDataExists()
        default_logger().info(f'Stock data cache file:{cache_file} exists ->{str(exists)}')
        stockDataLoaded = False
        if exists:
            with open(cache_file, 'rb') as f:
                try:
                    stockData = pickle.load(f)
                    if not downloadOnly:
                        print(colorText.BOLD + colorText.GREEN +
                            "[+] Automatically Using Cached Stock Data due to After-Market hours!" + colorText.END)
                    for stock in stockData:
                        stockDict[stock] = stockData.get(stock)
                    stockDataLoaded = True
                except pickle.UnpicklingError as e:
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    print(colorText.BOLD + colorText.FAIL +
                          "[+] Error while Reading Stock Cache." + colorText.END)
                    if tools.promptFileExists(defaultAnswer=defaultAnswer) == 'Y':
                        configManager.deleteStockData()
                except EOFError as e:
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    print(colorText.BOLD + colorText.FAIL +
                          "[+] Stock Cache Corrupted." + colorText.END)
                    if tools.promptFileExists(defaultAnswer=defaultAnswer) == 'Y':
                        configManager.deleteStockData()
        if not stockDataLoaded and ConfigManager.default_period == configManager.period and ConfigManager.default_duration == configManager.duration:
            cache_url = "https://raw.github.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/" + cache_file
            if proxyServer is not None:
                resp = requests.get(cache_url, stream=True, proxies={'https':proxyServer})
            else:
                resp = requests.get(cache_url, stream=True)
            default_logger().info(f'Stock data cache file:{cache_file} request status ->{resp.status_code}')
            if resp.status_code == 200:
                print(colorText.BOLD + colorText.FAIL +
                      "[+] After-Market Stock Data is not cached.." + colorText.END)
                print(colorText.BOLD + colorText.GREEN +
                      "[+] Downloading cache from pkscreener server for faster processing, Please Wait.." + colorText.END)
                try:
                    chunksize = 1024*1024*1
                    filesize = int(int(resp.headers.get('content-length'))/chunksize)
                    if filesize > 0:
                        bar, spinner = tools.getProgressbarStyle()
                        f = open(cache_file, 'wb')
                        dl = 0
                        with alive_bar(filesize, bar=bar, spinner=spinner, manual=True) as progressbar:
                            for data in resp.iter_content(chunk_size=chunksize):
                                dl += 1
                                f.write(data)
                                progressbar(dl/filesize)
                                if dl >= filesize:
                                    progressbar(1.0)
                        f.close()
                        stockDataLoaded = True
                    else:
                        default_logger().debug(f'Stock data cache file:{cache_file} on server has length ->{filesize}')
                except Exception as e:
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    print("[!] Download Error - " + str(e))
                print("")
                if not retrial:
                    # Don't try for more than once.
                    tools.loadStockData(stockDict, configManager, proxyServer, downloadOnly, defaultAnswer,retrial=True)
        if not stockDataLoaded:
            print(colorText.BOLD + colorText.FAIL +
                  "[+] Cache unavailable on pkscreener server, Continuing.." + colorText.END)

    # Save screened results to excel
    def promptSaveResults(df, defaultAnswer=None):
        try:
            if defaultAnswer is None:
                response = str(input(colorText.BOLD + colorText.WARN +
                                    '[>] Do you want to save the results in excel file? [Y/N]: ')).upper()
            else:
                response = defaultAnswer
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            response = 'Y'
        if response != 'N':
            filename = 'PKScreener-result_' + \
                tools.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")+".xlsx"
            df.to_excel(filename, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
            print(colorText.BOLD + colorText.GREEN +
                  ("[+] Results saved to %s" % filename) + colorText.END)
            return filename
        return None

    # Save screened results to excel
    def promptFileExists(cache_file='stock_data_*.pkl', defaultAnswer=None):
        try:
            if defaultAnswer is None:
                response = str(input(colorText.BOLD + colorText.WARN +
                                    '[>] ' + cache_file + ' already exists. Do you want to replace this? [Y/N]: ')).upper()
            else:
                response = defaultAnswer
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            pass
        return 'Y' if response != 'N' else 'N'
    
    # Prompt for asking RSI
    def promptRSIValues():
        try:
            minRSI, maxRSI = int(input(colorText.BOLD + colorText.WARN + "\n[+] Enter Min RSI value: " + colorText.END)), int(
                input(colorText.BOLD + colorText.WARN + "[+] Enter Max RSI value: " + colorText.END))
            if (minRSI >= 0 and minRSI <= 100) and (maxRSI >= 0 and maxRSI <= 100) and (minRSI <= maxRSI):
                return (minRSI, maxRSI)
            raise ValueError
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            return (0, 0)

    # Prompt for asking CCI
    def promptCCIValues(minCCI=None, maxCCI=None):
        if minCCI is not None and maxCCI is not None:
            return minCCI, maxCCI
        try:
            minCCI, maxCCI = int(input(colorText.BOLD + colorText.WARN + "\n[+] Enter Min CCI value: " + colorText.END)), int(
                input(colorText.BOLD + colorText.WARN + "[+] Enter Max CCI value: " + colorText.END))
            if (minCCI <= maxCCI):
                return (minCCI, maxCCI)
            raise ValueError
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            return (-100, 100)

    # Prompt for asking Volume ratio
    def promptVolumeMultiplier(volumeRatio=None):
        if volumeRatio is not None:
            return volumeRatio
        try:
            volumeRatio = int(input(colorText.BOLD + colorText.WARN + "\n[+] Enter Min Volume ratio value (Default = 2): " + colorText.END))
            if (volumeRatio > 0):
                return volumeRatio
            raise ValueError
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            return 2

    def promptMenus(menu):
        m = menus()
        return m.renderForMenu(menu)
    
    # Prompt for Reversal screening
    def promptReversalScreening(menu=None):
        try:
            tools.promptMenus(menu=menu)
            resp = int(input(colorText.BOLD + colorText.WARN + """[+] Select Option:""" + colorText.END))
            if resp >= 0 and resp <= 6:
                if resp == 4:
                    try:
                        maLength = int(input(colorText.BOLD + colorText.WARN +
                                             '\n[+] Enter MA Length (E.g. 50 or 200): ' + colorText.END))
                        return resp, maLength
                    except ValueError as e:
                        default_logger().debug(e, exc_info=True)
                        print(colorText.BOLD + colorText.FAIL +
                              '\n[!] Invalid Input! MA Lenght should be single integer value!\n' + colorText.END)
                        raise ValueError
                elif resp == 6:
                    try:
                        maLength = int(input(colorText.BOLD + colorText.WARN +
                                             '\n[+] Enter NR timeframe [Integer Number] (E.g. 4, 7, etc.): ' + colorText.END))
                        return resp, maLength
                    except ValueError as e:
                        default_logger().debug(e, exc_info=True)
                        print(colorText.BOLD + colorText.FAIL + '\n[!] Invalid Input! NR timeframe should be single integer value!\n' + colorText.END)
                        raise ValueError
                return resp, None
            raise ValueError
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            return None, None

    # Prompt for Reversal screening
    def promptChartPatterns(menu=None):
        try:
            tools.promptMenus(menu=menu)
            resp = int(input(colorText.BOLD + colorText.WARN + """[+] Select Option:""" + colorText.END))
            if resp == 1 or resp == 2:
                candles = int(input(colorText.BOLD + colorText.WARN +
                                    "\n[+] How many candles (TimeFrame) to look back Inside Bar formation? : " + colorText.END))
                return (resp, candles)
            if resp == 3:
                percent = float(input(colorText.BOLD + colorText.WARN +
                                      "\n[+] Enter Percentage within which all MA/EMAs should be (Ideal: 1-2%)? : " + colorText.END))
                return (resp, percent/100.0)
            if resp >= 0 and resp <= 5:
                return resp, 0
            raise ValueError
        except ValueError as e:
            default_logger().debug(e, exc_info=True)
            input(colorText.BOLD + colorText.FAIL +
                  "\n[+] Invalid Option Selected. Press Any Key to Continue..." + colorText.END)
            return (None, None)

    def getProgressbarStyle():
        bar = 'smooth'
        spinner = 'waves'
        if 'Windows' in platform.platform():
            bar = 'classic2'
            spinner = 'dots_recur'
        return bar, spinner

    def getNiftyModel(proxyServer=None, retrial=False):
        files = ['nifty_model_v2.h5', 'nifty_model_v2.pkl']
        model = None
        urls = [
            "https://raw.github.com/pkjmesra/PKScreener/main/src/ml/nifty_model_v2.h5",
            "https://raw.github.com/pkjmesra/PKScreener/main/src/ml/nifty_model_v2.pkl"
        ]
        if os.path.isfile(files[0]) and os.path.isfile(files[1]):
            file_age = (time.time() - os.path.getmtime(files[0]))/604800
            if file_age > 1:
                download = True
                os.remove(files[0])
                os.remove(files[1])
            else:
                download = False
        else:
            download = True
        if download:
            for file_url in urls:
                if proxyServer is not None:
                    resp = requests.get(file_url, stream=True, proxies={'https':proxyServer})
                else:
                    resp = requests.get(file_url, stream=True)
                if resp.status_code == 200:
                    print(colorText.BOLD + colorText.GREEN +
                            "[+] Downloading AI model (v2) for Nifty predictions, Please Wait.." + colorText.END)
                    try:
                        chunksize = 1024*1024*1
                        filesize = int(int(resp.headers.get('content-length'))/chunksize)
                        filesize = 1 if not filesize else filesize
                        bar, spinner = tools.getProgressbarStyle()
                        f = open(file_url.split('/')[-1], 'wb')
                        dl = 0
                        with alive_bar(filesize, bar=bar, spinner=spinner, manual=True) as progressbar:
                            for data in resp.iter_content(chunk_size=chunksize):
                                dl += 1
                                f.write(data)
                                progressbar(dl/filesize)
                                if dl >= filesize:
                                    progressbar(1.0)
                        f.close()
                    except Exception as e:
                        default_logger().debug(e, exc_info=True)
                        print("[!] Download Error - " + str(e))
            time.sleep(3)
        try:
            model = keras.models.load_model(files[0]) if Imports['keras'] else None
            pkl = joblib.load(files[1])
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            os.remove(files[0])
            os.remove(files[1])
            if not retrial:
                tools.getNiftyModel(proxyServer=proxyServer, retrial=True)
        return model, pkl

    def getSigmoidConfidence(x):
        out_min, out_max = 0, 100
        if x > 0.5:
            in_min = 0.50001
            in_max = 1
        else:
            in_min = 0
            in_max = 0.5
        return round(((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min),3)

    def alertSound(beeps=3, delay=0.2):
        for i in range(beeps):
            print('\a')
            sleep(delay)
    