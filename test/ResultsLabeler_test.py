"""
Unit tests for ResultsLabeler.py
Tests for results labeling and formatting.
"""

import pytest
import pandas as pd
import numpy as np
import os
from unittest.mock import Mock, MagicMock, patch


class TestResultsLabelerInit:
    """Tests for ResultsLabeler initialization"""

    def test_init(self):
        """Should initialize correctly"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        config_manager = Mock()
        
        labeler = ResultsLabeler(config_manager, "X > 12 > 9")
        
        assert labeler.config_manager == config_manager
        assert labeler.menu_choice_hierarchy == "X > 12 > 9"


class TestResultsLabelerLabelDataForPrinting:
    """Tests for label_data_for_printing method"""

    def test_handles_none_save_results(self):
        """Should handle None save_results"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame()
        result = labeler.label_data_for_printing(
            screen_df, None, 2.5, 9, 0, "X"
        )
        
        assert result[1] is None

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    @patch('pkscreener.classes.ResultsLabeler.Utility')
    @patch('pkscreener.classes.ResultsLabeler.ImageUtility')
    def test_sets_stock_index(self, mock_image, mock_utility, mock_utils):
        """Should set Stock as index"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        mock_utility.tools.formatRatio.return_value = "2.5x"
        mock_image.PKImageTools.removeAllColorStyles.return_value = "2.5"
        
        config_manager = Mock()
        config_manager.calculatersiintraday = False
        config_manager.daysToLookback = 22
        
        labeler = ResultsLabeler(config_manager)
        
        screen_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "volume": [1000, 2000],
            "RSI": [50, 60]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler.label_data_for_printing(
            screen_df, save_df, 2.5, 9, 0, "X"
        )
        
        assert result_screen.index.name == "Stock"


class TestResultsLabelerAddRsiIntraday:
    """Tests for _add_rsi_intraday method"""

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    def test_adds_rsi_intraday(self, mock_utils):
        """Should combine RSI and RSIi"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utils.isTradingTime.return_value = True
        mock_utils.isTodayHoliday.return_value = (False, None)
        
        config_manager = Mock()
        config_manager.calculatersiintraday = True
        
        labeler = ResultsLabeler(config_manager)
        
        screen_df = pd.DataFrame({
            "RSI": [50, 60],
            "RSIi": [55, 65]
        })
        save_df = screen_df.copy()
        
        with patch.dict(os.environ, {}, clear=True):
            result_screen, result_save = labeler._add_rsi_intraday(
                screen_df, save_df, None
            )
        
        assert "RSI/i" in result_screen.columns


class TestResultsLabelerGetSortKey:
    """Tests for _get_sort_key method"""

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    def test_default_sort_by_volume(self, mock_utils):
        """Should default to volume sort"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        
        labeler = ResultsLabeler(Mock(), "X > 12 > 9")
        
        sort_key, ascending = labeler._get_sort_key(9, 0, pd.DataFrame())
        
        assert sort_key == ["volume"]
        assert ascending == [False]

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    def test_sort_by_rsi(self, mock_utils):
        """Should sort by RSI when in hierarchy"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        
        labeler = ResultsLabeler(Mock(), "X > 12 > RSI")
        
        sort_key, ascending = labeler._get_sort_key(5, 0, pd.DataFrame())
        
        assert sort_key == ["RSI"]
        assert ascending == [True]

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    def test_option_21_mfi_sort(self, mock_utils):
        """Should sort by MFI for option 21"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        
        labeler = ResultsLabeler(Mock())
        
        sort_key, ascending = labeler._get_sort_key(21, 3, pd.DataFrame())
        
        assert sort_key == ["MFI"]

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    def test_option_7_superconf_sort(self, mock_utils):
        """Should sort by SuperConfSort for option 7:3"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        
        labeler = ResultsLabeler(Mock())
        
        df = pd.DataFrame({"SuperConfSort": [1, 2]})
        
        sort_key, ascending = labeler._get_sort_key(7, 3, df)
        
        assert sort_key == ["SuperConfSort"]

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    def test_option_31_pctchng_sort(self, mock_utils):
        """Should sort by %Chng for option 31"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        
        labeler = ResultsLabeler(Mock())
        
        sort_key, ascending = labeler._get_sort_key(31, 0, pd.DataFrame())
        
        assert sort_key == ["%Chng"]


class TestResultsLabelerApplySorting:
    """Tests for _apply_sorting method"""

    def test_sorts_dataframe(self):
        """Should sort dataframe"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame({"volume": [100, 300, 200]})
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler._apply_sorting(
            screen_df, save_df, ["volume"], [False]
        )
        
        assert result_screen["volume"].iloc[0] == 300

    def test_handles_nan_values(self):
        """Should handle NaN values"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame({"volume": [100, "", 200]})
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler._apply_sorting(
            screen_df, save_df, ["volume"], [False]
        )
        
        # Should not raise


class TestResultsLabelerRemoveUnusedColumns:
    """Tests for _remove_unused_columns method"""

    def test_removes_default_columns(self):
        """Should remove default unused columns"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame({
            "Stock": ["A"],
            "MFI": [50],
            "RSIi": [60],
            "volume": [1000]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler._remove_unused_columns(
            screen_df, save_df, 9, "X", None
        )
        
        assert "MFI" not in result_screen.columns
        assert "RSIi" not in result_screen.columns

    def test_removes_fairvalue_for_c(self):
        """Should remove FairValue for option C"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame({
            "Stock": ["A"],
            "FairValue": [100]
        })
        save_df = screen_df.copy()
        
        user_args = Mock()
        user_args.options = "C:12:9"
        
        result_screen, result_save = labeler._remove_unused_columns(
            screen_df, save_df, 9, "X", user_args
        )
        
        assert "FairValue" not in result_screen.columns


class TestResultsLabelerFormatVolume:
    """Tests for _format_volume method"""

    @patch('pkscreener.classes.ResultsLabeler.Utility')
    @patch('pkscreener.classes.ResultsLabeler.ImageUtility')
    def test_formats_volume(self, mock_image, mock_utility):
        """Should format volume with ratio"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_utility.tools.formatRatio.return_value = "2.5x"
        mock_image.PKImageTools.removeAllColorStyles.return_value = "2.5"
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame({"volume": [2.5, 3.0]})
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler._format_volume(
            screen_df, save_df, 2.5
        )
        
        assert "x" in result_save["volume"].iloc[0]


class TestResultsLabelerRenameTrendColumns:
    """Tests for _rename_trend_columns method"""

    def test_renames_columns(self):
        """Should rename trend columns with days"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        config_manager = Mock()
        config_manager.daysToLookback = 22
        
        labeler = ResultsLabeler(config_manager)
        
        screen_df = pd.DataFrame({
            "Trend": ["Up"],
            "Breakout": ["Yes"]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler._rename_trend_columns(
            screen_df, save_df
        )
        
        assert "Trend(22Prds)" in result_screen.columns
        assert "Breakout(22Prds)" in result_screen.columns


class TestResultsLabelerRemoveUnusedColumnsForOutput:
    """Tests for remove_unused_columns_for_output method"""

    def test_drops_specified_columns(self):
        """Should drop specified columns"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame({
            "Stock": ["A"],
            "DropMe": [1],
            "KeepMe": [2]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler.remove_unused_columns_for_output(
            screen_df, save_df, ["DropMe"]
        )
        
        assert "DropMe" not in result_screen.columns
        assert "KeepMe" in result_screen.columns


class TestResultsLabelerRemoveUnknowns:
    """Tests for remove_unknowns method"""

    def test_handles_none_input(self):
        """Should handle None input"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        result = labeler.remove_unknowns(None, None)
        
        assert result == (None, None)

    def test_removes_dash_rows(self):
        """Should remove rows with all dashes"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(Mock())
        
        screen_df = pd.DataFrame({
            "Stock": ["A", "-"],
            "Price": [100, "-"]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = labeler.remove_unknowns(screen_df, save_df)
        
        assert len(result_screen) == 1


class TestLabelDataForPrintingImpl:
    """Tests for label_data_for_printing_impl function"""

    def test_handles_none_save_results(self):
        """Should handle None save_results"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        result = label_data_for_printing_impl(
            pd.DataFrame(), None, Mock(), 2.5, 9, 0, "X"
        )
        
        assert result[1] is None

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    @patch('pkscreener.classes.ResultsLabeler.Utility')
    @patch('pkscreener.classes.ResultsLabeler.ImageUtility')
    def test_full_processing(self, mock_image, mock_utility, mock_utils):
        """Should process dataframe fully"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        mock_utility.tools.formatRatio.return_value = "2.5x"
        mock_image.PKImageTools.removeAllColorStyles.return_value = "2.5"
        
        config_manager = Mock()
        config_manager.calculatersiintraday = False
        config_manager.daysToLookback = 22
        
        screen_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "volume": [1000, 2000],
            "RSI": [50, 60]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = label_data_for_printing_impl(
            screen_df, save_df, config_manager, 2.5, 9, 0, "X"
        )
        
        assert result_screen.index.name == "Stock"

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    @patch('pkscreener.classes.ResultsLabeler.Utility')
    @patch('pkscreener.classes.ResultsLabeler.ImageUtility')
    def test_atr_cross_formatting(self, mock_image, mock_utility, mock_utils):
        """Should format ATR for option 27"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        mock_utility.tools.formatRatio.return_value = "2.5x"
        mock_image.PKImageTools.removeAllColorStyles.return_value = "2.5"
        
        config_manager = Mock()
        config_manager.calculatersiintraday = False
        config_manager.daysToLookback = 22
        
        screen_df = pd.DataFrame({
            "Stock": ["A"],
            "volume": [1000],
            "ATR": [5.5]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = label_data_for_printing_impl(
            screen_df, save_df, config_manager, 2.5, 27, 0, "X"
        )
        
        # ATR should be formatted with color

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    @patch('pkscreener.classes.ResultsLabeler.Utility')
    @patch('pkscreener.classes.ResultsLabeler.ImageUtility')
    def test_drops_na_columns(self, mock_image, mock_utility, mock_utils):
        """Should drop all-NA columns"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        mock_utils.isTradingTime.return_value = False
        mock_utils.isTodayHoliday.return_value = (False, None)
        mock_utility.tools.formatRatio.return_value = "2.5x"
        mock_image.PKImageTools.removeAllColorStyles.return_value = "2.5"
        
        config_manager = Mock()
        config_manager.calculatersiintraday = False
        config_manager.daysToLookback = 22
        
        screen_df = pd.DataFrame({
            "Stock": ["A"],
            "volume": [1000],
            "AllNA": [np.nan]
        })
        save_df = screen_df.copy()
        
        result_screen, result_save = label_data_for_printing_impl(
            screen_df, save_df, config_manager, 2.5, 9, 0, "X"
        )
        
        assert "AllNA" not in result_screen.columns

    @patch('pkscreener.classes.ResultsLabeler.PKDateUtilities')
    @patch('pkscreener.classes.ResultsLabeler.Utility')
    @patch('pkscreener.classes.ResultsLabeler.ImageUtility')
    def test_rsi_intraday_combination(self, mock_image, mock_utility, mock_utils):
        """Should combine RSI/RSIi during trading"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        mock_utils.isTradingTime.return_value = True
        mock_utils.isTodayHoliday.return_value = (False, None)
        mock_utility.tools.formatRatio.return_value = "2.5x"
        mock_image.PKImageTools.removeAllColorStyles.return_value = "2.5"
        
        config_manager = Mock()
        config_manager.calculatersiintraday = True
        config_manager.daysToLookback = 22
        
        screen_df = pd.DataFrame({
            "Stock": ["A"],
            "volume": [1000],
            "RSI": [50],
            "RSIi": [55]
        })
        save_df = screen_df.copy()
        
        with patch.dict(os.environ, {}, clear=True):
            result_screen, result_save = label_data_for_printing_impl(
                screen_df, save_df, config_manager, 2.5, 9, 0, "X"
            )
        
        assert "RSI/i" in result_screen.columns
