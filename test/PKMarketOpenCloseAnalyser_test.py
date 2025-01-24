import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from pkscreener.classes.Utility import tools
from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from pkscreener.classes.PKMarketOpenCloseAnalyser import PKMarketOpenCloseAnalyser

class TestPKMarketOpenCloseAnalyser(unittest.TestCase):

    @patch('pkscreener.classes.Utility.tools.loadStockData')
    def test_ensureIntradayStockDataExists_failure(self, mock_load):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = True
            with patch("pkscreener.classes.Utility.tools.afterMarketStockDataExists") as mock_data:
                mock_data.return_value = False, "stock_data_1.pkl"
                exists, cache_file, stockDict = PKMarketOpenCloseAnalyser.ensureIntradayStockDataExists(listStockCodes=['AAPL'])
                self.assertFalse(exists)
                self.assertIsInstance(stockDict, dict)

    @patch('pkscreener.classes.Utility.tools.loadStockData')
    def test_ensureIntradayStockDataExists_success(self, mock_load,):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = False
            with patch("pkscreener.classes.Utility.tools.afterMarketStockDataExists") as mock_data:
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

    @patch('pkscreener.classes.Utility.tools.loadStockData')
    def test_ensureDailyStockDataExists_success(self, mock_load):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = False
            with patch("pkscreener.classes.Utility.tools.afterMarketStockDataExists") as mock_data:
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

    @patch('pkscreener.classes.Utility.tools.loadStockData')
    def test_ensureDailyStockDataExists_failure(self, mock_load):
        mock_load.return_value = {'AAPL': {'data': [], 'columns': [], 'index': []}}  # Mocked return value
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.isTradingTime') as mock_PKDateUtilities:
            mock_PKDateUtilities.return_value = True
            with patch("pkscreener.classes.Utility.tools.afterMarketStockDataExists") as mock_data:
                mock_data.return_value = False, "stock_data_1.pkl"
                exists, cache_file, stockDict = PKMarketOpenCloseAnalyser.ensureDailyStockDataExists(listStockCodes=['AAPL'])
                self.assertFalse(exists)
                self.assertIsInstance(stockDict, dict)

    def test_getMorningOpen(self):
        df = pd.DataFrame({
            'Open': [None, None, 100, 110],
            'Close': [None, None, 105, 115]
        })
        open_price = PKMarketOpenCloseAnalyser.getMorningOpen(df)
        self.assertEqual(open_price, 100)

    def test_getMorningClose(self):
        df = pd.DataFrame({
            'Open': [90, 95, None, None],
            'Close': [None, None, 105, 110]
        })
        close_price = PKMarketOpenCloseAnalyser.getMorningClose(df)
        self.assertEqual(close_price, 110)

    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.getLatestDailyCandleData')
    @patch('pkscreener.classes.PKMarketOpenCloseAnalyser.PKMarketOpenCloseAnalyser.getIntradayCandleFromMorning')
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
            'AAPL': {'data': [[None, None, None, 152]], 'columns': ['Open', 'High', 'Low', 'Close'], 'index': [None]}
        }
        allDailyCandles = {
            'AAPL': {'data': [[None, None, None, 155]], 'columns': ['Open', 'High', 'Low', 'Close'], 'index': [None]}
        }

        save_df, screen_df = PKMarketOpenCloseAnalyser.diffMorningCandleDataWithLatestDailyCandleData(screen_df, save_df, updatedCandleData, allDailyCandles,"RunOptionName",['AAPL'])
        self.assertIn('LTP@Alert', screen_df.columns)
        self.assertIn('EoDDiff', screen_df.columns)
