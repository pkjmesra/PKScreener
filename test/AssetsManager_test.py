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
import unittest
import pytest
from unittest.mock import patch, mock_open, MagicMock

from PKDevTools.classes import Archiver
from PKDevTools.classes.ColorText import colorText

from pkscreener.classes.AssetsManager import PKAssetsManager

class TestAssetsManager(unittest.TestCase):

    def test_make_hyperlink_valid_url(self):
        url = "https://www.example.com"
        expected = '=HYPERLINK("https://in.tradingview.com/chart?symbol=NSE:https://www.example.com", "https://www.example.com")'
        result = PKAssetsManager.make_hyperlink(url)
        self.assertEqual(result, expected)

    def test_make_hyperlink_empty_string(self):
        url = ""
        expected = '=HYPERLINK("https://in.tradingview.com/chart?symbol=NSE:", "")'
        result = PKAssetsManager.make_hyperlink(url)
        self.assertEqual(result, expected)

    def test_make_hyperlink_none(self):
        url = None
        with self.assertRaises(TypeError):
            PKAssetsManager.make_hyperlink(url)

    @patch('builtins.input', return_value='y')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pandas.core.generic.NDFrame.to_excel')
    def test_prompt_save_results_yes(self, mock_to_csv, mock_open, mock_input):
        # Create a sample DataFrame
        sample_df = MagicMock()
        # Call the method under test
        PKAssetsManager.promptSaveResults("Sheetname",sample_df)
        # Check that input was called to prompt the user
        mock_input.assert_called_once_with(colorText.WARN + f"[>] Do you want to save the results in excel file? [Y/N](Default:{colorText.END}{colorText.FAIL}N{colorText.END}): ")

    @patch('os.path.exists')
    def test_after_market_stock_data_exists_true(self, mock_exists):
        # Mock os.path.exists to return True
        mock_exists.return_value = True
        symbol = 'AAPL'
        date = '2025-02-06'
        # Call the class method
        exist,result = PKAssetsManager.afterMarketStockDataExists(True, True)
        # Assertions
        self.assertFalse(exist)
        self.assertTrue(result.startswith("intraday_stock_data_"))


    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(False, 'test.pkl'))
    @patch('PKDevTools.classes.Archiver.get_user_data_dir', return_value='test_results')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.dump')
    def test_save_stock_data_success(self, mock_pickle_dump, mock_open, mock_path_exists, mock_print, mock_get_data_dir, mock_after_market_exists):
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.deleteFileWithPattern = MagicMock()
        load_count = 10
        result = PKAssetsManager.saveStockData(stock_dict, config_manager, load_count)
        # Verify cache file path
        expected_cache_path = os.path.join('test_results', 'test.pkl')
        self.assertEqual(result, expected_cache_path)
        # Verify file write operations
        mock_open.assert_called_once_with(expected_cache_path, 'wb')
        mock_pickle_dump.assert_called_once()

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(True, 'test.pkl'))
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_save_stock_data_already_cached(self, mock_print, mock_after_market_exists):
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        load_count = 10
        result = PKAssetsManager.saveStockData(stock_dict, config_manager, load_count)
        self.assertTrue(result.endswith("test.pkl"))
        # mock_print.assert_any_call("\033[32m=> Already Cached.\033[0m") or mock_print.assert_any_call("\x1b[32m=> Done.\x1b[0m")

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(False, 'test.pkl'))
    @patch('PKDevTools.classes.Archiver.get_user_data_dir', return_value='test_results')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('pickle.dump', side_effect=pickle.PicklingError("Pickle error"))
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    def test_save_stock_data_pickle_error(self, mock_print, mock_pickle_dump, mock_open, mock_path_exists, mock_get_data_dir, mock_after_market_exists):
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        load_count = 10
        PKAssetsManager.saveStockData(stock_dict, config_manager, load_count)
        # Verify the error message is printed
        mock_print.assert_any_call("\033[31m=> Error while Caching Stock Data.\033[0m")

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(False, 'test.pkl'))
    @patch('PKDevTools.classes.Archiver.get_user_data_dir', return_value='test_results')
    @patch('os.path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.copy')
    @patch('pickle.dump')
    def test_save_stock_data_download_only(self, mock_pickle_dump, mock_shutil_copy, mock_open, mock_path_exists, mock_get_data_dir, mock_after_market_exists):
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        load_count = 10
        result = PKAssetsManager.saveStockData(stock_dict, config_manager, load_count, downloadOnly=True)
        # Verify copy occurs for large files
        expected_cache_path = os.path.join('test_results', 'test.pkl')
        self.assertEqual(result, expected_cache_path)

        mock_shutil_copy.assert_not_called()  # Only triggers if file size exceeds 40MB

    @patch('pkscreener.classes.PKTask.PKTask')
    @patch('pkscreener.classes.PKScheduler.PKScheduler.scheduleTasks')
    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockDataWithArgs')
    @patch('PKDevTools.classes.SuppressOutput.SuppressOutput')
    @pytest.mark.skip(reason="API has changed")
    @patch('PKDevTools.classes.log.default_logger')
    def test_download_latest_data_success(self, mock_logger, mock_suppress_output, mock_fetch_data, mock_schedule_tasks, mock_task):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.period = "1d"
        config_manager.duration = "6mo"
        config_manager.longTimeout = 2
        config_manager.logsEnabled = False
        stock_codes = ['AAPL', 'GOOGL', 'MSFT']
        exchange_suffix = ".NS"
        download_only = False

        # Mock task result
        task_result = MagicMock()
        task_result.to_dict.return_value = {'date': ['2021-01-01'], "close": [150]}
        
        # Create a mock task
        task = MagicMock()
        task.result = {'AAPL.NS': task_result}
        task.userData = ['AAPL']

        mock_task.return_value = task
        mock_schedule_tasks.return_value = None
        mock_fetch_data.return_value = None
        mock_suppress_output.return_value.__enter__.return_value = None

        # Act
        result_dict, left_out_stocks = PKAssetsManager.downloadLatestData(stock_dict, config_manager, stock_codes, exchange_suffix, download_only)

        # Assert task creation and stock dict update
        self.assertEqual(len(result_dict), 0)
        # self.assertEqual(result_dict['AAPL'], {'date': ['2021-01-01'], "close": [150]})
        self.assertEqual(len(left_out_stocks), 3)  # GOOGL and MSFT were not processed

        # Check that scheduleTasks was called with the correct parameters
        mock_schedule_tasks.assert_called_once()

    @patch('pkscreener.classes.PKTask.PKTask')
    @patch('pkscreener.classes.PKScheduler.PKScheduler.scheduleTasks')
    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockDataWithArgs')
    @patch('PKDevTools.classes.SuppressOutput.SuppressOutput')
    def test_download_latest_data_no_stocks(self, mock_suppress_output, mock_fetch_data, mock_schedule_tasks, mock_task):
        # Test case when no stocks are passed (empty stockCodes)
        stock_dict = {}
        config_manager = MagicMock()
        stock_codes = []
        exchange_suffix = ".NS"
        download_only = False

        result_dict, left_out_stocks = PKAssetsManager.downloadLatestData(stock_dict, config_manager, stock_codes, exchange_suffix, download_only)

        # Assert no stocks to download
        self.assertEqual(result_dict, stock_dict)
        self.assertEqual(left_out_stocks, [])

    @patch('pkscreener.classes.PKTask.PKTask')
    @patch('pkscreener.classes.PKScheduler.PKScheduler.scheduleTasks')
    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockDataWithArgs')
    @patch('PKDevTools.classes.SuppressOutput.SuppressOutput')
    def test_download_latest_data_single_stock(self, mock_suppress_output, mock_fetch_data, mock_schedule_tasks, mock_task):
        # Test case when a single stock is passed
        stock_dict = {}
        config_manager = MagicMock()
        stock_codes = ['AAPL']
        exchange_suffix = ".NS"
        download_only = False

        # Mock task result
        task_result = MagicMock()
        task_result.to_dict.return_value = {'date': ['2021-01-01'], "close": [150]}
        
        # Mock task
        task = MagicMock()
        task.result = {'AAPL.NS': task_result}
        task.userData = ['AAPL']

        mock_task.return_value = task
        mock_schedule_tasks.return_value = None
        mock_fetch_data.return_value = None
        mock_suppress_output.return_value.__enter__.return_value = None

        # Act
        result_dict, left_out_stocks = PKAssetsManager.downloadLatestData(stock_dict, config_manager, stock_codes, exchange_suffix, download_only)

        # Assert single stock download
        self.assertEqual(len(result_dict), 0)
        # self.assertEqual(result_dict['AAPL'], {'date': ['2021-01-01'], "close": [150]})
        self.assertEqual(left_out_stocks, ['AAPL'])

    @patch('pkscreener.classes.Fetcher.screenerStockDataFetcher.fetchStockDataWithArgs', side_effect=Exception("Download failed"))
    @patch('pkscreener.classes.PKTask.PKTask')
    @patch('pkscreener.classes.PKScheduler.PKScheduler.scheduleTasks')
    @patch('PKDevTools.classes.SuppressOutput.SuppressOutput')
    def test_download_latest_data_download_error(self, mock_suppress_output, mock_schedule_tasks, mock_task, mock_fetch_data):
        # Test case when downloading stock data fails (exception)
        stock_dict = {}
        config_manager = MagicMock()
        stock_codes = ['AAPL']
        exchange_suffix = ".NS"
        download_only = False

        result_dict, left_out_stocks = PKAssetsManager.downloadLatestData(stock_dict, config_manager, stock_codes, exchange_suffix, download_only)

        # Assert that error was handled gracefully and the stock was left out
        self.assertEqual(result_dict, stock_dict)
        self.assertEqual(left_out_stocks, ['AAPL'])

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(True, 'test_cache.pkl'))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData',return_value=({'AAPL': {'price': 150}},[]))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle', return_value=({'AAPL': {'price': 150}}, True))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.saveStockData')
    @patch('os.path.exists', return_value=True)
    @patch('shutil.copy')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_stock_data_from_local_cache(self, mock_trading,mock_copy, mock_exists, mock_save, mock_load_data, mock_download_data, mock_after_market_exists):
        # Arrange
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = '1d'
        config_manager.duration = '6mo'
        config_manager.baseIndex = 'NIFTY'
        stock_codes = ['AAPL', 'GOOGL']
        exchange_suffix = '.NS'
        download_only = True
        force_load = False
        force_redownload = False

        # Act
        result = PKAssetsManager.loadStockData(stock_dict, config_manager, downloadOnly=download_only, forceLoad=force_load, forceRedownload=force_redownload, stockCodes=stock_codes, exchangeSuffix=exchange_suffix,userDownloadOption='B')

        # Assert that data was loaded from local pickle file
        # mock_load_data.assert_called_once()
        self.assertEqual(result, stock_dict)
        # mock_save.assert_called()

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(False, 'test_cache.pkl'))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData',return_value=({'AAPL': {'price': 150}},[]))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle', return_value=({'AAPL': {'price': 150}}, False))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadSavedDataFromServer',return_value=({'AAPL': {'price': 150}}, False))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.saveStockData')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_stock_data_force_redownload(self, mock_trading, mock_save, mock_download_server, mock_load_local, mock_download_data, mock_after_market_exists):
        # Arrange
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = '1d'
        config_manager.duration = '6mo'
        config_manager.baseIndex = 'NIFTY'
        stock_codes = ['AAPL', 'GOOGL']
        exchange_suffix = '.NS'
        download_only = False
        force_redownload = True

        # Act
        result = PKAssetsManager.loadStockData(stock_dict, config_manager, forceRedownload=force_redownload, stockCodes=stock_codes, exchangeSuffix=exchange_suffix)

        # Assert that data is redownloaded from the server
        mock_download_server.assert_called_once()
        mock_save.assert_not_called()
        self.assertEqual(result, stock_dict)

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(True, 'test_cache.pkl'))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData',return_value=({'AAPL': {'price': 150}},[]))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle', return_value=({}, False))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.saveStockData')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_stock_data_not_found_in_local_cache(self, mock_trading, mock_save, mock_load_local, mock_download_data, mock_after_market_exists):
        # Arrange
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = '1d'
        config_manager.duration = '6mo'
        config_manager.baseIndex = 'NIFTY'
        stock_codes = ['AAPL', 'GOOGL']
        exchange_suffix = '.NS'
        download_only = False
        force_load = False
        force_redownload = False

        # Act
        result = PKAssetsManager.loadStockData(stock_dict, config_manager, downloadOnly=download_only, forceLoad=force_load, forceRedownload=force_redownload, stockCodes=stock_codes, exchangeSuffix=exchange_suffix)

        # Assert that data was downloaded as it was not found in local cache
        mock_download_data.assert_called()
        mock_save.assert_not_called()
        self.assertEqual(result, stock_dict)

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists', return_value=(True, 'test_cache.pkl'))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadLatestData',return_value=({'AAPL': {'price': 150}},[]))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadDataFromLocalPickle', return_value=({}, False))
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.downloadSavedDataFromServer')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    @patch('os.path.exists', return_value=True)
    @patch('shutil.copy')
    def test_load_stock_data_download_only(self, mock_copy,mock_path,mock_trading, mock_download_server, mock_download_data, mock_load_local, mock_after_market_exists):
        # Test the case where downloadOnly is True
        stock_dict = {'AAPL': {'price': 150}}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        config_manager.period = '1d'
        config_manager.duration = '6mo'
        config_manager.baseIndex = 'NIFTY'
        stock_codes = ['AAPL', 'GOOGL']
        exchange_suffix = '.NS'
        download_only = False
        force_redownload = False

        # Act
        result = PKAssetsManager.loadStockData(stock_dict, config_manager, downloadOnly=download_only, forceRedownload=force_redownload, stockCodes=stock_codes, exchangeSuffix=exchange_suffix)

        # Assert that data is downloaded as downloadOnly is True
        mock_download_data.assert_called_once()
        mock_download_server.assert_not_called()  # Don't download from server if downloadOnly is True
        self.assertEqual(result, stock_dict)

    @patch('builtins.open', new_callable=mock_open, read_data=b'')
    @patch('pkscreener.classes.AssetsManager.pickle.load')
    @patch('pkscreener.classes.AssetsManager.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_success(self, mock_trading, mock_print, mock_pickle_load, mock_open):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        config_manager.isIntradayConfig.return_value = False
        exchange_suffix = ".NS"
        cache_file = 'test_cache.pkl'
        is_trading = False
        
        stock_data = {
            'AAPL': {'price': 150, "volume": 1000},
            'GOOGL': {'price': 2800, "volume": 500}
        }

        mock_pickle_load.return_value = stock_data
        
        # Act
        result, stock_data_loaded = PKAssetsManager.loadDataFromLocalPickle(stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, exchangeSuffix=exchange_suffix, cache_file=cache_file, isTrading=is_trading)

        # Assert
        self.assertTrue(stock_data_loaded)
        self.assertEqual(len(result), 2)
        self.assertIn('AAPL', result)
        self.assertIn('GOOGL', result)
        mock_print.assert_called_with(f"\x1b[32m\n  [+] Automatically Using [2] Tickers' Cached Stock Data due to After-Market hours\x1b[0m")

    @patch('builtins.open', new_callable=mock_open)
    @patch('pkscreener.classes.AssetsManager.pickle.load', side_effect=pickle.UnpicklingError)
    @patch('pkscreener.classes.AssetsManager.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.promptFileExists', return_value='Y')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_unpickling_error(self,mock_trading, mock_prompt, mock_print, mock_pickle_load, mock_open):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        exchange_suffix = ".NS"
        cache_file = 'test_cache.pkl'

        # Act
        result, stock_data_loaded = PKAssetsManager.loadDataFromLocalPickle(stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, exchangeSuffix=exchange_suffix, cache_file=cache_file, isTrading=False)

        # Assert
        self.assertFalse(stock_data_loaded)
        mock_print.assert_called_with("\033[31m  [+] Error while Reading Stock Cache.\033[0m")
        mock_prompt.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('pkscreener.classes.AssetsManager.pickle.load', side_effect=EOFError)
    @patch('pkscreener.classes.AssetsManager.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.promptFileExists', return_value='Y')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_eof_error(self, mock_trading, mock_prompt, mock_print, mock_pickle_load, mock_open):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        exchange_suffix = ".NS"
        cache_file = 'test_cache.pkl'

        # Act
        result, stock_data_loaded = PKAssetsManager.loadDataFromLocalPickle(stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, exchangeSuffix=exchange_suffix, cache_file=cache_file, isTrading=False)

        # Assert
        self.assertFalse(stock_data_loaded)
        mock_print.assert_called_with("\033[31m  [+] Error while Reading Stock Cache.\033[0m")
        mock_prompt.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data=b'')
    @patch('pkscreener.classes.AssetsManager.pickle.load')
    @patch('pkscreener.classes.AssetsManager.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_empty_data(self, mock_trading, mock_print, mock_pickle_load, mock_open):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        exchange_suffix = ".NS"
        cache_file = 'test_cache.pkl'
        is_trading = True
        
        # Return empty data from pickle
        mock_pickle_load.return_value = {}

        # Act
        result, stock_data_loaded = PKAssetsManager.loadDataFromLocalPickle(stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, exchangeSuffix=exchange_suffix, cache_file=cache_file, isTrading=is_trading)

        # Assert
        self.assertFalse(stock_data_loaded)

    @patch('builtins.open', new_callable=mock_open)
    @patch('pkscreener.classes.AssetsManager.pickle.load')
    @patch('pkscreener.classes.AssetsManager.OutputControls.printOutput')
    @patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime', return_value=False)
    def test_load_data_from_local_pickle_with_existing_data(self, mock_trading, mock_print, mock_pickle_load, mock_open):
        # Arrange
        stock_dict = {'AAPL': {'price': 140, "volume": 1000}}
        config_manager = MagicMock()
        exchange_suffix = ".NS"
        cache_file = 'test_cache.pkl'
        is_trading = False
        
        stock_data = {
            'AAPL': {'price': 150, "volume": 1100},
            'GOOGL': {'price': 2800, "volume": 500}
        }

        mock_pickle_load.return_value = stock_data

        # Act
        result, stock_data_loaded = PKAssetsManager.loadDataFromLocalPickle(stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, exchangeSuffix=exchange_suffix, cache_file=cache_file, isTrading=is_trading)

        # Assert
        self.assertTrue(stock_data_loaded)
        self.assertEqual(len(result), 2)
        self.assertIn('AAPL', result)
        self.assertIn('GOOGL', result)
        self.assertEqual(result['AAPL'], {'price': 150, "volume": 1100})  # Should update AAPL with new data
        mock_print.assert_called_with(f"\x1b[32m\n  [+] Automatically Using [2] Tickers' Cached Stock Data due to After-Market hours\x1b[0m")

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('PKDevTools.classes.log.emptylogger')
    def test_download_saved_defaults_success(self, mock_logger, mock_open, mock_tryFetchFromServer):
        # Arrange
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1024000'}
        mock_response.text = 'file content'
        mock_tryFetchFromServer.return_value = mock_response
        
        # Act
        file_downloaded = PKAssetsManager.downloadSavedDefaultsFromServer(cache_file)

        # Assert
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
        mock_open.assert_called_once_with(os.path.join(Archiver.get_user_data_dir(), cache_file), 'w+')
        mock_open.return_value.write.assert_called_once_with('file content')
        self.assertTrue(file_downloaded)
        # mock_logger.debug.assert_called_with(f"Stock data cache file:{cache_file} request status ->{mock_response.status_code}")

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    def test_download_saved_defaults_failed_request(self, mock_tryFetchFromServer):
        # Arrange
        cache_file = 'test_cache.pkl'
        mock_tryFetchFromServer.return_value = None

        # Act
        file_downloaded = PKAssetsManager.downloadSavedDefaultsFromServer(cache_file)

        # Assert
        self.assertFalse(file_downloaded)
        mock_tryFetchFromServer.assert_called_once_with(cache_file)

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_saved_defaults_invalid_status_code(self, mock_open, mock_tryFetchFromServer):
        # Arrange
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 500  # Invalid status code
        mock_response.headers = {'content-length': '1024'}
        mock_response.text = 'file content'
        mock_tryFetchFromServer.return_value = mock_response

        # Act
        file_downloaded = PKAssetsManager.downloadSavedDefaultsFromServer(cache_file)

        # Assert
        self.assertFalse(file_downloaded)
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
        mock_open.assert_not_called()

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_saved_defaults_small_file(self, mock_open, mock_tryFetchFromServer):
        # Arrange
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '10'}
        mock_response.text = 'file content'
        mock_tryFetchFromServer.return_value = mock_response

        # Act
        file_downloaded = PKAssetsManager.downloadSavedDefaultsFromServer(cache_file)

        # Assert
        self.assertFalse(file_downloaded)  # File size < 40 bytes, should not download
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
        mock_open.assert_not_called()

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_saved_defaults_file_write_error(self, mock_open, mock_tryFetchFromServer):
        # Arrange
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1024000'}
        mock_response.text = 'file content'
        mock_tryFetchFromServer.return_value = mock_response
        mock_open.side_effect = IOError("File write error")

        # Act
        file_downloaded = PKAssetsManager.downloadSavedDefaultsFromServer(cache_file)

        # Assert
        self.assertFalse(file_downloaded)
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
        mock_open.assert_called_once_with(os.path.join(Archiver.get_user_data_dir(), cache_file), 'w+')

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_saved_defaults_missing_content_length(self, mock_open, mock_tryFetchFromServer):
        # Arrange
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}  # No content-length header
        mock_response.text = 'file content'
        mock_tryFetchFromServer.return_value = mock_response

        # Act
        file_downloaded = PKAssetsManager.downloadSavedDefaultsFromServer(cache_file)

        # Assert
        self.assertFalse(file_downloaded)  # No content length header should prevent download
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
        mock_open.assert_not_called()

    @patch('pkscreener.classes.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('alive_progress.alive_bar')
    @patch('PKDevTools.classes.OutputControls.OutputControls.printOutput')
    @patch('shutil.copy')
    @patch('pickle.load',return_value={'NSE':40000})
    @patch('platform.platform',return_value="Windows")
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData',return_value={})
    def test_download_saved_data_from_server_success(self, mock_loadDict,mock_platform,mock_pickle,mock_copy, mock_print, mock_alive_bar, mock_open, mock_tryFetchFromServer):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '52428800'}  # 50MB
        mock_response.text = 'dummy content'  # Simulated file content
        mock_response.iter_content.return_value = [b'chunk_data'] * 50  # Mocked chunks
        mock_tryFetchFromServer.return_value = mock_response

        # Mock the progress bar and file write
        mock_alive_bar.return_value = MagicMock()
        mock_open.return_value.__enter__.return_value = MagicMock()

        # Act
        stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, 
            retrial=False, forceLoad=False, stockCodes=[], exchangeSuffix=".NS", 
            isIntraday=False, forceRedownload=False, cache_file=cache_file, isTrading=False
        )

        # Assert
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
        # mock_alive_bar.assert_called_once()
        mock_open.assert_called_with(os.path.join(Archiver.get_user_data_dir(), cache_file), 'rb')
        # mock_copy.assert_called_once()
        self.assertTrue(stockDataLoaded)

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData',return_value={})
    def test_download_saved_data_from_server_invalid_filesize(self, mock_loadDict, mock_open, mock_tryFetchFromServer):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '50'}
        mock_response.text = 'dummy content'  # Simulated file content
        mock_tryFetchFromServer.return_value = mock_response

        # Act
        stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, 
            retrial=False, forceLoad=False, stockCodes=[], exchangeSuffix=".NS", 
            isIntraday=False, forceRedownload=False, cache_file=cache_file, isTrading=False
        )

        # Assert
        self.assertFalse(stockDataLoaded)
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
        mock_open.assert_not_called()  # Since file size is too small, no file should be written

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pkscreener.classes.AssetsManager.OutputControls.printOutput')
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData',return_value={})
    def test_download_saved_data_from_server_file_write_error(self, mock_loadDict, mock_print, mock_open, mock_tryFetchFromServer):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '10485760'}
        mock_response.text = 'dummy content'
        mock_response.iter_content.return_value = [b'chunk_data'] * 10
        mock_tryFetchFromServer.return_value = mock_response

        # Simulate file write error
        mock_open.side_effect = IOError("File write error")

        # Act
        stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, 
            retrial=False, forceLoad=False, stockCodes=[], exchangeSuffix=".NS", 
            isIntraday=False, forceRedownload=False, cache_file=cache_file, isTrading=False
        )

        # Assert
        self.assertFalse(stockDataLoaded)

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData',return_value={})
    def test_download_saved_data_from_server_retry_on_failure(self, mock_loadDict, mock_open, mock_tryFetchFromServer):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 500  # Simulating a server error
        mock_tryFetchFromServer.return_value = mock_response

        # Act
        stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, 
            retrial=True, forceLoad=False, stockCodes=[], exchangeSuffix=".NS", 
            isIntraday=False, forceRedownload=False, cache_file=cache_file, isTrading=False
        )

        # Assert
        self.assertFalse(stockDataLoaded)
        mock_tryFetchFromServer.assert_called_with(cache_file)

    @patch('pkscreener.classes.AssetsManager.Utility.tools.tryFetchFromServer')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData',return_value={})
    def test_download_saved_data_from_server_corrupted_data(self, mock_loadDict, mock_open, mock_tryFetchFromServer):
        # Arrange
        stock_dict = {}
        config_manager = MagicMock()
        cache_file = 'test_cache.pkl'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '10485760'}
        mock_response.text = 'dummy content'
        mock_response.iter_content.return_value = [b'chunk_data'] * 10
        mock_tryFetchFromServer.return_value = mock_response

        # Simulate corrupted data after download
        mock_open.return_value.__enter__.return_value.read.return_value = b"corrupted data"
        mock_open.side_effect = pickle.UnpicklingError("Corrupted data")

        # Act
        stockDict, stockDataLoaded = PKAssetsManager.downloadSavedDataFromServer(
            stock_dict, config_manager, downloadOnly=False, defaultAnswer=None, 
            retrial=False, forceLoad=False, stockCodes=[], exchangeSuffix=".NS", 
            isIntraday=False, forceRedownload=False, cache_file=cache_file, isTrading=False
        )

        # Assert
        self.assertFalse(stockDataLoaded)
        # mock_open.assert_called()
        mock_tryFetchFromServer.assert_called_once_with(cache_file)
