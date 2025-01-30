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
import requests
from requests.exceptions import HTTPError
from requests import Response
import pytest
import io
import pandas as pd
from unittest.mock import ANY, MagicMock, patch
from unittest import mock
import json
from requests_cache import AnyResponse, CachedHTTPResponse, CachedResponse

def google_query(query):
    """
    trivial function that does a GET request
    against google, checks the status of the
    result and returns the raw content
    """
    url = "https://www.google.com"
    params = {'q': query}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.content

class RequestsMocker:
    def __init__(self) -> None:
        try:
            with open('test/Fixture.json') as f:
                d = json.load(f)
                self.savedResponses = d
        except:
            self.savedResponses = {}
            pass
        try:
            self.stockSortedDF = pd.read_html("test/StockSorted.html")
        except:
            self.stockSortedDF = pd.DataFrame()
            pass
        try:
            self.dateSortedDF = pd.read_html("test/DateSorted.html")
        except:
            self.dateSortedDF = pd.DataFrame()
            pass
        try:
            with open('pkscreener/release.md') as r:
                self.savedResponses["release.md"] = r.read()
        except:
            self.savedResponses["release.md"] = ""
            pass
        try:
            self.savedResponses["/finance/chart/"] = self.get_saved_yf_response()
        except:
            self.savedResponses["/finance/chart/"] = ""
            pass

    def patched_readhtml(self, *args, **kwargs) -> list[pd.DataFrame]:
        if args[0].endswith("StockSorted.html"):
            return self.stockSortedDF
        elif args[0].endswith("DateSorted.html"):
            return self.dateSortedDF

    def patched_yf(self, *args, **kwargs) -> pd.DataFrame:
        savedResponses = self.get_saved_yf_response()
        df = pd.DataFrame.from_dict(savedResponses, orient='columns')
        return df

    def get_saved_yf_response(self):
        savedResponses = ""
        with open('test/yahoo_response.txt') as f:
            savedResponses = json.load(f)
        return savedResponses
    
    def get_saved_yf_response_object(self):
        user_encode_data = json.dumps(self.get_saved_yf_response(), indent=2).encode('utf-8')
        r = CachedResponse(status_code=200)
        r._content = user_encode_data
        r.raw = CachedHTTPResponse(body=user_encode_data,status=200,reason="OK")
        return r
        
    def patched_get(self, *args, **kwargs) -> AnyResponse:
        return self.patched_fetchURL(*args, **kwargs)

    def patched_post(self, *args, **kwargs)-> AnyResponse:
        r = self.returnFromFixture(*args, **kwargs)
        if r is None and len(args) > 2:
            s = requests.Session()
            return s.post(args[0],data=args[2],**kwargs)
        return r

    def patched_fetchURL(self, *args, **kwargs) -> AnyResponse:
        r = None
        if args is not None and len(args) > 0:
            r = self.returnFromFixture(*args, **kwargs)
        if r is None and len(args) > 0:
            if "RECURSION_STOPPER" in args[0]:
                return self.defaultEmptyResponse()
            s = requests.Session()
            args=(f"{args[0]}{'&' if '?' in args[0] else '?'}RECURSION_STOPPER=1",)
            return s.get(args[0],**kwargs)
        return r

    def defaultEmptyResponse(self):
        user_encode_data = json.dumps("Empty mock up response! You need to define a fixture to capture this request!", indent=2).encode('utf-8')
        r = CachedResponse(status_code=200)
        r._content = user_encode_data
        r.raw = CachedHTTPResponse(body=user_encode_data,status=200,reason="OK")
        return r
    
    def returnFromFixture(self, *args, **kwargs) -> AnyResponse:
        if args[0] in self.savedResponses.keys():
            user_encode_data = json.dumps(self.savedResponses[args[0]], indent=2).encode('utf-8')
            r = CachedResponse(status_code=200)
            r._content = user_encode_data
            r.raw = CachedHTTPResponse(body=user_encode_data,status=200,reason="OK")
            return r
        else:
            foundKey = None
            for key in self.savedResponses.keys():
                if key in args[0]:
                    foundKey = key
                    break
            if foundKey is not None:
                user_encode_data = self.savedResponses[foundKey].encode('utf-8')
                r = CachedResponse(status_code=200)
                r._content = user_encode_data
                r.raw = CachedHTTPResponse(body=user_encode_data,status=200,reason="OK")
                return r
        return None
    """
    example text that mocks requests.get and
    returns a mock Response object
    """
    def _mock_response(
            self,
            status=200,
            content="CONTENT",
            json_data=None,
            raise_for_status=None):
        """
        since we typically test a bunch of different
        requests calls for a service, we are going to do
        a lot of mock responses, so its usually a good idea
        to have a helper function that builds these things
        """
        mock_resp = mock.Mock()
        # mock raise_for_status call w/optional error
        mock_resp.raise_for_status = mock.Mock()
        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status
        # set status code and content
        mock_resp.status_code = status
        mock_resp.content = content
        # add json data if provided
        if json_data:
            mock_resp.json = mock.Mock(
                return_value=json_data
            )
        return mock_resp

    @mock.patch('requests.get')
    def test_google_query(self, mock_get):
        """test google query method"""
        mock_resp = self._mock_response(content="ELEPHANTS")
        mock_get.return_value = mock_resp

        result = google_query('elephants')
        self.assertEqual(result, 'ELEPHANTS')
        self.assertTrue(mock_resp.raise_for_status.called)

    @mock.patch('requests.get')
    def test_failed_query(self, mock_get):
        """test case where google is down"""
        mock_resp = self._mock_response(status=500, raise_for_status=HTTPError("google is down"))
        mock_get.return_value = mock_resp
        self.assertRaises(HTTPError, google_query, 'elephants')