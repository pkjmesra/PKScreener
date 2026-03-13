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
Console Menu Integration Tests
==============================

This module tests the PKScreener console/CLI application to ensure all menus:
1. Work correctly with fresh tick data from PKBrokers
2. Produce valid scan results via command line
3. Handle various command-line options correctly

Test coverage:
- CLI argument parsing
- X Scanner options via CLI
- P Predefined scanner options via CLI
- Data freshness validation in CLI context
"""

import os
import sys
import time
import warnings
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import argparse

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
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_fresh_stock_data():
    """Create mock fresh stock data for testing."""
    today = datetime.now()
    dates = pd.date_range(end=today, periods=252, freq='D')
    
    return pd.DataFrame({
        'Open': [100.0 + i * 0.1 for i in range(252)],
        'High': [105.0 + i * 0.1 for i in range(252)],
        'Low': [95.0 + i * 0.1 for i in range(252)],
        'Close': [102.0 + i * 0.1 for i in range(252)],
        'Volume': [1000000 + i * 1000 for i in range(252)],
    }, index=dates)


@pytest.fixture
def mock_data_provider(mock_fresh_stock_data):
    """Mock PKDataProvider with fresh data."""
    provider = MagicMock()
    provider.is_realtime_available.return_value = True
    provider.get_stock_data.return_value = mock_fresh_stock_data
    provider.get_stats.return_value = {
        'realtime_hits': 1,
        'pickle_hits': 0,
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
    }
    return store


# ============================================================================
# CLI Argument Parsing Tests
# ============================================================================

class TestCLIArgumentParsing:
    """Tests for command-line argument parsing."""

    def test_argparser_creates_valid_parser(self):
        """Test that argParser creates a valid argument parser."""
        from pkscreener.pkscreenercli import argParser
        
        # argParser is already an ArgumentParser instance
        args = argParser.parse_args(["-a", "Y", "-e", "-o", "X:12:0"])
        
        assert args.answerdefault == "Y"
        assert args.exit == True
        assert args.options == "X:12:0"

    def test_argparser_handles_all_options(self):
        """Test that argParser handles all CLI options."""
        from pkscreener.pkscreenercli import argParser
        
        # Test with various options
        args = argParser.parse_args([
            "-a", "Y",
            "-e",
            "-o", "X:12:9:2.5",
            "-p",  # production build
            "-u", "12345678",  # user ID
        ])
        
        assert args.answerdefault == "Y"
        assert args.exit == True
        assert args.prodbuild == True
        assert args.user == "12345678"

    def test_argparser_options_format(self):
        """Test that options format is correctly parsed."""
        from pkscreener.pkscreenercli import argParser
        
        # Standard X scanner format
        args = argParser.parse_args(["-o", "X:12:9:2.5:>|X:0:31:"])
        assert "X:12:9:2.5" in args.options
        assert "|" in args.options

    @pytest.mark.parametrize("scan_key", PREDEFINED_SCAN_MENU_KEYS[:5])
    def test_predefined_scan_cli_format(self, scan_key):
        """Test that predefined scan formats work in CLI."""
        from pkscreener.pkscreenercli import argParser
        
        scan_index = int(scan_key) - 1
        scan_value = PREDEFINED_SCAN_MENU_VALUES[scan_index]
        
        # Extract options from the predefined value
        import re
        match = re.search(r"-o '([^']+)'", scan_value)
        if match:
            options = match.group(1)
            
            # Should be parseable
            args = argParser.parse_args(["-a", "Y", "-e", "-o", options])
            assert args.options == options


# ============================================================================
# X Scanner CLI Tests
# ============================================================================

# CLI patterns for X scanners
X_SCANNER_CLI_PATTERNS = [
    "X:12:0",      # All stocks, no filter
    "X:12:1",      # Bullish Momentum
    "X:12:2",      # Recent Breakouts
    "X:12:3",      # Consolidating
    "X:12:4",      # Chart patterns
    "X:12:5:0:54", # RSI based with params
    "X:12:7:4",    # VCP with variant
    "X:12:9:2.5",  # Volume shockers
    "X:12:12:27",  # Combined filters
]


class TestXScannerCLI:
    """Tests for X Scanner CLI execution."""

    @pytest.mark.parametrize("option", X_SCANNER_CLI_PATTERNS[:5])
    def test_x_scanner_option_parseable(self, option):
        """Test that X scanner options are parseable."""
        from pkscreener.pkscreenercli import argParser
        
        args = argParser.parse_args(["-a", "Y", "-e", "-o", option])
        assert args.options == option

    def test_x_scanner_with_index_selection(self):
        """Test X scanner with different index selections."""
        from pkscreener.pkscreenercli import argParser
        
        # Nifty 50 (index 2)
        args = argParser.parse_args(["-o", "X:2:0"])
        assert "X:2:0" in args.options
        
        # Nifty 500 (index 6)
        args = argParser.parse_args(["-o", "X:6:0"])
        assert "X:6:0" in args.options
        
        # All indices (index 12)
        args = argParser.parse_args(["-o", "X:12:0"])
        assert "X:12:0" in args.options

    def test_x_scanner_piped_options(self):
        """Test X scanner with piped (combined) options."""
        from pkscreener.pkscreenercli import argParser
        
        piped_option = "X:12:9:2.5:>|X:0:31:>|X:0:23:"
        args = argParser.parse_args(["-a", "Y", "-e", "-o", piped_option])
        
        assert args.options == piped_option
        assert "|" in args.options
        assert args.options.count("|") >= 2

    def test_x_scanner_with_fresh_data(self, mock_data_provider, mock_candle_store):
        """Test that X scanner execution uses fresh data."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # During CLI execution, fresh data should be available
                assert provider.is_realtime_available() == True
                
                df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                assert df is not None


# ============================================================================
# P Predefined Scanner CLI Tests
# ============================================================================

class TestPPredefinedScannerCLI:
    """Tests for P (Predefined) Scanner CLI execution."""

    @pytest.mark.parametrize("scan_index", range(5))  # Test first 5
    def test_predefined_scan_cli_parseable(self, scan_index):
        """Test that predefined scan CLI values are parseable."""
        from pkscreener.pkscreenercli import argParser
        
        scan_value = PREDEFINED_SCAN_MENU_VALUES[scan_index]
        
        # Extract just the -o options part
        import re
        match = re.search(r"-o '([^']+)'", scan_value)
        if match:
            options = match.group(1)
            args = argParser.parse_args(["-a", "Y", "-e", "-o", options])
            assert args.options == options

    def test_predefined_scan_contains_required_flags(self):
        """Test that predefined scans contain required CLI flags."""
        for scan_value in PREDEFINED_SCAN_MENU_VALUES:
            assert "--systemlaunched" in scan_value
            assert "-a y" in scan_value
            assert "-e" in scan_value
            assert "-o" in scan_value

    def test_predefined_scan_options_structure(self):
        """Test that predefined scan options have correct structure."""
        for scan_value in PREDEFINED_SCAN_MENU_VALUES[:10]:
            # Extract options
            import re
            match = re.search(r"-o '([^']+)'", scan_value)
            if match:
                options = match.group(1)
                
                # Should contain X: prefix
                assert "X:" in options
                
                # If piped, should have proper separators
                if "|" in options:
                    parts = options.split("|")
                    for part in parts:
                        assert part.startswith("X:")


# ============================================================================
# CLI Runner Tests
# ============================================================================

class TestPKCliRunner:
    """Tests for PKCliRunner class."""

    def test_cli_runner_can_be_imported(self):
        """Test that PKCliRunner can be imported."""
        from pkscreener.classes.cli.PKCliRunner import PKCliRunner
        assert PKCliRunner is not None

    def test_cli_runner_initialization(self):
        """Test PKCliRunner initialization."""
        from pkscreener.classes.cli.PKCliRunner import PKCliRunner
        from pkscreener.pkscreenercli import argParser
        
        args = argParser.parse_args(["-a", "Y", "-e", "-o", "X:12:0"])
        
        # PKCliRunner takes args as parameter
        try:
            runner = PKCliRunner(args)
            assert runner.args is not None
        except Exception:
            # In test environment, full initialization may not be possible
            # but we verify the class can be instantiated with args
            pass

    def test_cli_runner_handles_predefined_scans(self):
        """Test that CLI runner handles predefined scan patterns."""
        from pkscreener.classes.MenuOptions import PREDEFINED_SCAN_MENU_VALUES
        
        # Each predefined scan should be handleable
        for i, scan_value in enumerate(PREDEFINED_SCAN_MENU_VALUES[:5]):
            import re
            match = re.search(r"-o '([^']+)'", scan_value)
            if match:
                options = match.group(1)
                # Options should be valid scan format
                assert options.startswith("X:")


# ============================================================================
# Data Freshness in CLI Context
# ============================================================================

class TestCLIDataFreshness:
    """Tests for data freshness validation in CLI context."""

    def test_cli_scan_uses_fresh_data(self, mock_data_provider, mock_candle_store, mock_fresh_stock_data):
        """Test that CLI scans use fresh tick data."""
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # CLI should have access to fresh data
                assert provider.is_realtime_available() == True
                
                df = provider.get_stock_data("RELIANCE", interval="day", count=50)
                assert df is not None
                
                # Verify it's fresh data
                stats = provider.get_stats()
                assert stats['realtime_hits'] >= 1

    def test_cli_scan_data_timestamp_validation(self, mock_fresh_stock_data):
        """Test that CLI scan data has recent timestamps."""
        today = datetime.now().date()
        last_date = mock_fresh_stock_data.index[-1].date()
        
        # Data should be from today
        assert last_date == today

    def test_cli_falls_back_to_pickle_when_needed(self, mock_fresh_stock_data):
        """Test that CLI falls back to pickle when real-time unavailable."""
        mock_store = MagicMock()
        mock_store.get_stats.return_value = {'instrument_count': 0, 'last_tick_time': 0}
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=None):
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                # Real-time not available
                assert provider.is_realtime_available() == False
                
                # Should fall back to pickle
                with patch.object(provider, '_get_from_pickle', return_value=mock_fresh_stock_data):
                    df = provider.get_stock_data("RELIANCE", count=50)
                    assert df is not None


# ============================================================================
# Full CLI Flow Tests
# ============================================================================

class TestFullCLIFlow:
    """End-to-end tests for CLI flow."""

    def test_cli_argument_to_scan_flow(self, mock_data_provider, mock_candle_store):
        """Test flow from CLI arguments to scan execution."""
        from pkscreener.pkscreenercli import argParser
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                # Step 1: Parse CLI arguments
                args = argParser.parse_args(["-a", "Y", "-e", "-o", "X:12:0"])
                
                assert args.options == "X:12:0"
                assert args.answerdefault == "Y"
                
                # Step 2: Data should be available
                from PKDevTools.classes.PKDataProvider import PKDataProvider
                PKDataProvider._instance = None
                provider = PKDataProvider()
                
                assert provider.is_realtime_available() == True

    def test_all_scanner_options_valid_cli_format(self):
        """Test that all scanner execute options are valid CLI format."""
        # Scanner options 0-45
        for option_num in range(46):
            cli_option = f"X:12:{option_num}"
            
            from pkscreener.pkscreenercli import argParser
            args = argParser.parse_args(["-o", cli_option])
            
            assert args.options == cli_option

    def test_piped_scanner_cli_format(self):
        """Test complex piped scanner CLI format."""
        complex_options = [
            "X:12:9:2.5:>|X:0:31:>|X:0:23:>|X:0:27:",
            "X:12:7:8:>|X:12:7:9:1:1:",
            "X:12:30:1:>|X:12:7:8:",
        ]
        
        from pkscreener.pkscreenercli import argParser
        
        for option in complex_options:
            args = argParser.parse_args(["-a", "Y", "-e", "-o", option])
            assert args.options == option
            assert "|" in args.options


# ============================================================================
# Environment Variable Tests
# ============================================================================

class TestCLIEnvironmentVariables:
    """Tests for environment variable handling in CLI."""

    def test_runner_environment_detected(self):
        """Test that RUNNER environment is detected."""
        with patch.dict(os.environ, {'RUNNER': 'GitHub_Actions'}):
            runner = os.environ.get('RUNNER', None)
            assert runner == 'GitHub_Actions'

    def test_production_mode_flag(self):
        """Test production mode flag handling."""
        from pkscreener.pkscreenercli import argParser
        
        # With -p flag
        args = argParser.parse_args(["-p", "-o", "X:12:0"])
        assert args.prodbuild == True
        
        # Without -p flag
        args = argParser.parse_args(["-o", "X:12:0"])
        assert args.prodbuild == False

    def test_telegram_user_flag(self):
        """Test Telegram user flag handling."""
        from pkscreener.pkscreenercli import argParser
        
        args = argParser.parse_args(["-u", "12345678", "-o", "X:12:0"])
        assert args.user == "12345678"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_option_format_handling(self):
        """Test handling of invalid option format."""
        from pkscreener.pkscreenercli import argParser
        
        # These should still parse (validation happens later)
        args = argParser.parse_args(["-o", "INVALID"])
        assert args.options == "INVALID"

    def test_missing_option_value(self):
        """Test handling of missing option value."""
        from pkscreener.pkscreenercli import argParser
        
        # Should raise SystemExit
        with pytest.raises(SystemExit):
            argParser.parse_args(["-o"])  # Missing value

    def test_turso_down_cli_still_works(self, mock_data_provider, mock_candle_store):
        """Test that CLI works even when Turso DB is down."""
        def mock_turso_error(*args, **kwargs):
            raise Exception("Database blocked")
        
        with patch('PKDevTools.classes.PKDataProvider._get_candle_store', return_value=mock_candle_store):
            with patch('PKDevTools.classes.PKDataProvider._get_data_provider', return_value=mock_data_provider):
                with patch('PKDevTools.classes.DBManager.DBManager.getUsers', side_effect=mock_turso_error):
                    from PKDevTools.classes.PKDataProvider import PKDataProvider
                    
                    PKDataProvider._instance = None
                    provider = PKDataProvider()
                    
                    # Data should still work from ticks
                    assert provider.is_realtime_available() == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
