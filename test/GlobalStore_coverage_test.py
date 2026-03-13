"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for GlobalStore.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from argparse import Namespace
import warnings
warnings.filterwarnings("ignore")


class TestPKGlobalStoreCoverage:
    """Comprehensive tests for PKGlobalStore."""
    
    def test_global_store_singleton(self):
        """Test PKGlobalStore is singleton."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store1 = PKGlobalStore()
        store2 = PKGlobalStore()
        
        assert store1 is store2
    
    def test_global_store_init_config(self):
        """Test _initialize_config sets attributes."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        
        assert hasattr(store, 'configManager')
        assert hasattr(store, 'TEST_STKCODE')
        assert store.TEST_STKCODE == "SBIN"
        assert hasattr(store, 'defaultAnswer')
    
    def test_global_store_init_fetchers(self):
        """Test _initialize_fetchers sets attributes."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        
        assert hasattr(store, 'fetcher')
        assert hasattr(store, 'mstarFetcher')
    
    def test_global_store_init_menus(self):
        """Test _initialize_menus sets attributes."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        
        assert hasattr(store, 'm0')
        assert hasattr(store, 'm1')
        assert hasattr(store, 'm2')
        assert hasattr(store, 'm3')
        assert hasattr(store, 'm4')
        assert hasattr(store, 'selectedChoice')
        assert hasattr(store, 'menuChoiceHierarchy')
    
    def test_global_store_init_scan_state(self):
        """Test _initialize_scan_state sets attributes."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        
        assert hasattr(store, 'keyboardInterruptEvent')
        assert hasattr(store, 'keyboardInterruptEventFired')
        assert hasattr(store, 'loadCount')
        assert hasattr(store, 'screenCounter')
        assert hasattr(store, 'screener')
        assert hasattr(store, 'userPassedArgs')
    
    def test_global_store_init_results_state(self):
        """Test _initialize_results_state sets attributes."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        
        assert hasattr(store, 'screenResults')
        assert hasattr(store, 'backtest_df')
        assert hasattr(store, 'stockDictPrimary')
        assert hasattr(store, 'analysis_dict')
    
    def test_global_store_init_multiprocessing_state(self):
        """Test _initialize_multiprocessing_state sets attributes."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        
        assert hasattr(store, 'tasks_queue')
        assert hasattr(store, 'results_queue')
        assert hasattr(store, 'consumers')
        assert hasattr(store, 'mp_manager')
    
    def test_global_store_init_notification_state(self):
        """Test _initialize_notification_state sets attributes."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        
        assert hasattr(store, 'test_messages_queue')
        assert hasattr(store, 'download_trials')
        assert hasattr(store, 'media_group_dict')
        assert hasattr(store, 'DEV_CHANNEL_ID')
    
    def test_reset_for_new_scan(self):
        """Test reset_for_new_scan resets state."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.scanCycleRunning = False
        
        store.reset_for_new_scan()
        
        assert store.selectedChoice == {"0": "", "1": "", "2": "", "3": "", "4": ""}
        assert store.strategyFilter == []
        assert store.test_messages_queue == []
    
    def test_reset_for_new_scan_cycle_running(self):
        """Test reset_for_new_scan when cycle is running."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.scanCycleRunning = True
        store.elapsed_time = 100
        store.start_time = 50
        
        store.reset_for_new_scan()
        
        # Should preserve times when cycle is running
        assert store.elapsed_time == 100
        assert store.start_time == 50
    
    def test_reset_menu_choice_options(self):
        """Test reset_menu_choice_options resets menu state."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.media_group_dict = {"test": "value"}
        store.menuChoiceHierarchy = "X:12:1"
        store.userPassedArgs = None
        
        store.reset_menu_choice_options()
        
        assert store.media_group_dict == {}
        assert store.menuChoiceHierarchy == ""
    
    def test_reset_menu_choice_options_with_user_args(self):
        """Test reset_menu_choice_options with userPassedArgs."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.userPassedArgs = Namespace(pipedtitle="Test Title")
        store.media_group_dict = {"test": "value"}
        
        store.reset_menu_choice_options()
        
        assert store.userPassedArgs.pipedtitle == ""
    
    def test_is_interrupted_false(self):
        """Test is_interrupted returns False."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.keyboardInterruptEventFired = False
        
        assert store.is_interrupted() == False
    
    def test_is_interrupted_true(self):
        """Test is_interrupted returns True."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.keyboardInterruptEventFired = True
        
        assert store.is_interrupted() == True
    
    def test_initialize_multiprocessing(self):
        """Test initialize_multiprocessing sets up multiprocessing."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        # Reset to test initialization
        store.mp_manager = None
        store.keyboardInterruptEvent = None
        store.keyboardInterruptEventFired = False
        store.stockDictPrimary = None
        store.stockDictSecondary = None
        
        store.initialize_multiprocessing()
        
        assert store.screenCounter is not None
        assert store.screenResultsCounter is not None
        assert store.mp_manager is not None
        assert store.keyboardInterruptEvent is not None
        assert store.stockDictPrimary is not None
        assert store.stockDictSecondary is not None
    
    def test_initialize_multiprocessing_already_initialized(self):
        """Test initialize_multiprocessing when already done."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        import multiprocessing
        
        store = PKGlobalStore()
        store.mp_manager = multiprocessing.Manager()
        store.keyboardInterruptEvent = store.mp_manager.Event()
        store.stockDictPrimary = {}  # dict, not manager.dict
        
        store.initialize_multiprocessing()
        
        # Should still work
        assert store.screenCounter is not None
    
    def test_get_mkt_monitor_dict_new_manager(self):
        """Test get_mkt_monitor_dict creates new manager."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.mp_manager = None
        
        result = store.get_mkt_monitor_dict()
        
        assert result is not None
        assert store.mp_manager is not None
    
    def test_get_mkt_monitor_dict_existing_manager(self):
        """Test get_mkt_monitor_dict with existing manager."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        import multiprocessing
        
        store = PKGlobalStore()
        store.mp_manager = multiprocessing.Manager()
        
        result = store.get_mkt_monitor_dict()
        
        assert result is not None
    
    def test_get_global_store_function(self):
        """Test get_global_store convenience function."""
        from pkscreener.classes.GlobalStore import get_global_store, PKGlobalStore
        
        store = get_global_store()
        
        assert isinstance(store, PKGlobalStore)
    
    def test_global_store_multiprocessing_with_event_fired(self):
        """Test multiprocessing when event was fired."""
        from pkscreener.classes.GlobalStore import PKGlobalStore
        
        store = PKGlobalStore()
        store.mp_manager = None
        store.keyboardInterruptEvent = None
        store.keyboardInterruptEventFired = True  # Event was fired
        store.stockDictPrimary = None
        
        store.initialize_multiprocessing()
        
        # keyboardInterruptEvent should remain None since event was fired
        assert store.keyboardInterruptEvent is None
        assert store.keyboardInterruptEventFired == False  # Reset in the method
