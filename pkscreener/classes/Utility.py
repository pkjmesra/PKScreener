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
import copy
import datetime
import glob
import math
import os
import shutil
import sys
import textwrap
import random

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["AUTOGRAPH_VERBOSITY"] = "0"

import pickle
import platform
import tempfile
import time

import joblib
import numpy as np
import pytz
from halo import Halo
from genericpath import isfile
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.ColorText import colorText
from pkscreener import Imports

import warnings
from time import sleep

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
from alive_progress import alive_bar
from PIL import Image, ImageDraw, ImageFont
from PKDevTools.classes import Archiver
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.FunctionTimeouts import exit_after
from PKDevTools.classes.MarketHours import MarketHours
from tabulate import tabulate

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes import VERSION, Changelog
from pkscreener.classes.MenuOptions import menus
from PKNSETools.PKNSEStockDataFetcher import nseStockDataFetcher
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes.MarketStatus import MarketStatus
from pkscreener.classes.PKScheduler import PKScheduler
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.Utils import random_user_agent

from pkscreener.classes.ArtTexts import getArtText
from PKDevTools.classes.NSEMarketStatus import NSEMarketStatus

import PIL.Image
PIL.Image.MAX_IMAGE_PIXELS = None

configManager = ConfigManager.tools()
configManager.getConfig(ConfigManager.parser)
nseFetcher = nseStockDataFetcher()
fetcher = Fetcher.screenerStockDataFetcher()


artText = f"{getArtText()}\n"

STD_ENCODING=sys.stdout.encoding if sys.stdout is not None else 'utf-8'

def marketStatus():
    # task = PKTask("Nifty 50 Market Status",MarketStatus().getMarketStatus)
    lngStatus = MarketStatus().marketStatus
    nseStatus = ""
    next_bell = ""
    try:
        nseStatus = NSEMarketStatus({},None).status
        next_bell = NSEMarketStatus({},None).getNextBell()
    except:
        pass
    # scheduleTasks(tasksList=[task])
    if lngStatus == "":
        lngStatus = MarketStatus().getMarketStatus(exchangeSymbol="^IXIC" if configManager.defaultIndex == 15 else "^NSEI")
    if "Close" in lngStatus and nseStatus == "Open":
        lngStatus = lngStatus.replace("Closed","Open")
    if len(next_bell) > 0 and next_bell not in lngStatus:
        lngStatus = f"{lngStatus} | Next Bell: {colorText.WARN}{next_bell.replace('T',' ').split('+')[0]}{colorText.END}"
    return (lngStatus +"\n") if lngStatus is not None else "\n"

art = colorText.GREEN + f"{getArtText()}\n" + colorText.END + f"{marketStatus()}"

lastScreened = os.path.join(
    Archiver.get_user_data_dir(), "last_screened_results.pkl"
)

# Class for managing misc and utility methods

class tools:
    def clearScreen(userArgs=None,clearAlways=False,forceTop=False):
        if "RUNNER" in os.environ.keys() or (userArgs is not None and userArgs.prodbuild):
            if userArgs is not None and userArgs.v:
                os.environ["RUNNER"]="LOCAL_RUN_SCANNER"
            return
        elif (userArgs is not None and userArgs.runintradayanalysis):
            return
        if clearAlways or OutputControls().enableMultipleLineOutput:
            if platform.system() == "Windows":
                try:
                    os.system('color 0f') # sets the background to black with white forerground
                except:
                    pass
                if clearAlways:
                    os.system("cls")
            elif "Darwin" in platform.system():
                if clearAlways:
                    os.system("clear")
                # default_logger().debug("Darwin does not work for setting background")
            else:
                try:
                    os.system('setterm -background black -foreground white -store')
                except:
                    pass
                if clearAlways:
                    os.system("clear")
            OutputControls().moveCursorToStartPosition()
        try:
            forceTop = OutputControls().enableMultipleLineOutput
            if forceTop and OutputControls().lines == 0:
                OutputControls().lines = 9
                OutputControls().moveCursorToStartPosition()
                
            if clearAlways or OutputControls().enableMultipleLineOutput:
                art = colorText.GREEN + f"{getArtText()}\n" + colorText.END + f"{marketStatus()}"
                OutputControls().printOutput(art.encode('utf-8').decode(STD_ENCODING), enableMultipleLineOutput=True)
        except Exception as e:# pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass

    # Print about developers and repository
    def showDevInfo(defaultAnswer=None):
        OutputControls().printOutput("\n" + Changelog.changelog())
        devInfo = "\n[👨🏻‍💻] Developer: PK (PKScreener) 🇮🇳"
        versionInfo = "[🚦] Version: %s" % VERSION
        homePage = "[🏡] Home Page: https://github.com/pkjmesra/PKScreener\n[🤖] Telegram Bot:@nse_pkscreener_bot\n[🚨] Channel:https://t.me/PKScreener\n[💬] Discussions:https://t.me/PKScreeners"
        issuesInfo = (
            "[🚩] Read/Post Issues here: https://github.com/pkjmesra/PKScreener/issues"
        )
        communityInfo = "[📢] Join Community Discussions: https://github.com/pkjmesra/PKScreener/discussions"
        latestInfo = "[⏰] Download latest software from https://github.com/pkjmesra/PKScreener/releases/latest"
        donationInfo = "[💰] PKScreener is and will always remain free for everyone. Hosting servers and running services costs money.\n[💸] Please donate whatever you can: PKScreener@APL using UPI(India) or https://github.com/sponsors/pkjmesra 🙏🏻"
        totalDownloads = "200k+"
        respPepyTech = fetcher.fetchURL(url="https://static.pepy.tech/badge/pkscreener",headers={'user-agent': f'{random_user_agent()}'},timeout=2)
        if respPepyTech is not None and respPepyTech.status_code == 200:
            totalDownloads = respPepyTech.text.split("</text>")[-2].split(">")[-1]
        downloadsInfo = f"[🔥] Total Downloads: {totalDownloads}"
        OutputControls().printOutput(colorText.WARN + devInfo + colorText.END)
        OutputControls().printOutput(colorText.WARN + versionInfo + colorText.END)
        OutputControls().printOutput(colorText.GREEN + downloadsInfo + colorText.END)
        OutputControls().printOutput(homePage + colorText.END)
        OutputControls().printOutput(colorText.FAIL + issuesInfo + colorText.END)
        OutputControls().printOutput(colorText.GREEN + communityInfo + colorText.END)
        OutputControls().printOutput(colorText.BLUE + latestInfo + colorText.END)
        OutputControls().printOutput(colorText.FAIL + donationInfo + colorText.END)
        if defaultAnswer is None:
            OutputControls().takeUserInput(
                colorText.FAIL
                + "  [+] Press <Enter> to continue!"
                + colorText.END
            )
        return f"\n{Changelog.changelog()}\n\n{devInfo}\n{versionInfo}\n\n{downloadsInfo}\n{homePage}\n{issuesInfo}\n{communityInfo}\n{latestInfo}\n{donationInfo}"

    # Save last screened result to pickle file
    def setLastScreenedResults(df, df_save=None, choices=None):
        try:
            finalStocks = ""
            outputFolder = os.path.join(os.getcwd(),'actions-data-scan')
            if not os.path.isdir(outputFolder):
                os.makedirs(os.path.dirname(os.path.join(os.getcwd(),f"actions-data-scan{os.sep}")), exist_ok=True)
            fileName = os.path.join(outputFolder,f"{choices}.txt")
            items = []
            needsWriting = False
            if os.path.isfile(fileName):
                if df is not None and len(df) > 0:
                    #File already exists. Let's combine because there are new stocks found
                    with open(fileName, 'r') as fe:
                        stocks = fe.read()
                        items = stocks.replace("\n","").replace("\"","").split(",")
                        stockList = sorted(list(filter(None,list(set(items)))))
                        finalStocks = ",".join(stockList)
            else:
                needsWriting = True
            if df is not None and len(df) > 0:
                with pd.option_context('mode.chained_assignment', None):
                    df.sort_values(by=["Stock"], ascending=True, inplace=True)
                    df.to_pickle(lastScreened)
                    if choices is not None and df_save is not None:
                        df_s = df_save.copy()
                        df_s.reset_index(inplace=True)
                        newStocks = df_s["Stock"].to_json(orient='records', lines=True).replace("\n","").replace("\"","").split(",")
                        items.extend(newStocks)
                        stockList = sorted(list(filter(None,list(set(items)))))
                        finalStocks = ",".join(stockList)
                        needsWriting = True
            if needsWriting:
                with open(fileName, 'w') as f:
                    f.write(finalStocks)
        except IOError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + f"{e}\n  [+] Failed to save recently screened result table on disk! Skipping.."
                + colorText.END
            )
        except Exception as e:# pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass

    # Load last screened result to pickle file
    def getLastScreenedResults(defaultAnswer=None):
        try:
            df = pd.read_pickle(lastScreened)
            if df is not None and len(df) > 0:
                OutputControls().printOutput(
                    colorText.GREEN
                    + "\n  [+] Showing recently screened results..\n"
                    + colorText.END
                )
                df.sort_values(by=["Volume"], ascending=False, inplace=True)
                OutputControls().printOutput(
                    colorText.miniTabulator().tabulate(
                        df, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
                        maxcolwidths=tools.getMaxColumnWidths(df)
                    ).encode("utf-8").decode(STD_ENCODING)
                )
                OutputControls().printOutput(
                    colorText.WARN
                    + "  [+] Note: Trend calculation is based on number of recent days to screen as per your configuration."
                    + colorText.END
                )
            else:
                OutputControls().printOutput("Nothing to show here!")
        except FileNotFoundError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] Failed to load recently screened result table from disk! Skipping.."
                + colorText.END
            )
        if defaultAnswer is None:
            OutputControls().takeUserInput(
                colorText.GREEN
                + "  [+] Press <Enter> to continue.."
                + colorText.END
            )

    def formattedBacktestOutput(outcome, pnlStats=False, htmlOutput=True):
        if not pnlStats:
            if htmlOutput:
                if outcome >= 80:
                    return f'{colorText.GREEN}{"%.2f%%" % outcome}{colorText.END}'
                if outcome >= 60:
                    return f'{colorText.WARN}{"%.2f%%" % outcome}{colorText.END}'
                return f'{colorText.FAIL}{"%.2f%%" % outcome}{colorText.END}'
            else:
                return f'{colorText.GREEN}{"%.2f%%" % outcome}{colorText.END}'
        else:
            if outcome >= 0:
                return f'{colorText.GREEN}{"%.2f%%" % outcome}{colorText.END}'
            return f'{colorText.FAIL}{"%.2f%%" % outcome}{colorText.END}'

    def getFormattedBacktestSummary(x, pnlStats=False, columnName=None):
        if x is not None and "%" in str(x):
            values = x.split("%")
            if (
                len(values) == 2
                and columnName is not None
                and ("-Pd" in columnName or "Overall" in columnName)
            ):
                return "{0}{1}".format(
                    tools.formattedBacktestOutput(
                        float(values[0]), pnlStats=pnlStats, htmlOutput=False
                    ),
                    values[1],
                )
        return x

    def formatRatio(ratio, volumeRatio):
        if ratio >= volumeRatio and ratio != np.nan and (not math.isinf(ratio)):
            return colorText.GREEN + str(ratio) + "x" + colorText.END
        return colorText.FAIL + (f"{ratio}x" if pd.notna(ratio) else "") + colorText.END

    def getsize_multiline(font,srcText,x=0,y=0):
        zeroSizeImage = Image.new('RGB',(0, 0), (0,0,0))
        zeroDraw = ImageDraw.Draw(zeroSizeImage)
        # zeroDraw = ImageDraw.Draw(zeroSizeImage)
        bbox = zeroDraw.multiline_textbbox((x,y),srcText,font)
        # Calculate width and height from the bounding box
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        # default_logger().debug(f"Text size for text: {srcText}: {width}x{height}")
        return width, height

    def getsize(font,srcText,x=0,y=0):
        left, top, bottom, right = font.getbbox(srcText)
        return right - left, bottom - top
    
    def addQuickWatermark(sourceImage:Image, xVertical=None, dataSrc="", dataSrcFontSize=10):
        width, height = sourceImage.size
        watermarkText = f"© {datetime.date.today().year} pkjmesra | PKScreener"
        message_length = len(watermarkText)
        # load font (tweak ratio based on a particular font)
        FONT_RATIO = 1.5
        DIAGONAL_PERCENTAGE = .85
        DATASRC_FONTSIZE = dataSrcFontSize
        dataSrc = f"Src: {dataSrc}"
        diagonal_length = int(math.sqrt((width**2) + (height**2)))
        diagonal_to_use = diagonal_length * DIAGONAL_PERCENTAGE
        height_to_use = height * DIAGONAL_PERCENTAGE
        font_size = int(diagonal_to_use / (message_length / FONT_RATIO))
        font_size_vertical = int(height_to_use / (message_length / FONT_RATIO))
        fontPath = tools.setupReportFont()
        font = ImageFont.truetype(fontPath, font_size)
        font_vertical = ImageFont.truetype(fontPath, font_size_vertical)
        #font = ImageFont.load_default() # fallback

        # watermark 1
        opacity = int(256 * .6)
        _,_,mark_width, mark_height = font.getbbox(watermarkText)
        watermark = Image.new('RGBA', (mark_width, mark_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        draw.text((0, 0), text=watermarkText, font=font, fill=(128, 128, 128, opacity))
        angle = math.degrees(math.atan(height/width))
        watermark_diag = watermark.rotate(angle, expand=1)
        
        _,_,mark_width_ver, mark_height_ver = font_vertical.getbbox(watermarkText)
        watermark_ver = Image.new('RGBA', (mark_width_ver, mark_height_ver), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_ver)
        draw.text((0, 0), text=watermarkText, font=font_vertical, fill=(128, 128, 128, opacity))
        watermark_vertical = watermark_ver.rotate(90, expand=1)

        # merge
        try:
            logo_wm_path = os.path.join(Archiver.get_user_outputs_dir().replace("results","pkscreener"),"LogoWM.txt")
            if not os.path.isfile(logo_wm_path):
                resp = tools.tryFetchFromServer(cache_file="LogoWM.png",directory="screenshots/logos",hideOutput=True)
                with open(logo_wm_path,"wb",) as f:
                    f.write(resp.content)
            logo_img = Image.open(logo_wm_path,formats=["PNG"]).convert('LA')
            # logo_img = logo_img.resize((min(width,height),min(width,height)), Image.LANCZOS, reducing_gap=2)
            lx, ly = logo_img.size
            plx = int((width - lx)/4)
            ply = int((height - ly)/3)
            sourceImage.paste(logo_img, (plx, ply), logo_img)
        except Exception as e:
            default_logger().debug(e,exc_info=True)
            pass

        wx, wy = watermark_diag.size
        px = int((width - wx)/2)
        py = int((height - wy)/2)
        wxv, wyv = watermark_vertical.size
        pxv =  int((width - wxv)/12) if xVertical is None else xVertical
        pyv= int((height - wyv)/2)
        sourceImage.paste(watermark_diag, (px, py, px + wx, py + wy), watermark_diag)
        sourceImage.paste(watermark_vertical, (pxv, pyv, pxv + wxv, pyv + wyv), watermark_vertical)
        
        # Draw the data sources
        dataSrcFont = ImageFont.truetype(fontPath, DATASRC_FONTSIZE)
        dataSrc_width, dataSrc_height = tools.getsize_multiline(font=dataSrcFont,srcText=dataSrc)
        draw = ImageDraw.Draw(sourceImage)
        draw.text((width-dataSrc_width, height-dataSrc_height-2), text=dataSrc, font=dataSrcFont, fill=(128, 128, 128, opacity))
        # sourceImage.show()
        return sourceImage

    def roundOff(value,places):
        roundValue = value
        try:
            newValue = tools.removeAllColorStyles(str(roundValue))
            newValue = newValue.replace("%","").replace("x","")
            roundValue = round(float(newValue),places)
            if places == 0:
                roundValue = int(roundValue)
            roundValue = str(value).replace(str(newValue),str(roundValue))
        except:
            pass
        return roundValue
    
    def stockNameFromDecoratedName(stockName): 
        cleanName = tools.removeAllColorStyles(stockName.replace("\x1B]8;;",""))
        decoratedParts = cleanName.split("\x1B\\")
        if len(decoratedParts) > 1:
            cleanName = decoratedParts[1]
        return cleanName
    
    def stockDecoratedName(stockName,exchangeName):
        decoratedName = f"{colorText.WHITE}\x1B]8;;https://in.tradingview.com/chart?symbol={'NSE' if exchangeName=='INDIA' else 'NASDAQ'}%3A{stockName}\x1B\\{stockName}\x1B]8;;\x1B\\{colorText.END}"
        return decoratedName

    def removeAllColorStyles(styledText):
        styles = [
            colorText.HEAD,
            colorText.END,
            colorText.BOLD,
            colorText.UNDR,
            colorText.BLUE,
            colorText.GREEN,
            colorText.BRIGHTGREEN,
            colorText.WARN,
            colorText.BRIGHTYELLOW,
            colorText.FAIL,
            colorText.BRIGHTRED,
            colorText.WHITE,
        ]
        if isinstance(styledText,pd.DataFrame):
            styledTextCopy = styledText.copy()
            with pd.option_context('mode.chained_assignment', None):
                for col in styledTextCopy.columns:
                    for style in styles:
                        try:
                            styledTextCopy[col] = styledTextCopy[col].astype(str).str.replace(style,"")
                        except:
                            pass
            return styledTextCopy
        elif isinstance(styledText,str):
            cleanedUpStyledValue = str(styledText)
            for style in styles:
                cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
            return cleanedUpStyledValue
        else:
            return styledText

    def getCellColors(cellStyledValue="", defaultCellFillColor="black"):
        otherStyles = [colorText.HEAD, colorText.BOLD, colorText.UNDR]
        mainStyles = [
            colorText.BLUE,
            colorText.GREEN,
            colorText.BRIGHTGREEN,
            colorText.WARN,
            colorText.BRIGHTYELLOW,
            colorText.FAIL,
            colorText.BRIGHTRED,
            colorText.WHITE,
        ]
        colorsDict = {
            colorText.BLUE: "blue",
            colorText.BRIGHTGREEN: "darkgreen",
            colorText.GREEN: "green"
            if defaultCellFillColor == "black"
            else "lightgreen",
            colorText.WARN: "darkorange"
            if defaultCellFillColor == "black"
            else "yellow",
            colorText.BRIGHTYELLOW: "darkyellow",
            colorText.FAIL: "red",
            colorText.BRIGHTRED : "darkred",
            colorText.WHITE: "white" 
            if defaultCellFillColor == "white"
            else "black",
        }
        cleanedUpStyledValues = []
        cellFillColors = []
        cleanedUpStyledValue = cellStyledValue
        prefix = ""
        for style in otherStyles:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
        # Find how many different colors are used for the cell value
        coloredStyledValues = cleanedUpStyledValue.split(colorText.END)
        for cleanedUpStyledValue in coloredStyledValues:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(colorText.END,"")
            if cleanedUpStyledValue.strip() in ["", ",","/"]:
                if len(cleanedUpStyledValues) > 0:
                    cleanedUpStyledValues[len(cleanedUpStyledValues)-1] = f"{cleanedUpStyledValues[len(cleanedUpStyledValues)-1]}{cleanedUpStyledValue}"
                else:
                    prefix = cleanedUpStyledValue
            else:
                for style in mainStyles:
                    if style in cleanedUpStyledValue:
                        cellFillColors.append(colorsDict[style])
                        for style in mainStyles:
                            cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
                        cleanedUpStyledValues.append(prefix + cleanedUpStyledValue)
                        prefix = ""
                
        if len(cellFillColors) == 0:
            cellFillColors = [defaultCellFillColor]
        if len(cleanedUpStyledValues) == 0:
            cleanedUpStyledValues = [cellStyledValue]
        return cellFillColors, cleanedUpStyledValues

    @Halo(text='', spinner='dots')
    def tableToImage(
        table,
        styledTable,
        filename,
        label,
        backtestSummary=None,
        backtestDetail=None,
        addendum=None,
        addendumLabel=None,
        summaryLabel = None,
        detailLabel = None,
        legendPrefixText = ""
    ):
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            if (("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
                return
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        ART_FONT_SIZE = 30
        STD_FONT_SIZE = 60
        try:
            # First 4 lines are headers. Last 1 line is bottom grid line
            fontPath = tools.setupReportFont()
            artfont = ImageFont.truetype(fontPath, ART_FONT_SIZE)
            stdfont = ImageFont.truetype(fontPath, STD_FONT_SIZE)
            
            bgColor, gridColor, artColor, menuColor = tools.getDefaultColors()

            dfs_to_print = [styledTable, backtestSummary, backtestDetail]
            unstyled_dfs = [table, backtestSummary, backtestDetail]
            reportTitle = f"  [+] As of {PKDateUtilities.currentDateTime().strftime('%d-%m-%y %H.%M.%S')} IST > You chose {label}"
            titleLabels = [
                f"  [+] Scan results for {label} :",
                summaryLabel if summaryLabel is not None else "  [+] For chosen scan, summary of correctness from past: [Example, 70% of (100) under 1-Pd, means out of 100 stocks that were in the scan result in the past, 70% of them gained next day.)",
                detailLabel if detailLabel is not None else "  [+] 1 to 30 period gain/loss % for matching stocks on respective date from earlier predictions:[Example, 5% under 1-Pd, means the stock price actually gained 5% the next day from given date.]",
            ]

            artfont_arttext_width, artfont_arttext_height = tools.getsize_multiline(font=artfont,srcText=artText+ f"{marketStatus()}")
            stdFont_oneLinelabel_width, stdFont_oneLinelabel_height = tools.getsize_multiline(font=stdfont,srcText=label)
            stdFont_scanResulttext_width, stdFont_scanResulttext_height = tools.getsize_multiline(font=stdfont,srcText=table) if len(table) > 0 else (0,0)
            unstyled_backtestsummary = tools.removeAllColorStyles(backtestSummary)
            unstyled_backtestDetail = tools.removeAllColorStyles(backtestDetail)
            stdFont_backtestSummary_text_width,stdFont_backtestSummary_text_height= tools.getsize_multiline(font=stdfont,srcText=unstyled_backtestsummary) if len(unstyled_backtestsummary) > 0 else (0,0)
            stdFont_backtestDetail_text_width, stdFont_backtestDetail_text_height = tools.getsize_multiline(font=stdfont, srcText=unstyled_backtestDetail) if len(unstyled_backtestDetail) > 0 else (0,0)
            artfont_scanResultText_width, _ = tools.getsize_multiline(font=artfont,srcText=table) if len(table) > 0 else (0,0)
            artfont_backtestSummary_text_width, _ = tools.getsize_multiline(font= artfont,srcText=backtestSummary) if (backtestSummary is not None and len(backtestSummary)) > 0 else (0,0)
            stdfont_addendumtext_height = 0
            stdfont_addendumtext_width = 0
            if addendum is not None and len(addendum) > 0:
                unstyled_addendum = tools.removeAllColorStyles(addendum)
                stdfont_addendumtext_width , stdfont_addendumtext_height = tools.getsize_multiline(font=stdfont,srcText=unstyled_addendum)
                titleLabels.append(addendumLabel)
                dfs_to_print.append(addendum)
                unstyled_dfs.append(unstyled_addendum)

            repoText = tools.getRepoHelpText(table,backtestSummary)
            artfont_repotext_width, artfont_repotext_height = tools.getsize_multiline(font=artfont,srcText=repoText)
            legendText = legendPrefixText + tools.getLegendHelpText(table,backtestSummary)
            _, artfont_legendtext_height = tools.getsize_multiline(font=artfont,srcText=legendText)
            column_separator = "|"
            line_separator = "+"
            stdfont_sep_width, _ = tools.getsize_multiline(font=stdfont, srcText=column_separator)

            startColValue = 100
            xVertical = startColValue
            rowPixelRunValue = 9
            im_width = max(
                artfont_arttext_width,
                stdFont_oneLinelabel_width,
                stdFont_scanResulttext_width,
                stdFont_backtestSummary_text_width,
                stdFont_backtestDetail_text_width,
                artfont_repotext_width,
                artfont_scanResultText_width,
                artfont_backtestSummary_text_width,
                stdfont_addendumtext_width
            ) + int(startColValue * 2)
            im_height = int(
                        artfont_arttext_height # Always
                        + 3*stdFont_oneLinelabel_height # Title label # Always
                        + stdFont_scanResulttext_height + (stdFont_oneLinelabel_height if stdFont_scanResulttext_height > 0 else 0)
                        + stdFont_backtestSummary_text_height + (stdFont_oneLinelabel_height if stdFont_backtestSummary_text_height > 0 else 0)
                        + stdFont_backtestDetail_text_height + (stdFont_oneLinelabel_height if stdFont_backtestDetail_text_height > 0 else 0)
                        + artfont_repotext_height # Always
                        + artfont_legendtext_height # Always
                        + stdfont_addendumtext_height + (stdFont_oneLinelabel_height if stdfont_addendumtext_height > 0 else 0)
                    )
            im = Image.new("RGB",(im_width,im_height),bgColor)
            draw = ImageDraw.Draw(im)
            # artwork
            draw.text((startColValue, rowPixelRunValue), artText+ f"{tools.removeAllColorStyles(marketStatus())}", font=artfont, fill=artColor)
            rowPixelRunValue += artfont_arttext_height + 1
            # Report title
            # reportTitle = tools.wrapFitLegendText(table,backtestSummary, reportTitle)
            draw.text((startColValue, rowPixelRunValue), reportTitle, font=stdfont, fill=menuColor)
            rowPixelRunValue += stdFont_oneLinelabel_height + 1
            counter = -1
            for df in dfs_to_print:
                counter += 1
                colPixelRunValue = startColValue
                try:
                    if df is None or len(df) == 0:
                        continue
                except:
                    continue
                # selected menu options and As of DateTime
                draw.text(
                    (colPixelRunValue, rowPixelRunValue),
                    titleLabels[counter],
                    font=stdfont,
                    fill=menuColor,
                )
                rowPixelRunValue += stdFont_oneLinelabel_height
                unstyledLines = unstyled_dfs[counter].splitlines()
                lineNumber = 0
                screenLines = df.splitlines()
                for line in screenLines:
                    _, stdfont_line_height = tools.getsize_multiline(font=stdfont, srcText=line)
                    # Print the row separators
                    if not (line.startswith(column_separator)):
                        draw.text(
                            (colPixelRunValue, rowPixelRunValue),
                            line,
                            font=stdfont,
                            fill=gridColor,
                        )
                        rowPixelRunValue += stdfont_line_height + 1
                    else: # if (line.startswith(column_separator)):
                        # Print the row contents
                        columnNumber = 0
                        valueScreenCols = line.split(column_separator)
                        try:
                            del valueScreenCols[0] # Remove the empty column header at the first position
                            del valueScreenCols[-1] # Remove the empty column header at the last position
                        except Exception as e:# pragma: no cover
                            default_logger().debug(e, exc_info=True)
                            draw.text(
                                (colPixelRunValue, rowPixelRunValue),
                                line,
                                font=stdfont,
                                fill=gridColor,
                            )
                            lineNumber = lineNumber - 1
                            pass
                        # Print each colored value of each cell as we go over each row
                        for val in valueScreenCols:
                            if lineNumber >= len(unstyledLines):
                                continue
                            # Draw the column separator first
                            draw.text(
                                (colPixelRunValue, rowPixelRunValue),
                                column_separator,
                                font=stdfont,
                                fill=gridColor,
                            )
                            colPixelRunValue = colPixelRunValue + stdfont_sep_width
                            unstyledLine = unstyledLines[lineNumber]
                            cellStyles, cellCleanValues = tools.getCellColors(
                                val, defaultCellFillColor=gridColor
                            )
                            valCounter = 0
                            for style in cellStyles:
                                cleanValue = cellCleanValues[valCounter]
                                valCounter += 1
                                if columnNumber == 0 and len(cleanValue.strip()) > 0:
                                    if column_separator in unstyledLine:
                                        cleanValue = unstyledLine.split(column_separator)[1]
                                    if "\\" in cleanValue:
                                        cleanValue = cleanValue.split("\\")[-1]
                                    # style = style if "%" in cleanValue else gridColor
                                if bgColor == "white" and style == "yellow":
                                    # Yellow on a white background is difficult to read
                                    style = "blue"
                                elif bgColor == "black" and style == "blue":
                                    # blue on a black background is difficult to read
                                    style = "yellow"
                                col_width, _ = tools.getsize_multiline(font=stdfont, srcText=cleanValue)
                                draw.text(
                                    (colPixelRunValue, rowPixelRunValue),
                                    cleanValue,
                                    font=stdfont,
                                    fill=style,
                                )
                                colPixelRunValue = colPixelRunValue + col_width
                                if columnNumber == 0:
                                    xVertical = int(columnNumber/2)

                            columnNumber = columnNumber + 1
                        if len(valueScreenCols) > 0:
                            # Close the row with the separator
                            draw.text(
                                (colPixelRunValue, rowPixelRunValue),
                                column_separator,
                                font=stdfont,
                                fill=gridColor,
                            )
                            colPixelRunValue = startColValue
                        rowPixelRunValue +=  stdfont_line_height + 1
                    lineNumber = lineNumber + 1
                rowPixelRunValue += stdFont_oneLinelabel_height
            
            # Repo text
            draw.text(
                (colPixelRunValue, rowPixelRunValue + 1),
                repoText,
                font=artfont,
                fill=menuColor,
            )
            # Legend text
            rowPixelRunValue += 2 * stdFont_oneLinelabel_height + 20
            legendLines = legendText.splitlines()
            legendSeperator = "***"
            col_width_sep, _ = tools.getsize_multiline(font=artfont, srcText=legendSeperator)
            for line in legendLines:
                colPixelRunValue = startColValue
                _, artfont_line_height = tools.getsize_multiline(font=artfont, srcText=line)
                lineitems = line.split(legendSeperator)
                red = True
                for lineitem in lineitems:
                    if lineitem == "" or not red:
                        draw.text(
                            (colPixelRunValue, rowPixelRunValue),
                            legendSeperator,
                            font=artfont,
                            fill=gridColor,
                        )
                        colPixelRunValue += col_width_sep + 1
                    style = "red" if not red else gridColor
                    red = not red
                    lineitem = lineitem.replace(": ","***: ")
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        lineitem,
                        font=artfont,
                        fill=style,
                    )
                    col_width, _ = tools.getsize_multiline(font=artfont, srcText=lineitem)
                    # Move to the next text in the same line
                    colPixelRunValue += col_width + 1
                    
                # Let's go to the next line
                rowPixelRunValue += artfont_line_height + 1

            im = im.resize((int(im.size[0]*configManager.telegramImageCompressionRatio),int(im.size[1]*configManager.telegramImageCompressionRatio)), Image.LANCZOS, reducing_gap=2)
            im = tools.addQuickWatermark(im,xVertical,dataSrc="Yahoo!finance; Morningstar, Inc; National Stock Exchange of India Ltd;TradingHours.com;",dataSrcFontSize=ART_FONT_SIZE)
            im.save(filename, format=configManager.telegramImageFormat, bitmap_format=configManager.telegramImageFormat, optimize=True, quality=int(configManager.telegramImageQualityPercentage))
        except Exception as e:
            default_logger().debug(e, exc_info=True)
        # if 'RUNNER' not in os.environ.keys() and 'PKDevTools_Default_Log_Level' in os.environ.keys():
        # im.show()

    def wrapFitLegendText(table=None, backtestSummary=None, legendText=None):
        if legendText is None or len(legendText) < 1:
            return legendText
        wrapper = textwrap.TextWrapper(
            width=2
            * int(
                len(table.split("\n")[0])
                if (table is not None and len(table) > 0)
                else (len(backtestSummary.split("\n")[0]) if backtestSummary is not None else 80)
            )
        )
        if wrapper.width <= 0:
            return legendText
        word_list = wrapper.wrap(text=legendText)
        legendText_new = ""
        for ii in word_list[:-1]:
            legendText_new = legendText_new + ii + "\n"
        legendText_new += word_list[-1]
        legendText = legendText_new
        return legendText

    def getDefaultColors():
        artColors = ["blue", "indigo", "green", "red", "yellow","orange","violet"]
        bgColor = "white" if PKDateUtilities.currentDateTime().day % 2 == 0 else "black"
        gridColor = "black" if bgColor == "white" else "white"
        artColor = random.choice(artColors[3:]) if bgColor == "black" else random.choice(artColors[:3])
        menuColor = "red"
        return bgColor,gridColor,artColor,menuColor

    def setupReportFont():
        fontURL = "https://raw.githubusercontent.com/pkjmesra/pkscreener/main/pkscreener/courbd.ttf"
        fontFile = fontURL.split("/")[-1]
        bData, fontPath, _ = Archiver.findFile(fontFile)
        if bData is None:
            resp = fetcher.fetchURL(fontURL, stream=True)
            if resp is not None:
                with open(fontPath, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
            else:
                path1 = os.path.join(Archiver.get_user_outputs_dir().replace("results","pkscreener"),"courbd.ttf")
                path2 = os.path.join(os.getcwd(),"courbd.ttf")
                if os.path.isfile(path1):
                    fontPath = path1
                elif os.path.isfile(path2):
                    fontPath = path2
                else:
                    if "Windows" in platform.system():
                        fontPath = "arial.ttf"
                    elif "Darwin" in platform.system():
                        fontPath = "/System/Library/Fonts/Keyboard.ttf"
                    else:
                        fontPath = "/usr/share/fonts/truetype/freefont/FreeMono.ttf"
        return fontPath

    def getLegendHelpText(table=None,backtestSummary=None):
        legendText = "\n***1.Stock***: This is the NSE symbol/ticker for a company. Stocks that are NOT stage two, are coloured red.***2.Consol.***: It shows the price range in which stock is trading for the last 22 trading sessions(22 trading sessions per month)***3.Breakout(22Prds)***: The BO is Breakout level based on last 22 sessions. R is the resistance level (if available)."
        legendText = f"{legendText} An investor should consider both BO & R level to analyse entry / exits in their trading lessons. If the BO value is green, it means the stock has already broken out (is above BO level). If BO is in red, it means the stock is yet to break out.***4.LTP***: This is the last/latest trading/closing price of the given stock on a given date at NSE. The LTP in green/red means the"
        legendText = f"{legendText} stock price has increased / decreased since last trading session. (1.5%, 1.3%,1.8%) with LTP shows the stock price rose by 1.5%, 1.3% and 1.8% in the last 1, 2 and 3 trading sessions respectively.***5.%Chng***: This is the change(rise/fall in percentage) in closing/trading price from the previous trading session's closing price. Green means that price rose from the previous"
        legendText = f"{legendText} trading session. Red means it fell.***6.Volume***: This shows the relative volume in the most recent trading day /today with respect to last 20 trading periods moving average of Volume. For example, 8.5x would mean today's volume so far is 8.5 times the average volume traded in the last 20 trading sessions. Volume in green means that volume for the date so far has been at"
        legendText = f"{legendText} least 2.5 times more than the average volume of last 20 sessions. If the volume is in red, it means the given date's volume is less than 2.5 times the avg volume of the last 20 sessions.***7.MA-Signal***: It shows the price trend of the given stock by analyzing various 50-200 moving/exponential averages crossover strategies. Perform a Google search for the shown MA-Signals"
        legendText = f"{legendText} to learn about them more. If it is in green, the signal is bullish. Red means bearish.***8.RSI-or-RSI/i***: Relative Strength Index is a momentum index which describes 14-period relative strength at the given price. Generally, below 30 is considered oversold and above 80 is considered overbought. When RSI/i has value, say, 80/41, it means that the daily RSI value is 80 while"
        legendText = f"{legendText} the 1-minute intraday RSI is 41.***9.Trend(22Prds)***:  This describes the average trendline computed based on the last 22 trading sessions. Their strength is displayed depending on the steepness of the trendlines. (Strong / Weak) Up / Down shows how high/low the demand is respectively. A Sideways trend is the horizontal price movement that occurs when the forces of supply"
        legendText = f"{legendText} and demand are nearly equal. T:▲ or T:▼ shows the general moving average uptrend/downtrend from a 200 day MA perspective"
        legendText = f"{legendText} if the current 200DMA is more/less than the last 20/80/100 days' 200DMA. Similarly, t:▲ or t:▼ shows for 50DMA based on 9/14/20 days' 50DMA trend. MFI:▲ or MFI:▼ shows"
        legendText = f"{legendText} if the overall top 5 mutual funds and top 5 institutional investors ownership went up or down on the closing of the last month.***10.Pattern***:This shows if the chart or the candle (from the candlestick chart) is"
        legendText = f"{legendText} forming any known pattern in the recent timeframe or as per the selected screening options. Do a google search for the shown pattern names to learn.***11.CCI***: The Commodity Channel Index (CCI) is a technical indicator that measures the difference between the current price and the historical average price of the given stock. Generally below '- 100' is considered oversold"
        legendText = f"{legendText} and above 100 is considered overbought. If the CCI is < '-100' or CCI is > 100 and the Trend(22Prds) is Strong/Weak Up, it is shown in green. Otherwise it's in red.***12.1-Pd/2-Pd-etc.***: 60.29% of (413) under 1-Pd in green shows that the given scan option was correct 60.23% of the times for 413 stocks that scanner found in the last 22 trading sessions under the same scan"
        legendText = f"{legendText} options. Similarly, 61.69 % of (154) in green under 22-Pd, means we found that 61.56% of 154 stocks (~95 stocks) prices found under the same scan options increased in 22 trading periods. 57.87% of (2661) under 'Overall' means that over the last 22 trading sessions we found 2661 stock instances under the same scanning options (for example, Momentum Gainers), out of which 57.87%"
        legendText = f"{legendText} of the stock prices increased in one or more of the last 1 or 2 or 3 or 4 or 5 or 10 or 22 or 22 trading sessions. If you want to see by what percent the prices increased, you should see the details.***13.1-to-30-period-gain/loss%***: 4.17% under 1-Pd in green in the gain/loss table/grid means the stock price increased by 4.17% in the next 1 trading session. If this is in"
        legendText = f"{legendText} red, example, -5.67%, it means the price actually decreased by 5.67%. Gains are in green and losses are in red in this grid. The Date column has the date(s) on which that specific stock was found under the chosen scan options in the past 22 trading sessions.***14.52Wk-H/L***: These have 52 weeks high/low prices and will be shown in red, green or yellow based on how close the"
        legendText = f"{legendText} price is to the 52 wk high/low value.If the 52 week high/low value is within 10% of LTP:Yellow, LTP is above 52 week high:Green. If the LTP is below 90% of 52 week high:Red.***15.1-Pd-%***: Shows the 1 period gain in percent from the given date. Similarly 2-Pd-%, 3-Pd-% etc shows 2 day, 3 days gain etc.***16.1-Pd-10k***: Shows 1 period/day portfolio value if you would"
        legendText = f"{legendText} have invested 10,000 on the given date.***17.[T][_trend_]***: [T] is for Trends followed by the trend name in the filter.***18.[BO]***: This Shows the Breakout filter value from the backtest reports and will be available only if 'showpaststrategydata' configuration is turned on.***19.[P]***: [P] shows pattern name.***20.MFI***: Top 5 Mutual fund ownership and "
        legendText = f"{legendText} top 5 Institutional investor ownership status as on the last day of the last month, based on analysis from Morningstar.***21.FairValue***: Morningstar Fair value of a given stock as of last trading day as determined by 3rd party analysis based on fundamentals.***22.MCapWt%***: This shows the market-cap weighted portfolio weight to consider investing. "
        legendText = f"{legendText} ***23.Block/Bulk/Short Deals***: Ⓑ : Bulk Deals,Ⓛ: Block Deals,Ⓢ: Short deals. (B) indicates Buy, (S) indicates Sell. (1M) or (1K) indicates the quantity in million/kilo(thousand).\n"
        legendText = tools.wrapFitLegendText(table=table,backtestSummary=backtestSummary, legendText=legendText)
        # legendText = legendText.replace("***:", colorText.END + colorText.WHITE)
        # legendText = legendText.replace("***", colorText.END + colorText.FAIL)
        # return colorText.WHITE + legendText + colorText.END
        return legendText

    def getRepoHelpText(table,backtestSummary):
        repoText = f"Source: https://GitHub.com/pkjmesra/pkscreener/  | © {datetime.date.today().year} pkjmesra | Telegram: https://t.me/PKScreener |"
        disclaimer = f"The author is NOT a financial advisor and is NOT SEBI registered. This report is for learning/analysis purposes ONLY. Author assumes no responsibility or liability for any errors or omissions in this report or repository, or gain/loss bearing out of this analysis. The user MUST take advise ONLY from registered SEBI financial advisors only."
        repoText = f"{repoText}\n{tools.wrapFitLegendText(table,backtestSummary,disclaimer)}"
        repoText = f"{repoText}\n  [+] Understanding this report:\n\n"
        return repoText

    def set_github_output(name, value):
        if "GITHUB_OUTPUT" in os.environ.keys():
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                print(f"{name}={value}", file=fh)

    def afterMarketStockDataExists(intraday=False, forceLoad=False):
        curr = PKDateUtilities.currentDateTime()
        openTime = curr.replace(hour=MarketHours().openHour, minute=MarketHours().openMinute)
        cache_date = PKDateUtilities.previousTradingDate(PKDateUtilities.nextTradingDate(curr)) #curr  # for monday to friday
        weekday = curr.weekday()
        isTrading = PKDateUtilities.isTradingTime()
        if (forceLoad and isTrading) or isTrading:
            #curr = PKDateUtilities.tradingDate()
            cache_date = PKDateUtilities.previousTradingDate(curr) #curr - datetime.timedelta(1)
        # for monday to friday before market open or between market open to market close, we're backtesting
        if curr < openTime:
            cache_date = PKDateUtilities.previousTradingDate(curr) # curr - datetime.timedelta(1)
        if weekday == 0 and curr < openTime:  # for monday before market open
            cache_date = PKDateUtilities.previousTradingDate(curr) #curr - datetime.timedelta(3)
        if weekday == 5 or weekday == 6:  # for saturday and sunday
            cache_date = PKDateUtilities.previousTradingDate(curr) # curr - datetime.timedelta(days=weekday - 4)
        cache_date = cache_date.strftime("%d%m%y")
        pattern = f"{'intraday_' if intraday else ''}stock_data_"
        cache_file = pattern + str(cache_date) + ".pkl"
        exists = False
        for f in glob.glob(f"{pattern}*.pkl", root_dir=Archiver.get_user_data_dir()):
            if f.endswith(cache_file):
                exists = True
                break
        return exists, cache_file

    @Halo(text='', spinner='dots')
    def saveStockData(stockDict, configManager, loadCount, intraday=False, downloadOnly=False, forceSave=False):
        exists, fileName = tools.afterMarketStockDataExists(
            configManager.isIntradayConfig() or intraday
        )
        outputFolder = Archiver.get_user_data_dir()
        if downloadOnly:
            outputFolder = outputFolder.replace(f"results{os.sep}Data","actions-data-download")
            if not os.path.isdir(outputFolder):
                os.makedirs(os.path.dirname(f"{outputFolder}{os.sep}"), exist_ok=True)
            configManager.deleteFileWithPattern(rootDir=outputFolder)
        cache_file = os.path.join(outputFolder, fileName)
        if not os.path.exists(cache_file) or forceSave or (loadCount >= 0 and len(stockDict) > (loadCount + 1)):
            try:
                with open(cache_file, "wb") as f:
                    pickle.dump(stockDict.copy(), f, protocol=pickle.HIGHEST_PROTOCOL)
                    OutputControls().printOutput(colorText.GREEN + "=> Done." + colorText.END)
                if downloadOnly:
                    if "RUNNER" not in os.environ.keys():
                        copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{fileName}")
                        cacheFileSize = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
                        if os.path.exists(cache_file) and cacheFileSize >= 1024*1024*40:
                            shutil.copy(cache_file,copyFilePath) # copy is the saved source of truth

                    rootDirs = [Archiver.get_user_data_dir(),Archiver.get_user_indices_dir(),outputFolder]
                    patterns = ["*.csv","*.pkl"]
                    for dir in rootDirs:
                        for pattern in patterns:
                            for f in glob.glob(pattern, root_dir=dir, recursive=True):
                                OutputControls().printOutput(colorText.GREEN + f"=> {f}" + colorText.END)
                                if "RUNNER" in os.environ.keys():
                                    Committer.execOSCommand(f"git add {f} -f >/dev/null 2>&1")

            except pickle.PicklingError as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput(
                    colorText.FAIL
                    + "=> Error while Caching Stock Data."
                    + colorText.END
                )
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
        else:
            OutputControls().printOutput(
                colorText.GREEN + "=> Already Cached." + colorText.END
            )
            if downloadOnly:
                OutputControls().printOutput(colorText.GREEN + f"=> {cache_file}" + colorText.END)
        return cache_file

    @Halo(text='  [+] Downloading fresh data from Data Providers...', spinner='dots')
    def downloadLatestData(stockDict,configManager,stockCodes=[],exchangeSuffix=".NS",downloadOnly=False):
        numStocksPerIteration = (int(len(stockCodes)/int(len(stockCodes)/10)) if len(stockCodes) >= 10 else len(stockCodes)) + 1
        queueCounter = 0
        iterations = int(len(stockCodes)/numStocksPerIteration) + 1
        tasksList = []
        while queueCounter < iterations:
            stocks = []
            if queueCounter < iterations:
                stocks = stockCodes[numStocksPerIteration* queueCounter : numStocksPerIteration* (queueCounter + 1)]
            else:
                stocks = ["DUMMYStock"]#stockCodes[numStocksPerIteration* queueCounter :]
            fn_args = (stocks, configManager.period, configManager.duration,exchangeSuffix)
            task = PKTask(f"DataDownload-{queueCounter}",long_running_fn=fetcher.fetchStockDataWithArgs,long_running_fn_args=fn_args)
            task.userData = stocks
            if len(stocks) > 0:
                tasksList.append(task)
            queueCounter += 1
        
        processedStocks = []
        if len(tasksList) > 0:
            # Suppress any multiprocessing errors/warnings
            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                PKScheduler.scheduleTasks(tasksList=tasksList, 
                                        label=f"Downloading latest data [{configManager.period},{configManager.duration}] (Total={len(stockCodes)} records in {len(tasksList)} batches){'Be Patient!' if len(stockCodes)> 2000 else ''}",
                                        timeout=(5+2.5*configManager.longTimeout*(4 if downloadOnly else 1)), # 5 sec additional time for multiprocessing setup
                                        minAcceptableCompletionPercentage=(100 if downloadOnly else 100),
                                        showProgressBars=configManager.logsEnabled)
            for task in tasksList:
                if task.result is not None:
                    for stock in task.userData:
                        taskResult = task.result.get(f"{stock}{exchangeSuffix}")
                        if taskResult is not None:
                            stockDict[stock] = taskResult.to_dict("split")
                            processedStocks.append(stock)
        leftOutStocks = list(set(stockCodes)-set(processedStocks))
        default_logger().debug(f"Attempted fresh download of {len(stockCodes)} stocks and downloaded {len(processedStocks)} stocks. {len(leftOutStocks)} stocks remaining.")
        return stockDict, leftOutStocks

    def loadLargeDeals():
        shouldFetch = False
        dealsFile = os.path.join(Archiver.get_user_data_dir(),"large_deals.json")
        dealsFileSize = os.stat(dealsFile).st_size if os.path.exists(dealsFile) else 0
        if dealsFileSize > 0:
            modifiedDateTime = Archiver.get_last_modified_datetime(dealsFile)
            curr = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            shouldFetch = modifiedDateTime.date() < curr.date()
        else:
            shouldFetch = True
        if shouldFetch:
            from PKNSETools.Benny.NSE import NSE
            import json
            try:
                nseFetcher = NSE(Archiver.get_user_data_dir())
                jsonDict = nseFetcher.largeDeals()
                if jsonDict and len(jsonDict) > 0:
                    with open(dealsFile,"w") as f:
                        f.write(json.dumps(jsonDict))
            except Exception as e:
                default_logger().debug(e,exc_info=True)
                pass

    def loadStockData(
        stockDict,
        configManager,
        downloadOnly=False,
        defaultAnswer=None,
        retrial=False,
        forceLoad=False,
        stockCodes=[],
        exchangeSuffix=".NS",
        isIntraday = False,
        forceRedownload=False,
        userDownloadOption=None
    ):
        isIntraday = isIntraday or configManager.isIntradayConfig()
        exists, cache_file = tools.afterMarketStockDataExists(
            isIntraday, forceLoad=forceLoad
        )
        initialLoadCount = len(stockDict)
        leftOutStocks = None
        recentDownloadFromOriginAttempted = False
        isTrading = PKDateUtilities.isTradingTime() and (PKDateUtilities.wasTradedOn() or not PKDateUtilities.isTodayHoliday()[0])
        if userDownloadOption is not None and "B" in userDownloadOption: # Backtests
            isTrading = False
        # Check if NSEI data is requested
        if configManager.baseIndex not in stockCodes:
            stockCodes.insert(0,configManager.baseIndex)
        # stockCodes is not None mandates that we start our work based on the downloaded data from yesterday
        if (stockCodes is not None and len(stockCodes) > 0) and (isTrading or downloadOnly):
            recentDownloadFromOriginAttempted = True
            stockDict, leftOutStocks = tools.downloadLatestData(stockDict,configManager,stockCodes,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly)
            if len(leftOutStocks) > int(len(stockCodes)*0.05):
                # More than 5 % of stocks are still remaining
                stockDict, _ = tools.downloadLatestData(stockDict,configManager,leftOutStocks,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly)
            # return stockDict
        if downloadOnly or isTrading:
            # We don't want to download from local stale pkl file or stale file at server
            return stockDict
        
        default_logger().debug(
            f"Stock data cache file:{cache_file} exists ->{str(exists)}"
        )
        stockDataLoaded = False
        copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
        if os.path.exists(copyFilePath):
            shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
        if os.path.exists(srcFilePath) and not forceRedownload:
            stockDict, stockDataLoaded = tools.loadDataFromLocalPickle(stockDict,configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading)
        if (
            not stockDataLoaded
            and ("1d" if isIntraday else ConfigManager.default_period)
            == configManager.period
            and ("1m" if isIntraday else ConfigManager.default_duration)
            == configManager.duration
        ) or forceRedownload:
            stockDict, stockDataLoaded = tools.downloadSavedDataFromServer(stockDict,configManager, downloadOnly, defaultAnswer, retrial, forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, cache_file, isTrading)
        if not stockDataLoaded:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] Cache unavailable on pkscreener server, Continuing.."
                + colorText.END
            )
        if not stockDataLoaded and not recentDownloadFromOriginAttempted:
            stockDict, _ = tools.downloadLatestData(stockDict,configManager,stockCodes,exchangeSuffix=exchangeSuffix,downloadOnly=downloadOnly)
        # See if we need to save stock data
        stockDataLoaded = stockDataLoaded or (len(stockDict) > 0 and (len(stockDict) != initialLoadCount))
        if stockDataLoaded:
            tools.saveStockData(stockDict,configManager,initialLoadCount,isIntraday,downloadOnly, forceSave=stockDataLoaded)
        return stockDict

    @Halo(text='  [+] Loading data from local cache...', spinner='dots')
    def loadDataFromLocalPickle(stockDict, configManager, downloadOnly, defaultAnswer, exchangeSuffix, cache_file, isTrading):
        stockDataLoaded = False
        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
        with open(srcFilePath, "rb") as f:
            try:
                stockData = pickle.load(f)
                if not downloadOnly:
                    OutputControls().printOutput(
                            colorText.GREEN
                            + f"\n  [+] Automatically Using Cached Stock Data {'due to After-Market hours' if not PKDateUtilities.isTradingTime() else ''}!"
                            + colorText.END
                        )
                if stockData is not None and len(stockData) > 0:
                    multiIndex = stockData.keys()
                    if isinstance(multiIndex, pd.MultiIndex):
                            # If we requested for multiple stocks from yfinance
                            # we'd have received a multiindex dataframe
                        listStockCodes = multiIndex.get_level_values(0)
                        listStockCodes = sorted(list(filter(None,list(set(listStockCodes)))))
                        if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                            listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                    else:
                        listStockCodes = list(stockData.keys())
                        if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                            listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                    for stock in listStockCodes:
                        df_or_dict = stockData.get(stock)
                        df_or_dict = df_or_dict.to_dict("split") if isinstance(df_or_dict,pd.DataFrame) else df_or_dict
                            # This will keep all the latest security data we downloaded
                            # just now and also copy the additional data like, MF/FII,FairValue
                            # etc. data, from yesterday's saved data.
                        try:
                            existingPreLoadedData = stockDict.get(stock)
                            if existingPreLoadedData is not None:
                                if isTrading:
                                        # Only copy the MF/FII/FairValue data and leave the stock prices as is.
                                    cols = ["MF", "FII","MF_Date","FII_Date","FairValue"]
                                    for col in cols:
                                        existingPreLoadedData[col] = df_or_dict.get(col)
                                    stockDict[stock] = existingPreLoadedData
                                else:
                                    stockDict[stock] = df_or_dict | existingPreLoadedData
                            else:
                                if not isTrading:
                                    stockDict[stock] = df_or_dict
                        except:
                                # Probably, the "stock" got removed from the latest download
                                # and so, was not found in stockDict
                            continue
                    # if len(stockDict) > 0:
                    #     stockDict = stockDict | stockData
                    # else:
                    #     stockDict = stockData
                    stockDataLoaded = True
            except pickle.UnpicklingError as e:
                default_logger().debug(e, exc_info=True)
                f.close()
                OutputControls().printOutput(
                        colorText.FAIL
                        + "  [+] Error while Reading Stock Cache. Press <Enter> to continue..."
                        + colorText.END
                    )
                if tools.promptFileExists(defaultAnswer=defaultAnswer) == "Y":
                    configManager.deleteFileWithPattern()
            except EOFError as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                f.close()
                OutputControls().printOutput(
                        colorText.FAIL
                        + "  [+] Stock Cache Corrupted."
                        + colorText.END
                    )
                if tools.promptFileExists(defaultAnswer=defaultAnswer) == "Y":
                    configManager.deleteFileWithPattern()
        return stockDict, stockDataLoaded

    @Halo(text='', spinner='dots')
    def tryFetchFromServer(cache_file,repoOwner="pkjmesra",repoName="PKScreener",directory="actions-data-download",hideOutput=False):
        if not hideOutput:
            OutputControls().printOutput(
                        colorText.FAIL
                        + "[+] Loading data from server. Market Stock Data is not cached, or forced to redownload .."
                        + colorText.END
                    )
            OutputControls().printOutput(
                    colorText.GREEN
                    + f"  [+] Downloading {colorText.END}{colorText.FAIL}{'Intraday' if configManager.isIntradayConfig() else 'Daily'}{colorText.END}{colorText.GREEN} cache from server ({'Primary' if repoOwner=='pkjmesra' else 'Secondary'}) for faster processing, Please Wait.."
                    + colorText.END
                )
        cache_url = (
                f"https://raw.githubusercontent.com/{repoOwner}/{repoName}/actions-data-download/{directory}/"
                + cache_file  # .split(os.sep)[-1]
            )
        headers = {
                    'authority': 'raw.githubusercontent.com',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'dnt': '1',
                    'sec-ch-ua-mobile': '?0',
                    # 'sec-ch-ua-platform': '"macOS"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',                  
                    'origin': 'https://github.com',
                    'referer': f'https://github.com/{repoOwner}/{repoName}/blob/actions-data-download/{directory}/{cache_file}',
                    'user-agent': f'{random_user_agent()}' 
                    #'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
            }
        resp = fetcher.fetchURL(cache_url, headers=headers, stream=True)
        if resp is None or (resp is not None and resp.status_code != 200 and repoOwner=="pkjmesra"):
            return tools.tryFetchFromServer(cache_file,repoOwner=repoName)
        return resp

    @Halo(text='', spinner='dots')
    def downloadSavedDefaultsFromServer(cache_file):
        fileDownloaded = False
        resp = tools.tryFetchFromServer(cache_file)
        if resp is not None:
            default_logger().debug(
                    f"Stock data cache file:{cache_file} request status ->{resp.status_code}"
                )
        if resp is not None and resp.status_code == 200:
            contentLength = resp.headers.get("content-length")
            serverBytes = int(contentLength) if contentLength is not None else 0
            KB = 1024
            MB = KB * 1024
            chunksize = MB if serverBytes >= MB else (KB if serverBytes >= KB else 1)
            filesize = int( serverBytes / chunksize)
            if filesize > 40: #Something definitely went wrong. It should be upward of 40bytes
                try:
                    with open(os.path.join(Archiver.get_user_data_dir(), cache_file),"w+",) as f: # .split(os.sep)[-1]
                        f.write(resp.text)
                    fileDownloaded = True
                except:
                    pass
        return fileDownloaded

    def downloadSavedDataFromServer(stockDict, configManager, downloadOnly, defaultAnswer, retrial, forceLoad, stockCodes, exchangeSuffix, isIntraday, forceRedownload, cache_file, isTrading):
        stockDataLoaded = False
        resp = tools.tryFetchFromServer(cache_file)
        if resp is not None:
            default_logger().debug(
                    f"Stock data cache file:{cache_file} request status ->{resp.status_code}"
                )
        if resp is not None and resp.status_code == 200:
            contentLength = resp.headers.get("content-length")
            serverBytes = int(contentLength) if contentLength is not None else 0
            KB = 1024
            MB = KB * 1024
            chunksize = MB if serverBytes >= MB else (KB if serverBytes >= KB else 1)
            filesize = int( serverBytes / chunksize)
            if filesize > 40 and chunksize == MB: # Saved data can't be in KBs. Something definitely went wrong. It should be upward of 40MB
                bar, spinner = tools.getProgressbarStyle()
                try:
                    f = open(
                            os.path.join(Archiver.get_user_data_dir(), cache_file),
                            "w+b",
                        )  # .split(os.sep)[-1]
                    dl = 0
                    with alive_bar(
                            filesize, bar=bar, spinner=spinner, manual=True
                        ) as progressbar:
                        for data in resp.iter_content(chunk_size=chunksize):
                            dl += 1
                            f.write(data)
                            progressbar(dl / filesize)
                            if dl >= filesize:
                                progressbar(1.0)
                    f.close()
                    with open(
                            os.path.join(Archiver.get_user_data_dir(), cache_file),
                            "rb",
                        ) as f:
                        stockData = pickle.load(f)
                    if len(stockData) > 0:
                        multiIndex = stockData.keys()
                        if isinstance(multiIndex, pd.MultiIndex):
                                # If we requested for multiple stocks from yfinance
                                # we'd have received a multiindex dataframe
                            listStockCodes = multiIndex.get_level_values(0)
                            listStockCodes = sorted(list(filter(None,list(set(listStockCodes)))))
                            if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                                listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                        else:
                            listStockCodes = list(stockData.keys())
                            if len(listStockCodes) > 0 and len(exchangeSuffix) > 0 and exchangeSuffix in listStockCodes[0]:
                                listStockCodes = [x.replace(exchangeSuffix,"") for x in listStockCodes]
                        for stock in listStockCodes:
                            df_or_dict = stockData.get(stock)
                            df_or_dict = df_or_dict.to_dict("split") if isinstance(df_or_dict,pd.DataFrame) else df_or_dict
                                # This will keep all the latest security data we downloaded
                                # just now and also copy the additional data like, MF/FII,FairValue
                                # etc. data, from yesterday's saved data.
                            try:
                                existingPreLoadedData = stockDict.get(stock)
                                if existingPreLoadedData is not None:
                                    if isTrading:
                                            # Only copy the MF/FII/FairValue data and leave the stock prices as is.
                                        cols = ["MF", "FII","MF_Date","FII_Date","FairValue"]
                                        for col in cols:
                                            existingPreLoadedData[col] = df_or_dict.get(col)
                                        stockDict[stock] = existingPreLoadedData
                                    else:
                                        stockDict[stock] = df_or_dict | existingPreLoadedData
                                else:
                                    if not isTrading:
                                        stockDict[stock] = df_or_dict
                            except:
                                    # Probably, the "stock" got removed from the latest download
                                    # and so, was not found in stockDict
                                continue
                        stockDataLoaded = True
                        copyFilePath = os.path.join(Archiver.get_user_data_dir(), f"copy_{cache_file}")
                        srcFilePath = os.path.join(Archiver.get_user_data_dir(), cache_file)
                        if os.path.exists(copyFilePath) and os.path.exists(srcFilePath):
                            shutil.copy(copyFilePath,srcFilePath) # copy is the saved source of truth
                        if not os.path.exists(copyFilePath) and os.path.exists(srcFilePath): # Let's make a copy of the original one
                            shutil.copy(srcFilePath,copyFilePath)
                        # Remove the progress bar now!
                        OutputControls().moveCursorUpLines(1)
                except Exception as e:  # pragma: no cover
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    OutputControls().printOutput("[!] Download Error - " + str(e))
            else:
                default_logger().debug(
                        f"Stock data cache file:{cache_file} on server has length ->{filesize} {'Mb' if chunksize >= MB else ('Kb' if chunksize >= KB else 'bytes')}"
                    )
            if not retrial and not stockDataLoaded:
                    # Don't try for more than once.
                stockDict = tools.loadStockData(
                        stockDict,
                        configManager,
                        downloadOnly,
                        defaultAnswer,
                        retrial=True,
                        forceLoad=forceLoad,
                        stockCodes=stockCodes,
                        exchangeSuffix=exchangeSuffix,
                        isIntraday = isIntraday,
                        forceRedownload=forceRedownload
                    )
                
        return stockDict,stockDataLoaded

    def make_hyperlink(value):
        url = "https://in.tradingview.com/chart?symbol=NSE:{}"
        return '=HYPERLINK("%s", "%s")' % (url.format(tools.stockNameFromDecoratedName(value)), value)

    # Save screened results to excel
    def promptSaveResults(sheetName,df_save, defaultAnswer=None,pastDate=None,screenResults=None):
        """
        Tries to save the dataframe output into an excel file.

        It will first try to save to the current-working-directory/results/

        If it fails to save, it will then try to save to Desktop and then eventually into
        a temporary directory.
        """
        data = df_save.copy()
        try:
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)
            data = tools.removeAllColorStyles(data)
        except Exception as e:
            default_logger().debug(e,exc_info=True)
            pass
        try:
            data.reset_index(inplace=True)
            with pd.option_context('mode.chained_assignment', None):
                data["Stock"] = data['Stock'].apply(tools.make_hyperlink)
            data.set_index("Stock", inplace=True)
        except:
            pass
        df = data
        isSaved = False
        try:
            if defaultAnswer is None:
                responseLegends = str(
                        OutputControls().takeUserInput(
                            colorText.WARN
                            + f"[>] Do you want to review legends used in the report above? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): ",defaultInput="N"
                        ) or "N"
                    ).upper()
                if "Y" in responseLegends:
                    OutputControls().printOutput(tools.getLegendHelpText(table=None).replace("***:",colorText.END+":").replace("***"," " +colorText.FAIL))
                if not configManager.alwaysExportToExcel:
                    response = str(
                        input(
                            colorText.WARN
                            + f"[>] Do you want to save the results in excel file? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): "
                        ) or "N"
                    ).upper()
                else:
                    response = "Y"
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            response = "Y"
        if response is not None and response.upper() != "N":
            pastDateString = f"{pastDate}_to_" if pastDate is not None else ""
            filename = (
                f"PKS_{sheetName.strip()}_"
                + pastDateString
                + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
                + ".xlsx"
            )
            desktop = os.path.expanduser("~/Desktop")
            # # the above is valid on Windows (after 7) but if you want it in os normalized form:
            desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
            filePath = ""
            try:
                filePath = os.path.join(Archiver.get_user_reports_dir(), filename)
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                # Convert the dataframe to an XlsxWriter Excel object.
                df.to_excel(writer, sheet_name=sheetName[-31:]) # sheetname cannot be beyond 31 character
                # Close the Pandas Excel writer and output the Excel file.
                writer.close()
                isSaved = True
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                OutputControls().printOutput(
                    colorText.FAIL
                    + (
                        "  [+] Error saving file at %s"
                        % filePath
                    )
                    + colorText.END
                )
                try:
                    filePath = os.path.join(desktop, filename)
                    # Create a Pandas Excel writer using XlsxWriter as the engine.
                    writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                    # Convert the dataframe to an XlsxWriter Excel object.
                    df.to_excel(writer, sheet_name=sheetName)
                    # Close the Pandas Excel writer and output the Excel file.
                    writer.close()
                    isSaved = True
                except Exception as ex:  # pragma: no cover
                    default_logger().debug(ex, exc_info=True)
                    OutputControls().printOutput(
                        colorText.FAIL
                        + (
                            "  [+] Error saving file at %s"
                            % filePath
                        )
                        + colorText.END
                    )
                    filePath = os.path.join(tempfile.gettempdir(), filename)
                    # Create a Pandas Excel writer using XlsxWriter as the engine.
                    writer = pd.ExcelWriter(filePath, engine='xlsxwriter') # openpyxl throws an error exporting % sign.
                    # Convert the dataframe to an XlsxWriter Excel object.
                    df.to_excel(writer, sheet_name=sheetName)
                    # Close the Pandas Excel writer and output the Excel file.
                    writer.close()
                    isSaved = True
            OutputControls().printOutput(
                (colorText.GREEN if isSaved else colorText.FAIL)
                + (("  [+] Results saved to %s" % filePath) if isSaved else "  [+] Failed saving results into Excel file!")
                + colorText.END
            )
            return filePath
        return None

    # Save screened results to excel
    def promptFileExists(cache_file="stock_data_*.pkl", defaultAnswer=None):
        try:
            if defaultAnswer is None:
                response = str(
                    input(
                        colorText.WARN
                        + "[>] "
                        + cache_file
                        + " already exists. Do you want to replace this? [Y/N] (Default: Y): "
                ) or "Y").upper()
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        return "Y" if response != "N" else "N"

    # Prompt for asking RSI
    def promptRSIValues():
        tools.clearScreen(forceTop=True)
        try:
            minRSI, maxRSI = int(
                input(
                    colorText.WARN
                    + "\n  [+] Enter Min RSI value (Default=55): "
                    + colorText.END
                ) or 55
            ), int(
                input(
                    colorText.WARN
                    + "  [+] Enter Max RSI value (Default=68): "
                    + colorText.END
                ) or "68"
            )
            if (
                (minRSI >= 0 and minRSI <= 100)
                and (maxRSI >= 0 and maxRSI <= 100)
                and (minRSI <= maxRSI)
            ):
                return (minRSI, maxRSI)
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return (0, 0)

    # Prompt for asking CCI
    def promptCCIValues(minCCI=None, maxCCI=None):
        tools.clearScreen(forceTop=True)
        if minCCI is not None and maxCCI is not None:
            return minCCI, maxCCI
        try:
            minCCI, maxCCI = int(
                input(
                    colorText.WARN
                    + "\n  [+] Enter Min CCI value (Default=110): "
                    + colorText.END
                ) or "110"
            ), int(
                input(
                    colorText.WARN
                    + "  [+] Enter Max CCI value (Default=300): "
                    + colorText.END
                ) or "300"
            )
            if minCCI <= maxCCI:
                return (minCCI, maxCCI)
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return (-100, 100)

    # Prompt for asking Volume ratio
    def promptVolumeMultiplier(volumeRatio=None):
        tools.clearScreen(forceTop=True)
        if volumeRatio is not None:
            return volumeRatio
        try:
            volumeRatio = float(
                input(
                    colorText.WARN
                    + "\n  [+] Enter Min Volume ratio value (Default = 2.5): "
                    + colorText.END
                ) or "2.5"
            )
            if volumeRatio > 0:
                return volumeRatio
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return 2

    def promptMenus(menu):
        tools.clearScreen(forceTop=True)
        m = menus()
        m.level = menu.level if menu is not None else 0
        return m.renderForMenu(menu)

    def promptChartPatternSubMenu(menu,respChartPattern):
        tools.clearScreen(forceTop=True)
        m3 = menus()
        m3.renderForMenu(menu,asList=True)
        lMenu =  m3.find(str(respChartPattern))
        maLength = tools.promptSubMenuOptions(lMenu,defaultOption= "4" if respChartPattern == 3 else "1" )
        return maLength
    
    # Prompt for submenu options
    def promptSubMenuOptions(menu=None, defaultOption="1"):
        try:
            tools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.WARN
                    + """  [+] Select Option:"""
                    + colorText.END
                ) or defaultOption
            )
            if resp >= 0 and resp <= 10:
                return resp
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().takeUserInput(
                colorText.FAIL
                + "\n  [+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return None

    # Prompt for Reversal screening
    def promptReversalScreening(menu=None):
        try:
            tools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.WARN
                    + """  [+] Select Option:"""
                    + colorText.END
                ) or "3"
            )
            if resp >= 0 and resp <= 10:
                if resp == 4:
                    try:
                        defaultMALength = 9 if configManager.duration.endswith("m") else 50
                        maLength = int(
                            input(
                                colorText.WARN
                                + f"\n  [+] Enter MA Length (E.g. 9,10,20,50 or 200) (Default={defaultMALength}): "
                                + colorText.END
                            ) or str(defaultMALength)
                        )
                        return resp, maLength
                    except ValueError as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        OutputControls().printOutput(
                            colorText.FAIL
                            + "\n[!] Invalid Input! MA Length should be single integer value!\n"
                            + colorText.END
                        )
                        raise ValueError
                elif resp == 6:
                    try:
                        maLength = int(
                            input(
                                colorText.WARN
                                + "\n  [+] Enter NR timeframe [Integer Number] (E.g. 4, 7, etc.) (Default=4): "
                                + colorText.END
                            ) or "4"
                        )
                        return resp, maLength
                    except ValueError as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        OutputControls().printOutput(
                            colorText.FAIL
                            + "\n[!] Invalid Input! NR timeframe should be single integer value!\n"
                            + colorText.END
                        )
                        raise ValueError
                elif resp in [7,10]:
                    m3 = menus()
                    m3.renderForMenu(menu,asList=True)
                    lMenu =  m3.find(str(resp))
                    return resp, tools.promptSubMenuOptions(lMenu)
                return resp, None
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().takeUserInput(
                colorText.FAIL
                + "\n  [+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return None, None

    # Prompt for Reversal screening
    def promptChartPatterns(menu=None):
        try:
            tools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.WARN
                    + """  [+] Select Option:"""
                    + colorText.END
                ) or "3"
            )
            if resp == 1 or resp == 2:
                candles = int(
                    input(
                        colorText.WARN
                        + "\n  [+] How many candles (TimeFrame) to look back Inside Bar formation? (Default=3): "
                        + colorText.END
                    ) or "3"
                )
                return (resp, candles)
            if resp == 3:
                percent = float(
                    input(
                        colorText.WARN
                        + "\n  [+] Enter Percentage within which all MA/EMAs should be (Ideal: 0.1-2%)? (Default=0.8): "
                        + colorText.END
                    ) or "0.8"
                )
                return (resp, percent / 100.0)
            if resp >= 0 and resp <= 9:
                return resp, 0
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().takeUserInput(
                colorText.FAIL
                + "\n  [+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return (None, None)

    def getProgressbarStyle():
        bar = "smooth"
        spinner = "waves"
        if "Windows" in platform.platform():
            bar = "classic2"
            spinner = "dots_recur"
        return bar, spinner

    @Halo(text='', spinner='dots')
    def getNiftyModel(retrial=False):
        if "Windows" in platform.system() and not 'pytest' in sys.modules:
            try:
                sys.stdin.reconfigure(encoding='utf-8')
                sys.stdout.reconfigure(encoding='utf-8')
            except:
                pass
        files = [
            os.path.join(Archiver.get_user_data_dir(), "nifty_model_v2.h5"),
            os.path.join(Archiver.get_user_data_dir(), "nifty_model_v2.pkl"),
        ]
        model = None
        pkl = None
        urls = [
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/main/pkscreener/ml/nifty_model_v2.h5",
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/main/pkscreener/ml/nifty_model_v2.pkl",
        ]
        if os.path.isfile(files[0]) and os.path.isfile(files[1]):
            file_age = (time.time() - os.path.getmtime(files[0])) / 604800
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
                resp = fetcher.fetchURL(file_url, stream=True)
                if resp is not None and resp.status_code == 200:
                    OutputControls().printOutput(
                        colorText.GREEN
                        + "  [+] Downloading AI model (v2) for Nifty predictions, Please Wait.."
                        + colorText.END
                    )
                    try:
                        chunksize = 1024 * 1024 * 1
                        filesize = int(
                            int(resp.headers.get("content-length")) / chunksize
                        )
                        filesize = 1 if not filesize else filesize
                        bar, spinner = tools.getProgressbarStyle()
                        f = open(
                            os.path.join(
                                Archiver.get_user_data_dir(), file_url.split("/")[-1]
                            ),
                            "wb"
                        )
                        dl = 0
                        # with alive_bar(
                        #     filesize, bar=bar, spinner=spinner, manual=True
                        # ) as progressbar:
                        for data in resp.iter_content(chunk_size=chunksize):
                            dl += 1
                            f.write(data)
                                # progressbar(dl / filesize)
                                # if dl >= filesize:
                                #     progressbar(1.0)
                        f.close()
                    except Exception as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        OutputControls().printOutput("[!] Download Error - " + str(e))
            time.sleep(3)
        try:
            if os.path.isfile(files[0]) and os.path.isfile(files[1]):
                pkl = joblib.load(files[1])
                if Imports["keras"]:
                    try:
                        import keras
                    except:
                        OutputControls().printOutput("This installation might not work well, especially for NIFTY prediction. Please install 'keras' library on your machine!")
                        OutputControls().printOutput(
                                colorText.FAIL
                                + "  [+] 'Keras' library is not installed. You may wish to follow instructions from\n  [+] https://github.com/pkjmesra/PKScreener/"
                                + colorText.END
                            )
                        pass
                model = keras.models.load_model(files[0]) if Imports["keras"] else None
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            os.remove(files[0])
            os.remove(files[1])
            if not retrial:
                tools.getNiftyModel(retrial=True)
        if model is None:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] 'Keras' library is not installed. Prediction failed! You may wish to follow instructions from\n  [+] https://github.com/pkjmesra/PKScreener/"
                + colorText.END
            )
        return model, pkl

    def getSigmoidConfidence(x):
        out_min, out_max = 0, 100
        if x > 0.5:
            in_min = 0.50001
            in_max = 1
        else:
            in_min = 0
            in_max = 0.5
        return round(
            ((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min), 3
        )

    def alertSound(beeps=3, delay=0.2):
        for i in range(beeps):
            OutputControls().printOutput("\a")
            sleep(delay)
    
    def getMaxColumnWidths(df):
        columnWidths = [None]
        addnlColumnWidths = [40 if (x in ["Trend(22Prds)"] or "-Pd" in x) else (20 if (x in ["Pattern"]) else ((25 if (x in ["MA-Signal"]) else (10 if "ScanOption" in x else None)))) for x in df.columns]
        columnWidths.extend(addnlColumnWidths)
        columnWidths = columnWidths[:-1]
        return columnWidths