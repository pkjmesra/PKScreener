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

import pkscreener.classes.ConfigManager as ConfigManager
from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger

configManager = ConfigManager.tools()

level0MenuDict = {
    "X": "Scanners",
    "S": "Strategies",
    "B": "Backtests",
    "T": "~",
    "E": "Edit user configuration",
    "Y": "View your user configuration",
    "U": "Check for software update",
    "H": "Help / About Developer",
    "Z": "Exit (Ctrl + C)",
}
level1_X_MenuDict = {
    "W": "Screen stocks from my own Watchlist",
    "N": "Nifty Prediction using Artifical Intelligence (Use for Gap-Up/Gap-Down/BTST/STBT)",
    "E": "Live Index Scan : 5 EMA for Intraday",
    "0": "Screen stocks by the stock names (NSE Stock Code)",
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
    "11": "Nifty Midcap 150",
    "12": "Nifty (All Stocks)",
    "13": "Newly Listed (IPOs in last 2 Year)        ",
    "14": "F&O Stocks Only",
    "M": "Back to the Top/Main menu",
    "Z": "Exit (Ctrl + C)",
}
level2_X_MenuDict = {
    "0": "Full Screening (Shows Technical Parameters without any criterion)",
    "1": "Probable Breakouts              ",
    "2": "Recent Breakouts & Volumes",
    "3": "Consolidating stocks            ",
    "4": "Lowest Volume in last 'N'-days (Early Breakout Detection)",
    "5": "RSI screening                   ",
    "6": "Reversal Signals",
    "7": "Stocks making Chart Patterns    ",
    "8": "CCI outside of the given range",
    "9": "Volume gainers                  ",
    "10": "Closing at least 2% up since last 3 days",
    "11": "Short term bullish stocks(Intraday)",
    "12": "15 Minute Price & Volume breakout(Intraday)",
    "13": "Bullish RSI & MACD(Intraday)       ",
    "14": "NR4 Daily Today",
    "15": "52 week low breakout(today/1 wk)",
    "16": "10 days low breakout",
    "17": "52 week high breakout(today/1 wk)",
    "18": "Bullish Aroon(14) Crossover",
    "19": "MACD Histogram x below 0       ",
    "20": "Bullish for next day",
    "21": "RSI entering bullish territory     ",
    "23": "Bearish CCI crossover           ",
    "24": "RSI above 30 and price > psar      ",
    "25": "Intraday Momentum Build-up      ",
    "26": "Extremely bullish daily close      ",
    "27": "Rising RSI                      ",
    "28": "Dividend Yield",
    "42": "Show Last Screened Results",
    "M": "Back to the Top/Main menu",
    "Z": "Exit (Ctrl + C)",
}
level3_X_Reversal_MenuDict = {
    "1": "Buy Signals (Bullish Reversal)",
    "2": "Sell Signals (Bearish Reversal)",
    "3": "Momentum Gainers (Rising Bullish Momentum)",
    "4": "Reversal at Moving Average (Bullish Reversal)",
    "5": "Volume Spread Analysis (Bullish VSA Reversal)",
    "6": "Narrow Range (NRx) Reversal",
    "0": "Cancel",
}
level3_X_ChartPattern_MenuDict = {
    "1": "Bullish Inside Bar (Flag) Pattern",
    "2": "Bearish Inside Bar (Flag) Pattern",
    "3": "The Confluence (50 & 200 MA/EMA)",
    "4": "VCP (Experimental)",
    "5": "Buying at Trendline (Ideal for Swing/Mid/Long term)",
    "6": "Narrow Range (NRx) Reversal",
    "0": "Cancel",
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

    def create(self, key, text, level=0, isException=False, parent=None):
        self.menuKey = str(key)
        self.menuText = text
        self.level = level
        self.isException = isException
        self.parent = parent
        return self

    def keyTextLabel(self):
        return f"{self.menuKey} > {self.menuText}"

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

    def render(self):
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
        return t

    def renderSpecial(self, menuKey):
        configManager.getConfig(ConfigManager.parser)
        menuText = "~"
        if self.level == 0 and menuKey == "T":
            menuText = (
                "Toggle between long-term (Default)"
                + colorText.WARN
                + " [Current]"
                + colorText.END
                + " and Intraday user configuration\n"
                if not configManager.isIntradayConfig()
                else "Toggle between long-term (Default) and Intraday"
                + colorText.WARN
                + " [Current]"
                + colorText.END
                + " user configuration"
            )
        return menuText


# This Class manages application menus
class menus:
    def __init__(self):
        self.level = 0
        self.menuDict = {}

    def fromDictionary(
        self,
        rawDictionary={},
        renderStyle=MenuRenderStyle.STANDALONE,
        renderExceptionKeys=[],
        skip=[],
        parent=None,
    ):
        tabLevel = 0
        self.menuDict = {}
        for key in rawDictionary:
            if key in skip:
                continue
            m = menu()
            m.create(
                str(key).upper(), rawDictionary[key], level=self.level, parent=parent
            )
            if key in renderExceptionKeys:
                m.isException = True
            elif str(key).isnumeric():
                m.hasLeftSibling = False if tabLevel == 0 else True
                tabLevel = tabLevel + 1
                if tabLevel >= renderStyle.value:
                    tabLevel = 0
            self.menuDict[str(key).upper()] = m
        return self

    def render(self, asList=False):
        menuText = [] if asList else ""
        for k in self.menuDict.keys():
            m = self.menuDict[k]
            if asList:
                menuText.append(m)
            else:
                menuText = menuText + m.render()
        return menuText

    def renderForMenu(self, selectedMenu=None, skip=[], asList=False, renderStyle=None):
        if selectedMenu is None and self.level == 0:
            # Top level Application Main menu
            return self.renderLevel0Menus(
                skip=skip, asList=asList, renderStyle=renderStyle, parent=selectedMenu
            )
        elif selectedMenu is not None:
            if selectedMenu.level == 0:
                self.level = 1
                # sub-menu of the top level main selected menu
                return self.renderLevel1_X_Menus(
                    skip=skip,
                    asList=asList,
                    renderStyle=renderStyle,
                    parent=selectedMenu,
                )
            elif selectedMenu.level == 1:
                self.level = 2
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
                return (
                    self.renderLevel3_X_Reversal_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                    if selectedMenu.menuKey == "6"
                    else self.renderLevel3_X_ChartPattern_Menus(
                        skip=skip,
                        asList=asList,
                        renderStyle=renderStyle,
                        parent=selectedMenu,
                    )
                )

    def find(self, key=None):
        if key is not None:
            try:
                return self.menuDict[str(key).upper()]
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                return None
        return None

    def renderLevel0Menus(self, asList=False, renderStyle=None, parent=None, skip=None):
        menuText = self.fromDictionary(
            level0MenuDict,
            renderExceptionKeys=["T", "E", "U"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
        ).render(asList=asList)
        if asList:
            return menuText
        else:
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Select a menu option:"
                + colorText.END
            )
            print(
                colorText.BOLD
                + menuText
                + """

        Enter your choice >  (default is """
                + colorText.WARN
                + self.find("X").keyTextLabel()
                + ") "
                "" + colorText.END
            )
            return menuText

    def renderLevel1_X_Menus(
        self, skip=[], asList=False, renderStyle=None, parent=None
    ):
        menuText = self.fromDictionary(
            level1_X_MenuDict,
            renderExceptionKeys=["W", "0", "M"],
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.THREE_PER_ROW,
            skip=skip,
            parent=parent,
        ).render(asList=asList)
        if asList:
            return menuText
        else:
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Select an Index for Screening:"
                + colorText.END
            )
            print(
                colorText.BOLD
                + menuText
                + """

        Enter your choice > (default is """
                + colorText.WARN
                + self.find("12").keyTextLabel()
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
        ).render(asList=asList)
        if asList:
            return menuText
        else:
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Select a Criterion for Stock Screening: "
                + colorText.END
            )
            print(
                colorText.BOLD
                + menuText
                + """

        """
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
        ).render(asList=asList)
        if asList:
            return menuText
        else:
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Select an option: "
                + colorText.END
            )
            print(
                colorText.BOLD
                + menuText
                + """

        """
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
        ).render(asList=asList)
        if asList:
            return menuText
        else:
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Select an option: "
                + colorText.END
            )
            print(
                colorText.BOLD
                + menuText
                + """

        """
                + colorText.END
            )
            return menuText
