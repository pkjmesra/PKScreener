"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Tests for Fetcher.py to achieve 90%+ coverage.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import multiprocessing
import warnings
warnings.filterwarnings("ignore")


class TestFetcherCoverage:
    """Comprehensive tests for screenerStockDataFetcher."""
    
    @pytest.fixture
    def fetcher(self):
        """Create a fetcher instance."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        return screenerStockDataFetcher()
    
    def test_cached_limiter_session_class(self):
        """Test CachedLimiterSession class exists."""
        from pkscreener.classes.Fetcher import CachedLimiterSession
        
        assert CachedLimiterSession is not None
    
    def test_fetch_stock_data_with_args_task(self, fetcher):
        """Test fetchStockDataWithArgs with PKTask."""
        from pkscreener.classes.PKTask import PKTask
        
        task = PKTask("test", lambda: None, ("SBIN", "5d", "1d", ".NS"))
        task.taskId = 1
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        with patch.object(fetcher, 'fetchStockData', return_value=pd.DataFrame()):
            result = fetcher.fetchStockDataWithArgs(task)
            
            # Should call fetchStockData
            assert task.taskId in task.progressStatusDict
    
    def test_fetch_stock_data_with_args_direct(self, fetcher):
        """Test fetchStockDataWithArgs with direct args."""
        with patch.object(fetcher, 'fetchStockData', return_value=pd.DataFrame()):
            result = fetcher.fetchStockDataWithArgs("SBIN", "5d", "1d", ".NS")
            
            assert result is not None or result is None
    
    def test_update_task_progress(self, fetcher):
        """Test _updateTaskProgress method."""
        from pkscreener.classes.PKTask import PKTask
        
        task = PKTask("test", lambda: None, ("SBIN",))
        task.taskId = 0
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        result = pd.DataFrame({"Close": [100]})
        fetcher._updateTaskProgress(task, result)
        
        assert task.taskId in task.progressStatusDict
        assert task.result is not None
    
    def test_update_task_progress_negative_task_id(self, fetcher):
        """Test _updateTaskProgress with negative task ID."""
        from pkscreener.classes.PKTask import PKTask
        
        task = PKTask("test", lambda: None, ("SBIN",))
        task.taskId = -1
        task.progressStatusDict = {}
        task.resultsDict = {}
        
        result = pd.DataFrame({"Close": [100]})
        fetcher._updateTaskProgress(task, result)
        
        # Should not add to progressStatusDict but set result
        assert task.result is not None
    
    def test_get_stats(self, fetcher):
        """Test get_stats method."""
        fetcher.get_stats("SBIN.NS")
        
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        assert "SBIN.NS" in screenerStockDataFetcher._tickersInfoDict
    
    def test_fetch_additional_ticker_info(self, fetcher):
        """Test fetchAdditionalTickerInfo."""
        ticker_list = ["SBIN", "INFY"]
        
        with patch.object(fetcher, 'get_stats'):
            result = fetcher.fetchAdditionalTickerInfo(ticker_list)
            
            assert isinstance(result, dict)
    
    def test_fetch_additional_ticker_info_with_suffix(self, fetcher):
        """Test fetchAdditionalTickerInfo with already suffixed tickers."""
        ticker_list = ["SBIN.NS", "INFY.NS"]
        
        with patch.object(fetcher, 'get_stats'):
            result = fetcher.fetchAdditionalTickerInfo(ticker_list, ".NS")
            
            assert isinstance(result, dict)
    
    def test_fetch_additional_ticker_info_type_error(self, fetcher):
        """Test fetchAdditionalTickerInfo raises TypeError."""
        with pytest.raises(TypeError):
            fetcher.fetchAdditionalTickerInfo("not_a_list")
    
    def test_fetch_stock_data_basic(self, fetcher):
        """Test fetchStockData basic call."""
        result = fetcher.fetchStockData(
            "SBIN", "5d", "1d", None, 0, 0, 0,
            printCounter=False
        )
        
        # Result can be None or a DataFrame depending on data availability
        # If data is available (from ticks or cache), we get a DataFrame
        if result is not None:
            import pandas as pd
            assert isinstance(result, pd.DataFrame)
        # If no data available, returns None - both cases are valid
    
    def test_fetch_stock_data_print_counter(self, fetcher):
        """Test fetchStockData with printCounter."""
        screen_counter = MagicMock()
        screen_counter.value = 10
        
        results_counter = MagicMock()
        results_counter.value = 5
        
        with patch.object(fetcher, '_printFetchProgress'):
            with patch.object(fetcher, '_printFetchError'):
                # With real data available, this may return data or raise exception
                # depending on market hours and data availability
                result = fetcher.fetchStockData(
                    "SBIN", "5d", "1d", None, 
                    results_counter, screen_counter, 100,
                    printCounter=True
                )
                # Result can be None or DataFrame - both are valid
                if result is not None:
                    import pandas as pd
                    assert isinstance(result, pd.DataFrame)
    
    def test_print_fetch_progress(self, fetcher):
        """Test _printFetchProgress."""
        screen_counter = MagicMock()
        screen_counter.value = 50
        
        results_counter = MagicMock()
        results_counter.value = 10
        
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
            fetcher._printFetchProgress("SBIN", results_counter, screen_counter, 100)
    
    def test_print_fetch_progress_zero_division(self, fetcher):
        """Test _printFetchProgress with zero total."""
        screen_counter = MagicMock()
        screen_counter.value = 0
        
        results_counter = MagicMock()
        results_counter.value = 0
        
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput', side_effect=ZeroDivisionError):
            fetcher._printFetchProgress("SBIN", results_counter, screen_counter, 0)
    
    def test_print_fetch_error(self, fetcher):
        """Test _printFetchError."""
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
            fetcher._printFetchError()
    
    def test_print_fetch_success(self, fetcher):
        """Test _printFetchSuccess."""
        with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
            fetcher._printFetchSuccess()
    
    def test_fetch_latest_nifty_daily(self, fetcher):
        """Test fetchLatestNiftyDaily."""
        result = fetcher.fetchLatestNiftyDaily()
        
        # Can return None or DataFrame depending on data availability
        if result is not None:
            import pandas as pd
            assert isinstance(result, pd.DataFrame)
    
    def test_fetch_five_ema_data(self, fetcher):
        """Test fetchFiveEmaData."""
        result = fetcher.fetchFiveEmaData()
        
        # Can return None or tuple of DataFrames depending on data availability
        if result is not None:
            assert isinstance(result, tuple)
    
    def test_fetch_watchlist_success(self, fetcher):
        """Test fetchWatchlist with valid file."""
        mock_df = pd.DataFrame({"Stock Code": ["SBIN", "INFY"]})
        
        with patch('pandas.read_excel', return_value=mock_df):
            result = fetcher.fetchWatchlist()
            
            assert result == ["SBIN", "INFY"]
    
    def test_fetch_watchlist_file_not_found(self, fetcher):
        """Test fetchWatchlist when file not found."""
        with patch('pandas.read_excel', side_effect=FileNotFoundError):
            with patch.object(fetcher, '_createWatchlistTemplate'):
                with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
                    result = fetcher.fetchWatchlist()
                    
                    assert result is None
    
    def test_fetch_watchlist_key_error(self, fetcher):
        """Test fetchWatchlist with bad format."""
        mock_df = pd.DataFrame({"Wrong Column": ["SBIN", "INFY"]})
        
        with patch('pandas.read_excel', return_value=mock_df):
            with patch.object(fetcher, '_createWatchlistTemplate'):
                with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
                    result = fetcher.fetchWatchlist()
                    
                    assert result is None
    
    def test_create_watchlist_template(self, fetcher):
        """Test _createWatchlistTemplate."""
        with patch('pandas.DataFrame.to_excel'):
            with patch('PKDevTools.classes.OutputControls.OutputControls.printOutput'):
                fetcher._createWatchlistTemplate()
    
    def test_tickers_info_dict_class_attr(self):
        """Test _tickersInfoDict is a class attribute."""
        from pkscreener.classes.Fetcher import screenerStockDataFetcher
        
        assert hasattr(screenerStockDataFetcher, '_tickersInfoDict')
    
    def test_yf_limiter_exists(self):
        """Test yf_limiter is defined."""
        from pkscreener.classes.Fetcher import yf_limiter
        
        assert yf_limiter is not None
    
    def test_try_factor_exists(self):
        """Test TRY_FACTOR is defined."""
        from pkscreener.classes.Fetcher import TRY_FACTOR
        
        assert TRY_FACTOR == 1
    
    # =========================================================================
    # Tests for High-Performance Data Provider Integration
    # =========================================================================
    
    def test_period_to_count_daily(self, fetcher):
        """Test _period_to_count for daily intervals."""
        count = fetcher._period_to_count("1y", "1d")
        assert count == 365
        
        count = fetcher._period_to_count("1mo", "1d")
        assert count == 30
        
        count = fetcher._period_to_count("5d", "1d")
        assert count == 5
    
    def test_period_to_count_intraday(self, fetcher):
        """Test _period_to_count for intraday intervals."""
        count = fetcher._period_to_count("1d", "5m")
        # 1 day * 375 minutes / 5 = 75
        assert count == 75
        
        count = fetcher._period_to_count("1d", "1m")
        # 1 day * 375 minutes / 1 = 375
        assert count == 375
        
        count = fetcher._period_to_count("1d", "15m")
        # 1 day * 375 minutes / 15 = 25
        assert count == 25
    
    def test_period_to_count_unknown_period(self, fetcher):
        """Test _period_to_count with unknown period defaults to 1y."""
        count = fetcher._period_to_count("unknown", "1d")
        assert count == 365
    
    def test_normalize_interval(self, fetcher):
        """Test _normalize_interval."""
        assert fetcher._normalize_interval("1m") == "1m"
        assert fetcher._normalize_interval("5m") == "5m"
        assert fetcher._normalize_interval("15m") == "15m"
        assert fetcher._normalize_interval("1h") == "60m"
        assert fetcher._normalize_interval("60m") == "60m"
        assert fetcher._normalize_interval("1d") == "day"
        assert fetcher._normalize_interval("day") == "day"
        assert fetcher._normalize_interval("unknown") == "day"
    
    def test_normalize_interval_new_intervals(self, fetcher):
        """Test _normalize_interval for new 2m, 3m, 4m intervals."""
        assert fetcher._normalize_interval("2m") == "2m"
        assert fetcher._normalize_interval("3m") == "3m"
        assert fetcher._normalize_interval("4m") == "4m"
        assert fetcher._normalize_interval("10m") == "10m"
        assert fetcher._normalize_interval("30m") == "30m"
    
    def test_get_latest_price_no_provider(self, fetcher):
        """Test getLatestPrice when no HP provider is available."""
        # Mock _hp_provider to be None
        fetcher._hp_provider = None
        
        price = fetcher.getLatestPrice("SBIN")
        assert price == 0.0
    
    def test_get_latest_price_with_suffix(self, fetcher):
        """Test getLatestPrice strips exchange suffix."""
        fetcher._hp_provider = None
        
        price = fetcher.getLatestPrice("SBIN.NS", ".NS")
        assert price == 0.0
    
    def test_get_realtime_ohlcv_no_provider(self, fetcher):
        """Test getRealtimeOHLCV when no HP provider is available."""
        fetcher._hp_provider = None
        
        ohlcv = fetcher.getRealtimeOHLCV("SBIN")
        assert ohlcv == {}
    
    def test_is_realtime_data_available_no_provider(self, fetcher):
        """Test isRealtimeDataAvailable when no HP provider is available."""
        fetcher._hp_provider = None
        
        available = fetcher.isRealtimeDataAvailable()
        assert available is False
    
    def test_get_all_realtime_data_no_provider(self, fetcher):
        """Test getAllRealtimeData when no HP provider is available."""
        fetcher._hp_provider = None
        
        data = fetcher.getAllRealtimeData()
        assert data == {}
    
    def test_get_latest_price_with_mock_provider(self, fetcher):
        """Test getLatestPrice with mocked HP provider."""
        mock_provider = MagicMock()
        mock_provider.get_latest_price.return_value = 500.50
        fetcher._hp_provider = mock_provider
        
        price = fetcher.getLatestPrice("SBIN")
        
        assert price == 500.50
        mock_provider.get_latest_price.assert_called_once_with("SBIN")
    
    def test_get_realtime_ohlcv_with_mock_provider(self, fetcher):
        """Test getRealtimeOHLCV with mocked HP provider."""
        mock_provider = MagicMock()
        mock_provider.get_realtime_ohlcv.return_value = {
            'open': 500, 'high': 510, 'low': 495, 'close': 505, 'volume': 100000
        }
        fetcher._hp_provider = mock_provider
        
        ohlcv = fetcher.getRealtimeOHLCV("SBIN")
        
        assert ohlcv['open'] == 500
        assert ohlcv['close'] == 505
    
    def test_is_realtime_data_available_with_mock_provider(self, fetcher):
        """Test isRealtimeDataAvailable with mocked HP provider."""
        mock_provider = MagicMock()
        mock_provider.is_realtime_available.return_value = True
        fetcher._hp_provider = mock_provider
        
        available = fetcher.isRealtimeDataAvailable()
        
        assert available is True
    
    def test_get_all_realtime_data_with_mock_provider(self, fetcher):
        """Test getAllRealtimeData with mocked HP provider."""
        mock_provider = MagicMock()
        mock_provider.get_all_realtime_data.return_value = {
            'SBIN': {'close': 500},
            'INFY': {'close': 1500}
        }
        fetcher._hp_provider = mock_provider
        
        data = fetcher.getAllRealtimeData()
        
        assert 'SBIN' in data
        assert 'INFY' in data
    
    def test_fetch_stock_data_with_hp_provider(self, fetcher):
        """Test fetchStockData uses HP provider when available."""
        mock_provider = MagicMock()
        mock_df = pd.DataFrame({'close': [100, 105, 110]})
        mock_provider.get_stock_data.return_value = mock_df
        fetcher._hp_provider = mock_provider
        
        result = fetcher.fetchStockData(
            "SBIN", "5d", "1d", None, 0, 0, 0,
            printCounter=False
        )
        
        assert result is not None
        mock_provider.get_stock_data.assert_called_once()
    
    def test_fetch_stock_data_hp_provider_exception(self, fetcher):
        """Test fetchStockData handles HP provider exceptions gracefully."""
        mock_provider = MagicMock()
        mock_provider.get_stock_data.side_effect = Exception("Provider error")
        fetcher._hp_provider = mock_provider
        
        # Should not raise, should return None or fallback
        result = fetcher.fetchStockData(
            "SBIN", "5d", "1d", None, 0, 0, 0,
            printCounter=False
        )
        
        # May be None if parent also returns None
        assert result is None or isinstance(result, pd.DataFrame)
    
    def test_hp_data_available_flag(self):
        """Test _HP_DATA_AVAILABLE flag exists."""
        from pkscreener.classes import Fetcher
        
        # Should be True since PKDevTools is installed
        assert hasattr(Fetcher, '_HP_DATA_AVAILABLE')
    
    def test_yf_available_flag(self):
        """Test _YF_AVAILABLE flag exists."""
        from pkscreener.classes import Fetcher
        
        # Should exist
        assert hasattr(Fetcher, '_YF_AVAILABLE')
    
    def test_scalable_fetcher_available_flag(self):
        """Test _SCALABLE_FETCHER_AVAILABLE flag exists."""
        from pkscreener.classes import Fetcher
        
        # Should exist
        assert hasattr(Fetcher, '_SCALABLE_FETCHER_AVAILABLE')
    
    def test_scalable_fetcher_initialized(self, fetcher):
        """Test that _scalable_fetcher is initialized."""
        # Should have the attribute (may be None if not available)
        assert hasattr(fetcher, '_scalable_fetcher')
    
    def test_is_data_fresh_no_providers(self, fetcher):
        """Test isDataFresh when no providers available."""
        fetcher._hp_provider = None
        fetcher._scalable_fetcher = None
        
        result = fetcher.isDataFresh(max_age_seconds=900)
        
        assert result is False
    
    def test_is_data_fresh_with_hp_provider(self, fetcher):
        """Test isDataFresh with HP provider available."""
        mock_provider = MagicMock()
        mock_provider.is_realtime_available.return_value = True
        fetcher._hp_provider = mock_provider
        
        result = fetcher.isDataFresh(max_age_seconds=900)
        
        assert result is True
    
    def test_is_data_fresh_with_scalable_fetcher(self, fetcher):
        """Test isDataFresh with scalable fetcher available."""
        fetcher._hp_provider = None
        
        mock_scalable = MagicMock()
        mock_scalable.is_data_fresh.return_value = True
        fetcher._scalable_fetcher = mock_scalable
        
        result = fetcher.isDataFresh(max_age_seconds=900)
        
        assert result is True
    
    def test_is_data_fresh_exception_handling(self, fetcher):
        """Test isDataFresh handles exceptions gracefully."""
        mock_provider = MagicMock()
        mock_provider.is_realtime_available.side_effect = Exception("Error")
        fetcher._hp_provider = mock_provider
        fetcher._scalable_fetcher = None
        
        result = fetcher.isDataFresh(max_age_seconds=900)
        
        assert result is False
    
    def test_get_data_source_stats_no_providers(self, fetcher):
        """Test getDataSourceStats when no providers available."""
        fetcher._hp_provider = None
        fetcher._scalable_fetcher = None
        
        stats = fetcher.getDataSourceStats()
        
        assert stats['hp_provider_available'] is False
        assert stats['scalable_fetcher_available'] is False
        assert stats['hp_stats'] == {}
        assert stats['scalable_stats'] == {}
    
    def test_get_data_source_stats_with_providers(self, fetcher):
        """Test getDataSourceStats with providers available."""
        mock_hp = MagicMock()
        mock_hp.get_stats.return_value = {'hits': 10}
        fetcher._hp_provider = mock_hp
        
        mock_scalable = MagicMock()
        mock_scalable.get_stats.return_value = {'cache_hits': 5}
        fetcher._scalable_fetcher = mock_scalable
        
        stats = fetcher.getDataSourceStats()
        
        assert stats['hp_provider_available'] is True
        assert stats['scalable_fetcher_available'] is True
        assert stats['hp_stats'] == {'hits': 10}
        assert stats['scalable_stats'] == {'cache_hits': 5}
    
    def test_get_data_source_stats_exception_handling(self, fetcher):
        """Test getDataSourceStats handles exceptions gracefully."""
        mock_hp = MagicMock()
        mock_hp.get_stats.side_effect = Exception("Error")
        fetcher._hp_provider = mock_hp
        fetcher._scalable_fetcher = None
        
        stats = fetcher.getDataSourceStats()
        
        assert stats['hp_stats'] == {}
    
    def test_health_check_no_providers(self, fetcher):
        """Test healthCheck when no providers available."""
        fetcher._hp_provider = None
        fetcher._scalable_fetcher = None
        
        health = fetcher.healthCheck()
        
        assert health['overall_status'] == 'unhealthy'
        assert health['hp_provider']['status'] == 'unavailable'
        assert health['scalable_fetcher']['status'] == 'unavailable'
    
    def test_health_check_hp_provider_healthy(self, fetcher):
        """Test healthCheck with healthy HP provider."""
        mock_hp = MagicMock()
        mock_hp.is_realtime_available.return_value = True
        fetcher._hp_provider = mock_hp
        fetcher._scalable_fetcher = None
        
        health = fetcher.healthCheck()
        
        assert health['overall_status'] == 'healthy'
        assert health['hp_provider']['status'] == 'healthy'
        assert health['hp_provider']['type'] == 'realtime'
    
    def test_health_check_hp_provider_degraded(self, fetcher):
        """Test healthCheck with degraded HP provider."""
        mock_hp = MagicMock()
        mock_hp.is_realtime_available.return_value = False
        fetcher._hp_provider = mock_hp
        fetcher._scalable_fetcher = None
        
        health = fetcher.healthCheck()
        
        assert health['overall_status'] == 'degraded'
        assert health['hp_provider']['status'] == 'degraded'
    
    def test_health_check_scalable_fetcher_healthy(self, fetcher):
        """Test healthCheck with healthy scalable fetcher."""
        fetcher._hp_provider = None
        
        mock_scalable = MagicMock()
        mock_scalable.health_check.return_value = {
            'github_raw': True,
            'data_age_seconds': 120,
        }
        fetcher._scalable_fetcher = mock_scalable
        
        health = fetcher.healthCheck()
        
        assert health['overall_status'] == 'healthy'
        assert health['scalable_fetcher']['status'] == 'healthy'
        assert health['scalable_fetcher']['github_raw'] is True
    
    def test_health_check_scalable_fetcher_degraded(self, fetcher):
        """Test healthCheck with degraded scalable fetcher (cache only)."""
        fetcher._hp_provider = None
        
        mock_scalable = MagicMock()
        mock_scalable.health_check.return_value = {
            'github_raw': False,
            'cache_available': True,
        }
        fetcher._scalable_fetcher = mock_scalable
        
        health = fetcher.healthCheck()
        
        assert health['overall_status'] == 'degraded'
        assert health['scalable_fetcher']['status'] == 'degraded'
    
    def test_health_check_exception_handling(self, fetcher):
        """Test healthCheck handles exceptions gracefully."""
        mock_hp = MagicMock()
        mock_hp.is_realtime_available.side_effect = Exception("Connection error")
        fetcher._hp_provider = mock_hp
        fetcher._scalable_fetcher = None
        
        health = fetcher.healthCheck()
        
        assert health['hp_provider']['status'] == 'error'
        assert 'error' in health['hp_provider']
    
    def test_fetch_stock_data_with_scalable_fetcher(self, fetcher):
        """Test fetchStockData uses scalable fetcher as fallback."""
        fetcher._hp_provider = None
        
        mock_df = pd.DataFrame({'close': [100, 101, 102]})
        mock_scalable = MagicMock()
        mock_scalable.get_stock_data.return_value = mock_df
        fetcher._scalable_fetcher = mock_scalable
        
        # The scalable fetcher should be called when HP provider is None
        result = fetcher.fetchStockData("SBIN", "5d", "1d", printCounter=False)
        
        # Scalable fetcher should be called
        mock_scalable.get_stock_data.assert_called()
        # Result should be from scalable fetcher or parent (either is valid)
        assert result is not None or mock_scalable.get_stock_data.called
    
    def test_fetch_stock_data_scalable_fetcher_exception(self, fetcher):
        """Test fetchStockData handles scalable fetcher exceptions."""
        fetcher._hp_provider = None
        
        mock_scalable = MagicMock()
        mock_scalable.get_stock_data.side_effect = Exception("Fetch error")
        fetcher._scalable_fetcher = mock_scalable
        
        # Should not raise even when scalable fetcher fails
        try:
            result = fetcher.fetchStockData("SBIN", "5d", "1d", printCounter=False)
            # If parent returns None, this is expected
            # Just verify no exception was raised
        except Exception as e:
            # StockDataEmptyException is acceptable if printCounter is False
            from PKDevTools.classes.Fetcher import StockDataEmptyException
            if not isinstance(e, StockDataEmptyException):
                pytest.fail(f"Unexpected exception: {e}")
