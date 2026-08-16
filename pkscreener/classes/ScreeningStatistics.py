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

import math
import sys
import warnings
import datetime
import numpy as np
import os
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd

from sys import float_info as sflt
import pkscreener.classes.Utility as Utility
from pkscreener import Imports
from pkscreener.classes.Pktalib import pktalib
from PKDevTools.classes.OutputControls import OutputControls
from PKDevTools.classes import Archiver, log
from PKNSETools.morningstartools import Stock

if sys.version_info >= (3, 11):
    import advanced_ta as ata

# from sklearn.preprocessing import StandardScaler
if Imports["scipy"]:
    from scipy.stats import linregress

from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from PKDevTools.classes.SuppressOutput import SuppressOutput
from PKDevTools.classes.MarketHours import MarketHours
# from PKDevTools.classes.log import measure_time

# Exception for only downloading stock data and not screening
class DownloadDataOnly(Exception):
    pass

class EligibilityConditionNotMet(Exception):
    pass

# Exception for stocks which are not newly listed when screening only for Newly Listed
class NotNewlyListed(Exception):
    pass


# Exception for stocks which are not stage two
class NotAStageTwoStock(Exception):
    pass

# Exception for LTP not being in the range as per config
class LTPNotInConfiguredRange(Exception):
    pass

# Exception for stocks which are low in volume as per configuration of 'minimumVolume'
class NotEnoughVolumeAsPerConfig(Exception):
    pass


# Exception for newly listed stocks with candle nos < daysToLookback
class StockDataNotAdequate(Exception):
    pass


# This Class contains methods for stock analysis and screening validation
class ScreeningStatistics:
    def __init__(self, configManager=None, default_logger=None,shouldLog=False) -> None:
        self.configManager = configManager
        self.default_logger = default_logger
        self.shouldLog = shouldLog
        self.setupLogger(self.default_logger.level)
        pd.options.mode.chained_assignment = None  # 'warn' or 'raise' or None

    def setupLogger(self, log_level):
        if log_level > 0:
            os.environ["PKDevTools_Default_Log_Level"] = str(log_level)
        log.setup_custom_logger(
            "pkscreener",
            log_level,
            trace=False,
            log_file_path="pkscreener-logs.txt",
            filter=None,
            selective_debug= False if "PK_DEBUG_ALL" in os.environ.keys() else True
        )

    def calc_relative_strength(self,df:pd.DataFrame):
        if df is None or len(df) <= 1:
            return -1
        closeColumn = 'Adj Close'
        if closeColumn not in df.columns:
            closeColumn = "close"

        with pd.option_context('mode.chained_assignment', None):
            df.sort_index(inplace=True)
            ## relative gain and losses
            df['close_shift'] = df[closeColumn].shift(1)
            ## Gains (true) and Losses (False)
            df['gains'] = df.apply(lambda x: x[closeColumn] if x[closeColumn] >= x['close_shift'] else 0, axis=1)
            df['loss'] = df.apply(lambda x: x[closeColumn] if x[closeColumn] <= x['close_shift'] else 0, axis=1)

        avg_gain = df['gains'].mean()
        avg_losses = df['loss'].mean()

        return avg_gain / avg_losses

    # =============================================================================
    # SIGNAL COMPUTATION METHODS FOR TRADING SIGNALS
    # =============================================================================
    # =============================================================================
    # USAGE GUIDE
    # =============================================================================

    """
    WHICH METHOD TO USE WHEN:

    ┌─────────────────────────────────────────────────────────────────────────────┐
    │ METHOD                           │ USE CASE                                 │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ computeBuySellSignals()          │ Daily screening of 2000+ stocks          │
    │                                  │ First-pass filtering                     │
    │                                  │ When speed > granularity                 │
    │                                  │ Basic signal detection                   │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ computeBuySellSignalsWithScores()│ Portfolio construction                   │
    │                                  │ Ranking signals by strength              │
    │                                  │ Setting confidence thresholds            │
    │                                  │ Quantitative analysis                    │
    │                                  │ Backtesting strategies                   │
    ├─────────────────────────────────────────────────────────────────────────────┤
    │ computeBalancedSignals()         │ Active trading                           │
    │                                  │ Position management                      │
    │                                  │ Preventing overtrading                   │
    │                                  │ Asymmetric thresholds (stronger sells)   │
    │                                  │ Tracking current position                │
    └─────────────────────────────────────────────────────────────────────────────┘

    EXAMPLE PIPELINE:

    # Step 1: Screen 2000+ stocks (fast, first pass)
    df = screener.computeBuySellSignals(df, confirmation_bars=1)

    # Step 2: Score the best candidates (slower, detailed)
    candidates = df[df["Buy"] | df["Sell"]]
    if len(candidates) > 0:
        scored = screener.computeBuySellSignalsWithScores(candidates)
        
        # Step 3: Apply balanced filtering for final signals
        final = screener.computeBalancedSignals(
            scored, 
            buy_threshold=3,      # Require stronger buys
            sell_threshold=2,     # Accept moderate sells  
            min_bars_between_signals=3
        )
        
        # Step 4: Get actionable signals
        entries = final[final["Buy_Signal"] | final["Sell_Signal"]]
        high_confidence = entries[entries["Confidence"] == "HIGH"]
    """

    def addBearishSellSignals(self, df_src, min_confidence=50):
        """
        Add additional bearish sell signals when ATR-based signals are weak.
        
        This method provides sell signals based on:
        - Death crosses (50/200 SMA)
        - Breakdown below key moving averages
        - EMA crossovers
        - RSI bearish divergences
        
        Args:
            df_src: DataFrame with OHLCV data and indicators (SMA, LMA, RSI)
            min_confidence: Minimum confidence threshold to accept signal
        
        Returns:
            DataFrame with added Sell signals
        """
        if df_src is None or len(df_src) < 20:
            return df_src
        
        df = df_src.copy()
        original_sell_count = df["Sell"].sum() if "Sell" in df.columns else 0
        
        # Initialize signal columns if not present
        if "Sell" not in df.columns:
            df["Sell"] = False
        if "Signal_Strength" not in df.columns:
            df["Signal_Strength"] = 0
        if "Sell_Confidence" not in df.columns:
            df["Sell_Confidence"] = 0
        
        # Only add signals if we don't already have many sells
        if original_sell_count > 0:
            return df  # Already have signals, don't add noise
        
        # =============================================================
        # 1. DEATH CROSS (50 SMA below 200 SMA)
        # =============================================================
        if "SMA" in df.columns and "LMA" in df.columns:
            # Price below both MAs adds conviction
            price_below_both = (df["close"] < df["SMA"]) & (df["close"] < df["LMA"])
            death_cross = (df["SMA"] < df["LMA"]) & (df["SMA"].shift(1) > df["LMA"].shift(1))
            
            # Stronger signal when price confirms
            strong_death_cross = death_cross & price_below_both
            if strong_death_cross.any():
                df.loc[strong_death_cross, "Sell"] = True
                df.loc[strong_death_cross, "Signal_Strength"] = 4
                df.loc[strong_death_cross, "Sell_Confidence"] = 85
            elif death_cross.any():
                df.loc[death_cross, "Sell"] = True
                df.loc[death_cross, "Signal_Strength"] = 3
                df.loc[death_cross, "Sell_Confidence"] = 70
        
        # =============================================================
        # 2. BREAKDOWN BELOW 200 SMA
        # =============================================================
        if "LMA" in df.columns and not df["Sell"].any():
            # Close breaks below 200 SMA (major support)
            below_200_with_volume = (
                (df["close"] < df["LMA"]) & 
                (df["close"].shift(1) > df["LMA"].shift(1)) &
                (df["volume"] > df["volume"].rolling(20).mean() * 1.2 if "volume" in df.columns else True)
            )
            if below_200_with_volume.any():
                df.loc[below_200_with_volume, "Sell"] = True
                df.loc[below_200_with_volume, "Signal_Strength"] = 3
                df.loc[below_200_with_volume, "Sell_Confidence"] = 75
        
        # =============================================================
        # 3. BEARISH ENGULFING PATTERN
        # =============================================================
        if len(df) > 1:
            # Current candle engulfs previous candle's body
            bearish_engulfing = (
                (df["open"] > df["close"]) &  # Current is bearish
                (df["open"].shift(1) < df["close"].shift(1)) &  # Previous was bullish
                (df["open"] > df["close"].shift(1)) &  # Opens above prev close
                (df["close"] < df["open"].shift(1))    # Closes below prev open
            )
            if bearish_engulfing.any() and not df["Sell"].any():
                df.loc[bearish_engulfing, "Sell"] = True
                df.loc[bearish_engulfing, "Signal_Strength"] = 3
                df.loc[bearish_engulfing, "Sell_Confidence"] = 65
        
        # =============================================================
        # 4. RSI SELLING PRESSURE
        # =============================================================
        if "RSI" in df.columns and not df["Sell"].any():
            # RSI falling from overbought with bearish momentum
            rsi_sell_signal = (
                (df["RSI"] > 70) &  # Was overbought
                (df["RSI"] < df["RSI"].shift(1)) &  # Now falling
                (df["close"] < df["close"].shift(1))  # Price falling
            )
            if rsi_sell_signal.any():
                df.loc[rsi_sell_signal, "Sell"] = True
                df.loc[rsi_sell_signal, "Signal_Strength"] = 2
                df.loc[rsi_sell_signal, "Sell_Confidence"] = 60
        
        # =============================================================
        # 5. MACD BEARISH CROSSOVER
        # =============================================================
        if len(df) > 26 and not df["Sell"].any():
            try:
                macd_line = pktalib.MACD(df["close"], 12, 26, 9)[0]
                macd_signal = pktalib.MACD(df["close"], 12, 26, 9)[1]
                
                if len(macd_line) > 1 and len(macd_signal) > 1:
                    macd_bearish = (macd_line < macd_signal) & (macd_line.shift(1) > macd_signal.shift(1))
                    if macd_bearish.any():
                        df.loc[macd_bearish, "Sell"] = True
                        df.loc[macd_bearish, "Signal_Strength"] = 3
                        df.loc[macd_bearish, "Sell_Confidence"] = 70
            except Exception:
                pass
        
        # Log results
        # new_sells = df["Sell"].sum() - original_sell_count
        # if new_sells > 0 and self.default_logger:
        #     self.default_logger.debug(f"Added {new_sells} bearish sell signals")
        
        return df

    def computeBuySellSignals(self, df_src, ema_period=200, retry=True, confirmation_bars=1, min_strength=2, 
                        volume_confirmation=True, stock_name="Unknown"):
        """
        Compute basic Buy/Sell signals based on ATR Trailing Stop with confirmation filters.
        
        This is the primary signal computation method that provides balanced signals
        with configurable confirmation levels. It's best for general purpose screening
        and daily scanning.
        
        ============================================================================
        SIGNAL TYPES
        ============================================================================
        
        The method generates TWO types of signals:
        
        1. BUY Signals - When price crosses ABOVE the ATR Trailing Stop
        - Indicates potential uptrend start
        - Price momentum positive
        - Bullish trend confirmation
        
        2. SELL Signals - When price crosses BELOW the ATR Trailing Stop
        - Indicates potential downtrend start
        - Price momentum negative
        - Bearish trend confirmation
        
        ============================================================================
        SIGNAL GENERATION PROCESS
        ============================================================================
        
        Step 1: Calculate EMA for trend filter
        Step 2: Detect EMA/Price crossover with ATR Trailing Stop
        Step 3: Apply consecutive bar confirmation (reduces false signals)
        Step 4: Calculate signal strength (1-5 scale)
        Step 5: Apply min_strength threshold
        Step 6: Add volume confirmation (optional)
        Step 7: Calculate confidence scores (0-100)
        
        ============================================================================
        SIGNAL STRENGTH SCORING (1-5)
        ============================================================================
        
        Base Score: 1 (all signals start here)
        Additional points:
        +1 - Volume surge confirmation
        +1 - Trend alignment (RSI > 50 for buys, RSI < 50 for sells)
        +1 - RSI momentum (rising for buys, falling for sells)
        +0-2 - Price distance from ATR stop (further = stronger)
        
        Result: 1=Weak, 2=Moderate, 3=Strong, 4=Very Strong, 5=Extremely Strong
        
        ============================================================================
        CONFIDENCE SCORES (0-100)
        ============================================================================
        
        Confidence = (Signal_Strength * 16) + Price_Contribution
        Price_Contribution = 0-30 points based on distance from ATR stop
        Crossover signals get an additional +20 points
        
        Interpret as:
        0-30: Low confidence - Consider avoiding
        31-70: Medium confidence - Good for regular positions
        71-100: High confidence - Excellent for larger positions
        
        ============================================================================
        PARAMETERS
        ============================================================================
        
        Args:
            df_src (pd.DataFrame): OHLCV DataFrame with columns:
                - 'open', 'high', 'low', 'close', 'volume'
                - Must also have 'ATRTrailingStop' column pre-calculated
                - Data should be sorted newest first (descending index)
                
            ema_period (int): Period for Exponential Moving Average
                - Default: 200 (long-term trend filter)
                - Used to confirm overall trend direction
                - Price above EMA = bullish context, below = bearish context
                
            retry (bool): Whether to retry on dependency errors
                - Default: True
                - When True, attempts to download missing template files
                
            confirmation_bars (int): Number of consecutive bars required
                - Options: 1, 2, or 3
                - 1: Quick signals, more noise (good for day trading)
                - 2: Balanced signals (recommended for swing trading)
                - 3: Conservative signals, less noise (for long-term)
                
            min_strength (int): Minimum signal strength required
                - Options: 1-5
                - 1: All signals (highest noise)
                - 2: Moderate signals (recommended)
                - 3: Strong signals only
                - 4-5: Very strong signals only (rare)
                
            volume_confirmation (bool): Require volume surge confirmation
                - Default: True
                - Buys: Volume > 20-day average * 1.2
                - Sells: Volume > 20-day average * 1.15
                - False: Don't use volume filter
                
            stock_name (str): Stock symbol for debugging
                - Default: "Unknown"
                - Used in fallback logging
        
        ============================================================================
        RETURNS
        ============================================================================
        
        Returns:
            tuple: (df, debug_info)
                df (pd.DataFrame): Original DataFrame with additional columns:
                
                    Signal Columns:
                    - Buy (bool): True when qualified buy signal detected
                    - Sell (bool): True when qualified sell signal detected
                    - Above (bool): EMA crossed above ATR Trailing Stop
                    - Below (bool): EMA crossed below ATR Trailing Stop
                    
                    Strength Columns:
                    - Signal_Strength (int): 1-5 strength score
                    - Buy_Confidence (int): 0-100 confidence for buy
                    - Sell_Confidence (int): 0-100 confidence for sell
                    
                    Confirmation Columns:
                    - Price_To_Stop_Ratio (float): Distance % from ATR stop
                    Positive = above stop (bullish)
                    Negative = below stop (bearish)
                    
                    - Volume_Buy_Surge (bool): Volume confirmation for buys
                    - Volume_Sell_Surge (bool): Volume confirmation for sells
                    - Buy_Consecutive (bool): Consecutive bars above stop
                    - Sell_Consecutive (bool): Consecutive bars below stop
                    
                    Trend Columns:
                    - Bullish_Trend (bool): RSI > 50 or price > SMA-20
                    - Bearish_Trend (bool): RSI < 50 or price < SMA-20
                    
                debug_info (dict): Empty dict (reserved for debug version)
        
        ============================================================================
        USAGE EXAMPLES
        ============================================================================
        
        Example 1: Basic daily screening (fast, moderate quality)
        >>> df, _ = screener.computeBuySellSignals(df, confirmation_bars=1, min_strength=2)
        >>> buy_signals = df[df["Buy"]]
        >>> sell_signals = df[df["Sell"]]
        
        Example 2: Conservative long-term screening (slow, high quality)
        >>> df, _ = screener.computeBuySellSignals(df, confirmation_bars=2, min_strength=3, 
        ...                                     volume_confirmation=True)
        >>> high_confidence_buys = df[(df["Buy"]) & (df["Buy_Confidence"] > 70)]
        
        Example 3: Get signals by strength
        >>> df, _ = screener.computeBuySellSignals(df)
        >>> strong_buys = df[(df["Buy"]) & (df["Signal_Strength"] >= 4)]
        >>> strong_sells = df[(df["Sell"]) & (df["Signal_Strength"] >= 4)]
        
        Example 4: Filter by confidence
        >>> df, _ = screener.computeBuySellSignals(df)
        >>> high_conf_buys = df[df["Buy_Confidence"] > 80]
        >>> high_conf_sells = df[df["Sell_Confidence"] > 80]
        
        Example 5: Use with ATR Trailing Stop for position management
        >>> df, _ = screener.computeBuySellSignals(df, confirmation_bars=2)
        >>> 
        >>> # Entry: First buy signal
        >>> entry = df[df["Buy"]].iloc[0]
        >>> 
        >>> # Exit: First sell signal after entry
        >>> exit = df[df.index > entry.name][df["Sell"]].iloc[0] if len(df[df["Sell"]]) > 0 else None
        
        Example 6: Backtesting strategy
        >>> df, _ = screener.computeBuySellSignals(df, confirmation_bars=1)
        >>> 
        >>> # Long entries
        >>> entries = df[df["Buy"]]
        >>> 
        >>> # Stop loss at ATR stop price
        >>> stops = entries["ATRTrailingStop"]
        >>> 
        >>> # Take profit at 2x ATR from entry
        >>> targets = entries["close"] + 2 * entries["xATR"]
        
        ============================================================================
        TROUBLESHOOTING
        ============================================================================
        
        No signals generated:
        - Check if 'ATRTrailingStop' column exists
        - Check if DataFrame has enough rows (min 20)
        - Try lowering min_strength to 1
        - Try setting confirmation_bars to 1
        - Set volume_confirmation to False
        
        Too many false signals:
        - Increase confirmation_bars to 2 or 3
        - Increase min_strength to 3
        - Enable volume_confirmation=True
        
        Missing sell signals:
        - Check if price is actually crossing below ATR stop
        - Verify DataFrame is sorted newest first
        - Check fallback implementation (VectorBT may not be available)
        
        Slow performance:
        - Reduce DataFrame size (keep last 100-200 bars)
        - Use confirmation_bars=1 for faster screening
        - Consider using the fallback implementation (no VectorBT)
        
        ============================================================================
        NOTES
        ============================================================================
        
        1. VectorBT is preferred but not required
        2. Fallback implementation works in all cases but may be less accurate
        3. ATRTrailingStop must be pre-calculated before calling this method
        4. DataFrame should be sorted newest first (index descending)
        5. For best results, use at least 100 bars of daily data
        """
        # Create a copy to avoid modifying the original DataFrame
        df = df_src.copy() if df_src is not None else None
        
        try:
            # =====================================================================
            # INPUT VALIDATION
            # =====================================================================
            if df is None or len(df) == 0:
                if self.default_logger:
                    self.default_logger.warning("computeBuySellSignals: Empty DataFrame provided")
                return df, {}
            
            # Ensure required columns exist
            required_cols = ['close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                if self.default_logger:
                    self.default_logger.warning(f"Missing required columns: {missing_cols}")
                return df, {}
            
            # Check if ATRTrailingStop column exists
            # Ensure ATRTrailingStop column exists (fallback calculation if missing)
            if 'ATRTrailingStop' not in df.columns:
                if self.default_logger:
                    self.default_logger.warning(f"ATRTrailingStop column missing, calculating fallback for {stock_name}")
                # Fallback: simple trailing stop based on close price
                df['ATRTrailingStop'] = df['close'] * 0.95  # 5% below close as simple stop
            
            # Initialize all signal columns with default values
            df["Above"] = False
            df["Below"] = False
            df["Buy"] = False
            df["Sell"] = False
            df["Signal_Strength"] = 0
            df["Buy_Confidence"] = 0
            df["Sell_Confidence"] = 0
            df["Price_To_Stop_Ratio"] = 0.0
            df["Buy_Consecutive"] = False
            df["Sell_Consecutive"] = False
            
            if volume_confirmation:
                df["Volume_Buy_Surge"] = False
                df["Volume_Sell_Surge"] = False
                df["Avg_Volume_20"] = 0.0
            
            # =====================================================================
            # VECTORBT-BASED SIGNAL COMPUTATION (Preferred)
            # =====================================================================
            vectorbt_available = False
            try:
                if Imports["vectorbt"]:
                    from vectorbt.indicators import MA as vbt
                    vectorbt_available = True
                    # if self.default_logger:
                    #     self.default_logger.debug("Using VectorBT for signal computation")
            except (ImportError, OSError, FileNotFoundError) as e:
                # Handle missing vectorbt or template files
                # Try to download missing template files
                try:
                    import os
                    outputFolder = None
                    if hasattr(e, 'filename') and e.filename:
                        try:
                            outputFolder = os.sep.join(e.filename.split(os.sep)[:-1])
                        except Exception:
                            pass
                    
                    if outputFolder is None:
                        # Default template folder
                        dirName = 'templates'
                        outputFolder = os.path.join(os.getcwd(), dirName)
                    
                    # Download missing template JSON files
                    self.downloadSaveTemplateJsons(outputFolderPath=outputFolder)
                    
                    if retry:
                        # Retry the import after downloading templates
                        if Imports["vectorbt"]:
                            from vectorbt.indicators import MA as vbt
                            vectorbt_available = True
                            # if self.default_logger:
                            #     self.default_logger.debug("VectorBT loaded after template download")
                except Exception as ex:
                    if self.default_logger:
                        self.default_logger.debug(f"Error recovering from missing dependencies: {ex}", exc_info=True)
            
            if vectorbt_available:
                # if self.default_logger:
                #     self.default_logger.debug(f"Processing {len(df)} rows with VectorBT")
                
                # =================================================================
                # VECTORBT IMPLEMENTATION
                # =================================================================
                if df is not None and len(df) > 0:
                    # Calculate EMA for trend filter
                    ema = vbt.run(df["close"], 1, short_name='EMA', ewm=True)
                    
                    # Basic crossover detection (most reliable signals)
                    df["Above"] = ema.ma_crossed_above(df["ATRTrailingStop"])
                    df["Below"] = ema.ma_crossed_below(df["ATRTrailingStop"])
                    
                    # Only proceed with confirmations if we have enough data
                    if len(df) >= confirmation_bars + 1:
                        # Calculate price distance from ATR stop (as percentage)
                        atr_stop = df["ATRTrailingStop"]
                        df["Price_To_Stop_Ratio"] = (df["close"] - atr_stop) / atr_stop.replace(0, np.nan)
                        df["Price_To_Stop_Ratio"] = df["Price_To_Stop_Ratio"].fillna(0).clip(-0.5, 0.5)
                        
                        # ============ VOLUME CONFIRMATION ============
                        if volume_confirmation and 'volume' in df.columns:
                            # Calculate 20-day average volume
                            df["Avg_Volume_20"] = df["volume"].rolling(window=20, min_periods=10).mean()
                            df["Avg_Volume_20"] = df["Avg_Volume_20"].fillna(df["volume"].mean())
                            
                            # Volume surge for buys (accumulation)
                            df["Volume_Buy_Surge"] = df["volume"] > df["Avg_Volume_20"] * 1.2
                            
                            # Volume surge for sells (distribution)
                            df["Volume_Sell_Surge"] = df["volume"] > df["Avg_Volume_20"] * 1.15
                        
                        # ============ TREND STRENGTH INDICATORS ============
                        if 'RSI' in df.columns:
                            df["Bullish_Trend"] = df["RSI"] > 50
                            df["Bearish_Trend"] = df["RSI"] < 50
                            df["RSI_Momentum"] = df["RSI"] - df["RSI"].shift(1)
                            df["RSI_Momentum_Positive"] = df["RSI_Momentum"] > 0
                            df["RSI_Momentum_Negative"] = df["RSI_Momentum"] < 0
                        else:
                            # Use SMA-20 as fallback trend indicator
                            df["SMA_20"] = df["close"].rolling(window=20, min_periods=10).mean()
                            df["SMA_20"] = df["SMA_20"].fillna(method='bfill').fillna(df["close"])
                            df["Bullish_Trend"] = df["close"] > df["SMA_20"]
                            df["Bearish_Trend"] = df["close"] < df["SMA_20"]
                            df["Price_Momentum"] = df["close"] > df["close"].shift(1)
                        
                        # ============ CONSECUTIVE BAR CONFIRMATION ============
                        # Buy confirmation: price staying above ATR stop for X consecutive bars
                        above_stop = df["close"] > df["ATRTrailingStop"]
                        df["Buy_Consecutive"] = above_stop.rolling(
                            window=confirmation_bars, 
                            min_periods=confirmation_bars
                        ).sum() >= confirmation_bars
                        
                        # Sell confirmation: price staying below ATR stop for X consecutive bars
                        below_stop = df["close"] < df["ATRTrailingStop"]
                        df["Sell_Consecutive"] = below_stop.rolling(
                            window=confirmation_bars, 
                            min_periods=confirmation_bars
                        ).sum() >= confirmation_bars
                        
                        # ============ CALCULATE BUY SIGNAL STRENGTH (1-5) ============
                        buy_condition = above_stop
                        if buy_condition.any():
                            # Base strength starts at 1
                            buy_strength = pd.Series(1, index=df.index)
                            
                            # Add points for volume confirmation
                            if volume_confirmation:
                                buy_strength += df["Volume_Buy_Surge"].astype(int)
                            
                            # Add points for trend confirmation
                            if 'Bullish_Trend' in df.columns:
                                buy_strength += df["Bullish_Trend"].astype(int)
                            
                            # Add points for RSI momentum (rising RSI)
                            if 'RSI_Momentum_Positive' in df.columns:
                                buy_strength += df["RSI_Momentum_Positive"].astype(int)
                            
                            # Add points based on price distance from ATR stop (0-2)
                            distance_points = np.clip(df["Price_To_Stop_Ratio"] * 20, 0, 2).astype(int)
                            buy_strength += distance_points
                            
                            # Cap at 5 and store
                            df.loc[buy_condition, "Signal_Strength"] = np.clip(buy_strength, 1, 5)
                        
                        # ============ CALCULATE SELL SIGNAL STRENGTH (1-5) ============
                        sell_condition = below_stop
                        if sell_condition.any():
                            # Base strength starts at 1
                            sell_strength = pd.Series(1, index=df.index)
                            
                            # Add points for volume confirmation on sell
                            if volume_confirmation:
                                sell_strength += df["Volume_Sell_Surge"].astype(int)
                            
                            # Add points for bearish trend confirmation
                            if 'Bearish_Trend' in df.columns:
                                sell_strength += df["Bearish_Trend"].astype(int)
                            
                            # Add points for RSI momentum (falling RSI)
                            if 'RSI_Momentum_Negative' in df.columns:
                                sell_strength += df["RSI_Momentum_Negative"].astype(int)
                            
                            # Add points based on price distance (negative distance)
                            distance_points = np.clip(-df["Price_To_Stop_Ratio"] * 20, 0, 2).astype(int)
                            sell_strength += distance_points
                            
                            # Cap at 5 and store
                            df.loc[sell_condition, "Signal_Strength"] = np.clip(sell_strength, 1, 5)
                        
                        # ============ FINAL SIGNALS WITH CONFIRMATION THRESHOLDS ============
                        # Buy signals: price above stop AND strength >= min_strength AND consecutive confirmation
                        df["Buy"] = (buy_condition & 
                                    (df["Signal_Strength"] >= min_strength) & 
                                    (df["Buy_Consecutive"] if confirmation_bars > 1 else True))

                        # Sell signals: price below stop AND strength >= min_strength AND consecutive confirmation
                        df["Sell"] = (sell_condition & 
                                    (df["Signal_Strength"] >= min_strength) & 
                                    (df["Sell_Consecutive"] if confirmation_bars > 1 else True))

                        # Override with strong crossover signals (most reliable - always valid)
                        df.loc[df["Above"] == True, "Buy"] = True
                        df.loc[df["Below"] == True, "Sell"] = True

                        # ============ ADDITIONAL SELL SIGNALS FOR BEARISH MARKET ============
                        # These provide sell signals even when ATR conditions aren't met
                        if confirmation_bars <= 2:
                            
                            # 1. Death Cross (50 SMA crosses below 200 SMA) - Strong sell signal
                            if "SMA" in df.columns and "LMA" in df.columns and len(df) > 2:
                                death_cross = (df["SMA"] < df["LMA"]) & (df["SMA"].shift(1) > df["LMA"].shift(1))
                                df.loc[death_cross & ~df["Sell"], "Sell"] = True
                                df.loc[death_cross & ~df["Sell"], "Signal_Strength"] = 4
                                df.loc[death_cross & ~df["Sell"], "Sell_Confidence"] = 85
                                if self.default_logger and (death_cross & ~df["Sell"]).any():
                                    self.default_logger.debug("Added death cross sell signals")
                            
                            # 2. Close below 200 SMA (major breakdown) - Moderate sell signal
                            if "LMA" in df.columns:
                                below_200 = (df["close"] < df["LMA"]) & (df["close"].shift(1) > df["LMA"].shift(1))
                                df.loc[below_200 & ~df["Sell"], "Sell"] = True
                                df.loc[below_200 & ~df["Sell"], "Signal_Strength"] = 3
                                df.loc[below_200 & ~df["Sell"], "Sell_Confidence"] = 75
                                if self.default_logger and (below_200 & ~df["Sell"]).any():
                                    self.default_logger.debug("Added below 200MA sell signals")
                            
                            # 3. 5-day EMA crossing below 20-day EMA (short-term bearish)
                            if len(df) > 20:
                                ema5 = df["close"].ewm(span=5, adjust=False).mean()
                                ema20 = df["close"].ewm(span=20, adjust=False).mean()
                                ema_cross_below = (ema5 < ema20) & (ema5.shift(1) > ema20.shift(1))
                                df.loc[ema_cross_below & ~df["Sell"], "Sell"] = True
                                df.loc[ema_cross_below & ~df["Sell"], "Signal_Strength"] = 2
                                df.loc[ema_cross_below & ~df["Sell"], "Sell_Confidence"] = 55
                                if self.default_logger and (ema_cross_below & ~df["Sell"]).any():
                                    self.default_logger.debug("Added EMA5/20 cross sell signals")
                            
                            # 4. RSI overbought (bearish signal)
                            if "RSI" in df.columns:
                                rsi_overbought = df["RSI"] > 70
                                df.loc[rsi_overbought & ~df["Sell"], "Sell"] = True
                                df.loc[rsi_overbought & ~df["Sell"], "Signal_Strength"] = 2
                                df.loc[rsi_overbought & ~df["Sell"], "Sell_Confidence"] = 60
                                if self.default_logger and (rsi_overbought & ~df["Sell"]).any():
                                    self.default_logger.debug("Added RSI overbought sell signals")
                            
                            # 5. Price below 20 SMA (bearish)
                            if "SMA" in df.columns:
                                price_below_sma = df["close"] < df["SMA"]
                                df.loc[price_below_sma & ~df["Sell"], "Sell"] = True
                                df.loc[price_below_sma & ~df["Sell"], "Signal_Strength"] = 3
                                df.loc[price_below_sma & ~df["Sell"], "Sell_Confidence"] = 65
                                if self.default_logger and (price_below_sma & ~df["Sell"]).any():
                                    self.default_logger.debug("Added price below SMA sell signals")
                            
                            # 6. RSI downtrend with bearish divergence
                            if "RSI" in df.columns and len(df) > 5 and not df["Sell"].any():
                                # RSI falling from overbought (>70) to below 50
                                rsi_falling = (df["RSI"] < 50) & (df["RSI"].shift(1) >= 70)
                                df.loc[rsi_falling & ~df["Sell"], "Sell"] = True
                                df.loc[rsi_falling & ~df["Sell"], "Signal_Strength"] = 3
                                df.loc[rsi_falling & ~df["Sell"], "Sell_Confidence"] = 70
                                if self.default_logger and (rsi_falling & ~df["Sell"]).any():
                                    self.default_logger.debug("Added RSI falling from overbought sell signals")

                        # ============ CONFIDENCE SCORES (0-100) ============
                        # Buy confidence calculation
                        buy_mask = df["Buy"] == True
                        if buy_mask.any():
                            # Base confidence from signal strength (20-100)
                            base_confidence = df.loc[buy_mask, "Signal_Strength"] * 16
                            
                            # Add price distance contribution (0-30)
                            price_contribution = np.clip(df.loc[buy_mask, "Price_To_Stop_Ratio"] * 100, 0, 30)
                            
                            df.loc[buy_mask, "Buy_Confidence"] = np.clip(base_confidence + price_contribution, 0, 100)
                            
                            # Boost confidence for crossover signals (additional 20 points)
                            df.loc[buy_mask & (df["Above"] == True), "Buy_Confidence"] = np.clip(
                                df.loc[buy_mask & (df["Above"] == True), "Buy_Confidence"] + 20, 0, 100
                            )
                        
                        # Sell confidence calculation
                        sell_mask = df["Sell"] == True
                        if sell_mask.any():
                            # Base confidence from signal strength (20-100)
                            base_confidence = df.loc[sell_mask, "Signal_Strength"] * 16
                            
                            # Add price distance contribution (0-30)
                            price_contribution = np.clip(-df.loc[sell_mask, "Price_To_Stop_Ratio"] * 100, 0, 30)
                            
                            df.loc[sell_mask, "Sell_Confidence"] = np.clip(base_confidence + price_contribution, 0, 100)
                            
                            # Boost confidence for crossover signals (additional 20 points)
                            df.loc[sell_mask & (df["Below"] == True), "Sell_Confidence"] = np.clip(
                                df.loc[sell_mask & (df["Below"] == True), "Sell_Confidence"] + 20, 0, 100
                            )
                        
                    else:
                        # Insufficient data for confirmations - use basic signals
                        if self.default_logger:
                            self.default_logger.debug(f"Insufficient data ({len(df)} rows) for confirmations, using basic signals")
                        
                        df["Buy"] = (df["close"] > df["ATRTrailingStop"]) & (df["Above"] == True)
                        df["Sell"] = (df["close"] < df["ATRTrailingStop"]) & (df["Below"] == True)
                        df["Buy_Confidence"] = 50 if df["Buy"].any() else 0
                        df["Sell_Confidence"] = 50 if df["Sell"].any() else 0
                        df["Signal_Strength"] = 2  # Moderate default
                
                    # if self.default_logger:
                    #     buy_count = df["Buy"].sum() if "Buy" in df.columns else 0
                    #     sell_count = df["Sell"].sum() if "Sell" in df.columns else 0
                    #     self.default_logger.debug(f"VectorBT results: {buy_count} buys, {sell_count} sells")
            
            else:
                # =====================================================================
                # FALLBACK IMPLEMENTATION (Without VectorBT)
                # =====================================================================
                if self.default_logger:
                    self.default_logger.warning("VectorBT not available. Using fallback calculation.")
                
                if df is not None and len(df) > 0:
                    # Calculate EMA using pandas (for trend filter)
                    if ema_period > 1:
                        df["EMA"] = df["close"].ewm(span=ema_period, adjust=False, min_periods=1).mean()
                    else:
                        df["EMA"] = df["close"]
                    
                    # ============ PROPER CROSSOVER DETECTION ============
                    # Buy signal: price crosses ABOVE ATR stop (was below, now above)
                    # This is the most reliable signal type
                    df["Above"] = (df["close"] > df["ATRTrailingStop"]) & \
                                (df["close"].shift(1) <= df["ATRTrailingStop"].shift(1))
                    
                    # Sell signal: price crosses BELOW ATR stop (was above, now below)
                    df["Below"] = (df["close"] < df["ATRTrailingStop"]) & \
                                (df["close"].shift(1) >= df["ATRTrailingStop"].shift(1))
                    
                    # Fill NaN values with False
                    df["Above"] = df["Above"].fillna(False)
                    df["Below"] = df["Below"].fillna(False)
                    
                    # ============ VOLUME CONFIRMATION (if available) ============
                    if volume_confirmation and 'volume' in df.columns and len(df) >= 20:
                        df["Avg_Volume_20"] = df["volume"].rolling(window=20, min_periods=10).mean()
                        df["Avg_Volume_20"] = df["Avg_Volume_20"].fillna(df["volume"].mean())
                        df["Volume_Buy_Surge"] = df["volume"] > df["Avg_Volume_20"] * 1.2
                        df["Volume_Sell_Surge"] = df["volume"] > df["Avg_Volume_20"] * 1.15
                    else:
                        # Create dummy columns if volume not available
                        df["Volume_Buy_Surge"] = True
                        df["Volume_Sell_Surge"] = True
                        df["Avg_Volume_20"] = 0
                    
                    # ============ PRICE MOMENTUM for signal quality ============
                    if len(df) >= 2:
                        df["Price_Momentum"] = df["close"] > df["close"].shift(1)
                        df["Price_Momentum"] = df["Price_Momentum"].fillna(False)
                    else:
                        df["Price_Momentum"] = True
                    
                    # ============ GENERATE BUY SIGNALS ============
                    # Buy conditions:
                    # 1. Price is above ATR stop (trend strength)
                    price_above_stop = df["close"] > df["ATRTrailingStop"]
                    
                    # 2. Crossover detected OR price consistently above stop
                    buy_condition = df["Above"] | (price_above_stop & df["Above"].shift(1).fillna(False))
                    
                    # 3. Optional volume confirmation
                    if volume_confirmation and 'Volume_Buy_Surge' in df.columns:
                        buy_condition = buy_condition & df["Volume_Buy_Surge"]
                    
                    # 4. Price momentum (must be positive for buys)
                    buy_condition = buy_condition & (df["Price_Momentum"] == True)
                    
                    # Apply min_strength threshold for buys (in fallback, strength is binary)
                    if min_strength <= 2:
                        df["Buy"] = buy_condition
                    else:
                        # Require additional confirmation for higher strength
                        df["Buy"] = buy_condition & (df["Above"] == True)
                    
                    # ============ GENERATE SELL SIGNALS ============
                    # Sell conditions:
                    # 1. Price is below ATR stop (trend weakness)
                    price_below_stop = df["close"] < df["ATRTrailingStop"]
                    
                    # 2. Crossover detected OR price consistently below stop
                    sell_condition = df["Below"] | (price_below_stop & df["Below"].shift(1).fillna(False))
                    
                    # 3. Optional volume confirmation
                    if volume_confirmation and 'Volume_Sell_Surge' in df.columns:
                        sell_condition = sell_condition & df["Volume_Sell_Surge"]
                    
                    # 4. Price momentum (must be negative for sells)
                    sell_condition = sell_condition & (df["Price_Momentum"] == False)
                    
                    # Apply min_strength threshold for sells
                    if min_strength <= 2:
                        df["Sell"] = sell_condition
                    else:
                        df["Sell"] = sell_condition & (df["Below"] == True)
                    
                    # ============ SET CONFIDENCE AND STRENGTH ============
                    # For fallback, use simplified confidence based on signal type
                    df["Signal_Strength"] = 2  # Default moderate strength
                    df["Buy_Confidence"] = 0
                    df["Sell_Confidence"] = 0
                    
                    # Calculate confidence for buys
                    if df["Buy"].any():
                        # Base confidence 60, add volume surge points if available
                        if volume_confirmation and 'Volume_Buy_Surge' in df.columns:
                            df.loc[df["Buy"], "Buy_Confidence"] = 60 + (df.loc[df["Buy"], "Volume_Buy_Surge"].astype(int) * 10)
                        else:
                            df.loc[df["Buy"], "Buy_Confidence"] = 60
                        
                        # Boost confidence for crossover signals
                        df.loc[df["Buy"] & (df["Above"] == True), "Buy_Confidence"] += 20
                        
                        # Cap at 100
                        df["Buy_Confidence"] = np.clip(df["Buy_Confidence"], 0, 100)
                    
                    # Calculate confidence for sells
                    if df["Sell"].any():
                        # Base confidence 60, add volume surge points if available
                        if volume_confirmation and 'Volume_Sell_Surge' in df.columns:
                            df.loc[df["Sell"], "Sell_Confidence"] = 60 + (df.loc[df["Sell"], "Volume_Sell_Surge"].astype(int) * 10)
                        else:
                            df.loc[df["Sell"], "Sell_Confidence"] = 60
                        
                        # Boost confidence for crossover signals
                        df.loc[df["Sell"] & (df["Below"] == True), "Sell_Confidence"] += 20
                        
                        # Cap at 100
                        df["Sell_Confidence"] = np.clip(df["Sell_Confidence"], 0, 100)
                    
                    # Enhance signal strength based on crossing type
                    if df["Buy"].any():
                        df.loc[df["Buy"] & (df["Above"] == True), "Signal_Strength"] = 3
                    if df["Sell"].any():
                        df.loc[df["Sell"] & (df["Below"] == True), "Signal_Strength"] = 3
                    
                    # if self.default_logger:
                    #     buy_count = df["Buy"].sum() if "Buy" in df.columns else 0
                    #     sell_count = df["Sell"].sum() if "Sell" in df.columns else 0
                    #     self.default_logger.debug(f"Fallback results: {buy_count} buys, {sell_count} sells for {stock_name}")
            
        except KeyboardInterrupt:
            # Re-raise keyboard interrupt for proper handling
            raise KeyboardInterrupt
            
        except Exception as e:
            if self.default_logger:
                self.default_logger.error(f"computeBuySellSignals error: {e}", exc_info=True)
            
            # Ensure all expected columns exist even on error
            expected_cols = ['Buy', 'Sell', 'Buy_Confidence', 'Sell_Confidence', 'Signal_Strength',
                            'Above', 'Below', 'Price_To_Stop_Ratio']
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = False if col in ['Buy', 'Sell', 'Above', 'Below'] else 0
        
        # =========================================================================
        # FINAL CLEANUP AND VALIDATION
        # =========================================================================
        if df is not None:
            # Ensure no NaN values in boolean signal columns
            for col in ['Buy', 'Sell', 'Above', 'Below']:
                if col in df.columns:
                    df[col] = df[col].fillna(False)
            
            # Ensure no NaN values in numeric columns
            for col in ['Buy_Confidence', 'Sell_Confidence', 'Signal_Strength']:
                if col in df.columns:
                    df[col] = df[col].fillna(0)
        
        # Return tuple with empty debug info
        return df, {}

    # =============================================================================
    # COMPUTE SIGNALS WITH SCORES
    # =============================================================================

    def computeBuySellSignalsWithScores(self, df, ema_period=200, retry=True,stock_name="Unknown"):
        """
        Enhanced version that returns detailed signal scores for ranking and filtering.
        
        This method provides granular scoring (0-100) for both buy and sell signals,
        allowing you to rank signals by strength and filter out weak signals.
        
        Key Features:
        -------------
        - Granular 0-100 scoring for both buy and sell signals
        - Multi-factor scoring: price distance, volume, trend, RSI momentum
        - Signal quality classification (HIGH/MEDIUM/LOW)
        - Ranking scores for portfolio construction
        - Perfect for quantitative analysis and strategy backtesting
        
        Scoring Factors (0-100 scale):
        -------------------------------
        - Price Distance (30%): How far price is from ATR stop
        - Volume Confirmation (25%): Volume surge confirmation
        - Trend Alignment (25%): RSI or SMA trend direction
        - Momentum (20%): Rate of change or RSI momentum
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with ATRTrailingStop column
            ema_period (int): EMA period for trend filter (default: 200)
            retry (bool): Whether to retry on errors (default: True)
        
        Returns:
            pd.DataFrame: Original DataFrame with additional columns:
                - Signal_Score (int): 0-100 composite score (higher = stronger)
                - Signal_Direction (str): "BUY", "SELL", or "NEUTRAL"
                - Confidence (str): "HIGH", "MEDIUM", or "LOW"
                - Buy_Rank (int): Rank of buy signals (1=strongest)
                - Sell_Rank (int): Rank of sell signals (1=strongest)
                - Score_Breakdown (dict): Individual factor scores
        
        When to Use:
        -----------
        - When you need to rank/prioritize multiple signals
        - For portfolio construction (take top N signals)
        - When you want to set confidence thresholds (e.g., only HIGH confidence)
        - For quantitative analysis and strategy optimization
        - When comparing signal strength across different stocks
        
        Example:
        --------
        >>> df = screener.computeBuySellSignalsWithScores(df)
        >>> # Get only high-confidence signals
        >>> high_confidence = df[df["Confidence"] == "HIGH"]
        >>> # Get top 10 strongest buy signals
        >>> top_buys = df[df["Signal_Direction"] == "BUY"].nlargest(10, "Signal_Score")
        """
        try:
            # First compute base signals
            df, _ = self.computeBuySellSignals(df, ema_period=ema_period, retry=retry, 
                                            confirmation_bars=1, volume_confirmation=True, stock_name=stock_name)
            
            if df is None or len(df) == 0:
                return df
            
            # Initialize score columns
            df["Signal_Score"] = 0
            df["Signal_Direction"] = "NEUTRAL"
            df["Confidence"] = "LOW"
            df["Buy_Rank"] = 0
            df["Sell_Rank"] = 0
            
            # =========================================================================
            # FACTOR 1: Price Distance Score (0-30 points)
            # =========================================================================
            # Price distance from ATR stop as percentage
            # Positive for buys, negative for sells
            price_ratio = df["Price_To_Stop_Ratio"] if "Price_To_Stop_Ratio" in df.columns else 0
            
            # Buy price score: 0-30 based on how far above ATR stop
            buy_mask = df["Buy"] == True
            if buy_mask.any():
                buy_price_score = np.clip(price_ratio * 100, 0, 30)
                df.loc[buy_mask, "Price_Score"] = buy_price_score
            
            # Sell price score: 0-30 based on how far below ATR stop
            sell_mask = df["Sell"] == True
            if sell_mask.any():
                sell_price_score = np.clip(-price_ratio * 100, 0, 30)
                df.loc[sell_mask, "Price_Score"] = sell_price_score
            
            # Default zero for non-signal rows
            if "Price_Score" not in df.columns:
                df["Price_Score"] = 0
            
            # =========================================================================
            # FACTOR 2: Volume Confirmation Score (0-25 points)
            # =========================================================================
            df["Volume_Score"] = 0
            
            if 'volume' in df.columns:
                avg_volume = df["volume"].rolling(window=20, min_periods=10).mean()
                avg_volume = avg_volume.fillna(df["volume"].mean())
                volume_ratio = df["volume"] / avg_volume.replace(0, np.nan).fillna(1)
                volume_ratio = volume_ratio.fillna(1)
                
                # Volume surge gives higher scores (capped at 25)
                volume_score = np.clip((volume_ratio - 1) * 25, 0, 25)
                df["Volume_Score"] = volume_score
                
                # Boost for volume confirmation on signals
                if buy_mask.any():
                    df.loc[buy_mask & (df["Volume_Buy_Surge"] if "Volume_Buy_Surge" in df.columns else False), "Volume_Score"] += 5
                if sell_mask.any():
                    df.loc[sell_mask & (df["Volume_Sell_Surge"] if "Volume_Sell_Surge" in df.columns else False), "Volume_Score"] += 5
                
                df["Volume_Score"] = np.clip(df["Volume_Score"], 0, 25)
            
            # =========================================================================
            # FACTOR 3: Trend Alignment Score (0-25 points)
            # =========================================================================
            df["Trend_Score"] = 0
            
            # Use RSI if available
            if 'RSI' in df.columns:
                rsi = df["RSI"].fillna(50)
                
                # Buy: RSI above 50 gives higher scores (max 25 at RSI=75)
                if buy_mask.any():
                    buy_trend_score = np.clip((rsi - 50) * 1, 0, 25)
                    df.loc[buy_mask, "Trend_Score"] = buy_trend_score
                
                # Sell: RSI below 50 gives higher scores (max 25 at RSI=25)
                if sell_mask.any():
                    sell_trend_score = np.clip((50 - rsi) * 1, 0, 25)
                    df.loc[sell_mask, "Trend_Score"] = sell_trend_score
            else:
                # Use SMA-20 as fallback
                sma_20 = df["close"].rolling(window=20, min_periods=10).mean()
                sma_20 = sma_20.fillna(method='bfill').fillna(df["close"])
                
                # Calculate percentage above/below SMA
                sma_distance = (df["close"] - sma_20) / sma_20.replace(0, np.nan).fillna(1)
                sma_distance = sma_distance.fillna(0)
                
                if buy_mask.any():
                    buy_trend_score = np.clip(sma_distance * 100, 0, 25)
                    df.loc[buy_mask, "Trend_Score"] = buy_trend_score
                
                if sell_mask.any():
                    sell_trend_score = np.clip(-sma_distance * 100, 0, 25)
                    df.loc[sell_mask, "Trend_Score"] = sell_trend_score
            
            # =========================================================================
            # FACTOR 4: Momentum Score (0-20 points)
            # =========================================================================
            df["Momentum_Score"] = 0
            
            # Calculate rate of change (1-day momentum)
            roc = df["close"].pct_change() * 100
            roc = roc.fillna(0)
            
            # Buy: Positive ROC gives higher scores
            if buy_mask.any():
                buy_momentum_score = np.clip(roc * 5, 0, 20)  # 4% move = 20 points
                df.loc[buy_mask, "Momentum_Score"] = buy_momentum_score
            
            # Sell: Negative ROC gives higher scores
            if sell_mask.any():
                sell_momentum_score = np.clip(-roc * 5, 0, 20)
                df.loc[sell_mask, "Momentum_Score"] = sell_momentum_score
            
            # Add RSI momentum if available
            if 'RSI_Momentum_Positive' in df.columns and buy_mask.any():
                df.loc[buy_mask & df["RSI_Momentum_Positive"], "Momentum_Score"] += 5
            if 'RSI_Momentum_Negative' in df.columns and sell_mask.any():
                df.loc[sell_mask & df["RSI_Momentum_Negative"], "Momentum_Score"] += 5
            
            df["Momentum_Score"] = np.clip(df["Momentum_Score"], 0, 20)
            
            # =========================================================================
            # COMPOSITE SIGNAL SCORE (0-100)
            # =========================================================================
            df["Signal_Score"] = (
                df["Price_Score"] +
                df["Volume_Score"] +
                df["Trend_Score"] +
                df["Momentum_Score"]
            )
            
            # Boost score for crossover signals (most reliable)
            if buy_mask.any():
                df.loc[buy_mask & (df["Above"] == True), "Signal_Score"] += 10
            if sell_mask.any():
                df.loc[sell_mask & (df["Below"] == True), "Signal_Score"] += 10
            
            # Cap at 100
            df["Signal_Score"] = np.clip(df["Signal_Score"], 0, 100)
            
            # =========================================================================
            # SIGNAL DIRECTION AND CONFIDENCE
            # =========================================================================
            # Determine signal direction
            df.loc[buy_mask, "Signal_Direction"] = "BUY"
            df.loc[sell_mask, "Signal_Direction"] = "SELL"
            
            # Set confidence levels based on score
            df.loc[df["Signal_Score"] >= 70, "Confidence"] = "HIGH"
            df.loc[(df["Signal_Score"] >= 40) & (df["Signal_Score"] < 70), "Confidence"] = "MEDIUM"
            df.loc[(df["Signal_Score"] > 0) & (df["Signal_Score"] < 40), "Confidence"] = "LOW"
            
            # Override confidence for crossover signals (always HIGH confidence)
            if buy_mask.any():
                df.loc[buy_mask & (df["Above"] == True), "Confidence"] = "HIGH"
            if sell_mask.any():
                df.loc[sell_mask & (df["Below"] == True), "Confidence"] = "HIGH"
            
            # =========================================================================
            # RANKING SCORES (for portfolio construction)
            # =========================================================================
            # Rank buy signals (1 = strongest)
            if buy_mask.any():
                buy_scores = df.loc[buy_mask, "Signal_Score"]
                df.loc[buy_mask, "Buy_Rank"] = buy_scores.rank(ascending=False, method='min').astype(int)
            
            # Rank sell signals (1 = strongest)
            if sell_mask.any():
                sell_scores = df.loc[sell_mask, "Signal_Score"]
                df.loc[sell_mask, "Sell_Rank"] = sell_scores.rank(ascending=False, method='min').astype(int)
            
            # =========================================================================
            # SCORE BREAKDOWN (for debugging and analysis)
            # =========================================================================
            df["Score_Breakdown"] = df.apply(
                lambda row: {
                    "price": round(row.get("Price_Score", 0), 1),
                    "volume": round(row.get("Volume_Score", 0), 1),
                    "trend": round(row.get("Trend_Score", 0), 1),
                    "momentum": round(row.get("Momentum_Score", 0), 1),
                    "total": round(row.get("Signal_Score", 0), 1)
                } if row.get("Signal_Score", 0) > 0 else {},
                axis=1
            )
            
        except Exception as e:
            if self.default_logger:
                self.default_logger.error(f"computeBuySellSignalsWithScores error: {e}", exc_info=True)
            
            # Ensure required columns exist
            for col in ['Signal_Score', 'Signal_Direction', 'Confidence']:
                if col not in df.columns:
                    df[col] = 0 if col == 'Signal_Score' else ("NEUTRAL" if col == 'Signal_Direction' else "LOW")
        
        return df


    # =============================================================================
    # COMPUTE BALANCED SIGNALS
    # =============================================================================

    def computeBalancedSignals(self, df, ema_period=200, 
                            buy_threshold=2, sell_threshold=2,
                            min_bars_between_signals=5,
                            min_bars_between_sell_signals=0,
                            volume_confirmation=True,
                            confirmation_bars=1,
                            min_strength=2,
                            stock_name="Unknown"):
        """
        Compute balanced Buy/Sell signals with configurable thresholds and cooldown periods.
        
        This method is optimized for active trading and provides balanced signals
        with configurable strength thresholds and cooldown periods to prevent overtrading.
        
        Key Features:
        -------------
        - Configurable strength thresholds for buy (2-5) and sell (2-5)
        - Cooldown period between same-type signals (prevents overtrading)
        - Conflicting signal resolution (ensures no simultaneous buy/sell)
        - Signal quality filtering based on score thresholds
        - Position management signals (entry, exit, hold)
        
        Args:
            df (pd.DataFrame): OHLCV DataFrame with ATRTrailingStop column
            ema_period (int): EMA period for trend filter (default: 200)
            buy_threshold (int): Minimum signal strength for buy (1-5, default: 2)
            sell_threshold (int): Minimum signal strength for sell (1-5, default: 2)
            min_bars_between_signals (int): Minimum bars between same-type signals (default: 5)
            min_bars_between_sell_signals (int): Minimum bars between sell signals (default: 0)
            volume_confirmation (bool): Whether to require volume confirmation (default: True)
        
        Returns:
            pd.DataFrame: Original DataFrame with additional columns:
                - Buy_Signal (bool): Filtered buy signal (qualified)
                - Sell_Signal (bool): Filtered sell signal (qualified)
                - Signal_Quality (str): "BUY", "SELL", "NEUTRAL", "HOLD"
                - Bars_Since_Buy (int): Bars since last buy signal
                - Bars_Since_Sell (int): Bars since last sell signal
                - Buy_Filtered (bool): Buy signal after cooldown
                - Sell_Filtered (bool): Sell signal after cooldown
                - Position (str): "LONG", "SHORT", or "NEUTRAL"
        
        When to Use:
        -----------
        - For active trading with risk management
        - When you want to avoid overtrading (cooldown periods)
        - For position sizing and portfolio management
        - When you need asymmetric thresholds (e.g., require stronger sell signals)
        - For strategy that tracks current position state
        
        Example:
        --------
        >>> df = screener.computeBalancedSignals(df, buy_threshold=2, sell_threshold=3, min_bars_between_signals=3)
        >>> # Get entry signals only
        >>> entries = df[(df["Buy_Signal"]) | (df["Sell_Signal"])]
        >>> # Check current position
        >>> current_position = df.iloc[-1]["Position"]
        """
        try:
            # First compute base signals
            df, _ = self.computeBuySellSignals(df, ema_period=ema_period, 
                                            confirmation_bars=confirmation_bars,
                                            min_strength=min_strength,
                                            volume_confirmation=volume_confirmation,
                                            stock_name=stock_name)
            
            if df is None or len(df) == 0:
                return df
            
            # Get signal strength (default to 0 if not present)
            signal_strength = df.get("Signal_Strength", pd.Series(0, index=df.index))
            
            # =========================================================================
            # QUALIFIED SIGNALS WITH THRESHOLDS
            # =========================================================================
            # Buy signals meeting minimum strength
            buy_qualified = df["Buy"] & (signal_strength >= buy_threshold)
            
            # Sell signals meeting minimum strength
            sell_qualified = df["Sell"] & (signal_strength >= sell_threshold)
            
            # =========================================================================
            # CONFLICTING SIGNAL RESOLUTION
            # =========================================================================
            # Detect conflicting signals (both buy and sell on same bar)
            conflicting = buy_qualified & sell_qualified
            
            if conflicting.any():
                if self.default_logger:
                    self.default_logger.debug(f"Resolving {conflicting.sum()} conflicting signals")
                
                # Resolve by taking the stronger signal
                # If equal strength, take the one that aligns with trend
                if 'Trend_Score' in df.columns:
                    # Use trend alignment to resolve
                    df.loc[conflicting, "Buy_Qualified_Temp"] = buy_qualified & (df["Trend_Score"] > 0)
                    df.loc[conflicting, "Sell_Qualified_Temp"] = sell_qualified & (df["Trend_Score"] < 0)
                    
                    # If still conflicting, use signal strength
                    still_conflicting = conflicting & df["Buy_Qualified_Temp"] & df["Sell_Qualified_Temp"]
                    if still_conflicting.any():
                        df.loc[still_conflicting, "Buy_Qualified_Temp"] = signal_strength > signal_strength.shift(1)
                        df.loc[still_conflicting, "Sell_Qualified_Temp"] = ~df["Buy_Qualified_Temp"]
                    
                    buy_qualified = df.get("Buy_Qualified_Temp", buy_qualified)
                    sell_qualified = df.get("Sell_Qualified_Temp", sell_qualified)
                else:
                    # Default: use signal strength only
                    buy_qualified = buy_qualified & (signal_strength >= signal_strength.shift(1))
                    sell_qualified = sell_qualified & (~buy_qualified)
            
            # =========================================================================
            # COOLDOWN PERIOD (Prevent overtrading)
            # =========================================================================
            # Calculate bars since last buy and sell signals
            df["Bars_Since_Buy"] = 0
            df["Bars_Since_Sell"] = 0
            
            # Convert signals to integer for cumulative counting
            buy_int = buy_qualified.astype(int)
            sell_int = sell_qualified.astype(int)
            
            # Cumulative counter since last signal
            df["Bars_Since_Buy"] = df.groupby(buy_int.cumsum()).cumcount()
            df["Bars_Since_Sell"] = df.groupby(sell_int.cumsum()).cumcount()
            
            # Apply cooldown filter
            df["Buy_Filtered"] = buy_qualified & (df["Bars_Since_Buy"] >= min_bars_between_signals)
            df["Sell_Filtered"] = sell_qualified & (df["Bars_Since_Sell"] >= min_bars_between_sell_signals)
            
            # Final signals
            df["Buy_Signal"] = df["Buy_Filtered"]
            df["Sell_Signal"] = df["Sell_Filtered"]
            
            # =========================================================================
            # SIGNAL QUALITY CLASSIFICATION
            # =========================================================================
            df["Signal_Quality"] = "NEUTRAL"
            df.loc[df["Buy_Signal"], "Signal_Quality"] = "BUY"
            df.loc[df["Sell_Signal"], "Signal_Quality"] = "SELL"
            
            # Add quality tiers based on confidence
            if "Confidence" in df.columns:
                df.loc[df["Buy_Signal"] & (df["Confidence"] == "HIGH"), "Signal_Quality"] = "STRONG_BUY"
                df.loc[df["Sell_Signal"] & (df["Confidence"] == "HIGH"), "Signal_Quality"] = "STRONG_SELL"
                df.loc[df["Buy_Signal"] & (df["Confidence"] == "MEDIUM"), "Signal_Quality"] = "BUY"
                df.loc[df["Sell_Signal"] & (df["Confidence"] == "MEDIUM"), "Signal_Quality"] = "SELL"
                df.loc[df["Buy_Signal"] & (df["Confidence"] == "LOW"), "Signal_Quality"] = "WEAK_BUY"
                df.loc[df["Sell_Signal"] & (df["Confidence"] == "LOW"), "Signal_Quality"] = "WEAK_SELL"
            
            # =========================================================================
            # POSITION STATE TRACKING
            # =========================================================================
            # Track current position (LONG/SHORT/NEUTRAL)
            df["Position"] = "NEUTRAL"
            
            # Initialize position state
            current_position = "NEUTRAL"
            position_start = 0
            
            for i in range(len(df)):
                if df.iloc[i]["Buy_Signal"]:
                    current_position = "LONG"
                    position_start = i
                elif df.iloc[i]["Sell_Signal"]:
                    current_position = "SHORT"
                    position_start = i
                
                df.iloc[i, df.columns.get_loc("Position")] = current_position
            
            # Add position duration
            df["Position_Bars"] = df.groupby((df["Position"] != df["Position"].shift()).cumsum()).cumcount() + 1
            
            # =========================================================================
            # EXIT SIGNALS (Additional safety)
            # =========================================================================
            df["Exit_Signal"] = False
            
            # Exit conditions:
            # 1. Opposite signal appears
            df["Exit_Signal"] = df["Exit_Signal"] | ((df["Position"] == "LONG") & df["Sell_Signal"])
            df["Exit_Signal"] = df["Exit_Signal"] | ((df["Position"] == "SHORT") & df["Buy_Signal"])
            
            # 2. Stop loss (if ATR stop is breached significantly)
            if "Price_To_Stop_Ratio" in df.columns:
                # 5% breach of ATR stop
                df["Exit_Signal"] = df["Exit_Signal"] | (
                    (df["Position"] == "LONG") & (df["Price_To_Stop_Ratio"] < -0.05)
                )
                df["Exit_Signal"] = df["Exit_Signal"] | (
                    (df["Position"] == "SHORT") & (df["Price_To_Stop_Ratio"] > 0.05)
                )
            
            # 3. Maximum holding period (20 bars)
            df["Exit_Signal"] = df["Exit_Signal"] | (df["Position_Bars"] > 20)
            
            # Override position on exit
            df.loc[df["Exit_Signal"], "Position"] = "NEUTRAL"
            
            # =========================================================================
            # ADDITIONAL METRICS
            # =========================================================================
            # Signal strength adjusted for thresholds
            df["Adjusted_Strength"] = signal_strength
            df.loc[df["Buy_Signal"], "Adjusted_Strength"] = signal_strength - buy_threshold + 1
            df.loc[df["Sell_Signal"], "Adjusted_Strength"] = signal_strength - sell_threshold + 1
            df["Adjusted_Strength"] = np.clip(df["Adjusted_Strength"], 0, 5)
            
            # Days since last signal (for position management)
            df["Days_Since_Signal"] = np.minimum(df["Bars_Since_Buy"], df["Bars_Since_Sell"])
            
            # Signal frequency (avoid over-concentration)
            df["Signal_Frequency"] = 0
            window = 20  # Look back 20 bars
            df["Signal_Frequency"] = (df["Buy_Signal"].rolling(window=window).sum() + 
                                    df["Sell_Signal"].rolling(window=window).sum())
            
            # Warning for high frequency (potential overfitting)
            if (df["Signal_Frequency"] > 5).any():
                if self.default_logger:
                    self.default_logger.warning("High signal frequency detected - consider increasing min_bars_between_signals")
            
        except Exception as e:
            if self.default_logger:
                self.default_logger.error(f"computeBalancedSignals error: {e}", exc_info=True)
            
            # Ensure essential columns exist
            essential_cols = ['Buy_Signal', 'Sell_Signal', 'Signal_Quality', 'Position']
            for col in essential_cols:
                if col not in df.columns:
                    df[col] = False if col in ['Buy_Signal', 'Sell_Signal'] else ("NEUTRAL" if col == 'Position' else "NEUTRAL")
        
        return df

    
    # Example of combining UTBot Alerts with RSI and ADX
    def custom_strategy(self,dataframe):
        dataframe = self.findBuySellSignalsFromATRTrailing(dataframe, key_value=2, atr_period=7, ema_period=100)
        
        # Calculate RSI and ADX
        rsi = pktalib.RSI(dataframe["close"])
        adx = pktalib.ADX(dataframe["high"], dataframe["low"], dataframe["close"])
        
        # Define conditions based on UTBot Alerts and additional indicators
        # ... (your custom conditions here)
        
        return dataframe

    def downloadSaveTemplateJsons(self, outputFolderPath=None):
        from PKDevTools.classes.Fetcher import fetcher
        import os
        if outputFolderPath is None:
            dirName = 'templates'
            outputFolder = os.path.join(os.getcwd(),dirName)
        else:
            outputFolder = outputFolderPath
        outputFolder = f"{outputFolder}{os.sep}" if not outputFolder.endswith(f"{os.sep}") else outputFolder
        if not os.path.isdir(outputFolder):
            os.makedirs(outputFolder, exist_ok=True)
        json1 = "https://raw.githubusercontent.com/polakowo/vectorbt/master/vectorbt/templates/dark.json"
        json2 = "https://raw.githubusercontent.com/polakowo/vectorbt/master/vectorbt/templates/light.json"
        json3 = "https://raw.githubusercontent.com/polakowo/vectorbt/master/vectorbt/templates/seaborn.json"
        fileURLs = [json1,json2,json3]
        fileFetcher = fetcher()
        from PKDevTools.classes.Utils import random_user_agent
        for url in fileURLs:
            try:
                path = os.path.join(outputFolder,url.split("/")[-1])
                if not os.path.exists(path):
                    # if self.shouldLog:
                    #     self.default_logger.debug(f"Fetching {url} to keep at {path}")
                    resp = fileFetcher.fetchURL(url=url,trial=3,timeout=5,headers={'user-agent': f'{random_user_agent()}'})
                    if resp is not None and resp.status_code == 200:
                        with open(path, "w") as f:
                            f.write(resp.text)
                # else:
                #     if self.shouldLog:
                #         self.default_logger.debug(f"Already exists: {path}")
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                # if self.shouldLog:
                #     self.default_logger.debug(e, exc_info=True)
                continue

    # Find stocks that have broken through 52 week high with quality confirmation
    def find52WeekHighBreakout(self, df, screenDict=None, saveDict=None):
        """
        Identify high-quality 52-week high breakout patterns.
        
        A genuine 52-week high breakout should have:
        1. Price closing above previous 52-week high (not just intraday spike)
        2. Above-average volume confirming institutional interest
        3. Proper base/consolidation before breakout
        4. Not already overextended
        5. Strong relative strength
        
        Args:
            df: DataFrame with OHLCV data (latest first)
            screenDict: Optional dict for output formatting  
            saveDict: Optional dict for saving results
        
        Returns:
            bool: True if quality 52-week high breakout detected
        """
        if df is None or len(df) == 0:
            return False
        
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        
        # Need at least 260 days (52 weeks * 5 days) of data
        if len(data) < 260:
            return False
        
        # Ensure data is sorted with most recent first
        if not data.empty and hasattr(data.index, 'sort_values'):
            try:
                data = data.sort_index(ascending=False)
            except:
                pass
        
        one_week = 5
        week_52 = 50 * one_week  # 250 trading days (approx 52 weeks)
        
        today = data.iloc[0]
        
        # =============================================================
        # STEP 1: GET 52-WEEK DATA (excluding today)
        # =============================================================
        historical_data = data.iloc[1:week_52 + 1]  # Last 52 weeks excluding today
        previous_52_week_high = historical_data["high"].max()
        previous_52_week_close_high = historical_data["close"].max()
        
        if previous_52_week_high == 0:
            return False
        
        # =============================================================
        # STEP 2: PRIMARY BREAKOUT CONDITIONS
        # =============================================================
        
        # Condition 1: Close above previous 52-week high (more reliable than intraday high)
        close_breakout = today["close"] > previous_52_week_high
        
        # Alternative: Allow high breakout if close is very close (within 0.5%)
        high_breakout = today["high"] > previous_52_week_high
        close_near_high = (today["close"] / previous_52_week_high) > 0.995 if previous_52_week_high > 0 else False
        
        price_breakout = close_breakout or (high_breakout and close_near_high)
        
        if not price_breakout:
            return False
        
        # =============================================================
        # STEP 3: VOLUME CONFIRMATION (Critical for breakouts)
        # =============================================================
        
        # Calculate volume averages
        avg_volume_20 = data.iloc[1:21]["volume"].mean() if len(data) > 20 else 0
        avg_volume_50 = data.iloc[1:51]["volume"].mean() if len(data) > 50 else 0
        avg_volume_10 = data.iloc[1:11]["volume"].mean() if len(data) > 10 else 0
        
        # Volume should be significantly above average on breakout day
        volume_ratio_vs_20 = today["volume"] / avg_volume_20 if avg_volume_20 > 0 else 1
        volume_ratio_vs_50 = today["volume"] / avg_volume_50 if avg_volume_50 > 0 else 1
        volume_ratio_vs_10 = today["volume"] / avg_volume_10 if avg_volume_10 > 0 else 1
        
        # Quality breakout needs volume at least 1.5x the 50-day average
        volume_confirmation = (
            volume_ratio_vs_50 >= 1.5 or 
            (volume_ratio_vs_20 >= 1.3 and today["volume"] > 100000)  # For liquid stocks
        )
        
        # =============================================================
        # STEP 4: CONSOLIDATION/BASE CHECK (Avoid extended moves)
        # =============================================================
        
        # Check if stock has been consolidating near highs (not already extended)
        days_to_check = min(60, len(historical_data))
        recent_highs = historical_data["high"].iloc[:days_to_check]
        recent_high_max = recent_highs.max()
        
        # Calculate how close recent prices are to 52-week high
        # A good setup has price within 10-15% of 52-week high before breakout
        price_proximity = (previous_52_week_high - historical_data["close"].iloc[0]) / previous_52_week_high if previous_52_week_high > 0 else 1
        
        # Stock should be within 20% of 52-week high (not too far down)
        consolidation_check = price_proximity <= 0.20
        
        # Check for proper base (at least 4 weeks of consolidation)
        # Look for tight trading range in last 20 days
        last_20_days = historical_data.iloc[:20]
        if len(last_20_days) >= 20:
            price_range_pct = (last_20_days["high"].max() - last_20_days["low"].min()) / last_20_days["low"].min() * 100
            tight_base = price_range_pct <= 15  # Less than 15% range indicates consolidation
        else:
            tight_base = True
        
        # =============================================================
        # STEP 5: RELATIVE STRENGTH CHECK
        # =============================================================
        
        # Stock should show strength relative to its own history
        # Check if stock is making higher highs recently
        last_10_highs = historical_data["high"].iloc[:10]
        higher_highs_trend = all(
            last_10_highs.iloc[i] > last_10_highs.iloc[i+1] 
            for i in range(len(last_10_highs) - 1)
        ) if len(last_10_highs) >= 2 else False
        
        # Check RSI if available (should be strong but not extremely overbought)
        rsi_value = None
        if 'RSI' in data.columns:
            rsi_value = data['RSI'].iloc[0]
        else:
            # Quick RSI calculation
            from pkscreener.classes.Pktalib import pktalib
            rsi_series = pktalib.RSI(data["close"], timeperiod=14)
            rsi_value = rsi_series.iloc[0] if len(rsi_series) > 0 else None
        
        rsi_ok = rsi_value is None or (55 <= rsi_value <= 80)  # Strong but not extreme overbought
        
        # =============================================================
        # STEP 6: CANDLE QUALITY CHECK
        # =============================================================
        
        # Bullish candle (close > open)
        is_bullish = today["close"] > today["open"]
        
        # Close in top 40% of daily range (buyer control)
        daily_range = today["high"] - today["low"]
        if daily_range > 0:
            close_position = (today["close"] - today["low"]) / daily_range
            strong_close = close_position > 0.40
        else:
            strong_close = False
        
        # Check if it's a fresh breakout (not already up huge today)
        intraday_move = (today["high"] - today["low"]) / today["low"] * 100 if today["low"] > 0 else 0
        not_too_extended = intraday_move <= 7  # Less than 7% intraday range
        
        # =============================================================
        # STEP 7: RESISTANCE CHECK (No prior resistance above)
        # =============================================================
        
        # Look for any higher highs in the dataset (ensures it's truly 52-week)
        all_time_high = data["high"].max()
        is_all_time_high = today["high"] >= all_time_high - (all_time_high * 0.001) if all_time_high > 0 else False
        
        # =============================================================
        # STEP 8: FINAL QUALITY SCORING
        # =============================================================
        
        # Primary conditions (must have)
        primary_conditions = [
            price_breakout,
            volume_confirmation,
            consolidation_check,
            is_bullish or strong_close  # Either condition is acceptable
        ]
        
        # Secondary conditions (at least 2 of 3)
        secondary_conditions = [
            tight_base,
            higher_highs_trend or rsi_ok,  # Either strength indicator
            not_too_extended
        ]
        
        secondary_score = sum(secondary_conditions)
        
        is_quality_breakout = all(primary_conditions) and secondary_score >= 2
        
        # =============================================================
        # STEP 9: STORE RESULTS (if dictionaries provided)
        # =============================================================
        
        if screenDict is not None and saveDict is not None and is_quality_breakout:
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            
            # Build breakout description
            breakout_type = "ATH" if is_all_time_high else "52WH"
            volume_multiple = round(volume_ratio_vs_50, 1) if volume_ratio_vs_50 > 0 else 1
            
            breakout_details = f"{breakout_type}-BO (H:{previous_52_week_high:.2f}, V:{volume_multiple}x)"
            
            if close_breakout:
                breakout_details += " [Close]"
            
            screenDict["Pattern"] = saved[0] + colorText.GREEN + breakout_details + colorText.END
            saveDict["Pattern"] = saved[1] + breakout_details
            
            # Store additional metrics for sorting
            saveDict["BreakoutStrength"] = volume_multiple
            saveDict["BreakoutType"] = breakout_type
        
        return is_quality_breakout


    # Complementary method: Find stocks approaching 52-week high (pre-breakout)
    def findApproaching52WeekHigh(self, df, screenDict=None, saveDict=None, proximity_pct=5):
        """
        Find stocks approaching 52-week high (setups for potential breakout).
        
        Useful for finding candidates before the actual breakout.
        
        Args:
            df: DataFrame with OHLCV data (latest first)
            screenDict: Optional dict for output formatting
            saveDict: Optional dict for saving results
            proximity_pct: How close to 52-week high (default 5%)
        
        Returns:
            bool: True if stock is approaching 52-week high with good setup
        """
        if df is None or len(df) < 250:
            return False
        
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        
        if not data.empty and hasattr(data.index, 'sort_values'):
            try:
                data = data.sort_index(ascending=False)
            except:
                pass
        
        one_week = 5
        week_52 = 50 * one_week
        
        today = data.iloc[0]
        historical_data = data.iloc[1:week_52 + 1]
        previous_52_week_high = historical_data["high"].max()
        
        if previous_52_week_high == 0:
            return False
        
        # Calculate distance to 52-week high
        distance_to_high = (previous_52_week_high - today["close"]) / previous_52_week_high * 100
        
        # Within specified proximity
        is_approaching = 0 <= distance_to_high <= proximity_pct
        
        if not is_approaching:
            return False
        
        # Check for constructive consolidation (tight range)
        last_20_days = historical_data.iloc[:20]
        if len(last_20_days) >= 20:
            price_range_pct = (last_20_days["high"].max() - last_20_days["low"].min()) / last_20_days["low"].min() * 100
            tight_consolidation = price_range_pct <= 10  # Very tight for pre-breakout
        else:
            tight_consolidation = True
        
        # Volume should be drying up (accumulation phase)
        avg_volume_50 = historical_data["volume"].iloc[:50].mean() if len(historical_data) >= 50 else 0
        volume_contraction = today["volume"] < avg_volume_50 * 0.8 if avg_volume_50 > 0 else True
        
        # Above key moving averages
        sma_50 = historical_data["close"].iloc[:50].mean() if len(historical_data) >= 50 else 0
        sma_200 = historical_data["close"].iloc[:200].mean() if len(historical_data) >= 200 else 0
        above_mas = today["close"] > sma_50 > sma_200 if sma_50 > 0 and sma_200 > 0 else False
        
        quality_setup = tight_consolidation and volume_contraction and above_mas
        
        if screenDict is not None and saveDict is not None and quality_setup:
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            setup_details = f"Approaching-52WH ({distance_to_high:.1f}%)"
            screenDict["Pattern"] = saved[0] + colorText.WARN + setup_details + colorText.END
            saveDict["Pattern"] = saved[1] + setup_details
        
        return quality_setup

    #@measure_time
    # Find stocks' 52 week high/low.
    def find52WeekHighLow(self, df, saveDict, screenDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        week_52 = one_week * 50  # Considering holidays etc as well of 10 days
        full52Week = data.head(week_52 + 1).tail(week_52+1)
        recentHigh = data.head(1)["high"].iloc[0]
        recentLow = data.head(1)["low"].iloc[0]
        full52WeekHigh = full52Week["high"].max()
        full52WeekLow = full52Week["low"].min()

        saveDict["52Wk-H"] = "{:.2f}".format(full52WeekHigh)
        saveDict["52Wk-L"] = "{:.2f}".format(full52WeekLow)
        if recentHigh >= full52WeekHigh:
            highColor = colorText.GREEN
        elif recentHigh >= 0.9 * full52WeekHigh:
            highColor = colorText.WARN
        else:
            highColor = colorText.FAIL
        if recentLow <= full52WeekLow:
            lowColor = colorText.FAIL
        elif recentLow <= 1.1 * full52WeekLow:
            lowColor = colorText.WARN
        else:
            lowColor = colorText.GREEN
        screenDict[
            "52Wk-H"
        ] = f"{highColor}{str('{:.2f}'.format(full52WeekHigh))}{colorText.END}"
        screenDict[
            "52Wk-L"
        ] = f"{lowColor}{str('{:.2f}'.format(full52WeekLow))}{colorText.END}"
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))

    # Find stocks that have broken through 10 days low (bearish breakout)
    def find10DaysLowBreakout(self, df, screenDict=None, saveDict=None):
        """
        Identify genuine 10-day low breakout patterns with confirmation.
        A quality 10-day low breakout should have:
        1. Price breaking below recent support levels
        2. Increased volume confirming selling pressure
        3. Bearish candle confirmation
        4. Stock not already oversold (avoid false bottoms)
        
        Args:
            df: DataFrame with OHLCV data (latest first)
            screenDict: Optional dict for output formatting
            saveDict: Optional dict for saving results
        
        Returns:
            bool: True if quality 10-day low breakout detected
        """
        if df is None or len(df) == 0:
            return False
        
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        
        # Need at least 15 days of data for proper analysis (10 days + buffer)
        if len(data) < 15:
            return False
        
        # Ensure data is sorted with most recent first
        if not data.empty and hasattr(data.index, 'sort_values'):
            try:
                data = data.sort_index(ascending=False)
            except:
                pass
        
        # Get recent data
        today = data.iloc[0]
        yesterday = data.iloc[1] if len(data) > 1 else None
        
        if yesterday is None:
            return False
        
        # Calculate 10-day low (excluding today)
        ten_day_data = data.iloc[1:11]  # Last 10 trading days excluding today
        ten_day_low = ten_day_data['low'].min() if len(ten_day_data) > 0 else 0
        ten_day_high = ten_day_data['high'].max() if len(ten_day_data) > 0 else 0
        
        # Calculate 5-day average volume for confirmation
        five_day_avg_volume = data.iloc[1:6]['volume'].mean() if len(data) > 5 else 0
        
        # QUALITY BREAKOUT CONDITIONS:
        
        # 1. Today's low breaks below 10-day low (actual breakout)
        price_breakout = today['low'] < ten_day_low
        
        if not price_breakout:
            return False
        
        # 2. Volume confirmation - higher volume on breakout day
        volume_confirmation = today['volume'] > five_day_avg_volume * 1.2
        
        # 3. Close is near low of day (seller conviction) - close in bottom 25% of daily range
        daily_range = today['high'] - today['low']
        if daily_range > 0:
            close_position = (today['close'] - today['low']) / daily_range
            close_confirmation = close_position < 0.25  # Close in bottom 25%
        else:
            close_confirmation = False
        
        # 4. Not already oversold (avoid chasing extended moves)
        # Check if RSI exists, if not calculate it
        rsi_value = None
        if 'RSI' in data.columns:
            rsi_value = data['RSI'].iloc[0]
        else:
            # Quick RSI calculation for confirmation
            close_prices = data['close'].iloc[:14].values
            if len(close_prices) >= 14:
                from pkscreener.classes.Pktalib import pktalib
                rsi_series = pktalib.RSI(data['close'], timeperiod=14)
                rsi_value = rsi_series.iloc[0] if len(rsi_series) > 0 else None
        
        # Breakout is more reliable when RSI is between 30-60 (not already oversold)
        rsi_confirmation = rsi_value is None or (30 <= rsi_value <= 70)
        
        # 5. Trend confirmation - price below 20-day SMA (downtrend context)
        sma_20 = data['close'].iloc[1:21].mean() if len(data) > 20 else 0
        trend_confirmation = today['close'] < sma_20 if sma_20 > 0 else True
        
        # 6. Previous day not already at low (genuine fresh breakdown)
        fresh_breakout = yesterday['low'] > ten_day_low
        
        # Combined quality check
        is_quality_breakout = (
            price_breakout and
            volume_confirmation and
            close_confirmation and
            rsi_confirmation and
            trend_confirmation and
            fresh_breakout
        )
        
        # Optional: Add additional bearish confirmation
        # Check if today is a bearish candle
        is_bearish_candle = today['close'] < today['open']
        
        # Check if making lower low vs yesterday
        lower_low = today['low'] < yesterday['low']
        
        # Final quality score (at least 3 of 4 additional conditions)
        additional_conditions = sum([
            is_bearish_candle,
            lower_low,
            today['close'] < yesterday['close'],  # Lower close
            today['volume'] > yesterday['volume'] * 1.5  # Volume spike
        ])
        
        quality_breakout = is_quality_breakout and additional_conditions >= 2
        
        # Store results for display if dictionaries provided
        if screenDict is not None and saveDict is not None and quality_breakout:
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            breakout_details = f"10D-Low-BO (L:{ten_day_low:.2f}, V:{today['volume']/five_day_avg_volume:.1f}x)"
            screenDict["Pattern"] = saved[0] + colorText.FAIL + breakout_details + colorText.END
            saveDict["Pattern"] = saved[1] + breakout_details
        
        return quality_breakout


    # Alternative: Bullish 10-day high breakout (complementary method)
    def find10DaysHighBreakout(self, df, screenDict=None, saveDict=None):
        """
        Identify bullish 10-day high breakout patterns (breakout to upside).
        Conditions:
        1. Price breaks above 10-day high
        2. Volume confirmation
        3. Close near high of day (buyer conviction)
        4. Uptrend context
        """
        if df is None or len(df) == 0:
            return False
        
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        
        if len(data) < 15:
            return False
        
        # Ensure sorted with most recent first
        if not data.empty and hasattr(data.index, 'sort_values'):
            try:
                data = data.sort_index(ascending=False)
            except:
                pass
        
        today = data.iloc[0]
        yesterday = data.iloc[1] if len(data) > 1 else None
        
        if yesterday is None:
            return False
        
        # Calculate 10-day high (excluding today)
        ten_day_data = data.iloc[1:11]
        ten_day_high = ten_day_data['high'].max() if len(ten_day_data) > 0 else 0
        
        # Calculate averages
        five_day_avg_volume = data.iloc[1:6]['volume'].mean() if len(data) > 5 else 0
        sma_20 = data['close'].iloc[1:21].mean() if len(data) > 20 else 0
        
        # Breakout conditions
        price_breakout = today['high'] > ten_day_high
        volume_confirmation = today['volume'] > five_day_avg_volume * 1.2
        
        # Close in top 25% of daily range (buyer conviction)
        daily_range = today['high'] - today['low']
        if daily_range > 0:
            close_position = (today['close'] - today['low']) / daily_range
            close_confirmation = close_position > 0.75
        else:
            close_confirmation = False
        
        # Uptrend context
        trend_confirmation = today['close'] > sma_20 if sma_20 > 0 else True
        
        # Bullish candle
        is_bullish = today['close'] > today['open']
        
        quality_breakout = (
            price_breakout and
            volume_confirmation and
            close_confirmation and
            trend_confirmation and
            is_bullish
        )
        
        if screenDict is not None and saveDict is not None and quality_breakout:
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            breakout_details = f"10D-High-BO (H:{ten_day_high:.2f}, V:{today['volume']/five_day_avg_volume:.1f}x)"
            screenDict["Pattern"] = saved[0] + colorText.GREEN + breakout_details + colorText.END
            saveDict["Pattern"] = saved[1] + breakout_details
        
        return quality_breakout

    # Find stocks that have broken through 52 week low.
    def find52WeekLowBreakout(self, df):
        if df is None or len(df) == 0:
            return False
        # https://chartink.com/screener/52-week-low-breakout
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        one_week = 5
        recent = data.head(1)["low"].iloc[0]
        # last1Week = data.head(one_week)
        # last2Week = data.head(2 * one_week)
        # previousWeek = last2Week.tail(one_week)
        full52Week = data.head(50 * one_week)
        # last1WeekLow = last1Week["low"].min()
        # previousWeekLow = previousWeek["low"].min()
        full52WeekLow = full52Week["low"].min()
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return recent <= full52WeekLow

    # Find stocks that have broken through Aroon bullish crossover.
    def findAroonBullishCrossover(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        period = 14
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        aroondf = pktalib.Aroon(data["high"], data["low"], period)
        recent = aroondf.tail(1)
        up = recent[f"AROONU_{period}"].iloc[0]
        down = recent[f"AROOND_{period}"].iloc[0]
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return up > down
    
    # Find ATR cross stocks
    def findATRCross(self, df,saveDict, screenDict):
        #https://chartink.com/screener/stock-crossing-atr
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        recentCandleHeight = self.getCandleBodyHeight(recent)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        atr = pktalib.ATR(data["high"],data["low"],data["close"], 14)
        atrCross = recentCandleHeight >= atr.tail(1).iloc[0]
        bullishRSI = recent["RSI"].iloc[0] >= 55 or recent["RSIi"].iloc[0] >= 55
        smav7 = pktalib.SMA(data["volume"],timeperiod=7).tail(1).iloc[0]
        atrCrossCondition = atrCross and bullishRSI and (smav7 < recent["volume"].iloc[0])
        saveDict["ATR"] = round(atr.tail(1).iloc[0],1)
        screenDict["ATR"] = saveDict["ATR"] #(colorText.GREEN if atrCrossCondition else colorText.FAIL) + str(atr.tail(1).iloc[0]) + colorText.END
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return atrCrossCondition
    
    def findATRTrailingStops(self, df_src, sensitivity=1, atr_period=10, ema_period=1,
                            buySellAll=1, saveDict=None, screenDict=None,
                            use_scoring=False, 
                            min_confidence=50, 
                            consecutive_confirmation_bars=1,
                            volume_confirmation=True,
                            buy_threshold=2,
                            sell_threshold=2,
                            min_bars_between_signals=1,
                            min_bars_between_sell_signals=0,
                            min_strength_for_confirmation=2,
                            stock_name="Unknown"):
        """
        Find ATR Trailing Stop signals using progressive validation.
        
        This function provides comprehensive diagnostics to identify why signals are
        being rejected or accepted. It logs:
        - Data validation stages
        - ATR calculation details
        - Signal detection results
        - Confidence scores
        - Threshold comparisons
        
        Args:
            df_src: OHLCV DataFrame (newest first)
            sensitivity: ATR multiplier
            atr_period: Period for ATR calculation
            ema_period: Period for EMA trend filter
            buySellAll: 1=Buy, 2=Sell, 3=Any
            saveDict: Dictionary for storing results
            screenDict: Dictionary for formatted display
            use_scoring: Whether to use detailed scoring
            min_confidence: Minimum confidence threshold
            stock_name: Stock symbol for identification
        
        Returns:
            tuple: (result, debug_info) where debug_info contains detailed logs
        """
        # =========================================================================
        # LEVEL 1: QUICK VALIDATION - FAIL FAST FOR 2000+ STOCKS
        # =========================================================================
        if df_src is None:
            return False, {}
        
        if len(df_src) == 0:
            return False, {}
        
        df = df_src.copy()
        # Quick price check
        try:
            recent_close = df['close'].iloc[0] if not df.empty else 0
            if recent_close <= 0:
                return False, {}
                
            if hasattr(self, 'configManager') and self.configManager:
                min_ltp = getattr(self.configManager, 'minLTP', 20)
                max_ltp = getattr(self.configManager, 'maxLTP', 5000)
                if recent_close < min_ltp or recent_close > max_ltp:
                    return False, {}
        except Exception:
            return False, {}
        
        buy_confidence = 0
        sell_confidence = 0

        # Quick volume check
        if 'volume' in df.columns and len(df) > 20:
            try:
                avg_volume = df['volume'].head(20).mean()
                recent_volume = df['volume'].iloc[0] if not df.empty else 0
                min_volume = getattr(self.configManager, 'minVolume', 100000) if hasattr(self, 'configManager') else 100000
                
                if recent_volume < min_volume:
                    return False, {}
                elif recent_volume < avg_volume * 0.5:
                    return False, {}
            except Exception:
                pass
        
        # =========================================================================
        # LEVEL 2: ATR AND TRAILING STOP CALCULATION
        # =========================================================================
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse to oldest first (required for ATR)
        
        if len(data) > 150:
            data = data.tail(150)
        
        try:
            # Calculate ATR
            data["xATR"] = pktalib.ATR(data["high"], data["low"], data["close"], timeperiod=atr_period)
            data["nLoss"] = sensitivity * data["xATR"]
            
            # Calculate additional indicators needed for sell signals
            data["SMA"] = data["close"].rolling(window=20, min_periods=10).mean()
            data["LMA"] = data["close"].rolling(window=50, min_periods=20).mean()
            data["RSI"] = pktalib.RSI(data["close"], timeperiod=14)
            
            data = data.dropna()
            if len(data) < atr_period + 5:
                return False, {}
            
            data = data.reset_index(drop=True)
            data["ATRTrailingStop"] = 0.0
            
            # Initialize first value
            if len(data) > 0:
                data.loc[0, "ATRTrailingStop"] = data.loc[0, "close"] - data.loc[0, "nLoss"]
            
            # Calculate trailing stop for all bars
            for i in range(1, len(data)):
                data.loc[i, "ATRTrailingStop"] = self.xATRTrailingStop_func(
                    data.loc[i, "close"],
                    data.loc[i - 1, "close"],
                    data.loc[i - 1, "ATRTrailingStop"],
                    data.loc[i, "nLoss"],
                )
            
        except Exception as e:
            if self.default_logger:
                self.default_logger.debug(f"ATR calculation failed: {e}")
            return False, {}
        
        # Reverse back to newest first for signal detection
        data = data[::-1]
        
        # # =========================================================================
        # # LEVEL 3: DIRECT PRICE VS STOP ANALYSIS (Pre-signal check)
        # # =========================================================================
        # if len(data) >= 2:
        #     current_close = data["close"].iloc[0]
        #     current_stop = data["ATRTrailingStop"].iloc[0]
        #     prev_close = data["close"].iloc[1] if len(data) > 1 else current_close
        #     prev_stop = data["ATRTrailingStop"].iloc[1] if len(data) > 1 else current_stop
            
        #     price_above_stop = current_close > current_stop
        #     price_below_stop = current_close < current_stop
        #     above_cross = (prev_close <= prev_stop) and (current_close > current_stop)
        #     below_cross = (prev_close >= prev_stop) and (current_close < current_stop)
        #     if buySellAll == 1 and not (price_above_stop or above_cross):
        #         return False, {}
        #     elif buySellAll == 2 and not (price_below_stop or below_cross):
        #         return False, {}
        
        # =========================================================================
        # LEVEL 3: SIGNAL DETECTION USING computeBuySellSignals
        # =========================================================================
        try:
            data_with_signals, _ = self.computeBuySellSignals(
                data, 
                ema_period=ema_period,
                confirmation_bars=consecutive_confirmation_bars,
                volume_confirmation=volume_confirmation,
                min_strength=min_strength_for_confirmation,
                stock_name=stock_name
            )
            
            if data_with_signals is None:
                return False, {}
            # Add bearish sell signals if none found
            if data_with_signals is not None and not data_with_signals["Sell"].any():
                data_with_signals = self.addBearishSellSignals(data_with_signals)
        except Exception as e:
            if self.default_logger:
                self.default_logger.debug(f"computeBuySellSignals error: {e}")
            return False, {}
        
        # Get the most recent signal
        recent = data_with_signals.tail(1)
        if recent.empty:
            return False, {}
        
        # # ------------------------------------------------------------
        # # Count distinct bearish reasons for strong sell confirmation
        # # ------------------------------------------------------------
        # bearish_reasons = 0

        # # Helper to safely get boolean from series
        # def is_true(val):
        #     return bool(val) if not pd.isna(val) else False

        # # 1. RSI sell condition (RSI > 70 or RSI falling from overbought)
        # if 'RSI' in recent.columns:
        #     rsi_val = recent['RSI'].iloc[0]
        #     if not pd.isna(rsi_val) and rsi_val > 70:
        #         bearish_reasons += 1
        #     # Also check for RSI falling from above 70 (momentum loss)
        #     elif len(data_with_signals) >= 2:
        #         prev_rsi = data_with_signals['RSI'].iloc[-2]
        #         if not pd.isna(prev_rsi) and prev_rsi > 70 and rsi_val < prev_rsi:
        #             bearish_reasons += 1

        # # 2. MACD bearish (histogram < 0 and falling)
        # if 'MACD_Hist' in recent.columns:
        #     hist = recent['MACD_Hist'].iloc[0]
        #     if not pd.isna(hist) and hist < 0:
        #         if len(data_with_signals) >= 2:
        #             prev_hist = data_with_signals['MACD_Hist'].iloc[-2]
        #             if not pd.isna(prev_hist) and hist < prev_hist:
        #                 bearish_reasons += 1
        #         else:
        #             bearish_reasons += 1
        # else:
        #     # Compute MACD on the fly if not present
        #     try:
        #         _, _, hist = pktalib.MACD(data['close'])
        #         if len(hist) >= 2:
        #             curr_hist = hist.iloc[-1]
        #             prev_hist = hist.iloc[-2]
        #             if curr_hist < 0 and curr_hist < prev_hist:
        #                 bearish_reasons += 1
        #     except:
        #         pass

        # # 3. Volume sell confirmation (volume surge on down day)
        # if 'volume' in recent.columns and len(data_with_signals) > 20:
        #     curr_vol = recent['volume'].iloc[0]
        #     avg_vol = data_with_signals['volume'].iloc[1:21].mean()
        #     price_change = (recent['close'].iloc[0] - data_with_signals['close'].iloc[1]) / data_with_signals['close'].iloc[1]
        #     if avg_vol > 0 and curr_vol > avg_vol * 1.5 and price_change < -0.02:
        #         bearish_reasons += 1

        # # 4. Death cross (50 SMA < 200 SMA) or below 200 SMA
        # if 'SMA' in recent.columns and 'LMA' in recent.columns:
        #     sma_50 = recent['SMA'].iloc[0]
        #     sma_200 = recent['LMA'].iloc[0]
        #     if not pd.isna(sma_50) and not pd.isna(sma_200) and sma_50 < sma_200:
        #         bearish_reasons += 1
        # elif 'LMA' in recent.columns:
        #     # At least check if price is below 200 SMA
        #     if recent['close'].iloc[0] < recent['LMA'].iloc[0]:
        #         bearish_reasons += 1

        # # 5. Price below key moving averages (20 EMA, 50 SMA)
        # if 'close' in recent.columns:
        #     close_price = recent['close'].iloc[0]
        #     # 20 EMA (calculate quickly if not present)
        #     try:
        #         ema20 = pktalib.EMA(data['close'], 20).iloc[-1]
        #         if close_price < ema20 * 0.98:
        #             bearish_reasons += 1
        #     except:
        #         pass
        #     # 50 SMA already covered above, but add additional if below 20 SMA
        #     if 'SSMA20' in recent.columns and close_price < recent['SSMA20'].iloc[0]:
        #         bearish_reasons += 1
                
        # Extract signal values
        buy_signal = recent["Buy"].iloc[0] if "Buy" in recent.columns else False
        sell_signal = recent["Sell"].iloc[0] if "Sell" in recent.columns else False
        signal_strength = recent["Signal_Strength"].iloc[0] if "Signal_Strength" in recent.columns else 0
        buy_confidence = recent["Buy_Confidence"].iloc[0] if "Buy_Confidence" in recent.columns else 0
        sell_confidence = recent["Sell_Confidence"].iloc[0] if "Sell_Confidence" in recent.columns else 0
        # self.default_logger.debug(f"computeBuySellSignals for {stock_name}: Returned result=Buy:{buy_signal}, Sell:{sell_signal}, Strength:{signal_strength}, Buy_Conf:{buy_confidence}, Sell_Conf:{sell_confidence}")
        # =========================================================================
        # LEVEL 4: USE SCORING FOR CANDIDATE STOCKS (Optional)
        # =========================================================================
        if use_scoring and (buy_signal or sell_signal):
            try:
                scored_data = self.computeBuySellSignalsWithScores(
                    data.tail(50),
                    ema_period=ema_period,
                    stock_name=stock_name
                )
                
                if scored_data is not None and not scored_data.empty:
                    recent_scored = scored_data.tail(1)
                    if "Signal_Score" in recent_scored.columns:
                        signal_score = recent_scored["Signal_Score"].iloc[0]
                        # self.default_logger.debug(f"computeBuySellSignalsWithScores for {stock_name}: Signal_Score {signal_score}")
                        if buy_signal and signal_score < min_confidence:
                            buy_signal = False
                        elif buy_signal:
                            buy_confidence = signal_score
                        
                        if sell_signal and signal_score < min_confidence:
                            sell_signal = False
                        elif sell_signal:
                            sell_confidence = signal_score
                # self.default_logger.debug(f"computeBuySellSignalsWithScores for {stock_name}: Returned result=Buy:{buy_signal}, Sell:{sell_signal}")
            except Exception as e:
                if self.default_logger:
                    self.default_logger.debug(f"Scoring error: {e}")
        
        # =========================================================================
        # LEVEL 5: APPLY BALANCED FILTERS (Optional)
        # =========================================================================
        # Only apply balanced filter if we're looking for sell signals only
        if buySellAll == 2 and sell_signal:
            try:
                balanced_data = self.computeBalancedSignals(
                    data.tail(50),
                    ema_period=ema_period,
                    buy_threshold=buy_threshold if buySellAll == 1 else 1,
                    sell_threshold=sell_threshold if buySellAll == 2 else 1,
                    volume_confirmation=volume_confirmation,
                    min_bars_between_signals=min_bars_between_signals,
                    min_bars_between_sell_signals=min_bars_between_sell_signals,
                    confirmation_bars=consecutive_confirmation_bars,
                    min_strength=min_strength_for_confirmation,
                    stock_name=stock_name
                )
                
                if balanced_data is not None and not balanced_data.empty:
                    recent_balanced = balanced_data.tail(1)
                    if "Sell_Signal" in recent_balanced.columns:
                        sell_signal = sell_signal and recent_balanced["Sell_Signal"].iloc[0]
                    # self.default_logger.debug(f"computeBalancedSignals for {stock_name}: Returned result=Buy:{buy_signal}, Sell:{sell_signal}")
            except Exception as e:
                if self.default_logger:
                    self.default_logger.debug(f"Balanced filter error: {e}")
        
        # =========================================================================
        # LEVEL 6: APPLY CONFIDENCE THRESHOLDS + BEARISH REASONS FOR STRONG SELL
        # =========================================================================
        if buy_signal and buy_confidence < min_confidence:
            buy_signal = False
        
        if sell_signal and sell_confidence < min_confidence:
            sell_signal = False
        # # For sell signals, require BOTH confidence >= min_confidence AND at least 3 bearish reasons
        # if sell_signal:
        #     if sell_confidence < min_confidence:
        #         sell_signal = False
        #     elif bearish_reasons < 3:
        #         # Not enough bearish confirmation → downgrade to weak sell or neutral
        #         if self.default_logger:
        #             self.default_logger.debug(f"Strong sell rejected: only {bearish_reasons} bearish reasons (need ≥3)")
        #         sell_signal = False
        #     # Optional: also require sell_confidence >= 70 for strong sell
        #     elif sell_confidence >= 70 and bearish_reasons >= 3:
        #         # This is a high-conviction strong sell – keep as True
        #         pass
        # self.default_logger.debug(f"Level 6 for {stock_name}: Returned result=Buy:{buy_signal}, Sell:{sell_signal}, Buy_Conf:{buy_confidence}, Sell_Conf:{sell_confidence}")
        # =========================================================================
        # LEVEL 7: DETERMINE RETURN VALUE
        # =========================================================================
        result = False
        signal_type = "NA"
        
        if buySellAll == 1:  # Buy signals only
            result = buy_signal
            signal_type = "Buy" if buy_signal else "NA"
            sell_signal = False  # Ensure sell signal is False when looking for buy signals only
        elif buySellAll == 2:  # Sell signals only
            result = sell_signal
            signal_type = "Sell" if sell_signal else "NA"
            buy_signal = False  # Ensure buy signal is False when looking for sell signals only
        else:  # Any signal (buySellAll == 3)
            result = buy_signal or sell_signal
            if buy_signal:
                signal_type = "Buy"
            if sell_signal:
                signal_type = "Sell"
            if buy_signal and sell_signal:
                    signal_type = "Sell"
                    buy_signal = False  # Prioritize sell signal if both are present
                    sell_signal = True
        # self.default_logger.debug(f"Level 7 for {stock_name}: Returned result=Buy:{buy_signal}, Sell:{sell_signal}, Buy_Conf:{buy_confidence}, signal_type:{signal_type}, Sell_Conf:{sell_confidence}")
        # =========================================================================
        # LEVEL 8: STORE RESULTS (if dictionaries provided)
        # =========================================================================
        if saveDict is not None and screenDict is not None:
            saveDict["B/S"] = signal_type
            saveDict["Signal_Strength"] = signal_strength
            saveDict["Confidence"] = buy_confidence if buy_signal else sell_confidence if sell_signal else 0
            screenDict["Confidence"] = buy_confidence if buy_signal else sell_confidence if sell_signal else 0
            if result:
                if buy_signal and sell_signal:
                    saveDict["B/S"] = signal_type
                    saveDict["Signal_Strength"] = signal_strength
                    saveDict["Confidence"] = buy_confidence if buy_confidence >= sell_confidence else sell_confidence
                    screenDict["Confidence"] = buy_confidence if buy_confidence >= sell_confidence else sell_confidence
                    screenDict["B/S[%]"] = colorText.GREEN + f"{signal_type}[{int(buy_confidence)}]" + colorText.END
                elif buy_signal and buy_confidence > 0:
                    screenDict["B/S[%]"] = colorText.GREEN + f"{signal_type}[{int(buy_confidence)}]" + colorText.END
                elif sell_signal and sell_confidence > 0:
                    screenDict["B/S[%]"] = colorText.FAIL + f"{signal_type}[{int(sell_confidence)}]" + colorText.END
            else:
                screenDict["B/S[%]"] = colorText.WARN + "NA" + colorText.END
        
        # self.default_logger.debug(f"DEBUG: Returning result={result}, signal_type={signal_type}, buy_signal={buy_signal}, sell_signal={sell_signal}")
        return result, {}

    def findATRTrailingStopsBatch(self, stocks_df_dict, sensitivity=1, atr_period=10, 
                                ema_period=1, buySellAll=1, min_confidence=50,
                                max_workers=4):
        """
        Batch process multiple stocks for ATR Trailing Stop signals.
        
        This method is optimized for screening 2000+ stocks by using:
        1. Parallel processing across multiple workers
        2. Early filtering before expensive calculations
        3. Progressive confidence validation
        
        Args:
            stocks_df_dict (dict): Dictionary of {symbol: dataframe}
            sensitivity (float): ATR multiplier
            atr_period (int): ATR period
            ema_period (int): EMA period
            buySellAll (int): 1=Buy, 2=Sell, 3=Any
            min_confidence (int): Minimum confidence threshold
            max_workers (int): Maximum parallel workers
        
        Returns:
            dict: {symbol: (has_signal, confidence, signal_type)}
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        
        def process_stock(symbol, df):
            """Process a single stock with early exit"""
            # Quick pre-filter before full calculation
            if df is None or len(df) < 20:
                return symbol, (False, 0, "NA")
            
            # Quick price check
            try:
                recent_close = df['close'].iloc[0] if not df.empty else 0
                if recent_close <= 0:
                    return symbol, (False, 0, "NA")
            except:
                return symbol, (False, 0, "NA")
            
            # Quick volume check
            if 'volume' in df.columns and len(df) > 20:
                try:
                    avg_volume = df['volume'].head(20).mean()
                    recent_volume = df['volume'].iloc[0] if not df.empty else 0
                    if recent_volume < avg_volume * 0.5:
                        return symbol, (False, 0, "NA")
                except:
                    pass
            
            # Run the main signal detection
            save_dict = {}
            screen_dict = {}
            
            has_signal, _ = self.findATRTrailingStops(
                df, sensitivity, atr_period, ema_period, buySellAll,
                save_dict, screen_dict, use_scoring=True, min_confidence=min_confidence
            )
            
            confidence = save_dict.get("Confidence", 0)
            signal_type = save_dict.get("B/S", "NA")
            
            return symbol, (has_signal, confidence, signal_type)
        max_workers = max(2,max_workers)
        # Process stocks in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_stock, symbol, df): symbol 
                for symbol, df in stocks_df_dict.items()
            }
            
            for future in as_completed(futures):
                symbol, result = future.result()
                results[symbol] = result
        
        return results


    def findATRTrailingStopsWithRanking(self, df_list, sensitivity=1, atr_period=10, 
                                        ema_period=1, top_n=20):
        """
        Find and rank the best ATR Trailing Stop signals across multiple stocks.
        
        This method is ideal for portfolio construction where you want the
        strongest signals from a large universe of stocks.
        
        Args:
            df_list (list): List of (symbol, dataframe) tuples
            sensitivity (float): ATR multiplier
            atr_period (int): ATR period
            ema_period (int): EMA period
            top_n (int): Number of top signals to return
        
        Returns:
            list: Top N stocks ranked by signal strength, each as (symbol, score, type)
        """
        results = []
        
        for symbol, df in df_list:
            if df is None or len(df) < 20:
                continue
            
            # Use scoring method for detailed ranking
            save_dict = {}
            screen_dict = {}
            
            has_signal, _ = self.findATRTrailingStops(
                df, sensitivity, atr_period, ema_period, 3,  # Any signal
                save_dict, screen_dict, use_scoring=True, min_confidence=30
            )
            
            if has_signal:
                confidence = save_dict.get("Confidence", 0)
                signal_type = save_dict.get("B/S", "NA")
                results.append((symbol, confidence, signal_type))
        
        # Sort by confidence (highest first) and return top N
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    # def identify_demand_zone(self,data, cmp):
    #     demand_zones = []
    #     drop_base_rally_zone = False
    #     rally_base_rally_zone = False
        
    #     # Additional variables to track base candle prices for proximal line calculation
    #     base_candle_prices = []
        
    #     for i in range(len(data) - 2):
    #         if data['Candle Type'][i] == 'Drop Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count <= 4:  # Maximum of 4 base candles for weekly or monthly timeframe, else 3 for daily
    #                 if j < len(data) and data['Candle Type'][j] == 'Rally Candle':
    #                     if data["close"][j] > data["low"][i] + 0.6 * data['Candle Range'][i] and data["high"][i] <= cmp:
    #                         # Check for one more rally candle or green base candle
    #                         k = j + 1
    #                         while k < len(data):
    #                             if data['Candle Type'][k] == 'Rally Candle' or (data['Candle Type'][k] == 'Base Candle' and data["close"][k] > data["open"][k]):
    #                                 demand_zones.append((i, j, 'Drop Base Rally', base_count))
    #                                 drop_base_rally_zone = True
    #                                 break
    #                             k += 1
    #         elif data['Candle Type'][i] == 'Rally Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count >= 1:  # At least one base candle required
    #                 if j < len(data) and data['Candle Type'][j] == 'Rally Candle':
    #                     if data["close"][j] > data["close"][i] and data["high"][i] <= cmp:  # New condition: close of 2nd rally candle > 1st rally candle
    #                         # Check for one more rally candle or green base candle
    #                         k = j + 1
    #                         while k < len(data):
    #                             if data['Candle Type'][k] == 'Rally Candle' or (data['Candle Type'][k] == 'Base Candle' and data["close"][k] > data["open"][k]):
    #                                 demand_zones.append((i, j, 'Rally Base Rally', base_count))
    #                                 rally_base_rally_zone = True
    #                                 break
    #                             k += 1
                            
    #         # Collect base candle prices for proximal line calculation
    #         if data['Candle Type'][i] == 'Base Candle':
    #             base_candle_prices.append(data["close"][i])

    #     # Calculate proximal line price (highest price among base candles)
    #     proximal_line_price = max(base_candle_prices) if base_candle_prices else None

    #     return demand_zones, drop_base_rally_zone, rally_base_rally_zone, proximal_line_price

    # def identify_supply_zone(self,data, cmp):
    #     supply_zones = []
    #     rally_base_drop_zone = False
    #     drop_base_drop_zone = False
        
    #     # Additional variables to track base candle prices for proximal line calculation
    #     base_candle_prices = []
        
    #     for i in range(len(data) - 2):
    #         if data['Candle Type'][i] == 'Drop Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count <= 4:  # Maximum of 4 base candles for weekly or monthly timeframe, else 3 for daily
    #                 if j < len(data) and data['Candle Type'][j] == 'Drop Candle':
    #                     if data["close"][i] < data["low"][j] and data["low"][i] >= cmp:  # New condition: close of drop candle < low of base candle
    #                         # New logic: Look for one more drop candle or red base candle
    #                         k = j + 1
    #                         while k < len(data) and (data['Candle Type'][k] == 'Drop Candle' or data["close"][k] < data["open"][k]):
    #                             k += 1
    #                         if k < len(data) and (data['Candle Type'][k] == 'Drop Candle' or data["close"][k] < data["open"][k]):
    #                             supply_zones.append((i, j, 'Drop Base Drop', base_count))
    #                             drop_base_drop_zone = True
    #         elif data['Candle Type'][i] == 'Rally Candle' and data['Candle Type'][i + 1] == 'Base Candle':
    #             base_count = 1
    #             j = i + 2
    #             while j < len(data) and data['Candle Type'][j] == 'Base Candle':
    #                 base_count += 1
    #                 j += 1
                
    #             if base_count >= 1:  # At least one base candle required
    #                 if j < len(data) and data['Candle Type'][j] == 'Drop Candle':
    #                     if data["close"][j] < data["open"][j] and data["low"][i] >= cmp:  # Modified condition: close of drop candle < open of drop candle
    #                         supply_zones.append((i, j, 'Rally Base Drop', base_count))
    #                         rally_base_drop_zone = True
                            
    #         # Collect base candle prices for proximal line calculation
    #         if data['Candle Type'][i] == 'Base Candle':
    #             base_candle_prices.append(data["close"][i])

    #     # Calculate proximal line price (lowest price among base candles)
    #     proximal_line_price = min(base_candle_prices) if base_candle_prices else None

    #     return supply_zones, rally_base_drop_zone, drop_base_drop_zone, proximal_line_price

    # def calculate_demand_proximal_lines(self,data, demand_zones):
    #     proximal_line_prices = []
    #     for start, end, _, _ in demand_zones:
    #         base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), ["open", "close"]]
    #         max_price = base_candle_prices.max(axis=1).max()  # Get the maximum price among all base candles' open and close prices
    #         proximal_line_prices.append(max_price)
    #     return proximal_line_prices

    # def calculate_supply_proximal_lines(self,data, supply_zones):
    #     proximal_line_prices = []
    #     for start, end, _, _ in supply_zones:
    #         base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), ["open", "close"]]
    #         min_price = base_candle_prices.min(axis=1).min()  # Get the minimum price among all base candles' open and close prices
    #         proximal_line_prices.append(min_price)
    #     return proximal_line_prices
        
    # def calculate_demand_distal_lines(self,data, demand_zones):
    #     distal_line_prices = []
    #     for start, end, pattern, _ in demand_zones:
    #         if pattern == 'Drop Base Rally':
    #             # Logic for Drop Base Rally pattern: Take the lowest price among all components of the zone
    #             lowest_price = min(data["low"][start:end + 1])  # Get the lowest price within the zone
    #             distal_line_prices.append(lowest_price)
    #         elif pattern == 'Rally Base Rally':
    #             # Logic for Rally Base Rally pattern: Take the lowest of only all base candle and followed rally candle
    #             base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), "low"]
    #             rally_candle_prices = data.loc[(data['Candle Type'] == 'Rally Candle') & (data.index >= data.index[end]) & (data.index < data.index[end+1]), "low"]
    #             all_prices = pd.concat([base_candle_prices, rally_candle_prices])
    #             lowest_price = all_prices.min() if not all_prices.empty else None
    #             distal_line_prices.append(lowest_price)
    #     return distal_line_prices

    # def calculate_supply_distal_lines(self,data, supply_zones):
    #     distal_line_prices = []
    #     for start, end, pattern, _ in supply_zones:
    #         if pattern == 'Rally Base Drop':
    #             # Logic for Rally Base Drop pattern: Take the highest price among all components of the zone
    #             highest_price = max(data["high"][start:end + 1])  # Get the highest price within the zone
    #             distal_line_prices.append(highest_price)
    #         elif pattern == 'Drop Base Drop':
    #             # Logic for Drop Base Drop pattern: Take the highest of only all base candles and followed drop candle
    #             base_candle_prices = data.loc[(data['Candle Type'] == 'Base Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), "high"]
    #             drop_candle_prices = data.loc[(data['Candle Type'] == 'Drop Candle') & (data.index >= data.index[start]) & (data.index <= data.index[end]), "high"]
    #             all_prices = pd.concat([base_candle_prices, drop_candle_prices])
    #             highest_price = all_prices.max() if not all_prices.empty else None
    #             distal_line_prices.append(highest_price)
    #     return distal_line_prices

    # def is_zone_tested(self,data, start_index, end_index, proximal_line_price):
    #     """
    #     Check if the proximal line price has been tested by future prices.
        
    #     Args:
    #     - data: DataFrame containing stock data
    #     - start_index: Start index of the demand/supply zone
    #     - end_index: End index of the demand/supply zone
    #     - proximal_line_price: Proximal line price
        
    #     Returns:
    #     - True if the proximal line price is tested, False otherwise
    #     """
    #     for i in range(end_index + 1, len(data)):
    #         if data["low"][i] <= proximal_line_price <= data["high"][i]:
    #             return True
    #     return False

    # def calculate_zone_range(self,proximal_line, distal_line):
    #     """
    #     Calculate the range of a zone given its proximal and distal lines.
        
    #     Args:
    #     - proximal_line: Proximal line price
    #     - distal_line: Distal line price
        
    #     Returns:
    #     - Range of the zone
    #     """
    #     if proximal_line is not None and distal_line is not None:
    #         return abs(proximal_line - distal_line)
    #     else:
    #         return None

    # def calculate_demand_zone_ranges(self,demand_zones, demand_proximal_lines, demand_distal_lines):
    #     """
    #     Calculate the range of each demand zone.
        
    #     Args:
    #     - demand_zones: List of demand zone tuples (start, end, pattern, base_count)
    #     - demand_proximal_lines: List of proximal line prices for demand zones
    #     - demand_distal_lines: List of distal line prices for demand zones
        
    #     Returns:
    #     - List of ranges corresponding to each demand zone
    #     """
    #     demand_zone_ranges = []
    #     for i, (start, end, _, _) in enumerate(demand_zones):
    #         range_of_zone = self.calculate_zone_range(demand_proximal_lines[i], demand_distal_lines[i])
    #         demand_zone_ranges.append(range_of_zone)
    #     return demand_zone_ranges

    # def calculate_supply_zone_ranges(self,supply_zones, supply_proximal_lines, supply_distal_lines):
    #     """
    #     Calculate the range of each supply zone.
        
    #     Args:
    #     - supply_zones: List of supply zone tuples (start, end, pattern, base_count)
    #     - supply_proximal_lines: List of proximal line prices for supply zones
    #     - supply_distal_lines: List of distal line prices for supply zones
        
    #     Returns:
    #     - List of ranges corresponding to each supply zone
    #     """
    #     supply_zone_ranges = []
    #     for i, (start, end, _, _) in enumerate(supply_zones):
    #         range_of_zone = self.calculate_zone_range(supply_proximal_lines[i], supply_distal_lines[i])
    #         supply_zone_ranges.append(range_of_zone)
    #     return supply_zone_ranges

    # def filter_stocks_by_distance(self,data,symbol_list, threshold_percent, timeframe):
    #     filtered_stocks = []
    #     for symbol in symbol_list:
    #         if data is not None:
    #             cmp = data.iloc[-1]["close"]  # Current market price
    #             demand_zones, _, _, demand_proximal_line = self.identify_demand_zone(data, cmp)  # Pass cmp argument here
    #             supply_zones, _, _, supply_proximal_line = self.identify_supply_zone(data, cmp)  # Pass cmp argument here
                
    #             # Check if either demand or supply zones exist for the stock
    #             if demand_zones or supply_zones:
    #                 filtered_stocks.append(symbol)

    #     return filtered_stocks
    
    # def findDemandSupplyZones(self,data,threshold_percent=1):        
    #     # Initialize count for filtered stocks
    #     count_filtered_stocks = 0

    #     # Analyze demand and supply zones for each stock and save results in a file
    #     with open("demand_supply_zones.txt", "w") as file:
    #         for symbol in data["Stock"]:
    #             if data is not None:
    #                 cmp = data.iloc[-1]["close"]  # Current market price
    #                 demand_zones, _, _, demand_proximal_line = self.identify_demand_zone(data, cmp)
    #                 supply_zones, _, _, supply_proximal_line = self.identify_supply_zone(data, cmp)

    #                 # Step 1: Calculate proximal lines for demand and supply zones
    #                 demand_proximal_lines = self.calculate_demand_proximal_lines(data, demand_zones)
    #                 supply_proximal_lines = self.calculate_supply_proximal_lines(data, supply_zones)
                    
    #                 # Step 2: Calculate distal lines for demand zones and supply zones
    #                 demand_distal_lines = self.calculate_demand_distal_lines(data, demand_zones)
    #                 supply_distal_lines = self.calculate_supply_distal_lines(data, supply_zones)

    #                 # Calculate range of demand and supply zones
    #                 demand_zone_ranges = self.calculate_demand_zone_ranges(demand_zones, demand_proximal_lines, demand_distal_lines)
    #                 supply_zone_ranges = self.calculate_supply_zone_ranges(supply_zones, supply_proximal_lines, supply_distal_lines)
                    
    #                 file.write(f"\n\nAnalysis for {symbol} ({timeframe}):")
                    
    #                 # Demand Zones
    #                 file.write("\n\nDemand Zones:")
    #                 if demand_zones:  # Check if demand_zones is not empty
    #                     for i, (start, end, pattern, base_count) in enumerate(demand_zones):
    #                         dist_from_cmp = abs((cmp - demand_proximal_lines[i]) / cmp) * 100
    #                         file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                         file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                         file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                         if demand_proximal_lines:
    #                             file.write(f"\nProximal Line Price: {demand_proximal_lines[i]:.2f}")
    #                         if demand_distal_lines:  # Include distal line price if available
    #                             file.write(f"\nDistal Line Price: {demand_distal_lines[i]:.2f}")
    #                         # Include zone range
    #                             file.write(f"\nZone Range: {demand_zone_ranges[i]:.2f}")       
    #                         # Check if proximal line is tested
    #                         tested = self.is_zone_tested(data, start, end, demand_proximal_lines[i])
    #                         if tested:
    #                             file.write("\nZone is Tested")
    #                         else:
    #                             file.write("\nFresh Zone")
    #                 else:
    #                     file.write("\nNo demand zone patterns found.")

    #                 # Supply Zones
    #                 file.write("\n\nSupply Zones:")
    #                 if supply_zones:  # Check if supply_zones is not empty
    #                     for i, (start, end, pattern, base_count) in enumerate(supply_zones):
    #                         dist_from_cmp = abs((cmp - supply_proximal_lines[i]) / cmp) * 100
    #                         file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                         file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                         file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                         if supply_proximal_lines:
    #                             file.write(f"\nProximal Line Price: {supply_proximal_lines[i]:.2f}")
    #                         if supply_distal_lines:  # Include distal line price if available
    #                             file.write(f"\nDistal Line Price: {supply_distal_lines[i]:.2f}")
    #                         # Include zone range
    #                             file.write(f"\nZone Range: {supply_zone_ranges[i]:.2f}")
    #                         # Check if proximal line is tested
    #                         tested = is_zone_tested(data, start, end, supply_proximal_lines[i])
    #                         if tested:
    #                             file.write("\nZone is Tested")
    #                         else:
    #                             file.write("\nFresh Zone")
    #                 else:
    #                     file.write("\nNo supply zone patterns found.")

    #                 # Check if the stock has either demand or supply zone within the threshold
    #                 has_demand_or_supply_within_threshold = any(
    #                     abs((cmp - price) / cmp) * 100 <= threshold_percent
    #                     for price in demand_proximal_lines + supply_proximal_lines
    #                 )
                    
    #                 # If the stock has demand or supply zone within the threshold, increment the count
    #                 if has_demand_or_supply_within_threshold:
    #                     count_filtered_stocks += 1

    #     # Filter stocks based on the percentage threshold and save the results in another file
    #     filtered_stocks = self.filter_stocks_by_distance(stock_symbols, threshold_percent, timeframe)

    #     with open("filtered_stocks_data.txt", "w") as file:
    #         file.write(f"Number of stocks Filtered: {count_filtered_stocks}\n\n")
    #         file.write("Filtered Stock Data:\n\n")
            
    #         for symbol in filtered_stocks:
    #             if data is not None:
    #                 cmp = data.iloc[-1]["close"]  # Current market price
    #                 demand_zones, _, _, demand_proximal_line = self.identify_demand_zone(data, cmp)
    #                 supply_zones, _, _, supply_proximal_line = self.identify_supply_zone(data, cmp)

    #                 # Step 1: Calculate proximal lines for demand and supply zones
    #                 demand_proximal_lines = self.calculate_demand_proximal_lines(data, demand_zones)
    #                 supply_proximal_lines = self.calculate_supply_proximal_lines(data, supply_zones)
                    
    #                 # Step 2: Calculate distal lines for demand zones and supply zones
    #                 demand_distal_lines = self.calculate_demand_distal_lines(data, demand_zones)
    #                 supply_distal_lines = self.calculate_supply_distal_lines(data, supply_zones)
                    
    #                 # Calculate range of demand and supply zones
    #                 demand_zone_ranges = self.calculate_demand_zone_ranges(demand_zones, demand_proximal_lines, demand_distal_lines)
    #                 supply_zone_ranges = self.calculate_supply_zone_ranges(supply_zones, supply_proximal_lines, supply_distal_lines)
                                    
    #                 # Check if the stock has either demand or supply zone within the threshold
    #                 has_demand_or_supply_within_threshold = any(
    #                     abs((cmp - price) / cmp) * 100 <= threshold_percent
    #                     for price in demand_proximal_lines + supply_proximal_lines
    #                 )
                    
    #                 # If the stock has demand or supply zone within the threshold, write its analysis
    #                 if has_demand_or_supply_within_threshold:
    #                     file.write(f"Analysis for {symbol} ({timeframe}):\n")
                        
    #                     # Demand Zones
    #                     file.write("\n\nDemand Zones:")
    #                     if demand_zones:  # Check if demand_zones is not empty
    #                         for i, (start, end, pattern, base_count) in enumerate(demand_zones):
    #                             dist_from_cmp = abs((cmp - demand_proximal_lines[i]) / cmp) * 100
    #                             if abs(dist_from_cmp) <= threshold_percent:  # Check if dist_from_cmp is within threshold
    #                                 file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                                 file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                                 file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                                 if demand_proximal_lines:
    #                                     file.write(f"\nProximal Line Price: {demand_proximal_lines[i]:.2f}")
    #                                 if demand_distal_lines:  # Include distal line price if available
    #                                     file.write(f"\nDistal Line Price: {demand_distal_lines[i]:.2f}")
    #                                 # Include zone range
    #                                     file.write(f"\nZone Range: {demand_zone_ranges[i]:.2f}")
    #                                 # Check if proximal line is tested
    #                                 tested = is_zone_tested(data, start, end, demand_proximal_lines[i])
    #                                 if tested:
    #                                     file.write("\nZone is Tested")
    #                                 else:
    #                                     file.write("\nFresh Zone")
    #                     else:
    #                         file.write("\nNo demand zone patterns found.")

    #                     # Supply Zones
    #                     file.write("\n\nSupply Zones:")
    #                     if supply_zones:  # Check if supply_zones is not empty
    #                         for i, (start, end, pattern, base_count) in enumerate(supply_zones):
    #                             dist_from_cmp = abs((cmp - supply_proximal_lines[i]) / cmp) * 100
    #                             if abs(dist_from_cmp) <= threshold_percent:  # Check if dist_from_cmp is within threshold
    #                                 file.write(f"\n\nZone {i+1}: Start Date: {data.index[start].date()}, End Date: {data.index[end].date()}")
    #                                 file.write(f"\nPattern Name: {pattern}, Number of Base Candle: {base_count}")
    #                                 file.write(f"\nDistance from CMP: {dist_from_cmp:.2f}%")
    #                                 if supply_proximal_lines:
    #                                     file.write(f"\nProximal Line Price: {supply_proximal_lines[i]:.2f}")
    #                                 if supply_distal_lines:  # Include distal line price if available
    #                                     file.write(f"\nDistal Line Price: {supply_distal_lines[i]:.2f}")
    #                                 # Include zone range
    #                                     file.write(f"\nZone Range: {supply_zone_ranges[i]:.2f}")
    #                                 # Check if proximal line is tested
    #                                 tested = self.is_zone_tested(data, start, end, supply_proximal_lines[i])
    #                                 if tested:
    #                                     file.write("\nZone is Tested")
    #                                 else:
    #                                     file.write("\nFresh Zone")
    #                     else:
    #                         file.write("\nNo supply zone patterns found.")

    #                     file.write("\n\n")
                    
    #     print("Analysis completed and results saved.")

    # @measure_time
    def findBbandsSqueeze(self,fullData, screenDict, saveDict, filter=4):
        """
        The TTM Squeeze indicator measures the relationship between the 
        Bollinger Bands and Keltner's Channel. When the volatility increases, 
        so does the distance between the bands, and conversely, when the 
        volatility declines, the distance also decreases. The Squeeze indicator 
        finds sections of the Bollinger Bands study which fall inside the 
        Keltner's Channels.
        
        At the moment this squeeze happens, a price breakout from the upper 
        Bollinger Band would indicate the possibility of an uptrend in the 
        future. This is backed by the fact that once the price starts breaking 
        out of the bands, it would mean a relaxation of the squeeze and the 
        possibility of high market volatility and price movement in the future. 
        Similarly, a price breakout from the lower Bollinger Band after a squeeze 
        would indicate the possibility of a downtrend in the future and an 
        increased market volatility in the same direction. When the market 
        finishes a move, the indicator turns off, which corresponds to bands 
        having pushed well outside the range of Keltner's Channels.
        """
        if fullData is None or len(fullData) < 20:
            return False
        oldestRecordsFirst_df = fullData.head(30).copy()
        latestRecordsFirst_df = oldestRecordsFirst_df[::-1].tail(30)
        latestRecordsFirst_df = latestRecordsFirst_df.fillna(0)
        latestRecordsFirst_df = latestRecordsFirst_df.replace([np.inf, -np.inf], 0)
        # Bollinger bands
        latestRecordsFirst_df.loc[:,'BBands-U'], latestRecordsFirst_df.loc[:,'BBands-M'], latestRecordsFirst_df.loc[:,'BBands-L'] = pktalib.BBANDS(latestRecordsFirst_df["close"], 20)
        # compute Keltner's channel
        latestRecordsFirst_df['low_kel'], latestRecordsFirst_df['upp_kel'] = pktalib.KeltnersChannel(latestRecordsFirst_df["high"], latestRecordsFirst_df["low"],latestRecordsFirst_df["close"],20)
        # squeeze indicator
        def in_squeeze(df):
            return df['low_kel'] < df['BBands-L'] < df['BBands-U'] < df['upp_kel']

        latestRecordsFirst_df['squeeze'] = latestRecordsFirst_df.apply(in_squeeze, axis=1)

        # Let's review just the previous 3 candles including today (at the end)
        latestRecordsFirst_df = latestRecordsFirst_df.tail(3)
        # stock is coming out of the squeeze
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        candle3Sqz = latestRecordsFirst_df.iloc[-3]["squeeze"]
        candle1Sqz = latestRecordsFirst_df.iloc[-1]["squeeze"]
        candle2Sqz = latestRecordsFirst_df.iloc[-2]["squeeze"]
        if candle3Sqz and not candle1Sqz:
            # 3rd candle from the most recent one was in squeeze but the most recent one is not.
            if filter not in [1,3,4]: # Buy/Sell/All
                return False
            # decide which action to take by comparing distances                
            distance_to_upper = abs(latestRecordsFirst_df['BBands-U'].values[-1] - latestRecordsFirst_df["close"].values[-1])
            distance_to_lower = abs(latestRecordsFirst_df['BBands-L'].values[-1] - latestRecordsFirst_df["close"].values[-1])
            
            action = False
            if distance_to_upper < distance_to_lower:
                if filter not in [1,4]: # Buy/All
                    return False
                action = True
            elif filter not in [3,4]: # Sell/All
                return False
            screenDict["Pattern"] = saved[0] + (colorText.GREEN if action else colorText.FAIL) + f"BBands-SQZ-{'Buy' if action else 'Sell'}" + colorText.END
            saveDict["Pattern"] = saved[1] + f"TTM-SQZ-{'Buy' if action else 'Sell'}"
            return True
        elif candle3Sqz and candle2Sqz and candle1Sqz:
            # Last 3 candles in squeeze
            if filter not in [2,4]: # SqZ/All
                return False
            screenDict["Pattern"] = f'{saved[0]}{colorText.WARN}TTM-SQZ{colorText.END}'
            saveDict["Pattern"] = f'{saved[1]}TTM-SQZ'
            return True
        return False

    # Find accurate breakout value
    def findBreakingoutNow(self, df, fullData, saveDict, screenDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        reversedData = fullData[::-1].copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        recentCandleHeight = self.getCandleBodyHeight(recent)
        if len(data) < 11 or recentCandleHeight <= 0:
            return False
        totalCandleHeight = 0
        candle = 0
        while candle < 10:
            candle += 1
            candleHeight = abs(self.getCandleBodyHeight(data[candle:]))
            totalCandleHeight += candleHeight

        reversedData.loc[:,'BBands-U'], reversedData.loc[:,'BBands-M'], reversedData.loc[:,'BBands-L'] = pktalib.BBANDS(reversedData["close"], 20)
        reversedData = reversedData[::-1]
        recents = reversedData.head(6)
        ulr = self.non_zero_range(recents.loc[:,'BBands-U'], recents.loc[:,'BBands-L'])
        maxOfLast5Candles = ulr.tail(5).max()
        # bandwidth = 100 * ulr / recents.loc[:,'BBands-M']
        # percent = self.non_zero_range(recents.loc[:,"close"], recents.loc[:,'BBands-L']) / ulr
        saveDict["bbands_ulr_ratio_max5"] = round(ulr.iloc[0]/maxOfLast5Candles,2) #percent.iloc[0]
        screenDict["bbands_ulr_ratio_max5"] = saveDict["bbands_ulr_ratio_max5"]
        # saveDict["bbands_bandwidth"] = bandwidth.iloc[0]
        # screenDict["bbands_bandwidth"] = saveDict["bbands_bandwidth"]
        # saveDict["bbands_ulr"] = ulr.iloc[0]
        # screenDict["bbands_ulr"] = saveDict["bbands_ulr"]

        return (
            recentCandleHeight > 0
            and totalCandleHeight > 0
            and (recentCandleHeight >= 3 * (float(totalCandleHeight / candle)))
        )

    #@measure_time
    # Find accurate breakout value
    def findBreakoutValue(
        self, df, screenDict, saveDict, daysToLookback, alreadyBrokenout=False
    ):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        data = data[1:]
        maxHigh = round(data.describe()["high"]["max"], 2)
        maxClose = round(data.describe()["close"]["max"], 2)
        recentClose = round(recent["close"].iloc[0], 2)
        if np.isnan(maxClose) or np.isnan(maxHigh):
            saveDict["Breakout"] = "BO: 0 R: 0"
            screenDict["Breakout"] = (
                colorText.WARN + "BO: 0 R: 0" + colorText.END
            )
            # self.default_logger.info(
            #     f'For Stock:{saveDict["Stock"]}, the breakout is unknown because max-high ({maxHigh}) or max-close ({maxClose}) are not defined.'
            # )
            return False
        if maxHigh > maxClose:
            if (maxHigh - maxClose) <= (maxHigh * 2 / 100):
                saveDict["Breakout"] = "BO: " + str(maxClose) + " R: " + str(maxHigh)
                if recentClose >= maxClose:
                    screenDict["Breakout"] = (
                        colorText.GREEN
                        + "BO: "
                        + str(maxClose)
                        + colorText.END
                        + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                        + " R: "
                        + str(maxHigh)
                        + colorText.END
                    )
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, has a breakout because max-high ({maxHigh}) >= max-close ({maxClose})'
                    # )
                    return True and alreadyBrokenout and self.getCandleType(recent)
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, does not have a breakout yet because max-high ({maxHigh}) < max-close ({maxClose})'
                # )
                screenDict["Breakout"] = (
                    colorText.FAIL
                    + "BO: "
                    + str(maxClose)
                    + colorText.END
                    + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                    + " R: "
                    + str(maxHigh)
                    + colorText.END
                )
                return not alreadyBrokenout
            noOfHigherShadows = len(data[data.high > maxClose])
            if daysToLookback / noOfHigherShadows <= 3:
                saveDict["Breakout"] = "BO: " + str(maxHigh) + " R: 0"
                if recentClose >= maxHigh:
                    screenDict["Breakout"] = (
                        colorText.GREEN
                        + "BO: "
                        + str(maxHigh)
                        + " R: 0"
                        + colorText.END
                    )
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) >= max-high ({maxHigh})'
                    # )
                    return True and alreadyBrokenout and self.getCandleType(recent)
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, does not have a breakout yet because recent-close ({recentClose}) < max-high ({maxHigh})'
                # )
                screenDict["Breakout"] = (
                    colorText.FAIL
                    + "BO: "
                    + str(maxHigh)
                    + " R: 0"
                    + colorText.END
                )
                return not alreadyBrokenout
            saveDict["Breakout"] = "BO: " + str(maxClose) + " R: " + str(maxHigh)
            if recentClose >= maxClose:
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) >= max-close ({maxClose})'
                # )
                screenDict["Breakout"] = (
                    colorText.GREEN
                    + "BO: "
                    + str(maxClose)
                    + colorText.END
                    + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                    + " R: "
                    + str(maxHigh)
                    + colorText.END
                )
                return True and alreadyBrokenout and self.getCandleType(recent)
            # self.default_logger.info(
            #     f'Stock:{saveDict["Stock"]}, does not have a breakout yet because recent-close ({recentClose}) < max-high ({maxHigh})'
            # )
            screenDict["Breakout"] = (
                colorText.FAIL
                + "BO: "
                + str(maxClose)
                + colorText.END
                + (colorText.GREEN if recentClose >= maxHigh else colorText.FAIL)
                + " R: "
                + str(maxHigh)
                + colorText.END
            )
            return not alreadyBrokenout
        else:
            saveDict["Breakout"] = "BO: " + str(maxClose) + " R: 0"
            if recentClose >= maxClose:
                # self.default_logger.info(
                #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) >= max-close ({maxClose})'
                # )
                screenDict["Breakout"] = (
                    colorText.GREEN
                    + "BO: "
                    + str(maxClose)
                    + " R: 0"
                    + colorText.END
                )
                return True and alreadyBrokenout and self.getCandleType(recent)
            # self.default_logger.info(
            #     f'Stock:{saveDict["Stock"]}, has a breakout because recent-close ({recentClose}) < max-close ({maxClose})'
            # )
            screenDict["Breakout"] = (
                colorText.FAIL
                + "BO: "
                + str(maxClose)
                + " R: 0"
                + colorText.END
            )
            return not alreadyBrokenout

    def findBullishAVWAP(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        reversedData = data[::-1]  # Reverse the dataframe so that its the oldest date first
        # Find the anchor point. Find the candle where there's a major dip.
        majorLow = reversedData["low"].min()
        lowRow = reversedData[reversedData["low"] == majorLow]
        anchored_date = lowRow.index[0]
        avwap = pktalib.AVWAP(df=reversedData,anchored_date=anchored_date)
        if 'anchored_VWAP' not in reversedData.keys():
            reversedData.loc[:,'anchored_VWAP'] =avwap
        recentOpen = reversedData["open"].tail(1).head(1).iloc[0]
        recentClose = reversedData["close"].tail(1).head(1).iloc[0]
        recentLow = reversedData["low"].tail(1).head(1).iloc[0]
        recentAVWAP = reversedData["anchored_VWAP"].tail(1).head(1).iloc[0]
        recentVol = reversedData["volume"].tail(1).head(1).iloc[0]
        prevVol = reversedData["volume"].tail(2).head(1).iloc[0]
        avwap.replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna(inplace=True)
        reversedData = reversedData.tail(len(avwap))
        diffFromAVWAP = (abs(recentClose-recentAVWAP)/recentAVWAP) * 100
        x = reversedData.index
        y = avwap.astype(float)
        # Create a sequance of integers from 0 to x.size to use in np.polyfit() call
        x_seq = np.arange(x.size)
        # call numpy polyfit() method with x_seq, y 
        fit = np.polyfit(x_seq, y, 1)
        fit_fn = np.poly1d(fit)
        slope = fit[0]
        # print('Slope = ', fit[0], ", ","Intercept = ", fit[1])
        # print(fit_fn)
        isBullishAVWAP = (slope <= 1 and # AVWAP is flat
                recentOpen == recentLow and recentLow !=0 and # Open = Low candle
                recentClose > recentAVWAP and recentAVWAP != 0 and # price near AVWAP
                recentVol > (self.configManager.volumeRatio)*prevVol and prevVol != 0 and # volumes spiked
                diffFromAVWAP <= self.configManager.anchoredAVWAPPercentage)

        if isBullishAVWAP:
            saveDict["AVWAP"] = round(recentAVWAP,2)
            screenDict["AVWAP"] = round(recentAVWAP,2)
            saveDict["Anchor"] = str(anchored_date).split(" ")[0]
            screenDict["Anchor"] = str(anchored_date).split(" ")[0]
        return isBullishAVWAP

    # Find stocks that are bullish intraday: RSI crosses 55, Macd Histogram positive, price above EMA 10
    def findBullishIntradayRSIMACD(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["RSI12"] = pktalib.RSI(data["close"], 12)
        data["EMA10"] = pktalib.EMA(data["close"], 10)
        data["EMA200"] = pktalib.EMA(data["close"], 200)
        macd = pktalib.MACD(data["close"], 10, 18, 9)[2].tail(1)
        recent = data.tail(1)
        cond1 = recent["RSI12"].iloc[0] > 55
        cond2 = cond1 and (macd.iloc[:1][0] > 0)
        cond3 = cond2 and (recent["close"].iloc[0] > recent["EMA10"].iloc[0])
        cond4 = cond3 and (recent["close"].iloc[0] > recent["EMA200"].iloc[0])
        return cond4

    # Find stocks with RSI(14) divergence signals
    def findRSIDivergence(self, df, divergence_type='bullish', saveDict=None, screenDict=None):
        """
        Find stocks showing RSI(14) divergence patterns.

        Parameters:
        -----------
        df : DataFrame
            Stock price data with OHLC
        divergence_type : str
            Type of divergence to detect: 'bullish', 'bearish', 'hidden_bullish', 'hidden_bearish', 'any'
        saveDict : dict
            Dictionary to save additional screening data
        screenDict : dict
            Dictionary for screen output data

        Returns:
        --------
        bool
            True if divergence is detected, False otherwise
        """
        if df is None or len(df) == 0:
            return False

        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first

        # Detect divergences using pktalib
        divergences = pktalib.detect_rsi_divergence(data, rsi_period=14, swing_order=5, tolerance=2)

        # Check recent divergence signals (last 5 bars)
        recent_bars = 5
        has_divergence = False
        divergence_desc = []

        if divergence_type == 'bullish' or divergence_type == 'any':
            if np.any(divergences['regular_bullish'][-recent_bars:]):
                has_divergence = True
                divergence_desc.append("Regular Bullish")

        if divergence_type == 'bearish' or divergence_type == 'any':
            if np.any(divergences['regular_bearish'][-recent_bars:]):
                has_divergence = True
                divergence_desc.append("Regular Bearish")

        if divergence_type == 'hidden_bullish' or divergence_type == 'any':
            if np.any(divergences['hidden_bullish'][-recent_bars:]):
                has_divergence = True
                divergence_desc.append("Hidden Bullish")

        if divergence_type == 'hidden_bearish' or divergence_type == 'any':
            if np.any(divergences['hidden_bearish'][-recent_bars:]):
                has_divergence = True
                divergence_desc.append("Hidden Bearish")

        # Store divergence information in dictionaries if found
        if has_divergence and saveDict is not None:
            saveDict['RSI_Divergence'] = ', '.join(divergence_desc)
        if has_divergence and screenDict is not None:
            screenDict['RSI Div'] = ', '.join(divergence_desc)

        return has_divergence

    def findBuySellSignalsFromATRTrailing(self,df, key_value=1, atr_period=10, ema_period=200,buySellAll=1,saveDict=None,screenDict=None):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first

        # Calculate ATR and xATRTrailingStop
        xATR = np.array(pktalib.ATR(data["high"], data["low"], data["close"], timeperiod=atr_period))
        nLoss = key_value * xATR
        src = data["close"]
        # Initialize arrays
        xATRTrailingStop = np.zeros(len(data))
        xATRTrailingStop[0] = src[0] - nLoss[0]

        # Calculate xATRTrailingStop using vectorized operations
        mask_1 = (src > np.roll(xATRTrailingStop, 1)) & (np.roll(src, 1) > np.roll(xATRTrailingStop, 1))
        mask_2 = (src < np.roll(xATRTrailingStop, 1)) & (np.roll(src, 1) < np.roll(xATRTrailingStop, 1))
        mask_3 = src > np.roll(xATRTrailingStop, 1)

        xATRTrailingStop = np.where(mask_1, np.maximum(np.roll(xATRTrailingStop, 1), src - nLoss), xATRTrailingStop)
        xATRTrailingStop = np.where(mask_2, np.minimum(np.roll(xATRTrailingStop, 1), src + nLoss), xATRTrailingStop)
        xATRTrailingStop = np.where(mask_3, src - nLoss, xATRTrailingStop)

        mask_buy = (np.roll(src, 1) < xATRTrailingStop) & (src > np.roll(xATRTrailingStop, 1))
        mask_sell = (np.roll(src, 1) > xATRTrailingStop) & (src < np.roll(xATRTrailingStop, 1))

        pos = np.zeros(len(data))
        pos = np.where(mask_buy, 1, pos)
        pos = np.where(mask_sell, -1, pos)
        pos[~((pos == 1) | (pos == -1))] = 0

        ema = np.array(pktalib.EMA(data["close"], timeperiod=ema_period))

        buy_condition_utbot = (xATRTrailingStop > ema) & (pos > 0) & (src > ema)
        sell_condition_utbot = (xATRTrailingStop < ema) & (pos < 0) & (src < ema)

        # The resulting trend array holds values of 1 (buy), -1 (sell), or 0 (neutral).
        trend = np.where(buy_condition_utbot, 1, np.where(sell_condition_utbot, -1, 0))
        trend_arr = np.array(trend)
        data.insert(len(data.columns), "trend", trend_arr)
        trend = trend[0]
        saveDict["B/S"] = "Buy" if trend == 1 else ("Sell" if trend == -1 else "NA")
        screenDict["B/S"] = (colorText.GREEN + "Buy") if trend == 1 else ((colorText.FAIL+ "Sell") if trend == -1 else (colorText.WARN + "NA")) + colorText.END
        return buySellAll == trend

    # 1. Cup Formation (Bowl)
    # During the cup formation phase, the price experiences a prolonged downtrend or consolidation, 
    # creating a rounded or U-shaped bottom. This phase represents a period of price stabilization, 
    # where investors who bought at higher levels are selling to cut their losses, and new buyers 
    # cautiously enter the market as they see potential value at these lower price levels. The 
    # psychology during this phase includes:
        # Capitulation and Despair:
        # The initial phase of the cup is marked by capitulation, where panicked investors sell off 
        # their holdings due to fear and negative sentiment.
    # Value Perception:
        # As the price stabilizes and gradually starts to rise, some investors perceive value in the 
        # stock at these lower levels, leading to accumulation of shares.
    
    # 2. Handle Formation
    # The handle formation phase follows the cup’s rounded bottom, characterized by a short-term 
    # decline in price. This decline typically ranges from 10% to 20% and is often referred to as 
    # the “handle” of the pattern. During this phase, the psychology involves:
    # Consolidation and Profit-Taking:
        # After the cup’s advance, some investors decide to take profits, leading to a brief pullback 
        # in price. This retracement is seen as a normal part of the market cycle.
    # Temporary Skepticism:
        # The pullback in price could make some investors skeptical about the stock’s future prospects, 
        # creating a cautious sentiment.
    
    # 3. Breakout and Upside Potential
    # The psychology behind the breakout from the handle involves the culmination of buying pressure 
    # exceeding selling pressure. This breakout is signaled when the price breaks above the resistance 
    # level formed by the cup’s rim. Investors who missed the earlier opportunity or who had been 
    # waiting for confirmation now step in, leading to renewed buying interest. The psychology during 
    # this phase includes:
    # Confirmation of Strength:
        # The breakout above the resistance level validates the bullish sentiment and confirms that the 
        # consolidation phase is ending. This attracts traders looking for confirmation before committing 
        # capital.
    # Fear of Missing Out (FOMO):
        # As the price starts to rise and gain momentum, FOMO can kick in, driving more investors to buy 
        # in at fear of missing out on potential gains.
    # Recovery and Optimism:
        # The price’s ability to surpass previous highs reinforces optimism, encouraging further buying 
        # from both existing and new investors.
    def findCupAndHandlePattern(self, df, stockName):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        
        # Check if index is timezone-aware and convert to naive if needed
        if data.index.tz is not None:
            # Convert timezone-aware index to naive (remove timezone)
            data.index = data.index.tz_localize(None)
        
        # Also convert any datetime columns if they exist
        for col in data.select_dtypes(include=['datetime64']).columns:
            if data[col].dt.tz is not None:
                data[col] = data[col].dt.tz_localize(None)
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first

        df_point = pd.DataFrame(columns=['StockName', 'DateK', 'DateA', 'DateB', 'DateC', 'DateD', 'Gamma'])

        data = data.reset_index()
        data['Date'] = data['Date'].apply(lambda x : x.strftime('%Y-%m-%d'))
        data['Close_ch'] = data["close"].shift(+1)
        data['rpv'] = ((data["close"] / data['Close_ch']) - 1) * data["volume"]
        data['SMA50_Volume'] = data.volume.rolling(50).mean()
        data['SMA50_rpv'] = data.rpv.rolling(50).mean()

        T = 0
        i = 1
        t = 51
        foundStockWithCupNHandle = False
        while t < len(data)-T:
            dat = data.loc[t:]
            Dk = dat.loc[t]['Date']
            Pk = dat.loc[t]["close"]   
            # search for region K to A
            k = 25
            while k > 15:
                #print('Searching SETUP with width = ', k)
                datA = dat.loc[:t+k] # Dk = t
                # first find absolute maxima point A
                Da_index = datA[datA["close"] == max(datA["close"])]['Date'].index[0]
                Da_value = datA[datA["close"] == max(datA["close"])]['Date'].values[0]
                Pa_index = datA[datA["close"] == max(datA["close"])]["close"].index[0]
                Pa_value = datA[datA["close"] == max(datA["close"])]["close"].values[0]
                uprv1 = abs(datA.loc[t:Da_index].loc[datA['rpv'] > 0, :]['rpv'].mean())
                dprv1 = abs(datA.loc[t:Da_index].loc[datA['rpv'] <= 0, :]['rpv'].mean())
                if (dprv1 == 'NaN') | (dprv1 == 0):
                    dprv1 = datA['SMA50_rpv'].mean()   
                alpha1 = uprv1/dprv1
                #delta = Pa_index/t 
                delta = Pa_value/Pk
                if (delta > 1) & (alpha1 > 1):
                    #print('Okay good setup! Lets move on now')
                    a = 40
                    while a > 10:
                        #print('Lets search for LEFT SIDE CUP with width = ', a)
                        datB = dat.loc[Da_index:Da_index+a]
                        Db_index = datB[datB["close"] == min(datB["close"])]['Date'].index[0]
                        Db_value = datB[datB["close"] == min(datB["close"])]['Date'].values[0]
                        Pb_index = datB[datB["close"] == min(datB["close"])]["close"].index[0]
                        Pb_value = datB[datB["close"] == min(datB["close"])]["close"].values[0]
                        avg_vol = datB["volume"].mean()
                        avg_ma_vol = data['SMA50_Volume'].mean()
                        if (Pb_value < Pa_value) & (avg_vol < avg_ma_vol):
                            #print("Voila! You found the bottom, it's all uphill from here")
                            b = a
                            while b > round(a/3):
                                #print("Let's search for RIGHT SIDE CUP with width = ", b)
                                datC = dat.loc[Db_index:Db_index+b+1]
                                Dc_index = datC[datC["close"] == max(datC["close"])]['Date'].index[0]
                                Dc_value = datC[datC["close"] == max(datC["close"])]['Date'].values[0]
                                Pc_index = datC[datC["close"] == max(datC["close"])]["close"].index[0]
                                Pc_value = datC[datC["close"] == max(datC["close"])]["close"].values[0]
                                uprv2 = abs(datC.loc[datC['rpv'] > 0, :]['rpv'].mean())
                                dprv2 = abs(datC.loc[datC['rpv'] <= 0, :]['rpv'].mean())
                                if (dprv2 == 'NaN') | (dprv2 == 0):
                                    dprv2 = datC['SMA50_rpv'].mean()      
                                alpha2 = uprv2/dprv2
                                if (Pc_value > Pb_value) & (alpha2 > 1):
                                    #print("Almost there... be patient now! :D")
                                    # search for region C to D
                                    c = b/2
                                    while c > round(b/4):
                                        #print("Let's search for the handle now with width = ", c)
                                        #print(t, " ", k, " ", a, " ", b, " ", c)
                                        datD = dat.loc[Dc_index:Dc_index+c+1]
                                        Dd_index = datD[datD["close"] == min(datD["close"])]['Date'].index[0]
                                        Dd_value = datD[datD["close"] == min(datD["close"])]['Date'].values[0]
                                        Pd_index = datD[datD["close"] == min(datD["close"])]["close"].index[0]
                                        Pd_value = datD[datD["close"] == min(datD["close"])]["close"].values[0]
                                        uprv3 = abs(datD.loc[datD['rpv'] > 0, :]['rpv'].mean())
                                        dprv3 = abs(datD.loc[datD['rpv'] <= 0, :]['rpv'].mean())
                                        if (dprv3 == 'NaN') | (dprv3 == 0):
                                            dprv3 = datD['SMA50_rpv'].mean()      
                                        beta = uprv2/dprv3
                                        if (Pd_value <= Pc_value) & (Pd_value > 0.8 * Pc_value + 0.2 * Pb_value) & (beta > 1):
                                            if (Pc_value <= Pa_value) & (Pd_value > Pb_value):
                                                foundStockWithCupNHandle = True
                                                gamma = math.log(alpha2) + math.log(beta) + delta
                                                df_point.loc[len(df_point)] = [stockName, Dk, Da_value, Db_value, Dc_value, Dd_value, gamma]
                                                #print("Hurrah! Got "+str(i)+" hits!")
                                                k = 15
                                                a = 10
                                                b = round(a/3)
                                                c = round(b/4)
                                                i = i+1
                                                t = t+15
                                                break
                                        c = c-1
                                b = b-1
                        a = a-1
                k = k-1
            t = t + 1
        return foundStockWithCupNHandle, df_point

    def get_dynamic_order(self,df_src):
        """Dynamically calculate 'order' parameter for local extrema detection based on volatility."""
        df = df_src.copy()
        
        # Check if index is timezone-aware and convert to naive if needed
        if df.index.tz is not None:
            # Convert timezone-aware index to naive (remove timezone)
            df.index = df.index.tz_localize(None)
        
        # Also convert any datetime columns if they exist
        for col in df.select_dtypes(include=['datetime64']).columns:
            if df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
        avg_volatility = df['Volatility'].mean()
        
        # If volatility is high, require more data points to confirm a cup
        if avg_volatility > df["close"].mean() * 0.02:  
            return int(df["close"].mean() * 0.2) + 1  # Higher volatility → require more confirmation
        elif avg_volatility < df["close"].mean() * 0.005:  
            return int(df["close"].mean() * 0.05) + 1  # Lower volatility → allow faster pattern detection
        else:
            return 15  # Default case

    def validate_cup(self, df_src, cup_start, cup_bottom, cup_end):
        """
        Validate if the detected cup meets shape and depth criteria.
        
        A proper cup should have:
        1. U-shape (not V-shape) - prices arc smoothly
        2. Reasonable depth (10-40%)
        3. Symmetrical left and right sides
        4. Volume contraction at bottom
        """
        df = df_src.copy()
        
        # Handle timezone-aware indices - ONLY if index is DatetimeIndex
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Also convert any datetime columns if they exist
        for col in df.select_dtypes(include=['datetime64']).columns:
            if hasattr(df[col].dt, 'tz') and df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
        
        # Get price points using iloc since we're using integer indices
        start_price = df.iloc[cup_start]["close"]
        bottom_price = df.iloc[cup_bottom]["close"]
        end_price = df.iloc[cup_end]["close"]
        
        # =============================================================
        # CRITERION 1: Cup Depth (10% - 40% is healthy)
        # =============================================================
        depth = (start_price - bottom_price) / start_price * 100
        if depth < 8 or depth > 45:
            return False
        
        # =============================================================
        # CRITERION 2: Rim Symmetry (left and right rims within 5%)
        # =============================================================
        rim_diff_pct = abs(start_price - end_price) / start_price * 100
        if rim_diff_pct > 5:
            return False
        
        # =============================================================
        # CRITERION 3: U-Shape Validation (not V-shaped)
        # =============================================================
        # Check middle of cup - should be in lower half
        midpoint_idx = cup_start + (cup_end - cup_start) // 2
        midpoint_price = df.iloc[midpoint_idx]["close"]
        midpoint_position = (midpoint_price - bottom_price) / (start_price - bottom_price) * 100
        
        if midpoint_position > 40:  # Middle should be in lower 40% of cup
            return False
        
        # =============================================================
        # CRITERION 4: Smooth Arc (progressive price movement)
        # =============================================================
        # Left side prices should gradually descend, right side gradually ascend
        left_step = max(1, (cup_bottom - cup_start) // 10)
        right_step = max(1, (cup_end - cup_bottom) // 10)
        
        left_side_prices = [df.iloc[i]["close"] for i in range(cup_start, cup_bottom + 1, left_step)]
        right_side_prices = [df.iloc[i]["close"] for i in range(cup_bottom, cup_end + 1, right_step)]
        
        # Check for monotonic descent on left side (with some tolerance)
        left_descending = True
        for i in range(len(left_side_prices) - 1):
            if left_side_prices[i] < left_side_prices[i+1] * 0.98:
                left_descending = False
                break
        
        # Check for monotonic ascent on right side (with some tolerance)
        right_ascending = True
        for i in range(len(right_side_prices) - 1):
            if right_side_prices[i] > right_side_prices[i+1] * 1.02:
                right_ascending = False
                break
        
        if not (left_descending or right_ascending):
            # Allow slight wobbles, but reject severe choppiness
            left_volatility = np.std(left_side_prices) / np.mean(left_side_prices) if left_side_prices else 1
            right_volatility = np.std(right_side_prices) / np.mean(right_side_prices) if right_side_prices else 1
            if left_volatility > 0.05 or right_volatility > 0.05:  # More than 5% volatility
                return False
        
        # =============================================================
        # CRITERION 5: Cup Width (minimum 15 days, maximum 180 days)
        # =============================================================
        cup_width = cup_end - cup_start
        if cup_width < 15 or cup_width > 180:
            return False
        
        return True

    def validate_volume_for_cup(self, df_src, cup_start, cup_end, handle_end, volume_prices=None):
        """
        Ensure proper volume pattern for Cup and Handle:
        1. Volume declines into the cup bottom
        2. Volume is low and flat during handle formation
        3. Volume surges on breakout
        """
        df = df_src.copy()
        
        # Handle timezone-aware indices - ONLY if index is DatetimeIndex
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Also convert any datetime columns if they exist
        for col in df.select_dtypes(include=['datetime64']).columns:
            if hasattr(df[col].dt, 'tz') and df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
        
        # Check if volume column exists
        if "volume" not in df.columns:
            return True  # Skip volume validation if no volume data
        
        volume_prices = df["volume"]
        
        try:
            # =============================================================
            # CRITERION 1: Volume declines into cup bottom
            # =============================================================
            cup_length = cup_end - cup_start
            if cup_length > 10:
                # Volume in early cup vs late cup
                early_cup_end = cup_start + cup_length // 3
                late_cup_start = cup_end - cup_length // 3
                
                early_volume = volume_prices.iloc[cup_start:early_cup_end].mean()
                late_volume = volume_prices.iloc[late_cup_start:cup_end].mean()
                
                # Volume should be lower near the bottom (late cup)
                if early_volume > 0 and late_volume > early_volume * 1.1:
                    return False  # Volume increased into bottom (bad)
            
            # =============================================================
            # CRITERION 2: Volume contraction during handle
            # =============================================================
            handle_length = handle_end - cup_end
            if handle_length > 3:
                handle_volume = volume_prices.iloc[cup_end:handle_end].mean()
                cup_volume = volume_prices.iloc[cup_start:cup_end].mean()
                
                # Handle volume should be lower than cup average
                if cup_volume > 0 and handle_volume > cup_volume * 0.9:
                    return False  # Handle volume not contracting enough
            
            # =============================================================
            # CRITERION 3: Volume should trend downward in handle
            # =============================================================
            if handle_length > 5:
                handle_first_half = volume_prices.iloc[cup_end:cup_end + handle_length//2].mean()
                handle_second_half = volume_prices.iloc[cup_end + handle_length//2:handle_end].mean()
                
                # Volume should be lower in second half of handle (drying up)
                if handle_first_half > 0 and handle_second_half > handle_first_half * 0.85:
                    return False  # Volume not drying up sufficiently
            
            return True
            
        except Exception as e:
            if self.default_logger:
                self.default_logger.debug(f"Volume validation error: {e}")
            return True  # Don't reject pattern due to volume calculation errors
                
    def find_cup_and_handle(self, df_src, saveDict=None, screenDict=None, order=0):
        """
        Detect Cup and Handle pattern with integrated validation methods.
        
        Enhanced with 20 EMA retest and momentum confirmation for better signal quality.
        
        When configManager.cupAndHandle_20EMARetestOrMomentum is True:
        1. After cup formation, the algorithm checks if price is retesting the 20 EMA
        for handle formation (ideal entry point)
        2. OR checks for momentum confirmation (volume surge + price action)
        3. Returns True if either condition is met
        
        Args:
            df_src: DataFrame with OHLCV data (newest first)
            saveDict: Dictionary for saving results
            screenDict: Dictionary for screen display
            order: Order for extremum detection (auto-calculated if 0)
        
        Returns:
            tuple: (is_valid, pattern_details) where pattern_details contains indices
        """
        try:
            from scipy.signal import argrelextrema
        except ImportError:
            if self.default_logger:
                self.default_logger.warning("scipy.signal.argrelextrema not available")
            return False, None
        
        # =========================================================================
        # INPUT VALIDATION
        # =========================================================================
        if df_src is None or len(df_src) < 90:
            return False, None
        
        # Get configuration for EMA retest/momentum check
        check_ema_retest = getattr(self.configManager, 'cupAndHandle_20EMARetestOrMomentum', False)
        ema_period = 20  # Standard 20 EMA for retest confirmation
        
        # Make a copy and handle timezone
        df = df_src.copy()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        for col in df.select_dtypes(include=['datetime64']).columns:
            if df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
        
        # Ensure data is sorted with oldest first for pattern detection
        df_oldest_first = df[::-1].reset_index(drop=True)
        
        # Calculate 20 EMA for retest confirmation
        if check_ema_retest:
            df_oldest_first['EMA20'] = pktalib.EMA(df_oldest_first["close"], timeperiod=ema_period)
        
        close_prices = df_oldest_first["close"].values
        n = len(close_prices)
        
        # =========================================================================
        # STEP 1: DETECT LOCAL MINIMA AND MAXIMA
        # =========================================================================
        if order <= 0:
            order = max(5, min(15, n // 15))
        
        local_min_idx = argrelextrema(close_prices, np.less, order=order)[0]
        local_max_idx = argrelextrema(close_prices, np.greater, order=order)[0]
        
        if len(local_min_idx) < 2 or len(local_max_idx) < 3:
            return False, None
        
        # =========================================================================
        # STEP 2: FIND VALID CUP PATTERNS
        # =========================================================================
        valid_cups = []
        
        for bottom_idx in local_min_idx:
            if bottom_idx < 15 or bottom_idx > n - 30:
                continue
            
            # Find left and right rims
            left_candidates = [i for i in local_max_idx if i < bottom_idx]
            right_candidates = [i for i in local_max_idx if i > bottom_idx]
            
            if not left_candidates or not right_candidates:
                continue
            
            left_rim_idx = max(left_candidates)
            right_rim_idx = min(right_candidates)
            
            cup_start, cup_bottom, cup_end = left_rim_idx, bottom_idx, right_rim_idx
            
            # Use the validate_cup method
            if not self.validate_cup(df_oldest_first, cup_start, cup_bottom, cup_end):
                continue
            
            valid_cups.append((cup_start, cup_bottom, cup_end, close_prices[cup_start]))
        
        if not valid_cups:
            return False, None
        
        # =========================================================================
        # STEP 3: DETECT HANDLE AND VALIDATE VOLUME
        # =========================================================================
        best_pattern = None
        best_score = 0
        
        # Store retest and momentum status for reporting
        has_ema_retest = False
        has_momentum = False
        
        for cup_start, cup_bottom, cup_end, cup_rim_price in valid_cups:
            # Search for handle after cup end
            handle_search_end = min(cup_end + 35, n - 5)
            if handle_search_end <= cup_end + 3:
                continue
            
            # Find handle bottom
            handle_slice = close_prices[cup_end:handle_search_end]
            handle_bottom_local_idx = np.argmin(handle_slice)
            handle_bottom_idx = cup_end + handle_bottom_local_idx
            
            handle_low = close_prices[handle_bottom_idx]
            cup_bottom_price = close_prices[cup_bottom]
            cup_left_price = close_prices[cup_start]
            
            # Handle should be in upper half of cup
            cup_mid_price = (cup_left_price + cup_bottom_price) / 2
            if handle_low < cup_mid_price:
                continue
            
            # Calculate handle decline
            cup_depth_pct = (cup_left_price - cup_bottom_price) / cup_left_price * 100
            handle_decline_pct = (close_prices[cup_end] - handle_low) / close_prices[cup_end] * 100
            handle_decline_of_cup = (handle_decline_pct / cup_depth_pct * 100) if cup_depth_pct > 0 else 100
            
            # Handle decline should be 10-50% of cup depth
            if handle_decline_of_cup < 10 or handle_decline_of_cup > 50:
                continue
            
            # Validate volume pattern (if volume data exists)
            volume_valid = self.validate_volume_for_cup(df_oldest_first, cup_start, cup_end, handle_bottom_idx)
            if not volume_valid:
                continue
            
            # =========================================================================
            # STEP 3.5: 20 EMA RETEST AND MOMENTUM CHECK (if enabled)
            # =========================================================================
            ema_retest_valid = True  # Default to True if check is disabled
            momentum_valid = True     # Default to True if check is disabled
            
            if check_ema_retest:
                ema_retest_valid = False
                momentum_valid = False
                
                # Get recent price and EMA data around the handle
                recent_start = max(0, cup_end - 10)
                recent_end = min(n, handle_bottom_idx + 10)
                
                if 'EMA20' in df_oldest_first.columns:
                    ema_values = df_oldest_first['EMA20'].iloc[recent_start:recent_end].values
                    price_values = close_prices[recent_start:recent_end]
                    
                    # Check if price is retesting 20 EMA (touching or very close to EMA)
                    for i in range(len(price_values)):
                        if len(ema_values) > i and ema_values[i] > 0:
                            distance_to_ema = abs(price_values[i] - ema_values[i]) / ema_values[i] * 100
                            if distance_to_ema < 1.5:  # Within 1.5% of 20 EMA
                                ema_retest_valid = True
                                break
                    
                    # Alternative: Check if price is bouncing off 20 EMA from below
                    for i in range(1, len(price_values)):
                        if len(ema_values) > i:
                            # Price was below EMA, now above EMA (bounce)
                            if (price_values[i-1] < ema_values[i-1] and 
                                price_values[i] > ema_values[i]):
                                distance_to_ema = abs(price_values[i] - ema_values[i]) / ema_values[i] * 100
                                if distance_to_ema < 2.0:  # Within 2% after bounce
                                    ema_retest_valid = True
                                    break
                
                # Check for momentum confirmation
                # Momentum conditions:
                # 1. Volume surge in recent days
                # 2. Price making higher highs after handle
                # 3. RSI showing bullish momentum if available
                
                if 'volume' in df_oldest_first.columns:
                    # Volume surge check
                    volume_data = df_oldest_first['volume'].iloc[handle_bottom_idx:min(n, handle_bottom_idx + 10)].values
                    if len(volume_data) >= 5:
                        recent_volume = np.mean(volume_data[:5])
                        prior_volume = np.mean(df_oldest_first['volume'].iloc[max(0, cup_end-20):cup_end].values)
                        
                        if prior_volume > 0 and recent_volume > prior_volume * 1.3:
                            momentum_valid = True
                
                # Price momentum check
                if not momentum_valid:
                    # Check for higher highs after handle
                    post_handle_prices = close_prices[handle_bottom_idx:min(n, handle_bottom_idx + 15)]
                    if len(post_handle_prices) >= 3:
                        if (post_handle_prices[1] > post_handle_prices[0] and 
                            post_handle_prices[2] > post_handle_prices[1]):
                            momentum_valid = True
                
                # RSI momentum check if available
                if not momentum_valid and 'RSI' in df_oldest_first.columns:
                    rsi_values = df_oldest_first['RSI'].iloc[handle_bottom_idx:min(n, handle_bottom_idx + 10)].values
                    if len(rsi_values) >= 2:
                        # RSI rising from oversold/neutral levels
                        if rsi_values[-1] > rsi_values[0] and rsi_values[-1] > 55:
                            momentum_valid = True
                
                # # For pattern to be valid, either EMA retest OR momentum must be true
                # if not (ema_retest_valid or momentum_valid):
                #     continue  # Skip this cup if neither condition is met
            
            # =========================================================================
            # STEP 4: CHECK FOR BREAKOUT
            # =========================================================================
            breakout_idx = None
            for i in range(handle_bottom_idx + 1, min(handle_bottom_idx + 20, n)):
                if close_prices[i] > cup_rim_price * 0.995:
                    breakout_idx = i
                    break
            
            # Calculate quality score
            score = 0
            
            # Cup symmetry (30 points max)
            symmetry = 100 - abs(cup_left_price - close_prices[cup_end]) / cup_left_price * 100
            score += symmetry * 0.3
            
            # Cup depth (30 points max)
            if 15 <= cup_depth_pct <= 30:
                score += 30
            elif 10 <= cup_depth_pct <= 40:
                score += 20
            else:
                score += 10
            
            # Handle quality (25 points max)
            if 25 <= handle_decline_of_cup <= 35:
                score += 25
            elif 15 <= handle_decline_of_cup <= 45:
                score += 15
            else:
                score += 5
            
            # Breakout recency (15 points max)
            if breakout_idx is not None:
                days_since_breakout = n - breakout_idx
                if days_since_breakout <= 3:
                    score += 15
                elif days_since_breakout <= 10:
                    score += 10
                elif days_since_breakout <= 20:
                    score += 5
            
            # Boost score if EMA retest or momentum confirmed
            if check_ema_retest:
                if ema_retest_valid:
                    score += 10
                    self.has_ema_retest = True
                if momentum_valid:
                    score += 10
                    self.has_momentum = True
            
            if score > best_score:
                best_score = score
                best_pattern = {
                    'cup_start': cup_start,
                    'cup_bottom': cup_bottom,
                    'cup_end': cup_end,
                    'handle_bottom': handle_bottom_idx,
                    'breakout_idx': breakout_idx,
                    'cup_rim_price': cup_rim_price,
                    'cup_depth_pct': cup_depth_pct,
                    'handle_decline_pct': handle_decline_pct,
                    'score': score,
                    'ema_retest': ema_retest_valid if check_ema_retest else None,
                    'momentum': momentum_valid if check_ema_retest else None
                }
        
        # =========================================================================
        # STEP 5: RETURN RESULTS
        # =========================================================================
        if best_pattern is None or best_score < 30:
            return False, None
        
        pattern_details = (
            best_pattern['cup_start'], 
            best_pattern['cup_bottom'], 
            best_pattern['cup_end'],
            best_pattern['handle_bottom'], 
            best_pattern['breakout_idx']
        )
        
        if saveDict is not None and screenDict is not None:
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            
            # Build pattern display with additional info if retest/momentum enabled
            if check_ema_retest and (best_pattern.get('ema_retest') or best_pattern.get('momentum')):
                confirmation_tags = []
                if best_pattern.get('ema_retest'):
                    confirmation_tags.append("20EMA-Retest")
                if best_pattern.get('momentum'):
                    confirmation_tags.append("Momentum")
                confirmation_str = f" [{'+'.join(confirmation_tags)}]"
            else:
                confirmation_str = ""

            tier_quality = ""
            if "cup_depth_pct" in best_pattern and "handle_decline_pct" in best_pattern:
                # calculate quality tiers:
                tier_quality = f"[WEAK]({best_score:.0f}) "
                ideal_cup_depth_min = 15
                ideal_cup_depth_max = 30
                perfect_cup_depth_min = 20
                perfect_cup_depth_max = 25

                ideal_handle_decline_min = 5
                ideal_handle_decline_max = 15
                perfect_handle_decline_min = 8
                perfect_handle_decline_max = 12

                perfect_cup_depth = ideal_cup_depth_min <= best_pattern['cup_depth_pct'] <= ideal_cup_depth_max and perfect_cup_depth_min <= best_pattern['cup_depth_pct'] <= perfect_cup_depth_max
                ideal_cup_depth = ideal_cup_depth_min <= best_pattern['cup_depth_pct'] and best_pattern['cup_depth_pct'] <= ideal_cup_depth_max
                acceptable_cup_depth = 10 <= best_pattern['cup_depth_pct'] <= 40
                
                perfect_handle_decline = ideal_handle_decline_min <= best_pattern['handle_decline_pct'] <= ideal_handle_decline_max and perfect_handle_decline_min <= best_pattern['handle_decline_pct'] <= perfect_handle_decline_max
                ideal_handle_decline = ideal_handle_decline_min <= best_pattern['handle_decline_pct'] and best_pattern['handle_decline_pct'] <= ideal_handle_decline_max
                acceptable_handle_decline = 10 <= best_pattern['handle_decline_pct'] <= 50
                
                if perfect_cup_depth and perfect_handle_decline:
                    tier_quality = f"[PERFECT]({best_score:.0f}) "
                elif ideal_cup_depth and ideal_handle_decline:
                    tier_quality = f"[IDEAL]({best_score:.0f}) "
                elif acceptable_cup_depth and acceptable_handle_decline:
                    tier_quality = f"[ACCEPTABLE]({best_score:.0f}) "
            
            pattern_display = f"{tier_quality}Cup&Handle{confirmation_str} (D:{best_pattern['cup_depth_pct']:.0f}%, H:{best_pattern['handle_decline_pct']:.0f}%)"
            
            screenDict["Pattern"] = saved[0] + colorText.GREEN + pattern_display + colorText.END
            saveDict["Pattern"] = saved[1] + pattern_display
            saveDict["Score"] = best_score
            screenDict["Score"] = best_score
            
            # Store additional tracking info
            if check_ema_retest:
                saveDict["Cup_EMA_Retest"] = best_pattern.get('ema_retest', False)
                saveDict["Cup_Momentum"] = best_pattern.get('momentum', False)
        
        if self.default_logger and best_score >= 40:
            logger_msg = (
                f"Cup&Handle found: depth={best_pattern['cup_depth_pct']:.1f}%, "
                f"handle={best_pattern['handle_decline_pct']:.1f}%, score={best_score:.0f}"
            )
            if check_ema_retest:
                logger_msg += f", EMA_Retest={best_pattern.get('ema_retest', False)}, Momentum={best_pattern.get('momentum', False)}"
            self.default_logger.debug(logger_msg)
        
        return True, pattern_details

    def findCurrentSavedValue(self, screenDict, saveDict, key):
        existingScreen = screenDict.get(key)
        existingSave = saveDict.get(key)
        existingScreen = f"{existingScreen}, " if (existingScreen is not None and len(existingScreen) > 0) else ""
        existingSave = f"{existingSave}, " if (existingSave is not None and len(existingSave) > 0) else ""
        return existingScreen.replace("  "," "), existingSave.replace(" "," ")

    def findFibonacciRetracement(self, df, lookback_periods=None, threshold_pct=0.01,
                             high_col='high', low_col='low', close_col='close'):
        """
        Compute Fibonacci retracement levels (0.236, 0.382, 0.5, 0.618, 0.786)
        based on the highest high and lowest low in the given data.
        
        Returns:
            (is_near_level, levels_dict, (nearest_level_name, nearest_price), distance_percentage)
        """
        if df is None or len(df) < 2:
            return False, {}, None, 0

        data = df.copy()
        recent_data = data.head(lookback_periods) if lookback_periods and len(data) > lookback_periods else data

        swing_high = recent_data[high_col].max()
        swing_low = recent_data[low_col].min()
        current_price = data[close_col].iloc[0]

        if swing_high == swing_low:
            return False, {}, None, 0

        diff = swing_high - swing_low
        levels = {
            '0.236': swing_high - 0.236 * diff,
            '0.382': swing_high - 0.382 * diff,
            '0.5':   swing_high - 0.5 * diff,
            '0.618': swing_high - 0.618 * diff,
            '0.786': swing_high - 0.786 * diff,
        }

        nearest_level = None
        min_dist = float('inf')
        for name, price in levels.items():
            dist = abs(current_price - price) / current_price
            if dist < min_dist:
                min_dist = dist
                nearest_level = (name, price)

        is_near = min_dist <= threshold_pct
        return is_near, levels, nearest_level, min_dist * 100

    def findFibonacciExtension(self, df, retracement_level=0.618, lookback_periods=None,
                            threshold_pct=0.01, high_col='high', low_col='low', close_col='close'):
        """
        Identify a classic 3‑point pattern (swing high A, swing low B, retracement high C)
        and compute Fibonacci extension levels (1.272, 1.382, 1.618, 2.0, 2.618).
        """
        try:
            from scipy.signal import argrelextrema
            import numpy as np
        except ImportError:
            if self.default_logger:
                self.default_logger.warning("scipy.signal required for Fibonacci extensions")
            return False, {}, None, 0

        if df is None or len(df) < 20:
            return False, {}, None, 0

        data = df.copy()
        # Use newest-first order; need to detect local extrema
        highs = data[high_col].values
        lows = data[low_col].values
        order = max(3, len(highs) // 20)

        max_idx = argrelextrema(highs, np.greater_equal, order=order)[0]
        min_idx = argrelextrema(lows, np.less_equal, order=order)[0]

        if len(max_idx) < 2 or len(min_idx) < 1:
            return False, {}, None, 0

        # Most recent swing high A
        swing_high_idx = max_idx[-1]
        # Swing low B after A
        swing_low_idx = None
        for idx in min_idx:
            if idx > swing_high_idx:
                swing_low_idx = idx
                break
        if swing_low_idx is None:
            return False, {}, None, 0
        # Retracement high C after B
        retrace_high_idx = None
        for idx in max_idx:
            if idx > swing_low_idx:
                retrace_high_idx = idx
                break
        if retrace_high_idx is None:
            return False, {}, None, 0

        A = highs[swing_high_idx]
        B = lows[swing_low_idx]
        C = highs[retrace_high_idx]

        # Verify that C is near the expected Fibonacci retracement level
        expected_retrace = A - retracement_level * (A - B)
        if abs(C - expected_retrace) / expected_retrace > 0.05:
            return False, {}, None, 0

        move = C - B
        extension_levels = {
            '1.272': B + 1.272 * move,
            '1.382': B + 1.382 * move,
            '1.618': B + 1.618 * move,
            '2.0':   B + 2.0 * move,
            '2.618': B + 2.618 * move,
        }

        current_price = data[close_col].iloc[0]
        nearest = None
        min_dist = float('inf')
        for name, price in extension_levels.items():
            dist = abs(current_price - price) / current_price
            if dist < min_dist:
                min_dist = dist
                nearest = (name, price)

        is_near = min_dist <= threshold_pct
        return is_near, extension_levels, nearest, min_dist * 100

    def findHigherBullishOpens(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(2)
        if len(recent) < 2:
            return False
        return recent["open"].iloc[0] > recent["high"].iloc[1]

    # Find stocks that opened higher than the previous high
    def findHigherOpens(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(2)
        if len(recent) < 2:
            return False
        return recent["open"].iloc[0] > recent["close"].iloc[1]

    # Find DEEL Momentum
    def findHighMomentum(self, df, strict=False):
        #https://chartink.com/screener/deel-momentum-rsi-14-mfi-14-cci-14
        if df is None or len(df) < 2:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        mfis = pktalib.MFI(data["high"],data["low"],data["close"],data["volume"], 14)
        ccis = pktalib.CCI(data["high"],data["low"],data["close"], 14)
        sma7 = pktalib.SMA(data["close"], 7).tail(2)
        sma20 = pktalib.SMA(data["close"], 20).tail(2)
        recent = data.tail(2)
        percentChange = round((recent["close"].iloc[1] - recent["close"].iloc[0]) *100/recent["close"].iloc[0],1)
        rsi = recent["RSI"].iloc[1]
        mfi = mfis.tail(1).iloc[0]
        cci = ccis.tail(1).iloc[0]
        # Percent Change >= 1%
        # The filter checks if the current daily closing price is greater than the 
        # closing price from one day ago, increased by 1%. This means the current 
        # price should be at least 1% higher than the price from the previous day.
        # CCI > 110
        # A CCI value above 100 suggests that the stock's price is at least 10% 
        # higher than its average price over the past 14 days, reflecting strong 
        # upward momentum.
        # MFI > 68
        # MFI value above 68 suggests that the stock is experiencing strong buying 
        # pressure, indicating a potential overbought condition.
        # RSI > 68
        # RSI above 68 indicates that the stock is overbought, suggesting that it 
        # has increased by more than 68% from its average price over the last 14 days.
        deelMomentum1 = percentChange >= 1 and (rsi>= 68 and mfi >= 68 and cci >= 110)
        deelMomentum2 = (rsi>= 50 and mfi >= 50 and recent["close"].iloc[1] >= sma7.iloc[1] and 
                          recent["close"].iloc[1] >= sma20.iloc[1]) and not strict
        hasDeelMomentum = deelMomentum1 or deelMomentum2
                         
        # if self.shouldLog:
        #     self.default_logger.debug(data.head(10))
        return hasDeelMomentum

    def findIntradayHighCrossover(self, df, afterTimestamp=None):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        diff_df = None
        try:
            # Let's only consider those candles that are after the alert issue-time in the mornings + 2 candles (for buy/sell)
            diff_df = data[data.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30').to_datetime64()]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30').to_datetime64()
        except: # pragma: no cover
            diff_df = data[data.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30', utc=True)]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30', utc=True)
            pass
        dayHighAfterAlert = diff_df["high"].max()
        highRow = diff_df[diff_df["high"] >= dayHighAfterAlert]
        if highRow is not None and len(highRow) > 0:
            highRow = highRow.tail(1)
        return highRow.index[-1], highRow

    def findIntradayOpenSetup(self,df,df_intraday,saveDict,screenDict,buySellAll=1):
        if df is None or len(df) == 0 or df_intraday is None or len(df_intraday) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        previousDay = data.head(1)
        prevDayHigh = previousDay["high"].iloc[0]
        prevDayLow = previousDay["low"].iloc[0]
        candleDurations = [1,5,10,15,30]
        int_df = None
        hasIntradaySetup = False
        for candle1MinuteNumberSinceMarketStarted in candleDurations:
            try:
                int_df = df_intraday[df_intraday.index <=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+candle1MinuteNumberSinceMarketStarted}:00+05:30').to_datetime64()]
            except: # pragma: no cover
                int_df = df_intraday[df_intraday.index <=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+candle1MinuteNumberSinceMarketStarted}:00+05:30', utc=True)]
                pass
            if int_df is not None and len(int_df) > 0:
                combinedCandle = {"open":self.getMorningOpen(int_df), "high":max(int_df["high"]), 
                                "low":min(int_df["low"]),"close":self.getMorningClose(int_df),
                                "Adj Close":int_df["Adj Close"][-1],"volume":sum(int_df["volume"])}
                openPrice = combinedCandle["open"]
                lowPrice = combinedCandle["low"]
                closePrice = combinedCandle["close"]
                highPrice = combinedCandle["high"]
                if buySellAll == 1 or buySellAll == 3:
                    hasIntradaySetup = openPrice == lowPrice and openPrice < prevDayHigh and closePrice > prevDayHigh
                elif buySellAll == 2 or buySellAll == 3:
                    hasIntradaySetup = openPrice == highPrice and openPrice > prevDayLow and closePrice < prevDayLow
                if hasIntradaySetup:
                    saveDict["B/S"] = f"{'Buy' if buySellAll == 1 else ('Sell' if buySellAll == 2 else 'All')}-{candle1MinuteNumberSinceMarketStarted}m"
                    screenDict["B/S"] = (colorText.GREEN if buySellAll == 1 else (colorText.FAIL if buySellAll == 2 else colorText.WARN)) + f"{'Buy' if buySellAll == 1 else ('Sell' if buySellAll == 2 else 'All')}-{candle1MinuteNumberSinceMarketStarted}m" + colorText.END
                    break
        return hasIntradaySetup

    def findIntradayShortSellWithPSARVolumeSMA(self, df,df_intraday):
        if df is None or len(df) == 0 or df_intraday is None or len(df_intraday) == 0:
            return False
        data = df.copy()
        data_int = df_intraday.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data_int = pd.DataFrame(data_int)["close"].resample('30T', offset='15min').ohlc()
        # data_int = data_int[::-1]  # Reverse the dataframe so that its the oldest date first
        if len(data_int) < 5: # we need TMA for period 5
            return False
        data.loc[:,'PSAR'] = pktalib.psar(data["high"],data["low"],acceleration=0.08)
        data_int.loc[:,'TMA5'] = pktalib.TriMA(data_int["close"],length=5)
        recent = data.tail(4)
        recent = recent[::-1]
        recent_i = data_int[::-1]
        recent_i = recent_i.head(2)
        # recent_i = recent_i[::-1]
        if len(recent) < 4 or len(recent_i) < 2:
            return False
        # daily PSAR crossed above recent 30m TMA
        cond1 = recent["PSAR"].iloc[0] >= recent_i["TMA5"].iloc[0] and \
                recent["PSAR"].iloc[1] <= recent_i["TMA5"].iloc[1]
        # Daily volume > 1400k
        cond2 = cond1 and (recent["volume"].iloc[0] > 1400000)
        # Daily close above 50
        cond4 = cond2 and recent["close"].iloc[0] > 50
        return cond4

    def findIPOLifetimeFirstDayBullishBreak(self, df):
        if df is None or len(df) == 0 or len(df) >= 220:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data.dropna(axis=0, how="all", inplace=True) # Maybe there was no trade done at these times?
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        return data["high"].iloc[0] >= data["high"].max()

    def findMACDCrossover(self, df, afterTimestamp=None, nthCrossover=1, upDirection=True, minRSI=60):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data.dropna(axis=0, how="all", inplace=True) # Maybe there was no trade done at these times?
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macdLine, macdSignal, macdHist = pktalib.MACD(data["close"], 12, 26, 9)
        # rsi_df = pktalib.RSI(data["close"], 14)
        line_df = pd.DataFrame(macdLine)
        signal_df = pd.DataFrame(macdSignal)
        vol_df = data["volume"]
        diff_df = pd.concat([line_df, signal_df, signal_df-line_df,vol_df], axis=1)
        diff_df.columns = ["line","signal","diff","vol"]
        diff_df = diff_df[diff_df["vol"] > 0] # We're not going to do anything with a candle where there was no trade.
        # brokerSqrOfftime = None
        try:
            # Let's only consider those candles that are after the alert issue-time in the mornings + 2 candles (for buy/sell)
            diff_df = diff_df[diff_df.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30').to_datetime64()]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30').to_datetime64()
        except: # pragma: no cover
            diff_df = diff_df[diff_df.index >=  pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} {MarketHours().openHour:02}:{MarketHours().openMinute+self.configManager.morninganalysiscandlenumber + 2}:00+05:30', utc=True)]
            # brokerSqrOfftime = pd.to_datetime(f'{PKDateUtilities.tradingDate().strftime(f"%Y-%m-%d")} 15:14:00+05:30', utc=True)
            pass
        index = len(diff_df)
        crossOver = 0
        
        # Loop until we've found the nth crossover for MACD or we've reached the last point in time
        while (crossOver < nthCrossover and index > 0):
            try:
                if diff_df["diff"][index-1] < 0: # Signal line has not crossed yet and is below the zero line
                    while((diff_df["diff"][index-1] < 0 and index >=0)): # and diff_df.index <= brokerSqrOfftime): # or diff_df["rsi"][index-1] <= minRSI):
                        # Loop while Signal line has not crossed yet and is below the zero line and we've not reached the last point
                        index -= 1
                else:
                    while((diff_df["diff"][index-1] >= 0 and index >=0)): # and diff_df.index <= brokerSqrOfftime): # or diff_df["rsi"][index-1] <= minRSI):
                        # Loop until signal line has not crossed yet and is above the zero line
                        index -= 1
            except: # pragma: no cover
                continue
            crossOver += 1
        ts = diff_df.tail(len(diff_df)-index +1).head(1).index[-1]
        return ts, data[data.index == ts] #df.head(len(df) -index +1).tail(1)

    def findNR4Day(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        # https://chartink.com/screener/nr4-daily-today
        if data.tail(1)["volume"].iloc[0] <= 50000:
            return False
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["SMA10"] = pktalib.SMA(data["close"], 10)
        data["SMA50"] = pktalib.SMA(data["close"], 50)
        data["SMA200"] = pktalib.SMA(data["close"], 200)
        recent = data.tail(5)
        recent = recent[::-1]
        cond1 = (recent["high"].iloc[0] - recent["low"].iloc[0]) < (
            recent["high"].iloc[1] - recent["low"].iloc[1]
        )
        cond2 = cond1 and (recent["high"].iloc[0] - recent["low"].iloc[0]) < (
            recent["high"].iloc[2] - recent["low"].iloc[2]
        )
        cond3 = cond2 and (recent["high"].iloc[0] - recent["low"].iloc[0]) < (
            recent["high"].iloc[3] - recent["low"].iloc[3]
        )
        cond4 = cond3 and (recent["high"].iloc[0] - recent["low"].iloc[0]) < (
            recent["high"].iloc[4] - recent["low"].iloc[4]
        )
        cond5 = cond4 and (recent["SMA10"].iloc[0] > recent["SMA50"].iloc[0])
        cond6 = cond5 and (recent["SMA50"].iloc[0] > recent["SMA200"].iloc[0])
        return cond6

    def findPerfectShortSellsFutures(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data.loc[:,'BBands-U'], data.loc[:,'BBands-M'], data.loc[:,'BBands-L'] = pktalib.BBANDS(data["close"], 20)
        recent = data.tail(4)
        recent = recent[::-1]
        if len(recent) < 4:
            return False
        # 1 day ago high > 2 days ago high
        cond1 = recent["high"].iloc[1] > recent["high"].iloc[2]
        # 1 day ago close < 2 days ago high
        cond2 = cond1 and (recent["close"].iloc[1] < recent["high"].iloc[2])
        # 1 day ago volume > 3 days ago volume
        cond3 = cond2 and (recent["volume"].iloc[1] > recent["volume"].iloc[3])
        # daily high < 1 day ago high
        cond4 = cond3 and (recent["high"].iloc[0] < recent["high"].iloc[1])
        # daily close crossed below daily lower bollinger band(20,2)
        cond5 = cond4 and (recent["close"].iloc[0] <= recent["BBands-L"].iloc[0] and \
                           recent["close"].iloc[1] >= recent["BBands-L"].iloc[1])
        return cond5
    
    # Find potential breakout stocks
    # This scanner filters stocks whose current close price + 5% is higher
    # than the highest High price in past 200 candles and the maximum high
    # in the previous 30 candles is lower than the highest high made in the
    # previous 200 candles, starting from the previous 30th candle. At the
    # same time the current candle volume is higher than 200 SMA of volume.
    def findPotentialBreakout(self, df, screenDict, saveDict, daysToLookback):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data.head(231)
        recent = data.head(1)
        recentVolume = recent["volume"].iloc[0]
        recentClose = round(recent["close"].iloc[0] * 1.05, 2)
        highestHigh200 = round(data.head(201).tail(200).describe()["high"]["max"], 2)
        highestHigh30 = round(data.head(31).tail(30).describe()["high"]["max"], 2)
        highestHigh200From30 = round(data.tail(200).describe()["high"]["max"], 2)
        highestHigh8From30 = round(data.head(39).tail(8).describe()["high"]["max"], 2)
        data = data.head(200)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        vol200 = pktalib.SMA(data["volume"],timeperiod=200)
        data["SMA200V"] = vol200
        vol50 = pktalib.SMA(data["volume"],timeperiod=50)
        data["SMA50V"] = vol50
        recent = data.tail(1)
        sma200v = recent["SMA200V"].iloc[0]
        sma50v = recent["SMA50V"].iloc[0]
        if (
            np.isnan(recentClose)
            or np.isnan(highestHigh200)
            or np.isnan(highestHigh30)
            or np.isnan(highestHigh200From30)
            or np.isnan(highestHigh8From30)
            or np.isnan(recentVolume)
            or np.isnan(sma200v)
            or np.isnan(sma50v)
        ):
            return False
        if (
            (recentClose > highestHigh200)
            and (((highestHigh30 < highestHigh200From30) and (recentVolume > sma200v)) or \
                 ((highestHigh30 < highestHigh8From30) and (recentVolume > sma50v))
                )
        ):
            saveDict["Breakout"] = saveDict["Breakout"] + "(Potential)"
            screenDict["Breakout"] = screenDict["Breakout"] + (
                colorText.GREEN + " (Potential)" + colorText.END
            )
            return True
        return False

    def findPriceActionCross(self, df, ma, daysToConsider=1, baseMAOrPrice=None, isEMA=False,maDirectionFromBelow=True):
        ma_val = pktalib.EMA(df["close"],int(ma)) if isEMA else pktalib.SMA(df["close"],int(ma))
        ma = ma_val.tail(daysToConsider).head(1).iloc[0]
        ma_prev = ma_val.tail(daysToConsider+1).head(1).iloc[0]
        base = baseMAOrPrice.tail(daysToConsider).head(1).iloc[0]
        base_prev = baseMAOrPrice.tail(daysToConsider+1).head(1).iloc[0]
        percentageDiff = round(100*(base-ma)/ma,1)
        if maDirectionFromBelow: # base crosses ma line from below
            return (ma <= base and ma_prev >= base_prev), percentageDiff
        else: # base crosses ma line from above
            return (ma >= base and ma_prev <= base_prev), percentageDiff
        
    def findProbableShortSellsFutures(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        recent = data.tail(4)
        recent = recent[::-1]
        if len(recent) < 4:
            return False
        # 1 day ago high > 2 days ago high
        cond1 = recent["high"].iloc[1] > recent["high"].iloc[2]
        # daily close < 1 day ago high
        cond2 = cond1 and (recent["close"].iloc[0] < recent["high"].iloc[1])
        # Daily volume > 3 days ago volume
        cond3 = cond2 and (recent["volume"].iloc[0] > recent["volume"].iloc[3])
        # daily high < 1 day ago high
        cond4 = cond3 and (recent["high"].iloc[0] < recent["high"].iloc[1])
        return cond4
    
    # Find stocks with reversing PSAR and RSI
    def findPSARReversalWithRSI(self, df, screenDict, saveDict,minRSI=50):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data[::-1]
        psar = pktalib.psar(data["high"],data["low"])
        if len(psar) < 3:
            return False
        psar = psar.tail(3)
        data = data.tail(3)
        # dayMinus2Psar = psar.iloc[0]
        dayMinus1Psar = psar.iloc[1]
        dayPSAR = psar.iloc[2]
        # dayMinus2Close = data["close"].iloc[0]
        dayMinus1Close = data["close"].iloc[1]
        dayClose = data["close"].iloc[2]
        # dayMinus2RSI = data["RSI"].iloc[0]
        dayMinus1RSI = data["RSI"].iloc[1]
        dayRSI = data["RSI"].iloc[2]
        
        hasReversal= (((dayMinus1Psar >= dayMinus1Close) and \
                    (dayClose >= dayPSAR)) and \
                    (dayMinus1RSI <= minRSI) and \
                    (dayRSI >= dayMinus1RSI))
        if hasReversal:
            saved = self.findCurrentSavedValue(screenDict,saveDict, "Pattern")
            screenDict["Pattern"] = (
                saved[0] 
                + colorText.GREEN
                + f"PSAR-RSI-Rev"
                + colorText.END
            )
            saveDict["Pattern"] = saved[1] + f"PSAR-RSI-Rev"
                # (((dayMinus2Psar >= dayMinus2Close) and \
                # ((dayMinus1Close >= dayMinus1Psar) and \
                # (dayClose >= dayPSAR))) and \
                # (dayMinus2RSI >= minRSI) and \
                # (dayMinus1RSI >= dayMinus2RSI) and \
                # (dayRSI >= dayMinus1RSI)) or \
        return hasReversal

    # Find stock reversing at given MA
    def findReversalMA(self, df, screenDict, saveDict, maLength, percentage=0.02):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        maRange = [9, 10, 20, 50, 200] if maLength in [9,10,20,50,100] else [9,10,20,50,100,maLength]
        results = []
        hasReversals = False
        data = data[::-1]
        saved = self.findCurrentSavedValue(screenDict,saveDict, "MA-Signal")
        for maLength in maRange:
            dataCopy = data
            if self.configManager.useEMA or maLength == 9:
                maRev = pktalib.EMA(dataCopy["close"], timeperiod=maLength)
            else:
                maRev = pktalib.MA(dataCopy["close"], timeperiod=maLength)
            try:
                dataCopy.drop("maRev", axis=1, inplace=True, errors="ignore")
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception:# pragma: no cover
                pass
            dataCopy.insert(len(dataCopy.columns), "maRev", maRev)
            dataCopy = dataCopy[::-1].head(4)
            bullishMAReversal = dataCopy["maRev"].iloc[0] >= dataCopy["maRev"].iloc[1] and \
                dataCopy["maRev"].iloc[1] >= dataCopy["maRev"].iloc[2] and \
                    dataCopy["maRev"].iloc[2] < dataCopy["maRev"].iloc[3]
            bullishClose = dataCopy.head(1)["close"].iloc[0] >= dataCopy.head(1)["maRev"].iloc[0]
            bearishMAReversal = dataCopy["maRev"].iloc[0] <= dataCopy["maRev"].iloc[1] and \
                dataCopy["maRev"].iloc[1] <= dataCopy["maRev"].iloc[2] and \
                    dataCopy["maRev"].iloc[2] > dataCopy["maRev"].iloc[3]
            isRecentCloseWithinPercentRange = dataCopy.equals(dataCopy[(dataCopy.close >= (dataCopy.maRev - (dataCopy.maRev * percentage))) & (dataCopy.close <= (dataCopy.maRev + (dataCopy.maRev * percentage)))])
            if (isRecentCloseWithinPercentRange and bullishClose and bullishMAReversal) or \
                (isRecentCloseWithinPercentRange and not bullishClose and bearishMAReversal):
                hasReversals = True
                results.append(str(maLength))
        if hasReversals:
            screenDict["MA-Signal"] = (
                saved[0] 
                + (colorText.GREEN if bullishMAReversal else (colorText.FAIL if bearishMAReversal else colorText.WARN))
                + f"Reversal-[{','.join(results)}]{'EMA' if (maLength == 9 or self.configManager.useEMA) else 'MA'}"
                + colorText.END
            )
            saveDict["MA-Signal"] = saved[1] + f"Reversal-[{','.join(results)}]{'EMA' if (maLength == 9 or self.configManager.useEMA) else 'MA'}"
        return hasReversals
    
    # Find stocks with rising RSI from lower levels
    def findRisingRSI(self, df, rsiKey="RSI"):
        if df is None or len(df) == 0:
            return False
        if rsiKey not in df.columns:
            return False
        data = df.copy()
        # Ensure data is sorted with latest date first (descending)
        if not data.empty and hasattr(data.index, 'sort_values'):
            try:
                data = data.sort_index(ascending=False)
            except:
                pass
        # Get the 3 most recent rows (latest date first, so head(3) gets newest 3)
        recent = data.head(3)
        if len(recent) < 3:
            return False
        # recent.iloc[0] = today (most recent), iloc[1] = yesterday, iloc[2] = day before yesterday
        dayRSI = recent["RSI"].iloc[0]  # Today's RSI
        dayMinus1RSI = recent["RSI"].iloc[1]  # Yesterday's RSI
        dayMinus2RSI = recent["RSI"].iloc[2]  # Day before yesterday's RSI
        returnValue = (dayMinus2RSI <= 35 and dayMinus1RSI > dayMinus2RSI and dayRSI > dayMinus1RSI) or \
                (dayMinus1RSI <= 35 and dayRSI > dayMinus1RSI)
        if rsiKey == "RSI":
            returnValue = self.findRisingRSI(df, rsiKey="RSIi") or returnValue
        return returnValue

    # Find stock showing RSI crossing with RSI 9 SMA
    def findRSICrossingMA(self, df, screenDict, saveDict,lookFor=1, maLength=9, rsiKey="RSI"):
        if df is None or len(df) == 0:
            return False
        if rsiKey not in df.columns:
            return False
        data = df.copy()
        data = data[::-1]
        maRsi = pktalib.MA(data[rsiKey], timeperiod=maLength)
        data = data[::-1].head(3)
        maRsi = maRsi[::-1].head(3)
        saved = self.findCurrentSavedValue(screenDict,saveDict,"Trend")
        if lookFor in [1,3] and maRsi.iloc[0] <= data[rsiKey].iloc[0] and maRsi.iloc[1] > data[rsiKey].iloc[1]:
            screenDict['MA-Signal'] = saved[0] + colorText.GREEN + f'RSI-MA-Buy' + colorText.END
            saveDict['MA-Signal'] = saved[1] + f'RSI-MA-Buy'
            return True if (rsiKey == "RSIi") else (self.findRSICrossingMA(df, screenDict, saveDict,lookFor=lookFor, maLength=maLength, rsiKey="RSIi") or True)
        elif lookFor in [2,3] and maRsi.iloc[0] >= data[rsiKey].iloc[0] and maRsi.iloc[1] < data[rsiKey].iloc[1]:
            screenDict['MA-Signal'] = saved[0] + colorText.FAIL + f'RSI-MA-Sell' + colorText.END
            saveDict['MA-Signal'] = saved[1] + f'RSI-MA-Sell'
            return True if (rsiKey == "RSIi") else (self.findRSICrossingMA(df, screenDict, saveDict,lookFor=lookFor, maLength=maLength, rsiKey="RSIi") or True)
        return False if (rsiKey == "RSIi") else (self.findRSICrossingMA(df, screenDict, saveDict,lookFor=lookFor, maLength=maLength, rsiKey="RSIi"))

    # Find price/RSI(14) divergence using swing highs/lows.
    # Bullish: price makes a lower low while RSI makes a higher low (momentum fading on the downside).
    # Bearish: price makes a higher high while RSI makes a lower high (momentum fading on the upside).
    def findRSIDivergence(self, df, screenDict=None, saveDict=None, lookFor=3, lookback=14, rsiKey="RSI"):
        if df is None or len(df) == 0:
            return False
        if rsiKey not in df.columns or "close" not in df.columns:
            return False
        data = df.copy()
        data = data[::-1]  # oldest first, so swings read left-to-right in time
        data = data.tail(lookback + 4)
        if len(data) < 9:
            return False
        closes = data["close"].to_numpy()
        rsis = data[rsiKey].to_numpy()
        n = len(closes)
        order = 2  # a bar must be the extreme within +/- `order` bars to count as a swing point

        def swingIndices(values, findHigh):
            indices = []
            for i in range(order, n - order):
                window = values[i - order:i + order + 1]
                if (findHigh and values[i] == window.max()) or (not findHigh and values[i] == window.min()):
                    indices.append(i)
            return indices

        foundBullish = False
        foundBearish = False

        if lookFor in [1, 3]:
            lows = swingIndices(closes, findHigh=False)
            if len(lows) >= 2:
                i1, i2 = lows[-2], lows[-1]
                if closes[i2] < closes[i1] and rsis[i2] > rsis[i1]:
                    foundBullish = True
                    if screenDict is not None and saveDict is not None:
                        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                        label = f"Bullish RSI({lookback}) Divergence"
                        screenDict["Pattern"] = saved[0] + colorText.GREEN + label + colorText.END
                        saveDict["Pattern"] = saved[1] + label

        if lookFor in [2, 3]:
            highs = swingIndices(closes, findHigh=True)
            if len(highs) >= 2:
                i1, i2 = highs[-2], highs[-1]
                if closes[i2] > closes[i1] and rsis[i2] < rsis[i1]:
                    foundBearish = True
                    if screenDict is not None and saveDict is not None:
                        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                        label = f"Bearish RSI({lookback}) Divergence"
                        screenDict["Pattern"] = saved[0] + colorText.FAIL + label + colorText.END
                        saveDict["Pattern"] = saved[1] + label

        return foundBullish or foundBearish

    def findRSRating(self, stock_rs_value=-1, index_rs_value=-1,df=None,screenDict={}, saveDict={}):
        if stock_rs_value <= 0:
            stock_rs_value = self.calc_relative_strength(df=df)
        rs_rating = round(100 * ( stock_rs_value / index_rs_value ),2)
        screenDict[f"RS_Rating{self.configManager.baseIndex}"] = rs_rating
        saveDict[f"RS_Rating{self.configManager.baseIndex}"] = rs_rating
        return rs_rating
    
    # Relative volatality measure
    def findRVM(self, df=None,screenDict={}, saveDict={}):
        if df is None or len(df) == 0 or len(df) < 144:
            return 0
        # RVM over the lookback period of 15 periods
        rvm = pktalib.RVM(df["high"],df["low"],df["close"],15)
        screenDict["RVM(15)"] = rvm
        saveDict["RVM(15)"] = rvm
        return rvm

    def findShortSellCandidatesForVolumeSMA(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data.loc[:,'SMAV10'] = pktalib.SMA(data["volume"], 10)
        recent = data.tail(4)
        recent = recent[::-1]
        if len(recent) < 4:
            return False
        # daily close < 1 day ago close * .97
        cond1 = recent["close"].iloc[0] < recent["close"].iloc[1] * 0.97
        # Daily volume > 100k
        cond2 = cond1 and (recent["volume"].iloc[0] > 100000)
        # Daily volume * Daily Close > 1000k
        cond3 = cond2 and (recent["volume"].iloc[0] * recent["close"].iloc[0] > 1000000)
        # Daily close above 8
        cond4 = cond3 and recent["close"].iloc[0] > 8
        cond5 = cond4 and (recent["volume"].iloc[0] > recent["SMAV10"].iloc[0] * 0.75)
        return cond5
    
    def findSuperGainersLosers(self, df, percentChangeRequired=15, gainer=True):
        if df is None or len(df) < 2:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        recent = data.tail(2)
        percentChange = round((recent["close"].iloc[1] - recent["close"].iloc[0]) *100/recent["close"].iloc[0],1)
        return percentChange >= percentChangeRequired if gainer else percentChange <= percentChangeRequired

    def findStrongBuySignals(self, df, screenDict=None, saveDict=None):
        """
        Find stocks with Strong Buy signals using multi-indicator analysis.
        
        Uses the TradingSignals class to analyze multiple technical indicators
        and returns True if the stock qualifies as a Strong Buy.
        
        Args:
            df: OHLCV DataFrame
            screenDict: Dictionary for screen display results
            saveDict: Dictionary for saving results
            
        Returns:
            True if stock is a Strong Buy, False otherwise
        """
        try:
            from pkscreener.classes.screening.signals import TradingSignals
            signals = TradingSignals(self.configManager)
            return signals.find_strong_buys(df, saveDict, screenDict)
        except Exception as e:
            if self.default_logger:
                self.default_logger.debug(f"findStrongBuySignals error: {e}")
            return False

    def findStrongSellSignals(self, df, screenDict=None, saveDict=None):
        """
        Find stocks with Strong Sell signals using multi-indicator analysis.
        
        Uses the TradingSignals class to analyze multiple technical indicators
        and returns True if the stock qualifies as a Strong Sell.
        
        Args:
            df: OHLCV DataFrame
            screenDict: Dictionary for screen display results
            saveDict: Dictionary for saving results
            
        Returns:
            True if stock is a Strong Sell, False otherwise
        """
        try:
            from pkscreener.classes.screening.signals import TradingSignals
            signals = TradingSignals(self.configManager)
            return signals.find_strong_sells(df, saveDict, screenDict)
        except Exception as e:
            if self.default_logger:
                self.default_logger.debug(f"findStrongSellSignals error: {e}")
            return False
        # """
        # Enhanced sell signal detection using ATR trailing stop + bearish add-ons.
        # """
        # if df is None or len(df) < 20:
        #     return False

        # # First compute ATR-based signals (gives Sell/Confidence)
        # has_signal, _ = self.findATRTrailingStops(
        #     df, 
        #     sensitivity=2,           # standard multiplier
        #     atr_period=10,
        #     ema_period=200,
        #     buySellAll=2,            # 2 = sell signals only
        #     min_confidence=60,       # strong sell needs >=60
        #     use_scoring=True,
        #     consecutive_confirmation_bars=2,
        #     volume_confirmation=True,
        #     sell_threshold=3,        # require stronger sell signals
        #     min_bars_between_sell_signals=1,
        #     stock_name=saveDict.get("Stock", "Unknown") if saveDict else "Unknown"
        # )
        
        # if has_signal and saveDict is not None:
        #     # Override with "STRONG_SELL" label for consistency
        #     saveDict['Signal'] = "STRONG_SELL"
        #     if screenDict is not None:
        #         screenDict['Signal'] = colorText.FAIL + "STRONG SELL" + colorText.END
        
        # return has_signal

    def findAllBuySignals(self, df, screenDict=None, saveDict=None):
        """
        Find stocks with any Buy signal (Strong, Regular, or Weak).
        
        Uses the TradingSignals class to analyze multiple technical indicators
        and returns True if the stock has any buy signal.
        
        Args:
            df: OHLCV DataFrame
            screenDict: Dictionary for screen display results
            saveDict: Dictionary for saving results
            
        Returns:
            True if stock has a buy signal, False otherwise
        """
        try:
            from pkscreener.classes.screening.signals import TradingSignals
            signals = TradingSignals(self.configManager)
            return signals.find_buy_signals(df, saveDict, screenDict)
        except Exception as e:
            if self.default_logger:
                self.default_logger.debug(f"findAllBuySignals error: {e}")
            return False

    def findAllSellSignals(self, df, screenDict=None, saveDict=None):
        """
        Find stocks with any Sell signal (Strong, Regular, or Weak).
        
        Uses the TradingSignals class to analyze multiple technical indicators
        and returns True if the stock has any sell signal.
        
        Args:
            df: OHLCV DataFrame
            screenDict: Dictionary for screen display results
            saveDict: Dictionary for saving results
            
        Returns:
            True if stock has a sell signal, False otherwise
        """
        try:
            from pkscreener.classes.screening.signals import TradingSignals
            signals = TradingSignals(self.configManager)
            return signals.find_sell_signals(df, saveDict, screenDict)
        except Exception as e:
            if self.default_logger:
                self.default_logger.debug(f"findAllSellSignals error: {e}")
            return False

    #@measure_time
    # Find out trend for days to lookback
    def findTrend(self, df, screenDict, saveDict, daysToLookback=None, stockName=""):
        if df is None or len(df) == 0:
            return "Unknown"
        data = df.copy()
        if daysToLookback is None:
            daysToLookback = self.configManager.daysToLookback
        data = data.head(daysToLookback)
        data = data[::-1]
        data = data.set_index(np.arange(len(data)))
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        saved = self.findCurrentSavedValue(screenDict,saveDict,"Trend")
        try:
            with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
                data["tops"] = data["close"].iloc[
                    list(
                        pktalib.argrelextrema(
                            np.array(data["close"]), np.greater_equal, order=1
                        )[0]
                    )
                ]
            data = data.fillna(0)
            data = data.replace([np.inf, -np.inf], 0)

            try:
                # if len(data) < daysToLookback:
                #     self.default_logger.debug(data)
                #     raise StockDataNotAdequate
                data = data.replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna()
                if len(data["tops"][data.tops > 0]) > 1:
                    slope = np.polyfit(
                        data.index[data.tops > 0], data["tops"][data.tops > 0], 1
                    )[0]
                else:
                    slope = 0
            except np.linalg.LinAlgError as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                screenDict["Trend"] = (
                    saved[0] + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Unknown"
                return saveDict["Trend"]
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                slope, _ = 0, 0
            angle = np.rad2deg(np.arctan(slope))
            if angle == 0:
                screenDict["Trend"] = (
                    saved[0] + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Unknown"
            elif angle <= 30 and angle >= -30:
                screenDict["Trend"] = (
                    saved[0] + colorText.WARN + "Sideways" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Sideways"
            elif angle >= 30 and angle < 61:
                screenDict["Trend"] = (
                    saved[0] + colorText.GREEN + "Weak Up" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Weak Up"
            elif angle >= 60:
                screenDict["Trend"] = (
                    saved[0] + colorText.GREEN + "Strong Up" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Strong Up"
            elif angle <= -30 and angle > -61:
                screenDict["Trend"] = (
                    saved[0] + colorText.FAIL + "Weak Down" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Weak Down"
            elif angle < -60:
                screenDict["Trend"] = (
                    saved[0] + colorText.FAIL + "Strong Down" + colorText.END
                )
                saveDict["Trend"] = saved[1] + "Strong Down"
        except np.linalg.LinAlgError as e: # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            screenDict["Trend"] = (
                saved[0] + colorText.WARN + "Unknown" + colorText.END
            )
            saveDict["Trend"] = saved[1] + "Unknown"
        return saveDict["Trend"]

    # Find stocks approching to long term trendlines
    def findTrendlines(self, df, screenDict, saveDict, percentage=0.05):
        # period = int("".join(c for c in self.configManager.period if c.isdigit()))
        # if len(data) < period:
        #     return False
        data = df.copy()
        data = data[::-1]
        data["Number"] = np.arange(len(data)) + 1
        data_low = data.copy()
        points = 30

        """ Ignoring the Resitance for long-term purpose
        while len(data_high) > points:
            slope, intercept, r_value, p_value, std_err = linregress(x=data_high['Number'], y=data_high["high"])
            data_high = data_high.loc[data_high["high"] > slope * data_high['Number'] + intercept]
        slope, intercept, r_value, p_value, std_err = linregress(x=data_high['Number'], y=data_high["close"])
        data['Resistance'] = slope * data['Number'] + intercept
        """

        while len(data_low) > points:
            try:
                slope, intercept, r_value, p_value, std_err = linregress(
                    x=data_low["Number"], y=data_low["low"]
                )
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                continue
            data_low = data_low.loc[
                data_low["low"] < slope * data_low["Number"] + intercept
            ]

        slope, intercept, r_value, p_value, std_err = linregress(
            x=data_low["Number"], y=data_low["close"]
        )
        data["Support"] = slope * data["Number"] + intercept
        now = data.tail(1)

        limit_upper = now["Support"].iloc[0] + (now["Support"].iloc[0] * percentage)
        limit_lower = now["Support"].iloc[0] - (now["Support"].iloc[0] * percentage)
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        if limit_lower < now["close"].iloc[0] < limit_upper and slope > 0.15:
            screenDict["Pattern"] = (
                saved[0] + colorText.GREEN + "Trendline-Support" + colorText.END
            )
            saveDict["Pattern"] = saved[1] + "Trendline-Support"
            return True

        """ Plots for debugging
        import matplotlib.pyplot as plt
        fig, ax1 = plt.subplots(figsize=(15,10))
        color = 'tab:green'
        xdate = [x.date() for x in data.index]
        ax1.set_xlabel('Date', color=color)
        ax1.plot(xdate, data.close, label="close", color=color)
        ax1.tick_params(axis='x', labelcolor=color)

        ax2 = ax1.twiny() # ax2 and ax1 will have common y axis and different x axis, twiny
        ax2.plot(data.Number, data.Resistance, label="Res")
        ax2.plot(data.Number, data.Support, label="Sup")

        plt.legend()
        plt.grid()
        plt.show()
        """
        return False

    # @measure_time
    def findUptrend(self, df, screenDict, saveDict, testing, stock,onlyMF=False,hostData=None,exchangeName="INDIA",refreshMFAndFV=True,downloadOnly=False):
        # shouldProceed = True
        isUptrend = False
        isDowntrend = False
        is50DMAUptrend = False
        is50DMADowntrend = False
        decision = ""
        dma50decision = ""
        fairValue = 0
        fairValueDiff = 0
        # if df is None or len(df) < 220 or testing:
        #     shouldProceed = False
        if df is not None:
            try:
                data = df.copy()
                data = data[::-1] # Ensure oldest first
                today_sma = pktalib.SMA(data["close"], timeperiod=50)
                sma_minus9 = pktalib.SMA(data.head(len(data)-9)["close"], timeperiod=50)
                sma_minus14 = pktalib.SMA(data.head(len(data)-14)["close"], timeperiod=50)
                sma_minus20 = pktalib.SMA(data.head(len(data)-20)["close"], timeperiod=50)
                today_lma = pktalib.SMA(data["close"], timeperiod=200)
                lma_minus20 = pktalib.SMA(data.head(len(data)-20)["close"], timeperiod=200)
                lma_minus80 = pktalib.SMA(data.head(len(data)-80)["close"], timeperiod=200)
                lma_minus100 = pktalib.SMA(data.head(len(data)-100)["close"], timeperiod=200)
                today_lma = today_lma.iloc[len(today_lma)-1] if today_lma is not None else 0
                lma_minus20 = lma_minus20.iloc[len(lma_minus20)-1] if lma_minus20 is not None else 0
                lma_minus80 = lma_minus80.iloc[len(lma_minus80)-1] if lma_minus80 is not None else 0
                lma_minus100 = lma_minus100.iloc[len(lma_minus100)-1] if lma_minus100 is not None else 0
                today_sma = today_sma.iloc[len(today_sma)-1] if today_sma is not None else 0
                sma_minus9 = sma_minus9.iloc[len(sma_minus9)-1] if sma_minus9 is not None else 0
                sma_minus14 = sma_minus14.iloc[len(sma_minus14)-1] if sma_minus14 is not None else 0
                sma_minus20 = sma_minus20.iloc[len(sma_minus20)-1] if sma_minus20 is not None else 0
                isUptrend = (today_lma > lma_minus20) or (today_lma > lma_minus80) or (today_lma > lma_minus100)
                isDowntrend = (today_lma < lma_minus20) and (today_lma < lma_minus80) and (today_lma < lma_minus100)
                is50DMAUptrend = (today_sma > sma_minus9) or (today_sma > sma_minus14) or (today_sma > sma_minus20)
                is50DMADowntrend = (today_sma < sma_minus9) and (today_sma < sma_minus14) and (today_sma < sma_minus20)
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception:  # pragma: no cover
                # self.default_logger.debug(e, exc_info=True)
                pass
        decision = f'T:{colorText.UPARROW}' if isUptrend else (f'T:{colorText.DOWNARROW}' if isDowntrend else '')
        dma50decision = f't:{colorText.UPARROW}' if is50DMAUptrend else (f't:{colorText.DOWNARROW}' if is50DMADowntrend else '')
        mf_inst_ownershipChange = 0
        change_millions =""
        mf = ""
        mfs = ""
        if refreshMFAndFV:
            try:
                mf_inst_ownershipChange = self.getMutualFundStatus(stock,onlyMF=onlyMF,hostData=hostData,force=(hostData is None or hostData.empty or not ("MF" in hostData.columns or "FII" in hostData.columns)) and downloadOnly,exchangeName=exchangeName)
                if isinstance(mf_inst_ownershipChange, pd.Series):
                    mf_inst_ownershipChange = 0
                roundOff = 2
                millions = round(mf_inst_ownershipChange/1000000,roundOff)
                while float(millions) == 0 and roundOff <=5:
                    roundOff +=1
                    millions = round(mf_inst_ownershipChange/1000000,roundOff)
                change_millions = f"({millions}M)"
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
            try:
                #Let's get the fair value, either saved or fresh from service
                fairValue = self.getFairValue(stock,hostData,force=(hostData is None or hostData.empty or "FairValue" not in hostData.columns) and downloadOnly,exchangeName=exchangeName)
                if fairValue is not None and fairValue != 0:
                    ltp = saveDict["LTP"]
                    fairValueDiff = round(fairValue - ltp,0)
                    saveDict["FairValue"] = str(fairValue)
                    saveDict["FVDiff"] = fairValueDiff
                    screenDict["FVDiff"] = fairValueDiff
                    screenDict["FairValue"] = (colorText.GREEN if fairValue >= ltp else colorText.FAIL) + saveDict["FairValue"] + colorText.END
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e:  # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
            
            if mf_inst_ownershipChange > 0:
                mf = f"MFI:{colorText.UPARROW} {change_millions}"
                mfs = colorText.GREEN + mf + colorText.END
            elif mf_inst_ownershipChange < 0:
                mf = f"MFI:{colorText.DOWNARROW} {change_millions}"
                mfs = colorText.FAIL + mf + colorText.END

        # Let's get the large deals for the stock
        try:
            dealsInfo = ""
            symbolKeys = ["Ⓑ","Ⓛ","Ⓢ"] # Bulk, Block/Large and Short deals
            largeDealsData, filePath, modifiedDateTime = Archiver.findFileInAppResultsDirectory(directory=Archiver.get_user_data_dir(), fileName="large_deals.json")
            dealsFileSize = os.stat(filePath).st_size if os.path.exists(filePath) else 0
            if dealsFileSize > 0 and len(largeDealsData) > 0:
                import json
                countKeys = ["BULK_DEALS","BLOCK_DEALS","SHORT_DEALS"]
                dataKeys = ["BULK_DEALS_DATA","BLOCK_DEALS_DATA","SHORT_DEALS_DATA"]
                jsonDeals = json.loads(largeDealsData)
                index = 0
                for countKey in countKeys:
                    if countKey in jsonDeals.keys() and int(jsonDeals[countKey]) > 0 and dataKeys[index] in jsonDeals.keys() and len(jsonDeals[dataKeys[index]]) > 0:
                        for deal in jsonDeals[dataKeys[index]]:
                            if stock.upper() == deal["symbol"]:
                                buySellInfo = "" if deal["buySell"] is None else (f"({'B' if deal['buySell'] == 'BUY' else 'S'})")
                                qty = int(deal["qty"])
                                qtyInfo = f"({int(qty/1000000)}M)" if qty >= 1000000 else (f"({int(qty/1000)}K)" if qty >= 1000 else f"({qty})")
                                dealsInfo = f"{dealsInfo} {buySellInfo}{qtyInfo}{symbolKeys[index]}"
                    index += 1
        except: # pragma: no cover
            pass

        saved = self.findCurrentSavedValue(screenDict,saveDict,"Trend")
        decision_scr = (colorText.GREEN if isUptrend else (colorText.FAIL if isDowntrend else colorText.WARN)) + f"{decision}" + colorText.END
        dma50decision_scr = (colorText.GREEN if is50DMAUptrend else (colorText.FAIL if is50DMADowntrend else colorText.WARN)) + f"{dma50decision}" + colorText.END
        saveDict["Trend"] = f"{saved[1]} {decision}{dma50decision} {mf}{dealsInfo}"
        for symbol in symbolKeys:
            dealParts = dealsInfo.split(" ")
            dealPartsRefined = []
            for dealPart in dealParts:
                dealPart = dealPart.replace(symbol,(colorText.GREEN+symbol+colorText.END) if ("(B)" in dealPart) else ((colorText.FAIL+symbol+colorText.END) if ("(S)" in dealPart) else symbol))
                dealPartsRefined.append(dealPart)
            dealsInfo = f' {" ".join(dealPartsRefined).strip()}'
        screenDict["Trend"] = f"{saved[0].strip()} {decision_scr}{dma50decision_scr}{mfs}{dealsInfo}".replace("   "," ").replace("  "," ")
        saveDict["MFI"] = mf_inst_ownershipChange
        screenDict["MFI"] = mf_inst_ownershipChange
        return isUptrend, mf_inst_ownershipChange, fairValueDiff

    def getCandleBodyHeight(self, dailyData):
        bodyHeight = dailyData["close"].iloc[0] - dailyData["open"].iloc[0]
        return bodyHeight

    # Private method to find candle type
    # True = Bullish, False = Bearish
    def getCandleType(self, dailyData):
        return bool(dailyData["close"].iloc[0] >= dailyData["open"].iloc[0])

    def getFairValue(self, stock, hostData=None, force=False,exchangeName="INDIA"):
        if hostData is None or len(hostData) < 1:
            hostData = pd.DataFrame()
        # Let's look for fair values
        fairValue = 0
        if "FairValue" in hostData.columns and PKDateUtilities.currentDateTime().weekday() <= 4:
            try:
                fairValue = hostData.loc[hostData.index[-1],"FairValue"]
            except (KeyError,IndexError):
                    pass
        else:
            if PKDateUtilities.currentDateTime().weekday() >= 5 or force:
                security = None
                # Refresh each saturday or sunday or when not found in saved data
                try:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        security = Stock(stock,exchange=exchangeName)
                except ValueError: # pragma: no cover
                    # We did not find the stock? It's okay. Move on to the next one.
                    pass
                except (TimeoutError, ConnectionError) as e:
                    self.default_logger.debug(e, exc_info=True)
                    pass
                except KeyboardInterrupt: # pragma: no cover
                    raise KeyboardInterrupt
                except Exception as e: # pragma: no cover
                    self.default_logger.debug(e, exc_info=True)
                    pass
                if security is not None:
                    with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                        fv = security.fairValue()
                    if fv is not None:
                        try:
                            fvResponseValue = fv["latestFairValue"]
                            if fvResponseValue is not None:
                                fairValue = float(fvResponseValue)
                        except: # pragma: no cover
                            pass
                            # self.default_logger.debug(f"{e}\nResponse:fv:\n{fv}", exc_info=True)
                    fairValue = round(float(fairValue),1)
                    try:
                        hostData.loc[hostData.index[-1],"FairValue"] = fairValue
                    except (KeyError,IndexError):
                        pass
        return fairValue

    def getFreshMFIStatus(self, stock,exchangeName="INDIA"):
        changeStatusDataMF = None
        changeStatusDataInst = None
        netChangeMF = 0
        netChangeInst = 0
        latest_mfdate = None
        latest_instdate = None
        security = None
        try:
            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                security = Stock(stock,exchange=exchangeName)
        except ValueError:
            # We did not find the stock? It's okay. Move on to the next one.
            pass
        except (TimeoutError, ConnectionError) as e:
            self.default_logger.debug(e, exc_info=True)
            pass
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            pass
        if security is not None:
            try:
                with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                    changeStatusRowsMF = security.mutualFundOwnership(top=5)
                    changeStatusRowsInst = security.institutionOwnership(top=5)
                    changeStatusDataMF = security.mutualFundFIIChangeData(changeStatusRowsMF)
                    changeStatusDataInst = security.mutualFundFIIChangeData(changeStatusRowsInst)
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                # TypeError or ConnectionError because we could not find the stock or MFI data isn't available?
                pass
            lastDayLastMonth = PKDateUtilities.last_day_of_previous_month(PKDateUtilities.currentDateTime())
            lastDayLastMonth = lastDayLastMonth.strftime("%Y-%m-%dT00:00:00.000")
            if changeStatusDataMF is not None and len(changeStatusDataMF) > 0:
                df_groupedMF = changeStatusDataMF.groupby("date", sort=False)
                for mfdate, df_groupMF in df_groupedMF:
                    netChangeMF = df_groupMF["changeAmount"].sum()
                    latest_mfdate = mfdate
                    break
            if changeStatusDataInst is not None and len(changeStatusDataInst) > 0:
                df_groupedInst = changeStatusDataInst.groupby("date", sort=False)
                for instdate, df_groupInst in df_groupedInst:
                    if (latest_mfdate is not None and latest_mfdate == instdate) or (latest_mfdate is None) or (instdate == lastDayLastMonth):
                        netChangeInst = df_groupInst["changeAmount"].sum()
                        latest_instdate = instdate
                    break
        return netChangeMF,netChangeInst,latest_mfdate,latest_instdate

    def getMorningClose(self,df):
        close = df["close"][-1]
        index = len(df)
        while close is np.nan and index >= 0:
            close = df["close"][index - 1]
            index -= 1
        return close

    def getMorningOpen(self,df):
        open = df["open"][0]
        index = 0
        while open is np.nan and index < len(df):
            open = df["open"][index + 1]
            index += 1
        return open

    def getMutualFundStatus(self, stock,onlyMF=False, hostData=None, force=False,exchangeName="INDIA"):
        if hostData is None or len(hostData) < 1:
            hostData = pd.DataFrame()
        
        netChangeMF = 0
        netChangeInst = 0
        latest_mfdate = None
        latest_instdate = None
        needsFreshUpdate = True
        lastDayLastMonth = PKDateUtilities.last_day_of_previous_month(PKDateUtilities.currentDateTime())
        if hostData is not None and len(hostData) > 0:
            if "MF" in hostData.columns or "FII" in hostData.columns:
                try:
                    netChangeMF = hostData.loc[hostData.index[-1],"MF"]
                except (KeyError,IndexError):
                    pass
                try:
                    netChangeInst = hostData.loc[hostData.index[-1],"FII"]
                except (KeyError,IndexError):
                    pass
                try:
                    latest_mfdate = hostData.loc[hostData.index[-1],"MF_Date"]
                    if isinstance(latest_mfdate, float):
                        latest_mfdate = datetime.datetime.fromtimestamp(latest_mfdate).strftime('%Y-%m-%d')
                except (KeyError,IndexError):
                    pass
                try:
                    latest_instdate = hostData.loc[hostData.index[-1],"FII_Date"]
                    if isinstance(latest_instdate, float):
                        latest_instdate = datetime.datetime.fromtimestamp(latest_instdate).strftime('%Y-%m-%d')
                except (KeyError,IndexError):
                    pass
                if latest_mfdate is not None:
                    saved_mfdate = PKDateUtilities.dateFromYmdString(latest_mfdate.split("T")[0])
                else:
                    saved_mfdate = lastDayLastMonth - datetime.timedelta(1)
                if latest_instdate is not None:
                    saved_instdate = PKDateUtilities.dateFromYmdString(latest_instdate.split("T")[0])
                else:
                    saved_instdate = lastDayLastMonth - datetime.timedelta(1)
                today = PKDateUtilities.currentDateTime()
                needsFreshUpdate = (saved_mfdate.date() < lastDayLastMonth.date()) and (saved_instdate.date() < lastDayLastMonth.date())
            else:
                needsFreshUpdate = True

        if needsFreshUpdate and force:
            netChangeMF, netChangeInst, latest_mfdate, latest_instdate = self.getFreshMFIStatus(stock,exchangeName=exchangeName)
            if netChangeMF is not None:
                try:
                    hostData.loc[hostData.index[-1],"MF"] = netChangeMF
                except (KeyError,IndexError):
                    pass
            else:
                netChangeMF = 0
            if latest_mfdate is not None:
                try:
                    hostData.loc[hostData.index[-1],"MF_Date"] = latest_mfdate
                except (KeyError,IndexError):
                    pass
            if netChangeInst is not None:
                try:
                    hostData.loc[hostData.index[-1],"FII"] = netChangeInst
                except (KeyError,IndexError):
                    pass
            else:
                netChangeInst = 0
            if latest_instdate is not None:
                try:
                    hostData.loc[hostData.index[-1],"FII_Date"] = latest_instdate
                except (KeyError,IndexError):
                    pass
        lastDayLastMonth = lastDayLastMonth.strftime("%Y-%m-%dT00:00:00.000")
        if onlyMF:
            return netChangeMF
        if latest_instdate == latest_mfdate:
            return (netChangeMF + netChangeInst)
        elif latest_mfdate == lastDayLastMonth:
            return netChangeMF
        elif latest_instdate == lastDayLastMonth:
            return netChangeInst
        else:
            # find the latest date
            if latest_mfdate is not None:
                latest_mfdate = PKDateUtilities.dateFromYmdString(latest_mfdate.split("T")[0])
            if latest_instdate is not None:
                latest_instdate = PKDateUtilities.dateFromYmdString(latest_instdate.split("T")[0])
            return netChangeMF if ((latest_mfdate is not None) and latest_mfdate > (latest_instdate if latest_instdate is not None else (latest_mfdate - datetime.timedelta(1)))) else netChangeInst


    def getNiftyPrediction(self, df):
        import warnings

        warnings.filterwarnings("ignore")
        data = df.copy()
        data = data.rename(columns=str.capitalize)
        # df.columns = df.columns.str.title()
        # data.columns = [col.capitalize() for col in data.columns]

        model, pkl = Utility.tools.getNiftyModel()
        if model is None or pkl is None:
            return 0, "Unknown", "Unknown"
        with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
            data = data[pkl["columns"]]
            ### v2 Preprocessing
            data["High"] = data["High"].pct_change() * 100
            data["Low"] = data["Low"].pct_change() * 100
            data["Open"] = data["Open"].pct_change() * 100
            data["Close"] = data["Close"].pct_change() * 100
            data = data.iloc[-1]
            ###
            data = pkl["scaler"].transform([data])
            with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
                pred = model.predict(data)[0]
        if pred > 0.5:
            outText = "BEARISH"
            out = (
                colorText.FAIL
                + outText
                + colorText.END
            )
            sug = "Hold your Short position!"
        else:
            outText = "BULLISH"
            out = (
                colorText.GREEN
                + outText
                + colorText.END
            )
            sug = "Stay Bullish!"
        if PKDateUtilities.isClosingHour():
            OutputControls().printOutput(
                colorText.WARN
                + "Note: The AI prediction should be executed After 3 PM or Near to Closing time as the Prediction Accuracy is based on the Closing price!"
                + colorText.END
            )
        predictionText = "Market may Open {} next day! {}".format(out, sug)
        strengthText = "Probability/Strength of Prediction = {}%".format(
            Utility.tools.getSigmoidConfidence(pred[0])
        )
        OutputControls().printOutput(
            colorText.BLUE
            + "\n"
            + "  [+] Nifty AI Prediction -> "
            + colorText.END
            + predictionText
            + colorText.END
        )
        OutputControls().printOutput(
            colorText.BLUE
            + "\n"
            + "  [+] Nifty AI Prediction -> "
            + colorText.END
            + strengthText
        )

        return pred, predictionText.replace(out, outText), strengthText

    def getTopsAndBottoms(self, df, window=3, numTopsBottoms=6):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data.reset_index(inplace=True)
        data.rename(columns={"index": "Date"}, inplace=True)
        data = data[data["high"]>0]
        data = data[data["low"]>0]
        data["tops"] = (data["high"].iloc[list(pktalib.argrelextrema(np.array(data["high"]), np.greater_equal, order=window)[0])].head(numTopsBottoms))
        data["bots"] = (data["low"].iloc[list(pktalib.argrelextrema(np.array(data["low"]), np.less_equal, order=window)[0])].head(numTopsBottoms))
        tops = data[data.tops > 0]
        bots = data[data.bots > 0]
        return tops, bots

    def monitorFiveEma(self, fetcher, result_df, last_signal, risk_reward=3):
        col_names = ["high", "low", "close", "5EMA"]
        data_list = ["nifty_buy", "banknifty_buy", "nifty_sell", "banknifty_sell"]

        data_tuple = fetcher.fetchFiveEmaData()
        for cnt in range(len(data_tuple)):
            d = data_tuple[cnt]
            d["5EMA"] = pktalib.EMA(d["close"], timeperiod=5)
            d = d[col_names]
            d = d.dropna().round(2)

            with SuppressOutput(suppress_stderr=True, suppress_stdout=True):
                if "sell" in data_list[cnt]:
                    streched = d[(d.low > d["5EMA"]) & (d.low - d["5EMA"] > 0.5)]
                    streched["SL"] = streched.high
                    validate = d[
                        (d.low.shift(1) > d["5EMA"].shift(1))
                        & (d.low.shift(1) - d["5EMA"].shift(1) > 0.5)
                    ]
                    old_index = validate.index
                else:
                    mask = (d.high < d["5EMA"]) & (d["5EMA"] - d.high > 0.5)  # Buy
                    streched = d[mask]
                    streched["SL"] = streched.low
                    validate = d.loc[mask.shift(1).fillna(False)]
                    old_index = validate.index
            tgt = pd.DataFrame(
                (
                    validate.close.reset_index(drop=True)
                    - (
                        (
                            streched.SL.reset_index(drop=True)
                            - validate.close.reset_index(drop=True)
                        )
                        * risk_reward
                    )
                ),
                columns=["Target"],
            )
            validate = pd.concat(
                [
                    validate.reset_index(drop=True),
                    streched["SL"].reset_index(drop=True),
                    tgt,
                ],
                axis=1,
            )
            validate = validate.tail(len(old_index))
            validate = validate.set_index(old_index)
            if "sell" in data_list[cnt]:
                final = validate[validate.close < validate["5EMA"]].tail(1)
            else:
                final = validate[validate.close > validate["5EMA"]].tail(1)

            if data_list[cnt] not in last_signal:
                last_signal[data_list[cnt]] = final
            elif data_list[cnt] in last_signal:
                try:
                    condition = last_signal[data_list[cnt]][0]["SL"][0]
                except (KeyError,IndexError) as e: # pragma: no cover
                    try:
                        condition = last_signal[data_list[cnt]]["SL"][0]
                    except (KeyError,IndexError) as e: # pragma: no cover
                        condition = None
                # if last_signal[data_list[cnt]] is not final:          # Debug - Shows all conditions
                if len(final["SL"]) > 0 and condition != final["SL"].iloc[0]:
                    # Do something with results
                    try:
                        result_df = pd.concat(
                            [
                                result_df,
                                pd.DataFrame(
                                    [
                                        [
                                            colorText.BLUE
                                            + str(final.index[0])
                                            + colorText.END,
                                            colorText.WARN
                                            + data_list[cnt].split("_")[0].upper()
                                            + colorText.END,
                                            (
                                                colorText.FAIL
                                                + data_list[cnt].split("_")[1].upper()
                                                + colorText.END
                                            )
                                            if "sell" in data_list[cnt]
                                            else (
                                                colorText.GREEN
                                                + data_list[cnt].split("_")[1].upper()
                                                + colorText.END
                                            ),
                                            colorText.FAIL
                                            + str(final.SL[0])
                                            + colorText.END,
                                            colorText.GREEN
                                            + str(final.Target[0])
                                            + colorText.END,
                                            f"1:{risk_reward}",
                                        ]
                                    ],
                                    columns=result_df.columns,
                                ),
                            ],
                            axis=0,
                        )
                        result_df.reset_index(drop=True, inplace=True)
                    except KeyboardInterrupt: # pragma: no cover
                        raise KeyboardInterrupt
                    except Exception as e:  # pragma: no cover
                        self.default_logger.debug(e, exc_info=True)
                        pass
                    # Then update
                    last_signal[data_list[cnt]] = [final]
        if result_df is not None:
            result_df.drop_duplicates(keep="last", inplace=True)
            result_df.sort_values(by="Time", inplace=True)
        return result_df[::-1]

    def non_zero_range(self, high: pd.Series, low: pd.Series) -> pd.Series:
        """Returns the difference of two series and adds epsilon to any zero values.  This occurs commonly in crypto data when "high" = "low"."""
        diff = high - low
        if diff.eq(0).any().any():
            diff += sflt.epsilon
        return diff
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_long_min.value) & # trend strength confirmation
                        (dataframe['adx'] < self.adx_long_max.value) & # trend strength confirmation
                        (dataframe['trend_l'] > 0) &
                        (dataframe["volume"] > dataframe['volume_mean']) &
                        (dataframe["volume"] > 0)

            ),
            'enter_long'] = 1

        dataframe.loc[
            (
                        (dataframe['adx'] > self.adx_short_min.value) & # trend strength confirmation
                        (dataframe['adx'] < self.adx_short_max.value) & # trend strength confirmation
                        (dataframe['trend_s'] < 0) &
                        (dataframe["volume"] > dataframe['volume_mean_s']) # volume weighted indicator
            ),
            'enter_short'] = 1
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:

        conditions_long = []
        conditions_short = []
        dataframe.loc[:, 'exit_tag'] = ''

        exit_long = (
                # (dataframe["close"] < dataframe["low"].shift(self.sell_shift.value)) &
                (dataframe["close"] < dataframe['ema_l']) &
                (dataframe["volume"] > dataframe['volume_mean_exit'])
        )

        exit_short = (
                # (dataframe["close"] > dataframe["high"].shift(self.sell_shift_short.value)) &
                (dataframe["close"] > dataframe['ema_s']) &
                (dataframe["volume"] > dataframe['volume_mean_exit_s'])
        )


        conditions_short.append(exit_short)
        dataframe.loc[exit_short, 'exit_tag'] += 'exit_short'


        conditions_long.append(exit_long)
        dataframe.loc[exit_long, 'exit_tag'] += 'exit_long'


        if conditions_long:
            dataframe.loc[
                pd.reduce(lambda x, y: x | y, conditions_long),
                'exit_long'] = 1

        if conditions_short:
            dataframe.loc[
                pd.reduce(lambda x, y: x | y, conditions_short),
                'exit_short'] = 1
            
        return dataframe

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        if not self.dp:
            # Don't do anything if DataProvider is not available.
            return dataframe
        L_optimize_trend_alert  = self.findBuySellSignalsFromATRTrailing(dataframe=dataframe, key_value= self.key_value_l.value, atr_period= self.atr_period_l.value, ema_period=self.ema_period_l.value)
        # Long position?
        dataframe['trend_l'] = L_optimize_trend_alert['trend']
        S_optimize_trend_alert  = self.findBuySellSignalsFromATRTrailing(dataframe=dataframe, key_value= self.key_value_s.value, atr_period= self.atr_period_s.value, ema_period=self.ema_period_s.value)
        # Short position?
        dataframe['trend_s'] = S_optimize_trend_alert['trend']

        # ADX
        dataframe['adx'] = pktalib.ADX(dataframe)
        
        # RSI
        # dataframe['rsi'] = ta.RSI(dataframe)

        # EMA
        dataframe['ema_l'] = pktalib.EMA(dataframe["close"], timeperiod=self.ema_period_l_exit.value)
        dataframe['ema_s'] = pktalib.EMA(dataframe["close"], timeperiod=self.ema_period_s_exit.value)


        # Volume Weighted
        dataframe['volume_mean'] = dataframe["volume"].rolling(self.volume_check.value).mean().shift(1)
        dataframe['volume_mean_exit'] = dataframe["volume"].rolling(self.volume_check_exit.value).mean().shift(1)

        dataframe['volume_mean_s'] = dataframe["volume"].rolling(self.volume_check_s.value).mean().shift(1)
        dataframe['volume_mean_exit_s'] = dataframe["volume"].rolling(self.volume_check_exit_s.value).mean().shift(1)
        return dataframe
    
    # Preprocess the acquired data
    def preprocessData(self, df, daysToLookback=None,recentDaysToDiscard=0):
        """
        Preprocess the acquired data by calculating technical indicators and adding them as new columns to the dataframe.
        The indicators calculated include:
        - SMA (Simple Moving Average) for 50, 200, 9, and 20 periods
        - EMA (Exponential Moving Average) for 50, 200, 9, and 20 periods (if useEMA is True in config)
        - Volatility (20-day rolling standard deviation of close price)
        - VolMA (20-day rolling mean of volume)
        - RSI (Relative Strength Index) for 14 periods
        - CCI (Commodity Channel Index) for 14 periods
        - STOCHRSI (Stochastic RSI) for 14 periods with fastk_period of 5 and fastd_period of 3
        The function returns a tuple of (fullData, trimmedData) where fullData is the dataframe with all calculated indicators and trimmedData is the dataframe limited to the specified number of days to look back.

        Args:
            df (pd.DataFrame): The input dataframe in descending order containing stock data with columns like 'close', 'high', 'low', 'volume', etc.
            daysToLookback (int, optional): The number of recent days to include in the trimmedData. If None, it defaults to the value specified in the configuration manager.
        """
        assert isinstance(df, pd.DataFrame)
        data = df.copy()
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first for technical indicator calculations
        # Discard rows with dates later than the calculated cutoff
        if recentDaysToDiscard > 0:
            cutoff_date_str = PKDateUtilities.nthPastTradingDateStringFromFutureDate(recentDaysToDiscard)
            cutoff_date = datetime.datetime.strptime(cutoff_date_str, "%Y-%m-%d").date()
            # Filter: keep rows where the index date <= cutoff_date
            data = data[data.index.date <= cutoff_date]
        try:
            data = data.replace(np.inf, np.nan).replace(-np.inf, np.nan).dropna(how="all")
            if data.empty:
                return (data,data)
            # self.default_logger.info(f"Preprocessing data:\n{data.head(1)}\n")
            if daysToLookback is None:
                daysToLookback = self.configManager.daysToLookback
            volatility = df["close"].rolling(window=20).std()
            if self.configManager.useEMA:
                sma = pktalib.EMA(data["close"], timeperiod=50)
                lma = pktalib.EMA(data["close"], timeperiod=200)
                ssma = pktalib.EMA(data["close"], timeperiod=9)
                ssma20 = pktalib.EMA(data["close"], timeperiod=20)
                data.insert(len(data.columns), "SMA", sma)
                data.insert(len(data.columns), "LMA", lma)
                data.insert(len(data.columns), "SSMA", ssma)
                data.insert(len(data.columns), "SSMA20", ssma20)
                data.insert(len(data.columns), "Volatility", volatility)
            else:
                sma = pktalib.SMA(data["close"], timeperiod=50)
                lma = pktalib.SMA(data["close"], timeperiod=200)
                ssma = pktalib.SMA(data["close"], timeperiod=9)
                ssma20 = pktalib.SMA(data["close"], timeperiod=20)
                data.insert(len(data.columns), "SMA", sma)
                data.insert(len(data.columns), "LMA", lma)
                data.insert(len(data.columns), "SSMA", ssma)
                data.insert(len(data.columns), "SSMA20", ssma20)
                data.insert(len(data.columns), "Volatility", volatility)
            vol = pktalib.SMA(data["volume"], timeperiod=20)
            rsi = pktalib.RSI(data["close"], timeperiod=14)
            data.insert(len(data.columns), "VolMA", vol)
            data.insert(len(data.columns), "RSI", rsi)
            cci = pktalib.CCI(data["high"], data["low"], data["close"], timeperiod=14)
            data.insert(len(data.columns), "CCI", cci)
            try:
                fastk, fastd = pktalib.STOCHRSI(
                    data["close"], timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0
                )
                data.insert(len(data.columns), "FASTK", fastk)
                data.insert(len(data.columns), "FASTD", fastd)
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                pass
        data = data[::-1]  # Reverse the dataframe
        # data = data.fillna(0)
        # data = data.replace([np.inf, -np.inf], 0)
        fullData = data
        trimmedData = data.head(daysToLookback)
        return (fullData, trimmedData)
    
    # Validate if the stock is bullish in the short term
    def validate15MinutePriceVolumeBreakout(self, df):
        if df is None or len(df) == 0:
            return False
        # https://chartink.com/screener/15-min-price-volume-breakout
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        # Need at least 20 rows for SMA20 calculation
        if len(data) < 20:
            return False
        # Ensure data is sorted with oldest date first for SMA calculation
        if not data.empty and hasattr(data.index, 'sort_values'):
            try:
                data = data.sort_index(ascending=True)
            except:
                pass
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        data["SMA20"] = pktalib.SMA(data["close"], 20)
        data["SMA20V"] = pktalib.SMA(data["volume"], 20)
        data = data[
            ::-1
        ]  # Reverse the dataframe so that it's the most recent date first
        recent = data.head(3)
        if len(recent) < 3:
            return False
        # Price at least 1% higher than previous close
        cond1 = recent["close"].iloc[0] > 1.01*recent["close"].iloc[1]
        # Volume at least 5% higher than previous volume
        cond6 = recent["volume"].iloc[0] > 1.05*recent["volume"].iloc[1]
        cond2 = cond1 and cond6 and (recent["close"].iloc[0] > recent["SMA20"].iloc[0])
        cond3 = cond2 and (recent["close"].iloc[1] > recent["high"].iloc[2])
        cond4 = cond3 and (recent["volume"].iloc[0] > 1.05*recent["SMA20V"].iloc[0])
        cond5 = cond4 and (recent["volume"].iloc[1] > recent["SMA20V"].iloc[0])
        return cond5

    def validateBullishForTomorrow(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        # https://chartink.com/screener/bullish-for-tomorrow
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macdLine = pktalib.MACD(data["close"], 12, 26, 9)[0].tail(3)
        macdSignal = pktalib.MACD(data["close"], 12, 26, 9)[1].tail(3)
        macdHist = pktalib.MACD(data["close"], 12, 26, 9)[2].tail(3)

        return (
            (macdHist.iloc[:1].iloc[0] < macdHist.iloc[:2].iloc[1])
            and (macdHist.iloc[:3].iloc[2] > macdHist.iloc[:2].iloc[1])
            and (
                (macdLine.iloc[:3].iloc[2] - macdSignal.iloc[:3].iloc[2])
                - (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1])
                >= 0.4
            )
            and (
                (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1])
                - (macdLine.iloc[:1].iloc[0] - macdSignal.iloc[:1].iloc[0])
                <= 0.2
            )
            and (macdLine.iloc[:3].iloc[2] > macdSignal.iloc[:3].iloc[2])
            and (
                (macdLine.iloc[:3].iloc[2] - macdSignal.iloc[:3].iloc[2])
                - (macdLine.iloc[:2].iloc[1] - macdSignal.iloc[:2].iloc[1])
                < 1
            )
        )

    #@measure_time
    # validate if CCI is within given range
    def validateCCI(self, df, screenDict, saveDict, minCCI, maxCCI):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        cci = int(data.head(1)["CCI"].iloc[0])
        saveDict["CCI"] = cci
        if (cci >= minCCI and cci <= maxCCI) and "Trend" in saveDict.keys():
            if ("Up" in saveDict["Trend"]):
                screenDict["CCI"] = (
                    (colorText.BOLD if ("Strong" in saveDict["Trend"]) else "") + colorText.GREEN + str(cci) + colorText.END
                )
            else:
                screenDict["CCI"] = (
                    (colorText.BOLD if ("Strong" in saveDict["Trend"]) else "") + colorText.FAIL + str(cci) + colorText.END
                )
            return True
        screenDict["CCI"] = colorText.FAIL + str(cci) + colorText.END
        return False

    # Find Conflucence
    def validateConfluence(self, stock, df, full_df, screenDict, saveDict, percentage=0.1,confFilter=3):
        if df is None or len(df) == 0:
            return False
        data = df.copy() if confFilter < 4 else full_df.copy()
        recent = data.head(2)
        if len(recent) < 2:
            return False
        key1 = "SMA"
        key2 = "LMA"
        key3 = "50DMA"
        key4 = "200DMA"
        saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
        if confFilter == 4:
            maxRecentDays = int(self.configManager.superConfluenceMaxReviewDays)
            recentCurrentDay = 1
            isSuperConfluence = False
            ema_8 = 0
            ema_21 = 0
            ema_55 = 0
            reversedData = data[::-1]  # Reverse the dataframe so that it's oldest data first
            emas = self.configManager.superConfluenceEMAPeriods.split(",")
            if len(emas) < 2:
                emas = [8,21,]
            ema8CrossedEMA21 = False
            ema8CrossedEMA55 = False
            ema21CrossedEMA55 = False
            emasCrossedSMA200 = False
            silverCross = False
            while recentCurrentDay <= maxRecentDays:
                # 8 ema>21 ema > 55 ema >200 sma each OF THE ema AND THE 200 sma SEPARATED BY LESS THAN 1%(ideally 0.1% TO 0.5%) DURING CONFLUENCE
                if len(emas) >= 1:
                    ema_8 = pktalib.EMA(reversedData["close"],int(emas[0])).tail(recentCurrentDay).head(1).iloc[0]
                    ema_8_prev = pktalib.EMA(reversedData["close"],int(emas[0])).tail(recentCurrentDay+1).head(1).iloc[0]
                if len(emas) >= 2:
                    ema_21 = pktalib.EMA(reversedData["close"],int(emas[1])).tail(recentCurrentDay).head(1).iloc[0]
                    ema_21_prev = pktalib.EMA(reversedData["close"],int(emas[1])).tail(recentCurrentDay+1).head(1).iloc[0]
                if len(emas) >= 3:
                    ema_55 = pktalib.EMA(reversedData["close"],int(emas[2])).tail(recentCurrentDay).head(1).iloc[0]
                    ema_55_prev = pktalib.EMA(reversedData["close"],int(emas[2])).tail(recentCurrentDay+1).head(1).iloc[0]
                
                ema8CrossedEMA21 = (ema_8 >= ema_21 and ema_8_prev <= ema_21_prev) or ema8CrossedEMA21
                ema8CrossedEMA55 = (ema_8 >= ema_55 and ema_8_prev <= ema_55_prev) or ema8CrossedEMA55
                ema21CrossedEMA55 = (ema_21 >= ema_55 and ema_21_prev <= ema_55_prev) or ema21CrossedEMA55
                
                sma_200 = pktalib.SMA(reversedData["close"],200).tail(recentCurrentDay).head(1).iloc[0]
                # ema9 = pktalib.EMA(reversedData["close"],9).tail(recentCurrentDay).head(1).iloc[0]
                # smaRange = sma_200 * percentage
                superConfluenceEnforce200SMA = self.configManager.superConfluenceEnforce200SMA
                # ema_min = min(ema_8, ema_21, ema_55)
                ema55_percentage = abs(ema_55 - sma_200) / ema_55
                emasCrossedSMA200 = ((ema55_percentage <= percentage)) or emasCrossedSMA200 # (sma_200 <= ema_min and sma_200 <= ema_55)
                if not superConfluenceEnforce200SMA:
                    emasCrossedSMA200 = True
                superbConfluence = sum([ema8CrossedEMA21, emasCrossedSMA200]) >= 2 # ema8CrossedEMA55, ema21CrossedEMA55
                if superbConfluence:
                    indexDate = PKDateUtilities.dateFromYmdString(str(data.index[recentCurrentDay-1]).split(" ")[0])
                    dayDate = f"{indexDate.day}/{indexDate.month}"
                    screenDict["MA-Signal"] = (
                        saved[0] 
                        + (colorText.GREEN)
                        + f"SuperGoldenConf.({dayDate})"
                        + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"SuperGoldenConf(-{dayDate})"
                    screenDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{colorText.GREEN if (ema_8>=ema_21 and ema_8>=ema_55) else (colorText.WARN if (ema_8>=ema_21 or ema_8>=ema_55) else colorText.FAIL)}{round(ema_8,1)}{colorText.END},{colorText.GREEN if ema_21>=ema_55 else colorText.FAIL}{round(ema_21,1)}{colorText.END},{round(ema_55,1)}, {colorText.GREEN if sma_200<= ema_55 and emasCrossedSMA200 else (colorText.WARN if sma_200<= ema_55 else colorText.FAIL)}{round(sma_200,1)} ({round(ema55_percentage*100,1)}%){colorText.END}"
                    saveDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{round(ema_8,1)},{round(ema_21,1)},{round(ema_55,1)}, {round(sma_200,1)} ({round(ema55_percentage*100,1)}%)"
                    saveDict[f"SuperConfSort"] = int(f"{indexDate.year:04}{indexDate.month:02}{indexDate.day:02}") #0 if ema_8>=ema_21 and ema_8>=ema_55 and ema_21>=ema_55 and sma_200<=ema_55 else (1 if (ema_8>=ema_21 or ema_8>=ema_55) else (2 if sma_200<=ema_55 else 3))
                    screenDict[f"SuperConfSort"] = saveDict[f"SuperConfSort"]
                    return superbConfluence
                elif ema8CrossedEMA21 and ema8CrossedEMA55 and ema21CrossedEMA55:
                    indexDate = PKDateUtilities.dateFromYmdString(str(data.index[recentCurrentDay-1]).split(" ")[0])
                    dayDate = f"{indexDate.day}/{indexDate.month}"
                    screenDict["MA-Signal"] = (
                        saved[0] 
                        + (colorText.WHITE)
                        + f"SilverCrossConf.({dayDate})"
                        + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"SilverCrossConf.({dayDate})"
                    screenDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{colorText.GREEN if (ema_8>=ema_21 and ema_8>=ema_55) else (colorText.WARN if (ema_8>=ema_21 or ema_8>=ema_55) else colorText.FAIL)}{round(ema_8,1)}{colorText.END},{colorText.GREEN if ema_21>=ema_55 else colorText.FAIL}{round(ema_21,1)}{colorText.END},{round(ema_55,1)}, {colorText.GREEN if sma_200<= ema_55 and emasCrossedSMA200 else (colorText.WARN if sma_200<= ema_55 else colorText.FAIL)}{round(sma_200,1)} ({round(ema55_percentage*100,1)}%){colorText.END}"
                    saveDict[f"Latest EMA-{self.configManager.superConfluenceEMAPeriods}, SMA-200 (EMA55 %)"] = f"{round(ema_8,1)},{round(ema_21,1)},{round(ema_55,1)}, {round(sma_200,1)} ({round(ema55_percentage*100,1)}%)"
                    saveDict[f"SuperConfSort"] = int(f"{indexDate.year:04}{indexDate.month:02}{indexDate.day:02}") #0 if ema_8>=ema_21 and ema_8>=ema_55 and ema_21>=ema_55 and sma_200<=ema_55 else (1 if (ema_8>=ema_21 or ema_8>=ema_55) else (2 if sma_200<=ema_55 else 3))
                    screenDict[f"SuperConfSort"] = saveDict[f"SuperConfSort"]
                    silverCross = True
                
                recentCurrentDay += 1
            
            if silverCross:
                return True
        is20DMACrossover50DMA = (recent["SSMA20"].iloc[0] >= recent["SMA"].iloc[0]) and \
                            (recent["SSMA20"].iloc[1] <= recent["SMA"].iloc[1])
        is50DMACrossover200DMA = (recent["SMA"].iloc[0] >= recent["LMA"].iloc[0]) and \
                            (recent["SMA"].iloc[1] <= recent["LMA"].iloc[1])
        isGoldenCrossOver = is20DMACrossover50DMA or is50DMACrossover200DMA
        is50DMACrossover200DMADown = (recent["SMA"].iloc[0] <= recent["LMA"].iloc[0]) and \
                            (recent["SMA"].iloc[1] >= recent["LMA"].iloc[1])
        is20DMACrossover50DMADown = (recent["SSMA20"].iloc[0] <= recent["SMA"].iloc[0]) and \
                            (recent["SSMA20"].iloc[1] >= recent["SMA"].iloc[1])
        isDeadCrossOver = is20DMACrossover50DMADown or is50DMACrossover200DMADown
        deadxOverText = f'DeadCrossover{"(20)" if is20DMACrossover50DMADown else ("(50)" if is50DMACrossover200DMADown else "")}'
        goldenxOverText = f'GoldenCrossover{"(20)" if is20DMACrossover50DMA else ("(50)" if is50DMACrossover200DMA else "")}'
        if is20DMACrossover50DMA or is20DMACrossover50DMADown:
            key1 = "SSMA20"
            key2 = "SMA"
            key3 = "20DMA"
            key4 = "50DMA"
        is50DMAUpTrend = (recent[key1].iloc[0] > recent[key2].iloc[1])
        is50DMADownTrend = (recent[key1].iloc[0] < recent[key1].iloc[1])
        is50DMA = (recent[key1].iloc[0] <= recent["close"].iloc[0])
        is200DMA = (recent[key2].iloc[0] <= recent["close"].iloc[0])
        difference = round((recent[key1].iloc[0] - recent[key2].iloc[0])
                / recent["close"].iloc[0]
                * 100,
                2,
            )
        saveDict["ConfDMADifference"] = difference
        screenDict["ConfDMADifference"] = difference
        # difference = abs(difference)
        confText = f"{goldenxOverText if isGoldenCrossOver else (deadxOverText if isDeadCrossOver else ('Conf.Up' if is50DMAUpTrend else ('Conf.Down' if is50DMADownTrend else (key3 if is50DMA else (key4 if is200DMA else 'Unknown')))))}"
        if abs(recent[key1].iloc[0] - recent[key2].iloc[0]) <= (
            recent[key1].iloc[0] * percentage
        ):
            if recent[key1].iloc[0] >= recent[key2].iloc[0]:
                screenDict["MA-Signal"] = (
                    saved[0] 
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            else:
                screenDict["MA-Signal"] = (
                    saved[0] 
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            return confFilter == 3 or \
                (confFilter == 1 and not isDeadCrossOver and (is50DMAUpTrend or (isGoldenCrossOver or 'Up' in confText))) or \
                (confFilter == 2 and not isGoldenCrossOver and (is50DMADownTrend or isDeadCrossOver or 'Down' in confText))
        # Maybe the difference is not within the range, but we'd still like to keep the stock in
        # the list if it's a golden crossover or dead crossover
        if isGoldenCrossOver or isDeadCrossOver:
            screenDict["MA-Signal"] = (
                    saved[0] 
                    + (colorText.GREEN if is50DMAUpTrend else (colorText.FAIL if is50DMADownTrend else colorText.WARN))
                    + f"{confText} ({difference}%)"
                    + colorText.END
                )
            saveDict["MA-Signal"] = saved[1] + f"{confText} ({difference}%)"
            return confFilter == 3 or \
                (confFilter == 1 and isGoldenCrossOver) or \
                (confFilter == 2 and isDeadCrossOver)
        return False

    def findPotentialProfitableEntriesBullishTodayForPDOPDC(self, df, saveDict, screenDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        reversedData = data[::-1]  # Reverse the dataframe
        recentClose = reversedData["close"].tail(1).head(1).iloc[0]
        yesterdayClose = reversedData["close"].tail(2).head(1).iloc[0]
        recentOpen = reversedData["open"].tail(1).head(1).iloc[0]
        yesterdayOpen = reversedData["open"].tail(2).head(1).iloc[0]
        recentVol = reversedData["volume"].tail(1).head(1).iloc[0]
        # Daily open > 1 day ago open &
        # Daily Close > 1 day ago close &
        # Volume > 1000000
        return recentOpen > yesterdayOpen and recentClose > yesterdayClose and recentVol >= 1000000
    
    # - 200 MA is rising for at least 3 months.
    # - 50 MA is above 200MA
    # - Current price is above 20Osma and preferably above 50 to 100
    # - Current price is at least above 100 % from 52week low
    # - The stock should have made a 52 week high at least once every 4 to 6 month
    def findPotentialProfitableEntriesFrequentHighsBullishMAs(self, df, full_df, saveDict, screenDict):
        if df is None or len(df) == 0 or full_df is None or len(full_df) == 0:
            return False
        data = full_df.copy()
        one_week = 5
        if len(data) < 45 * one_week:
            return False
        reversedData = data[::-1]  # Reverse the dataframe
        lma_200 = reversedData["LMA"]
        sma_50 = reversedData["SMA"]
        full52Week = reversedData.tail(50 * one_week)
        full52WeekLow = full52Week["low"].min()
        #200 MA is rising for at least 3 months
        today = 1
        while today <= one_week * 12: # last 3 months
            if lma_200.tail(today).head(1).iloc[0] < lma_200.tail(today + 1).head(1).iloc[0]:
                return False
            today += 1
        # 50 MA is above 200MA
        if sma_50.tail(1).head(1).iloc[0] <= lma_200.tail(1).head(1).iloc[0]:
            return False
        # Current price is above 20Osma and preferably above 50 to 100
        recentClose = reversedData["close"].tail(1).head(1).iloc[0]
        if recentClose < lma_200.tail(1).head(1).iloc[0] or recentClose < 50 or recentClose > 100:
            return False
        # Current price is at least above 100 % from 52week low
        if recentClose <= 2*full52WeekLow:
            return False
        # The stock should have made a 52 week high at least once every 4 to 6 month
        highAsc = reversedData.sort_values(by=["high"], ascending=True)
        highs = highAsc.tail(13)
        dateDiffs = highs.index.to_series().diff().dt.days
        index = 0
        while index < 12:
            if abs(dateDiffs.tail(12).iloc[index]) >= 120: # max 6 months = 120 days
                return False
            index += 1
        return True

    # - Stock must be trading above 2% on day
    # - stock must be trading above previous day high 
    # - stock must be above daily 50ma
    # - stock must be above 200ma on 5min TF
    def findPotentialProfitableEntriesForFnOTradesAbove50MAAbove200MA5Min(self, df_5min, full_df, saveDict, screenDict):
        if df_5min is None or len(df_5min) == 0 or full_df is None or len(full_df) == 0:
            return False
        data = full_df.copy()
        reversedData = data[::-1]  # Reverse the dataframe
        recentClose = reversedData["close"].tail(1).head(1).iloc[0]
        prevClose = reversedData["close"].tail(2).head(1).iloc[0]
        tradingAbove2Percent = (recentClose-prevClose)*100/prevClose > 2
        if tradingAbove2Percent:
            prevHigh = reversedData["high"].tail(2).head(1).iloc[0]
            tradingAbovePrevHighAnd50MA = (recentClose > prevHigh) and (recentClose > reversedData["SMA"].tail(1).head(1).iloc[0])
            # return tradingAbovePrevHighAnd50MA
            # resampling 1-min data to 5 min for 200MA requires at least 5d data to
            # be downloaded which is pretty huge (~460MB). So skipping this for now.
            if tradingAbovePrevHighAnd50MA:
                ohlc_dict = {
                    "open":'first',
                    "high":'max',
                    "low":'min',
                    "close":'last',
                    'Adj Close': 'last',
                    "volume":'sum'
                }
                data_5min = df_5min.copy()
                reversedData_5min = data_5min[::-1]  # Reverse the dataframe
                reversedData_5min = reversedData_5min.resample(f'5T', offset='15min').agg(ohlc_dict)
                reversedData_5min.dropna(inplace=True)
                sma200_5min = pktalib.SMA(reversedData_5min["close"],timeperiod=200)
                return recentClose > sma200_5min.tail(1).head(1).iloc[0]
        return False

    #@measure_time
    # Validate if share prices are consolidating
    def validateConsolidation(self, df, screenDict, saveDict, percentage=10):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        hc = data.describe()["close"]["max"]
        lc = data.describe()["close"]["min"]
        if (hc - lc) <= (hc * percentage / 100) and (hc - lc != 0):
            screenDict["Consol."] = (
                colorText.GREEN
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        else:
            screenDict["Consol."] = (
                colorText.FAIL
                + "Range:"
                + str(round((abs((hc - lc) / hc) * 100), 1))
                + "%"
                + colorText.END
            )
        saveDict["Consol."] = f'Range:{str(round((abs((hc-lc)/hc)*100),1))+"%"}'
        return round((abs((hc - lc) / hc) * 100), 1)

    def validateConsolidationContraction(self, df,legsToCheck=2,stockName=None):
        if df is None or len(df) == 0:
            return False,[],0
        data = df.copy()
        # We can use window =3 because we need at least 3 candles to get the next top or bottom
        # but to better identify the pattern, we'd use window = 5
        tops, bots = self.getTopsAndBottoms(df=data,window=5,numTopsBottoms=3*(legsToCheck if legsToCheck > 0 else 3))
        # bots = bots.tail(3*legsToCheck-1)
        consolidationPercentages = []
        # dfc.assign(topbots=dfc["tops","bots"].sum(1)).drop("tops","bots", 1)
        dfc = pd.concat([tops,bots],axis=0)
        dfc.sort_index(inplace=True)
        dfc = dfc.assign(topbots=dfc[["tops","bots"]].sum(1))
        if np.isnan(dfc["tops"].iloc[0]): # For a leg to form, we need two tops and one bottom \_/\_/\_/
            dfc = dfc.tail(len(dfc)-1)
        indexLength = len(dfc)
        toBeDroppedIndices = []
        index = 0
        while index < indexLength-1:
            top = dfc["tops"].iloc[index]
            top_next = dfc["tops"].iloc[index+1]
            bot = dfc["bots"].iloc[index]
            bot_next = dfc["bots"].iloc[index+1]
            if not np.isnan(top) and not np.isnan(top_next):
                if top >= top_next:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index+1])].index
                else:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index])].index
                toBeDroppedIndices.append(indexVal)
            if not np.isnan(bot) and not np.isnan(bot_next):
                if bot <= bot_next:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index+1])].index
                else:
                    indexVal = dfc[(dfc.Date == dfc["Date"].iloc[index])].index
                toBeDroppedIndices.append(indexVal)
            index += 1

        for indexVal in toBeDroppedIndices:
            dfc.drop(indexVal,axis=0, inplace=True, errors="ignore")
        index = 0
        indexLength = len(dfc)
        relativeLegsTocheck = (legsToCheck if legsToCheck >= 3 else 3)
        while index < indexLength-3:
            top1 = dfc["tops"].iloc[index]
            top2 = dfc["tops"].iloc[index+2]
            top = max(top1,top2)
            bot = dfc["bots"].iloc[index+1]
            if bot != 0 and not np.isnan(top) and not np.isnan(bot):
                legConsolidation = int(round((top-bot)*100/bot,0))
            else:
                legConsolidation = 0
            consolidationPercentages.append(legConsolidation)
            if len(consolidationPercentages) >= relativeLegsTocheck:
                break
            index += 2
        # Check for consolidation/tightening.
        # Every next leg should be tighter than the previous one
        consolidationPercentages = list(reversed(consolidationPercentages))
        devScore = 0
        if self.configManager.enableAdditionalVCPFilters:
            if len(consolidationPercentages) >= 2:
                index = 0
                while (index+1) < legsToCheck:
                    # prev one < new one.
                    if len(consolidationPercentages) >= index+2 and consolidationPercentages[index] <= consolidationPercentages[index+1]:
                        return False, consolidationPercentages[:relativeLegsTocheck], devScore
                    if index < relativeLegsTocheck and len(consolidationPercentages) >= index+2:
                        devScore += 2-(consolidationPercentages[index]/consolidationPercentages[index+1])
                    index += 1
        
        # Return the first requested number of legs in the order of leg1, leg2, leg3 etc.
        conditionMet = len(consolidationPercentages[:relativeLegsTocheck]) >= legsToCheck
        return conditionMet, consolidationPercentages[:relativeLegsTocheck], devScore

    # validate if the stock has been having higher highs, higher lows
    # and higher close with latest close > supertrend and 8-EMA.
    def validateHigherHighsHigherLowsHigherClose(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        day0 = data
        day1 = data[1:]
        day2 = data[2:]
        day3 = data[3:]
        if len(day1) < 1 or len(day2) < 1 or len(day3) < 1:
            return False
        higherHighs = (
            (day0["high"].iloc[0] > day1["high"].iloc[0])
            and (day1["high"].iloc[0] > day2["high"].iloc[0])
            and (day2["high"].iloc[0] > day3["high"].iloc[0])
        )
        higherLows = (
            (day0["low"].iloc[0] > day1["low"].iloc[0])
            and (day1["low"].iloc[0] > day2["low"].iloc[0])
            and (day2["low"].iloc[0] > day3["low"].iloc[0])
        )
        higherClose = (
            (day0["close"].iloc[0] > day1["close"].iloc[0])
            and (day1["close"].iloc[0] > day2["close"].iloc[0])
            and (day2["close"].iloc[0] > day3["close"].iloc[0])
        )
        # higherRSI = (day0["RSI"].iloc[0] > day1["RSI"].iloc[0]) and \
        #                 (day1["RSI"].iloc[0] > day2["RSI"].iloc[0]) and \
        #                 (day2["RSI"].iloc[0] > day3["RSI"].iloc[0]) and \
        #                 day3["RSI"].iloc[0] >= 50 and day0["RSI"].iloc[0] >= 65
        reversedData = data[::-1].copy()
        reversedData["SUPERT"] = pktalib.supertrend(reversedData, 7, 3)["SUPERT_7_3.0"]
        reversedData["EMA8"] = pktalib.EMA(reversedData["close"], timeperiod=9)
        higherClose = (
            higherClose
            and day0["close"].iloc[0] > reversedData.tail(1)["SUPERT"].iloc[0]
            and day0["close"].iloc[0] > reversedData.tail(1)["EMA8"].iloc[0]
        )
        return higherHighs and higherLows and higherClose

    #@measure_time
    # Validate 'Inside Bar' structure for recent days
    def validateInsideBar(
        self, df, screenDict, saveDict, chartPattern=1, daysToLookback=5
    ):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        orgData = data
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        for i in range(int(daysToLookback), int(round(daysToLookback * 0.5)) - 1, -1):
            if i == 2:
                return 0  # Exit if only last 2 candles are left
            if chartPattern == 1:
                if "Up" in saveDict["Trend"] and (
                    "Bull" in saveDict["MA-Signal"]
                    or "Support" in saveDict["MA-Signal"]
                ):
                    data = orgData.head(i)
                    refCandle = data.tail(1)
                    if (
                        (len(data.high[data.high > refCandle.high.item()]) == 0)
                        and (len(data.low[data.low < refCandle.low.item()]) == 0)
                        and (len(data.open[data.open > refCandle.high.item()]) == 0)
                        and (len(data.close[data.close < refCandle.low.item()]) == 0)
                    ):
                        screenDict["Pattern"] = (
                            saved[0]
                            + colorText.WARN
                            + ("Inside Bar (%d)" % i)
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Inside Bar (%d)" % i
                        return i
                else:
                    return 0
            else:
                if "Down" in saveDict["Trend"] and (
                    "Bear" in saveDict["MA-Signal"] or "Resist" in saveDict["MA-Signal"]
                ):
                    data = orgData.head(i)
                    refCandle = data.tail(1)
                    if (
                        (len(data.high[data.high > refCandle.high.item()]) == 0)
                        and (len(data.low[data.low < refCandle.low.item()]) == 0)
                        and (len(data.open[data.open > refCandle.high.item()]) == 0)
                        and (len(data.close[data.close < refCandle.low.item()]) == 0)
                    ):
                        screenDict["Pattern"] = (
                            saved[0]
                            + colorText.WARN
                            + ("Inside Bar (%d)" % i)
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Inside Bar (%d)" % i
                        return i
                else:
                    return 0
        return 0

    # Find IPO base
    def validateIpoBase(self, stock, df, screenDict, saveDict, percentage=0.3):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        listingPrice = data[::-1].head(1)["open"].iloc[0]
        currentPrice = data.head(1)["close"].iloc[0]
        ATH = data.describe()["high"]["max"]
        if ATH > (listingPrice + (listingPrice * percentage)):
            return False
        away = round(((currentPrice - listingPrice) / listingPrice) * 100, 1)
        if (
            (listingPrice - (listingPrice * percentage))
            <= currentPrice
            <= (listingPrice + (listingPrice * percentage))
        ):
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            if away > 0:
                screenDict["Pattern"] = (
                    saved[0] 
                    + colorText.GREEN
                    + f"IPO Base ({away} %)"
                    + colorText.END
                )
            else:
                screenDict["Pattern"] = (
                    saved[0]
                    + colorText.GREEN
                    + "IPO Base "
                    + colorText.FAIL
                    + f"({away} %)"
                    + colorText.END
                )
            saveDict["Pattern"] = saved[1] + f"IPO Base ({away} %)"
            return True
        return False

    #@measure_time
    # Validate Lorentzian Classification signal
    def validateLorentzian(self, df, screenDict, saveDict, lookFor=3,stock=None):
        if df is None or len(df) < 20:
            return False
        data = df.copy()
        # lookFor: 1-Buy, 2-Sell, 3-Any
        data = data[::-1]  # Reverse the dataframe
        data = data.rename(
            columns={
                "open": "open",
                "close": "close",
                "high": "high",
                "low": "low",
                "volume": "volume",
            }
        )
        try:
            with SuppressOutput(suppress_stdout=True, suppress_stderr=True):
                lc = ata.LorentzianClassification(data=data,
                features=[
                    ata.LorentzianClassification.Feature("RSI", 14, 2),  # f1
                    ata.LorentzianClassification.Feature("WT", 10, 11),  # f2
                    ata.LorentzianClassification.Feature("CCI", 20, 2),  # f3
                    ata.LorentzianClassification.Feature("ADX", 20, 2),  # f4
                    ata.LorentzianClassification.Feature("RSI", 9, 2),   # f5
                    pktalib.MFI(data["high"], data["low"], data["close"], data["volume"], 14) #f6
                ],
                settings=ata.LorentzianClassification.Settings(
                    source=data["close"],
                    neighborsCount=8,
                    maxBarsBack=2000,
                    useDynamicExits=False
                ),
                filterSettings=ata.LorentzianClassification.FilterSettings(
                    useVolatilityFilter=True,
                    useRegimeFilter=True,
                    useAdxFilter=False,
                    regimeThreshold=-0.1,
                    adxThreshold=20,
                    kernelFilter = ata.LorentzianClassification.KernelFilter(
                        useKernelSmoothing = False,
                        lookbackWindow = 8,
                        relativeWeight = 8.0,
                        regressionLevel = 25,
                        crossoverLag = 2,
                    )
                ))
            # if stock is not None:
            #     lc.dump(f'{stock}_result.csv')
            #     lc.plot(f'{stock}_result.jpg')
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            if lc.df.iloc[-1]["isNewBuySignal"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.GREEN + "Lorentzian-Buy" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + "Lorentzian-Buy"
                if lookFor != 2: # Not Sell
                    return True
            elif lc.df.iloc[-1]["isNewSellSignal"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.FAIL + "Lorentzian-Sell" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + "Lorentzian-Sell"
                if lookFor != 1: # Not Buy
                    return True
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except IndexError:
            pass
        except Exception as e:  # pragma: no cover
            # ValueError: operands could not be broadcast together with shapes (20,) (26,)
            # File "/opt/homebrew/lib/python3.11/site-packages/advanced_ta/LorentzianClassification/Classifier.py", line 186, in __init__
            # File "/opt/homebrew/lib/python3.11/site-packages/advanced_ta/LorentzianClassification/Classifier.py", line 395, in __classify
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/common.py", line 76, in new_method
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/arraylike.py", line 70, in __and__
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/series.py", line 5810, in _logical_method
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/array_ops.py", line 456, in logical_op
            # File "/opt/homebrew/lib/python3.11/site-packages/pandas/core/ops/array_ops.py", line 364, in na_logical_op
            self.default_logger.debug(e, exc_info=True)
            pass
        return False

    # validate if the stock has been having lower lows, lower highs
    def validateLowerHighsLowerLows(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        day0 = data
        day1 = data[1:]
        day2 = data[2:]
        day3 = data[3:]
        lowerHighs = (
            (day0["high"].iloc[0] < day1["high"].iloc[0])
            and (day1["high"].iloc[0] < day2["high"].iloc[0])
            and (day2["high"].iloc[0] < day3["high"].iloc[0])
        )
        lowerLows = (
            (day0["low"].iloc[0] < day1["low"].iloc[0])
            and (day1["low"].iloc[0] < day2["low"].iloc[0])
            and (day2["low"].iloc[0] < day3["low"].iloc[0])
        )
        higherRSI = (
            (day0["RSI"].iloc[0] < day1["RSI"].iloc[0])
            and (day1["RSI"].iloc[0] < day2["RSI"].iloc[0])
            and (day2["RSI"].iloc[0] < day3["RSI"].iloc[0])
            and day0["RSI"].iloc[0] >= 50
        )
        return lowerHighs and lowerLows and higherRSI

    # Validate if recent volume is lowest of last 'N' Days
    def validateLowestVolume(self, df, daysForLowestVolume):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        if daysForLowestVolume is None:
            daysForLowestVolume = 30
        if len(data) < daysForLowestVolume:
            return False
        data = data.head(daysForLowestVolume)
        recent = data.head(1)
        if len(recent) < 1:
            return False
        if (recent["volume"].iloc[0] <= data.describe()["volume"]["min"]) and recent[
            "volume"
        ][0] != np.nan:
            return True
        return False

    # Validate LTP within limits
    def validateLTP(self, df, screenDict, saveDict, minLTP=None, maxLTP=None,minChange=0):
        data = df.copy()
        ltpValid = False
        if minLTP is None:
            minLTP = self.configManager.minLTP
        if maxLTP is None:
            maxLTP = self.configManager.maxLTP
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        # Ensure data is sorted with latest date first (in case it wasn't sorted during load)
        if not data.empty and hasattr(data.index, 'sort_values'):
            try:
                data = data.sort_index(ascending=False)
            except:
                pass
        recent = data.head(1)

        pct_change = (data[::-1]["close"].pct_change() * 100).iloc[-1]
        if pct_change == np.inf or pct_change == -np.inf:
            pct_change = 0
        pct_save = "%.1f%%" % pct_change
        if pct_change > 0.2:
            pct_change = colorText.GREEN + ("%.1f%%" % pct_change) + colorText.END
        elif pct_change < -0.2:
            pct_change = colorText.FAIL + ("%.1f%%" % pct_change) + colorText.END
        else:
            pct_change = colorText.WARN + ("%.1f%%" % pct_change) + colorText.END
        saveDict["%Chng"] = pct_save
        screenDict["%Chng"] = pct_change
        ltp = round(recent["close"].iloc[0], 2)
        verifyStageTwo = True
        if len(data) > 250:
            yearlyLow = data.head(250)["close"].min()
            yearlyHigh = data.head(250)["close"].max()
            if ltp < (2 * yearlyLow) and ltp < (0.75 * yearlyHigh):
                verifyStageTwo = False
                screenDict["Stock"] = colorText.FAIL + saveDict["Stock"] + colorText.END
        if ltp >= minLTP and ltp <= maxLTP:
            ltpValid = True
            if minChange != 0:
                # User has supplied some filter for percentage change
                ltpValid = float(str(pct_save).replace("%","")) >= minChange
            saveDict["LTP"] = round(ltp, 2)
            screenDict["LTP"] = (colorText.GREEN if ltpValid else colorText.FAIL) + ("%.2f" % ltp) + colorText.END
            try:
                # Use the latest date from the full dataset (data.index[0] after sorting)
                # This ensures we always show the most recent trading date
                latest_date_index = data.index[0] if not data.empty else (recent.index[0] if not recent.empty else None)
                if latest_date_index is None:
                    # Fallback to recent if data is empty
                    latest_date_index = recent.index[0] if not recent.empty else None
                
                if latest_date_index is not None:
                    dateTimePart = str(latest_date_index).split(" ")
                    if len(dateTimePart) == 1:
                        indexDate = PKDateUtilities.dateFromYmdString(dateTimePart[0])
                        dayDate = f"{indexDate.day}/{indexDate.month}"
                    elif len(dateTimePart) == 2:
                        today = PKDateUtilities.currentDateTime()
                        try:
                            indexDate = datetime.datetime.strptime(str(latest_date_index),"%Y-%m-%d %H:%M:%S").replace(tzinfo=today.tzinfo)
                        except: # pragma: no cover
                            try:
                                indexDate = datetime.datetime.strptime(str(latest_date_index),"%Y-%m-%d %H:%M:%S%z").replace(tzinfo=today.tzinfo)
                            except:
                                # Try parsing with pd.to_datetime as fallback
                                try:
                                    indexDate = pd.to_datetime(str(latest_date_index), format='mixed', utc=True)
                                    if hasattr(indexDate, 'tz') and indexDate.tz is not None:
                                        indexDate = indexDate.tz_convert(today.tzinfo)
                                    else:
                                        indexDate = indexDate.replace(tzinfo=today.tzinfo)
                                except:
                                    indexDate = today
                            pass
                        
                        # If the time is 00:00, assume market close (15:30) for that day
                        if indexDate.hour == 0 and indexDate.minute == 0:
                            indexDate = indexDate.replace(hour=15, minute=30, second=0, microsecond=0)
                        
                        dayDate = f"{indexDate.day}/{indexDate.month}/{str(indexDate.year)[-2:]} {indexDate.hour}:{indexDate.minute}"
                        screenDict["Time"] = f"{colorText.WHITE}{dayDate}{colorText.END}"
                        saveDict["Time"] = str(dayDate)
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except Exception as e: # pragma: no cover
                self.default_logger.debug(e, exc_info=True)
                ltpValid = False
                verifyStageTwo = False
                pass
            
            return ltpValid, verifyStageTwo
        screenDict["LTP"] = colorText.FAIL + ("%.2f" % ltp) + colorText.END
        saveDict["LTP"] = round(ltp, 2)
        return ltpValid, verifyStageTwo

    def validateLTPForPortfolioCalc(self, df, screenDict, saveDict,requestedPeriod=0):
        data = df.copy()
        data = data.sort_index(ascending=True)
        periods = self.configManager.periodsRange
        if requestedPeriod > 0 and requestedPeriod not in periods:
            periods.append(requestedPeriod)
        calcDate_recent = data.tail(1)
        calcDate_recent.reset_index(inplace=True)
        calc_date = str(calcDate_recent.iloc[:, 0][0]).split(" ")[0]
        for prd in periods:
            if len(data) >= prd + 1:
                baseLtp = data["close"].iloc[0]
                prdLtp = data["close"].iloc[prd]
                if isinstance(baseLtp,pd.Series):
                    baseLtp = baseLtp[0]
                    prdLtp = prdLtp[0]
                screenDict[f"LTP{prd}"] = (
                    (colorText.GREEN if (prdLtp >= baseLtp) else (colorText.FAIL))
                    + str("{:.2f}".format(prdLtp))
                    + colorText.END
                )
                screenDict[f"Growth{prd}"] = (
                    (colorText.GREEN if (prdLtp >= baseLtp) else (colorText.FAIL))
                    + str("{:.2f}".format(prdLtp - baseLtp))
                    + colorText.END
                )
                saveDict[f"LTP{prd}"] = round(prdLtp, 2)
                saveDict[f"Growth{prd}"] = round(prdLtp - baseLtp, 2)
                if prd == 22 or (prd == requestedPeriod):
                    changePercent = round(((baseLtp-prdLtp) if requestedPeriod ==0 else (prdLtp - baseLtp))*100/baseLtp, 2) if baseLtp != 0 else 0
                    saveDict[f"{prd}-Pd"] = f"{changePercent}% ({prdLtp})" if not pd.isna(changePercent) else '-'
                    screenDict[f"{prd}-Pd"] = ((colorText.GREEN if changePercent >=0 else colorText.FAIL) + f"{changePercent}% ({prdLtp})" + colorText.END) if not pd.isna(changePercent) else '-'
                    if (prd == requestedPeriod):
                        slice_df = data.tail(prd)
                        maxLTPPotential = slice_df["high"].max()
                        max_high_idx = slice_df["high"].idxmax()
                        max_date_str = max_high_idx.strftime("%d/%m")
                        screenDict[f"MaxLTP"] = (
                            (colorText.GREEN if (maxLTPPotential >= baseLtp) else colorText.FAIL)
                            + f"{maxLTPPotential:.2f} ({max_date_str})"
                            + colorText.END
                        )
                        screenDict[f"Pot.Grw"] = (
                            (colorText.GREEN if (maxLTPPotential >= baseLtp) else (colorText.FAIL))
                            + str("{:.2f}%".format((maxLTPPotential - baseLtp)*100/baseLtp))
                            + colorText.END
                        )
                        saveDict[f"MaxLTP"] = f"{round(maxLTPPotential, 2)} ({max_date_str})"
                        saveDict[f"Pot.Grw"] = f"{round((maxLTPPotential - baseLtp)*100/baseLtp, 2)}%"
                screenDict["Date"] = calc_date
                saveDict["Date"] = calc_date
            else:
                saveDict[f"LTP{prd}"] = np.nan
                saveDict[f"Growth{prd}"] = np.nan
                screenDict["Date"] = calc_date
                saveDict["Date"] = calc_date

    # Find stocks that are bearish intraday: Macd Histogram negative
    def validateMACDHistogramBelow0(self, df):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data[::-1]  # Reverse the dataframe so that its the oldest date first
        macd = pktalib.MACD(data["close"], 12, 26, 9)[2].tail(1)
        return macd.iloc[:1][0] < 0

    #@measure_time
    # Find if stock gaining bullish momentum
    def validateMomentum(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        try:
            data = data.head(3)
            if len(data) < 3:
                return False
            for row in data.iterrows():
                # All 3 candles should be Green and NOT Circuits
                yc = row[1]["close"]
                yo = row[1]["open"]
                if yc <= yo:
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because yesterday-close ({yc}) <= yesterday-open ({yo})'
                    # )
                    return False
            openDesc = data.sort_values(by=["open"], ascending=False)
            closeDesc = data.sort_values(by=["close"], ascending=False)
            volDesc = data.sort_values(by=["volume"], ascending=False)
            try:
                if (
                    data.equals(openDesc)
                    and data.equals(closeDesc)
                    and data.equals(volDesc)
                ):
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, open,close and volume equal from day before yesterday. A potential momentum-gainer!'
                    # )
                    to = data["open"].iloc[0]
                    yc = data["close"].iloc[1]
                    yo = data["open"].iloc[1]
                    dyc = data["close"].iloc[2]
                    if (to >= yc) and (yo >= dyc):
                        # self.default_logger.info(
                        #     f'Stock:{saveDict["Stock"]}, is a momentum-gainer because today-open ({to}) >= yesterday-close ({yc}) and yesterday-open({yo}) >= day-before-close({dyc})'
                        # )
                        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                        screenDict["Pattern"] = (
                            saved[0]
                            + colorText.GREEN
                            + "Momentum Gainer"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Momentum Gainer"
                        return True
                    # self.default_logger.info(
                    #     f'Stock:{saveDict["Stock"]}, is not a momentum-gainer because either today-open ({to}) < yesterday-close ({yc}) or yesterday-open({yo}) < day-before-close({dyc})'
                    # )
            except IndexError as e: # pragma: no cover
                # self.default_logger.debug(e, exc_info=True)
                # self.default_logger.debug(data)
                pass
            return False
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            return False

    #@measure_time
    # Validate Moving averages and look for buy/sell signals
    def validateMovingAverages(self, df, screenDict, saveDict, maRange=2.5,maLength=0,filters={}):
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        maSignals = []
        if str(maLength) in ["0","2","3"]:
            saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
            if (
                recent["SMA"].iloc[0] > recent["LMA"].iloc[0]
                and recent["close"].iloc[0] > recent["SMA"].iloc[0]
            ):
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.GREEN + "Bullish" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Bullish"
                maSignals.append("3")
            elif recent["SMA"].iloc[0] < recent["LMA"].iloc[0]:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.FAIL + "Bearish" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Bearish"
                maSignals.append("2")
            elif recent["SMA"].iloc[0] == 0:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.WARN + "Unknown" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Unknown"
            else:
                screenDict["MA-Signal"] = (
                    saved[0] + colorText.WARN + "Neutral" + colorText.END
                )
                saveDict["MA-Signal"] = saved[1] + "Neutral"
        reversedData = data[::-1]  # Reverse the dataframe
        ema_20 = pktalib.EMA(reversedData["close"],20).tail(1).iloc[0]
        vwap = pktalib.VWAP(reversedData["high"],reversedData["low"],reversedData["close"],reversedData["volume"]).tail(1).iloc[0]
        smaDev = data["SMA"].iloc[0] * maRange / 100
        lmaDev = data["LMA"].iloc[0] * maRange / 100
        emaDev = ema_20 * maRange / 100
        vwapDev = vwap * maRange / 100
        open, high, low, close, sma, lma = (
            data["open"].iloc[0],
            data["high"].iloc[0],
            data["low"].iloc[0],
            data["close"].iloc[0],
            data["SMA"].iloc[0],
            data["LMA"].iloc[0],
        )
        mas = [sma,lma,ema_20,vwap] #if maLength==0 else [sma,lma,ema_20]
        maDevs = [smaDev, lmaDev, emaDev, vwapDev] #if maLength==0 else [smaDev, lmaDev, emaDev]
        maTexts = ["50MA","200MA","20EMA","VWAP"] #if maLength==0 else ["50MA","200MA","20EMA"]
        maReversal = 0
        index = 0
        bullishCandle = self.getCandleType(data)
        if str(maLength) not in ["2","3"]:
            for ma in mas:
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                # Taking Support
                if close > ma and low <= (ma + maDevs[index]) and str(maLength) in ["0","1"]:
                    screenDict["MA-Signal"] = (
                        saved[0] + colorText.GREEN + f"{maTexts[index]}-Support" + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"{maTexts[index]}-Support"
                    maReversal = 1
                    maSignals.append("1")
                # Validating Resistance
                elif close < ma and high >= (ma - maDevs[index]) and str(maLength) in ["0","6"]:
                    screenDict["MA-Signal"] = (
                        saved[0] + colorText.FAIL + f"{maTexts[index]}-Resist" + colorText.END
                    )
                    saveDict["MA-Signal"] = saved[1] + f"{maTexts[index]}-Resist"
                    maReversal = -1
                    maSignals.append("6")
                    
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                # For a Bullish Candle
                if bullishCandle:
                    # Crossing up
                    if open < ma and close > ma:
                        if (str(maLength) in ["0","5"]) or (str(maLength) in ["7"] and index == maTexts.index("VWAP")):
                            screenDict["MA-Signal"] = (
                                saved[0] + colorText.GREEN + f"BullCross-{maTexts[index]}" + colorText.END
                            )
                            saveDict["MA-Signal"] = saved[1] + f"BullCross-{maTexts[index]}"
                            maReversal = 1
                            maSignals.append(str(maLength))
                # For a Bearish Candle
                elif not bullishCandle:
                    # Crossing down
                    if open > sma and close < sma and str(maLength) in ["0","4"]:
                        screenDict["MA-Signal"] = (
                            saved[0] + colorText.FAIL + f"BearCross-{maTexts[index]}" + colorText.END
                        )
                        saveDict["MA-Signal"] = saved[1] + f"BearCross-{maTexts[index]}"
                        maReversal = -1
                        maSignals.append("4")
                index += 1
        returnValue = maReversal
        if maLength != 0:
            hasRespectiveMAInList = str(maLength) in maSignals
            hasVWAP = "BullCross-VWAP" in saveDict["MA-Signal"]
            returnValue = (hasVWAP and hasRespectiveMAInList) if maLength == 7 else hasRespectiveMAInList
        savedMASignals = saveDict["MA-Signal"]
        return returnValue, savedMASignals.count("Bull") + savedMASignals.count("Support"), savedMASignals.count("Bear") + savedMASignals.count("Resist")

    # Find NRx range for Reversal
    def validateNarrowRange(self, df, screenDict, saveDict, nr=4):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
        if PKDateUtilities.isTradingTime():
            rangeData = data.head(nr + 1)[1:]
            now_candle = data.head(1)
            rangeData["Range"] = abs(rangeData["close"] - rangeData["open"])
            recent = rangeData.head(1)
            if (
                len(recent) == 1
                and recent["Range"].iloc[0] == rangeData.describe()["Range"]["min"]
            ):
                if (
                    self.getCandleType(recent)
                    and now_candle["close"].iloc[0] >= recent["close"].iloc[0]
                ):
                    screenDict["Pattern"] = (
                        saved[0] + colorText.GREEN + f"Buy-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = saved[1] + f"Buy-NR{nr}"
                    return True
                elif (
                    not self.getCandleType(recent)
                    and now_candle["close"].iloc[0] <= recent["close"].iloc[0]
                ):
                    screenDict["Pattern"] = (
                        saved[0] + colorText.FAIL + f"Sell-NR{nr}" + colorText.END
                    )
                    saveDict["Pattern"] = saved[1] + f"Sell-NR{nr}"
                    return True
            return False
        else:
            rangeData = data.head(nr)
            rangeData.loc[:,'Range'] = abs(rangeData["close"] - rangeData["open"])
            recent = rangeData.head(1)
            if recent["Range"].iloc[0] == rangeData.describe()["Range"]["min"]:
                screenDict["Pattern"] = (
                    saved[0] + colorText.GREEN + f"NR{nr}" + colorText.END
                )
                saveDict["Pattern"] = saved[1] + f"NR{nr}"
                return True
            return False

    # Find if stock is newly listed
    def validateNewlyListed(self, df, daysToLookback):
        if df is None or len(df) == 0 or len(df) > 220:
            return False
        data = df.copy()
        if str(daysToLookback).endswith("y"):
            daysToLookback = '220d'
        daysToLookback = int(daysToLookback[:-1])
        recent = data.head(1)
        if len(recent) < 1:
            return False
        if len(data) < daysToLookback and (
            recent["close"].iloc[0] != np.nan and recent["close"].iloc[0] > 0
        ):
            return True
        return False

    def validatePriceActionCrosses(self, full_df, screenDict, saveDict,mas=[], isEMA=False, maDirectionFromBelow=True):
        if full_df is None or len(full_df) == 0:
            return False
        data = full_df.copy()
        reversedData = data[::-1]  # Reverse the dataframe so that it's oldest data first
        hasAtleastOneMACross = False
        for ma in mas:
            if len(reversedData) <= int(ma):
                continue
            hasCrossed, percentageDiff = self.findPriceActionCross(df=reversedData,ma=ma,daysToConsider=1,baseMAOrPrice=reversedData["close"].tail(2),isEMA=isEMA,maDirectionFromBelow=maDirectionFromBelow)
            if hasCrossed:
                if not hasAtleastOneMACross:
                    hasAtleastOneMACross = True
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                maText = f"{ma}-{'EMA' if isEMA else 'SMA'}-Cross-{'FromBelow' if maDirectionFromBelow else 'FromAbove'}"
                saveDict["MA-Signal"] = saved[1] + maText + f"({percentageDiff}%)"
                screenDict["MA-Signal"] = saved[0] + f"{colorText.GREEN}{maText}{colorText.END}{colorText.FAIL if abs(percentageDiff) > 1 else colorText.WARN}({percentageDiff}%){colorText.END}"
        return hasAtleastOneMACross

    def validatePriceActionCrossesForPivotPoint(self, df, screenDict, saveDict, pivotPoint="1", crossDirectionFromBelow=True):
        if df is None or len(df) == 0:
            return False
        hasPriceCross = False
        data = df.copy()
        pp_map = {"1":"PP","2":"S1","3":"S2","4":"S3","5":"R1","6":"R2","7":"R3"}
        if pivotPoint is not None and pivotPoint != "0" and str(pivotPoint).isnumeric():
            ppToCheck = pp_map[str(pivotPoint)]
            ppsr_df = pktalib.get_ppsr_df(data["high"],data["low"],data["close"],ppToCheck)
            if ppsr_df is None:
                return False
            if crossDirectionFromBelow:
                hasPriceCross = (ppsr_df["close"].iloc[0] > ppsr_df[ppToCheck].iloc[0] and 
                             ppsr_df["close"].iloc[1] <= ppsr_df[ppToCheck].iloc[1])
            else:
                hasPriceCross = (ppsr_df["close"].iloc[0] < ppsr_df[ppToCheck].iloc[0] and 
                             ppsr_df["close"].iloc[1] >= ppsr_df[ppToCheck].iloc[1])
            if hasPriceCross:
                percentageDiff = round(100*(ppsr_df["close"].iloc[0]-ppsr_df[ppToCheck].iloc[0])/ppsr_df[ppToCheck].iloc[0],1)
                saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                maText = f"Cross-{'FromBelow' if crossDirectionFromBelow else 'FromAbove'}({ppToCheck}:{ppsr_df[ppToCheck].iloc[0]})"
                saveDict["MA-Signal"] = saved[1] + maText + f"({percentageDiff}%)"
                screenDict["MA-Signal"] = saved[0] + f"{colorText.GREEN}{maText}{colorText.END}{colorText.FAIL if abs(percentageDiff) > 1 else colorText.WARN}({percentageDiff}%){colorText.END}"
        return hasPriceCross

    # Validate if the stock prices are at least rising by 2% for the last 3 sessions
    def validatePriceRisingByAtLeast2Percent(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        data = data.head(4)
        if len(data) < 4:
            return False
        day0 = data.iloc[0]["close"].item()
        dayMinus1 = data.iloc[1]["close"].item()
        dayMinus2 = data.iloc[2]["close"].item()
        dayMinus3 = data.iloc[3]["close"].item()
        percent3 = round((dayMinus2 - dayMinus3) * 100 / dayMinus3, 2)
        percent2 = round((dayMinus1 - dayMinus2) * 100 / dayMinus2, 2)
        percent1 = round((day0 - dayMinus1) * 100 / dayMinus1, 2)

        if percent1 >= 2 and percent2 >= 2 and percent3 >= 2:
            pct_change_text = (
                ("%.1f%%" % percent1)
                + (" (%.1f%%," % percent2)
                + (" %.1f%%)" % percent3)
            )
            saveDict["%Chng"] = pct_change_text
            screenDict["%Chng"] = colorText.GREEN + pct_change_text + colorText.END
            return True and self.getCandleType(data.head(1))
        return False

    #@measure_time
    # validate if RSI is within given range
    def validateRSI(self, df, screenDict, saveDict, minRSI, maxRSI,rsiKey="RSI"):
        if df is None or len(df) == 0:
            return False
        if rsiKey not in df.columns:
            return False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        rsi = int(data.head(1)[rsiKey].iloc[0])
        saveDict[rsiKey] = rsi
        # https://chartink.com/screener/rsi-screening
        if rsi> 0 and rsi >= minRSI and rsi <= maxRSI:  # or (rsi <= 71 and rsi >= 67):
            screenDict[rsiKey] = (
                colorText.GREEN + str(rsi) + colorText.END
            )
            return True if (rsiKey == "RSIi") else (self.validateRSI(df, screenDict, saveDict, minRSI, maxRSI,rsiKey="RSIi") or True)
        screenDict[rsiKey] = colorText.FAIL + str(rsi) + colorText.END
        # If either daily or intraday RSI comes within range?
        return False if (rsiKey == "RSIi") else (self.validateRSI(df, screenDict, saveDict, minRSI, maxRSI,rsiKey="RSIi"))

    # Validate if the stock is bullish in the short term
    def validateShortTermBullish(self, df, screenDict, saveDict):
        if df is None or len(df) == 0:
            return False
        data = df.copy()
        # https://chartink.com/screener/short-term-bullish
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        fk = 0 if len(data) < 3 else np.round(data["FASTK"].iloc[2], 5)
        # Reverse the dataframe for ichimoku calculations with date in ascending order
        df_new = data[::-1]
        try:
            df_ichi = df_new.rename(
                columns={
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "volume": "volume",
                }
            )
            ichi = pktalib.ichimoku(df_ichi, 9, 26, 52, 26)
            if ichi is None:
                return False
            df_new = pd.concat([df_new, ichi], axis=1)
            # Reverse again to get the most recent date on top
            df_new = df_new[::-1]
            df_new = df_new.head(1)
            df_new["cloud_green"] = df_new["ISA_9"].iloc[0] > df_new["ISB_26"].iloc[0]
            df_new["cloud_red"] = df_new["ISB_26"].iloc[0] > df_new["ISA_9"].iloc[0]
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            pass
        aboveCloudTop = False
        # baseline > cloud top (cloud is bound by span a and span b) and close is > cloud top
        if df_new["cloud_green"].iloc[0]:
            aboveCloudTop = (
                df_new["IKS_26"].iloc[0] > df_new["ISA_9"].iloc[0]
                and recent["close"].iloc[0] > df_new["ISA_9"].iloc[0]
            )
        elif df_new["cloud_red"].iloc[0]:
            aboveCloudTop = (
                df_new["IKS_26"].iloc[0] > df_new["ISB_26"].iloc[0]
                and recent["close"].iloc[0] > df_new["ISB_26"].iloc[0]
            )

        # Latest Ichimoku baseline is < latest Ichimoku conversion line
        if aboveCloudTop and df_new["IKS_26"].iloc[0] < df_new["ITS_9"].iloc[0]:
            # StochRSI crossed 20 and RSI > 50
            if fk > 20 and recent["RSI"].iloc[0] > 50:
                # condition of crossing the StochRSI main signal line from bottom to top
                if (
                    data["FASTD"].iloc[100] < data["FASTK"].iloc[100]
                    and data["FASTD"].iloc[101] > data["FASTK"].iloc[101]
                ):
                    # close > 50 period SMA/EMA and 200 period SMA/EMA
                    if (
                        recent["SSMA"].iloc[0] > recent["SMA"].iloc[0]
                        and recent["close"].iloc[0] > recent["SSMA"].iloc[0]
                        and recent["close"].iloc[0] > recent["LMA"].iloc[0]
                    ):
                        saved = self.findCurrentSavedValue(screenDict,saveDict,"MA-Signal")
                        screenDict["MA-Signal"] = (
                            saved[0] + colorText.GREEN + "Bullish" + colorText.END
                        )
                        saveDict["MA-Signal"] = saved[1] + "Bullish"
                        return True
        return False
    
    # Validate VCP
    def validateVCP(
        self, 
        df, 
        screenDict, 
        saveDict, 
        stockName=None, 
        window=3, 
        percentageFromTop=3
    ):
        """
        Validate Volatility Contraction Pattern (VCP) - Mark Minervini Style.
        
        ============================================================================
        WHAT IS VCP (Volatility Contraction Pattern)?
        ============================================================================
        The VCP is a bullish continuation pattern where a stock consolidates after 
        an uptrend, with each subsequent pullback becoming smaller in magnitude.
        
        A classic VCP consists of 3 legs of pullbacks, each approximately 70% of 
        the previous. This implementation focuses on the 3-leg pattern:
        
        - Leg 1: 20% pullback (from Peak1 to Trough1)
        - Leg 2: 14% pullback (from Peak2 to Trough2) - 70% of Leg1
        - Leg 3: 10% pullback (from Peak3 to Trough3) - 71% of Leg2
        
        ============================================================================
        CRITICAL CONDITIONS FOR A VALID VCP:
        ============================================================================
        
        1. 4 PEAKS AND 3 TROUGHS (3-Leg Structure)
        2. STRICTLY HIGHER LOWS (T1 < T2 < T3) - Non-negotiable
        3. PROGRESSIVE TIGHTENING (L1 > L2 > L3)
        4. POSITIVE PULLBACKS (All legs > 0)
        5. 70% RULE (L2/L1 ≤ 70%, L3/L2 ≤ 70%)
        6. VOLATILITY CONTRACTION (RVM < 30)
        7. MINIMUM TIGHTENING (Leg1-Leg2 ≥ 2%, Leg2-Leg3 ≥ 1%)
        8. PROXIMITY TO ATH (≤ 20%)
        9. PRICE ABOVE LAST TROUGH, BELOW HIGHEST PEAK
        
        ============================================================================
        """
        
        # =========================================================================
        # INPUT VALIDATION
        # =========================================================================
        if df is None or len(df) < 120:
            return False
        
        data = df.copy()
        
        # Get configuration values
        enable_filters = getattr(self.configManager, 'enableAdditionalVCPFilters', False)
        max_rvm_allowed = getattr(self.configManager, 'vcpMaxRVM', 60)
        # These parameters enforce minimum contraction requirements between consecutive 
        # legs of the VCP pattern. They ensure that each subsequent pullback is 
        # meaningfully smaller than the previous one, not just marginally smaller.
        # In a true VCP, each leg's pullback should be significantly smaller than the previous leg:
        # Leg 1: 20% pullback
        # Leg 2: 14% pullback (6% smaller = tightening)
        # Leg 3: 10% pullback (4% smaller = further tightening). The problem is that some 
        # patterns show negligible tightening - for example:
        # Leg 1: 20% pullback
        # Leg 2: 19.5% pullback (only 0.5% smaller) ← This is NOT meaningful tightening
        # Leg 3: 19.0% pullback (only 0.5% smaller) ← Still not meaningful
        # These min_tightening parameters reject such weak patterns.
        min_tightening_leg2 = getattr(self.configManager, 'vcpMinTighteningLeg2', 2) # default 2%
        min_tightening_leg3 = getattr(self.configManager, 'vcpMinTighteningLeg3', 1) # default 1%
        
        try:
            # =========================================================================
            # STEP 1: OPTIONAL EMA FILTERS
            # =========================================================================
            if hasattr(self, 'configManager') and self.configManager and \
            getattr(self.configManager, 'enableAdditionalVCPEMAFilters', False):
                reversedData = data[::-1] 
                ema50 = pktalib.EMA(reversedData["close"], timeperiod=50)
                ema20 = pktalib.EMA(reversedData["close"], timeperiod=20)
                
                if len(ema50) > 0 and len(ema20) > 0:
                    current_close = data["close"].iloc[0]
                    if not (current_close >= ema50.tail(1).iloc[0] and 
                            current_close >= ema20.tail(1).iloc[0]):
                        return False
            
            # =========================================================================
            # STEP 2: DETECT LOCAL PEAKS AND TROUGHS
            # =========================================================================
            percentageFromTop /= 100
            data_reset = data.reset_index(drop=False)
            
            if 'index' in data_reset.columns:
                data_reset.rename(columns={"index": "Date"}, inplace=True)
            else:
                data_reset['Date'] = data_reset.index
            
            high_values = np.array(data_reset["high"])
            low_values = np.array(data_reset["low"])
            
            try:
                top_indices = pktalib.argrelextrema(high_values, np.greater_equal, order=window)[0]
                bot_indices = pktalib.argrelextrema(low_values, np.less_equal, order=window)[0]
            except Exception as e:
                return False
            
            data_reset["tops"] = 0
            data_reset["bots"] = 0
            
            for idx in top_indices[:8]:
                if idx < len(data_reset):
                    data_reset.loc[idx, "tops"] = data_reset.loc[idx, "high"]
            
            for idx in bot_indices[:8]:
                if idx < len(data_reset):
                    data_reset.loc[idx, "bots"] = data_reset.loc[idx, "low"]
            
            # =========================================================================
            # STEP 3: BUILD ALTERNATING PEAK-TROUGH SEQUENCE
            # =========================================================================
            peaks_found = []
            troughs_found = []
            
            for i in range(len(data_reset)):
                if data_reset.iloc[i]["tops"] > 0:
                    peaks_found.append((i, data_reset.iloc[i]["tops"]))
                if data_reset.iloc[i]["bots"] > 0:
                    troughs_found.append((i, data_reset.iloc[i]["bots"]))
            
            all_points = []
            for idx, val in peaks_found:
                all_points.append((idx, val, 'peak'))
            for idx, val in troughs_found:
                all_points.append((idx, val, 'trough'))
            
            all_points.sort(key=lambda x: x[0], reverse=True)
            
            sequence = []
            last_was_peak = None
            
            for idx, val, ptype in all_points:
                if last_was_peak is None and ptype == 'peak':
                    sequence.append((idx, val, ptype))
                    last_was_peak = True
                elif last_was_peak == True and ptype == 'trough':
                    sequence.append((idx, val, ptype))
                    last_was_peak = False
                elif last_was_peak == False and ptype == 'peak':
                    sequence.append((idx, val, ptype))
                    last_was_peak = True
            
            peaks_in_sequence = [s for s in sequence if s[2] == 'peak']
            troughs_in_sequence = [s for s in sequence if s[2] == 'trough']
            
            if len(peaks_in_sequence) < 4 or len(troughs_in_sequence) < 3:
                return False
            
            recent_peaks = peaks_in_sequence[:4]
            recent_troughs = troughs_in_sequence[:3]
            
            peak4_idx, peak4_val, _ = recent_peaks[0] if len(recent_peaks) >= 1 else (0, 0, 'peak')
            peak3_idx, peak3_val, _ = recent_peaks[1] if len(recent_peaks) >= 2 else (0, 0, 'peak')
            peak2_idx, peak2_val, _ = recent_peaks[2] if len(recent_peaks) >= 3 else (0, 0, 'peak')
            peak1_idx, peak1_val, _ = recent_peaks[3] if len(recent_peaks) >= 4 else (0, 0, 'peak')
            
            trough3_idx, trough3_val, _ = recent_troughs[0] if len(recent_troughs) >= 1 else (0, 0, 'trough')
            trough2_idx, trough2_val, _ = recent_troughs[1] if len(recent_troughs) >= 2 else (0, 0, 'trough')
            trough1_idx, trough1_val, _ = recent_troughs[2] if len(recent_troughs) >= 3 else (0, 0, 'trough')
            
            if any(v == 0 for v in [peak1_val, peak2_val, peak3_val, peak4_val, 
                                    trough1_val, trough2_val, trough3_val]):
                return False
            
            pattern_valid = (peak1_idx < trough1_idx < peak2_idx < 
                            trough2_idx < peak3_idx < trough3_idx < peak4_idx)
            
            if not pattern_valid and enable_filters:
                return False
            
            # =========================================================================
            # STEP 4: PROXIMITY TO ALL-TIME HIGH
            # =========================================================================
            all_time_high = peak1_val
            current_price = data_reset["close"].iloc[0] if len(data_reset) > 0 else 0
            
            max_distance_allowed = 20
            if hasattr(self, 'configManager') and self.configManager:
                max_distance_allowed = getattr(self.configManager, 'vcpRangePercentageFromTop', 20)
            
            distance_from_ath_pct = ((all_time_high - current_price) / all_time_high) * 100 if all_time_high > 0 else 100
            
            if enable_filters and distance_from_ath_pct > max_distance_allowed:
                return False
            
            # =========================================================================
            # STEP 5: STRICTLY HIGHER LOWS (T1 < T2 < T3)
            # =========================================================================
            if not (trough1_val < trough2_val < trough3_val):
                return False
            
            # =========================================================================
            # STEP 6: PEAKS NOT DESCENDING SIGNIFICANTLY
            # =========================================================================
            if enable_filters:
                peak4_decline = ((peak1_val - peak4_val) / peak1_val) * 100 if peak1_val > 0 else 0
                if peak4_decline > 25:
                    return False
            
            # =========================================================================
            # STEP 7: CALCULATE PULLBACK PERCENTAGES
            # =========================================================================
            leg1_pullback = ((peak1_val - trough1_val) / peak1_val) * 100 if peak1_val > 0 else 0
            leg2_pullback = ((peak2_val - trough2_val) / peak2_val) * 100 if peak2_val > 0 else 0
            leg3_pullback = ((peak3_val - trough3_val) / peak3_val) * 100 if peak3_val > 0 else 0
            
            # =========================================================================
            # STEP 8: POSITIVE PULLBACKS VALIDATION
            # =========================================================================
            if leg1_pullback <= 0 or leg2_pullback <= 0 or leg3_pullback <= 0:
                return False
            
            # =========================================================================
            # STEP 9: PROGRESSIVE TIGHTENING
            # =========================================================================
            if not (leg2_pullback < leg1_pullback and leg3_pullback < leg2_pullback):
                return False
            
            # =========================================================================
            # STEP 10: MINIMUM TIGHTENING THRESHOLDS
            # =========================================================================
            tightening_leg2 = leg1_pullback - leg2_pullback
            tightening_leg3 = leg2_pullback - leg3_pullback
            
            if enable_filters:
                if tightening_leg2 < min_tightening_leg2:
                    return False
                if tightening_leg3 < min_tightening_leg3:
                    return False
            
            # =========================================================================
            # STEP 11: 70% RULE - Pullback percentage of each leg should be ≤ 70% of the previous leg
            # =========================================================================
            if enable_filters:
                pullback_threshold = float(getattr(self.configManager, 'vcp321RulePullbackPercentage', 70)) / 100
                
                if 0 < pullback_threshold < 1:
                    ratio_2_1 = leg2_pullback / leg1_pullback if leg1_pullback > 0 else 1
                    ratio_3_2 = leg3_pullback / leg2_pullback if leg2_pullback > 0 else 1
                    
                    if ratio_2_1 > pullback_threshold or ratio_3_2 > pullback_threshold:
                        return False
            
            # =========================================================================
            # STEP 12: VOLATILITY CONTRACTION (RVM VALIDATION - FIXED)
            # =========================================================================
            rvm_value = 0
            rvm_score = 0
            
            if enable_filters:
                try:
                    # Calculate RVM(15) - FIXED to handle Series return
                    rvm_result = pktalib.RVM(data["high"], data["low"], data["close"], 15)
                    
                    # Extract scalar value from Series if needed
                    if isinstance(rvm_result, pd.Series):
                        rvm_value = rvm_result.iloc[-1] if len(rvm_result) > 0 else 0
                    elif isinstance(rvm_result, (int, float)):
                        rvm_value = rvm_result
                    else:
                        rvm_value = 0
                    
                    # Ensure we have a scalar
                    rvm_value = float(rvm_value) if rvm_value is not None else 0
                    
                    # Check if RVM exceeds maximum allowed
                    if rvm_value > max_rvm_allowed and max_rvm_allowed > 0:
                        # if stockName and self.default_logger:
                        #     self.default_logger.debug(
                        #         f"{stockName}: VCP failed - RVM(15)={rvm_value:.1f} exceeds maximum allowed ({max_rvm_allowed})"
                        #     )
                        return False
                    
                    # Calculate RVM score for quality rating
                    if rvm_value < 15:
                        rvm_score = 30
                    elif rvm_value < 25:
                        rvm_score = 20
                    elif rvm_value < 35:
                        rvm_score = 10
                    else:
                        rvm_score = 0
                        
                except Exception as rvm_e:
                    # if stockName and self.default_logger:
                    #     self.default_logger.debug(f"RVM calculation failed for {stockName}: {rvm_e}")
                    # Don't fail VCP due to RVM calculation errors - just set to 0
                    rvm_value = 0
                    rvm_score = 0
            
            # =========================================================================
            # STEP 13: PRICE POSITION VALIDATION
            # =========================================================================
            price_above_last_trough = current_price > trough3_val
            price_below_highest_peak = current_price < peak1_val
            
            if not (price_above_last_trough and price_below_highest_peak):
                return False
            
            # =========================================================================
            # STEP 14: CALCULATE QUALITY SCORE (0-100)
            # =========================================================================
            quality_rvm_score = rvm_score
            
            ratio_2_1 = leg2_pullback / leg1_pullback if leg1_pullback > 0 else 1
            ratio_3_2 = leg3_pullback / leg2_pullback if leg2_pullback > 0 else 1
            
            if ratio_2_1 <= 0.65 and ratio_3_2 <= 0.65:
                quality_tightening_score = 30
            elif ratio_2_1 <= 0.75 and ratio_3_2 <= 0.75:
                quality_tightening_score = 25
            elif ratio_2_1 <= 0.85 and ratio_3_2 <= 0.85:
                quality_tightening_score = 20
            elif ratio_2_1 <= 0.95 and ratio_3_2 <= 0.95:
                quality_tightening_score = 15
            else:
                quality_tightening_score = 10
            
            low_rise_t2 = ((trough2_val - trough1_val) / trough1_val) * 100 if trough1_val > 0 else 0
            low_rise_t3 = ((trough3_val - trough2_val) / trough2_val) * 100 if trough2_val > 0 else 0
            avg_low_rise = (low_rise_t2 + low_rise_t3) / 2
            
            if avg_low_rise >= 5:
                quality_lows_score = 20
            elif avg_low_rise >= 3:
                quality_lows_score = 15
            elif avg_low_rise >= 1:
                quality_lows_score = 10
            else:
                quality_lows_score = 5
            
            if distance_from_ath_pct <= 5:
                quality_ath_score = 20
            elif distance_from_ath_pct <= 10:
                quality_ath_score = 15
            elif distance_from_ath_pct <= 15:
                quality_ath_score = 12
            elif distance_from_ath_pct <= 20:
                quality_ath_score = 10
            else:
                quality_ath_score = 0
            
            quality_score = quality_rvm_score + quality_tightening_score + quality_lows_score + quality_ath_score
            
            if quality_score >= 85:
                quality_rating = "EXCELLENT"
                quality_icon = "⭐"
            elif quality_score >= 70:
                quality_rating = "GOOD"
                quality_icon = "⭐"
            elif quality_score >= 50:
                quality_rating = "ACCEPTABLE"
                quality_icon = "⚠️"
            else:
                quality_rating = "POOR"
                quality_icon = "❌"
            
            # =========================================================================
            # STEP 15: SUCCESS! VALID 3-LEG VCP DETECTED
            # =========================================================================
            consolidations = [f"{int(leg1_pullback)}%", f"{int(leg2_pullback)}%", f"{int(leg3_pullback)}%"]
            low_rise_pct_t2 = ((trough2_val - trough1_val) / trough1_val) * 100 if trough1_val > 0 else 0
            low_rise_pct_t3 = ((trough3_val - trough2_val) / trough2_val) * 100 if trough2_val > 0 else 0
            
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            
            screenDict["Pattern"] = (
                saved[0] 
                + colorText.GREEN
                + f"VCP (BO: {peak1_val:.1f}, Cons.:{','.join(consolidations)})"
                + colorText.END
            )
            
            screenDict["Quality(Score)"] = f"{quality_icon} {quality_rating} ({quality_score})"
            screenDict["Score"] = quality_score
            
            saveDict["Pattern"] = saved[1] + f"VCP (BO: {peak1_val:.1f}, Cons.:{','.join(consolidations)})"
            saveDict["Quality(Score)"] = f"{quality_icon} {quality_rating} ({quality_score})"
            saveDict["Score"] = quality_score
            saveDict["deviationScore"] = round((low_rise_pct_t2 + low_rise_pct_t3) / 2, 2)
            
            # saveDict["VCP_Leg1_Pullback"] = round(leg1_pullback, 1)
            # saveDict["VCP_Leg2_Pullback"] = round(leg2_pullback, 1)
            # saveDict["VCP_Leg3_Pullback"] = round(leg3_pullback, 1)
            # saveDict["VCP_Trough1"] = round(trough1_val, 2)
            # saveDict["VCP_Trough2"] = round(trough2_val, 2)
            # saveDict["VCP_Trough3"] = round(trough3_val, 2)
            # saveDict["VCP_Peak1"] = round(peak1_val, 2)
            # saveDict["VCP_Peak4"] = round(peak4_val, 2)
            # saveDict["VCP_DistanceFromATH"] = round(distance_from_ath_pct, 1)
            # saveDict["VCP_RisingLowScore"] = round((low_rise_pct_t2 + low_rise_pct_t3) / 2, 2)
            # saveDict["VCP_RVM"] = round(rvm_value, 1) if rvm_value > 0 else 0
            # saveDict["VCP_Tightening_Leg2"] = round(tightening_leg2, 1)
            # saveDict["VCP_Tightening_Leg3"] = round(tightening_leg3, 1)
            
            # if stockName and self.default_logger and enable_filters:
            #     self.default_logger.debug(
            #         f"{stockName}: ✓ VALID 3-LEG VCP - Pullbacks: {leg1_pullback:.1f}% → {leg2_pullback:.1f}% → {leg3_pullback:.1f}%, "
            #         f"Lows: {trough1_val:.2f} → {trough2_val:.2f} → {trough3_val:.2f}, "
            #         f"RVM: {rvm_value:.1f}, Quality: {quality_rating} ({quality_score})"
            #     )
            
            return True
            
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            if self.default_logger and stockName:
                self.default_logger.debug(f"validateVCP error for {stockName}: {e}")
            return False

    # Validate VCP as per Mark Minervini
    # https://chartink.com/screener/volatility-compression
    def validateVCPMarkMinervini(self, df: pd.DataFrame, screenDict, saveDict):
        """
        Validate Mark Minervini's VCP (Volatility Contraction Pattern) criteria.
        
        Key Elements:
        1. Uptrend: Price above key MAs with MA alignment (EMA13 > EMA26 > SMA50)
        2. Tightening: Each pullback is ≤70% of previous pullback
        3. Volume contraction: Volume dries up during pullbacks
        4. Pivot: Breakout attempt on above-average volume
        
        Args:
            df: Daily OHLCV data (newest first)
            screenDict: Dictionary for screen display
            saveDict: Dictionary for saving results
            
        Returns:
            bool: True if VCP pattern detected
        """
        if df is None or len(df) < 90:  # Minervini needs ~1 year of data
            return False
        
        data = df.copy()
        ohlc_dict = {
            "open": 'first',
            "high": 'max',
            "low": 'min',
            "close": 'last',
            "volume": 'sum'
        }
        try:
            # Weekly timeframe for trend analysis
            weeklyData = data.resample('W-FRI', offset=None).agg(ohlc_dict)
            weeklyData = weeklyData.dropna()
            
            if len(weeklyData) < 50:
                return False
        
            # =========================================================
            # PART 1: TREND ANALYSIS (Minervini's "Stage 2" Uptrend)
            # =========================================================
            w_ema_13 = pktalib.EMA(weeklyData["close"], timeperiod=13).tail(1).iloc[0]
            w_ema_26 = pktalib.EMA(weeklyData["close"], timeperiod=26).tail(1).iloc[0]
            w_sma_50 = pktalib.SMA(weeklyData["close"], timeperiod=50).tail(1).iloc[0]
        except:
            return False
        
        # Uptrend condition: 13EMA > 26EMA > 50SMA
        if not (w_ema_13 > w_ema_26 > w_sma_50):
            return False
        
        current_price = data["close"].iloc[0]
        
        # =========================================================
        # PART 2: DETECT SWING HIGHS AND MEASURE PULLBACKS
        # =========================================================
        # Find swing highs (peaks) using argrelextrema
        from scipy.signal import argrelextrema
        import numpy as np
        
        highs = data['high'].values
        lows = data['low'].values
        closes = data['close'].values
        
        # Find local maxima (peaks) over 10-day window
        window = 10
        peak_indices = argrelextrema(highs, np.greater_equal, order=window)[0]
        trough_indices = argrelextrema(lows, np.less_equal, order=window)[0]
        
        # Filter to last 90 days only
        peak_indices = [i for i in peak_indices if i < 90]
        trough_indices = [i for i in trough_indices if i < 90]
        
        if len(peak_indices) < 3:
            return False
        
        # Get most recent 4 peaks
        peaks = [(idx, highs[idx]) for idx in peak_indices[-4:]]
        
        # Measure pullback percentages between peaks
        pullbacks = []
        for i in range(1, len(peaks)):
            prev_peak_price = peaks[i-1][1]
            current_peak_price = peaks[i][1]
            
            # Find lowest point between these two peaks
            start_idx = peaks[i-1][0]
            end_idx = peaks[i][0]
            if start_idx < end_idx:
                lowest_in_between = min(lows[start_idx:end_idx+1])
                pullback_pct = ((prev_peak_price - lowest_in_between) / prev_peak_price) * 100
                pullbacks.append(pullback_pct)
        
        # Need at least 2 pullbacks for valid VCP
        if len(pullbacks) < 2:
            return False
        
        # =========================================================
        # PART 3: PROGRESSIVE TIGHTENING CHECK (70% RULE)
        # =========================================================
        is_tightening = True
        tightening_details = []
        
        for i in range(1, len(pullbacks)):
            prev = pullbacks[i-1]
            current = pullbacks[i]
            ratio = current / prev if prev > 0 else 1
            
            if ratio <= 0.70:
                tightening_details.append(f"Leg {i}: {current:.1f}% ≤ 70% of {prev:.1f}% ✓")
            else:
                is_tightening = False
                tightening_details.append(f"Leg {i}: {current:.1f}% > 70% of {prev:.1f}% ✗")
                break
        
        if not is_tightening:
            return False
        
        # =========================================================
        # PART 4: VOLUME CONTRACTION DURING PULLBACKS
        # =========================================================
        # Volume should dry up significantly during pullbacks
        has_volume_contraction = True
        
        # Get average volume on up days vs down days in recent pullback
        last_peak_idx = peaks[-1][0]
        if last_peak_idx + 10 < len(data):
            # Check volume in last pullback
            pullback_start = peaks[-2][0] if len(peaks) >= 2 else 0
            pullback_end = last_peak_idx
            
            if pullback_start < pullback_end:
                pullback_volumes = data['volume'].iloc[pullback_start:pullback_end+1]
                avg_pullback_volume = pullback_volumes.mean()
                
                # Get average volume on up days in last 10 days
                up_day_volumes = data['volume'].iloc[:10][data['close'].iloc[:10] > data['close'].shift(1).iloc[:10]]
                avg_up_volume = up_day_volumes.mean() if len(up_day_volumes) > 0 else avg_pullback_volume
                
                if avg_pullback_volume and avg_up_volume:
                    vol_ratio = avg_pullback_volume / avg_up_volume
                    if vol_ratio > 0.7:  # Pullback volume should be less than 70% of up-day volume
                        has_volume_contraction = False
        
        # =========================================================
        # PART 5: ABOVE-AVERAGE VOLUME ON RECENT UPTICK
        # =========================================================
        recent_avg_volume = data['volume'].iloc[1:11].mean()
        current_volume = data['volume'].iloc[0]
        has_recent_volume_surge = current_volume > recent_avg_volume * 1.2
        
        # =========================================================
        # PART 6: PRICE POSITION (near recent high, not extended)
        # =========================================================
        recent_high = max(highs[:20])  # Highest in last 20 days
        price_position = (current_price / recent_high) * 100 if recent_high > 0 else 0
        
        # Price should be within 10% of recent high (not extended)
        is_near_high = price_position > 90
        
        # Price should be above key moving averages
        sma_50 = pktalib.SMA(data['close'], timeperiod=50).tail(1).iloc[0]
        sma_150 = pktalib.SMA(data['close'], timeperiod=150).tail(1).iloc[0]
        sma_200 = pktalib.SMA(data['close'], timeperiod=200).tail(1).iloc[0]
        
        above_key_ma = current_price > sma_50 > sma_150 > sma_200
        
        # =========================================================
        # PART 7: FINAL VALIDATION
        # =========================================================
        is_vcp = (is_tightening and 
                is_near_high and 
                above_key_ma and 
                has_recent_volume_surge and
                has_volume_contraction)
        
        if is_vcp:
            saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
            tightening_str = " → ".join([f"{p:.1f}%" for p in pullbacks[:3]])
            screenDict["Pattern"] = (
                saved[0] 
                + colorText.GREEN
                + f"VCP(Minervini)"
                + colorText.END
            )
            saveDict["Pattern"] = saved[1] + f"VCP(Minervini)"
            saveDict["Pattern_Details"] = f"Pullbacks: {tightening_str}"
        
        return is_vcp

    # Validate if volume of last day is higher than avg
    def validateVolume(
        self, df, screenDict, saveDict, volumeRatio=2.5, minVolume=100
    ):
        if df is None or len(df) == 0:
            return False, False
        data = df.copy()
        data = data.fillna(0)
        data = data.replace([np.inf, -np.inf], 0)
        recent = data.head(1)
        # Either the rolling volume of past 20 sessions or today's volume should be > min volume
        hasMinimumVolume = (
            recent["VolMA"].iloc[0] >= minVolume
            or recent["volume"].iloc[0] >= minVolume
        )
        if recent["VolMA"].iloc[0] == 0:  # Handles Divide by 0 warning
            saveDict["volume"] = 0  # "Unknown"
            screenDict["volume"] = 0
            return False, hasMinimumVolume
        ratio = round(recent["volume"].iloc[0] / recent["VolMA"].iloc[0], 2)
        saveDict["volume"] = ratio
        if ratio >= volumeRatio and ratio != np.nan and (not math.isinf(ratio)):
            screenDict["volume"] = ratio
            return True, hasMinimumVolume
        screenDict["volume"] = ratio
        return False, hasMinimumVolume

    # Find if stock is validating volume spread analysis
    def validateVolumeSpreadAnalysis(self, df, screenDict, saveDict):
        try:
            if df is None or len(df) == 0:
                return False
            data = df.copy()
            data = data.head(2)
            if len(data) < 2:
                return False
            try:
                # Check for previous RED candles
                # Current candle = 0th, Previous Candle = 1st for following logic
                if data.iloc[1]["open"] >= data.iloc[1]["close"]:
                    spread1 = abs(data.iloc[1]["open"] - data.iloc[1]["close"])
                    spread0 = abs(data.iloc[0]["open"] - data.iloc[0]["close"])
                    lower_wick_spread0 = (
                        max(data.iloc[0]["open"], data.iloc[0]["close"])
                        - data.iloc[0]["low"]
                    )
                    vol1 = data.iloc[1]["volume"]
                    vol0 = data.iloc[0]["volume"]
                    saved = self.findCurrentSavedValue(screenDict, saveDict, "Pattern")
                    if (
                        spread0 > spread1
                        and vol0 < vol1
                        and data.iloc[0]["volume"] < data.iloc[0]["VolMA"]
                        and data.iloc[0]["close"] <= data.iloc[1]["open"]
                        and spread0 < lower_wick_spread0
                        and data.iloc[0]["volume"] <= int(data.iloc[1]["volume"] * 0.75)
                    ):
                        screenDict["Pattern"] = (
                            saved[0] 
                            + colorText.GREEN
                            + "Supply Drought"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Supply Drought"
                        return True
                    if (
                        spread0 < spread1
                        and vol0 > vol1
                        and data.iloc[0]["volume"] > data.iloc[0]["VolMA"]
                        and data.iloc[0]["close"] <= data.iloc[1]["open"]
                    ):
                        screenDict["Pattern"] = (
                            saved[0] 
                            + colorText.GREEN
                            + "Demand Rise"
                            + colorText.END
                        )
                        saveDict["Pattern"] = saved[1] + "Demand Rise"
                        return True
            except KeyboardInterrupt: # pragma: no cover
                raise KeyboardInterrupt
            except IndexError as e: # pragma: no cover
                # self.default_logger.debug(e, exc_info=True)
                pass
            return False
        except KeyboardInterrupt: # pragma: no cover
            raise KeyboardInterrupt
        except Exception as e:  # pragma: no cover
            self.default_logger.debug(e, exc_info=True)
            return False

    # Function to compute ATRTrailingStop
    def xATRTrailingStop_func(self,close, prev_close, prev_atr, nloss):
        if close > prev_atr and prev_close > prev_atr:
            return max(prev_atr, close - nloss)
        elif close < prev_atr and prev_close < prev_atr:
            return min(prev_atr, close + nloss)
        elif close > prev_atr:
            return close - nloss
        else:
            return close + nloss
