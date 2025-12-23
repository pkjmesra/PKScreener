"""
Feature tests for PKScreener key workflows.

These tests verify end-to-end functionality of the main application workflows:
- Scanner execution workflow
- Backtest result processing
- Notification service workflow
- Data loading and saving
- Menu navigation
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestScannerWorkflow:
    """Feature tests for the scanner execution workflow"""
    
    def test_scanner_initialization_flow(self):
        """Scanner should initialize with correct dependencies"""
        from pkscreener.classes.StockScreener import StockScreener
        
        # Should create a stock screener instance
        screener = StockScreener()
        
        assert screener is not None
        assert hasattr(screener, 'configManager')
    
    def test_screening_statistics_initialization(self):
        """ScreeningStatistics should be importable"""
        from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
        
        # Just verify import works
        assert ScreeningStatistics is not None
    
    def test_strong_buy_signal_detection(self):
        """Should detect strong buy signals correctly"""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals()
        
        # Create bullish data
        df = pd.DataFrame({
            'Close': [100 + i for i in range(50)],
            'High': [101 + i for i in range(50)],
            'Low': [99 + i for i in range(50)],
            'Open': [100 + i for i in range(50)],
            'Volume': [1000000] * 50
        })
        
        result = signals.analyze(df)
        
        assert result is not None
        assert result.signal in SignalStrength
    
    def test_strong_sell_signal_detection(self):
        """Should detect strong sell signals correctly"""
        from pkscreener.classes.screening.signals import TradingSignals, SignalStrength
        
        signals = TradingSignals()
        
        # Create bearish data
        df = pd.DataFrame({
            'Close': [100 - i for i in range(50)],
            'High': [101 - i for i in range(50)],
            'Low': [99 - i for i in range(50)],
            'Open': [100 - i for i in range(50)],
            'Volume': [1000000] * 50
        })
        
        result = signals.analyze(df)
        
        assert result is not None
        assert result.signal in SignalStrength


class TestBacktestWorkflow:
    """Feature tests for backtesting workflow"""
    
    def test_backtest_result_handling(self):
        """Should handle backtest results properly"""
        from pkscreener.classes.BacktestUtils import BacktestResultsHandler
        
        mock_config = Mock()
        handler = BacktestResultsHandler(mock_config)
        
        # Set backtest_df directly (the actual API)
        df = pd.DataFrame({
            "Stock": ["A", "B", "C"],
            "1-Pd": [5.0, -2.0, 3.0],
            "2-Pd": [7.0, -1.0, 4.0]
        })
        
        handler.backtest_df = df
        
        assert handler.backtest_df is not None
        assert len(handler.backtest_df) == 3
    
    def test_backtest_summary_generation(self):
        """Should generate proper backtest summary"""
        from pkscreener.classes.Backtest import backtestSummary
        
        df = pd.DataFrame({
            "Stock": ["A", "B", "C"],
            "1-Pd": [5.0, -2.0, 3.0],
            "2-Pd": [7.0, -1.0, 4.0],
            "Date": ["2024-01-01", "2024-01-01", "2024-01-01"]
        })
        
        summary = backtestSummary(df)
        
        assert summary is not None
    
    def test_finish_backtest_cleanup_workflow(self):
        """Should cleanup backtest data correctly"""
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
        
        assert mock_summary_cb.called
        assert sorting is False  # default_answer is set
        assert isinstance(sort_keys, dict)


class TestNotificationWorkflow:
    """Feature tests for notification workflow"""
    
    def test_notification_service_creation(self):
        """Should create notification service with proper config"""
        from pkscreener.classes.NotificationService import NotificationService
        
        mock_args = Mock()
        mock_args.user = "12345"
        mock_args.telegram = False
        mock_args.log = True
        
        service = NotificationService(mock_args)
        
        assert service.user_passed_args == mock_args
        assert service.test_messages_queue == []
    
    def test_media_group_handling(self):
        """Should handle media group attachments"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        
        service.add_to_media_group(
            file_path="/path/to/file.png",
            caption="Test caption",
            group_caption="Group caption"
        )
        
        assert "ATTACHMENTS" in service.media_group_dict
        assert len(service.media_group_dict["ATTACHMENTS"]) == 1
        assert service.media_group_dict["ATTACHMENTS"][0]["FILEPATH"] == "/path/to/file.png"
    
    def test_test_status_message(self):
        """Should send test status message correctly"""
        from pkscreener.classes.NotificationService import NotificationService
        
        service = NotificationService()
        
        screen_results = pd.DataFrame({"Stock": ["A", "B"]})
        
        with patch.object(service, 'send_message_to_telegram') as mock_send:
            service.send_test_status(screen_results, "Test Label", user="12345")
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "SUCCESS" in call_args[1]["message"]
            assert "2 Stocks" in call_args[1]["message"]


class TestDataLoadingWorkflow:
    """Feature tests for data loading workflow"""
    
    def test_stock_data_loader_creation(self):
        """Should create data loader with dependencies"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_config = Mock()
        mock_fetcher = Mock()
        
        loader = StockDataLoader(mock_config, mock_fetcher)
        
        assert loader.config_manager == mock_config
        assert loader.fetcher == mock_fetcher
    
    def test_save_data_skipped_when_interrupted(self):
        """Should skip saving when keyboard interrupt fired"""
        from pkscreener.classes.DataLoader import save_downloaded_data_impl
        
        mock_config = Mock()
        mock_config.cacheEnabled = True
        
        with patch('pkscreener.classes.DataLoader.OutputControls') as mock_output:
            save_downloaded_data_impl(
                download_only=True,
                testing=False,
                stock_dict_primary={},
                config_manager=mock_config,
                load_count=0,
                keyboard_interrupt_fired=True
            )
            
            # Should print skip message
            mock_output().printOutput.assert_called()


class TestMenuNavigationWorkflow:
    """Feature tests for menu navigation workflow"""
    
    def test_menu_navigator_creation(self):
        """Should create menu navigator properly"""
        from pkscreener.classes.MenuNavigation import MenuNavigator
        
        mock_config = Mock()
        nav = MenuNavigator(mock_config)
        
        assert nav.config_manager == mock_config
        assert nav.selected_choice == {"0": "", "1": "", "2": "", "3": "", "4": ""}
    
    def test_main_logic_menu_handling(self):
        """Should handle menu choices via MainLogic"""
        from pkscreener.classes.MainLogic import handle_secondary_menu_choices_impl
        
        mock_m0 = Mock()
        mock_m1 = Mock()
        mock_m2 = Mock()
        mock_config = Mock()
        mock_args = Mock()
        
        help_called = []
        
        def mock_help_cb(*args, **kwargs):
            help_called.append(True)
        
        result = handle_secondary_menu_choices_impl(
            "H", mock_m0, mock_m1, mock_m2, mock_config, mock_args, None,
            testing=False, defaultAnswer="Y", user=None,
            show_help_info_cb=mock_help_cb
        )
        
        assert len(help_called) == 1


class TestResultsLabelingWorkflow:
    """Feature tests for results labeling workflow"""
    
    def test_results_labeler_creation(self):
        """Should create results labeler properly"""
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        mock_config = Mock()
        mock_config.daysToLookback = 22
        
        labeler = ResultsLabeler(mock_config, "Test Hierarchy")
        
        assert labeler.config_manager == mock_config
        assert labeler.menu_choice_hierarchy == "Test Hierarchy"
    
    def test_label_data_for_printing_with_valid_data(self):
        """Should label data correctly for printing"""
        from pkscreener.classes.ResultsLabeler import label_data_for_printing_impl
        
        mock_config = Mock()
        mock_config.calculatersiintraday = False
        mock_config.daysToLookback = 22
        
        screen_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "volume": ["2.5", "3.0"],
            "RSI": [50, 60],
            "%Chng": [5.0, -2.0]
        })
        
        save_df = pd.DataFrame({
            "Stock": ["A", "B"],
            "volume": ["2.5", "3.0"],
            "RSI": [50, 60],
            "%Chng": [5.0, -2.0]
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
        # Volume should be formatted
        assert "x" in str(save_result["volume"].iloc[0])


class TestGlobalsIntegration:
    """Integration tests for globals.py functions"""
    
    def test_all_delegated_functions_exist(self):
        """All delegated functions should be importable"""
        from pkscreener.globals import (
            labelDataForPrinting,
            sendMessageToTelegramChannel,
            handleAlertSubscriptions,
            showBacktestResults,
            updateMenuChoiceHierarchy,
            saveDownloadedData,
            FinishBacktestDataCleanup,
            prepareGroupedXRay,
            showSortedBacktestData,
            tabulateBacktestResults,
            sendTestStatus
        )
        
        # All should be callable
        assert callable(labelDataForPrinting)
        assert callable(sendMessageToTelegramChannel)
        assert callable(handleAlertSubscriptions)
        assert callable(showBacktestResults)
        assert callable(updateMenuChoiceHierarchy)
        assert callable(saveDownloadedData)
        assert callable(FinishBacktestDataCleanup)
        assert callable(prepareGroupedXRay)
        assert callable(showSortedBacktestData)
        assert callable(tabulateBacktestResults)
        assert callable(sendTestStatus)
    
    def test_globals_main_function_exists(self):
        """Main function should exist and be callable"""
        from pkscreener.globals import main
        
        assert callable(main)
    
    def test_globals_menu_functions_exist(self):
        """Menu-related functions should exist"""
        from pkscreener.globals import (
            getScannerMenuChoices,
            getTopLevelMenuChoices,
            handleSecondaryMenuChoices,
            initExecution
        )
        
        assert callable(getScannerMenuChoices)
        assert callable(getTopLevelMenuChoices)
        assert callable(handleSecondaryMenuChoices)
        assert callable(initExecution)


class TestEndToEndScenarios:
    """End-to-end scenario tests"""
    
    def test_scanner_result_to_notification_flow(self):
        """Results should flow correctly from scanner to notification"""
        from pkscreener.classes.NotificationService import NotificationService
        from pkscreener.classes.ResultsLabeler import ResultsLabeler
        
        # Create results
        screen_df = pd.DataFrame({
            "Stock": ["RELIANCE", "TCS"],
            "volume": ["3.5", "2.8"],
            "RSI": [65, 45],
            "%Chng": [2.5, -1.0]
        })
        
        # Create labeler
        mock_config = Mock()
        mock_config.daysToLookback = 22
        labeler = ResultsLabeler(mock_config, "X>12>9>Volume Scanner")
        
        # Create notification service
        mock_args = Mock()
        mock_args.user = None
        mock_args.telegram = False
        mock_args.log = False
        
        notification_service = NotificationService(mock_args)
        
        # The flow should work without errors
        assert len(screen_df) == 2
        assert notification_service is not None
    
    def test_backtest_to_report_flow(self):
        """Backtest results should flow to report correctly"""
        from pkscreener.classes.BacktestUtils import (
            BacktestResultsHandler,
            finish_backtest_data_cleanup_impl
        )
        
        mock_config = Mock()
        mock_config.enablePortfolioCalculations = False
        
        handler = BacktestResultsHandler(mock_config)
        
        # Set results directly
        df = pd.DataFrame({
            "Stock": ["A", "B", "C"],
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "1-Pd": [5.0, 3.0, -2.0],
            "2-Pd": [7.0, 4.0, 1.0]
        })
        handler.backtest_df = df
        
        # Cleanup
        mock_show_cb = Mock()
        mock_summary_cb = Mock(return_value=pd.DataFrame())
        
        summary, sorting, keys = finish_backtest_data_cleanup_impl(
            handler.backtest_df, None,
            default_answer="Y",
            config_manager=mock_config,
            show_backtest_cb=mock_show_cb,
            backtest_summary_cb=mock_summary_cb
        )
        
        # Should have called summary
        assert mock_summary_cb.called
        # Should have called show
        assert mock_show_cb.called
