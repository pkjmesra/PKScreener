# PKScreener Developer Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Project Structure](#project-structure)
4. [Core Concepts](#core-concepts)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Debugging](#debugging)

---

## Introduction

PKScreener is a comprehensive stock screening and analysis tool for the Indian (NSE) and US (NASDAQ) markets. It provides technical analysis, pattern recognition, backtesting capabilities, and automated scanning through a CLI and Telegram bot interface.

### Key Features
- **Stock Screening**: 47+ technical screening criteria
- **Chart Pattern Recognition**: VCP, Inside Bar, Confluence, etc.
- **Backtesting**: Historical performance analysis
- **Piped Scanners**: Chain multiple scanners together
- **Telegram Integration**: Bot-based notifications and commands
- **Multi-Index Support**: NSE indices, NASDAQ, sectoral indices

---

## Getting Started

### Prerequisites
```bash
# Python 3.11+ recommended
python --version

# Install dependencies
pip install -r requirements.txt

# Optional: TA-Lib for advanced indicators
# Follow instructions at: https://github.com/ta-lib/ta-lib-python
```

### Running the Application
```bash
# CLI Mode
python pkscreener/pkscreenercli.py

# With specific options
python pkscreener/pkscreenercli.py -o "X:12:1"  # Run scanner X, index 12, option 1

# Telegram Bot Mode
python pkscreener/pkscreenerbot.py
```

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `RUNNER` | Set when running in CI/CD | Not set |
| `PKDevTools_Default_Log_Level` | Logging level (10=DEBUG, 20=INFO) | 30 |
| `CHAT_ID` | Telegram chat ID for notifications | Required for bot |
| `TOKEN` | Telegram bot token | Required for bot |

---

## Project Structure

```
PKScreener-main/
├── pkscreener/
│   ├── __init__.py              # Package initialization, version info
│   ├── globals.py               # Global state, main() function, core workflow
│   ├── pkscreenercli.py         # CLI entry point
│   ├── pkscreenerbot.py         # Telegram bot entry point
│   ├── MainApplication.py       # Application bootstrapping
│   │
│   └── classes/
│       ├── MenuOptions.py       # Menu definitions and scan options
│       ├── MenuManager.py       # Menu rendering and navigation
│       ├── MenuNavigation.py    # User input handling for menus
│       ├── MainLogic.py         # Core business logic handlers
│       │
│       ├── StockScreener.py     # Main screening orchestrator
│       ├── ScreeningStatistics.py # Technical analysis calculations
│       ├── Pktalib.py           # Technical indicators wrapper
│       ├── CandlePatterns.py    # Candlestick pattern detection
│       │
│       ├── Fetcher.py           # Stock data fetching
│       ├── DataLoader.py        # Data loading and caching
│       ├── ConfigManager.py     # User configuration management
│       │
│       ├── BacktestHandler.py   # Backtesting workflow
│       ├── Backtest.py          # Backtest calculations
│       ├── BacktestUtils.py     # Backtest utilities
│       │
│       ├── ResultsManager.py    # Result formatting and display
│       ├── ResultsLabeler.py    # Result labeling and categorization
│       │
│       ├── TelegramNotifier.py  # Telegram messaging
│       ├── bot/
│       │   └── BotHandlers.py   # Telegram bot command handlers
│       │
│       └── Exchange/            # Exchange-specific implementations
│           └── Index/
│               └── Scanners/
│                   └── Scanner.py
│
├── test/                        # Unit and integration tests
├── docs/                        # Documentation
└── screenshots/                 # UI screenshots
```

---

## Core Concepts

### 1. Menu System
PKScreener uses a hierarchical menu system defined in `MenuOptions.py`:

```
Level 0 (Main Menu)
├── X: Scanners
├── P: Piped Scanners
├── C: Intraday Analysis
├── D: Data Downloads
├── F: Find Stock in Scanners
├── M: Monitor Intraday
├── T: Time Period Settings
├── E: Edit Configuration
└── ...

Level 1 (Index Selection)
├── 0: Custom stock list
├── 1-15: Nifty indices
├── W: Watchlist
├── S: Sectoral indices
└── ...

Level 2 (Scan Criteria) - 47+ options
├── 0: Full Screening
├── 1: Breakouts/Breakdowns
├── 7: Chart Patterns
├── 21: MF/FII Popular Stocks
└── ...
```

### 2. Options String Format
Scan options are encoded as colon-separated strings:

```
Format: MenuOption:IndexOption:ExecuteOption:SubOptions

Examples:
- X:12:1     → Scanner(X), All Nifty(12), Breakouts(1)
- X:1:7:4    → Scanner(X), Nifty50(1), Chart Patterns(7), VCP(4)
- B:12:1     → Backtest(B), All Nifty(12), Breakouts(1)
- P:1:3      → Piped(P), Predefined(1), Scan#3
```

### 3. Piped Scanners
Chain multiple scanners using the `>|` operator:

```
X:12:9:2.5:>|X:0:31:>|X:0:27:
│           │        │
│           │        └── ATR Cross filter
│           └── High Momentum filter
└── Volume > 2.5x average
```

### 4. Data Flow

```
┌─────────────────┐    ┌──────────────┐    ┌────────────────────┐
│   User Input    │───▶│  MenuSystem  │───▶│  getScannerMenu    │
│  (CLI/Bot/API)  │    │              │    │  Choices()         │
└─────────────────┘    └──────────────┘    └────────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌──────────────┐    ┌────────────────────┐
│  Display        │◀───│  Results     │◀───│  runScanners()     │
│  Results        │    │  Manager     │    │                    │
└─────────────────┘    └──────────────┘    └────────────────────┘
                                                      │
                              ┌────────────────────────┴──────────────┐
                              ▼                                       ▼
                   ┌────────────────────┐              ┌────────────────────┐
                   │  Multiprocessing   │              │   StockScreener    │
                   │  Pool              │              │   .screenStocks()  │
                   └────────────────────┘              └────────────────────┘
                                                                 │
                                                                 ▼
                                                      ┌────────────────────┐
                                                      │ ScreeningStatistics│
                                                      │ (Technical Calcs)  │
                                                      └────────────────────┘
```

---

## Development Workflow

### Adding a New Scanner

1. **Define Menu Option** in `MenuOptions.py`:
```python
level2_X_MenuDict = {
    # ... existing options ...
    "48": "Your New Scanner Description",
}
MAX_SUPPORTED_MENU_OPTION = 48  # Update this
```

2. **Implement Logic** in `ScreeningStatistics.py`:
```python
def validateYourNewScanner(self, df, screenDict, saveDict):
    """
    Implement your screening logic here.
    
    Args:
        df: pandas DataFrame with OHLCV data
        screenDict: Dictionary for display results
        saveDict: Dictionary for saved results
    
    Returns:
        bool: True if stock passes the criteria
    """
    # Your implementation
    close = df['Close'].iloc[-1]
    sma_50 = df['Close'].rolling(50).mean().iloc[-1]
    
    if close > sma_50:
        screenDict['Signal'] = 'Bullish'
        saveDict['Signal'] = 'Bullish'
        return True
    return False
```

3. **Add to Screening Flow** in `StockScreener.py`:
```python
# In screenStocks() method, around line 200+
elif executeOption == 48:
    isValid = self.screeningStatistics.validateYourNewScanner(
        df, screenDict, saveDict
    )
```

4. **Add Tests** in `test/ScreeningStatistics_test.py`:
```python
def test_validateYourNewScanner_bullish(self):
    df = create_sample_df(close_trend='up')
    result = self.stats.validateYourNewScanner(df, {}, {})
    assert result == True
```

### Adding a New Chart Pattern

1. **Define Sub-Menu** in `MenuOptions.py`:
```python
level3_X_ChartPattern_MenuDict = {
    # ... existing patterns ...
    "10": "Your New Pattern",
}
```

2. **Implement in `CandlePatterns.py`** or `ScreeningStatistics.py`:
```python
def findYourNewPattern(self, df):
    """Detect your pattern in the data."""
    # Implementation
    return pattern_found, pattern_details
```

---

## Testing

### Running Tests
```bash
# Run all tests
pytest test/ -v

# Run specific test file
pytest test/ScreeningStatistics_test.py -v

# Run with coverage
coverage run -m pytest test/
coverage report --include="pkscreener/**"

# Run with timeout (for long-running tests)
pytest test/ --timeout=30
```

### Test Structure
```python
# test/YourModule_test.py
import pytest
from unittest.mock import MagicMock, patch

class TestYourFeature:
    def setup_method(self):
        """Setup before each test."""
        self.mock_config = MagicMock()
    
    def test_feature_positive_case(self):
        """Test description."""
        # Arrange
        input_data = create_test_data()
        
        # Act
        result = your_function(input_data)
        
        # Assert
        assert result == expected_value
    
    @patch('pkscreener.classes.Fetcher.fetchData')
    def test_with_mocking(self, mock_fetch):
        """Test with external dependency mocked."""
        mock_fetch.return_value = mock_data
        # ... test implementation
```

---

## Debugging

### Enable Debug Logging
```bash
# Set environment variable
export PKDevTools_Default_Log_Level=10

# Or in code
import logging
logging.getLogger('pkscreener').setLevel(logging.DEBUG)
```

### Common Debug Points
1. **Menu Selection**: `globals.py` → `getScannerMenuChoices()`
2. **Stock Fetching**: `Fetcher.py` → `fetchStockDataWithArgs()`
3. **Screening Logic**: `ScreeningStatistics.py` → specific `validate*()` methods
4. **Results Processing**: `ResultsManager.py` → `formatResults()`

### Useful Debug Commands
```python
# Print DataFrame info
print(df.info())
print(df.tail())

# Check screening dict
import json
print(json.dumps(screenDict, indent=2, default=str))
```

---

## Next Steps
- See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system architecture
- See [SCAN_WORKFLOWS.md](SCAN_WORKFLOWS.md) for scan category details
- See [Contributing Guidelines](https://github.com/pkjmesra/PKScreener/blob/main/CONTRIBUTING.md) for contribution guidelines
