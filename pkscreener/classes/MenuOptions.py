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

STOCK_EXCHANGE_DICT = {
    "1" : "NSE - India",
    "2" : "NASDAQ - US",
    "3" : "Borso - Turkey",
}

userTypeMenuDict = {
    "1": "I am a paid/premium subscriber",
    "2": "I am a free/trial user",
    "Z": "Exit (Ctrl + C)",
}

userDemoMenuDict = {
    "1": "Show me a demo!",
    "2": "I would like to subscribe",
    "3": "I am already a subscriber",
    "Z": "Exit (Ctrl + C)",
}

level0MenuDict = {
    "F": "Find a stock in scanners",
    "M": "Monitor Intraday",
    "S": "Strategies",
    "B": "Backtests",
    "G": "Growth of 10k",
    "C": "Analyse morning vs close outcomes",
    "P": "Piped Scanners",
    "D": "Data Downloads",
    "X": "Scanners",
    "T": "~",
    "E": "Edit user configuration",
    "Y": "View your user configuration",
    "U": "Check for software update",
    "L": "Collect Logs for Debugging",
    "H": "About PKScreener",
    "Z": "Exit (Ctrl + C)",
}
level1_index_options_sectoral= {
    "1": "BSE Sensex (^BSESN)                               ",
    "2": "Nifty 50 (^NSEI)                                  ",
    "3": "NIFTY 100 (^CNX100)                               ",
    "4": "Nifty 100 ESG Sector Leaders (NIFTY100_ESG.NS)    ",
    "5": "NIFTY 200 (^CNX200)                               ",
    "6": "NIFTY 500 (^CNX500)                               ",
    "7": "NIFTY500 MULTICAP 50:25:25 (NIFTY500_MULTICAP.NS) ",
    "8": "NIFTY ALPHA 50 (NIFTYALPHA50.NS)                  ",
    "9": "Nifty Auto (^CNXAUTO)                             ",
    "10": "Nifty Bank (^NSEBANK)                            ",
    "11": "NIFTY COMMODITIES (^CNXCMDT)                     ",
    "12": "Nifty Consumer Durables (NIFTY_CONSR_DURBL.NS)   ",
    "13": "Nifty Consumption (^CNXCONSUM)                   ",
    "14": "NIFTY CPSE (NIFTY_CPSE.NS)                       ",
    "15": "Nifty Energy (^CNXENERGY)                        ",
    "16": "Nifty Financial Services 25/50 (^CNXFIN)         ",
    "17": "Nifty Financial Services (NIFTY_FIN_SERVICE.NS)  ",
    "18": "Nifty FMCG (^CNXFMCG)                            ",
    "19": "Nifty Healthcare (NIFTY_HEALTHCARE.NS)           ",
    "20": "Nifty IT (^CNXIT)                                ",
    "21": "Nifty Infra (^CNXINFRA)                          ",
    "22": "Nifty Large and MidCap 250 (NIFTY_LARGEMID_250.NS)",
    "23": "Nifty Media (^CNXMEDIA)                          ",
    "24": "Nifty Metal (^CNXMETAL)                          ",
    "25": "NIFTY MICROCAP 250 (NIFTY_MICROCAP250.NS)        ",
    "26": "Nifty MidCap 50 (^NSEMDCP50)                     ",
    "27": "Nifty MidCap 100 (NIFTY_MIDCAP_100.NS)           ",
    "28": "NIFTY MIDCAP 150 (NIFTYMIDCAP150.NS)             ",
    "29": "NIFTY MIDCAP SELECT (NIFTY_MID_SELECT.NS)        ",
    "30": "NIFTY MIDSMALLCAP 400 (NIFTYMIDSML400.NS)        ",
    "31": "Nifty MidSmall Healthcare (NIFTY_MIDSML_HLTH.NS) ",
    "32": "NIFTY MNC (^CNXMNC)                              ",
    "33": "NIFTY NEXT 50 (^NSMIDCP)                         ",
    "34": "Nifty Oil and Gas (NIFTY_OIL_AND_GAS.NS)         ",
    "35": "Nifty Pharma (^CNXPHARMA)                        ",
    "36": "Nifty Private Bank (NIFTY_PVT_BANK.NS)           ",
    "37": "NIFTY PSE (^CNXPSE)                              ",
    "38": "Nifty PSU Bank (^CNXPSUBANK)                     ",
    "39": "Nifty Realty (^CNXREALTY)                        ",
    "40": "Nifty Service Sector (^CNXSERVICE)               ",
    "41": "NIFTY SMALLCAP 50 (NIFTYSMLCAP50.NS)             ",
    "42": "NIFTY SMALLCAP 100 (^CNXSC)                      ",
    "43": "NIFTY SMALLCAP 250 (NIFTYSMLCAP250.NS)           ",
    "44": "NIFTY TOTAL MARKET (NIFTY_TOTAL_MKT.NS)          ",
    "45": "INDIA VIX (^INDIAVIX)                            ",

    "46": "All of the above",
}
level1_P_MenuDict = {
    "1": "Predefined Piped Scanners",
    "2": "Define my custom Piped Scanner",
    "3": "Run Piped Scans Saved So Far",
    "4": "Predefined Piped Scanners for My Watchlist",
    "M": "Back to the Top/Main menu",
}
LEVEL_1_DATA_DOWNLOADS = {
    "D": "Download Daily OHLC Data for the Past Year",
    "I": "Download Intraday OHLC Data for the Last Trading Day",
    "N": "NSE Equity Symbols",
    "S": "NSE Symbols with Sector/Industry Details",
    "M": "Back to the Top/Main menu",
}
PREDEFINED_SCAN_ALERT_MENU_KEYS = ["1","5","6","8","18","22","25","27","28","29","30","31","32","33"]
PREDEFINED_SCAN_MENU_KEYS = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20", "21", "22", "23", "24", "25","26","27","28","29","30","31","32","33"]
PREDEFINED_SCAN_MENU_TEXTS = [
    "Volume Scanners | High Momentum | Breaking Out Now | ATR Cross     ",  # 1
    "Volume Scanners | High Momentum | ATR Cross",                          # 2
    "Volume Scanners | High Momentum                                    ",  # 3
    "Volume Scanners | ATR Cross",                                          # 4
    "Volume Scanners | High Bid/Ask Build Up                            ",  # 5
    "Volume Scanners | ATR Cross | ATR Trailing Stops",                     # 6
    "Volume Scanners | ATR Trailing Stops                               ",  # 7
    "High Momentum | ATR Cross",                                            # 8
    "High Momentum | ATR Trailing Stop                                  ",  # 9
    "ATR Cross | ATR Trailing Stop",                                        # 10
    "TTM Sqeeze Buy | RSI b/w 0 to 54                                   ",  # 11
    "Volume Scanners | High Momentum | Breaking Out Now | ATR Cross | RSI b/w 0 to 54", # 12
    "Volume Scanners | ATR Cross | RSI b/w 0 to 54                      ",  # 13
    "VCP (Mark Minervini) | Chart Patterns | MA Support",                   # 14
    "VCP | Chart Patterns | MA Support                                  ",  # 15
    "Already Breaking out | VCP (Minervini) | Chart Patterns | MA Support", # 16
    "ATR Trailing Stops | VCP (Minervini)                               ",  # 17
    "VCP | ATR Trailing Stops",                                             # 18
    "Nifty 50,Nifty Bank | VCP | ATR Trailing Stops                     ",  # 19
    "Volume Scanners | High Momentum | Breaking Out Now | ATR Cross | VCP | ATR Trailing Stops", # 20
    "BullCross-MA | Fair Value Buy Opportunities                        ",  # 21
    "VCP | Chart Patterns | MA Support | Bullish AVWAP",                    # 22
    "VCP (Mark Minervini) | Chart Patterns | MA Support | Bullish AVWAP ",  # 23
    "BullCross-VWAP | Volume Scanners",                                     # 24
    "BullCross-VWAP | ATR Cross | ATR Trailing Stop                     ",  # 25
    "Super-Confluence | ATR Trailing Stop                               ",  # 26
    "BullCross-VWAP | Super-Confluence (BTST)                           ",  # 27
    "VCP | Volume-Breakout                                              ",  # 28
    "VCP | Volume-Breakout | Price Breakout                             ",  # 29
    "VCP | Super-Confluence                                             ",  # 30
    "Bullish Today x PDO/PDC | VCP                                      ",  # 31
    "Intraday(15m) VCP | Breaking out now                               ",  # 32
    "ATR Cross | Low RSI (<=40)                                         ",  # 33
]
level2_P_MenuDict = {}
for key in PREDEFINED_SCAN_MENU_KEYS:
    level2_P_MenuDict[key] = PREDEFINED_SCAN_MENU_TEXTS[int(key)-1]
level2_P_MenuDict["M"] = "Back to the Top/Main menu"
NA_NON_MARKET_HOURS = ["X:12:9:2.5:>|X:0:29:"]
PREDEFINED_SCAN_MENU_VALUES =[
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:'", # 1
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:27:'",          # 2
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:'",                   # 3
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:27:'",                   # 4
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:29:'",                   # 5
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:27:>|X:12:30:1:'",       # 6
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:12:30:1:'",                # 7
    "--systemlaunched -a y -e -o 'X:12:31:>|X:0:27:'",                      # 8
    "--systemlaunched -a y -e -o 'X:12:31:>|X:0:30:1:'",                    # 9
    "--systemlaunched -a y -e -o 'X:12:27:>|X:0:30:1:'",                    # 10
    "--systemlaunched -a y -e -o 'X:12:7:6:1:>|X:0:5:0:54: i 1m'",               # 11
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:>|X:0:5:0:54:i 1m'", # 12
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:27:>|X:0:5:0:54:i 1m'",      # 13
    "--systemlaunched -a y -e -o 'X:12:7:8:>|X:12:7:9:1:1:'",               # 14
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:12:7:9:1:1:'",               # 15
    "--systemlaunched -a y -e -o 'X:12:2:>|X:12:7:8:>|X:12:7:9:1:1:'",      # 16
    "--systemlaunched -a y -e -o 'X:12:30:1:>|X:12:7:8:'",                  # 17
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:12:30:1:'",                  # 18
    "--systemlaunched -a y -e -o 'X:0:0:^NSEI,^NSEBANK:>|X:12:7:4:>|X:12:30:1:'", # 19
    "--systemlaunched -a y -e -o 'X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:>|X:12:7:4:>|X:12:30:1:'",  # 20
    "--systemlaunched -a y -e -o 'X:12:7:9:5:>|X:12:21:8:'",                # 21
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:12:7:9:1:1:>|X:12:34:'",     # 22
    "--systemlaunched -a y -e -o 'X:12:7:8:>|X:12:7:9:1:1:>|X:12:34:'",     # 23
    "--systemlaunched -a y -e -o 'X:12:7:9:7:>|X:0:9:2.5:'",                # 24
    "--systemlaunched -a y -e -o 'X:12:7:9:7:>|X:0:31:>|X:0:30:1:'",        # 25
    "--systemlaunched -a y -e -o 'X:12:7:3:0.008:4:>|X:0:30:1:'",           # 26
    # Running super conf at the beginning will be faster because there will be less number of stocks.
    # Running it at the end is essential because we want to see the dates of super-conf
    "--systemlaunched -a y -e -o 'X:12:7:3:0.008:4:>|X:12:7:9:7:>|X:0:7:3:0.008:4:'", # 27
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:0:9:2.5:'",                  # 28
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:0:9:2.5:>|X:0:27:'",         # 29
    "--systemlaunched -a y -e -o 'X:12:7:4:>|X:0:7:3:0.008:4:'",            # 30
    "--systemlaunched -a y -e -o 'X:12:33:2:>|X:0:7:4:'",                   # 31
    "--systemlaunched -a y -e -o 'X:14:7:4:i 15m:>|X:0:23:'",               # 32
    "--systemlaunched -a y -e -o 'X:12:27:>|X:0:5:0:40:i 1m:'",             # 33
]
PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS = []
PREDEFINED_PIPED_MENU_OPTIONS = {}
pipedIndex = 0
for option in PREDEFINED_SCAN_MENU_VALUES:
    pipedOptions = []
    argOptions = option.split("-o ")[-1]
    analysisOptions = argOptions.split("|")
    for analysisOption in analysisOptions:
        analysisOption = analysisOption.replace(">","").replace("X:0:","X:12:").replace("'","").replace("\"","")
        if "." in analysisOption:
            inputOptions = analysisOption.split(":")
            inputOptionsCopy = inputOptions
            for inputOption in inputOptions:
                if "." in inputOption:
                    inputOptionsCopy.remove(inputOption)
            analysisOption = ":".join(inputOptionsCopy)
        pipedOptions.append(analysisOption)
    PREDEFINED_PIPED_MENU_OPTIONS[f"P_1_{PREDEFINED_SCAN_MENU_KEYS[pipedIndex]}"] = pipedOptions
    pipedIndex += 1
    analysisOptions[-1] = analysisOptions[-1].replace("X:","C:")
    argOptions = "|".join(analysisOptions)
    PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS.append(argOptions.replace("'","").replace("\"",""))

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
    "2": "Weekly (5y, 1wk)",
    "3": "Monthly (max, 1mo)",
    "4": "Hourly (4mo, 1h)",
    "5": "Custom",

    "M": "Back to the Top/Main menu",
}
level2_T_MenuDict_S = {
    "1": "1m (1d, 1m)",
    "2": "5m (5d, 5m)",
    "3": "15m (1mo, 15m)",
    "4": "30m (2mo, 30m)",
    "5": "Custom",

    "M": "Back to the Top/Main menu",
}
CANDLE_PERIOD_DICT={}
CANDLE_DURATION_DICT={}
frequencyDicts = [level2_T_MenuDict_L,level2_T_MenuDict_S]
for frequencyDict in frequencyDicts:
    for candlePeriodKey in frequencyDict.keys():
        if frequencyDict[candlePeriodKey] != "Custom" and candlePeriodKey != "M":
            periodDurationTuple = frequencyDict[candlePeriodKey].split("(")[1].split(")")[0]
            period = periodDurationTuple.split(",")[0].strip()
            duration = periodDurationTuple.split(",")[1].strip()
            CANDLE_PERIOD_DICT[period] = duration
            CANDLE_DURATION_DICT[duration] = period

level1_S_MenuDict = {
    "S": "Summary",

    "M": "Back to the Top/Main menu",
    "Z": "Exit (Ctrl + C)",
}

INDICES_MAP = {}

level1_X_MenuDict = {
    "0": "Screen stocks by the stock names",
    "1": "Nifty 50          ",
    "N": "Nifty Prediction using Artifical Intelligence (Use for Gap-Up/Gap-Down/BTST/STBT)",
    "S": "Sectoral Indices",
    "E": "Live Index Scan : 5 EMA for Intraday",
    "W": "Screen stocks from my own Watchlist",
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
    "13": "Newly Listed (IPOs in last 1 Year)           ",
    "14": "F&O Stocks Only", #Discontinued:  https://nsearchives.nseindia.com/content/circulars/FAOP61157.pdf
    "15": "NASDAQ",

    "M": "Back to the Top/Main menu",
    "Z": "Exit (Ctrl + C)",
}
for indexKey in level1_X_MenuDict.keys():
    if (indexKey.isnumeric() and int(indexKey) > 0) or (indexKey in ["M"]):
        INDICES_MAP[indexKey] = level1_X_MenuDict[indexKey].strip()

level2_X_MenuDict = {
    "0": "Full Screening (Shows Technical Parameters without any criterion)",
    "1": "Probable Breakouts/Breakdowns             ",
    "2": "Today's Breakouts/Breakdowns              ",
    "3": "Consolidating stocks                      ",
    "4": "Lowest Volume in last N-days (Early Breakout Detection)",
    "5": "RSI screening                             ",
    "6": "Reversal Signals                          ",
    "7": "Stocks making Chart Patterns              ",
    "8": "CCI outside of the given range            ",
    "9": "Volume gainers                            ",
    "10": "Closing at least 2% up since last 3 days ",
    "11": "Short term bullish (Ichimoku)            ",
    "12": "N-Minute Price & Volume breakout(Intraday)",
    "13": "Bullish RSI & MACD                       ",
    "14": "NR4 Daily Today                          ",
    "15": "52 week low breakout(today)(Sell)        ",
    "16": "10 days low breakout(Sell)               ",
    "17": "52 week high breakout(today)             ",
    "18": "Bullish Aroon(14) Crossover              ",
    "19": "MACD Histogram x below 0 (Sell)          ",
    "20": "Bullish for next day                     ",
    "21": "MF/FIIs Popular Stocks                   ",
    "22": "View Stock Performance                   ",
    "23": "Breaking out now                         ",
    "24": "Higher Highs,Lows & Close (SuperTrend)   ",
    "25": "Lower Highs,Lows (Watch for Rev.)        ",
    "26": "Stocks with stock-split/bonus/dividends  ",
    "27": "ATR Cross                                ",
    "28": "Bullish Higher Opens                     ",
    "29": "Intraday Bid/Ask Build-up                ",
    "30": "ATR Trailing Stops(Swing Paper Trading)  ",
    "31": "High Momentum(RSI,MFI,CCI)               ",
    "32": "Intraday Breakout/Breakdown setup        ",
    "33": "Potential Profitable setups              ",
    "34": "Bullish Anchored-VWAP                    ",
    "35": "Perfect Short Sells (Futures)            ",
    "36": "Probable Short Sells (Futures)           ",
    "37": "Short Sell Candidates (Volume SMA)       ",
    "38": "Intraday Short Sell (PSAR / Volume SMA)  ",
    "39": "IPO-Lifetime First day bullish break     ",
    "40": "Price Action                             ",
    "41": "Pivot Points                             ",
    "50": "Show Last Screened Results               ",

    "M": "Back to the Top/Main menu                 ",
    "Z": "Exit (Ctrl + C)                           ",
}
MAX_SUPPORTED_MENU_OPTION = 41
MAX_MENU_OPTION = 50

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
level3_X_PotentialProfitable_MenuDict = {
    "1": "Frequent highs with bullish MAs",
    "2": "Bullish Today for Previous Day Open/Close (PDO/PDC) with 1M Volume",
    "3": "FnO Trades > 2% /Above 50MA/200MA(5Min)",

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
    "7": "BullCross VWAP",

    "0": "Cancel",
}

level4_X_ChartPattern_BBands_SQZ_MenuDict = {
    "1": "TTM Squeeze-Buy",
    "2": "TTM In-Squeeze",
    "3": "TTM Squeeze-Sell",
    "4": "Any/All",

    "0": "Cancel",
}

level4_X_ChartPattern_Confluence_MenuDict = {
    "1": "Confluence up / GoldenCrossOver / DMA50 / DMA200",
    "2": "Confluence Down / DeadCrossOver",
    "3": "Any/All (Confluence up/down/Crossovers)",
    "4": "8,21,55-EMA / 200-SMA Super-Confluence (BTST-Buy at close, Sell early next day)",

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
    "3": "Use Sliding-Window-Timeframe to run this scan category or piped scan {0}",
    "4": "Add {0} to my monitoring options",
    "5": "Pipe outputs of {0} into another scanner",

    "M": "Back to the Top/Main menu",
}
Pin_MenuDict_Keys = [x for x in Pin_MenuDict.keys() if str(x).isnumeric()]

PRICE_CROSS_SMA_EMA_TYPE_MENUDICT = {
    "1": "SMA",
    "2": "EMA",

    "0": "Cancel"
}
PRICE_CROSS_PIVOT_POINT_TYPE_MENUDICT = {
    "1": "Pivot Point (PP)",

    "2": "Support Level 1 (S1)",
    "3": "Support Level 2 (S2)",
    "4": "Support Level 3 (S3)",

    "5": "Resistance Level 1 (R1)",
    "6": "Resistance Level 2 (R2)",
    "7": "Resistance Level 3 (R3)",

    "0": "Cancel"
}
PRICE_CROSS_SMA_EMA_DIRECTION_MENUDICT = {
    "1": "Price Crosses From Above (Sell)",
    "2": "Price Crosses From Below (Buy)",

    "0": "Cancel"
}

from pkscreener.classes.CandlePatterns import CandlePatterns
CANDLESTICK_DICT = {}
candleStickMenuIndex = 1
for candlestickPattern in CandlePatterns.reversalPatternsBullish:
    CANDLESTICK_DICT[str(candleStickMenuIndex)] = candlestickPattern
    candleStickMenuIndex += 1
for candlestickPattern in CandlePatterns.reversalPatternsBearish:
    CANDLESTICK_DICT[str(candleStickMenuIndex)] = candlestickPattern
    candleStickMenuIndex += 1
CANDLESTICK_DICT["0"] = "No Filter"
CANDLESTICK_DICT["M"] = "Cancel"

CANDLESTICK_DICT_Keys = [x for x in CANDLESTICK_DICT.keys() if str(x).isnumeric() and int(x) > 0]

class MenuRenderStyle(Enum):
    STANDALONE = 1
    TWO_PER_ROW = 2
    THREE_PER_ROW = 3


class menu:
    def __init__(self,menuKey="",level=0,parent=None):
        self.menuKey = menuKey
        self.menuText = ""
        self.submenu = None
        self.level = level
        self.isException = None
        self.hasLeftSibling = False
        self.parent = parent
        self.line = 0
        self.lineIndex = 0
        self.isPremium = False

    def create(self, key, text, level=0, isException=False, parent=None):
        self.menuKey = str(key)
        self.menuText = text
        self.level = level
        self.isException = isException
        self.parent = parent
        self.line = 0
        self.lineIndex = 0
        self.isPremium
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
        self.isPremium = "₹/$" in t
        if self.isPremium:
            t = t.replace("(₹/$)",f"{colorText.WHITE}({colorText.END}{colorText.FAIL}₹/${colorText.END}{colorText.WHITE}){colorText.END}")    
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
        if index > MAX_MENU_OPTION:
            return [], {}
        menuOptions = [topLevel]
        indexOptions =[index]
        # Ignore the option "0" and the last 3 menu keys because 
        # those are to exit, going back to main menu and showing 
        # last screen results 
        scanOptionKeys = list(level2_X_MenuDict.keys()) #[1:-3]
        # These have to be ignored because these are irrelevant from 
        # scan perspective
        scanOptionsToIgnore = ["0","22","26","29",str(MAX_MENU_OPTION),"M","Z"]
        from PKDevTools.classes.PKDateUtilities import PKDateUtilities
        isTrading = PKDateUtilities.isTradingTime()
        if isTrading:
            # Don't ignore the bid/ask difference scan option if it's 
            # trading hour. Bid vs ask can only be run during trading 
            # hours.
            scanOptionsToIgnore.remove("29")
        for scanOption in scanOptionsToIgnore:
            scanOptionKeys.remove(scanOption)
        scanOptions = scanOptionKeys
        runOptions = []
        runKeyOptions = {}
        topMenu = menu(menuKey=topLevel,level=0)
        for menuOption in menuOptions:
            for indexOption in indexOptions:
                parentMenu = menu(menuKey=scanOptions[0],level=1,parent=topMenu)
                menuItems = menus()
                childMenus  = menuItems.renderForMenu(parentMenu,asList=True)
                for childMenu in childMenus:
                    if childMenu.menuKey in scanOptionsToIgnore:
                        continue
                    level1ChildMenus  = menuItems.renderForMenu(childMenu,asList=True)
                    if level1ChildMenus is None:
                        runOption = f"{menuOption}:{indexOption}:{childMenu.menuKey}:D:D:D:D:D"
                        runOptions.append(runOption)
                        runKeyOptions[runOption.replace(":D","")] = childMenu.menuText.strip()
                    else:
                        for level1ChildMenu in level1ChildMenus:
                            if level1ChildMenu.menuText in ["Any/All","Cancel"]:
                                continue
                            level2ChildMenus  = menuItems.renderForMenu(level1ChildMenu,asList=True)
                            if level2ChildMenus is None:
                                runOption = f"{menuOption}:{indexOption}:{childMenu.menuKey}:{level1ChildMenu.menuKey}:D:D:D:D:D"
                                runOptions.append(runOption)
                                runKeyOptions[runOption.replace(":D","")] = f"{childMenu.menuText.strip()}>{level1ChildMenu.menuText.strip()}"
                            else:
                                for level2ChildMenu in level2ChildMenus:
                                    if level2ChildMenu.menuText in ["Any/All","Cancel"]:
                                        continue
                                    level3ChildMenus  = menuItems.renderForMenu(level2ChildMenu,asList=True)
                                    if level3ChildMenus is None:
                                        runOption = f"{menuOption}:{indexOption}:{childMenu.menuKey}:{level1ChildMenu.menuKey}:{level2ChildMenu.menuKey}:D:D:D:D:D"
                                        runOptions.append(runOption)
                                        runKeyOptions[runOption.replace(":D","")] = f"{childMenu.menuText.strip()}>{level1ChildMenu.menuText.strip()}>{level2ChildMenu.menuText.strip()}"
                                    else:
                                        for level3ChildMenu in level3ChildMenus:
                                            if level3ChildMenu.menuText in ["Any/All","Cancel"]:
                                                continue
                                            level4ChildMenus  = menuItems.renderForMenu(level3ChildMenu,asList=True)
                                            if level4ChildMenus is None:
                                                runOption = f"{menuOption}:{indexOption}:{childMenu.menuKey}:{level1ChildMenu.menuKey}:{level2ChildMenu.menuKey}:{level3ChildMenu.menuKey}:D:D:D:D:D"
                                                runOptions.append(runOption)
                                                runKeyOptions[runOption.replace(":D","")] = f"{childMenu.menuText.strip()}>{level1ChildMenu.menuText.strip()}>{level2ChildMenu.menuText.strip()}>{level3ChildMenu.menuText.strip()}"
                                            else:
                                                for level4ChildMenu in level4ChildMenus:
                                                    if level4ChildMenu.menuText in ["Any/All","Cancel"]:
                                                        continue
                                                    level5ChildMenus  = menuItems.renderForMenu(level4ChildMenu,asList=True)
                                                    if level5ChildMenus is None:
                                                        runOption = f"{menuOption}:{indexOption}:{childMenu.menuKey}:{level1ChildMenu.menuKey}:{level2ChildMenu.menuKey}:{level3ChildMenu.menuKey}:{level4ChildMenu.menuKey}:D:D:D:D:D"
                                                        runOptions.append(runOption)
                                                        runKeyOptions[runOption.replace(":D","")] = f"{childMenu.menuText.strip()}>{level1ChildMenu.menuText.strip()}>{level2ChildMenu.menuText.strip()}>{level3ChildMenu.menuText.strip()}>{level4ChildMenu.menuText.strip()}"
                                                    else:
                                                        for level5ChildMenu in level5ChildMenus:
                                                            if level5ChildMenu.menuText in ["Any/All","Cancel"]:
                                                                continue
                                                            try:
                                                                level6ChildMenus  = menuItems.renderForMenu(level5ChildMenu,asList=True)
                                                            except: # pragma: no cover
                                                                level6ChildMenus = None
                                                                pass
                                                            if level6ChildMenus is None:
                                                                runOption = f"{menuOption}:{indexOption}:{childMenu.menuKey}:{level1ChildMenu.menuKey}:{level2ChildMenu.menuKey}:{level3ChildMenu.menuKey}:{level4ChildMenu.menuKey}:{level5ChildMenu.menuKey}:D:D:D:D:D"
                                                                runOptions.append(runOption)
                                                                runKeyOptions[runOption.replace(":D","")] = f"{childMenu.menuText.strip()}>{level1ChildMenu.menuText.strip()}>{level2ChildMenu.menuText.strip()}>{level3ChildMenu.menuText.strip()}>{level4ChildMenu.menuText.strip()}>{level5ChildMenu.menuText.strip()}"
        return runOptions, runKeyOptions

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
        substitutes=[],
        subOnly=[]
    ):
        tabLevel = 0
        self.menuDict = {}
        line = 0
        lineIndex = 1
        substituteIndex = 0
        rawDictionary = { k:v.strip() for k, v in rawDictionary.items()}
        dictToRender = dict((key,rawDictionary[key]) for key in rawDictionary.keys() if str(key).isnumeric())
        dictToRenderOnTheirOwnLine = {key: rawDictionary[key] for key in renderExceptionKeys}
        keysToRender = set(dictToRender) - set(dictToRenderOnTheirOwnLine)
        dictToRender = {key: rawDictionary[key] for key in keysToRender}
        if len(dictToRender.keys()) > 0:
            maxLengthOfItem = len(max(dictToRender.values(), key=len)) + 4
        else:
            maxLengthOfItem = 0
        for key in rawDictionary:
            if skip is not None and key in skip:
                continue
            m = menu()
            menuText = str(rawDictionary[key])
            if "{0}" in menuText and len(substitutes) > 0:
                if isinstance(substitutes[substituteIndex],int) and substitutes[substituteIndex] == 0:
                    substituteIndex += 1
                    continue
                menuText = menuText.format(f"{colorText.WARN}{substitutes[substituteIndex]}{colorText.END}")
                substituteIndex += 1
            menuText = f"{menuText if str(key) not in subOnly else f'{menuText}(₹/$)'}"
            menuText = menuText.ljust(maxLengthOfItem+7) if key in dictToRender.keys() else menuText
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

    def renderPinnedMenu(self,substitutes=[],skip=[]):
        return self.renderMenuFromDictionary(dict=Pin_MenuDict,
                                                 exceptionKeys=["M"],
                                                 coloredValues=(["M"]),
                                                 defaultMenu="M",
                                                 substitutes = substitutes,
                                                 skip=skip,
                                                 subOnly=Pin_MenuDict_Keys)
    
    def renderCandleStickPatterns(self,skip=[]):
        return self.renderMenuFromDictionary(dict=CANDLESTICK_DICT,
                                                 exceptionKeys=["0","M"],
                                                 coloredValues=(["0"]),
                                                 defaultMenu="0",
                                                 renderStyle=MenuRenderStyle.TWO_PER_ROW,
                                                 optionText="  [+] Would you like to filter by a specific Candlestick pattern? Select filter:",
                                                 skip=skip)
    
    def renderUserType(self, selectedMenu:menu=None, skip=[], asList=False, renderStyle=None):
            # Top level Application Main menu for user type
            return self.renderMenuFromDictionary(dict=userTypeMenuDict,
                                                exceptionKeys=["1","2","Z"],
                                                coloredValues=(["1"] if not asList else []),
                                                defaultMenu="1",
                                                skip=skip, 
                                                asList=asList, 
                                                renderStyle=renderStyle, 
                                                parent=selectedMenu,
                                                checkUpdate=True,
                                                subOnly=["1"])
    
    def renderUserDemoMenu(self, selectedMenu:menu=None, skip=[], asList=False, renderStyle=None):
        return self.renderMenuFromDictionary(dict=userDemoMenuDict,
                                                exceptionKeys=["1","2","Z"],
                                                coloredValues=(["1"] if not asList else []),
                                                defaultMenu="1",
                                                skip=skip, 
                                                asList=asList, 
                                                renderStyle=renderStyle, 
                                                parent=selectedMenu,
                                                checkUpdate=True,
                                                subOnly=[])
    
    def renderForMenu(self, selectedMenu:menu=None, skip=[], asList=False, renderStyle=None):
        if selectedMenu is None and self.level == 0:
            # Top level Application Main menu
            return self.renderMenuFromDictionary(dict=level0MenuDict,
                                                 exceptionKeys=["X","T", "E", "U", "Z", "L", "D", "P"],
                                                 coloredValues=(["P","X"] if not asList else []),
                                                 defaultMenu="P",
                                                 skip=skip, 
                                                 asList=asList, 
                                                 renderStyle=renderStyle, 
                                                 parent=selectedMenu,
                                                 checkUpdate=True,
                                                 subOnly=["F", "M", "S", "B", "G", "C", "P", "D"])
        elif selectedMenu is not None:
            if selectedMenu.menuKey == "S" and selectedMenu.level == 0:
                strategies = self.strategyNames
                counter = 1
                menuDict = {}
                for strategyName in strategies:
                    menuDict[f"{counter}"] = strategyName.ljust(20)
                    counter += 1
                for key in level1_S_MenuDict.keys():
                    menuDict[key] = level1_S_MenuDict[key]
                return self.renderMenuFromDictionary(dict=menuDict,
                                                 exceptionKeys=level1_S_MenuDict.keys(),
                                                 skip=skip, 
                                                 asList=asList, 
                                                 renderStyle=renderStyle
                                                    if renderStyle is not None
                                                    else MenuRenderStyle.THREE_PER_ROW, 
                                                 parent=selectedMenu,
                                                 checkUpdate=False)
            if selectedMenu.level == 0:
                self.level = 1
                if selectedMenu.menuKey in ["T"]:
                    defaultKey = 'L' if configManager.period == '1y' else 'S'
                    return self.renderMenuFromDictionary(dict=level1_T_MenuDict,
                                                 exceptionKeys=["M", "B"],
                                                 coloredValues=([defaultKey,"B"]),
                                                 defaultMenu=defaultKey,
                                                 skip=skip, 
                                                 asList=asList, 
                                                 optionText="  [+] Select a configuration period for Screening:",
                                                 renderStyle=renderStyle, 
                                                 parent=selectedMenu,
                                                 checkUpdate=False)
                elif selectedMenu.menuKey in ["P"]:
                    return self.renderMenuFromDictionary(dict=level1_P_MenuDict,
                                                 exceptionKeys=["M", "4"],
                                                 coloredValues=(["1"] if not asList else []),
                                                 defaultMenu="1",
                                                 skip=skip, 
                                                 asList=asList, 
                                                 renderStyle=renderStyle, 
                                                 parent=selectedMenu,
                                                 checkUpdate=False)
                elif selectedMenu.menuKey in ["D"]:
                    return self.renderMenuFromDictionary(dict=LEVEL_1_DATA_DOWNLOADS,
                                                         exceptionKeys=["M",],
                                                         coloredValues=(["D"] if not asList else []),
                                                         defaultMenu="D",
                                                         skip=skip, 
                                                         asList=asList, 
                                                         renderStyle=renderStyle, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False)
                else:
                    # sub-menu of the top level main selected menu
                    return self.renderMenuFromDictionary(dict=level1_X_MenuDict,
                                                         exceptionKeys=["E", "M", "S", "15"],
                                                         coloredValues=(["15",str(configManager.defaultIndex)] if not asList else []),
                                                         defaultMenu=str(configManager.defaultIndex),
                                                         skip=skip, 
                                                         asList=asList, 
                                                         renderStyle=renderStyle
                                                            if renderStyle is not None
                                                            else MenuRenderStyle.THREE_PER_ROW, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False,
                                                         subOnly=["W","E","S","2","3","4","5","6","7","8","9","10","11","12","13","14","15"])
            elif selectedMenu.level == 1:
                self.level = 2
                if selectedMenu.parent.menuKey in ["D"]:
                    return self.renderMenuFromDictionary(dict=INDICES_MAP,
                                                         exceptionKeys=["M","15"],
                                                         coloredValues=(["12","15"] if not asList else []),
                                                         defaultMenu="12",
                                                         skip=skip, 
                                                         asList=asList, 
                                                         renderStyle=renderStyle, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False)
                if selectedMenu.parent.menuKey in ["T"]:
                    if selectedMenu.menuKey in ["L"]:
                        return self.renderMenuFromDictionary(dict=level2_T_MenuDict_L,
                                                         exceptionKeys=["5","4","M"],
                                                         coloredValues=(["1"] if not asList else []),
                                                         defaultMenu="1",
                                                         skip=skip, 
                                                         asList=asList,
                                                         optionText="  [+] Select a config period/candle-duration combination: ",
                                                         renderStyle=renderStyle, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False)
                    elif selectedMenu.menuKey in ["S"]:
                        return self.renderMenuFromDictionary(dict=level2_T_MenuDict_S,
                                                         exceptionKeys=["5","M"],
                                                         coloredValues=(["1"] if not asList else []),
                                                         defaultMenu="1",
                                                         skip=skip, 
                                                         asList=asList,
                                                         optionText="  [+] Select a config period/candle-duration combination: ",
                                                         renderStyle=renderStyle, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False)
                elif selectedMenu.parent.menuKey in ["P"]:
                    return self.renderMenuFromDictionary(dict=level2_P_MenuDict,
                                                         exceptionKeys=["M"],
                                                         coloredValues=(["1"] if not asList else []),
                                                         defaultMenu="1",
                                                         skip=skip, 
                                                         asList=asList,
                                                         optionText="  [+] Options with (₹/$) are paid/premium. Select a scanner:",
                                                         renderStyle=renderStyle
                                                            if renderStyle is not None
                                                            else MenuRenderStyle.TWO_PER_ROW, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False,
                                                         subOnly=PREDEFINED_SCAN_MENU_KEYS)
                elif selectedMenu.menuKey == "S":
                    indexKeys = level1_index_options_sectoral.keys()
                    return self.renderMenuFromDictionary(dict=level1_index_options_sectoral,
                                                         exceptionKeys=[str(len(indexKeys))],
                                                         coloredValues=([str(len(indexKeys))] if not asList else []),
                                                         defaultMenu=str(len(indexKeys)),
                                                         skip=skip, 
                                                         asList=asList,
                                                         optionText="  [+] Options with (₹/$) are paid/premium. Select a sectoral index:",
                                                         renderStyle=renderStyle
                                                            if renderStyle is not None
                                                            else MenuRenderStyle.TWO_PER_ROW, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False)
                else:
                    # next levelsub-menu of the selected sub-menu
                    return self.renderMenuFromDictionary(dict=level2_X_MenuDict,
                                                         exceptionKeys=["0", str(MAX_MENU_OPTION), "M"],
                                                         coloredValues=(["9"] if not asList else []),
                                                         defaultMenu="9",
                                                         skip=skip, 
                                                         asList=asList,
                                                         optionText="  [+] Options with (₹/$) are paid/premium. Select a Criterion for Stock Screening: ",
                                                         renderStyle=renderStyle
                                                            if renderStyle is not None
                                                            else MenuRenderStyle.TWO_PER_ROW, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False,
                                                         subOnly=[] if selectedMenu.menuKey in ["1"] else [x for x in level2_X_MenuDict.keys() if x not in ["M", "Z",str(MAX_MENU_OPTION)]])
            elif selectedMenu.level == 2:
                self.level = 3
                # next levelsub-menu of the selected sub-menu
                if selectedMenu.menuKey == "6":
                    return self.renderMenuFromDictionary(dict=level3_X_Reversal_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=(["3"] if not asList else []),
                                                         defaultMenu="3",
                                                         skip=skip, 
                                                         asList=asList,
                                                         optionText="  [+] Options with (₹/$) are paid/premium. Select an option: ",
                                                         renderStyle=renderStyle
                                                            if renderStyle is not None
                                                            else MenuRenderStyle.STANDALONE, 
                                                         parent=selectedMenu,
                                                         checkUpdate=False)
                elif selectedMenu.menuKey == "7":
                    return self.renderMenuFromDictionary(dict=level3_X_ChartPattern_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["3"],
                                                         defaultMenu="3",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                elif selectedMenu.menuKey == "21":
                    return self.renderMenuFromDictionary(dict=level3_X_PopularStocks_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["1"],
                                                         defaultMenu="1",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                elif selectedMenu.menuKey == "22":
                    return self.renderMenuFromDictionary(dict=level3_X_StockPerformance_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["1"],
                                                         defaultMenu="1",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                elif selectedMenu.menuKey in ["30","32"]:
                    return self.renderMenuFromDictionary(dict=level4_X_Lorenzian_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["1"],
                                                         defaultMenu="1",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                elif selectedMenu.menuKey in ["33"]:
                    return self.renderMenuFromDictionary(dict=level3_X_PotentialProfitable_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["2"],
                                                         defaultMenu="2",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip,
                                                         parent=selectedMenu)
                elif selectedMenu.menuKey in ["40"]:
                    return self.renderMenuFromDictionary(dict=PRICE_CROSS_SMA_EMA_TYPE_MENUDICT,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["2"],
                                                         defaultMenu="2",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                elif selectedMenu.menuKey in ["41"]:
                    return self.renderMenuFromDictionary(dict=PRICE_CROSS_PIVOT_POINT_TYPE_MENUDICT,
                                                         exceptionKeys=["0","1","2","5"],
                                                         coloredValues=["1"],
                                                         defaultMenu="1",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
            elif selectedMenu.level == 3:
                self.level = 4
                # next levelsub-menu of the selected sub-menu
                if selectedMenu.parent.menuKey == "6" and selectedMenu.menuKey in ["7","10"]:
                    return self.renderMenuFromDictionary(dict=level4_X_Lorenzian_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["1"],
                                                         defaultMenu="1",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                if selectedMenu.parent.menuKey == "7" and selectedMenu.menuKey == "3":
                    return self.renderMenuFromDictionary(dict=level4_X_ChartPattern_Confluence_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["4"],
                                                         defaultMenu="4",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                if selectedMenu.parent.menuKey == "7" and selectedMenu.menuKey == "6":
                    return self.renderMenuFromDictionary(dict=level4_X_ChartPattern_BBands_SQZ_MenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["1"],
                                                         defaultMenu="1",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                if selectedMenu.parent.menuKey == "7" and selectedMenu.menuKey == "9":
                    return self.renderMenuFromDictionary(dict=level4_X_ChartPattern_MASignalMenuDict,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["1"],
                                                         defaultMenu="1",
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip, 
                                                         parent=selectedMenu)
                if ((selectedMenu.parent.menuKey == "40" and 
                        selectedMenu.menuKey in PRICE_CROSS_SMA_EMA_TYPE_MENUDICT.keys()) or 
                    (selectedMenu.parent.menuKey == "41" and 
                        selectedMenu.menuKey in PRICE_CROSS_PIVOT_POINT_TYPE_MENUDICT.keys())):
                    return self.renderMenuFromDictionary(dict=PRICE_CROSS_SMA_EMA_DIRECTION_MENUDICT,
                                                         exceptionKeys=["0"],
                                                         coloredValues=["2"],
                                                         defaultMenu="2", 
                                                         parent=selectedMenu,
                                                         asList=asList,
                                                         renderStyle=renderStyle,
                                                         skip=skip)


    def find(self, key=None):
        if key is not None:
            try:
                return self.menuDict[str(key).upper()]
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                default_logger().debug(e, exc_info=True)
                return None
        return None

    def renderMenuFromDictionary(self, dict={},exceptionKeys=[],coloredValues=[], optionText="  [+] Options with (₹/$) are paid/premium. Select a menu option:", defaultMenu="0", asList=False, renderStyle=None, parent=None, skip=None, substitutes=[],checkUpdate=False,subOnly=[]):
        menuText = self.fromDictionary(
            dict,
            renderExceptionKeys=exceptionKeys,
            renderStyle=renderStyle
            if renderStyle is not None
            else MenuRenderStyle.STANDALONE,
            skip=skip,
            parent=parent,
            substitutes = substitutes,
            subOnly=subOnly
        ).render(asList=asList,coloredValues=coloredValues)
        if asList:
            return menuText
        else:
            if OutputControls().enableMultipleLineOutput:
                OutputControls().printOutput(
                    colorText.WARN
                    + optionText
                    + colorText.END
                )
                OutputControls().printOutput(
                    menuText
                    + """

    Enter your choice > (default is """
                    + colorText.WARN
                    + (self.find(defaultMenu) or menu().create('?','?')).keyTextLabel().strip()
                    + ") "
                    "" + colorText.END
                )
                if checkUpdate:
                    try:
                        OTAUpdater.checkForUpdate(VERSION, skipDownload=True)
                    except: # pragma: no cover
                        pass
            return menuText
        
# Fundamentally good compnaies but nearing 52 week low
# https://www.tickertape.in/screener/equity/prebuilt/SCR0005

# Dividend Gems
# https://www.tickertape.in/screener/equity/prebuilt/SCR0027

# Cash rich small caps
# https://www.tickertape.in/screener/equity/prebuilt/SCR0017

# m = menus.allMenus()