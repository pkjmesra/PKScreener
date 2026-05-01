# PKScreener Scan Workflows

This document provides detailed documentation for each scan category and their execution workflows.

---

## Table of Contents
1. [Scan Option Format](#scan-option-format)
2. [Main Scan Categories (Level 0)](#main-scan-categories-level-0)
3. [Index Selection (Level 1)](#index-selection-level-1)
4. [Scanner Options (Level 2)](#scanner-options-level-2)
5. [Piped Scanners](#piped-scanners)
6. [Adding New Scanners](#adding-new-scanners)

---

## Scan Option Format

### Option String Structure
```
MenuOption:IndexOption:ExecuteOption:SubOption1:SubOption2:...

Examples:
┌────────────────────────────────────────────────────────────────────┐
│ X:12:1         → Scanner, All Nifty, Breakouts                     │
│ X:1:7:4        → Scanner, Nifty50, Chart Patterns, VCP             │
│ X:12:5:30:70   → Scanner, All Nifty, RSI, Min=30, Max=70           │
│ X:12:7:6:1     → Scanner, All Nifty, Charts, TTM Squeeze, Buy      │
│ B:12:1         → Backtest, All Nifty, Breakouts                    │
│ P:1:5          → Piped, Predefined, Scan#5                         │
└────────────────────────────────────────────────────────────────────┘
```

### Piped Scanner Format
```
FirstScanner:>|SecondScanner:>|ThirdScanner:

Example: X:12:9:2.5:>|X:0:31:>|X:0:27:
         ↓           ↓          ↓
         Volume>2.5x  High Mom   ATR Cross
```

---

## Main Scan Categories (Level 0)

### X - Scanners (Primary)
**Entry Point**: `globals.py::main()` → `getScannerMenuChoices()`
**Handler**: `StockScreener.screenStocks()` with selected criteria

```
Workflow:
1. User selects "X" from main menu
2. Index selection menu displayed (Level 1)
3. Scan criteria menu displayed (Level 2)
4. Sub-options if applicable (Level 3+)
5. Stock data loaded from cache or fetched
6. Multiprocessing pool screens each stock
7. Results aggregated and displayed
```

### B - Backtests
**Entry Point**: `globals.py::main()` → `BacktestHandler`
**Handler**: `Backtest.backtest()` with historical analysis

```
Workflow:
1. User selects "B" → Index → Scan criteria
2. User enters backtest period (days)
3. For each qualifying stock:
   - Run screening on historical dates
   - Calculate returns for 1,2,3,4,5,10,15,22,30 periods
4. Aggregate statistics displayed
5. Summary with strategy correctness
```

### G - Growth of 10k
**Entry Point**: `globals.py::prepareGrowthOf10kResults()`
**Purpose**: Track hypothetical investment growth

### P - Piped Scanners
**Entry Point**: `globals.py::addOrRunPipedMenus()`
**Handler**: Sequential filter application

```
Workflow:
1. User selects predefined or custom piped scan
2. First scanner runs on full stock universe
3. Results filtered to next scanner input
4. Process repeats for each pipe stage
5. Final filtered results displayed
```

### C - Intraday Analysis
**Entry Point**: `PKMarketOpenCloseAnalyser`
**Purpose**: Compare morning vs close outcomes

### D - Data Downloads
**Entry Point**: `MainLogic._handle_download_menu()`
**Options**:
- D: Daily OHLCV data
- I: Intraday OHLCV data
- N: NSE equity symbols
- S: Sector/Industry details

### F - Find Stock in Scanners
**Purpose**: Check which scanners a specific stock qualifies for

### M - Monitor Intraday
**Entry Point**: `MarketMonitor`
**Purpose**: Real-time monitoring with configurable intervals

### T - Time Period Settings
**Purpose**: Configure candle periods (daily, weekly, intraday)

---

## Index Selection (Level 1)

| Key | Index | Stock Count (approx) |
|-----|-------|---------------------|
| 0 | Custom stock list | User defined |
| 1 | Nifty 50 | 50 |
| 2 | Nifty Next 50 | 50 |
| 3 | Nifty 100 | 100 |
| 4 | Nifty 200 | 200 |
| 5 | Nifty 500 | 500 |
| 6 | Nifty Smallcap 50 | 50 |
| 7 | Nifty Smallcap 100 | 100 |
| 8 | Nifty Smallcap 250 | 250 |
| 9 | Nifty Midcap 50 | 50 |
| 10 | Nifty Midcap 100 | 100 |
| 11 | Nifty Midcap 150 | 150 |
| 12 | All Nifty Stocks | ~2000+ |
| 13 | IPOs (Last 1 Year) | Variable |
| 14 | F&O Stocks | ~180 |
| 15 | NASDAQ | ~100 |
| W | Watchlist | User defined |
| S | Sectoral Indices | Sub-menu |
| N | Nifty Prediction (AI) | 50 |
| E | Live 5 EMA Scan | Real-time |

---

## Scanner Options (Level 2)

### Full Screening (0)
**Method**: `ScreeningStatistics.validateFullScreen()`
**Purpose**: Display all technical parameters without filtering

```python
# Shows: LTP, Change%, Volume, RSI, MACD, 50MA, 200MA, Trend, etc.
```

---

### Breakouts/Breakdowns (1, 2)
**Method**: `ScreeningStatistics.validateBreakout()`, `validateBreakdown()`
**Logic**:
```python
# Breakout (Option 1): Close > Resistance levels
# Breakdown (Option 2): Close < Support levels
# Uses consolidation range detection
```

---

### Consolidation (3)
**Method**: `ScreeningStatistics.validateConsolidation()`
**Logic**:
```python
# Price range < consolidationPercentage% over lookback period
# Indicates potential breakout setup
```

---

### Lowest Volume (4)
**Method**: `ScreeningStatistics.validateLowestVolume()`
**Logic**:
```python
# Volume is lowest in last N days
# Early breakout detection signal
# User specifies N days
```

---

### RSI Screening (5)
**Method**: `ScreeningStatistics.validateRSI()`
**Parameters**: minRSI, maxRSI
**Logic**:
```python
# RSI between user-specified range
# Example: RSI between 30-40 for oversold bounce plays
```

---

### Reversal Signals (6)
**Method**: `ScreeningStatistics.validateReversal()`
**Sub-Options**:

| Key | Signal | Description |
|-----|--------|-------------|
| 1 | Buy (Bullish) | Bullish reversal patterns |
| 2 | Sell (Bearish) | Bearish reversal patterns |
| 3 | Momentum Gainers | Rising bullish momentum |
| 4 | MA Reversal | Price bouncing off moving averages |
| 5 | VSA Reversal | Volume Spread Analysis signals |
| 6 | NRx Reversal | Narrow Range patterns |
| 7 | Lorentzian | ML-based classifier |
| 8 | PSAR+RSI | Combined indicator reversal |
| 9 | Rising RSI | RSI trending up |
| 10 | RSI MA Reversal | RSI crossing its MA |

---

### Chart Patterns (7)
**Method**: `ScreeningStatistics.validateChartPattern()`, `CandlePatterns`
**Sub-Options**:

| Key | Pattern | Description |
|-----|---------|-------------|
| 1 | Bullish Inside Bar | Flag pattern (bullish) |
| 2 | Bearish Inside Bar | Flag pattern (bearish) |
| 3 | Confluence | 50 & 200 MA/EMA convergence |
| 4 | VCP | Volatility Contraction Pattern |
| 5 | Trendline Support | Buying at support |
| 6 | TTM Squeeze | Bollinger Bands squeeze |
| 7 | Candlestick Patterns | All candlestick patterns |
| 8 | VCP (Minervini) | Mark Minervini's VCP criteria |
| 9 | Moving Average Signals | MA crossovers and support |

#### Chart Pattern Sub-Sub-Options

**TTM Squeeze (7:6:x)**:
| Key | Signal |
|-----|--------|
| 1 | Squeeze Buy |
| 2 | In Squeeze |
| 3 | Squeeze Sell |
| 4 | Any/All |

**Confluence (7:3:x)**:
| Key | Signal |
|-----|--------|
| 1 | Golden Crossover (50>200) |
| 2 | Dead Crossover (50<200) |
| 3 | Any/All |
| 4 | Super-Confluence (8,21,55 EMA + 200 SMA) |

**MA Signals (7:9:x)**:
| Key | Signal |
|-----|--------|
| 1 | MA Support |
| 2 | Bearish Signals |
| 3 | Bullish Signals |
| 4 | BearCross MA |
| 5 | BullCross MA |
| 6 | MA Resist |
| 7 | BullCross VWAP |

---

### CCI Screening (8)
**Method**: `ScreeningStatistics.validateCCI()`
**Logic**: CCI outside specified range

---

### Volume Gainers (9)
**Method**: `ScreeningStatistics.validateVolumeSpread()`
**Parameter**: volumeRatio (default 2.5)
**Logic**:
```python
# Current volume > volumeRatio * average volume
# Indicates unusual trading activity
```

---

### Closing Up 2%+ (10)
**Method**: `ScreeningStatistics.validate52WeekLowBreakout()` variant
**Logic**: Stock closing at least 2% up for last 3 consecutive days

---

### Ichimoku Bullish (11)
**Method**: `ScreeningStatistics.validateIchimoku()`
**Logic**: Price above Ichimoku cloud, bullish signals

---

### N-Minute Breakout (12)
**Method**: `ScreeningStatistics.validatePriceVolumeBreakout()`
**Purpose**: Intraday price and volume breakout detection

---

### RSI + MACD (13)
**Method**: Combined RSI and MACD validation
**Logic**: Both indicators showing bullish signals

---

### NR4 Daily (14)
**Method**: `ScreeningStatistics.validateNR4()`
**Logic**: Today's range is narrowest of last 4 days

---

### 52 Week Low Breakout (15)
**Method**: `ScreeningStatistics.validate52WeekLowBreakout()`
**Purpose**: Selling signal (breaking 52-week low)

---

### 10 Days Low Breakout (16)
**Method**: Similar to 52-week but 10-day period

---

### 52 Week High Breakout (17)
**Method**: `ScreeningStatistics.validate52WeekHighBreakout()`
**Purpose**: Buying on new highs

---

### Aroon Crossover (18)
**Method**: `ScreeningStatistics.validateAroonCrossover()`
**Logic**: Aroon Up crossing above Aroon Down

---

### MACD Histogram Sell (19)
**Method**: MACD histogram crossing below zero

---

### Bullish for Next Day (20)
**Method**: Combined end-of-day bullish signals

---

### MF/FII Popular (21)
**Method**: `ScreeningStatistics.validateMutualFunds()`
**Sub-Options**:

| Key | Criteria |
|-----|----------|
| 1 | Shares bought/sold by MF/FII |
| 2 | Shareholding by number of funds |
| 3 | MF/FII ownership increased |
| 4 | Dividend yield |
| 5 | Only MF ownership increased |
| 6 | Only MF ownership decreased |
| 7 | MF/FII ownership decreased |
| 8 | Fair value buy opportunities |
| 9 | Fair value sell opportunities |

---

### Breaking Out Now (23)
**Method**: `ScreeningStatistics.validateBreakingOutNow()`
**Logic**: Real-time breakout detection during market hours

---

### Higher Highs/Lows (24)
**Method**: SuperTrend and HH/HL pattern
**Logic**: Price making higher highs and higher lows

---

### Lower Highs (25)
**Method**: Watch for potential reversal
**Logic**: Price making lower highs

---

### Corporate Actions (26)
**Method**: Check for splits/bonus/dividends

---

### ATR Cross (27)
**Method**: `ScreeningStatistics.validateATRCross()`
**Logic**: ATR-based breakout signal

---

### Higher Opens (28)
**Method**: Bullish opening patterns

---

### Bid/Ask Buildup (29)
**Method**: Intraday order book analysis

---

### ATR Trailing Stops (30)
**Method**: `ScreeningStatistics.validateATRTrailingStops()`
**Purpose**: Swing trading with ATR-based stops

---

### High Momentum (31)
**Method**: `ScreeningStatistics.validateHighMomentum()`
**Logic**: RSI, MFI, CCI all showing momentum

---

### Intraday Setup (32)
**Method**: Breakout/breakdown setup for intraday

---

### Potential Profitable (33)
**Sub-Options**:
| Key | Setup |
|-----|-------|
| 1 | Frequent highs with bullish MAs |
| 2 | Bullish today for PDO/PDC |
| 3 | FnO > 2% above 50MA/200MA |

---

### Bullish AVWAP (34)
**Method**: Anchored VWAP analysis

---

### Short Sells (35-38)
**Methods**: Various short selling criteria

---

### IPO First Day (39)
**Method**: IPO lifetime first day bullish break

---

### Price Action (40)
**Method**: Pure price action analysis

---

### Pivot Points (41)
**Method**: `ScreeningStatistics.validatePivotPoints()`

---

### Super Gainers/Losers (42, 43)
**Method**: Biggest movers of the day

---

### Strong Signals (44-47)
**Methods**: Multi-indicator buy/sell signals

---

## Piped Scanners

### Predefined Piped Scans

| # | Description | Pipeline |
|---|-------------|----------|
| 1 | Volume + Momentum + Breakout + ATR | Vol>2.5x → Momentum → Breaking → ATR |
| 2 | Volume + Momentum + ATR | Vol>2.5x → Momentum → ATR |
| 3 | Volume + Momentum | Vol>2.5x → Momentum |
| 14 | VCP (Minervini) + Charts + MA | VCP → Patterns → MA Support |
| 20 | Full Combo | Vol → Mom → Break → ATR → VCP → Trail |
| 27 | Super-Confluence BTST | Confluence → VWAP Cross → Confluence |

### Custom Piped Scans
Users can define custom pipes using the format:
```
X:12:criteria1:>|X:0:criteria2:>|X:0:criteria3:
```

---

## Adding New Scanners

### Step-by-Step Guide

#### 1. Define Menu Entry
**File**: `pkscreener/classes/MenuOptions.py`

```python
level2_X_MenuDict = {
    # ... existing entries ...
    "48": "Your New Scanner Name",
}
MAX_SUPPORTED_MENU_OPTION = 48
```

#### 2. Implement Validation Logic
**File**: `pkscreener/classes/ScreeningStatistics.py`

```python
class ScreeningStatistics:
    # ... existing methods ...
    
    def validateYourNewScanner(
        self, 
        df: pd.DataFrame, 
        screenDict: dict, 
        saveDict: dict,
        **kwargs
    ) -> bool:
        """
        Validate if stock meets your new scanner criteria.
        
        Args:
            df: OHLCV DataFrame with columns [Open, High, Low, Close, Volume]
            screenDict: Dictionary to populate for display
            saveDict: Dictionary to populate for saving
            **kwargs: Additional parameters
            
        Returns:
            bool: True if stock passes criteria
        """
        try:
            # Get recent data
            close = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            
            # Calculate indicators
            sma_20 = pktalib.SMA(df['Close'], 20)
            rsi = pktalib.RSI(df['Close'], 14)
            
            # Your criteria
            condition1 = close > sma_20.iloc[-1]
            condition2 = rsi.iloc[-1] > 50
            condition3 = volume > df['Volume'].rolling(20).mean().iloc[-1] * 1.5
            
            if condition1 and condition2 and condition3:
                # Populate result dictionaries
                screenDict['Pattern'] = 'Your Pattern'
                screenDict['Signal'] = colorText.GREEN + 'Buy' + colorText.END
                saveDict['Pattern'] = 'Your Pattern'
                saveDict['Signal'] = 'Buy'
                return True
                
            return False
            
        except Exception as e:
            self.default_logger.debug(f"Error in validateYourNewScanner: {e}")
            return False
```

#### 3. Add to Screening Switch
**File**: `pkscreener/classes/StockScreener.py`

```python
# In screenStocks() method, find the executeOption switch
elif executeOption == 48:
    isValid = screeningDictionary.validateYourNewScanner(
        processedData,
        screenDict,
        saveDict,
        # Additional parameters if needed
    )
```

#### 4. Add Sub-Options (if needed)
**File**: `pkscreener/classes/MenuOptions.py`

```python
level3_X_YourScanner_MenuDict = {
    "1": "Sub-option 1",
    "2": "Sub-option 2",
    "0": "Cancel",
}
```

#### 5. Handle Sub-Options
**File**: `pkscreener/globals.py` or `pkscreener/classes/MainLogic.py`

```python
if executeOption == 48:
    # Handle sub-option input
    subOption = getSubOptionFromUser(level3_X_YourScanner_MenuDict)
```

#### 6. Write Tests
**File**: `test/ScreeningStatistics_test.py`

```python
class TestValidateYourNewScanner:
    def test_bullish_case(self):
        # Create test data
        df = create_bullish_test_data()
        stats = ScreeningStatistics(mock_config, mock_logger)
        
        result = stats.validateYourNewScanner(df, {}, {})
        assert result == True
    
    def test_bearish_case(self):
        df = create_bearish_test_data()
        stats = ScreeningStatistics(mock_config, mock_logger)
        
        result = stats.validateYourNewScanner(df, {}, {})
        assert result == False
```

#### 7. Document
Add entry to this documentation with:
- Method description
- Logic explanation
- Parameters
- Example usage

---

## See Also
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Getting started
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
