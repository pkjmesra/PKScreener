"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestPKGlobalStore:
    """Test cases for PKGlobalStore class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('pkscreener.classes.GlobalStore.ConfigManager') as mock_config, \
             patch('pkscreener.classes.GlobalStore.Fetcher') as mock_fetcher, \
             patch('pkscreener.classes.GlobalStore.morningstarDataFetcher') as mock_mstar, \
             patch('pkscreener.classes.GlobalStore.menus') as mock_menus, \
             patch('pkscreener.classes.GlobalStore.ScreeningStatistics') as mock_screener, \
             patch('pkscreener.classes.GlobalStore.default_logger') as mock_logger:
            
            mock_config.tools.return_value = MagicMock()
            mock_config.parser = MagicMock()
            mock_fetcher.screenerStockDataFetcher.return_value = MagicMock()
            mock_mstar.return_value = MagicMock()
            mock_menus.return_value = MagicMock()
            mock_screener.return_value = MagicMock()
            mock_logger.return_value = MagicMock()
            
            yield {
                'config': mock_config,
                'fetcher': mock_fetcher,
                'mstar': mock_mstar,
                'menus': mock_menus,
                'screener': mock_screener,
                'logger': mock_logger
            }
    
    def test_singleton_pattern(self, mock_dependencies):
        """Test that PKGlobalStore follows singleton pattern."""
        from pkscreener.classes.GlobalStore import PKGlobalStore, get_global_store
        
        # Reset singleton for testing
        PKGlobalStore._instances = {}
        
        store1 = get_global_store()
        store2 = get_global_store()
        
        assert store1 is store2
        
    def test_initialization(self, mock_dependencies):
        """Test PKGlobalStore initialization."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        # Reset singleton for testing
        PKGlobalStore._instances = {}
        
        store = PKGlobalStore()
        
        # Check config initialization
        assert store.configManager is not None
        assert store.TEST_STKCODE == "SBIN"
        assert store.defaultAnswer is None
        
    def test_initialize_menus(self, mock_dependencies):
        """Test menu initialization."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        PKGlobalStore._instances = {}
        store = PKGlobalStore()
        
        assert store.m0 is not None
        assert store.m1 is not None
        assert store.m2 is not None
        assert store.m3 is not None
        assert store.m4 is not None
        assert store.selectedChoice == {"0": "", "1": "", "2": "", "3": "", "4": ""}
        
    def test_initialize_scan_state(self, mock_dependencies):
        """Test scan state initialization."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        PKGlobalStore._instances = {}
        store = PKGlobalStore()
        
        # Re-initialize to get fresh state
        store._initialize_scan_state()
        
        assert store.keyboardInterruptEvent is None
        assert store.keyboardInterruptEventFired == False
        assert store.loadCount == 0
        assert store.loadedStockData == False
        assert store.elapsed_time == 0
        assert store.scanCycleRunning == False
        
    def test_reset_for_new_scan(self, mock_dependencies):
        """Test resetting state for new scan."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        PKGlobalStore._instances = {}
        store = PKGlobalStore()
        
        # Set some values
        store.selectedChoice = {"0": "X", "1": "1", "2": "2", "3": "", "4": ""}
        store.elapsed_time = 100
        store.strategyFilter = ["filter1"]
        
        # Reset
        store.reset_for_new_scan()
        
        assert store.selectedChoice == {"0": "", "1": "", "2": "", "3": "", "4": ""}
        assert store.strategyFilter == []
        
    def test_is_interrupted(self, mock_dependencies):
        """Test interrupt check."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        PKGlobalStore._instances = {}
        store = PKGlobalStore()
        
        assert store.is_interrupted() == False
        
        store.keyboardInterruptEventFired = True
        assert store.is_interrupted() == True
        
    def test_reset_menu_choice_options(self, mock_dependencies):
        """Test resetting menu choice options."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        PKGlobalStore._instances = {}
        store = PKGlobalStore()
        
        store.media_group_dict = {"key": "value"}
        store.menuChoiceHierarchy = "X > 1 > 2"
        store.userPassedArgs = MagicMock()
        store.userPassedArgs.pipedtitle = "Test Title"
        
        store.reset_menu_choice_options()
        
        assert store.media_group_dict == {}
        assert store.menuChoiceHierarchy == ""
        assert store.userPassedArgs.pipedtitle == ""
        
    def test_notification_state_initialization(self, mock_dependencies):
        """Test notification state initialization."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        PKGlobalStore._instances = {}
        store = PKGlobalStore()
        
        # test_messages_queue may be None or [] depending on initialization order and state
        assert store.test_messages_queue is None or store.test_messages_queue == []
        assert store.download_trials == 0
        assert store.media_group_dict == {}
        assert store.DEV_CHANNEL_ID == "-1001785195297"
        
    def test_results_state_initialization(self, mock_dependencies):
        """Test results state initialization."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        PKGlobalStore._instances = {}
        store = PKGlobalStore()
        
        # Re-initialize to get fresh state
        store._initialize_results_state()
        
        assert store.screenResults is None
        assert store.backtest_df is None
        assert store.stockDictPrimary is None
        assert store.stockDictSecondary is None
        assert store.analysis_dict == {}


class TestGetGlobalStore:
    """Test cases for get_global_store function."""
    
    def test_get_global_store_returns_instance(self):
        """Test that get_global_store returns a PKGlobalStore instance."""
        with patch('pkscreener.classes.GlobalStore.ConfigManager') as mock_config, \
             patch('pkscreener.classes.GlobalStore.Fetcher') as mock_fetcher, \
             patch('pkscreener.classes.GlobalStore.morningstarDataFetcher') as mock_mstar, \
             patch('pkscreener.classes.GlobalStore.menus') as mock_menus, \
             patch('pkscreener.classes.GlobalStore.ScreeningStatistics') as mock_screener, \
             patch('pkscreener.classes.GlobalStore.default_logger') as mock_logger:
            
            mock_config.tools.return_value = MagicMock()
            mock_config.parser = MagicMock()
            mock_fetcher.screenerStockDataFetcher.return_value = MagicMock()
            mock_mstar.return_value = MagicMock()
            mock_menus.return_value = MagicMock()
            mock_screener.return_value = MagicMock()
            mock_logger.return_value = MagicMock()
            
            from pkscreener.classes.GlobalStore import PKGlobalStore, get_global_store
            
            PKGlobalStore._instances = {}
            
            store = get_global_store()
            
            assert isinstance(store, PKGlobalStore)



