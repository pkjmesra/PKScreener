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

    Trading Signals Module
    ======================
    
    This module provides comprehensive buy/sell signal detection using multiple
    technical indicators and strategies. It aggregates various signal sources
    to produce strong buy/sell recommendations.
    
    Indicators Used:
    - RSI (Relative Strength Index) - Momentum oscillator
    - MACD (Moving Average Convergence Divergence) - Trend following
    - ATR Trailing Stops - Volatility-based stop loss
    - Volume Analysis - Confirmation of price movements
    - Moving Average Crossovers - Trend direction changes
    - Price Action Patterns - Higher highs/lows, lower highs/lows
    - CCI (Commodity Channel Index) - Overbought/oversold
    - MFI (Money Flow Index) - Volume-weighted momentum
    
    Example:
        >>> from pkscreener.classes.screening.signals import TradingSignals
        >>> signals = TradingSignals(configManager)
        >>> 
        >>> # Analyze a single stock
        >>> result = signals.analyze(df)
        >>> if result.is_strong_buy:
        >>>     print(f"Strong Buy: {result.confidence}% confidence")
        >>>     print(f"Reasons: {result.reasons}")
        >>> 
        >>> # Batch analysis for multiple stocks
        >>> strong_buys = []
        >>> for symbol, stock_df in stock_data.items():
        >>>     if signals.find_strong_buys(stock_df):
        >>>         strong_buys.append(symbol)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.log import default_logger


class SignalStrength(Enum):
    """
    Enumeration of signal strength levels for trading recommendations.
    
    This enum provides a hierarchical scale from strong sell to strong buy,
    allowing for nuanced recommendations rather than binary buy/sell signals.
    
    Attributes:
        STRONG_BUY (int): Strong buy recommendation with high confidence (value 5)
        BUY (int): Buy recommendation with good confidence (value 4)
        WEAK_BUY (int): Weak buy recommendation (value 3)
        NEUTRAL (int): Neutral/no clear signal (value 2)
        WEAK_SELL (int): Weak sell recommendation (value 1)
        SELL (int): Sell recommendation with good confidence (value 0)
        STRONG_SELL (int): Strong sell recommendation with high confidence (value -1)
    
    Example:
        >>> from pkscreener.classes.screening.signals import SignalStrength
        >>> if signal == SignalStrength.STRONG_BUY:
        >>>     print("Strong Buy Signal!")
        >>> elif signal == SignalStrength.STRONG_SELL:
        >>>     print("Strong Sell Signal!")
    """
    STRONG_BUY = 5   # Strong buy recommendation with high confidence
    BUY = 4          # Buy recommendation with good confidence
    WEAK_BUY = 3     # Weak buy recommendation
    NEUTRAL = 2      # Neutral/no clear signal
    WEAK_SELL = 1    # Weak sell recommendation
    SELL = 0         # Sell recommendation with good confidence
    STRONG_SELL = -1 # Strong sell recommendation with high confidence


@dataclass
class SignalResult:
    """
    Container for trading signal analysis results.
    
    This dataclass encapsulates the complete analysis result including the
    signal strength, confidence level, contributing reasons, and indicator values.
    
    Attributes:
        signal (SignalStrength): The overall signal strength (STRONG_BUY to STRONG_SELL)
        confidence (float): Confidence level as percentage (0-100%)
        reasons (List[str]): List of reasons supporting the signal decision
        indicators (Dict[str, float]): Dictionary of indicator values used in analysis
            (e.g., {'RSI': 28.5, 'MFI': 25.3})
    
    Properties:
        is_buy (bool): True if signal is any buy level (WEAK_BUY, BUY, or STRONG_BUY)
        is_sell (bool): True if signal is any sell level (WEAK_SELL, SELL, or STRONG_SELL)
        is_strong_buy (bool): True if signal is STRONG_BUY
        is_strong_sell (bool): True if signal is STRONG_SELL
    
    Example:
        >>> result = signals.analyze(df)
        >>> print(f"Signal: {result.signal.name}")
        >>> print(f"Confidence: {result.confidence}%")
        >>> if result.reasons:
        >>>     for reason in result.reasons:
        >>>         print(f"  - {reason}")
        >>> if result.is_strong_buy:
        >>>     # Execute buy order
        >>>     place_order(symbol, action="BUY")
    """
    signal: SignalStrength
    confidence: float  # Confidence level as percentage (0-100%)
    reasons: List[str] = field(default_factory=list)  # Reasons supporting the signal
    indicators: Dict[str, float] = field(default_factory=dict)  # Indicator values
    
    @property
    def is_buy(self) -> bool:
        """
        Check if the signal indicates any level of buy recommendation.
        
        Returns:
            bool: True if signal is WEAK_BUY, BUY, or STRONG_BUY, False otherwise
        """
        return self.signal.value >= SignalStrength.WEAK_BUY.value
    
    @property
    def is_sell(self) -> bool:
        """
        Check if the signal indicates any level of sell recommendation.
        
        Returns:
            bool: True if signal is WEAK_SELL, SELL, or STRONG_SELL, False otherwise
        """
        return self.signal.value <= SignalStrength.WEAK_SELL.value
    
    @property
    def is_strong_buy(self) -> bool:
        """
        Check if the signal is a STRONG_BUY recommendation.
        
        Returns:
            bool: True if signal is STRONG_BUY, False otherwise
        """
        return self.signal == SignalStrength.STRONG_BUY
    
    @property
    def is_strong_sell(self) -> bool:
        """
        Check if the signal is a STRONG_SELL recommendation.
        
        Returns:
            bool: True if signal is STRONG_SELL, False otherwise
        """
        return self.signal == SignalStrength.STRONG_SELL


class TradingSignals:
    """
    Comprehensive trading signal detector that combines multiple technical indicators.
    
    This class analyzes OHLCV data to generate buy/sell signals with confidence
    scores. It uses a weighted scoring system that aggregates signals from:
    
    1. RSI (Relative Strength Index) - 15% weight
       - Identifies oversold (<30) and overbought (>70) conditions
       
    2. MACD (Moving Average Convergence Divergence) - 15% weight
       - Detects bullish/bearish crossovers and histogram trends
       
    3. ATR Trailing Stops - 20% weight
       - Volatility-based trailing stops for trend following
       
    4. Volume Analysis - 15% weight
       - Volume surges with price changes for confirmation
       
    5. Moving Average Crossovers - 15% weight
       - Golden/death crosses and MA alignments
       
    6. Price Action Patterns - 10% weight
       - Higher highs/lows (uptrend) and lower highs/lows (downtrend)
       
    7. Momentum Indicators (CCI, MFI) - 10% weight
       - Overbought/oversold conditions from CCI and MFI
    
    The final score is normalized to 0-100, where:
    - 0-20: STRONG_SELL
    - 20-35: SELL
    - 35-45: WEAK_SELL
    - 45-55: NEUTRAL
    - 55-65: WEAK_BUY
    - 65-80: BUY
    - 80-100: STRONG_BUY
    
    Attributes:
        WEIGHTS (Dict[str, int]): Weight configuration for each indicator type
        configManager: Configuration manager instance for custom settings
        logger: Logger instance for debugging and error tracking
    
    Example:
        >>> from pkscreener.classes.screening.signals import TradingSignals
        >>> 
        >>> # Initialize the analyzer
        >>> signals = TradingSignals(configManager)
        >>> 
        >>> # Analyze a single stock
        >>> result = signals.analyze(df)
        >>> print(f"Signal: {result.signal.name}")
        >>> print(f"Confidence: {result.confidence}%")
        >>> print(f"RSI Value: {result.indicators.get('RSI', 'N/A')}")
        >>> 
        >>> # Check for strong buys in a portfolio
        >>> strong_buys = []
        >>> for symbol, stock_data in portfolio.items():
        >>>     if signals.find_strong_buys(stock_data):
        >>>         strong_buys.append(symbol)
        >>> print(f"Strong buys today: {strong_buys}")
        >>> 
        >>> # Batch analysis with result storage
        >>> for symbol, df in stock_dict.items():
        >>>     save_dict = {}
        >>>     screen_dict = {}
        >>>     if signals.find_buy_signals(df, save_dict, screen_dict):
        >>>         print(f"{symbol}: {save_dict.get('Signal')} ({save_dict.get('Confidence')})")
    """
    
    # Signal weight configuration - defines importance of each indicator
    WEIGHTS = {
        'rsi': 15,          # RSI weight (0-100 scale)
        'macd': 15,         # MACD weight (0-100 scale)
        'atr_trailing': 20, # ATR trailing stop weight (0-100 scale)
        'volume': 15,       # Volume analysis weight (0-100 scale)
        'ma_crossover': 15, # Moving average crossover weight (0-100 scale)
        'price_action': 10, # Price action weight (0-100 scale)
        'momentum': 10,     # Momentum indicators weight (0-100 scale)
    }
    
    def __init__(self, configManager=None):
        """
        Initialize the TradingSignals analyzer.
        
        Args:
            configManager: Configuration manager instance (optional). 
                         If provided, can be used to customize thresholds
                         and behavior based on user preferences.
        
        Example:
            >>> from pkscreener.classes import ConfigManager
            >>> config = ConfigManager.tools()
            >>> signals = TradingSignals(config)
        """
        self.configManager = configManager
        self.logger = default_logger()
    
    def analyze(self, df: pd.DataFrame, saveDict: Dict = None, 
                screenDict: Dict = None) -> SignalResult:
        """
        Analyze a stock's OHLCV data for trading signals.
        
        This method performs comprehensive technical analysis by evaluating
        all configured indicators and combining their signals using the
        weighted scoring system.
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with columns:
                - 'open': Opening prices
                - 'high': High prices
                - 'low': Low prices
                - 'close': Closing prices
                - 'volume': Trading volume (optional but recommended)
                DataFrame should have at least 20 rows for meaningful analysis.
                
            saveDict (Dict, optional): Dictionary to store analysis results
                for persistence. If provided, 'Signal' and 'Confidence' keys
                will be added with the analysis results.
                
            screenDict (Dict, optional): Dictionary to store formatted results
                for screen display. If provided, 'Signal' and 'Confidence' keys
                will be added with color-formatted text.
        
        Returns:
            SignalResult: A dataclass containing:
                - signal: The overall signal strength (SignalStrength enum)
                - confidence: Confidence percentage (0-100%)
                - reasons: List of explanatory reasons
                - indicators: Dictionary of indicator values
        
        Example:
            >>> result = signals.analyze(df)
            >>> if result.is_strong_buy:
            >>>     print(f"Strong Buy! Confidence: {result.confidence}%")
            >>>     print("Reasons:")
            >>>     for reason in result.reasons:
            >>>         print(f"  - {reason}")
        """
        # Validate input data - need at least 20 periods for meaningful analysis
        if df is None or len(df) < 20:
            return SignalResult(
                signal=SignalStrength.NEUTRAL,
                confidence=0,
                reasons=["Insufficient data for analysis (need at least 20 periods)"]
            )
        
        # Import technical analysis library
        try:
            from pkscreener.classes.Pktalib import pktalib
        except ImportError:
            return SignalResult(
                signal=SignalStrength.NEUTRAL,
                confidence=0,
                reasons=["Technical analysis library (pktalib) not available"]
            )
        
        signals = []        # List of (indicator_name, signal_score)
        reasons = []        # List of reason strings
        indicators = {}     # Dictionary of indicator values
        
        # 1. RSI Analysis - Momentum oscillator
        rsi_signal, rsi_reason, rsi_value = self._analyze_rsi(df, pktalib)
        signals.append(('rsi', rsi_signal))
        if rsi_reason:
            reasons.append(rsi_reason)
        indicators['RSI'] = rsi_value
        
        # 2. MACD Analysis - Trend following
        macd_signal, macd_reason = self._analyze_macd(df, pktalib)
        signals.append(('macd', macd_signal))
        if macd_reason:
            reasons.append(macd_reason)
        
        # 3. ATR Trailing Stop Analysis - Volatility-based
        atr_signal, atr_reason = self._analyze_atr_trailing(df, pktalib)
        signals.append(('atr_trailing', atr_signal))
        if atr_reason:
            reasons.append(atr_reason)
        
        # 4. Volume Analysis - Confirmation
        volume_signal, volume_reason = self._analyze_volume(df)
        signals.append(('volume', volume_signal))
        if volume_reason:
            reasons.append(volume_reason)
        
        # 5. Moving Average Crossover Analysis - Trend direction
        ma_signal, ma_reason = self._analyze_ma_crossover(df, pktalib)
        signals.append(('ma_crossover', ma_signal))
        if ma_reason:
            reasons.append(ma_reason)
        
        # 6. Price Action Analysis - Patterns
        pa_signal, pa_reason = self._analyze_price_action(df)
        signals.append(('price_action', pa_signal))
        if pa_reason:
            reasons.append(pa_reason)
        
        # 7. Momentum Analysis - CCI/MFI
        mom_signal, mom_reason = self._analyze_momentum(df, pktalib)
        signals.append(('momentum', mom_signal))
        if mom_reason:
            reasons.append(mom_reason)
        
        # Calculate weighted score
        total_weight = sum(self.WEIGHTS.values())
        weighted_score = 0
        
        for indicator, signal in signals:
            weight = self.WEIGHTS.get(indicator, 10)
            weighted_score += (signal * weight)
        
        # Normalize to 0-100 scale
        normalized_score = (weighted_score / total_weight) * 100
        
        # Determine signal strength based on normalized score
        overall_signal = self._score_to_signal(normalized_score)
        
        # Calculate confidence as distance from neutral (50)
        # Higher confidence when score is far from neutral
        confidence = min(100, abs(normalized_score - 50) * 2)
        
        # Update output dictionaries if provided
        signal_text = self._format_signal_text(overall_signal)
        if saveDict is not None:
            saveDict['Signal'] = overall_signal.name
            saveDict['Confidence'] = f"{confidence:.1f}%"
        if screenDict is not None:
            screenDict['Signal'] = signal_text
            screenDict['Confidence'] = f"{confidence:.1f}%"
        
        return SignalResult(
            signal=overall_signal,
            confidence=confidence,
            reasons=reasons,
            indicators=indicators
        )
    
    def _analyze_rsi(self, df: pd.DataFrame, pktalib) -> Tuple[float, Optional[str], float]:
        """
        Analyze RSI (Relative Strength Index) for buy/sell signals.
        
        RSI values:
        - Below 30: Oversold (bullish signal)
        - Below 40: Approaching oversold (weak bullish)
        - Above 70: Overbought (bearish signal)
        - Above 60: Approaching overbought (weak bearish)
        - 40-60: Neutral range
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with 'close' prices
            pktalib: Technical analysis library instance
            
        Returns:
            Tuple containing:
                - signal_score (float): 0=sell, 0.5=neutral, 1=buy
                - reason (str or None): Explanation of the signal
                - rsi_value (float): Current RSI value
        """
        try:
            # Calculate 14-period RSI
            rsi = pktalib.RSI(df['close'], timeperiod=14)
            if rsi is None or len(rsi) == 0:
                return 0.5, None, 50
            
            current_rsi = rsi.iloc[-1] if hasattr(rsi, 'iloc') else rsi[-1]
            
            # Determine signal based on RSI value
            if current_rsi < 30:
                # Strong oversold condition
                return 0.8, f"RSI oversold ({current_rsi:.1f})", current_rsi
            elif current_rsi < 40:
                # Mild oversold condition
                return 0.65, f"RSI approaching oversold ({current_rsi:.1f})", current_rsi
            elif current_rsi > 70:
                # Strong overbought condition
                return 0.2, f"RSI overbought ({current_rsi:.1f})", current_rsi
            elif current_rsi > 60:
                # Mild overbought condition
                return 0.35, f"RSI approaching overbought ({current_rsi:.1f})", current_rsi
            else:
                # Neutral range
                return 0.5, None, current_rsi
        except Exception as e:
            self.logger.debug(f"RSI analysis error: {e}")
            return 0.5, None, 50
    
    def _analyze_macd(self, df: pd.DataFrame, pktalib) -> Tuple[float, Optional[str]]:
        """
        Analyze MACD (Moving Average Convergence Divergence) for buy/sell signals.
        
        MACD Components:
        - MACD Line: Fast EMA - Slow EMA
        - Signal Line: EMA of MACD line
        - Histogram: MACD line - Signal line
        
        Signal Detection:
        - Bullish crossover: Histogram crosses from negative to positive
        - Bearish crossover: Histogram crosses from positive to negative
        - Histogram trend: Increasing/decreasing confirms momentum
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with 'close' prices
            pktalib: Technical analysis library instance
            
        Returns:
            Tuple containing:
                - signal_score (float): 0=sell, 0.5=neutral, 1=buy
                - reason (str or None): Explanation of the signal
        """
        try:
            # Calculate MACD (12, 26, 9 are standard parameters)
            macd, signal, hist = pktalib.MACD(df['close'])
            if macd is None or len(macd) == 0:
                return 0.5, None
            
            current_macd = macd.iloc[-1] if hasattr(macd, 'iloc') else macd[-1]
            current_signal = signal.iloc[-1] if hasattr(signal, 'iloc') else signal[-1]
            current_hist = hist.iloc[-1] if hasattr(hist, 'iloc') else hist[-1]
            
            prev_hist = hist.iloc[-2] if hasattr(hist, 'iloc') else hist[-2]
            
            # Detect crossovers
            if current_hist > 0 and prev_hist <= 0:
                # Bullish crossover (strong buy signal)
                return 0.85, "MACD bullish crossover"
            elif current_hist < 0 and prev_hist >= 0:
                # Bearish crossover (strong sell signal)
                return 0.15, "MACD bearish crossover"
            elif current_hist > 0 and current_hist > prev_hist:
                # Bullish histogram trend
                return 0.7, "MACD histogram increasing"
            elif current_hist < 0 and current_hist < prev_hist:
                # Bearish histogram trend
                return 0.3, "MACD histogram decreasing"
            else:
                return 0.5, None
        except Exception as e:
            self.logger.debug(f"MACD analysis error: {e}")
            return 0.5, None
    
    def _analyze_atr_trailing(self, df: pd.DataFrame, pktalib) -> Tuple[float, Optional[str]]:
        """
        Analyze ATR (Average True Range) Trailing Stop for buy/sell signals.
        
        ATR Trailing Stop calculates a dynamic stop level based on volatility.
        When price is above the trailing stop, it indicates an uptrend (bullish).
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with 'high', 'low', 'close' prices
            pktalib: Technical analysis library instance
            
        Returns:
            Tuple containing:
                - signal_score (float): 0=sell, 0.5=neutral, 1=buy
                - reason (str or None): Explanation of the signal
        """
        try:
            # Calculate 14-period ATR
            atr = pktalib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            if atr is None or len(atr) == 0:
                return 0.5, None
            
            close = df['close'].iloc[-1]
            current_atr = atr.iloc[-1] if hasattr(atr, 'iloc') else atr[-1]
            
            # Calculate trailing stop level (2x ATR is standard)
            key_value = 2
            trailing_stop = close - (key_value * current_atr)
            
            # Compare price to trailing stop
            if close > trailing_stop * 1.02:  # Price 2% above trailing stop
                return 0.75, "Price above ATR trailing stop"
            elif close < trailing_stop * 0.98:  # Price 2% below trailing stop
                return 0.25, "Price below ATR trailing stop"
            else:
                return 0.5, None
        except Exception as e:
            self.logger.debug(f"ATR analysis error: {e}")
            return 0.5, None
    
    def _analyze_volume(self, df: pd.DataFrame) -> Tuple[float, Optional[str]]:
        """
        Analyze volume patterns to confirm price movements.
        
        Volume analysis looks for:
        - Volume surges with price increases (bullish confirmation)
        - Volume surges with price decreases (bearish confirmation)
        - Above average volume with gains (weak bullish)
        - Above average volume with losses (weak bearish)
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with 'close' and 'volume' columns
            
        Returns:
            Tuple containing:
                - signal_score (float): 0=sell, 0.5=neutral, 1=buy
                - reason (str or None): Explanation of the signal
        """
        try:
            # Check if volume data is available
            if 'volume' not in df.columns:
                return 0.5, None
            
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
            
            if avg_volume == 0:
                return 0.5, None
            
            volume_ratio = current_volume / avg_volume
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            
            # High volume with positive price = bullish
            if volume_ratio > 2 and price_change > 0.01:
                return 0.85, f"Volume surge ({volume_ratio:.1f}x) with price increase"
            elif volume_ratio > 1.5 and price_change > 0:
                return 0.7, f"Above average volume ({volume_ratio:.1f}x) with gain"
            # High volume with negative price = bearish
            elif volume_ratio > 2 and price_change < -0.01:
                return 0.15, f"Volume surge ({volume_ratio:.1f}x) with price decrease"
            elif volume_ratio > 1.5 and price_change < 0:
                return 0.3, f"Above average volume ({volume_ratio:.1f}x) with loss"
            else:
                return 0.5, None
        except Exception as e:
            self.logger.debug(f"Volume analysis error: {e}")
            return 0.5, None
    
    def _analyze_ma_crossover(self, df: pd.DataFrame, pktalib) -> Tuple[float, Optional[str]]:
        """
        Analyze moving average crossovers for trend direction signals.
        
        Moving Averages Used:
        - EMA 20: Short-term trend
        - EMA 50: Medium-term trend  
        - SMA 200: Long-term trend
        
        Signals:
        - Golden Cross: EMA20 crosses above EMA50 (bullish)
        - Death Cross: EMA20 crosses below EMA50 (bearish)
        - Bullish Alignment: Price > EMA20 > EMA50 > SMA200
        - Bearish Alignment: Price < EMA20 < EMA50 < SMA200
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with 'close' prices
            pktalib: Technical analysis library instance
            
        Returns:
            Tuple containing:
                - signal_score (float): 0=sell, 0.5=neutral, 1=buy
                - reason (str or None): Explanation of the signal
        """
        try:
            # Calculate moving averages
            ema_20 = pktalib.EMA(df['close'], timeperiod=20)
            ema_50 = pktalib.EMA(df['close'], timeperiod=50)
            sma_200 = pktalib.SMA(df['close'], timeperiod=200)
            
            if ema_20 is None or ema_50 is None:
                return 0.5, None
            
            current_ema20 = ema_20.iloc[-1] if hasattr(ema_20, 'iloc') else ema_20[-1]
            current_ema50 = ema_50.iloc[-1] if hasattr(ema_50, 'iloc') else ema_50[-1]
            prev_ema20 = ema_20.iloc[-2] if hasattr(ema_20, 'iloc') else ema_20[-2]
            prev_ema50 = ema_50.iloc[-2] if hasattr(ema_50, 'iloc') else ema_50[-2]
            
            close = df['close'].iloc[-1]
            
            # Detect Golden Cross (bullish)
            if prev_ema20 <= prev_ema50 and current_ema20 > current_ema50:
                return 0.9, "Golden cross (EMA20 > EMA50)"
            # Detect Death Cross (bearish)
            elif prev_ema20 >= prev_ema50 and current_ema20 < current_ema50:
                return 0.1, "Death cross (EMA20 < EMA50)"
            # Check alignment when SMA200 available
            elif sma_200 is not None:
                sma_200_val = sma_200.iloc[-1] if hasattr(sma_200, 'iloc') else sma_200[-1]
                # Bullish alignment
                if close > current_ema20 > current_ema50 > sma_200_val:
                    return 0.75, "Price above all major MAs (bullish alignment)"
                # Bearish alignment
                elif close < current_ema20 < current_ema50 < sma_200_val:
                    return 0.25, "Price below all major MAs (bearish alignment)"
            
            return 0.5, None
        except Exception as e:
            self.logger.debug(f"MA crossover analysis error: {e}")
            return 0.5, None
    
    def _analyze_price_action(self, df: pd.DataFrame) -> Tuple[float, Optional[str]]:
        """
        Analyze price action patterns for trend identification.
        
        Price Action Patterns:
        - Higher highs and higher lows: Uptrend (bullish)
        - Lower highs and lower lows: Downtrend (bearish)
        - Higher lows only: Potential bullish reversal
        - Lower highs only: Weakening momentum (bearish)
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with 'high' and 'low' prices
            
        Returns:
            Tuple containing:
                - signal_score (float): 0=sell, 0.5=neutral, 1=buy
                - reason (str or None): Explanation of the signal
        """
        try:
            # Need at least 5 periods for pattern analysis
            if len(df) < 5:
                return 0.5, None
            
            # Get last 5 periods' highs and lows
            highs = df['high'].tail(5).values
            lows = df['low'].tail(5).values
            closes = df['close'].tail(5).values
            
            # Detect uptrend (higher highs AND higher lows)
            higher_highs = all(highs[i] >= highs[i-1] for i in range(1, len(highs)))
            higher_lows = all(lows[i] >= lows[i-1] for i in range(1, len(lows)))
            
            # Detect downtrend (lower highs AND lower lows)
            lower_highs = all(highs[i] <= highs[i-1] for i in range(1, len(highs)))
            lower_lows = all(lows[i] <= lows[i-1] for i in range(1, len(lows)))
            
            if higher_highs and higher_lows:
                return 0.8, "Higher highs and higher lows (uptrend)"
            elif lower_highs and lower_lows:
                return 0.2, "Lower highs and lower lows (downtrend)"
            elif higher_lows:
                return 0.65, "Higher lows (potential reversal)"
            elif lower_highs:
                return 0.35, "Lower highs (weakening momentum)"
            else:
                return 0.5, None
        except Exception as e:
            self.logger.debug(f"Price action analysis error: {e}")
            return 0.5, None
    
    def _analyze_momentum(self, df: pd.DataFrame, pktalib) -> Tuple[float, Optional[str]]:
        """
        Analyze momentum indicators (CCI and MFI) for overbought/oversold conditions.
        
        Momentum Indicators:
        - CCI (Commodity Channel Index): Measures price deviation from statistical mean
          * Below -100: Oversold (bullish)
          * Above +100: Overbought (bearish)
          
        - MFI (Money Flow Index): Volume-weighted RSI
          * Below 20: Oversold (bullish)
          * Above 80: Overbought (bearish)
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with price and volume data
            pktalib: Technical analysis library instance
            
        Returns:
            Tuple containing:
                - signal_score (float): 0=sell, 0.5=neutral, 1=buy
                - reason (str or None): Explanation of the signal
        """
        try:
            # Calculate CCI (Commodity Channel Index)
            cci = pktalib.CCI(df['high'], df['low'], df['close'], timeperiod=20)
            
            # Calculate MFI (Money Flow Index) if volume available
            if 'volume' in df.columns:
                mfi = pktalib.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=14)
            else:
                mfi = None
            
            signals = []
            
            # Analyze CCI
            if cci is not None and len(cci) > 0:
                current_cci = cci.iloc[-1] if hasattr(cci, 'iloc') else cci[-1]
                if current_cci < -100:
                    signals.append((0.75, "CCI oversold"))
                elif current_cci > 100:
                    signals.append((0.25, "CCI overbought"))
            
            # Analyze MFI
            if mfi is not None and len(mfi) > 0:
                current_mfi = mfi.iloc[-1] if hasattr(mfi, 'iloc') else mfi[-1]
                if current_mfi < 20:
                    signals.append((0.8, "MFI oversold"))
                elif current_mfi > 80:
                    signals.append((0.2, "MFI overbought"))
            
            # Combine signals if any exist
            if signals:
                avg_signal = sum(s[0] for s in signals) / len(signals)
                reasons = [s[1] for s in signals]
                return avg_signal, "; ".join(reasons)
            
            return 0.5, None
        except Exception as e:
            self.logger.debug(f"Momentum analysis error: {e}")
            return 0.5, None
    
    def _score_to_signal(self, score: float) -> SignalStrength:
        """
        Convert normalized score to SignalStrength enum value.
        
        Score to Signal Mapping:
            - 80-100: STRONG_BUY
            - 65-80: BUY
            - 55-65: WEAK_BUY
            - 45-55: NEUTRAL
            - 35-45: WEAK_SELL
            - 20-35: SELL
            - 0-20: STRONG_SELL
        
        Args:
            score (float): Normalized score between 0 and 100
            
        Returns:
            SignalStrength: Corresponding signal strength enum value
        """
        if score >= 80:
            return SignalStrength.STRONG_BUY
        elif score >= 65:
            return SignalStrength.BUY
        elif score >= 55:
            return SignalStrength.WEAK_BUY
        elif score >= 45:
            return SignalStrength.NEUTRAL
        elif score >= 35:
            return SignalStrength.WEAK_SELL
        elif score >= 20:
            return SignalStrength.SELL
        else:
            return SignalStrength.STRONG_SELL
    
    def _format_signal_text(self, signal: SignalStrength) -> str:
        """
        Format signal for display with appropriate color codes.
        
        Color Mapping:
            - All BUY signals: Green (colorText.GREEN)
            - NEUTRAL signal: Yellow/Warning (colorText.WARN)
            - All SELL signals: Red/Fail (colorText.FAIL)
        
        Args:
            signal (SignalStrength): The signal strength enum value
            
        Returns:
            str: Color-formatted signal text for console display
        """
        color_map = {
            SignalStrength.STRONG_BUY: colorText.GREEN,
            SignalStrength.BUY: colorText.GREEN,
            SignalStrength.WEAK_BUY: colorText.GREEN,
            SignalStrength.NEUTRAL: colorText.WARN,
            SignalStrength.WEAK_SELL: colorText.FAIL,
            SignalStrength.SELL: colorText.FAIL,
            SignalStrength.STRONG_SELL: colorText.FAIL,
        }
        color = color_map.get(signal, colorText.END)
        # Replace underscores with spaces for better readability
        return f"{color}{signal.name.replace('_', ' ')}{colorText.END}"
    
    def find_strong_buys(self, df: pd.DataFrame, saveDict: Dict = None,
                         screenDict: Dict = None) -> bool:
        """
        Check if stock qualifies as a Strong Buy signal.
        
        A Strong Buy requires:
        - Signal strength of STRONG_BUY
        - Confidence level of at least 60%
        
        This method is useful for filtering a watchlist to find the
        most promising buying opportunities.
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame to analyze
            saveDict (Dict, optional): Dictionary to store analysis results
            screenDict (Dict, optional): Dictionary for screen display results
            
        Returns:
            bool: True if stock is a Strong Buy, False otherwise
            
        Example:
            >>> strong_buys = []
            >>> for symbol, stock_df in stock_data.items():
            >>>     if signals.find_strong_buys(stock_df):
            >>>         strong_buys.append(symbol)
            >>> print(f"Strong buy recommendations: {strong_buys}")
        """
        result = self.analyze(df, saveDict, screenDict)
        return result.is_strong_buy and result.confidence >= 60
    
    def find_strong_sells(self, df: pd.DataFrame, saveDict: Dict = None,
                          screenDict: Dict = None) -> bool:
        """
        Check if stock qualifies as a Strong Sell signal.
        
        A Strong Sell requires:
        - Signal strength of STRONG_SELL
        - Confidence level of at least 60%
        
        This method helps identify stocks that should be exited or shorted.
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame to analyze
            saveDict (Dict, optional): Dictionary to store analysis results
            screenDict (Dict, optional): Dictionary for screen display results
            
        Returns:
            bool: True if stock is a Strong Sell, False otherwise
            
        Example:
            >>> strong_sells = []
            >>> for symbol, stock_df in portfolio.items():
            >>>     if signals.find_strong_sells(stock_df):
            >>>         strong_sells.append(symbol)
            >>> print(f"Consider selling: {strong_sells}")
        """
        result = self.analyze(df, saveDict, screenDict)
        return result.is_strong_sell and result.confidence >= 60
    
    def find_buy_signals(self, df: pd.DataFrame, saveDict: Dict = None,
                         screenDict: Dict = None) -> bool:
        """
        Check if stock qualifies for any buy signal (including weak).
        
        This method is more inclusive than find_strong_buys, capturing
        all bullish signals regardless of strength.
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame to analyze
            saveDict (Dict, optional): Dictionary to store analysis results
            screenDict (Dict, optional): Dictionary for screen display results
            
        Returns:
            bool: True if stock has any buy signal, False otherwise
            
        Example:
            >>> potential_buys = []
            >>> for symbol, stock_df in watchlist.items():
            >>>     if signals.find_buy_signals(stock_df):
            >>>         potential_buys.append(symbol)
            >>> print(f"Stocks with bullish signals: {potential_buys}")
        """
        result = self.analyze(df, saveDict, screenDict)
        return result.is_buy
    
    def find_sell_signals(self, df: pd.DataFrame, saveDict: Dict = None,
                          screenDict: Dict = None) -> bool:
        """
        Check if stock qualifies for any sell signal (including weak).
        
        This method is more inclusive than find_strong_sells, capturing
        all bearish signals regardless of strength.
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame to analyze
            saveDict (Dict, optional): Dictionary to store analysis results
            screenDict (Dict, optional): Dictionary for screen display results
            
        Returns:
            bool: True if stock has any sell signal, False otherwise
            
        Example:
            >>> warnings = []
            >>> for symbol, stock_df in portfolio.items():
            >>>     if signals.find_sell_signals(stock_df):
            >>>         warnings.append(symbol)
            >>> print(f"Stocks showing weakness: {warnings}")
        """
        result = self.analyze(df, saveDict, screenDict)
        return result.is_sell