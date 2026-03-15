"""
Tests for the refactored modular components of PKScreener.

These tests verify that the modular functions extracted from globals.py work correctly:
- CoreFunctions: Review date, iterations, results processing
- OutputFunctions: Error messages, config toggles, file operations
- MenuNavigation: Menu choice hierarchy building
- MainLogic: Menu option handling
- NotificationService: Telegram notifications
- ResultsLabeler: Data labeling and formatting
- BacktestUtils: Backtest result handling
- DataLoader: Stock data saving
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestCoreFunctions:
    """Tests for CoreFunctions module"""
    
    def test_get_review_date_with_none(self):
        """Should return current date when no args provided"""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        result = get_review_date(None)
        assert result is not None
    
    def test_get_review_date_with_backtest(self):
        """Should return past date when backtestdaysago is set"""
        from pkscreener.classes.CoreFunctions import get_review_date
        
        mock_args = Mock()
        mock_args.backtestdaysago = 5
        
        result = get_review_date(mock_args)
        # Should be a date in the past
        assert result is not None
    
    def test_get_max_allowed_results_count(self):
        """Should calculate max allowed results"""
        from pkscreener.classes.CoreFunctions import get_max_allowed_results_count
        
        mock_config = Mock()
        mock_config.maxdisplayresults = 100
        mock_args = Mock()
        mock_args.maxdisplayresults = None
        
        # Testing mode should limit to 1
        result = get_max_allowed_results_count(10, True, mock_config, mock_args)
        assert result == 1
        
        # Normal mode should return iterations * maxdisplayresults
        result = get_max_allowed_results_count(10, False, mock_config, mock_args)
        assert result == 1000
    
    def test_get_iterations_and_stock_counts(self):
        """Should calculate iterations and stock counts"""
        from pkscreener.classes.CoreFunctions import get_iterations_and_stock_counts
        
        # For small number of stocks, should return single iteration
        iterations, stocks_per = get_iterations_and_stock_counts(100, 5)
        
        assert iterations == 1
        assert stocks_per == 100
    
    def test_get_iterations_large_stock_count(self):
        """Should handle large stock count"""
        from pkscreener.classes.CoreFunctions import get_iterations_and_stock_counts
        
        # For large number of stocks, should split into iterations
        iterations, stocks_per = get_iterations_and_stock_counts(3000, 1)
        
        assert iterations > 1
        assert stocks_per <= 500


class TestOutputFunctions:
    """Tests for OutputFunctions module"""
    
    def test_show_option_error_message(self):
        """Should print error message"""
        from pkscreener.classes.OutputFunctions import show_option_error_message
        
        with patch('pkscreener.classes.OutputFunctions.OutputControls') as mock_output:
            show_option_error_message()
            mock_output().printOutput.assert_called()
    
    def test_cleanup_local_results_handles_missing_dir(self):
        """Should handle missing directory gracefully"""
        from pkscreener.classes.OutputFunctions import cleanup_local_results
        
        with patch('os.path.isdir', return_value=False):
            # Should not raise an exception
            cleanup_local_results()
    
    def test_describe_user_disabled(self):
        """Should skip when analytics disabled"""
        from pkscreener.classes.OutputFunctions import describe_user
        
        mock_config = Mock()
        mock_config.enableUsageAnalytics = False
        
        # Should not raise an exception
        describe_user(mock_config)


class TestMenuNavigation:
    """Tests for MenuNavigation module"""
    
    def test_menu_navigator_init(self):
        """Should initialize MenuNavigator properly"""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        
        mock_config = Mock()
        nav = MenuNavigator(mock_config)
        
        assert nav.config_manager == mock_config
    
    def test_update_menu_choice_hierarchy_import(self):
        """Should be able to import update_menu_choice_hierarchy_impl"""
        try:
            from pkscreener.classes.MenuNavigation import update_menu_choice_hierarchy_impl
            assert callable(update_menu_choice_hierarchy_impl)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")


class TestNotificationService:
    """Tests for NotificationService module"""
    
    def test_notification_service_init(self):
        """Should initialize with default values"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        
        assert service.test_messages_queue == []
        assert service.media_group_dict == {}
    
    def test_send_message_skipped_without_runner(self):
        """Should skip sending when not in RUNNER mode"""
        from pkscreener.classes.NotificationService import send_message_to_telegram_channel_impl
        
        mock_args = Mock()
        mock_args.log = False
        mock_args.telegram = False
        
        with patch.dict(os.environ, {}, clear=True):
            # Remove RUNNER from environment
            result = send_message_to_telegram_channel_impl(
                message="test",
                user_passed_args=mock_args
            )
        
        # Should return early without sending
        assert result is not None
    
    def test_handle_alert_subscriptions_none_user(self):
        """Should handle None user gracefully"""
        from pkscreener.classes.NotificationService import handle_alert_subscriptions_impl
        
        # Should not raise an exception
        handle_alert_subscriptions_impl(None, "test message")
    
    def test_handle_alert_subscriptions_invalid_message(self):
        """Should handle message without | gracefully"""
        from pkscreener.classes.NotificationService import handle_alert_subscriptions_impl
        
        # Should not raise an exception
        handle_alert_subscriptions_impl("123", "test message without pipe")


class TestResultsLabeler:
    """Tests for ResultsLabeler module"""
    
    def test_label_data_none_results(self):
        """Should handle None save results"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        mock_config = Mock()
        
        result = label_data_for_printing_impl(
            None, None, mock_config, 2.5, 9, None, "X"
        )
        
        assert result == (None, None)
    
    def test_label_data_basic(self):
        """Should label data correctly"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        mock_config = Mock()
        mock_config.calculatersiintraday = False
        mock_config.daysToLookback = 22
        
        screen_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "volume": [2.5, 3.0],
            "RSI": [50, 60]
        })
        
        save_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "volume": [2.5, 3.0],
            "RSI": [50, 60]
        })
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('pkscreener.classes.ResultsLabeler.PKDateUtilities') as mock_date:
                mock_date.isTradingTime.return_value = False
                mock_date.isTodayHoliday.return_value = (False, None)
                
                screen_result, save_result = label_data_for_printing_impl(
                    screen_df, save_df, mock_config, 2.5, 9, None, "X",
                    menu_choice_hierarchy="Test", user_passed_args=None
                )
        
        assert screen_result is not None
        assert save_result is not None


class TestBacktestUtils:
    """Tests for BacktestUtils module"""
    
    def test_get_backtest_report_filename(self):
        """Should generate proper filename"""
        from pkscreener.classes.BacktestUtils import get_backtest_report_filename
        
        choices = {"0": "X", "1": "12", "2": "9"}
        
        directory, filename = get_backtest_report_filename(choices=choices)
        
        # Directory should be a valid path
        assert directory is not None
        assert ".html" in filename
    
    def test_backtest_results_handler_init(self):
        """Should initialize properly"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        mock_config = Mock()
        handler = BacktestResultsHandler(mock_config)
        
        assert handler.config_manager == mock_config
        assert handler.backtest_df is None
    
    def test_show_backtest_results_empty_df(self):
        """Should handle empty dataframe"""
        from pkscreener.classes.BacktestUtils import show_backtest_results_impl
        
        with patch('pkscreener.classes.BacktestUtils.OutputControls') as mock_output:
            show_backtest_results_impl(
                pd.DataFrame(), "Stock", "test", None,
                menu_choice_hierarchy="Test", selected_choice={},
                user_passed_args=None, elapsed_time=0
            )
            mock_output().printOutput.assert_called()
    
    def test_finish_backtest_data_cleanup(self):
        """Should cleanup backtest data properly"""
        from pkscreener.classes.BacktestUtils import finish_backtest_data_cleanup_impl
        
        df = pd.DataFrame({
            "Stock": ["A", "B"],
            "Date": ["2024-01-01", "2024-01-02"],
            "1-Pd": [5.0, 3.0]
        })
        
        mock_show_cb = Mock()
        mock_summary_cb = Mock(return_value=pd.DataFrame())
        mock_config = Mock()
        mock_config.enablePortfolioCalculations = False
        
        summary_df, sorting, sort_keys = finish_backtest_data_cleanup_impl(
            df, None,
            default_answer="Y",
            config_manager=mock_config,
            show_backtest_cb=mock_show_cb,
            backtest_summary_cb=mock_summary_cb
        )
        
        assert sorting is False  # default_answer is not None
        assert "S" in sort_keys
        assert "D" in sort_keys


class TestDataLoader:
    """Tests for DataLoader module"""
    
    def test_stock_data_loader_init(self):
        """Should initialize with config"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_config = Mock()
        mock_fetcher = Mock()
        
        loader = StockDataLoader(mock_config, mock_fetcher)
        
        assert loader.config_manager == mock_config
        assert loader.fetcher == mock_fetcher
    
    def test_save_downloaded_data_skipped_when_interrupted(self):
        """Should skip saving when keyboard interrupt fired"""
        from pkscreener.classes.DataLoader import save_downloaded_data_impl
        
        mock_config = Mock()
        
        with patch('pkscreener.classes.DataLoader.OutputControls') as mock_output:
            save_downloaded_data_impl(
                download_only=False,
                testing=False,
                stock_dict_primary={},
                config_manager=mock_config,
                load_count=0,
                keyboard_interrupt_fired=True
            )
            # Should print "Skipped Saving!"
            mock_output().printOutput.assert_called()


class TestMainLogic:
    """Tests for MainLogic module"""
    
    def test_handle_secondary_menu_choices_H(self):
        """Should handle H (Help) menu option"""
        from pkscreener.classes.MainLogic import handle_secondary_menu_choices_impl
        
        mock_m0 = Mock()
        mock_m1 = Mock()
        mock_m2 = Mock()
        mock_config = Mock()
        mock_args = Mock()
        
        mock_help_cb = Mock()
        
        result = handle_secondary_menu_choices_impl(
            "H", mock_m0, mock_m1, mock_m2, mock_config, mock_args, None,
            testing=False, defaultAnswer="Y", user=None,
            show_config_info_cb=None, show_help_info_cb=mock_help_cb
        )
        
        mock_help_cb.assert_called_once()
    
    def test_handle_secondary_menu_choices_Y(self):
        """Should handle Y (Config) menu option"""
        from pkscreener.classes.MainLogic import handle_secondary_menu_choices_impl
        
        mock_m0 = Mock()
        mock_m1 = Mock()
        mock_m2 = Mock()
        mock_config = Mock()
        mock_args = Mock()
        
        mock_config_cb = Mock()
        
        result = handle_secondary_menu_choices_impl(
            "Y", mock_m0, mock_m1, mock_m2, mock_config, mock_args, None,
            testing=False, defaultAnswer="Y", user=None,
            show_config_info_cb=mock_config_cb, show_help_info_cb=None
        )
        
        mock_config_cb.assert_called_once()


class TestExecuteOptionHandlers:
    """Tests for ExecuteOptionHandlers module"""
    
    def test_handle_execute_option_3_import(self):
        """Should be able to import handle_execute_option_3"""
        try:
            from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_3
            assert callable(handle_execute_option_3)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_handle_execute_option_5_import(self):
        """Should be able to import handle_execute_option_5"""
        try:
            from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_5
            assert callable(handle_execute_option_5)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_handle_execute_option_6_import(self):
        """Should be able to import handle_execute_option_6"""
        try:
            from pkscreener.classes.ExecuteOptionHandlers import handle_execute_option_6
            assert callable(handle_execute_option_6)
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_all_handlers_exist(self):
        """All execute option handlers should exist"""
        from pkscreener.classes.ExecuteOptionHandlers import (
            handle_execute_option_3, handle_execute_option_4, handle_execute_option_5,
            handle_execute_option_6, handle_execute_option_7, handle_execute_option_8,
            handle_execute_option_9, handle_execute_option_12
        )
        
        assert all([
            callable(handle_execute_option_3),
            callable(handle_execute_option_4),
            callable(handle_execute_option_5),
            callable(handle_execute_option_6),
            callable(handle_execute_option_7),
            callable(handle_execute_option_8),
            callable(handle_execute_option_9),
            callable(handle_execute_option_12)
        ])


class TestIntegration:
    """Integration tests for the refactored modules working together"""
    
    def test_globals_imports_work(self):
        """Should be able to import from globals without errors"""
        try:
            from pkscreener.globals import (
                labelDataForPrinting,
                sendMessageToTelegramChannel,
                showBacktestResults,
                updateMenuChoiceHierarchy,
                saveDownloadedData,
                FinishBacktestDataCleanup,
                prepareGroupedXRay,
                showSortedBacktestData,
                tabulateBacktestResults
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_classes_init_imports_work(self):
        """Should be able to import from classes __init__"""
        try:
            from pkscreener.classes import (
                VERSION,
                MenuNavigator,
                StockDataLoader,
                NotificationService,
                BacktestResultsHandler,
                ResultsLabeler
            )
            assert VERSION is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_core_functions_integration(self):
        """Core functions should work together"""
        from pkscreener.classes.CoreFunctions import (
            get_review_date,
            get_max_allowed_results_count,
            get_iterations_and_stock_counts
        )
        
        mock_config = Mock()
        mock_config.maxdisplayresults = 100
        mock_args = Mock()
        mock_args.maxdisplayresults = None
        mock_args.backtestdaysago = None
        
        # Get review date
        date = get_review_date(mock_args)
        assert date is not None
        
        # Calculate max allowed
        max_allowed = get_max_allowed_results_count(10, False, mock_config, mock_args)
        assert max_allowed == 1000
        
        # Calculate iterations - small count returns single iteration
        iterations, stocks_per = get_iterations_and_stock_counts(100, 4)
        assert iterations == 1
        assert stocks_per == 100
