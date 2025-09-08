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
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
import pytest

from pkscreener.classes.MarketMonitor import MarketMonitor

# class TestMarketMonitor(unittest.TestCase):
    
#     def setUp(self):
#         self.market_monitor = MarketMonitor(monitors=['Monitor1', 'Monitor2'])

#     def test_currentMonitorOption(self):
#         # Positive test case
#         option = self.market_monitor.currentMonitorOption()
#         self.assertEqual(option, 'Monitor1')
        
#         # Test wrapping around monitor index
#         self.market_monitor.monitorIndex = 1
#         option = self.market_monitor.currentMonitorOption()
#         self.assertEqual(option, 'Monitor2')
        
#         option = self.market_monitor.currentMonitorOption()
#         self.assertEqual(option, 'Monitor1')  # Should wrap back to the first monitor

#     def test_saveMonitorResultStocks(self):
#         # Positive test case
#         results_df = pd.DataFrame(index=['AAPL', 'GOOGL'],columns=["close"],data=[1,2])
#         self.market_monitor.saveMonitorResultStocks(results_df)
#         # self.assertIn('0', self.market_monitor.monitorResultStocks)
#         # self.assertEqual(self.market_monitor.monitorResultStocks['0'], 'AAPL,GOOGL')
#         self.assertTrue('AAPL,GOOGL' in self.market_monitor.monitorResultStocks.values())
#         results_df = pd.DataFrame(index=['AAPL', 'GOOGL', "PK"],columns=["close"],data=[1,2,100])
#         self.market_monitor.saveMonitorResultStocks(results_df)
#         self.assertTrue(len(self.market_monitor.alertStocks) > 0)
        
#         # Negative test case with empty DataFrame
#         results_df = pd.DataFrame()
#         self.market_monitor.saveMonitorResultStocks(results_df)
#         self.assertTrue('NONE' in self.market_monitor.monitorResultStocks.values())
#         # self.assertIn('0', self.market_monitor.monitorResultStocks)
#         # self.assertEqual(self.market_monitor.monitorResultStocks['0'], 'NONE')

#     def test_refresh(self):
#         # Positive test case with valid DataFrame
#         screen_df = pd.DataFrame({
#             'Stock': ['AAPL', 'GOOGL'],
#             'LTP': [150, 2800],
#             '%Chng': ['1% (up)', '2% (up)'],
#             '52Wk-H': [200, 2900],
#             'RSI': [70, 65],
#             "volume": [1000, 2000]
#         })
#         self.market_monitor.refresh(screen_df=screen_df, screenOptions='Monitor1', chosenMenu='Menu1')
#         self.assertFalse(self.market_monitor.monitor_df.empty)

#         # Negative test case with empty DataFrame
#         self.market_monitor.refresh(screen_df=None, screenOptions=None)
#         self.assertFalse(self.market_monitor.monitor_df.empty)

#     def test_updateDataFrameForTelegramMode(self):
#         # Positive test case
#         screen_monitor_df = pd.DataFrame({
#             'Stock': ['AAPL', 'GOOGL'],
#             'LTP': [150, 2800],
#             'Ch%': ['1% (up)', '2% (up)'],
#             'Vol': ['1000x', '2000x']
#         })
#         telegram_df = self.market_monitor.updateDataFrameForTelegramMode(telegram=True, screen_monitor_df=screen_monitor_df)
#         self.assertEqual(telegram_df.shape[0], 2)  # Should return a DataFrame with 2 rows

#         # Negative test case
#         telegram_df = self.market_monitor.updateDataFrameForTelegramMode(telegram=False, screen_monitor_df=screen_monitor_df)
#         self.assertIsNone(telegram_df)

#     def test_getScanOptionName(self):
#         # Positive test case
#         option_name = self.market_monitor.getScanOptionName("X:12:9:2.5:>|X:0:31:")
#         self.assertEqual(option_name, "P_1_3:")  # Assuming predefined scan exists

#         # Negative test case with invalid input
#         option_name = self.market_monitor.getScanOptionName(None)
#         self.assertEqual(option_name, "")

class TestMarketMonitor2(unittest.TestCase):

    def setUp(self):
        # Setup a MarketMonitor instance for testing
        self.monitor = MarketMonitor(monitors=['AAPL', 'GOOGL', 'MSFT'])

    def test_initialization_with_empty_monitors(self):
        monitor = MarketMonitor(monitors=[])
        self.assertEqual(monitor.monitors, self.monitor.monitors)
        self.assertEqual(monitor.monitorResultStocks, {})

    def test_currentMonitorOption(self):
        option = self.monitor.currentMonitorOption()
        self.assertEqual(option, 'AAPL')
        # Call again to test cycling through monitors
        option = self.monitor.currentMonitorOption()
        self.assertEqual(option, 'GOOGL')
        option = self.monitor.currentMonitorOption()
        self.assertEqual(option, 'MSFT')

    def test_saveMonitorResultStocks_with_empty_dataframe(self):
        df = pd.DataFrame()
        self.monitor.saveMonitorResultStocks(df)
        self.assertEqual(self.monitor.monitorResultStocks[str(self.monitor.monitorIndex)], "NONE")

    def test_saveMonitorResultStocks_with_valid_dataframe(self):
        df = pd.DataFrame(index=['AAPL', 'MSFT'],columns=["close"],data=[1,2])
        self.monitor.saveMonitorResultStocks(df)
        self.assertTrue('AAPL,MSFT' in self.monitor.monitorResultStocks.values())
        # self.assertIn('0', self.monitor.monitorResultStocks)
        # self.assertEqual(self.monitor.monitorResultStocks['0'], 'AAPL,MSFT')

    def test_refresh_with_empty_dataframe(self):
        self.monitor.refresh(screen_df=None, screenOptions='AAPL')
        self.assertFalse(self.monitor.monitor_df is None)
        # self.assertTrue(self.monitor.monitor_df.empty)

    def test_refresh_with_valid_dataframe(self):
        data = {
            'Stock': ['AAPL', 'GOOGL', 'MSFT'],
            'LTP': [150, 2800, 300],
            '%Chng': ['1.5%', '2.0%', '3.0%'],
            '52Wk-H': [160, 2900, 310],
            "volume": [1000, 2000, 1500],
            'RSI': [45, 46, 64],
        }
        df = pd.DataFrame(data)
        df.set_index("Stock",inplace=True)
        self.monitor.refresh(screen_df=df, screenOptions='AAPL')
        self.assertFalse(self.monitor.monitor_df.empty)
        self.assertIn('LTP', self.monitor.monitor_df.columns)

    def test_refresh_with_pinnedMode(self):
        data = {
            'Stock': ['AAPL', 'GOOGL', 'MSFT'],
            'LTP': [150, 2800, 300],
            '%Chng': ['1.5%', '2.0%', '3.0%'],
            '52Wk-H': [160, 2900, 310],
            "volume": [1000, 2000, 1500],
            'RSI': [45, 46, 64],
        }
        df = pd.DataFrame(data)
        df.set_index("Stock",inplace=True)
        self.monitor.isPinnedSingleMonitorMode = True
        self.monitor.pinnedIntervalWaitSeconds = 0.1
        self.monitor.refresh(screen_df=df, screenOptions='AAPL')
        self.assertFalse(self.monitor.monitor_df.empty)
        self.assertIn('LTP', self.monitor.monitor_df.columns)

    def test_updateDataFrameForTelegramMode(self):
        data = {
            'Stock': ['AAPL', 'GOOGL'],
            'LTP': ['150', '2800'],
            'Ch%': ['1.5%', '2.0%'],
            'Vol': ['1000', '2000']
        }
        df = pd.DataFrame(data)
        result_df = self.monitor.updateDataFrameForTelegramMode(telegram=True, screen_monitor_df=df)
        self.assertEqual(len(result_df), 2)
        self.assertIn('LTP', result_df.columns)

    def test_getScanOptionName_with_valid_options(self):
        option_name = self.monitor.getScanOptionName("C:12:9:2.5:>|X:0:29:")
        self.assertNotEqual(option_name, "")

    def test_getScanOptionName_with_none(self):
        option_name = self.monitor.getScanOptionName(None)
        self.assertEqual(option_name, "")

    @patch('pkscreener.classes.Utility.tools.alertSound')
    def test_refresh_alert_condition(self, mock_alert):
        data = {
            'Stock': ['AAPL', 'GOOGL'],
            'LTP': [150, 2800],
            '%Chng': ['1.5%', '2.0%'],
            '52Wk-H': [160, 2900],
            "volume": [1000, 2000],
            'RSI': [45, 46],
        }
        df = pd.DataFrame(data)
        self.monitor.alertOptions = ['AAPL']
        self.monitor.refresh(screen_df=df, screenOptions='AAPL')
        mock_alert.assert_called_once()

    def test_updateIfRunningInTelegramBotMode(self):
        data = {
            'Stock': ['AAPL', 'GOOGL'],
            'LTP': ['150', '2800'],
            'Ch%': ['1.5%', '2.0%'],
            'Vol': ['1000', '2000']
        }
        df = pd.DataFrame(data)
        # Check if a file was created (mocking file operations could be done for more robust tests)
        with patch("pkscreener.classes.MarketMonitor.MarketMonitor.getScanOptionName") as mock_scanOption:
            mock_scanOption.return_value ="SomeOption"
            with patch('builtins.open') as mock_open:
                mock_open.return_value.close.return_value = None
                self.monitor.updateIfRunningInTelegramBotMode(screenOptions='AAPL', chosenMenu='Test Menu > 1 > 2 > 3 > 4', dbTimestamp='2023-10-01', telegram=True, telegram_df=df)
                mock_open.return_value.write.assert_called()

class TestMarketMonitor3(unittest.TestCase):

    def setUp(self):
        # Setup a MarketMonitor instance for testing
        self.monitor = MarketMonitor(monitors=['AAPL1', 'GOOGL1', 'MSFT1'])

    def test_saveMonitorResultStocks_with_valid_dataframe_prev_saved(self):
        indices = [0,1,2]        
        for index in indices:
            self.monitor.monitorIndex = index
            df0Stocks = pd.DataFrame()
            df2Stocks = pd.DataFrame(index=['AAPL1', 'MSFT1'],columns=["close"],data=[1,2])
            df3Stocks = pd.DataFrame(index=['AAPL1', 'MSFT1','GOOG1'],columns=["close"],data=[1,2,3])
            df4Stocks = pd.DataFrame(index=['AAPL1', 'MSFT1','GOOG1','TSLA1'],columns=["close"],data=[1,2,3,4])
            df5Stocks = pd.DataFrame(index=['AAPL1', 'MSFT1','GOOG1','TSLA1','OpenAI'],columns=["close"],data=[1,2,3,4,5])
            dfNewStocks = pd.DataFrame(index=['NewStock'],columns=["close"],data=[1])
            self.monitor.saveMonitorResultStocks(df2Stocks)
            # Initially all stocks should be in alert
            self.assertTrue(len(self.monitor.alertStocks) == 2)
            self.monitor.saveMonitorResultStocks(df3Stocks)
            # Only newly added stock should be in alert
            self.assertTrue('GOOG1' in self.monitor.alertStocks)
            self.assertTrue(len(self.monitor.alertStocks) == 1)
            self.monitor.saveMonitorResultStocks(df0Stocks)
            # Empty results should not cause any alert
            self.assertTrue(len(self.monitor.alertStocks) == 0)
            self.monitor.saveMonitorResultStocks(df2Stocks)
            # Same stocks being added again should not cause alerts
            self.assertTrue(len(self.monitor.alertStocks) == 0)
            # Same stocks being added again should not cause alerts
            self.monitor.saveMonitorResultStocks(df3Stocks)
            self.assertTrue(len(self.monitor.alertStocks) == 0)
            # Same stocks being added again should not cause alerts
            self.monitor.saveMonitorResultStocks(df2Stocks)
            self.assertTrue(len(self.monitor.alertStocks) == 0)
            # Only newly added stock should be in alert
            self.monitor.saveMonitorResultStocks(df4Stocks)
            self.assertTrue('TSLA1' in self.monitor.alertStocks)
            self.monitor.saveMonitorResultStocks(df0Stocks)
            # Empty results should not cause any alert
            self.assertTrue(len(self.monitor.alertStocks) == 0)
            # Only newly added stock should be in alert
            self.monitor.saveMonitorResultStocks(df5Stocks)
            self.assertTrue('OpenAI' in self.monitor.alertStocks)
            self.assertTrue(len(self.monitor.alertStocks) == 1)
            self.monitor.alertedStocks[str(self.monitor.monitorIndex)].extend(['NewStock'])
            self.monitor.saveMonitorResultStocks(dfNewStocks)
            self.assertTrue('NewStock' not in self.monitor.alertStocks)
            self.assertTrue(len(self.monitor.alertStocks) == 0)