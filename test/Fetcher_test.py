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
from unittest import mock
from unittest.mock import ANY, MagicMock, patch

import pandas as pd
import pytest
from requests.exceptions import ConnectTimeout, ReadTimeout
from urllib3.exceptions import ReadTimeoutError

from pkscreener.classes import ConfigManager
from pkscreener.classes.Fetcher import StockDataEmptyException, tools


@pytest.fixture
def configManager():
    return ConfigManager.tools()

@pytest.fixture
def tools_instance(configManager):
    return tools(configManager)

def test_fetchCodes_positive(configManager, tools_instance):
    with patch('requests_cache.CachedSession.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "SYMBOL\nAAPL\nGOOG\n"
        result = tools_instance.fetchCodes(12)
        assert result == ['AAPL', 'GOOG']
        mock_get.assert_called_once_with(
            "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
            proxies=None,
            stream = False,
            timeout=ANY
        )

def test_fetchCodes_positive_proxy(configManager, tools_instance):
    with patch('requests_cache.CachedSession.get') as mock_get:
        with patch('pkscreener.classes.Fetcher.tools._getProxyServer') as mock_proxy:
            mock_proxy.return_value = {"https": "127.0.0.1:8080"}
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "SYMBOL\nAAPL\nGOOG\n"
            result = tools_instance.fetchCodes(12)
            assert result == ['AAPL', 'GOOG']
            mock_get.assert_called_once_with(
                "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
                proxies={"https":"127.0.0.1:8080"},
                stream = False,
                timeout=ANY
            )

def test_fetchCodes_negative(configManager, tools_instance):
    with patch('requests_cache.CachedSession.get') as mock_get:
        with patch('pkscreener.classes.Fetcher.tools._getProxyServer') as mock_proxy:
            mock_proxy.return_value = {"https": "127.0.0.1:8080"}
            mock_get.side_effect = Exception("Error fetching data")
            with pytest.raises(Exception):
                result = tools_instance.fetchCodes(12)
                assert result == []
                mock_get.assert_called_once_with(
                    "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
                    roxies=mock_proxy.return_value,
                    stream = False,
                    timeout=ANY
                )

def test_fetchCodes_ReadTimeoutError_negative(configManager, tools_instance):
    with patch('requests_cache.CachedSession.get') as mock_get:
        mock_get.side_effect = ReadTimeoutError(None,None,"Error fetching data")
        result = tools_instance.fetchCodes(12)
        assert len(result) > 0
        1 < mock_get.call_count <= int(configManager.maxNetworkRetryCount)

def test_fetchCodes_Exception_negative(configManager, tools_instance):
    with patch('requests_cache.CachedSession.get') as mock_get:
        mock_get.side_effect = Exception("sqlite3.OperationalError: attempt to write a readonly database")
        result = tools_instance.fetchURL("https://exampl.ecom/someresource/", stream=True)
        assert result is None
        1 < mock_get.call_count <= int(configManager.maxNetworkRetryCount)

def test_fetchCodes_Exception_fallback_requests(configManager, tools_instance):
    with patch('requests_cache.CachedSession.get') as mock_get:
        with patch('requests.get') as mock_fallback_get:
            mock_get.side_effect = Exception("sqlite3.OperationalError: attempt to write a readonly database")
            result = tools_instance.fetchURL("https://exampl.ecom/someresource/", stream=True)
            assert result is not None # because mock_fallback_get will be assigned
            mock_fallback_get.assert_called()
            1 < mock_get.call_count <= int(configManager.maxNetworkRetryCount)

def test_fetchStockCodes_positive(configManager, tools_instance):
    with patch('pkscreener.classes.Fetcher.tools.fetchCodes') as mock_fetchCodes:
        mock_fetchCodes.return_value = ['AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG',]
        result = tools_instance.fetchStockCodes(1)
        assert len(result) == len(['AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG'])
        mock_fetchCodes.assert_called_once_with(1)

def test_fetchStockCodes_positive_proxy(configManager, tools_instance):
    with patch('pkscreener.classes.Fetcher.tools._getProxyServer') as mock_proxy:
        with patch('requests_cache.CachedSession.get') as mock_get:
            mock_proxy.return_value = {"https": "127.0.0.1:8080"}
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "\n".join([',,,',',,AAPL', ',,GOOG',',,AAPL', ',,GOOG',',,AAPL', ',,GOOG',',,AAPL', ',,GOOG',',,AAPL', ',,GOOG',',,AAPL', ',,GOOG'])
            result = tools_instance.fetchStockCodes(1)
            assert len(result) == len(['AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG','AAPL', 'GOOG'])
            mock_get.assert_called_with(ANY, proxies=mock_proxy.return_value, stream=False, timeout=ANY)

def test_fetchStockCodes_negative(configManager, tools_instance):
    with patch('pkscreener.classes.Fetcher.tools.fetchCodes') as mock_fetchCodes:
        mock_fetchCodes.side_effect = Exception("Error fetching stock codes")
        with pytest.raises(Exception):
            result = tools_instance.fetchStockCodes(1)
            assert result == []
            mock_fetchCodes.assert_called_once_with(1)

def test_fetchStockData_positive(configManager, tools_instance):
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = pd.DataFrame({'Close': [100, 200, 300]})
        result = tools_instance.fetchStockData('AAPL', '1d', '1m', None, 0, 0, 1)
        assert result.equals(pd.DataFrame({'Close': [100, 200, 300]}))
        mock_download.assert_called_once_with(
            tickers='AAPL.NS',
            period='1d',
            interval='1m',
            proxy=None,
            progress=False,
            timeout=configManager.longTimeout
        )

def test_fetchStockData_negative(configManager, tools_instance):
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = pd.DataFrame()
        with pytest.raises(StockDataEmptyException):
            tools_instance.fetchStockData('AAPL', '1d', '1m', None, 0, 0, 1,printCounter=True)
        mock_download.assert_called_once_with(
            tickers='AAPL.NS',
            period='1d',
            interval='1m',
            proxy=None,
            progress=False,
            timeout=configManager.longTimeout
        )

def test_fetchLatestNiftyDaily_positive(configManager, tools_instance):
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = pd.DataFrame({'Close': [100, 200, 300]})
        result = tools_instance.fetchLatestNiftyDaily()
        assert result.equals(pd.DataFrame({'Close': [100, 200, 300]}))
        mock_download.assert_called_once_with(
            tickers='^NSEI',
            period='5d',
            interval='1d',
            proxy=None,
            progress=False,
            timeout=configManager.longTimeout
        )

def test_fetchFiveEmaData_positive(configManager, tools_instance):
    with patch('yfinance.download') as mock_download:
        mock_download.side_effect = [
            pd.DataFrame({'Close': [100, 200, 300]}),
            pd.DataFrame({'Close': [400, 500, 600]}),
            pd.DataFrame({'Close': [700, 800, 900]}),
            pd.DataFrame({'Close': [1000, 1100, 1200]})
        ]
        r1,r2,r3,r4 = tools_instance.fetchFiveEmaData()
        r1_diff = pd.concat([r1,pd.DataFrame({'Close': [700, 800, 900]})]).drop_duplicates(keep=False)
        r2_diff = pd.concat([r2,pd.DataFrame({'Close': [1000, 1100, 1200]})]).drop_duplicates(keep=False)
        r3_diff = pd.concat([r3,pd.DataFrame({'Close': [100, 200, 300]})]).drop_duplicates(keep=False)
        r4_diff = pd.concat([r4,pd.DataFrame({'Close': [400, 500, 600]})]).drop_duplicates(keep=False)
        assert r1_diff.empty is True
        assert r2_diff.empty is True
        assert r3_diff.empty is True
        assert r4_diff.empty is True
        mock_download.assert_has_calls([
            mock.call(
                tickers='^NSEI',
                period='5d',
                interval='5m',
                proxy=None,
                progress=False,
                timeout=configManager.longTimeout
            ),
            mock.call(
                tickers='^NSEBANK',
                period='5d',
                interval='5m',
                proxy=None,
                progress=False,
                timeout=configManager.longTimeout
            ),
            mock.call(
                tickers='^NSEI',
                period='5d',
                interval='15m',
                proxy=None,
                progress=False,
                timeout=configManager.longTimeout
            ),
            mock.call(
                tickers='^NSEBANK',
                period='5d',
                interval='15m',
                proxy=None,
                progress=False,
                timeout=configManager.longTimeout
            )
        ])

def test_fetchWatchlist_positive(tools_instance):
    with patch('pandas.read_excel') as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame({'Stock Code': ['AAPL', 'GOOG']})
        result = tools_instance.fetchWatchlist()
        assert result == ['AAPL', 'GOOG']
        mock_read_excel.assert_called_once_with("watchlist.xlsx")

def test_fetchWatchlist_negative(tools_instance):
    with patch('pandas.read_excel') as mock_read_excel:
        mock_read_excel.side_effect = FileNotFoundError("File not found")
        result = tools_instance.fetchWatchlist()
        assert result is None
        mock_read_excel.assert_called_once_with("watchlist.xlsx")

def test_fetchWatchlist_Actual_file(tools_instance):
    sample = {"Stock Code": ["SBIN", "INFY", "TATAMOTORS", "ITC"]}
    sample_data = pd.DataFrame(sample, columns=["Stock Code"])
    sample_data.to_excel("watchlist.xlsx", index=False, header=True)
    result = tools_instance.fetchWatchlist()
    assert result == ["SBIN", "INFY", "TATAMOTORS", "ITC"]

def test_postURL_positive(tools_instance):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    response = MagicMock()
    response.status_code = 200
    with patch("requests_cache.CachedSession.post", return_value=response) as mock_post:
        result = tools_instance.postURL(url, data=data, headers=headers)
        mock_post.assert_called_once_with(url, proxies=None, data=data, headers=headers, timeout=2)
        assert result == response

def test_postURL_connect_timeout(tools_instance):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    with patch("requests_cache.CachedSession.post", side_effect=ConnectTimeout) as mock_post:
        tools_instance.postURL(url, data=data, headers=headers)
        mock_post.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=8)

def test_postURL_read_timeout(tools_instance):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    with patch("requests_cache.CachedSession.post", side_effect=ReadTimeout) as mock_post:
        tools_instance.postURL(url, data=data, headers=headers)
        mock_post.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=8)

def test_postURL_other_exception(tools_instance):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content": "application/json"}
    with patch("requests_cache.CachedSession.post", side_effect=Exception) as mock_post:
        tools_instance.postURL(url, data=data, headers=headers)
        mock_post.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=8)

def test_postURL_retry_connect_timeout(tools_instance):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    response = MagicMock()
    response.status_code = 200
    with patch("requests_cache.CachedSession.post", side_effect=[ConnectTimeout, response]) as mock_post:
        result = tools_instance.postURL(url, data=data, headers=headers)
        mock_post.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=4)
        assert result == response

def test_postURL_retry_read_timeout(tools_instance):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    response = MagicMock()
    response.status_code = 200
    with patch("requests_cache.CachedSession.post", side_effect=[ReadTimeout, response]) as mock_post:
        result = tools_instance.postURL(url, data=data, headers=headers)
        mock_post.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=4)
        assert result == response

def test_postURL_retry_other_exception(tools_instance):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    response = MagicMock()
    response.status_code = 200
    with patch("requests_cache.CachedSession.post", side_effect=[Exception, response]) as mock_post:
        result = tools_instance.postURL(url, data=data, headers=headers)
        mock_post.assert_called_with (url,proxies=None, data=data, headers=headers, timeout=4)
        assert result == response

def test_postURL_retry_max_retries(tools_instance, configManager):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    response = MagicMock()
    response.status_code = 200
    configManager.maxNetworkRetryCount = 4
    with patch("requests_cache.CachedSession.post", side_effect=[ConnectTimeout]):
        with patch("requests.post") as mock_post_later:
            tools_instance.postURL(url, data=data, headers=headers)
            mock_post_later.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=4)

def test_postURL_retry_disable_cache(tools_instance, configManager):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    response = MagicMock()
    response.status_code = 200
    configManager.maxNetworkRetryCount = 3
    with patch("requests_cache.CachedSession.post", side_effect=[ConnectTimeout, response]):
        with patch("requests_cache.is_installed", return_value=True) as mock_is_installed:
            tools_instance.postURL(url, data=data, headers=headers)
            mock_is_installed.assert_called_once()

def test_postURL_retry_enable_cache_restart(tools_instance, configManager):
    url = "https://example.com"
    data = {"key": "value"}
    headers = {"Content-Type": "application/json"}
    response = MagicMock()
    response.status_code = 200
    configManager.maxNetworkRetryCount = 3
    with patch("requests_cache.CachedSession.post", side_effect=[ConnectTimeout, response]):
        with patch("requests_cache.is_installed", return_value=False):
            with patch("pkscreener.classes.ConfigManager.tools.restartRequestsCache") as mock_restart_cache:
                tools_instance.postURL(url, data=data, headers=headers, trial=2)
                mock_restart_cache.assert_called_once()

# def test_postURL_retry_enable_cache_uninstall(tools_instance, configManager):
#     url = "https://example.com"
#     data = {"key": "value"}
#     headers = {"Content-Type": "application/json"}
#     response = MagicMock()
#     response.status_code = 200
#     configManager.maxNetworkRetryCount = 3
#     with patch("requests.post", side_effect=[Exception, response]):
#         with patch("requests_cache.is_installed", return_value=False):
#             with patch("requests_cache.uninstall_cache") as mock_uninstall_cache:
#                 tools_instance.postURL(url, data=data, headers=headers, trial=2)
#                 mock_uninstall_cache.assert_called_once()

# def test_postURL_retry_enable_cache_clear(tools_instance, configManager):
#     url = "https://example.com"
#     data = {"key": "value"}
#     headers = {"Content-Type": "application/json"}
#     response = MagicMock()
#     response.status_code = 200
#     configManager.maxNetworkRetryCount = 3
#     with patch("requests_cache.CachedSession.post", side_effect=[ConnectTimeout, response]) as mock_post:
#         with patch("requests_cache.is_installed", return_value=False) as mock_is_installed:
#             with patch("requests_cache.clear") as mock_clear_cache:
#                 result = tools_instance.postURL(url, data=data, headers=headers)
#                 mock_post.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=6)
#                 mock_is_installed.assert_called_once()
#                 mock_clear_cache.assert_called_once()
#                 assert result == response

# def test_postURL_retry_enable_cache_restart_uninstall_clear(tools_instance, configManager):
#     url = "https://example.com"
#     data = {"key": "value"}
#     headers = {"Content-Type": "application/json"}
#     response = MagicMock()
#     response.status_code = 200
#     configManager.maxNetworkRetryCount = 3
#     with patch("requests_cache.CachedSession.post", side_effect=[ConnectTimeout, response]) as mock_post:
#         with patch("requests_cache.is_installed", return_value=False) as mock_is_installed:
#             with patch("tools.restartRequestsCache") as mock_restart_cache:
#                 with patch("requests_cache.uninstall_cache") as mock_uninstall_cache:
#                     with patch("requests_cache.clear") as mock_clear_cache:
#                         result = tools_instance.postURL(url, data=data, headers=headers)
#                         mock_post.assert_called_with(url, proxies=None, data=data, headers=headers, timeout=6)
#                         mock_is_installed.assert_called_once()
#                         mock_restart_cache.assert_called_once()
#                         mock_uninstall_cache.assert_called_once()
#                         mock_clear_cache.assert_called_once()
#                         assert result == response

# def test_postURL_retry_enable_cache_restart_uninstall_clear_max_retries(tools_instance, configManager):
#     url = "https://example.com"
#     data = {"key": "value"}
#     headers = {"Content-Type": "application/json"}
#     configManager.maxNetwork = 1
#     with patch("requests_cache.CachedSession.post", side_effect=ConnectTimeout):
#         with patch("postURL.requests_cache.is_installed", return_value=False) as mock_is_installed:
#             with patch("postURL.tools.restartRequestsCache") as mock_restart_cache:
#                 with patch("postURL.requests_cache.uninstall_cache") as mock_uninstall_cache:
#                     with patch("postURL.requests_cache.clear") as mock_clear_cache:
#                         with pytest.raises(ConnectTimeout):
#                             tools_instance.postURL(url, data=data, headers=headers)
#                         mock_is_installed.assert_called_once()
#                         mock_restart_cache.assert_not_called()
#                         mock_uninstall_cache.assert_not_called()
#                         mock_clear_cache.assert_not_called()
