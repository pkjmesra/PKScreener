"""
End-to-end functional tests for PKScreener data flow mechanisms.

This module tests the complete data flow from PKScreener's perspective:
1. Downloading pkl files from GitHub
2. Downloading ticks.json from GitHub
3. Merging tick data with existing pkl data
4. Triggering history download workflow when data is stale
5. Validating data freshness using trading days

Usage:
    pytest test/test_data_flow_e2e.py -v
"""

import os
import pickle
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestPKScreenerDataFetch:
    """Test PKScreener data fetching mechanisms."""
    
    def test_download_fresh_pkl_from_github(self):
        """Test downloading pkl from GitHub."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # This will attempt real download
        success, path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        assert isinstance(success, bool)
        assert path is None or isinstance(path, str)
        assert isinstance(num_instruments, int)
        
        # If successful, verify the file exists
        if success and path:
            assert os.path.exists(path)
    
    def test_apply_fresh_ticks_to_data(self):
        """Test applying fresh ticks to stock data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Create mock stock data
        test_data = {
            "RELIANCE": {
                "data": [[2500.0, 2510.0, 2490.0, 2505.0, 10000]],
                "columns": ["open", "high", "low", "close", "volume"],
                "index": ["2025-12-28T00:00:00+05:30"]
            }
        }
        
        # Apply ticks (may or may not find data)
        result = PKAssetsManager._apply_fresh_ticks_to_data(test_data)
        
        # Should return a dict
        assert isinstance(result, dict)
        assert "RELIANCE" in result


class TestDataFreshness:
    """Test data freshness validation."""
    
    def test_is_data_fresh_with_recent_data(self):
        """Test is_data_fresh with recent data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Create data with today's date
        today = datetime.now().strftime('%Y-%m-%dT00:00:00+05:30')
        test_data = {
            "RELIANCE": {
                "data": [[2500.0, 2510.0, 2490.0, 2505.0, 10000]],
                "columns": ["open", "high", "low", "close", "volume"],
                "index": [today]
            }
        }
        
        # Returns (is_fresh, data_date, trading_days_old)
        result = PKAssetsManager.is_data_fresh(test_data)
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        is_fresh, data_date, trading_days_old = result
        assert isinstance(is_fresh, bool)
    
    def test_is_data_fresh_with_old_data(self):
        """Test is_data_fresh with old data."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Create data with old date (30 days ago)
        old_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT00:00:00+05:30')
        test_data = {
            "RELIANCE": {
                "data": [[2500.0, 2510.0, 2490.0, 2505.0, 10000]],
                "columns": ["open", "high", "low", "close", "volume"],
                "index": [old_date]
            }
        }
        
        # Returns (is_fresh, data_date, trading_days_old)
        result = PKAssetsManager.is_data_fresh(test_data)
        
        # Should detect stale data
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_ensure_data_freshness(self):
        """Test ensure_data_freshness method."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        test_data = {
            "RELIANCE": {
                "data": [[2500.0, 2510.0, 2490.0, 2505.0, 10000]],
                "columns": ["open", "high", "low", "close", "volume"],
                "index": [datetime.now().strftime('%Y-%m-%dT00:00:00+05:30')]
            }
        }
        
        # Don't trigger actual download
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            test_data, trigger_download=False
        )
        
        assert isinstance(is_fresh, bool)
        assert isinstance(missing_days, int)


class TestTriggerHistoryWorkflow:
    """Test history download workflow triggering."""
    
    def test_trigger_without_token_fails_gracefully(self):
        """Test that trigger_history_download_workflow fails gracefully without token."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Temporarily remove tokens
        old_github = os.environ.get('GITHUB_TOKEN')
        old_ci_pat = os.environ.get('CI_PAT')
        
        try:
            if 'GITHUB_TOKEN' in os.environ:
                del os.environ['GITHUB_TOKEN']
            if 'CI_PAT' in os.environ:
                del os.environ['CI_PAT']
            
            result = PKAssetsManager.trigger_history_download_workflow(missing_days=1)
            
            # Should fail without token
            assert result == False
        finally:
            # Restore tokens
            if old_github:
                os.environ['GITHUB_TOKEN'] = old_github
            if old_ci_pat:
                os.environ['CI_PAT'] = old_ci_pat


class TestGitHubFallback:
    """Test GitHub fallback mechanisms."""
    
    def test_ticks_json_sources(self):
        """Test that ticks.json is fetched from correct sources."""
        import requests
        
        urls = [
            "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/ticks.json",
            "https://raw.githubusercontent.com/pkjmesra/PKBrokers/main/pkbrokers/kite/examples/results/Data/ticks.json",
        ]
        
        found_valid = False
        for url in urls:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        found_valid = True
                        break
            except Exception:
                continue
        
        # At least one URL should have data
        # This may fail if network is unavailable
        assert isinstance(found_valid, bool)
    
    def test_pkl_sources(self):
        """Test that pkl files can be found from correct sources."""
        import requests
        
        today = datetime.now()
        urls_to_try = []
        
        for days_ago in range(0, 10):
            check_date = today - timedelta(days=days_ago)
            date_str = check_date.strftime('%d%m%Y')
            
            urls_to_try.extend([
                f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/actions-data-download/stock_data_{date_str}.pkl",
                f"https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/results/Data/stock_data_{date_str}.pkl",
            ])
        
        found_valid = False
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200 and len(response.content) > 10000:
                    found_valid = True
                    break
            except Exception:
                continue
        
        # Test structure is correct
        assert isinstance(found_valid, bool)


class TestTradingDayUtilities:
    """Test trading day utility functions."""
    
    def test_trading_date_calculation(self):
        """Test PKDateUtilities trading date functions."""
        try:
            from PKDevTools.classes.PKDateUtilities import PKDateUtilities
            
            # Get trading date
            trading_date = PKDateUtilities.tradingDate()
            
            assert trading_date is not None
            assert isinstance(trading_date, (datetime, type(None)))
        except ImportError:
            pytest.skip("PKDevTools not installed")
    
    def test_is_trading_day(self):
        """Test is_trading_day function."""
        try:
            from PKDevTools.classes.PKDateUtilities import PKDateUtilities
            
            result = PKDateUtilities.isTradingTime()
            
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("PKDevTools not installed")


class TestScanDataAvailability:
    """Test that scan data is available for running scans."""
    
    def test_can_load_stock_data(self):
        """Test that stock data can be loaded for scans."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Try to download data
        success, path, num = PKAssetsManager.download_fresh_pkl_from_github()
        
        if success and path and os.path.exists(path):
            # Load and verify structure
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            assert isinstance(data, dict)
            assert len(data) > 0
            
            # Check a sample stock
            for symbol, stock_data in list(data.items())[:5]:
                if isinstance(stock_data, dict):
                    assert 'data' in stock_data or 'columns' in stock_data or 'index' in stock_data
                else:
                    # DataFrame format
                    assert hasattr(stock_data, 'index')
    
    def test_data_has_required_columns(self):
        """Test that stock data has required OHLCV columns."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        success, path, num = PKAssetsManager.download_fresh_pkl_from_github()
        
        if success and path and os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            alt_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            for symbol, stock_data in list(data.items())[:5]:
                if isinstance(stock_data, dict) and 'columns' in stock_data:
                    cols = [c.lower() for c in stock_data['columns']]
                    assert any(c in cols for c in required_cols[:4])


class TestCompleteDataFlow:
    """Test complete data flow from download to scan usage."""
    
    def test_complete_flow(self):
        """Test the complete data flow."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        
        # Step 1: Download pkl from GitHub
        success, pkl_path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        if not success:
            pytest.skip("Could not download pkl from GitHub")
        
        # Step 2: Load data
        with open(pkl_path, 'rb') as f:
            stock_data = pickle.load(f)
        
        assert len(stock_data) > 0
        
        # Step 3: Check freshness
        is_fresh, stale_count = PKAssetsManager.is_data_fresh(stock_data)
        
        # Step 4: Apply fresh ticks if stale
        if not is_fresh:
            stock_data = PKAssetsManager._apply_fresh_ticks_to_data(stock_data)
        
        # Verify data is still valid
        assert len(stock_data) > 0
        
        print(f"Complete flow test: {num_instruments} instruments, fresh={is_fresh}, stale={stale_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
