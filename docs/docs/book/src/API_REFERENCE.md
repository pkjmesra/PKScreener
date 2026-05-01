# PKScreener API Reference

This document provides detailed API documentation for the key classes and functions in PKScreener.

---

## Table of Contents
1. [Core Classes](#core-classes)
2. [Data Classes](#data-classes)
3. [Utility Classes](#utility-classes)
4. [Global Functions](#global-functions)

---

## Core Classes

### StockScreener

**Location**: `pkscreener/classes/StockScreener.py`

Main orchestrator for stock screening operations.

```python
class StockScreener:
    """
    Orchestrates the stock screening process for individual stocks.
    Used as the target function for multiprocessing pool.
    """
    
    def screenStocks(
        self,
        runOption: str,              # Current run option string
        menuOption: str,             # Main menu selection (X, B, G, etc.)
        exchangeName: str,           # Exchange name (NSE, NASDAQ)
        executeOption: int,          # Scan criteria number (0-47)
        reversalOption: int,         # Sub-option for reversals
        maLength: int,               # Moving average period
        daysForLowestVolume: int,    # Days for volume analysis
        minRSI: float,               # Minimum RSI threshold
        maxRSI: float,               # Maximum RSI threshold
        respChartPattern: int,       # Chart pattern selection
        insideBarToLookback: int,    # Inside bar lookback period
        totalSymbols: int,           # Total symbols being screened
        shouldCache: bool,           # Whether to cache data
        stock: str,                  # Stock symbol to screen
        newlyListedOnly: bool,       # Filter for IPOs only
        downloadOnly: bool,          # Only download, don't screen
        volumeRatio: float,          # Volume ratio threshold
        testbuild: bool = False,     # Test mode flag
        userArgs: Namespace = None,  # User passed arguments
        backtestDuration: int = 0,   # Backtest duration in days
        backtestPeriodToLookback: int = 30,
        logLevel: int = 0,
        portfolio: bool = False,
        testData: pd.DataFrame = None,
        hostRef: Any = None,         # PKMultiProcessorClient reference
    ) -> Tuple:
        """
        Screen a single stock against selected criteria.
        
        Returns:
            Tuple containing:
            - stock: Stock symbol
            - processedData: Processed DataFrame
            - originalData: Original DataFrame  
            - screenDict: Display dictionary
            - saveDict: Save dictionary
            - additionalData: Any additional computed data
            - backtest_df: Backtest results if applicable
            - xray_df: X-ray analysis data
        """
```

---

### ScreeningStatistics

**Location**: `pkscreener/classes/ScreeningStatistics.py`

Contains all technical analysis and screening validation methods.

```python
class ScreeningStatistics:
    """
    Provides technical analysis calculations and validation methods
    for all screening criteria.
    """
    
    def __init__(
        self, 
        configManager: ConfigManager = None,
        default_logger: Logger = None,
        shouldLog: bool = False
    ):
        """Initialize with configuration and logging."""
    
    # Core Validation Methods
    
    def validateFullScreen(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        processedData: pd.DataFrame
    ) -> bool:
        """
        Full technical screening with all parameters displayed.
        Always returns True (informational only).
        """
    
    def validateBreakout(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        daysToLookback: int
    ) -> bool:
        """
        Detect breakout from consolidation range.
        
        Args:
            df: OHLCV DataFrame
            screenDict: Display results dictionary
            saveDict: Save results dictionary
            daysToLookback: Number of days for range calculation
            
        Returns:
            bool: True if breakout detected
        """
    
    def validateBreakdown(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        daysToLookback: int
    ) -> bool:
        """Detect breakdown from consolidation range."""
    
    def validateConsolidation(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        percentage: float = 10
    ) -> bool:
        """
        Check if stock is in consolidation phase.
        
        Args:
            percentage: Maximum price range percentage
        """
    
    def validateLowestVolume(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        daysForLowestVolume: int
    ) -> bool:
        """Check if current volume is lowest in N days."""
    
    def validateRSI(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        minRSI: float,
        maxRSI: float
    ) -> bool:
        """
        Validate RSI is within specified range.
        
        Args:
            minRSI: Minimum RSI value
            maxRSI: Maximum RSI value
        """
    
    def validateReversal(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        reversalOption: int,
        maLength: int = 0
    ) -> bool:
        """
        Detect reversal patterns.
        
        Args:
            reversalOption: Type of reversal (1-10)
                1: Bullish reversal
                2: Bearish reversal
                3: Momentum gainers
                4: MA reversal
                5: VSA reversal
                6: NR reversal
                7: Lorentzian
                8: PSAR+RSI
                9: Rising RSI
                10: RSI MA reversal
        """
    
    def validateChartPattern(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        respChartPattern: int,
        daysToLookback: int
    ) -> bool:
        """
        Detect chart patterns.
        
        Args:
            respChartPattern: Pattern type (1-9)
        """
    
    def validateVolumeSpread(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        volumeRatio: float
    ) -> bool:
        """
        Check for volume spike.
        
        Args:
            volumeRatio: Minimum volume ratio vs average
        """
    
    def validateHighMomentum(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict
    ) -> bool:
        """Check RSI, MFI, CCI for momentum signals."""
    
    def validateATRCross(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict
    ) -> bool:
        """Detect ATR-based breakout signal."""
    
    def validateATRTrailingStops(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        atrMultiplier: float = 1.0
    ) -> bool:
        """
        ATR trailing stop analysis for swing trading.
        
        Args:
            atrMultiplier: ATR multiplier for stop calculation
        """
    
    # Technical Indicator Methods
    
    def getCCI(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate Commodity Channel Index."""
    
    def getRSI(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
    
    def getMACD(
        self, 
        df: pd.DataFrame
    ) -> Tuple[float, float, float]:
        """
        Calculate MACD.
        
        Returns:
            Tuple of (macd, signal, histogram)
        """
    
    def getSMA(self, df: pd.DataFrame, period: int) -> float:
        """Calculate Simple Moving Average."""
    
    def getEMA(self, df: pd.DataFrame, period: int) -> float:
        """Calculate Exponential Moving Average."""
    
    def getVWAP(self, df: pd.DataFrame) -> float:
        """Calculate Volume Weighted Average Price."""
    
    def getSupertrend(
        self, 
        df: pd.DataFrame,
        multiplier: float = 3.0,
        period: int = 10
    ) -> Tuple[pd.Series, str]:
        """
        Calculate Supertrend indicator.
        
        Returns:
            Tuple of (supertrend_series, direction)
        """
```

---

### CandlePatterns

**Location**: `pkscreener/classes/CandlePatterns.py`

Candlestick pattern detection.

```python
class CandlePatterns:
    """Detects various candlestick patterns."""
    
    reversalPatternsBullish = [
        "Morning Star", "Morning Doji Star", "Hammer",
        "Inverted Hammer", "Bullish Engulfing", ...
    ]
    
    reversalPatternsBearish = [
        "Evening Star", "Evening Doji Star", 
        "Bearish Engulfing", "Hanging Man", ...
    ]
    
    def findPattern(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        hostRef: Any = None
    ) -> bool:
        """
        Detect any candlestick pattern.
        
        Returns:
            bool: True if pattern found
        """
    
    def findBullishInsideBar(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        daysToLookback: int
    ) -> bool:
        """Detect bullish inside bar (flag) pattern."""
    
    def findBearishInsideBar(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict,
        daysToLookback: int
    ) -> bool:
        """Detect bearish inside bar pattern."""
    
    def findVCP(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict
    ) -> bool:
        """Detect Volatility Contraction Pattern."""
    
    def findMinerviniVCP(
        self,
        df: pd.DataFrame,
        screenDict: dict,
        saveDict: dict
    ) -> bool:
        """Detect Mark Minervini's VCP criteria."""
```

---

### Pktalib

**Location**: `pkscreener/classes/Pktalib.py`

Technical indicator calculations wrapper.

```python
class pktalib:
    """
    Static class wrapping TA-Lib or pandas-ta for technical indicators.
    Falls back to pandas-ta if TA-Lib not available.
    """
    
    @staticmethod
    def SMA(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
    
    @staticmethod
    def EMA(series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
    
    @staticmethod
    def RSI(series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
    
    @staticmethod
    def MACD(
        series: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD indicator.
        
        Returns:
            Tuple of (macd, signal, histogram)
        """
    
    @staticmethod
    def BBANDS(
        series: pd.Series,
        period: int = 20,
        std: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands.
        
        Returns:
            Tuple of (upper, middle, lower)
        """
    
    @staticmethod
    def ATR(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """Average True Range."""
    
    @staticmethod
    def STOCH(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator.
        
        Returns:
            Tuple of (slowK, slowD)
        """
    
    @staticmethod
    def ADX(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """Average Directional Index."""
```

---

## Data Classes

### Fetcher

**Location**: `pkscreener/classes/Fetcher.py`

Stock data fetching from various sources with high-performance real-time support.

```python
class screenerStockDataFetcher:
    """
    Fetches stock data from various sources with priority:
    1. In-memory candle store (real-time during market hours)
    2. Local pickle files
    3. Remote GitHub pickle files
    """
    
    def __init__(self, configManager: ConfigManager):
        """
        Initialize with configuration.
        
        Also initializes high-performance data provider if available.
        """
    
    def fetchStockData(
        self,
        stockCode: str,
        period: str,
        duration: str,
        proxyServer: str = None,
        screenResultsCounter: int = 0,
        screenCounter: int = 0,
        totalSymbols: int = 0,
        printCounter: bool = False,
        start: datetime = None,
        end: datetime = None,
        exchangeSuffix: str = ".NS",
        attempt: int = 0
    ) -> pd.DataFrame:
        """
        Fetch stock price data using high-performance data provider.
        
        Uses the following priority:
        1. In-memory candle store (real-time, during market hours)
        2. Local pickle files
        3. Remote GitHub pickle files
        
        Args:
            stockCode: Stock symbol (e.g., "RELIANCE")
            period: Data period (e.g., "1d", "5d", "1mo", "1y")
            duration: Candle interval (e.g., "1m", "5m", "1d")
            proxyServer: Optional proxy URL (deprecated, unused)
            screenResultsCounter: Counter for screening results
            screenCounter: Current screen position counter
            totalSymbols: Total number of symbols being processed
            printCounter: Whether to print progress to console
            start: Optional start date for data range
            end: Optional end date for data range
            exchangeSuffix: Exchange suffix (default: ".NS")
            attempt: Current retry attempt number
            
        Returns:
            pandas.DataFrame with OHLCV data or None
            
        Raises:
            StockDataEmptyException: If no data is fetched and printCounter is True
        """
    
    def fetchStockDataWithArgs(
        self,
        stockCodes: List[str],
        period: str = "1y",
        duration: str = "1d",
        exchangeSuffix: str = ".NS",
        **kwargs
    ) -> Tuple[Dict[str, pd.DataFrame], Dict]:
        """
        Fetch stock data for multiple symbols.
        
        Args:
            stockCodes: List of stock symbols
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
            duration: Candle duration (1m, 2m, 3m, 4m, 5m, 10m, 15m, 30m, 60m, 1d)
            exchangeSuffix: Exchange suffix (.NS, .BO, etc.)
            
        Returns:
            Tuple of (stock_data_dict, metadata_dict)
        """
    
    # High-Performance Real-Time Methods
    
    def getLatestPrice(
        self, 
        symbol: str, 
        exchangeSuffix: str = ".NS"
    ) -> float:
        """
        Get the latest price for a stock from real-time data.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE" or "RELIANCE.NS")
            exchangeSuffix: Exchange suffix to strip
            
        Returns:
            float: Latest price or 0.0 if not available
        """
    
    def getRealtimeOHLCV(
        self, 
        symbol: str, 
        exchangeSuffix: str = ".NS"
    ) -> dict:
        """
        Get real-time OHLCV data for a stock.
        
        Args:
            symbol: Stock symbol
            exchangeSuffix: Exchange suffix to strip
            
        Returns:
            dict: {'open': float, 'high': float, 'low': float, 
                   'close': float, 'volume': int} or empty dict
        """
    
    def isRealtimeDataAvailable(self) -> bool:
        """
        Check if real-time data is available.
        
        Real-time data is available when:
        1. PKBrokers is installed
        2. InMemoryCandleStore has instruments
        3. Last tick was received within 5 minutes
        
        Returns:
            bool: True if real-time data is available
        """
    
    def getAllRealtimeData(self) -> dict:
        """
        Get real-time OHLCV for all available stocks.
        
        Returns:
            dict: Mapping of symbol to OHLCV data
        """
    
    def fetchLatestNiftyDaily(self, proxyServer: str = None) -> pd.DataFrame:
        """
        Fetch daily Nifty 50 index data.
        
        Args:
            proxyServer: Optional proxy URL (deprecated)
            
        Returns:
            pandas.DataFrame with Nifty 50 daily data or None
        """
    
    def fetchFiveEmaData(self, proxyServer: str = None) -> tuple:
        """
        Fetch data required for the Five EMA strategy.
        
        Fetches both Nifty 50 and Bank Nifty data at 5m and 15m intervals.
        
        Args:
            proxyServer: Optional proxy URL (deprecated)
            
        Returns:
            tuple: (nifty_buy, banknifty_buy, nifty_sell, banknifty_sell)
                   or None if data unavailable
        """
    
    # Internal Helper Methods
    
    def _period_to_count(self, period: str, interval: str) -> int:
        """
        Convert period string to candle count.
        
        Args:
            period: Period string (e.g., "1y", "1mo", "5d")
            interval: Interval string (e.g., "5m", "1d")
            
        Returns:
            int: Number of candles
        """
    
    def _normalize_interval(self, interval: str) -> str:
        """
        Normalize interval string to standard format.
        
        Supported intervals:
        - 1m, 2m, 3m, 4m, 5m, 10m, 15m, 30m, 60m, day
        
        Args:
            interval: Input interval string
            
        Returns:
            str: Normalized interval
        """
    
    def fetchFileFromHostServer(
        self,
        filePath: str,
        tickerOption: int,
        fileContents: str = ""
    ) -> str:
        """Fetch pre-computed data from GitHub."""
```

### DataLoader

**Location**: `pkscreener/classes/DataLoader.py`

Data caching and loading utilities.

```python
def save_downloaded_data_impl(
    downloadOnly: bool,
    testing: bool,
    stockDictPrimary: Dict[str, pd.DataFrame],
    configManager: ConfigManager,
    loadCount: int
) -> None:
    """Save downloaded data to cache."""

def load_stock_data(
    intraday: bool = False
) -> Tuple[Dict[str, pd.DataFrame], bool]:
    """
    Load stock data from cache.
    
    Returns:
        Tuple of (stock_data_dict, was_loaded_from_cache)
    """
```

---

### ConfigManager

**Location**: `pkscreener/classes/ConfigManager.py`

Configuration management.

```python
class tools:
    """Configuration management utilities."""
    
    # Key configuration properties
    period: str = "1y"           # Data period
    duration: str = "1d"         # Candle duration
    daysToLookback: int = 22     # Analysis lookback days
    minLTP: float = 20.0         # Minimum price filter
    maxLTP: float = 50000.0      # Maximum price filter
    volumeRatio: float = 2.5     # Volume ratio threshold
    consolidationPercentage: float = 10  # Consolidation %
    shuffle: bool = True         # Shuffle stock order
    cacheEnabled: bool = True    # Enable data caching
    stageTwo: bool = True        # Stage 2 filter
    maxdisplayresults: int = 100 # Max results to display
    
    def getConfig(self, parser: ConfigParser) -> None:
        """Load configuration from file."""
    
    def setConfig(
        self,
        parser: ConfigParser,
        default: bool = False,
        showFileCreatedText: bool = True
    ) -> None:
        """Save configuration to file."""
    
    def toggleConfig(self, config_key: str) -> None:
        """Toggle a boolean configuration value."""
```

---

## Utility Classes

### ResultsManager

**Location**: `pkscreener/classes/ResultsManager.py`

Result formatting and display.

```python
class ResultsManager:
    """Manages result formatting, display, and export."""
    
    def format_results(
        self,
        screen_results: pd.DataFrame,
        save_results: pd.DataFrame,
        configManager: ConfigManager
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Format results for display and saving."""
    
    def label_data_for_printing(
        self,
        screenResults: pd.DataFrame,
        saveResults: pd.DataFrame,
        volumeRatio: float,
        executeOption: int,
        reversalOption: int,
        menuOption: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Apply labels and formatting to results."""
```

### BacktestHandler

**Location**: `pkscreener/classes/BacktestHandler.py`

Backtesting workflow management.

```python
class BacktestHandler:
    """Manages backtesting operations."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize with configuration."""
    
    def show_backtest_results(
        self,
        backtest_df: pd.DataFrame,
        sort_key: str = None,
        optional_name: str = ""
    ) -> str:
        """
        Display backtest results.
        
        Args:
            backtest_df: Backtest results DataFrame
            sort_key: Column to sort by
            optional_name: Optional name for output
            
        Returns:
            Formatted table string
        """
    
    def finish_backtest_data_cleanup(
        self,
        backtest_df: pd.DataFrame,
        df_xray: pd.DataFrame,
        default_answer: str = None
    ) -> Tuple[pd.DataFrame, bool, dict]:
        """
        Finalize and cleanup backtest data.
        
        Returns:
            Tuple of (summary_df, should_sort, sort_keys)
        """
    
    def take_backtest_inputs(
        self,
        userPassedArgs: Namespace
    ) -> int:
        """Get backtest period from user."""
```

### TelegramNotifier

**Location**: `pkscreener/classes/TelegramNotifier.py`

Telegram notifications.

```python
class TelegramNotifier:
    """Handles Telegram messaging for scan results."""
    
    @staticmethod
    def send_quick_scan_result(
        menu_choice_hierarchy: str,
        user: str,
        tabulated_results: str,
        markdown_results: str,
        caption: str,
        pngName: str = "scan",
        pngExtension: str = ".png"
    ) -> None:
        """
        Send scan results to Telegram.
        
        Args:
            menu_choice_hierarchy: Scan option string
            user: Target user/chat ID
            tabulated_results: HTML table string
            markdown_results: Markdown formatted results
            caption: Message caption
            pngName: Output image name
            pngExtension: Image file extension
        """
```

---

## Global Functions

### globals.py Functions

**Location**: `pkscreener/globals.py`

```python
def main(userArgs: Namespace) -> Optional[Tuple]:
    """
    Main entry point for screening operations.
    
    Args:
        userArgs: Parsed command line arguments
        
    Returns:
        Optional tuple with screening results
    """

def getScannerMenuChoices(
    testing: bool,
    downloadOnly: bool,
    startupoptions: str,
    defaultAnswer: str,
    options: str,
    user: str = None,
    userPassedArgs: Namespace = None
) -> Tuple[str, int, int, dict]:
    """
    Handle menu navigation and option selection.
    
    Returns:
        Tuple of (menuOption, indexOption, executeOption, selectedChoice)
    """

def runScanners(
    menuOption: str,
    indexOption: int,
    executeOption: int,
    reversalOption: int,
    listStockCodes: List[str],
    screenResults: pd.DataFrame,
    saveResults: pd.DataFrame,
    **kwargs
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Run screening across all stocks using multiprocessing.
    
    Returns:
        Tuple of (screenResults, saveResults, backtest_df)
    """

def printNotifySaveScreenedResults(
    screenResults: pd.DataFrame,
    saveResults: pd.DataFrame,
    iterations: int,
    numStocks: int,
    **kwargs
) -> None:
    """Display and save screening results."""

def finishScreening(
    downloadOnly: bool,
    testing: bool,
    stockDictPrimary: Dict,
    configManager: ConfigManager,
    loadCount: int,
    testBuild: bool,
    screenResults: pd.DataFrame,
    saveResults: pd.DataFrame,
    user: str = None
) -> None:
    """Cleanup and finalize screening session."""
```

---

## See Also
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Getting started
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [SCAN_WORKFLOWS.md](SCAN_WORKFLOWS.md) - Scan workflows
