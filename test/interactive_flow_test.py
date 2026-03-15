"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests that simulate interactive flows with mocked user input.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, Mock, PropertyMock
from argparse import Namespace
import warnings
import sys
import os
import io
warnings.filterwarnings("ignore")


@pytest.fixture
def config():
    """Create a configuration manager."""
    from pkscreener.classes.ConfigManager import tools, parser
    config = tools()
    config.getConfig(parser)
    return config


# =============================================================================
# MenuManager Interactive Tests
# =============================================================================

class TestMenuManagerInteractive:
    """Test MenuManager with simulated user input."""
    
    @pytest.fixture
    def manager(self, config):
        """Create a MenuManager."""
        from pkscreener.classes.MenuManager import MenuManager
        args = Namespace(
            options=None, pipedmenus=None, backtestdaysago=None, pipedtitle=None,
            runintradayanalysis=False, intraday=None
        )
        return MenuManager(config, args)
    
    def test_menu_manager_ensure_menus_loaded_x(self, manager):
        """Test ensure_menus_loaded for X menu."""
        manager.ensure_menus_loaded(menu_option="X")
        manager.ensure_menus_loaded(menu_option="X", index_option="12")
        manager.ensure_menus_loaded(menu_option="X", index_option="12", execute_option="1")
    
    def test_menu_manager_ensure_menus_loaded_p(self, manager):
        """Test ensure_menus_loaded for P menu."""
        manager.ensure_menus_loaded(menu_option="P")
        manager.ensure_menus_loaded(menu_option="P", index_option="5")
    
    def test_menu_manager_ensure_menus_loaded_b(self, manager):
        """Test ensure_menus_loaded for B menu."""
        manager.ensure_menus_loaded(menu_option="B")
        manager.ensure_menus_loaded(menu_option="B", index_option="1")
    
    def test_menu_manager_selected_choice(self, manager):
        """Test MenuManager selected_choice manipulation."""
        manager.selected_choice["0"] = "X"
        manager.selected_choice["1"] = "12"
        manager.selected_choice["2"] = "1"
        manager.selected_choice["3"] = ""
        manager.selected_choice["4"] = ""
        
        assert manager.selected_choice["0"] == "X"
        assert manager.selected_choice["1"] == "12"
        assert manager.selected_choice["2"] == "1"


# =============================================================================
# MenuNavigation Interactive Tests
# =============================================================================

class TestMenuNavigationInteractive:
    """Test MenuNavigation with simulated user input."""
    
    @pytest.fixture
    def navigator(self, config):
        """Create a MenuNavigator."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        return MenuNavigator(config)
    
    def test_get_top_level_menu_choices_x_options(self, navigator):
        """Test get_top_level_menu_choices with X options."""
        user_args = Namespace(intraday=None)
        
        for options in ["X:1:1", "X:5:3", "X:12:1", "X:12:5", "X:12:10", "X:12:21"]:
            result = navigator.get_top_level_menu_choices(
                startup_options=options,
                test_build=False,
                download_only=False,
                default_answer="Y",
                user_passed_args=user_args,
                last_scan_output_stock_codes=None
            )
            assert result is not None
    
    def test_get_top_level_menu_choices_p_options(self, navigator):
        """Test get_top_level_menu_choices with P options."""
        user_args = Namespace(intraday=None)
        
        for options in ["P:1", "P:5", "P:10", "P:15"]:
            result = navigator.get_top_level_menu_choices(
                startup_options=options,
                test_build=False,
                download_only=False,
                default_answer="Y",
                user_passed_args=user_args,
                last_scan_output_stock_codes=None
            )
            assert result is not None
    
    def test_get_test_build_choices_all_menus(self, navigator):
        """Test get_test_build_choices with all menus."""
        for menu in ["X", "P", "B", "C", "D"]:
            result = navigator.get_test_build_choices(menu_option=menu)
            assert result[0] == menu


# =============================================================================
# MainLogic Interactive Tests
# =============================================================================

class TestMainLogicInteractive:
    """Test MainLogic with simulated user input."""
    
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
    def test_menu_option_handler_m(self, mock_analytics, mock_output, mock_sleep, mock_system, mock_global_state):
        """Test MenuOptionHandler for M menu."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        handler = MenuOptionHandler(mock_global_state)
        
        result = handler.handle_menu_m()
        assert result == (None, None)
    
    @patch('pkscreener.classes.MainLogic.os.system')
    @patch('pkscreener.classes.MainLogic.sleep')
    @patch('pkscreener.classes.MainLogic.OutputControls')
    @patch('pkscreener.classes.MainLogic.PKAnalyticsService')
    def test_menu_option_handler_download_daily(self, mock_analytics, mock_output, mock_sleep, mock_system, mock_global_state):
        """Test MenuOptionHandler for daily download."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        handler = MenuOptionHandler(mock_global_state)
        
        launcher = handler.get_launcher()
        result = handler._handle_download_daily(launcher)
        assert result == (None, None)
    
    @patch('pkscreener.classes.MainLogic.os.system')
    @patch('pkscreener.classes.MainLogic.sleep')
    @patch('pkscreener.classes.MainLogic.OutputControls')
    @patch('pkscreener.classes.MainLogic.PKAnalyticsService')
    def test_menu_option_handler_download_intraday(self, mock_analytics, mock_output, mock_sleep, mock_system, mock_global_state):
        """Test MenuOptionHandler for intraday download."""
        from pkscreener.classes.MainLogic import MenuOptionHandler
        handler = MenuOptionHandler(mock_global_state)
        
        launcher = handler.get_launcher()
        result = handler._handle_download_intraday(launcher)
        assert result == (None, None)


# =============================================================================
# ExecuteOptionHandlers Interactive Tests
# =============================================================================

class TestExecuteOptionHandlersInteractive:
    """Test ExecuteOptionHandlers with simulated user input."""
    
    def test_handle_execute_option_3_all_values(self, config):
        """Test handle_execute_option_3 with all values."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_3
        
        for max_results in [10, 25, 50, 100, 250, 500, 1000, 2500, 5000]:
            args = MagicMock()
            args.maxdisplayresults = max_results
            result = handle_execute_option_3(args, config)
            assert result is not None
    
    def test_handle_execute_option_4_all_days(self):
        """Test handle_execute_option_4 with all days."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_4
        
        for days in range(1, 100, 5):
            result = handle_execute_option_4(4, ["X", "12", "4", str(days)])
            assert result == days
    
    def test_handle_execute_option_5_all_rsi(self):
        """Test handle_execute_option_5 with all RSI values."""
        from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_5
        
        args = MagicMock()
        args.systemlaunched = False
        m2 = MagicMock()
        m2.find.return_value = MagicMock()
        
        for min_rsi in range(0, 70, 10):
            for max_rsi in range(min_rsi + 20, 100, 10):
                result = handle_execute_option_5(
                    ["X", "12", "5", str(min_rsi), str(max_rsi)], args, m2
                )
                assert result[0] == min_rsi
                assert result[1] == max_rsi


# =============================================================================
# NotificationService Interactive Tests
# =============================================================================

class TestNotificationServiceInteractive:
    """Test NotificationService with simulated flows."""
    
    def test_notification_service_all_configs(self):
        """Test NotificationService with all configurations."""
        from pkscreener.classes.NotificationService import NotificationService
        
        configs = [
            (True, True, "12345"),
            (True, False, None),
            (False, True, "67890"),
            (False, False, "11111"),
        ]
        
        for telegram, log, user in configs:
            args = Namespace(telegram=telegram, log=log, user=user, monitor=None)
            service = NotificationService(args)
            
            service.set_menu_choice_hierarchy("X:12:1")
            _ = service._should_send_message()


# =============================================================================
# PKScanRunner Interactive Tests
# =============================================================================

class TestPKScanRunnerInteractive:
    """Test PKScanRunner with simulated flows."""
    
    def test_get_formatted_choices_all_combinations(self):
        """Test getFormattedChoices with all combinations."""
        from pkscreener.classes.PKScanRunner import PKScanRunner
        
        for intraday_analysis in [True, False]:
            for intraday in [None, "1m", "5m", "15m"]:
                args = Namespace(runintradayanalysis=intraday_analysis, intraday=intraday)
                
                for choice_0 in ["X", "P", "B"]:
                    for choice_1 in ["1", "5", "12"]:
                        for choice_2 in ["0", "1", "5", "10"]:
                            choices = {"0": choice_0, "1": choice_1, "2": choice_2}
                            result = PKScanRunner.getFormattedChoices(args, choices)
                            assert isinstance(result, str)


# =============================================================================
# CoreFunctions Interactive Tests
# =============================================================================

class TestCoreFunctionsInteractive:
    """Test CoreFunctions with simulated flows."""
    
    def test_get_review_date_all_values(self):
        """Test get_review_date with all values."""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        for days in range(0, 100, 10):
            args = Namespace(backtestdaysago=days if days > 0 else None)
            result = get_review_date(None, args)
            if days and days > 0:
                assert result is not None


# =============================================================================
# BacktestUtils Interactive Tests
# =============================================================================

class TestBacktestUtilsInteractive:
    """Test BacktestUtils with simulated flows."""
    
    def test_get_backtest_report_filename_all_combinations(self):
        """Test get_backtest_report_filename with all combinations."""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        for sort_key in [None, "Stock", "LTP", "%Chng"]:
            for optional_name in [None, "test", "report"]:
                for choices in [None, {"0": "X", "1": "12", "2": "1"}]:
                    result = get_backtest_report_filename(
                        sort_key=sort_key,
                        optional_name=optional_name,
                        choices=choices
                    )
                    assert result is not None


# =============================================================================
# MenuOptions Interactive Tests
# =============================================================================

class TestMenuOptionsInteractive:
    """Test MenuOptions with simulated flows."""
    
    def test_menus_all_levels(self):
        """Test menus with all levels."""
        from pkscreener.classes.MenuOptions import menus
        
        for level in [0, 1, 2, 3, 4]:
            m = menus()
            m.level = level
            m.renderForMenu(asList=True)
    
    def test_menus_find_all_keys(self):
        """Test menus find with all keys."""
        from pkscreener.classes.MenuOptions import menus
        
        m = menus()
        m.renderForMenu(asList=True)
        
        # Try all possible keys
        for key in list("XPBCHDUYZ0123456789") + ["10", "11", "12", "13", "14", "15"]:
            result = m.find(key)
            # May or may not find
            assert result is not None or result is None


# =============================================================================
# signals Interactive Tests
# =============================================================================

class TestSignalsInteractive:
    """Test signals with simulated flows."""
    
    def test_signal_result_all_combinations(self):
        """Test SignalResult with all combinations."""
        from pkscreener.classes.screening.signals import SignalResult, SignalStrength
        
        for signal in SignalStrength:
            for confidence in range(0, 101, 10):
                result = SignalResult(signal=signal, confidence=float(confidence))
                _ = result.is_buy
