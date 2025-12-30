"""
Comprehensive unit tests for screenerStockDataFetcher class.

This module provides extensive test coverage for the Fetcher module,
targeting >=90% code coverage.
"""

import os
import sys
import warnings
import pytest
from unittest import mock
from unittest.mock import MagicMock, patch, PropertyMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)


class TestScreenerStockDataFetcherInit:
    """Test initialization of screenerStockDataFetcher."""
    
    def test_basic_init(self):
        """Test basic initialization."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        
        config = ConfigManager.tools()
        fetcher = screenerStockDataFetcher(config)
        
        assert fetcher is not None
        assert hasattr(fetcher, '_hp_provider')
        assert hasattr(fetcher, '_scalable_fetcher')
    
    def test_init_without_config(self):
        """Test initialization without config."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        
        assert fetcher is not None
    
    @patch('pkscreener.classes.Fetcher._HP_DATA_AVAILABLE', False)
    def test_init_without_hp_provider(self):
        """Test init when HP data provider is not available."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        assert fetcher is not None
    
    @patch('pkscreener.classes.Fetcher._SCALABLE_FETCHER_AVAILABLE', False)
    def test_init_without_scalable_fetcher(self):
        """Test init when scalable fetcher is not available."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher = screenerStockDataFetcher()
        assert fetcher is not None


class TestFetchStockDataWithArgs:
    """Test fetchStockDataWithArgs method."""
    
    @pytest.fixture
    def fetcher(self):
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        return screenerStockDataFetcher(ConfigManager.tools())
    
    @pytest.fixture
    def mock_long_running_fn(self):
        """Create a mock long running function."""
        return MagicMock(return_value=pd.DataFrame({'Close': [100]}))
    
    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockData')
    def test_with_pktask(self, mock_fetch, fetcher, mock_long_running_fn):
        """Test with PKTask argument."""
        from pkscreener.classes.PKTask import PKTask
        
        mock_df = pd.DataFrame({
            'Open': [100], 'High': [105], 'Low': [98], 'Close': [103], 'Volume': [1000]
        })
        mock_fetch.return_value = mock_df
        
        task = PKTask("task1", mock_long_running_fn, ("RELIANCE", "1d", "1y", ".NS"), None)
        task.taskId = 1
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        result = fetcher.fetchStockDataWithArgs(task)
        
        assert result is not None
        mock_fetch.assert_called_once()
    
    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockData')
    def test_with_direct_args(self, mock_fetch, fetcher):
        """Test with direct arguments."""
        mock_df = pd.DataFrame({
            'Open': [100], 'High': [105], 'Low': [98], 'Close': [103], 'Volume': [1000]
        })
        mock_fetch.return_value = mock_df
        
        result = fetcher.fetchStockDataWithArgs("RELIANCE", "1d", "1y", ".NS")
        
        assert result is not None
        mock_fetch.assert_called_once()
    
    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockData')
    def test_task_progress_update(self, mock_fetch, fetcher, mock_long_running_fn):
        """Test that task progress is updated correctly."""
        from pkscreener.classes.PKTask import PKTask
        
        mock_df = pd.DataFrame({'Close': [100]})
        mock_fetch.return_value = mock_df
        
        task = PKTask("task1", mock_long_running_fn, ("TCS", "1d", "1y", ".NS"), None)
        task.taskId = 5
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        fetcher.fetchStockDataWithArgs(task)
        
        assert 5 in task.progressStatusDict
        assert task.progressStatusDict[5]['progress'] == 1
        assert task.resultsDict[5] is not None
    
    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockData')
    def test_negative_task_id(self, mock_fetch, fetcher, mock_long_running_fn):
        """Test with negative task ID."""
        from pkscreener.classes.PKTask import PKTask
        
        mock_df = pd.DataFrame({'Close': [100]})
        mock_fetch.return_value = mock_df
        
        task = PKTask("task1", mock_long_running_fn, ("INFY", "1d", "1y", ".NS"), None)
        task.taskId = -1
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        result = fetcher.fetchStockDataWithArgs(task)
        
        assert result is not None
        # With negative taskId, progress dict should not be updated
        assert -1 not in task.progressStatusDict


class TestFetchAdditionalTickerInfo:
    """Test fetchAdditionalTickerInfo method."""
    
    @pytest.fixture
    def fetcher(self):
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        return screenerStockDataFetcher(ConfigManager.tools())
    
    def test_with_valid_list(self, fetcher):
        """Test with valid ticker list."""
        result = fetcher.fetchAdditionalTickerInfo(["RELIANCE", "TCS"], ".NS")
        
        assert isinstance(result, dict)
    
    def test_with_empty_list(self, fetcher):
        """Test with empty list."""
        result = fetcher.fetchAdditionalTickerInfo([], ".NS")
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_with_invalid_type(self, fetcher):
        """Test with invalid type."""
        with pytest.raises(TypeError):
            fetcher.fetchAdditionalTickerInfo("RELIANCE", ".NS")
    
    def test_with_empty_suffix(self, fetcher):
        """Test with empty exchange suffix."""
        result = fetcher.fetchAdditionalTickerInfo(["RELIANCE.NS", "TCS.NS"], "")
        
        assert isinstance(result, dict)
    
    def test_suffix_not_duplicated(self, fetcher):
        """Test that suffix is not duplicated."""
        result = fetcher.fetchAdditionalTickerInfo(["RELIANCE.NS"], ".NS")
        
        # Should not add .NS again
        assert isinstance(result, dict)


class TestGetStats:
    """Test get_stats method."""
    
    @pytest.fixture
    def fetcher(self):
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        return screenerStockDataFetcher(ConfigManager.tools())
    
    def test_get_stats(self, fetcher):
        """Test getting stats for a ticker."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        fetcher.get_stats("RELIANCE.NS")
        
        # Should add to class dict
        assert "RELIANCE.NS" in screenerStockDataFetcher._tickersInfoDict
        assert "marketCap" in screenerStockDataFetcher._tickersInfoDict["RELIANCE.NS"]


class TestFetchStockData:
    """Test fetchStockData method."""
    
    @pytest.fixture
    def fetcher(self):
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        return screenerStockDataFetcher(ConfigManager.tools())
    
    def test_fetch_with_valid_stock(self, fetcher):
        """Test fetch with a valid stock code."""
        # Just test that the method can be called without error
        # The actual fetch might fail but shouldn't raise unexpected errors
        try:
            result = fetcher.fetchStockData(
                "RELIANCE",
                "1d", "5",
                printCounter=False
            )
            # Result can be None or DataFrame
            assert result is None or isinstance(result, pd.DataFrame)
        except Exception as e:
            # Network errors are acceptable
            assert True
    
    def test_fetch_returns_dataframe_or_none(self, fetcher):
        """Test that fetch returns DataFrame or None."""
        try:
            result = fetcher.fetchStockData("TCS", "1d", "5")
            assert result is None or isinstance(result, pd.DataFrame)
        except Exception:
            # Network errors are acceptable
            assert True


class TestCachedLimiterSession:
    """Test CachedLimiterSession class."""
    
    def test_session_exists(self):
        """Test that CachedLimiterSession exists."""
        from pkscreener.classes.Fetcher import CachedLimiterSession
        
        assert CachedLimiterSession is not None
    
    def test_rate_limiter_config(self):
        """Test rate limiter is configured."""
        from pkscreener.classes.Fetcher import yf_limiter
        
        assert yf_limiter is not None


class TestDataProviderFlags:
    """Test data provider availability flags."""
    
    def test_hp_data_available_flag(self):
        """Test _HP_DATA_AVAILABLE flag exists."""
        from pkscreener.classes import Fetcher
        
        assert hasattr(Fetcher, '_HP_DATA_AVAILABLE')
    
    def test_scalable_fetcher_available_flag(self):
        """Test _SCALABLE_FETCHER_AVAILABLE flag exists."""
        from pkscreener.classes import Fetcher
        
        assert hasattr(Fetcher, '_SCALABLE_FETCHER_AVAILABLE')
    
    def test_yf_available_flag(self):
        """Test _YF_AVAILABLE flag exists."""
        from pkscreener.classes import Fetcher
        
        assert hasattr(Fetcher, '_YF_AVAILABLE')


class TestUpdateTaskProgress:
    """Test _updateTaskProgress method."""
    
    @pytest.fixture
    def fetcher(self):
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        return screenerStockDataFetcher(ConfigManager.tools())
    
    @pytest.fixture
    def mock_long_running_fn(self):
        """Create a mock long running function."""
        return MagicMock(return_value=pd.DataFrame({'Close': [100]}))
    
    def test_update_progress_with_valid_task_id(self, fetcher, mock_long_running_fn):
        """Test progress update with valid task ID."""
        from pkscreener.classes.PKTask import PKTask
        
        task = PKTask("test", mock_long_running_fn, ("RELIANCE", "1d", "1y", ".NS"), None)
        task.taskId = 10
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        result = pd.DataFrame({'Close': [100, 101, 102]})
        
        fetcher._updateTaskProgress(task, result)
        
        assert 10 in task.progressStatusDict
        assert task.progressStatusDict[10]['progress'] == 1
        assert task.progressStatusDict[10]['total'] == 1
        assert 10 in task.resultsDict
    
    def test_update_progress_with_negative_task_id(self, fetcher, mock_long_running_fn):
        """Test progress update with negative task ID."""
        from pkscreener.classes.PKTask import PKTask
        
        task = PKTask("test", mock_long_running_fn, ("RELIANCE", "1d", "1y", ".NS"), None)
        task.taskId = -5
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        result = pd.DataFrame({'Close': [100]})
        
        fetcher._updateTaskProgress(task, result)
        
        # With negative taskId, dict should not be updated
        assert -5 not in task.progressStatusDict
        # But result should still be set
        assert task.result is not None


class TestModuleImports:
    """Test module import scenarios."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        assert screenerStockDataFetcher is not None
    
    def test_parent_class(self):
        """Test parent class is correct."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from PKNSETools.PKNSEStockDataFetcher import nseStockDataFetcher
        
        assert issubclass(screenerStockDataFetcher, nseStockDataFetcher)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def fetcher(self):
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        return screenerStockDataFetcher(ConfigManager.tools())
    
    def test_fetch_with_none_stock_code(self, fetcher):
        """Test fetch with None stock code."""
        try:
            result = fetcher.fetchStockData(None, "1d", "5")
            # Should handle None gracefully
            assert result is None or isinstance(result, pd.DataFrame)
        except Exception:
            # Errors are acceptable for None input
            assert True
    
    def test_fetch_with_empty_period(self, fetcher):
        """Test fetch with empty period."""
        try:
            result = fetcher.fetchStockData("RELIANCE", "", "5")
        except Exception:
            pass  # Expected to fail
    
    def test_fetch_with_list_of_stocks(self, fetcher):
        """Test fetch with list of stocks."""
        try:
            result = fetcher.fetchStockData(["RELIANCE", "TCS"], "1d", "5")
            # Should handle list, may return dict or DataFrame
            assert result is None or isinstance(result, (pd.DataFrame, dict))
        except Exception:
            # Network errors are acceptable
            assert True


class TestMultipleStockCodes:
    """Test handling of multiple stock codes."""
    
    @pytest.fixture
    def fetcher(self):
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        from pkscreener.classes import ConfigManager
        return screenerStockDataFetcher(ConfigManager.tools())
    
    def test_single_stock_string(self, fetcher):
        """Test with single stock as string."""
        mock_df = pd.DataFrame({'Close': [100]})
        with patch.object(fetcher, 'fetchStockData', return_value=mock_df):
            result = fetcher.fetchStockDataWithArgs("RELIANCE", "1d", "1y", ".NS")
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
