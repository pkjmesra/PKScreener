# PKScreener Documentation

Welcome to the PKScreener developer documentation. This documentation is designed to help contributors understand the codebase and make meaningful contributions.

## Quick Links

| Document | Description |
|----------|-------------|
| [Developer Guide](DEVELOPER_GUIDE.md) | Getting started, project structure, development workflow |
| [Architecture](ARCHITECTURE.md) | System architecture, component details, data flow |
| [Scalable Architecture](SCALABLE_ARCHITECTURE.md) | GitHub-based data layer, **24x7 data availability**, workflow orchestration |
| [High-Performance Data](HIGH_PERFORMANCE_DATA.md) | Real-time data system, in-memory candle store |
| [Scan Workflows](SCAN_WORKFLOWS.md) | Detailed scan category workflows, option formats |
| [API Reference](API_REFERENCE.md) | Key classes, methods, and function signatures |
| [Testing Guide](TESTING.md) | Writing and running tests, mocking guidelines |
| [Contributing](https://github.com/pkjmesra/PKScreener/blob/main/CONTRIBUTING.md) | Contribution guidelines, code of conduct |

## Overview

PKScreener is a stock screening and analysis tool that provides:

- **47+ Technical Scanners**: From breakouts to chart patterns
- **Multi-Index Support**: NSE, NASDAQ, sectoral indices
- **Backtesting**: Historical performance analysis
- **Piped Scanners**: Chain multiple filters together
- **Telegram Bot**: Automated alerts and commands
- **CLI Interface**: Powerful command-line access
- **24x7 Data Availability**: Run scans anytime - market hours with real-time data, after-hours with end-of-day data

## Architecture at a Glance

\`\`\`
+-------------------------------------------------------------+
|                    User Interfaces                          |
|     CLI (pkscreenercli.py) | Bot (pkscreenerbot.py)        |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|              GitHub Actions Workflow Layer                   |
|   w7-workflow-prod-scans-trigger.yml (Scheduler)            |
|   w8-workflow-alert-scan_generic.yml (Scan Runner)          |
|   w-data-publisher.yml (Data Publisher - 24x7)              |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                  Core Orchestration                          |
|                     globals.py                               |
|   main() -> getScannerMenuChoices() -> runScanners()          |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                   Screening Engine                           |
|   StockScreener -> ScreeningStatistics -> Pktalib            |
|              (47+ validation methods)                        |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                High-Performance Data Layer                   |
|  +-------------------------------------------------------+ |
|  | Priority 1: PKBrokers InMemoryCandleStore (Real-time) | |
|  | Priority 2: PKScalableDataFetcher (GitHub Raw)        | |
|  | Priority 3: PKDataProvider (Local Cache)              | |
|  | Priority 4: Remote Pickle Files (Fallback)            | |
|  +-------------------------------------------------------+ |
|  Intervals: 1m, 2m, 3m, 4m, 5m, 10m, 15m, 30m, 60m, daily  |
+-------------------------------------------------------------+
\`\`\`

**Data Flow**: 
- Real-time: See [High-Performance Data](HIGH_PERFORMANCE_DATA.md)
- Workflow-based: See [Scalable Architecture](SCALABLE_ARCHITECTURE.md)
- **24x7 Availability**: Data is always available - real-time during market hours, cached EOD data outside market hours

## Key Concepts

### Option String Format
\`\`\`
MenuOption:IndexOption:ExecuteOption:SubOptions

X:12:7:4 = Scanner -> All Nifty -> Chart Patterns -> VCP
\`\`\`

### Piped Scanners
\`\`\`
X:12:9:2.5:>|X:0:31:>|X:0:27:
Volume>2.5x -> High Momentum -> ATR Cross
\`\`\`

## 24x7 Data Availability

PKScreener provides stock data availability around the clock, enabling users to trigger scans from the Telegram bot at any time:

| Time Period | Data Source | Update Frequency |
|-------------|-------------|------------------|
| **Market hours** (9:15 AM - 3:30 PM IST) | Real-time ticks | Every 5 minutes |
| **After market hours** | EOD pickle files | Every 2 hours |
| **Weekends/Holidays** | Cached data | Every 2 hours |

**Key Workflows:**
- \`w-data-publisher.yml\` - Publishes data 24x7 to GitHub
- \`w9-workflow-download-data.yml\` - Downloads 52-week historical data after market close

See [Scalable Architecture](SCALABLE_ARCHITECTURE.md) for detailed implementation.

## 24x7 Data Availability

PKScreener provides stock data availability around the clock, enabling users to trigger scans anytime:

```
┌─────────────────────────────────────────────────────────────────┐
│                   24x7 DATA AVAILABILITY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MARKET HOURS (9:15 AM - 3:30 PM IST)                           │
│  └── Real-time tick data, updated every 5 minutes               │
│                                                                  │
│  AFTER MARKET HOURS                                              │
│  └── End-of-day OHLCV data from last trading session            │
│                                                                  │
│  WEEKENDS & HOLIDAYS                                             │
│  └── Last available trading data, refreshed every 2 hours       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Time Period | Data Source | Update Frequency |
|-------------|-------------|------------------|
| Market hours | Real-time ticks | Every 5 minutes |
| After market | EOD pickle files | Every 2 hours |
| Weekends/Holidays | Cached data | Every 2 hours |

**Key Workflows:**
- `w-data-publisher.yml` - Publishes data 24x7 to GitHub
- `w9-workflow-download-data.yml` - Downloads 52-week historical data after market close
  - Includes fallback: converts `ticks.json.zip` to pickle if database is unavailable

See [Scalable Architecture](SCALABLE_ARCHITECTURE.md) for detailed implementation.

## Getting Started

1. **Read the [Developer Guide](DEVELOPER_GUIDE.md)** for project setup
2. **Understand the [Architecture](ARCHITECTURE.md)** for system design
3. **Explore [Scan Workflows](SCAN_WORKFLOWS.md)** for scanner details
4. **Reference the [API](API_REFERENCE.md)** for implementation details

## Contributing

See [Contributing Guidelines](https://github.com/pkjmesra/PKScreener/blob/main/CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Testing requirements
- Issue reporting

## Support

- **Issues**: [GitHub Issues](https://github.com/pkjmesra/PKScreener/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pkjmesra/PKScreener/discussions)
