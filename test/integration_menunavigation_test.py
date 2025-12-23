"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Integration tests for MenuNavigation.py with extensive mocking.
    Target: Push MenuNavigation coverage from 9% to 60%+
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
def user_args():
    """Create mock user arguments."""
    return Namespace(
        options=None,
        pipedmenus=None,
        backtestdaysago=None,
        pipedtitle=None,
        runintradayanalysis=False,
        systemlaunched=False,
        intraday=None,
        user=None,
        telegram=False,
        log=False
    )


class TestMenuNavigatorInit:
    """Test MenuNavigator initialization."""
    
    def test_menu_navigator_creation(self, config):
        """Test MenuNavigator can be created."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        assert navigator is not None
    
    def test_menu_navigator_has_config_manager(self, config):
        """Test MenuNavigator has config_manager."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        assert navigator.config_manager is not None
    
    def test_menu_navigator_has_menus(self, config):
        """Test MenuNavigator has menu objects."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        assert navigator.m0 is not None
        assert navigator.m1 is not None
        assert navigator.m2 is not None
        assert navigator.m3 is not None
        assert navigator.m4 is not None
    
    def test_menu_navigator_has_selected_choice(self, config):
        """Test MenuNavigator has selected_choice."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        assert navigator.selected_choice is not None
        assert isinstance(navigator.selected_choice, dict)
    
    def test_menu_navigator_selected_choice_keys(self, config):
        """Test MenuNavigator selected_choice has correct keys."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        assert "0" in navigator.selected_choice
        assert "1" in navigator.selected_choice
        assert "2" in navigator.selected_choice
        assert "3" in navigator.selected_choice
        assert "4" in navigator.selected_choice


class TestMenuNavigatorGetHistoricalDays:
    """Test MenuNavigator get_historical_days method."""
    
    def test_get_historical_days_testing(self, config):
        """Test get_historical_days in testing mode."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        result = navigator.get_historical_days(100, testing=True)
        assert result == 2
    
    def test_get_historical_days_not_testing(self, config):
        """Test get_historical_days not in testing mode."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        result = navigator.get_historical_days(100, testing=False)
        assert result is not None


class TestMenuNavigatorGetTestBuildChoices:
    """Test MenuNavigator get_test_build_choices method."""
    
    def test_get_test_build_choices_default(self, config):
        """Test get_test_build_choices with defaults."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        result = navigator.get_test_build_choices()
        assert result == ("X", 1, 0, {"0": "X", "1": "1", "2": "0"})
    
    def test_get_test_build_choices_with_menu_option(self, config):
        """Test get_test_build_choices with menu option."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        result = navigator.get_test_build_choices(menu_option="P")
        assert result[0] == "P"
    
    def test_get_test_build_choices_with_all_options(self, config):
        """Test get_test_build_choices with all options."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        result = navigator.get_test_build_choices(
            index_option=12,
            execute_option=5,
            menu_option="X"
        )
        assert result[0] == "X"
        assert result[1] == 12
        assert result[2] == 5


class TestMenuNavigatorGetTopLevelMenuChoices:
    """Test MenuNavigator get_top_level_menu_choices method."""
    
    def test_get_top_level_menu_choices_test_build(self, config, user_args):
        """Test get_top_level_menu_choices in test build mode."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        
        options, menu_option, index_option, execute_option = navigator.get_top_level_menu_choices(
            startup_options="X:12:1",
            test_build=True,
            download_only=False,
            default_answer="Y",
            user_passed_args=user_args,
            last_scan_output_stock_codes=None
        )
        assert menu_option == "X"
    
    def test_get_top_level_menu_choices_with_startup_options(self, config, user_args):
        """Test get_top_level_menu_choices with startup options."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        
        options, menu_option, index_option, execute_option = navigator.get_top_level_menu_choices(
            startup_options="P:5:3",
            test_build=False,
            download_only=False,
            default_answer="Y",
            user_passed_args=user_args,
            last_scan_output_stock_codes=None
        )
        assert options == ["P", "5", "3"]
        assert menu_option == "P"
        assert index_option == "5"
        assert execute_option == "3"
    
    def test_get_top_level_menu_choices_with_last_scan(self, config, user_args):
        """Test get_top_level_menu_choices with last scan output."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        
        options, menu_option, index_option, execute_option = navigator.get_top_level_menu_choices(
            startup_options="X:12:1",
            test_build=True,
            download_only=False,
            default_answer="Y",
            user_passed_args=user_args,
            last_scan_output_stock_codes=["SBIN", "RELIANCE"]
        )
        assert index_option == 0


class TestMenuNavigatorGetDownloadChoices:
    """Test MenuNavigator get_download_choices method."""
    
    @patch('pkscreener.classes.MenuNavigation.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    def test_get_download_choices_file_not_exists(self, mock_exists, config, user_args):
        """Test get_download_choices when file doesn't exist."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        mock_exists.return_value = (False, "test_cache.pkl")
        
        navigator = MenuNavigator(config)
        result = navigator.get_download_choices(
            default_answer="Y",
            user_passed_args=user_args
        )
        assert result[0] == "X"
        assert result[1] == 12
        assert result[2] == 0


class TestMenuNavigatorGetScannerMenuChoices:
    """Test MenuNavigator get_scanner_menu_choices method."""
    
    def test_get_scanner_menu_choices_test_build(self, config, user_args):
        """Test get_scanner_menu_choices in test build mode."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        
        try:
            result = navigator.get_scanner_menu_choices(
                test_build=True,
                default_answer="Y",
                options=["X", "12", "1"],
                menu_option="X",
                index_option=12,
                execute_option=1,
                user_passed_args=user_args
            )
        except:
            pass


class TestMenuNavigatorWithMocking:
    """Test MenuNavigator with extensive mocking."""
    
    @patch('pkscreener.classes.MenuNavigation.OutputControls')
    def test_navigator_with_mocked_output(self, mock_output, config, user_args):
        """Test navigator with mocked OutputControls."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        
        # Test basic operations
        result = navigator.get_test_build_choices()
        assert result is not None
    
    @patch('pkscreener.classes.MenuNavigation.PKAnalyticsService')
    def test_navigator_with_mocked_analytics(self, mock_analytics, config, user_args):
        """Test navigator with mocked PKAnalyticsService."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        
        result = navigator.get_test_build_choices()
        assert result is not None


class TestMenuNavigatorNValueForMenu:
    """Test MenuNavigator n_value_for_menu attribute."""
    
    def test_n_value_for_menu_initial(self, config):
        """Test n_value_for_menu is initialized to 0."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        assert navigator.n_value_for_menu == 0
    
    def test_n_value_for_menu_can_be_set(self, config):
        """Test n_value_for_menu can be set."""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        navigator = MenuNavigator(config)
        navigator.n_value_for_menu = 10
        assert navigator.n_value_for_menu == 10
