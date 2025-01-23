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
import logging
import os
import sys
import builtins
from unittest.mock import patch,ANY,MagicMock, call
from unittest import mock
import unittest
import csv
import re
import tempfile
from pkscreener.pkscreenercli import logFilePath, setupLogger, warnAboutDependencies, runApplication, updateProgressStatus, generateIntradayAnalysisReports, saveSendFinalOutcomeDataframe, checkIntradayComponent, updateConfigDurations, pipeResults, removeOldInstances, updateConfig, pkscreenercli, runApplicationForScreening

import pytest
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger
import setuptools.dist
from pkscreener import pkscreenercli, Imports
from pkscreener.classes.PKScanRunner import PKScanRunner

class TestPKScreenerFunctions(unittest.TestCase):

    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    def test_logFilePath(self, mock_get_user_data_dir):
        with patch("builtins.open", return_value=None):
            # Positive case
            mock_get_user_data_dir.return_value = "/mock/path"
            expected_path = os.path.join("/mock/path", "pkscreener-logs.txt")
            result = logFilePath()
            self.assertEqual(result, expected_path)
            self.assertFalse(os.path.exists(result))

        # Negative case (simulating an exception)
        with patch('builtins.open', side_effect=Exception("Error")):
            result = logFilePath()
            self.assertIn(tempfile.gettempdir(), result)

    @patch('os.remove')
    @patch('os.path.exists', return_value=True)
    @patch('PKDevTools.classes.log.setup_custom_logger')
    def test_setupLogger(self, mock_setup_custom_logger, mock_exists, mock_remove):
        with patch('pkscreener.pkscreenercli.logFilePath', return_value="mock_path"):
            setupLogger(shouldLog=True, trace=False)
            mock_remove.assert_called_once_with("mock_path")
            mock_setup_custom_logger.assert_called_once()

        # Test logger not set up
        setupLogger(shouldLog=False)
        self.assertNotIn('PKDevTools_Default_Log_Level', os.environ)

    @patch.dict(Imports, {"talib": False, "pandas_ta": False})
    def test_warnAboutDependencies(self):
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput') as mock_output_controls:
            # Positive case: TA-Lib not installed, pandas_ta installed
            warnAboutDependencies()
            mock_output_controls.assert_called()

        # Negative case: Neither installed
        with patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput') as mock_input:
                from PKDevTools.classes.OutputControls import OutputControls
                prevValue = OutputControls().enableUserInput
                OutputControls().enableUserInput = True
                warnAboutDependencies()
                OutputControls().enableUserInput = prevValue
                mock_input.assert_called()

    @patch('pkscreener.globals.main')
    def test_runApplication(self, mock_main):
        mock_main.return_value = (MagicMock(), MagicMock())
        with patch('pkscreener.pkscreenercli.get_debug_args', return_value=MagicMock()):
            runApplication()
            mock_main.assert_called()

    def test_updateProgressStatus(self):
        args = MagicMock()
        args.options = "X:12:9:2.5:>|X:12:30:1:"
        args.systemlaunched = True
        args, choices = updateProgressStatus(args)
        self.assertIn("Running", args.progressstatus)

    @patch('pkscreener.globals.main')
    def test_generateIntradayAnalysisReports(self, mock_main):
        args = MagicMock()
        args.options = "X:12:9:2.5:>|X:12:30:1:"
        mock_main.return_value = (MagicMock(), MagicMock())
        args.pipedmenus = None
        with patch('pkscreener.globals.resetUserMenuChoiceOptions'):
            generateIntradayAnalysisReports(args)
            mock_main.assert_called()

    def test_saveSendFinalOutcomeDataframe(self):
        # Positive case
        df = MagicMock()
        df.empty = False
        df.columns = ['Pattern', 'LTP', 'LTP@Alert', 'SqrOffLTP', 'SqrOffDiff', 'EoDDiff', 'DayHigh', 'DayHighDiff']
        saveSendFinalOutcomeDataframe(df)

        # Negative case
        df.empty = True
        saveSendFinalOutcomeDataframe(df)

    def test_checkIntradayComponent(self):
        args = MagicMock()
        monitorOption = "mock:monitorOption"
        result = checkIntradayComponent(args, monitorOption)
        self.assertIn("mock", result)

    def test_updateConfigDurations(self):
        args = MagicMock()
        args.options = "X:12:9:2.5:i 1m>|X:12:30:1:"
        updateConfigDurations(args)
        self.assertIsNotNone(args.intraday)

    def test_pipeResults(self):
        args = MagicMock()
        args.options = "X:12:9:2.5:i 1m>|X:12:30:1:"
        import pandas as pd
        prevOutput = pd.DataFrame(["Dummy"],columns=["Stock"])
        result = pipeResults(prevOutput, args)
        self.assertTrue(result)

    @patch('glob.glob')
    @patch('os.remove')
    def test_removeOldInstances(self, mock_remove, mock_glob):
        mock_glob.return_value = ["pkscreenercli_test"]
        removeOldInstances()
        mock_remove.assert_called()

    @patch('pkscreener.pkscreenercli.configManager')
    def test_updateConfig(self, mock_config):
        args = MagicMock()
        args.intraday = "1m"
        updateConfig(args)
        mock_config.toggleConfig.assert_called()

    @patch('pkscreener.pkscreenercli.runApplicationForScreening')
    def test_pkscreenercli(self, mock_run_application):
        args = MagicMock()
        args.options = "mock:options"
        with pytest.raises((SystemExit)):
            pkscreenercli.pkscreenercli()
            mock_run_application.assert_called()

    # @patch('pkscreener.pkscreenercli.runApplicationForScreening')
    # def test_runApplicationForScreening(self, mock_run_application):
    #     args = MagicMock()
    #     args.croninterval = None
    #     with pytest.raises((SystemExit)):
    #         runApplicationForScreening()
    #         mock_run_application.assert_called()

# Mocking necessary functions or dependencies
@pytest.fixture(autouse=True)
def mock_dependencies():
    pkscreenercli.args.exit = True
    # pkscreenercli.args.download = False
    pkscreenercli.args.answerdefault = "Y"
    pkscreenercli.args.testbuild = True
    with patch("pkscreener.globals.main"):
        with patch("pkscreener.classes.Utility.tools.clearScreen"):
            yield


def patched_caller(*args, **kwargs):
    if kwargs is not None:
        userArgs = kwargs["userArgs"]
        maxCount = userArgs.options
        pkscreenercli.args.options = str(int(maxCount) - 1)
        if int(pkscreenercli.args.options) == 0:
            pkscreenercli.args.exit = True
    else:
        pkscreenercli.args.exit = True


# Positive test case - Test if pkscreenercli function runs in download-only mode
def test_pkscreenercli_download_only_mode():
    with patch("pkscreener.globals.main") as mock_main:
        with pytest.raises(SystemExit):
            pkscreenercli.args.download = True
            pkscreenercli.pkscreenercli()
            mock_main.assert_called_once_with(
                userArgs=ANY
            )


# Positive test case - Test if pkscreenercli function runs with cron interval
def test_pkscreenercli_with_cron_interval():
    pkscreenercli.args.croninterval = "3"
    with patch("pkscreener.globals.main", new=patched_caller) as mock_main:
        with patch(
            "PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime"
        ) as mock_is_trading_time:
            mock_is_trading_time.return_value = True
            pkscreenercli.args.exit = False
            pkscreenercli.args.options = "2"
            with pytest.raises(SystemExit):
                pkscreenercli.pkscreenercli()
                assert mock_main.call_count == 2


# Positive test case - Test if pkscreenercli function runs without cron interval
def test_pkscreenercli_with_cron_interval_preopen():
    pkscreenercli.args.croninterval = "3"
    with patch("pkscreener.globals.main", new=patched_caller) as mock_main:
        with patch(
            "PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime"
        ) as mock_is_trading_time:
            mock_is_trading_time.return_value = False
            with patch(
                "PKDevTools.classes.PKDateUtilities.PKDateUtilities.secondsBeforeOpenTime"
            ) as mock_secondsBeforeOpenTime:
                mock_secondsBeforeOpenTime.return_value = -3601
                pkscreenercli.args.exit = False
                pkscreenercli.args.options = "1"
                with pytest.raises(SystemExit):
                    pkscreenercli.pkscreenercli()
                    assert mock_main.call_count == 1


# Positive test case - Test if pkscreenercli function runs without any errors
def test_pkscreenercli_exits():
    with patch("pkscreener.globals.main") as mock_main:
        with pytest.raises(SystemExit):
            pkscreenercli.pkscreenercli()
            mock_main.assert_called_once()


def test_intraday_enabled():
    with patch(
        "PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime"
    ) as mock_is_trading_time:
        with patch(
            "pkscreener.classes.ConfigManager.tools.restartRequestsCache"
        ) as mock_cache:
            with pytest.raises(SystemExit):
                pkscreenercli.args.intraday = "15m"
                mock_is_trading_time.return_value = False
                pkscreenercli.pkscreenercli()
                mock_cache.assert_called_once()


# Positive test case - Test if setupLogger function is called when logging is enabled
def test_setupLogger_logging_enabled():
    with patch("PKDevTools.classes.log.setup_custom_logger") as mock_setup_logger:
        with patch(
            "PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime"
        ) as mock_is_trading_time:
            with pytest.raises(SystemExit):
                pkscreenercli.args.log = True
                pkscreenercli.args.prodbuild = False
                pkscreenercli.args.answerdefault = None
                mock_is_trading_time.return_value = False
                with patch("builtins.input") as mock_input:
                    pkscreenercli.pkscreenercli()
                    mock_setup_logger.assert_called_once()
                    assert default_logger().level == logging.DEBUG
                    mock_input.assert_called_once()


# Negative test case - Test if setupLogger function is not called when logging is disabled
def test_setupLogger_logging_disabled():
    with patch("PKDevTools.classes.log.setup_custom_logger") as mock_setup_logger:
        with patch(
            "PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime"
        ) as mock_is_trading_time:
            mock_is_trading_time.return_value = False
            mock_setup_logger.assert_not_called()
            assert default_logger().level in (logging.NOTSET, logging.DEBUG)

def test_setupLogger_shouldNotLog():
    with patch("PKDevTools.classes.log.setup_custom_logger") as mock_setup_logger:
        os.environ["PKDevTools_Default_Log_Level"] = "1"
        pkscreenercli.setupLogger(False,True)
        mock_setup_logger.assert_not_called()
        assert 'PKDevTools_Default_Log_Level' not in os.environ.keys()

def test_setupLogger_LogFileDoesNotExist():
    try:
        filePath = pkscreenercli.logFilePath()
        os.remove(pkscreenercli.logFilePath())
    except:
        pass
    with patch("PKDevTools.classes.log.setup_custom_logger") as mock_setup_logger:
        with patch("pkscreener.pkscreenercli.logFilePath") as mock_file_path:
            mock_file_path.return_value = filePath
            pkscreenercli.setupLogger(True,True)
            mock_setup_logger.assert_called()

# Positive test case - Test if pkscreenercli function runs in test-build mode
def test_pkscreenercli_test_build_mode():
    with patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit):
            pkscreenercli.args.testbuild = True
            pkscreenercli.pkscreenercli()
            mock_print.assert_called_with(
                colorText.FAIL
                + "  [+] Started in TestBuild mode!"
                + colorText.END
            )


def test_pkscreenercli_prodbuild_mode():
    with patch("pkscreener.pkscreenercli.disableSysOut") as mock_disableSysOut:
        pkscreenercli.args.prodbuild = True
        with pytest.raises(SystemExit):
            pkscreenercli.pkscreenercli()
            mock_disableSysOut.assert_called_once()
    try:
        import signal

        signal.signal(signal.SIGBREAK, PKScanRunner.shutdown)
        signal.signal(signal.SIGTERM, PKScanRunner.shutdown)
    except Exception:# pragma: no cover
        pass

def test_pkscreenercli_decorator():
    with patch("builtins.print") as mock_print:
        builtins.print = pkscreenercli.decorator(builtins.print)
        pkscreenercli.printenabled = False
        print("something")
        mock_print.assert_not_called()
        pkscreenercli.printenabled = True
        print("something else")
        mock_print.assert_called()

def test_pkscreenercli_disablesysout():
    originalStdOut = sys.stdout
    original__stdout = sys.__stdout__
    with patch("pkscreener.pkscreenercli.decorator") as mock_decorator:
        pkscreenercli.originalStdOut = None
        pkscreenercli.disableSysOut(disable=True)
        mock_decorator.assert_called()
        assert sys.stdout != originalStdOut
        assert sys.__stdout__ != original__stdout
    with patch("pkscreener.pkscreenercli.decorator") as mock_disabled_decorator:        
        pkscreenercli.disableSysOut(disable=False)
        mock_disabled_decorator.assert_not_called()
        assert sys.stdout == originalStdOut
        assert sys.__stdout__ == original__stdout
    with patch("pkscreener.pkscreenercli.decorator") as mock_disabled_decorator:        
        pkscreenercli.originalStdOut = None
        pkscreenercli.disableSysOut(input=False, disable=True)
        mock_disabled_decorator.assert_called()
        mock_disabled_decorator.call_count = 1

def test_pkscreenercli_warnAboutDependencies():
    with patch.dict("pkscreener.Imports", {"talib": False}):
        with patch("builtins.print") as mock_print:
            with patch("builtins.input") as mock_input:
                pkscreenercli.warnAboutDependencies()
                mock_print.assert_called()
                mock_print.call_count = 2
                mock_input.assert_not_called()
    with patch.dict("pkscreener.Imports", {"talib": False, "pandas_ta":False}):
        with patch("builtins.print") as mock_print:
            with patch("builtins.input") as mock_input:
                from PKDevTools.classes.OutputControls import OutputControls
                prevValue = OutputControls().enableUserInput
                OutputControls().enableUserInput = True
                pkscreenercli.warnAboutDependencies()
                OutputControls().enableUserInput = prevValue
                mock_print.assert_called()
                mock_print.call_count = 2
                mock_input.assert_called()
    with patch.dict("pkscreener.Imports", {"talib": True, "pandas_ta":True}):
        with patch("builtins.print") as mock_print:
            with patch("builtins.input") as mock_input:
                pkscreenercli.warnAboutDependencies()
                mock_print.assert_not_called()
                mock_input.assert_not_called()

def test_pkscreenercli_multiprocessing_patch():
    with patch("sys.platform") as mock_platform:
        mock_platform.return_value = "darwin"
        with patch("multiprocessing.set_start_method") as mock_mp:
            with pytest.raises((SystemExit)):
                pkscreenercli.pkscreenercli()
                mock_mp.assert_called_once_with("fork")
        
        mock_platform.return_value = "linux"
        with patch("sys.platform.startswith") as mock_platform_starts_with:
            mock_platform_starts_with.return_value = False
            with patch("multiprocessing.set_start_method") as mock_mp:
                with pytest.raises((SystemExit)):
                    pkscreenercli.pkscreenercli()
                    mock_mp.assert_not_called()

def test_pkscreenercli_clearscreen_is_called_whenstdOut_NotSet():
    with patch("pkscreener.classes.Utility.tools.clearScreen") as mock_clearscreen:
        with pytest.raises((SystemExit)):
            pkscreenercli.pkscreenercli()
            mock_clearscreen.assert_called_once()

def test_pkscreenercli_setConfig_is_called_if_NotSet():
    with patch("pkscreener.classes.ConfigManager.tools.checkConfigFile") as mock_chkConfig:
        mock_chkConfig.return_value = False
        with patch("pkscreener.classes.ConfigManager.tools.setConfig") as mock_setConfig:
            with pytest.raises((SystemExit)):
                pkscreenercli.pkscreenercli()
                mock_setConfig.assert_called_once()

from pkscreener.pkscreenercli import csv_split,re_split, get_debug_args

class TestCsvAndReSplit(unittest.TestCase):

    def test_csv_split(self):
        # Positive test case
        self.assertEqual(csv_split("a b c"), ['a', 'b', 'c'])
        self.assertEqual(csv_split("1,2,3"), ['1,2,3'])  # Note: delimiter is space, so no split happens

        # Negative test case
        self.assertNotEqual(csv_split(""), ['a', 'b', 'c'])  # Empty string should not match any values

    def test_re_split(self):
        # Positive test cases
        self.assertEqual(re_split('a "b c" d'), ['a', 'b c', 'd'])
        self.assertEqual(re_split("'single quoted' text"), ['single quoted', 'text'])
        self.assertEqual(re_split('escaped \\"quote\\"'), ['escaped', '"quote"'])
        self.assertEqual(re_split('-e -a Y -o "X:12:23:>|X:0:5:0:30:i 1m:"'), ['-e', '-a','Y','-o','X:12:23:>|X:0:5:0:30:i 1m:'])
        self.assertEqual(re_split('-e -a Y -o "X:12:23:i 15m:>|X:0:5:0:30:i 1m:"'), ['-e', '-a','Y','-o','X:12:23:i 15m:>|X:0:5:0:30:i 1m:'])
        self.assertEqual(re_split('-e -a Y -o "X:12:23:i 15m:>|X:0:5:0:30:"'), ['-e', '-a','Y','-o','X:12:23:i 15m:>|X:0:5:0:30:'])
        self.assertEqual(re_split("-e -a Y -o 'X:12:23:>|X:0:5:0:30:i 1m:'"), ['-e', '-a','Y','-o','X:12:23:>|X:0:5:0:30:i 1m:'])
        self.assertEqual(re_split("-e -a Y -o 'X:12:23:i 15m:>|X:0:5:0:30:i 1m:'"), ['-e', '-a','Y','-o','X:12:23:i 15m:>|X:0:5:0:30:i 1m:'])
        self.assertEqual(re_split("-e -a Y -o 'X:12:23:i 15m:>|X:0:5:0:30:'"), ['-e', '-a','Y','-o','X:12:23:i 15m:>|X:0:5:0:30:'])
        self.assertEqual(re_split("-e -a Y -o 'X:12:23:i 15m:>|X:0:5:0:30:' -l"), ['-e', '-a','Y','-o','X:12:23:i 15m:>|X:0:5:0:30:','-l'])

        # Negative test cases
        self.assertEqual(re_split('"unmatched quote'), ['"unmatched', 'quote'])  # Should return the unmatched quote as is
        self.assertEqual(re_split(""), [])  # Empty string should return an empty list

    def test_get_debug_args(self):
        # Mocking sys.argv for testing
        original_argv = sys.argv
        
        try:
            import argparse
            # Positive test case
            sys.argv = ['script_name', 'arg1 arg2']
            self.assertTrue(isinstance(get_debug_args(),argparse.Namespace))
            
            # Another positive test case
            sys.argv = ['script_name', '"arg with spaces"']
            self.assertTrue(isinstance(get_debug_args(),argparse.Namespace))
            
            # Negative test case
            sys.argv = ['script_name']
            self.assertTrue(isinstance(get_debug_args(),argparse.Namespace))
            
            # Check for invalid input
            sys.argv = ['script_name', '']
            self.assertTrue(isinstance(get_debug_args(),argparse.Namespace))

        finally:
            sys.argv = original_argv  # Restore original argv

from pkscreener.pkscreenercli import configManager, exitGracefully
from pkscreener.classes import ConfigManager
class TestExitGracefully(unittest.TestCase):

    @patch('os.remove')
    @patch('os.path.join')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('pkscreener.globals.resetConfigToDefault')
    @patch('argparse.ArgumentParser.parse_known_args')
    @patch('pkscreener.classes.ConfigManager.tools.setConfig')
    def test_exitGracefully_success(self, mock_setConfig, mock_parse_known_args, mock_resetConfigToDefault,
                                     mock_get_user_data_dir, mock_path_join, mock_remove):
        # Setup mocks
        mock_get_user_data_dir.return_value = '/mock/user/data/dir'
        mock_path_join.return_value = '/mock/user/data/dir/monitor_outputs'
        mock_parse_known_args.return_value = (MagicMock(options='SomeOption'),)
        configManager.maxDashboardWidgetsPerRow = 2
        configManager.maxNumResultRowsInMonitor = 3
        
        # Call the function
        exitGracefully()

        # Check if files were attempted to be removed
        expected_calls = [call('/mock/user/data/dir/monitor_outputs_0.txt'),
                          call('/mock/user/data/dir/monitor_outputs_1.txt'),
                          call('/mock/user/data/dir/monitor_outputs_2.txt'),
                          call('/mock/user/data/dir/monitor_outputs_3.txt'),
                          call('/mock/user/data/dir/monitor_outputs_4.txt'),
                          call('/mock/user/data/dir/monitor_outputs_5.txt')]
        mock_remove.assert_has_calls(expected_calls, any_order=True)

        # Check if resetConfigToDefault was called
        mock_resetConfigToDefault.assert_called_once_with(force=True)

        # Check if setConfig was called with correct parameters
        mock_setConfig.assert_called_once_with(ConfigManager.parser, default=True, showFileCreatedText=False)

    @patch('os.remove')
    @patch('os.path.join')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('pkscreener.globals.resetConfigToDefault')
    @patch('argparse.ArgumentParser.parse_known_args')
    @patch('pkscreener.classes.ConfigManager.tools.setConfig')
    def test_exitGracefully_no_files(self, mock_setConfig, mock_parse_known_args, mock_resetConfigToDefault,
                                      mock_get_user_data_dir, mock_path_join, mock_remove):
        # Setup mocks
        mock_get_user_data_dir.return_value = '/mock/user/data/dir'
        mock_path_join.return_value = None  # Simulate no file path
        mock_parse_known_args.return_value = (MagicMock(options='SomeOption'),)

        # Call the function
        exitGracefully()

        # Check that remove was never called
        mock_remove.assert_not_called()
        mock_resetConfigToDefault.assert_not_called()

    @patch('os.remove')
    @patch('os.path.join')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('pkscreener.globals.resetConfigToDefault')
    @patch('argparse.ArgumentParser.parse_known_args')
    @patch('pkscreener.classes.ConfigManager.tools.setConfig')
    def test_exitGracefully_runtime_error(self, mock_setConfig, mock_parse_known_args, mock_resetConfigToDefault,
                                           mock_get_user_data_dir, mock_path_join, mock_remove):
        # Setup mocks
        mock_setConfig.side_effect = RuntimeError("Test RuntimeError")
        mock_parse_known_args.return_value = (MagicMock(options='SomeOption'),)

        # Call the function
        with patch("builtins.print") as mock_print:
            exitGracefully()
            mock_print.assert_called_with("\x1b[33mIf you're running from within docker, please run like this:\x1b[0m\n\x1b[31mdocker run -it pkjmesra/pkscreener:latest\n\x1b[0m", sep=' ', end='\n', flush=False)
            

    @patch('os.remove')
    @patch('os.path.join')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('pkscreener.globals.resetConfigToDefault')
    @patch('argparse.ArgumentParser.parse_known_args')
    @patch('pkscreener.classes.ConfigManager.tools.setConfig')
    def test_exitGracefully_invalid_option(self, mock_setConfig, mock_parse_known_args, mock_resetConfigToDefault,
                                            mock_get_user_data_dir, mock_path_join, mock_remove):
        # Setup mocks
        mock_get_user_data_dir.return_value = '/mock/user/data/dir'
        mock_path_join.return_value = '/mock/user/data/dir/monitor_outputs'
        mock_parse_known_args.return_value = (MagicMock(options='T-InvalidOption'),)

        # Call the function
        exitGracefully()

        # Check that resetConfigToDefault was not called
        mock_resetConfigToDefault.assert_not_called()

# def test_intraday_args_are_parsed():
#     with patch("pkscreener.globals.main") as mock_main:
#         sys.argv[0] = "launcher"
#         sys.argv[1] = "-e -a Y -p -o 'X:0:0:SBIN:i 1m'"
#         mock_main.return_value = (MagicMock(), MagicMock())
#         pkscreenercli.pkscreenercli()
#         mock_main.assert_called_with(None)

# def test_pkscreenercli_monitor_mode():
#     with patch("builtins.print") as mock_print:
#         pkscreenercli.args.monitor = True
#         pkscreenercli.pkscreenercli()
#         mock_print.assert_called_with('\x1b[32mBy using this Software and passing a value for [answerdefault=Y], you agree to\n[+] having read through the Disclaimer\x1b[0m (\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b\\https://pkjmesra.github.io/PKScreener/Disclaimer.txt\x1b]8;;\x1b\\\x1b[0m)\n[+]\x1b[32m and accept Terms Of Service \x1b[0m(\x1b[97m\x1b]8;;https://pkjmesra.github.io/PKScreener/tos.txt\x1b\\https://pkjmesra.github.io/PKScreener/tos.txt\x1b]8;;\x1b\\\x1b[0m)\x1b[32m of PKScreener. \x1b[0m\n[+] \x1b[33mIf that is not the case, you MUST immediately terminate PKScreener by pressing Ctrl+C now!\x1b[0m', sep=' ', end=ANY, flush=False)

def test_pkscreenercli_workflow_mode_screening():
    with patch("pkscreener.pkscreenercli.disableSysOut") as mock_disableSysOut:
        with patch("pkscreener.pkscreenercli.runApplication"):
            # run_once = mock.Mock(side_effect=[True, False])
            pkscreenercli.args.v = True
            pkscreenercli.args.monitor = False
            pkscreenercli.args.croninterval = None
            pkscreenercli.args.download = False
            pkscreenercli.runApplicationForScreening()
            mock_disableSysOut.assert_called_with(disable=False)
            with pytest.raises((SystemExit)):
                # run_once = mock.Mock(side_effect=[True, False])
                pkscreenercli.args.v = False
                pkscreenercli.runApplicationForScreening()
                mock_disableSysOut.assert_not_called()

def test_pkscreenercli_cron_mode_scheduling():
    with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime") as mock_tradingtime:
        mock_tradingtime.return_value = False
        with patch("time.sleep") as mock_sleep:
            with patch("pkscreener.pkscreenercli.runApplication") as mock_runApplication:
                with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.secondsAfterCloseTime") as mock_seconds_after:
                    with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.nextRunAtDateTime") as mock_nextRun:
                        mock_nextRun.return_value = "Test Next Run Schedule"
                        with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.secondsBeforeOpenTime") as mock_seconds_before:
                            mock_seconds_after.return_value = 3601
                            mock_seconds_before.return_value = -3601
                            pkscreenercli.args.croninterval = 1
                            pkscreenercli.args.exit = True
                            pkscreenercli.args.download = False
                            with patch("pkscreener.globals.main") as mock_main:
                                pkscreenercli.scheduleNextRun()
                                # mock_sleep.assert_called_once_with(pkscreenercli.args.croninterval)
                                mock_runApplication.assert_called()


# def test_pkscreenercli_cron_std_mode_screening():
#     with patch("pkscreener.pkscreenercli.scheduleNextRun") as mock_scheduleNextRun:
#         with pytest.raises((SystemExit)):
#             pkscreenercli.args.croninterval = 99999999
#             pkscreenercli.args.download = False
#             pkscreenercli.pkscreenercli()
#             mock_scheduleNextRun.assert_called_once()

# def test_pkscreenercli_std_mode_screening():
#     with patch("pkscreener.pkscreenercli.runApplication") as mock_runApplication:
#         with pytest.raises((SystemExit)):
#             pkscreenercli.pkscreenercli()
#             mock_runApplication.assert_called_once()

# def test_pkscreenercli_cron_std_mode_screening_with_no_schedules():
#     with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime") as mock_tradingtime:
#         mock_tradingtime.return_value = True
#         with patch("time.sleep") as mock_sleep:
#             with patch("pkscreener.pkscreenercli.runApplication") as mock_runApplication:
#                 with pytest.raises((SystemExit)):
#                     pkscreenercli.args.croninterval = 99999999
#                     pkscreenercli.args.exit = True
#                     pkscreenercli.pkscreenercli()
#                     mock_runApplication.assert_called_once()
#                     mock_sleep.assert_called_once_with(3)

# def test_pkscreenercli_cron_std_mode_screening_with_schedules():
#     with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime") as mock_tradingtime:
#         mock_tradingtime.return_value = False
#         with patch("time.sleep") as mock_sleep:
#             with patch("pkscreener.pkscreenercli.runApplication") as mock_runApplication:
#                 with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.secondsAfterCloseTime") as mock_seconds:
#                     mock_seconds.return_value = 3601
#                     with pytest.raises((SystemExit)):
#                         pkscreenercli.args.croninterval = 1
#                         pkscreenercli.args.exit = True
#                         pkscreenercli.args.download = False
#                         pkscreenercli.pkscreenercli()
#                         mock_sleep.assert_called_once_with(pkscreenercli.args.croninterval)
#                         mock_runApplication.assert_called()
#                 with patch("PKDevTools.classes.PKDateUtilities.PKDateUtilities.secondsBeforeOpenTime") as mock_seconds:
#                     mock_seconds.return_value = -3601
#                     with pytest.raises((SystemExit)):
#                         pkscreenercli.args.croninterval = 1
#                         pkscreenercli.args.exit = True
#                         pkscreenercli.args.download = False
#                         pkscreenercli.pkscreenercli()
#                         mock_sleep.assert_called_once_with(pkscreenercli.args.croninterval)
#                         mock_runApplication.assert_called()