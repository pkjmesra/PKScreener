"""
Unit tests for DataLoader.py
Tests for stock data loading and preparation.
"""

import pytest
import pandas as pd
import os
from unittest.mock import Mock, MagicMock, patch, PropertyMock


class TestStockDataLoaderInit:
    """Tests for StockDataLoader initialization"""

    def test_init_default_values(self):
        """Should initialize with default values"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        config_manager = Mock()
        fetcher = Mock()
        
        loader = StockDataLoader(config_manager, fetcher)
        
        assert loader.config_manager == config_manager
        assert loader.fetcher == fetcher
        assert loader.stock_dict_primary is None
        assert loader.stock_dict_secondary is None
        assert loader.loaded_stock_data is False
        assert loader.load_count == 0


class TestStockDataLoaderInitializeDicts:
    """Tests for initialize_dicts method"""

    def test_initialize_with_mp_manager(self):
        """Should use mp_manager dicts when provided"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        mp_manager = Mock()
        mp_manager.dict.return_value = {}
        
        loader.initialize_dicts(mp_manager)
        
        assert mp_manager.dict.call_count == 2
        assert loader.load_count == 0

    def test_initialize_without_mp_manager(self):
        """Should use regular dicts when mp_manager is None"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        loader.initialize_dicts(None)
        
        assert isinstance(loader.stock_dict_primary, dict)
        assert isinstance(loader.stock_dict_secondary, dict)
        assert loader.load_count == 0


class TestStockDataLoaderShouldLoadSecondaryData:
    """Tests for _should_load_secondary_data method"""

    def test_returns_false_for_menu_c(self):
        """Should return False for menu option C"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        
        result = loader._should_load_secondary_data("C", None)
        assert result is False

    def test_returns_false_when_user_args_none(self):
        """Should return False when user_passed_args is None"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        
        result = loader._should_load_secondary_data("X", None)
        assert result is False

    def test_returns_true_for_monitor(self):
        """Should return True when monitor is set"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        user_args = Mock()
        user_args.monitor = True
        user_args.options = None
        
        result = loader._should_load_secondary_data("X", user_args)
        assert result is True

    def test_returns_true_for_pipe_intraday(self):
        """Should return True for pipe with intraday option"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        user_args = Mock()
        user_args.monitor = None
        user_args.options = "X:12|C:9:i"
        
        result = loader._should_load_secondary_data("X", user_args)
        assert result is True

    def test_returns_true_for_option_33_3(self):
        """Should return True for option 33:3"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        user_args = Mock()
        user_args.monitor = None
        user_args.options = "X:12:33:3:"
        
        result = loader._should_load_secondary_data("X", user_args)
        assert result is True

    def test_returns_true_for_option_32(self):
        """Should return True for option 32"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        user_args = Mock()
        user_args.monitor = None
        user_args.options = "X:12:32:1"
        
        result = loader._should_load_secondary_data("X", user_args)
        assert result is True

    def test_returns_false_for_regular_options(self):
        """Should return False for regular options"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        user_args = Mock()
        user_args.monitor = None
        user_args.options = "X:12:9:2.5"
        
        result = loader._should_load_secondary_data("X", user_args)
        assert result is False


class TestStockDataLoaderGetLatestTradeDatetime:
    """Tests for get_latest_trade_datetime method"""

    @patch('pkscreener.classes.DataLoader.PKDateUtilities')
    def test_empty_stock_dict(self, mock_utils):
        """Should return current datetime for empty stock dict"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_dt = Mock()
        mock_dt.strftime.side_effect = lambda fmt: "2025-01-01" if "Y" in fmt else "10:00:00"
        mock_utils.currentDateTime.return_value = mock_dt
        
        loader = StockDataLoader(Mock(), Mock())
        loader.stock_dict_primary = {}
        
        date, time = loader.get_latest_trade_datetime()
        
        assert date == "2025-01-01"
        assert time == "10:00:00"

    @patch('pkscreener.classes.DataLoader.PKDateUtilities')
    @patch('pkscreener.classes.DataLoader.pd')
    def test_valid_stock_dict(self, mock_pd, mock_utils):
        """Should extract datetime from stock data"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_dt = Mock()
        mock_dt.strftime.side_effect = lambda fmt: "2025-01-01" if "Y" in fmt else "10:00:00"
        mock_utils.currentDateTime.return_value = mock_dt
        
        loader = StockDataLoader(Mock(), Mock())
        loader.stock_dict_primary = {
            "RELIANCE": {
                "data": [[100, 105, 95, 102, 1000000]],
                "columns": ["Open", "High", "Low", "Close", "Volume"],
                "index": [1735689600]  # Unix timestamp
            }
        }
        
        # Mock DataFrame behavior
        mock_df = Mock()
        mock_df.index = [1735689600]
        mock_pd.DataFrame.return_value = mock_df
        
        mock_datetime = Mock()
        mock_datetime.strftime.side_effect = lambda fmt: "2025-01-01" if "Y" in fmt else "10:00:00"
        mock_pd.to_datetime.return_value = mock_datetime
        
        date, time = loader.get_latest_trade_datetime()


class TestStockDataLoaderPrepareStocksForScreening:
    """Tests for prepare_stocks_for_screening method"""

    def test_returns_existing_list(self):
        """Should return existing list if provided"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        existing_list = ["RELIANCE", "TCS", "INFY"]
        
        result = loader.prepare_stocks_for_screening(
            testing=False,
            download_only=False,
            list_stock_codes=existing_list,
            index_option=0
        )
        
        assert result == existing_list

    @patch('pkscreener.classes.DataLoader.SuppressOutput')
    @patch('pkscreener.classes.DataLoader.OutputControls')
    def test_fetches_stock_codes(self, mock_output, mock_suppress):
        """Should fetch stock codes when list is empty"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        fetcher = Mock()
        fetcher.fetchStockCodes.return_value = ["RELIANCE", "TCS"]
        config_manager = Mock()
        config_manager.shuffleEnabled = False
        
        mock_output.return_value.enableMultipleLineOutput = True
        
        loader = StockDataLoader(config_manager, fetcher)
        
        result = loader.prepare_stocks_for_screening(
            testing=False,
            download_only=False,
            list_stock_codes=None,
            index_option=0
        )
        
        fetcher.fetchStockCodes.assert_called_once()
        assert result == ["RELIANCE", "TCS"]

    @patch('pkscreener.classes.DataLoader.SuppressOutput')
    @patch('pkscreener.classes.DataLoader.OutputControls')
    def test_shuffles_when_enabled(self, mock_output, mock_suppress):
        """Should shuffle stocks when shuffleEnabled is True"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        fetcher = Mock()
        fetcher.fetchStockCodes.return_value = list(range(100))
        config_manager = Mock()
        config_manager.shuffleEnabled = True
        
        mock_output.return_value.enableMultipleLineOutput = True
        mock_output.return_value.printOutput = Mock()
        
        loader = StockDataLoader(config_manager, fetcher)
        
        result = loader.prepare_stocks_for_screening(
            testing=False,
            download_only=False,
            list_stock_codes=None,
            index_option=0
        )
        
        # Note: shuffling randomizes, so we just check it returns same length
        assert len(result) == 100


class TestStockDataLoaderHandleRequestForSpecificStocks:
    """Tests for handle_request_for_specific_stocks method"""

    def test_short_options_list(self):
        """Should return None for short options list"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        
        result = loader.handle_request_for_specific_stocks(["X", "12"], 0)
        assert result is None

    def test_comma_separated_stocks(self):
        """Should parse comma-separated stocks"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        
        result = loader.handle_request_for_specific_stocks(
            ["X", "12", "RELIANCE,TCS,INFY"], 0
        )
        
        assert result == ["RELIANCE", "TCS", "INFY"]

    def test_dot_separated_stocks(self):
        """Should parse dot-separated stocks"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        
        result = loader.handle_request_for_specific_stocks(
            ["X", "12", "RELIANCE.TCS.INFY"], 0
        )
        
        assert result == ["RELIANCE", "TCS", "INFY"]

    def test_uses_options_3_when_4_available(self):
        """Should use options[3] when 4 elements available"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        
        result = loader.handle_request_for_specific_stocks(
            ["X", "12", "9", "RELIANCE,TCS"], 0
        )
        
        assert result == ["RELIANCE", "TCS"]


class TestStockDataLoaderRefreshStockData:
    """Tests for refresh_stock_data method"""

    def test_resets_state(self):
        """Should reset all stock data state"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        loader.stock_dict_primary = {"data": "value"}
        loader.stock_dict_secondary = {"data": "value"}
        loader.loaded_stock_data = True
        
        loader.refresh_stock_data()
        
        assert loader.stock_dict_primary is None
        assert loader.stock_dict_secondary is None
        assert loader.loaded_stock_data is False


class TestStockDataLoaderSaveDownloadedData:
    """Tests for save_downloaded_data method"""

    def test_returns_early_on_interrupt(self):
        """Should return early when keyboard interrupt fired"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        loader = StockDataLoader(Mock(), Mock())
        
        result = loader.save_downloaded_data(
            download_only=True,
            testing=False,
            load_count=100,
            keyboard_interrupt_fired=True
        )
        
        assert result is None

    @patch('pkscreener.classes.DataLoader.PKDateUtilities')
    @patch('pkscreener.classes.DataLoader.AssetsManager')
    @patch('pkscreener.classes.DataLoader.OutputControls')
    def test_saves_when_download_only(self, mock_output, mock_assets, mock_utils):
        """Should save data in download only mode"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_utils.isTradingTime.return_value = False
        mock_output.return_value.printOutput = Mock()
        mock_assets.PKAssetsManager.saveStockData.return_value = "/path/to/file.pkl"
        
        config_manager = Mock()
        config_manager.cacheEnabled = True
        config_manager.isIntradayConfig.return_value = False
        
        loader = StockDataLoader(config_manager, Mock())
        loader.stock_dict_primary = {"data": "value"}
        
        # Mock os.stat to return a large file size
        with patch('pkscreener.classes.DataLoader.os') as mock_os:
            mock_os.path.exists.return_value = True
            mock_os.stat.return_value.st_size = 50 * 1024 * 1024  # 50MB
            
            result = loader.save_downloaded_data(
                download_only=True,
                testing=False,
                load_count=100,
                keyboard_interrupt_fired=False
            )
        
        mock_assets.PKAssetsManager.saveStockData.assert_called()


class TestSaveDownloadedDataImpl:
    """Tests for save_downloaded_data_impl function"""

    @patch('pkscreener.classes.DataLoader.PKDateUtilities')
    @patch('pkscreener.classes.DataLoader.AssetsManager')
    @patch('pkscreener.classes.DataLoader.OutputControls')
    def test_skips_when_trading(self, mock_output, mock_assets, mock_utils):
        """Should skip saving during trading hours"""
        from pkscreener.classes.DataLoader import save_downloaded_data_impl
        
        mock_utils.isTradingTime.return_value = True
        mock_output.return_value.printOutput = Mock()
        
        config_manager = Mock()
        config_manager.cacheEnabled = True
        config_manager.isIntradayConfig.return_value = False
        
        save_downloaded_data_impl(
            download_only=False,
            testing=False,
            stock_dict_primary={},
            config_manager=config_manager,
            load_count=100,
            keyboard_interrupt_fired=False
        )
        
        mock_output.return_value.printOutput.assert_called()

    def test_skips_on_keyboard_interrupt(self):
        """Should not save on keyboard interrupt"""
        from pkscreener.classes.DataLoader import save_downloaded_data_impl
        
        with patch('pkscreener.classes.DataLoader.AssetsManager') as mock_assets:
            save_downloaded_data_impl(
                download_only=True,
                testing=False,
                stock_dict_primary={},
                config_manager=Mock(),
                load_count=100,
                keyboard_interrupt_fired=True
            )
            
            mock_assets.PKAssetsManager.saveStockData.assert_not_called()


class TestStockDataLoaderLoadDatabaseOrFetch:
    """Tests for load_database_or_fetch method"""

    @patch('pkscreener.classes.DataLoader.AssetsManager')
    @patch('pkscreener.classes.DataLoader.Utility')
    def test_loads_primary_data(self, mock_utility, mock_assets):
        """Should load primary stock data"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_assets.PKAssetsManager.loadStockData.return_value = {"RELIANCE": {}}
        mock_utility.tools.loadLargeDeals = Mock()
        
        config_manager = Mock()
        config_manager.defaultIndex = 0
        
        loader = StockDataLoader(config_manager, Mock())
        
        primary, secondary = loader.load_database_or_fetch(
            download_only=False,
            list_stock_codes=["RELIANCE"],
            menu_option="X",
            index_option=0
        )
        
        mock_assets.PKAssetsManager.loadStockData.assert_called_once()
        assert loader.loaded_stock_data is True

    @patch('pkscreener.classes.DataLoader.AssetsManager')
    @patch('pkscreener.classes.DataLoader.Utility')
    def test_skips_for_menu_c(self, mock_utility, mock_assets):
        """Should skip primary load for menu option C"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        mock_utility.tools.loadLargeDeals = Mock()
        
        config_manager = Mock()
        config_manager.defaultIndex = 0
        
        loader = StockDataLoader(config_manager, Mock())
        
        primary, secondary = loader.load_database_or_fetch(
            download_only=False,
            list_stock_codes=["RELIANCE"],
            menu_option="C",
            index_option=0
        )
        
        mock_assets.PKAssetsManager.loadStockData.assert_not_called()


class TestStockDataLoaderTryLoadDataOnBackgroundThread:
    """Tests for try_load_data_on_background_thread method"""

    @patch('pkscreener.classes.DataLoader.SuppressOutput')
    @patch('pkscreener.classes.DataLoader.ConfigManager')
    def test_initializes_dicts_if_none(self, mock_config, mock_suppress):
        """Should initialize dicts if None"""
        from pkscreener.classes.DataLoader import StockDataLoader
        
        config_manager = Mock()
        config_manager.defaultIndex = "0"
        fetcher = Mock()
        fetcher.fetchStockCodes.return_value = []
        
        loader = StockDataLoader(config_manager, fetcher)
        loader.stock_dict_primary = None
        
        # Mock the load method to prevent actual loading
        loader.load_database_or_fetch = Mock()
        
        loader.try_load_data_on_background_thread()
        
        assert loader.stock_dict_primary is not None or loader.load_database_or_fetch.called
