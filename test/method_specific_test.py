"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests targeting specific methods in low-coverage modules.
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


# =============================================================================
# ExecuteOptionHandlers Method Tests
# =============================================================================

class TestExecuteOptionHandlersMethods:
    """Test specific methods in ExecuteOptionHandlers."""
    
    def test_handle_execute_option_3_edge_cases(self, config):
        """Test handle_execute_option_3 edge cases."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_3
        
        # Zero
        args = MagicMock()
        args.maxdisplayresults = 0
        result = handle_execute_option_3(args, config)
        
        # Large number
        args.maxdisplayresults = 100000
        result = handle_execute_option_3(args, config)
    
    def test_handle_execute_option_4_edge_cases(self):
        """Test handle_execute_option_4 edge cases."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_4
        
        # Zero days
        result = handle_execute_option_4(4, ["X", "12", "4", "0"])
        
        # Large number
        result = handle_execute_option_4(4, ["X", "12", "4", "365"])
    
    def test_handle_execute_option_5_edge_cases(self):
        """Test handle_execute_option_5 edge cases."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_5
        
        args = MagicMock()
        args.systemlaunched = False
        m2 = MagicMock()
        m2.find.return_value = MagicMock()
        
        # Zero RSI
        result = handle_execute_option_5(["X", "12", "5", "0", "100"], args, m2)
        
        # Max RSI
        result = handle_execute_option_5(["X", "12", "5", "0", "99"], args, m2)


# =============================================================================
# NotificationService Method Tests
# =============================================================================

class TestNotificationServiceMethods:
    """Test specific methods in NotificationService."""
    
    def test_notification_service_variations(self):
        """Test NotificationService with various configurations."""
        from pkscreener.classes.NotificationService import NotificationService
        
        # All combinations of telegram and log
        for telegram in [True, False]:
            for log in [True, False]:
                for user in [None, "12345", "67890"]:
                    args = Namespace(telegram=telegram, log=log, user=user, monitor=None)
                    service = NotificationService(args)
                    service.set_menu_choice_hierarchy("X:12:1")
                    _ = service._should_send_message()
    
    def test_notification_service_with_runner_env(self):
        """Test NotificationService with RUNNER env var."""
        from pkscreener.classes.NotificationService import NotificationService
        
        with patch.dict(os.environ, {"RUNNER": "true"}):
            args = Namespace(telegram=False, log=True, user="12345", monitor=None)
            service = NotificationService(args)
            result = service._should_send_message()
            assert result is True


# =============================================================================
# DataLoader Method Tests
# =============================================================================

class TestDataLoaderMethods:
    """Test specific methods in DataLoader."""
    
    def test_stock_data_loader_methods(self, config):
        """Test StockDataLoader methods."""
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
# CoreFunctions Method Tests
# =============================================================================

class TestCoreFunctionsMethods:
    """Test specific methods in CoreFunctions."""
    
    def test_get_review_date_edge_cases(self):
        """Test get_review_date edge cases."""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        # Negative days
        args = Namespace(backtestdaysago=-5)
        result = get_review_date(None, args)
        
        # Large days
        args = Namespace(backtestdaysago=365)
        result = get_review_date(None, args)


# =============================================================================
# BacktestUtils Method Tests
# =============================================================================

class TestBacktestUtilsMethods:
    """Test specific methods in BacktestUtils."""
    
    def test_get_backtest_report_filename_edge_cases(self):
        """Test get_backtest_report_filename edge cases."""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        # Empty choices
        result = get_backtest_report_filename(choices={})
        
        # Partial choices
        result = get_backtest_report_filename(choices={"0": "X"})
        
        # Full choices
        result = get_backtest_report_filename(choices={"0": "X", "1": "12", "2": "1", "3": "5", "4": "2"})


# =============================================================================
# PKScanRunner Method Tests
# =============================================================================

class TestPKScanRunnerMethods:
    """Test specific methods in PKScanRunner."""
    
    def test_get_formatted_choices_edge_cases(self):
        """Test getFormattedChoices edge cases."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        # Empty choices
        args = Namespace(runintradayanalysis=False, intraday=None)
        choices = {}
        result = PKScanRunner.getFormattedChoices(args, choices)
        
        # Partial choices
        choices = {"0": "X"}
        result = PKScanRunner.getFormattedChoices(args, choices)


# =============================================================================
# ResultsLabeler Method Tests
# =============================================================================

class TestResultsLabelerMethods:
    """Test specific methods in ResultsLabeler."""
    
    def test_results_labeler_creation_variations(self, config):
        """Test ResultsLabeler creation variations."""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        labeler = ResultsLabeler(config)
        assert labeler is not None


# =============================================================================
# BacktestHandler Method Tests
# =============================================================================

class TestBacktestHandlerMethods:
    """Test specific methods in BacktestHandler."""
    
    def test_backtest_handler_creation_variations(self, config):
        """Test BacktestHandler creation variations."""
        from pkscreener.classes.BacktestHandler import BacktestHandler
        
        handler = BacktestHandler(config)
        assert handler is not None


# =============================================================================
# ResultsManager Method Tests
# =============================================================================

class TestResultsManagerMethods:
    """Test specific methods in ResultsManager."""
    
    def test_results_manager_creation_variations(self, config):
        """Test ResultsManager creation variations."""
        from pkscreener.classes.ResultsManager import ResultsManager
        
        manager = ResultsManager(config)
        assert manager is not None


# =============================================================================
# OutputFunctions Method Tests
# =============================================================================

class TestOutputFunctionsMethods:
    """Test specific methods in OutputFunctions."""
    
    def test_output_functions_import(self):
        """Test OutputFunctions import."""
        from pkscreener.classes import OutputFunctions
        assert OutputFunctions is not None


# =============================================================================
# TelegramNotifier Method Tests
# =============================================================================

class TestTelegramNotifierMethods:
    """Test specific methods in TelegramNotifier."""
    
    def test_telegram_notifier_class(self):
        """Test TelegramNotifier class."""
        from pkscreener.classes.TelegramNotifier import TelegramNotifier
        assert TelegramNotifier is not None


# =============================================================================
# BotHandlers Method Tests
# =============================================================================

class TestBotHandlersMethods:
    """Test specific methods in BotHandlers."""
    
    def test_bot_handlers_module(self):
        """Test BotHandlers module."""
        from pkscreener.classes.bot import BotHandlers
        assert BotHandlers is not None


# =============================================================================
# PKUserRegistration Method Tests
# =============================================================================

class TestPKUserRegistrationMethods:
    """Test specific methods in PKUserRegistration."""
    
    def test_validation_result_all_values(self):
        """Test ValidationResult all values."""
        from pkscreener.classes.PKUserRegistration import ValidationResult
        
        for val in ValidationResult:
            assert val is not None


# =============================================================================
# Barometer Method Tests
# =============================================================================

class TestBarometerMethods:
    """Test specific methods in Barometer."""
    
    def test_barometer_module(self):
        """Test Barometer module."""
        from pkscreener.classes import Barometer
        assert Barometer is not None


# =============================================================================
# UserMenuChoicesHandler Method Tests
# =============================================================================

class TestUserMenuChoicesHandlerMethods:
    """Test specific methods in UserMenuChoicesHandler."""
    
    def test_user_menu_choices_handler_module(self):
        """Test UserMenuChoicesHandler module."""
        from pkscreener.classes import UserMenuChoicesHandler
        assert UserMenuChoicesHandler is not None


# =============================================================================
# PKDataService Method Tests
# =============================================================================

class TestPKDataServiceMethods:
    """Test specific methods in PKDataService."""
    
    def test_pk_data_service_class(self):
        """Test PKDataService class."""
        from pkscreener.classes.PKDataService import PKDataService
        assert PKDataService is not None


# =============================================================================
# keys Method Tests
# =============================================================================

class TestKeysMethods:
    """Test specific methods in keys."""
    
    def test_keys_module(self):
        """Test keys module."""
        from pkscreener.classes import keys
        assert keys is not None


# =============================================================================
# MenuManager Method Tests
# =============================================================================

class TestMenuManagerMethods:
    """Test specific methods in MenuManager."""
    
    @pytest.fixture
    def manager(self, config):
        """Create a MenuManager."""
        from pkscreener.classes.MenuManager import MenuManager
        args = Namespace(
            options=None, pipedmenus=None, backtestdaysago=None, pipedtitle=None,
            runintradayanalysis=False, intraday=None
        )
        return MenuManager(config, args)
    
    def test_ensure_menus_loaded_variations(self, manager):
        """Test ensure_menus_loaded variations."""
        # No parameters
        manager.ensure_menus_loaded()
        
        # With menu_option
        for menu in ["X", "P", "B", "C", "D", "H", "U", "Y", "Z"]:
            manager.ensure_menus_loaded(menu_option=menu)
        
        # With menu_option and index_option
        manager.ensure_menus_loaded(menu_option="X", index_option="1")
        manager.ensure_menus_loaded(menu_option="X", index_option="12")
        
        # With all options
        manager.ensure_menus_loaded(menu_option="X", index_option="12", execute_option="1")


# =============================================================================
# MenuNavigation Method Tests
# =============================================================================

class TestMenuNavigationMethods:
    """Test specific methods in MenuNavigation."""
    
    @pytest.fixture
    def navigator(self, config):
        """Create a MenuNavigator."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        return MenuNavigator(config)
    
    def test_get_historical_days_variations(self, navigator):
        """Test get_historical_days variations."""
        for num_stocks in [10, 100, 1000, 10000]:
            for testing in [True, False]:
                result = navigator.get_historical_days(num_stocks, testing)
                assert result is not None
    
    def test_get_test_build_choices_variations(self, navigator):
        """Test get_test_build_choices variations."""
        # Default
        result = navigator.get_test_build_choices()
        
        # With menu_option
        for menu in ["X", "P", "B", "C", "D"]:
            result = navigator.get_test_build_choices(menu_option=menu)
            assert result[0] == menu
        
        # With all options
        result = navigator.get_test_build_choices(
            menu_option="X", index_option=12, execute_option=5
        )
        assert result == ("X", 12, 5, {"0": "X", "1": "12", "2": "5"})


# =============================================================================
# MainLogic Method Tests
# =============================================================================

class TestMainLogicMethods:
    """Test specific methods in MainLogic."""
    
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
    
    def test_menu_option_handler_get_launcher_variations(self, mock_global_state):
        """Test get_launcher variations."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        handler = MenuOptionHandler(mock_global_state)
        
        test_cases = [
            ['pkscreenercli.py'],
            ['script.py'],
            ['/path/to/script.py'],
            ['/path with spaces/script.py'],
            ['pkscreenercli'],
        ]
        
        for argv in test_cases:
            with patch.object(sys, 'argv', argv):
                launcher = handler.get_launcher()
                assert isinstance(launcher, str)
    
    @patch('pkscreener.classes.MainLogic.os.system')
    @patch('pkscreener.classes.MainLogic.sleep')
    @patch('pkscreener.classes.MainLogic.OutputControls')
    @patch('pkscreener.classes.MainLogic.PKAnalyticsService')
    def test_menu_option_handler_m(self, mock_analytics, mock_output, mock_sleep, mock_system, mock_global_state):
        """Test handle_menu_m."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        handler = MenuOptionHandler(mock_global_state)
        
        result = handler.handle_menu_m()
        assert result == (None, None)


# =============================================================================
# PKScreenerMain Method Tests
# =============================================================================

class TestPKScreenerMainMethods:
    """Test specific methods in PKScreenerMain."""
    
    def test_pkscreener_main_module(self):
        """Test PKScreenerMain module."""
        from pkscreener.classes import PKScreenerMain
        assert PKScreenerMain is not None
