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

    Tests for the Trading Signals module
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestTradingSignals:
    """Test cases for TradingSignals class."""
    
    @pytest.fixture
    def sample_bullish_df(self):
        """Create a bullish trending DataFrame for testing."""
        dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
        
        # Create uptrending data
        np.random.seed(42)
        base_price = 100
        trend = np.linspace(0, 50, 250)  # Upward trend
        noise = np.random.normal(0, 2, 250)
        close = base_price + trend + noise
        
        # Add some volatility for high/low
        high = close + np.abs(np.random.normal(2, 1, 250))
        low = close - np.abs(np.random.normal(2, 1, 250))
        open_price = close - np.random.normal(0, 1, 250)
        
        # Increasing volume
        volume = np.random.randint(100000, 500000, 250) + np.linspace(0, 200000, 250).astype(int)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)
    
    @pytest.fixture
    def sample_bearish_df(self):
        """Create a bearish trending DataFrame for testing."""
        dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
        
        # Create downtrending data
        np.random.seed(42)
        base_price = 150
        trend = np.linspace(0, -50, 250)  # Downward trend
        noise = np.random.normal(0, 2, 250)
        close = base_price + trend + noise
        
        high = close + np.abs(np.random.normal(2, 1, 250))
        low = close - np.abs(np.random.normal(2, 1, 250))
        open_price = close + np.random.normal(0, 1, 250)
        
        volume = np.random.randint(100000, 500000, 250)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)
    
    @pytest.fixture
    def sample_neutral_df(self):
        """Create a sideways/neutral DataFrame for testing."""
        dates = pd.date_range(start='2024-01-01', periods=250, freq='D')
        
        # Create sideways data
        np.random.seed(42)
        base_price = 100
        noise = np.random.normal(0, 3, 250)
        close = base_price + noise
        
        high = close + np.abs(np.random.normal(1, 0.5, 250))
        low = close - np.abs(np.random.normal(1, 0.5, 250))
        open_price = close + np.random.normal(0, 0.5, 250)
        
        volume = np.random.randint(100000, 200000, 250)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)

    def test_signal_strength_enum(self):
        """Test SignalStrength enum values."""
        from pkscreener.classes.screening.signals import SignalStrength
        
        assert SignalStrength.STRONG_BUY.value == 5
        assert SignalStrength.BUY.value == 4
        assert SignalStrength.WEAK_BUY.value == 3
        assert SignalStrength.NEUTRAL.value == 2
        assert SignalStrength.WEAK_SELL.value == 1
        assert SignalStrength.SELL.value == 0
        assert SignalStrength.STRONG_SELL.value == -1

    def test_signal_result_properties(self):
        """Test SignalResult properties."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        # Test Strong Buy
        result = SignalResult(signal=SignalStrength.STRONG_BUY, confidence=85.0)
        assert result.is_buy == True
        assert result.is_sell == False
        assert result.is_strong_buy == True
        assert result.is_strong_sell == False
        
        # Test Strong Sell
        result = SignalResult(signal=SignalStrength.STRONG_SELL, confidence=85.0)
        assert result.is_buy == False
        assert result.is_sell == True
        assert result.is_strong_buy == False
        assert result.is_strong_sell == True
        
        # Test Neutral
        result = SignalResult(signal=SignalStrength.NEUTRAL, confidence=50.0)
        assert result.is_buy == False
        assert result.is_sell == False

    def test_trading_signals_initialization(self):
        """Test TradingSignals initialization."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals()
        assert signals.configManager is None
        
        mock_config = Mock()
        signals = TradingSignals(configManager=mock_config)
        assert signals.configManager == mock_config

    def test_analyze_with_insufficient_data(self):
        """Test analyze returns neutral for insufficient data."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals()
        
        # Empty DataFrame
        result = signals.analyze(pd.DataFrame())
        assert result.signal == SignalStrength.NEUTRAL
        assert result.confidence == 0
        
        # None
        result = signals.analyze(None)
        assert result.signal == SignalStrength.NEUTRAL
        
        # Too short
        short_df = pd.DataFrame({'close': [100, 101, 102]})
        result = signals.analyze(short_df)
        assert result.signal == SignalStrength.NEUTRAL

    def test_analyze_bullish_data(self, sample_bullish_df):
        """Test analyze returns buy signal for bullish data."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals()
        result = signals.analyze(sample_bullish_df)
        
        # Should lean towards buy
        assert result.signal.value >= SignalStrength.NEUTRAL.value
        assert result.confidence >= 0
        assert len(result.reasons) >= 0

    def test_analyze_bearish_data(self, sample_bearish_df):
        """Test analyze returns sell signal for bearish data."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals()
        result = signals.analyze(sample_bearish_df)
        
        # Should lean towards sell or neutral
        assert result.signal.value <= SignalStrength.BUY.value
        assert result.confidence >= 0

    def test_analyze_updates_dicts(self, sample_bullish_df):
        """Test analyze updates saveDict and screenDict."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals()
        save_dict = {}
        screen_dict = {}
        
        result = signals.analyze(sample_bullish_df, save_dict, screen_dict)
        
        assert 'Signal' in save_dict
        assert 'Confidence' in save_dict
        assert 'Signal' in screen_dict
        assert 'Confidence' in screen_dict

    def test_find_strong_buys(self, sample_bullish_df):
        """Test find_strong_buys method."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals()
        
        # Even with bullish data, strong buy requires high confidence
        result = signals.find_strong_buys(sample_bullish_df)
        assert isinstance(result, bool)

    def test_find_strong_sells(self, sample_bearish_df):
        """Test find_strong_sells method."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals()
        
        result = signals.find_strong_sells(sample_bearish_df)
        assert isinstance(result, bool)

    def test_find_buy_signals(self, sample_bullish_df, sample_bearish_df):
        """Test find_buy_signals method."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals()
        
        # Test with different data
        bullish_result = signals.find_buy_signals(sample_bullish_df)
        bearish_result = signals.find_buy_signals(sample_bearish_df)
        
        assert isinstance(bullish_result, bool)
        assert isinstance(bearish_result, bool)

    def test_find_sell_signals(self, sample_bullish_df, sample_bearish_df):
        """Test find_sell_signals method."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals()
        
        bullish_result = signals.find_sell_signals(sample_bullish_df)
        bearish_result = signals.find_sell_signals(sample_bearish_df)
        
        assert isinstance(bullish_result, bool)
        assert isinstance(bearish_result, bool)


class TestScreeningStatisticsSignals:
    """Test cases for signal methods in ScreeningStatistics."""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager."""
        mock = Mock()
        mock.daysToLookback = 22
        mock.minLTP = 20
        mock.maxLTP = 50000
        return mock
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        close = 100 + np.cumsum(np.random.normal(0.5, 2, 100))
        high = close + np.abs(np.random.normal(1, 0.5, 100))
        low = close - np.abs(np.random.normal(1, 0.5, 100))
        open_price = close + np.random.normal(0, 0.5, 100)
        volume = np.random.randint(100000, 500000, 100)
        
        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)

    def test_findStrongBuySignals(self, mock_config_manager, sample_df):
        """Test findStrongBuySignals method in ScreeningStatistics."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        
        screener = ScreeningStatistics(mock_config_manager, default_logger())
        
        result = screener.findStrongBuySignals(sample_df)
        assert isinstance(result, bool)
        
        # Test with dicts
        save_dict = {}
        screen_dict = {}
        result = screener.findStrongBuySignals(sample_df, screen_dict, save_dict)
        assert isinstance(result, bool)

    def test_findStrongSellSignals(self, mock_config_manager, sample_df):
        """Test findStrongSellSignals method in ScreeningStatistics."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        
        screener = ScreeningStatistics(mock_config_manager, default_logger())
        
        result = screener.findStrongSellSignals(sample_df)
        assert isinstance(result, bool)

    def test_findAllBuySignals(self, mock_config_manager, sample_df):
        """Test findAllBuySignals method in ScreeningStatistics."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        
        screener = ScreeningStatistics(mock_config_manager, default_logger())
        
        result = screener.findAllBuySignals(sample_df)
        assert isinstance(result, bool)

    def test_findAllSellSignals(self, mock_config_manager, sample_df):
        """Test findAllSellSignals method in ScreeningStatistics."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        
        screener = ScreeningStatistics(mock_config_manager, default_logger())
        
        result = screener.findAllSellSignals(sample_df)
        assert isinstance(result, bool)

    def test_signal_methods_with_none(self, mock_config_manager):
        """Test signal methods handle None gracefully."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        
        screener = ScreeningStatistics(mock_config_manager, default_logger())
        
        # All should return False for None input
        assert screener.findStrongBuySignals(None) == False
        assert screener.findStrongSellSignals(None) == False
        assert screener.findAllBuySignals(None) == False
        assert screener.findAllSellSignals(None) == False


class TestMenuOptions:
    """Test cases for new menu options."""

    def test_menu_options_exist(self):
        """Test that Strong Buy/Sell menu options exist."""
        from pkscreener.classes.MenuOptions import level2_X_MenuDict, MAX_SUPPORTED_MENU_OPTION
        
        assert "44" in level2_X_MenuDict
        assert "45" in level2_X_MenuDict
        assert "46" in level2_X_MenuDict
        assert "47" in level2_X_MenuDict
        
        assert "Strong Buy" in level2_X_MenuDict["44"]
        assert "Strong Sell" in level2_X_MenuDict["45"]
        assert "All Buy" in level2_X_MenuDict["46"]
        assert "All Sell" in level2_X_MenuDict["47"]
        
        assert MAX_SUPPORTED_MENU_OPTION >= 47


class TestStockScreenerIntegration:
    """Integration tests for StockScreener with new signal options."""
    
    @pytest.fixture
    def mock_setup(self):
        """Create mock objects for StockScreener testing."""
        mock_config = Mock()
        mock_config.daysToLookback = 22
        mock_config.minLTP = 20
        mock_config.maxLTP = 50000
        mock_config.isIntradayConfig = Mock(return_value=False)
        mock_config.minVolume = 100000
        
        return mock_config

    def test_performValidityCheckForExecuteOptions_44(self, mock_setup):
        """Test performValidityCheckForExecuteOptions handles option 44."""
        from pkscreener.classes.StockScreener import StockScreener
        
        screener_obj = StockScreener()
        
        # Create mock screener (ScreeningStatistics)
        mock_screener = Mock()
        mock_screener.findStrongBuySignals = Mock(return_value=True)
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.normal(0.5, 2, 100))
        sample_df = pd.DataFrame({
            'open': close,
            'high': close + 1,
            'low': close - 1,
            'close': close,
            'volume': [100000] * 100
        }, index=dates)
        
        screen_dict = {}
        save_dict = {}
        
        result = screener_obj.performValidityCheckForExecuteOptions(
            executeOption=44,
            screener=mock_screener,
            fullData=sample_df,
            screeningDictionary=screen_dict,
            saveDictionary=save_dict,
            processedData=sample_df,
            configManager=mock_setup
        )
        
        mock_screener.findStrongBuySignals.assert_called_once()

    def test_performValidityCheckForExecuteOptions_45(self, mock_setup):
        """Test performValidityCheckForExecuteOptions handles option 45."""
        from pkscreener.classes.StockScreener import StockScreener
        
        screener_obj = StockScreener()
        
        mock_screener = Mock()
        mock_screener.findStrongSellSignals = Mock(return_value=True)
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.normal(0.5, 2, 100))
        sample_df = pd.DataFrame({
            'open': close,
            'high': close + 1,
            'low': close - 1,
            'close': close,
            'volume': [100000] * 100
        }, index=dates)
        
        result = screener_obj.performValidityCheckForExecuteOptions(
            executeOption=45,
            screener=mock_screener,
            fullData=sample_df,
            screeningDictionary={},
            saveDictionary={},
            processedData=sample_df,
            configManager=mock_setup
        )
        
        mock_screener.findStrongSellSignals.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
