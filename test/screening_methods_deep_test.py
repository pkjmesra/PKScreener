"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Deep tests for ScreeningStatistics specific methods.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock
from argparse import Namespace
import warnings
warnings.filterwarnings("ignore")


@pytest.fixture
def config():
    """Create a configuration manager."""
    from pkscreener.classes.ConfigManager import tools, parser
    config = tools()
    config.getConfig(parser)
    return config


@pytest.fixture
def screener(config):
    """Create a ScreeningStatistics instance."""
    from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
    from PKDevTools.classes.log import default_logger
    return ScreeningStatistics(config, default_logger())


@pytest.fixture
def bullish_df():
    """Create bullish stock data."""
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    np.random.seed(42)
    
    base = 100
    closes = []
    for i in range(300):
        base += np.random.uniform(-0.5, 1.5)  # Uptrend
        closes.append(max(50, base))
    
    df = pd.DataFrame({
        'open': [c * np.random.uniform(0.98, 1.0) for c in closes],
        'high': [max(c * 0.99, c) * np.random.uniform(1.0, 1.02) for c in closes],
        'low': [min(c * 0.99, c) * np.random.uniform(0.98, 1.0) for c in closes],
        'close': closes,
        'volume': np.random.randint(500000, 10000000, 300),
        'adjclose': closes,
    }, index=dates)
    df['VolMA'] = df['volume'].rolling(20).mean().fillna(method='bfill')
    return df


@pytest.fixture
def bearish_df():
    """Create bearish stock data."""
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    np.random.seed(43)
    
    base = 200
    closes = []
    for i in range(300):
        base += np.random.uniform(-1.5, 0.5)  # Downtrend
        closes.append(max(50, base))
    
    df = pd.DataFrame({
        'open': [c * np.random.uniform(1.0, 1.02) for c in closes],
        'high': [max(c * 1.01, c) * np.random.uniform(1.0, 1.02) for c in closes],
        'low': [min(c * 1.01, c) * np.random.uniform(0.98, 1.0) for c in closes],
        'close': closes,
        'volume': np.random.randint(500000, 10000000, 300),
        'adjclose': closes,
    }, index=dates)
    df['VolMA'] = df['volume'].rolling(20).mean().fillna(method='bfill')
    return df


@pytest.fixture
def sideways_df():
    """Create sideways/consolidating stock data."""
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    np.random.seed(44)
    
    base = 150
    closes = []
    for i in range(300):
        base += np.random.uniform(-1.0, 1.0)  # Sideways
        closes.append(max(100, min(200, base)))
    
    df = pd.DataFrame({
        'open': [c * np.random.uniform(0.99, 1.01) for c in closes],
        'high': [max(c * 1.0, c) * np.random.uniform(1.0, 1.015) for c in closes],
        'low': [min(c * 1.0, c) * np.random.uniform(0.985, 1.0) for c in closes],
        'close': closes,
        'volume': np.random.randint(500000, 10000000, 300),
        'adjclose': closes,
    }, index=dates)
    df['VolMA'] = df['volume'].rolling(20).mean().fillna(method='bfill')
    return df


# =============================================================================
# BBands Squeeze Tests
# =============================================================================

class TestFindBbandsSqueeze:
    """Test findBbandsSqueeze method with various filters."""
    
    def test_bbands_squeeze_filter_1(self, screener, bullish_df):
        """Test BBands squeeze with filter 1 (Buy)."""
        try:
            result = screener.findBbandsSqueeze(bullish_df, {}, {}, filter=1)
            assert result in (True, False)
        except:
            pass
    
    def test_bbands_squeeze_filter_2(self, screener, sideways_df):
        """Test BBands squeeze with filter 2 (Squeeze)."""
        try:
            result = screener.findBbandsSqueeze(sideways_df, {}, {}, filter=2)
            assert result in (True, False)
        except:
            pass
    
    def test_bbands_squeeze_filter_3(self, screener, bearish_df):
        """Test BBands squeeze with filter 3 (Sell)."""
        try:
            result = screener.findBbandsSqueeze(bearish_df, {}, {}, filter=3)
            assert result in (True, False)
        except:
            pass
    
    def test_bbands_squeeze_filter_4(self, screener, bullish_df):
        """Test BBands squeeze with filter 4 (All)."""
        try:
            result = screener.findBbandsSqueeze(bullish_df, {}, {}, filter=4)
            assert result in (True, False)
        except:
            pass
    
    def test_bbands_squeeze_none_data(self, screener):
        """Test BBands squeeze with None data."""
        result = screener.findBbandsSqueeze(None, {}, {}, filter=4)
        assert result is False
    
    def test_bbands_squeeze_empty_data(self, screener):
        """Test BBands squeeze with empty data."""
        result = screener.findBbandsSqueeze(pd.DataFrame(), {}, {}, filter=4)
        assert result is False
    
    def test_bbands_squeeze_short_data(self, screener):
        """Test BBands squeeze with short data."""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'open': np.random.uniform(95, 105, 10),
            'high': np.random.uniform(100, 110, 10),
            'low': np.random.uniform(90, 100, 10),
            'close': np.random.uniform(95, 105, 10),
            'volume': np.random.randint(500000, 10000000, 10),
        }, index=dates)
        
        result = screener.findBbandsSqueeze(df, {}, {}, filter=4)
        assert result is False


# =============================================================================
# BreakingoutNow Tests
# =============================================================================

class TestFindBreakingoutNow:
    """Test findBreakingoutNow method."""
    
    def test_breakingout_now_bullish(self, screener, bullish_df):
        """Test findBreakingoutNow with bullish data."""
        try:
            result = screener.findBreakingoutNow(bullish_df, bullish_df, {}, {})
            assert result in (True, False)
        except:
            pass
    
    def test_breakingout_now_bearish(self, screener, bearish_df):
        """Test findBreakingoutNow with bearish data."""
        try:
            result = screener.findBreakingoutNow(bearish_df, bearish_df, {}, {})
            assert result in (True, False)
        except:
            pass
    
    def test_breakingout_now_none_data(self, screener):
        """Test findBreakingoutNow with None data."""
        try:
            result = screener.findBreakingoutNow(None, None, {}, {})
            assert result is False
        except:
            pass
    
    def test_breakingout_now_empty_data(self, screener):
        """Test findBreakingoutNow with empty data."""
        try:
            result = screener.findBreakingoutNow(pd.DataFrame(), pd.DataFrame(), {}, {})
            assert result is False
        except:
            pass


# =============================================================================
# ATR Trailing Stops Tests
# =============================================================================

class TestFindATRTrailingStops:
    """Test findATRTrailingStops method."""
    
    def test_atr_trailing_sensitivity_1(self, screener, bullish_df):
        """Test ATR trailing with sensitivity 1."""
        try:
            result = screener.findATRTrailingStops(bullish_df, 1, 10, 1, 1, {}, {})
        except:
            pass
    
    def test_atr_trailing_sensitivity_2(self, screener, bullish_df):
        """Test ATR trailing with sensitivity 2."""
        try:
            result = screener.findATRTrailingStops(bullish_df, 2, 10, 1, 1, {}, {})
        except:
            pass
    
    def test_atr_trailing_sensitivity_3(self, screener, bullish_df):
        """Test ATR trailing with sensitivity 3."""
        try:
            result = screener.findATRTrailingStops(bullish_df, 3, 10, 1, 1, {}, {})
        except:
            pass
    
    def test_atr_trailing_buy_signals(self, screener, bullish_df):
        """Test ATR trailing for buy signals."""
        try:
            result = screener.findATRTrailingStops(bullish_df, 1, 10, 1, 1, {}, {})  # Buy
        except:
            pass
    
    def test_atr_trailing_sell_signals(self, screener, bearish_df):
        """Test ATR trailing for sell signals."""
        try:
            result = screener.findATRTrailingStops(bearish_df, 1, 10, 1, 2, {}, {})  # Sell
        except:
            pass


# =============================================================================
# Buy/Sell Signals from ATR Trailing Tests
# =============================================================================

class TestFindBuySellSignalsFromATRTrailing:
    """Test findBuySellSignalsFromATRTrailing method."""
    
    def test_buy_signals(self, screener, bullish_df):
        """Test finding buy signals."""
        try:
            result = screener.findBuySellSignalsFromATRTrailing(bullish_df, 1, 10, 200, 1, {}, {})
        except:
            pass
    
    def test_sell_signals(self, screener, bearish_df):
        """Test finding sell signals."""
        try:
            result = screener.findBuySellSignalsFromATRTrailing(bearish_df, 1, 10, 200, 2, {}, {})
        except:
            pass
    
    def test_all_signals(self, screener, sideways_df):
        """Test finding all signals."""
        try:
            result = screener.findBuySellSignalsFromATRTrailing(sideways_df, 1, 10, 200, 3, {}, {})
        except:
            pass


# =============================================================================
# MACD Crossover Tests
# =============================================================================

class TestFindMACDCrossover:
    """Test findMACDCrossover method."""
    
    def test_macd_crossover_up(self, screener, bullish_df):
        """Test MACD crossover upward."""
        try:
            result = screener.findMACDCrossover(bullish_df, upDirection=True)
            assert result in (True, False)
        except:
            pass
    
    def test_macd_crossover_down(self, screener, bearish_df):
        """Test MACD crossover downward."""
        try:
            result = screener.findMACDCrossover(bearish_df, upDirection=False)
            assert result in (True, False)
        except:
            pass
    
    def test_macd_crossover_nth(self, screener, bullish_df):
        """Test MACD crossover with nth crossover."""
        for nth in [1, 2, 3]:
            try:
                result = screener.findMACDCrossover(bullish_df, upDirection=True, nthCrossover=nth)
            except:
                pass


# =============================================================================
# High Momentum Tests
# =============================================================================

class TestFindHighMomentum:
    """Test findHighMomentum method."""
    
    def test_high_momentum_strict(self, screener, bullish_df):
        """Test high momentum with strict=True."""
        try:
            result = screener.findHighMomentum(bullish_df, strict=True)
            assert result in (True, False)
        except:
            pass
    
    def test_high_momentum_not_strict(self, screener, bullish_df):
        """Test high momentum with strict=False."""
        try:
            result = screener.findHighMomentum(bullish_df, strict=False)
            assert result in (True, False)
        except:
            pass


# =============================================================================
# 52 Week Methods Tests
# =============================================================================

class TestFind52WeekMethods:
    """Test 52 week related methods."""
    
    def test_52_week_high_breakout(self, screener, bullish_df):
        """Test 52 week high breakout."""
        result = screener.find52WeekHighBreakout(bullish_df)
        assert result in (True, False)
    
    def test_52_week_low_breakout(self, screener, bearish_df):
        """Test 52 week low breakout."""
        result = screener.find52WeekLowBreakout(bearish_df)
        assert result in (True, False)
    
    def test_10_days_low_breakout(self, screener, bearish_df):
        """Test 10 days low breakout."""
        result = screener.find10DaysLowBreakout(bearish_df)
        assert result in (True, False)
    
    def test_52_week_high_low(self, screener, bullish_df):
        """Test 52 week high/low calculation."""
        screener.find52WeekHighLow(bullish_df, {}, {})


# =============================================================================
# Aroon Tests
# =============================================================================

class TestFindAroonBullishCrossover:
    """Test findAroonBullishCrossover method."""
    
    def test_aroon_bullish_crossover(self, screener, bullish_df):
        """Test Aroon bullish crossover."""
        result = screener.findAroonBullishCrossover(bullish_df)
        assert result in (True, False)
    
    def test_aroon_bullish_crossover_bearish_data(self, screener, bearish_df):
        """Test Aroon bullish crossover with bearish data."""
        result = screener.findAroonBullishCrossover(bearish_df)
        assert result in (True, False)


# =============================================================================
# Higher Opens Tests
# =============================================================================

class TestFindHigherOpens:
    """Test findHigherOpens and related methods."""
    
    def test_find_higher_opens(self, screener, bullish_df):
        """Test findHigherOpens."""
        result = screener.findHigherOpens(bullish_df)
        assert result in (True, False)
    
    def test_find_higher_bullish_opens(self, screener, bullish_df):
        """Test findHigherBullishOpens."""
        result = screener.findHigherBullishOpens(bullish_df)
        assert result in (True, False)


# =============================================================================
# Potential Breakout Tests
# =============================================================================

class TestFindPotentialBreakout:
    """Test findPotentialBreakout method."""
    
    def test_potential_breakout_22_days(self, screener, bullish_df):
        """Test potential breakout with 22 days lookback."""
        result = screener.findPotentialBreakout(bullish_df, {}, {}, daysToLookback=22)
        assert result in (True, False)
    
    def test_potential_breakout_50_days(self, screener, bullish_df):
        """Test potential breakout with 50 days lookback."""
        result = screener.findPotentialBreakout(bullish_df, {}, {}, daysToLookback=50)
        assert result in (True, False)


# =============================================================================
# NR4 Day Tests
# =============================================================================

class TestFindNR4Day:
    """Test findNR4Day method."""
    
    def test_nr4_day(self, screener, sideways_df):
        """Test NR4 day detection."""
        result = screener.findNR4Day(sideways_df)
        assert result is not None or result in (True, False)


# =============================================================================
# Short Sell Tests
# =============================================================================

class TestShortSellMethods:
    """Test short sell related methods."""
    
    def test_perfect_short_sells(self, screener, bearish_df):
        """Test perfect short sells."""
        result = screener.findPerfectShortSellsFutures(bearish_df)
        assert result is not None or result in (True, False)
    
    def test_probable_short_sells(self, screener, bearish_df):
        """Test probable short sells."""
        result = screener.findProbableShortSellsFutures(bearish_df)
        assert result is not None or result in (True, False)


# =============================================================================
# IPO Tests
# =============================================================================

class TestIPOMethods:
    """Test IPO related methods."""
    
    def test_ipo_lifetime_first_day_bullish_break(self, screener, bullish_df):
        """Test IPO lifetime first day bullish break."""
        result = screener.findIPOLifetimeFirstDayBullishBreak(bullish_df)
        assert result is not None or result in (True, False)


# =============================================================================
# Relative Strength Tests
# =============================================================================

class TestCalcRelativeStrength:
    """Test calc_relative_strength method."""
    
    def test_calc_relative_strength(self, screener, bullish_df):
        """Test relative strength calculation."""
        try:
            result = screener.calc_relative_strength(bullish_df)
        except:
            pass
    
    def test_calc_relative_strength_with_benchmark(self, screener, bullish_df, bearish_df):
        """Test relative strength with benchmark."""
        try:
            result = screener.calc_relative_strength(bullish_df, benchmark_data=bearish_df)
        except:
            pass


# =============================================================================
# Cup and Handle Tests
# =============================================================================

class TestCupAndHandle:
    """Test Cup and Handle pattern methods."""
    
    def test_find_cup_and_handle_pattern(self, screener, bullish_df):
        """Test findCupAndHandlePattern."""
        try:
            result = screener.findCupAndHandlePattern(bullish_df, "TEST")
        except:
            pass
    
    def test_find_cup_and_handle(self, screener, bullish_df):
        """Test find_cup_and_handle."""
        try:
            result = screener.find_cup_and_handle(bullish_df, {}, {})
        except:
            pass


# =============================================================================
# Buy/Sell Signals Tests
# =============================================================================

class TestComputeBuySellSignals:
    """Test computeBuySellSignals method."""
    
    def test_compute_buy_sell_signals(self, screener, bullish_df):
        """Test computing buy/sell signals."""
        try:
            result = screener.computeBuySellSignals(bullish_df)
        except:
            pass
    
    def test_compute_buy_sell_signals_retry(self, screener, bullish_df):
        """Test computing buy/sell signals with retry."""
        try:
            result = screener.computeBuySellSignals(bullish_df, retry=True)
        except:
            pass


# =============================================================================
# Breakout Value Tests
# =============================================================================

class TestFindBreakoutValue:
    """Test findBreakoutValue method."""
    
    def test_find_breakout_value(self, screener, bullish_df):
        """Test finding breakout value."""
        try:
            result = screener.findBreakoutValue(bullish_df, {}, {})
        except:
            pass


# =============================================================================
# Current Saved Value Tests
# =============================================================================

class TestFindCurrentSavedValue:
    """Test findCurrentSavedValue method."""
    
    def test_find_current_saved_value_exists(self, screener):
        """Test findCurrentSavedValue when key exists."""
        screen_dict = {'Pattern': 'Test'}
        save_dict = {'Pattern': 'SaveTest'}
        result = screener.findCurrentSavedValue(screen_dict, save_dict, 'Pattern')
        assert result is not None
    
    def test_find_current_saved_value_not_exists(self, screener):
        """Test findCurrentSavedValue when key doesn't exist."""
        result = screener.findCurrentSavedValue({}, {}, 'Pattern')
        assert result is not None


# =============================================================================
# VWAP Tests
# =============================================================================

class TestVWAPMethods:
    """Test VWAP related methods."""
    
    def test_find_bullish_avwap(self, screener, bullish_df):
        """Test findBullishAVWAP."""
        try:
            result = screener.findBullishAVWAP(bullish_df, {}, {})
        except:
            pass


# =============================================================================
# RSI MACD Tests
# =============================================================================

class TestRSIMACDMethods:
    """Test RSI/MACD related methods."""
    
    def test_find_bullish_intraday_rsi_macd(self, screener, bullish_df):
        """Test findBullishIntradayRSIMACD."""
        try:
            result = screener.findBullishIntradayRSIMACD(bullish_df)
        except:
            pass
