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

import datetime
import glob
import math
import os
import textwrap

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["AUTOGRAPH_VERBOSITY"] = "0"

import pickle
import platform
import tempfile
import time

import joblib
import numpy as np
import pytz
from genericpath import isfile
from PKDevTools.classes.log import default_logger

from pkscreener import Imports

if Imports["keras"]:
    import keras

import warnings
from time import sleep

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
from alive_progress import alive_bar
from PIL import Image, ImageDraw, ImageFont
from PKDevTools.classes import Archiver
from PKDevTools.classes.ColorText import colorText
from requests_cache import CachedSession
from tabulate import tabulate

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
from pkscreener.classes import VERSION, Changelog
from pkscreener.classes.MenuOptions import menus

session = CachedSession(
    cache_name=f"{Archiver.get_user_outputs_dir().split(os.sep)[-1]}{os.sep}PKDevTools_cache",
    db_path=os.path.join(Archiver.get_user_outputs_dir(), "PKDevTools_cache.sqlite"),
    cache_control=True,
)
fetcher = Fetcher.screenerStockDataFetcher(ConfigManager.tools())
artText = """
PPPPPPPPPPPPPPPPP   KKKKKKKKK    KKKKKKK   SSSSSSSSSSSSSSS                                                                                                                                         TM
UPI:8007162973@APL  K:::::::K    K:::::K SS:::::::::::::::S
P::::::PPPPPP:::::P K:::::::K    K:::::KS:::::SSSSSS::::::S
PP:::::P     P:::::PK:::::::K   K::::::KS:::::S     SSSSSSS
  P::::P     P:::::PKK::::::K  K:::::KKKS:::::S                ccccccccccccccccrrrrr   rrrrrrrrr       eeeeeeeeeeee        eeeeeeeeeeee    nnnn  nnnnnnnn        eeeeeeeeeeee    rrrrr   rrrrrrrrr
  P::::P     P:::::P  K:::::K K:::::K   S:::::S              cc:::::::::::::::cr::::rrr:::::::::r    ee::::::::::::ee    ee::::::::::::ee  n:::nn::::::::nn    ee::::::::::::ee  r::::rrr:::::::::r
  P::::PPPPPP:::::P   K::::::K:::::K     S::::SSSS          c:::::::::::::::::cr:::::::::::::::::r  e::::::eeeee:::::ee e::::::eeeee:::::een::::::::::::::nn  e::::::eeeee:::::eer:::::::::::::::::r
  P:::::::::::::PP    K:::::::::::K       SS::::::SSSSS    c:::::::cccccc:::::crr::::::rrrrr::::::re::::::e     e:::::ee::::::e     e:::::enn:::::::::::::::ne::::::e     e:::::err::::::rrrrr::::::r
  P::::PPPPPPPPP      K:::::::::::K         SSS::::::::SS  c::::::c     ccccccc r:::::r     r:::::re:::::::eeeee::::::ee:::::::eeeee::::::e  n:::::nnnn:::::ne:::::::eeeee::::::e r:::::r     r:::::r
  P::::P              K::::::K:::::K           SSSSSS::::S c:::::c              r:::::r     rrrrrrre:::::::::::::::::e e:::::::::::::::::e   n::::n    n::::ne:::::::::::::::::e  r:::::r     rrrrrrr
  P::::P              K:::::K K:::::K               S:::::Sc:::::c              r:::::r            e::::::eeeeeeeeeee  e::::::eeeeeeeeeee    n::::n    n::::ne::::::eeeeeeeeeee   r:::::r
  P::::P            KK::::::K  K:::::KKK            S:::::Sc::::::c     ccccccc r:::::r            e:::::::e           e:::::::e             n::::n    n::::ne:::::::e            r:::::r
PP::::::PP          K:::::::K   K::::::KSSSSSSS     S:::::Sc:::::::cccccc:::::c r:::::r            e::::::::e          e::::::::e            n::::n    n::::ne::::::::e           r:::::r
P::::::::P          K:::::::K    K:::::KS::::::SSSSSS:::::S c:::::::::::::::::c r:::::r             e::::::::eeeeeeee   e::::::::eeeeeeee    n::::n    n::::n e::::::::eeeeeeee   r:::::r
P::::::::P          K:::::::K    K:::::KS:::::::::::::::SS   cc:::::::::::::::c r:::::r              ee:::::::::::::e    ee:::::::::::::e    n::::n    n::::n  ee:::::::::::::e   r:::::r
PPPPPPPPPP          KKKKKKKKK    KKKKKKK SSSSSSSSSSSSSSS       cccccccccccccccc rrrrrrr                eeeeeeeeeeeeee      eeeeeeeeeeeeee    nnnnnn    nnnnnn    eeeeeeeeeeeeee   rrrrrrr
"""
artText = f"{artText}\nv{VERSION}"
art = colorText.GREEN + artText + colorText.END

lastScreened = os.path.join(
    Archiver.get_user_outputs_dir(), "last_screened_results.pkl"
)

# Class for managing misc and utility methods


class tools:
    def clearScreen():
        if platform.system() == "Windows":
            os.system("cls")
        else:
            os.system("clear")
        print(art)

    # Print about developers and repository
    def showDevInfo(defaultAnswer=None):
        print("\n" + Changelog.changelog())
        devInfo = "\n[+] Developer: PK (PKScreener)"
        versionInfo = "[+] Version: %s" % VERSION
        homePage = "[+] Home Page: https://github.com/pkjmesra/PKScreener\nTelegram Bot:@nse_pkscreener_bot\nChannel:https://t.me/PKScreener\nDiscussions:https://t.me/PKScreeners"
        issuesInfo = (
            "[+] Read/Post Issues here: https://github.com/pkjmesra/PKScreener/issues"
        )
        communityInfo = "[+] Join Community Discussions: https://github.com/pkjmesra/PKScreener/discussions"
        latestInfo = "[+] Download latest software from https://github.com/pkjmesra/PKScreener/releases/latest"
        print(colorText.BOLD + colorText.WARN + devInfo + colorText.END)
        print(colorText.BOLD + colorText.WARN + versionInfo + colorText.END)
        print(colorText.BOLD + homePage + colorText.END)
        print(colorText.BOLD + colorText.FAIL + issuesInfo + colorText.END)
        print(colorText.BOLD + colorText.GREEN + communityInfo + colorText.END)
        print(colorText.BOLD + colorText.BLUE + latestInfo + colorText.END)
        if defaultAnswer != "Y":
            input(
                colorText.BOLD
                + colorText.FAIL
                + "[+] Press <Enter> to continue!"
                + colorText.END
            )
        return f"\n{Changelog.changelog()}\n\n{devInfo}\n{versionInfo}\n\n{homePage}\n{issuesInfo}\n{communityInfo}\n{latestInfo}"

    # Save last screened result to pickle file
    def setLastScreenedResults(df):
        try:
            df.sort_values(by=["Stock"], ascending=True, inplace=True)
            df.to_pickle(lastScreened)
        except IOError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            input(
                colorText.BOLD
                + colorText.FAIL
                + "[+] Failed to save recently screened result table on disk! Skipping.."
                + colorText.END
            )

    # Load last screened result to pickle file
    def getLastScreenedResults():
        try:
            df = pd.read_pickle(lastScreened)
            print(
                colorText.BOLD
                + colorText.GREEN
                + "\n[+] Showing recently screened results..\n"
                + colorText.END
            )
            print(
                colorText.miniTabulator().tabulate(
                    df, headers="keys", tablefmt=colorText.No_Pad_GridFormat
                )
            )
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Note: Trend calculation is based on number of recent days to screen as per your configuration."
                + colorText.END
            )
            input(
                colorText.BOLD
                + colorText.GREEN
                + "[+] Press <Enter> to continue.."
                + colorText.END
            )
        except FileNotFoundError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] Failed to load recently screened result table from disk! Skipping.."
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
            return colorText.BOLD + colorText.GREEN + str(ratio) + "x" + colorText.END
        return colorText.BOLD + colorText.FAIL + str(ratio) + "x" + colorText.END

    def removeAllColorStyles(styledText):
        styles = [
            colorText.HEAD,
            colorText.END,
            colorText.BOLD,
            colorText.UNDR,
            colorText.BLUE,
            colorText.GREEN,
            colorText.WARN,
            colorText.FAIL,
            colorText.WHITE,
        ]
        cleanedUpStyledValue = str(styledText)
        for style in styles:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
        return cleanedUpStyledValue

    def getCellColor(cellStyledValue="", defaultCellFillColor="black"):
        otherStyles = [colorText.HEAD, colorText.END, colorText.BOLD, colorText.UNDR]
        mainStyles = [
            colorText.BLUE,
            colorText.GREEN,
            colorText.WARN,
            colorText.FAIL,
            colorText.WHITE,
        ]
        colorsDict = {
            colorText.BLUE: "blue",
            colorText.GREEN: "darkgreen"
            if defaultCellFillColor == "black"
            else "lightgreen",
            colorText.WARN: "darkorange"
            if defaultCellFillColor == "black"
            else "yellow",
            colorText.FAIL: "red",
            colorText.WHITE: "white",
        }
        cleanedUpStyledValue = cellStyledValue
        cellFillColor = defaultCellFillColor
        for style in otherStyles:
            cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
        for style in mainStyles:
            if style in cleanedUpStyledValue:
                cleanedUpStyledValue = cleanedUpStyledValue.replace(style, "")
                cellFillColor = colorsDict[style]
                break
        return cellFillColor, cleanedUpStyledValue

    def tableToImage(
        table,
        styledTable,
        filename,
        label,
        backtestSummary=None,
        backtestDetail=None,
        addendum=None,
        addendumLabel=None,
    ):
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        # First 4 lines are headers. Last 1 line is bottom grid line
        fontURL = "https://raw.githubusercontent.com/pkjmesra/pkscreener/main/pkscreener/courbd.ttf"
        fontFile = fontURL.split("/")[-1]
        bData, fontPath, _ = Archiver.findFile(fontFile)
        if bData is None:
            resp = fetcher.fetchURL(fontURL, stream=True)
            with open(fontPath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)

        bgColor = "white" if tools.currentDateTime().day % 2 == 0 else "black"
        gridColor = "black" if bgColor == "white" else "white"
        artColor = "lightgreen" if bgColor == "black" else "blue"
        menuColor = "red"

        repoText = f"Source: https://GitHub.com/pkjmesra/pkscreener/  | © {datetime.date.today().year} pkjmesra |Telegram: https://t.me/PKScreener | This report is for learning/analysis purposes ONLY. pkjmesra assumes no responsibility or liability for any errors or omissions in this report or repository or gain/loss bearing out of this analysis.\n"
        repoText = f"{repoText}\n[+] Understanding this report:\n"
        legendText = "\n*** 1. Stock ***: This is the NSE symbol/ticker for a company. Stocks that are NOT stage two, are coloured red. *** 2. Consol.(30Prds) *** : It shows the price range in which stock is trading for the last 30 trading sessions(20 trading sessions per month) 3. *** Breakout(30Prds) ***: The BO is Breakout level based on last 30 sessions. R is the resistance level (if available)."
        legendText = f"{legendText} An investor should consider both BO & R level to analyse entry / exits in their trading lessons. If the BO value is green, it means the stock has already broken out (is above BO level). If BO is in red, it means the stock is yet to break out.  *** 4. LTP ***: This is the last/latest trading/closing price of the given stock on a given date at NSE. The LTP in green/red means the"
        legendText = f"{legendText} stock price has increased / decreased since last trading session. (1.5%, 1.3%,1.8%) with LTP shows the stock price rose by 1.5%, 1.3% and 1.8% in the last 1, 2 and 3 trading sessions respectively.*** 5. %Chng ***: This is the change(rise/fall in percentage) in closing/trading price from the previous trading session's closing price. Green means that price rose from the previous"
        legendText = f"{legendText} trading session. Red means it fell.  *** 6. Volume ***: This shows the relative volume in the most recent trading day /today with respect to last 20 trading periods moving average of Volume. For example, 8.5x would mean today's volume so far is 8.5 times the average volume traded in the last 20 trading sessions. Volume in green means that volume for the date so far has been at"
        legendText = f"{legendText} least 2.5 times more than the average volume of last 20 sessions. If the volume is in red, it means the given date's volume is less than 2.5 times the avg volume of the last 20 sessions. *** 7. MA-Signal ***: It shows the price trend of the given stock by analyzing various 50-200 moving/exponential averages crossover strategies. Perform a Google search for the shown MA-Signals"
        legendText = f"{legendText} to learn about them more. If it is in green, the signal is bullish. Red means bearish. *** 8. RSI ***: Relative Strength Index is a momentum index which describes 14-period relative strength at the given price. Generally, below 30 is considered oversold and above 80 is considered overbought.  *** 9. Trend(30Prds) ***:  This describes the average trendline computed based on the"
        legendText = f"{legendText} last 30 trading sessions. Their strength is displayed depending on the steepness of the trendlines. (Strong / Weak) Up / Down shows how high/low the demand is respectively. A Sideways trend is the horizontal price movement that occurs when the forces of supply and demand are nearly equal. *** 10. Pattern ***:This shows if the chart or the candle (from the candlestick chart) is"
        legendText = f"{legendText} forming any known pattern in the recent timeframe or as per the selected screening options. Do a google search for the shown pattern names to learn. *** 11. CCI ***: The Commodity Channel Index (CCI) is a technical indicator that measures the difference between the current price and the historical average price of the given stock. Generally below '- 100' is considered oversold"
        legendText = f"{legendText} and above 100 is considered overbought. If the CCI is < '-100' or CCI is > 100 and the Trend(30Prds) is Strong/Weak Up, it is shown in green. Otherwise it's in red. *** 12. 1-Pd/2-Pd etc. ***: 60.29% of (413) under 1-Pd in green shows that the given scan option was correct 60.23% of the times for 413 stocks that scanner found in the last 30 trading sessions under the same scan"
        legendText = f"{legendText} options. Similarly, 61.69 % of (154) in green under 22-Pd, means we found that 61.56% of 154 stocks (~95 stocks) prices found under the same scan options increased in 22 trading periods. 57.87% of (2661) under 'Overall' means that over the last 30 trading sessions we found 2661 stock instances under the same scanning options (for example, Momentum Gainers), out of which 57.87%"
        legendText = f"{legendText} of the stock prices increased in one or more of the last 1 or 2 or 3 or 4 or 5 or 10 or 22 or 30 trading sessions. If you want to see by what percent the prices increased, you should see the details. *** 13. 1 to 30 period gain/loss % ***: 4.17% under 1-Pd in green in the gain/loss table/grid means the stock price increased by 4.17% in the next 1 trading session. If this is in"
        legendText = f"{legendText} red, example, -5.67%, it means the price actually decreased by 5.67%. Gains are in green and losses are in red in this grid. The Date column has the date(s) on which that specific stock was found under the chosen scan options in the past 30 trading sessions. *** 14. 52Wk H/L ***: These have 52 weeks high/low prices within 10% of LTP:Yellow, above high:Green. Below 90% High:Red."
        legendText = f"{legendText} *** 1D-% ***: Shows the 1 period gain in percent from the given date. Similarly 2D-%, 3D-% etc shows 2 day, 3 days gain etc. *** 1D-10k ***: Shows 1 period/day portfolio value if you would have invested 10,000 on the given date. *** [T]... *** : [T] is for Trends followed by the trend name in the filter. *** [BO] ***: Shows the Breakout filter value. *** [P] ***: [P] shows pattern name\n"

        artfont = ImageFont.truetype(fontPath, 30)
        font = ImageFont.truetype(fontPath, 60)
        arttext_width, arttext_height = artfont.getsize_multiline(artText)
        oneLinelabel_width, oneLinelabel_height = font.getsize_multiline(label)
        scanResulttext_width, scanResulttext_height = font.getsize_multiline(table)
        (
            backtestSummary_text_width,
            backtestSummary_text_height,
        ) = font.getsize_multiline(backtestSummary)
        backtestDetail_text_width, backtestDetail_text_height = font.getsize_multiline(
            backtestDetail
        )
        repotext_width, repotext_height = artfont.getsize_multiline(repoText)

        scanResultText_width_inArtfont, _ = artfont.getsize_multiline(table)
        backtestSummary_text_width_inArtfont, _ = font.getsize_multiline(
            backtestSummary
        )

        startColValue = 100
        im_width = max(
            arttext_width,
            oneLinelabel_width,
            scanResulttext_width,
            backtestSummary_text_width,
            backtestDetail_text_width,
            repotext_width,
            scanResultText_width_inArtfont,
            backtestSummary_text_width_inArtfont,
        ) + int(startColValue * 2)

        wrapper = textwrap.TextWrapper(
            width=2
            * int(
                len(table.split("\n")[0])
                if len(table) > 0
                else len(backtestSummary.split("\n")[0])
            )
        )
        word_list = wrapper.wrap(text=legendText)
        legendText_new = ""
        for ii in word_list[:-1]:
            legendText_new = legendText_new + ii + "\n"
        legendText_new += word_list[-1]
        legendText = legendText_new
        legendtext_width, legendtext_height = artfont.getsize_multiline(legendText)
        addendumtext_height = 0
        if addendum is not None and len(addendum) > 0:
            addendumtext_width, addendumtext_height = font.getsize_multiline(addendum)
        im = Image.new(
            "RGB",
            (
                im_width,
                arttext_height
                + scanResulttext_height
                + backtestSummary_text_height
                + backtestDetail_text_height
                + oneLinelabel_height
                + repotext_height
                + legendtext_height
                + addendumtext_height
                + oneLinelabel_height,
            ),
            bgColor,
        )
        draw = ImageDraw.Draw(im)
        # artwork
        draw.text((startColValue, 7), artText, font=artfont, fill=artColor)
        rowPixelRunValue = 10 + arttext_height
        separator = "|"
        sep_width, sep_height = font.getsize_multiline(separator)
        dfs_to_print = [styledTable, backtestSummary, backtestDetail]
        unstyled_dfs = [table, backtestSummary, backtestDetail]
        reportTitle = f"[+] As of {tools.currentDateTime().strftime('%d-%m-%y %H.%M.%S')} IST > You chose {label}"
        titleLabels = [
            f"[+] Scan results for {label} :",
            "[+] For chosen scan, summary of correctness from past: [Example, 70% of (100) under 1-Pd, means out of 100 stocks that were in the scan result in the past, 70% of them gained next day.)",
            "[+] 1 to 30 period gain/loss % for matching stocks on respective date from earlier predictions:[Example, 5% under 1-Pd, means the stock price actually gained 5% the next day from given date.]",
        ]
        if addendum is not None and len(addendum) > 0:
            titleLabels.append(addendumLabel)
            dfs_to_print.append(addendum)
            unstyled_dfs.append(tools.removeAllColorStyles(addendum))
        draw.text(
            (startColValue, rowPixelRunValue), reportTitle, font=font, fill=menuColor
        )
        rowPixelRunValue += oneLinelabel_height + 1
        counter = -1
        for df in dfs_to_print:
            counter += 1
            colPixelRunValue = startColValue
            if df is None or len(df) == 0:
                continue
            # selected menu options and As of DateTime
            draw.text(
                (colPixelRunValue, rowPixelRunValue),
                titleLabels[counter],
                font=font,
                fill=menuColor,
            )
            rowPixelRunValue = rowPixelRunValue + oneLinelabel_height
            unstyledLines = unstyled_dfs[counter].splitlines()
            lineNumber = 0
            screenLines = df.splitlines()
            for line in screenLines:
                line_width, line_height = font.getsize_multiline(line)
                # Print the header columns and bottom grid line
                if (
                    lineNumber == 0
                    or (lineNumber % 2) == 0
                    or lineNumber == len(screenLines) - 1
                ):
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        line,
                        font=font,
                        fill=gridColor,
                    )
                    rowPixelRunValue = rowPixelRunValue + line_height + 1
                elif lineNumber == 1:
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        line,
                        font=font,
                        fill=gridColor,
                    )
                    rowPixelRunValue = rowPixelRunValue + line_height + 1
                else:
                    valueScreenCols = line.split(separator)
                    columnNumber = 0
                    del valueScreenCols[0]
                    del valueScreenCols[-1]
                    for val in valueScreenCols:
                        if lineNumber >= len(unstyledLines):
                            continue
                        unstyledLine = unstyledLines[lineNumber]
                        style, cleanValue = tools.getCellColor(
                            val, defaultCellFillColor=gridColor
                        )
                        if columnNumber == 0:
                            cleanValue = unstyledLine.split(separator)[1]
                            style = style if "%" in cleanValue else gridColor
                        if bgColor == "white" and style == "yellow":
                            # Yellow on a white background is difficult to read
                            style = "blue"
                        elif bgColor == "black" and style == "blue":
                            # blue on a black background is difficult to read
                            style = "yellow"
                        col_width, col_height = font.getsize_multiline(cleanValue)
                        draw.text(
                            (colPixelRunValue, rowPixelRunValue),
                            separator,
                            font=font,
                            fill=gridColor,
                        )
                        colPixelRunValue = colPixelRunValue + sep_width
                        draw.text(
                            (colPixelRunValue, rowPixelRunValue),
                            cleanValue,
                            font=font,
                            fill=style,
                        )
                        colPixelRunValue = colPixelRunValue + col_width
                        columnNumber = columnNumber + 1
                    # Close the row with the separator
                    draw.text(
                        (colPixelRunValue, rowPixelRunValue),
                        separator,
                        font=font,
                        fill=gridColor,
                    )
                    colPixelRunValue = startColValue
                    rowPixelRunValue = rowPixelRunValue + line_height + 1
                lineNumber = lineNumber + 1
            rowPixelRunValue = rowPixelRunValue + oneLinelabel_height
        draw.text(
            (colPixelRunValue, rowPixelRunValue + 1),
            repoText,
            font=artfont,
            fill=menuColor,
        )
        draw.text(
            (colPixelRunValue, rowPixelRunValue + 2 * oneLinelabel_height + 10),
            legendText,
            font=artfont,
            fill=gridColor,
        )
        im = im.resize(im.size, Image.ANTIALIAS, reducing_gap=2)
        im.save(filename, format="png", bitmap_format="png", optimize=True, quality=20)
        # if 'RUNNER' not in os.environ.keys() and 'PKDevTools_Default_Log_Level' in os.environ.keys():
        # im.show()

    def tradingDate(simulate=False, day=None):
        curr = tools.currentDateTime(simulate=simulate, day=day)
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
                return (curr - datetime.timedelta(days=(curr.weekday() - 4))).date()

    def dateFromYmdString(Ymd=None):
        return datetime.datetime.strptime(Ymd, "%Y-%m-%d")

    def days_between(d1, d2):
        return abs((d2 - d1).days)

    def trading_days_between(d1, d2):
        return np.busday_count(
            d1, d2
        )  # ,weekmask=[1,1,1,1,1,0,0],holidays=['2020-01-01'])

    def currentDateTime(simulate=False, day=None, hour=None, minute=None):
        curr = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        if simulate:
            return curr.replace(day=day if day is not None else curr.day,
                                hour=hour if hour is not None else curr.hour,
                                minute=minute if minute is not None else curr.minute,)
        else:
            return curr

    def isTradingTime():
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=9, minute=15)
        closeTime = curr.replace(hour=15, minute=30)
        return (openTime <= curr <= closeTime) and tools.isTradingWeekday()

    def isTradingWeekday():
        curr = tools.currentDateTime()
        return 0 <= curr.weekday() <= 4

    def ispreMarketTime():
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=9, minute=15)
        return (openTime > curr) and tools.isTradingWeekday()

    def ispostMarketTime():
        curr = tools.currentDateTime()
        closeTime = curr.replace(hour=15, minute=30)
        return (closeTime < curr) and tools.isTradingWeekday()

    def isClosingHour():
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=15, minute=00)
        closeTime = curr.replace(hour=15, minute=30)
        return (openTime <= curr <= closeTime) and tools.isTradingWeekday()

    def secondsAfterCloseTime():
        curr = tools.currentDateTime()  # (simulate=True,day=7,hour=8,minute=14)
        closeTime = curr.replace(hour=15, minute=30)
        return (curr - closeTime).total_seconds()

    def secondsBeforeOpenTime():
        curr = tools.currentDateTime()  # (simulate=True,day=7,hour=8,minute=14)
        openTime = curr.replace(hour=9, minute=15)
        return (curr - openTime).total_seconds()

    def nextRunAtDateTime(bufferSeconds=3600, cronWaitSeconds=300):
        curr = tools.currentDateTime()  # (simulate=True,day=7,hour=8,minute=14)
        nextRun = curr + datetime.timedelta(seconds=cronWaitSeconds)
        if 0 <= curr.weekday() <= 4:
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
                    nextRun = curr + datetime.timedelta(
                        days=daysToAdd,
                        seconds=1.5 * cronWaitSeconds
                        + bufferSeconds
                        - secondsAfterClosingTime,
                    )
                elif secondsAfterClosingTime > (bufferSeconds + 1.5 * cronWaitSeconds):
                    # Same day, upto 11:59:59pm
                    curr = curr + datetime.timedelta(
                        days=3 if curr.weekday() == 4 else 1
                    )
                    nextRun = curr.replace(hour=9, minute=15) - datetime.timedelta(
                        days=daysToAdd, seconds=1.5 * cronWaitSeconds + bufferSeconds
                    )
            elif secondsAfterClosingTime < 0:
                # Next day
                nextRun = curr.replace(hour=9, minute=15) - datetime.timedelta(
                    days=daysToAdd, seconds=1.5 * cronWaitSeconds + bufferSeconds
                )
        return nextRun

    def set_github_output(name, value):
        if "GITHUB_OUTPUT" in os.environ.keys():
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                print(f"{name}={value}", file=fh)

    def afterMarketStockDataExists(intraday=False, forceLoad=False):
        curr = tools.currentDateTime()
        openTime = curr.replace(hour=9, minute=15)
        cache_date = curr  # for monday to friday
        weekday = curr.weekday()
        # for monday to friday before 9:15 or between 9:15am to 3:30pm, we're backtesting
        if curr < openTime or (forceLoad and tools.isTradingTime()):
            cache_date = curr - datetime.timedelta(1)
        if weekday == 0 and curr < openTime:  # for monday before 9:15
            cache_date = curr - datetime.timedelta(3)
        if weekday == 5 or weekday == 6:  # for saturday and sunday
            cache_date = curr - datetime.timedelta(days=weekday - 4)
        cache_date = cache_date.strftime("%d%m%y")
        pattern = f"{'intraday_' if intraday else ''}stock_data_"
        cache_file = pattern + str(cache_date) + ".pkl"
        exists = False
        for f in glob.glob(f"{pattern}*.pkl", root_dir=Archiver.get_user_outputs_dir()):
            if f.endswith(cache_file):
                exists = True
                break
        return exists, cache_file

    def saveStockData(stockDict, configManager, loadCount, intraday=False):
        exists, cache_file = tools.afterMarketStockDataExists(
            configManager.isIntradayConfig() or intraday
        )
        if exists:
            configManager.deleteFileWithPattern(excludeFile=cache_file)
        cache_file = os.path.join(Archiver.get_user_outputs_dir(), cache_file)
        if not os.path.exists(cache_file) or len(stockDict) > (loadCount + 1):
            try:
                with open(cache_file, "wb") as f:
                    pickle.dump(stockDict.copy(), f, protocol=pickle.HIGHEST_PROTOCOL)
                    print(colorText.BOLD + colorText.GREEN + "=> Done." + colorText.END)
            except pickle.PicklingError as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                print(
                    colorText.BOLD
                    + colorText.FAIL
                    + "=> Error while Caching Stock Data."
                    + colorText.END
                )
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
        else:
            print(
                colorText.BOLD + colorText.GREEN + "=> Already Cached." + colorText.END
            )

    def loadStockData(
        stockDict,
        configManager,
        downloadOnly=False,
        defaultAnswer=None,
        retrial=False,
        forceLoad=False,
    ):
        if downloadOnly:
            return
        isIntraday = configManager.isIntradayConfig()
        exists, cache_file = tools.afterMarketStockDataExists(
            isIntraday, forceLoad=forceLoad
        )
        default_logger().info(
            f"Stock data cache file:{cache_file} exists ->{str(exists)}"
        )
        stockDataLoaded = False
        if exists:
            with open(
                os.path.join(Archiver.get_user_outputs_dir(), cache_file), "rb"
            ) as f:
                try:
                    stockData = pickle.load(f)
                    if not downloadOnly:
                        print(
                            colorText.BOLD
                            + colorText.GREEN
                            + f"[+] Automatically Using Cached Stock Data {'due to After-Market hours' if not tools.isTradingTime() else ''}!"
                            + colorText.END
                        )
                    for stock in stockData:
                        stockDict[stock] = stockData.get(stock)
                    stockDataLoaded = True
                except pickle.UnpicklingError as e:
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    print(
                        colorText.BOLD
                        + colorText.FAIL
                        + "[+] Error while Reading Stock Cache."
                        + colorText.END
                    )
                    if tools.promptFileExists(defaultAnswer=defaultAnswer) == "Y":
                        configManager.deleteFileWithPattern()
                except EOFError as e:  # pragma: no cover
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    print(
                        colorText.BOLD
                        + colorText.FAIL
                        + "[+] Stock Cache Corrupted."
                        + colorText.END
                    )
                    if tools.promptFileExists(defaultAnswer=defaultAnswer) == "Y":
                        configManager.deleteFileWithPattern()
        if (
            not stockDataLoaded
            and ("1d" if isIntraday else ConfigManager.default_period)
            == configManager.period
            and ("1m" if isIntraday else ConfigManager.default_duration)
            == configManager.duration
        ):
            cache_url = (
                "https://raw.github.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/"
                + cache_file  # .split(os.sep)[-1]
            )
            resp = fetcher.fetchURL(cache_url, stream=True)
            if resp is not None:
                default_logger().info(
                    f"Stock data cache file:{cache_file} request status ->{resp.status_code}"
                )
            if resp is not None and resp.status_code == 200:
                print(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] After-Market Stock Data is not cached.."
                    + colorText.END
                )
                print(
                    colorText.BOLD
                    + colorText.GREEN
                    + "[+] Downloading cache from pkscreener server for faster processing, Please Wait.."
                    + colorText.END
                )
                try:
                    chunksize = 1024 * 1024 * 1
                    filesize = int(int(resp.headers.get("content-length")) / chunksize)
                    if filesize > 0:
                        bar, spinner = tools.getProgressbarStyle()
                        f = open(
                            os.path.join(Archiver.get_user_outputs_dir(), cache_file),
                            "wb",
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
                        stockDataLoaded = True
                    else:
                        default_logger().debug(
                            f"Stock data cache file:{cache_file} on server has length ->{filesize}"
                        )
                except Exception as e:  # pragma: no cover
                    default_logger().debug(e, exc_info=True)
                    f.close()
                    print("[!] Download Error - " + str(e))
                print("")
                if not retrial and not stockDataLoaded:
                    # Don't try for more than once.
                    tools.loadStockData(
                        stockDict,
                        configManager,
                        downloadOnly,
                        defaultAnswer,
                        retrial=True,
                        forceLoad=forceLoad,
                    )
        if not stockDataLoaded:
            print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] Cache unavailable on pkscreener server, Continuing.."
                + colorText.END
            )

    # Save screened results to excel
    def promptSaveResults(df, defaultAnswer=None):
        try:
            if defaultAnswer is None:
                response = str(
                    input(
                        colorText.BOLD
                        + colorText.WARN
                        + "[>] Do you want to save the results in excel file? [Y/N]: "
                    )
                ).upper()
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            response = "Y"
        if response != "N":
            filename = (
                "PKScreener-result_"
                + tools.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
                + ".xlsx"
            )
            desktop = os.path.expanduser("~/Desktop")
            # the above is valid on Windows (after 7) but if you want it in os normalized form:
            desktop = os.path.normpath(os.path.expanduser("~/Desktop"))
            try:
                df.to_excel(
                    os.path.join(os.getcwd(), filename), engine="xlsxwriter"
                )  # openpyxl throws an error exporting % sign.
                filename = os.path.join(os.getcwd(), filename)
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                print(
                    colorText.FAIL
                    + (
                        "[+] Error saving file at %s"
                        % os.path.join(os.getcwd(), filename)
                    )
                    + colorText.END
                )
                try:
                    df.to_excel(
                        os.path.join(desktop, filename), engine="xlsxwriter"
                    )  # openpyxl throws an error exporting % sign.
                    filename = os.path.join(desktop, filename)
                except Exception as ex:  # pragma: no cover
                    default_logger().debug(ex, exc_info=True)
                    print(
                        colorText.FAIL
                        + (
                            "[+] Error saving file at %s"
                            % os.path.join(desktop, filename)
                        )
                        + colorText.END
                    )
                    df.to_excel(
                        os.path.join(tempfile.gettempdir(), filename),
                        engine="xlsxwriter",
                    )
                    filename = os.path.join(tempfile.gettempdir(), filename)
            print(
                colorText.BOLD
                + colorText.GREEN
                + ("[+] Results saved to %s" % filename)
                + colorText.END
            )
            return filename
        return None

    # Save screened results to excel
    def promptFileExists(cache_file="stock_data_*.pkl", defaultAnswer=None):
        try:
            if defaultAnswer is None:
                response = str(
                    input(
                        colorText.BOLD
                        + colorText.WARN
                        + "[>] "
                        + cache_file
                        + " already exists. Do you want to replace this? [Y/N]: "
                    )
                ).upper()
            else:
                response = defaultAnswer
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        return "Y" if response != "N" else "N"

    # Prompt for asking RSI
    def promptRSIValues():
        try:
            minRSI, maxRSI = int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + "\n[+] Enter Min RSI value: "
                    + colorText.END
                )
            ), int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Enter Max RSI value: "
                    + colorText.END
                )
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
        if minCCI is not None and maxCCI is not None:
            return minCCI, maxCCI
        try:
            minCCI, maxCCI = int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + "\n[+] Enter Min CCI value: "
                    + colorText.END
                )
            ), int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Enter Max CCI value: "
                    + colorText.END
                )
            )
            if minCCI <= maxCCI:
                return (minCCI, maxCCI)
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return (-100, 100)

    # Prompt for asking Volume ratio
    def promptVolumeMultiplier(volumeRatio=None):
        if volumeRatio is not None:
            return volumeRatio
        try:
            volumeRatio = int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + "\n[+] Enter Min Volume ratio value (Default = 2.5): "
                    + colorText.END
                )
            )
            if volumeRatio > 0:
                return volumeRatio
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            return 2

    def promptMenus(menu):
        m = menus()
        return m.renderForMenu(menu)

    # Prompt for Popular stocks
    def promptPopularStocks(menu=None):
        try:
            tools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + """[+] Select Option:"""
                    + colorText.END
                )
            )
            if resp >= 0 and resp <= 3:
                return resp
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            input(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return None

    # Prompt for Reversal screening
    def promptReversalScreening(menu=None):
        try:
            tools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + """[+] Select Option:"""
                    + colorText.END
                )
            )
            if resp >= 0 and resp <= 7:
                if resp == 4:
                    try:
                        maLength = int(
                            input(
                                colorText.BOLD
                                + colorText.WARN
                                + "\n[+] Enter MA Length (E.g. 50 or 200): "
                                + colorText.END
                            )
                        )
                        return resp, maLength
                    except ValueError as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        print(
                            colorText.BOLD
                            + colorText.FAIL
                            + "\n[!] Invalid Input! MA Length should be single integer value!\n"
                            + colorText.END
                        )
                        raise ValueError
                elif resp == 6:
                    try:
                        maLength = int(
                            input(
                                colorText.BOLD
                                + colorText.WARN
                                + "\n[+] Enter NR timeframe [Integer Number] (E.g. 4, 7, etc.): "
                                + colorText.END
                            )
                        )
                        return resp, maLength
                    except ValueError as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        print(
                            colorText.BOLD
                            + colorText.FAIL
                            + "\n[!] Invalid Input! NR timeframe should be single integer value!\n"
                            + colorText.END
                        )
                        raise ValueError
                return resp, None
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            input(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Invalid Option Selected. Press <Enter> to try again..."
                + colorText.END
            )
            return None, None

    # Prompt for Reversal screening
    def promptChartPatterns(menu=None):
        try:
            tools.promptMenus(menu=menu)
            resp = int(
                input(
                    colorText.BOLD
                    + colorText.WARN
                    + """[+] Select Option:"""
                    + colorText.END
                )
            )
            if resp == 1 or resp == 2:
                candles = int(
                    input(
                        colorText.BOLD
                        + colorText.WARN
                        + "\n[+] How many candles (TimeFrame) to look back Inside Bar formation? : "
                        + colorText.END
                    )
                )
                return (resp, candles)
            if resp == 3:
                percent = float(
                    input(
                        colorText.BOLD
                        + colorText.WARN
                        + "\n[+] Enter Percentage within which all MA/EMAs should be (Ideal: 1-2%)? : "
                        + colorText.END
                    )
                )
                return (resp, percent / 100.0)
            if resp >= 0 and resp <= 6:
                return resp, 0
            raise ValueError
        except ValueError as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            input(
                colorText.BOLD
                + colorText.FAIL
                + "\n[+] Invalid Option Selected. Press <Enter> to try again..."
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

    def getNiftyModel(retrial=False):
        files = [
            os.path.join(Archiver.get_user_outputs_dir(), "nifty_model_v2.h5"),
            os.path.join(Archiver.get_user_outputs_dir(), "nifty_model_v2.pkl"),
        ]
        model = None
        urls = [
            "https://raw.github.com/pkjmesra/PKScreener/main/pkscreener/ml/nifty_model_v2.h5",
            "https://raw.github.com/pkjmesra/PKScreener/main/pkscreener/ml/nifty_model_v2.pkl",
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
                    print(
                        colorText.BOLD
                        + colorText.GREEN
                        + "[+] Downloading AI model (v2) for Nifty predictions, Please Wait.."
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
                                Archiver.get_user_outputs_dir(), file_url.split("/")[-1]
                            ),
                            "wb",
                        )
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
                    except Exception as e:  # pragma: no cover
                        default_logger().debug(e, exc_info=True)
                        print("[!] Download Error - " + str(e))
            time.sleep(3)
        try:
            if os.path.isfile(files[0]) and os.path.isfile(files[1]):
                pkl = joblib.load(files[1])
                model = keras.models.load_model(files[0]) if Imports["keras"] else None
        except Exception as e:  # pragma: no cover
            default_logger().debug(e, exc_info=True)
            os.remove(files[0])
            os.remove(files[1])
            if not retrial:
                tools.getNiftyModel(retrial=True)
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
            print("\a")
            sleep(delay)
