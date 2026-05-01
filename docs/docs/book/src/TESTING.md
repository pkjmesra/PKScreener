# PKScreener Testing Guide

This document provides comprehensive guidance for writing and running tests for PKScreener.

---

## Table of Contents
1. [Test Structure](#test-structure)
2. [Running Tests](#running-tests)
3. [Writing Tests](#writing-tests)
4. [Mocking Guidelines](#mocking-guidelines)
5. [Test Coverage](#test-coverage)
6. [Best Practices](#best-practices)

---

## Test Structure

### Directory Layout
```
test/
├── asserters.py                    # Common assertion helpers
├── sharedmock.py                   # Shared mock objects
├── RequestsMocker.py               # HTTP request mocking
│
├── globals_test.py                 # Tests for globals.py
├── pkscreenercli_test.py           # CLI tests
├── pkscreenerbot_test.py           # Bot tests
│
├── ScreeningStatistics_test.py     # Screening logic tests
├── StockScreener_test.py           # Screener orchestration tests
├── CandlePatterns_test.py          # Pattern detection tests
│
├── BacktestHandler_test.py         # Backtest tests
├── BacktestHandler_feature_test.py # Backtest feature tests
│
├── ResultsManager_test.py          # Results formatting tests
├── TelegramNotifier_test.py        # Notification tests
├── BotHandlers_feature_test.py     # Bot handler tests
│
├── Fetcher_test.py                 # Data fetching tests
├── Configmanager_test.py           # Configuration tests
│
├── MainLogic_comprehensive_test.py # Main logic tests
├── integration_mainlogic_test.py   # Integration tests
│
└── ...                             # Other test files
```

### Test File Naming Convention
- Unit tests: `ModuleName_test.py`
- Feature tests: `ModuleName_feature_test.py`
- Integration tests: `integration_modulename_test.py`

---

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest test/ -v

# Run specific test file
pytest test/ScreeningStatistics_test.py -v

# Run specific test class
pytest test/ScreeningStatistics_test.py::TestBreakoutValidation -v

# Run specific test method
pytest test/ScreeningStatistics_test.py::TestBreakoutValidation::test_breakout_detected -v
```

### With Coverage
```bash
# Run with coverage measurement
coverage run -m pytest test/ -v

# Generate coverage report
coverage report --include="pkscreener/**"

# Generate HTML report
coverage html --include="pkscreener/**"

# Show missing lines
coverage report --show-missing --include="pkscreener/classes/StockScreener.py"
```

### With Timeout
```bash
# Prevent hanging tests
pytest test/ --timeout=30 -v
```

### Common Options
```bash
# Quiet mode (less output)
pytest test/ -q

# Stop on first failure
pytest test/ -x

# Show local variables on failure
pytest test/ -l

# Run in parallel (requires pytest-xdist)
pytest test/ -n auto

# Skip slow tests
pytest test/ -m "not slow"
```

---

## Writing Tests

### Basic Test Structure
```python
"""
Tests for YourModule.py
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock
from argparse import Namespace


class TestYourFeature:
    """Test suite for YourFeature."""
    
    def setup_method(self):
        """Setup before each test method."""
        self.mock_config = MagicMock()
        self.mock_config.period = "1y"
        self.mock_config.duration = "1d"
    
    def teardown_method(self):
        """Cleanup after each test method."""
        pass
    
    def test_feature_positive_case(self):
        """Test description - what we're testing."""
        # Arrange
        input_data = self._create_test_data()
        expected_result = True
        
        # Act
        result = your_function(input_data)
        
        # Assert
        assert result == expected_result
    
    def test_feature_edge_case(self):
        """Test edge case handling."""
        # Test with edge case data
        pass
    
    def _create_test_data(self):
        """Helper to create test data."""
        return pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [98, 99, 100],
            'Close': [103, 104, 105],
            'Volume': [1000, 1100, 1200]
        })
```

### Testing with Fixtures
```python
import pytest

@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    return pd.DataFrame({
        'Open': np.random.uniform(100, 110, 100),
        'High': np.random.uniform(110, 120, 100),
        'Low': np.random.uniform(90, 100, 100),
        'Close': np.random.uniform(100, 115, 100),
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

@pytest.fixture
def mock_config_manager():
    """Create mock ConfigManager."""
    config = MagicMock()
    config.period = "1y"
    config.duration = "1d"
    config.daysToLookback = 22
    config.volumeRatio = 2.5
    return config

@pytest.fixture
def mock_user_args():
    """Create mock user arguments."""
    return Namespace(
        options="X:12:1",
        testbuild=True,
        download=False,
        log=False
    )


class TestWithFixtures:
    def test_using_fixtures(self, sample_ohlcv_data, mock_config_manager):
        """Test using pytest fixtures."""
        # Use fixtures directly
        assert len(sample_ohlcv_data) == 100
        assert mock_config_manager.period == "1y"
```

### Testing ScreeningStatistics
```python
class TestBreakoutValidation:
    """Tests for validateBreakout method."""
    
    def setup_method(self):
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        
        self.mock_config = MagicMock()
        self.mock_config.daysToLookback = 22
        self.mock_logger = MagicMock()
        
        self.stats = ScreeningStatistics(
            configManager=self.mock_config,
            default_logger=self.mock_logger
        )
    
    def _create_breakout_data(self):
        """Create data that should trigger breakout."""
        # Create consolidation followed by breakout
        prices = [100] * 20 + [110, 115]  # Consolidation then breakout
        return pd.DataFrame({
            'Open': prices,
            'High': [p + 2 for p in prices],
            'Low': [p - 2 for p in prices],
            'Close': prices,
            'Volume': [1000] * 20 + [5000, 6000]  # Volume spike
        })
    
    def _create_no_breakout_data(self):
        """Create data that should not trigger breakout."""
        prices = [100 + i*0.1 for i in range(22)]  # Gradual rise
        return pd.DataFrame({
            'Open': prices,
            'High': [p + 1 for p in prices],
            'Low': [p - 1 for p in prices],
            'Close': prices,
            'Volume': [1000] * 22
        })
    
    def test_breakout_detected(self):
        """Test breakout is correctly detected."""
        df = self._create_breakout_data()
        screenDict = {}
        saveDict = {}
        
        result = self.stats.validateBreakout(df, screenDict, saveDict, 20)
        
        assert result == True
        assert 'Breakout' in screenDict.get('Pattern', '')
    
    def test_no_breakout(self):
        """Test no false positive for non-breakout."""
        df = self._create_no_breakout_data()
        screenDict = {}
        saveDict = {}
        
        result = self.stats.validateBreakout(df, screenDict, saveDict, 20)
        
        assert result == False
    
    def test_with_exception_handling(self):
        """Test graceful handling of invalid data."""
        df = pd.DataFrame()  # Empty DataFrame
        
        # Should not raise exception
        result = self.stats.validateBreakout(df, {}, {}, 20)
        
        assert result == False
```

---

## Mocking Guidelines

### Common Mocking Patterns

#### Mocking Output Controls
```python
with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
    # Code that prints output
    result = function_that_prints()
```

#### Mocking User Input
```python
with patch('builtins.input', return_value='Y'):
    # Code that asks for input
    result = function_that_asks()
```

#### Mocking External Services
```python
with patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockDataWithArgs') as mock_fetch:
    mock_fetch.return_value = (mock_stock_dict, {})
    result = function_that_fetches()
```

#### Mocking Configuration
```python
mock_config = MagicMock()
mock_config.period = "1y"
mock_config.duration = "1d"
mock_config.volumeRatio = 2.5

with patch('pkscreener.globals.configManager', mock_config):
    result = function_using_config()
```

#### Mocking Telegram
```python
with patch('PKDevTools.classes.Telegram.is_token_telegram_configured', return_value=True):
    with patch('PKDevTools.classes.Telegram.send_message') as mock_send:
        mock_send.return_value = MagicMock(text='Success')
        result = send_notification()
```

### Mocking Global State
```python
import pkscreener.globals as gbl

def test_with_global_state():
    original_args = gbl.userPassedArgs
    original_choice = gbl.selectedChoice
    
    try:
        # Set test state
        gbl.userPassedArgs = MagicMock()
        gbl.userPassedArgs.options = "X:12:1"
        gbl.selectedChoice = {"0": "X", "1": "12", "2": "1"}
        
        # Run test
        result = function_using_globals()
        
        assert result is not None
    finally:
        # Restore original state
        gbl.userPassedArgs = original_args
        gbl.selectedChoice = original_choice
```

### Mocking DataFrames
```python
def create_mock_stock_data(trend='up', length=100):
    """Create mock stock data with specified trend."""
    if trend == 'up':
        close = [100 + i for i in range(length)]
    elif trend == 'down':
        close = [200 - i for i in range(length)]
    else:
        close = [100] * length
    
    return pd.DataFrame({
        'Open': [c - 1 for c in close],
        'High': [c + 2 for c in close],
        'Low': [c - 2 for c in close],
        'Close': close,
        'Volume': [1000 + i * 10 for i in range(length)],
        'date': pd.date_range('2023-01-01', periods=length)
    })
```

---

## Test Coverage

### Current Coverage Targets

| Module | Target | Current |
|--------|--------|---------|
| BacktestHandler.py | 90% | 90% ✓ |
| ResultsManager.py | 90% | 90% ✓ |
| TelegramNotifier.py | 90% | 94% ✓ |
| BotHandlers.py | 90% | 93% ✓ |
| PKUserRegistration.py | 90% | 93% ✓ |
| Barometer.py | 90% | 100% ✓ |
| globals.py | 90% | 45% |
| MainLogic.py | 90% | 69% |
| pkscreenercli.py | 90% | 57% |

### Checking Coverage for Specific Files
```bash
# Check coverage for a specific file
coverage run -m pytest test/ScreeningStatistics_test.py
coverage report --include="pkscreener/classes/ScreeningStatistics.py" --show-missing
```

### Coverage Report Interpretation
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
pkscreener/classes/StockScreener.py      200     50    75%   45-60, 120-135
```
- **Stmts**: Total statements
- **Miss**: Uncovered statements
- **Cover**: Coverage percentage
- **Missing**: Line numbers not covered

---

## Best Practices

### 1. Test Isolation
```python
# Good: Each test is independent
class TestFeature:
    def setup_method(self):
        self.fresh_instance = MyClass()
    
    def test_one(self):
        result = self.fresh_instance.method()
        assert result == expected

# Bad: Tests depend on each other
class TestFeature:
    shared_state = None
    
    def test_one(self):
        TestFeature.shared_state = "value"
    
    def test_two(self):
        assert TestFeature.shared_state == "value"  # Depends on test_one
```

### 2. Descriptive Test Names
```python
# Good
def test_breakout_detected_when_price_exceeds_resistance():
    pass

def test_rsi_returns_none_for_insufficient_data():
    pass

# Bad
def test_1():
    pass

def test_breakout():
    pass
```

### 3. Arrange-Act-Assert Pattern
```python
def test_volume_spike_detection(self):
    # Arrange
    df = self._create_volume_spike_data()
    expected_spike = True
    
    # Act
    result = detect_volume_spike(df, threshold=2.0)
    
    # Assert
    assert result == expected_spike
```

### 4. Test Edge Cases
```python
def test_empty_dataframe():
    """Test handling of empty input."""
    result = process_data(pd.DataFrame())
    assert result is None

def test_single_row():
    """Test with minimum data."""
    df = pd.DataFrame({'Close': [100]})
    result = calculate_sma(df, 20)
    assert np.isnan(result)

def test_nan_values():
    """Test handling of NaN values."""
    df = pd.DataFrame({'Close': [100, np.nan, 102]})
    result = process_data(df)
    assert result is not None
```

### 5. Use Parameterized Tests
```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    (0, "Zero"),
    (1, "One"),
    (-1, "Negative"),
    (100, "Hundred"),
])
def test_number_to_text(input_value, expected):
    result = number_to_text(input_value)
    assert result == expected
```

### 6. Mock External Dependencies
```python
# Good: Mock external API calls
@patch('requests.get')
def test_fetch_data(mock_get):
    mock_get.return_value.json.return_value = {'data': [1, 2, 3]}
    result = fetch_external_data()
    assert result == [1, 2, 3]

# Bad: Actually calling external APIs in tests
def test_fetch_data():
    result = fetch_external_data()  # Flaky, slow, depends on network
```

---

## See Also
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development setup
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [Contributing Guidelines](https://github.com/pkjmesra/PKScreener/blob/main/CONTRIBUTING.md) - Contribution guidelines
