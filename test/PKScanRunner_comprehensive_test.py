"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Comprehensive tests for PKScanRunner.py to achieve 90%+ coverage.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock, PropertyMock
from argparse import Namespace
import warnings
import sys
import os
import multiprocessing
warnings.filterwarnings("ignore")


@pytest.fixture
def user_args():
    """Create user args namespace."""
    return Namespace(
        options="X:12:1",
        singlethread=False,
        monitor=None,
        intraday=None,
        runintradayanalysis=False,
        backtestdaysago=None,
        testalloptions=False,
        log=False,
        forceBacktestsForZeroResultDays=False
    )


# =============================================================================
# initDataframes Tests
# =============================================================================

class TestInitDataframes:
    """Test initDataframes method."""
    
    def test_init_dataframes_returns_tuple(self):
        """Test initDataframes returns tuple of DataFrames."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        screen_results, save_results = PKScanRunner.initDataframes()
        
        assert isinstance(screen_results, pd.DataFrame)
        assert isinstance(save_results, pd.DataFrame)
    
    def test_init_dataframes_has_correct_columns(self):
        """Test initDataframes has correct columns."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        screen_results, save_results = PKScanRunner.initDataframes()
        
        expected_columns = [
            "Stock", "Consol.", "Breakout", "LTP", "52Wk-H", "52Wk-L",
            "%Chng", "volume", "MA-Signal", "RSI", "RSIi", "Trend", "Pattern", "CCI"
        ]
        
        for col in expected_columns:
            assert col in screen_results.columns
            assert col in save_results.columns
    
    def test_init_dataframes_are_empty(self):
        """Test initDataframes returns empty DataFrames."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        screen_results, save_results = PKScanRunner.initDataframes()
        
        assert len(screen_results) == 0
        assert len(save_results) == 0


# =============================================================================
# initQueues Tests
# =============================================================================

class TestInitQueues:
    """Test initQueues method."""
    
    def test_init_queues_returns_tuple(self, user_args):
        """Test initQueues returns tuple."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        tasks_queue, results_queue, total_consumers, logging_queue = PKScanRunner.initQueues(10, user_args)
        
        assert tasks_queue is not None
        assert results_queue is not None
        assert total_consumers >= 2
        assert logging_queue is not None
    
    def test_init_queues_singlethread(self):
        """Test initQueues with singlethread."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        args = Namespace(singlethread=True)
        tasks_queue, results_queue, total_consumers, logging_queue = PKScanRunner.initQueues(10, args)
        
        # Single thread should result in 2 consumers (minimum)
        assert total_consumers >= 2
    
    def test_init_queues_no_args(self):
        """Test initQueues without userPassedArgs."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        tasks_queue, results_queue, total_consumers, logging_queue = PKScanRunner.initQueues(10, None)
        
        assert tasks_queue is not None
        assert results_queue is not None
    
    def test_init_queues_minimum_count_zero(self):
        """Test initQueues with minimumCount=0."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        tasks_queue, results_queue, total_consumers, logging_queue = PKScanRunner.initQueues(0, None)
        
        # total_consumers calculation depends on min(0, cpu_count)
        # With the code: totalConsumers = min(minimumCount, cpu_count) = min(0, N) = 0
        # Then if totalConsumers == 1: totalConsumers = 2, but 0 != 1 so it stays 0
        assert total_consumers >= 0


# =============================================================================
# populateQueues Tests
# =============================================================================

class TestPopulateQueues:
    """Test populateQueues method."""
    
    def test_populate_queues_basic(self, user_args):
        """Test populateQueues basic functionality."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        tasks_queue = multiprocessing.JoinableQueue()
        items = ["SBIN", "RELIANCE", "TCS"]
        
        # Should not raise
        PKScanRunner.populateQueues(items, tasks_queue, exit=False, userPassedArgs=user_args)
        assert tasks_queue is not None
    
    def test_populate_queues_with_exit(self):
        """Test populateQueues with exit=True."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        args = Namespace(options="X:12:1", monitor=None)
        tasks_queue = multiprocessing.JoinableQueue()
        items = ["SBIN"]
        
        # Should not raise
        PKScanRunner.populateQueues(items, tasks_queue, exit=True, userPassedArgs=args)
        assert tasks_queue is not None
    
    def test_populate_queues_with_piped(self):
        """Test populateQueues with piped options."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        args = Namespace(options="X:12:1|P:5", monitor=None)
        tasks_queue = multiprocessing.JoinableQueue()
        items = ["SBIN"]
        
        # Should not raise - piped options prevent adding None signals
        PKScanRunner.populateQueues(items, tasks_queue, exit=True, userPassedArgs=args)
        assert tasks_queue is not None
    
    def test_populate_queues_with_monitor(self):
        """Test populateQueues with monitor."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        args = Namespace(options="X:12:1", monitor="SomeMonitor")
        tasks_queue = multiprocessing.JoinableQueue()
        items = ["SBIN"]
        
        # Should not raise - monitor prevents adding None signals
        PKScanRunner.populateQueues(items, tasks_queue, exit=True, userPassedArgs=args)
        assert tasks_queue is not None
    
    def test_populate_queues_empty_items(self, user_args):
        """Test populateQueues with empty items."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        tasks_queue = multiprocessing.JoinableQueue()
        items = []
        
        # Should not raise
        PKScanRunner.populateQueues(items, tasks_queue, exit=False, userPassedArgs=user_args)
        assert tasks_queue is not None


# =============================================================================
# getScanDurationParameters Tests
# =============================================================================

class TestGetScanDurationParameters:
    """Test getScanDurationParameters method."""
    
    def test_get_scan_duration_backtest_testing(self):
        """Test getScanDurationParameters for backtest testing."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        sampling, filler, actual = PKScanRunner.getScanDurationParameters(testing=True, menuOption="B")
        
        assert sampling == 3
        assert filler == 1
        assert actual == 2
    
    def test_get_scan_duration_backtest_not_testing(self):
        """Test getScanDurationParameters for backtest not testing."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        sampling, filler, actual = PKScanRunner.getScanDurationParameters(testing=False, menuOption="B")
        
        assert filler == 1
        assert actual == sampling - filler
    
    def test_get_scan_duration_not_backtest(self):
        """Test getScanDurationParameters for non-backtest."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        sampling, filler, actual = PKScanRunner.getScanDurationParameters(testing=False, menuOption="X")
        
        assert sampling == 2
        assert filler == 2
        assert actual == 0
    
    def test_get_scan_duration_all_menu_options(self):
        """Test getScanDurationParameters for all menu options."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for menu in ["X", "P", "B", "G", "C"]:
            sampling, filler, actual = PKScanRunner.getScanDurationParameters(testing=True, menuOption=menu)
            assert sampling >= 0
            assert filler >= 0


# =============================================================================
# getBacktestDaysForScan Tests
# =============================================================================

class TestGetBacktestDaysForScan:
    """Test getBacktestDaysForScan method."""
    
    def test_get_backtest_days_menu_b(self, user_args):
        """Test getBacktestDaysForScan for menu B."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        days = PKScanRunner.getBacktestDaysForScan(user_args, 10, "B", 5)
        
        assert days == 5  # actualHistoricalDuration
    
    def test_get_backtest_days_menu_g(self, user_args):
        """Test getBacktestDaysForScan for menu G."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        days = PKScanRunner.getBacktestDaysForScan(user_args, 10, "G", 5)
        
        assert days == 10  # backtestPeriod
    
    def test_get_backtest_days_menu_x_no_backtest(self, user_args):
        """Test getBacktestDaysForScan for menu X without backtestdaysago."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        user_args.backtestdaysago = None
        days = PKScanRunner.getBacktestDaysForScan(user_args, 10, "X", 5)
        
        assert days == 0
    
    def test_get_backtest_days_menu_x_with_backtest(self, user_args):
        """Test getBacktestDaysForScan for menu X with backtestdaysago."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        user_args.backtestdaysago = 15
        days = PKScanRunner.getBacktestDaysForScan(user_args, 10, "X", 5)
        
        assert days == 15


# =============================================================================
# getFormattedChoices Tests
# =============================================================================

class TestGetFormattedChoices:
    """Test getFormattedChoices method."""
    
    def test_get_formatted_choices_basic(self, user_args):
        """Test getFormattedChoices basic."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        selected_choice = {"0": "X", "1": "12", "2": "1"}
        result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
        
        assert "X" in result
        assert "12" in result
        assert "1" in result
    
    def test_get_formatted_choices_with_intraday_analysis(self, user_args):
        """Test getFormattedChoices with intraday analysis."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        user_args.runintradayanalysis = True
        selected_choice = {"0": "X", "1": "12", "2": "1"}
        result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
        
        assert "_IA" in result
    
    def test_get_formatted_choices_without_intraday_analysis(self, user_args):
        """Test getFormattedChoices without intraday analysis."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        user_args.runintradayanalysis = False
        selected_choice = {"0": "X", "1": "12", "2": "1"}
        result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
        
        assert "_IA" not in result
    
    def test_get_formatted_choices_empty_choice(self, user_args):
        """Test getFormattedChoices with empty choice."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        selected_choice = {"0": "X", "1": "", "2": "1"}
        result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
        
        assert "X" in result
    
    def test_get_formatted_choices_with_comma(self, user_args):
        """Test getFormattedChoices with comma in choice."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        selected_choice = {"0": "X", "1": "SBIN,RELIANCE", "2": "1"}
        result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
        
        # Comma should be excluded
        assert "SBIN,RELIANCE" not in result
    
    def test_get_formatted_choices_with_dot(self, user_args):
        """Test getFormattedChoices with dot in choice."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        selected_choice = {"0": "X", "1": "2.5", "2": "1"}
        result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
        
        # Dot should be excluded
        assert "2.5" not in result
    
    def test_get_formatted_choices_all_menu_options(self, user_args):
        """Test getFormattedChoices with all menu options."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for menu in ["X", "P", "B", "G", "C", "D"]:
            selected_choice = {"0": menu, "1": "12", "2": "1"}
            result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
            assert menu in result


# =============================================================================
# refreshDatabase Tests
# =============================================================================

class TestRefreshDatabase:
    """Test refreshDatabase method."""
    
    def test_refresh_database(self):
        """Test refreshDatabase."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        mock_worker1 = MagicMock()
        mock_worker2 = MagicMock()
        consumers = [mock_worker1, mock_worker2]
        
        stock_dict_primary = {"SBIN": MagicMock()}
        stock_dict_secondary = {"TCS": MagicMock()}
        
        PKScanRunner.refreshDatabase(consumers, stock_dict_primary, stock_dict_secondary)
        
        assert mock_worker1.objectDictionaryPrimary == stock_dict_primary
        assert mock_worker1.objectDictionarySecondary == stock_dict_secondary
        assert mock_worker1.refreshDatabase is True
        assert mock_worker2.objectDictionaryPrimary == stock_dict_primary


# =============================================================================
# shutdown Tests
# =============================================================================

class TestShutdown:
    """Test shutdown method."""
    
    @patch('pkscreener.classes.PKScanRunner.OutputControls')
    def test_shutdown(self, mock_output):
        """Test shutdown."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        PKScanRunner.shutdown(None, None)
        # Should not raise


# =============================================================================
# addStocksToItemList Tests
# =============================================================================

class TestAddStocksToItemList:
    """Test addStocksToItemList method."""
    
    @patch('pkscreener.classes.PKScanRunner.PKScanRunner.fetcher')
    def test_add_stocks_to_item_list(self, mock_fetcher, user_args):
        """Test addStocksToItemList."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        mock_fetcher.fetchStockData.return_value = None
        
        items = []
        list_stock_codes = ["SBIN", "RELIANCE"]
        
        result = PKScanRunner.addStocksToItemList(
            userArgs=user_args,
            testing=True,
            testBuild=False,
            newlyListedOnly=False,
            downloadOnly=False,
            minRSI=50,
            maxRSI=70,
            insideBarToLookback=7,
            respChartPattern=None,
            daysForLowestVolume=30,
            backtestPeriod=10,
            reversalOption=None,
            maLength=50,
            listStockCodes=list_stock_codes,
            menuOption="X",
            exchangeName="NSE",
            executeOption=1,
            volumeRatio=2.5,
            items=items,
            daysInPast=0,
            runOption="X:12:1"
        )
        
        assert len(result) == 2  # Two stocks added


# =============================================================================
# terminateAllWorkers Tests
# =============================================================================

class TestTerminateAllWorkers:
    """Test terminateAllWorkers method."""
    
    @patch('pkscreener.classes.PKScanRunner.SuppressOutput')
    def test_terminate_all_workers(self, mock_suppress, user_args):
        """Test terminateAllWorkers."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        mock_suppress.return_value.__enter__ = Mock()
        mock_suppress.return_value.__exit__ = Mock()
        
        mock_worker = MagicMock()
        mock_worker.is_alive.return_value = False
        consumers = [mock_worker]
        
        tasks_queue = multiprocessing.JoinableQueue()
        
        PKScanRunner.terminateAllWorkers(user_args, consumers, tasks_queue, testing=False)
        
        # Check that class variables are reset
        assert PKScanRunner.tasks_queue is None
        assert PKScanRunner.results_queue is None
        assert PKScanRunner.scr is None
        assert PKScanRunner.consumers is None


# =============================================================================
# downloadSavedResults Tests
# =============================================================================

class TestDownloadSavedResults:
    """Test downloadSavedResults method."""
    
    @patch('pkscreener.classes.PKScanRunner.PKScanRunner.getFormattedChoices')
    @patch('pkscreener.classes.PKScanRunner.PKDateUtilities.nthPastTradingDateStringFromFutureDate')
    @patch('pkscreener.classes.PKScanRunner.Archiver.get_user_outputs_dir')
    @patch('pkscreener.classes.PKScanRunner.downloadFolder')
    @patch('pkscreener.classes.PKScanRunner.os.path.isfile')
    def test_download_saved_results_file_not_exists(self, mock_isfile, mock_download, mock_outputs, mock_date, mock_formatted):
        """Test downloadSavedResults when file doesn't exist."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        mock_formatted.return_value = "X_12_1"
        mock_date.return_value = "2023-12-01"
        mock_outputs.return_value = "/tmp/outputs"
        mock_download.return_value = "/tmp/outputs/actions-data-scan"
        mock_isfile.return_value = False
        
        past_date, saved_list = PKScanRunner.downloadSavedResults(5, downloadedRecently=False)
        
        assert past_date == "2023-12-01"
        assert saved_list == []
    
    @patch('pkscreener.classes.PKScanRunner.PKScanRunner.getFormattedChoices')
    @patch('pkscreener.classes.PKScanRunner.PKDateUtilities.nthPastTradingDateStringFromFutureDate')
    @patch('pkscreener.classes.PKScanRunner.Archiver.get_user_outputs_dir')
    @patch('pkscreener.classes.PKScanRunner.os.path.isfile')
    def test_download_saved_results_already_downloaded(self, mock_isfile, mock_outputs, mock_date, mock_formatted):
        """Test downloadSavedResults when already downloaded."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        mock_formatted.return_value = "X_12_1"
        mock_date.return_value = "2023-12-01"
        mock_outputs.return_value = "/tmp/outputs"
        mock_isfile.return_value = False
        
        past_date, saved_list = PKScanRunner.downloadSavedResults(5, downloadedRecently=True)
        
        assert past_date == "2023-12-01"
        assert saved_list == []


# =============================================================================
# addScansWithDefaultParams Tests
# =============================================================================

class TestAddScansWithDefaultParams:
    """Test addScansWithDefaultParams method."""
    
    @patch('pkscreener.classes.PKScanRunner.os.path.exists')
    def test_add_scans_with_default_params_no_file(self, mock_exists, user_args):
        """Test addScansWithDefaultParams when defaults file doesn't exist."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        mock_exists.return_value = False
        
        items = []
        result = PKScanRunner.addScansWithDefaultParams(
            userArgs=user_args,
            testing=True,
            testBuild=False,
            newlyListedOnly=False,
            downloadOnly=False,
            backtestPeriod=10,
            listStockCodes=["SBIN"],
            menuOption="X",
            exchangeName="NSE",
            executeOption=1,
            volumeRatio=2.5,
            items=items,
            daysInPast=0,
            runOption=""
        )
        
        assert result == items


# =============================================================================
# Integration Tests
# =============================================================================

class TestPKScanRunnerIntegration:
    """Integration tests for PKScanRunner."""
    
    def test_full_init_flow(self, user_args):
        """Test full initialization flow."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        # Initialize dataframes
        screen_results, save_results = PKScanRunner.initDataframes()
        assert len(screen_results) == 0
        
        # Initialize queues
        tasks_queue, results_queue, total_consumers, logging_queue = PKScanRunner.initQueues(10, user_args)
        assert tasks_queue is not None
        
        # Get scan duration parameters
        sampling, filler, actual = PKScanRunner.getScanDurationParameters(testing=True, menuOption="X")
        assert sampling >= 0
        
        # Get backtest days
        days = PKScanRunner.getBacktestDaysForScan(user_args, 10, "X", 5)
        assert days >= 0
        
        # Get formatted choices
        selected_choice = {"0": "X", "1": "12", "2": "1"}
        choices = PKScanRunner.getFormattedChoices(user_args, selected_choice)
        assert "X" in choices
    
    def test_all_menu_options_scan_duration(self):
        """Test getScanDurationParameters for all menu options."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for menu in ["X", "P", "B", "G", "C", "S", "F"]:
            for testing in [True, False]:
                sampling, filler, actual = PKScanRunner.getScanDurationParameters(testing, menu)
                assert sampling >= 0
                assert filler >= 0
    
    def test_all_menu_options_backtest_days(self, user_args):
        """Test getBacktestDaysForScan for all menu options."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for menu in ["X", "P", "B", "G", "C", "S", "F"]:
            days = PKScanRunner.getBacktestDaysForScan(user_args, 10, menu, 5)
            assert days >= 0
    
    def test_all_formatted_choices_combinations(self, user_args):
        """Test getFormattedChoices with various combinations."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for menu in ["X", "P", "B", "G"]:
            for index in ["1", "5", "12"]:
                for execute in ["0", "1", "5"]:
                    selected_choice = {"0": menu, "1": index, "2": execute}
                    result = PKScanRunner.getFormattedChoices(user_args, selected_choice)
                    assert menu in result
