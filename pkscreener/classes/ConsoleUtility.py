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
import platform
import pandas as pd

from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.Utils import random_user_agent

from pkscreener.classes import VERSION, Changelog, Utility
from pkscreener.classes.ArtTexts import getArtText
from pkscreener.classes.Utility import marketStatus,STD_ENCODING,lastScreened
import pkscreener.classes.Fetcher as Fetcher

# Class for managing misc image utility methods
class PKConsoleTools:
    
    fetcher = Fetcher.screenerStockDataFetcher()
    def clearScreen(userArgs=None,clearAlways=False,forceTop=False):
        timeit = 'timeit' in os.environ.keys()
        if timeit:
            return
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
                except: # pragma: no cover
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
                except: # pragma: no cover
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
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
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
        freeInfo = "[💰] PKScreener had been free for a long time"
        donationInfo = ", but owing to cost/budgeting issues, only a basic set of features will always remain free for everyone. Consider donating to help cover the basic server costs or subscribe to premium.\n[💸] Please donate whatever you can: PKScreener@APL using UPI(India) or https://github.com/sponsors/pkjmesra 🙏🏻"
        totalDownloads = "200k+"
        respPepyTech = PKConsoleTools.fetcher.fetchURL(url="https://static.pepy.tech/badge/pkscreener",headers={'user-agent': f'{random_user_agent()}'},timeout=2)
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
        OutputControls().printOutput(colorText.GREEN + freeInfo + colorText.END + colorText.FAIL + donationInfo + colorText.END)
        if defaultAnswer is None:
            OutputControls().takeUserInput(
                colorText.FAIL
                + "  [+] Press <Enter> to continue!"
                + colorText.END
            )
        return f"\n{Changelog.changelog()}\n\n{devInfo}\n{versionInfo}\n\n{downloadsInfo}\n{homePage}\n{issuesInfo}\n{communityInfo}\n{latestInfo}\n{freeInfo}{donationInfo}"

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
        except IOError as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + f"{e}\n  [+] Failed to save recently screened result table on disk! Skipping.."
                + colorText.END
            )
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
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
                df.sort_values(by=["volume" if "volume" in df.keys() else df.keys()[0]], ascending=False, inplace=True)
                OutputControls().printOutput(
                    colorText.miniTabulator().tabulate(
                        df, headers="keys", tablefmt=colorText.No_Pad_GridFormat,
                        maxcolwidths=Utility.tools.getMaxColumnWidths(df)
                    ).encode("utf-8").decode(STD_ENCODING)
                )
                OutputControls().printOutput(
                    colorText.WARN
                    + "  [+] Note: Trend calculation is based on number of recent days to screen as per your configuration."
                    + colorText.END
                )
            else:
                OutputControls().printOutput("Nothing to show here!")
        except FileNotFoundError as e: # pragma: no cover
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
                    PKConsoleTools.formattedBacktestOutput(
                        float(values[0]), pnlStats=pnlStats, htmlOutput=False
                    ),
                    values[1],
                )
        return x
