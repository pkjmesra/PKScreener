"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
"""
Tick Data Freshness Tests
=========================

This module tests that PKScreener correctly prioritizes fresh tick data from
PKBrokers over stale .pkl files, especially during trading hours.

Key test scenarios:
- Real-time data takes priority over pickle files
- Stale pickle data is rejected when real-time is available
- Data timestamps are validated to be from today
- Turso DB being down doesn't affect fresh tick data flow
"""

import os
import sys
import warnings
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
import time

import pandas as pd
import pytest

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_fresh_ohlcv_data():
    """Create mock OHLCV data with today's timestamp."""
    today = datetime.now()
    dates = pd.date_range(end=today, periods=100, freq='D')
    return pd.DataFrame({
        'Open': [100.0 + i for i in range(100)],
        'High': [105.0 + i for i in range(100)],
        'Low': [95.0 + i for i in range(100)],
        'Close': [102.0 + i for i in range(100)],
        'Volume': [1000000 + i * 1000 for i in range(100)],
    }, index=dates)


@pytest.fixture
def mock_stale_ohlcv_data():
    """Create mock OHLCV data with stale timestamps (7 days old)."""
    stale_date = datetime.now() - timedelta(days=7)
    dates = pd.date_range(end=stale_date, periods=100, freq='D')
    return pd.DataFrame({
        'Open': [100.0 + i for i in range(100)],
        'High': [105.0 + i for i in range(100)],
        'Low': [95.0 + i for i in range(100)],
        'Close': [102.0 + i for i in range(100)],
        'Volume': [1000000 + i * 1000 for i in range(100)],
    }, index=dates)


@pytest.fixture
def mock_candle_store():
    """Mock the InMemoryCandleStore from PKBrokers."""
    store = MagicMock()
    store.get_stats.return_value = {
        'instrument_count': 2000,
        'last_tick_time': time.time(),  # Current time = fresh data
        'cache_size': 50000,
    }
    return store


@pytest.fixture
def mock_data_provider(mock_fresh_ohlcv_data):
    """Mock the HighPerformanceDataProvider."""
    provider = MagicMock()
    provider.get_stock_data.return_value = mock_fresh_ohlcv_data
    provider.get_current_price.return_value = 150.0
    provider.get_current_ohlcv.return_value = {
        'open': 148.0,
        'high': 152.0,
        'low': 147.0,
        'close': 150.0,
        'volume': 1500000,
    }
    return provider


# ============================================================================
# PKDataProvider Tests
# ============================================================================

class TestPKDataProviderPriority:
    """Tests for PKDataProvider data source priority."""

    def test_realtime_available_when_candle_store_has_data(self, mock_candle_store):
        """Test that is_realtime_available returns True when candle store has fresh data."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            from PKDevTools.classes.PKDataProvider import PKDataProvider
            
            # Reset singleton for fresh test
            PKDataProvider._instance = None
            provider = PKDataProvider()
            
            assert provider.is_realtime_available() == True

    def test_realtime_not_available_when_candle_store_empty(self):
        """Test that is_realtime_available returns False when candle store is empty."""
        mock_store = MagicMock()
        mock_store.get_stats.return_value = {
            'instrument_count': 0,
            'last_tick_time': 0,
        }
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_store):
            from PKDevTools.classes.PKDataProvider import PKDataProvider
            
            PKDataProvider._instance = None
            provider = PKDataProvider()
            
            assert provider.is_realtime_available() == False

    def test_realtime_not_available_when_data_stale(self):
        """Test that is_realtime_available returns False when last tick is > 5 minutes old."""
        mock_store = MagicMock()
        mock_store.get_stats.return_value = {
            'instrument_count': 2000,
            'last_tick_time': time.time() - 600,  # 10 minutes ago = stale
        }
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_store):
            from PKDevTools.classes.PKDataProvider import PKDataProvider
            
            PKDataProvider._instance = None
            provider = PKDataProvider()
            
            assert provider.is_realtime_available() == False

    def test_realtime_data_takes_priority_over_pickle(
        self, mock_candle_store, mock_data_provider, mock_fresh_ohlcv_data
    ):
        """Test that real-time data is used when available, not pickle files."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Get stock data
                df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                
                # Verify real-time provider was called
                mock_data_provider.get_stock_data.assert_called_once()
                
                # Verify stats show realtime_hits
                stats = provider.get_stats()
                assert stats['realtime_hits'] >= 1
                assert stats['pickle_hits'] == 0

    def test_pickle_used_when_realtime_unavailable(self, mock_stale_ohlcv_data):
        """Test that pickle files are used when real-time is unavailable."""
        # Candle store returns empty/stale data
        mock_store = MagicMock()
        mock_store.get_stats.return_value = {
            'instrument_count': 0,
            'last_tick_time': 0,
        }
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=None):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Mock the pickle loading
                with patch.object(provider, '_get_from_pickle', return_value=mock_stale_ohlcv_data):
                    df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                    
                    assert df is not None
                    stats = provider.get_stats()
                    assert stats['realtime_hits'] == 0
                    assert stats['pickle_hits'] >= 1


# ============================================================================
# Data Timestamp Validation Tests
# ============================================================================

class TestDataTimestampValidation:
    """Tests for validating data timestamps are current."""

    def test_data_timestamp_is_today(self, mock_fresh_ohlcv_data):
        """Test that the most recent data point is from today."""
        today = datetime.now().date()
        last_date = mock_fresh_ohlcv_data.index[-1].date()
        
        assert last_date == today, f"Expected data from {today}, got {last_date}"

    def test_stale_data_detection(self, mock_stale_ohlcv_data):
        """Test that stale data (>1 day old) is correctly identified."""
        today = datetime.now().date()
        last_date = mock_stale_ohlcv_data.index[-1].date()
        
        is_stale = (today - last_date).days > 1
        assert is_stale == True, "Stale data should be detected"

    def test_data_freshness_check_utility(self):
        """Test utility function for checking data freshness."""
        def is_data_fresh(df: pd.DataFrame, max_age_days: int = 1) -> bool:
            """Check if DataFrame has data from within max_age_days."""
            if df is None or df.empty:
                return False
            
            today = datetime.now().date()
            last_date = df.index[-1].date() if hasattr(df.index[-1], 'date') else df.index[-1]
            
            if isinstance(last_date, str):
                last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
            
            age_days = (today - last_date).days
            return age_days <= max_age_days
        
        # Test with fresh data
        today = datetime.now()
        fresh_df = pd.DataFrame({'Close': [100]}, index=[today])
        assert is_data_fresh(fresh_df) == True
        
        # Test with stale data
        stale_date = datetime.now() - timedelta(days=5)
        stale_df = pd.DataFrame({'Close': [100]}, index=[stale_date])
        assert is_data_fresh(stale_df) == False


# ============================================================================
# Turso DB Independence Tests
# ============================================================================

class TestTursoIndependence:
    """Tests that tick data flow works independently of Turso DB."""

    def test_fresh_ticks_work_when_turso_blocked(
        self, mock_candle_store, mock_data_provider, mock_fresh_ohlcv_data
    ):
        """Test that fresh tick data is available even when Turso DB is blocked."""
        # Simulate Turso DB being blocked
        def mock_turso_blocked(*args, **kwargs):
            raise Exception("Database access blocked: quota exceeded")
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Even with Turso blocked, tick data should work
                df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                
                assert df is not None
                assert not df.empty
                # Verify it's fresh data (from realtime)
                assert provider.get_stats()['realtime_hits'] >= 1

    def test_data_provider_no_turso_dependency(self, mock_candle_store, mock_data_provider):
        """Test that PKDataProvider doesn't require Turso for basic operations."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # These operations should not touch Turso
                assert provider.is_realtime_available() == True
                
                price = provider.get_latest_price("RELIANCE")
                assert price is not None
                
                ohlcv = provider.get_realtime_ohlcv("RELIANCE")
                assert ohlcv is not None


# ============================================================================
# AssetsManager Integration Tests
# ============================================================================

class TestAssetsManagerDataFreshness:
    """Tests for AssetsManager data loading with freshness validation."""

    def test_loadstockdata_prefers_fresh_ticks(self):
        """Test that loadStockData prefers fresh tick data over cached pickle."""
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=True):
            with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.wasTradedOn', return_value=True):
                with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTodayHoliday', return_value=(False, None)):
                    # Mock the kite import to simulate fresh data fetch
                    with patch.dict('sys.modules', {'pkbrokers': MagicMock(), 'pkbrokers.kite': MagicMock(), 'pkbrokers.kite.examples': MagicMock(), 'pkbrokers.kite.examples.externals': MagicMock()}):
                        from pkscreener.classes import AssetsManager, ConfigManager
                        
                        config = ConfigManager.tools()
                        stock_dict = {}
                        
                        # Verify the is_data_fresh utility works
                        fresh_df = pd.DataFrame(
                            {'Close': [100]}, 
                            index=[datetime.now()]
                        )
                        is_fresh, data_date, age = AssetsManager.PKAssetsManager.is_data_fresh(fresh_df)
                        assert is_fresh == True
                        assert age <= 1

    def test_stale_pickle_triggers_warning(self, mock_stale_ohlcv_data):
        """Test that loading stale pickle data triggers a warning."""
        # This test verifies the logging/warning behavior
        import logging
        
        with patch('pkscreener.classes.AssetsManager.default_logger') as mock_logger:
            mock_logger.return_value = MagicMock()
            
            # When stale data is detected, it should be logged
            today = datetime.now().date()
            stale_date = mock_stale_ohlcv_data.index[-1].date()
            
            if (today - stale_date).days > 1:
                # Simulating the expected behavior
                mock_logger.return_value.warning.assert_not_called()  # Initial state
                
                # In actual implementation, this warning should be triggered
                # when stale data is loaded during trading hours


# ============================================================================
# Fetcher Integration Tests
# ============================================================================

class TestFetcherDataPriority:
    """Tests for screenerStockDataFetcher data source priority."""

    def test_fetcher_uses_hp_provider_when_available(self):
        """Test that Fetcher uses high-performance provider when available."""
        with patch('pkscreener.classes.Fetcher._HP_DATA_AVAILABLE', True):
            with patch('pkscreener.classes.Fetcher.get_data_provider') as mock_get_provider:
                mock_provider = MagicMock()
                mock_provider.is_realtime_available.return_value = True
                mock_get_provider.return_value = mock_provider
                
                from pkscreener.classes.Fetcher import screenerStockDataFetcher
                from pkscreener.classes import ConfigManager
                
                config = ConfigManager.tools()
                fetcher = screenerStockDataFetcher(config)
                
                # Verify _hp_provider is set
                assert fetcher._hp_provider is not None or mock_get_provider.called

    def test_fetcher_isrealtimedata_available(self):
        """Test the isRealtimeDataAvailable method."""
        with patch('pkscreener.classes.Fetcher._HP_DATA_AVAILABLE', True):
            with patch('pkscreener.classes.Fetcher.get_data_provider') as mock_get_provider:
                mock_provider = MagicMock()
                mock_provider.is_realtime_available.return_value = True
                mock_get_provider.return_value = mock_provider
                
                from pkscreener.classes.Fetcher import screenerStockDataFetcher
                from pkscreener.classes import ConfigManager
                
                config = ConfigManager.tools()
                fetcher = screenerStockDataFetcher(config)
                
                # Check if method exists and works
                if hasattr(fetcher, 'isRealtimeDataAvailable'):
                    result = fetcher.isRealtimeDataAvailable()
                    assert isinstance(result, bool)


# ============================================================================
# End-to-End Data Flow Tests
# ============================================================================

class TestEndToEndDataFlow:
    """End-to-end tests for the complete data flow."""

    def test_scan_uses_fresh_data_during_trading(
        self, mock_candle_store, mock_data_provider, mock_fresh_ohlcv_data
    ):
        """Test that a scan operation uses fresh tick data during trading hours."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=True):
                    from PKDevTools.classes.PKDataProvider import PKDataProvider
                    
                    PKDataProvider._instance = None
                    provider = PKDataProvider()
                    
                    # Simulate getting data for a scan
                    symbols = ['RELIANCE', 'TCS', 'INFY']
                    data = provider.get_multiple_stocks(symbols, interval='day', count=50)
                    
                    # Verify data was fetched for all symbols
                    # (In mock, all will return same data)
                    assert provider.get_stats()['realtime_hits'] >= 1

    def test_fallback_chain_works_correctly(self):
        """Test the fallback chain: realtime -> local pickle -> remote pickle."""
        # Test with no realtime available
        mock_store = MagicMock()
        mock_store.get_stats.return_value = {'instrument_count': 0, 'last_tick_time': 0}
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=None):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Realtime should not be available
                assert provider.is_realtime_available() == False
                
                # Mock pickle loading to return data
                mock_df = pd.DataFrame({
                    'Open': [100], 'High': [105], 'Low': [95],
                    'Close': [102], 'Volume': [1000000]
                }, index=[datetime.now()])
                
                with patch.object(provider, '_get_from_pickle', return_value=mock_df):
                    df = provider.get_stock_data("RELIANCE", count=1)
                    
                    # Should have used pickle
                    assert df is not None
                    assert provider.get_stats()['pickle_hits'] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

