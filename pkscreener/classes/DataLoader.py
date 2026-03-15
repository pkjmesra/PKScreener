"""
DataLoader - Stock data loading and preparation for PKScreener

This module handles:
- Loading stock data from cache or downloading fresh data
- Preparing stocks for screening
- Managing stock data dictionaries
"""

import os
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes import Archiver
from PKDevTools.classes.log import default_logger

from pkscreener.classes import Utility, AssetsManager
import pkscreener.classes.ConfigManager as ConfigManager


class StockDataLoader:
    """
    Handles loading and management of stock data.
    
    This class encapsulates the data loading logic that was previously
    in globals.py.
    """
    
    def __init__(self, config_manager, fetcher):
        self.config_manager = config_manager
        self.fetcher = fetcher
        self.stock_dict_primary = None
        self.stock_dict_secondary = None
        self.loaded_stock_data = False
        self.load_count = 0
    
    def initialize_dicts(self, mp_manager=None):
        """Initialize stock dictionaries using multiprocessing manager if available"""
        if mp_manager is not None:
            self.stock_dict_primary = mp_manager.dict()
            self.stock_dict_secondary = mp_manager.dict()
        else:
            self.stock_dict_primary = {}
            self.stock_dict_secondary = {}
        self.load_count = 0
    
    def load_database_or_fetch(
        self,
        download_only: bool,
        list_stock_codes: List[str],
        menu_option: str,
        index_option: int,
        default_answer=None,
        user_passed_args=None
    ) -> Tuple[Dict, Dict]:
        """
        Load stock data from cache or fetch from data providers.
        
        Args:
            download_only: Whether to only download data
            list_stock_codes: List of stock codes to load
            menu_option: Current menu option
            index_option: Current index option
            default_answer: Default answer for prompts
            user_passed_args: User passed arguments
            
        Returns:
            Tuple of (stock_dict_primary, stock_dict_secondary)
        """
        if self.stock_dict_primary is None:
            self.stock_dict_primary = {}
            self.stock_dict_secondary = {}
        
        exchange_suffix = "" if (index_option == 15 or 
            (self.config_manager.defaultIndex == 15 and index_option == 0)) else ".NS"
        
        if menu_option not in ["C"]:
            self.stock_dict_primary = AssetsManager.PKAssetsManager.loadStockData(
                self.stock_dict_primary,
                self.config_manager,
                downloadOnly=download_only,
                defaultAnswer=default_answer,
                forceLoad=(menu_option in ["X", "B", "G", "S", "F"]),
                stockCodes=list_stock_codes,
                exchangeSuffix=exchange_suffix,
                userDownloadOption=menu_option
            )
        
        # Load secondary (intraday) data if needed
        if self._should_load_secondary_data(menu_option, user_passed_args):
            self._load_secondary_data(
                download_only, list_stock_codes, menu_option, 
                index_option, default_answer, user_passed_args
            )
        
        self.loaded_stock_data = True
        self.load_count = len(self.stock_dict_primary) if self.stock_dict_primary else 0
        
        Utility.tools.loadLargeDeals()
        
        return self.stock_dict_primary, self.stock_dict_secondary
    
    def _should_load_secondary_data(self, menu_option: str, user_passed_args) -> bool:
        """Check if secondary (intraday) data should be loaded"""
        if menu_option in ["C"]:
            return False
        
        if user_passed_args is None:
            return False
        
        if user_passed_args.monitor is not None:
            return True
        
        if user_passed_args.options:
            if "|" in user_passed_args.options and ':i' in user_passed_args.options:
                return True
            if any(opt in user_passed_args.options for opt in [":33:3:", ":32:", ":38:"]):
                return True
        
        return False
    
    def _load_secondary_data(
        self,
        download_only: bool,
        list_stock_codes: List[str],
        menu_option: str,
        index_option: int,
        default_answer,
        user_passed_args
    ):
        """Load secondary (intraday) stock data"""
        prev_duration = self.config_manager.duration
        prev_period = self.config_manager.period
        
        candle_duration = "1m"
        if user_passed_args and user_passed_args.intraday:
            candle_duration = user_passed_args.intraday
        elif self.config_manager.duration.endswith("d"):
            candle_duration = "1m"
        else:
            candle_duration = self.config_manager.duration
        
        self.config_manager.toggleConfig(candleDuration=candle_duration, clearCache=False)
        
        # Handle special case for option 33:3
        if user_passed_args and user_passed_args.options and ":33:3:" in user_passed_args.options:
            exists, cache_file = AssetsManager.PKAssetsManager.afterMarketStockDataExists(
                True, forceLoad=(menu_option in ["X", "B", "G", "S", "F"])
            )
            cache_file = os.path.join(Archiver.get_user_data_dir(), cache_file)
            cache_file_size = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
            
            if cache_file_size < 1024 * 1024 * 100:  # Less than 100MB
                self.config_manager.deleteFileWithPattern(
                    pattern="*intraday_stock_data_*.pkl",
                    rootDir=Archiver.get_user_data_dir()
                )
            
            self.config_manager.duration = "1m"
            self.config_manager.period = "5d"
            self.config_manager.setConfig(
                ConfigManager.parser, default=True, showFileCreatedText=False
            )
        
        exchange_suffix = "" if (index_option == 15 or 
            (self.config_manager.defaultIndex == 15 and index_option == 0)) else ".NS"
        
        self.stock_dict_secondary = AssetsManager.PKAssetsManager.loadStockData(
            self.stock_dict_secondary,
            self.config_manager,
            downloadOnly=download_only,
            defaultAnswer=default_answer,
            forceLoad=(menu_option in ["X", "B", "G", "S", "F"]),
            stockCodes=list_stock_codes,
            isIntraday=True,
            exchangeSuffix=exchange_suffix,
            userDownloadOption=menu_option
        )
        
        # Restore original config
        self.config_manager.duration = prev_duration
        self.config_manager.period = prev_period
        self.config_manager.setConfig(
            ConfigManager.parser, default=True, showFileCreatedText=False
        )
    
    def get_latest_trade_datetime(self) -> Tuple[str, str]:
        """Get the latest trade date and time from loaded data"""
        if not self.stock_dict_primary:
            return PKDateUtilities.currentDateTime().strftime("%Y-%m-%d"), \
                   PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
        
        try:
            stocks = list(self.stock_dict_primary.keys())
            stock = stocks[0]
            
            last_trade_date = PKDateUtilities.currentDateTime().strftime("%Y-%m-%d")
            last_trade_time_ist = PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
            
            df = pd.DataFrame(
                data=self.stock_dict_primary[stock]["data"],
                columns=self.stock_dict_primary[stock]["columns"],
                index=self.stock_dict_primary[stock]["index"]
            )
            ts = df.index[-1]
            last_traded = pd.to_datetime(ts, unit='s', utc=True)
            last_trade_date = last_traded.strftime("%Y-%m-%d")
            last_trade_time = last_traded.strftime("%H:%M:%S")
            
            if last_trade_time == "00:00:00":
                last_trade_time = last_trade_time_ist
                
            return last_trade_date, last_trade_time
            
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            return PKDateUtilities.currentDateTime().strftime("%Y-%m-%d"), \
                   PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
    
    def prepare_stocks_for_screening(
        self,
        testing: bool,
        download_only: bool,
        list_stock_codes: Optional[List[str]],
        index_option: int,
        newly_listed_only: bool = False,
        user_passed_args=None
    ) -> List[str]:
        """
        Prepare the list of stocks for screening.
        
        Args:
            testing: Whether in test mode
            download_only: Whether to only download
            list_stock_codes: Pre-existing list of stock codes
            index_option: Selected index option
            newly_listed_only: Filter to newly listed only
            user_passed_args: User passed arguments
            
        Returns:
            List of stock codes to screen
        """
        should_suppress = not OutputControls().enableMultipleLineOutput
        
        if list_stock_codes is not None and len(list_stock_codes) > 0:
            return list_stock_codes
        
        with SuppressOutput(suppress_stderr=should_suppress, suppress_stdout=should_suppress):
            list_stock_codes = self.fetcher.fetchStockCodes(index_option, stockCode=None)
        
        if newly_listed_only:
            list_stock_codes = self._filter_newly_listed(list_stock_codes)
        
        # Shuffle if configured
        if not testing and self.config_manager.shuffleEnabled:
            import random
            random.shuffle(list_stock_codes)
            OutputControls().printOutput(
                f"{colorText.GREEN}[+] Stock shuffling is active.{colorText.END}"
            )
        
        return list_stock_codes
    
    def _filter_newly_listed(self, list_stock_codes: List[str]) -> List[str]:
        """Filter to only newly listed stocks"""
        # Implementation depends on how newly listed stocks are determined
        # This is a placeholder
        return list_stock_codes
    
    def handle_request_for_specific_stocks(
        self,
        options: List[str],
        index_option: int
    ) -> Optional[List[str]]:
        """Handle request for specific stock codes from options"""
        if len(options) >= 3:
            specific_stocks = options[2] if len(options) <= 3 else options[3]
            if "," in specific_stocks or "." in specific_stocks:
                return specific_stocks.replace(".", ",").split(",")
        return None
    
    def refresh_stock_data(self, startup_options=None):
        """Refresh stock data by clearing and reloading"""
        self.stock_dict_primary = None
        self.stock_dict_secondary = None
        self.loaded_stock_data = False
    
    def save_downloaded_data(
        self,
        download_only: bool,
        testing: bool,
        load_count: int,
        default_answer=None,
        user_passed_args=None,
        keyboard_interrupt_fired: bool = False,
        download_trials: int = 0
    ):
        """Save downloaded stock data to cache"""
        if keyboard_interrupt_fired:
            return
        
        intraday = (user_passed_args.intraday if user_passed_args else None) or \
                   self.config_manager.isIntradayConfig()
        
        should_save = download_only or (
            self.config_manager.cacheEnabled and 
            not PKDateUtilities.isTradingTime() and 
            not testing
        )
        
        if should_save:
            OutputControls().printOutput(
                f"{colorText.GREEN}  [+] Caching Stock Data for future use, Please Wait... {colorText.END}",
                end=""
            )
            
            AssetsManager.PKAssetsManager.saveStockData(
                self.stock_dict_primary, 
                self.config_manager, 
                load_count, 
                intraday
            )
            
            if download_only:
                cache_file = AssetsManager.PKAssetsManager.saveStockData(
                    self.stock_dict_primary,
                    self.config_manager,
                    load_count,
                    intraday,
                    downloadOnly=download_only
                )
                cache_file_size = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
                
                if cache_file_size < 1024 * 1024 * 40 and download_trials < 3:
                    OutputControls().printOutput(
                        f"\n{colorText.WARN}Download appears incomplete. "
                        f"Retrying... ({download_trials + 1}/3){colorText.END}"
                    )
                    return download_trials + 1
                    
            OutputControls().printOutput(f"{colorText.GREEN}Done!{colorText.END}")
        
        return 0
    
    def try_load_data_on_background_thread(self, default_answer="Y"):
        """Load data on background thread (for pre-loading)"""
        if self.stock_dict_primary is None:
            self.stock_dict_primary = {}
            self.stock_dict_secondary = {}
            self.loaded_stock_data = False
        
        self.config_manager.getConfig(parser=ConfigManager.parser)
        
        should_suppress = True
        with SuppressOutput(suppress_stderr=should_suppress, suppress_stdout=should_suppress):
            list_stock_codes = self.fetcher.fetchStockCodes(
                int(self.config_manager.defaultIndex), 
                stockCode=None
            )
        
        self.load_database_or_fetch(
            download_only=True,
            list_stock_codes=list_stock_codes,
            menu_option="X",
            index_option=int(self.config_manager.defaultIndex),
            default_answer=default_answer
        )


def save_downloaded_data_impl(
    download_only: bool,
    testing: bool,
    stock_dict_primary,
    config_manager,
    load_count: int,
    user_passed_args=None,
    keyboard_interrupt_fired: bool = False,
    send_message_cb=None,
    dev_channel_id: str = None
):
    """
    Implementation of saveDownloadedData for delegation from globals.py.
    
    This function saves downloaded stock data to cache.
    """
    from pkscreener.classes import AssetsManager
    from pkscreener.classes.PKAnalytics import PKAnalyticsService
    
    args_intraday = user_passed_args is not None and user_passed_args.intraday is not None
    intraday_config = config_manager.isIntradayConfig()
    intraday = intraday_config or args_intraday
    
    if not keyboard_interrupt_fired and (download_only or (
        config_manager.cacheEnabled and not PKDateUtilities.isTradingTime() and not testing
    )):
        OutputControls().printOutput(
            colorText.GREEN
            + "  [+] Caching Stock Data for future use, Please Wait... "
            + colorText.END,
            end="",
        )
        AssetsManager.PKAssetsManager.saveStockData(stock_dict_primary, config_manager, load_count, intraday)
        
        if download_only:
            cache_file = AssetsManager.PKAssetsManager.saveStockData(
                stock_dict_primary, config_manager, load_count, intraday, downloadOnly=download_only
            )
            cache_file_size = os.stat(cache_file).st_size if os.path.exists(cache_file) else 0
            
            if cache_file_size < 1024 * 1024 * 40:
                try:
                    from PKDevTools.classes import Archiver
                    log_file_path = os.path.join(Archiver.get_user_data_dir(), "pkscreener-logs.txt")
                    message = f"{cache_file} has size: {cache_file_size}! Something is wrong!"
                    
                    if send_message_cb:
                        if os.path.exists(log_file_path):
                            send_message_cb(caption=message, document_filePath=log_file_path, user=dev_channel_id)
                        else:
                            send_message_cb(message=message, user=dev_channel_id)
                except Exception:
                    pass
                
                # Retry with logging
                if "PKDevTools_Default_Log_Level" not in os.environ.keys():
                    import sys
                    launcher = f'"{sys.argv[0]}"' if " " in sys.argv[0] else sys.argv[0]
                    launcher = f"python3.12 {launcher}" if (launcher.endswith('.py"') or launcher.endswith(".py")) else launcher
                    intraday_flag = '-i 1m' if config_manager.isIntradayConfig() else ''
                    os.system(f"{launcher} -a Y -e -l -d {intraday_flag}")
                else:
                    del os.environ['PKDevTools_Default_Log_Level']
                    PKAnalyticsService().send_event("app_exit")
                    import sys
                    sys.exit(0)
    else:
        OutputControls().printOutput(colorText.GREEN + "  [+] Skipped Saving!" + colorText.END)
