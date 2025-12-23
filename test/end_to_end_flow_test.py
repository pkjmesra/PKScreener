"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    End-to-end integration tests that mock full application flows.
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
    """Create comprehensive stock DataFrame."""
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
# Full Screening Flow Tests
# =============================================================================

class TestFullScreeningFlow:
    """Test full screening flow with mocked data."""
    
    @pytest.fixture
    def mock_host_ref(self, config, stock_df):
        """Create a mock hostRef for screenStocks."""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        from pkscreener.classes.CandlePatterns import CandlePatterns
        from PKDevTools.classes.log import default_logger
        
        host = MagicMock()
        host.configManager = config
        host.fetcher = MagicMock()
        host.screener = ScreeningStatistics(config, default_logger())
        host.candlePatterns = CandlePatterns()
        host.default_logger = default_logger()
        host.processingCounter = multiprocessing.Value('i', 0)
        host.processingResultsCounter = multiprocessing.Value('i', 0)
        host.objectDictionaryPrimary = {
            'SBIN': stock_df,
            'RELIANCE': stock_df,
            'TCS': stock_df,
        }
        host.objectDictionarySecondary = {}
        
        return host
    
    def test_screening_flow_x_12_1(self, config, mock_host_ref, stock_df):
        """Test screening flow for X:12:1."""
        from pkscreener.classes.StockScreener import StockScreener
        
        screener = StockScreener()
        screener.configManager = config
        
        for stock in ['SBIN', 'RELIANCE', 'TCS']:
            try:
                result = screener.screenStocks(
                    runOption="X:12:1",
                    menuOption="X",
                    exchangeName="NSE",
                    executeOption=1,
                    reversalOption=None,
                    maLength=50,
                    daysForLowestVolume=30,
                    minRSI=0,
                    maxRSI=100,
                    respChartPattern=None,
                    insideBarToLookback=7,
                    totalSymbols=100,
                    shouldCache=True,
                    stock=stock,
                    newlyListedOnly=False,
                    downloadOnly=False,
                    volumeRatio=2.5,
                    testbuild=True,
                    userArgs=Namespace(log=False),
                    hostRef=mock_host_ref,
                    testData=stock_df
                )
            except Exception:
                pass
    
    def test_screening_flow_multiple_execute_options(self, config, mock_host_ref, stock_df):
        """Test screening with multiple execute options."""
        from pkscreener.classes.StockScreener import StockScreener
        
        screener = StockScreener()
        screener.configManager = config
        
        for execute_option in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            try:
                result = screener.screenStocks(
                    runOption=f"X:12:{execute_option}",
                    menuOption="X",
                    exchangeName="NSE",
                    executeOption=execute_option,
                    reversalOption=None,
                    maLength=50,
                    daysForLowestVolume=30,
                    minRSI=0,
                    maxRSI=100,
                    respChartPattern=None,
                    insideBarToLookback=7,
                    totalSymbols=100,
                    shouldCache=True,
                    stock="SBIN",
                    newlyListedOnly=False,
                    downloadOnly=False,
                    volumeRatio=2.5,
                    testbuild=True,
                    userArgs=Namespace(log=False),
                    hostRef=mock_host_ref,
                    testData=stock_df
                )
            except Exception:
                pass


# =============================================================================
# Menu Navigation Flow Tests
# =============================================================================

class TestMenuNavigationFlow:
    """Test menu navigation flows."""
    
    def test_full_menu_navigation_x_branch(self, config):
        """Test full menu navigation for X branch."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        
        navigator = MenuNavigator(config)
        
        # Test with different startup options
        for options in ["X:1:1", "X:5:3", "X:12:1", "X:12:5", "X:12:10"]:
            args = Namespace(intraday=None)
            result = navigator.get_top_level_menu_choices(
                startup_options=options,
                test_build=False,
                download_only=False,
                default_answer="Y",
                user_passed_args=args,
                last_scan_output_stock_codes=None
            )
            assert result is not None
    
    def test_full_menu_navigation_p_branch(self, config):
        """Test full menu navigation for P branch."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        
        navigator = MenuNavigator(config)
        
        # Test P (Piped) menu
        for options in ["P:1", "P:5", "P:10"]:
            args = Namespace(intraday=None)
            result = navigator.get_top_level_menu_choices(
                startup_options=options,
                test_build=False,
                download_only=False,
                default_answer="Y",
                user_passed_args=args,
                last_scan_output_stock_codes=None
            )
            assert result is not None
    
    def test_full_menu_navigation_b_branch(self, config):
        """Test full menu navigation for B branch."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        
        navigator = MenuNavigator(config)
        
        # Test B (Backtest) menu
        for options in ["B:1:1", "B:5:3", "B:12:1"]:
            args = Namespace(intraday=None)
            result = navigator.get_top_level_menu_choices(
                startup_options=options,
                test_build=False,
                download_only=False,
                default_answer="Y",
                user_passed_args=args,
                last_scan_output_stock_codes=None
            )
            assert result is not None


# =============================================================================
# ExecuteOption Handler Flow Tests
# =============================================================================

class TestExecuteOptionFlow:
    """Test execute option handler flows."""
    
    def test_execute_option_3_flow(self, config):
        """Test execute option 3 flow."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_3
        
        for max_results in [10, 50, 100, 500, 1000, 5000]:
            args = MagicMock()
            args.maxdisplayresults = max_results
            result = handle_execute_option_3(args, config)
            # Result may be max_results or config default
            assert result is not None
    
    def test_execute_option_4_flow(self):
        """Test execute option 4 flow."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_4
        
        # Numeric inputs
        for days in [7, 14, 21, 30, 45, 60, 90]:
            result = handle_execute_option_4(4, ["X", "12", "4", str(days)])
            assert result == days
        
        # Default input
        result = handle_execute_option_4(4, ["X", "12", "4", "D"])
        assert result == 30
    
    def test_execute_option_5_flow(self):
        """Test execute option 5 flow."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_5
        
        args = MagicMock()
        args.systemlaunched = False
        m2 = MagicMock()
        m2.find.return_value = MagicMock()
        
        # Various RSI ranges
        test_cases = [
            (30, 70), (40, 80), (20, 90), (50, 60), (60, 75)
        ]
        
        for min_rsi, max_rsi in test_cases:
            result_min, result_max = handle_execute_option_5(
                ["X", "12", "5", str(min_rsi), str(max_rsi)], args, m2
            )
            assert result_min == min_rsi
            assert result_max == max_rsi
    
    def test_execute_option_5_default_flow(self):
        """Test execute option 5 with defaults."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_5
        
        args = MagicMock()
        args.systemlaunched = True
        m2 = MagicMock()
        m2.find.return_value = MagicMock()
        
        result_min, result_max = handle_execute_option_5(
            ["X", "12", "5", "D", "D"], args, m2
        )
        assert result_min == 60
        assert result_max == 75


# =============================================================================
# ResultsLabeler Flow Tests
# =============================================================================

class TestResultsLabelerFlow:
    """Test results labeler flows."""
    
    def test_results_labeler_creation_flow(self, config):
        """Test ResultsLabeler creation flow."""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(config)
        assert labeler is not None
        assert hasattr(labeler, 'config_manager')


# =============================================================================
# PKScanRunner Flow Tests
# =============================================================================

class TestPKScanRunnerFlow:
    """Test PKScanRunner flows."""
    
    def test_get_formatted_choices_flow(self):
        """Test getFormattedChoices flow."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        # Without intraday
        args = Namespace(runintradayanalysis=False, intraday=None)
        
        for choice_0 in ["X", "P", "B"]:
            for choice_1 in ["1", "5", "12"]:
                for choice_2 in ["0", "1", "5", "10"]:
                    choices = {"0": choice_0, "1": choice_1, "2": choice_2}
                    result = PKScanRunner.getFormattedChoices(args, choices)
                    assert isinstance(result, str)
                    assert "_IA" not in result
    
    def test_get_formatted_choices_intraday_flow(self):
        """Test getFormattedChoices with intraday flow."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        # With intraday
        args = Namespace(runintradayanalysis=True, intraday=None)
        
        for choice_0 in ["X", "P", "B"]:
            choices = {"0": choice_0, "1": "12", "2": "1"}
            result = PKScanRunner.getFormattedChoices(args, choices)
            assert "_IA" in result


# =============================================================================
# NotificationService Flow Tests
# =============================================================================

class TestNotificationServiceFlow:
    """Test notification service flows."""
    
    def test_notification_service_flow(self):
        """Test NotificationService flow."""
        from pkscreener.classes.NotificationService import NotificationService
        
        # Test with various configurations
        configs = [
            Namespace(telegram=False, log=True, user="12345", monitor=None),
            Namespace(telegram=True, log=False, user=None, monitor=None),
            Namespace(telegram=False, log=False, user="67890", monitor=None),
        ]
        
        for args in configs:
            service = NotificationService(args)
            service.set_menu_choice_hierarchy("X:12:1")
            _ = service._should_send_message()


# =============================================================================
# DataLoader Flow Tests
# =============================================================================

class TestDataLoaderFlow:
    """Test data loader flows."""
    
    def test_stock_data_loader_flow(self, config):
        """Test StockDataLoader flow."""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_fetcher = MagicMock()
        loader = StockDataLoader(config, mock_fetcher)
        
        assert loader is not None
        assert hasattr(loader, 'initialize_dicts')
        assert hasattr(loader, 'get_latest_trade_datetime')


# =============================================================================
# BacktestHandler Flow Tests
# =============================================================================

class TestBacktestHandlerFlow:
    """Test backtest handler flows."""
    
    def test_backtest_handler_flow(self, config):
        """Test BacktestHandler flow."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        
        handler = BacktestHandler(config)
        
        assert handler is not None
        assert hasattr(handler, 'config_manager')


# =============================================================================
# BacktestUtils Flow Tests
# =============================================================================

class TestBacktestUtilsFlow:
    """Test backtest utils flows."""
    
    def test_get_backtest_report_filename_flow(self):
        """Test get_backtest_report_filename flow."""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        # All parameter combinations
        for sort_key in [None, "Stock", "LTP", "%Chng"]:
            for optional_name in [None, "test", "report"]:
                result = get_backtest_report_filename(
                    sort_key=sort_key,
                    optional_name=optional_name
                )
                assert result is not None
    
    def test_backtest_results_handler_flow(self, config):
        """Test BacktestResultsHandler flow."""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        handler = BacktestResultsHandler(config)
        
        assert handler is not None


# =============================================================================
# signals Flow Tests
# =============================================================================

class TestSignalsFlow:
    """Test signals module flows."""
    
    def test_signal_result_flow(self):
        """Test SignalResult flow."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        # Test all signal types
        for signal_type in SignalStrength:
            for confidence in [0, 25, 50, 75, 100]:
                result = SignalResult(signal=signal_type, confidence=float(confidence))
                
                assert result.signal == signal_type
                assert result.confidence == float(confidence)
                _ = result.is_buy


# =============================================================================
# CoreFunctions Flow Tests
# =============================================================================

class TestCoreFunctionsFlow:
    """Test core functions flows."""
    
    def test_get_review_date_flow(self):
        """Test get_review_date flow."""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        # Test various backtestdaysago values
        for days in [None, 0, 1, 5, 10, 30, 60, 90]:
            args = Namespace(backtestdaysago=days)
            result = get_review_date(None, args)
            if days and days > 0:
                assert result is not None


# =============================================================================
# MenuManager Flow Tests
# =============================================================================

class TestMenuManagerFlow:
    """Test menu manager flows."""
    
    def test_menu_manager_full_flow(self, config):
        """Test MenuManager full flow."""
        from pkscreener.classes.MenuManager import MenuManager
        
        args = Namespace(
            options=None, pipedmenus=None, backtestdaysago=None, pipedtitle=None,
            runintradayanalysis=False, intraday=None
        )
        
        manager = MenuManager(config, args)
        
        # Test menu loading
        manager.ensure_menus_loaded()
        manager.ensure_menus_loaded(menu_option="X")
        manager.ensure_menus_loaded(menu_option="X", index_option="12")
        manager.ensure_menus_loaded(menu_option="X", index_option="12", execute_option="1")
        
        # Test selected_choice manipulation
        manager.selected_choice["0"] = "X"
        manager.selected_choice["1"] = "12"
        manager.selected_choice["2"] = "1"
        
        assert manager.selected_choice["0"] == "X"


# =============================================================================
# MainLogic Flow Tests
# =============================================================================

class TestMainLogicFlow:
    """Test main logic flows."""
    
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
    def test_menu_option_handler_flow(self, mock_analytics, mock_output, mock_sleep, mock_system, mock_global_state):
        """Test MenuOptionHandler flow."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        
        handler = MenuOptionHandler(mock_global_state)
        
        # Test all methods
        launcher = handler.get_launcher()
        assert isinstance(launcher, str)
        
        result = handler.handle_menu_m()
        assert result == (None, None)
        
        result = handler._handle_download_daily(launcher)
        assert result == (None, None)
        
        result = handler._handle_download_intraday(launcher)
        assert result == (None, None)
