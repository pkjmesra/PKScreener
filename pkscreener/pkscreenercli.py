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
# =============================================================================
# PKScreener CLI - Command Line Interface
# =============================================================================
# Pyinstaller compile Windows: pyinstaller --onefile --icon=screenshots\icon.ico pkscreener\pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive_progress
# Pyinstaller compile Linux  : pyinstaller --onefile --icon=screenshots/icon.ico pkscreener/pkscreenercli.py  --hidden-import cmath --hidden-import talib.stream --hidden-import numpy --hidden-import pandas --hidden-import alive_progress

import warnings
warnings.simplefilter("ignore", UserWarning, append=True)

import argparse
import builtins
import datetime
import json
import logging
import os
import sys
import tempfile
import time
import traceback

os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["AUTOGRAPH_VERBOSITY"] = "0"

import multiprocessing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    logging.getLogger("tensorflow").setLevel(logging.ERROR)
except Exception:
    pass

from time import sleep

from PKDevTools.classes import log as log
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.FunctionTimeouts import ping

from pkscreener import Imports
from pkscreener.classes.MarketMonitor import MarketMonitor
from pkscreener.classes.PKAnalytics import PKAnalyticsService
import pkscreener.classes.ConfigManager as ConfigManager

if __name__ == '__main__':
    multiprocessing.freeze_support()
    from unittest.mock import patch
    patch("multiprocessing.resource_tracker.register", lambda *args, **kwargs: None)


# =============================================================================
# ARGUMENT PARSER
# =============================================================================

class ArgumentParser:
    """Handles command line argument parsing for PKScreener."""
    
    @staticmethod
    def create_parser():
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="PKScreener - Stock Screening Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Answer/Default options
        parser.add_argument(
            "-a", "--answerdefault",
            help="Pass default answer to questions/choices (Y/N)",
            required=False,
        )
        
        # Backtest options
        parser.add_argument(
            "--backtestdaysago",
            help="Run scanner for N days ago from today",
            required=False,
        )
        
        # Barometer option
        parser.add_argument(
            "--barometer",
            action="store_true",
            help="Send global market barometer to telegram channel or user",
            required=False,
        )
        
        # Bot options
        parser.add_argument(
            "--bot",
            action="store_true",
            help="Run only in telegram bot mode",
            required=False,
        )
        parser.add_argument(
            "--botavailable",
            action="store_true",
            help="Enforce bot availability status",
            required=False,
        )
        
        # Cron/Scheduling options
        parser.add_argument(
            "-c", "--croninterval",
            help="Interval in seconds between runs",
            required=False,
        )
        
        # Download option
        parser.add_argument(
            "-d", "--download",
            action="store_true",
            help="Only download stock data (no analysis)",
            required=False,
        )
        
        # Exit option
        parser.add_argument(
            "-e", "--exit",
            action="store_true",
            help="Exit after single execution",
            required=False,
        )
        
        # File options
        parser.add_argument(
            "--fname",
            help="File name with results contents",
            required=False,
        )
        
        # Force backtest option
        parser.add_argument(
            "--forceBacktestsForZeroResultDays",
            help="Force backtests even for zero-result days",
            action=argparse.BooleanOptionalAction,
        )
        
        # Intraday option
        parser.add_argument(
            "-i", "--intraday",
            help="Intraday candlestick duration (1m, 5m, 15m, 1h, etc.)",
            required=False,
        )
        
        # Monitor option
        parser.add_argument(
            "-m", "--monitor",
            help="Monitor for intraday scanners",
            nargs='?',
            const='X',
            type=str,
            required=False,
        )
        
        # Display options
        parser.add_argument(
            "--maxdisplayresults",
            help="Maximum results to display",
            required=False,
        )
        parser.add_argument(
            "--maxprice",
            help="Maximum stock price filter",
            required=False,
        )
        parser.add_argument(
            "--minprice",
            help="Minimum stock price filter",
            required=False,
        )
        
        # Options/Menu option
        parser.add_argument(
            "-o", "--options",
            help="Menu options in MainMenu:SubMenu:SubMenu format (e.g., X:12:10)",
            required=False,
        )
        
        # Build mode options
        parser.add_argument(
            "-p", "--prodbuild",
            action="store_true",
            help="Run in production-build mode",
            required=False,
        )
        parser.add_argument(
            "-t", "--testbuild",
            action="store_true",
            help="Run in test-build mode",
            required=False,
        )
        
        # Progress/Status options
        parser.add_argument(
            "--progressstatus",
            help="Progress status to display during scans",
            required=False,
        )
        parser.add_argument(
            "--runintradayanalysis",
            action="store_true",
            help="Run intraday analysis (morning vs EoD)",
            required=False,
        )
        
        # Simulation options
        parser.add_argument(
            "--simulate",
            type=json.loads,
            help='Simulate conditions (JSON format)',
            required=False,
        )
        parser.add_argument(
            "--singlethread",
            action="store_true",
            help="Run in single-threaded mode for debugging",
            required=False,
        )
        parser.add_argument(
            "--slicewindow",
            type=str,
            help="Time slice window (datetime with timezone)",
            required=False,
        )
        
        # Stock list option
        parser.add_argument(
            "--stocklist",
            type=str,
            help="Comma-separated list of stocks",
            required=False,
        )
        
        # System options
        parser.add_argument(
            "--systemlaunched",
            action="store_true",
            help="Indicate system-launched screener",
            required=False,
        )
        parser.add_argument(
            "--telegram",
            action="store_true",
            help="Run as telegram bot instance",
            required=False,
        )
        parser.add_argument(
            "--triggertimestamp",
            help="Trigger timestamp value",
            required=False,
        )
        
        # User options
        parser.add_argument(
            "-u", "--user",
            help="Telegram user ID for results",
            required=False,
        )
        parser.add_argument(
            "-l", "--log",
            action="store_true",
            help="Enable full logging",
            required=False,
        )
        parser.add_argument("-v", action="store_true")  # Pytest dummy arg
        
        # Piped options
        parser.add_argument(
            "--pipedtitle",
            help="Piped scan titles",
            required=False,
        )
        parser.add_argument(
            "--pipedmenus",
            help="Piped menu options",
            required=False,
        )
        parser.add_argument(
            "--usertag",
            help="User-defined tag values",
            required=False,
        )
        parser.add_argument(
            "--testalloptions",
            action="store_true",
            help="Test all menu options",
            required=False,
        )
        
        return parser


# =============================================================================
# OUTPUT CONTROL
# =============================================================================

class OutputController:
    """Controls output (stdout/stderr) for production mode."""
    
    _print_enabled = False
    _original_stdout = None
    _original__stdout = None
    _devnull_stdout = None
    _devnull__stdout = None
    
    @staticmethod
    def _decorator(func):
        """Decorator to conditionally execute print."""
        def new_func(*args, **kwargs):
            if OutputController._print_enabled:
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    default_logger().debug(e, exc_info=True)
        return new_func
    
    @classmethod
    def disable_output(cls, disable_input=True, disable=True):
        """Disable or enable system output."""
        cls._print_enabled = not disable
        
        if disable:
            if cls._original_stdout is None:
                builtins.print = cls._decorator(builtins.print)
                if disable_input:
                    builtins.input = cls._decorator(builtins.input)
                cls._original_stdout = sys.stdout
                cls._original__stdout = sys.__stdout__
            cls._devnull_stdout = open(os.devnull, "w")
            cls._devnull__stdout = open(os.devnull, "w")
            sys.stdout = cls._devnull_stdout
            sys.__stdout__ = cls._devnull__stdout
        else:
            try:
                # Close the devnull file handles, not the original stdout
                if hasattr(cls, '_devnull_stdout') and cls._devnull_stdout:
                    cls._devnull_stdout.close()
                if hasattr(cls, '_devnull__stdout') and cls._devnull__stdout:
                    cls._devnull__stdout.close()
            except Exception as e:
                default_logger().debug(e, exc_info=True)
            sys.stdout = cls._original_stdout if cls._original_stdout else sys.stdout
            sys.__stdout__ = cls._original__stdout if cls._original__stdout else sys.__stdout__


# =============================================================================
# LOGGER SETUP
# =============================================================================

class LoggerSetup:
    """Handles logging configuration for the application."""
    
    @staticmethod
    def get_log_file_path():
        """Get the path for the log file."""
        try:
            from PKDevTools.classes import Archiver
            file_path = os.path.join(Archiver.get_user_data_dir(), "pkscreener-logs.txt")
            with open(file_path, "w") as f:
                f.write("Logger file for pkscreener!")
        except Exception:
            file_path = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
        return file_path
    
    @staticmethod
    def setup(should_log=False, trace=False):
        """Setup logging based on configuration."""
        if not should_log:
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                del os.environ['PKDevTools_Default_Log_Level']
            return
        
        log_file_path = LoggerSetup.get_log_file_path()
        
        if os.path.exists(log_file_path):
            try:
                os.remove(log_file_path)
            except Exception:
                pass
        
        OutputControls().printOutput(colorText.FAIL + "\n  [+] Logs will be written to:" + colorText.END)
        OutputControls().printOutput(colorText.GREEN + f"  [+] {log_file_path}" + colorText.END)
        OutputControls().printOutput(
            colorText.FAIL + "  [+] If you need to share, open this folder, copy and zip the log file to share.\n" + colorText.END
        )
        
        os.environ["PKDevTools_Default_Log_Level"] = str(log.logging.DEBUG)
        log.setup_custom_logger(
            "pkscreener",
            log.logging.DEBUG,
            trace=trace,
            log_file_path=log_file_path,
            filter=None,
        )


# =============================================================================
# DEPENDENCY CHECKER
# =============================================================================

class DependencyChecker:
    """Checks and warns about missing dependencies."""
    
    @staticmethod
    def warn_about_dependencies():
        """Check for required dependencies and warn if missing."""
        if not Imports["talib"]:
            OutputControls().printOutput(
                colorText.FAIL + "  [+] TA-Lib is not installed. Looking for pandas_ta_classic." + colorText.END
            )
            sleep(1)
            
            issue_link = "https://github.com/pkjmesra/PKScreener"
            issue_link = f"\x1b[97m\x1b]8;;{issue_link}\x1b\\{issue_link}\x1b]8;;\x1b\\\x1b[0m"
            
            if Imports["pandas_ta_classic"]:
                ta_link = "https://github.com/ta-lib/ta-lib-python"
                ta_link = f"\x1b[97m\x1b]8;;{ta_link}\x1b\\{ta_link}\x1b]8;;\x1b\\\x1b[0m"
                OutputControls().printOutput(
                    colorText.GREEN +
                    f"  [+] Found and falling back on pandas_ta_classic.\n"
                    f"  [+] For full coverage (candle patterns), read README: {issue_link}\n"
                    f"  [+] or follow instructions from {ta_link}" +
                    colorText.END
                )
                sleep(1)
            else:
                OutputControls().printOutput(
                    colorText.FAIL +
                    f"  [+] Neither ta-lib nor pandas_ta_classic found.\n"
                    f"  [+] Please follow instructions from README: {issue_link}" +
                    colorText.END
                )
                OutputControls().takeUserInput("Press any key to try anyway...")


# =============================================================================
# APPLICATION RUNNER
# =============================================================================

class ApplicationRunner:
    """Manages the main application execution flow."""
    
    def __init__(self, config_manager, args, arg_parser):
        """
        Initialize the application runner.
        
        Args:
            config_manager: Configuration manager instance
            args: Parsed command line arguments
            arg_parser: Argument parser instance
        """
        self.config_manager = config_manager
        self.args = args
        self.arg_parser = arg_parser
        self.results = None
        self.result_stocks = None
        self.plain_results = None
        self.db_timestamp = None
        self.elapsed_time = 0
        self.start_time = None
    
    def run(self):
        """Run the main application."""
        from pkscreener.globals import (
            main, sendQuickScanResult, sendMessageToTelegramChannel,
            sendGlobalMarketBarometer, updateMenuChoiceHierarchy, isInterrupted,
            refreshStockData, closeWorkersAndExit, resetUserMenuChoiceOptions,
            menuChoiceHierarchy
        )
        from pkscreener.classes.MenuOptions import (
            menus, PREDEFINED_SCAN_MENU_TEXTS,
            PREDEFINED_PIPED_MENU_ANALYSIS_OPTIONS, PREDEFINED_SCAN_MENU_VALUES
        )
        
        # Preserve piped args
        saved_piped_args = getattr(self.args, 'pipedmenus', None)
        
        # Re-parse args if needed
        self.args = self._refresh_args()
        self.args.pipedmenus = saved_piped_args
        
        # Setup user and timestamp
        self._setup_user_and_timestamp()
        
        # Handle options processing
        if self.args.options is not None:
            self.args.options = self.args.options.replace("::", ":").replace('"', "").replace("'", "")
            if self.args.options.upper().startswith("C") or "C:" in self.args.options.upper():
                self.args.runintradayanalysis = True
            self.args, _ = self._update_progress_status()
        
        # Route to appropriate handler
        if self.args.runintradayanalysis:
            self._run_intraday_analysis()
        elif self.args.testalloptions:
            self._test_all_options(menus, main)
        elif self.args.barometer:
            sendGlobalMarketBarometer(userArgs=self.args)
            sys.exit(0)
        else:
            self._run_standard_scan(main, closeWorkersAndExit, isInterrupted,
                                   updateMenuChoiceHierarchy, refreshStockData)
    
    def _refresh_args(self):
        """Refresh arguments from parser."""
        args = _get_debug_args()
        if not isinstance(args, argparse.Namespace) and not hasattr(args, "side_effect"):
            argsv = self.arg_parser.parse_known_args(args=args)
            args = argsv[0]
        if args is not None and not args.exit and not args.monitor:
            argsv = self.arg_parser.parse_known_args()
            args = argsv[0]
        return args
    
    def _setup_user_and_timestamp(self):
        """Setup user ID and trigger timestamp."""
        if self.args.user is None:
            from PKDevTools.classes.Environment import PKEnvironment
            channel_id, _, _, _ = PKEnvironment().secrets
            if channel_id is not None and len(str(channel_id)) > 0:
                self.args.user = int(f"-{channel_id}")
        
        if self.args.triggertimestamp is None:
            self.args.triggertimestamp = int(PKDateUtilities.currentDateTimestamp())
        else:
            self.args.triggertimestamp = int(self.args.triggertimestamp)
        
        if self.args.systemlaunched and self.args.options is not None:
            self.args.systemlaunched = self.args.options
    
    def _update_progress_status(self, monitor_options=None):
        """Update progress status for display."""
        from pkscreener.classes.MenuOptions import (
            PREDEFINED_SCAN_MENU_TEXTS, PREDEFINED_SCAN_MENU_VALUES, INDICES_MAP
        )
        
        choices = ""
        try:
            if self.args.systemlaunched or monitor_options is not None:
                options_to_use = self.args.options if monitor_options is None else monitor_options
                choices = f"--systemlaunched -a y -e -o '{options_to_use.replace('C:', 'X:').replace('D:', '')}'"
                
                search_choices = choices
                for index_key in INDICES_MAP.keys():
                    if index_key.isnumeric():
                        search_choices = search_choices.replace(f"X:{index_key}:", "X:12:")
                
                index_num = PREDEFINED_SCAN_MENU_VALUES.index(search_choices)
                selected_index_option = choices.split(":")[1]
                choices = f"P_1_{str(index_num + 1)}_{str(selected_index_option)}" if ">|" in choices else choices
                self.args.progressstatus = f"  [+] {choices} => Running {choices}"
                self.args.usertag = PREDEFINED_SCAN_MENU_TEXTS[index_num]
                self.args.maxdisplayresults = 2000
        except:
            choices = ""
        return self.args, choices
    
    def _run_intraday_analysis(self):
        """Run intraday analysis reports."""
        from pkscreener.classes.cli.PKCliRunner import IntradayAnalysisRunner
        runner = IntradayAnalysisRunner(self.config_manager, self.args)
        runner.generate_reports()
    
    def _test_all_options(self, menus, main_func):
        """Test all menu options."""
        all_menus, _ = menus.allMenus(index=0)
        for scan_option in all_menus:
            self.args.options = f"{scan_option}:SBIN,"
            main_func(userArgs=self.args)
        sys.exit(0)
    
    def _run_standard_scan(self, main, close_workers, is_interrupted,
                          update_menu_hierarchy, refresh_data):
        """Run standard scanning mode."""
        from pkscreener.classes.cli.PKCliRunner import PKCliRunner
        
        cli_runner = PKCliRunner(self.config_manager, self.args)
        monitor_option_org = ""
        
        # Handle monitor mode
        if self.args.monitor:
            self._setup_monitor_mode(cli_runner, refresh_data)
            monitor_option_org = MarketMonitor().currentMonitorOption()
        
        # Run the scan
        try:
            self._execute_scan(main, close_workers, is_interrupted,
                              update_menu_hierarchy, cli_runner, monitor_option_org)
        except SystemExit:
            close_workers()
            _exit_gracefully(self.config_manager, self.arg_parser)
            sys.exit(0)
        except KeyboardInterrupt:
            close_workers()
            _exit_gracefully(self.config_manager, self.arg_parser)
            sys.exit(0)
        except Exception as e:
            default_logger().debug(e, exc_info=True)
            if self.args.log:
                traceback.print_exc()
    
    def _setup_monitor_mode(self, cli_runner, refresh_data):
        """Setup monitor mode."""
        self.args.monitor = self.args.monitor.replace("::", ":").replace('"', "").replace("'", "")
        self.config_manager.getConfig(ConfigManager.parser)
        self.args.answerdefault = self.args.answerdefault or 'Y'
        MarketMonitor().hiddenColumns = self.config_manager.alwaysHiddenDisplayColumns
        
        if MarketMonitor().monitorIndex == 0:
            self.db_timestamp = PKDateUtilities.currentDateTime().strftime("%H:%M:%S")
            self.elapsed_time = 0
            if self.start_time is None:
                self.start_time = time.time()
            else:
                self.elapsed_time = round(time.time() - self.start_time, 2)
                self.start_time = time.time()
    
    def _execute_scan(self, main, close_workers, is_interrupted,
                     update_menu_hierarchy, cli_runner, monitor_option_org):
        """Execute the scanning process."""
        self.results = None
        self.plain_results = None
        self.result_stocks = None
        
        if self.args is not None and ((self.args.options is not None and "|" in self.args.options) or self.args.systemlaunched):
            self.args.maxdisplayresults = 2000
        
        cli_runner.update_config_durations()
        cli_runner.update_config()
        
        self.results, self.plain_results = main(userArgs=self.args)
        
        # Handle piped menus
        if self.args.pipedmenus is not None:
            while self.args.pipedmenus is not None:
                self.args, _ = self._update_progress_status()
                self.results, self.plain_results = main(userArgs=self.args)
        
        if is_interrupted():
            close_workers()
            _exit_gracefully(self.config_manager, self.arg_parser)
            sys.exit(0)
        
        # Handle piped scans
        run_piped_scans = True
        while run_piped_scans:
            run_piped_scans = cli_runner.pipe_results(self.plain_results)
            if run_piped_scans:
                self.args, _ = self._update_progress_status()
                self.results, self.plain_results = main(userArgs=self.args)
            elif self.args is not None and self.args.pipedtitle is not None and "|" in self.args.pipedtitle:
                OutputControls().printOutput(
                    colorText.WARN +
                    f"  [+] Pipe Results Found: {self.args.pipedtitle}. "
                    f"{'Reduce number of piped scans if no stocks found.' if '[0]' in self.args.pipedtitle else ''}" +
                    colorText.END
                )
                if self.args.answerdefault is None:
                    OutputControls().takeUserInput("Press <Enter> to continue...")
        
        # Process results
        self._process_results(update_menu_hierarchy, monitor_option_org)
    
    def _process_results(self, update_menu_hierarchy, monitor_option_org):
        """Process scan results."""
        if self.plain_results is not None and not self.plain_results.empty:
            try:
                self.plain_results.set_index("Stock", inplace=True)
            except:
                pass
            try:
                self.results.set_index("Stock", inplace=True)
            except:
                pass
            self.plain_results = self.plain_results[~self.plain_results.index.duplicated(keep='first')]
            self.results = self.results[~self.results.index.duplicated(keep='first')]
            self.result_stocks = self.plain_results.index
        
        if self.args.monitor is not None:
            MarketMonitor().saveMonitorResultStocks(self.plain_results)
            if self.results is not None and len(monitor_option_org) > 0:
                chosen_menu = self.args.pipedtitle if self.args.pipedtitle is not None else update_menu_hierarchy()
                MarketMonitor().refresh(
                    screen_df=self.results,
                    screenOptions=monitor_option_org,
                    chosenMenu=chosen_menu[:120],
                    dbTimestamp=f"{self.db_timestamp} | CycleTime:{self.elapsed_time}s",
                    telegram=self.args.telegram
                )
                self.args.pipedtitle = ""
            
            # Check market close
            self._check_market_close()
    
    def _check_market_close(self):
        """Check if market has closed and exit if needed."""
        if "RUNNER" in os.environ.keys() and self.args.triggertimestamp is not None:
            from datetime import timezone
            from PKDevTools.classes.MarketHours import MarketHours
            
            market_close_ts = PKDateUtilities.currentDateTime(
                simulate=True,
                hour=MarketHours().closeHour,
                minute=MarketHours().closeMinute
            ).replace(tzinfo=timezone.utc).timestamp()
            
            if (int(self.args.triggertimestamp) < int(market_close_ts) and
                int(PKDateUtilities.currentDateTimestamp()) >= market_close_ts):
                OutputControls().printOutput("Exiting monitor now since market has closed!", enableMultipleLineOutput=True)
                sys.exit(0)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_debug_args():
    """Get debug arguments from command line."""
    import csv
    import re
    
    def re_split(s):
        def strip_quotes(s):
            if s and (s[0] == '"' or s[0] == "'") and s[0] == s[-1]:
                return s[1:-1]
            return s
        return [strip_quotes(p).replace('\\"', '"').replace("\\'", "'")
                for p in re.findall(r'(?:[^"\s]*"(?:\\.|[^"])*"[^"\s]*)+|(?:[^\'\s]*\'(?:\\.|[^\'])*\'[^\'\s]*)+|[^\s]+', s)]
    
    global args
    try:
        if args is not None:
            args = list(args)
        return args
    except NameError:
        args = sys.argv[1:]
        if isinstance(args, list):
            if len(args) == 1:
                return re_split(args[0])
            return args
        return None
    except TypeError:
        return args
    except Exception:
        return None


def _exit_gracefully(config_manager, arg_parser):
    """Perform graceful exit cleanup."""
    try:
        from PKDevTools.classes import Archiver
        from pkscreener.globals import resetConfigToDefault
        
        file_path = None
        try:
            file_path = os.path.join(Archiver.get_user_data_dir(), "monitor_outputs")
        except:
            pass
        
        if file_path is None:
            return
        
        # Clean up monitor output files
        index = 0
        while index < config_manager.maxDashboardWidgetsPerRow * config_manager.maxNumResultRowsInMonitor:
            try:
                os.remove(f"{file_path}_{index}.txt")
            except:
                pass
            index += 1
        
        # Reset config if needed
        argsv = arg_parser.parse_known_args()
        args = argsv[0]
        if args is not None and args.options is not None and not args.options.upper().startswith("T"):
            resetConfigToDefault(force=True)
        
        if "PKDevTools_Default_Log_Level" in os.environ.keys():
            if args is None or (args is not None and args.options is not None and "|" not in args.options):
                del os.environ['PKDevTools_Default_Log_Level']
        
        config_manager.logsEnabled = False
        config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    except RuntimeError:
        OutputControls().printOutput(
            f"{colorText.WARN}If you're running from within docker, please run like this:{colorText.END}\n"
            f"{colorText.FAIL}docker run -it pkjmesra/pkscreener:latest\n{colorText.END}"
        )


def _remove_old_instances():
    """Remove old CLI instances."""
    import glob
    pattern = "pkscreenercli*"
    this_instance = sys.argv[0]
    for f in glob.glob(pattern, root_dir=os.getcwd(), recursive=True):
        file_to_delete = f if (os.sep in f and f.startswith(this_instance[:10])) else os.path.join(os.getcwd(), f)
        if not file_to_delete.endswith(this_instance):
            try:
                os.remove(file_to_delete)
            except:
                pass


# =============================================================================
# MAIN ENTRY POINTS
# =============================================================================

# Global state
args = None
argParser = ArgumentParser.create_parser()
configManager = ConfigManager.tools()

# Parse initial arguments
args = _get_debug_args()
argsv = argParser.parse_known_args(args=args)
args = argsv[0]


def runApplication():
    """Run the main application."""
    global args
    runner = ApplicationRunner(configManager, args, argParser)
    runner.run()


def runApplicationForScreening():
    """Run application in screening mode."""
    from pkscreener.globals import closeWorkersAndExit
    
    try:
        has_cron_interval = args.croninterval is not None and str(args.croninterval).isnumeric()
        should_break = (args.exit and not has_cron_interval) or args.user is not None or args.testbuild
        
        if has_cron_interval:
            _schedule_next_run()
        else:
            runApplication()
        
        while True:
            if should_break:
                break
            if has_cron_interval:
                _schedule_next_run()
            else:
                runApplication()
        
        if args.v:
            OutputController.disable_output(disable=False)
            return
        
        closeWorkersAndExit()
        _exit_gracefully(configManager, argParser)
        sys.exit(0)
        
    except SystemExit:
        closeWorkersAndExit()
        _exit_gracefully(configManager, argParser)
        sys.exit(0)
    except (RuntimeError, Exception) as e:
        default_logger().debug(e, exc_info=True)
        if args.prodbuild:
            OutputController.disable_output(disable=False)
        OutputControls().printOutput(
            f"{e}\n  [+] An error occurred! Please run with '-l' option to collect the logs.\n"
            f"  [+] For example, 'pkscreener -l' and then contact the developer!"
        )
        if "RUNNER" in os.environ.keys() or ('PKDevTools_Default_Log_Level' in os.environ.keys() and
                                             os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
            traceback.print_exc()
        
        if args.v:
            OutputController.disable_output(disable=False)
            return
        
        closeWorkersAndExit()
        _exit_gracefully(configManager, argParser)
        sys.exit(0)


_cron_runs = 0

def _schedule_next_run():
    """Schedule next run based on cron interval."""
    global _cron_runs
    
    sleep_until_next = not PKDateUtilities.isTradingTime()
    while sleep_until_next:
        OutputControls().printOutput(
            colorText.FAIL +
            f"SecondsAfterClosingTime[{int(PKDateUtilities.secondsAfterCloseTime())}] "
            f"SecondsBeforeMarketOpen [{int(PKDateUtilities.secondsBeforeOpenTime())}]. "
            f"Next run at [{PKDateUtilities.nextRunAtDateTime(bufferSeconds=3600, cronWaitSeconds=int(args.croninterval))}]" +
            colorText.END
        )
        
        if (PKDateUtilities.secondsAfterCloseTime() >= 3600 and
            PKDateUtilities.secondsAfterCloseTime() <= (3600 + 1.5 * int(args.croninterval))):
            sleep_until_next = False
        
        if (PKDateUtilities.secondsBeforeOpenTime() <= -3600 and
            PKDateUtilities.secondsBeforeOpenTime() >= (-3600 - 1.5 * int(args.croninterval))):
            sleep_until_next = False
        
        sleep(int(args.croninterval))
    
    if _cron_runs > 0:
        next_time = (PKDateUtilities.currentDateTime() + datetime.timedelta(seconds=120)).strftime("%Y-%m-%d %H:%M:%S")
        OutputControls().printOutput(
            colorText.GREEN + f'=> Going to fetch again in {int(args.croninterval)} sec. at {next_time} IST...' + colorText.END,
            end="\r",
            flush=True,
        )
        sleep(int(args.croninterval) if not args.testbuild else 3)
    
    runApplication()
    _cron_runs += 1


@ping(interval=60, instance=PKAnalyticsService())
def pkscreenercli():
    """Main CLI entry point."""
    global args
    
    # Setup multiprocessing for macOS
    if sys.platform.startswith("darwin"):
        try:
            multiprocessing.set_start_method("fork")
        except RuntimeError as e:
            if "RUNNER" not in os.environ.keys() and ('PKDevTools_Default_Log_Level' in os.environ.keys() and
                                                      os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
                OutputControls().printOutput("  [+] RuntimeError with 'multiprocessing'.\n  [+] Please contact the Developer!")
                OutputControls().printOutput(e)
                traceback.print_exc()
    
    try:
        _remove_old_instances()
        OutputControls(
            enableMultipleLineOutput=(args is None or args.monitor is None or args.runintradayanalysis),
            enableUserInput=(args is None or args.answerdefault is None)
        ).printOutput("", end="\r")
        
        configManager.getConfig(ConfigManager.parser)
        
        # Validate TOS acceptance
        from pkscreener.classes.cli.PKCliRunner import CliConfigManager
        cli_config = CliConfigManager(configManager, args)
        if not cli_config.validate_tos_acceptance():
            sys.exit(0)
        
        # Setup configuration
        try:
            from pkscreener.classes import VERSION
            del os.environ['PKDevTools_Default_Log_Level']
        except:
            pass
        
        configManager.logsEnabled = False
        configManager.tosAccepted = True
        from pkscreener.classes import VERSION
        configManager.appVersion = VERSION
        configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        
        import atexit
        atexit.register(lambda: _exit_gracefully(configManager, argParser))
        
        # Set trigger timestamp
        if args.triggertimestamp is None:
            args.triggertimestamp = int(PKDateUtilities.currentDateTimestamp())
        else:
            args.triggertimestamp = int(args.triggertimestamp)
        
        # Setup monitor if requested
        if args.monitor is not None:
            from pkscreener.classes.MenuOptions import NA_NON_MARKET_HOURS
            configured_options = (configManager.defaultMonitorOptions.split("~")
                                if len(configManager.myMonitorOptions) < 1
                                else configManager.myMonitorOptions.split("~"))
            
            for option in NA_NON_MARKET_HOURS:
                if option in configured_options and not PKDateUtilities.isTradingTime():
                    configured_options.remove(option)
            
            MarketMonitor(
                monitors=args.monitor.split("~") if len(args.monitor) > 5 else configured_options,
                maxNumResultsPerRow=configManager.maxDashboardWidgetsPerRow,
                maxNumColsInEachResult=6,
                maxNumRowsInEachResult=10,
                maxNumResultRowsInMonitor=configManager.maxNumResultRowsInMonitor,
                pinnedIntervalWaitSeconds=configManager.pinnedMonitorSleepIntervalSeconds,
                alertOptions=configManager.soundAlertForMonitorOptions.split("~")
            )
        
        # Setup logging
        if args.log or configManager.logsEnabled:
            LoggerSetup.setup(should_log=True, trace=args.testbuild)
            if not args.prodbuild and args.answerdefault is None:
                try:
                    OutputControls().takeUserInput("Press <Enter> to continue...")
                except EOFError:
                    OutputControls().printOutput(
                        f"{colorText.WARN}If you're running from within docker, please run like this:{colorText.END}\n"
                        f"{colorText.FAIL}docker run -it pkjmesra/pkscreener:latest\n{colorText.END}"
                    )
        else:
            if "PKDevTools_Default_Log_Level" in os.environ.keys():
                del os.environ['PKDevTools_Default_Log_Level']
        
        # Handle simulation
        if args.simulate:
            os.environ["simulation"] = json.dumps(args.simulate)
        elif "simulation" in os.environ.keys():
            del os.environ['simulation']
        
        # Import dependencies
        from pkscreener.classes import Utility, ConsoleUtility
        
        configManager.default_logger = default_logger()
        
        if OutputController._original_stdout is None:
            ConsoleUtility.PKConsoleTools.clearScreen(userArgs=args, clearAlways=True)
        
        DependencyChecker.warn_about_dependencies()
        
        # Handle production mode
        if args.prodbuild:
            if args.options and len(args.options.split(":")) > 0:
                do_not_disable = any(f":{i}:30:" in args.options for i in range(16))
                if not do_not_disable:
                    OutputController.disable_output()
            else:
                OutputController.disable_output()
        
        # Ensure config file exists
        if not configManager.checkConfigFile():
            configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        
        # Validate premium user for system-launched
        from pkscreener.classes.PKUserRegistration import PKUserRegistration, ValidationResult
        if args.systemlaunched and not PKUserRegistration.validateToken()[0]:
            result = PKUserRegistration.login()
            if result != ValidationResult.Success:
                OutputControls().printOutput(f"\n[+] {colorText.FAIL}You MUST be a premium/paid user to use this feature!{colorText.END}\n")
                input("Press any key to exit...")
                sys.exit(0)
        
        if args.systemlaunched and args.options is not None:
            args.systemlaunched = args.options
        
        # Handle telegram mode
        if args.telegram:
            if (PKDateUtilities.isTradingTime() and not PKDateUtilities.isTodayHoliday()[0]) or ("PKDevTools_Default_Log_Level" in os.environ.keys()):
                from PKDevTools.classes import Archiver
                file_path = os.path.join(Archiver.get_user_data_dir(), "monitor_outputs_1.txt")
                if os.path.exists(file_path):
                    default_logger().info("monitor_outputs_1.txt exists! Another instance may be running. Exiting...")
                    return
            else:
                default_logger().info("--telegram option must be launched ONLY during NSE trading hours. Exiting...")
                return
        
        # Handle bot mode
        if args.bot:
            from pkscreener import pkscreenerbot
            pkscreenerbot.runpkscreenerbot(availability=args.botavailable)
            return
        
        # Update configuration
        from pkscreener.classes.cli.PKCliRunner import PKCliRunner
        cli_runner = PKCliRunner(configManager, args)
        cli_runner.update_config()
        
        if args.options is not None:
            if str(args.options) == "0":
                args.options = None
            else:
                args.options = args.options.replace("::", ":")
        
        # Apply price filters
        if args.maxprice:
            configManager.maxLTP = args.maxprice
            configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        if args.minprice:
            configManager.minLTP = args.minprice
            configManager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
        
        # Handle login
        global LoggedIn
        try:
            LoggedIn
        except NameError:
            LoggedIn = False
        
        if not LoggedIn and not args.telegram and not args.bot and not args.systemlaunched and not args.testbuild:
            if not PKUserRegistration.login():
                sys.exit(0)
            LoggedIn = True
        
        # Run appropriate mode
        if args.testbuild and not args.prodbuild:
            OutputControls().printOutput(colorText.FAIL + "  [+] Started in TestBuild mode!" + colorText.END)
            runApplication()
            from pkscreener.globals import closeWorkersAndExit
            closeWorkersAndExit()
            _exit_gracefully(configManager, argParser)
            sys.exit(0)
        elif args.download:
            OutputControls().printOutput(colorText.FAIL + "  [+] Download ONLY mode! Stocks will not be screened!" + colorText.END)
            configManager.restartRequestsCache()
            runApplication()
            from pkscreener.globals import closeWorkersAndExit
            closeWorkersAndExit()
            _exit_gracefully(configManager, argParser)
            sys.exit(0)
        else:
            runApplicationForScreening()
            
    except KeyboardInterrupt:
        from pkscreener.globals import closeWorkersAndExit
        closeWorkersAndExit()
        _exit_gracefully(configManager, argParser)
        sys.exit(0)
    except Exception as e:
        if "RUNNER" not in os.environ.keys() and ('PKDevTools_Default_Log_Level' in os.environ.keys() and
                                                  os.environ["PKDevTools_Default_Log_Level"] != str(log.logging.NOTSET)):
            OutputControls().printOutput("  [+] RuntimeError with 'multiprocessing'.\n  [+] Please contact the Developer!")
            OutputControls().printOutput(e)
            traceback.print_exc()


# Backward compatibility aliases
disableSysOut = OutputController.disable_output
setupLogger = LoggerSetup.setup
logFilePath = LoggerSetup.get_log_file_path
warnAboutDependencies = DependencyChecker.warn_about_dependencies
exitGracefully = lambda: _exit_gracefully(configManager, argParser)


if __name__ == "__main__":
    if "RUNNER" in os.environ.keys():
        try:
            owner = os.popen('git ls-remote --get-url origin | cut -d/ -f4').read().replace("\n", "")
            repo = os.popen('git ls-remote --get-url origin | cut -d/ -f5').read().replace(".git", "").replace("\n", "")
            if owner.lower() not in ["pkjmesra", "pkscreener"]:
                sys.exit(0)
        except:
            pass
    
    try:
        pkscreenercli()
    except KeyboardInterrupt:
        from pkscreener.globals import closeWorkersAndExit
        closeWorkersAndExit()
        _exit_gracefully(configManager, argParser)
        sys.exit(0)
