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
import pandas as pd
import numpy as np
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.OutputControls import OutputControls
from pkscreener.classes.Pktalib import pktalib  # Replace with the actual module name where pktalib is defined

class TestPktalib(unittest.TestCase):

    def setUp(self):
        # Sample DataFrame for testing
        self.df = pd.DataFrame({
            'High': [10, 20, 30, 25, 15],
            'Low': [5, 10, 15, 10, 5],
            'Close': [8, 18, 28, 20, 12],
            'Volume': [100, 200, 300, 400, 500],
            'Date': pd.date_range(start='2023-01-01', periods=5)
        })
        self.df.set_index('Date', inplace=True)
        self.large_df = pd.DataFrame({
            'High': np.random.rand(1000) * 100,
            'Low': np.random.rand(1000) * 100,
            'Close': np.random.rand(1000) * 100,
            'Volume': np.random.randint(1, 1000, size=1000),
            'Date': pd.date_range(start='2023-01-01', periods=1000)
        })
        self.large_df.set_index('Date', inplace=True)

    def test_AVWAP(self):
        anchored_date = pd.Timestamp('2023-01-03')
        result = pktalib.AVWAP(self.df, anchored_date)
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(result.index[2], pd.Timestamp('2023-01-03'))

    def test_BBANDS(self):
        result = pktalib.BBANDS(self.df['Close'], timeperiod=3)
        self.assertEqual(len(result), 3)  # Upper, Middle, Lower bands
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_EMA(self):
        result = pktalib.EMA(self.df['Close'], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_VWAP(self):
        result = pktalib.VWAP(self.df['High'], self.df['Low'], self.df['Close'], self.df['Volume'])
        self.assertEqual(len(result), len(self.df))
        self.assertTrue(np.all(np.isfinite(result)))

    def test_KeltnersChannel(self):
        result = pktalib.KeltnersChannel(self.df['High'], self.df['Low'], self.df['Close'], timeperiod=3)
        self.assertEqual(len(result), 2)
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_SMA(self):
        result = pktalib.SMA(self.df['Close'], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_WMA(self):
        result = pktalib.WMA(self.df['Close'], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_MA(self):
        result = pktalib.MA(self.df['Close'], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_TriMA(self):
        result = pktalib.TriMA(self.df['Close'], length=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_RVM(self):
        result = pktalib.RVM(self.large_df['High'], self.large_df['Low'], self.large_df['Close'], timeperiod=3)
        self.assertEqual(len(result), 1)
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_ATR(self):
        result = pktalib.ATR(self.df['High'], self.df['Low'], self.df['Close'], timeperiod=3)
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_TrueRange(self):
        result = pktalib.TRUERANGE(self.df['High'], self.df['Low'], self.df['Close'])
        self.assertEqual(len(result), len(self.df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_invalid_input(self):
        with self.assertRaises(TypeError):
            pktalib.BBANDS("invalid_input", timeperiod=3)

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=['High', 'Low', 'Close', 'Volume'])
        with self.assertRaises(TypeError):
            pktalib.AVWAP(empty_df, pd.Timestamp('2023-01-01'))

    def test_edge_case(self):
        single_row_df = pd.DataFrame({
            'High': [10],
            'Low': [5],
            'Close': [8],
            'Volume': [100],
            'Date': pd.date_range(start='2023-01-01', periods=1)
        })
        single_row_df.set_index('Date', inplace=True)
        with self.assertRaises(Exception):
            # TA_BAD_PARAM
            pktalib.EMA(single_row_df['Close'], timeperiod=1)

    def test_performance(self):
        result = pktalib.ATR(self.large_df['High'], self.large_df['Low'], self.large_df['Close'])
        self.assertEqual(len(result), 1000)

    def test_MACD(self):
        result = pktalib.MACD(self.large_df["Close"], 10, 18, 9)
        self.assertEqual(len(result), 3)
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_RSI(self):
        result = pktalib.RSI(self.large_df['Close'],timeperiod=14)
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_MFI(self):
        result = pktalib.MFI(self.large_df['High'], self.large_df['Low'], self.large_df['Close'],self.large_df["Volume"])
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_CCI(self):
        result = pktalib.CCI(self.large_df['High'], self.large_df['Low'], self.large_df['Close'],timeperiod=14)
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_Aroon(self):
        result = pktalib.Aroon(self.large_df['High'], self.large_df['Low'],timeperiod=14)
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_Stochf(self):
        result = pktalib.STOCHF(self.large_df['High'], self.large_df['Low'], self.large_df['Close'],fastk_period=5,fastd_period=3,fastd_matype=0)
        self.assertEqual(len(result), 2)
        for df in result:
            df = df.replace('nan', np.nan)
            df = df.dropna()
            self.assertTrue(np.all(np.isfinite(df)))
            self.assertTrue(len(df) > 0)

    def test_StochRSI(self):
        result = pktalib.STOCHRSI(self.large_df['Close'],timeperiod=14,fastk_period=5,fastd_period=3,fastd_matype=0)
        self.assertEqual(len(result), 2)
        for df in result:
            self.assertTrue(len(df) > 0)
    
    def test_PSAR(self):
        result = pktalib.psar(self.large_df['High'], self.large_df['Low'])
        self.assertEqual(len(result), len(self.large_df))
        result = result.replace('nan', np.nan)
        result = result.dropna()
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(len(result) > 0)

    def test_PPSR(self):
        pp_map = {"1":"PP","2":"S1","3":"S2","4":"S3","5":"R1","6":"R2","7":"R3"}
        for pivotPoint in pp_map.keys():
            ppToCheck = pp_map[str(pivotPoint)]
            result = pktalib.get_ppsr_df(self.large_df["High"],self.large_df["Low"],self.large_df["Close"],ppToCheck)
            self.assertEqual(len(result), len(self.large_df))
            result = result.replace('nan', np.nan)
            result = result.dropna()
            self.assertTrue(np.all(np.isfinite(result)))
            self.assertTrue(len(result) > 0)

    def test_cupNhandleCandle(self):
        df = pd.DataFrame({
            'High': [31, 20, 25, 32, 32,30,30,25],
            'Date': pd.date_range(start='2023-01-01', periods=8)
        })
        df.set_index('Date', inplace=True)
        result = pktalib.CDLCUPANDHANDLE(None,df["High"],None,None)
        self.assertTrue(result)
        result = pktalib.CDLCUPANDHANDLE(None,df["High"].tail(6),None,None)
        self.assertFalse(result)