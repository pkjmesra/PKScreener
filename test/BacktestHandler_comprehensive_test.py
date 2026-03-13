"""
Comprehensive unit tests for BacktestHandler class.

This module provides extensive test coverage for the BacktestHandler module,
targeting >=90% code coverage.
"""

import os
import sys
import pytest
from unittest import mock
from unittest.mock import MagicMock, patch, PropertyMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestBacktestHandlerInit:
    """Test BacktestHandler initialization."""
    
    def test_basic_init(self):
        """Test basic initialization."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        
        mock_config = MagicMock()
        mock_config.backtestPeriod = 30
        
        handler = BacktestHandler(mock_config)
        
        assert handler is not None
        assert handler.config_manager == mock_config
        assert handler.elapsed_time == 0
    
    def test_init_with_user_args(self):
        """Test initialization with user arguments."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        
        mock_config = MagicMock()
        mock_args = MagicMock()
        
        handler = BacktestHandler(mock_config, mock_args)
        
        assert handler.user_passed_args == mock_args


class TestGetHistoricalDays:
    """Test get_historical_days method."""
    
    @pytest.fixture
    def handler(self):
        from pkscreener.classes.BacktestHandler import BacktestHandler
        mock_config = MagicMock()
        mock_config.backtestPeriod = 30
        return BacktestHandler(mock_config)
    
    def test_testing_mode(self, handler):
        """Test returns 2 in testing mode."""
        result = handler.get_historical_days(100, testing=True)
        assert result == 2
    
    def test_non_testing_mode(self, handler):
        """Test returns config value in non-testing mode."""
        result = handler.get_historical_days(100, testing=False)
        assert result == 30
    
    def test_with_different_period(self):
        """Test with different backtest period."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        
        mock_config = MagicMock()
        mock_config.backtestPeriod = 15
        handler = BacktestHandler(mock_config)
        
        result = handler.get_historical_days(50, testing=False)
        assert result == 15


class TestTakeBacktestInputs:
    """Test take_backtest_inputs method."""
    
    @pytest.fixture
    def handler(self):
        from pkscreener.classes.BacktestHandler import BacktestHandler
        mock_config = MagicMock()
        mock_config.backtestPeriod = 30
        return BacktestHandler(mock_config)
    
    def test_with_preset_period(self, handler):
        """Test with pre-set backtest period."""
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
            result = handler.take_backtest_inputs(
                menu_option="B",
                index_option=1,
                execute_option=1,
                backtest_period=15
            )
            
            assert result[2] == 15
    
    def test_default_period_for_growth(self, handler):
        """Test default period for Growth of 10k."""
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
            with patch('builtins.input', side_effect=ValueError()):
                result = handler.take_backtest_inputs(
                    menu_option="G",
                    backtest_period=0
                )
                
                assert result[2] == 3
    
    def test_default_period_for_backtest(self, handler):
        """Test default period for regular backtest."""
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
            with patch('builtins.input', side_effect=ValueError()):
                result = handler.take_backtest_inputs(
                    menu_option="B",
                    backtest_period=0
                )
                
                assert result[2] == 30


class TestUpdateBacktestResults:
    """Test update_backtest_results method."""
    
    @pytest.fixture
    def handler(self):
        from pkscreener.classes.BacktestHandler import BacktestHandler
        mock_config = MagicMock()
        mock_config.backtestPeriod = 30
        return BacktestHandler(mock_config)
    
    @patch('pkscreener.classes.BacktestHandler.backtest')
    def test_basic_update(self, mock_backtest, handler):
        """Test basic update of backtest results."""
        import time
        
        mock_df = pd.DataFrame({'Stock': ['RELIANCE'], 'Return': [5.0]})
        mock_backtest.return_value = mock_df
        
        result = (
            pd.DataFrame({'Stock': ['TCS']}),  # result[0]
            pd.DataFrame({'Col': [1]}),        # result[1]
            pd.DataFrame({'Col': [2]}),        # result[2]
            pd.DataFrame({'Col': [3]}),        # result[3]
        )
        
        selected_choice = {"2": "1", "3": "1"}
        
        updated_df = handler.update_backtest_results(
            backtest_period=10,
            start_time=time.time(),
            result=result,
            sample_days=5,
            backtest_df=None,
            selected_choice=selected_choice
        )
        
        assert updated_df is not None
        mock_backtest.assert_called_once()
    
    @patch('pkscreener.classes.BacktestHandler.backtest')
    def test_sell_signal_detection(self, mock_backtest, handler):
        """Test sell signal detection."""
        import time
        
        mock_df = pd.DataFrame()
        mock_backtest.return_value = mock_df
        
        result = (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )
        
        # Sell signal conditions
        selected_choice = {"2": "6", "3": "2"}
        
        handler.update_backtest_results(
            backtest_period=10,
            start_time=time.time(),
            result=result,
            sample_days=5,
            backtest_df=None,
            selected_choice=selected_choice
        )
        
        # Check that backtest was called with sell_signal=True
        call_args = mock_backtest.call_args
        assert call_args[0][7] == True  # sell_signal is 8th argument


class TestElapsedTime:
    """Test elapsed time tracking."""
    
    def test_elapsed_time_updated(self):
        """Test that elapsed_time is updated after backtest."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        import time
        
        mock_config = MagicMock()
        handler = BacktestHandler(mock_config)
        
        initial_time = handler.elapsed_time
        assert initial_time == 0
        
        with patch('pkscreener.classes.BacktestHandler.backtest', return_value=pd.DataFrame()):
            start = time.time()
            result = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
            
            handler.update_backtest_results(
                backtest_period=5,
                start_time=start,
                result=result,
                sample_days=5,
                backtest_df=None,
                selected_choice={"2": "1", "3": "1"}
            )
            
            # Elapsed time should be updated
            assert handler.elapsed_time >= 0


class TestSellSignalConditions:
    """Test sell signal detection conditions."""
    
    @pytest.fixture
    def handler(self):
        from pkscreener.classes.BacktestHandler import BacktestHandler
        mock_config = MagicMock()
        return BacktestHandler(mock_config)
    
    @patch('pkscreener.classes.BacktestHandler.backtest')
    def test_sell_signal_option_6_2(self, mock_backtest, handler):
        """Test sell signal with option 6, 2."""
        import time
        
        mock_backtest.return_value = pd.DataFrame()
        result = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        
        handler.update_backtest_results(
            backtest_period=5,
            start_time=time.time(),
            result=result,
            sample_days=5,
            backtest_df=None,
            selected_choice={"2": "6", "3": "2"}
        )
        
        call_args = mock_backtest.call_args[0]
        assert call_args[7] == True
    
    @patch('pkscreener.classes.BacktestHandler.backtest')
    def test_sell_signal_option_7_2(self, mock_backtest, handler):
        """Test sell signal with option 7, 2."""
        import time
        
        mock_backtest.return_value = pd.DataFrame()
        result = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        
        handler.update_backtest_results(
            backtest_period=5,
            start_time=time.time(),
            result=result,
            sample_days=5,
            backtest_df=None,
            selected_choice={"2": "7", "3": "2"}
        )
        
        call_args = mock_backtest.call_args[0]
        assert call_args[7] == True
    
    @patch('pkscreener.classes.BacktestHandler.backtest')
    def test_sell_signal_option_15(self, mock_backtest, handler):
        """Test sell signal with option 15."""
        import time
        
        mock_backtest.return_value = pd.DataFrame()
        result = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        
        handler.update_backtest_results(
            backtest_period=5,
            start_time=time.time(),
            result=result,
            sample_days=5,
            backtest_df=None,
            selected_choice={"2": "15", "3": "1"}
        )
        
        call_args = mock_backtest.call_args[0]
        assert call_args[7] == True
    
    @patch('pkscreener.classes.BacktestHandler.backtest')
    def test_no_sell_signal(self, mock_backtest, handler):
        """Test no sell signal with regular options."""
        import time
        
        mock_backtest.return_value = pd.DataFrame()
        result = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        
        handler.update_backtest_results(
            backtest_period=5,
            start_time=time.time(),
            result=result,
            sample_days=5,
            backtest_df=None,
            selected_choice={"2": "1", "3": "1"}
        )
        
        call_args = mock_backtest.call_args[0]
        assert call_args[7] == False


class TestModuleImports:
    """Test module imports."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        assert BacktestHandler is not None
    
    def test_backtest_import(self):
        """Test backtest function import."""
        from pkscreener.classes.Backtest import backtest
        assert backtest is not None
    
    def test_backtest_summary_import(self):
        """Test backtestSummary import."""
        from pkscreener.classes.Backtest import backtestSummary
        assert backtestSummary is not None


class TestEdgeCases:
    """Test edge cases."""
    
    @pytest.fixture
    def handler(self):
        from pkscreener.classes.BacktestHandler import BacktestHandler
        mock_config = MagicMock()
        mock_config.backtestPeriod = 30
        return BacktestHandler(mock_config)
    
    def test_empty_backtest_df(self, handler):
        """Test with empty backtest DataFrame."""
        import time
        
        with patch('pkscreener.classes.BacktestHandler.backtest', return_value=pd.DataFrame()):
            result = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
            
            updated = handler.update_backtest_results(
                backtest_period=5,
                start_time=time.time(),
                result=result,
                sample_days=0,
                backtest_df=pd.DataFrame(),
                selected_choice={"2": "1", "3": "1"}
            )
            
            assert isinstance(updated, pd.DataFrame)
    
    def test_with_existing_backtest_df(self, handler):
        """Test with existing backtest DataFrame."""
        import time
        
        existing_df = pd.DataFrame({'Stock': ['RELIANCE'], 'Return': [5.0]})
        new_df = pd.DataFrame({'Stock': ['TCS'], 'Return': [3.0]})
        
        with patch('pkscreener.classes.BacktestHandler.backtest', return_value=new_df):
            result = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
            
            updated = handler.update_backtest_results(
                backtest_period=5,
                start_time=time.time(),
                result=result,
                sample_days=5,
                backtest_df=existing_df,
                selected_choice={"2": "1", "3": "1"}
            )
            
            assert updated is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
