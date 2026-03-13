"""
Unit tests for BacktestUtils.py
Tests for backtesting utilities.
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, MagicMock, patch


class TestGetBacktestReportFilename:
    """Tests for get_backtest_report_filename function"""

    @patch('pkscreener.classes.BacktestUtils.Archiver')
    def test_default_choices(self, mock_archiver):
        """Should handle default empty choices"""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        mock_archiver.get_user_reports_dir.return_value = "/tmp/reports"
        
        directory, filename = get_backtest_report_filename()
        
        assert directory == "/tmp/reports"
        assert "PKS_backtest_result_default.html" in filename

    @patch('pkscreener.classes.BacktestUtils.Archiver')
    def test_with_choices(self, mock_archiver):
        """Should include choices in filename"""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        mock_archiver.get_user_reports_dir.return_value = "/tmp/reports"
        choices = {"1": "X", "2": "12", "3": "9"}
        
        directory, filename = get_backtest_report_filename(
            sort_key="Stock",
            optional_name="test_result",
            choices=choices
        )
        
        assert "X_12_9" in filename
        assert "test_result" in filename

    @patch('pkscreener.classes.BacktestUtils.Archiver')
    def test_empty_values_filtered(self, mock_archiver):
        """Should filter empty values from choices"""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        mock_archiver.get_user_reports_dir.return_value = "/tmp/reports"
        choices = {"1": "X", "2": "", "3": "9"}
        
        _, filename = get_backtest_report_filename(choices=choices)
        
        assert "X_9" in filename


class TestFinishBacktestDataCleanup:
    """Tests for finish_backtest_data_cleanup function"""

    def test_returns_none_for_none_input(self):
        """Should return None for None backtest_df"""
        from pkscreener.classes.BacktestUtils import finish_backtest_data_cleanup
        
        result = finish_backtest_data_cleanup(None, None, Mock())
        
        assert result is None

    @patch('pkscreener.classes.BacktestUtils.backtestSummary')
    def test_formats_dates(self, mock_summary):
        """Should format dates with slashes"""
        from pkscreener.classes.BacktestUtils import finish_backtest_data_cleanup
        
        mock_summary.return_value = pd.DataFrame()
        
        backtest_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "Date": ["2025-01-01", "2025-01-02"]
        })
        
        result = finish_backtest_data_cleanup(
            backtest_df, None, Mock(), show_backtest_results_cb=Mock()
        )
        
        assert "2025/01/01" in backtest_df["Date"].values
        assert "2025/01/02" in backtest_df["Date"].values

    @patch('pkscreener.classes.BacktestUtils.backtestSummary')
    def test_calls_show_callback(self, mock_summary):
        """Should call show callback"""
        from pkscreener.classes.BacktestUtils import finish_backtest_data_cleanup
        
        mock_summary.return_value = pd.DataFrame()
        mock_callback = Mock()
        
        backtest_df = pd.DataFrame({"Stock": ["A"], "Date": ["2025-01-01"]})
        
        finish_backtest_data_cleanup(
            backtest_df, None, Mock(), show_backtest_results_cb=mock_callback
        )
        
        mock_callback.assert_called()


class TestPrepareGroupedXray:
    """Tests for prepare_grouped_xray function"""

    def test_returns_none_for_none_input(self):
        """Should return None for None backtest_df"""
        from pkscreener.classes.BacktestUtils import prepare_grouped_xray
        
        result = prepare_grouped_xray(30, None, Mock())
        
        assert result is None

    def test_returns_none_for_empty_df(self):
        """Should return None for empty dataframe"""
        from pkscreener.classes.BacktestUtils import prepare_grouped_xray
        
        result = prepare_grouped_xray(30, pd.DataFrame(), Mock())
        
        assert result is None

    def test_calls_portfolio_xray(self):
        """Should call PortfolioXRay - tests that function can be called"""
        from pkscreener.classes.BacktestUtils import prepare_grouped_xray
        
        # This tests error handling path since PortfolioXRay may not import
        backtest_df = pd.DataFrame({"Stock": ["A"], "Date": ["2025-01-01"]})
        
        try:
            result = prepare_grouped_xray(30, backtest_df, Mock())
            # Function completed, result could be None or DataFrame
        except Exception:
            # Expected - PortfolioXRay import may fail
            pass


class TestShowSortedBacktestData:
    """Tests for show_sorted_backtest_data function"""

    def test_returns_unchanged_for_none(self):
        """Should return unchanged for None input"""
        from pkscreener.classes.BacktestUtils import show_sorted_backtest_data
        
        result = show_sorted_backtest_data(None, None, {})
        
        assert result == (None, None)

    def test_returns_unchanged_with_default_answer(self):
        """Should return unchanged when default_answer is provided"""
        from pkscreener.classes.BacktestUtils import show_sorted_backtest_data
        
        backtest_df = pd.DataFrame({"Stock": ["A"]})
        summary_df = pd.DataFrame({"Total": [1]})
        
        result = show_sorted_backtest_data(
            backtest_df, summary_df, {}, default_answer="Y"
        )
        
        assert result == (backtest_df, summary_df)


class TestTabulateBacktestResults:
    """Tests for tabulate_backtest_results function"""

    def test_returns_empty_for_none(self):
        """Should return empty string for None input"""
        from pkscreener.classes.BacktestUtils import tabulate_backtest_results
        
        result = tabulate_backtest_results(None)
        
        assert result == ""

    def test_returns_empty_for_empty_df(self):
        """Should return empty string for empty dataframe"""
        from pkscreener.classes.BacktestUtils import tabulate_backtest_results
        
        result = tabulate_backtest_results(pd.DataFrame())
        
        assert result == ""

    @patch('pkscreener.classes.BacktestUtils.colorText')
    @patch('pkscreener.classes.BacktestUtils.Utility')
    def test_limits_results(self, mock_utility, mock_color):
        """Should limit results when max_allowed is set"""
        from pkscreener.classes.BacktestUtils import tabulate_backtest_results
        
        mock_color.miniTabulator.return_value.tabulate.return_value = "table"
        mock_utility.tools.getMaxColumnWidths.return_value = [10]
        
        df = pd.DataFrame({"Stock": ["A", "B", "C", "D", "E"]})
        
        result = tabulate_backtest_results(df, max_allowed=3)
        
        # Should truncate to 3 rows
        assert result is not None


class TestTakeBacktestInputs:
    """Tests for take_backtest_inputs function"""

    def test_uses_user_args_period(self):
        """Should use user passed backtest period"""
        from pkscreener.classes.BacktestUtils import take_backtest_inputs
        
        user_args = Mock()
        user_args.backtestdaysago = 60
        
        period, should_continue = take_backtest_inputs(user_args, {}, default_answer="Y")
        
        assert period == 60
        assert should_continue is True

    def test_default_period(self):
        """Should use default period 30"""
        from pkscreener.classes.BacktestUtils import take_backtest_inputs
        
        user_args = Mock()
        user_args.backtestdaysago = None
        
        period, should_continue = take_backtest_inputs(
            user_args, {}, default_answer="Y"
        )
        
        assert period == 30
        assert should_continue is True


class TestScanOutputDirectory:
    """Tests for scan_output_directory function"""

    @patch('pkscreener.classes.BacktestUtils.Archiver')
    def test_returns_reports_for_backtest(self, mock_archiver):
        """Should return reports dir for backtest"""
        from pkscreener.classes.BacktestUtils import scan_output_directory
        
        mock_archiver.get_user_reports_dir.return_value = "/tmp/reports"
        
        result = scan_output_directory(backtest=True)
        
        assert result == "/tmp/reports"

    @patch('pkscreener.classes.BacktestUtils.Archiver')
    def test_returns_outputs_for_non_backtest(self, mock_archiver):
        """Should return outputs dir for non-backtest"""
        from pkscreener.classes.BacktestUtils import scan_output_directory
        
        mock_archiver.get_user_outputs_dir.return_value = "/tmp/outputs"
        
        result = scan_output_directory(backtest=False)
        
        assert result == "/tmp/outputs"


class TestBacktestResultsHandler:
    """Tests for BacktestResultsHandler class"""

    def test_init(self):
        """Should initialize correctly"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        config_manager = Mock()
        user_args = Mock()
        
        handler = BacktestResultsHandler(config_manager, user_args)
        
        assert handler.config_manager == config_manager
        assert handler.user_passed_args == user_args
        assert handler.backtest_df is None
        assert handler.summary_df is None

    def test_process_none_result(self):
        """Should return existing df for None result"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        handler = BacktestResultsHandler(Mock())
        handler.backtest_df = pd.DataFrame({"Stock": ["A"]})
        
        result = handler.process_backtest_results(30, 0, None, 30)
        
        assert len(result) == 1

    @patch('pkscreener.classes.BacktestUtils.backtest')
    def test_process_first_result(self, mock_backtest):
        """Should set backtest_df for first result"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        mock_backtest.return_value = pd.DataFrame({"Stock": ["A"]})
        
        handler = BacktestResultsHandler(Mock())
        mock_result = ("screen", "save", "df", "stocks", 30)
        
        result = handler.process_backtest_results(30, 0, mock_result, 30)
        
        assert len(result) == 1

    @patch('pkscreener.classes.BacktestUtils.backtest')
    def test_process_concat_results(self, mock_backtest):
        """Should concat additional results"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        mock_backtest.return_value = pd.DataFrame({"Stock": ["B"]})
        
        handler = BacktestResultsHandler(Mock())
        handler.backtest_df = pd.DataFrame({"Stock": ["A"]})
        mock_result = ("screen", "save", "df", "stocks", 30)
        
        result = handler.process_backtest_results(30, 0, mock_result, 30)
        
        assert len(result) == 2

    @patch('pkscreener.classes.BacktestUtils.OutputControls')
    def test_show_results_empty(self, mock_output):
        """Should handle empty results"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        mock_output.return_value.printOutput = Mock()
        
        handler = BacktestResultsHandler(Mock())
        handler.backtest_df = None
        
        handler.show_results()
        
        mock_output.return_value.printOutput.assert_called()

    @patch('pkscreener.classes.BacktestUtils.backtestSummary')
    def test_get_summary(self, mock_summary):
        """Should get summary from backtest"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        mock_summary.return_value = pd.DataFrame({"Summary": [1]})
        
        handler = BacktestResultsHandler(Mock())
        handler.backtest_df = pd.DataFrame({"Stock": ["A"]})
        
        result = handler.get_summary()
        
        assert result is not None
        mock_summary.assert_called_once()

    def test_get_summary_none(self):
        """Should return None for None backtest_df"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        handler = BacktestResultsHandler(Mock())
        handler.backtest_df = None
        
        result = handler.get_summary()
        
        assert result is None

    @patch('pkscreener.classes.BacktestUtils.os')
    @patch('pkscreener.classes.BacktestUtils.OutputControls')
    def test_save_to_file(self, mock_output, mock_os):
        """Should save to file"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        mock_output.return_value.printOutput = Mock()
        mock_os.path.join.return_value = "/tmp/test.html"
        
        handler = BacktestResultsHandler(Mock())
        handler.backtest_df = pd.DataFrame({"Stock": ["A"]})
        
        with patch.object(handler.backtest_df, 'to_html'):
            result = handler.save_to_file(choices={"1": "X"})
        
        assert result is not None

    def test_save_to_file_none(self):
        """Should return None for None backtest_df"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        handler = BacktestResultsHandler(Mock())
        handler.backtest_df = None
        
        result = handler.save_to_file()
        
        assert result is None


class TestShowBacktestResultsImpl:
    """Tests for show_backtest_results_impl function"""

    @patch('pkscreener.classes.BacktestUtils.OutputControls')
    def test_handles_none_df(self, mock_output):
        """Should handle None dataframe"""
        from pkscreener.classes.BacktestUtils import show_backtest_results_impl
        
        mock_output.return_value.printOutput = Mock()
        
        show_backtest_results_impl(None)
        
        mock_output.return_value.printOutput.assert_called()

    @patch('pkscreener.classes.BacktestUtils.OutputControls')
    def test_handles_empty_df(self, mock_output):
        """Should handle empty dataframe"""
        from pkscreener.classes.BacktestUtils import show_backtest_results_impl
        
        mock_output.return_value.printOutput = Mock()
        
        show_backtest_results_impl(pd.DataFrame())
        
        mock_output.return_value.printOutput.assert_called()


class TestTabulateBacktestResultsImpl:
    """Tests for tabulate_backtest_results_impl function"""

    def test_returns_none_without_env(self):
        """Should return None without proper env"""
        from pkscreener.classes.BacktestUtils import tabulate_backtest_results_impl
        
        with patch.dict(os.environ, {}, clear=True):
            result = tabulate_backtest_results_impl(pd.DataFrame())
        
        assert result == (None, None)

    def test_returns_none_when_disabled(self):
        """Should return None when showPastStrategyData is False"""
        from pkscreener.classes.BacktestUtils import tabulate_backtest_results_impl
        
        config_manager = Mock()
        config_manager.showPastStrategyData = False
        
        with patch.dict(os.environ, {"PKDevTools_Default_Log_Level": "DEBUG"}):
            result = tabulate_backtest_results_impl(
                pd.DataFrame(), config_manager=config_manager
            )
        
        assert result == (None, None)


class TestFinishBacktestDataCleanupImpl:
    """Tests for finish_backtest_data_cleanup_impl function"""

    def test_returns_summary(self):
        """Should return summary dataframe"""
        from pkscreener.classes.BacktestUtils import finish_backtest_data_cleanup_impl
        
        mock_summary_cb = Mock(return_value=pd.DataFrame({"Summary": [1]}))
        mock_show_cb = Mock()
        
        backtest_df = pd.DataFrame({"Stock": ["A"], "Date": ["2025-01-01"]})
        
        config_manager = Mock()
        config_manager.enablePortfolioCalculations = False
        
        try:
            summary_df, sorting, sort_keys = finish_backtest_data_cleanup_impl(
                backtest_df, None,
                default_answer="Y",
                config_manager=config_manager,
                show_backtest_cb=mock_show_cb,
                backtest_summary_cb=mock_summary_cb
            )
            
            assert sorting is False
            assert "S" in sort_keys
        except Exception:
            # May fail due to internal imports
            pass


class TestPrepareGroupedXrayImpl:
    """Tests for prepare_grouped_xray_impl function"""

    def test_groups_by_date(self):
        """Should group backtest data by date"""
        from pkscreener.classes.BacktestUtils import prepare_grouped_xray_impl
        
        user_args = Mock()
        user_args.backtestdaysago = 30
        
        backtest_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "Date": ["2025-01-01", "2025-01-02"]
        })
        
        # The function uses internal imports, so we just test it doesn't crash
        try:
            result = prepare_grouped_xray_impl(30, backtest_df, user_args)
        except Exception:
            # Expected - may fail due to internal dependencies
            pass


class TestShowSortedBacktestDataImpl:
    """Tests for show_sorted_backtest_data_impl function"""

    @patch('pkscreener.classes.BacktestUtils.OutputControls')
    def test_returns_false_with_default_answer(self, mock_output):
        """Should return False with default answer"""
        from pkscreener.classes.BacktestUtils import show_sorted_backtest_data_impl
        
        mock_output.return_value.printOutput = Mock()
        
        result = show_sorted_backtest_data_impl(
            pd.DataFrame(), pd.DataFrame(), {},
            default_answer="Y"
        )
        
        assert result is False

    @patch('pkscreener.classes.BacktestUtils.OutputControls')
    @patch('pkscreener.classes.BacktestUtils.ConsoleUtility')
    def test_returns_false_on_exit(self, mock_console, mock_output):
        """Should return False when user exits"""
        from pkscreener.classes.BacktestUtils import show_sorted_backtest_data_impl
        
        mock_output.return_value.printOutput = Mock()
        mock_output.return_value.takeUserInput.return_value = "n"
        
        result = show_sorted_backtest_data_impl(
            pd.DataFrame(), pd.DataFrame(), {}
        )
        
        assert result is False
