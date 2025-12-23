import unittest
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from pkscreener.classes.Utility import tools
from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser

class TestPKMarketOpenCloseAnalyser(unittest.TestCase):

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData')
    def test_ensureIntradayStockDataExists_failure(self, mock_load):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = True
            with patch("pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists") as mock_data:
                mock_data.return_value = False, "stock_data_1.pkl"
                exists, cache_file, stockDict = PKMarketOpenCloseAnalyser.ensureIntradayStockDataExists(listStockCodes=['AAPL'])
                self.assertFalse(exists)
                self.assertIsInstance(stockDict, dict)

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData')
    def test_ensureIntradayStockDataExists_success(self, mock_load,):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = False
            with patch("pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists") as mock_data:
                mock_data.return_value = False, "stock_data_1.pkl"
                with patch("os.path.exists") as mock_path:
                    mock_path.return_value = True
                    with patch("os.path.isdir") as mock_dir:
                        mock_dir.return_value = True
                        with patch("os.stat") as mock_stat:
                            mock_stat.return_value.st_size = 1024*1024*40
                            mock_stat.return_value.st_mode = 1
                            with patch("shutil.copy") as mock_shutil:
                                exists, cache_file, stockDict = PKMarketOpenCloseAnalyser.ensureIntradayStockDataExists(listStockCodes=['AAPL'])
                                self.assertTrue(exists)

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData')
    def test_ensureDailyStockDataExists_success(self, mock_load):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = False
            with patch("pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists") as mock_data:
                mock_data.return_value = False, "stock_data_1.pkl"
                with patch("os.path.exists") as mock_path:
                    mock_path.return_value = True
                    with patch("os.path.isdir") as mock_dir:
                        mock_dir.return_value = True
                        with patch("os.stat") as mock_stat:
                            mock_stat.return_value.st_size = 1024*1024*40
                            mock_stat.return_value.st_mode = 1
                            with patch("shutil.copy") as mock_shutil:
                                exists, cache_file, stockDict = PKMarketOpenCloseAnalyser.ensureDailyStockDataExists(listStockCodes=['AAPL'])
                                self.assertTrue(exists)

    @patch('pkscreener.classes.AssetsManager.PKAssetsManager.loadStockData')
    def test_ensureDailyStockDataExists_failure(self, mock_load):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = True
            with patch("pkscreener.classes.AssetsManager.PKAssetsManager.afterMarketStockDataExists") as mock_data:
                mock_data.return_value = False, "stock_data_1.pkl"
                exists, cache_file, stockDict = PKMarketOpenCloseAnalyser.ensureDailyStockDataExists(listStockCodes=['AAPL'])
                self.assertFalse(exists)
                self.assertIsInstance(stockDict, dict)

    def test_getMorningOpen(self):
        df = pd.DataFrame({
            "open": [None, None, 100, 110],
            "close": [None, None, 105, 115]
        })
        open_price = PKMarketOpenCloseAnalyser.getMorningOpen(df)
        self.assertEqual(open_price, 100)

    def test_getMorningClose(self):
        df = pd.DataFrame({
            "open": [90, 95, None, None],
            "close": [None, None, 105, 110]
        })
        close_price = PKMarketOpenCloseAnalyser.getMorningClose(df)
        self.assertEqual(close_price, 110)

    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.getLatestDailyCandleData')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning')
    @pytest.mark.skip(reason="API has changed")
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation')
    def test_getStockDataForSimulation(self, mock_combine, mock_intraday, mock_daily):
        mock_daily.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}
        mock_intraday.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}
        mock_combine.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}

        updatedCandleData, allDailyCandles = PKMarketOpenCloseAnalyser.getStockDataForSimulation(listStockCodes=['AAPL'])
        self.assertIsNotNone(updatedCandleData)
        self.assertIsNotNone(allDailyCandles)

    def test_diffMorningCandleDataWithLatestDailyCandleData(self):
        save_df = pd.DataFrame({
            'Stock': ['AAPL'],
            'LTP': [150],
            'EoDLTP': [155],
            "LTP@Alert": [150], 
            "AlertTime": ["09:30"], 
            "SqrOff":["09:40"], 
            "SqrOffLTP": [150], 
            "SqrOffDiff": [150],
            "DayHighTime": ["09:45"],
            "DayHigh": [150],
            "DayHighDiff": [150], 
            "EoDLTP": [150], 
            "EoDDiff": [150]
        })
        screen_df = pd.DataFrame({
            'Stock': ['NSE%3AAAPL'],
            'LTP': [150]
        })

        updatedCandleData = {
            'AAPL': {'data': [[None, None, None, 152]], 'columns': ["open", "high", "low", "close"], 'index': [None]}
        }
        allDailyCandles = {
            'AAPL': {'data': [[None, None, None, 155]], 'columns': ["open", "high", "low", "close"], 'index': [None]}
        }

        save_df, screen_df = PKMarketOpenCloseAnalyser.diffMorningCandleDataWithLatestDailyCandleData(screen_df, save_df, updatedCandleData, allDailyCandles,"RunOptionName",['AAPL'])
        self.assertIn('LTP@Alert', screen_df.columns)
        self.assertIn('EoDDiff', screen_df.columns)

class TestCombineDailyStockDataWithMorningSimulation(unittest.TestCase):

    def setUp(self):
        self.allDailyCandles = {
            'AAPL': {
                'data': [[1, 2, 3, 150], [1, 2, 3, 155]],
                'index': ['2023-10-01', '2023-10-02']
            },
            'MSFT': {
                'data': [[1, 2, 3, 250], [1, 2, 3, 255]],
                'index': ['2023-10-01', '2023-10-02']
            },
        }
        
        self.morningIntradayCandle = {
            'AAPL': {
                'data': [[1, 2, 3, 152]],
                'index': ['2023-10-02 09:30']
            }
        }

    def test_combine_data_success(self):
        expected_output = {
            'AAPL': {'data': [[1, 2, 3, 150], [1, 2, 3, 152]],
                    'index': ['2023-10-01', '2023-10-02 09:30']
                    }
                }
        
        result = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(self.allDailyCandles, self.morningIntradayCandle)
        self.assertEqual(result, expected_output)

    def test_missing_intraday_stock(self):
        # Test when there are stocks in allDailyCandles that are not in morningIntradayCandle
        morning_candle = {
            'AAPL': {
                'data': [[1, 2, 3, 152]],
                'index': ['2023-10-02 09:30']
            }
        }
        expected_output = {
            'AAPL': {'data': [[1, 2, 3, 150], [1, 2, 3, 152]],
                    'index': ['2023-10-01', '2023-10-02 09:30']
                    }
                }
        result = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(self.allDailyCandles, morning_candle)
        self.assertEqual(result, expected_output)

    def test_no_daily_data(self):
        # Test when allDailyCandles is empty
        empty_all_daily_candles = {}
        expected_output = {}
        
        result = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(empty_all_daily_candles, self.morningIntradayCandle)
        self.assertEqual(result, expected_output)

    def test_no_intraday_data(self):
        # Test when morningIntradayCandle is empty
        expected_output = {
            'AAPL': {
                'data': [[1, 2, 3, 150], [1, 2, 3, 155]],
                'index': ['2023-10-01', '2023-10-02']
            },
            'MSFT': {
                'data': [[1, 2, 3, 250], [1, 2, 3, 255]],
                'index': ['2023-10-01', '2023-10-02']
            },
        }
        
        result = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(self.allDailyCandles, {})
        self.assertEqual(result, {})

    def test_invalid_data_format(self):
        # Test when the input data format is incorrect
        malformed_daily_candles = {
            'AAPL': {
                'data': 'not a list',
                'index': ['2023-10-01']
            }
        }
        
        result = PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(malformed_daily_candles, self.morningIntradayCandle)
        self.assertEqual(result, {})

    def test_error_logging(self):
        # Test logging when encountering an error
        with patch('os.environ', {'PKDevTools_Default_Log_Level': 'DEBUG'}):
            result =PKMarketOpenCloseAnalyser.combineDailyStockDataWithMorningSimulation(self.allDailyCandles, self.morningIntradayCandle)
            self.assertIn('AAPL', result)

class TestGetIntradayCandleFromMorning(unittest.TestCase):

    @patch('pkscreener.classes.ConfigManager.tools')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKIntradayStockDataDB')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.getMorningOpen')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.getMorningClose')
    def test_positive_case_with_stock_dict(self, mock_get_morning_close, mock_get_morning_open, mock_intraday_db, mock_config_manager):
        # Setup mock data
        mock_config_manager.morninganalysiscandlenumber = 5
        mock_config_manager.morninganalysiscandleduration = "1m"
        
        mock_data = {
            'AAPL': {
                "data": [
                    {"open": 150, "high": 155, "low": 149, "close": 154, "Adj Close": 154, "volume": 1000},
                    {"open": 154, "high": 156, "low": 153, "close": 155, "Adj Close": 155, "volume": 1100}
                ],
                "columns": ["open", "high", "low", "close", "Adj Close", "volume"],
                "index": pd.date_range(start='2023-10-01 09:15', periods=2, freq='T')
            }
        }
        
        mock_get_morning_open.return_value = 150
        mock_get_morning_close.return_value = 155
        
        # Call the function
        result = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(stockDictInt=mock_data)
        
        # Assertions
        self.assertIn('AAPL', result)
        self.assertEqual(result['AAPL']['data'][0][0], 150)
        self.assertEqual(result['AAPL']['data'][0][1], 156)
        self.assertEqual(result['AAPL']['data'][0][2], 149)
        self.assertEqual(result['AAPL']['data'][0][3], 155)

    @patch('pkscreener.classes.ConfigManager.tools')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKIntradayStockDataDB')
    def test_negative_case_with_invalid_data(self, mock_intraday_db, mock_config_manager):
        # Setup mock data
        mock_config_manager.morninganalysiscandlenumber = 5
        mock_data = {
            'AAPL': {
                "data": [],
                "columns": ["open", "high", "low", "close", "Adj Close", "volume"],
                "index": []
            }
        }

        # Call the function
        result = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(stockDictInt=mock_data)

        # Assertions
        self.assertEqual(result, {})

    @patch('pkscreener.classes.ConfigManager.tools')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKIntradayStockDataDB')
    def test_exception_handling(self, mock_intraday_db, mock_config_manager):
        # Setup mock data
        mock_config_manager.morninganalysiscandlenumber = 5
        mock_data = {
            'AAPL': {
                "data": [
                    {"open": 150, "high": 155, "low": 149, "close": 154, "Adj Close": 154, "volume": 1000},
                ],
                "columns": ["open", "high", "low", "close", "Adj Close", "volume"],
                "index": pd.date_range(start='2023-10-01 09:15', periods=1, freq='T')
            }
        }

        # Simulate an exception in getMorningOpen
        with patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.getMorningOpen', side_effect=Exception("Test Exception")):
            result = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(stockDictInt=mock_data)
            self.assertEqual(result, {})

    @patch('pkscreener.classes.ConfigManager.tools')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKIntradayStockDataDB')
    def test_no_stocks_case(self, mock_intraday_db, mock_config_manager):
        # Call the function with no stocks
        result = PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning(stockDictInt={})

        # Assertions
        self.assertEqual(result, {})
