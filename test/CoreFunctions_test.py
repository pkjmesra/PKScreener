"""
Unit tests for CoreFunctions.py
Tests for core scanning and processing functions.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime, UTC
import logging


class TestGetReviewDate:
    """Tests for get_review_date function"""

    def test_get_review_date_with_criteria_datetime(self):
        """Should return criteria_date_time when provided"""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        result = get_review_date(None, "2025-01-01")
        assert result == "2025-01-01"

    @patch('pkscreener.classes.CoreFunctions.PKDateUtilities')
    def test_get_review_date_without_criteria_datetime(self, mock_utils):
        """Should return trading date when criteria_date_time is None"""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        mock_date = Mock()
        mock_date.strftime.return_value = "2025-12-30"
        mock_utils.tradingDate.return_value = mock_date
        
        result = get_review_date(None, None)
        assert result == "2025-12-30"

    @patch('pkscreener.classes.CoreFunctions.PKDateUtilities')
    def test_get_review_date_with_backtestdaysago(self, mock_utils):
        """Should use nthPastTradingDateStringFromFutureDate when backtestdaysago provided"""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        mock_utils.nthPastTradingDateStringFromFutureDate.return_value = "2025-12-25"
        mock_date = Mock()
        mock_date.strftime.return_value = "2025-12-30"
        mock_utils.tradingDate.return_value = mock_date
        
        user_args = Mock()
        user_args.backtestdaysago = 5
        
        result = get_review_date(user_args, None)
        assert result == "2025-12-25"
        mock_utils.nthPastTradingDateStringFromFutureDate.assert_called_once_with(5)


class TestGetMaxAllowedResultsCount:
    """Tests for get_max_allowed_results_count function"""

    def test_returns_1_when_testing(self):
        """Should return 1 when testing is True"""
        from pkscreener.classes.CoreFunctions import get_max_allowed_results_count
        
        config_manager = Mock()
        config_manager.maxdisplayresults = 100
        
        result = get_max_allowed_results_count(5, True, config_manager, None)
        assert result == 1

    def test_uses_config_maxdisplayresults(self):
        """Should use config maxdisplayresults when not testing"""
        from pkscreener.classes.CoreFunctions import get_max_allowed_results_count
        
        config_manager = Mock()
        config_manager.maxdisplayresults = 50
        
        result = get_max_allowed_results_count(3, False, config_manager, None)
        assert result == 150  # 3 * 50

    def test_uses_user_maxdisplayresults(self):
        """Should use user passed maxdisplayresults when provided"""
        from pkscreener.classes.CoreFunctions import get_max_allowed_results_count
        
        config_manager = Mock()
        config_manager.maxdisplayresults = 50
        
        user_args = Mock()
        user_args.maxdisplayresults = 200
        
        result = get_max_allowed_results_count(2, False, config_manager, user_args)
        assert result == 400  # 2 * 200


class TestGetIterationsAndStockCounts:
    """Tests for get_iterations_and_stock_counts function"""

    def test_small_stock_count(self):
        """Should return 1 iteration for small stock counts"""
        from pkscreener.classes.CoreFunctions import get_iterations_and_stock_counts
        
        iterations, stocks_per_iter = get_iterations_and_stock_counts(100, 1)
        assert iterations == 1
        assert stocks_per_iter == 100

    def test_exactly_2500_stocks(self):
        """Should return 1 iteration for exactly 2500 stocks"""
        from pkscreener.classes.CoreFunctions import get_iterations_and_stock_counts
        
        iterations, stocks_per_iter = get_iterations_and_stock_counts(2500, 1)
        assert iterations == 1
        assert stocks_per_iter == 2500

    def test_large_stock_count(self):
        """Should split into multiple iterations for large stock counts"""
        from pkscreener.classes.CoreFunctions import get_iterations_and_stock_counts
        
        iterations, stocks_per_iter = get_iterations_and_stock_counts(5000, 1)
        assert iterations > 1
        assert stocks_per_iter <= 500

    def test_very_large_stock_count(self):
        """Should cap stocks per iteration at 500"""
        from pkscreener.classes.CoreFunctions import get_iterations_and_stock_counts
        
        iterations, stocks_per_iter = get_iterations_and_stock_counts(10000, 1)
        assert stocks_per_iter <= 500


class TestProcessSingleResult:
    """Tests for process_single_result function"""

    def test_none_result(self):
        """Should handle None result gracefully"""
        from pkscreener.classes.CoreFunctions import process_single_result
        
        lst_screen = []
        lst_save = []
        
        result = process_single_result("X", 30, None, lst_screen, lst_save, None)
        
        assert len(lst_screen) == 0
        assert len(lst_save) == 0
        assert result is None

    def test_valid_result_non_backtest(self):
        """Should append results for non-backtest menu option"""
        from pkscreener.classes.CoreFunctions import process_single_result
        
        lst_screen = []
        lst_save = []
        mock_result = ("screen_data", "save_data", "df", "stocks", 30)
        
        result = process_single_result("X", 30, mock_result, lst_screen, lst_save, None)
        
        assert len(lst_screen) == 1
        assert len(lst_save) == 1
        assert lst_screen[0] == "screen_data"
        assert lst_save[0] == "save_data"

    @patch('pkscreener.classes.CoreFunctions.update_backtest_results')
    def test_valid_result_backtest(self, mock_update):
        """Should call update_backtest_results for backtest menu option"""
        from pkscreener.classes.CoreFunctions import process_single_result
        
        lst_screen = []
        lst_save = []
        mock_result = ("screen_data", "save_data", "df", "stocks", 30)
        mock_update.return_value = pd.DataFrame()
        
        result = process_single_result("B", 30, mock_result, lst_screen, lst_save, None)
        
        mock_update.assert_called_once()


class TestUpdateBacktestResults:
    """Tests for update_backtest_results function"""

    def test_none_result(self):
        """Should return existing backtest_df for None result"""
        from pkscreener.classes.CoreFunctions import update_backtest_results
        
        existing_df = pd.DataFrame({'col': [1, 2, 3]})
        result = update_backtest_results(30, None, 30, existing_df)
        
        assert result is existing_df

    @patch('pkscreener.classes.CoreFunctions.backtest')
    def test_first_backtest_result(self, mock_backtest):
        """Should set backtest_df when it's None"""
        from pkscreener.classes.CoreFunctions import update_backtest_results
        
        new_df = pd.DataFrame({'Stock': ['A'], 'Price': [100]})
        mock_backtest.return_value = new_df
        mock_result = ("screen", "save", "df", "stocks", 30)
        
        result = update_backtest_results(30, mock_result, 30, None)
        
        assert result is not None
        assert len(result) == 1

    @patch('pkscreener.classes.CoreFunctions.backtest')
    def test_concat_backtest_results(self, mock_backtest):
        """Should concat results when backtest_df exists"""
        from pkscreener.classes.CoreFunctions import update_backtest_results
        
        existing_df = pd.DataFrame({'Stock': ['A'], 'Price': [100]})
        new_df = pd.DataFrame({'Stock': ['B'], 'Price': [200]})
        mock_backtest.return_value = new_df
        mock_result = ("screen", "save", "df", "stocks", 30)
        
        result = update_backtest_results(30, mock_result, 30, existing_df)
        
        assert len(result) == 2

    @patch('pkscreener.classes.CoreFunctions.backtest')
    def test_handles_backtest_exception(self, mock_backtest):
        """Should handle exception from backtest function"""
        from pkscreener.classes.CoreFunctions import update_backtest_results
        
        mock_backtest.side_effect = Exception("Backtest error")
        mock_result = ("screen", "save", "df", "stocks", 30)
        
        result = update_backtest_results(30, mock_result, 30, None)
        
        assert result is None


class TestShouldShowLiveResults:
    """Tests for _should_show_live_results function"""

    def test_monitor_mode_returns_false(self):
        """Should return False in monitor mode"""
        from pkscreener.classes.CoreFunctions import _should_show_live_results
        
        user_args = Mock()
        user_args.monitor = True
        
        result = _should_show_live_results([1, 2, 3], user_args)
        assert result is False

    def test_empty_list_returns_false(self):
        """Should return False for empty list"""
        from pkscreener.classes.CoreFunctions import _should_show_live_results
        
        user_args = Mock()
        user_args.monitor = False
        user_args.options = "X:12:29"
        
        result = _should_show_live_results([], user_args)
        assert result is False

    def test_none_options_returns_false(self):
        """Should return False when options is None"""
        from pkscreener.classes.CoreFunctions import _should_show_live_results
        
        user_args = Mock()
        user_args.monitor = False
        user_args.options = None
        
        result = _should_show_live_results([1], user_args)
        assert result is False

    def test_option_29_returns_true(self):
        """Should return True for option 29"""
        from pkscreener.classes.CoreFunctions import _should_show_live_results
        
        user_args = Mock()
        user_args.monitor = False
        user_args.options = "X:12:29"
        
        result = _should_show_live_results([1], user_args)
        assert result is True

    def test_non_29_option_returns_false(self):
        """Should return False for non-29 option"""
        from pkscreener.classes.CoreFunctions import _should_show_live_results
        
        user_args = Mock()
        user_args.monitor = False
        user_args.options = "X:12:30"
        
        result = _should_show_live_results([1], user_args)
        assert result is False


class TestShowLiveResults:
    """Tests for _show_live_results function"""

    @patch('pkscreener.classes.CoreFunctions.OutputControls')
    @patch('pkscreener.classes.CoreFunctions.colorText')
    @patch('pkscreener.classes.CoreFunctions.Utility')
    def test_show_live_results_basic(self, mock_utility, mock_color, mock_output):
        """Should display live results"""
        from pkscreener.classes.CoreFunctions import _show_live_results
        
        mock_output.return_value.printOutput = Mock()
        mock_output.return_value.moveCursorUpLines = Mock()
        mock_utility.tools.getMaxColumnWidths.return_value = [10]
        mock_color.miniTabulator.return_value.tb.tabulate.return_value = "table"
        
        lst_screen = [{"Stock": "A", "%Chng": 5, "LTP": 100, "volume": 1000}]
        _show_live_results(lst_screen)

    def test_empty_available_cols(self):
        """Should handle empty available columns"""
        from pkscreener.classes.CoreFunctions import _show_live_results
        
        lst_screen = [{"Other": "data"}]
        # Should not raise exception
        _show_live_results(lst_screen)


class TestHandleKeyboardInterrupt:
    """Tests for _handle_keyboard_interrupt function"""

    @patch('pkscreener.classes.CoreFunctions.PKScanRunner')
    @patch('pkscreener.classes.CoreFunctions.OutputControls')
    @patch('pkscreener.classes.CoreFunctions.logging')
    def test_sets_interrupt_event(self, mock_logging, mock_output, mock_runner):
        """Should set keyboard interrupt event"""
        from pkscreener.classes.CoreFunctions import _handle_keyboard_interrupt
        
        mock_event = Mock()
        interrupt_ref = [False]
        
        _handle_keyboard_interrupt(
            mock_event, interrupt_ref, Mock(), [], Mock(), False
        )
        
        mock_event.set.assert_called_once()
        assert interrupt_ref[0] is True

    @patch('pkscreener.classes.CoreFunctions.PKScanRunner')
    @patch('pkscreener.classes.CoreFunctions.OutputControls')
    @patch('pkscreener.classes.CoreFunctions.logging')
    def test_terminates_workers(self, mock_logging, mock_output, mock_runner):
        """Should terminate all workers"""
        from pkscreener.classes.CoreFunctions import _handle_keyboard_interrupt
        
        user_args = Mock()
        consumers = []
        tasks_queue = Mock()
        
        _handle_keyboard_interrupt(
            None, [False], user_args, consumers, tasks_queue, False
        )
        
        mock_runner.terminateAllWorkers.assert_called_once()


class TestUpdateCriteriaDatetime:
    """Tests for _update_criteria_datetime function"""

    def test_none_result(self):
        """Should not update when result is None"""
        from pkscreener.classes.CoreFunctions import _update_criteria_datetime
        
        criteria_ref = [None]
        _update_criteria_datetime(None, None, None, criteria_ref)
        
        assert criteria_ref[0] is None

    def test_empty_result(self):
        """Should not update when result is empty"""
        from pkscreener.classes.CoreFunctions import _update_criteria_datetime
        
        criteria_ref = [None]
        _update_criteria_datetime([], None, None, criteria_ref)
        
        assert criteria_ref[0] is None

    @patch('pkscreener.classes.CoreFunctions.PKDateUtilities')
    def test_sets_criteria_from_result(self, mock_utils):
        """Should set criteria datetime from result"""
        from pkscreener.classes.CoreFunctions import _update_criteria_datetime
        
        df = pd.DataFrame({'col': [1, 2, 3]}, index=pd.date_range('2025-01-01', periods=3))
        result = ["screen", "save", df, "stocks", 30]
        criteria_ref = [None]
        
        user_args = Mock()
        user_args.backtestdaysago = None
        user_args.slicewindow = None
        
        mock_utils.currentDateTime.return_value.astimezone.return_value.tzinfo = "UTC"
        
        _update_criteria_datetime(result, pd.DataFrame(), user_args, criteria_ref)


class TestRunScanners:
    """Tests for run_scanners function - integration tests"""

    @patch('pkscreener.classes.CoreFunctions.PKScanRunner')
    @patch('pkscreener.classes.CoreFunctions.OutputControls')
    @patch('pkscreener.classes.CoreFunctions.Utility')
    @patch('pkscreener.classes.CoreFunctions.alive_bar')
    @patch('pkscreener.classes.CoreFunctions.get_review_date')
    @patch('pkscreener.classes.CoreFunctions.get_max_allowed_results_count')
    @patch('pkscreener.classes.CoreFunctions.get_iterations_and_stock_counts')
    def test_run_scanners_basic(
        self, mock_iters, mock_max, mock_review, mock_bar, 
        mock_utility, mock_output, mock_runner
    ):
        """Should run scanners and return results"""
        from pkscreener.classes.CoreFunctions import run_scanners
        
        mock_review.return_value = "2025-01-01"
        mock_max.return_value = 100
        mock_iters.return_value = (1, 100)
        mock_utility.tools.getProgressbarStyle.return_value = ("bar", "spinner")
        mock_bar.return_value.__enter__ = Mock(return_value=Mock())
        mock_bar.return_value.__exit__ = Mock(return_value=False)
        mock_runner.runScan.return_value = (None, None)
        
        user_args = Mock()
        user_args.download = False
        user_args.progressstatus = None
        user_args.options = "X:12:9"
        user_args.monitor = False
        
        config_manager = Mock()
        config_manager.period = "1y"
        config_manager.duration = "1d"
        
        screen_results, save_results, backtest_df = run_scanners(
            menu_option="X",
            items=[],
            tasks_queue=Mock(),
            results_queue=Mock(),
            num_stocks=100,
            backtest_period=30,
            iterations=1,
            consumers=[],
            screen_results=pd.DataFrame(),
            save_results=pd.DataFrame(),
            backtest_df=None,
            testing=False,
            config_manager=config_manager,
            user_passed_args=user_args,
            keyboard_interrupt_event=None,
            keyboard_interrupt_fired_ref=[False],
            criteria_date_time_ref=[None],
            scan_cycle_running_ref=[False],
            start_time_ref=[0],
            elapsed_time_ref=[0]
        )
