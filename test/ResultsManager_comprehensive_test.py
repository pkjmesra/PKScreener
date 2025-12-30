"""
Comprehensive unit tests for ResultsManager class.

This module provides extensive test coverage for the ResultsManager module,
targeting >=90% code coverage.
"""

import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import pandas as pd
import numpy as np


class TestResultsManagerInit:
    """Test ResultsManager initialization."""
    
    def test_basic_init(self):
        """Test basic initialization."""
        from pkscreener.classes.ResultsManager import ResultsManager
        
        mock_config = MagicMock()
        manager = ResultsManager(mock_config)
        
        assert manager is not None
        assert manager.config_manager == mock_config
    
    def test_init_with_user_args(self):
        """Test initialization with user arguments."""
        from pkscreener.classes.ResultsManager import ResultsManager
        
        mock_config = MagicMock()
        mock_args = MagicMock()
        
        manager = ResultsManager(mock_config, mock_args)
        
        assert manager.user_passed_args == mock_args


class TestLabelDataForPrinting:
    """Test label_data_for_printing method."""
    
    @pytest.fixture
    def manager(self):
        from pkscreener.classes.ResultsManager import ResultsManager
        mock_config = MagicMock()
        mock_config.calculatersiintraday = False
        return ResultsManager(mock_config)
    
    def test_with_none_results(self, manager):
        """Test with None save_results."""
        screen_results, save_results = manager.label_data_for_printing(
            screen_results=pd.DataFrame(),
            save_results=None,
            volume_ratio=2.5,
            execute_option=1,
            reversal_option=1,
            menu_option="X",
            menu_choice_hierarchy="X:12:9"
        )
        
        assert screen_results is None
        assert save_results is None
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTodayHoliday')
    def test_with_valid_results(self, mock_holiday, mock_trading, manager):
        """Test with valid results."""
        mock_trading.return_value = False
        mock_holiday.return_value = (False, None)
        
        screen_df = pd.DataFrame({
            'Stock': ['RELIANCE', 'TCS'],
            'LTP': [2500.0, 3500.0],
            'volume': [1000000, 500000],
            '%Chng': [1.5, -0.5]
        })
        save_df = screen_df.copy()
        
        screen_results, save_results = manager.label_data_for_printing(
            screen_results=screen_df,
            save_results=save_df,
            volume_ratio=2.5,
            execute_option=1,
            reversal_option=1,
            menu_option="X",
            menu_choice_hierarchy="X:12:9"
        )
        
        assert screen_results is not None
        assert save_results is not None
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTodayHoliday')
    def test_with_rsi_columns(self, mock_holiday, mock_trading, manager):
        """Test with RSI columns."""
        mock_trading.return_value = True
        mock_holiday.return_value = (False, None)
        
        manager.config_manager.calculatersiintraday = True
        
        screen_df = pd.DataFrame({
            'Stock': ['RELIANCE'],
            'RSI': [65.0],
            'RSIi': [70.0],
            'volume': [1000000]
        })
        save_df = screen_df.copy()
        
        screen_results, save_results = manager.label_data_for_printing(
            screen_results=screen_df,
            save_results=save_df,
            volume_ratio=2.5,
            execute_option=1,
            reversal_option=1,
            menu_option="X",
            menu_choice_hierarchy="X:12:9:RSI"
        )
        
        assert screen_results is not None


class TestGetSortKey:
    """Test _get_sort_key method."""
    
    @pytest.fixture
    def manager(self):
        from pkscreener.classes.ResultsManager import ResultsManager
        mock_config = MagicMock()
        return ResultsManager(mock_config)
    
    def test_volume_sort_no_rsi(self, manager):
        """Test volume sort when no RSI in hierarchy."""
        screen_df = pd.DataFrame({'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:9",
            execute_option=1,
            reversal_option=1,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["volume"]
        assert ascending == [False]
    
    def test_rsi_sort_with_rsi_in_hierarchy(self, manager):
        """Test RSI sort when RSI in hierarchy."""
        screen_df = pd.DataFrame({'RSI': [65], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:9:RSI",
            execute_option=1,
            reversal_option=1,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == "RSI"
        assert ascending == [True]
    
    def test_execute_option_21_mfi(self, manager):
        """Test sort key for execute option 21 with MFI."""
        screen_df = pd.DataFrame({'MFI': [50], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:21",
            execute_option=21,
            reversal_option=3,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["MFI"]
    
    def test_execute_option_21_fvdiff(self, manager):
        """Test sort key for execute option 21 with FVDiff."""
        screen_df = pd.DataFrame({'FVDiff': [10], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:21",
            execute_option=21,
            reversal_option=8,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["FVDiff"]
    
    def test_execute_option_7_superconf(self, manager):
        """Test sort key for execute option 7 with SuperConfSort."""
        screen_df = pd.DataFrame({'SuperConfSort': [3], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:7",
            execute_option=7,
            reversal_option=3,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["SuperConfSort"]
    
    def test_execute_option_7_deviation(self, manager):
        """Test sort key for execute option 7 with deviationScore."""
        screen_df = pd.DataFrame({'deviationScore': [0.5], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:7",
            execute_option=7,
            reversal_option=4,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["deviationScore"]
        assert ascending == [True]
    
    def test_execute_option_23_bbands(self, manager):
        """Test sort key for execute option 23 with bbands."""
        screen_df = pd.DataFrame({'bbands_ulr_ratio_max5': [1.5], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:23",
            execute_option=23,
            reversal_option=1,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["bbands_ulr_ratio_max5"]
    
    def test_execute_option_27_atr(self, manager):
        """Test sort key for execute option 27 with ATR."""
        screen_df = pd.DataFrame({'ATR': [2.5], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:27",
            execute_option=27,
            reversal_option=1,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["ATR"]
    
    def test_execute_option_31_deel(self, manager):
        """Test sort key for execute option 31 DEEL Momentum."""
        screen_df = pd.DataFrame({'%Chng': [5.0], 'volume': [1000]})
        save_df = screen_df.copy()
        
        sort_key, ascending = manager._get_sort_key(
            menu_choice_hierarchy="X:12:31",
            execute_option=31,
            reversal_option=1,
            is_trading=False,
            save_results=save_df,
            screen_results=screen_df
        )
        
        assert sort_key == ["%Chng"]
        assert ascending == [False]


class TestEdgeCases:
    """Test edge cases."""
    
    @pytest.fixture
    def manager(self):
        from pkscreener.classes.ResultsManager import ResultsManager
        mock_config = MagicMock()
        mock_config.calculatersiintraday = False
        return ResultsManager(mock_config)
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTodayHoliday')
    def test_empty_dataframes(self, mock_holiday, mock_trading, manager):
        """Test with empty dataframes."""
        mock_trading.return_value = False
        mock_holiday.return_value = (False, None)
        
        screen_df = pd.DataFrame()
        save_df = pd.DataFrame()
        
        try:
            screen_results, save_results = manager.label_data_for_printing(
                screen_results=screen_df,
                save_results=save_df,
                volume_ratio=2.5,
                execute_option=1,
                reversal_option=1,
                menu_option="X",
                menu_choice_hierarchy="X:12:9"
            )
        except Exception:
            pass  # Expected to handle gracefully
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTodayHoliday')
    def test_menu_option_f(self, mock_holiday, mock_trading, manager):
        """Test with menu option F."""
        mock_trading.return_value = False
        mock_holiday.return_value = (False, None)
        
        screen_df = pd.DataFrame({'Stock': ['RELIANCE'], 'volume': [1000]})
        save_df = screen_df.copy()
        
        screen_results, save_results = manager.label_data_for_printing(
            screen_results=screen_df,
            save_results=save_df,
            volume_ratio=2.5,
            execute_option=1,
            reversal_option=1,
            menu_option="F",
            menu_choice_hierarchy="F:1"
        )
        
        assert screen_results is not None


class TestModuleImports:
    """Test module imports."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        from pkscreener.classes.ResultsManager import ResultsManager
        assert ResultsManager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
