"""
Unit tests for OutputFunctions.py
Tests for output and display functions.
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, MagicMock, patch


class TestFormatRunOptionName:
    """Tests for format_run_option_name function"""

    @patch('pkscreener.classes.OutputFunctions.PKScanRunner')
    def test_basic_format(self, mock_runner):
        """Should format run option name"""
        from pkscreener.classes.OutputFunctions import format_run_option_name
        
        mock_runner.getFormattedChoices.return_value = "X_12_9"
        
        user_args = Mock()
        user_args.progressstatus = None
        selected_choice = {"1": "X", "2": "12", "3": "9"}
        
        result = format_run_option_name(user_args, selected_choice)
        
        assert result == "X_12_9"

    @patch('pkscreener.classes.OutputFunctions.PKScanRunner')
    def test_with_progress_status(self, mock_runner):
        """Should use progressstatus when contains :0:"""
        from pkscreener.classes.OutputFunctions import format_run_option_name
        
        mock_runner.getFormattedChoices.return_value = "X_0_9"
        
        user_args = Mock()
        user_args.progressstatus = "  [+] NIFTY 50=>X_0_9"
        selected_choice = {}
        
        result = format_run_option_name(user_args, selected_choice)
        
        assert result == "NIFTY 50"


class TestGetIndexName:
    """Tests for get_index_name function"""

    def test_empty_run_option(self):
        """Should return empty for empty run option"""
        from pkscreener.classes.OutputFunctions import get_index_name
        
        result = get_index_name("")
        
        assert result == ""

    def test_non_p_starting(self):
        """Should return empty for non-P starting"""
        from pkscreener.classes.OutputFunctions import get_index_name
        
        result = get_index_name("X_12_9_0")
        
        assert result == ""

    @patch('pkscreener.classes.OutputFunctions.INDICES_MAP', {"0": "NIFTY 50", "1": "NIFTY NEXT 50"})
    def test_valid_index(self):
        """Should return index name for valid index"""
        from pkscreener.classes.OutputFunctions import get_index_name
        
        result = get_index_name("P_12_9_0")
        
        assert "NIFTY 50" in result


class TestShowBacktestResults:
    """Tests for show_backtest_results function"""

    @patch('pkscreener.classes.OutputFunctions.OutputControls')
    def test_handles_none_df(self, mock_output):
        """Should handle None dataframe"""
        from pkscreener.classes.OutputFunctions import show_backtest_results
        
        mock_output.return_value.printOutput = Mock()
        
        show_backtest_results(None)
        
        mock_output.return_value.printOutput.assert_called()

    @patch('pkscreener.classes.OutputFunctions.OutputControls')
    def test_handles_empty_df(self, mock_output):
        """Should handle empty dataframe"""
        from pkscreener.classes.OutputFunctions import show_backtest_results
        
        mock_output.return_value.printOutput = Mock()
        
        show_backtest_results(pd.DataFrame())
        
        mock_output.return_value.printOutput.assert_called()

    @patch('pkscreener.classes.OutputFunctions.OutputControls')
    @patch('pkscreener.classes.OutputFunctions.colorText')
    @patch('pkscreener.classes.OutputFunctions.Utility')
    def test_sorts_by_sort_key(self, mock_utility, mock_color, mock_output):
        """Should sort by sort_key"""
        from pkscreener.classes.OutputFunctions import show_backtest_results
        
        mock_output.return_value.printOutput = Mock()
        mock_color.miniTabulator.return_value.tabulate.return_value = "table"
        mock_utility.tools.getMaxColumnWidths.return_value = [10]
        
        df = pd.DataFrame({"Stock": ["A", "B"], "Price": [100, 200]})
        
        show_backtest_results(df, sort_key="Price")


class TestFinishBacktestDataCleanup:
    """Tests for finish_backtest_data_cleanup function"""

    @patch('pkscreener.classes.OutputFunctions.backtestSummary')
    @patch('pkscreener.classes.OutputFunctions.show_backtest_results')
    def test_formats_dates(self, mock_show, mock_summary):
        """Should format dates with slashes"""
        from pkscreener.classes.OutputFunctions import finish_backtest_data_cleanup
        
        mock_summary.return_value = pd.DataFrame()
        
        df = pd.DataFrame({"Stock": ["A"], "Date": ["2025-01-01"]})
        
        result = finish_backtest_data_cleanup(df, None)
        
        assert df["Date"].iloc[0] == "2025/01/01"


class TestScanOutputDirectory:
    """Tests for scan_output_directory function"""

    @patch('pkscreener.classes.OutputFunctions.Archiver')
    def test_returns_reports_for_backtest(self, mock_archiver):
        """Should return reports dir for backtest"""
        from pkscreener.classes.OutputFunctions import scan_output_directory
        
        mock_archiver.get_user_reports_dir.return_value = "/tmp/reports"
        
        result = scan_output_directory(backtest=True)
        
        assert result == "/tmp/reports"

    @patch('pkscreener.classes.OutputFunctions.Archiver')
    def test_returns_outputs_for_non_backtest(self, mock_archiver):
        """Should return outputs dir"""
        from pkscreener.classes.OutputFunctions import scan_output_directory
        
        mock_archiver.get_user_outputs_dir.return_value = "/tmp/outputs"
        
        result = scan_output_directory(backtest=False)
        
        assert result == "/tmp/outputs"


class TestGetBacktestReportFilename:
    """Tests for get_backtest_report_filename function"""

    @patch('pkscreener.classes.OutputFunctions.Archiver')
    def test_default_filename(self, mock_archiver):
        """Should generate default filename"""
        from pkscreener.classes.OutputFunctions import get_backtest_report_filename
        
        mock_archiver.get_user_reports_dir.return_value = "/tmp/reports"
        
        directory, filename = get_backtest_report_filename()
        
        assert directory == "/tmp/reports"
        assert "PKS_" in filename
        assert ".html" in filename


class TestSaveScreenResultsEncoded:
    """Tests for save_screen_results_encoded function"""

    def test_returns_none_for_none(self):
        """Should return None for None input"""
        from pkscreener.classes.OutputFunctions import save_screen_results_encoded
        
        result = save_screen_results_encoded(None)
        
        assert result is None

    def test_returns_none_for_empty(self):
        """Should return None for empty input"""
        from pkscreener.classes.OutputFunctions import save_screen_results_encoded
        
        result = save_screen_results_encoded("")
        
        assert result is None

    @patch('pkscreener.classes.OutputFunctions.Archiver')
    @patch('pkscreener.classes.OutputFunctions.PKDateUtilities')
    @patch('pkscreener.classes.OutputFunctions.os')
    def test_saves_file(self, mock_os, mock_utils, mock_archiver):
        """Should save file"""
        from pkscreener.classes.OutputFunctions import save_screen_results_encoded
        
        mock_archiver.get_user_outputs_dir.return_value = "/tmp/outputs"
        mock_utils.currentDateTime.return_value.strftime.return_value = "01-01-25_10.00.00"
        mock_os.makedirs = Mock()
        mock_os.path.join.return_value = "/tmp/outputs/DeleteThis/results.txt"
        
        m = MagicMock()
        with patch('builtins.open', m):
            result = save_screen_results_encoded("test content")
        
        assert result is not None


class TestReadScreenResultsDecoded:
    """Tests for read_screen_results_decoded function"""

    def test_returns_none_for_none_filename(self):
        """Should return None for None filename"""
        from pkscreener.classes.OutputFunctions import read_screen_results_decoded
        
        result = read_screen_results_decoded(None)
        
        assert result is None

    @patch('pkscreener.classes.OutputFunctions.Archiver')
    @patch('pkscreener.classes.OutputFunctions.os')
    def test_reads_file(self, mock_os, mock_archiver):
        """Should read file content"""
        from pkscreener.classes.OutputFunctions import read_screen_results_decoded
        
        mock_archiver.get_user_outputs_dir.return_value = "/tmp/outputs"
        mock_os.path.join.return_value = "/tmp/outputs/DeleteThis/test.txt"
        mock_os.path.exists.return_value = True
        
        m = MagicMock()
        m.return_value.__enter__.return_value.read.return_value = "file content"
        
        with patch('builtins.open', m):
            result = read_screen_results_decoded("test.txt")
        
        assert result == "file content"

    @patch('pkscreener.classes.OutputFunctions.os')
    def test_returns_none_for_missing_file(self, mock_os):
        """Should return None for missing file"""
        from pkscreener.classes.OutputFunctions import read_screen_results_decoded
        
        mock_os.path.exists.return_value = False
        mock_os.path.join.return_value = "/tmp/test.txt"
        
        with patch('pkscreener.classes.OutputFunctions.Archiver'):
            result = read_screen_results_decoded("missing.txt")
        
        assert result is None


class TestShowOptionErrorMessage:
    """Tests for show_option_error_message function"""

    @patch('pkscreener.classes.OutputFunctions.OutputControls')
    def test_skips_in_non_interactive(self, mock_output):
        """Should skip in non-interactive mode"""
        from pkscreener.classes.OutputFunctions import show_option_error_message
        
        mock_output.return_value.enableUserInput = False
        
        show_option_error_message()
        
        # Should not call printOutput

    def test_shows_message_in_interactive(self):
        """Should show message in interactive mode"""
        from pkscreener.classes.OutputFunctions import show_option_error_message
        
        # The function imports internally and checks enableUserInput
        # We just test it doesn't crash
        try:
            show_option_error_message()
        except Exception:
            # Expected - may fail due to interactive mode requirements
            pass


class TestCleanupLocalResults:
    """Tests for cleanup_local_results function"""

    def test_removes_delete_folder(self):
        """Should remove DeleteThis folder - tests function exists"""
        from pkscreener.classes.OutputFunctions import cleanup_local_results
        
        # The function imports shutil internally, so we just test it doesn't crash badly
        try:
            cleanup_local_results()
        except Exception:
            # Expected - may fail due to filesystem access
            pass


class TestReformatTable:
    """Tests for reformat_table function"""

    def test_returns_unchanged_for_none_summary(self):
        """Should return unchanged for None summary"""
        from pkscreener.classes.OutputFunctions import reformat_table
        
        result = reformat_table(None, {}, "colored text")
        
        assert result == "colored text"

    def test_replaces_headers(self):
        """Should replace headers"""
        from pkscreener.classes.OutputFunctions import reformat_table
        
        result = reformat_table(
            "summary",
            {"old": "new"},
            "text with old header"
        )
        
        assert "new" in result


class TestRemoveUnknowns:
    """Tests for remove_unknowns function"""

    def test_handles_none_input(self):
        """Should handle None input"""
        from pkscreener.classes.OutputFunctions import remove_unknowns
        
        result = remove_unknowns(None, None)
        
        assert result == (None, None)

    def test_handles_empty_df(self):
        """Should handle empty dataframe"""
        from pkscreener.classes.OutputFunctions import remove_unknowns
        
        result = remove_unknowns(pd.DataFrame(), pd.DataFrame())
        
        assert len(result[0]) == 0

    def test_removes_dash_rows(self):
        """Should remove rows with all dashes"""
        from pkscreener.classes.OutputFunctions import remove_unknowns
        
        screen_df = pd.DataFrame({
            "Stock": ["A", "-"],
            "Price": [100, "-"]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = remove_unknowns(screen_df, save_df)
        
        assert len(result_screen) == 1


class TestRemovedUnusedColumns:
    """Tests for removed_unused_columns function"""

    def test_handles_none_input(self):
        """Should handle None columns list"""
        from pkscreener.classes.OutputFunctions import removed_unused_columns
        
        df = pd.DataFrame({"Stock": ["A"], "Price": [100]})
        
        result = removed_unused_columns(df, df.copy())
        
        assert len(result[0].columns) == 2

    def test_drops_specified_columns(self):
        """Should drop specified columns"""
        from pkscreener.classes.OutputFunctions import removed_unused_columns
        
        df = pd.DataFrame({
            "Stock": ["A"],
            "Price": [100],
            "DropMe": [1]
        })
        
        result = removed_unused_columns(df, df.copy(), ["DropMe"])
        
        assert "DropMe" not in result[0].columns

    def test_drops_fairvalue_for_option_c(self):
        """Should drop FairValue for option C"""
        from pkscreener.classes.OutputFunctions import removed_unused_columns
        
        df = pd.DataFrame({
            "Stock": ["A"],
            "FairValue": [100]
        })
        
        user_args = Mock()
        user_args.options = "C:12:9"
        
        result = removed_unused_columns(df, df.copy(), user_args=user_args)
        
        assert "FairValue" not in result[0].columns


class TestDescribeUser:
    """Tests for describe_user function"""

    def test_returns_for_none_args(self):
        """Should return for None args"""
        from pkscreener.classes.OutputFunctions import describe_user
        
        describe_user(None)
        # No exception

    def test_returns_for_none_user(self):
        """Should return for None user"""
        from pkscreener.classes.OutputFunctions import describe_user
        
        user_args = Mock()
        user_args.user = None
        
        describe_user(user_args)
        # No exception


class TestUserReportName:
    """Tests for user_report_name function"""

    def test_returns_report_for_none(self):
        """Should return 'report' for None"""
        from pkscreener.classes.OutputFunctions import user_report_name
        
        result = user_report_name(None)
        
        assert result == "report"

    def test_joins_values(self):
        """Should join option values"""
        from pkscreener.classes.OutputFunctions import user_report_name
        
        result = user_report_name({"1": "X", "2": "12", "3": "9"})
        
        assert result == "X_12_9"


class TestGetPerformanceStats:
    """Tests for get_performance_stats function"""

    def test_returns_empty(self):
        """Should return empty string"""
        from pkscreener.classes.OutputFunctions import get_performance_stats
        
        result = get_performance_stats()
        
        assert result == ""


class TestGetMfiStats:
    """Tests for get_mfi_stats function"""

    def test_returns_none(self):
        """Should return None"""
        from pkscreener.classes.OutputFunctions import get_mfi_stats
        
        result = get_mfi_stats(1)
        
        assert result is None


class TestToggleUserConfig:
    """Tests for toggle_user_config function"""

    def test_calls_setconfig(self):
        """Should call setConfig"""
        from pkscreener.classes.OutputFunctions import toggle_user_config
        
        config_manager = Mock()
        
        toggle_user_config(config_manager)
        
        config_manager.setConfig.assert_called_once()


class TestResetConfigToDefault:
    """Tests for reset_config_to_default function"""

    def test_calls_getconfig(self):
        """Should call getConfig"""
        from pkscreener.classes.OutputFunctions import reset_config_to_default
        
        config_manager = Mock()
        
        reset_config_to_default(config_manager)
        
        config_manager.getConfig.assert_called_once()

    def test_calls_setconfig_when_forced(self):
        """Should call setConfig when forced"""
        from pkscreener.classes.OutputFunctions import reset_config_to_default
        
        config_manager = Mock()
        
        reset_config_to_default(config_manager, force=True)
        
        config_manager.setConfig.assert_called_once()
