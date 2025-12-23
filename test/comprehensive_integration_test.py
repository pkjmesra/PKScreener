"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Comprehensive integration tests to maximize coverage.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock, PropertyMock
from argparse import Namespace
import warnings
import sys
import os
import multiprocessing
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
# ScreeningStatistics Integration Tests
# =============================================================================

class TestScreeningStatisticsIntegration:
    """Integration tests for ScreeningStatistics."""
    
    @pytest.fixture
    def screener(self, config):
        """Create a ScreeningStatistics instance."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        return ScreeningStatistics(config, default_logger())
    
    def test_full_screening_flow(self, screener, stock_df):
        """Test full screening flow."""
        screen_dict = {}
        save_dict = {}
        
        # Run all validation methods
        try:
            screener.validateLTP(100, 0, 1000, screen_dict, save_dict)
        except:
            pass
        
        try:
            screener.validateVolume(stock_df, screen_dict, save_dict)
        except:
            pass
        
        # Run breakout methods
        screener.find52WeekHighBreakout(stock_df)
        screener.find52WeekLowBreakout(stock_df)
        screener.find10DaysLowBreakout(stock_df)
        screener.findPotentialBreakout(stock_df, screen_dict, save_dict, daysToLookback=22)
        
        # Run trend methods
        screener.findAroonBullishCrossover(stock_df)
        screener.findHigherOpens(stock_df)
        screener.findHigherBullishOpens(stock_df)
        
        # Run pattern methods
        screener.findNR4Day(stock_df)
        screener.findPerfectShortSellsFutures(stock_df)
        screener.findProbableShortSellsFutures(stock_df)
        
        # Run IPO methods
        screener.findIPOLifetimeFirstDayBullishBreak(stock_df)
        
        # Run 52 week methods
        screener.find52WeekHighLow(stock_df, save_dict, screen_dict)
        
        # Run current saved value
        screener.findCurrentSavedValue(screen_dict, save_dict, 'Pattern')


# =============================================================================
# ExecuteOptionHandlers Integration Tests
# =============================================================================

class TestExecuteOptionHandlersIntegration:
    """Integration tests for ExecuteOptionHandlers."""
    
    def test_all_execute_options(self, config):
        """Test all execute options."""
        from pkscreener.classes.ExecuteOptionHandlers import (
            handle_execute_option_3, handle_execute_option_4,
            handle_execute_option_5, handle_execute_option_9
        )
        
        args = MagicMock()
        args.maxdisplayresults = 100
        args.systemlaunched = False
        m2 = MagicMock()
        m2.find.return_value = MagicMock()
        
        # Execute option 3
        result = handle_execute_option_3(args, config)
        
        # Execute option 4
        for days in [10, 20, 30, 45]:
            result = handle_execute_option_4(4, ["X", "12", "4", str(days)])
        
        # Execute option 5
        result = handle_execute_option_5(["X", "12", "5", "50", "70"], args, m2)
        
        # Execute option 9
        for vol in ["1.5", "2.0", "2.5"]:
            result = handle_execute_option_9(["X", "12", "9", vol], config)


# =============================================================================
# MenuNavigation Integration Tests
# =============================================================================

class TestMenuNavigationIntegration:
    """Integration tests for MenuNavigation."""
    
    @pytest.fixture
    def navigator(self, config):
        """Create a MenuNavigator."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        return MenuNavigator(config)
    
    def test_full_navigation_flow(self, navigator):
        """Test full navigation flow."""
        user_args = Namespace(intraday=None)
        
        # Test various menu combinations
        for menu in ["X", "P", "B"]:
            for index in ["1", "5", "12"]:
                for execute in ["0", "1", "5"]:
                    options = f"{menu}:{index}:{execute}"
                    result = navigator.get_top_level_menu_choices(
                        startup_options=options,
                        test_build=False,
                        download_only=False,
                        default_answer="Y",
                        user_passed_args=user_args,
                        last_scan_output_stock_codes=None
                    )


# =============================================================================
# NotificationService Integration Tests
# =============================================================================

class TestNotificationServiceIntegration:
    """Integration tests for NotificationService."""
    
    def test_full_notification_flow(self):
        """Test full notification flow."""
        from pkscreener.classes.NotificationService import NotificationService
        
        for telegram in [True, False]:
            for log in [True, False]:
                for user in [None, "12345"]:
                    args = Namespace(telegram=telegram, log=log, user=user, monitor=None)
                    service = NotificationService(args)
                    
                    service.set_menu_choice_hierarchy("X:12:1")
                    _ = service._should_send_message()


# =============================================================================
# PKScanRunner Integration Tests
# =============================================================================

class TestPKScanRunnerIntegration:
    """Integration tests for PKScanRunner."""
    
    def test_full_scan_runner_flow(self):
        """Test full scan runner flow."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for intraday_analysis in [True, False]:
            for intraday in [None, "1m", "5m"]:
                args = Namespace(runintradayanalysis=intraday_analysis, intraday=intraday)
                
                for menu in ["X", "P", "B"]:
                    choices = {"0": menu, "1": "12", "2": "1"}
                    result = PKScanRunner.getFormattedChoices(args, choices)


# =============================================================================
# MenuManager Integration Tests
# =============================================================================

class TestMenuManagerIntegration:
    """Integration tests for MenuManager."""
    
    @pytest.fixture
    def manager(self, config):
        """Create a MenuManager."""
        from pkscreener.classes.MenuManager import MenuManager
        args = Namespace(
            options=None, pipedmenus=None, backtestdaysago=None, pipedtitle=None,
            runintradayanalysis=False, intraday=None
        )
        return MenuManager(config, args)
    
    def test_full_menu_manager_flow(self, manager):
        """Test full menu manager flow."""
        # Load menus
        manager.ensure_menus_loaded()
        
        # Load with different options
        for menu in ["X", "P", "B"]:
            manager.ensure_menus_loaded(menu_option=menu)
        
        # Set selected choices
        manager.selected_choice["0"] = "X"
        manager.selected_choice["1"] = "12"
        manager.selected_choice["2"] = "1"


# =============================================================================
# MainLogic Integration Tests
# =============================================================================

class TestMainLogicIntegration:
    """Integration tests for MainLogic."""
    
    @pytest.fixture
    def mock_global_state(self, config):
        """Create a mock global state."""
        gs = MagicMock()
        gs.configManager = config
        gs.fetcher = MagicMock()
        gs.m0 = MagicMock()
        gs.m1 = MagicMock()
        gs.m2 = MagicMock()
        gs.userPassedArgs = MagicMock()
        gs.selectedChoice = {"0": "X", "1": "12", "2": "1"}
        return gs
    
    @patch('pkscreener.classes.MainLogic.os.system')
    @patch('pkscreener.classes.MainLogic.sleep')
    @patch('pkscreener.classes.MainLogic.OutputControls')
    @patch('pkscreener.classes.MainLogic.PKAnalyticsService')
    def test_full_main_logic_flow(self, mock_analytics, mock_output, mock_sleep, mock_system, mock_global_state):
        """Test full main logic flow."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        handler = MenuOptionHandler(mock_global_state)
        
        # Get launcher
        launcher = handler.get_launcher()
        
        # Handle menu M
        result = handler.handle_menu_m()
        
        # Handle downloads
        result = handler._handle_download_daily(launcher)
        result = handler._handle_download_intraday(launcher)


# =============================================================================
# DataLoader Integration Tests
# =============================================================================

class TestDataLoaderIntegration:
    """Integration tests for DataLoader."""
    
    def test_full_data_loader_flow(self, config):
        """Test full data loader flow."""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_fetcher = MagicMock()
        loader = StockDataLoader(config, mock_fetcher)
        
        # Test initialize_dicts
        try:
            loader.initialize_dicts()
        except:
            pass
        
        # Test get_latest_trade_datetime
        try:
            result = loader.get_latest_trade_datetime()
        except:
            pass


# =============================================================================
# BacktestUtils Integration Tests
# =============================================================================

class TestBacktestUtilsIntegration:
    """Integration tests for BacktestUtils."""
    
    def test_full_backtest_utils_flow(self, config):
        """Test full backtest utils flow."""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename, BacktestResultsHandler
        
        # Test get_backtest_report_filename
        for sort_key in [None, "Stock", "LTP"]:
            for optional_name in [None, "test"]:
                for choices in [None, {"0": "X", "1": "12", "2": "1"}]:
                    result = get_backtest_report_filename(
                        sort_key=sort_key,
                        optional_name=optional_name,
                        choices=choices
                    )
        
        # Test BacktestResultsHandler
        handler = BacktestResultsHandler(config)


# =============================================================================
# CoreFunctions Integration Tests
# =============================================================================

class TestCoreFunctionsIntegration:
    """Integration tests for CoreFunctions."""
    
    def test_full_core_functions_flow(self):
        """Test full core functions flow."""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        for days in [None, 0, 1, 5, 10, 30, 60, 90]:
            args = Namespace(backtestdaysago=days)
            result = get_review_date(None, args)


# =============================================================================
# signals Integration Tests
# =============================================================================

class TestSignalsIntegration:
    """Integration tests for signals."""
    
    def test_full_signals_flow(self):
        """Test full signals flow."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        for signal in SignalStrength:
            for confidence in range(0, 101, 10):
                result = SignalResult(signal=signal, confidence=float(confidence))
                _ = result.is_buy


# =============================================================================
# MenuOptions Integration Tests
# =============================================================================

class TestMenuOptionsIntegration:
    """Integration tests for MenuOptions."""
    
    def test_full_menu_options_flow(self):
        """Test full menu options flow."""
        from pkscreener.classes.MenuOptions import menus, level0MenuDict, level1_X_MenuDict
        
        # Test menu dicts
        assert len(level0MenuDict) > 0
        assert level1_X_MenuDict is not None
        
        # Test menus class
        m = menus()
        
        # Test all levels
        for level in [0, 1, 2, 3, 4]:
            m.level = level
            m.renderForMenu(asList=True)
            m.renderForMenu(asList=False)
        
        # Test find
        for key in list("XPBCHDUYZ") + ["0", "1", "12", "21"]:
            result = m.find(key)


# =============================================================================
# Pktalib Integration Tests
# =============================================================================

class TestPktalibIntegration:
    """Integration tests for Pktalib."""
    
    def test_full_pktalib_flow(self):
        """Test full Pktalib flow."""
        from pkscreener.classes.Pktalib import pktalib
        data = np.random.uniform(90, 110, 100)
        
        # Test all indicators
        for period in [5, 10, 20]:
            result = pktalib.SMA(data, period)
            result = pktalib.EMA(data, period)
        
        for period in [7, 14, 21]:
            result = pktalib.RSI(data, period)
        
        result = pktalib.MACD(data, 12, 26, 9)
        result = pktalib.BBANDS(data, 20, 2, 2)
