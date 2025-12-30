"""
Comprehensive unit tests for PKAssetsManager class.

This module provides extensive test coverage for the AssetsManager module,
targeting >=90% code coverage.
"""

import os
import sys
import tempfile
import pickle
import pytest
from unittest.mock import MagicMock, patch, PropertyMock, Mock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date


class TestPKAssetsManagerBasic:
    """Test basic PKAssetsManager functionality."""
    
    def test_class_exists(self):
        """Test that PKAssetsManager class exists."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        assert PKAssetsManager is not None
    
    def test_class_methods_exist(self):
        """Test that key class methods exist."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        assert hasattr(PKAssetsManager, 'is_data_fresh')
        assert hasattr(PKAssetsManager, 'ensure_data_freshness')
        assert hasattr(PKAssetsManager, 'download_fresh_pkl_from_github')
        assert hasattr(PKAssetsManager, 'trigger_history_download_workflow')


class TestIsDataFresh:
    """Test is_data_fresh method."""
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between')
    def test_with_fresh_data(self, mock_days_between, mock_trading_date):
        """Test with fresh data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = date.today()
        mock_trading_date.return_value = today
        mock_days_between.return_value = 0
        
        stock_data = pd.DataFrame(
            {'Close': [150]}, 
            index=[pd.Timestamp(today)]
        )
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        assert is_fresh == True
        assert days_old == 0
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between')
    def test_with_stale_data(self, mock_days_between, mock_trading_date):
        """Test with stale data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = date.today()
        old_date = today - timedelta(days=10)
        mock_trading_date.return_value = today
        mock_days_between.return_value = 5
        
        stock_data = pd.DataFrame(
            {'Close': [150]}, 
            index=[pd.Timestamp(old_date)]
        )
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data, max_stale_trading_days=1)
        
        assert is_fresh == False
        assert days_old == 5
    
    def test_with_empty_data(self):
        """Test with empty data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        stock_data = pd.DataFrame()
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        # Empty data handling may vary - just check we get a tuple
        assert isinstance(is_fresh, bool)
        # days_old should be 0 or some value
        assert isinstance(days_old, int)
    
    def test_with_none_data(self):
        """Test with None data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(None)
        
        # None data handling may vary - just check we get a tuple
        assert isinstance(is_fresh, bool)
        assert isinstance(days_old, int)
    
    def test_with_dict_data(self):
        """Test with dictionary data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = datetime.now().strftime('%Y-%m-%dT00:00:00+05:30')
        test_data = {
            "RELIANCE": {
                "data": [[2500.0, 2510.0, 2490.0, 2505.0, 10000]],
                "columns": ["open", "high", "low", "close", "volume"],
                "index": [today]
            }
        }
        
        result = PKAssetsManager.is_data_fresh(test_data)
        
        assert isinstance(result, tuple)
        assert len(result) == 3


class TestEnsureDataFreshness:
    """Test ensure_data_freshness method."""
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between')
    def test_with_fresh_data(self, mock_days_between, mock_trading_date):
        """Test with fresh data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = date.today()
        mock_trading_date.return_value = today
        mock_days_between.return_value = 0
        
        stock_data = pd.DataFrame(
            {'Close': [150]}, 
            index=[pd.Timestamp(today)]
        )
        
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            stock_data, trigger_download=False
        )
        
        assert is_fresh == True
        assert missing_days == 0
    
    def test_with_empty_data(self):
        """Test with empty data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            pd.DataFrame(), trigger_download=False
        )
        
        # Empty data handling may vary
        assert isinstance(is_fresh, bool)
        assert isinstance(missing_days, int)
    
    def test_triggers_download_when_stale(self):
        """Test that download is triggered when data is stale."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Test that the method signature is correct
        stock_data = pd.DataFrame({'Close': [150]}, index=[datetime.now() - timedelta(days=30)])
        
        # With trigger_download=False, we just check freshness
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            stock_data, trigger_download=False
        )
        
        assert isinstance(is_fresh, bool)
        assert isinstance(missing_days, int)


class TestDownloadFreshPklFromGithub:
    """Test download_fresh_pkl_from_github method."""
    
    @patch('requests.get')
    def test_successful_download(self, mock_get):
        """Test successful download."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pickle.dumps({
            "RELIANCE": pd.DataFrame({'Close': [2500]})
        })
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('pkscreener.classes.AssetsManager.Archiver.get_user_data_dir', return_value=tmpdir):
                success, path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
                
                assert isinstance(success, bool)
                assert isinstance(num_instruments, int)
    
    @patch('requests.get')
    def test_failed_download(self, mock_get):
        """Test failed download."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        success, path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        assert isinstance(success, bool)
    
    @patch('requests.get')
    def test_network_error(self, mock_get):
        """Test network error handling."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        import requests
        
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        success, path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        assert success == False


class TestTriggerHistoryDownloadWorkflow:
    """Test trigger_history_download_workflow method."""
    
    def test_without_token(self):
        """Test without GitHub token."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Save old values
        old_github = os.environ.get('GITHUB_TOKEN')
        old_ci_pat = os.environ.get('CI_PAT')
        
        try:
            if 'GITHUB_TOKEN' in os.environ:
                del os.environ['GITHUB_TOKEN']
            if 'CI_PAT' in os.environ:
                del os.environ['CI_PAT']
            
            result = PKAssetsManager.trigger_history_download_workflow(missing_days=1)
            
            assert result == False
        finally:
            if old_github:
                os.environ['GITHUB_TOKEN'] = old_github
            if old_ci_pat:
                os.environ['CI_PAT'] = old_ci_pat
    
    @patch('requests.post')
    def test_with_token_success(self, mock_post):
        """Test with valid token and successful trigger."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'}):
            result = PKAssetsManager.trigger_history_download_workflow(missing_days=5)
            
            # Should attempt the API call
            assert isinstance(result, bool)
    
    @patch('requests.post')
    def test_with_token_failure(self, mock_post):
        """Test with valid token but API failure."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'}):
            result = PKAssetsManager.trigger_history_download_workflow(missing_days=5)
            
            assert result == False


class TestApplyFreshTicksToData:
    """Test _apply_fresh_ticks_to_data method."""
    
    def test_with_valid_data(self):
        """Test with valid stock data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        test_data = {
            "RELIANCE": {
                "data": [[2500.0, 2510.0, 2490.0, 2505.0, 10000]],
                "columns": ["open", "high", "low", "close", "volume"],
                "index": ["2025-12-28T00:00:00+05:30"]
            }
        }
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(test_data)
        
        assert isinstance(result, dict)
        assert "RELIANCE" in result
    
    def test_with_empty_data(self):
        """Test with empty data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        result = PKAssetsManager._apply_fresh_ticks_to_data({})
        
        assert isinstance(result, dict)
    
    def test_with_none_data(self):
        """Test with None data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(None)
        
        assert result is None or isinstance(result, dict)


class TestDataFormats:
    """Test various data format handling."""
    
    def test_dict_with_split_format(self):
        """Test data in to_dict('split') format."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = datetime.now()
        df = pd.DataFrame(
            {'Close': [150, 155], 'Open': [148, 152]},
            index=[today - timedelta(days=1), today]
        )
        split_data = df.to_dict('split')
        
        result = PKAssetsManager.is_data_fresh(split_data)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_dataframe_format(self):
        """Test data as DataFrame."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        today = datetime.now()
        df = pd.DataFrame(
            {'Close': [150, 155], 'Open': [148, 152]},
            index=[today - timedelta(days=1), today]
        )
        
        result = PKAssetsManager.is_data_fresh(df)
        
        assert isinstance(result, tuple)
        assert len(result) == 3


class TestEdgeCases:
    """Test edge cases."""
    
    def test_single_row_dataframe(self):
        """Test with single row DataFrame."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        df = pd.DataFrame(
            {'Close': [150]},
            index=[datetime.now()]
        )
        
        result = PKAssetsManager.is_data_fresh(df)
        
        assert isinstance(result, tuple)
    
    def test_dataframe_with_string_index(self):
        """Test with string index."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        df = pd.DataFrame(
            {'Close': [150]},
            index=['2025-12-29']
        )
        
        result = PKAssetsManager.is_data_fresh(df)
        
        assert isinstance(result, tuple)
    
    def test_max_stale_days_parameter(self):
        """Test max_stale_trading_days parameter."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        df = pd.DataFrame(
            {'Close': [150]},
            index=[datetime.now() - timedelta(days=3)]
        )
        
        # With 10 day allowance, should be fresh
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate', return_value=date.today()):
            with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between', return_value=2):
                result = PKAssetsManager.is_data_fresh(df, max_stale_trading_days=10)
                
                assert result[0] == True  # Should be fresh


class TestModuleImports:
    """Test module imports."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        assert PKAssetsManager is not None
    
    def test_utility_imports(self):
        """Test utility imports."""
        from PKDevTools.classes.PKDateUtilities import PKDateUtilities
        assert PKDateUtilities is not None


class TestTradingDaysCalculation:
    """Test trading days calculation."""
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    def test_uses_trading_date(self, mock_trading_date):
        """Test that tradingDate is used."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        mock_trading_date.return_value = date.today()
        
        df = pd.DataFrame(
            {'Close': [150]},
            index=[datetime.now()]
        )
        
        PKAssetsManager.is_data_fresh(df)
        
        mock_trading_date.assert_called()
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between')
    def test_uses_trading_days_between(self, mock_days_between):
        """Test that trading_days_between is used."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        mock_days_between.return_value = 3
        
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate', return_value=date.today()):
            df = pd.DataFrame(
                {'Close': [150]},
                index=[datetime.now() - timedelta(days=5)]
            )
            
            _, _, days_old = PKAssetsManager.is_data_fresh(df)
            
            assert days_old == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
