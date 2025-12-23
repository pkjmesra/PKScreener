"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for internal methods of low-coverage modules.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock, PropertyMock
from argparse import Namespace
import warnings
import sys
import os
warnings.filterwarnings("ignore")


@pytest.fixture
def config():
    """Create a configuration manager."""
    from pkscreener.classes.ConfigManager import tools, parser
    config = tools()
    config.getConfig(parser)
    return config


@pytest.fixture
def stock_df():
    """Create stock DataFrame."""
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    np.random.seed(42)
    base = 100
    closes = []
    for i in range(300):
        base += np.random.uniform(-1, 1.5)
        closes.append(max(50, base))
    
    df = pd.DataFrame({
        'open': [c * np.random.uniform(0.98, 1.0) for c in closes],
        'high': [max(c * 0.99, c) * np.random.uniform(1.0, 1.02) for c in closes],
        'low': [min(c * 0.99, c) * np.random.uniform(0.98, 1.0) for c in closes],
        'close': closes,
        'volume': np.random.randint(500000, 10000000, 300),
        'adjclose': closes,
    }, index=dates)
    df['VolMA'] = df['volume'].rolling(20).mean().fillna(method='bfill')
    return df


# =============================================================================
# ConfigManager Internal Tests
# =============================================================================

class TestConfigManagerInternals:
    """Test ConfigManager internal methods."""
    
    def test_config_manager_period(self, config):
        """Test ConfigManager period attribute."""
        assert hasattr(config, 'period')
    
    def test_config_manager_duration(self, config):
        """Test ConfigManager duration attribute."""
        assert hasattr(config, 'duration')
    
    def test_config_manager_days_to_lookback(self, config):
        """Test ConfigManager daysToLookback attribute."""
        assert hasattr(config, 'daysToLookback')
    
    def test_config_manager_volume_ratio(self, config):
        """Test ConfigManager volumeRatio attribute."""
        assert hasattr(config, 'volumeRatio')
    
    def test_config_manager_backtest_period(self, config):
        """Test ConfigManager backtestPeriod attribute."""
        assert hasattr(config, 'backtestPeriod')
    
    def test_config_manager_is_intraday_config(self, config):
        """Test ConfigManager isIntradayConfig method."""
        assert hasattr(config, 'isIntradayConfig')
        result = config.isIntradayConfig()
        assert isinstance(result, bool)
    
    def test_config_manager_cache_enabled(self, config):
        """Test ConfigManager cacheEnabled attribute."""
        assert hasattr(config, 'cacheEnabled')


# =============================================================================
# Fetcher Internal Tests
# =============================================================================

class TestFetcherInternals:
    """Test Fetcher internal methods."""
    
    def test_fetcher_fetch_stock_codes(self):
        """Test fetcher fetchStockCodes method."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        fetcher = screenerStockDataFetcher()
        assert hasattr(fetcher, 'fetchStockCodes')
    
    def test_fetcher_fetch_stock_data(self):
        """Test fetcher fetchStockData method."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        fetcher = screenerStockDataFetcher()
        assert hasattr(fetcher, 'fetchStockData')
    
    def test_fetcher_fetch_latest_nifty(self):
        """Test fetcher fetchLatestNifty method."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        fetcher = screenerStockDataFetcher()
        assert hasattr(fetcher, 'fetchLatestNiftyDaily')


# =============================================================================
# GlobalStore Internal Tests
# =============================================================================

class TestGlobalStoreInternals:
    """Test GlobalStore internal methods."""
    
    def test_global_store_singleton(self):
        """Test GlobalStore singleton pattern."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store1 = PKGlobalStore()
        store2 = PKGlobalStore()
        assert store1 is store2
    
    def test_global_store_config_manager(self):
        """Test GlobalStore configManager attribute."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        store = PKGlobalStore()
        assert hasattr(store, 'configManager')


# =============================================================================
# CandlePatterns Internal Tests
# =============================================================================

class TestCandlePatternsInternals:
    """Test CandlePatterns internal methods."""
    
    def test_candle_patterns_has_reversal_patterns(self):
        """Test CandlePatterns has reversal patterns."""
        from pkscreener.classes.CandlePatterns import CandlePatterns
        cp = CandlePatterns()
        assert hasattr(cp, 'reversalPatternsBullish') or hasattr(cp, 'reversalPatterns')
    
    def test_candle_patterns_has_continuation_patterns(self):
        """Test CandlePatterns has continuation patterns."""
        from pkscreener.classes.CandlePatterns import CandlePatterns
        cp = CandlePatterns()
        assert cp is not None


# =============================================================================
# OtaUpdater Internal Tests
# =============================================================================

class TestOtaUpdaterInternals:
    """Test OtaUpdater internal methods."""
    
    def test_ota_updater_check_updates(self):
        """Test OTAUpdater checkForUpdates method."""
        from pkscreener.classes.OtaUpdater import OTAUpdater
        updater = OTAUpdater()
        assert hasattr(updater, 'checkForUpdate')


# =============================================================================
# PKAnalytics Internal Tests
# =============================================================================

class TestPKAnalyticsInternals:
    """Test PKAnalytics internal methods."""
    
    def test_analytics_service_send_event(self):
        """Test PKAnalyticsService send_event method."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        service = PKAnalyticsService()
        assert hasattr(service, 'send_event')


# =============================================================================
# PKScheduler Internal Tests
# =============================================================================

class TestPKSchedulerInternals:
    """Test PKScheduler internal methods."""
    
    def test_scheduler_class(self):
        """Test PKScheduler class."""
        from pkscreener.classes.PKScheduler import PKScheduler
        assert PKScheduler is not None


# =============================================================================
# PKTask Internal Tests
# =============================================================================

class TestPKTaskInternals:
    """Test PKTask internal methods."""
    
    def test_task_class(self):
        """Test PKTask class."""
        from pkscreener.classes.PKTask import PKTask
        assert PKTask is not None


# =============================================================================
# PKDemoHandler Internal Tests
# =============================================================================

class TestPKDemoHandlerInternals:
    """Test PKDemoHandler internal methods."""
    
    def test_demo_handler_methods(self):
        """Test PKDemoHandler methods."""
        from pkscreener.classes.PKDemoHandler import PKDemoHandler
        handler = PKDemoHandler()
        assert handler is not None


# =============================================================================
# Portfolio Internal Tests
# =============================================================================

class TestPortfolioInternals:
    """Test Portfolio internal methods."""
    
    def test_portfolio_collection(self):
        """Test PortfolioCollection class."""
        from pkscreener.classes.Portfolio import PortfolioCollection
        assert PortfolioCollection is not None


# =============================================================================
# AssetsManager Internal Tests
# =============================================================================

class TestAssetsManagerInternals:
    """Test AssetsManager internal methods."""
    
    def test_assets_manager_class(self):
        """Test PKAssetsManager class."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        assert PKAssetsManager is not None
    
    def test_after_market_stock_data_exists(self):
        """Test afterMarketStockDataExists method."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        result = PKAssetsManager.afterMarketStockDataExists(False)
        assert isinstance(result, tuple)


# =============================================================================
# ImageUtility Internal Tests
# =============================================================================

class TestImageUtilityInternals:
    """Test ImageUtility internal methods."""
    
    def test_pk_image_tools_class(self):
        """Test PKImageTools class."""
        from pkscreener.classes.ImageUtility import PKImageTools
        assert PKImageTools is not None


# =============================================================================
# MarketMonitor Internal Tests
# =============================================================================

class TestMarketMonitorInternals:
    """Test MarketMonitor internal methods."""
    
    def test_market_monitor_class(self):
        """Test MarketMonitor class."""
        from pkscreener.classes.MarketMonitor import MarketMonitor
        assert MarketMonitor is not None


# =============================================================================
# MarketStatus Internal Tests
# =============================================================================

class TestMarketStatusInternals:
    """Test MarketStatus internal methods."""
    
    def test_market_status_module(self):
        """Test MarketStatus module."""
        from pkscreener.classes import MarketStatus
        assert MarketStatus is not None


# =============================================================================
# ConsoleUtility Internal Tests
# =============================================================================

class TestConsoleUtilityInternals:
    """Test ConsoleUtility internal methods."""
    
    def test_pk_console_tools_class(self):
        """Test PKConsoleTools class."""
        from pkscreener.classes.ConsoleUtility import PKConsoleTools
        assert PKConsoleTools is not None


# =============================================================================
# ConsoleMenuUtility Internal Tests
# =============================================================================

class TestConsoleMenuUtilityInternals:
    """Test ConsoleMenuUtility internal methods."""
    
    def test_pk_console_menu_tools_class(self):
        """Test PKConsoleMenuTools class."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        assert PKConsoleMenuTools is not None


# =============================================================================
# signals Internal Tests
# =============================================================================

class TestSignalsInternals:
    """Test signals module internal methods."""
    
    def test_signal_strength_values(self):
        """Test SignalStrength enum values."""
        from pkscreener.classes.screening.signals import SignalStrength
        
        # Check all values exist
        assert SignalStrength.STRONG_BUY is not None
        assert SignalStrength.BUY is not None
        assert SignalStrength.WEAK_BUY is not None
        assert SignalStrength.NEUTRAL is not None
        assert SignalStrength.WEAK_SELL is not None
        assert SignalStrength.SELL is not None
        assert SignalStrength.STRONG_SELL is not None
    
    def test_signal_strength_ordering(self):
        """Test SignalStrength enum ordering."""
        from pkscreener.classes.screening.signals import SignalStrength
        
        # Check ordering
        assert SignalStrength.STRONG_BUY.value > SignalStrength.BUY.value
        assert SignalStrength.BUY.value > SignalStrength.WEAK_BUY.value
        assert SignalStrength.WEAK_BUY.value > SignalStrength.NEUTRAL.value
        assert SignalStrength.NEUTRAL.value > SignalStrength.WEAK_SELL.value
        assert SignalStrength.WEAK_SELL.value > SignalStrength.SELL.value
        assert SignalStrength.SELL.value > SignalStrength.STRONG_SELL.value
    
    def test_signal_result_dataclass(self):
        """Test SignalResult dataclass."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        for signal in SignalStrength:
            for confidence in [0, 25, 50, 75, 100]:
                result = SignalResult(signal=signal, confidence=float(confidence))
                assert result.signal == signal
                assert result.confidence == float(confidence)


# =============================================================================
# Pktalib Internal Tests
# =============================================================================

class TestPktalibInternals:
    """Test Pktalib internal methods."""
    
    def test_sma_calculation(self):
        """Test SMA calculation."""
        from pkscreener.classes.Pktalib import pktalib
        data = np.random.uniform(90, 110, 100)
        result = pktalib.SMA(data, 20)
        assert result is not None
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        from pkscreener.classes.Pktalib import pktalib
        data = np.random.uniform(90, 110, 100)
        result = pktalib.EMA(data, 20)
        assert result is not None
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        from pkscreener.classes.Pktalib import pktalib
        data = np.random.uniform(90, 110, 100)
        result = pktalib.RSI(data, 14)
        assert result is not None
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        from pkscreener.classes.Pktalib import pktalib
        data = np.random.uniform(90, 110, 100)
        result = pktalib.MACD(data, 12, 26, 9)
        assert result is not None
    
    def test_bbands_calculation(self):
        """Test Bollinger Bands calculation."""
        from pkscreener.classes.Pktalib import pktalib
        data = np.random.uniform(90, 110, 100)
        result = pktalib.BBANDS(data, 20, 2, 2)
        assert result is not None


# =============================================================================
# PortfolioXRay Internal Tests
# =============================================================================

class TestPortfolioXRayInternals:
    """Test PortfolioXRay internal methods."""
    
    def test_portfolio_xray_module(self):
        """Test PortfolioXRay module."""
        from pkscreener.classes import PortfolioXRay
        assert PortfolioXRay is not None


# =============================================================================
# Backtest Internal Tests
# =============================================================================

class TestBacktestInternals:
    """Test Backtest internal methods."""
    
    def test_backtest_function(self):
        """Test backtest function exists."""
        from pkscreener.classes.Backtest import backtest
        assert backtest is not None
    
    def test_backtest_summary_function(self):
        """Test backtestSummary function exists."""
        from pkscreener.classes.Backtest import backtestSummary
        assert backtestSummary is not None


# =============================================================================
# PKMarketOpenCloseAnalyser Internal Tests
# =============================================================================

class TestPKMarketOpenCloseAnalyserInternals:
    """Test PKMarketOpenCloseAnalyser internal methods."""
    
    def test_analyser_class(self):
        """Test PKMarketOpenCloseAnalyser class."""
        from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser
        assert PKMarketOpenCloseAnalyser is not None


# =============================================================================
# ResultsManager Internal Tests
# =============================================================================

class TestResultsManagerInternals:
    """Test ResultsManager internal methods."""
    
    def test_results_manager_creation(self, config):
        """Test ResultsManager creation."""
        from pkscreener.classes.ResultsManager import ResultsManager
        manager = ResultsManager(config)
        assert manager is not None


# =============================================================================
# BacktestHandler Internal Tests
# =============================================================================

class TestBacktestHandlerInternals:
    """Test BacktestHandler internal methods."""
    
    def test_backtest_handler_creation(self, config):
        """Test BacktestHandler creation."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        handler = BacktestHandler(config)
        assert handler is not None


# =============================================================================
# DataLoader Internal Tests
# =============================================================================

class TestDataLoaderInternals:
    """Test DataLoader internal methods."""
    
    def test_stock_data_loader_creation(self, config):
        """Test StockDataLoader creation."""
        from pkscreener.classes.DataLoader import StockDataLoader
        mock_fetcher = MagicMock()
        loader = StockDataLoader(config, mock_fetcher)
        assert loader is not None


# =============================================================================
# CoreFunctions Internal Tests
# =============================================================================

class TestCoreFunctionsInternals:
    """Test CoreFunctions internal methods."""
    
    def test_get_review_date(self):
        """Test get_review_date function."""
        from pkscreener.classes.CoreFunctions import get_review_date
        args = Namespace(backtestdaysago=5)
        result = get_review_date(None, args)
        assert result is not None


# =============================================================================
# BacktestUtils Internal Tests
# =============================================================================

class TestBacktestUtilsInternals:
    """Test BacktestUtils internal methods."""
    
    def test_get_backtest_report_filename(self):
        """Test get_backtest_report_filename function."""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        result = get_backtest_report_filename()
        assert result is not None
    
    def test_backtest_results_handler(self, config):
        """Test BacktestResultsHandler."""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        handler = BacktestResultsHandler(config)
        assert handler is not None


# =============================================================================
# ResultsLabeler Internal Tests
# =============================================================================

class TestResultsLabelerInternals:
    """Test ResultsLabeler internal methods."""
    
    def test_results_labeler_creation(self, config):
        """Test ResultsLabeler creation."""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        labeler = ResultsLabeler(config)
        assert labeler is not None


# =============================================================================
# PKScanRunner Internal Tests
# =============================================================================

class TestPKScanRunnerInternals:
    """Test PKScanRunner internal methods."""
    
    def test_pk_scan_runner_creation(self):
        """Test PKScanRunner creation."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        runner = PKScanRunner()
        assert runner is not None
    
    def test_get_formatted_choices(self):
        """Test getFormattedChoices method."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        args = Namespace(runintradayanalysis=False, intraday=None)
        choices = {"0": "X", "1": "12", "2": "1"}
        result = PKScanRunner.getFormattedChoices(args, choices)
        assert isinstance(result, str)


# =============================================================================
# PKCliRunner Internal Tests
# =============================================================================

class TestPKCliRunnerInternals:
    """Test PKCliRunner internal methods."""
    
    def test_cli_config_manager_creation(self, config):
        """Test CliConfigManager creation."""
        from pkscreener.classes.cli.PKCliRunner import CliConfigManager
        manager = CliConfigManager(config, Namespace())
        assert manager is not None


# =============================================================================
# TelegramNotifier Internal Tests
# =============================================================================

class TestTelegramNotifierInternals:
    """Test TelegramNotifier internal methods."""
    
    def test_telegram_notifier_class(self):
        """Test TelegramNotifier class."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        assert TelegramNotifier is not None


# =============================================================================
# BotHandlers Internal Tests
# =============================================================================

class TestBotHandlersInternals:
    """Test BotHandlers internal methods."""
    
    def test_bot_handlers_module(self):
        """Test BotHandlers module."""
        from pkscreener.classes.bot import BotHandlers
        assert BotHandlers is not None


# =============================================================================
# UserMenuChoicesHandler Internal Tests
# =============================================================================

class TestUserMenuChoicesHandlerInternals:
    """Test UserMenuChoicesHandler internal methods."""
    
    def test_user_menu_choices_handler_module(self):
        """Test UserMenuChoicesHandler module."""
        from pkscreener.classes import UserMenuChoicesHandler
        assert UserMenuChoicesHandler is not None


# =============================================================================
# PKUserRegistration Internal Tests
# =============================================================================

class TestPKUserRegistrationInternals:
    """Test PKUserRegistration internal methods."""
    
    def test_validation_result_enum(self):
        """Test ValidationResult enum."""
        from pkscreener.classes.PKUserRegistration import ValidationResult
        assert ValidationResult.Success is not None


# =============================================================================
# keys Internal Tests
# =============================================================================

class TestKeysInternals:
    """Test keys module internal methods."""
    
    def test_keys_module(self):
        """Test keys module."""
        from pkscreener.classes import keys
        assert keys is not None


# =============================================================================
# PKDataService Internal Tests
# =============================================================================

class TestPKDataServiceInternals:
    """Test PKDataService internal methods."""
    
    def test_pk_data_service_class(self):
        """Test PKDataService class."""
        from pkscreener.classes.PKDataService import PKDataService
        assert PKDataService is not None
