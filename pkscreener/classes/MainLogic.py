"""
MainLogic - Main execution logic for PKScreener

This module contains the core logic extracted from the main() function
in globals.py. It handles menu processing, scanning, and result handling.
"""

import os
import sys
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger

from pkscreener.classes import ConsoleUtility, Utility
from pkscreener.classes.PKAnalytics import PKAnalyticsService
from pkscreener.classes.MenuOptions import INDICES_MAP, PIPED_SCANNERS, PREDEFINED_SCAN_MENU_KEYS, PREDEFINED_SCAN_MENU_TEXTS


class MenuOptionHandler:
    """Handles individual menu option processing"""
    
    def __init__(self, global_state):
        """
        Initialize with a reference to global state.
        global_state should have access to: configManager, fetcher, m0, m1, m2, 
        userPassedArgs, selectedChoice, etc.
        """
        self.gs = global_state
    
    def get_launcher(self) -> str:
        """Get the launcher command for subprocess calls"""
        launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
        if launcher.endswith(".py\"") or launcher.endswith(".py"):
            launcher = f"python3.12 {launcher}"
        return launcher
    
    def handle_menu_m(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Handle Monitor menu option"""
        launcher = self.get_launcher()
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener in monitoring mode. "
            f"If it does not launch, please try with the following:{colorText.END}\n"
            f"{colorText.FAIL}{launcher} --systemlaunched -a Y -m 'X'{colorText.END}\n"
            f"{colorText.WARN}Press Ctrl + C to exit monitoring mode.{colorText.END}"
        )
        PKAnalyticsService().send_event("monitor_M")
        sleep(2)
        os.system(f"{launcher} --systemlaunched -a Y -m 'X'")
        return None, None
    
    def handle_menu_d(self, m0, m1, m2) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Handle Download menu option"""
        launcher = self.get_launcher()
        selectedMenu = m0.find("D")
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        m1.renderForMenu(selectedMenu)
        
        selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "D"
        OutputControls().printOutput(colorText.END, end="")
        
        if selDownloadOption.upper() == "D":
            return self._handle_download_daily(launcher)
        elif selDownloadOption.upper() == "I":
            return self._handle_download_intraday(launcher)
        elif selDownloadOption.upper() == "N":
            return self._handle_download_nse_indices(launcher, m1, m2)
        elif selDownloadOption.upper() == "S":
            return self._handle_download_sector_info(m1, m2)
        elif selDownloadOption.upper() == "M":
            PKAnalyticsService().send_event("D_M")
            return None, None
        
        return None, None
    
    def _handle_download_daily(self, launcher) -> Tuple[None, None]:
        """Handle daily download option"""
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener to Download daily OHLC data. "
            f"If it does not launch, please try with the following:{colorText.END}\n"
            f"{colorText.FAIL}{launcher} -a Y -e -d{colorText.END}\n"
            f"{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}"
        )
        PKAnalyticsService().send_event("D_D")
        sleep(2)
        os.system(f"{launcher} -a Y -e -d")
        return None, None
    
    def _handle_download_intraday(self, launcher) -> Tuple[None, None]:
        """Handle intraday download option"""
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener to Download intraday OHLC data. "
            f"If it does not launch, please try with the following:{colorText.END}\n"
            f"{colorText.FAIL}{launcher} -a Y -e -d -i 1m{colorText.END}\n"
            f"{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}"
        )
        PKAnalyticsService().send_event("D_I")
        sleep(2)
        os.system(f"{launcher} -a Y -e -d -i 1m")
        return None, None
    
    def _handle_download_nse_indices(self, launcher, m1, m2) -> Tuple[None, None]:
        """Handle NSE indices download option"""
        from PKNSETools.Nasdaq.PKNasdaqIndex import PKNasdaqIndexFetcher
        
        selectedMenu = m1.find("N")
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        m2.renderForMenu(selectedMenu)
        PKAnalyticsService().send_event("D_N")
        
        selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "12"
        OutputControls().printOutput(colorText.END, end="")
        
        filePrefix = "Download"
        if selDownloadOption.upper() in INDICES_MAP.keys():
            filePrefix = INDICES_MAP.get(selDownloadOption.upper()).replace(" ", "")
        
        filename = (
            f"PKS_Data_{filePrefix}_"
            + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
            + ".csv"
        )
        filePath = os.path.join(Archiver.get_user_indices_dir(), filename)
        PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
        
        if selDownloadOption.upper() == "15":
            nasdaq = PKNasdaqIndexFetcher(self.gs.configManager)
            _, nasdaq_df = nasdaq.fetchNasdaqIndexConstituents()
            try:
                nasdaq_df.to_csv(filePath)
            except Exception as e:
                OutputControls().printOutput(
                    f"{colorText.FAIL}We encountered an error. Please try again!{colorText.END}\n"
                    f"{colorText.WARN}{e}{colorText.END}"
                )
            OutputControls().printOutput(f"{colorText.GREEN}{filePrefix} Saved at: {filePath}{colorText.END}")
            input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")
            return None, None
        elif selDownloadOption.upper() == "M":
            return None, None
        else:
            fileContents = self.gs.fetcher.fetchFileFromHostServer(
                filePath=filePath, tickerOption=int(selDownloadOption), fileContents=""
            )
            if len(fileContents) > 0:
                OutputControls().printOutput(f"{colorText.GREEN}{filePrefix} Saved at: {filePath}{colorText.END}")
            else:
                OutputControls().printOutput(f"{colorText.FAIL}We encountered an error. Please try again!{colorText.END}")
            input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")
            return None, None
    
    def _handle_download_sector_info(self, m1, m2) -> Tuple[None, None]:
        """Handle sector info download option"""
        selectedMenu = m1.find("S")
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        m2.renderForMenu(selectedMenu, skip=["15"])
        
        selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "12"
        OutputControls().printOutput(colorText.END, end="")
        
        filePrefix = "Download"
        if selDownloadOption.upper() in INDICES_MAP.keys():
            filePrefix = INDICES_MAP.get(selDownloadOption.upper()).replace(" ", "")
        
        filename = (
            f"PKS_Data_{filePrefix}_"
            + PKDateUtilities.currentDateTime().strftime("%d-%m-%y_%H.%M.%S")
            + ".csv"
        )
        PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
        filePath = os.path.join(Archiver.get_user_reports_dir(), filename)
        
        if selDownloadOption.upper() == "M":
            return None, None
        
        indexOption = int(selDownloadOption)
        if indexOption > 0 and indexOption <= 14:
            shouldSuppress = not OutputControls().enableMultipleLineOutput
            with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                listStockCodes = self.gs.fetcher.fetchStockCodes(indexOption, stockCode=None)
            
            OutputControls().printOutput(f"{colorText.GREEN}Please be patient. It might take a while...{colorText.END}")
            
            from pkscreener.classes.PKDataService import PKDataService
            dataSvc = PKDataService()
            stockDictList, leftOutStocks = dataSvc.getSymbolsAndSectorInfo(
                self.gs.configManager, stockCodes=listStockCodes
            )
            
            if len(stockDictList) > 0:
                sector_df = pd.DataFrame(stockDictList)
                sector_df.to_csv(filePath)
                OutputControls().printOutput(
                    f"{colorText.GREEN}Sector/Industry info for {filePrefix}, saved at: {filePath}{colorText.END}"
                )
            else:
                OutputControls().printOutput(
                    f"{colorText.FAIL}We encountered an error. Please try again!{colorText.END}"
                )
            input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")
        
        return None, None
    
    def handle_menu_l(self) -> Tuple[None, None]:
        """Handle Log collection menu option"""
        launcher = self.get_launcher()
        PKAnalyticsService().send_event("L")
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener to collect logs. "
            f"If it does not launch, please try with the following:{colorText.END}\n"
            f"{colorText.FAIL}{launcher} -a Y -l{colorText.END}\n"
            f"{colorText.WARN}Press Ctrl + C to exit at any time.{colorText.END}"
        )
        sleep(2)
        os.system(f"{launcher} -a Y -l")
        return None, None
    
    def handle_menu_f(self, options) -> Optional[List[str]]:
        """Handle Fundamental menu option - returns list of stock codes"""
        PKAnalyticsService().send_event("F")
        
        shouldSuppress = not OutputControls().enableMultipleLineOutput
        listStockCodes = None
        
        userPassedArgs = self.gs.userPassedArgs
        if userPassedArgs is not None and userPassedArgs.options is not None:
            if len(userPassedArgs.options.split(":")) >= 3:
                stockOptions = userPassedArgs.options.split(":")
                stockOptions = userPassedArgs.options.split(":")[2 if len(stockOptions) <= 3 else 3]
                listStockCodes = stockOptions.replace(".", ",").split(",")
        
        if listStockCodes is None or len(listStockCodes) == 0:
            with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
                listStockCodes = self.gs.fetcher.fetchStockCodes(tickerOption=0, stockCode=None)
        
        ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
        return listStockCodes
    
    def handle_menu_p(self, options, m0, m1, m2, defaultAnswer, resultsContentsEncoded) -> Tuple[Any, ...]:
        """
        Handle Predefined scans menu option.
        Returns tuple of (should_continue, menuOption, indexOption, executeOption, listStockCodes)
        """
        launcher = self.get_launcher()
        userPassedArgs = self.gs.userPassedArgs
        selectedChoice = self.gs.selectedChoice
        configManager = self.gs.configManager
        
        predefinedOption = None
        selPredefinedOption = None
        selIndexOption = None
        
        if len(options) >= 3:
            predefinedOption = str(options[1]) if str(options[1]).isnumeric() else '1'
            selPredefinedOption = str(options[2]) if str(options[2]).isnumeric() else '1'
            if len(options) >= 4:
                selIndexOption = str(options[3]) if str(options[3]).isnumeric() else '12'
        
        selectedChoice["0"] = "P"
        
        selectedMenu = m0.find("P")
        m1.renderForMenu(selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
        
        needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
        pastDate = ""
        if needsCalc:
            pastDate = (
                f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}"
                f"{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago))}"
                f"{colorText.END} ]\n"
            )
        
        if predefinedOption is None:
            predefinedOption = OutputControls().takeUserInput(colorText.FAIL + f"{pastDate}  [+] Select option: ") or "1"
        OutputControls().printOutput(colorText.END, end="")
        
        if predefinedOption not in ["1", "2", "3", "4"]:
            return (False, None, None, None, None)
        
        selectedChoice["1"] = predefinedOption
        
        if predefinedOption in ["1", "4"]:
            return self._handle_predefined_scan(
                predefinedOption, selPredefinedOption, selIndexOption,
                pastDate, launcher, m1, m2, defaultAnswer, resultsContentsEncoded
            )
        elif predefinedOption == "2":
            # User chose custom - switch to X menu
            return (True, "X", None, None, None)
        elif predefinedOption == "3":
            if userPassedArgs.pipedmenus is not None:
                # Will be handled by addOrRunPipedMenus
                return (False, "P", None, None, None)
        
        return (False, None, None, None, None)
    
    def _handle_predefined_scan(self, predefinedOption, selPredefinedOption, selIndexOption,
                                 pastDate, launcher, m1, m2, defaultAnswer, resultsContentsEncoded):
        """Handle predefined scan options 1 and 4"""
        userPassedArgs = self.gs.userPassedArgs
        selectedChoice = self.gs.selectedChoice
        configManager = self.gs.configManager
        listStockCodes = self.gs.listStockCodes
        
        selectedMenu = m1.find(predefinedOption)
        m2.renderForMenu(selectedMenu=selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
        
        if selPredefinedOption is None:
            selPredefinedOption = OutputControls().takeUserInput(colorText.FAIL + f"{pastDate}  [+] Select option: ") or "1"
        OutputControls().printOutput(colorText.END, end="")
        
        if selPredefinedOption not in PREDEFINED_SCAN_MENU_KEYS:
            return (False, None, None, None, None)
        
        scannerOption = PIPED_SCANNERS[selPredefinedOption]
        
        if predefinedOption == "4":  # Watchlist
            scannerOption = scannerOption.replace("-o 'X:12:", "-o 'X:W:")
        elif predefinedOption == "1":  # Predefined
            if selIndexOption is None and (userPassedArgs is None or userPassedArgs.answerdefault is None):
                from pkscreener.classes.MenuOptions import m0 as menu0
                m1.renderForMenu(menu0.find(key="X"), skip=["W", "N", "E", "S", "Z"],
                               asList=(userPassedArgs is not None and userPassedArgs.options is not None))
                selIndexOption = OutputControls().takeUserInput(colorText.FAIL + f"{pastDate}  [+] Select option: ") or str(configManager.defaultIndex)
                if str(selIndexOption).upper() == "M":
                    return (False, None, None, None, None)
            if selIndexOption is not None:
                scannerOption = scannerOption.replace("-o 'X:12:", f"-o 'X:{selIndexOption}:")
        
        if userPassedArgs is not None:
            userPassedArgs.usertag = PREDEFINED_SCAN_MENU_TEXTS[int(selPredefinedOption) - 1]
        
        selectedChoice["2"] = selPredefinedOption
        
        # Build and execute scanner command
        scannerOptionQuoted = scannerOption.replace("'", '"')
        if listStockCodes is not None and len(listStockCodes) > 0:
            scannerOptionQuoted = scannerOptionQuoted.replace(":12:", ":0:")
            scannerOptionQuotedParts = scannerOptionQuoted.split(">|")
            scannerOptionQuotedParts[0] = f"{scannerOptionQuotedParts[0]}{'' if scannerOptionQuotedParts[0].endswith(':') else ':'}{','.join(listStockCodes)}"
            scannerOptionQuoted = ">|".join(scannerOptionQuotedParts)
        
        requestingUser = f" -u {userPassedArgs.user}" if userPassedArgs.user is not None else ""
        enableLog = " -l" if userPassedArgs.log else ""
        enableTelegramMode = " --telegram" if userPassedArgs is not None and userPassedArgs.telegram else ""
        backtestParam = f" --backtestdaysago {userPassedArgs.backtestdaysago}" if userPassedArgs.backtestdaysago else ""
        stockListParam = f" --stocklist {userPassedArgs.stocklist}" if userPassedArgs.stocklist else ""
        slicewindowParam = f" --slicewindow {userPassedArgs.slicewindow}" if userPassedArgs.slicewindow else ""
        fnameParam = f" --fname {resultsContentsEncoded}" if resultsContentsEncoded else ""
        
        if userPassedArgs.monitor and "-e -o" in scannerOptionQuoted:
            scannerOptionQuoted = scannerOptionQuoted.replace("-e -o", "-m")
        
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener with piped scanners. "
            f"If it does not launch, please try with the following:{colorText.END}\n"
            f"{colorText.FAIL}{launcher} {scannerOptionQuoted}{requestingUser}{enableLog}"
            f"{backtestParam}{enableTelegramMode}{stockListParam}{slicewindowParam}{fnameParam}{colorText.END}"
        )
        sleep(2)
        os.system(
            f"{launcher} {scannerOptionQuoted}{requestingUser}{enableLog}"
            f"{backtestParam}{enableTelegramMode}{stockListParam}{slicewindowParam}{fnameParam}"
        )
        
        OutputControls().printOutput(
            f"{colorText.GREEN}  [+] Finished running all piped scanners!{colorText.END}"
        )
        
        if defaultAnswer is None:
            OutputControls().takeUserInput("Press <Enter> to continue...")
        
        ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
        return (False, None, None, None, None)


class GlobalStateProxy:
    """Proxy class to provide access to global state"""
    
    def __init__(self):
        self.configManager = None
        self.fetcher = None
        self.userPassedArgs = None
        self.selectedChoice = {"0": "", "1": "", "2": "", "3": "", "4": ""}
        self.listStockCodes = None
    
    def update_from_globals(self, globals_module):
        """Update state from globals module"""
        self.configManager = globals_module.configManager
        self.fetcher = globals_module.fetcher
        self.userPassedArgs = globals_module.userPassedArgs
        self.selectedChoice = globals_module.selectedChoice
        self.listStockCodes = getattr(globals_module, 'listStockCodes', None)


def create_menu_handler(globals_module) -> MenuOptionHandler:
    """Factory function to create MenuOptionHandler with global state"""
    gs = GlobalStateProxy()
    gs.update_from_globals(globals_module)
    return MenuOptionHandler(gs)


def handle_mdilf_menus(
    menuOption: str,
    m0, m1, m2,
    configManager,
    fetcher,
    userPassedArgs,
    selectedChoice: Dict[str, str],
    listStockCodes: Optional[List[str]]
) -> Tuple[bool, Optional[List[str]], Optional[int], Optional[int]]:
    """
    Handle M, D, I, L, F menu options.
    
    Returns:
        Tuple of (should_return_early, listStockCodes, indexOption, executeOption)
        If should_return_early is True, caller should return None, None
    """
    launcher = _get_launcher()
    
    if menuOption == "M":
        _handle_monitor_menu(launcher)
        return (True, listStockCodes, None, None)
    
    elif menuOption == "D":
        result = _handle_download_menu(launcher, m0, m1, m2, configManager, fetcher)
        return (result, listStockCodes, None, None)
    
    elif menuOption == "L":
        _handle_log_menu(launcher)
        return (True, listStockCodes, None, None)
    
    elif menuOption == "F":
        listStockCodes = _handle_fundamental_menu(fetcher, userPassedArgs, listStockCodes, selectedChoice)
        return (False, listStockCodes, 0, None)
    
    else:
        ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
        return (True, listStockCodes, None, None)


def _get_launcher() -> str:
    """Get launcher command"""
    launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
    if launcher.endswith(".py\"") or launcher.endswith(".py"):
        launcher = f"python3.12 {launcher}"
    return launcher


def _handle_monitor_menu(launcher: str):
    """Handle Monitor menu"""
    OutputControls().printOutput(
        f"{colorText.GREEN}Launching PKScreener in monitoring mode. "
        f"If it does not launch, please try with the following:{colorText.END}\n"
        f"{colorText.FAIL}{launcher} --systemlaunched -a Y -m 'X'{colorText.END}\n"
        f"{colorText.WARN}Press Ctrl + C to exit monitoring mode.{colorText.END}"
    )
    PKAnalyticsService().send_event("monitor_M")
    sleep(2)
    os.system(f"{launcher} --systemlaunched -a Y -m 'X'")


def _handle_download_menu(launcher, m0, m1, m2, configManager, fetcher) -> bool:
    """
    Handle Download menu.
    Returns True if caller should return early.
    """
    from PKNSETools.Nasdaq.PKNasdaqIndex import PKNasdaqIndexFetcher
    
    selectedMenu = m0.find("D")
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    m1.renderForMenu(selectedMenu)
    selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "D"
    OutputControls().printOutput(colorText.END, end="")
    
    if selDownloadOption.upper() == "D":
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener to Download daily OHLC data.{colorText.END}\n"
            f"{colorText.FAIL}{launcher} -a Y -e -d{colorText.END}"
        )
        PKAnalyticsService().send_event("D_D")
        sleep(2)
        os.system(f"{launcher} -a Y -e -d")
        return True
    
    elif selDownloadOption.upper() == "I":
        OutputControls().printOutput(
            f"{colorText.GREEN}Launching PKScreener to Download intraday OHLC data.{colorText.END}\n"
            f"{colorText.FAIL}{launcher} -a Y -e -d -i 1m{colorText.END}"
        )
        PKAnalyticsService().send_event("D_I")
        sleep(2)
        os.system(f"{launcher} -a Y -e -d -i 1m")
        return True
    
    elif selDownloadOption.upper() == "N":
        return _handle_download_nse_indices(launcher, m1, m2, configManager, fetcher)
    
    elif selDownloadOption.upper() == "S":
        return _handle_download_sector_info(m1, m2, configManager, fetcher)
    
    elif selDownloadOption.upper() == "M":
        PKAnalyticsService().send_event("D_M")
        return True
    
    return True


def _handle_download_nse_indices(launcher, m1, m2, configManager, fetcher) -> bool:
    """Handle NSE indices download"""
    from PKNSETools.Nasdaq.PKNasdaqIndex import PKNasdaqIndexFetcher
    
    selectedMenu = m1.find("N")
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    m2.renderForMenu(selectedMenu)
    PKAnalyticsService().send_event("D_N")
    selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "12"
    OutputControls().printOutput(colorText.END, end="")
    
    filePrefix = "Download"
    if selDownloadOption.upper() in INDICES_MAP.keys():
        filePrefix = INDICES_MAP.get(selDownloadOption.upper()).replace(" ", "")
    
    filename = f"PKS_Data_{filePrefix}_{PKDateUtilities.currentDateTime().strftime('%d-%m-%y_%H.%M.%S')}.csv"
    filePath = os.path.join(Archiver.get_user_indices_dir(), filename)
    PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
    
    if selDownloadOption.upper() == "15":
        nasdaq = PKNasdaqIndexFetcher(configManager)
        _, nasdaq_df = nasdaq.fetchNasdaqIndexConstituents()
        try:
            nasdaq_df.to_csv(filePath)
        except Exception as e:
            OutputControls().printOutput(f"{colorText.FAIL}Error: {e}{colorText.END}")
        OutputControls().printOutput(f"{colorText.GREEN}{filePrefix} Saved at: {filePath}{colorText.END}")
        input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")
        return True
    elif selDownloadOption.upper() == "M":
        return True
    else:
        fileContents = fetcher.fetchFileFromHostServer(filePath=filePath, tickerOption=int(selDownloadOption), fileContents="")
        if len(fileContents) > 0:
            OutputControls().printOutput(f"{colorText.GREEN}{filePrefix} Saved at: {filePath}{colorText.END}")
        else:
            OutputControls().printOutput(f"{colorText.FAIL}Error occurred. Please try again!{colorText.END}")
        input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")
        return True


def _handle_download_sector_info(m1, m2, configManager, fetcher) -> bool:
    """Handle sector info download"""
    selectedMenu = m1.find("S")
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    m2.renderForMenu(selectedMenu, skip=["15"])
    selDownloadOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "12"
    OutputControls().printOutput(colorText.END, end="")
    
    filePrefix = "Download"
    if selDownloadOption.upper() in INDICES_MAP.keys():
        filePrefix = INDICES_MAP.get(selDownloadOption.upper()).replace(" ", "")
    
    filename = f"PKS_Data_{filePrefix}_{PKDateUtilities.currentDateTime().strftime('%d-%m-%y_%H.%M.%S')}.csv"
    PKAnalyticsService().send_event(f"D_{selDownloadOption.upper()}")
    filePath = os.path.join(Archiver.get_user_reports_dir(), filename)
    
    if selDownloadOption.upper() == "M":
        return True
    
    indexOption = int(selDownloadOption)
    if indexOption > 0 and indexOption <= 14:
        shouldSuppress = not OutputControls().enableMultipleLineOutput
        with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
            listStockCodes = fetcher.fetchStockCodes(indexOption, stockCode=None)
        OutputControls().printOutput(f"{colorText.GREEN}Please be patient...{colorText.END}")
        from pkscreener.classes.PKDataService import PKDataService
        dataSvc = PKDataService()
        stockDictList, leftOutStocks = dataSvc.getSymbolsAndSectorInfo(configManager, stockCodes=listStockCodes)
        if len(stockDictList) > 0:
            sector_df = pd.DataFrame(stockDictList)
            sector_df.to_csv(filePath)
            OutputControls().printOutput(f"{colorText.GREEN}Saved at: {filePath}{colorText.END}")
        else:
            OutputControls().printOutput(f"{colorText.FAIL}Error occurred.{colorText.END}")
        input(f"{colorText.GREEN}Press any key to continue...{colorText.END}")
    
    return True


def _handle_log_menu(launcher: str):
    """Handle Log menu"""
    PKAnalyticsService().send_event("L")
    OutputControls().printOutput(
        f"{colorText.GREEN}Launching PKScreener to collect logs.{colorText.END}\n"
        f"{colorText.FAIL}{launcher} -a Y -l{colorText.END}"
    )
    sleep(2)
    os.system(f"{launcher} -a Y -l")


def _handle_fundamental_menu(
    fetcher,
    userPassedArgs,
    listStockCodes: Optional[List[str]],
    selectedChoice: Dict[str, str]
) -> List[str]:
    """Handle Fundamental menu, returns listStockCodes"""
    PKAnalyticsService().send_event("F")
    selectedChoice["0"] = "F"
    selectedChoice["1"] = "0"
    
    shouldSuppress = not OutputControls().enableMultipleLineOutput
    
    if userPassedArgs is not None and userPassedArgs.options is not None:
        if len(userPassedArgs.options.split(":")) >= 3:
            stockOptions = userPassedArgs.options.split(":")
            stockOptions = userPassedArgs.options.split(":")[2 if len(stockOptions) <= 3 else 3]
            listStockCodes = stockOptions.replace(".", ",").split(",")
    
    if listStockCodes is None or len(listStockCodes) == 0:
        with SuppressOutput(suppress_stderr=shouldSuppress, suppress_stdout=shouldSuppress):
            listStockCodes = fetcher.fetchStockCodes(tickerOption=0, stockCode=None)
    
    ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
    return listStockCodes


def handle_predefined_menu(
    options: List[str],
    m0, m1, m2,
    configManager,
    userPassedArgs,
    selectedChoice: Dict[str, str],
    listStockCodes: Optional[List[str]],
    defaultAnswer,
    resultsContentsEncoded,
    update_hierarchy_cb,
    add_piped_menus_cb
) -> Tuple[bool, Optional[str], Optional[List[str]]]:
    """
    Handle Predefined (P) menu.
    
    Returns:
        Tuple of (should_return_early, new_menu_option, listStockCodes)
    """
    predefinedOption = None
    selPredefinedOption = None
    selIndexOption = None
    
    if len(options) >= 3:
        predefinedOption = str(options[1]) if str(options[1]).isnumeric() else '1'
        selPredefinedOption = str(options[2]) if str(options[2]).isnumeric() else '1'
        if len(options) >= 4:
            selIndexOption = str(options[3]) if str(options[3]).isnumeric() else '12'
    
    selectedChoice["0"] = "P"
    update_hierarchy_cb()
    
    selectedMenu = m0.find("P")
    m1.renderForMenu(selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    
    needsCalc = userPassedArgs is not None and userPassedArgs.backtestdaysago is not None
    pastDate = ""
    if needsCalc:
        pastDate = (
            f"  [+] [ Running in Quick Backtest Mode for {colorText.WARN}"
            f"{PKDateUtilities.nthPastTradingDateStringFromFutureDate(int(userPassedArgs.backtestdaysago))}"
            f"{colorText.END} ]\n"
        )
    
    if predefinedOption is None:
        predefinedOption = OutputControls().takeUserInput(colorText.FAIL + f"{pastDate}  [+] Select option: ") or "1"
    OutputControls().printOutput(colorText.END, end="")
    
    if predefinedOption not in ["1", "2", "3", "4"]:
        return (True, None, listStockCodes)
    
    selectedChoice["1"] = predefinedOption
    update_hierarchy_cb()
    
    if predefinedOption in ["1", "4"]:
        return _handle_predefined_option_1_4(
            predefinedOption, selPredefinedOption, selIndexOption, pastDate,
            m0, m1, m2, configManager, userPassedArgs, selectedChoice,
            listStockCodes, defaultAnswer, resultsContentsEncoded,
            update_hierarchy_cb, add_piped_menus_cb
        )
    elif predefinedOption == "2":
        # User chose custom - switch to X menu
        if userPassedArgs.pipedmenus is None:
            userPassedArgs.pipedmenus = ""
        return (False, "X", listStockCodes)
    elif predefinedOption == "3":
        if userPassedArgs.pipedmenus is not None:
            return (True, None, listStockCodes)  # Will call addOrRunPipedMenus in caller
    
    return (False, None, listStockCodes)


def _handle_predefined_option_1_4(
    predefinedOption, selPredefinedOption, selIndexOption, pastDate,
    m0, m1, m2, configManager, userPassedArgs, selectedChoice,
    listStockCodes, defaultAnswer, resultsContentsEncoded,
    update_hierarchy_cb, add_piped_menus_cb
) -> Tuple[bool, Optional[str], Optional[List[str]]]:
    """Handle predefined options 1 and 4"""
    selectedMenu = m1.find(predefinedOption)
    m2.renderForMenu(selectedMenu=selectedMenu, asList=(userPassedArgs is not None and userPassedArgs.options is not None))
    
    if selPredefinedOption is None:
        selPredefinedOption = OutputControls().takeUserInput(colorText.FAIL + f"{pastDate}  [+] Select option: ") or "1"
    OutputControls().printOutput(colorText.END, end="")
    
    if selPredefinedOption not in PREDEFINED_SCAN_MENU_KEYS:
        return (True, None, listStockCodes)
    
    scannerOption = PIPED_SCANNERS[selPredefinedOption]
    
    if predefinedOption == "4":  # Watchlist
        scannerOption = scannerOption.replace("-o 'X:12:", "-o 'X:W:")
    elif predefinedOption == "1":  # Predefined
        if selIndexOption is None and (userPassedArgs is None or userPassedArgs.answerdefault is None):
            m1.renderForMenu(m0.find(key="X"), skip=["W", "N", "E", "S", "Z"],
                           asList=(userPassedArgs is not None and userPassedArgs.options is not None))
            selIndexOption = OutputControls().takeUserInput(colorText.FAIL + f"{pastDate}  [+] Select option: ") or str(configManager.defaultIndex)
            if str(selIndexOption).upper() == "M":
                return (True, None, listStockCodes)
        if selIndexOption is not None:
            scannerOption = scannerOption.replace("-o 'X:12:", f"-o 'X:{selIndexOption}:")
    
    if userPassedArgs is not None:
        userPassedArgs.usertag = PREDEFINED_SCAN_MENU_TEXTS[int(selPredefinedOption) - 1]
    
    selectedChoice["2"] = selPredefinedOption
    update_hierarchy_cb()
    
    if userPassedArgs.pipedmenus is not None:
        chosenOptions = scannerOption.split("-o ")[1]
        userPassedArgs.options = chosenOptions.replace("'", "")
        return (True, None, listStockCodes)  # Will call addOrRunPipedMenus
    
    # Build launcher command
    launcher = _get_launcher()
    scannerOptionQuoted = scannerOption.replace("'", '"')
    
    if listStockCodes is not None and len(listStockCodes) > 0:
        scannerOptionQuoted = scannerOptionQuoted.replace(":12:", ":0:")
        scannerOptionQuotedParts = scannerOptionQuoted.split(">|")
        scannerOptionQuotedParts[0] = (
            f"{scannerOptionQuotedParts[0]}"
            f"{'' if scannerOptionQuotedParts[0].endswith(':') else ':'}"
            f"{','.join(listStockCodes)}"
        )
        scannerOptionQuoted = ">|".join(scannerOptionQuotedParts)
    
    # Check intraday config
    if configManager.isIntradayConfig() and userPassedArgs is not None and userPassedArgs.answerdefault is None:
        shouldUseIntraday = OutputControls().takeUserInput(
            "  [+] Use Intraday config candles? [Y/N] [Default: N]: ",
            enableUserInput=True, defaultInput="N"
        )
        if shouldUseIntraday is not None and "y" in shouldUseIntraday.lower():
            scannerOptionQuotedParts = scannerOptionQuoted.split(">|")
            updatedScannerParts = []
            for quotedPart in scannerOptionQuotedParts:
                lastPartQuoted = quotedPart.split(":")
                if "i" not in lastPartQuoted[-1] and "i" not in lastPartQuoted[-2]:
                    if ':"' not in quotedPart:
                        updatedScannerParts.append(f"{quotedPart}i {configManager.duration}")
                    else:
                        updatedScannerParts.append(quotedPart.replace(':"', f':i {configManager.duration}"'))
                else:
                    updatedScannerParts.append(quotedPart)
            if updatedScannerParts:
                scannerOptionQuoted = ">|".join(updatedScannerParts)
    
    # Build params
    requestingUser = f" -u {userPassedArgs.user}" if userPassedArgs.user is not None else ""
    enableLog = " -l" if userPassedArgs.log else ""
    enableTelegramMode = " --telegram" if userPassedArgs is not None and userPassedArgs.telegram else ""
    backtestParam = f" --backtestdaysago {userPassedArgs.backtestdaysago}" if userPassedArgs.backtestdaysago else ""
    stockListParam = f" --stocklist {userPassedArgs.stocklist}" if userPassedArgs.stocklist else ""
    slicewindowParam = f" --slicewindow {userPassedArgs.slicewindow}" if userPassedArgs.slicewindow else ""
    fnameParam = f" --fname {resultsContentsEncoded}" if resultsContentsEncoded else ""
    
    if userPassedArgs.monitor and "-e -o" in scannerOptionQuoted:
        scannerOptionQuoted = scannerOptionQuoted.replace("-e -o", "-m")
    
    OutputControls().printOutput(
        f"{colorText.GREEN}Launching PKScreener with piped scanners.{colorText.END}\n"
        f"{colorText.FAIL}{launcher} {scannerOptionQuoted}{requestingUser}{enableLog}"
        f"{backtestParam}{enableTelegramMode}{stockListParam}{slicewindowParam}{fnameParam}{colorText.END}"
    )
    sleep(2)
    os.system(
        f"{launcher} {scannerOptionQuoted}{requestingUser}{enableLog}"
        f"{backtestParam}{enableTelegramMode}{stockListParam}{slicewindowParam}{fnameParam}"
    )
    
    OutputControls().printOutput(f"{colorText.GREEN}  [+] Finished running all piped scanners!{colorText.END}")
    
    if defaultAnswer is None:
        OutputControls().takeUserInput("Press <Enter> to continue...")
    
    ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
    return (True, None, listStockCodes)


def handle_backtest_menu(
    options: List[str],
    menuOption: str,
    indexOption,
    executeOption,
    configManager,
    take_backtest_inputs_cb
) -> Tuple[Any, Any, int]:
    """
    Handle B/G (Backtest) menu.
    Returns (indexOption, executeOption, backtestPeriod)
    """
    backtestPeriod = 0
    
    if len(options) >= 2:
        if str(indexOption).isnumeric():
            backtestPeriod = int(indexOption)
        if len(options) >= 4:
            indexOption = executeOption
            executeOption = options[3]
        del options[1]  # Delete the backtestperiod from options
    
    indexOption, executeOption, backtestPeriod = take_backtest_inputs_cb(
        str(menuOption).upper(), indexOption, executeOption, backtestPeriod
    )
    backtestPeriod = backtestPeriod * configManager.backtestPeriodFactor
    
    return indexOption, executeOption, backtestPeriod


def handle_strategy_menu(
    options: List[str],
    m0, m1,
    defaultAnswer,
    strategy_filter: List[str],
    get_scanner_choices_cb,
    testBuild: bool,
    testing: bool,
    downloadOnly: bool,
    startupoptions,
    indexOption,
    executeOption,
    user
) -> Tuple[bool, Optional[str], Any, Any, Dict[str, str]]:
    """
    Handle S (Strategy) menu.
    Returns (should_return_early, menuOption, indexOption, executeOption, selectedChoice)
    """
    from pkscreener.classes import PortfolioXRay, Utility
    from pkscreener.classes.Utility import STD_ENCODING
    
    userOption = None
    if len(options) >= 2:
        userOption = options[1]
    
    if defaultAnswer is None:
        selectedMenu = m0.find("S")
        m1.strategyNames = PortfolioXRay.strategyNames()
        m1.renderForMenu(selectedMenu=selectedMenu)
        try:
            userOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ")
            OutputControls().printOutput(colorText.END, end="")
            if userOption == "":
                userOption = "37"  # NoFilter
            elif userOption == "38":
                userOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Enter Exact Pattern name:")
                OutputControls().printOutput(colorText.END, end="")
                if userOption == "":
                    userOption = "37"  # NoFilter
                else:
                    strategy_filter.append(f"[P]{userOption}")
                    userOption = "38"
        except EOFError:
            userOption = "37"  # NoFilter
        except Exception as e:
            default_logger().debug(e, exc_info=True)
    
    userOption = userOption.upper() if userOption else "37"
    
    if userOption == "M":
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        return (True, None, None, None, {})
    elif userOption == "Z":
        return (True, None, None, None, {})
    
    if userOption == "S":
        # Show summary
        OutputControls().printOutput(
            f"{colorText.GREEN}  [+] Collecting all metrics for summarising...{colorText.END}"
        )
        savedValue = getattr(PortfolioXRay.configManager, 'showPastStrategyData', False) if hasattr(PortfolioXRay, 'configManager') else False
        df_all = PortfolioXRay.summariseAllStrategies()
        if df_all is not None and len(df_all) > 0:
            tabulated = colorText.miniTabulator().tabulate(
                df_all, headers="keys",
                tablefmt=colorText.No_Pad_GridFormat,
                showindex=False,
                maxcolwidths=Utility.tools.getMaxColumnWidths(df_all)
            ).encode("utf-8").decode(STD_ENCODING)
            OutputControls().printOutput(tabulated)
        else:
            OutputControls().printOutput("[!] Nothing to show here yet. Check back later.")
        
        if defaultAnswer is None:
            OutputControls().takeUserInput("Press <Enter> to continue...")
        return (True, None, None, None, {})
    else:
        userOptions = userOption.split(",")
        for usrOption in userOptions:
            strategy_filter.append(m1.find(usrOption).menuText.strip())
        
        menuOption, indexOption, executeOption, selectedChoice = get_scanner_choices_cb(
            testBuild or testing, downloadOnly, startupoptions,
            menuOption="X", indexOption=indexOption, executeOption=executeOption,
            defaultAnswer=defaultAnswer, user=user
        )
        return (False, "X", indexOption, executeOption, selectedChoice)


def handle_secondary_menu_choices_impl(
    menuOption: str,
    m0, m1, m2,
    configManager,
    userPassedArgs,
    resultsContentsEncoded,
    testing: bool = False,
    defaultAnswer = None,
    user = None,
    show_config_info_cb = None,
    show_help_info_cb = None,
    toggle_config_cb = None,
    send_message_cb = None
) -> Optional[Tuple[None, None]]:
    """
    Handle secondary menu choices (H, U, T, E, Y).
    Returns None to continue or (None, None) to exit.
    """
    import pkscreener.classes.ConfigManager as ConfigManager
    from pkscreener.classes.OtaUpdater import OTAUpdater
    from pkscreener.classes import VERSION
    from PKDevTools.classes import Archiver
    
    if menuOption == "H":
        if show_help_info_cb:
            show_help_info_cb(defaultAnswer, user)
    
    elif menuOption == "U":
        OTAUpdater.checkForUpdate(VERSION, skipDownload=testing)
        if defaultAnswer is None:
            OutputControls().takeUserInput("Press <Enter> to continue...")
    
    elif menuOption == "T":
        return _handle_period_menu(
            m0, m1, m2, configManager, userPassedArgs, resultsContentsEncoded,
            defaultAnswer, toggle_config_cb
        )
    
    elif menuOption == "E":
        configManager.setConfig(ConfigManager.parser)
    
    elif menuOption == "Y":
        if show_config_info_cb:
            show_config_info_cb(defaultAnswer, user)
    
    return None


def _handle_period_menu(
    m0, m1, m2, configManager, userPassedArgs, resultsContentsEncoded,
    defaultAnswer, toggle_config_cb
) -> Optional[Tuple[None, None]]:
    """Handle T (Toggle Period) menu"""
    import pkscreener.classes.ConfigManager as ConfigManager
    from PKDevTools.classes import Archiver
    
    if userPassedArgs is None or userPassedArgs.options is None:
        selectedMenu = m0.find("T")
        m1.renderForMenu(selectedMenu=selectedMenu)
        periodOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or (
            'L' if configManager.period == '1y' else 'S'
        )
        OutputControls().printOutput(colorText.END, end="")
        
        if periodOption is None or periodOption.upper() not in ["L", "S", "B"]:
            return None
        
        ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
        
        if periodOption.upper() in ["L", "S"]:
            return _handle_long_short_period(
                m1, m2, configManager, periodOption, toggle_config_cb
            )
        elif periodOption.upper() == "B":
            return _handle_backtest_period(
                configManager, userPassedArgs, resultsContentsEncoded
            )
    
    elif userPassedArgs is not None and userPassedArgs.options is not None:
        options = userPassedArgs.options.split(":")
        selectedMenu = m0.find(options[0])
        m1.renderForMenu(selectedMenu=selectedMenu, asList=True)
        selectedMenu = m1.find(options[1])
        m2.renderForMenu(selectedMenu=selectedMenu, asList=True)
        
        if options[2] in ["1", "2", "3", "4"]:
            selectedMenu = m2.find(options[2])
            period_durations = selectedMenu.menuText.split("(")[1].split(")")[0].split(", ")
            configManager.period = period_durations[0]
            configManager.duration = period_durations[1]
            import pkscreener.classes.ConfigManager as CM
            configManager.setConfig(CM.parser, default=True, showFileCreatedText=False)
        else:
            if toggle_config_cb:
                toggle_config_cb()
    else:
        if toggle_config_cb:
            toggle_config_cb()
    
    return None


def _handle_long_short_period(m1, m2, configManager, periodOption, toggle_config_cb):
    """Handle Long/Short period selection"""
    import pkscreener.classes.ConfigManager as ConfigManager
    from PKDevTools.classes import Archiver
    
    selectedMenu = m1.find(periodOption)
    m2.renderForMenu(selectedMenu=selectedMenu)
    durationOption = OutputControls().takeUserInput(colorText.FAIL + "  [+] Select option: ") or "1"
    OutputControls().printOutput(colorText.END, end="")
    
    if durationOption is None or durationOption.upper() not in ["1", "2", "3", "4", "5"]:
        return None
    
    ConsoleUtility.PKConsoleTools.clearScreen(forceTop=True)
    
    if durationOption.upper() in ["1", "2", "3", "4"]:
        selectedMenu = m2.find(durationOption)
        period_durations = selectedMenu.menuText.split("(")[1].split(")")[0].split(", ")
        configManager.period = period_durations[0]
        configManager.duration = period_durations[1]
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        configManager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(), pattern="*stock_data_*.pkl*")
    elif durationOption.upper() == "5":
        configManager.setConfig(ConfigManager.parser, default=False, showFileCreatedText=True)
        configManager.deleteFileWithPattern(rootDir=Archiver.get_user_data_dir(), pattern="*stock_data_*.pkl*")
    
    return None


def _handle_backtest_period(configManager, userPassedArgs, resultsContentsEncoded):
    """Handle Backtest period selection"""
    last_trading_date = PKDateUtilities.nthPastTradingDateStringFromFutureDate(
        n=(22 if configManager.period == '1y' else 15)
    )
    backtest_days_ago = OutputControls().takeUserInput(
        f"{colorText.FAIL}  [+] Enter no. of days/candles in the past as starting candle\n"
        f"  [+] You can also enter a past date in {colorText.END}{colorText.GREEN}YYYY-MM-DD{colorText.END}"
        f"{colorText.FAIL} format\n"
        f"  [+] (e.g. {colorText.GREEN}10{colorText.END} for 10 candles ago or "
        f"{colorText.GREEN}0{colorText.END} for today or "
        f"{colorText.GREEN}{last_trading_date}{colorText.END}):"
    ) or ('22' if configManager.period == '1y' else '15')
    OutputControls().printOutput(colorText.END, end="")
    
    if len(str(backtest_days_ago)) >= 3 and "-" in str(backtest_days_ago):
        try:
            backtest_days_ago = abs(PKDateUtilities.trading_days_between(
                d1=PKDateUtilities.dateFromYmdString(str(backtest_days_ago)),
                d2=PKDateUtilities.currentDateTime()
            ))
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            OutputControls().printOutput("An error occurred! Going ahead with default inputs.")
            backtest_days_ago = '22' if configManager.period == '1y' else '15'
            sleep(3)
    
    launcher = _get_launcher()
    requesting_user = f" -u {userPassedArgs.user}" if userPassedArgs.user is not None else ""
    enable_log = " -l" if userPassedArgs.log else ""
    enable_telegram = " --telegram" if userPassedArgs is not None and userPassedArgs.telegram else ""
    stocklist_param = f" --stocklist {userPassedArgs.stocklist}" if userPassedArgs.stocklist else ""
    slicewindow_param = f" --slicewindow {userPassedArgs.slicewindow}" if userPassedArgs.slicewindow else ""
    fname_param = f" --fname {resultsContentsEncoded}" if resultsContentsEncoded else ""
    
    OutputControls().printOutput(
        f"{colorText.GREEN}Launching PKScreener in quick backtest mode.{colorText.END}\n"
        f"{colorText.FAIL}{launcher} --backtestdaysago {int(backtest_days_ago)}"
        f"{requesting_user}{enable_log}{enable_telegram}{stocklist_param}{slicewindow_param}{fname_param}{colorText.END}\n"
        f"{colorText.WARN}Press Ctrl + C to exit.{colorText.END}"
    )
    sleep(2)
    os.system(
        f"{launcher} --systemlaunched -a Y -e --backtestdaysago {int(backtest_days_ago)}"
        f"{requesting_user}{enable_log}{enable_telegram}{stocklist_param}{slicewindow_param}{fname_param}"
    )
    ConsoleUtility.PKConsoleTools.clearScreen(clearAlways=True, forceTop=True)
    return (None, None)

