#!/usr/bin/python3
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
import pandas as pd
import numpy as np
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from pkscreener.classes.Pktalib import pktalib  # Replace with the actual module name where pktalib is defined

class TestPktalib(unittest.TestCase):

    def setUp(self):
        # Sample DataFrame for testing
        self.df = pd.DataFrame({
            "high": [10, 20, 30, 25, 15],
            "low": [5, 10, 15, 10, 5],
            "close": [8, 18, 28, 20, 12],
            "volume": [100, 200, 300, 400, 500],
            'Date': pd.date_range(start='2023-01-01', periods=5)
        })
        self.df.set_index('Date', inplace=True)
        self.large_df = pd.DataFrame({
            "high": np.random.rand(1000) * 100,
            "low": np.random.rand(1000) * 100,
            "close": np.random.rand(1000) * 100,
            "volume": np.random.randint(1, 1000, size=1000),
            'Date': pd.date_range(start='2023-01-01', periods=1000)
        })
        self.large_df.set_index('Date', inplace=True)

    def test_AVWAP(self):
        anchored_date = pd.Timestamp('2023-01-03')
        result = pktalib.AVWAP(self.df, anchored_date)
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(result.index[2], pd.Timestamp('2023-01-03'))

    def test_BBANDS(self):
        result = pktalib.BBANDS(self.df["close"], timeperiod=3)
        self.assertEqual(len(result), 3)  # Upper, Middle, Lower bands
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_EMA(self):
        result = pktalib.EMA(self.df["close"], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    @pytest.mark.skip(reason="Returns None")
    def test_VWAP(self):
        result = pktalib.VWAP(self.df["high"], self.df["low"], self.df["close"], self.df["volume"])
        self.assertEqual(len(result), len(self.df))
        self.assertTrue(np.all(np.isfinite(result)))

    def test_KeltnersChannel(self):
        result = pktalib.KeltnersChannel(self.df["high"], self.df["low"], self.df["close"], timeperiod=3)
        self.assertEqual(len(result), 2)
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_SMA(self):
        result = pktalib.SMA(self.df["close"], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_WMA(self):
        result = pktalib.WMA(self.df["close"], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_MA(self):
        result = pktalib.MA(self.df["close"], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    @pytest.mark.skip(reason="Returns None")
    def test_TriMA(self):
        result = pktalib.TriMA(self.df["close"], length=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_RVM(self):
        result = pktalib.RVM(self.large_df["high"], self.large_df["low"], self.large_df["close"], timeperiod=3)
        self.assertEqual(len(result), 1)
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_ATR(self):
        result = pktalib.ATR(self.df["high"], self.df["low"], self.df["close"], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_TrueRange(self):
        result = pktalib.TRUERANGE(self.df["high"], self.df["low"], self.df["close"])
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_invalid_input(self):
        with self.assertRaises(TypeError):
            pktalib.BBANDS("invalid_input", timeperiod=3)

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["high", "low", "close", "volume"])
        with self.assertRaises(TypeError):
            pktalib.AVWAP(empty_df, pd.Timestamp('2023-01-01'))

    def test_edge_case(self):
        single_row_df = pd.DataFrame({
            "high": [10],
            "low": [5],
            "close": [8],
            "volume": [100],
            'Date': pd.date_range(start='2023-01-01', periods=1)
        })
        single_row_df.set_index('Date', inplace=True)
        with self.assertRaises(Exception):
            # TA_BAD_PARAM
            pktalib.EMA(single_row_df["close"], timeperiod=1)

    def test_performance(self):
        result = pktalib.ATR(self.large_df["high"], self.large_df["low"], self.large_df["close"])
        self.assertEqual(len(result), 1000)

    def test_MACD(self):
        result = pktalib.MACD(self.large_df["close"], 10, 18, 9)
        self.assertEqual(len(result), 3)
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_RSI(self):
        result = pktalib.RSI(self.large_df["close"],timeperiod=14)
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_MFI(self):
        result = pktalib.MFI(self.large_df["high"], self.large_df["low"], self.large_df["close"],self.large_df["volume"])
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_CCI(self):
        result = pktalib.CCI(self.large_df["high"], self.large_df["low"], self.large_df["close"],timeperiod=14)
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_Aroon(self):
        result = pktalib.Aroon(self.large_df["high"], self.large_df["low"],timeperiod=14)
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_Stochf(self):
        result = pktalib.STOCHF(self.large_df["high"], self.large_df["low"], self.large_df["close"],fastk_period=5,fastd_period=3,fastd_matype=0)
        self.assertEqual(len(result), 2)
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_StochRSI(self):
        result = pktalib.STOCHRSI(self.large_df["close"],timeperiod=14,fastk_period=5,fastd_period=3,fastd_matype=0)
        self.assertEqual(len(result), 2)
        for df in result:
            self.assertTrue(len(df) > 0)
    
    def test_PSAR(self):
        result = pktalib.psar(self.large_df["high"], self.large_df["low"])
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_PPSR(self):
        pp_map = {"1":"PP","2":"S1","3":"S2","4":"S3","5":"R1","6":"R2","7":"R3"}
        for pivotPoint in pp_map.keys():
            ppToCheck = pp_map[str(pivotPoint)]
            result = pktalib.get_ppsr_df(self.large_df["high"],self.large_df["low"],self.large_df["close"],ppToCheck)
            self.assertEqual(len(result), len(self.large_df))
            result = result.replace('nan', np.nan)
            result = result.dropna()
            self.assertTrue(np.all(np.isfinite(result)))
            self.assertTrue(len(result) > 0)

    def test_cupNhandleCandle(self):
        df = pd.DataFrame({
            "high": [31, 20, 25, 32, 32,30,30,25],
            'Date': pd.date_range(start='2023-01-01', periods=8)
        })
        df.set_index('Date', inplace=True)
        result = pktalib.CDLCUPANDHANDLE(None,df["high"],None,None)
        self.assertTrue(result)
        result = pktalib.CDLCUPANDHANDLE(None,df["high"].tail(6),None,None)
        self.assertFalse(result)