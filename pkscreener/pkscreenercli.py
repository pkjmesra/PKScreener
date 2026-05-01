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

# Disable protobuf logging
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['PROTOBUF_PYTHON_SILENT_WARNINGS'] = '1'
os.environ["PYTHONWARNINGS"] = "ignore::UserWarning"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["AUTOGRAPH_VERBOSITY"] = "0"

import multiprocessing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# PROTOBUF PATCH - MUST BE FIRST
# =============================================================================
"""
This patch fixes the 'GetPrototype' AttributeError in protobuf by monkey-patching
the MessageFactory class before any other code imports it.
"""
import sys
import os

# Set environment variables to reduce protobuf logging
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['PROTOBUF_PYTHON_SILENT_WARNINGS'] = '1'

# Force import of protobuf modules first
try:
    import google.protobuf.message_factory
    
    # Patch MessageFactory class
    if hasattr(google.protobuf.message_factory, 'MessageFactory'):
        # Store the original __init__
        original_init = google.protobuf.message_factory.MessageFactory.__init__
        
        def patched_init(self, *args, **kwargs):
            """Patched __init__ that adds GetPrototype method to MessageFactory instances.
            
            This function monkey-patches the MessageFactory constructor to add a
            GetPrototype method if it doesn't exist, ensuring compatibility with
            different versions of protobuf.
            
            Args:
                self: The MessageFactory instance
                *args: Variable length argument list
                **kwargs: Arbitrary keyword arguments
            """
            original_init(self, *args, **kwargs)
            
            # Add GetPrototype if it doesn't exist
            if not hasattr(self, 'GetPrototype'):
                def get_prototype(self, descriptor):
                    """Add GetPrototype method to MessageFactory instances.
                    
                    This method provides a GetPrototype implementation that works
                    across different protobuf versions by trying multiple fallback methods.
                    
                    Args:
                        self: The MessageFactory instance
                        descriptor: The protobuf descriptor to get prototype for
                    
                    Returns:
                        A message class or dummy message for the given descriptor
                    """
                    try:
                        # Try the modern method
                        return self._GetPrototype(descriptor)
                    except AttributeError:
                        try:
                            # Try the older method
                            from google.protobuf import message_factory
                            return message_factory.GetMessageClass(descriptor)
                        except (ImportError, AttributeError):
                            # Ultimate fallback - create a dummy class
                            class DummyMessage:
                                DESCRIPTOR = descriptor
                                @classmethod
                                def FromString(cls, s):
                                    return cls()
                            return DummyMessage
                
                # Bind the method to the instance
                self.GetPrototype = get_prototype.__get__(self)
        
        # Apply the patch
        google.protobuf.message_factory.MessageFactory.__init__ = patched_init
        
        # Also patch the module-level function if needed
        if not hasattr(google.protobuf.message_factory, 'GetPrototype'):
            def module_get_prototype(descriptor):
                """Module-level GetPrototype function for protobuf compatibility.
                
                This function provides a module-level GetPrototype implementation
                that works across different protobuf versions.
                
                Args:
                    descriptor: The protobuf descriptor to get prototype for
                
                Returns:
                    A message class or dynamic message for the given descriptor
                """
                try:
                    return google.protobuf.message_factory.GetMessageClass(descriptor)
                except AttributeError:
                    # Create a dynamic message class
                    from google.protobuf import descriptor_pb2
                    from google.protobuf.message import Message
                    
                    class DynamicMessage(Message):
                        DESCRIPTOR = descriptor
                        
                        def __init__(self, **kwargs):
                            super().__init__(**kwargs)
                        
                        @classmethod
                        def FromString(cls, s):
                            return cls()
                    
                    return DynamicMessage
            
            google.protobuf.message_factory.GetPrototype = module_get_prototype
    
except ImportError:
    # protobuf not installed, nothing to patch
    pass
except Exception as e:
    print(f"⚠️ Protobuf patch warning: {e}", file=sys.stderr)

from time import sleep

from PKDevTools.classes import log as log
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes.FunctionTimeouts import ping
from PKDevTools.classes.DebugConfig import DebugConfigManager

from pkscreener import Imports
from pkscreener.classes.MarketMonitor import MarketMonitor
from pkscreener.classes.PKAnalytics import PKAnalyticsService
import pkscreener.classes.ConfigManager as ConfigManager
from PKDevTools.classes import Archiver

if __name__ == '__main__':
    multiprocessing.freeze_support()
    from unittest.mock import patch
    patch("multiprocessing.resource_tracker.register", lambda *args, **kwargs: None)


# =============================================================================
# ARGUMENT PARSER
# =============================================================================

class ArgumentParser:
    """Handles command line argument parsing for PKScreener.
    
    This class provides static methods to create and configure the argument
    parser for the PKScreener CLI application, defining all available command
    line options and their behaviors.
    """
    
    @staticmethod
    def create_parser():
        """Create and configure the argument parser.
        
        This method creates an ArgumentParser instance with all available command
        line options for PKScreener, including scanning, monitoring, backtesting,
        and telegram integration options.
        
        Returns:
            argparse.ArgumentParser: Configured argument parser instance
        """
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
    """Controls output (stdout/stderr) for production mode.
    
    This class provides methods to disable or enable system output streams,
    which is useful for production builds where console output should be suppressed.
    It uses a decorator pattern to conditionally execute print and input functions.
    """
    
    _print_enabled = False
    _original_stdout = None
    _original__stdout = None
    _devnull_stdout = None
    _devnull__stdout = None
    
    @staticmethod
    def _decorator(func):
        """Decorator to conditionally execute print/input functions.
        
        This decorator wraps a function (print or input) and only executes it
        if output is currently enabled.
        
        Args:
            func (callable): The function to decorate (print or input)
        
        Returns:
            callable: Wrapped function that checks output state before executing
        """
        def new_func(*args, **kwargs):
            if OutputController._print_enabled:
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    default_logger().debug(e, exc_info=True)
        return new_func
    
    @classmethod
    def disable_output(cls, disable_input=True, disable=True):
        """Disable or enable system output.
        
        This method redirects stdout to devnull and optionally disables input
        functions to suppress console output in production mode.
        
        Args:
            disable_input (bool, optional): Whether to also disable input functions.
                Defaults to True.
            disable (bool, optional): True to disable output, False to re-enable.
                Defaults to True.
        """
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
    """Handles logging configuration for the application.
    
    This class provides static methods to configure logging for PKScreener,
    including setting up log file paths and configuring log levels.
    """
    
    @staticmethod
    def get_log_file_path():
        """Get the path for the log file.
        
        This method determines the appropriate location for the log file,
        preferring the user data directory and falling back to temp directory.
        
        Returns:
            str: Path to the log file
        """
        try:
            file_path = os.path.join(Archiver.get_user_data_dir(), "pkscreener-logs.txt")
            with open(file_path, "w") as f:
                f.write("Logger file for pkscreener!")
        except Exception:
            file_path = os.path.join(tempfile.gettempdir(), "pkscreener-logs.txt")
        return file_path
    
    @staticmethod
    def setup(should_log=False, trace=False):
        """Setup logging based on configuration.
        
        This method configures the logging system for the application,
        setting up log levels, file output, and optional trace mode.
        
        Args:
            should_log (bool, optional): Whether logging should be enabled.
                Defaults to False.
            trace (bool, optional): Whether to enable trace-level logging.
                Defaults to False.
        """
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
    """Checks and warns about missing dependencies.
    
    This class provides methods to verify that required dependencies
    (like TA-Lib) are installed and to warn users about missing packages.
    """
    
    @staticmethod
    def warn_about_dependencies():
        """Check for required dependencies and warn if missing.
        
        This method checks for TA-Lib and pandas_ta_classic dependencies,
        displaying appropriate warnings and fallback information to the user.
        """
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
    """Manages the main application execution flow.
    
    This class orchestrates the entire execution of the PKScreener application,
    handling different modes (standard scan, intraday analysis, test mode, monitor mode)
    and managing the flow of data between components.
    
    Attributes:
        config_manager: Configuration manager instance
        args: Parsed command line arguments
        arg_parser: Argument parser instance
        results: Store for scan results
        result_stocks: Store for result stock symbols
        plain_results: Store for plain results data
        db_timestamp: Database timestamp for monitoring
        elapsed_time: Elapsed time for current operation
        start_time: Start time of current operation
    """
    
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
        """Run the main application.
        
        This method determines the appropriate execution mode based on command
        line arguments and routes to the correct handler method.
        """
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
            if str(self.args.options).upper().startswith("C") or "C:" in str(self.args.options).upper():
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
        """Refresh arguments from parser.
        
        This method re-parses command line arguments to ensure the latest
        values are used, especially after potential modifications.
        
        Returns:
            argparse.Namespace: Refreshed arguments
        """
        args = _get_debug_args()
        if not isinstance(args, argparse.Namespace) and not hasattr(args, "side_effect"):
            argsv = self.arg_parser.parse_known_args(args=args)
            args = argsv[0]
        if args is not None and not args.exit and not args.monitor:
            argsv = self.arg_parser.parse_known_args()
            args = argsv[0]
        return args
    
    def _setup_user_and_timestamp(self):
        """Setup user ID and trigger timestamp.
        
        This method configures the user ID for Telegram notifications and
        sets up the trigger timestamp for scheduled operations.
        """
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
        """Update progress status for display.
        
        This method updates the progress status text shown during scans
        based on the current menu options being executed.
        
        Args:
            monitor_options (str, optional): Monitor options to use instead of args
            
        Returns:
            tuple: Updated args and choices string
        """
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
        """Run intraday analysis reports.
        
        This method executes the intraday analysis mode, generating reports
        comparing morning and end-of-day data.
        """
        from pkscreener.classes.cli.PKCliRunner import IntradayAnalysisRunner
        runner = IntradayAnalysisRunner(self.config_manager, self.args)
        runner.generate_reports()
    
    def _test_all_options(self, menus, main_func):
        """Test all menu options.
        
        This method runs through all available menu options for testing purposes,
        executing scans for each predefined menu choice.
        
        Args:
            menus: Menu options object
            main_func: Main function to execute for each option
        """
        all_menus, _ = menus.allMenus(index=0)
        for scan_option in all_menus:
            self.args.options = f"{scan_option}:SBIN,"
            main_func(userArgs=self.args)
        sys.exit(0)
    
    def _run_standard_scan(self, main, close_workers, is_interrupted,
                          update_menu_hierarchy, refresh_data):
        """Run standard scanning mode.
        
        This method executes the standard screening process, handling monitor mode,
        piped scans, and result processing.
        
        Args:
            main: Main scanning function
            close_workers: Function to close worker processes
            is_interrupted: Function to check for interruption
            update_menu_hierarchy: Function to update menu hierarchy
            refresh_data: Function to refresh stock data
        """
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
        """Setup monitor mode.
        
        This method configures the application for monitor mode, which continuously
        watches for screening opportunities.
        
        Args:
            cli_runner: CLI runner instance
            refresh_data: Function to refresh stock data
        """
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
        """Execute the scanning process.
        
        This method performs the actual stock screening, handling piped scans
        and managing result data.
        
        Args:
            main: Main scanning function
            close_workers: Function to close worker processes
            is_interrupted: Function to check for interruption
            update_menu_hierarchy: Function to update menu hierarchy
            cli_runner: CLI runner instance
            monitor_option_org: Original monitor option
        """
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
        """Process scan results.
        
        This method processes the scan results, removing duplicates, saving
        results for monitoring, and checking market closure.
        
        Args:
            update_menu_hierarchy: Function to update menu hierarchy
            monitor_option_org: Original monitor option
        """
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
        """Check if market has closed and exit if needed.
        
        This method checks whether the market has closed and exits the monitor
        mode if appropriate.
        """
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
    """Get debug arguments from command line - fixed version.
    
    This function retrieves command line arguments, handling quoted strings
    and spaces properly using shell-style parsing.
    
    Returns:
        list: List of command line arguments
    """
    import sys
    import shlex
    
    try:
        if args is not None:
            # If args is already set, use it
            if isinstance(args, str):
                # Split the string properly, respecting quotes
                return shlex.split(args)
            return list(args) if args else []
    except NameError:
        # Get from sys.argv
        args = sys.argv[1:]
        # If there's only one argument and it contains spaces, split it
        if len(args) == 1 and ' ' in args[0]:
            return shlex.split(args[0])
        return args
    except Exception:
        pass
    return []


def _exit_gracefully(config_manager, arg_parser):
    """Perform graceful exit cleanup.
    
    This function performs cleanup operations before exiting the application,
    including removing temporary files and resetting configuration.
    
    Args:
        config_manager: Configuration manager instance
        arg_parser: Argument parser instance for accessing arguments
    """
    try:
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
        if args is not None and args.options is not None and not str(args.options).upper().startswith("T"):
            resetConfigToDefault(force=True)
        
        if "PKDevTools_Default_Log_Level" in os.environ.keys():
            if args is None or (args is not None and args.options is not None and "|" not in str(args.options)):
                del os.environ['PKDevTools_Default_Log_Level']
        
        config_manager.logsEnabled = False
        config_manager.setConfig(ConfigManager.parser, default=True, showFileCreatedText=False)
    except RuntimeError:
        OutputControls().printOutput(
            f"{colorText.WARN}If you're running from within docker, please run like this:{colorText.END}\n"
            f"{colorText.FAIL}docker run -it pkjmesra/pkscreener:latest\n{colorText.END}"
        )


def _remove_old_instances():
    """Remove old CLI instances.
    
    This function removes old executable instances of pkscreenercli to prevent
    conflicts and ensure only the current version is running.
    """
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
argsv = argParser.parse_known_args(args=args) if args is not None else argParser.parse_known_args()
args = argsv[0]


def runApplication():
    """Run the main application.
    
    This function creates an ApplicationRunner instance and executes the
    main application logic.
    """
    global args
    runner = ApplicationRunner(configManager, args, argParser)
    runner.run()


def runApplicationForScreening():
    """Run application in screening mode.
    
    This function handles the screening mode execution, including scheduling
    for cron jobs and handling errors appropriately.
    """
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
    """Schedule next run based on cron interval.
    
    This function manages the scheduling of recurring scans, handling
    non-trading hours by sleeping until market open.
    """
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
    """Main CLI entry point.
    
    This is the main function for the PKScreener CLI application. It handles
    initial setup, argument parsing, dependency checking, and routes to the
    appropriate execution mode.
    
    The function performs the following steps:
    1. Sets up multiprocessing for macOS
    2. Configures debug settings
    3. Validates terms of service acceptance
    4. Configures logging
    5. Sets up monitoring if requested
    6. Checks dependencies
    7. Validates user registration for premium features
    8. Routes to appropriate execution mode (normal, bot, telegram, test)
    
    Returns:
        None
    """
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
        debug_config_path = os.path.join(Archiver.get_user_data_dir(), "debug_config.ini")
        if os.path.exists(debug_config_path) and os.path.isfile(debug_config_path):
            manager = DebugConfigManager()
            config = manager.load_from_file(debug_config_path)
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
        PKUserRegistration.populateSavedUserCreds()
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
        
        auth_not_required = LoggedIn or args.telegram or args.bot or args.systemlaunched or args.testbuild
        if not auth_not_required:
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
        if "RUNNER" in os.environ.keys():
            OutputControls().printOutput(e)
            traceback.print_exc()
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
    """Main entry point when script is executed directly.
    
    This block checks that the repository is the official PKScreener repository
    before executing, then calls the main CLI function.
    """
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
    except Exception as e:
        default_logger().debug(e, exc_info=True)
        if args.log:
            traceback.print_exc()
        from pkscreener.globals import closeWorkersAndExit
        closeWorkersAndExit()
        _exit_gracefully(configManager, argParser)
        sys.exit(0)