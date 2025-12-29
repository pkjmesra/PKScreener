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

import os
import random
import warnings
warnings.simplefilter("ignore", UserWarning, append=True)
os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import logging
import multiprocessing
import sys
import time
import urllib
import warnings
from datetime import datetime, UTC, timedelta
from time import sleep

import numpy as np

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
from alive_progress import alive_bar
from PKDevTools.classes.Committer import Committer
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes import Archiver
from PKDevTools.classes.Telegram import (
    is_token_telegram_configured,
    send_document,
    send_message,
    send_photo,
    send_media_group
)
from PKNSETools.morningstartools.PKMorningstarDataFetcher import morningstarDataFetcher
from PKNSETools.Nasdaq.PKNasdaqIndex import PKNasdaqIndexFetcher
from tabulate import tabulate
from halo import Halo

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Fetcher as Fetcher
import pkscreener.classes.ScreeningStatistics as ScreeningStatistics
from pkscreener.classes import Utility, ConsoleUtility, ConsoleMenuUtility, ImageUtility
from pkscreener.classes.Utility import STD_ENCODING
from pkscreener.classes import VERSION, PortfolioXRay
from pkscreener.classes.Backtest import backtest, backtestSummary
from pkscreener.classes.PKSpreadsheets import PKSpreadsheets
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.Environment import PKEnvironment
from pkscreener.classes.CandlePatterns import CandlePatterns
from pkscreener.classes import AssetsManager
from PKDevTools.classes.FunctionTimeouts import exit_after
from pkscreener.classes.MenuOptions import (
    level0MenuDict,
    level1_X_MenuDict,
    level1_P_MenuDict,
    level2_X_MenuDict,
    level2_P_MenuDict,
    level3_X_ChartPattern_MenuDict,
    level3_X_PopularStocks_MenuDict,
    level3_X_PotentialProfitable_MenuDict,
    PRICE_CROSS_SMA_EMA_DIRECTION_MENUDICT,
    PRICE_CROSS_SMA_EMA_TYPE_MENUDICT,
    PRICE_CROSS_PIVOT_POINT_TYPE_MENUDICT,
    level3_X_Reversal_MenuDict,
    level4_X_Lorenzian_MenuDict,
    level4_X_ChartPattern_Confluence_MenuDict,
    level4_X_ChartPattern_BBands_SQZ_MenuDict,
    level4_X_ChartPattern_MASignalMenuDict,
    level1_index_options_sectoral,
    menus,
    MAX_SUPPORTED_MENU_OPTION,
    MAX_MENU_OPTION,
    PIPED_SCANNERS,
    PREDEFINED_SCAN_MENU_KEYS,
    PREDEFINED_SCAN_MENU_TEXTS,
    INDICES_MAP,
    CANDLESTICK_DICT
)
from pkscreener.classes.OtaUpdater import OTAUpdater
from pkscreener.classes.Portfolio import PortfolioCollection
from pkscreener.classes.PKTask import PKTask
from pkscreener.classes.PKScheduler import PKScheduler
from pkscreener.classes.PKScanRunner import PKScanRunner
from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser
from pkscreener.classes.PKPremiumHandler import PKPremiumHandler
from pkscreener.classes.AssetsManager import PKAssetsManager
from pkscreener.classes.PKAnalytics import PKAnalyticsService

if __name__ == '__main__':
    multiprocessing.freeze_support()

# Constants
np.seterr(divide="ignore", invalid="ignore")
TEST_STKCODE = "SBIN"


class MenuManager:
    """
    Manages all menu navigation, selection, and hierarchy for the PKScreener application.
    Handles user input, menu rendering, and option validation across all menu levels.
    """

    def __init__(self, config_manager, user_passed_args):
        """
        Initialize the MenuManager with configuration and user arguments.
        
        Args:
            config_manager: Configuration manager instance
            user_passed_args: User passed arguments
        """
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args
        self.m0 = menus()
        self.m1 = menus()
        self.m2 = menus()
        self.m3 = menus()
        self.m4 = menus()
        self.selected_choice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        self.menu_choice_hierarchy = ""
        self.n_value_for_menu = 0

    def ensure_menus_loaded(self, menu_option=None, index_option=None, execute_option=None):
        """
        Ensure all menus are loaded and rendered for the given options.
        
        Args:
            menu_option: Selected menu option
            index_option: Selected index option
            execute_option: Selected execute option
        """
        try:
            if len(self.m0.menuDict.keys()) == 0:
                self.m0.renderForMenu(asList=True)
                
            if len(self.m1.menuDict.keys()) == 0:
                self.m1.renderForMenu(selected_menu=self.m0.find(menu_option), asList=True)
                
            if len(self.m2.menuDict.keys()) == 0:
                self.m2.renderForMenu(selected_menu=self.m1.find(index_option), asList=True)
                
            if len(self.m3.menuDict.keys()) == 0:
                self.m3.renderForMenu(selected_menu=self.m2.find(execute_option), asList=True)
        except:
            pass

    def init_execution(self, menu_option=None):
        """
        Initialize execution by showing main menu and getting user selection.
        
        Args:
            menu_option: Pre-selected menu option
            
        Returns:
            object: Selected menu object
        """
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        
        if self.user_passed_args is not None and self.user_passed_args.pipedmenus is not None:
            OutputControls().printOutput(
                colorText.FAIL
                + "  [+] You chose: "
                + f" (Piped Scan Mode) [{self.user_passed_args.pipedmenus}]"
                + colorText.END
            )
            
        self.m0.renderForMenu(selected_menu=None, asList=(self.user_passed_args is not None and self.user_passed_args.options is not None))
        
        try:
            needs_calc = self.user_passed_args is not None and self.user_passed_args.backtestdaysago is not None
            past_date = f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(self.user_passed_args.backtestdaysago) if needs_calc else 0)}{colorText.END} ]\n" if needs_calc else ""
            
            if menu_option is None:
                if "PKDevTools_Default_Log_Level" in os.environ.keys():
                    from PKDevTools.classes import Archiver
                    log_file_path = os.path.join(Archiver.get_user_data_dir(), "pkscreener-logs.txt")
                    OutputControls().printOutput(colorText.FAIL + "\n      [+] Logs will be written to:" + colorText.END)
                    OutputControls().printOutput(colorText.GREEN + f"      [+] {log_file_path}" + colorText.END)
                    OutputControls().printOutput(colorText.FAIL + "      [+] If you need to share,run through the menus that are causing problems. At the end, open this folder, zip the log file to share at https://github.com/pkjmesra/PKScreener/issues .\n" + colorText.END)
                    
                # In non-interactive mode (bot/systemlaunched), default to X (Scanners) not P (Piped Scanners)
                # to avoid infinite loops where P triggers another P selection
                default_menu_option = "X" if (self.user_passed_args is not None and (self.user_passed_args.systemlaunched or self.user_passed_args.answerdefault is not None or self.user_passed_args.telegram)) else "P"
                menu_option = OutputControls().takeUserInput(colorText.FAIL + f"{past_date}  [+] Select option: ", defaultInput=default_menu_option)
                OutputControls().printOutput(colorText.END, end="")
                
            if menu_option == "" or menu_option is None:
                menu_option = "X"
                
            menu_option = menu_option.upper()
            selected_menu = self.m0.find(menu_option)
            
            if selected_menu is not None:
                if selected_menu.menuKey == "Z":
                    OutputControls().takeUserInput(
                        colorText.FAIL
                        + "  [+] Press <Enter> to Exit!"
                        + colorText.END
                    )
                    PKAnalyticsService().send_event("app_exit")
                    sys.exit(0)
                elif selected_menu.menuKey in ["B", "C", "G", "H", "U", "T", "S", "E", "X", "Y", "M", "D", "I", "L", "F"]:
                    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                    self.selected_choice["0"] = selected_menu.menuKey
                    return selected_menu
                elif selected_menu.menuKey in ["P"]:
                    return selected_menu
                    
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            self.show_option_error_message()
            return self.init_execution()

        self.show_option_error_message()
        return self.init_execution()

    def init_post_level0_execution(self, menu_option=None, index_option=None, execute_option=None, skip=[], retrial=False):
        """
        Initialize execution after level 0 menu selection.
        
        Args:
            menu_option: Selected menu option
            index_option: Selected index option
            execute_option: Selected execute option
            skip: List of options to skip
            retrial (bool): Whether this is a retry
            
        Returns:
            tuple: Index option and execute option
        """
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        
        if menu_option is None:
            OutputControls().printOutput('You must choose an option from the previous menu! Defaulting to "X"...')
            menu_option = "X"
            
        OutputControls().printOutput(
            colorText.FAIL
            + "  [+] You chose: "
            + level0MenuDict[menu_option].strip()
            + (f" (Piped Scan Mode) [{self.user_passed_args.pipedmenus}]" if (self.user_passed_args is not None and self.user_passed_args.pipedmenus is not None) else "")
            + colorText.END
        )
        
        if index_option is None:
            selected_menu = self.m0.find(menu_option)
            self.m1.renderForMenu(selected_menu=selected_menu, skip=skip, asList=(self.user_passed_args is not None and self.user_passed_args.options is not None))
            
        try:
            needs_calc = self.user_passed_args is not None and self.user_passed_args.backtestdaysago is not None
            past_date = f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(self.user_passed_args.backtestdaysago) if needs_calc else 0)}{colorText.END} ]\n" if needs_calc else ""
            
            if index_option is None:
                index_option = OutputControls().takeUserInput(
                    colorText.FAIL + f"{past_date}  [+] Select option: "
                )
                OutputControls().printOutput(colorText.END, end="")
                
            if (str(index_option).isnumeric() and int(index_option) > 1 and str(execute_option).isnumeric() and int(str(execute_option)) <= MAX_SUPPORTED_MENU_OPTION) or \
                    str(index_option).upper() in ["S", "E", "W"]:
                self.ensure_menus_loaded(menu_option, index_option, execute_option)
                
                if not PKPremiumHandler.hasPremium(self.m1.find(str(index_option).upper())):
                    PKAnalyticsService().send_event(f"non_premium_user_{menu_option}_{index_option}_{execute_option}")
                    return None, None
                    
            if index_option == "" or index_option is None:
                index_option = int(self.config_manager.defaultIndex)
            elif not str(index_option).isnumeric():
                index_option = index_option.upper()
                
                if index_option in ["M", "E", "N", "Z"]:
                    return index_option, 0
            else:
                index_option = int(index_option)
                
                if index_option < 0 or index_option > 15:
                    raise ValueError
                elif index_option == 13:
                    self.config_manager.period = "2y"
                    self.config_manager.getConfig(ConfigManager.parser)
                    self.newlyListedOnly = True
                    index_option = 12
                    
            if index_option == 15:
                from pkscreener.classes.MarketStatus import MarketStatus
                MarketStatus().exchange = "^IXIC"
                
            self.selected_choice["1"] = str(index_option)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] Please enter a valid numeric option & Try Again!"
                + colorText.END
            )
            
            if not retrial:
                sleep(2)
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                return self.init_post_level0_execution(retrial=True)
                
        return index_option, execute_option

    def init_post_level1_execution(self, index_option, execute_option=None, skip=[], retrial=False):
        """
        Initialize execution after level 1 menu selection.
        
        Args:
            index_option: Selected index option
            execute_option: Selected execute option
            skip: List of options to skip
            retrial (bool): Whether this is a retry
            
        Returns:
            tuple: Index option and execute option
        """
        list_stock_codes = [] if self.list_stock_codes is None or len(self.list_stock_codes) == 0 else self.list_stock_codes
        
        if execute_option is None:
            if index_option is not None and index_option != "W":
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                OutputControls().printOutput(
                    colorText.FAIL
                    + "  [+] You chose: "
                    + level0MenuDict[self.selected_choice["0"]].strip()
                    + " > "
                    + level1_X_MenuDict[self.selected_choice["1"]].strip()
                    + (f" (Piped Scan Mode) [{self.user_passed_args.pipedmenus}]" if (self.user_passed_args is not None and self.user_passed_args.pipedmenus is not None) else "")
                    + colorText.END
                )
                
                selected_menu = self.m1.find(index_option)
                self.m2.renderForMenu(selected_menu=selected_menu, skip=skip, asList=(self.user_passed_args is not None and self.user_passed_args.options is not None))
                stock_index_code = str(len(level1_index_options_sectoral.keys()))
                
                if index_option == "S":
                    self.ensure_menus_loaded("X", index_option, execute_option)
                    
                    if not PKPremiumHandler.hasPremium(selected_menu):
                        PKAnalyticsService().send_event(f"non_premium_user_X_{index_option}_{execute_option}")
                        PKAnalyticsService().send_event("app_exit")
                        sys.exit(0)
                        
                    index_keys = level1_index_options_sectoral.keys()
                    stock_index_code = OutputControls().takeUserInput(
                        colorText.FAIL + "  [+] Select option: "
                    ) or str(len(index_keys))
                    OutputControls().printOutput(colorText.END, end="")
                    
                    if stock_index_code == str(len(index_keys)):
                        for index_code in index_keys:
                            if index_code != str(len(index_keys)):
                                self.list_stock_codes.append(level1_index_options_sectoral[str(index_code)].split("(")[1].split(")")[0])
                    else:
                        self.list_stock_codes = [level1_index_options_sectoral[str(stock_index_code)].split("(")[1].split(")")[0]]
                        
                    selected_menu.menuKey = "0"  # Reset because user must have selected specific index menu with single stock
                    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                    self.m2.renderForMenu(selected_menu=selected_menu, skip=skip, asList=(self.user_passed_args is not None and self.user_passed_args.options is not None))
                    
        try:
            needs_calc = self.user_passed_args is not None and self.user_passed_args.backtestdaysago is not None
            past_date = f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(self.user_passed_args.backtestdaysago) if needs_calc else 0)}{colorText.END} ]\n" if needs_calc else ""
            
            if index_option is not None and index_option != "W":
                if execute_option is None:
                    execute_option = OutputControls().takeUserInput(
                        colorText.FAIL + f"{past_date}  [+] Select option: "
                    ) or "9"
                    OutputControls().printOutput(colorText.END, end="")
                    
                self.ensure_menus_loaded("X", index_option, execute_option)
                
                if not PKPremiumHandler.hasPremium(self.m2.find(str(execute_option))):
                    PKAnalyticsService().send_event(f"non_premium_user_X_{index_option}_{execute_option}")
                    return None, None
                    
                if execute_option == "":
                    execute_option = 1
                    
                if not str(execute_option).isnumeric():
                    execute_option = execute_option.upper()
                else:
                    execute_option = int(execute_option)
                    
                    if execute_option < 0 or execute_option > MAX_MENU_OPTION:
                        raise ValueError
            else:
                execute_option = 0
                
            self.selected_choice["2"] = str(execute_option)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] Please enter a valid numeric option & Try Again!"
                + colorText.END
            )
            
            if not retrial:
                sleep(2)
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                return self.init_post_level1_execution(index_option, execute_option, retrial=True)
                
        return index_option, execute_option

    def update_menu_choice_hierarchy(self):
        """
        Update the menu choice hierarchy string based on current selections.
        """
        try:
            self.menu_choice_hierarchy = f'{level0MenuDict[self.selected_choice["0"]].strip()}'
            top_level_menu_dict = level1_X_MenuDict if self.selected_choice["0"] not in "P" else level1_P_MenuDict
            level2_menu_dict = level2_X_MenuDict if self.selected_choice["0"] not in "P" else level2_P_MenuDict
            
            if len(self.selected_choice["1"]) > 0:
                self.menu_choice_hierarchy = f'{self.menu_choice_hierarchy}>{top_level_menu_dict[self.selected_choice["1"]].strip()}'
                
            if len(self.selected_choice["2"]) > 0:
                self.menu_choice_hierarchy = f'{self.menu_choice_hierarchy}>{level2_menu_dict[self.selected_choice["2"]].strip()}'
                
            if self.selected_choice["0"] not in "P":
                if self.selected_choice["2"] == "6":
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{level3_X_Reversal_MenuDict[self.selected_choice["3"]].strip()}'
                    )
                    
                    if len(self.selected_choice) >= 5 and self.selected_choice["3"] in ["7", "10"]:
                        self.menu_choice_hierarchy = (
                            self.menu_choice_hierarchy
                            + f'>{level4_X_Lorenzian_MenuDict[self.selected_choice["4"]].strip()}'
                        )
                        
                elif self.selected_choice["2"] in ["30"]:
                    if len(self.selected_choice) >= 3:
                        self.menu_choice_hierarchy = (
                            self.menu_choice_hierarchy
                            + f'>{level4_X_Lorenzian_MenuDict[self.selected_choice["3"]].strip()}'
                        )
                        
                elif self.selected_choice["2"] == "7":
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{level3_X_ChartPattern_MenuDict[self.selected_choice["3"]].strip()}'
                    )
                    
                    if len(self.selected_choice) >= 5 and self.selected_choice["3"] == "3":
                        self.menu_choice_hierarchy = (
                            self.menu_choice_hierarchy
                            + f'>{level4_X_ChartPattern_Confluence_MenuDict[self.selected_choice["4"]].strip()}'
                        )
                    elif len(self.selected_choice) >= 5 and self.selected_choice["3"] == "6":
                        self.menu_choice_hierarchy = (
                            self.menu_choice_hierarchy
                            + f'>{level4_X_ChartPattern_BBands_SQZ_MenuDict[self.selected_choice["4"]].strip()}'
                        )
                    elif len(self.selected_choice) >= 5 and self.selected_choice["3"] == "9":
                        self.menu_choice_hierarchy = (
                            self.menu_choice_hierarchy
                            + f'>{level4_X_ChartPattern_MASignalMenuDict[self.selected_choice["4"]].strip()}'
                        )
                    elif len(self.selected_choice) >= 5 and self.selected_choice["3"] == "7":
                        self.menu_choice_hierarchy = (
                            self.menu_choice_hierarchy
                            + f'>{CANDLESTICK_DICT[self.selected_choice["4"]].strip() if self.selected_choice["4"] != 0 else "No Filter"}'
                        )
                        
                elif self.selected_choice["2"] == "21":
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{level3_X_PopularStocks_MenuDict[self.selected_choice["3"]].strip()}'
                    )
                    
                elif self.selected_choice["2"] == "33":
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{level3_X_PotentialProfitable_MenuDict[self.selected_choice["3"]].strip()}'
                    )
                    
                elif self.selected_choice["2"] == "40":
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{PRICE_CROSS_SMA_EMA_DIRECTION_MENUDICT[self.selected_choice["3"]].strip()}'
                    )
                    
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{PRICE_CROSS_SMA_EMA_TYPE_MENUDICT[self.selected_choice["4"]].strip()}'
                    )
                    
                elif self.selected_choice["2"] == "41":
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{PRICE_CROSS_PIVOT_POINT_TYPE_MENUDICT[self.selected_choice["3"]].strip()}'
                    )
                    
                    self.menu_choice_hierarchy = (
                        self.menu_choice_hierarchy
                        + f'>{PRICE_CROSS_SMA_EMA_DIRECTION_MENUDICT[self.selected_choice["4"]].strip()}'
                    )
            
            intraday = "(Intraday)" if ("Intraday" not in self.menu_choice_hierarchy and (self.user_passed_args is not None and self.user_passed_args.intraday) or self.config_manager.isIntradayConfig()) else ""
            self.menu_choice_hierarchy = f"{self.menu_choice_hierarchy}{intraday}"
            
            self.menu_choice_hierarchy = self.menu_choice_hierarchy.replace("N-", f"{self.n_value_for_menu}-")
        except:
            pass
            
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        needs_calc = self.user_passed_args is not None and self.user_passed_args.backtestdaysago is not None
        past_date = f"[ {PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(self.user_passed_args.backtestdaysago) if needs_calc else 0)} ]" if needs_calc else ""
        
        report_title = f"{self.user_passed_args.pipedtitle}|" if self.user_passed_args is not None and self.user_passed_args.pipedtitle is not None else ""
        run_option_name = PKScanRunner.getFormattedChoices(self.user_passed_args, self.selected_choice)
        
        if ((":0:" in run_option_name or "_0_" in run_option_name) and self.user_passed_args.progressstatus is not None) or self.user_passed_args.progressstatus is not None:
            run_option_name = self.user_passed_args.progressstatus.split("=>")[0].split("  [+] ")[1].strip()
            
        report_title = f"{run_option_name} | {report_title}" if run_option_name is not None else report_title
        
        if len(run_option_name) >= 5:
            PKAnalyticsService().send_event(run_option_name)
            
        OutputControls().printOutput(
            colorText.FAIL
            + f"  [+] You chose: {report_title} "
            + self.menu_choice_hierarchy
            + (f" (Piped Scan Mode) [{self.user_passed_args.pipedmenus}] {past_date}" if (self.user_passed_args is not None and self.user_passed_args.pipedmenus is not None) else "")
            + colorText.END
        )
        
        default_logger().info(self.menu_choice_hierarchy)
        return self.menu_choice_hierarchy

    def show_option_error_message(self):
        """Display an error message for invalid menu options - only in interactive mode."""
        # Only show error message and wait if in interactive mode
        if not OutputControls().enableUserInput:
            return  # Skip error message in non-interactive/bot mode
        
        OutputControls().printOutput(
            colorText.FAIL
            + "\n  [+] Please enter a valid option & try Again!"
            + colorText.END
        )
        sleep(2)
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)

    def handle_secondary_menu_choices(self, menu_option, testing=False, default_answer=None, user=None):
        """
        Handle secondary menu choices (help, update, config, etc.).
        
        Args:
            menu_option: Selected menu option
            testing (bool): Whether running in test mode
            default_answer: Default answer for prompts
            user: User identifier
        """
        if menu_option == "H":
            self.show_send_help_info(default_answer, user)
        elif menu_option == "U":
            OTAUpdater.checkForUpdate(VERSION, skipDownload=testing)
            if default_answer is None:
                OutputControls().takeUserInput("Press <Enter> to continue...")
        elif menu_option == "T":
            if self.user_passed_args is None or self.user_passed_args.options is None:
                selected_menu = self.m0.find(menu_option)
                self.m1.renderForMenu(selected_menu=selected_menu)
                period_option = OutputControls().takeUserInput(
                    colorText.FAIL + "  [+] Select option: "
                ) or ('L' if self.config_manager.period == '1y' else 'S')
                OutputControls().printOutput(colorText.END, end="")
                
                if period_option is None or period_option.upper() not in ["L", "S", "B"]:
                    return
                    
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                
                if period_option.upper() in ["L", "S"]:
                    selected_menu = self.m1.find(period_option)
                    self.m2.renderForMenu(selected_menu=selected_menu)
                    duration_option = OutputControls().takeUserInput(
                        colorText.FAIL + "  [+] Select option: "
                    ) or "1"
                    OutputControls().printOutput(colorText.END, end="")
                    
                    if duration_option is None or duration_option.upper() not in ["1", "2", "3", "4", "5"]:
                        return
                        
                    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                    
                    if duration_option.upper() in ["1", "2", "3", "4"]:
                        selected_menu = self.m2.find(duration_option)
                        period_durations = selected_menu.menuText.split("(")[1].split(")")[0].split(", ")
                        self.config_manager.period = period_durations[0]
                        self.config_manager.duration = period_durations[1]
                        self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
                        self.config_manager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(), pattern="*stock_data_*.pkl*")
                    elif duration_option.upper() in ["5"]:
                        self.config_manager.setConfig(ConfigManager.parser, default=False, showFileCreatedText=True)
                        self.config_manager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(), pattern="*stock_data_*.pkl*")
                    return
                elif period_option.upper() in ["B"]:
                    last_trading_date = PKDateUtilities.nthPastTradingDateStringFromFutureDate(n=(22 if self.config_manager.period == '1y' else 15))
                    backtest_days_ago = OutputControls().takeUserInput(
                        f"{colorText.FAIL}  [+] Enter no. of days/candles in the past as starting candle for which you'd like to run the scans\n  [+] You can also enter a past date in {colorText.END}{colorText.GREEN}YYYY-MM-DD{colorText.END}{colorText.FAIL} format\n  [+] (e.g. {colorText.GREEN}10{colorText.END} for 10 candles ago or {colorText.GREEN}0{colorText.END} for today or {colorText.GREEN}{last_trading_date}{colorText.END}):"
                    ) or ('22' if self.config_manager.period == '1y' else '15')
                    OutputControls().printOutput(colorText.END, end="")
                    
                    if len(str(backtest_days_ago)) >= 3 and "-" in str(backtest_days_ago):
                        try:
                            backtest_days_ago = abs(PKDateUtilities.trading_days_between(
                                d1=PKDateUtilities.dateFromYmdString(str(backtest_days_ago)),
                                d2=PKDateUtilities.currentDateTime()))
                        except Exception as e:
                            default_logger().debug(e, exc_info=True)
                            OutputControls().printOutput(f"An error occured! Going ahead with default inputs.")
                            backtest_days_ago = ('22' if self.config_manager.period == '1y' else '15')
                            sleep(3)
                            pass
                            
                    launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
                    requesting_user = f" -u {self.user_passed_args.user}" if self.user_passed_args.user is not None else ""
                    enable_log = f" -l" if self.user_passed_args.log else ""
                    enable_telegram_mode = f" --telegram" if self.user_passed_args is not None and self.user_passed_args.telegram else ""
                    stock_list_param = f" --stocklist {self.user_passed_args.stocklist}" if self.user_passed_args.stocklist else ""
                    slicewindow_param = f" --slicewindow {self.user_passed_args.slicewindow}" if self.user_passed_args.slicewindow else ""
                    fname_param = f" --fname {self.results_contents_encoded}" if self.results_contents_encoded else ""
                    launcher = f"python3.12 {launcher}" if (launcher.endswith(".py\"") or launcher.endswith(".py")) else launcher
                    
                    OutputControls().printOutput(f"{colorText.GREEN}Launching PKScreener in quick backtest mode. If it does not launch, please try with the following:{colorText.END}\n{colorText.FAIL}{launcher} --backtestdaysago {int(backtest_days_ago)}{requesting_user}{enable_log}{enable_telegram_mode}{stock_list_param}{slicewindow_param}{fname_param}{colorText.END}\n{colorText.WARN}Press Ctrl + C to exit quick backtest mode.{colorText.END}")
                    sleep(2)
                    os.system(f"{launcher} --systemlaunched -a Y -e --backtestdaysago {int(backtest_days_ago)}{requesting_user}{enable_log}{enable_telegram_mode}{stock_list_param}{slicewindow_param}{fname_param}")
                    ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
                    return None, None
            elif self.user_passed_args is not None and self.user_passed_args.options is not None:
                options = self.user_passed_args.options.split(":")
                selected_menu = self.m0.find(options[0])
                self.m1.renderForMenu(selected_menu=selected_menu, asList=True)
                selected_menu = self.m1.find(options[1])
                self.m2.renderForMenu(selected_menu=selected_menu, asList=True)
                
                if options[2] in ["1", "2", "3", "4"]:
                    selected_menu = self.m2.find(options[2])
                    period_durations = selected_menu.menuText.split("(")[1].split(")")[0].split(", ")
                    self.config_manager.period = period_durations[0]
                    self.config_manager.duration = period_durations[1]
                    self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
                else:
                    self.toggle_user_config()
            else:
                self.toggle_user_config()
        elif menu_option == "E":
            self.config_manager.setConfig(ConfigManager.parser)
        elif menu_option == "Y":
            self.show_send_config_info(default_answer, user)
            
        return

    def show_send_config_info(self, default_answer=None, user=None):
        """
        Show and send configuration information.
        
        Args:
            default_answer: Default answer for prompts
            user: User identifier
        """
        config_data = self.config_manager.showConfigFile(default_answer=('Y' if user is not None else default_answer))
        
        if user is not None:
            self.send_message_to_telegram_channel(message=ImageUtility.PKImageTools.removeAllColorStyles(config_data), user=user)
            
        if default_answer is None:
            input("Press any key to continue...")

    def show_send_help_info(self, default_answer=None, user=None):
        """
        Show and send help information.
        
        Args:
            default_answer: Default answer for prompts
            user: User identifier
        """
        help_data = ConsoleUtility.PKConsoleTools.showDevInfo(default_answer=('Y' if user is not None else default_answer))
        
        if user is not None:
            self.send_message_to_telegram_channel(message=ImageUtility.PKImageTools.removeAllColorStyles(help_data), user=user)
            
        if default_answer is None:
            input("Press any key to continue...")

    def toggle_user_config(self):
        """Toggle user configuration between intraday and daily modes."""
        self.config_manager.toggleConfig(
            candleDuration="1d" if self.config_manager.isIntradayConfig() else "1m"
        )
        OutputControls().printOutput(
            colorText.GREEN
            + "\nConfiguration toggled to duration: "
            + str(self.config_manager.duration)
            + " and period: "
            + str(self.config_manager.period)
            + colorText.END
        )
        input("\nPress <Enter> to Continue...\n")


class ScanExecutor:
    """
    Executes scanning operations including stock screening, backtesting, and data processing.
    Manages worker processes, task queues, and result collection.
    """

    def __init__(self, config_manager, user_passed_args):
        """
        Initialize the ScanExecutor with configuration and user arguments.
        
        Args:
            config_manager: Configuration manager instance
            user_passed_args: User passed arguments
        """
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args
        self.fetcher = Fetcher.screenerStockDataFetcher(self.config_manager)
        self.screener = ScreeningStatistics.ScreeningStatistics(self.config_manager, default_logger())
        self.tasks_queue = None
        self.results_queue = None
        self.consumers = None
        self.logging_queue = None
        self.mp_manager = None
        self.keyboard_interrupt_event = None
        self.keyboard_interrupt_event_fired = False
        self.screen_counter = None
        self.screen_results_counter = None
        self.elapsed_time = 0
        self.start_time = 0
        self.scan_cycle_running = False
        self.screen_results = None
        self.save_results = None
        self.backtest_df = None
        self.selected_choice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        self.criteria_date_time = None

    def run_scanners(self, menu_option, items, tasks_queue, results_queue, num_stocks,
                    backtest_period, iterations, consumers, screen_results, save_results,
                    backtest_df, testing=False):
        """
        Execute scanning operations with the given parameters.
        
        Args:
            menu_option: Selected menu option
            items: List of items to scan
            tasks_queue: Tasks queue for multiprocessing
            results_queue: Results queue for multiprocessing
            num_stocks: Number of stocks to process
            backtest_period: Backtest period in days
            iterations: Number of iterations
            consumers: Consumer processes
            screen_results: Screen results container
            save_results: Save results container
            backtest_df: Backtest dataframe
            testing (bool): Whether running in test mode
            
        Returns:
            tuple: Screen results, save results, and backtest dataframe
        """
        result = None
        backtest_df = None
        review_date = self.get_review_date() if self.criteria_date_time is None else self.criteria_date_time
        max_allowed = self.get_max_allowed_results_count(iterations, testing)
        
        try:
            original_number_of_stocks = num_stocks
            iterations, num_stocks_per_iteration = self.get_iterations_and_stock_counts(num_stocks, iterations)
            
            OutputControls().printOutput(
                colorText.GREEN
                + f"  [+] For {review_date}, total {'Scanners' if menu_option in ['F'] else 'Stocks'} under review: {num_stocks} over {iterations} iterations..."
                + colorText.END
            )
            
            if not self.user_passed_args.download:
                OutputControls().printOutput(colorText.WARN
                    + f"  [+] Starting {'Stock' if menu_option not in ['C'] else 'Intraday'} {'Screening' if menu_option=='X' else ('Analysis' if menu_option == 'C' else 'Look-up' if menu_option in ['F'] else 'Backtesting.')}. Press Ctrl+C to stop!"
                    + colorText.END
                )
                
                if self.user_passed_args.progressstatus is not None:
                    OutputControls().printOutput(f"{colorText.GREEN}{self.user_passed_args.progressstatus}{colorText.END}")
            else:
                OutputControls().printOutput(
                    colorText.FAIL
                    + f"  [+] Download ONLY mode (OHLCV for period:{self.config_manager.period}, candle-duration:{self.config_manager.duration} )! Stocks will not be screened!"
                    + colorText.END
                )
                
            bar, spinner = Utility.tools.getProgressbarStyle()
            
            with alive_bar(num_stocks, bar=bar, spinner=spinner) as progressbar:
                lstscreen = []
                lstsave = []
                result = None
                backtest_df = None
                self.start_time = time.time() if not self.scan_cycle_running else self.start_time
                self.scan_cycle_running = True
                
                def process_results_callback(result_item, processed_count, result_df, *other_args):
                    (menu_option, backtest_period, result, lstscreen, lstsave) = other_args
                    num_stocks = processed_count
                    result = result_item
                    backtest_df = self.process_results(menu_option, backtest_period, result, lstscreen, lstsave, result_df)
                    progressbar()
                    progressbar.text(
                        colorText.GREEN
                        + f"{'Remaining' if self.user_passed_args.download else ('Found' if menu_option in ['X','F'] else 'Analysed')} {len(lstscreen) if not self.user_passed_args.download else processed_count} {'Stocks' if menu_option in ['X'] else 'Records'}"
                        + colorText.END
                    )
                    
                    if result is not None:
                        if not self.user_passed_args.monitor and len(lstscreen) > 0 and self.user_passed_args is not None and self.user_passed_args.options.split(":")[2] in ["29"]:
                            scr_df = pd.DataFrame(lstscreen)
                            existing_columns = ["Stock","%Chng","LTP","volume"]
                            new_columns = ["BidQty","AskQty","LwrCP","UprCP","VWAP","DayVola","Del(%)"]
                            existing_columns.extend(new_columns)
                            scr_df = scr_df[existing_columns]
                            scr_df.sort_values(by=["volume","BidQty"], ascending=False, inplace=True)
                            tabulated_results = colorText.miniTabulator().tb.tabulate(
                                    scr_df,
                                    headers="keys",
                                    showindex=False,
                                    tablefmt=colorText.No_Pad_GridFormat,
                                    maxcolwidths=Utility.tools.getMaxColumnWidths(scr_df)
                                )
                            table_length = 2*len(lstscreen)+5
                            OutputControls().printOutput('\n'+tabulated_results)
                            OutputControls().moveCursorUpLines(table_length)
                            
                    if self.keyboard_interrupt_event_fired:
                        return False, backtest_df
                    return not ((testing and len(lstscreen) >= 1) or len(lstscreen) >= max_allowed), backtest_df
                    
                other_args = (menu_option, backtest_period, result, lstscreen, lstsave)
                backtest_df, result = PKScanRunner.runScan(self.user_passed_args, testing, num_stocks, iterations, items, num_stocks_per_iteration, tasks_queue, results_queue, original_number_of_stocks, backtest_df, *other_args, resultsReceivedCb=process_results_callback)

            OutputControls().moveCursorUpLines(3 if OutputControls().enableMultipleLineOutput else 1)
            self.elapsed_time = time.time() - self.start_time
            
            if menu_option in ["X", "G", "C", "F"]:
                screen_results = pd.DataFrame(lstscreen)
                save_results = pd.DataFrame(lstsave)
                
        except KeyboardInterrupt:
            try:
                self.keyboard_interrupt_event.set()
                self.keyboard_interrupt_event_fired = True
                OutputControls().printOutput(
                    colorText.FAIL
                    + "\n  [+] Terminating Script, Please wait..."
                    + colorText.END
                )
                PKScanRunner.terminateAllWorkers(userPassedArgs=self.user_passed_args, consumers=consumers, tasks_queue=tasks_queue, testing=testing)
                logging.shutdown()
            except KeyboardInterrupt:
                pass
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput(
                colorText.FAIL
                + f"\nException:\n{e}\n  [+] Terminating Script, Please wait..."
                + colorText.END
            )
            PKScanRunner.terminateAllWorkers(userPassedArgs=self.user_passed_args, consumers=consumers, tasks_queue=tasks_queue, testing=testing)
            logging.shutdown()

        if result is not None and len(result) >=1 and self.criteria_date_time is None:
            if self.user_passed_args is not None and self.user_passed_args.backtestdaysago is not None:
                self.criteria_date_time = result[2].copy().index[-1-int(self.user_passed_args.backtestdaysago)]
            else:
                self.criteria_date_time = result[2].copy().index[-1] if self.user_passed_args.slicewindow is None else datetime.strptime(self.user_passed_args.slicewindow.replace("'",""),"%Y-%m-%d %H:%M:%S.%f%z")
            local_tz = datetime.now(UTC).astimezone().tzinfo
            exchange_tz = PKDateUtilities.currentDateTime().astimezone().tzinfo
            
            if local_tz != exchange_tz:
                self.criteria_date_time = PKDateUtilities.utc_to_ist(self.criteria_date_time, localTz=local_tz)
                
        if result is not None and len(result) >=1 and "Date" not in save_results.columns:
            temp_df = result[2].copy()
            temp_df.reset_index(inplace=True)
            temp_df = temp_df.tail(1)
            temp_df.rename(columns={"index": "Date"}, inplace=True)
            target_date = (
                temp_df["Date"].iloc[0]
                if "Date" in temp_df.columns
                else str(temp_df.iloc[:, 0][0])
            )
            save_results["Date"] = str(target_date).split(" ")[0]
            
        return screen_results, save_results, backtest_df

    def process_results(self, menu_option, backtest_period, result, lstscreen, lstsave, backtest_df):
        """
        Process scanning results and update data structures.
        
        Args:
            menu_option: Selected menu option
            backtest_period: Backtest period in days
            result: Result data
            lstscreen: Screen results list
            lstsave: Save results list
            backtest_df: Backtest dataframe
            
        Returns:
            DataFrame: Updated backtest dataframe
        """
        if result is not None:
            lstscreen.append(result[0])
            lstsave.append(result[1])
            sample_days = result[4]
            
            if menu_option == "B":
                backtest_df = self.update_backtest_results(
                    backtest_period, self.start_time, result, sample_days, backtest_df
                )
                
            self.elapsed_time = time.time() - self.start_time
            
        return backtest_df

    def update_backtest_results(self, backtest_period, start_time, result, sample_days, backtest_df):
        """
        Update backtest results with new data.
        
        Args:
            backtest_period: Backtest period in days
            start_time: Start time of operation
            result: Result data
            sample_days: Number of sample days
            backtest_df: Backtest dataframe
            
        Returns:
            DataFrame: Updated backtest dataframe
        """
        sell_signal = (
            str(self.selected_choice["2"]) in ["6", "7"] and str(self.selected_choice["3"]) in ["2"]
        ) or self.selected_choice["2"] in ["15", "16", "19", "25"]
        
        backtest_df = backtest(
            result[3],
            result[2],
            result[1],
            result[0],
            backtest_period,
            sample_days,
            backtest_df,
            sell_signal,
        )
        
        self.elapsed_time = time.time() - start_time
        return backtest_df

    def get_review_date(self):
        """
        Get the review date for scanning operations.
        
        Returns:
            str: Review date string
        """
        review_date = PKDateUtilities.tradingDate().strftime('%Y-%m-%d')
        
        if self.user_passed_args is not None and self.user_passed_args.backtestdaysago is not None:
            review_date = PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(self.user_passed_args.backtestdaysago))
            
        return review_date

    def get_max_allowed_results_count(self, iterations, testing):
        """
        Get the maximum allowed results count based on iterations and testing mode.
        
        Args:
            iterations: Number of iterations
            testing (bool): Whether running in test mode
            
        Returns:
            int: Maximum allowed results count
        """
        return iterations * (self.config_manager.maxdisplayresults if self.user_passed_args.maxdisplayresults is None else (int(self.user_passed_args.maxdisplayresults) if not testing else 1))

    def get_iterations_and_stock_counts(self, num_stocks, iterations):
        """
        Calculate iterations and stock counts for scanning operations.
        
        Args:
            num_stocks: Number of stocks to process
            iterations: Number of iterations
            
        Returns:
            tuple: Iterations count and stocks per iteration
        """
        if num_stocks <= 2500:
            return 1, num_stocks
            
        original_iterations = iterations
        ideal_num_stocks_max_per_iteration = 100
        iterations = int(num_stocks * iterations / ideal_num_stocks_max_per_iteration) + 1
        num_stocks_per_iteration = int(num_stocks / int(iterations))
        
        if num_stocks_per_iteration < 10:
            num_stocks_per_iteration = num_stocks if (iterations == 1 or num_stocks <= iterations) else int(num_stocks / int(iterations))
            iterations = original_iterations
            
        if num_stocks_per_iteration > 500:
            num_stocks_per_iteration = 500
            iterations = int(num_stocks / num_stocks_per_iteration) + 1
            
        return iterations, num_stocks_per_iteration

    def close_workers_and_exit(self):
        """Close all worker processes and exit the application."""
        if self.consumers is not None:
            PKScanRunner.terminateAllWorkers(userPassedArgs=self.user_passed_args, consumers=self.consumers, 
                                           tasks_queue=self.tasks_queue, testing=self.user_passed_args.testbuild)


class ResultProcessor:
    """
    Processes, formats, and displays screening results.
    Handles data labeling, filtering, and presentation of scan outcomes.
    """

    def __init__(self, config_manager, user_passed_args):
        """
        Initialize the ResultProcessor with configuration and user arguments.
        
        Args:
            config_manager: Configuration manager instance
            user_passed_args: User passed arguments
        """
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args
        self.saved_screen_results = None
        self.show_saved_diff_results = False
        self.results_contents_encoded = None
        self.criteria_date_time = None

    def label_data_for_printing(self, screen_results, save_results, volume_ratio, execute_option, reversal_option, menu_option):
        """
        Label and format data for printing and display.
        
        Args:
            screen_results: Screen results data
            save_results: Results to save
            volume_ratio: Volume ratio for formatting
            execute_option: Execute option value
            reversal_option: Reversal option value
            menu_option: Menu option value
            
        Returns:
            tuple: Formatted screen results and save results
        """
        if save_results is None:
            return screen_results, save_results
            
        try:
            is_trading = PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]
            
            if "RUNNER" not in os.environ.keys() and (is_trading or self.user_passed_args.monitor or ("RSIi" in save_results.columns)) and self.config_manager.calculatersiintraday:
                screen_results['RSI'] = screen_results['RSI'].astype(str) + "/" + screen_results['RSIi'].astype(str)
                save_results['RSI'] = save_results['RSI'].astype(str) + "/" + save_results['RSIi'].astype(str)
                screen_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
                save_results.rename(columns={"RSI": "RSI/i"}, inplace=True)
                
            sort_key = ["volume"] if "RSI" not in self.menu_choice_hierarchy else ("RSIi" if (is_trading or "RSIi" in save_results.columns) else "RSI")
            ascending = [False if "RSI" not in self.menu_choice_hierarchy else True]
            
            if execute_option == 21:
                if reversal_option in [3, 5, 6, 7]:
                    sort_key = ["MFI"]
                    ascending = [reversal_option in [6, 7]]
                elif reversal_option in [8, 9]:
                    sort_key = ["FVDiff"]
                    ascending = [reversal_option in [9]]
            elif execute_option == 7:
                if reversal_option in [3]:
                    if "SuperConfSort" in save_results.columns:
                        sort_key = ["SuperConfSort"]
                        ascending = [False]
                    else:
                        sort_key = ["volume"]
                        ascending = [False]
                elif reversal_option in [4]:
                    if "deviationScore" in save_results.columns:
                        sort_key = ["deviationScore"]
                        ascending = [True]
                    else:
                        sort_key = ["volume"]
                        ascending = [False]
            elif execute_option == 23:
                sort_key = ["bbands_ulr_ratio_max5"] if "bbands_ulr_ratio_max5" in screen_results.columns else ["volume"]
                ascending = [False]
            elif execute_option == 27:  # ATR Cross
                sort_key = ["ATR"] if "ATR" in screen_results.columns else ["volume"]
                ascending = [False]
            elif execute_option == 31:  # DEEL Momentum
                sort_key = ["%Chng"]
                ascending = [False]
                
            try:
                try:
                    screen_results[sort_key] = screen_results[sort_key].replace("", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
                except:
                    pass
                    
                try:
                    save_results[sort_key] = save_results[sort_key].replace("", np.nan).replace(np.inf, np.nan).replace(-np.inf, np.nan).astype(float)
                except:
                    pass
                    
                screen_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
                save_results.sort_values(by=sort_key, ascending=ascending, inplace=True)
            except Exception as e:
                default_logger().debug(e, exc_info=True)
                pass
                
            columns_to_be_deleted = ["MFI", "FVDiff", "ConfDMADifference", "bbands_ulr_ratio_max5", "RSIi"]
            
            if menu_option not in ["F"]:
                columns_to_be_deleted.extend(["ScanOption"])
                
            if "EoDDiff" in save_results.columns:
                columns_to_be_deleted.extend(["Trend", "Breakout"])
                
            if "SuperConfSort" in save_results.columns:
                columns_to_be_deleted.extend(["SuperConfSort"])
                
            if "deviationScore" in save_results.columns:
                columns_to_be_deleted.extend(["deviationScore"])
                
            if self.user_passed_args is not None and self.user_passed_args.options is not None and self.user_passed_args.options.upper().startswith("C"):
                columns_to_be_deleted.append("FairValue")
                
            if execute_option == 27 and "ATR" in screen_results.columns:  # ATR Cross
                screen_results['ATR'] = screen_results['ATR'].astype(str)
                screen_results['ATR'] = colorText.GREEN + screen_results['ATR'] + colorText.END
                
            for column in columns_to_be_deleted:
                if column in save_results.columns:
                    save_results.drop(column, axis=1, inplace=True, errors="ignore")
                    screen_results.drop(column, axis=1, inplace=True, errors="ignore")
                    
            if "Stock" in screen_results.columns:
                screen_results.set_index("Stock", inplace=True)
                
            if "Stock" in save_results.columns:
                save_results.set_index("Stock", inplace=True)
                
            screen_results["volume"] = screen_results["volume"].astype(str)
            save_results["volume"] = save_results["volume"].astype(str)
            
            screen_results.loc[:, "volume"] = screen_results.loc[:, "volume"].apply(
                lambda x: Utility.tools.formatRatio(float(ImageUtility.PKImageTools.removeAllColorStyles(x)), volume_ratio) if len(str(x).strip()) > 0 else ''
            )
            
            save_results.loc[:, "volume"] = save_results.loc[:, "volume"].apply(
                lambda x: str(x) + "x"
            )
            
            screen_results.rename(
                columns={
                    "Trend": f"Trend({self.config_manager.daysToLookback}Prds)",
                    "Breakout": f"Breakout({self.config_manager.daysToLookback}Prds)",
                },
                inplace=True,
            )
            
            save_results.rename(
                columns={
                    "Trend": f"Trend({self.config_manager.daysToLookback}Prds)",
                    "Breakout": f"Breakout({self.config_manager.daysToLookback}Prds)",
                },
                inplace=True,
            )
            
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            
        screen_results.dropna(how="all" if menu_option not in ["F"] else "any", axis=1, inplace=True)
        save_results.dropna(how="all" if menu_option not in ["F"] else "any", axis=1, inplace=True)
        
        return screen_results, save_results

    def print_notify_save_screened_results(self, screen_results, save_results, selected_choice, 
                                          menu_choice_hierarchy, testing, user=None, execute_option=None, menu_option=None):
        """
        Print, notify, and save screened results.
        
        Args:
            screen_results: Screen results data
            save_results: Results to save
            selected_choice: Selected choice dictionary
            menu_choice_hierarchy: Menu choice hierarchy string
            testing (bool): Whether running in test mode
            user: User identifier
            execute_option: Execute option value
            menu_option: Menu option value
        """
        # [Implementation of the complex result processing logic would go here]
        # This method handles the complete result presentation pipeline
        
        pass

    def remove_unknowns(self, screen_results, save_results):
        """
        Remove unknown values from results data.
        
        Args:
            screen_results: Screen results data
            save_results: Results to save
            
        Returns:
            tuple: Cleaned screen results and save results
        """
        for col in screen_results.keys():
            screen_results = screen_results[
                screen_results[col].astype(str).str.contains("Unknown") == False
            ]
            
        for col in save_results.keys():
            save_results = save_results[
                save_results[col].astype(str).str.contains("Unknown") == False
            ]
            
        return screen_results, save_results

    def removed_unused_columns(self, screen_results, save_results, drop_additional_columns=[], user_args=None):
        """
        Remove unused columns from results data.
        
        Args:
            screen_results: Screen results data
            save_results: Results to save
            drop_additional_columns: Additional columns to drop
            user_args: User arguments
            
        Returns:
            str: Summary returns string
        """
        periods = self.config_manager.periodsRange
        
        if user_args is not None and user_args.backtestdaysago is not None and int(user_args.backtestdaysago) < 22:
            drop_additional_columns.append("22-Pd")
            
        summary_returns = ""  # ("w.r.t. " + save_results["Date"].iloc[0]) if "Date" in save_results.columns else ""
        
        for period in periods:
            if save_results is not None:
                with pd.option_context('mode.chained_assignment', None):
                    save_results.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
                    save_results.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
                    
                if len(drop_additional_columns) > 0:
                    for col in drop_additional_columns:
                        if col in save_results.columns:
                            save_results.drop(col, axis=1, inplace=True, errors="ignore")
                            
            if screen_results is not None:
                with pd.option_context('mode.chained_assignment', None):
                    screen_results.drop(f"LTP{period}", axis=1, inplace=True, errors="ignore")
                    screen_results.drop(f"Growth{period}", axis=1, inplace=True, errors="ignore")
                    
                    if len(drop_additional_columns) > 0:
                        for col in drop_additional_columns:
                            if col in screen_results.columns:
                                screen_results.drop(col, axis=1, inplace=True, errors="ignore")
                                
        return summary_returns

    def save_screen_results_encoded(self, encoded_text=None):
        """
        Save screen results in encoded format.
        
        Args:
            encoded_text: Encoded text to save
            
        Returns:
            str: File name identifier
        """
        import uuid
        uuid_file_name = str(uuid.uuid4())
        os.makedirs(os.path.dirname(os.path.join(Archiver.get_user_outputs_dir(), f"DeleteThis{os.sep}")), exist_ok=True)
        to_be_deleted_folder = os.path.join(Archiver.get_user_outputs_dir(), "DeleteThis")
        file_name = os.path.join(to_be_deleted_folder, uuid_file_name)
        
        try:
            with open(file_name, 'w', encoding="utf-8") as f:
                f.write(encoded_text)
        except:
            pass
            
        return f'{uuid_file_name}~{PKDateUtilities.currentDateTime().strftime("%Y-%m-%d %H:%M:%S.%f%z").replace(" ","~")}'

    def read_screen_results_decoded(self, file_name=None):
        """
        Read screen results from encoded format.
        
        Args:
            file_name: File name to read
            
        Returns:
            str: Decoded contents
        """
        os.makedirs(os.path.dirname(os.path.join(Archiver.get_user_outputs_dir(), f"DeleteThis{os.sep}")), exist_ok=True)
        to_be_deleted_folder = os.path.join(Archiver.get_user_outputs_dir(), "DeleteThis")
        file_path = os.path.join(to_be_deleted_folder, file_name)
        contents = None
        
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                contents = f.read()
        except:
            pass
            
        return contents


class TelegramNotifier:
    """
    Handles all Telegram notifications and communications.
    Manages message sending, media attachments, and user subscriptions.
    """

    def __init__(self, dev_channel_id="-1001785195297"):
        """
        Initialize the TelegramNotifier with development channel ID.
        
        Args:
            dev_channel_id: Development channel ID for notifications
        """
        self.DEV_CHANNEL_ID = dev_channel_id
        self.test_messages_queue = []
        self.media_group_dict = {}

    def send_message_to_telegram_channel(self, message=None, photo_file_path=None, 
                                        document_file_path=None, caption=None, user=None, mediagroup=False):
        """
        Send message to Telegram channel with various attachment options.
        
        Args:
            message: Text message to send
            photo_file_path: Path to photo file
            document_file_path: Path to document file
            caption: Caption for media
            user: User identifier
            mediagroup (bool): Whether sending media group
        """
        default_logger().debug(f"Received message:{message}, caption:{caption}, for user : {user} with mediagroup:{mediagroup}")
        
        if ("RUNNER" not in os.environ.keys() and (self.user_passed_args is not None and not self.user_passed_args.log)) or (self.user_passed_args is not None and self.user_passed_args.telegram):
            return
            
        if user is None and self.user_passed_args is not None and self.user_passed_args.user is not None:
            user = self.user_passed_args.user
            
        if not mediagroup:
            if self.test_messages_queue is not None:
                self.test_messages_queue.append(f"message:{message}\ncaption:{caption}\nuser:{user}\ndocument:{document_file_path}")
                
                if len(self.test_messages_queue) > 10:
                    self.test_messages_queue.pop(0)
                    
            if user is not None and caption is not None:
                caption = f"{caption.replace('&','n')}."
                
            if message is not None:
                try:
                    message = message.replace("&", "n").replace("<", "*")
                    send_message(message, userID=user)
                except Exception as e:
                    default_logger().debug(e, exc_info=True)
            else:
                message = ""
                
            if photo_file_path is not None:
                try:
                    if caption is not None:
                        caption = f"{caption.replace('&','n')}"
                    send_photo(photo_file_path, (caption if len(caption) <= 1024 else ""), userID=user)
                    sleep(2)
                except Exception as e:
                    default_logger().debug(e, exc_info=True)
                    
            if document_file_path is not None:
                try:
                    if caption is not None and isinstance(caption, str):
                        caption = f"{caption.replace('&','n')}"
                    send_document(document_file_path, (caption if len(caption) <= 1024 else ""), userID=user)
                    sleep(2)
                except Exception as e:
                    default_logger().debug(e, exc_info=True)
        else:
            file_paths = []
            file_captions = []
            
            if "ATTACHMENTS" in self.media_group_dict.keys():
                attachments = self.media_group_dict["ATTACHMENTS"]
                num_files = len(attachments)
                
                if num_files >= 4:
                    self.media_group_dict["ATTACHMENTS"] = []
                    
                for attachment in attachments:
                    file_paths.append(attachment["FILEPATH"])
                    clean_caption = attachment["CAPTION"].replace('&', 'n')[:1024]
                    
                    if "<pre>" in clean_caption and "</pre>" not in clean_caption:
                        clean_caption = f"{clean_caption[:1018]}</pre>"
                        
                    file_captions.append(clean_caption)
                    
                if self.test_messages_queue is not None:
                    self.test_messages_queue.append(f"message:{file_captions[-1]}\ncaption:{file_captions[-1]}\nuser:{user}\ndocument:{file_paths[-1]}")
                    
                    if len(self.test_messages_queue) > 10:
                        self.test_messages_queue.pop(0)
                        
                if len(file_paths) > 0 and not self.user_passed_args.monitor:
                    resp = send_media_group(user=self.user_passed_args.user,
                                                    png_paths=[],
                                                    png_album_caption=None,
                                                    file_paths=file_paths,
                                                    file_captions=file_captions)
                    
                    if resp is not None:
                        default_logger().debug(resp.text, exc_info=True)
                        
                caption = f"{str(len(file_captions))} files sent!"
                message = self.media_group_dict["CAPTION"].replace('&', 'n').replace("<", "*")[:1024] if "CAPTION" in self.media_group_dict.keys() else "-"
                default_logger().debug(f"Received updated message:{message}, caption:{caption}, for user : {user} with mediagroup:{mediagroup}")
            else:
                default_logger().debug(f"No ATTACHMENTS in media_group_dict: {self.media_group_dict.keys(),}\nReceived updated message:{message}, caption:{caption}, for user : {user} with mediagroup:{mediagroup}")
                
            for f in file_paths:
                try:
                    if "RUNNER" in os.environ.keys():
                        os.remove(f)
                    elif not f.endswith("xlsx"):
                        os.remove(f)
                except:
                    pass
                    
            self.handle_alert_subscriptions(user, message)
            
        if user is not None:
            if str(user) != str(self.DEV_CHANNEL_ID) and self.user_passed_args is not None and not self.user_passed_args.monitor:
                send_message(
                    f"Responded back to userId:{user} with {caption}.{message} [{self.user_passed_args.options.replace(':D','')}]",
                    userID=self.DEV_CHANNEL_ID,
                )

    def handle_alert_subscriptions(self, user, message):
        """
        Handle user subscriptions to automated alerts.
        
        Args:
            user: User identifier
            message: Message content
        """
        if user is not None and message is not None and "|" in str(message):
            if int(user) > 0:
                scan_id = message.split("|")[0].replace("*b>", "").strip()
                from PKDevTools.classes.DBManager import DBManager
                db_manager = DBManager()
                
                if db_manager.url is not None and db_manager.token is not None:
                    alert_user = db_manager.alertsForUser(int(user))
                    
                    if alert_user is None or len(alert_user.scannerJobs) == 0 or str(scan_id) not in alert_user.scannerJobs:
                        reply_markup = {
                            "inline_keyboard": [
                                [{"text": f"Yes! Subscribe", "callback_data": f"SUB_{scan_id}"}]
                            ],
                        }
                        
                        send_message(message=f"🔴 <b>Please check your current alerts, balance and subscriptions using /OTP before subscribing for alerts</b>.🔴 If you are not already subscribed to this alert, would you like to subscribe to this ({scan_id}) automated scan alert for a day during market hours (NSE - IST timezone)? You will need to pay ₹ {'40' if str(scan_id).upper().startswith('P') else '31'} (One time) for automated alerts to {scan_id} all day on the day of subscription. 🔴 If you say <b>Yes</b>, the corresponding charges will be deducted from your alerts balance!🔴",
                            userID=int(user),
                            reply_markup=reply_markup)
                    elif alert_user is not None and len(alert_user.scannerJobs) > 0 and str(scan_id) in alert_user.scannerJobs:
                        send_message(message=f"Thank you for subscribing to (<b>{scan_id}</b>) automated scan alert! We truly hope you are enjoying the alerts! You will continue to receive alerts for the duration of NSE Market hours for today. For any feedback, drop a note to @ItsOnlyPK.",
                            userID=int(user),)

    def send_test_status(self, screen_results, label, user=None):
        """
        Send test status message to Telegram.
        
        Args:
            screen_results: Screen results data
            label: Test label
            user: User identifier
        """
        msg = "<b>SUCCESS</b>" if (screen_results is not None and len(screen_results) >= 1) else "<b>FAIL</b>"
        self.send_message_to_telegram_channel(
            message=f"{msg}: Found {len(screen_results) if screen_results is not None else 0} Stocks for {label}", user=user
        )

    def send_quick_scan_result(self, menu_choice_hierarchy, user, tabulated_results, 
                              markdown_results, caption, png_name, png_extension, 
                              addendum=None, addendum_label=None, backtest_summary="", 
                              backtest_detail="", summary_label=None, detail_label=None, 
                              legend_prefix_text="", force_send=False):
        """
        Send quick scan result to Telegram with formatted output.
        
        Args:
            menu_choice_hierarchy: Menu choice hierarchy string
            user: User identifier
            tabulated_results: Tabulated results text
            markdown_results: Markdown formatted results
            caption: Caption for the message
            png_name: PNG file name
            png_extension: PNG file extension
            addendum: Additional content
            addendum_label: Label for addendum
            backtest_summary: Backtest summary
            backtest_detail: Backtest detail
            summary_label: Label for summary
            detail_label: Label for detail
            legend_prefix_text: Legend prefix text
            force_send (bool): Whether to force send
        """
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            if (("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and os.environ["RUNNER"] == "LOCAL_RUN_SCANNER")):
                return
                
        try:
            if not is_token_telegram_configured():
                return
                
            ImageUtility.PKImageTools.tableToImage(
                markdown_results,
                tabulated_results,
                png_name + png_extension,
                menu_choice_hierarchy,
                backtestSummary=backtest_summary,
                backtestDetail=backtest_detail,
                addendum=addendum,
                addendumLabel=addendum_label,
                summaryLabel=summary_label,
                detailLabel=detail_label,
                legendPrefixText=legend_prefix_text
            )
            
            if force_send:
                self.send_message_to_telegram_channel(
                    message=None,
                    document_filePath=png_name + png_extension,
                    caption=caption,
                    user=user,
                )
                os.remove(png_name + png_extension)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass


class DataManager:
    """
    Manages data loading, caching, and storage operations.
    Handles database interactions, file operations, and data retrieval.
    """

    def __init__(self, config_manager, user_passed_args):
        """
        Initialize the DataManager with configuration and user arguments.
        
        Args:
            config_manager: Configuration manager instance
            user_passed_args: User passed arguments
        """
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args
        self.fetcher = Fetcher.screenerStockDataFetcher(self.config_manager)
        self.mstar_fetcher = morningstarDataFetcher(self.config_manager)
        self.stock_dict_primary = None
        self.stock_dict_secondary = None
        self.load_count = 0
        self.loaded_stock_data = False
        self.list_stock_codes = None
        self.last_scan_output_stock_codes = None
        self.run_clean_up = False

    @exit_after(10)
    def try_load_data_on_background_thread(self):
        """Attempt to load data on a background thread with timeout."""
        if self.stock_dict_primary is None:
            self.stock_dict_primary = {}
            self.stock_dict_secondary = {}
            self.loaded_stock_data = False
            
        self.config_manager.getConfig(ConfigManager.parser)
        self.default_answer = "Y"
        self.user_passed_args = None
        
        with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
            list_stock_codes = self.fetcher.fetchStockCodes(int(self.config_manager.defaultIndex), stockCode=None)
            
        self.load_database_or_fetch(downloadOnly=True, list_stock_codes=list_stock_codes, 
                                   menu_option="X", index_option=int(self.config_manager.defaultIndex))

    def load_database_or_fetch(self, download_only, list_stock_codes, menu_option, index_option):
        """
        Load data from database or fetch from source.
        
        Args:
            download_only (bool): Whether only downloading data
            list_stock_codes: List of stock codes to process
            menu_option: Selected menu option
            index_option: Selected index option
            
        Returns:
            tuple: Primary and secondary stock data dictionaries
        """
        if menu_option not in ["C"]:
            self.stock_dict_primary = AssetsManager.PKAssetsManager.loadStockData(
                self.stock_dict_primary,
                self.config_manager,
                downloadOnly=download_only,
                defaultAnswer=self.default_answer,
                forceLoad=(menu_option in ["X", "B", "G", "S", "F"]),
                stockCodes=list_stock_codes,
                exchangeSuffix="" if (index_option == 15 or (self.config_manager.defaultIndex == 15 and index_option == 0)) else ".NS",
                userDownloadOption=menu_option
            )
            
        if menu_option not in ["C"] and (self.user_passed_args is not None and 
            (self.user_passed_args.monitor is not None or \
            ("|" in self.user_passed_args.options and ':i' in self.user_passed_args.options) or \
            (":33:3:" in self.user_passed_args.options or \
            ":32:" in self.user_passed_args.options or \
            ":38:" in self.user_passed_args.options))):
            
            prev_duration = self.config_manager.duration
            prev_period = self.config_manager.period
            candle_duration = (self.user_passed_args.intraday if (self.user_passed_args is not None and self.user_passed_args.intraday is not None) else ("1m" if self.config_manager.duration.endswith("d") else self.config_manager.duration))
            
            self.config_manager.toggleConfig(candleDuration=candle_duration, clearCache=False)
            
            if self.user_passed_args is not None and ":33:3:" in self.user_passed_args.options:
                exists, cache_file = AssetsManager.PKAssetsManager.afterMarketStockDataExists(True, forceLoad=(menu_option in ["X", "B", "G", "S", "F"]))
                cache_file = os.path.join(Archiver.get_user_data_dir(), cache_file)
                cache_file_size = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
                
                if cache_file_size < 1024 * 1024 * 100:  # 1m data for 5d is at least 450MB
                    self.config_manager.deleteFileWithPattern(pattern="*intraday_stock_data_*.pkl", rootDir=Archiver.get_user_data_dir())
                    
                self.config_manager.duration = "1m"
                self.config_manager.period = "5d"
                self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
                
            self.stock_dict_secondary = AssetsManager.PKAssetsManager.loadStockData(
                self.stock_dict_secondary,
                self.config_manager,
                downloadOnly=download_only,
                defaultAnswer=self.default_answer,
                forceLoad=(menu_option in ["X", "B", "G", "S", "F"]),
                stockCodes=list_stock_codes,
                isIntraday=True,
                exchangeSuffix="" if (index_option == 15 or (self.config_manager.defaultIndex == 15 and index_option == 0)) else ".NS",
                userDownloadOption=menu_option
            )
            
            self.config_manager.duration = prev_duration
            self.config_manager.period = prev_period
            self.config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
            
        self.loaded_stock_data = True
        Utility.tools.loadLargeDeals()
        
        return self.stock_dict_primary, self.stock_dict_secondary

    def get_latest_trade_date_time(self, stock_dict_primary):
        """
        Get the latest trade date and time from stock data.
        
        Args:
            stock_dict_primary: Primary stock data dictionary
            
        Returns:
            tuple: Last trade date and time strings
        """
        stocks = list(stock_dict_primary.keys())
        stock = stocks[0]
        
        try:
            last_trade_date = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
            last_trade_time_ist = PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
            df = pd.DataFrame(data=stock_dict_primary[stock]["data"],
                            columns=stock_dict_primary[stock]["columns"],
                            index=stock_dict_primary[stock]["index"])
            ts = df.index[-1]
            last_traded = pd.to_datetime(ts, unit='s', utc=True)
            last_trade_date = last_traded.strftime("%Y-%m-%d")
            last_trade_time = last_traded.strftime("%H:%M:%S")
            
            if last_trade_time == "00:00:00":
                last_trade_time = last_trade_time_ist
        except:
            pass
            
        return last_trade_date, last_trade_time

    def prepare_stocks_for_screening(self, testing, download_only, list_stock_codes, index_option):
        """
        Prepare stocks for screening operations.
        
        Args:
            testing (bool): Whether running in test mode
            download_only (bool): Whether only downloading data
            list_stock_codes: List of stock codes to process
            index_option: Selected index option
            
        Returns:
            list: Prepared list of stock codes
        """
        # Note: update_menu_choice_hierarchy should be called by PKScreenerMain, not here
        # since DataManager doesn't have access to menu state
            
        index_option = int(index_option)
        
        if list_stock_codes is None or len(list_stock_codes) == 0:
            if index_option >= 0 and index_option <= 14:
                should_suppress = not OutputControls().enableMultipleLineOutput
                
                with SuppressOutput(suppress_stderr=should_suppress, suppress_stdout=should_suppress):
                    list_stock_codes = self.fetcher.fetchStockCodes(
                        index_option, stockCode=None
                    )
            elif index_option == 15:
                OutputControls().printOutput("  [+] Getting Stock Codes From NASDAQ... ", end="")
                nasdaq = PKNasdaqIndexFetcher(self.config_manager)
                list_stock_codes, _ = nasdaq.fetchNasdaqIndexConstituents()
                
                if len(list_stock_codes) > 10:
                    OutputControls().printOutput(
                        colorText.GREEN
                        + ("=> Done! Fetched %d stock codes." % len(list_stock_codes))
                        + colorText.END
                    )
                    
                    if self.config_manager.shuffleEnabled:
                        random.shuffle(list_stock_codes)
                        OutputControls().printOutput(
                            colorText.BLUE
                            + "  [+] Stock shuffling is active."
                            + colorText.END
                        )
                else:
                    OutputControls().printOutput(
                        colorText.FAIL
                        + ("=> Failed! Could not fetch stock codes from NASDAQ!")
                        + colorText.END
                    )
                    
            if (list_stock_codes is None or len(list_stock_codes) == 0) and testing:
                list_stock_codes = [TEST_STKCODE if index_option < 15 else "AMD"]
                
        if index_option == 0:
            self.selected_choice["3"] = ".".join(list_stock_codes)
            
        if testing:
            list_stock_codes = [random.choice(list_stock_codes)]
            
        return list_stock_codes

    @Halo(text='', spinner='dots')
    def get_performance_stats(self):
        """Get performance statistics from Morningstar."""
        return self.mstar_fetcher.fetchMorningstarStocksPerformanceForExchange()

    @Halo(text='', spinner='dots')
    def get_mfi_stats(self, pop_option):
        """
        Get MFI (Money Flow Index) statistics.
        
        Args:
            pop_option: Population option
            
        Returns:
            DataFrame: MFI statistics results
        """
        if pop_option == 4:
            screen_results = self.mstar_fetcher.fetchMorningstarTopDividendsYieldStocks()
        elif pop_option in [1, 2]:
            screen_results = self.mstar_fetcher.fetchMorningstarFundFavouriteStocks(
                "NoOfFunds" if pop_option == 2 else "ChangeInShares"
            )
            
        return screen_results

    def handle_request_for_specific_stocks(self, options, index_option):
        """
        Handle request for specific stocks based on options.
        
        Args:
            options: Options list
            index_option: Selected index option
            
        Returns:
            list: List of specific stock codes
        """
        list_stock_codes = [] if self.list_stock_codes is None or len(self.list_stock_codes) == 0 else self.list_stock_codes
        str_options = ""
        
        if isinstance(options, list):
            str_options = ":".join(options).split(">")[0]
        else:
            str_options = options.split(">")[0]
            
        if index_option == 0:
            if len(str_options) >= 4:
                str_options = str_options.replace(":D:", ":").replace(">", "")
                provided_options = str_options.split(":")
                
                for option in provided_options:
                    if not "".join(str(option).split(".")).isdecimal() and len(option.strip()) > 1:
                        list_stock_codes = str(option.strip()).split(",")
                        break
                        
        return list_stock_codes

    def cleanup_local_results(self):
        """Clean up local results and temporary files."""
        # global run_clean_up
        self.run_clean_up = True
        
        if self.user_passed_args.answerdefault is not None or self.user_passed_args.systemlaunched or self.user_passed_args.testbuild:
            return
            
        from PKDevTools.classes.NSEMarketStatus import NSEMarketStatus
        
        if not NSEMarketStatus().shouldFetchNextBell()[0]:
            return
            
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        should_prompt = (launcher.endswith(".py\"") or launcher.endswith(".py")) and (self.user_passed_args is None or self.user_passed_args.answerdefault is None)
        response = "N"
        
        if should_prompt:
            response = OutputControls().takeUserInput(f"  [+] {colorText.WARN}Clean up local non-essential system generated data?{colorText.END}{colorText.FAIL}[Default: {response}]{colorText.END}\n    (User generated reports won't be deleted.)        :") or response
            
        if "y" in response.lower():
            dirs = [Archiver.get_user_data_dir(), Archiver.get_user_cookies_dir(), 
                    Archiver.get_user_temp_dir(), Archiver.get_user_indices_dir()]
                    
            for dir in dirs:
                self.config_manager.deleteFileWithPattern(rootDir=dir, pattern="*")
                
            response = OutputControls().takeUserInput(f"\n  [+] {colorText.WARN}Clean up local user generated reports as well?{colorText.END} {colorText.FAIL}[Default: N]{colorText.END} :") or "n"
            
            if "y" in response.lower():
                self.config_manager.deleteFileWithPattern(rootDir=Archiver.get_user_reports_dir(), pattern="*.*")
                
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)


class BacktestManager:
    """
    Manages backtesting operations and analysis.
    Handles backtest execution, result processing, and performance reporting.
    """

    def __init__(self, config_manager, user_passed_args):
        """
        Initialize the BacktestManager with configuration and user arguments.
        
        Args:
            config_manager: Configuration manager instance
            user_passed_args: User passed arguments
        """
        self.config_manager = config_manager
        self.user_passed_args = user_passed_args

    def take_backtest_inputs(self, menu_option=None, index_option=None, execute_option=None, backtest_period=0):
        """
        Take backtest inputs from user.
        
        Args:
            menu_option: Selected menu option
            index_option: Selected index option
            execute_option: Selected execute option
            backtest_period: Backtest period in days
            
        Returns:
            tuple: Index option, execute option, and backtest period
        """
        g10k = '"Growth of 10k"'
        OutputControls().printOutput(
            colorText.GREEN
            + f"  [+] For {g10k if menu_option == 'G' else 'backtesting'}, you can choose from (1,2,3,4,5,10,15,22,30) or any other custom periods (< 1y)."
        )
        
        try:
            if backtest_period == 0:
                backtest_period = int(
                    input(
                        colorText.FAIL
                        + f"  [+] Enter {g10k if menu_option == 'G' else 'backtesting'} period (Default is {15 if menu_option == 'G' else 30} [days]): "
                    )
                )
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            
        if backtest_period == 0:
            backtest_period = 3 if menu_option == "G" else 30
            
        index_option, execute_option = self.init_post_level0_execution(
            menu_option=menu_option,
            index_option=index_option,
            execute_option=execute_option,
            skip=["N", "E"],
        )
        
        index_option, execute_option = self.init_post_level1_execution(
            index_option=index_option,
            execute_option=execute_option,
            skip=[
                "0",
                "29",
                "42",
            ],
        )
        
        return index_option, execute_option, backtest_period

    @Halo(text='', spinner='dots')
    def prepare_grouped_x_ray(self, backtest_period, backtest_df):
        """
        Prepare grouped X-ray analysis for backtest results.
        
        Args:
            backtest_period: Backtest period in days
            backtest_df: Backtest dataframe
            
        Returns:
            DataFrame: Grouped X-ray analysis results
        """
        df_grouped = backtest_df.groupby("Date")
        self.user_passed_args.backtestdaysago = backtest_period
        df_xray = None
        group_counter = 0
        tasks_list = []
        
        for calc_for_date, df_group in df_grouped:
            group_counter += 1
            func_args = (df_group, self.user_passed_args, calc_for_date, f"Portfolio X-Ray | {calc_for_date} | {group_counter} of {len(df_grouped)}")
            task = PKTask(f"Portfolio X-Ray | {calc_for_date} | {group_counter} of {len(df_grouped)}",
                          long_running_fn=PortfolioXRay.performXRay,
                          long_running_fn_args=func_args)
            task.total = len(df_grouped)
            tasks_list.append(task)
            
        try:
            if 'RUNNER' not in os.environ.keys():
                PKScheduler.scheduleTasks(tasks_list, f"Portfolio X-Ray for ({len(df_grouped)})", showProgressBars=False, timeout=600)
            else:
                for task in tasks_list:
                    task.long_running_fn(*(task,))
                    
            for task in tasks_list:
                p_df = task.result
                
                if p_df is not None:
                    if df_xray is not None:
                        df_xray = pd.concat([df_xray, p_df.copy()], axis=0)
                    else:
                        df_xray = p_df.copy()
                        
            self.removed_unused_columns(None, backtest_df, ["Consol.", "Breakout", "RSI", "Pattern", "CCI"], userArgs=self.user_passed_args)
            df_xray = df_xray.replace(np.nan, "", regex=True)
            df_xray = PortfolioXRay.xRaySummary(df_xray)
            df_xray.loc[:, "Date"] = df_xray.loc[:, "Date"].apply(
                lambda x: x.replace("-", "/")
            )
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            pass
            
        return df_xray

    def finish_backtest_data_cleanup(self, backtest_df, df_xray):
        """
        Finish backtest data cleanup and preparation.
        
        Args:
            backtest_df: Backtest dataframe
            df_xray: X-ray analysis dataframe
            
        Returns:
            tuple: Summary dataframe, sorting flag, and sort keys
        """
        if df_xray is not None and len(df_xray) > 10:
            self.show_backtest_results(df_xray, sortKey="Date", optionalName="Insights")
            
        summary_df = backtestSummary(backtest_df)
        backtest_df.loc[:, "Date"] = backtest_df.loc[:, "Date"].apply(
            lambda x: x.replace("-", "/")
        )
        
        self.show_backtest_results(backtest_df)
        self.show_backtest_results(summary_df, optionalName="Summary")
        
        sorting = False if self.default_answer is not None else True
        tasks_list = []
        sort_keys = {
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
            "V": "volume",
            "M": "MA-Signal",
        }
        
        if self.config_manager.enablePortfolioCalculations:
            if 'RUNNER' not in os.environ.keys():
                task1 = PKTask("PortfolioLedger", long_running_fn=PortfolioCollection().getPortfoliosAsDataframe)
                task2 = PKTask("PortfolioLedgerSnapshots", long_running_fn=PortfolioCollection().getLedgerSummaryAsDataframe)
                tasks_list = [task1, task2]
                PKScheduler.scheduleTasks(tasks_list=tasks_list, label=f"Portfolio Calculations Report Export(Total={len(tasks_list)})", timeout=600)
            else:
                for task in tasks_list:
                    task.long_running_fn(*(task,))
                    
            for task in tasks_list:
                if task.result is not None:
                    self.show_backtest_results(task.result, sortKey=None, optionalName=task.taskName)
                    
        return summary_df, sorting, sort_keys

    def show_sorted_backtest_data(self, backtest_df, summary_df, sort_keys):
        """
        Show sorted backtest data with user interaction.
        
        Args:
            backtest_df: Backtest dataframe
            summary_df: Summary dataframe
            sort_keys: Sort keys dictionary
            
        Returns:
            bool: Whether sorting should continue
        """
        OutputControls().printOutput(
            colorText.FAIL
            + "  [+] Would you like to sort the results?"
            + colorText.END
        )
        
        OutputControls().printOutput(
            colorText.GREEN
            + "  [+] Press :\n   [+] s, v, t, m : sort by Stocks, Volume, Trend, MA-Signal\n   [+] d : sort by date\n   [+] 1,2,3...30 : sort by period\n   [+] n : Exit sorting\n"
            + colorText.END
        )
        
        if self.default_answer is None:
            choice = OutputControls().takeUserInput(
                colorText.FAIL + "  [+] Select option:"
            )
            OutputControls().printOutput(colorText.END, end="")
            
            if choice.upper() in sort_keys.keys():
                ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
                self.show_backtest_results(backtest_df, sort_keys[choice.upper()])
                self.show_backtest_results(summary_df, optionalName="Summary")
            else:
                sorting = False
        else:
            OutputControls().printOutput("Finished backtesting!")
            sorting = False
            
        return sorting

    def show_backtest_results(self, backtest_df, sort_key="Stock", optional_name="backtest_result", choices=None):
        """
        Show backtest results in formatted output.
        
        Args:
            backtest_df: Backtest dataframe
            sort_key: Sort key for results
            optional_name: Optional name for the report
            choices: Choices string for filename
        """
        pd.set_option("display.max_rows", 800)
        
        if backtest_df is None or backtest_df.empty or len(backtest_df) < 1:
            OutputControls().printOutput("Empty backtest dataframe encountered! Cannot generate the backtest report")
            return
            
        backtest_df.drop_duplicates(inplace=True)
        summary_text = f"Auto-generated in {round(self.elapsed_time,2)} sec. as of {PKDateUtilities.currentDateTime().strftime('%d-%m-%y %H:%M:%S IST')}\n{self.menu_choice_hierarchy.replace('Backtests','Growth of 10K' if optional_name=='Insights' else 'Backtests')}"
        last_summary_row = None
        
        if "Summary" not in optional_name:
            if sort_key is not None and len(sort_key) > 0:
                backtest_df.sort_values(by=[sort_key], ascending=False, inplace=True)
        else:
            last_row = backtest_df.iloc[-1, :]
            
            if last_row.iloc[0] == "SUMMARY":
                last_summary_row = pd.DataFrame(last_row).transpose()
                last_summary_row.set_index("Stock", inplace=True)
                last_summary_row = last_summary_row.iloc[:, last_summary_row.columns != "Stock"]
                
            if "Insights" in optional_name:
                summary_text = f"{summary_text}\nActual returns at a portfolio level with 1-stock each based on selected scan-parameters:"
            else:
                summary_text = f"{summary_text}\nOverall Summary of (correctness of) Strategy Prediction Positive outcomes:"
                
        tabulated_text = ""
        
        if backtest_df is not None and len(backtest_df) > 0:
            try:
                tabulated_text = colorText.miniTabulator().tabulate(
                    backtest_df,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                    showindex=False,
                    maxcolwidths=Utility.tools.getMaxColumnWidths(backtest_df)
                ).encode("utf-8").decode(STD_ENCODING)
            except ValueError:
                OutputControls().printOutput("ValueError! Going ahead without any column width restrictions!")
                tabulated_text = colorText.miniTabulator().tabulate(
                    backtest_df,
                    headers="keys",
                    tablefmt=colorText.No_Pad_GridFormat,
                    showindex=False,
                ).encode("utf-8").decode(STD_ENCODING)
                pass
                
        OutputControls().printOutput(colorText.FAIL + summary_text + colorText.END + "\n")
        OutputControls().printOutput(tabulated_text + "\n")
        
        choices, filename = self.get_backtest_report_filename(sort_key, optional_name, choices=choices)
        header_dict = {0: "<th></th>"}
        index = 1
        
        for col in backtest_df.columns:
            if col != "Stock":
                header_dict[index] = f"<th>{col}</th>"
                index += 1

        colored_text = backtest_df.to_html(index=False)
        summary_text = summary_text.replace("\n", "<br />")
        
        if "Summary" in optional_name:
            summary_text = f"{summary_text}<br /><input type='checkbox' id='chkActualNumbers' name='chkActualNumbers' value='0'><label for='chkActualNumbers'>Sort by actual numbers (Stocks + Date combinations of results. Higher the count, better the prediction reliability)</label><br>"
            
        colored_text = self.reformat_table(summary_text, header_dict, colored_text, sorting=True)
        filename = os.path.join(self.scan_output_directory(True), filename)
        
        try:
            os.remove(filename)
        except Exception:
            pass
        finally:
            colored_text = colored_text.encode('utf-8').decode(STD_ENCODING)
            
            with open(filename, "w") as f:
                f.write(colored_text)
                
            if "RUNNER" in os.environ.keys():
                Committer.execOSCommand(f"git add {filename} -f >/dev/null 2>&1")
                
        try:
            if self.config_manager.alwaysExportToExcel:
                excel_sheetname = filename.split(os.sep)[-1].replace("PKScreener_", "").replace(".html", "")
                PKAssetsManager.promptSaveResults(sheetName=excel_sheetname, df_save=backtest_df, defaultAnswer=self.user_passed_args.answerdefault, pastDate=None)
        except:
            pass
            
        if last_summary_row is not None:
            oneline_text = last_summary_row.to_html(header=False, index=False)
            oneline_text = self.reformat_table(
                summary_text, header_dict, oneline_text, sorting=False
            )
            oneline_summary_file = f"PKScreener_{choices}_OneLine_{optional_name}.html"
            oneline_summary_file = os.path.join(
                self.scan_output_directory(True), oneline_summary_file
            )
            
            try:
                os.remove(oneline_summary_file)
            except Exception:
                pass
            finally:
                oneline_text = f"{oneline_text}<td class='w'>{PKDateUtilities.currentDateTime().strftime('%Y/%m/%d')}</td><td class='w'>{round(self.elapsed_time,2)}</td>"
                
                with open(oneline_summary_file, "w") as f:
                    f.write(oneline_text)
                    
                if "RUNNER" in os.environ.keys():
                    Committer.execOSCommand(f"git add {oneline_summary_file} -f >/dev/null 2>&1")

    def scan_output_directory(self, backtest=False):
        """
        Get the scan output directory path.
        
        Args:
            backtest (bool): Whether for backtest results
            
        Returns:
            str: Output directory path
        """
        dir_name = 'actions-data-scan' if not backtest else "Backtest-Reports"
        output_folder = os.path.join(os.getcwd(), dir_name)
        
        if not os.path.isdir(output_folder):
            OutputControls().printOutput("Creating actions-data-scan directory now...")
            os.makedirs(os.path.dirname(os.path.join(os.getcwd(), f"{dir_name}{os.sep}")), exist_ok=True)
            
        return output_folder

    def get_backtest_report_filename(self, sort_key="Stock", optional_name="backtest_result", choices=None):
        """
        Get backtest report filename.
        
        Args:
            sort_key: Sort key for filename
            optional_name: Optional name for filename
            choices: Choices string for filename
            
        Returns:
            tuple: Choices string and filename
        """
        if choices is None:
            choices = PKScanRunner.getFormattedChoices(self.user_passed_args, self.selected_choice).strip()
            
        filename = f"PKScreener_{choices.strip()}_{optional_name.strip()}_{sort_key.strip() if sort_key is not None else 'Default'}Sorted.html"
        return choices.strip(), filename.strip()

    def reformat_table(self, summary_text, header_dict, colored_text, sorting=True):
        """
        Reformat table for HTML output.
        
        Args:
            summary_text: Summary text
            header_dict: Header dictionary
            colored_text: Colored text content
            sorting (bool): Whether to enable sorting
            
        Returns:
            str: Reformatted table HTML
        """
        if sorting:
            table_text = "<!DOCTYPE html><html><head><script type='application/javascript' src='https://pkjmesra.github.io/pkjmesra/pkscreener/classes/tableSorting.js' ></script><style type='text/css'>body, table {background-color: black; color: white;} table, th, td {border: 1px solid white;} th {cursor: pointer; color:white; text-decoration:underline;} .r {color:red;font-weight:bold;} .br {border-color:green;border-width:medium;} .w {color:white;font-weight:bold;} .g {color:lightgreen;font-weight:bold;} .y {color:yellow;} .bg {background-color:darkslategrey;} .bb {background-color:black;} input#searchReports { width: 220px; } table thead tr th { background-color: black; position: sticky; z-index: 100; top: 0; } </style></head><body><span style='color:white;' >"
            colored_text = colored_text.replace(
                "<table", f"{table_text}{summary_text}<br /><input type='text' id='searchReports' onkeyup='searchReportsByAny()' placeholder='Search for stock/scan reports..' title='Type in a name/ID'><table")
            colored_text = colored_text.replace("<table ", "<table id='resultsTable' ")
            colored_text = colored_text.replace('<tr style="text-align: right;">', '<tr style="text-align: right;" class="header">')
            
            for key in header_dict.keys():
                if key > 0:
                    colored_text = colored_text.replace(
                        header_dict[key], f"<th>{header_dict[key][4:]}"
                    )
                else:
                    colored_text = colored_text.replace(
                        header_dict[key], f"<th>Stock{header_dict[key][4:]}"
                    )
        else:
            colored_text = colored_text.replace('<table border="1" class="dataframe">', "")
            colored_text = colored_text.replace("<tbody>", "")
            colored_text = colored_text.replace("<tr>", "")
            colored_text = colored_text.replace("</tr>", "")
            colored_text = colored_text.replace("</tbody>", "")
            colored_text = colored_text.replace("</table>", "")
            
        colored_text = colored_text.replace(colorText.BOLD, "")
        colored_text = colored_text.replace(f"{colorText.GREEN}", "<span class='g'>")
        colored_text = colored_text.replace(f"{colorText.FAIL}", "<span class='r'>")
        colored_text = colored_text.replace(f"{colorText.WARN}", "<span class='y'>")
        colored_text = colored_text.replace(f"{colorText.WHITE}", "<span class='w'>")
        colored_text = colored_text.replace("<td><span class='w'>", "<td class='br'><span class='w'>")
        colored_text = colored_text.replace(colorText.END, "</span>")
        colored_text = colored_text.replace("\n", "")
        
        if sorting:
            colored_text = colored_text.replace("</table>", "</table></span></body></html>")
            
        return colored_text

    def tabulate_backtest_results(self, save_results, max_allowed=0, force=False):
        """
        Tabulate backtest results for display.
        
        Args:
            save_results: Results to save
            max_allowed: Maximum allowed results
            force (bool): Whether to force display
            
        Returns:
            tuple: Tabulated summary and detail text
        """
        if "PKDevTools_Default_Log_Level" not in os.environ.keys():
            if ("RUNNER" not in os.environ.keys()) or ("RUNNER" in os.environ.keys() and not force):
                return None, None
                
        if not self.config_manager.showPastStrategyData:
            return None, None
            
        tabulated_backtest_summary = ""
        tabulated_backtest_detail = ""
        summary_df, detail_df = self.get_summary_correctness_of_strategy(save_results)
        
        if summary_df is not None and len(summary_df) > 0:
            tabulated_backtest_summary = colorText.miniTabulator().tabulate(
                summary_df,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
                maxcolwidths=Utility.tools.getMaxColumnWidths(summary_df)
            ).encode("utf-8").decode(STD_ENCODING)
            
        if detail_df is not None and len(detail_df) > 0:
            if max_allowed != 0 and len(detail_df) > 2 * max_allowed:
                detail_df = detail_df.head(2 * max_allowed)
                
            tabulated_backtest_detail = colorText.miniTabulator().tabulate(
                detail_df,
                headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
                maxcolwidths=Utility.tools.getMaxColumnWidths(detail_df)
            ).encode("utf-8").decode(STD_ENCODING)
            
        if tabulated_backtest_summary != "":
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] For chosen scan, summary of correctness from past: [Example, 70% of (100) under 1-Pd, means out of 100 stocks that were in the scan result in the past, 70% of them gained next day.)"
                + colorText.END
            )
            OutputControls().printOutput(tabulated_backtest_summary)
            
        if tabulated_backtest_detail != "":
            OutputControls().printOutput(
                colorText.FAIL
                + "\n  [+] 1 to 30 period gain/loss % on respective date for matching stocks from earlier predictions:[Example, 5% under 1-P")