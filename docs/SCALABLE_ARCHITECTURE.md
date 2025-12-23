# Scalable Architecture Design

## Overview

This document describes a scalable architecture for the PKScreener ecosystem that operates entirely within GitHub Actions, using Telegram for orchestration signals and GitHub as the data layer.

## Current Architecture Problems

| Problem | Impact | Current Workaround |
|---------|--------|-------------------|
| Telegram as data bus | Slow, rate-limited, 50MB file limit | Split files, polling |
| No persistent data layer | Each workflow downloads full data | Cache in artifacts |
| Bot-to-bot communication fragile | Depends on Telegram reliability | Retry logic |
| Large file transfers | 10-50MB ticks.json | Zip compression |
| No parallel data access | Workflows queue for data | Sequential runs |
| High GitHub minutes usage | Long-running data jobs | Manual optimization |

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                                  │
│                        (Telegram Bots - Signals Only)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  PKScreenerBot  │  │   PKTickBot     │  │   User CLI      │             │
│  │  (Commands)     │  │  (Tick Status)  │  │  (Local Runs)   │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                     │                       │
│           │    CONTROL SIGNALS ONLY (no data)       │                       │
│           └────────────────────┼─────────────────────┘                       │
└────────────────────────────────┼─────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GITHUB ACTIONS LAYER                                │
│                       (Compute - Ephemeral Workers)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Workflow: Data Collector                           │  │
│  │  • Runs during market hours (9:15 AM - 3:30 PM IST)                  │  │
│  │  • Connects to Zerodha WebSocket                                     │  │
│  │  • Aggregates ticks into candles (InMemoryCandleStore)               │  │
│  │  • Publishes to GitHub Data Repository every 5 minutes               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Workflow: Scan Workers (Parallel)                  │  │
│  │  • Triggered by schedule or user command                             │  │
│  │  • Pulls latest data from GitHub Data Repository                     │  │
│  │  • Runs scans using PKScreener                                       │  │
│  │  • Posts results to Telegram                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GITHUB DATA REPOSITORY                                │
│                  (Persistent Storage - Free & Fast)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Repository: pkjmesra/PKScreener-Data (or actions-data-download branch)     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  /data/                                                              │   │
│  │  ├── candles/                                                        │   │
│  │  │   ├── 2024-01-15/                                                │   │
│  │  │   │   ├── candles_0915.json.gz    (9:15 AM snapshot)            │   │
│  │  │   │   ├── candles_0920.json.gz    (9:20 AM snapshot)            │   │
│  │  │   │   ├── candles_0925.json.gz    (9:25 AM incremental)         │   │
│  │  │   │   └── ...                                                    │   │
│  │  │   └── latest.json.gz              (symlink to most recent)       │   │
│  │  │                                                                   │   │
│  │  ├── ticks/                                                          │   │
│  │  │   └── ticks_latest.json.gz        (current day's OHLCV summary) │   │
│  │  │                                                                   │   │
│  │  └── metadata.json                   (last update time, version)    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Access: Raw GitHub URLs (no API rate limits for raw content)               │
│  Example: https://raw.githubusercontent.com/.../data/candles/latest.json.gz│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Broadcast Pattern (Push) Instead of Request-Response (Pull)

**Before (Request-Response):**
```
Scanner Workflow → Request /ticks → PKTickBot → Send File → Scanner Workflow
                   (waits 30-60s)        (blocked)
```

**After (Broadcast/Push):**
```
Data Collector → Push to GitHub → (available immediately)
                    ↓
Scanner Workflow 1 → Pull from GitHub (parallel)
Scanner Workflow 2 → Pull from GitHub (parallel)
Scanner Workflow N → Pull from GitHub (parallel)
```

### 2. Incremental Updates

Instead of sending full 50MB files, send only changed data:

```json
// metadata.json
{
  "last_full_snapshot": "2024-01-15T09:15:00Z",
  "last_incremental": "2024-01-15T14:25:00Z",
  "incremental_files": [
    "candles_0920.json.gz",
    "candles_0925.json.gz",
    "candles_0930.json.gz"
  ],
  "version": "1.0.0"
}
```

### 3. Telegram for Signals Only

```
┌─────────────────────────────────────────────────────────────────┐
│ User sends: /scan X:12:7:4                                       │
│                                                                   │
│ PKScreenerBot responds:                                          │
│   "🚀 Scan queued! Workflow triggered."                         │
│   (triggers GitHub workflow via API)                             │
│                                                                   │
│ Workflow completes → Posts results to Telegram                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Layered Data Access

```python
class ScalableDataProvider:
    """
    Data access priority:
    1. Local cache (if fresh < 5 min)
    2. GitHub raw content (latest.json.gz)
    3. GitHub API (if raw fails)
    4. Telegram fallback (last resort)
    """
    
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download"
    
    def get_candle_data(self):
        # Try local cache first
        if self._is_cache_fresh():
            return self._load_from_cache()
        
        # Try GitHub raw content (fastest, no rate limits)
        data = self._fetch_from_github_raw()
        if data:
            self._update_cache(data)
            return data
        
        # Fallback to Telegram (last resort)
        return self._fetch_from_telegram()
```

## Implementation Components

### Component 1: Data Publisher Workflow

```yaml
# .github/workflows/w-data-publisher.yml
name: Data Publisher

on:
  schedule:
    # Run every 5 minutes during market hours (IST: 9:15-15:30)
    - cron: '*/5 3-10 * * 1-5'  # UTC times
  workflow_dispatch:

jobs:
  publish_data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: actions-data-download
          
      - name: Setup Python
        uses: actions/setup-python@v5
        
      - name: Collect and Publish Data
        run: |
          python scripts/collect_and_publish.py
        env:
          KTOKEN: ${{ secrets.KTOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Commit Data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "actions@github.com"
          git add data/
          git commit -m "Data update $(date -u +%Y-%m-%dT%H:%M:%SZ)" || true
          git push
```

### Component 2: Scalable Data Fetcher

```python
# PKDevTools/classes/PKScalableDataFetcher.py

import gzip
import json
import os
import time
from typing import Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError

class PKScalableDataFetcher:
    """
    Scalable data fetcher that uses GitHub as primary data source.
    Eliminates Telegram dependency for data transfer.
    """
    
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com/pkjmesra/PKScreener/actions-data-download/data"
    CACHE_TTL_SECONDS = 300  # 5 minutes
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.expanduser("~"), ".pkscreener", "cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        self._metadata_cache = None
        self._metadata_fetch_time = 0
    
    def get_latest_candles(self) -> Optional[Dict[str, Any]]:
        """Get latest candle data from the most efficient source."""
        
        # 1. Check local cache
        cached = self._get_from_cache("candles_latest.json")
        if cached and self._is_fresh(cached.get("_cache_time", 0)):
            return cached
        
        # 2. Fetch from GitHub (primary source)
        data = self._fetch_from_github("candles/latest.json.gz")
        if data:
            data["_cache_time"] = time.time()
            self._save_to_cache("candles_latest.json", data)
            return data
        
        # 3. Return stale cache if available
        if cached:
            return cached
        
        return None
    
    def get_ticks_summary(self) -> Optional[Dict[str, Any]]:
        """Get current day's OHLCV summary for all instruments."""
        return self._fetch_from_github("ticks/ticks_latest.json.gz")
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get data repository metadata."""
        if self._metadata_cache and self._is_fresh(self._metadata_fetch_time):
            return self._metadata_cache
        
        self._metadata_cache = self._fetch_from_github("metadata.json", compressed=False)
        self._metadata_fetch_time = time.time()
        return self._metadata_cache
    
    def _fetch_from_github(
        self, 
        path: str, 
        compressed: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Fetch data from GitHub raw content."""
        url = f"{self.GITHUB_RAW_BASE}/{path}"
        
        try:
            request = Request(url, headers={"User-Agent": "PKScreener/1.0"})
            with urlopen(request, timeout=30) as response:
                content = response.read()
                
                if compressed and path.endswith(".gz"):
                    content = gzip.decompress(content)
                
                return json.loads(content.decode("utf-8"))
                
        except (URLError, json.JSONDecodeError) as e:
            print(f"GitHub fetch failed for {path}: {e}")
            return None
    
    def _is_fresh(self, cache_time: float) -> bool:
        """Check if cached data is still fresh."""
        return (time.time() - cache_time) < self.CACHE_TTL_SECONDS
    
    def _get_from_cache(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load data from local cache."""
        cache_path = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        return None
    
    def _save_to_cache(self, filename: str, data: Dict[str, Any]):
        """Save data to local cache."""
        cache_path = os.path.join(self.cache_dir, filename)
        
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f)
        except IOError as e:
            print(f"Cache save failed: {e}")
```

### Component 3: Data Publisher Script

```python
# scripts/collect_and_publish.py

import gzip
import json
import os
from datetime import datetime

def collect_candle_data():
    """Collect candle data from InMemoryCandleStore."""
    try:
        from pkbrokers.kite import get_candle_store
        
        store = get_candle_store()
        
        # Export to JSON format
        all_data = {}
        
        for token, instrument in store.instruments.items():
            symbol = store.instrument_symbols.get(token, str(token))
            all_data[symbol] = {
                "token": token,
                "candles": {}
            }
            
            # Export each interval
            for interval in ["1m", "5m", "15m", "60m", "day"]:
                candles = store.get_candles(
                    instrument_token=token,
                    interval=interval,
                    count=100
                )
                if candles:
                    all_data[symbol]["candles"][interval] = candles
        
        return all_data
        
    except ImportError:
        return None

def publish_to_github(data, output_dir="data"):
    """Publish data to GitHub repository structure."""
    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H%M")
    
    # Create directory structure
    candles_dir = os.path.join(output_dir, "candles", today)
    os.makedirs(candles_dir, exist_ok=True)
    
    # Save timestamped snapshot
    snapshot_path = os.path.join(candles_dir, f"candles_{current_time}.json.gz")
    with gzip.open(snapshot_path, "wt", encoding="utf-8") as f:
        json.dump(data, f)
    
    # Update latest symlink
    latest_path = os.path.join(output_dir, "candles", "latest.json.gz")
    with gzip.open(latest_path, "wt", encoding="utf-8") as f:
        json.dump(data, f)
    
    # Update metadata
    metadata = {
        "last_update": datetime.utcnow().isoformat() + "Z",
        "snapshot_count": len(os.listdir(candles_dir)),
        "instrument_count": len(data),
        "version": "2.0.0"
    }
    
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Published {len(data)} instruments to {snapshot_path}")

if __name__ == "__main__":
    data = collect_candle_data()
    if data:
        publish_to_github(data)
    else:
        print("No data to publish")
```

## Workflow Optimization

### Before: Sequential Bot Communication
```
Workflow Start → Wait for PKTickBot → Download File → Process → Complete
    (0s)              (30-60s)           (10-30s)      (60s)     (2-3 min)
```

### After: Parallel GitHub Access
```
Workflow Start → Fetch from GitHub → Process → Complete
    (0s)              (2-5s)          (60s)     (1 min)
```

### GitHub Minutes Savings

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| Single scan | 3 min | 1 min | 66% |
| 10 parallel scans | 30 min | 10 min | 66% |
| Daily scheduled (50 scans) | 150 min | 50 min | 100 min/day |

## Telegram Bot Changes

### PKScreenerBot (Minimal Changes)

```python
# Only change: Add workflow trigger instead of data fetch

async def handle_scan_command(update, context):
    user_id = update.effective_user.id
    scan_params = parse_scan_command(update.message.text)
    
    # Trigger GitHub workflow (no data transfer via Telegram)
    success = trigger_github_workflow(
        workflow="w8-workflow-alert-scan_generic.yml",
        params={
            "params": scan_params,
            "user": str(user_id)
        }
    )
    
    if success:
        await update.message.reply_text(
            f"🚀 Scan queued!\n"
            f"Parameters: {scan_params}\n"
            f"Results will be posted here when ready."
        )
    else:
        await update.message.reply_text("❌ Failed to queue scan. Try again.")
```

### PKTickBot (Simplified)

```python
# PKTickBot now only needs to:
# 1. Collect ticks and aggregate to candles
# 2. Push to GitHub (not Telegram)
# 3. Report status via Telegram

class PKTickBot:
    async def status(self, update, context):
        """Report data collection status."""
        store = get_candle_store()
        stats = store.get_stats()
        
        await update.message.reply_text(
            f"📊 Data Collection Status\n"
            f"Instruments: {stats['instrument_count']}\n"
            f"Ticks Processed: {stats['ticks_processed']}\n"
            f"Last Update: {stats['last_tick_time']}\n"
            f"Data available on GitHub ✓"
        )
    
    # Remove: send_ticks, send_db (no longer needed via Telegram)
```

## Migration Path

### Phase 1: Add GitHub Publishing (Week 1)
- Add data publisher workflow
- Keep existing Telegram data transfer as fallback
- Test GitHub raw content access

### Phase 2: Update Data Consumers (Week 2)
- Add PKScalableDataFetcher to PKDevTools
- Update screenerStockDataFetcher to use new fetcher
- Test parallel workflow execution

### Phase 3: Simplify Telegram Bots (Week 3)
- Remove data transfer commands from PKTickBot
- Keep status and control commands
- Remove PKTickBotConsumer (no longer needed)

### Phase 4: Optimization (Week 4)
- Implement incremental updates
- Add compression optimization
- Monitor and tune cache TTL

## Fallback Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Access Priority                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Local Cache (< 5 min old)     │ Instant           │ Primary  │
│ 2. GitHub Raw Content            │ 2-5 seconds       │ Primary  │
│ 3. GitHub API                    │ 5-10 seconds      │ Fallback │
│ 4. InMemoryCandleStore (if live) │ Instant (in-proc) │ Fallback │
│ 5. Telegram Bot (/ticks)         │ 30-60 seconds     │ Last     │
└─────────────────────────────────────────────────────────────────┘
```

## Monitoring & Alerts

```python
# Add to metadata.json for monitoring
{
    "health": {
        "last_successful_publish": "2024-01-15T14:25:00Z",
        "consecutive_failures": 0,
        "data_freshness_seconds": 300
    },
    "alerts": {
        "stale_data_threshold_minutes": 15,
        "alert_channel": "@pktickbot_alerts"
    }
}
```


## 24x7 Data Availability

The system is designed to provide stock data availability around the clock, enabling users to trigger scans from the Telegram bot at any time.

### Architecture Overview

```
+---------------------------------------------------------------------+
|                      24x7 DATA AVAILABILITY                          |
+---------------------------------------------------------------------+
|                                                                      |
|  MARKET HOURS (9:15 AM - 3:30 PM IST, Mon-Fri)                      |
|  +-- w-data-publisher.yml runs every 5 minutes                      |
|  +-- Uses real-time ticks from PKTickBot/InMemoryCandleStore        |
|  +-- Aggregates into 1m, 2m, 3m, 4m, 5m, 10m, 15m, 30m, 60m candles |
|  +-- Publishes fresh data to GitHub (results/Data/)                 |
|                                                                      |
|  AFTER MARKET HOURS                                                  |
|  +-- w9-workflow-download-data.yml runs at 3:28 PM IST             |
|  +-- Downloads 52-week historical data for all stocks              |
|  +-- Saves pickle files to actions-data-download/                   |
|  +-- w-data-publisher.yml runs every 2 hours, uses pickle data     |
|                                                                      |
|  WEEKENDS & HOLIDAYS                                                 |
|  +-- Data publisher continues running every 2 hours                 |
|  +-- Uses last available pickle/cached data                         |
|  +-- Ensures data is always accessible via GitHub                   |
|                                                                      |
|  USER TRIGGERS SCAN (anytime, 24x7)                                 |
|  +-- Telegram bot -> GitHub workflow dispatch                        |
|  +-- Scan workflow fetches from GitHub raw content                  |
|  +-- Data always available (fresh during market, cached otherwise)  |
|  +-- 2-5 second latency vs 30-60 seconds via Telegram              |
|                                                                      |
+---------------------------------------------------------------------+
```

### Data Source Priority (24x7)

The system uses a layered approach to ensure data is always available:

| Priority | Source | When Used | Latency |
|----------|--------|-----------|---------|
| 1 | Real-time ticks (InMemoryCandleStore) | Market hours, live tick collection | Instant |
| 2 | GitHub ticks.json | Fresh data published during market | 2-5s |
| 3 | Pickle files (w9 workflow) | After market, weekends, holidays | 2-5s |
| 4 | Local disk cache | Network issues, fallback | Instant |
| 5 | Stale cache data | All sources fail | Instant |

### Workflow Schedule

```yaml
# w-data-publisher.yml schedule
on:
  schedule:
    # During market hours: every 5 minutes
    - cron: '*/5 3-10 * * 1-5'  # UTC (IST 9:00-16:00)
    # Outside market hours: every 2 hours for 24x7 availability
    - cron: '30 */2 * * *'
```

### Data Freshness Guarantees

| Time Period | Data Type | Max Age | Update Frequency |
|-------------|-----------|---------|------------------|
| Market hours | Real-time ticks | 5 min | Every 5 min |
| After market (same day) | End-of-day OHLCV | 2 hours | Every 2 hours |
| Weekends/Holidays | Last trading day | 2 hours | Every 2 hours |
| Network failure | Cached data | 24 hours | On recovery |

### Integration with Existing Workflows

The 24x7 data availability integrates with existing PKScreener workflows:

1. **w7-workflow-prod-scans-trigger.yml** - Scheduled production scans
   - Now uses GitHub data layer instead of Telegram
   - Can run anytime with available data

2. **w8-workflow-alert-scan_generic.yml** - User-triggered scans
   - Fetches data from GitHub raw content
   - Works 24x7 with appropriate data (fresh or cached)

3. **w9-workflow-download-data.yml** - After-market data download
   - Downloads 52-week historical data
   - Pickle files used by data publisher for non-market hours

### User Experience

Users can trigger scans from Telegram at any time:

```
+------------------------------------------------------------------+
| User: /scan X:12:7:4 (at 11:00 PM IST)                            |
|                                                                    |
| System:                                                            |
| 1. Bot receives command -> Triggers GitHub workflow               |
| 2. Workflow starts -> Fetches data from GitHub                    |
| 3. Data source: End-of-day OHLCV from last trading session        |
| 4. Scan runs with available data                                   |
| 5. Results posted to Telegram                                      |
|                                                                    |
| Response: "Scan complete! Using data from 2024-01-15 EOD"         |
+------------------------------------------------------------------+
```

### Metadata Tracking

The data publisher maintains metadata for transparency:

```json
{
  "last_update": "2024-01-15T22:30:00Z",
  "last_update_ist": "2024-01-16T04:00:00+05:30",
  "is_market_hours": false,
  "data_source": "pickle",
  "instrument_count": 2500,
  "version": "2.0.0",
  "publisher": "w-data-publisher.yml",
  "availability": "24x7",
  "health": {
    "status": "healthy"
  }
}
```

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Data Transfer | Telegram (slow, limited) | GitHub (fast, unlimited) |
| Parallelism | 1 workflow at a time | Unlimited parallel |
| Latency | 30-60 seconds | 2-5 seconds |
| Reliability | Depends on Telegram | Git-backed durability |
| Cost | High GitHub minutes | 66% reduction |
| Complexity | Bot-to-bot messaging | Simple HTTP GET |
| **Availability** | **Market hours only** | **24x7** |
| **After-hours scans** | **Not supported** | **Full support with EOD data** |
