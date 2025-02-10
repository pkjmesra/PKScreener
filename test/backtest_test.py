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

import warnings

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
import pytest

from pkscreener.classes import Utility, ConsoleUtility
from pkscreener.classes.Backtest import backtest, backtestSummary

@pytest.fixture
def sample_data():
    data = pd.DataFrame(
        {
            "Date": [
                "2021-01-01",
                "2021-01-02",
                "2021-01-03",
                "2021-01-04",
                "2021-01-05",
            ],
            "Close": [100, 110, 120, 130, 140],
            "Stock": ["SBIN", "IRCTC", "SBIN", "TCS", "HDFC"],
        }
    )
    return data


@pytest.fixture
def sample_screened_dict():
    periods = [1, 2, 3, 4, 5, 10, 15, 22, 30]
    screened_dict = {
        "Date": "2023-12-30",
        "Volume": 1000,
        "Trend": "Up",
        "MA-Signal": "Buy",
        "LTP": 100,
        "52Wk-H": 100,
        "52Wk-L": 10,
        "Consol.": "Range: 5%",
        "Breakout": "BO: 101 R: 115",
        "RSI": 68,
        "Pattern": "NR4",
        "CCI": 201,
    }
    for period in periods:
        screened_dict[f"LTP{period}"] = screened_dict["LTP"] * period / 10
    return screened_dict


def test_backtest_no_data():
    result = backtest("", None)
    assert result is None


def test_backtest_no_strategy(sample_data):
    result = backtest("AAPL", sample_data, saveDict=None, screenedDict=None)
    assert result is None


def test_backtest_with_data_and_strategy(sample_screened_dict,sample_data):
    result = backtest(
        "AAPL",
        sample_data,
        saveDict=sample_screened_dict,
        screenedDict=sample_screened_dict,
        sellSignal=True
    )
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1


def test_backtest_summary_no_data():
    result = backtestSummary(None)
    assert result is None


def test_backtest_summary_with_data():
    result = backtestSummary(sample_summary_data())
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2


def test_formatted_output_high_outcome():
    result = ConsoleUtility.PKConsoleTools.formattedBacktestOutput(85)
    assert result == "\x1b[32m85.00%\x1b[0m"


def test_formatted_output_medium_outcome():
    result = ConsoleUtility.PKConsoleTools.formattedBacktestOutput(65)
    assert result == "\x1b[33m65.00%\x1b[0m"


def test_formatted_output_low_outcome():
    result = ConsoleUtility.PKConsoleTools.formattedBacktestOutput(45)
    assert result == "\x1b[31m45.00%\x1b[0m"


def sample_summary_data():
    data = {
        "Stock": [
            "AAPL",
            "AAPL",
            "AAPL",
            "AAPL",
            "AAPL",
            "AAPL",
            "AAPL",
            "AAPL",
            "AAPL",
            "AAPL",
        ],
        "Date": [
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
            "2022-01-01",
        ],
        "Volume": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        "LTP": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        "Trend": ["Up", "Up", "Down", "Up", "Down", "Up", "Down", "Up", "Down", "Up"],
        "MA-Signal": [
            "Buy",
            "Buy",
            "Sell",
            "Buy",
            "Sell",
            "Buy",
            "Sell",
            "Buy",
            "Sell",
            "Buy",
        ],
        "1-Pd": [
            "10%",
            "20%",
            "-5%",
            "15%",
            "-10%",
            "25%",
            "-15%",
            "30%",
            "-20%",
            "35%",
        ],
        "2-Pd": [
            "15%",
            "25%",
            "-10%",
            "20%",
            "-15%",
            "30%",
            "-20%",
            "35%",
            "-25%",
            "40%",
        ],
        "3-Pd": [
            "20%",
            "30%",
            "-15%",
            "25%",
            "-20%",
            "35%",
            "-25%",
            "40%",
            "-30%",
            "45%",
        ],
        "4-Pd": [
            "25%",
            "35%",
            "-20%",
            "30%",
            "-25%",
            "40%",
            "-30%",
            "45%",
            "-35%",
            "50%",
        ],
        "5-Pd": [
            "30%",
            "40%",
            "-25%",
            "35%",
            "-30%",
            "45%",
            "-35%",
            "50%",
            "-40%",
            "55%",
        ],
        "10-Pd": [
            "35%",
            "45%",
            "-30%",
            "40%",
            "-35%",
            "50%",
            "-40%",
            "55%",
            "-45%",
            "60%",
        ],
        "15-Pd": [
            "40%",
            "50%",
            "-35%",
            "45%",
            "-40%",
            "55%",
            "-45%",
            "60%",
            "-50%",
            "65%",
        ],
        "22-Pd": [
            "45%",
            "55%",
            "-40%",
            "50%",
            "-45%",
            "60%",
            "-50%",
            "65%",
            "-55%",
            "70%",
        ],
        "30-Pd": [
            "50%",
            "60%",
            "-45%",
            "55%",
            "-50%",
            "65%",
            "-55%",
            "70%",
            "-60%",
            "75%",
        ],
    }
    return pd.DataFrame(data)


def test_backtestSummary_positive():
    summary_df = backtestSummary(sample_summary_data())
    assert isinstance(summary_df, pd.DataFrame)
    assert len(summary_df) == 2
    assert summary_df.columns.tolist() == [
        "Stock",
        "1-Pd",
        "2-Pd",
        "3-Pd",
        "4-Pd",
        "5-Pd",
        "10-Pd",
        "15-Pd",
        "22-Pd",
        "30-Pd",
        "Overall",
    ]
    assert summary_df["Stock"].tolist() == ["AAPL", "SUMMARY"]


def test_backtestSummary_no_data():
    summary_df = backtestSummary(None)
    assert summary_df is None


def test_formattedOutput():
    assert ConsoleUtility.PKConsoleTools.formattedBacktestOutput(85) == "\x1b[32m85.00%\x1b[0m"
    assert ConsoleUtility.PKConsoleTools.formattedBacktestOutput(70) == "\x1b[33m70.00%\x1b[0m"
    assert ConsoleUtility.PKConsoleTools.formattedBacktestOutput(40) == "\x1b[31m40.00%\x1b[0m"


def test_backtest(sample_data):
    stock = "AAPL"
    screenedDict = {
        "Consol.": True,
        "Breakout": False,
        "MA-Signal": True,
        "Volume": False,
        "LTP": True,
        "52Wk-H": False,
        "52Wk-L": True,
        "RSI": True,
        "Trend": False,
        "Pattern": True,
        "CCI": False
    }
    saveDict = screenedDict
    saveDict["Date"] = "SomeDate"
    periods = 30
    backTestedData = None
    sellSignal = False

    result = backtest(stock, sample_data, saveDict, screenedDict, periods, backTestedData, sellSignal)

    assert result is not None

def test_backtest_no_data_empty():
    stock = "AAPL"
    data = None
    saveDict = None
    screenedDict = {
        "Consol.": True,
        "Breakout": False,
        "MA-Signal": True,
        "Volume": False,
        "LTP": True,
        "52Wk-H": False,
        "52Wk-L": True,
        "RSI": True,
        "Trend": False,
        "Pattern": True,
        "CCI": False
    }
    periods = 30
    backTestedData = None
    sellSignal = False

    result = backtest(stock, data, saveDict, screenedDict, periods, 30, backTestedData, sellSignal)
    assert result is None
    backTestedData = pd.DataFrame([{}])
    result = backtest(stock, pd.DataFrame(), saveDict, screenedDict, periods, 1, backTestedData, sellSignal)
    pd.testing.assert_frame_equal(result,backTestedData)

def test_backtestSummary_2row_summary():
    df = pd.DataFrame({
        "Stock": ["AAPL", "AAPL", "AAPL"],
        "1-Pd": [1, 0, 1],
        "2-Pd": [0, 1, 0],
        "Overall": [50.0, 50.0, 50.0]
    })

    result = backtestSummary(df)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
