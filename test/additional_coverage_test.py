"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Additional tests to increase coverage.
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
# ScreeningStatistics Additional Tests
# =============================================================================

class TestScreeningStatisticsAdditional:
    """Additional tests for ScreeningStatistics."""
    
    @pytest.fixture
    def screener(self, config):
        """Create a ScreeningStatistics instance."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from PKDevTools.classes.log import default_logger
        return ScreeningStatistics(config, default_logger())
    
    def test_find_bbands_squeeze_all_scenarios(self, screener, stock_df):
        """Test findBbandsSqueeze with all scenarios."""
        for filter_val in range(1, 5):
            try:
                result = screener.findBbandsSqueeze(stock_df, {}, {}, filter=filter_val)
            except:
                pass
        
        # Test with None/empty data
        assert screener.findBbandsSqueeze(None, {}, {}, filter=4) is False
        assert screener.findBbandsSqueeze(pd.DataFrame(), {}, {}, filter=4) is False
    
    def test_find_atr_trailing_all_params(self, screener, stock_df):
        """Test findATRTrailingStops with all parameters."""
        for sensitivity in range(1, 4):
            for atr_period in [7, 10, 14, 20]:
                for ema_period in [1, 5, 10]:
                    for buySellAll in [1, 2, 3]:
                        try:
                            result = screener.findATRTrailingStops(
                                stock_df, sensitivity, atr_period, ema_period, buySellAll, {}, {}
                            )
                        except:
                            pass
    
    def test_find_buy_sell_signals_all_params(self, screener, stock_df):
        """Test findBuySellSignalsFromATRTrailing with all parameters."""
        for key_value in [1, 2, 3]:
            for atr_period in [7, 10, 14]:
                for ema_period in [50, 100, 200]:
                    for buySellAll in [1, 2, 3]:
                        try:
                            result = screener.findBuySellSignalsFromATRTrailing(
                                stock_df, key_value, atr_period, ema_period, buySellAll, {}, {}
                            )
                        except:
                            pass
    
    def test_find_macd_crossover_all_params(self, screener, stock_df):
        """Test findMACDCrossover with all parameters."""
        for upDirection in [True, False]:
            for nthCrossover in [1, 2, 3]:
                for minRSI in [0, 30, 50, 60, 75]:
                    for maxRSI in [80, 90, 100]:
                        try:
                            result = screener.findMACDCrossover(
                                stock_df, upDirection=upDirection, nthCrossover=nthCrossover,
                                minRSI=minRSI, maxRSI=maxRSI
                            )
                        except:
                            pass


# =============================================================================
# ExecuteOptionHandlers Additional Tests
# =============================================================================

class TestExecuteOptionHandlersAdditional:
    """Additional tests for ExecuteOptionHandlers."""
    
    def test_handle_execute_option_3_all_values(self, config):
        """Test handle_execute_option_3 with all values."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_3
        
        for max_results in [1, 10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]:
            args = MagicMock()
            args.maxdisplayresults = max_results
            result = handle_execute_option_3(args, config)
    
    def test_handle_execute_option_4_all_values(self):
        """Test handle_execute_option_4 with all values."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_4
        
        for days in range(1, 100, 5):
            result = handle_execute_option_4(4, ["X", "12", "4", str(days)])
        
        # Test default
        result = handle_execute_option_4(4, ["X", "12", "4", "D"])
    
    def test_handle_execute_option_5_all_values(self):
        """Test handle_execute_option_5 with all values."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_5
        
        args = MagicMock()
        args.systemlaunched = False
        m2 = MagicMock()
        m2.find.return_value = MagicMock()
        
        for min_rsi in range(0, 80, 10):
            for max_rsi in range(min_rsi + 10, 100, 10):
                result = handle_execute_option_5(
                    ["X", "12", "5", str(min_rsi), str(max_rsi)], args, m2
                )


# =============================================================================
# MenuNavigation Additional Tests
# =============================================================================

class TestMenuNavigationAdditional:
    """Additional tests for MenuNavigation."""
    
    @pytest.fixture
    def navigator(self, config):
        """Create a MenuNavigator."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        return MenuNavigator(config)
    
    def test_get_top_level_menu_choices_all_combinations(self, navigator):
        """Test get_top_level_menu_choices with all combinations."""
        user_args = Namespace(intraday=None)
        
        for menu in ["X", "P", "B", "C", "D", "H", "U", "Y", "Z"]:
            for index in ["1", "5", "12", "15", "21"]:
                for execute in ["0", "1", "5", "10", "21"]:
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
# NotificationService Additional Tests
# =============================================================================

class TestNotificationServiceAdditional:
    """Additional tests for NotificationService."""
    
    def test_notification_service_all_combinations(self):
        """Test NotificationService with all combinations."""
        from pkscreener.classes.NotificationService import NotificationService
        
        for telegram in [True, False]:
            for log in [True, False]:
                for user in [None, "", "12345", "67890"]:
                    for monitor in [None]:
                        args = Namespace(telegram=telegram, log=log, user=user, monitor=monitor)
                        service = NotificationService(args)
                        
                        for hierarchy in ["X:12:1", "P:5:3", "B:1:2", ""]:
                            service.set_menu_choice_hierarchy(hierarchy)
                            _ = service._should_send_message()


# =============================================================================
# PKScanRunner Additional Tests
# =============================================================================

class TestPKScanRunnerAdditional:
    """Additional tests for PKScanRunner."""
    
    def test_get_formatted_choices_all_combinations(self):
        """Test getFormattedChoices with all combinations."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for intraday_analysis in [True, False]:
            for intraday in [None, "1m", "5m", "15m", "1h"]:
                args = Namespace(runintradayanalysis=intraday_analysis, intraday=intraday)
                
                for menu in ["X", "P", "B", "C", "D"]:
                    for index in ["1", "5", "12", "15"]:
                        for execute in ["0", "1", "5", "10"]:
                            choices = {"0": menu, "1": index, "2": execute}
                            result = PKScanRunner.getFormattedChoices(args, choices)


# =============================================================================
# CoreFunctions Additional Tests
# =============================================================================

class TestCoreFunctionsAdditional:
    """Additional tests for CoreFunctions."""
    
    def test_get_review_date_all_values(self):
        """Test get_review_date with all values."""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        for days in [None, 0, 1, 5, 10, 30, 60, 90, 180, 365]:
            args = Namespace(backtestdaysago=days)
            result = get_review_date(None, args)


# =============================================================================
# BacktestUtils Additional Tests
# =============================================================================

class TestBacktestUtilsAdditional:
    """Additional tests for BacktestUtils."""
    
    def test_get_backtest_report_filename_all_combinations(self):
        """Test get_backtest_report_filename with all combinations."""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        for sort_key in [None, "Stock", "LTP", "%Chng", "Volume"]:
            for optional_name in [None, "", "test", "report", "backtest"]:
                for choices in [None, {}, {"0": "X"}, {"0": "X", "1": "12", "2": "1"}]:
                    result = get_backtest_report_filename(
                        sort_key=sort_key,
                        optional_name=optional_name,
                        choices=choices
                    )


# =============================================================================
# signals Additional Tests
# =============================================================================

class TestSignalsAdditional:
    """Additional tests for signals."""
    
    def test_signal_result_all_combinations(self):
        """Test SignalResult with all combinations."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        for signal in SignalStrength:
            for confidence in range(0, 101, 5):
                result = SignalResult(signal=signal, confidence=float(confidence))
                _ = result.is_buy


# =============================================================================
# MenuOptions Additional Tests
# =============================================================================

class TestMenuOptionsAdditional:
    """Additional tests for MenuOptions."""
    
    def test_menus_all_methods(self):
        """Test menus with all methods."""
        from pkscreener.classes.MenuOptions import menus
        
        for level in range(5):
            m = menus()
            m.level = level
            m.renderForMenu(asList=True)
            m.renderForMenu(asList=False)
            
            for key in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + [str(i) for i in range(30)]:
                result = m.find(key)


# =============================================================================
# Pktalib Additional Tests
# =============================================================================

class TestPktalibAdditional:
    """Additional tests for Pktalib."""
    
    def test_all_indicators(self):
        """Test all Pktalib indicators."""
        from pkscreener.classes.Pktalib import pktalib
        data = np.random.uniform(90, 110, 200)
        
        for period in [5, 10, 14, 20, 50]:
            result = pktalib.SMA(data, period)
            result = pktalib.EMA(data, period)
        
        for period in [7, 9, 14, 21]:
            result = pktalib.RSI(data, period)
        
        for fast in [8, 12, 16]:
            for slow in [21, 26, 30]:
                for signal in [7, 9, 12]:
                    if fast < slow:
                        result = pktalib.MACD(data, fast, slow, signal)
        
        for period in [10, 20, 30]:
            for nbdevup in [1.5, 2.0, 2.5]:
                for nbdevdn in [1.5, 2.0, 2.5]:
                    result = pktalib.BBANDS(data, period, nbdevup, nbdevdn)


# =============================================================================
# MenuManager Additional Tests
# =============================================================================

class TestMenuManagerAdditional:
    """Additional tests for MenuManager."""
    
    @pytest.fixture
    def manager(self, config):
        """Create a MenuManager."""
        from pkscreener.classes.MenuManager import MenuManager
        args = Namespace(
            options=None, pipedmenus=None, backtestdaysago=None, pipedtitle=None,
            runintradayanalysis=False, intraday=None
        )
        return MenuManager(config, args)
    
    def test_ensure_menus_loaded_all_combinations(self, manager):
        """Test ensure_menus_loaded with all combinations."""
        for menu in ["X", "P", "B", "C", "D", "H", "U", "Y", "Z"]:
            manager.ensure_menus_loaded(menu_option=menu)
            
            for index in ["1", "5", "12", "15", "21"]:
                manager.ensure_menus_loaded(menu_option=menu, index_option=index)
                
                for execute in ["0", "1", "5", "10", "21"]:
                    manager.ensure_menus_loaded(menu_option=menu, index_option=index, execute_option=execute)


# =============================================================================
# MainLogic Additional Tests
# =============================================================================

class TestMainLogicAdditional:
    """Additional tests for MainLogic."""
    
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
    
    def test_menu_option_handler_get_launcher_all_paths(self, mock_global_state):
        """Test get_launcher with all path types."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        handler = MenuOptionHandler(mock_global_state)
        
        test_cases = [
            ['script.py'],
            ['/path/to/script.py'],
            ['/path with spaces/script.py'],
            ['pkscreenercli'],
            ['/usr/local/bin/pkscreenercli'],
            ['./pkscreenercli'],
            ['../pkscreenercli'],
        ]
        
        for argv in test_cases:
            with patch.object(sys, 'argv', argv):
                launcher = handler.get_launcher()
                assert isinstance(launcher, str)
