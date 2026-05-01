# High-Performance Real-Time Data System

This document describes the high-performance, in-memory candle data system integrated into PKScreener for real-time stock screening.

## Overview

The high-performance data system provides instant access to OHLCV candle data across all supported timeframes without external API rate limits or database latency. It replaces Yahoo Finance as the primary data source during market hours.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Zerodha Kite WebSocket API                           │
│                    (Real-time tick data stream)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────-─┐
│                           PKBrokers Layer                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  ZerodhaWebSocketClient → KiteTokenWatcher → InMemoryCandleStore    │     │
│  │                                                                     │     │
│  │  Features:                                                          │     │
│  │    • Real-time tick aggregation into OHLCV candles                  │     │
│  │    • All intervals: 1m, 2m, 3m, 4m, 5m, 10m, 15m, 30m, 60m, daily   │     │
│  │    • O(1) access time for any candle                                │     │
│  │    • Memory-efficient rolling windows                               │     │
│  │    • Auto-persistence every 5 minutes                               │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────-─┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PKDevTools Layer                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  PKDataProvider - Unified data access with automatic fallback       │    │
│  │                                                                     │    │
│  │  Data Source Priority:                                              │    │
│  │    1. InMemoryCandleStore (real-time) ◄── Primary                   │    │
│  │    2. Local pickle files (cached)                                   │    │
│  │    3. Remote GitHub pickle files (fallback)                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PKScreener Layer                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  screenerStockDataFetcher - Enhanced with real-time support         │    │
│  │                                                                     │    │
│  │  New Methods:                                                       │    │
│  │    • getLatestPrice(symbol)                                         │    │
│  │    • getRealtimeOHLCV(symbol)                                       │    │
│  │    • isRealtimeDataAvailable()                                      │    │
│  │    • getAllRealtimeData()                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Supported Timeframes

| Interval | Description | Candles Stored | Use Case |
|----------|-------------|----------------|----------|
| `1m` | 1 minute | 390 | Ultra-short term, scalping |
| `2m` | 2 minutes | 195 | Short term patterns |
| `3m` | 3 minutes | 130 | Custom analysis |
| `4m` | 4 minutes | 98 | Custom analysis |
| `5m` | 5 minutes | 78 | Intraday trading |
| `10m` | 10 minutes | 39 | Intraday swings |
| `15m` | 15 minutes | 26 | Intraday trends |
| `30m` | 30 minutes | 13 | Position trading |
| `60m` | 60 minutes | 7 | Swing trading |
| `day` | Daily | 365 | Trend following |

## Usage

### Basic Usage in Scans

```python
from pkscreener.classes.Fetcher import screenerStockDataFetcher
from pkscreener.classes import ConfigManager

# Initialize fetcher
config = ConfigManager.tools()
fetcher = screenerStockDataFetcher(config)

# Check if real-time data is available
if fetcher.isRealtimeDataAvailable():
    print("Real-time data mode active!")
    
    # Get latest price
    price = fetcher.getLatestPrice("RELIANCE")
    print(f"RELIANCE price: ₹{price}")
    
    # Get real-time OHLCV
    ohlcv = fetcher.getRealtimeOHLCV("TCS")
    print(f"TCS - O:{ohlcv['open']} H:{ohlcv['high']} L:{ohlcv['low']} C:{ohlcv['close']}")
    
    # Get all market data
    all_data = fetcher.getAllRealtimeData()
    print(f"Tracking {len(all_data)} instruments")
else:
    print("Falling back to cached data")
```

### Fetching Stock Data

```python
# Fetch 5-minute candles
df = fetcher.fetchStockData(
    stockCode="RELIANCE",
    period="1d",
    duration="5m",
    exchangeSuffix=".NS"
)

# Data is automatically sourced from:
# 1. Real-time candle store (if available)
# 2. Local pickle files (if cached)
# 3. Remote GitHub files (fallback)

if df is not None:
    print(f"Got {len(df)} candles")
    print(df.tail())
```

### Direct Access to PKDataProvider

```python
from PKDevTools.classes.PKDataProvider import get_data_provider

provider = get_data_provider()

# Get stock data with automatic source selection
df = provider.get_stock_data("INFY", interval="15m", count=50)

# Get multiple stocks
data = provider.get_multiple_stocks(
    ["RELIANCE", "TCS", "INFY"],
    interval="day",
    count=100
)

# Check statistics
stats = provider.get_stats()
print(f"Real-time hits: {stats['realtime_hits']}")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Pickle hits: {stats['pickle_hits']}")
```

## Benefits

### Removed Dependencies

| Before | After |
|--------|-------|
| Yahoo Finance API | ❌ Removed |
| yfinance rate limits | ❌ No limits |
| External API latency | ❌ In-memory access |
| API downtime issues | ❌ Local fallback |

### Performance Improvements

| Metric | Before (Yahoo) | After (Real-time) |
|--------|----------------|-------------------|
| Data Latency | 500ms - 2s | < 1ms |
| Rate Limits | 2000/hour | None |
| API Failures | Common | N/A |
| Market Hours Data | Delayed | Real-time |
| Multi-timeframe | Multiple API calls | Single store access |

## Data Source Priority

The system automatically selects the best available data source:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Request                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Is Real-time    │
                    │ Available?      │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ Yes                         │ No
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │ InMemoryCandle  │           │ Local Pickle    │
    │ Store           │           │ Files           │
    └────────┬────────┘           └────────┬────────┘
             │                              │
             │ Data Found?                  │ Data Found?
             │                              │
        ┌────┴────┐                   ┌────-┴───┐
        │Yes  │No │                   │Yes  │No │
        ▼     ▼   │                   ▼     ▼   │
    ┌──────┐ │    │               ┌──────┐      │
    │Return│ │    │               │Return│      ▼
    │Data  │ │    │               │Data  │  ┌──────────────┐
    └──────┘ │    │               └──────┘  │Remote GitHub │
             │    │                         │Pickle Files  │
             ▼    ▼                         └──────────────┘
         ┌────────────────────────────────────────────────┐
         │              Fallback Chain                    │
         │  Real-time → Local Pickle → Remote Pickle      │
         └────────────────────────────────────────────────┘
```

## Configuration

### Enabling Real-Time Data

Real-time data requires PKBrokers to be running with active Zerodha WebSocket connection:

```python
# In PKBrokers - Start the tick watcher
from pkbrokers.kite.kiteTokenWatcher import KiteTokenWatcher

watcher = KiteTokenWatcher()
watcher.watch()  # Starts WebSocket connections

# Real-time data is now available in PKScreener
```

### Environment Variables

```bash
# Kite credentials (required for real-time)
export KTOKEN="your_kite_enctoken"
export KUSER="your_kite_user_id"

# Optional: Enable database persistence
export DB_TICKS="1"
```

## Troubleshooting

### No Real-Time Data Available

```python
from pkscreener.classes.Fetcher import screenerStockDataFetcher

fetcher = screenerStockDataFetcher()

if not fetcher.isRealtimeDataAvailable():
    # Check why
    if fetcher._hp_provider is None:
        print("PKBrokers not installed or PKDataProvider not available")
    else:
        stats = fetcher._hp_provider.get_stats()
        print(f"Instruments: {stats.get('instrument_count', 0)}")
        print(f"Last tick: {stats.get('last_tick_time', 'N/A')}")
```

### Data Not Updating

1. Check if KiteTokenWatcher is running
2. Verify WebSocket connections are active
3. Check network connectivity
4. Review PKBrokers logs for errors

### Memory Usage

```python
from PKDevTools.classes.PKDataProvider import get_data_provider

provider = get_data_provider()
stats = provider.get_stats()
print(f"Cache size: {stats['cache_size']}")

# Clear cache if needed
provider.clear_cache()
```


## 24x7 Data Availability

The high-performance data system is designed to work 24x7, ensuring stock data is always available for scans:

| Time Period | Data Source | Description |
|-------------|-------------|-------------|
| **Market Hours** (9:15 AM - 3:30 PM IST) | InMemoryCandleStore | Real-time tick aggregation |
| **After Market** | Pickle Files | EOD data from w9-workflow |
| **Weekends/Holidays** | Cached Data | Last trading session data |

### Data Source Priority (24x7)

```
+-------------------------------------------------------------------+
| Priority 1: InMemoryCandleStore (Real-time)                       |
|    -> Live tick data during market hours                          |
|                                                                   |
| Priority 2: PKScalableDataFetcher (GitHub Raw)                    |
|    -> Pre-published data via w-data-publisher.yml                 |
|                                                                   |
| Priority 3: Local Pickle Cache                                    |
|    -> Downloaded data from previous sessions                      |
|                                                                   |
| Priority 4: Remote GitHub Pickle Files                            |
|    -> 52-week historical data from w9-workflow                    |
+-------------------------------------------------------------------+
```

### How It Works

1. **During Market Hours**: Real-time ticks from Zerodha WebSocket are aggregated into candles
2. **After Market Close**: w9-workflow downloads 52-week data and saves to pickle files
3. **24x7 Publisher**: w-data-publisher.yml runs every 5 min during market, every 2 hours otherwise
4. **Scan Anytime**: Users can trigger scans from Telegram bot at any time with available data

See [Scalable Architecture](SCALABLE_ARCHITECTURE.md) for detailed 24x7 implementation.

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [Scalable Architecture](SCALABLE_ARCHITECTURE.md) - 24x7 data availability, GitHub-based data layer
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [PKBrokers Documentation](https://github.com/pkjmesra/PKBrokers) - PKBrokers high performance candles documentation
