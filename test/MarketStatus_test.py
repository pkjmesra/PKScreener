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
import pytest
from unittest.mock import patch, MagicMock

from pkscreener.classes.MarketStatus import MarketStatus

@pytest.mark.skip(reason="API has changed")
class TestMarketStatus(unittest.TestCase):
    
    def setUp(self):
        self.market_status = MarketStatus()
        self.market_status.attributes = {}

    def test_exchange_property_getter_default(self):
        self.assertEqual(self.market_status.exchange, "^NSEI")

    def test_exchange_property_setter(self):
        self.market_status.exchange = "^BSESN"
        self.assertEqual(self.market_status.exchange, "^BSESN")
        self.assertIn("exchange", self.market_status.attributes)

    def test_exchange_property_setter_no_change(self):
        self.market_status.exchange = "^NSEI"
        self.assertEqual(self.market_status.exchange, "^NSEI")
        self.assertIn("exchange", self.market_status.attributes)

    @patch('PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.capitalMarketStatus')
    def test_marketStatus_property_getter_default(self, mock_capitalMarketStatus):
        self.assertEqual(self.market_status.marketStatus, "")

    @patch('PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.capitalMarketStatus')
    def test_marketStatus_property_setter(self, mock_capitalMarketStatus):
        self.market_status.marketStatus = "open"
        self.assertEqual(self.market_status.marketStatus, "open")
        self.assertIn("marketStatus", self.market_status.attributes)

    def test_getMarketStatus_success(self):
        mock_fetcher = MagicMock()
        mock_fetcher.capitalMarketStatus.return_value = ("open", "Closed", None)
        MarketStatus.nseFetcher = mock_fetcher
        
        result = self.market_status.getMarketStatus(exchangeSymbol="^NSEI")
        self.assertTrue("open" in result or "close" in result)
        self.assertIn("marketStatus", self.market_status.attributes)
        self.assertTrue("open" in self.market_status.marketStatus or "close" in self.market_status.marketStatus)

    @patch('PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.capitalMarketStatus', side_effect=Exception("Fetch Error"))
    def test_getMarketStatus_exception(self, mock_capitalMarketStatus):
        result = self.market_status.getMarketStatus(exchangeSymbol="^NSEI")
        self.assertEqual(result, "")
        self.assertIn("marketStatus", self.market_status.attributes)
        self.assertEqual(self.market_status.marketStatus, "")

    @patch('os.environ', {'PKDevTools_Default_Log_Level': '0'})
    @patch('PKNSETools.PKNSEStockDataFetcher.nseStockDataFetcher.capitalMarketStatus')
    def test_getMarketStatus_with_progress(self, mock_capitalMarketStatus):
        mock_fetcher = MagicMock()
        mock_fetcher.capitalMarketStatus.return_value = ("open", "Closed", None)
        MarketStatus.nseFetcher = mock_fetcher
        
        progress = {}
        result = self.market_status.getMarketStatus(progress=progress, task_id=1, exchangeSymbol="^NSEI")
        
        self.assertTrue("open" in result or "close" in result)
        # self.assertIn(1, progress)
        # self.assertEqual(progress[1], {"progress": 1, "total": 1})

    def test_getMarketStatus_invalid_exchange(self):
        result = self.market_status.getMarketStatus(exchangeSymbol="^INVALID")
        self.assertEqual(result, "S&P BSE SENSEX | Closed | 2025-02-13 | 76138.97 | \x1b[31m▼-32.11\x1b[0m (\x1b[31m-0.04\x1b[0m%)")
        self.assertEqual(self.market_status.marketStatus, "S&P BSE SENSEX | Closed | 2025-02-13 | 76138.97 | \x1b[31m▼-32.11\x1b[0m (\x1b[31m-0.04\x1b[0m%)")
