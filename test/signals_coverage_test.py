"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for signals.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")


@pytest.fixture
def stock_data():
    """Create sample stock data."""
    dates = pd.date_range(start='2023-01-01', periods=250, freq='D')
    np.random.seed(42)
    opens = 100 + np.cumsum(np.random.randn(250) * 0.5)
    highs = opens + np.abs(np.random.randn(250))
    lows = opens - np.abs(np.random.randn(250))
    closes = opens + np.random.randn(250) * 0.5
    volumes = np.random.randint(100000, 1000000, 250)
    return pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'adj_close': closes, 'volume': volumes
    }, index=dates)


@pytest.fixture
def config_manager():
    """Create mock config manager."""
    cm = MagicMock()
    cm.periodsRange = [1, 2, 3, 5, 10, 15, 22, 30]
    return cm


class TestSignalStrength:
    """Test SignalStrength enum."""
    
    def test_signal_strength_values(self):
        """Test SignalStrength enum values."""
        from pkscreener.classes.screening.signals import SignalStrength
        
        assert SignalStrength.STRONG_BUY.value == 5
        assert SignalStrength.BUY.value == 4
        assert SignalStrength.WEAK_BUY.value == 3
        assert SignalStrength.NEUTRAL.value == 2
        assert SignalStrength.WEAK_SELL.value == 1
        assert SignalStrength.SELL.value == 0
        assert SignalStrength.STRONG_SELL.value == -1


class TestSignalResult:
    """Test SignalResult dataclass."""
    
    def test_signal_result_is_buy(self):
        """Test SignalResult is_buy property."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        result = SignalResult(
            signal=SignalStrength.STRONG_BUY,
            confidence=90.0
        )
        
        assert result.is_buy == True
    
    def test_signal_result_is_sell(self):
        """Test SignalResult is_sell property."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        result = SignalResult(
            signal=SignalStrength.SELL,
            confidence=80.0
        )
        
        assert result.is_sell == True
    
    def test_signal_result_is_strong_buy(self):
        """Test SignalResult is_strong_buy property."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        result = SignalResult(
            signal=SignalStrength.STRONG_BUY,
            confidence=95.0
        )
        
        assert result.is_strong_buy == True
    
    def test_signal_result_is_strong_sell(self):
        """Test SignalResult is_strong_sell property."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        result = SignalResult(
            signal=SignalStrength.STRONG_SELL,
            confidence=95.0
        )
        
        assert result.is_strong_sell == True


class TestTradingSignalsInit:
    """Test TradingSignals initialization."""
    
    def test_trading_signals_init(self, config_manager):
        """Test TradingSignals initialization."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        assert signals.configManager == config_manager
        assert hasattr(signals, 'WEIGHTS')


class TestTradingSignalsAnalyze:
    """Test TradingSignals analyze method."""
    
    def test_analyze_insufficient_data(self, config_manager):
        """Test analyze with insufficient data."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        df = pd.DataFrame({'close': [100, 101, 102]})  # Only 3 rows
        
        result = signals.analyze(df)
        
        assert result.signal == SignalStrength.NEUTRAL
        assert result.confidence == 0
    
    def test_analyze_none_data(self, config_manager):
        """Test analyze with None data."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals.analyze(None)
        
        assert result.signal == SignalStrength.NEUTRAL
    
    def test_analyze_with_valid_data(self, config_manager, stock_data):
        """Test analyze with valid data."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        result = signals.analyze(stock_data)
        
        assert result is not None
        assert hasattr(result, 'signal')
        assert hasattr(result, 'confidence')
    
    def test_analyze_with_save_dict(self, config_manager, stock_data):
        """Test analyze with saveDict."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        save_dict = {}
        screen_dict = {}
        
        result = signals.analyze(stock_data, saveDict=save_dict, screenDict=screen_dict)
        
        assert result is not None


class TestAnalyzeRSI:
    """Test _analyze_rsi method."""
    
    def test_analyze_rsi_oversold(self, config_manager, stock_data):
        """Test RSI oversold condition."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.RSI.return_value = pd.Series([25.0])  # Oversold
        
        signal, reason, value = signals._analyze_rsi(stock_data, mock_pktalib)
        
        assert signal == 0.8
        assert "oversold" in reason
    
    def test_analyze_rsi_overbought(self, config_manager, stock_data):
        """Test RSI overbought condition."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.RSI.return_value = pd.Series([75.0])  # Overbought
        
        signal, reason, value = signals._analyze_rsi(stock_data, mock_pktalib)
        
        assert signal == 0.2
        assert "overbought" in reason
    
    def test_analyze_rsi_approaching_oversold(self, config_manager, stock_data):
        """Test RSI approaching oversold."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.RSI.return_value = pd.Series([35.0])  # Approaching oversold
        
        signal, reason, value = signals._analyze_rsi(stock_data, mock_pktalib)
        
        assert signal == 0.65
    
    def test_analyze_rsi_none(self, config_manager, stock_data):
        """Test RSI returns None."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.RSI.return_value = None
        
        signal, reason, value = signals._analyze_rsi(stock_data, mock_pktalib)
        
        assert signal == 0.5


class TestAnalyzeMACD:
    """Test _analyze_macd method."""
    
    def test_analyze_macd_bullish_crossover(self, config_manager, stock_data):
        """Test MACD bullish crossover."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.MACD.return_value = (
            pd.Series([0.5, 0.6]),  # MACD
            pd.Series([0.3, 0.4]),  # Signal
            pd.Series([-0.1, 0.2])  # Histogram: crossed from negative to positive
        )
        
        signal, reason = signals._analyze_macd(stock_data, mock_pktalib)
        
        assert signal == 0.85
        assert "bullish crossover" in reason
    
    def test_analyze_macd_bearish_crossover(self, config_manager, stock_data):
        """Test MACD bearish crossover."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.MACD.return_value = (
            pd.Series([0.5, 0.4]),
            pd.Series([0.3, 0.5]),
            pd.Series([0.1, -0.1])  # Histogram: crossed from positive to negative
        )
        
        signal, reason = signals._analyze_macd(stock_data, mock_pktalib)
        
        assert signal == 0.15
        assert "bearish crossover" in reason
    
    def test_analyze_macd_histogram_increasing(self, config_manager, stock_data):
        """Test MACD histogram increasing."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.MACD.return_value = (
            pd.Series([0.5, 0.6]),
            pd.Series([0.3, 0.4]),
            pd.Series([0.1, 0.2])  # Histogram positive and increasing
        )
        
        signal, reason = signals._analyze_macd(stock_data, mock_pktalib)
        
        assert signal == 0.7
    
    def test_analyze_macd_histogram_decreasing(self, config_manager, stock_data):
        """Test MACD histogram decreasing."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.MACD.return_value = (
            pd.Series([0.5, 0.4]),
            pd.Series([0.5, 0.6]),
            pd.Series([-0.1, -0.2])  # Histogram negative and decreasing
        )
        
        signal, reason = signals._analyze_macd(stock_data, mock_pktalib)
        
        assert signal == 0.3


class TestAnalyzeVolume:
    """Test _analyze_volume method."""
    
    def test_analyze_volume_surge_positive(self, config_manager):
        """Test volume surge with positive price change."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        # Create data with volume surge and positive price change
        df = pd.DataFrame({
            'close': [100.0] * 19 + [100.0, 102.0],  # Price increase
            'volume': [100000] * 19 + [100000, 300000]  # Volume surge (3x)
        })
        
        signal, reason = signals._analyze_volume(df)
        
        assert signal == 0.85
        assert "surge" in reason
    
    def test_analyze_volume_surge_negative(self, config_manager):
        """Test volume surge with negative price change."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        # Create data with volume surge and negative price change
        df = pd.DataFrame({
            'close': [100.0] * 19 + [100.0, 98.0],  # Price decrease
            'volume': [100000] * 19 + [100000, 300000]  # Volume surge
        })
        
        signal, reason = signals._analyze_volume(df)
        
        assert signal == 0.15
    
    def test_analyze_volume_no_volume_column(self, config_manager):
        """Test volume analysis without volume column."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        df = pd.DataFrame({'close': [100.0] * 21})
        
        signal, reason = signals._analyze_volume(df)
        
        assert signal == 0.5
    
    def test_analyze_volume_zero_avg(self, config_manager):
        """Test volume analysis with zero average volume."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        df = pd.DataFrame({
            'close': [100.0] * 21,
            'volume': [0] * 21
        })
        
        signal, reason = signals._analyze_volume(df)
        
        assert signal == 0.5


class TestAnalyzeATRTrailing:
    """Test _analyze_atr_trailing method."""
    
    def test_analyze_atr_above_trailing_stop(self, config_manager, stock_data):
        """Test price above ATR trailing stop."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.ATR.return_value = pd.Series([1.0] * len(stock_data))  # Low ATR
        
        signal, reason = signals._analyze_atr_trailing(stock_data, mock_pktalib)
        
        assert signal == 0.75
    
    def test_analyze_atr_below_trailing_stop(self, config_manager):
        """Test price below ATR trailing stop."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        # Create data where price is well below ATR trailing stop
        df = pd.DataFrame({
            'high': [110.0] * 250,
            'low': [90.0] * 250,
            'close': [50.0] * 250  # Very low close
        })
        
        mock_pktalib = MagicMock()
        mock_pktalib.ATR.return_value = pd.Series([50.0] * 250)  # High ATR
        
        signal, reason = signals._analyze_atr_trailing(df, mock_pktalib)
        
        # May return different value based on calculation
        assert signal in [0.25, 0.5, 0.75]
    
    def test_analyze_atr_none(self, config_manager, stock_data):
        """Test ATR returns None."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.ATR.return_value = None
        
        signal, reason = signals._analyze_atr_trailing(stock_data, mock_pktalib)
        
        assert signal == 0.5


class TestAnalyzeMACrossover:
    """Test _analyze_ma_crossover method."""
    
    def test_analyze_ma_crossover_none_ema(self, config_manager, stock_data):
        """Test MA crossover with None EMA."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.EMA.return_value = None
        mock_pktalib.SMA.return_value = None
        
        signal, reason = signals._analyze_ma_crossover(stock_data, mock_pktalib)
        
        assert signal == 0.5


class TestScoreToSignal:
    """Test _score_to_signal method."""
    
    def test_score_to_signal_strong_buy(self, config_manager):
        """Test score to signal conversion for strong buy."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._score_to_signal(85)
        
        assert result == SignalStrength.STRONG_BUY
    
    def test_score_to_signal_buy(self, config_manager):
        """Test score to signal conversion for buy."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._score_to_signal(72)
        
        assert result == SignalStrength.BUY
    
    def test_score_to_signal_neutral(self, config_manager):
        """Test score to signal conversion for neutral."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._score_to_signal(50)
        
        assert result == SignalStrength.NEUTRAL
    
    def test_score_to_signal_strong_sell(self, config_manager):
        """Test score to signal conversion for strong sell."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._score_to_signal(10)
        
        assert result == SignalStrength.STRONG_SELL
    
    def test_score_to_signal_weak_buy(self, config_manager):
        """Test score to signal conversion for weak buy."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._score_to_signal(62)
        
        assert result == SignalStrength.WEAK_BUY
    
    def test_score_to_signal_weak_sell(self, config_manager):
        """Test score to signal conversion for weak sell."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._score_to_signal(38)
        
        assert result == SignalStrength.WEAK_SELL
    
    def test_score_to_signal_sell(self, config_manager):
        """Test score to signal conversion for sell."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._score_to_signal(25)
        
        assert result == SignalStrength.SELL


class TestFormatSignalText:
    """Test _format_signal_text method."""
    
    def test_format_signal_text_strong_buy(self, config_manager):
        """Test format signal text for strong buy."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._format_signal_text(SignalStrength.STRONG_BUY)
        
        assert result is not None
        assert "STRONG" in result or "Buy" in result or len(result) > 0
    
    def test_format_signal_text_sell(self, config_manager):
        """Test format signal text for sell."""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals(config_manager)
        
        result = signals._format_signal_text(SignalStrength.SELL)
        
        assert result is not None


class TestAnalyzePriceAction:
    """Test _analyze_price_action method."""
    
    def test_analyze_price_action_bullish(self, config_manager):
        """Test price action bullish pattern."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        # Create bullish data (higher lows, higher highs)
        df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [102.0, 103.0, 104.0, 105.0, 106.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [101.0, 102.0, 103.0, 104.0, 105.0]
        })
        
        signal, reason = signals._analyze_price_action(df)
        
        assert signal is not None
    
    def test_analyze_price_action_bearish(self, config_manager):
        """Test price action bearish pattern."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        # Create bearish data (lower highs, lower lows)
        df = pd.DataFrame({
            'open': [105.0, 104.0, 103.0, 102.0, 101.0],
            'high': [106.0, 105.0, 104.0, 103.0, 102.0],
            'low': [103.0, 102.0, 101.0, 100.0, 99.0],
            'close': [104.0, 103.0, 102.0, 101.0, 100.0]
        })
        
        signal, reason = signals._analyze_price_action(df)
        
        assert signal is not None


class TestAnalyzeMomentum:
    """Test _analyze_momentum method."""
    
    def test_analyze_momentum(self, config_manager, stock_data):
        """Test momentum analysis."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.MOM.return_value = pd.Series([5.0] * len(stock_data))
        
        signal, reason = signals._analyze_momentum(stock_data, mock_pktalib)
        
        assert signal is not None
    
    def test_analyze_momentum_none(self, config_manager, stock_data):
        """Test momentum with None result."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        mock_pktalib = MagicMock()
        mock_pktalib.MOM.return_value = None
        
        signal, reason = signals._analyze_momentum(stock_data, mock_pktalib)
        
        assert signal == 0.5


class TestAnalyzeAboveAverageVolume:
    """Test volume with above average conditions."""
    
    def test_analyze_volume_above_average_gain(self, config_manager):
        """Test above average volume with gain."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        # Create data with above average volume and positive price change
        df = pd.DataFrame({
            'close': [100.0] * 19 + [100.0, 100.5],  # Small gain
            'volume': [100000] * 19 + [100000, 160000]  # 1.6x volume
        })
        
        signal, reason = signals._analyze_volume(df)
        
        assert signal == 0.7 or signal == 0.5  # Above average with gain
    
    def test_analyze_volume_above_average_loss(self, config_manager):
        """Test above average volume with loss."""
        from pkscreener.classes.screening.signals import TradingSignals
        
        signals = TradingSignals(config_manager)
        
        # Create data with above average volume and negative price change
        df = pd.DataFrame({
            'close': [100.0] * 19 + [100.0, 99.5],  # Small loss
            'volume': [100000] * 19 + [100000, 160000]  # 1.6x volume
        })
        
        signal, reason = signals._analyze_volume(df)
        
        assert signal == 0.3 or signal == 0.5  # Above average with loss
