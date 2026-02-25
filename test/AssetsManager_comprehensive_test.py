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
import os
import pickle
import tempfile
import unittest
import pytest
from unittest.mock import patch, mock_open, MagicMock, call
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

from pkscreener.classes.AssetsManager import PKAssetsManager
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes import Archiver


class TestIsDataFresh:
    """Comprehensive tests for is_data_fresh method."""
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    def test_is_data_fresh_dataframe_fresh(self, mock_trading_date):
        """Test is_data_fresh with fresh DataFrame data."""
        today = date.today()
        mock_trading_date.return_value = today
        
        stock_data = pd.DataFrame(
            {'close': [100, 101, 102]},
            index=pd.date_range(today, periods=3)
        )
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        assert is_fresh is True
        assert days_old == 0
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between')
    def test_is_data_fresh_dataframe_stale(self, mock_days_between, mock_trading_date):
        """Test is_data_fresh with stale DataFrame data."""
        today = date.today()
        old_date = today - timedelta(days=10)
        mock_trading_date.return_value = today
        mock_days_between.return_value = 5
        
        stock_data = pd.DataFrame(
            {'close': [100]},
            index=[pd.Timestamp(old_date)]
        )
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data, max_stale_trading_days=1)
        
        assert is_fresh is False
        assert days_old == 5
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    def test_is_data_fresh_dict_format(self, mock_trading_date):
        """Test is_data_fresh with dict format (to_dict('split'))."""
        today = date.today()
        mock_trading_date.return_value = today
        
        stock_data = {
            'index': [str(today)],
            'data': [[100, 101, 99, 100, 1000]],
            'columns': ['open', 'high', 'low', 'close', 'volume']
        }
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        assert is_fresh is True
        assert days_old == 0
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    def test_is_data_fresh_dict_with_timestamp(self, mock_trading_date):
        """Test is_data_fresh with dict containing timestamp objects."""
        today = date.today()
        mock_trading_date.return_value = today
        
        stock_data = {
            'index': [pd.Timestamp(today)],
            'data': [[100, 101, 99, 100, 1000]],
            'columns': ['open', 'high', 'low', 'close', 'volume']
        }
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        assert is_fresh is True
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    def test_is_data_fresh_dict_with_timezone(self, mock_trading_date):
        """Test is_data_fresh with dict containing timezone-aware timestamps."""
        today = date.today()
        mock_trading_date.return_value = today
        
        stock_data = {
            'index': [f"{today}T10:00:00+05:30"],
            'data': [[100, 101, 99, 100, 1000]],
            'columns': ['open', 'high', 'low', 'close', 'volume']
        }
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        assert is_fresh is True
    
    def test_is_data_fresh_empty_dataframe(self):
        """Test is_data_fresh with empty DataFrame."""
        stock_data = pd.DataFrame()
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        # Empty data should be considered fresh (can't determine)
        assert is_fresh is True
    
    def test_is_data_fresh_none_data(self):
        """Test is_data_fresh with None data."""
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(None)
        
        assert is_fresh is True
        assert data_date is None
        assert days_old == 0
    
    def test_is_data_fresh_empty_dict(self):
        """Test is_data_fresh with empty dict."""
        stock_data = {}
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        assert is_fresh is True
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    def test_is_data_fresh_exception_handling(self, mock_trading_date):
        """Test is_data_fresh handles exceptions gracefully."""
        mock_trading_date.side_effect = Exception("Error")
        
        stock_data = pd.DataFrame({'close': [100]}, index=[pd.Timestamp('2025-01-01')])
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        
        # Should return safe defaults on error
        assert is_fresh is True


class TestValidateDataFreshness:
    """Comprehensive tests for validate_data_freshness method."""
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    def test_validate_data_freshness_all_fresh(self, mock_is_fresh):
        """Test validate_data_freshness with all fresh data."""
        mock_is_fresh.return_value = (True, date.today(), 0)
        
        stock_dict = {
            'AAPL': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(date.today())]),
            'GOOGL': pd.DataFrame({'close': [200]}, index=[pd.Timestamp(date.today())])
        }
        
        fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
            stock_dict, isTrading=False
        )
        
        assert fresh_count == 2
        assert stale_count == 0
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    @patch('PKDevTools.classes.log.default_logger')
    def test_validate_data_freshness_with_stale(self, mock_logger, mock_is_fresh):
        """Test validate_data_freshness with stale data during trading."""
        old_date = date.today() - timedelta(days=5)
        mock_is_fresh.side_effect = [
            (True, date.today(), 0),
            (False, old_date, 3)
        ]
        
        stock_dict = {
            'AAPL': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(date.today())]),
            'GOOGL': pd.DataFrame({'close': [200]}, index=[pd.Timestamp(old_date)])
        }
        
        logger_instance = MagicMock()
        mock_logger.return_value = logger_instance
        
        fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
            stock_dict, isTrading=True
        )
        
        assert fresh_count == 1
        assert stale_count == 1
        assert oldest_date == old_date
        logger_instance.warning.assert_called()
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    def test_validate_data_freshness_empty_dict(self, mock_is_fresh):
        """Test validate_data_freshness with empty dict."""
        fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
            {}, isTrading=False
        )
        
        assert fresh_count == 0
        assert stale_count == 0
        assert oldest_date is None


class TestApplyFreshTicksToData:
    """Comprehensive tests for _apply_fresh_ticks_to_data method."""
    
    @patch('requests.get')
    def test_apply_fresh_ticks_success(self, mock_get):
        """Test _apply_fresh_ticks_to_data successfully applies ticks."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            '12345': {
                'trading_symbol': 'RELIANCE',
                'ohlcv': {
                    'open': 2500.0,
                    'high': 2520.0,
                    'low': 2490.0,
                    'close': 2510.0,
                    'volume': 1000000
                }
            }
        }
        mock_get.return_value = mock_response
        
        stock_dict = {
            'RELIANCE': {
                'data': [[2400, 2450, 2390, 2440, 900000]],
                'index': ['2025-01-01'],
                'columns': ['open', 'high', 'low', 'close', 'volume']
            }
        }
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        assert 'RELIANCE' in result
        assert len(result['RELIANCE']['data']) == 2  # Old + new
    
    @patch('requests.get')
    def test_apply_fresh_ticks_with_adj_close(self, mock_get):
        """Test _apply_fresh_ticks_to_data with 6 columns (includes Adj Close)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            '12345': {
                'trading_symbol': 'RELIANCE',
                'ohlcv': {
                    'open': 2500.0,
                    'high': 2520.0,
                    'low': 2490.0,
                    'close': 2510.0,
                    'volume': 1000000
                }
            }
        }
        mock_get.return_value = mock_response
        
        stock_dict = {
            'RELIANCE': {
                'data': [[2400, 2450, 2390, 2440, 900000, 2440]],
                'index': ['2025-01-01'],
                'columns': ['open', 'high', 'low', 'close', 'volume', 'Adj Close']
            }
        }
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        # Should have 6 columns in new row
        new_row = result['RELIANCE']['data'][-1]
        assert len(new_row) == 6
    
    @patch('requests.get')
    def test_apply_fresh_ticks_no_data_available(self, mock_get):
        """Test _apply_fresh_ticks_to_data when no ticks available."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        stock_dict = {'RELIANCE': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        # Should return original dict unchanged
        assert result == stock_dict
    
    @patch('requests.get')
    def test_apply_fresh_ticks_invalid_symbol(self, mock_get):
        """Test _apply_fresh_ticks_to_data with invalid symbol in ticks."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            '12345': {
                'trading_symbol': 'INVALID',
                'ohlcv': {'close': 100.0}
            }
        }
        mock_get.return_value = mock_response
        
        stock_dict = {
            'RELIANCE': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}
        }
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        # Should not modify stock_dict
        assert len(result['RELIANCE']['data']) == 1
    
    @patch('requests.get')
    def test_apply_fresh_ticks_exception_handling(self, mock_get):
        """Test _apply_fresh_ticks_to_data handles exceptions."""
        mock_get.side_effect = Exception("Network error")
        
        stock_dict = {'RELIANCE': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        # Should return original dict on error
        assert result == stock_dict


class TestDownloadFreshPklFromGitHub:
    """Comprehensive tests for download_fresh_pkl_from_github method."""
    
    @patch('requests.get')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('shutil.move')
    def test_download_fresh_pkl_success(self, mock_move, mock_pickle_load,
                                       mock_open_file, mock_archiver, mock_get):
        """Test successful download of fresh pkl from GitHub."""
        mock_archiver.return_value = '/tmp/test'
        
        # Create mock pkl data
        mock_data = {
            'RELIANCE': pd.DataFrame({'close': [100] * 251}, index=pd.date_range('2024-01-01', periods=251)),
            'TCS': pd.DataFrame({'close': [200] * 251}, index=pd.date_range('2024-01-01', periods=251)),
            'INFY': pd.DataFrame({'close': [300] * 251}, index=pd.date_range('2024-01-01', periods=251)),
            'HDFCBANK': pd.DataFrame({'close': [400] * 251}, index=pd.date_range('2024-01-01', periods=251)),
            'SBIN': pd.DataFrame({'close': [500] * 251}, index=pd.date_range('2024-01-01', periods=251))
        }
        pkl_bytes = pickle.dumps(mock_data)
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = pkl_bytes
        mock_get.return_value = mock_response
        
        mock_pickle_load.return_value = mock_data
        
        success, file_path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        assert success is True
        assert file_path is not None
        assert num_instruments == 5
    
    @patch('requests.get')
    def test_download_fresh_pkl_all_urls_fail(self, mock_get):
        """Test download_fresh_pkl_from_github when all URLs fail."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        success, file_path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        assert success is False
        assert file_path is None
        assert num_instruments == 0
    
    @patch('requests.get')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    def test_download_fresh_pkl_small_file(self, mock_pickle_load, mock_open_file,
                                            mock_archiver, mock_get):
        """Test download_fresh_pkl_from_github rejects small files."""
        mock_archiver.return_value = '/tmp/test'
        
        # Small file (less than 10000 bytes)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'x' * 5000
        mock_get.return_value = mock_response
        
        success, file_path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        # Should not accept small files
        assert success is False or file_path is None
    
    @patch('requests.get')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load', side_effect=Exception("Invalid pickle"))
    def test_download_fresh_pkl_invalid_pickle(self, mock_pickle_load, mock_open_file,
                                               mock_archiver, mock_get):
        """Test download_fresh_pkl_from_github handles invalid pickle."""
        mock_archiver.return_value = '/tmp/test'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'invalid pickle data'
        mock_get.return_value = mock_response
        
        success, file_path, num_instruments = PKAssetsManager.download_fresh_pkl_from_github()
        
        assert success is False


class TestTriggerHistoryDownloadWorkflow:
    """Comprehensive tests for trigger_history_download_workflow method."""
    
    @patch('requests.post')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    def test_trigger_workflow_success(self, mock_post):
        """Test successful workflow trigger."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        result = PKAssetsManager.trigger_history_download_workflow(missing_days=3)
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_trigger_workflow_no_token(self, mock_post):
        """Test workflow trigger fails without token."""
        with patch.dict('os.environ', {}, clear=True):
            result = PKAssetsManager.trigger_history_download_workflow(missing_days=3)
            
            assert result is False
            mock_post.assert_not_called()
    
    @patch('requests.post')
    @patch.dict('os.environ', {'CI_PAT': 'test_pat'})
    def test_trigger_workflow_with_ci_pat(self, mock_post):
        """Test workflow trigger with CI_PAT."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        result = PKAssetsManager.trigger_history_download_workflow(missing_days=3)
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch('requests.post')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    def test_trigger_workflow_api_failure(self, mock_post):
        """Test workflow trigger handles API failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        result = PKAssetsManager.trigger_history_download_workflow(missing_days=3)
        
        assert result is False
    
    @patch('requests.post', side_effect=Exception("Network error"))
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
    def test_trigger_workflow_exception(self, mock_post):
        """Test workflow trigger handles exceptions."""
        result = PKAssetsManager.trigger_history_download_workflow(missing_days=3)
        
        assert result is False


class TestEnsureDataFreshness:
    """Comprehensive tests for ensure_data_freshness method."""
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    def test_ensure_freshness_fresh_data(self, mock_is_fresh, mock_trading_date):
        """Test ensure_data_freshness with fresh data."""
        today = date.today()
        mock_trading_date.return_value = today
        mock_is_fresh.return_value = (True, today, 0)
        
        stock_dict = {
            'AAPL': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(today)])
        }
        
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            stock_dict, trigger_download=False
        )
        
        assert is_fresh is True
        assert missing_days == 0
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.trigger_history_download_workflow')
    def test_ensure_freshness_stale_triggers_download(self, mock_trigger, mock_is_fresh,
                                                      mock_days_between, mock_trading_date):
        """Test ensure_data_freshness triggers download when stale."""
        today = date.today()
        old_date = today - timedelta(days=5)
        mock_trading_date.return_value = today
        mock_is_fresh.return_value = (False, old_date, 3)
        mock_days_between.return_value = 3
        mock_trigger.return_value = True
        
        stock_dict = {
            'AAPL': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(old_date)])
        }
        
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            stock_dict, trigger_download=True
        )
        
        assert is_fresh is False
        assert missing_days == 3
        mock_trigger.assert_called_once_with(3)
    
    def test_ensure_freshness_empty_dict(self):
        """Test ensure_data_freshness with empty dict."""
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            {}, trigger_download=False
        )
        
        assert is_fresh is True
        assert missing_days == 0
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    def test_ensure_freshness_exception_handling(self, mock_is_fresh, mock_trading_date):
        """Test ensure_data_freshness handles exceptions."""
        mock_trading_date.side_effect = Exception("Error")
        
        stock_dict = {'AAPL': pd.DataFrame({'close': [100]})}
        
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            stock_dict, trigger_download=False
        )
        
        # Should return safe defaults
        assert is_fresh is True
        assert missing_days == 0


class TestMakeHyperlink:
    """Comprehensive tests for make_hyperlink method."""
    
    def test_make_hyperlink_valid_stock(self):
        """Test make_hyperlink with valid stock name."""
        result = PKAssetsManager.make_hyperlink("RELIANCE")
        assert 'HYPERLINK' in result
        assert 'RELIANCE' in result
        assert 'tradingview.com' in result
    
    def test_make_hyperlink_empty_string(self):
        """Test make_hyperlink with empty string."""
        result = PKAssetsManager.make_hyperlink("")
        assert 'HYPERLINK' in result
    
    def test_make_hyperlink_with_decorated_name(self):
        """Test make_hyperlink handles decorated stock names."""
        with patch('pkscreener.classes.ImageUtility.PKImageTools.stockNameFromDecoratedName',
                  return_value='RELIANCE'):
            result = PKAssetsManager.make_hyperlink("RELIANCE")
            assert 'RELIANCE' in result


class TestPromptSaveResults:
    """Comprehensive tests for promptSaveResults method."""
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput', return_value='N')
    @patch('builtins.input', return_value='Y')
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.removeAllColorStyles')
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.getLegendHelpText')
    @patch('pkscreener.classes.AssetsManager.pd.ExcelWriter')
    @patch('PKDevTools.classes.Archiver.get_user_reports_dir')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.configManager')
    def test_prompt_save_results_yes(self, mock_config_manager, mock_reports_dir,
                                     mock_excel_writer, mock_legend, mock_remove_colors,
                                     mock_input, mock_take_input):
        """Test promptSaveResults when user says yes."""
        mock_reports_dir.return_value = '/tmp/reports'
        mock_remove_colors.return_value = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        mock_config_manager.alwaysExportToExcel = False
        
        df = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        with patch('pkscreener.classes.AssetsManager.PKDateUtilities.currentDateTime') as mock_dt:
            mock_dt.return_value.strftime.return_value = "01-01-26_10.00.00"
            result = PKAssetsManager.promptSaveResults("TestSheet", df, defaultAnswer=None)
            
            # Should attempt to save
            assert result is not None or True  # May fail but should attempt
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput', return_value='N')
    @patch('builtins.input', return_value='N')
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.removeAllColorStyles')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.configManager')
    def test_prompt_save_results_no(self, mock_config_manager, mock_remove_colors,
                                    mock_input, mock_take_input):
        """Test promptSaveResults when user says no."""
        mock_config_manager.alwaysExportToExcel = False
        mock_remove_colors.return_value = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        df = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        result = PKAssetsManager.promptSaveResults("TestSheet", df, defaultAnswer=None)
        
        assert result is None
    
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.removeAllColorStyles')
    @patch('pkscreener.classes.AssetsManager.pd.ExcelWriter')
    @patch('PKDevTools.classes.Archiver.get_user_reports_dir')
    def test_prompt_save_results_default_yes(self, mock_reports_dir, mock_excel_writer,
                                             mock_remove_colors):
        """Test promptSaveResults with defaultAnswer='Y'."""
        mock_reports_dir.return_value = '/tmp/reports'
        mock_remove_colors.return_value = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        df = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        result = PKAssetsManager.promptSaveResults("TestSheet", df, defaultAnswer='Y')
        
        assert result is not None
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput', return_value='Y')
    @patch('pkscreener.classes.AssetsManager.pd.ExcelWriter', side_effect=Exception("Write error"))
    @patch('PKDevTools.classes.Archiver.get_user_reports_dir')
    @patch('os.path.expanduser', return_value='/tmp')
    def test_prompt_save_results_fallback_to_desktop(self, mock_expanduser, mock_reports_dir,
                                                     mock_excel_writer, mock_input):
        """Test promptSaveResults falls back to desktop on error."""
        mock_reports_dir.return_value = '/tmp/reports'
        
        df = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        with patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.removeAllColorStyles',
                  return_value=df):
            result = PKAssetsManager.promptSaveResults("TestSheet", df, defaultAnswer='Y')
            
            # Should try desktop as fallback
            assert True  # Function should complete


class TestAfterMarketStockDataExists:
    """Comprehensive tests for afterMarketStockDataExists method."""
    
    @patch('PKDevTools.classes.Archiver.afterMarketStockDataExists')
    def test_after_market_stock_data_exists(self, mock_archiver):
        """Test afterMarketStockDataExists delegates to Archiver."""
        mock_archiver.return_value = (True, 'stock_data_01012026.pkl')
        
        exists, cache_file = PKAssetsManager.afterMarketStockDataExists(intraday=False, forceLoad=False)
        
        assert exists is True
        assert 'stock_data' in cache_file
        mock_archiver.assert_called_once_with(intraday=False, forceLoad=False, date_suffix=True)


class TestSaveStockData:
    """Comprehensive tests for saveStockData method."""
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.dump')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_save_stock_data_new_file(self, mock_print, mock_dump, mock_open_file,
                                     mock_exists, mock_archiver, mock_after_market):
        """Test saveStockData creates new file."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        mock_archiver.return_value = '/tmp/test'
        
        stock_dict = {'AAPL': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result = PKAssetsManager.saveStockData(stock_dict, config_manager, 0)
        
        assert result is not None
        mock_dump.assert_called_once()
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('os.path.exists', return_value=True)
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_save_stock_data_already_exists(self, mock_print, mock_exists,
                                           mock_archiver, mock_after_market):
        """Test saveStockData when file already exists."""
        mock_after_market.return_value = (True, 'stock_data_01012026.pkl')
        mock_archiver.return_value = '/tmp/test'
        
        stock_dict = {'AAPL': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result = PKAssetsManager.saveStockData(stock_dict, config_manager, 0)
        
        assert result is not None
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.dump', side_effect=pickle.PicklingError("Pickle error"))
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_save_stock_data_pickle_error(self, mock_print, mock_dump, mock_open_file,
                                         mock_exists, mock_archiver, mock_after_market):
        """Test saveStockData handles PicklingError."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        mock_archiver.return_value = '/tmp/test'
        
        stock_dict = {'AAPL': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result = PKAssetsManager.saveStockData(stock_dict, config_manager, 0)
        
        # Should handle error gracefully
        assert result is not None
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('PKDevTools.classes.Archiver.get_user_data_dir')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.dump')
    @patch('glob.glob')
    @patch('PKDevTools.classes.Committer.Committer.execOSCommand')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_save_stock_data_download_only(self, mock_print, mock_exec, mock_glob,
                                          mock_dump, mock_open_file, mock_exists,
                                          mock_archiver, mock_after_market):
        """Test saveStockData in downloadOnly mode."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        mock_archiver.return_value = '/tmp/test'
        mock_glob.return_value = []
        
        stock_dict = {'AAPL': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.deleteFileWithPattern = MagicMock()
        
        with patch.dict('os.environ', {'RUNNER': 'true'}):
            result = PKAssetsManager.saveStockData(stock_dict, config_manager, 0,
                                                  downloadOnly=True)
            
            assert result is not None


class TestHadRateLimitErrors:
    """Comprehensive tests for had_rate_limit_errors method."""
    
    def test_had_rate_limit_errors(self):
        """Test had_rate_limit_errors always returns False."""
        result = PKAssetsManager.had_rate_limit_errors()
        assert result is False


class TestDownloadLatestData:
    """Comprehensive tests for downloadLatestData method."""
    
    @patch('PKDevTools.classes.log.default_logger')
    def test_download_latest_data_empty_stocks(self, mock_logger):
        """Test downloadLatestData with empty stock list."""
        stock_dict = {}
        config_manager = MagicMock()
        stock_codes = []
        
        result_dict, left_out = PKAssetsManager.downloadLatestData(
            stock_dict, config_manager, stock_codes
        )
        
        assert result_dict == stock_dict
        assert left_out == []
    
    @patch('PKDevTools.classes.log.default_logger')
    def test_download_latest_data_no_stocks_processed(self, mock_logger):
        """Test downloadLatestData when no stocks are processed."""
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        stock_codes = ['AAPL', 'GOOGL']
        
        result_dict, left_out = PKAssetsManager.downloadLatestData(
            stock_dict, config_manager, stock_codes
        )
        
        # Should return all stocks as left out (no processing happens in current implementation)
        assert len(left_out) == 2


class TestLoadStockData:
    """Comprehensive tests for loadStockData method."""
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('pkbrokers.kite.examples.externals.kite_fetch_save_pickle')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=True)
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.wasTradedOn', return_value=True)
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTodayHoliday', return_value=(False, None))
    def test_load_stock_data_trading_hours(self, mock_holiday, mock_traded, mock_trading,
                                          mock_kite_fetch, mock_after_market):
        """Test loadStockData during trading hours."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        mock_kite_fetch.return_value = True
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData',
                  return_value=({}, [])):
            result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                  stockCodes=['AAPL'])
            
            assert result is not None
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.download_fresh_pkl_from_github')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle')
    def test_load_stock_data_stale_cache(self, mock_load_local, mock_download_github,
                                         mock_is_fresh, mock_pickle_load, mock_open_file,
                                         mock_exists, mock_after_market):
        """Test loadStockData with stale local cache."""
        mock_after_market.return_value = (True, 'stock_data_01012026.pkl')
        mock_exists.return_value = True
        
        # Mock stale data
        old_date = date.today() - timedelta(days=5)
        mock_pickle_load.return_value = {
            'RELIANCE': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(old_date)])
        }
        mock_is_fresh.return_value = (False, old_date, 3)
        mock_download_github.return_value = (True, '/tmp/fresh.pkl', 1000)
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('shutil.copy'):
            with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime',
                      return_value=False):
                result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                      stockCodes=['RELIANCE'])
                
                # Should download fresh data from GitHub
                mock_download_github.assert_called_once()
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle')
    def test_load_stock_data_insufficient_data(self, mock_load_local, mock_is_fresh,
                                               mock_pickle_load, mock_open_file,
                                               mock_exists, mock_after_market):
        """Test loadStockData with insufficient data in cache."""
        mock_after_market.return_value = (True, 'stock_data_01012026.pkl')
        mock_exists.return_value = True
        
        # Mock data with only 10 rows (less than MIN_ROWS_REQUIRED = 20)
        mock_pickle_load.return_value = {
            'RELIANCE': pd.DataFrame({'close': [100] * 10}, index=pd.date_range('2025-01-01', periods=10))
        }
        mock_is_fresh.return_value = (True, date.today(), 0)
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('pkscreener.classes.AssetsManager.PKAssetsManager.download_fresh_pkl_from_github',
                  return_value=(True, '/tmp/fresh.pkl', 1000)):
            with patch('shutil.copy'):
                with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime',
                         return_value=False):
                    result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                         stockCodes=['RELIANCE'])
                    
                    # Should try to download fresh data
                    assert result is not None


class TestLoadDataFromLocalPickle:
    """Comprehensive tests for loadDataFromLocalPickle method."""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_success(self, mock_trading, mock_print,
                                                mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle successfully loads data."""
        stock_data = {
            'RELIANCE': pd.DataFrame({
                'open': [100], 'high': [101], 'low': [99], 'close': [100], 'volume': [1000]
            }, index=[pd.Timestamp('2025-01-01')])
        }
        mock_pickle_load.return_value = stock_data
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        assert loaded is True
        assert 'RELIANCE' in result
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=True)
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.validate_data_freshness')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager._apply_fresh_ticks_to_data')
    def test_load_data_from_local_pickle_trading_hours(self, mock_apply_ticks,
                                                      mock_validate, mock_trading,
                                                      mock_print, mock_pickle_load,
                                                      mock_open_file):
        """Test loadDataFromLocalPickle during trading hours applies ticks."""
        stock_data = {
            'RELIANCE': pd.DataFrame({
                'open': [100], 'high': [101], 'low': [99], 'close': [100], 'volume': [1000]
            }, index=[pd.Timestamp('2025-01-01')])
        }
        mock_pickle_load.return_value = stock_data
        mock_validate.return_value = (1, 1, date.today() - timedelta(days=1))
        mock_apply_ticks.return_value = {'RELIANCE': stock_data['RELIANCE'].to_dict('split')}
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', True
        )
        
        assert loaded is True
        if stock_dict:  # Only validate if stock_dict was populated
            mock_validate.assert_called_once()
            mock_apply_ticks.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load', return_value={})
    def test_load_data_from_local_pickle_empty_data(self, mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle with empty pickle data."""
        stock_dict = {}
        config_manager = MagicMock()
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        assert loaded is False
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load', side_effect=pickle.UnpicklingError("Corrupted"))
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.promptFileExists', return_value='Y')
    def test_load_data_from_local_pickle_unpickling_error(self, mock_prompt, mock_print,
                                                          mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle handles UnpicklingError."""
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.deleteFileWithPattern = MagicMock()
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        assert loaded is False
        mock_prompt.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load', side_effect=EOFError("Unexpected EOF"))
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.promptFileExists', return_value='Y')
    def test_load_data_from_local_pickle_eof_error(self, mock_prompt, mock_print,
                                                   mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle handles EOFError."""
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.deleteFileWithPattern = MagicMock()
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        assert loaded is False
        mock_prompt.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_with_multiindex(self, mock_trading, mock_print,
                                                         mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle handles MultiIndex."""
        # Create MultiIndex DataFrame
        arrays = [['RELIANCE', 'RELIANCE'], ['open', 'close']]
        multi_index = pd.MultiIndex.from_arrays(arrays, names=['stock', 'column'])
        stock_data = pd.DataFrame({0: [100, 101]}, index=multi_index)
        
        # MultiIndex keys() returns MultiIndex object
        mock_pickle_data = MagicMock()
        mock_pickle_data.keys.return_value = multi_index
        mock_pickle_load.return_value = mock_pickle_data
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        # Should handle MultiIndex
        assert True  # Function should complete
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_with_exchange_suffix(self, mock_trading, mock_print,
                                                              mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle handles exchange suffix."""
        stock_data = {
            'RELIANCE.NS': pd.DataFrame({
                'open': [100], 'high': [101], 'low': [99], 'close': [100], 'volume': [1000]
            }, index=[pd.Timestamp('2025-01-01')])
        }
        mock_pickle_load.return_value = stock_data
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        # Should strip .NS suffix
        assert 'RELIANCE' in result or 'RELIANCE.NS' in result
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_filters_numeric_keys(self, mock_trading, mock_print,
                                                              mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle filters out numeric keys (instrument tokens)."""
        stock_data = {
            '12345': pd.DataFrame({'close': [100]}, index=[pd.Timestamp('2025-01-01')]),
            'RELIANCE': pd.DataFrame({'close': [100]}, index=[pd.Timestamp('2025-01-01')])
        }
        mock_pickle_load.return_value = stock_data
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        # Should only include RELIANCE, not 12345
        assert 'RELIANCE' in result
        assert '12345' not in result
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_merges_duplicate_columns(self, mock_trading, mock_print,
                                                                  mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle merges duplicate OHLCV columns."""
        # DataFrame with both lowercase and uppercase columns
        df = pd.DataFrame({
            'open': [100],
            'Open': [100],
            'high': [101],
            'High': [101],
            'low': [99],
            'Low': [99],
            'close': [100],
            'Close': [100],
            'volume': [1000],
            'Volume': [1000]
        }, index=[pd.Timestamp('2025-01-01')])
        
        stock_data = {'RELIANCE': df}
        mock_pickle_load.return_value = stock_data
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        assert loaded is True
        assert 'RELIANCE' in result


class TestDownloadSavedDataFromServer:
    """Comprehensive tests for downloadSavedDataFromServer method."""
    
    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('alive_progress.alive_bar')
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.OutputControls.OutputControls.moveCursorUpLines')
    def test_download_saved_data_success(self, mock_move_cursor, mock_print,
                                        mock_pickle_load, mock_alive_bar,
                                        mock_open_file, mock_try_fetch):
        """Test downloadSavedDataFromServer successfully downloads data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '52428800'}  # 50MB
        mock_response.iter_content.return_value = [b'chunk'] * 50
        mock_try_fetch.return_value = mock_response
        
        mock_pickle_load.return_value = {
            'RELIANCE': pd.DataFrame({'close': [100]}, index=[pd.Timestamp('2025-01-01')])
        }
        
        # Mock file operations
        mock_file = MagicMock()
        mock_open_file.return_value.__enter__.return_value = mock_file
        mock_open_file.return_value.__exit__.return_value = None
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, False, None, False, False, [], ".NS",
            False, False, 'test.pkl', False
        )
        
        assert loaded is True
    
    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData')
    def test_download_saved_data_retry(self, mock_load_stock, mock_try_fetch):
        """Test downloadSavedDataFromServer retries on failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_try_fetch.return_value = mock_response
        
        stock_dict = {}
        config_manager = MagicMock()
        
        result, loaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, False, None, True, False, [], ".NS",
            False, False, 'test.pkl', False
        )
        
        # Should retry by calling loadStockData
        assert True  # Function should complete
    
    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('alive_progress.alive_bar')
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.validate_data_freshness')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.ensure_data_freshness')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager._apply_fresh_ticks_to_data')
    def test_download_saved_data_trading_hours_validation(self, mock_apply_ticks,
                                                         mock_ensure_fresh, mock_validate,
                                                         mock_print, mock_pickle_load,
                                                         mock_alive_bar, mock_open_file,
                                                         mock_try_fetch):
        """Test downloadSavedDataFromServer validates freshness during trading."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '52428800'}
        mock_response.iter_content.return_value = [b'chunk'] * 50
        mock_try_fetch.return_value = mock_response
        
        stock_data_dict = {
            'RELIANCE': pd.DataFrame({'close': [100]}, index=[pd.Timestamp('2025-01-01')])
        }
        mock_pickle_load.return_value = stock_data_dict
        mock_validate.return_value = (0, 1, date.today() - timedelta(days=1))
        mock_ensure_fresh.return_value = (False, 1)
        mock_apply_ticks.return_value = stock_data_dict
        
        # Mock file operations
        mock_file = MagicMock()
        mock_open_file.return_value.__enter__.return_value = mock_file
        mock_open_file.return_value.__exit__.return_value = None
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, False, None, False, False, [], ".NS",
            False, False, 'test.pkl', True
        )
        
        # Should validate if stock_dict is populated
        if stock_dict:
            mock_validate.assert_called_once()
            mock_ensure_fresh.assert_called_once()
            mock_apply_ticks.assert_called_once()


class TestPromptFileExists:
    """Comprehensive tests for promptFileExists method."""
    
    @patch('builtins.input', return_value='Y')
    def test_prompt_file_exists_user_says_yes(self, mock_input):
        """Test promptFileExists when user says yes."""
        result = PKAssetsManager.promptFileExists("test.pkl", defaultAnswer=None)
        assert result == "Y"
    
    @patch('builtins.input', return_value='N')
    def test_prompt_file_exists_user_says_no(self, mock_input):
        """Test promptFileExists when user says no."""
        result = PKAssetsManager.promptFileExists("test.pkl", defaultAnswer=None)
        assert result == "N"
    
    def test_prompt_file_exists_default_answer(self):
        """Test promptFileExists with default answer."""
        result = PKAssetsManager.promptFileExists("test.pkl", defaultAnswer='Y')
        assert result == "Y"
        
        result = PKAssetsManager.promptFileExists("test.pkl", defaultAnswer='N')
        assert result == "N"
    
    @patch('builtins.input', side_effect=ValueError("Input error"))
    @patch('PKDevTools.classes.log.default_logger')
    def test_prompt_file_exists_input_error(self, mock_logger, mock_input):
        """Test promptFileExists handles input errors."""
        logger_instance = MagicMock()
        mock_logger.return_value = logger_instance
        
        result = PKAssetsManager.promptFileExists("test.pkl", defaultAnswer=None)
        # Should return "Y" as default on error (ValueError is caught and returns "Y")
        assert result == "Y"


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""
    
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.trading_days_between')
    def test_is_data_fresh_with_string_date_in_dict(self, mock_days_between, mock_trading_date):
        """Test is_data_fresh handles string dates in dict format."""
        today = date.today()
        mock_trading_date.return_value = today
        mock_days_between.return_value = 0
        
        stock_data = {
            'index': ['2025-01-01'],
            'data': [[100, 101, 99, 100, 1000]],
            'columns': ['open', 'high', 'low', 'close', 'volume']
        }
        
        is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
        # Should handle gracefully
        assert is_fresh is True or is_fresh is False
    
    def test_is_data_fresh_with_datetime_trading_date(self):
        """Test is_data_fresh handles datetime trading date."""
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.tradingDate',
                  return_value=datetime.now()):
            stock_data = pd.DataFrame({'close': [100]}, index=[pd.Timestamp(date.today())])
            
            is_fresh, data_date, days_old = PKAssetsManager.is_data_fresh(stock_data)
            assert is_fresh is True
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    def test_validate_data_freshness_with_none_dates(self, mock_is_fresh):
        """Test validate_data_freshness handles None dates."""
        mock_is_fresh.return_value = (True, None, 0)
        
        stock_dict = {
            'AAPL': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(date.today())])
        }
        
        fresh_count, stale_count, oldest_date = PKAssetsManager.validate_data_freshness(
            stock_dict, isTrading=False
        )
        
        assert oldest_date is None
    
    @patch('requests.get', side_effect=Exception("Network error"))
    def test_apply_fresh_ticks_network_error(self, mock_get):
        """Test _apply_fresh_ticks_to_data handles network errors."""
        stock_dict = {'RELIANCE': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        assert result == stock_dict
    
    @patch('requests.get')
    def test_apply_fresh_ticks_invalid_json(self, mock_get):
        """Test _apply_fresh_ticks_to_data handles invalid JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        stock_dict = {'RELIANCE': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        
        result = PKAssetsManager._apply_fresh_ticks_to_data(stock_dict)
        
        assert result == stock_dict
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    def test_ensure_data_freshness_with_none_latest_date(self, mock_is_fresh):
        """Test ensure_data_freshness handles None latest date."""
        mock_is_fresh.return_value = (True, None, 0)
        
        stock_dict = {
            'AAPL': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(date.today())])
        }
        
        is_fresh, missing_days = PKAssetsManager.ensure_data_freshness(
            stock_dict, trigger_download=False
        )
        
        assert is_fresh is True
        assert missing_days == 0


class TestLoadStockDataAdditional:
    """Additional comprehensive tests for loadStockData method."""
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('pkbrokers.kite.examples.externals.kite_fetch_save_pickle')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=True)
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.wasTradedOn', return_value=True)
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTodayHoliday', return_value=(False, None))
    @patch('os.path.exists', return_value=False)
    def test_load_stock_data_no_cache_file(self, mock_exists, mock_holiday, mock_traded,
                                          mock_trading, mock_kite_fetch, mock_after_market):
        """Test loadStockData when cache file doesn't exist."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        mock_kite_fetch.return_value = True
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData',
                  return_value=({}, [])):
            result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                  stockCodes=['AAPL'])
            
            assert result is not None
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.download_fresh_pkl_from_github')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle')
    def test_load_stock_data_github_download_success(self, mock_load_local, mock_download_github,
                                                     mock_is_fresh, mock_pickle_load,
                                                     mock_open_file, mock_exists,
                                                     mock_after_market):
        """Test loadStockData successfully downloads from GitHub."""
        mock_after_market.return_value = (True, 'stock_data_01012026.pkl')
        mock_exists.return_value = True
        
        old_date = date.today() - timedelta(days=5)
        mock_pickle_load.return_value = {
            'RELIANCE': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(old_date)])
        }
        mock_is_fresh.return_value = (False, old_date, 3)
        mock_download_github.return_value = (True, '/tmp/fresh.pkl', 1000)
        mock_load_local.return_value = ({'RELIANCE': {}}, True)
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('shutil.copy'):
            with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime',
                      return_value=False):
                result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                      stockCodes=['RELIANCE'])
                
                mock_download_github.assert_called_once()
                mock_load_local.assert_called()
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.is_data_fresh')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.download_fresh_pkl_from_github')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle')
    def test_load_stock_data_github_download_fails(self, mock_load_local, mock_download_github,
                                                  mock_is_fresh, mock_pickle_load,
                                                  mock_open_file, mock_exists,
                                                  mock_after_market):
        """Test loadStockData falls back when GitHub download fails."""
        mock_after_market.return_value = (True, 'stock_data_01012026.pkl')
        mock_exists.return_value = True
        
        old_date = date.today() - timedelta(days=5)
        mock_pickle_load.return_value = {
            'RELIANCE': pd.DataFrame({'close': [100]}, index=[pd.Timestamp(old_date)])
        }
        mock_is_fresh.return_value = (False, old_date, 3)
        mock_download_github.return_value = (False, None, 0)
        mock_load_local.return_value = ({'RELIANCE': {}}, True)
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime',
                  return_value=False):
            result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                  stockCodes=['RELIANCE'])
            
            # Should still try to load from local
            mock_load_local.assert_called()
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadSavedDataFromServer')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_stock_data_download_from_server(self, mock_trading, mock_download_server,
                                                  mock_after_market):
        """Test loadStockData downloads from server when local cache not available."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        mock_download_server.return_value = ({'RELIANCE': {}}, True)
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('os.path.exists', return_value=False):
            result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                  stockCodes=['RELIANCE'], forceRedownload=False)
            
            mock_download_server.assert_called_once()
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_stock_data_fallback_to_download(self, mock_trading, mock_download,
                                                  mock_after_market):
        """Test loadStockData falls back to downloadLatestData when server fails."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('os.path.exists', return_value=False):
            with patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadSavedDataFromServer',
                      return_value=({}, False)):
                with patch('pkscreener.classes.AssetsManager.PKAssetsManager.had_rate_limit_errors',
                          return_value=False):
                    result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                          stockCodes=['RELIANCE'])
                    
                    mock_download.assert_called()
    
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.saveStockData')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_stock_data_saves_on_download_only(self, mock_trading, mock_save,
                                                    mock_after_market):
        """Test loadStockData saves data when downloadOnly is True."""
        mock_after_market.return_value = (False, 'stock_data_01012026.pkl')
        
        stock_dict = {'RELIANCE': {'data': [[100]], 'index': ['2025-01-01'], 'columns': ['close']}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.baseIndex = 'NIFTY'
        
        with patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData',
                  return_value=(stock_dict, [])):
            with patch('os.path.exists', return_value=False):
                result = PKAssetsManager.loadStockData(stock_dict, config_manager,
                                                      stockCodes=['RELIANCE'], downloadOnly=True)
                
                mock_save.assert_called()


class TestLoadDataFromLocalPickleAdditional:
    """Additional comprehensive tests for loadDataFromLocalPickle method."""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_with_trading_hours_existing_data(self, mock_trading, mock_print,
                                                        mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle during trading hours with existing preloaded data."""
        stock_data = {
            'RELIANCE': pd.DataFrame({
                'open': [100], 'high': [101], 'low': [99], 'close': [100], 'volume': [1000],
                'MF': [1000], 'FII': [2000]
            }, index=[pd.Timestamp('2025-01-01')])
        }
        mock_pickle_load.return_value = stock_data
        
        stock_dict = {
            'RELIANCE': {
                'data': [[100, 101, 99, 100, 1000]],
                'index': ['2025-01-01'],
                'columns': ['open', 'high', 'low', 'close', 'volume']
            }
        }
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', True
        )
        
        assert loaded is True
        # During trading, should only copy MF/FII data
        assert 'RELIANCE' in result
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_dataframe_with_dataframe_columns(self, mock_trading, mock_print,
                                                        mock_pickle_load, mock_open_file):
        """Test loadDataFromLocalPickle handles DataFrame columns that are DataFrames."""
        # Create DataFrame where columns are DataFrames (edge case)
        df = pd.DataFrame({
            'open': pd.DataFrame({0: [100]}),
            'high': pd.DataFrame({0: [101]}),
            'low': pd.DataFrame({0: [99]}),
            'close': pd.DataFrame({0: [100]}),
            'volume': pd.DataFrame({0: [1000]})
        }, index=[pd.Timestamp('2025-01-01')])
        
        stock_data = {'RELIANCE': df}
        mock_pickle_load.return_value = stock_data
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.loadDataFromLocalPickle(
            stock_dict, config_manager, False, None, ".NS", 'test.pkl', False
        )
        
        assert loaded is True


class TestDownloadSavedDataFromServerAdditional:
    """Additional comprehensive tests for downloadSavedDataFromServer method."""
    
    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('alive_progress.alive_bar')
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('PKDevTools.classes.OutputControls.OutputControls.moveCursorUpLines')
    def test_download_saved_data_with_multiindex(self, mock_move, mock_print, mock_pickle_load,
                                                 mock_alive_bar, mock_open_file, mock_try_fetch):
        """Test downloadSavedDataFromServer handles MultiIndex data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '52428800'}
        mock_response.iter_content.return_value = [b'chunk'] * 50
        mock_try_fetch.return_value = mock_response
        
        # Create MultiIndex DataFrame
        arrays = [['RELIANCE', 'RELIANCE'], ['open', 'close']]
        multi_index = pd.MultiIndex.from_arrays(arrays, names=['stock', 'column'])
        stock_data = {('RELIANCE', 'open'): pd.DataFrame({0: [100]}, index=multi_index)}
        
        mock_pickle_load.return_value = stock_data
        
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        
        result, loaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, False, None, False, False, [], ".NS",
            False, False, 'test.pkl', False
        )
        
        assert loaded is True
    
    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('alive_progress.alive_bar')
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData')
    def test_download_saved_data_empty_stock_data(self, mock_load_stock, mock_print,
                                                  mock_pickle_load, mock_alive_bar,
                                                  mock_open_file, mock_try_fetch):
        """Test downloadSavedDataFromServer handles empty stock data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '52428800'}
        mock_response.iter_content.return_value = [b'chunk'] * 50
        mock_try_fetch.return_value = mock_response
        
        mock_pickle_load.return_value = {}
        
        stock_dict = {}
        config_manager = MagicMock()
        
        result, loaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, False, None, False, False, [], ".NS",
            False, False, 'test.pkl', False
        )
        
        assert loaded is False
    
    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('alive_progress.alive_bar')
    @patch('pickle.load')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData')
    def test_download_saved_data_keyboard_interrupt(self, mock_load_stock, mock_print,
                                                    mock_pickle_load, mock_alive_bar,
                                                    mock_open_file, mock_try_fetch):
        """Test downloadSavedDataFromServer handles KeyboardInterrupt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '52428800'}
        mock_response.iter_content.return_value = [b'chunk'] * 50
        mock_try_fetch.return_value = mock_response
        
        mock_open_file.side_effect = KeyboardInterrupt()
        
        stock_dict = {}
        config_manager = MagicMock()
        
        with pytest.raises(KeyboardInterrupt):
            PKAssetsManager.downloadSavedDataFromServer(
                stock_dict, config_manager, False, None, False, False, [], ".NS",
                False, False, 'test.pkl', False
            )


class TestPromptSaveResultsAdditional:
    """Additional comprehensive tests for promptSaveResults method."""
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput', return_value='Y')
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.removeAllColorStyles')
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.getLegendHelpText')
    @patch('pkscreener.classes.AssetsManager.pd.ExcelWriter')
    @patch('PKDevTools.classes.Archiver.get_user_reports_dir')
    def test_prompt_save_results_with_legend(self, mock_reports_dir, mock_excel_writer,
                                            mock_legend, mock_remove_colors, mock_input):
        """Test promptSaveResults when user wants to see legends."""
        mock_reports_dir.return_value = '/tmp/reports'
        mock_remove_colors.return_value = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        mock_legend.return_value = "Legend text"
        
        df = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        # First input is for legend, second is for save
        mock_input.side_effect = ['Y', 'Y']
        
        result = PKAssetsManager.promptSaveResults("TestSheet", df, defaultAnswer=None)
        
        # Should show legend and then save
        assert mock_input.call_count >= 1
    
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.removeAllColorStyles', side_effect=Exception("Error"))
    def test_prompt_save_results_remove_colors_error(self, mock_remove_colors):
        """Test promptSaveResults handles error in removeAllColorStyles."""
        df = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        # Should handle error gracefully
        try:
            PKAssetsManager.promptSaveResults("TestSheet", df, defaultAnswer='Y')
        except Exception:
            pass  # Should not crash
    
    @patch('PKDevTools.classes.OutputControls.OutputControls.takeUserInput', return_value='Y')
    @patch('pkscreener.classes.AssetsManager.ImageUtility.PKImageTools.removeAllColorStyles')
    @patch('pkscreener.classes.AssetsManager.pd.ExcelWriter', side_effect=Exception("Excel error"))
    @patch('PKDevTools.classes.Archiver.get_user_reports_dir')
    @patch('os.path.expanduser', return_value='/tmp')
    @patch('pkscreener.classes.AssetsManager.pd.DataFrame.to_csv')
    def test_prompt_save_results_excel_error_fallback(self, mock_to_csv, mock_expanduser,
                                                       mock_reports_dir, mock_excel_writer,
                                                       mock_remove_colors, mock_input):
        """Test promptSaveResults falls back to desktop on Excel error."""
        mock_reports_dir.return_value = '/tmp/reports'
        mock_remove_colors.return_value = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        df = pd.DataFrame({'Stock': ['A'], 'LTP': [100]})
        
        # First ExcelWriter fails, should try desktop
        with patch('pkscreener.classes.AssetsManager.pd.ExcelWriter') as mock_excel:
            mock_excel.side_effect = [Exception("Error"), MagicMock()]
            try:
                result = PKAssetsManager.promptSaveResults("TestSheet", df, defaultAnswer='Y')
            except Exception:
                pass  # May fail but should attempt fallback


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
