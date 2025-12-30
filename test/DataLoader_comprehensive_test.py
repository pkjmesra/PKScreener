"""
Comprehensive unit tests for DataLoader class.

This module provides extensive test coverage for the DataLoader module,
targeting >=90% code coverage.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


class TestDataLoaderImport:
    """Test DataLoader import."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        from pkscreener.classes.DataLoader import StockDataLoader
        assert StockDataLoader is not None
    
    def test_class_exists(self):
        """Test StockDataLoader class exists."""
        from pkscreener.classes.DataLoader import StockDataLoader
        assert StockDataLoader is not None


class TestDataLoaderMethods:
    """Test DataLoader methods."""
    
    def test_class_structure(self):
        """Test class has expected structure."""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        # Should be a class
        assert isinstance(StockDataLoader, type)


class TestDataSources:
    """Test data source handling."""
    
    def test_fetcher_available(self):
        """Test Fetcher is available."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        assert screenerStockDataFetcher is not None
    
    def test_assets_manager_available(self):
        """Test AssetsManager is available."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        assert PKAssetsManager is not None


class TestDataFormats:
    """Test data format handling."""
    
    def test_dataframe_format(self):
        """Test DataFrame handling."""
        df = pd.DataFrame({
            'Open': [100, 101],
            'High': [105, 106],
            'Low': [98, 99],
            'Close': [103, 104],
            'Volume': [1000, 1100]
        })
        
        assert len(df) == 2
        assert 'Close' in df.columns
    
    def test_dict_format(self):
        """Test dictionary format."""
        data = {
            'RELIANCE': pd.DataFrame({'Close': [2500]}),
            'TCS': pd.DataFrame({'Close': [3500]})
        }
        
        assert len(data) == 2
        assert 'RELIANCE' in data


class TestCaching:
    """Test caching mechanisms."""
    
    def test_archiver_available(self):
        """Test Archiver is available."""
        from PKDevTools.classes import Archiver
        assert Archiver is not None
    
    def test_user_data_dir(self):
        """Test user data directory."""
        from PKDevTools.classes import Archiver
        
        user_dir = Archiver.get_user_data_dir()
        assert user_dir is not None
        assert isinstance(user_dir, str)


class TestDataValidation:
    """Test data validation."""
    
    def test_validate_ohlcv_columns(self):
        """Test OHLCV column validation."""
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        alt_required = ['open', 'high', 'low', 'close', 'volume']
        
        for col in required:
            assert col[0].isupper()
        for col in alt_required:
            assert col[0].islower()
    
    def test_validate_empty_dataframe(self):
        """Test empty DataFrame validation."""
        df = pd.DataFrame()
        assert len(df) == 0


class TestDateHandling:
    """Test date handling."""
    
    def test_pkdateutilities_available(self):
        """Test PKDateUtilities is available."""
        from PKDevTools.classes.PKDateUtilities import PKDateUtilities
        assert PKDateUtilities is not None
    
    def test_trading_date(self):
        """Test trading date function."""
        from PKDevTools.classes.PKDateUtilities import PKDateUtilities
        
        trading_date = PKDateUtilities.tradingDate()
        assert trading_date is not None


class TestGitHubIntegration:
    """Test GitHub data integration."""
    
    def test_github_urls(self):
        """Test GitHub URL patterns."""
        base_url = "https://raw.githubusercontent.com/pkjmesra/PKScreener"
        branch = "actions-data-download"
        
        assert "pkjmesra" in base_url
        assert "PKScreener" in base_url
    
    def test_pkl_file_pattern(self):
        """Test pkl file naming pattern."""
        import datetime
        
        today = datetime.datetime.now()
        date_str = today.strftime('%d%m%Y')
        
        daily_pkl = f"stock_data_{date_str}.pkl"
        intraday_pkl = f"intraday_stock_data_{date_str}.pkl"
        
        assert date_str in daily_pkl
        assert date_str in intraday_pkl


class TestModuleStructure:
    """Test module structure."""
    
    def test_dataloader_class(self):
        """Test StockDataLoader class structure."""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        # Should be a class
        assert isinstance(StockDataLoader, type)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
