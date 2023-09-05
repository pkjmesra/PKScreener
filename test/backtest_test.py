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

from pkscreener.classes.Backtest import (backtest, backtestSummary,
                                         formattedOutput)


def sample_data():
    data = pd.DataFrame({
        'Date': ['2021-01-01', '2021-01-02', '2021-01-03', '2021-01-04', '2021-01-05'],
        'Close': [100, 110, 120, 130, 140],
        "Stock":["SBIN","IRCTC","SBIN","TCS","HDFC"],
    })
    return data

@pytest.fixture
def sample_screened_dict():
    screened_dict = {
        'Volume': 1000,
        'Trend': 'Up',
        'MA-Signal': 'Buy'
    }
    return screened_dict

def test_backtest_no_data():
    result = backtest("", None)
    assert result is None

def test_backtest_no_strategy():
    result = backtest("AAPL", sample_data(), screenedDict=None)
    assert result is None

def test_backtest_with_data_and_strategy(sample_screened_dict):
    result = backtest("AAPL", sample_data(), screenedDict=sample_screened_dict)
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
    result = formattedOutput(85)
    assert result == '\x1b[92m85.00%\x1b[0m'

def test_formatted_output_medium_outcome():
    result = formattedOutput(65)
    assert result == '\x1b[93m65.00%\x1b[0m'

def test_formatted_output_low_outcome():
    result = formattedOutput(45)
    assert result == '\x1b[91m45.00%\x1b[0m'

def sample_summary_data():
    data = {
        "Stock": ["AAPL", "AAPL", "AAPL", "AAPL", "AAPL", "AAPL", "AAPL", "AAPL", "AAPL", "AAPL"],
        "Base-Date": ["2022-01-01", "2022-01-01", "2022-01-01", "2022-01-01", "2022-01-01", "2022-01-01", "2022-01-01", "2022-01-01", "2022-01-01", "2022-01-01"],
        "Volume": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        "Trend": ["Up", "Up", "Down", "Up", "Down", "Up", "Down", "Up", "Down", "Up"],
        "MA-Signal": ["Buy", "Buy", "Sell", "Buy", "Sell", "Buy", "Sell", "Buy", "Sell", "Buy"],
        "1-Pd": ["10%", "20%", "-5%", "15%", "-10%", "25%", "-15%", "30%", "-20%", "35%"],
        "2-Pd": ["15%", "25%", "-10%", "20%", "-15%", "30%", "-20%", "35%", "-25%", "40%"],
        "3-Pd": ["20%", "30%", "-15%", "25%", "-20%", "35%", "-25%", "40%", "-30%", "45%"],
        "4-Pd": ["25%", "35%", "-20%", "30%", "-25%", "40%", "-30%", "45%", "-35%", "50%"],
        "5-Pd": ["30%", "40%", "-25%", "35%", "-30%", "45%", "-35%", "50%", "-40%", "55%"],
        "10-Pd": ["35%", "45%", "-30%", "40%", "-35%", "50%", "-40%", "55%", "-45%", "60%"],
        "15-Pd": ["40%", "50%", "-35%", "45%", "-40%", "55%", "-45%", "60%", "-50%", "65%"],
        "22-Pd": ["45%", "55%", "-40%", "50%", "-45%", "60%", "-50%", "65%", "-55%", "70%"],
        "30-Pd": ["50%", "60%", "-45%", "55%", "-50%", "65%", "-55%", "70%", "-60%", "75%"],
    }
    return pd.DataFrame(data)

def test_backtestSummary_positive():
    summary_df = backtestSummary(sample_summary_data())
    assert isinstance(summary_df, pd.DataFrame)
    assert len(summary_df) == 2
    assert summary_df.columns.tolist() == ['Stock', '1-Pd', '2-Pd', '3-Pd', '4-Pd', '5-Pd', '10-Pd', '15-Pd', '22-Pd', '30-Pd', 'Overall']
    assert summary_df["Stock"].tolist() == ["AAPL", "SUMMARY"]

def test_backtestSummary_no_data():
    summary_df = backtestSummary(None)
    assert summary_df is None

def test_formattedOutput():
    assert formattedOutput(85) == "\x1b[92m85.00%\x1b[0m"
    assert formattedOutput(70) == "\x1b[93m70.00%\x1b[0m"
    assert formattedOutput(40) == "\x1b[91m40.00%\x1b[0m"