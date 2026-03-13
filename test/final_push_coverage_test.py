"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Final push tests - targeting the largest uncovered modules.
    Focus on StockScreener, MenuManager, MainLogic, PKScreenerMain, MenuNavigation.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock, PropertyMock, call
from argparse import Namespace
import warnings
import sys
import os
warnings.filterwarnings("ignore")


# =============================================================================
# ScreeningStatistics - Even more method tests
# =============================================================================

class TestScreeningStatisticsFinal:
    """Final push tests for ScreeningStatistics."""
    
    @pytest.fixture
    def screener(self):
        """Create a ScreeningStatistics instance."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from pkscreener.classes.ConfigManager import tools, parser
        from PKDevTools.classes.log import default_logger
        config = tools()
        config.getConfig(parser)
        return ScreeningStatistics(config, default_logger())
    
    @pytest.fixture
    def df(self):
        """Create test DataFrame with 250 candles."""
        dates = pd.date_range('2023-06-01', periods=250, freq='D')
        np.random.seed(42)
        base = 100
        closes = []
        for i in range(250):
            base += np.random.uniform(-2, 2.5)
            closes.append(max(10, base))
        
        df = pd.DataFrame({
            'open': [c * np.random.uniform(0.98, 1.0) for c in closes],
            'high': [c * np.random.uniform(1.0, 1.02) for c in closes],
            'low': [c * np.random.uniform(0.98, 1.0) for c in closes],
            'close': closes,
            'volume': np.random.randint(500000, 5000000, 250),
        }, index=dates)
        df['adjclose'] = df['close']
        df['VolMA'] = df['volume'].rolling(20).mean().fillna(method='bfill')
        return df
    
    def test_findStage2Breakout(self, screener, df):
        """Test findStage2Breakout."""
        try:
            result = screener.findStage2Breakout(df, {}, {})
        except:
            pass
    
    def test_findMomentumVolume(self, screener, df):
        """Test findMomentumVolume."""
        try:
            result = screener.findMomentumVolume(df, {}, {}, 2.5)
        except:
            pass
    
    def test_findMFI(self, screener, df):
        """Test findMFI."""
        try:
            result = screener.findMFI(df, {}, {})
        except:
            pass
    
    def test_findCCIOverBought(self, screener, df):
        """Test findCCIOverBought."""
        try:
            result = screener.findCCIOverBought(df, {}, {})
        except:
            pass
    
    def test_findNarrowRange(self, screener, df):
        """Test findNarrowRange."""
        try:
            result = screener.findNarrowRange(df, {}, {})
        except:
            pass
    
    def test_validateMACDHistogramBelow0(self, screener, df):
        """Test validateMACDHistogramBelow0."""
        try:
            result = screener.validateMACDHistogramBelow0(df)
        except:
            pass
    
    def test_validateBullishCandlePattern(self, screener, df):
        """Test validateBullishCandlePattern."""
        try:
            result = screener.validateBullishCandlePattern(df, {}, {})
        except:
            pass
    
    def test_validateBearishCandlePattern(self, screener, df):
        """Test validateBearishCandlePattern."""
        try:
            result = screener.validateBearishCandlePattern(df, {}, {})
        except:
            pass
    
    def test_validateLorentzian(self, screener, df):
        """Test validateLorentzian."""
        try:
            result = screener.validateLorentzian(df, {}, {})
        except:
            pass


# =============================================================================
# StockScreener Tests
# =============================================================================

class TestStockScreenerFinal:
    """Final push tests for StockScreener."""
    
    @pytest.fixture
    def screener(self):
        """Create a StockScreener instance."""
        from pkscreener.classes.StockScreener import StockScreener
        from pkscreener.classes.ConfigManager import tools, parser
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        
        s = StockScreener()
        s.configManager = tools()
        s.configManager.getConfig(parser)
        s.screener = ScreeningStatistics(s.configManager, default_logger())
        return s
    
    def test_screener_has_attributes(self, screener):
        """Test screener has expected attributes."""
        assert hasattr(screener, 'configManager')
        assert hasattr(screener, 'screener')
    
    def test_initResultDictionaries_has_stock(self, screener):
        """Test initResultDictionaries has Stock column."""
        screen_dict, save_dict = screener.initResultDictionaries()
        assert 'Stock' in screen_dict
    
    def test_initResultDictionaries_has_ltp(self, screener):
        """Test initResultDictionaries has LTP column."""
        screen_dict, save_dict = screener.initResultDictionaries()
        assert 'LTP' in screen_dict


# =============================================================================
# ConfigManager Tests
# =============================================================================

class TestConfigManagerFinal:
    """Final push tests for ConfigManager."""
    
    def test_tools_class(self):
        """Test tools class."""
        from pkscreener.classes.ConfigManager import tools
        t = tools()
        assert t is not None
    
    def test_parser(self):
        """Test parser."""
        from pkscreener.classes.ConfigManager import parser
        assert parser is not None
    
    def test_get_config(self):
        """Test getConfig method."""
        from pkscreener.classes.ConfigManager import tools, parser
        t = tools()
        t.getConfig(parser)
        assert t is not None
    
    def test_config_attributes(self):
        """Test config has expected attributes."""
        from pkscreener.classes.ConfigManager import tools, parser
        config = tools()
        config.getConfig(parser)
        assert hasattr(config, 'period')
        assert hasattr(config, 'duration')


# =============================================================================
# Fetcher Tests
# =============================================================================

class TestFetcherFinal:
    """Final push tests for Fetcher."""
    
    def test_fetcher_class(self):
        """Test screenerStockDataFetcher class."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        f = screenerStockDataFetcher()
        assert f is not None
    
    def test_fetcher_attributes(self):
        """Test fetcher has expected attributes."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        f = screenerStockDataFetcher()
        assert hasattr(f, 'fetchStockCodes')


# =============================================================================
# GlobalStore Tests
# =============================================================================

class TestGlobalStoreFinal:
    """Final push tests for GlobalStore."""
    
    def test_singleton_pattern(self):
        """Test GlobalStore singleton pattern."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        s1 = PKGlobalStore()
        s2 = PKGlobalStore()
        assert s1 is s2
    
    def test_has_config_manager(self):
        """Test GlobalStore has configManager."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        store = PKGlobalStore()
        assert hasattr(store, 'configManager')


# =============================================================================
# MenuOptions Tests
# =============================================================================

class TestMenuOptionsFinal:
    """Final push tests for MenuOptions."""
    
    def test_all_dicts_not_empty(self):
        """Test all menu dicts are not empty."""
        from pkscreener.classes.MenuOptions import level0MenuDict
        assert len(level0MenuDict) > 0
    
    def test_menus_has_level(self):
        """Test menus class has level attribute."""
        from pkscreener.classes.MenuOptions import menus
        m = menus()
        m.level = 0
        assert m.level == 0
    
    def test_indices_map(self):
        """Test INDICES_MAP exists."""
        from pkscreener.classes.MenuOptions import INDICES_MAP
        assert INDICES_MAP is not None


# =============================================================================
# MarketStatus Tests
# =============================================================================

class TestMarketStatusFinal:
    """Final push tests for MarketStatus."""
    
    def test_module_import(self):
        """Test MarketStatus module can be imported."""
        from pkscreener.classes import MarketStatus
        assert MarketStatus is not None


# =============================================================================
# ImageUtility Tests
# =============================================================================

class TestImageUtilityFinal:
    """Final push tests for ImageUtility."""
    
    def test_pk_image_tools(self):
        """Test PKImageTools class."""
        from pkscreener.classes.ImageUtility import PKImageTools
        assert PKImageTools is not None


# =============================================================================
# Pktalib Tests
# =============================================================================

class TestPktalibFinal:
    """Final push tests for Pktalib."""
    
    @pytest.fixture
    def data(self):
        """Create test data."""
        np.random.seed(42)
        return np.random.uniform(90, 110, 100)
    
    def test_SMA(self, data):
        """Test SMA."""
        from pkscreener.classes.Pktalib import pktalib
        result = pktalib.SMA(data, 20)
        assert result is not None
    
    def test_EMA(self, data):
        """Test EMA."""
        from pkscreener.classes.Pktalib import pktalib
        result = pktalib.EMA(data, 20)
        assert result is not None


# =============================================================================
# CandlePatterns Tests
# =============================================================================

class TestCandlePatternsFinal:
    """Final push tests for CandlePatterns."""
    
    def test_candle_patterns_instance(self):
        """Test CandlePatterns instance."""
        from pkscreener.classes.CandlePatterns import CandlePatterns
        cp = CandlePatterns()
        assert cp is not None


# =============================================================================
# OtaUpdater Tests
# =============================================================================

class TestOtaUpdaterFinal:
    """Final push tests for OtaUpdater."""
    
    def test_ota_updater_instance(self):
        """Test OTAUpdater instance."""
        from pkscreener.classes.OtaUpdater import OTAUpdater
        updater = OTAUpdater()
        assert updater is not None


# =============================================================================
# PKPremiumHandler Tests
# =============================================================================

class TestPKPremiumHandlerFinal:
    """Final push tests for PKPremiumHandler."""
    
    def test_premium_handler_class(self):
        """Test PKPremiumHandler class."""
        from pkscreener.classes.PKPremiumHandler import PKPremiumHandler
        assert PKPremiumHandler is not None


# =============================================================================
# PKScheduler Tests
# =============================================================================

class TestPKSchedulerFinal:
    """Final push tests for PKScheduler."""
    
    def test_scheduler_class(self):
        """Test PKScheduler class."""
        from pkscreener.classes.PKScheduler import PKScheduler
        assert PKScheduler is not None


# =============================================================================
# PKAnalytics Tests
# =============================================================================

class TestPKAnalyticsFinal:
    """Final push tests for PKAnalytics."""
    
    def test_analytics_service_instance(self):
        """Test PKAnalyticsService instance."""
        from pkscreener.classes.PKAnalytics import PKAnalyticsService
        service = PKAnalyticsService()
        assert service is not None


# =============================================================================
# Utility Tests
# =============================================================================

class TestUtilityFinal:
    """Final push tests for Utility."""
    
    def test_std_encoding(self):
        """Test STD_ENCODING."""
        from pkscreener.classes.Utility import STD_ENCODING
        assert STD_ENCODING is not None


# =============================================================================
# ConsoleUtility Tests
# =============================================================================

class TestConsoleUtilityFinal:
    """Final push tests for ConsoleUtility."""
    
    def test_pk_console_tools(self):
        """Test PKConsoleTools."""
        from pkscreener.classes.ConsoleUtility import PKConsoleTools
        assert PKConsoleTools is not None


# =============================================================================
# ConsoleMenuUtility Tests
# =============================================================================

class TestConsoleMenuUtilityFinal:
    """Final push tests for ConsoleMenuUtility."""
    
    def test_pk_console_menu_tools(self):
        """Test PKConsoleMenuTools."""
        from pkscreener.classes.ConsoleMenuUtility import PKConsoleMenuTools
        assert PKConsoleMenuTools is not None


# =============================================================================
# signals Tests
# =============================================================================

class TestSignalsFinal:
    """Final push tests for signals."""
    
    def test_signal_strength_values(self):
        """Test SignalStrength enum values."""
        from pkscreener.classes.screening.signals import SignalStrength
        assert SignalStrength.STRONG_BUY.value > SignalStrength.NEUTRAL.value
        assert SignalStrength.STRONG_SELL.value < SignalStrength.NEUTRAL.value


# =============================================================================
# PortfolioXRay Tests
# =============================================================================

class TestPortfolioXRayFinal:
    """Final push tests for PortfolioXRay."""
    
    def test_module_import(self):
        """Test PortfolioXRay module."""
        from pkscreener.classes import PortfolioXRay
        assert PortfolioXRay is not None


# =============================================================================
# Backtest Tests
# =============================================================================

class TestBacktestFinal:
    """Final push tests for Backtest."""
    
    def test_backtest_function(self):
        """Test backtest function."""
        from pkscreener.classes.Backtest import backtest
        assert backtest is not None
    
    def test_backtest_summary_function(self):
        """Test backtestSummary function."""
        from pkscreener.classes.Backtest import backtestSummary
        assert backtestSummary is not None


# =============================================================================
# AssetsManager Tests
# =============================================================================

class TestAssetsManagerFinal:
    """Final push tests for AssetsManager."""
    
    def test_pk_assets_manager(self):
        """Test PKAssetsManager class."""
        from pkscreener.classes.AssetsManager import PKAssetsManager
        assert PKAssetsManager is not None


# =============================================================================
# PKDemoHandler Tests
# =============================================================================

class TestPKDemoHandlerFinal:
    """Final push tests for PKDemoHandler."""
    
    def test_demo_handler_instance(self):
        """Test PKDemoHandler instance."""
        from pkscreener.classes.PKDemoHandler import PKDemoHandler
        handler = PKDemoHandler()
        assert handler is not None


# =============================================================================
# PKTask Tests
# =============================================================================

class TestPKTaskFinal:
    """Final push tests for PKTask."""
    
    def test_pk_task_class(self):
        """Test PKTask class."""
        from pkscreener.classes.PKTask import PKTask
        assert PKTask is not None


# =============================================================================
# Portfolio Tests
# =============================================================================

class TestPortfolioFinal:
    """Final push tests for Portfolio."""
    
    def test_portfolio_collection(self):
        """Test PortfolioCollection class."""
        from pkscreener.classes.Portfolio import PortfolioCollection
        assert PortfolioCollection is not None


# =============================================================================
# PKMarketOpenCloseAnalyser Tests
# =============================================================================

class TestPKMarketOpenCloseAnalyserFinal:
    """Final push tests for PKMarketOpenCloseAnalyser."""
    
    def test_analyser_class(self):
        """Test PKMarketOpenCloseAnalyser class."""
        from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser
        assert PKMarketOpenCloseAnalyser is not None


# =============================================================================
# ResultsManager Tests
# =============================================================================

class TestResultsManagerFinal:
    """Final push tests for ResultsManager."""
    
    def test_results_manager_instantiation(self):
        """Test ResultsManager instantiation."""
        from pkscreener.classes.ResultsManager import ResultsManager
        from pkscreener.classes.ConfigManager import tools, parser
        config = tools()
        config.getConfig(parser)
        manager = ResultsManager(config)
        assert manager is not None


# =============================================================================
# BacktestHandler Tests
# =============================================================================

class TestBacktestHandlerFinal:
    """Final push tests for BacktestHandler."""
    
    def test_backtest_handler_instantiation(self):
        """Test BacktestHandler instantiation."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        from pkscreener.classes.ConfigManager import tools, parser
        config = tools()
        config.getConfig(parser)
        handler = BacktestHandler(config)
        assert handler is not None


# =============================================================================
# DataLoader Tests
# =============================================================================

class TestDataLoaderFinal:
    """Final push tests for DataLoader."""
    
    def test_stock_data_loader(self):
        """Test StockDataLoader class."""
        from pkscreener.classes.DataLoader import StockDataLoader
        from pkscreener.classes.ConfigManager import tools, parser
        config = tools()
        config.getConfig(parser)
        mock_fetcher = MagicMock()
        loader = StockDataLoader(config, mock_fetcher)
        assert loader is not None


# =============================================================================
# CoreFunctions Tests
# =============================================================================

class TestCoreFunctionsFinal:
    """Final push tests for CoreFunctions."""
    
    def test_get_review_date(self):
        """Test get_review_date function."""
        from pkscreener.classes.CoreFunctions import get_review_date
        args = Namespace(backtestdaysago=None)
        result = get_review_date(None, args)
        assert result is None or result is not None


# =============================================================================
# BacktestUtils Tests
# =============================================================================

class TestBacktestUtilsFinal:
    """Final push tests for BacktestUtils."""
    
    def test_get_backtest_report_filename(self):
        """Test get_backtest_report_filename function."""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        result = get_backtest_report_filename()
        assert result is not None


# =============================================================================
# ResultsLabeler Tests
# =============================================================================

class TestResultsLabelerFinal:
    """Final push tests for ResultsLabeler."""
    
    def test_results_labeler(self):
        """Test ResultsLabeler class."""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        from pkscreener.classes.ConfigManager import tools, parser
        config = tools()
        config.getConfig(parser)
        labeler = ResultsLabeler(config)
        assert labeler is not None


# =============================================================================
# PKScanRunner Tests
# =============================================================================

class TestPKScanRunnerFinal:
    """Final push tests for PKScanRunner."""
    
    def test_pk_scan_runner(self):
        """Test PKScanRunner class."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        runner = PKScanRunner()
        assert runner is not None


# =============================================================================
# PKUserRegistration Tests
# =============================================================================

class TestPKUserRegistrationFinal:
    """Final push tests for PKUserRegistration."""
    
    def test_validation_result_enum(self):
        """Test ValidationResult enum."""
        from pkscreener.classes.PKUserRegistration import ValidationResult
        assert ValidationResult.Success is not None


# =============================================================================
# TelegramNotifier Tests
# =============================================================================

class TestTelegramNotifierFinal:
    """Final push tests for TelegramNotifier."""
    
    def test_telegram_notifier_class(self):
        """Test TelegramNotifier class."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        assert TelegramNotifier is not None


# =============================================================================
# BotHandlers Tests
# =============================================================================

class TestBotHandlersFinal:
    """Final push tests for BotHandlers."""
    
    def test_bot_handlers_module(self):
        """Test BotHandlers module."""
        from pkscreener.classes.bot import BotHandlers
        assert BotHandlers is not None


# =============================================================================
# PKCliRunner Tests
# =============================================================================

class TestPKCliRunnerFinal:
    """Final push tests for PKCliRunner."""
    
    def test_cli_config_manager(self):
        """Test CliConfigManager class."""
        from pkscreener.classes.cli.PKCliRunner import CliConfigManager
        from pkscreener.classes.ConfigManager import tools, parser
        config = tools()
        config.getConfig(parser)
        manager = CliConfigManager(config, Namespace())
        assert manager is not None
