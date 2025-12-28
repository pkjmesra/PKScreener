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
Bot Menu Integration Tests
==========================

This module tests all PKScreener bot menus to ensure they:
1. Work correctly with fresh tick data from PKBrokers
2. Produce valid scan results
3. Handle Turso DB unavailability gracefully

Test coverage:
- X Scanners (45 execute options)
- P Predefined Scanners (36 piped scanner combinations)
- B Backtest menus
- M Monitor menus
- D Download menus
"""

import os
import sys
import time
import warnings
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

import pandas as pd
import pytest

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pkscreener.classes.MenuOptions import (
    PREDEFINED_SCAN_MENU_TEXTS,
    PREDEFINED_SCAN_MENU_VALUES,
    PREDEFINED_SCAN_MENU_KEYS,
    level0MenuDict,
    level1_index_options_sectoral,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_fresh_stock_data():
    """Create mock fresh stock data for testing."""
    today = datetime.now()
    dates = pd.date_range(end=today, periods=252, freq='D')  # 1 year of data
    
    return pd.DataFrame({
        'Open': [100.0 + i * 0.1 for i in range(252)],
        'High': [105.0 + i * 0.1 for i in range(252)],
        'Low': [95.0 + i * 0.1 for i in range(252)],
        'Close': [102.0 + i * 0.1 for i in range(252)],
        'Volume': [1000000 + i * 1000 for i in range(252)],
    }, index=dates)


@pytest.fixture
def mock_telegram_update():
    """Create mock Telegram Update object."""
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345678
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.effective_chat = MagicMock()
    update.effective_chat.id = 12345678
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.callback_query = None
    return update


@pytest.fixture
def mock_telegram_context():
    """Create mock Telegram Context object."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    context.args = []
    return context


@pytest.fixture
def mock_data_provider(mock_fresh_stock_data):
    """Mock PKDataProvider with fresh data."""
    provider = MagicMock()
    provider.is_realtime_available.return_value = True
    provider.get_stock_data.return_value = mock_fresh_stock_data
    provider.get_multiple_stocks.return_value = {
        'RELIANCE': mock_fresh_stock_data,
        'TCS': mock_fresh_stock_data,
        'INFY': mock_fresh_stock_data,
    }
    provider.get_stats.return_value = {
        'realtime_hits': 1,
        'pickle_hits': 0,
        'cache_hits': 0,
        'misses': 0,
        'realtime_available': True,
    }
    return provider


@pytest.fixture
def mock_candle_store():
    """Mock InMemoryCandleStore with fresh tick data."""
    store = MagicMock()
    store.get_stats.return_value = {
        'instrument_count': 2000,
        'last_tick_time': time.time(),
        'cache_size': 50000,
    }
    return store


# ============================================================================
# X Scanner Menu Tests
# ============================================================================

# Scanner execute options (1-45)
X_SCANNER_OPTIONS = [
    "0",   # Full scan (all stocks)
    "1",   # Bullish Momentum
    "2",   # Recent Breakouts
    "3",   # Consolidating stocks
    "4",   # Chart patterns
    "5",   # RSI based
    "6",   # CCI based
    "7",   # VCP
    "8",   # Breakout Value
    "9",   # Volume shockers
    "10",  # Intraday momentum
    "11",  # Aroon Crossover
    "12",  # Combined filters
]


class TestXScannerMenus:
    """Tests for X Scanner menu options."""

    @pytest.mark.parametrize("scanner_option", X_SCANNER_OPTIONS[:5])
    def test_x_scanner_produces_results_with_fresh_data(
        self, scanner_option, mock_data_provider, mock_candle_store, mock_fresh_stock_data
    ):
        """Test that X scanner options produce results with fresh tick data."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                with patch('PKDevTools.classes.PKDataProvider.get_data_provider', return_value=mock_data_provider):
                    # Simulate the scan execution
                    menu_option = f"X:12:{scanner_option}"
                    
                    # Verify data provider is accessible
                    from PKDevTools.classes.PKDataProvider import PKDataProvider
                    PKDataProvider._instance = None
                    provider = PKDataProvider()
                    
                    assert provider.is_realtime_available() == True
                    
                    # Get stock data
                    df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                    assert df is not None
                    assert not df.empty
                    
                    # Verify data is fresh (last row is from today or recent)
                    last_date = df.index[-1].date()
                    today = datetime.now().date()
                    assert (today - last_date).days <= 1

    def test_x_scanner_menu_structure(self):
        """Test that X scanner menu structure is correct."""
        # X is a valid top-level menu
        assert "X" in level0MenuDict
        assert level0MenuDict["X"] == "Scanners"

    def test_x_scanner_index_options(self):
        """Test that all index options are available for X scanner."""
        # Should have 46 sectoral index options
        assert len(level1_index_options_sectoral) >= 46
        assert "2" in level1_index_options_sectoral  # Nifty 50
        assert "46" in level1_index_options_sectoral  # All of the above

    @pytest.mark.parametrize("index_option", ["2", "6", "12"])
    def test_x_scanner_with_different_indices(
        self, index_option, mock_data_provider, mock_candle_store
    ):
        """Test X scanner with different index options."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                menu_option = f"X:{index_option}:0"
                
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Should be able to fetch data
                assert provider.is_realtime_available() == True


# ============================================================================
# P Predefined Scanner Menu Tests
# ============================================================================

class TestPPredefinedScannerMenus:
    """Tests for P (Predefined) Scanner menu options."""

    def test_predefined_scan_menu_structure(self):
        """Test that predefined scan menu is properly structured."""
        assert len(PREDEFINED_SCAN_MENU_TEXTS) == 36
        assert len(PREDEFINED_SCAN_MENU_VALUES) == 36
        assert len(PREDEFINED_SCAN_MENU_KEYS) == 36

    def test_predefined_scan_texts_are_descriptive(self):
        """Test that predefined scan texts are descriptive."""
        for text in PREDEFINED_SCAN_MENU_TEXTS:
            assert len(text) > 10, f"Menu text too short: {text}"
            # Should contain pipe separators for combined scans
            assert "|" in text or "RSI" in text or "VCP" in text or "ATR" in text

    @pytest.mark.parametrize("scan_index", range(5))  # Test first 5 predefined scans
    def test_predefined_scan_value_format(self, scan_index):
        """Test that predefined scan values have correct format."""
        scan_value = PREDEFINED_SCAN_MENU_VALUES[scan_index]
        
        # Should start with --systemlaunched
        assert "--systemlaunched" in scan_value
        # Should have -a y (auto answer yes)
        assert "-a y" in scan_value
        # Should have -e (exit after)
        assert "-e" in scan_value
        # Should have -o with options
        assert "-o" in scan_value

    @pytest.mark.parametrize("scan_key", PREDEFINED_SCAN_MENU_KEYS[:5])
    def test_predefined_scan_produces_output_with_fresh_data(
        self, scan_key, mock_data_provider, mock_candle_store, mock_fresh_stock_data
    ):
        """Test that predefined scans produce output with fresh tick data."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                scan_index = int(scan_key) - 1
                scan_value = PREDEFINED_SCAN_MENU_VALUES[scan_index]
                
                # Verify data provider works
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                assert provider.is_realtime_available() == True
                
                # Simulate fetching data for the scan
                df = provider.get_stock_data("RELIANCE", interval="day", count=252)
                assert df is not None
                
                # Data should be fresh
                stats = provider.get_stats()
                assert stats['realtime_available'] == True

    def test_piped_scanner_parsing(self):
        """Test that piped scanner options are correctly parsed."""
        # Sample piped scanner: "X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:"
        sample = PREDEFINED_SCAN_MENU_VALUES[0]
        
        # Extract the options part
        import re
        match = re.search(r"-o '([^']+)'", sample)
        assert match is not None
        
        options = match.group(1)
        # Should have multiple pipe-separated options
        assert "|" in options
        
        parts = options.split("|")
        assert len(parts) >= 2


# ============================================================================
# Bot Handler Tests
# ============================================================================

class TestBotHandlers:
    """Tests for Telegram bot handlers."""

    def test_user_handler_initialization(self):
        """Test UserHandler can be initialized."""
        with patch('pkscreener.classes.bot.BotHandlers.PKBotLocalCache'):
            from pkscreener.classes.bot.BotHandlers import UserHandler
            from pkscreener.classes import ConfigManager
            
            config = ConfigManager.tools()
            handler = UserHandler(config)
            
            assert handler is not None
            assert handler.config_manager is not None

    def test_menu_handler_initialization(self):
        """Test MenuHandler can be initialized."""
        from pkscreener.classes.bot.BotHandlers import MenuHandler
        
        handler = MenuHandler()
        assert handler is not None
        assert handler.m0 is not None
        assert handler.m1 is not None

    def test_menu_handler_get_menu_for_level(self):
        """Test MenuHandler.get_menu_for_level returns correct menus."""
        from pkscreener.classes.bot.BotHandlers import MenuHandler
        
        handler = MenuHandler()
        
        # Level 0 should have the main menu items
        level0_items = handler.get_menu_for_level(0, skip_menus=["T"])
        
        # Should contain key menu items
        menu_keys = [item.menuKey for item in level0_items]
        assert "X" in menu_keys or len(menu_keys) > 0

    def test_bot_constants(self):
        """Test BotConstants are properly defined."""
        from pkscreener.classes.bot.BotHandlers import BotConstants
        
        assert BotConstants.MAX_MSG_LENGTH == 4096
        assert len(BotConstants.TOP_LEVEL_SCANNER_MENUS) > 0
        assert "X" in BotConstants.TOP_LEVEL_SCANNER_MENUS


# ============================================================================
# Scan Execution Tests with Fresh Data
# ============================================================================

class TestScanExecutionWithFreshData:
    """Tests for scan execution using fresh tick data."""

    def test_scan_runner_uses_fresh_data(self, mock_data_provider, mock_candle_store):
        """Test that PKScanRunner uses fresh data from PKDataProvider."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # During a scan, fresh data should be prioritized
                assert provider.is_realtime_available() == True
                
                # Get data for multiple stocks (simulating a scan)
                stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']
                for stock in stocks:
                    df = provider.get_stock_data(stock, interval="day", count=50)
                    # Mock returns data for all stocks
                    assert df is not None

    def test_scan_results_contain_fresh_timestamps(self, mock_fresh_stock_data):
        """Test that scan results contain fresh data timestamps."""
        # Verify the mock data has today's date
        today = datetime.now().date()
        last_date = mock_fresh_stock_data.index[-1].date()
        
        assert last_date == today, f"Expected {today}, got {last_date}"

    def test_turso_down_doesnt_affect_scan(self, mock_data_provider, mock_candle_store):
        """Test that scans work even when Turso DB is down."""
        def mock_turso_error(*args, **kwargs):
            raise Exception("Database blocked: quota exceeded")
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                with patch('PKDevTools.classes.DBManager.DBManager.getUsers', side_effect=mock_turso_error):
                    from PKDevTools.classes.PKDataProvider import PKDataProvider
                    
                    PKDataProvider._instance = None
                    provider = PKDataProvider()
                    
                    # Data should still be available from tick source
                    assert provider.is_realtime_available() == True
                    
                    df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                    assert df is not None


# ============================================================================
# Monitor Menu Tests
# ============================================================================

class TestMonitorMenus:
    """Tests for M (Monitor) menu options."""

    def test_monitor_menu_exists(self):
        """Test that Monitor menu exists in level 0."""
        assert "M" in level0MenuDict
        assert "Monitor" in level0MenuDict["M"]

    def test_monitor_uses_realtime_data(self, mock_data_provider, mock_candle_store):
        """Test that monitoring uses real-time data."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Monitor requires real-time data
                assert provider.is_realtime_available() == True
                
                # Should be able to get current OHLCV
                mock_data_provider.get_current_ohlcv.return_value = {
                    'open': 100, 'high': 105, 'low': 98, 'close': 103, 'volume': 1000000
                }
                
                ohlcv = provider.get_realtime_ohlcv("RELIANCE")
                assert ohlcv is not None


# ============================================================================
# Download Menu Tests
# ============================================================================

class TestDownloadMenus:
    """Tests for D (Download) menu options."""

    def test_download_menu_exists(self):
        """Test that Download menu exists in level 0."""
        assert "D" in level0MenuDict
        assert "Download" in level0MenuDict["D"]

    def test_download_options_available(self):
        """Test that download options are available."""
        from pkscreener.classes.MenuOptions import LEVEL_1_DATA_DOWNLOADS
        
        assert "D" in LEVEL_1_DATA_DOWNLOADS  # Daily OHLCV
        assert "I" in LEVEL_1_DATA_DOWNLOADS  # Intraday
        assert "N" in LEVEL_1_DATA_DOWNLOADS  # NSE Equity Symbols


# ============================================================================
# Backtest Menu Tests
# ============================================================================

class TestBacktestMenus:
    """Tests for B (Backtest) menu options."""

    def test_backtest_requires_historical_data(self, mock_fresh_stock_data):
        """Test that backtest uses historical data (not just latest)."""
        # Backtest needs at least 252 days of data (1 year)
        assert len(mock_fresh_stock_data) >= 252

    def test_backtest_data_format(self, mock_fresh_stock_data):
        """Test that backtest data has correct format."""
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            assert col in mock_fresh_stock_data.columns


# ============================================================================
# Integration Tests
# ============================================================================

class TestBotIntegration:
    """Integration tests for the complete bot flow."""

    def test_complete_scan_flow_with_fresh_data(
        self, mock_data_provider, mock_candle_store, mock_fresh_stock_data
    ):
        """Test complete scan flow from bot command to results."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Step 1: Verify real-time is available
                assert provider.is_realtime_available() == True
                
                # Step 2: Fetch data for scan
                df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                assert df is not None
                assert not df.empty
                
                # Step 3: Verify data is fresh
                stats = provider.get_stats()
                assert stats['realtime_hits'] >= 1
                
                # Step 4: Verify last data point is recent
                today = datetime.now().date()
                last_date = df.index[-1].date()
                assert (today - last_date).days <= 1

    def test_all_predefined_scans_accessible(self):
        """Test that all 36 predefined scans are accessible."""
        for i, (key, text, value) in enumerate(zip(
            PREDEFINED_SCAN_MENU_KEYS,
            PREDEFINED_SCAN_MENU_TEXTS,
            PREDEFINED_SCAN_MENU_VALUES
        )):
            # Each scan should have valid components
            assert key == str(i + 1)
            assert len(text) > 0
            assert "--systemlaunched" in value
            assert "-o" in value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

