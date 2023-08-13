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
"""
 *  Project             :   Screenipy
 *  Author              :   Pranjal Joshi
 *  Created             :   28/04/2021
 *  Description         :   Class for managing the user configuration
"""

import configparser
import glob
import os
import sys

from pkscreener.classes.ColorText import colorText
from pkscreener.classes.log import default_logger

parser = configparser.ConfigParser(strict=False)

# Default attributes for Downloading Cache from Git repo
default_period = "400d"
default_duration = "1d"
default_timeout = 2


# This Class manages read/write of user configuration
class tools:
    def __init__(self):
        self.consolidationPercentage = 10
        self.volumeRatio = 2.5
        self.minLTP = 20.0
        self.maxLTP = 50000
        self.period = "400d"
        self.duration = "1d"
        self.daysToLookback = 30
        self.shuffleEnabled = True
        self.cacheEnabled = True
        self.stageTwo = True
        self.useEMA = False
        self.logsEnabled = False
        self.generalTimeout = 2
        self.longTimeout = 4
        self.logger = None

    @property
    def default_logger(self):
        return self.logger if self.logger is not None else default_logger()

    @default_logger.setter
    def default_logger(self, logger):
        self.logger = logger

    def deleteFileWithPattern(self, pattern="stock_data*.pkl", excludeFile=None):
        for f in glob.glob(pattern):
            try:
                if excludeFile is not None:
                    if not f.endswith(excludeFile):
                        os.remove(f)
                else:
                    os.remove(f)
            except Exception as e:
                self.default_logger.debug(e, exc_info=True)
                pass

    # Handle user input and save config

    def setConfig(self, parser, default=False, showFileCreatedText=True):
        if default:
            try:
                parser.remove_section("config")
            except Exception as e:
                self.default_logger.debug(e, exc_info=True)
                pass
            parser.add_section("config")
            parser.set("config", "period", self.period)
            parser.set("config", "daysToLookback", str(self.daysToLookback))
            parser.set("config", "duration", self.duration)
            parser.set("config", "minPrice", str(self.minLTP))
            parser.set("config", "maxPrice", str(self.maxLTP))
            parser.set("config", "volumeRatio", str(self.volumeRatio))
            parser.set(
                "config", "consolidationPercentage", str(self.consolidationPercentage)
            )
            parser.set("config", "shuffle", "y" if self.shuffleEnabled else "n")
            parser.set("config", "cacheStockData", "y" if self.cacheEnabled else "n")
            parser.set("config", "onlyStageTwoStocks", "y" if self.stageTwo else "n")
            parser.set("config", "useEMA", "y" if self.useEMA else "n")
            parser.set("config", "logsEnabled", "y" if self.logsEnabled else "n")
            parser.set("config", "generalTimeout", str(self.generalTimeout))
            parser.set("config", "longTimeout", str(self.longTimeout))
            try:
                fp = open("pkscreener.ini", "w")
                parser.write(fp)
                fp.close()
                if showFileCreatedText:
                    print(
                        colorText.BOLD
                        + colorText.GREEN
                        + "[+] Default configuration generated as user configuration is not found!"
                        + colorText.END
                    )
                    print(
                        colorText.BOLD
                        + colorText.GREEN
                        + "[+] Use Option > 5 to edit in future."
                        + colorText.END
                    )
                    print(
                        colorText.BOLD
                        + colorText.GREEN
                        + "[+] Close and Restart the program now."
                        + colorText.END
                    )
                    input("")
                    sys.exit(0)
            except IOError as e:
                self.default_logger.debug(e, exc_info=True)
                print(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] Failed to save user config. Exiting.."
                    + colorText.END
                )
                input("")
                sys.exit(1)
        else:
            parser = configparser.ConfigParser(strict=False)
            parser.add_section("config")
            print("")
            print(
                colorText.BOLD
                + colorText.GREEN
                + "[+] PKScreener User Configuration:"
                + colorText.END
            )
            self.period = input(
                "[+] Enter number of days for which stock data to be downloaded (Days)(Optimal = 365): "
            )
            self.daysToLookback = input(
                "[+] Number of recent days (TimeFrame) to screen for Breakout/Consolidation (Days)(Optimal = 20): "
            )
            self.duration = input(
                "[+] Enter Duration of each candle (Days)(Optimal = 1): "
            )
            self.minLTP = input(
                "[+] Minimum Price of Stock to Buy (in RS)(Optimal = 20): "
            )
            self.maxLTP = input(
                "[+] Maximum Price of Stock to Buy (in RS)(Optimal = 50000): "
            )
            self.volumeRatio = input(
                "[+] How many times the volume should be more than average for the breakout? (Number)(Optimal = 2.5): "
            )
            self.consolidationPercentage = input(
                "[+] How many % the price should be in range to consider it as consolidation? (Number)(Optimal = 10): "
            )
            self.shuffle = str(
                input(
                    "[+] Shuffle stocks rather than screening alphabetically? (Y/N): "
                )
            ).lower()
            self.cacheStockData = str(
                input(
                    "[+] Enable High-Performance and Data-Saver mode? (This uses little bit more CPU but performs High Performance Screening) (Y/N): "
                )
            ).lower()
            self.stageTwoPrompt = str(
                input(
                    "[+] Screen only for Stage-2 stocks?\n(What are the stages? => https://www.investopedia.com/articles/trading/08/stock-cycle-trend-price.asp)\n(Y/N): "
                )
            ).lower()
            self.useEmaPrompt = str(
                input(
                    "[+] Use EMA instead of SMA? (EMA is good for Short-term & SMA for Mid/Long-term trades)[Y/N]: "
                )
            ).lower()
            self.logsEnabledPrompt = str(
                input(
                    "[+] Enable Viewing logs? You can ebale if you are having problems.[Y/N]: "
                )
            ).lower()
            self.generalTimeout = input(
                "[+] General network timeout (in seconds)(Optimal = 2 for good networks): "
            )
            self.longTimeout = input(
                "[+] Long network timeout for heavier downloads(in seconds)(Optimal = 4 for good networks): "
            )
            parser.set("config", "period", self.period + "d")
            parser.set("config", "daysToLookback", self.daysToLookback)
            parser.set("config", "duration", self.duration + "d")
            parser.set("config", "minPrice", self.minLTP)
            parser.set("config", "maxPrice", self.maxLTP)
            parser.set("config", "volumeRatio", self.volumeRatio)
            parser.set(
                "config", "consolidationPercentage", self.consolidationPercentage
            )
            parser.set("config", "shuffle", self.shuffle)
            parser.set("config", "cacheStockData", self.cacheStockData)
            parser.set("config", "onlyStageTwoStocks", self.stageTwoPrompt)
            parser.set("config", "useEMA", self.useEmaPrompt)
            parser.set("config", "logsEnabled", self.logsEnabledPrompt)
            parser.set("config", "generalTimeout", self.generalTimeout)
            parser.set("config", "longTimeout", self.longTimeout)
            # delete stock data due to config change
            self.deleteFileWithPattern()
            print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] Cached Stock Data Deleted."
                + colorText.END
            )

            try:
                fp = open("pkscreener.ini", "w")
                parser.write(fp)
                fp.close()
                print(
                    colorText.BOLD
                    + colorText.GREEN
                    + "[+] User configuration saved."
                    + colorText.END
                )
                print(
                    colorText.BOLD
                    + colorText.GREEN
                    + "[+] Restart the Program to start Screening..."
                    + colorText.END
                )
                input("")
                sys.exit(0)
            except IOError as e:
                self.default_logger.debug(e, exc_info=True)
                print(
                    colorText.BOLD
                    + colorText.FAIL
                    + "[+] Failed to save user config. Exiting.."
                    + colorText.END
                )
                input("")
                sys.exit(1)

    # Load user config from file
    def getConfig(self, parser):
        if len(parser.read("pkscreener.ini")):
            try:
                self.duration = parser.get("config", "duration")
                self.period = parser.get("config", "period")
                self.minLTP = float(parser.get("config", "minprice"))
                self.maxLTP = float(parser.get("config", "maxprice"))
                self.volumeRatio = float(parser.get("config", "volumeRatio"))
                self.consolidationPercentage = float(
                    parser.get("config", "consolidationPercentage")
                )
                self.daysToLookback = int(parser.get("config", "daysToLookback"))
                self.shuffleEnabled = (
                    True
                    if "n" not in str(parser.get("config", "shuffle")).lower()
                    else False
                )
                self.cacheEnabled = (
                    True
                    if "n" not in str(parser.get("config", "cachestockdata")).lower()
                    else False
                )
                self.stageTwo = (
                    True
                    if "n"
                    not in str(parser.get("config", "onlyStageTwoStocks")).lower()
                    else False
                )
                self.useEMA = (
                    False
                    if "y" not in str(parser.get("config", "useEMA")).lower()
                    else True
                )
                self.logsEnabled = (
                    False
                    if "y" not in str(parser.get("config", "logsEnabled")).lower()
                    else True
                )
                self.generalTimeout = float(parser.get("config", "generalTimeout"))
                self.longTimeout = float(parser.get("config", "longTimeout"))
            except configparser.NoOptionError as e:
                self.default_logger.debug(e, exc_info=True)
                # input(colorText.BOLD + colorText.FAIL +
                #       '[+] pkscreener requires user configuration again. Press enter to continue..' + colorText.END)
                parser.remove_section("config")
                self.setConfig(parser, default=True, showFileCreatedText=False)
            except Exception as e:
                self.default_logger.debug(e, exc_info=True)
                # input(colorText.BOLD + colorText.FAIL +
                #       '[+] pkscreener requires user configuration again. Press enter to continue..' + colorText.END)
                parser.remove_section("config")
                self.setConfig(parser, default=True, showFileCreatedText=False)
        else:
            self.setConfig(parser, default=True, showFileCreatedText=False)

    # Toggle the duration and period for use in intraday and swing trading
    def toggleConfig(self):
        self.getConfig(parser)
        if not self.isIntradayConfig():
            self.period = "1d"
            self.duration = "1m"
            self.cacheEnabled = False
        else:
            self.period = "400d"
            self.duration = "1d"
            self.cacheEnabled = True
        self.setConfig(parser, default=True, showFileCreatedText=False)

    def isIntradayConfig(self):
        return (
            self.period == "1d" and self.duration[-1] == "m" and not self.cacheEnabled
        )

    # Print config file
    def showConfigFile(self, defaultAnswer=None):
        try:
            prompt = "[+] PKScreener User Configuration:"
            f = open("pkscreener.ini", "r")
            print(colorText.BOLD + colorText.GREEN + prompt + colorText.END)
            configData = f.read()
            f.close()
            print("\n" + configData)
            if defaultAnswer != "Y":
                input("Press any key to continue...")
            return f"{prompt}\n{configData}"
        except Exception as e:
            self.default_logger.debug(e, exc_info=True)
            print(
                colorText.BOLD
                + colorText.FAIL
                + "[+] User Configuration not found!"
                + colorText.END
            )
            print(
                colorText.BOLD
                + colorText.WARN
                + "[+] Configure the limits to continue."
                + colorText.END
            )
            self.setConfig(parser, default=True, showFileCreatedText=False)

    # Check if config file exists
    def checkConfigFile(self):
        try:
            f = open("pkscreener.ini", "r")
            f.close()
            self.getConfig(parser)
            return True
        except FileNotFoundError as e:
            self.default_logger.debug(e, exc_info=True)
            self.setConfig(parser, default=True, showFileCreatedText=False)
