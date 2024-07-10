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
from enum import Enum

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.OutputControls import OutputControls
import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes import VERSION

configManager = ConfigManager.tools()
MENU_SEPARATOR = ""
LINE_SEPARATOR = "\n"
MAX_SUPPORTED_MENU_OPTION = 33
MAX_MENU_OPTION = 41

level0MenuDict = {
    "X": "Scanners",
    "M": "Monitor Intraday",
    "S": "Strategies",
    "B": "Backtests",
    "G": "Growth of 10k",
    "C": "Analyse morning vs close outcomes",
    "P": "Piped Scanners",
    "T": "~",
    "D": "Download Daily OHLC Data for the Past Year",
    "I": "Download Intraday OHLC Data for the Last Trading Day",
    "E": "Edit user configuration",
    "Y": "View your user configuration",
    "U": "Check for software update",
    "L": "Collect Logs for Debugging",
    "H": "Help / About Developer",
    "Z": "Exit (Ctrl + C)",
}
level1_index_options_sectoral= {
    "1": "Nifty Auto (^CNXAUTO)",
    "2": "Nifty Bank (^NSEBANK)                             ",
    "3": "Nifty Consumption (^CNXCONSUM)",
    "4": "Nifty Financial Services (NIFTY_FIN_SERVICE.NS)   ",
    "5": "Nifty Financial Services 25/50 (^CNXFIN)",
    "6": "Nifty FMCG (^CNXFMCG)                             ",
    "7": "Nifty Healthcare (NIFTY_HEALTHCARE.NS)",
    "8": "Nifty IT (^CNXIT)                                 ",
    "9": "Nifty Media (^CNXMEDIA)",
    "10": "Nifty Metal (^CNXMETAL)                          ",
    "11": "Nifty Pharma (^CNXPHARMA)",
    "12": "Nifty Private Bank (NIFTY_PVT_BANK.NS)           ",
    "13": "Nifty PSU Bank (^CNXPSUBANK)",
    "14": "Nifty Realty (^CNXREALTY)                        ",
    "15": "Nifty Consumer Durables (NIFTY_CONSR_DURBL.NS)",
    "16": "Nifty Oil and Gas (NIFTY_OIL_AND_GAS.NS)         ",
    "17": "Nifty MidSmall Healthcare (NIFTY_MIDSML_HLTH.NS)",
}
level1_P_MenuDict = {
    "1": "Predefined Piped Scanners",
    "2": "Define my custom Piped Scanner",
    "3": "Run Piped Scans Saved So Far",
    "M": "Back to the Top/Main menu",
}
PREDEFINED_SCAN_MENU_KEYS = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20"]
PREDEFINED_SCAN_MENU_TEXTS = [
    "Volume Scanners | High Momentum | Breaking Out Now | ATR Cross     ",
    "Volume Scanners | High Momentum | ATR Cross",
    "Volume Scanners | High Momentum                                    ",
    "Volume Scanners | ATR Cross",
    "Volume Scanners | High Bid/Ask Build Up                            ",
    "Volume Scanners | ATR Cross | ATR Trailing Stops",
    "Volume Scanners | ATR Trailing Stops                               ",
    "High Momentum | ATR Cross",
    "High Momentum | ATR Trailing Stop                                  ",
    "ATR Cross | ATR Trailing Stop",
    "TTM Sqeeze Buy | Intraday RSI b/w 0 to 54                          ",
    "Volume Scanners | High Momentum | Breaking Out Now | ATR Cross | Intraday RSI b/w 0 to 54",
    "Volume Scanners | ATR Cross | Intraday RSI b/w 0 to 54             ",
    "VCP (Mark Minervini) | Chart Patterns | MA Support",
    "VCP | Chart Patterns | MA Support                                  ",
    "Already Breaking out | VCP (Minervini) | Chart Patterns | MA Support",
    "ATR Trailing Stops | VCP (Minervini)                               ",
    "VCP | ATR Trailing Stops",
    "Nifty 50,Nifty Bank | VCP | ATR Trailing Stops                     ",
    "Volume Scanners | High Momentum | Breaking Out Now | ATR Cross | VCP | ATR Trailing Stops",
]
level2_P_MenuDict = {}
for key in PREDEFINED_SCAN_MENU_KEYS:
    level2_P_MenuDict[key] = PREDEFINED_SCAN_MENU_TEXTS[int(key)-1]
level2_P_MenuDict["M"] = "Back to the Top/Main menu"
PREDEFINED_SCAN_MENU_VALUES =[
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:27:'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:27:'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:29:'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:27:>|X:12:30:1:'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:12:30:1:'",
    "--systemlaunched -a y -e -o 'X:12:31:>|X:0:27:'",
    "--systemlaunched -a y -e -o 'X:12:31:>|X:0:30:1:'",
    "--systemlaunched -a y -e -o 'X:12:27:>|X:0:30:1:'",
    "--systemlaunched -a y -e -o 'X:12:7:6:1:>|X:0:5:0:54:i 1m'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:>|X:0:5:0:54:i 1m'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:27:>|X:0:5:0:54:i 1m'",
    "--systemlaunched -a y -e -o 'X:12:7:8:>|X:12:7:9:1:1:'",
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:12:7:9:1:1:'",
    "--systemlaunched -a y -e -o 'X:12:2:>|X:12:7:8:>|X:12:7:9:1:1:'",
    "--systemlaunched -a y -e -o 'X:12:30:1:>|X:12:7:8:'",
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:12:30:1:'",
    "--systemlaunched -a y -e -o 'X:0:0:^NSEI,^NSEBANK:>|X:12:7:4:>|X:12:30:1:'",
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:>|X:12:7:4:>|X:12:30:1:'",
]
PREDEFINED_PIPED_MENU_OPTIONS = []
for option in PREDEFINED_SCAN_MENU_VALUES:
    argOptions = option.split("-o ")[-1]
    analysisOptions = argOptions.split("|")
    analysisOptions[-1] = analysisOptions[-1].replace("X:","C:")
    argOptions = "|".join(analysisOptions)
    PREDEFINED_PIPED_MENU_OPTIONS.append(argOptions.replace("'","").replace("\"",""))

PIPED_SCANNERS = {}
for key in PREDEFINED_SCAN_MENU_KEYS:
    PIPED_SCANNERS[key] = PREDEFINED_SCAN_MENU_VALUES[int(key)-1]

level1_T_MenuDict = {
    "L": "Long Term",
    "S": "Short Term (Intraday)",
    "B": "Quick Backtest for N-days/candles ago",
    "M": "Back to the Top/Main menu",
}
# Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
# Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
level2_T_MenuDict_L = {
    "1": "Daily (1y, 1d)",
    "2": "Weekly (1y, 1wk)",
    "3": "Monthly (1y, 1mo)",
    "4": "Hourly (1y, 1h)",
    "5": "Custom",
    "M": "Back to the Top/Main menu",
}
level2_T_MenuDict_S = {
    "1": "1m (1d, 1m)",
    "2": "5m (1d, 5m)",
    "3": "15m (1d, 15m)",
    "4": "30m (1d, 30m)",
    "5": "Custom",
    "M": "Back to the Top/Main menu",
}
level1_S_MenuDict = {
    "S": "Summary",
    "M": "Back to the Top/Main menu",
    "Z": "Exit (Ctrl + C)",
}
level1_X_MenuDict = {
    "W": "Screen stocks from my own Watchlist",
    "N": "Nifty Prediction using Artifical Intelligence (Use for Gap-Up/Gap-Down/BTST/STBT)",
    "E": "Live Index Scan : 5 EMA for Intraday",
    "S": "Sectoral Indices",
    "0": "Screen stocks/index by the stock/index names (NSE Stock Code, e.g. SBIN,BANKINDIA or Yahoo Finance index symbol, e.g. ^NSEI, ^NSEBANK, ^BSESN)",
    "1": "Nifty 50          ",
    "2": "Nifty Next 50     ",
    "3": "Nifty 100         ",
    "4": "Nifty 200         ",
    "5": "Nifty 500         ",
    "6": "Nifty Smallcap 50 ",
    "7": "Nifty Smallcap 100",
    "8": "Nifty Smallcap 250",
    "9": "Nifty Midcap 50   ",
    "10": "Nifty Midcap 100",
    "11": "Nifty Midcap 150 ",
    "12": "Nifty (All Stocks)",
    "13": "Newly Listed (IPOs in last 2 Year)           ",
    "14": "F&O Stocks Only", #Discontinued:  https://nsearchives.nseindia.com/content/circulars/FAOP61157.pdf
    "15": "NASDAQ",
    "M": "Back to the Top/Main menu",
    "Z": "Exit (Ctrl + C)",
}
level2_X_MenuDict = {
    "0": "Full Screening (Shows Technical Parameters without any criterion)",
    "1": "Probable Breakouts/Breakdowns   ",
    "2": "Today's Breakouts/Breakdowns",
    "3": "Consolidating stocks            ",
    "4": "Lowest Volume in last N-days (Early Breakout Detection)",
    "5": "RSI screening                   ",
    "6": "Reversal Signals",
    "7": "Stocks making Chart Patterns    ",
    "8": "CCI outside of the given range",
    "9": "Volume gainers                  ",
    "10": "Closing at least 2% up since last 3 days",
    "11": "Short term bullish (Ichimoku)  ",
    "12": "N-Minute Price & Volume breakout(Intraday)",
    "13": "Bullish RSI & MACD             ",
    "14": "NR4 Daily Today",
    "15": "52 week low breakout(today)(Sell)",
    "16": "10 days low breakout(Sell)",
    "17": "52 week high breakout(today)     ",
    "18": "Bullish Aroon(14) Crossover",
    "19": "MACD Histogram x below 0 (Sell) ",
    "20": "Bullish for next day",
    "21": "MF/FIIs Popular Stocks         ",
    "22": "View Stock Performance         ",
    "23": "Breaking out now               ",
    "24": "Higher Highs,Lows & Close (SuperTrend)",
    "25": "Lower Highs,Lows (Watch for Rev.)",
    "26": "Stocks with stock-split/bonus/dividends",
    "27": "ATR Cross                      ",
    "28": "Bullish Higher Opens           ",
    "29": "Intraday Bid/Ask Build-up      ",
    "30": "ATR Trailing Stops(Swing Paper Trading)",
    "31": "High Momentum(RSI,MFI,CCI)     ",
    "32": "Intraday Breakout/Breakdown setup     ",
    # "32": "High Momentum(14)",
    # "28": "Extremely bullish daily close      ",
    # "29": "Rising RSI                      ",
    # "30": "RSI entering bullish territory",
    "42": "Show Last Screened Results",
    "M": "Back to the Top/Main menu",
    "Z": "Exit (Ctrl + C)",
}
level3_X_Reversal_MenuDict = {
    "1": "Buy Signals (Bullish Reversal)",
    "2": "Sell Signals (Bearish Reversal)",
    "3": "Momentum Gainers (Rising Bullish Momentum)",
    "4": "Reversal at Moving Average (Bullish/Bearish Reversal)",
    "5": "Volume Spread Analysis (Bullish VSA Reversal)",
    "6": "Narrow Range (NRx) Reversal",
    "7": "Lorentzian Classifier (Machine Learning based indicator)",
    "8": "PSAR and RSI reversal",
    "9": "Rising RSI",
    "10": "RSI MA Reversal",
    "0": "Cancel",
}
level3_X_ChartPattern_MenuDict = {
    "1": "Bullish Inside Bar (Flag) Pattern",
    "2": "Bearish Inside Bar (Flag) Pattern(Sell)",
    "3": "The Confluence (50 & 200 MA/EMA)",
    "4": "VCP (Volatility Contraction Pattern)",
    "5": "Buying at Trendline Support (Ideal for Swing/Mid/Long term)",
    "6": "Bollinger Bands (TTM) Squeeze",
    "7": "Candle-stick Patterns",
    "8": "VCP (Mark Minervini)",
    "9": "Moving Average Signals",
    "0": "Cancel",
}

level4_X_ChartPattern_MASignalMenuDict = {
    "1": "MA-Support",
    "2": "Bearish Signals",
    "3": "Bullish Signals",
    "4": "BearCross MA",
    "5": "BullCross MA",
    "6": "MA-Resist",
    "0": "Cancel",
}

level4_X_ChartPattern_BBands_SQZ_MenuDict = {
    "1": "TTM Squeeze-Buy",
    "2": "TTM In-Squeeze",
    "3": "TTM Squeeze-Sell",
    "4": "All/Any",
    "0": "Cancel",
}

level4_X_ChartPattern_Confluence_MenuDict = {
    "1": "Confluence up / GoldenCrossOver / DMA50 / DMA200",
    "2": "Confluence Down / DeadCrossOver",
    "3": "Any/All (Confluence up/down/Crossovers)",
    "4": "8,21,55-EMA / 200-SMA Super-Confluence",
    "0": "Cancel",
}

level3_X_PopularStocks_MenuDict = {
    "1": "Shares bought/sold by Mutual Funds/FIIs (M*)",
    "2": "Shareholding by number of Mutual Funds/FIIs (M*)",
    "3": "MF/FIIs Net Ownership Increased",
    "4": "Dividend Yield (M*)",
    "5": "Only MF Net Ownership Increased",
    "6": "Only MF Net Ownership Decreased",
    "7": "MF/FIIs Net Ownership Decreased",
    "8": "Fair Value Buy Opportunities",
    "9": "Fair Value Sell Opportunities",
    "0": "Cancel",
}

level3_X_StockPerformance_MenuDict = {
    "1": "Short term",
    "2": "Medium term",
    "3": "Long term",
    "0": "Cancel",
}

level4_X_Lorenzian_MenuDict = {
    "1": "Buy",
    "2": "Sell",
    "3": "Any/All",
    "0": "Cancel",
}
Pin_MenuDict = {
    "1": "Pin this scan category or piped scan {0}",
    "2": "Pin these {0} stocks in the scan results (Just keep tracking only these {0} stocks)",
    "M": "Back to the Top/Main menu",
}

class MenuRenderStyle(Enum):
    STANDALONE = 1
    TWO_PER_ROW = 2
    THREE_PER_ROW = 3


class menu:
    def __init__(self):
        self.menuKey = ""
        self.menuText = ""
        self.submenu = None
        self.level = 0
        self.isException = None
        self.hasLeftSibling = False
        self.parent = None
        self.line = 0
        self.lineIndex = 0

    def create(self, key, text, level=0, isException=False, parent=None):
        self.menuKey = str(key)
        self.menuText = text
        self.level = level
        self.isException = isException
        self.parent = parent
        self.line = 0
        self.lineIndex = 0
        return self

    def keyTextLabel(self):
        return f"{MENU_SEPARATOR}{self.menuKey} > {self.menuText}"

    def commandTextKey(self, hasChildren=False):
        cmdText = ""
        if self.parent is None:
            cmdText = f"/{self.menuKey}"
            return cmdText
        else:
            cmdText = f"{self.parent.commandTextKey(hasChildren=True)}_{self.menuKey}"
            return cmdText

    def commandTextLabel(self, hasChildren=False):
        cmdText = ""
        if self.parent is None:
            cmdText = f"{self.menuText}" if hasChildren else f"{self.menuText}"
            return cmdText
        else:
            cmdText = (
                f"{self.parent.commandTextLabel(hasChildren=True)} > {self.menuText}"
            )
            return f"{cmdText}"

    def render(self,coloredValues=[]):
        t = ""
        if self.isException:
            if self.menuText.startswith("~"):
                self.menuText = self.renderSpecial(self.menuKey)
            t = f"\n\n     {self.keyTextLabel()}"
        elif not self.menuKey.isnumeric():
            t = f"\n     {self.keyTextLabel()}"
        else:
            # 9 to adjust an extra space when 10 becomes a 2 digit number
            spaces = "     " if int(self.menuKey) <= 9 else "    "
            if not self.hasLeftSibling:
                t = f"\n{spaces}{self.keyTextLabel()}"
            else:
                t = f"\t{self.keyTextLabel()}"
        if coloredValues is not None and str(self.menuKey) in coloredValues:
            t = f"{colorText.FAIL}{t}{colorText.END}"
        return t

    def renderSpecial(self, menuKey):
        configManager.getConfig(ConfigManager.parser)
        menuText = "~"
        if self.level == 0 and menuKey == "T":
            currentConfig = f" [Current ({configManager.period}, {configManager.duration})]"
            menuText = (
                "Toggle between long-term (Default)"
                + colorText.WARN
                + currentConfig
                + colorText.END
                + " and Intraday user configuration\n"
                if not configManager.isIntradayConfig()
                else "Toggle between long-term (Default) and Intraday"
                + colorText.WARN
                + currentConfig
                + colorText.END
                + " user configuration"
            )
        return menuText


# This Class manages application menus
class menus:
    
    @staticmethod
    def allMenus(topLevel="X",index=12):
        menuOptions = [topLevel]
        indexOptions =[index]
        scanOptions = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,23,24,25,27,28,30,31]
        scanSubOptions = {
                            6:[1,2,3,4,5,6,{7:[1,2]},8,9,10],
                            7:[1,2,{3:[1,2]},4,5,{6:[1,3]},7],
                            30:[1,2],
                            # 21:[3,5,6,7,8,9]
                         }
        runOptions = []
        for menuOption in menuOptions:
            for indexOption in indexOptions:
                for scanOption in scanOptions:
                    if scanOption in scanSubOptions.keys():
                        for scanSubOption in scanSubOptions[scanOption]:
                            if isinstance(scanSubOption, dict):
                                for childLevelOption in scanSubOption.keys():
                                    for value in scanSubOption[childLevelOption]:
                                        runOption = f"{menuOption}:{indexOption}:{scanOption}:{childLevelOption}:{value}:D:D:D:D:D"
                                        runOptions.append(runOption)
                            else:
                                runOption = f"{menuOption}:{indexOption}:{scanOption}:{scanSubOption}:D:D:D:D:D"
                                runOptions.append(runOption)
                    else:
                        runOption = f"{menuOption}:{indexOption}:{scanOption}:D:D:D:D:D"
                        runOptions.append(runOption)
        return runOptions

    def __init__(self):
        self.level = 0
        self.menuDict = {}
        self.strategyNames = []

    def fromDictionary(
        self,
        rawDictionary={},
        renderStyle=MenuRenderStyle.STANDALONE,
        renderExceptionKeys=[],
        skip=[],
        parent=None,
        substitutes=[]
    ):
        tabLevel = 0
        self.menuDict = {}
        line = 0
        lineIndex = 1
        substituteIndex = 0
        for key in rawDictionary:
            if skip is not None and key in skip:
                continue
            m = menu()
            menuText = rawDictionary[key]
            if "{0}" in menuText and len(substitutes) > 0:
                if substitutes[substituteIndex] == 0:
                    continue
                menuText = menuText.format(f"{colorText.WARN}{substitutes[substituteIndex]}{colorText.END}")
                substituteIndex += 1
            m.create(
                str(key).upper(), menuText, level=self.level, parent=parent
            )
            if key in renderExceptionKeys:
                m.isException = True
                line += 2
                lineIndex = 1
                m.line = line
                m.lineIndex = lineIndex
            elif str(key).isnumeric():
                m.hasLeftSibling = False if tabLevel == 0 else True
                if tabLevel == 0:
                    line += 1
                lineIndex = tabLevel + 1
                m.line = line
                m.lineIndex = lineIndex
                tabLevel = tabLevel + 1
                if tabLevel >= renderStyle.value:
                    tabLevel = 0
            else:
                line += 1
                lineIndex = 1
                m.line = line
                m.lineIndex = lineIndex
            self.menuDict[str(key).upper()] = m
        return self

    def render(self, asList=False, coloredValues=[]):
        menuText = [] if asList else ""
        for k in self.menuDict.keys():
            m = self.menuDict[k]
            if asList:
                menuText.append(m)
            else:
                menuText = menuText + m.render(coloredValues=([] if asList else coloredValues))
        return menuText

    def renderPinnedMenu(self,substitutes=[]):
        return self.renderPinSubmenus(substitutes=substitutes)
    
    def renderForMenu(self, selectedMenu:menu=None, skip=[], asList=False, renderStyle=None):
        if selectedMenu is None and self.level == 0:
            # Top level Application Main menu
            return self.renderLevel0Menus(
                skip=skip, asList=asList, renderStyle=renderStyle, parent=selectedMenu
            )
        elif selectedMenu is not None:
            if selectedMenu.menuKey == "S" and selectedMenu.level == 0:
                    return self.renderLevel1_S_Menus(
                    skip=skip,
                    asList=asList,
                    renderStyle=renderStyle,
                    parent=selectedMenu,
                )
            if selectedMenu.level == 0:
                self.level = 1
                if selectedMenu.menuKey in ["T"]:
                    return self.renderLevel1_T_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                elif selectedMenu.menuKey in ["P"]:
                    return self.renderLevel1_P_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                else:
                    # sub-menu of the top level main selected menu
                    return self.renderLevel1_X_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
            elif selectedMenu.level == 1:
                self.level = 2
                if selectedMenu.parent.menuKey in ["T"]:
                    if selectedMenu.menuKey in ["L"]:
                        return self.level2_T_MenuDict_L(
                            skip=skip,
                            asList=asList,
                            renderStyle=renderStyle,
                            parent=selectedMenu,
                        )
                    elif selectedMenu.menuKey in ["S"]:
                        return self.level2_T_MenuDict_S(
                            skip=skip,
                            asList=asList,
                            renderStyle=renderStyle,
                            parent=selectedMenu,
                        )
                elif selectedMenu.parent.menuKey in ["P"]:
                    return self.renderLevel2_P_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                elif selectedMenu.menuKey == "S":
                    return self.renderLevel2_Sectoral_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                else:
                    # next levelsub-menu of the selected sub-menu
                    return self.renderLevel2_X_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
            elif selectedMenu.level == 2:
                self.level = 3
                # next levelsub-menu of the selected sub-menu
                if selectedMenu.menuKey == "6":
                    return self.renderLevel3_X_Reversal_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                elif selectedMenu.menuKey == "7":
                    return self.renderLevel3_X_ChartPattern_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                elif selectedMenu.menuKey == "21":
                    return self.renderLevel3_X_PopularStocks_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                elif selectedMenu.menuKey == "22":
                    return self.renderLevel3_X_StockPerformance_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                elif selectedMenu.menuKey in ["30","32"]:
                    return self.renderLevel4_X_Lorenzian_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
            elif selectedMenu.level == 3:
                self.level = 4
                # next levelsub-menu of the selected sub-menu
                if selectedMenu.parent.menuKey == "6" and selectedMenu.menuKey in ["7","10"]:
                    return self.renderLevel4_X_Lorenzian_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                if selectedMenu.parent.menuKey == "7" and selectedMenu.menuKey == "3":
                    return self.renderLevel4_X_ChartPattern_Confluence_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                if selectedMenu.parent.menuKey == "7" and selectedMenu.menuKey == "6":
                    return self.renderLevel4_X_ChartPattern_BBands_SQZ_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                if selectedMenu.parent.menuKey == "7" and selectedMenu.menuKey == "9":
                    return self.renderLevel4_X_ChartPattern_MASignal_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                

    def find(self, key=None):
        if key is not None:
            try:
                return self.menuDict[str(key).upper()]
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                return None
        return None

    def renderPinSubmenus(self, asList=False, renderStyle=None, parent=None, skip=None, substitutes=[]):
        menuText = self.fromDictionary(
            Pin_MenuDict,
            renderExceptionKeys=["M"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
            substitutes = substitutes
        ).render(asList=asList,coloredValues=["M"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a menu option:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("M") or menu().create('?','?')).keyTextLabel().strip()
                    + ") "
                    "" + colorText.END
                )
            return menuText
        
    def renderLevel0Menus(self, asList=False, renderStyle=None, parent=None, skip=None):
        menuText = self.fromDictionary(
            level0MenuDict,
            renderExceptionKeys=["P", "T", "E", "U", "Z", "L", "D"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=["X"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a menu option:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("X") or menu().create('?','?')).keyTextLabel().strip()
                    + ") "
                    "" + colorText.END
                )
                try:
                    OTAUpdater.checkForUpdate(VERSION, skipDownload=True)
                except:
                    pass
            return menuText

    def renderLevel1_S_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        strategies = self.strategyNames
        counter = 1
        menuDict = {}
        for strategyName in strategies:
            menuDict[f"{counter}"] = strategyName.ljust(20)
            counter += 1
        for key in level1_S_MenuDict.keys():
            menuDict[key] = level1_S_MenuDict[key]

        menuText = self.fromDictionary(
            menuDict,
            renderExceptionKeys=level1_S_MenuDict.keys(),
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.THREE_PER_ROW,
            skip=skip,
            parent=parent,
        ).render(asList=asList)
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a Strategy for Screening:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > """
                    ""
                )
            return menuText
        
    def renderLevel1_T_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        defaultKey = 'L' if configManager.period == '1y' else 'S'
        menuText = self.fromDictionary(
            level1_T_MenuDict,
            renderExceptionKeys=["M","B"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=[defaultKey,"B"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a configuration period for Screening:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find(defaultKey) or menu().create('?','?')).keyTextLabel().strip()
                    + ")  "
                    "" + colorText.END
                )
            return menuText
        
    def renderLevel1_P_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level1_P_MenuDict,
            renderExceptionKeys=["M"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find('1') or menu().create('?','?')).keyTextLabel().strip()
                    + ")  "
                    "" + colorText.END
                )
            return menuText

    def renderLevel2_P_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level2_P_MenuDict,
            renderExceptionKeys=["M"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.TWO_PER_ROW,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a scanner:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find('1') or menu().create('?','?')).keyTextLabel().strip()
                    + ")  "
                    "" + colorText.END
                )
            return menuText

    def renderLevel2_Sectoral_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level1_index_options_sectoral,
            renderExceptionKeys=["2"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.TWO_PER_ROW,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=["2"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a sectoral index:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find('2') or menu().create('?','?')).keyTextLabel().strip()
                    + ")  "
                    "" + colorText.END
                )
            return menuText

    def renderLevel1_X_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level1_X_MenuDict,
            renderExceptionKeys=["W", "0", "M", "S", "15"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.THREE_PER_ROW,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["0", "15",str(configManager.defaultIndex)] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an Index for Screening:"
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find(str(configManager.defaultIndex)) or menu().create('?','?')).keyTextLabel().strip()
                    + ")  "
                    "" + colorText.END
                )
            return menuText

    def level2_T_MenuDict_L(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level2_T_MenuDict_L,
            renderExceptionKeys=["4","5","M"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a config period/candle-duration combination: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("1") or menu().create('?','?')).keyTextLabel().strip()
                    + ")  "
                    "" + colorText.END
                )
            return menuText

    def level2_T_MenuDict_S(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level2_T_MenuDict_S,
            renderExceptionKeys=["5", "M"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a config period/candle-duration combination: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("1") or menu().create('?','?')).keyTextLabel().strip()
                    + ")  "
                    "" + colorText.END
                )
            return menuText
        
    def renderLevel2_X_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level2_X_MenuDict,
            renderExceptionKeys=["0", "42", "M"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.TWO_PER_ROW,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["9"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select a Criterion for Stock Screening: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("9") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText

    def renderLevel3_X_Reversal_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level3_X_Reversal_MenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=["3"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("3") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText

    def renderLevel3_X_ChartPattern_Menus(
        self, skip=[], asList=False, renderStyle=MenuRenderStyle.STANDALONE, parent=None
    ):
        menuText = self.fromDictionary(
            level3_X_ChartPattern_MenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=["3"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("3") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText

    def renderLevel3_X_PopularStocks_Menus(
        self, skip=[], asList=False, renderStyle=MenuRenderStyle.STANDALONE, parent=None
    ):
        menuText = self.fromDictionary(
            level3_X_PopularStocks_MenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + ((self.find("1")) or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText

    def renderLevel3_X_StockPerformance_Menus(
        self, skip=[], asList=False, renderStyle=MenuRenderStyle.STANDALONE, parent=None
    ):
        menuText = self.fromDictionary(
            level3_X_StockPerformance_MenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("1") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText

    def renderLevel4_X_Lorenzian_Menus(
        self, skip=[], asList=False, renderStyle=MenuRenderStyle.STANDALONE, parent=None
    ):
        menuText = self.fromDictionary(
            level4_X_Lorenzian_MenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("1") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText


    def renderLevel4_X_ChartPattern_BBands_SQZ_Menus(
        self, skip=[], asList=False, renderStyle=MenuRenderStyle.STANDALONE, parent=None
    ):
        menuText = self.fromDictionary(
            level4_X_ChartPattern_BBands_SQZ_MenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("1") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText

    def renderLevel4_X_ChartPattern_MASignal_Menus(
        self, skip=[], asList=False, renderStyle=MenuRenderStyle.STANDALONE, parent=None
    ):
        menuText = self.fromDictionary(
            level4_X_ChartPattern_MASignalMenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList, coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("1") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText
        
    def renderLevel4_X_ChartPattern_Confluence_Menus(
        self, skip=[], asList=False, renderStyle=MenuRenderStyle.STANDALONE, parent=None
    ):
        menuText = self.fromDictionary(
            level4_X_ChartPattern_Confluence_MenuDict,
            renderExceptionKeys=["0"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList,coloredValues=["1"] if not asList else [])
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.BOLD
                    + colorText.WARN
                    + "[+] Select an option: "
                    + colorText.END
                )
                OutputControls().printOutput(
                    colorText.BOLD
                    + menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find("1") or menu().create('?','?')).keyTextLabel().strip() + ")"
                    + colorText.END
                )
            return menuText
        
# Fundamentally good compnaies but nearing 52 week low
# https://www.tickertape.in/screener/equity/prebuilt/SCR0005

# Dividend Gems
# https://www.tickertape.in/screener/equity/prebuilt/SCR0027

# Cash rich small caps
# https://www.tickertape.in/screener/equity/prebuilt/SCR0017
