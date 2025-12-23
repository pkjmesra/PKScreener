# PKScreener System Architecture

## Overview

PKScreener is built as a modular, multi-process stock screening application with the following architectural principles:
- **Separation of Concerns**: Clear boundaries between UI, business logic, and data layers
- **Parallel Processing**: Multiprocessing for efficient stock screening
- **Extensibility**: Easy addition of new scanners and patterns
- **Multi-Interface Support**: CLI, Telegram Bot, and programmatic access

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   CLI Interface │  │  Telegram Bot   │  │  GitHub Actions │             │
│  │ pkscreenercli.py│  │pkscreenerbot.py │  │   Workflows     │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        globals.py (Main Orchestrator)                │   │
│  │  • main() - Entry point for all screening operations                │   │
│  │  • runScanners() - Multiprocessing coordinator                      │   │
│  │  • getScannerMenuChoices() - Menu flow management                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌──────────────────┬──────────────┼──────────────┬──────────────────┐     │
│  ▼                  ▼              ▼              ▼                  ▼     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐│
│  │MenuManager │ │MainLogic.py│ │BacktestHdlr│ │ResultsMgr  │ │ConfigMgr  ││
│  │Navigation  │ │ExecuteOpts │ │BacktestUtil│ │ResultsLblr │ │           ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └───────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUSINESS LOGIC LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     StockScreener.screenStocks()                     │   │
│  │  • Orchestrates the screening process per stock                     │   │
│  │  • Manages parallel execution context                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┼─────────────────────────────────┐     │
│  ▼                                 ▼                                 ▼     │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐     │
│  │ScreeningStatistics │ │  CandlePatterns    │ │     Pktalib        │     │
│  │• 47+ validators    │ │• Pattern detection │ │• TA-Lib wrapper    │     │
│  │• Technical calcs   │ │• Candlestick types │ │• EMA, SMA, RSI...  │     │
│  └────────────────────┘ └────────────────────┘ └────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐      │
│  │     Fetcher.py     │ │   DataLoader.py    │ │  AssetsManager.py  │      │
│  │• Yahoo Finance API │ │• Local caching     │ │• GitHub data sync  │      │
│  │• NSE data sources  │ │• Pickle storage    │ │• Index constituents│      │
│  └────────────────────┘ └────────────────────┘ └────────────────────┘      │
│                                    │                                        │
│  ┌─────────────────────────────────┼─────────────────────────────────┐     │
│  ▼                                 ▼                                 ▼     │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                      External Data Sources                          │    │
│  │  • Yahoo Finance  • NSE India  • Morning Star  • GitHub Actions    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Entry Points

#### `pkscreenercli.py`
The CLI entry point that handles:
- Argument parsing (`ArgumentParser`)
- Output control setup (`OutputController`)
- Logging configuration (`LoggerSetup`)
- Dependency checking (`DependencyChecker`)
- Application lifecycle (`ApplicationRunner`)

```python
# Execution flow
def pkscreenercli():
    args = ArgumentParser().parse_args()
    LoggerSetup.setup_logging(args)
    OutputController.setup_output_controller(args)
    runApplicationForScreening()  # Main loop
```

#### `pkscreenerbot.py`
Telegram bot interface using `python-telegram-bot`:
- Command handlers for user interactions
- Inline keyboard menus
- Scan result notifications
- Alert subscriptions

---

### 2. Core Orchestration (globals.py)

The `globals.py` module is the heart of the application, containing:

#### Key Functions

| Function | Purpose |
|----------|---------|
| `main(args)` | Main entry point, orchestrates entire workflow |
| `getScannerMenuChoices()` | Handles menu navigation and option selection |
| `runScanners()` | Multiprocessing coordinator for stock screening |
| `printNotifySaveScreenedResults()` | Result display and notification |
| `finishScreening()` | Cleanup and result persistence |

#### Global State Variables
```python
# Key global variables managed in globals.py
configManager = ConfigManager.tools()    # Configuration
selectedChoice = {}                       # Current menu selections
userPassedArgs = None                    # CLI arguments
keyboardInterruptEvent = None            # Interrupt handling
stockDictPrimary = {}                    # Loaded stock data
```

---

### 3. Menu System

#### MenuOptions.py
Contains all menu definitions as dictionaries:

```python
# Menu hierarchy
level0MenuDict = {           # Main menu (X, P, C, D, etc.)
level1_X_MenuDict = {        # Index selection (0-15, W, S, etc.)
level2_X_MenuDict = {        # Scan options (0-47)
level3_X_Reversal_MenuDict   # Sub-options for reversals
level3_X_ChartPattern_MenuDict  # Sub-options for patterns
# ... etc.
```

#### MenuManager.py
Handles menu rendering and navigation:
- `menus` class - Menu container
- `renderForMenu()` - Display menu options
- `find()` - Locate menu by key

---

### 4. Screening Engine

#### StockScreener.py
Main screening orchestrator:

```python
class StockScreener:
    def screenStocks(self, ...):
        """
        Process a single stock through the screening pipeline.
        
        1. Fetch/validate stock data
        2. Apply pre-filters (volume, price range)
        3. Execute selected screening criteria
        4. Build result dictionaries
        5. Return results tuple
        """
```

#### ScreeningStatistics.py
Contains 47+ validation methods:

| Execute Option | Method | Description |
|----------------|--------|-------------|
| 0 | `validateFullScreen` | Technical overview |
| 1 | `validateBreakout` | Breakout detection |
| 2 | `validateBreakdown` | Breakdown detection |
| 3 | `validateConsolidation` | Range consolidation |
| 4 | `validateLowestVolume` | Volume drying up |
| 5 | `validateRSI` | RSI screening |
| 6 | `validateReversal` | Reversal patterns |
| 7 | `validateChartPattern` | Chart patterns |
| ... | ... | ... |

---

### 5. Multiprocessing Model

```
┌───────────────────────────────────────────────────────────────┐
│                     Main Process                               │
│  globals.py::runScanners()                                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Pool = multiprocessing.Pool(processes=cpu_count)       │  │
│  │                                                          │  │
│  │  results = pool.imap_unordered(                         │  │
│  │      StockScreener.screenStocks,                        │  │
│  │      [(stock1, params), (stock2, params), ...]          │  │
│  │  )                                                       │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Worker 1       │ │  Worker 2       │ │  Worker N       │
│  screenStocks() │ │  screenStocks() │ │  screenStocks() │
│  - RELIANCE     │ │  - TCS          │ │  - INFY         │
│  - HDFC         │ │  - WIPRO        │ │  - ...          │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┴───────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  Result Aggregation                            │
│  processResults() → lstscreen, lstsave → DataFrame            │
└───────────────────────────────────────────────────────────────┘
```

---

### 6. Data Flow

#### Stock Data Loading
```python
# Data sources priority (High-Performance Mode)
1. In-Memory Candle Store (PKBrokers) - Real-time during market hours
2. Local pickle files - Cached historical data
3. Remote GitHub pickle files - Fallback for historical data

# Legacy Mode (fallback if PKBrokers unavailable)
1. Local cache (pickle files)
2. GitHub Actions pre-downloaded data
```

#### Cache Structure
```
~/.pkscreener/
├── stock_data_DDMMYY.pkl       # Daily OHLCV data
├── stock_data_intraday.pkl     # Intraday data
├── candle_store.pkl            # In-memory candle store backup
├── ticks.json                  # Real-time tick data
├── indices/                    # Index constituent lists
└── outputs/                    # Scan results
```

---

### 6.1 High-Performance Real-Time Data Architecture

The system includes a high-performance, in-memory candle data system that provides instant access to OHLCV candles across all supported timeframes without database dependency.

#### Supported Timeframes

| Interval | Description | Max Candles Stored |
|----------|-------------|-------------------|
| `1m` | 1 minute | 390 (full trading day) |
| `2m` | 2 minutes | 195 |
| `3m` | 3 minutes | 130 |
| `4m` | 4 minutes | 98 |
| `5m` | 5 minutes | 78 |
| `10m` | 10 minutes | 39 |
| `15m` | 15 minutes | 26 |
| `30m` | 30 minutes | 13 |
| `60m` | 60 minutes (1 hour) | 7 |
| `day` | Daily candles | 365 (1 year) |

#### Real-Time Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ZERODHA KITE WEBSOCKET API                            │
│  Real-time tick data for all NSE/BSE instruments                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ZerodhaWebSocketClient (PKBrokers)                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Manages multiple WebSocket connections (500 instruments each)     │   │
│  │  • Parses binary tick data into structured format                   │   │
│  │  • Puts ticks into multiprocessing queue                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       KiteTokenWatcher (PKBrokers)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Processes tick batches every 5 seconds                           │   │
│  │  • Maintains only latest tick per instrument (deduplication)        │   │
│  │  • Updates InMemoryCandleStore with each batch                      │   │
│  │  • Sends data to JSON writer for persistence                        │   │
│  │  • Optionally sends to database (Turso/SQLite)                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐
│    InMemoryCandleStore          │ │         JSONFileWriter                   │
│    (PKBrokers - Singleton)      │ │  • Writes ticks.json every 5 seconds    │
│  ┌─────────────────────────┐   │ │  • Maintains OHLCV per instrument        │
│  │ • All intervals stored  │   │ └─────────────────────────────────────────┘
│  │ • O(1) access time      │   │
│  │ • Thread-safe (RLock)   │   │
│  │ • Auto-aggregation      │   │
│  │ • Rolling windows       │   │
│  │ • 5-min auto-persist    │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PKDataProvider (PKDevTools)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Unified Data Access Layer with Priority:                           │   │
│  │    1. InMemoryCandleStore (real-time) ◄──── PRIMARY                 │   │
│  │    2. Local pickle files (cached)                                   │   │
│  │    3. Remote GitHub pickle files (fallback)                         │   │
│  │                                                                      │   │
│  │  Features:                                                           │   │
│  │    • Automatic source selection                                     │   │
│  │    • In-memory caching with TTL                                     │   │
│  │    • Statistics tracking                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐
│  nseStockDataFetcher            │ │    screenerStockDataFetcher              │
│     (PKNSETools)                │ │       (PKScreener)                       │
│  ┌─────────────────────────┐   │ │  ┌─────────────────────────────────┐    │
│  │ • fetchStockData()      │   │ │  │ • fetchStockData()              │    │
│  │ • getLatestPrice()      │   │ │  │ • getLatestPrice()              │    │
│  │ • getRealtimeOHLCV()    │   │ │  │ • getRealtimeOHLCV()            │    │
│  │ • isRealtimeAvailable() │   │ │  │ • isRealtimeDataAvailable()     │    │
│  └─────────────────────────┘   │ │  │ • getAllRealtimeData()          │    │
└─────────────────────────────────┘ │  │ • fetchFiveEmaData()            │    │
                                    │  │ • fetchLatestNiftyDaily()       │    │
                                    │  └─────────────────────────────────┘    │
                                    └─────────────────────────────────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PKScreener Scan Engine                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • StockScreener.screenStocks() - Uses real-time data              │   │
│  │  • ScreeningStatistics - Technical analysis on live data           │   │
│  │  • CandlePatterns - Pattern detection on current candles           │   │
│  │  • Multiprocessing pool - Parallel screening                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Benefits:                                                                   │
│    ✓ No database latency for real-time data                                │
│    ✓ Instant access to any timeframe                                       │
│    ✓ No Yahoo Finance dependency (removed)                                 │
│    ✓ No rate limiting issues                                               │
│    ✓ Automatic fallback to cached data                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Component Responsibilities

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `ZerodhaWebSocketClient` | PKBrokers | WebSocket connection management |
| `KiteTokenWatcher` | PKBrokers | Tick processing and distribution |
| `InMemoryCandleStore` | PKBrokers | Real-time candle storage |
| `CandleAggregator` | PKBrokers | Timeframe aggregation |
| `TickProcessor` | PKBrokers | Tick-to-candle bridge |
| `HighPerformanceDataProvider` | PKBrokers | Convenience API |
| `PKDataProvider` | PKDevTools | Unified data access |
| `screenerStockDataFetcher` | PKScreener | Scan data fetching |

#### Performance Characteristics

| Metric | Value |
|--------|-------|
| Access Time | O(1) for any candle |
| Memory Usage | ~100 bytes per candle |
| Memory per Instrument | ~50KB (all intervals) |
| Total Memory (2000 stocks) | ~100MB |
| Persistence Interval | 5 minutes |
| Recovery Time | < 1 second from disk |

---

### 7. Notification System

```
┌─────────────────────────────────────────────────────────────────┐
│                    TelegramNotifier                              │
├─────────────────────────────────────────────────────────────────┤
│  send_quick_scan_result()                                       │
│    │                                                             │
│    ├── Generate HTML table                                      │
│    ├── Create PNG image (optional)                              │
│    ├── send_message() / send_photo() / send_document()         │
│    └── send_media_group() for multiple attachments              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PKDevTools.classes.Telegram                      │
│  • is_token_telegram_configured()                               │
│  • send_message()                                               │
│  • send_photo()                                                 │
│  • send_document()                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8. Configuration Management

#### ConfigManager.py
Handles user preferences stored in `pkscreener.ini`:

```ini
[config]
period = 1y
duration = 1d
daysToLookback = 22
minLTP = 20.0
maxLTP = 50000.0
volumeRatio = 2.5
consolidationPercentage = 10
shuffle = True
cacheEnabled = True
stageTwo = True
# ... many more options
```

#### Key Configuration Classes
- `tools()` - Main configuration manager
- `getConfig()` / `setConfig()` - Read/write config
- `toggleConfig()` - Toggle boolean settings

---

## Extension Points

### Adding New Technical Indicators
1. Add to `Pktalib.py` or use `TA-Lib` directly
2. Create validation method in `ScreeningStatistics.py`
3. Register in `StockScreener.py` execute option switch

### Adding New Data Sources
1. Implement fetcher in `Fetcher.py` or new module
2. Integrate with `DataLoader.py` caching
3. Update `AssetsManager.py` if needed

### Adding New Notification Channels
1. Create handler class similar to `TelegramNotifier.py`
2. Integrate with `globals.py::sendMessageToTelegramChannel()`
3. Add configuration options

---

## Performance Considerations

1. **Caching**: Enable `cacheEnabled` in config to avoid re-fetching
2. **Parallel Processing**: Uses all CPU cores by default
3. **Data Filtering**: Apply volume/price filters early to reduce processing
4. **Piped Scanners**: Filter progressively to minimize stock count

---

## See Also
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Getting started
- [SCAN_WORKFLOWS.md](SCAN_WORKFLOWS.md) - Detailed scan workflows
