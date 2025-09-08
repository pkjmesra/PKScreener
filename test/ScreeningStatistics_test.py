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
from unittest.mock import ANY, MagicMock, patch, PropertyMock, mock_open
import unittest

import numpy as np
import platform

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)
import pandas as pd
import pytest
from PKDevTools.classes.log import default_logger as dl
from PKDevTools.classes.ColorText import colorText
import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Utility as Utility
from pkscreener.classes.ScreeningStatistics import ScreeningStatistics
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
@pytest.fixture
def configManager():
    return ConfigManager.tools()


@pytest.fixture
def default_logger():
    return dl()


@pytest.fixture
def tools_instance(configManager, default_logger):
    return ScreeningStatistics(configManager, default_logger)


def test_positive_case_find52WeekHighBreakout(tools_instance):
    df = pd.DataFrame({
        "high": [50, 60, 70, 80, 90, 100]  # Assuming recent high is 100
    })
    assert tools_instance.find52WeekHighBreakout(df) == False

def test_negative_case_find52WeekHighBreakout(tools_instance):
    df = pd.DataFrame({
        "high": [50, 60, 70, 80, 90, 80]  # Assuming recent high is 80
    })
    assert tools_instance.find52WeekHighBreakout(df) == False

def test_empty_dataframe_find52WeekHighBreakout(tools_instance):
    df = pd.DataFrame()
    assert tools_instance.find52WeekHighBreakout(df) == False

def test_dataframe_with_nan_find52WeekHighBreakout(tools_instance):
    df = pd.DataFrame({
        "high": [50, 60, np.nan, 80, 90, 100]  # Assuming recent high is 100
    })
    assert tools_instance.find52WeekHighBreakout(df) == False

def test_dataframe_with_inf_find52WeekHighBreakout(tools_instance):
    df = pd.DataFrame({
        "high": [50, 60, np.inf, 80, 90, 100]  # Assuming recent high is 100
    })
    assert tools_instance.find52WeekHighBreakout(df) == False

def test_find52WeekHighBreakout_positive(tools_instance):
    data = pd.DataFrame({"high": [110, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == True


def test_find52WeekHighBreakout_negative(tools_instance):
    data = pd.DataFrame({"high": [50, 60, 80, 60, 60, 40, 100, 110, 120, 50, 170]})
    assert tools_instance.find52WeekHighBreakout(data) == False


def test_find52WeekHighBreakout_edge(tools_instance):
    data = pd.DataFrame(
        {
            "high": [
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ]
        }
    )
    assert tools_instance.find52WeekHighBreakout(data) == False


def test_find52WeekHighBreakout_nan_values(tools_instance):
    data = pd.DataFrame({"high": [50, 60, np.nan, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False


def test_find52WeekHighBreakout_inf_values(tools_instance):
    data = pd.DataFrame({"high": [50, 60, np.inf, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False


def test_find52WeekHighBreakout_negative_inf_values(tools_instance):
    data = pd.DataFrame({"high": [50, 60, -np.inf, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False


def test_find52WeekHighBreakout_last1WeekHigh_greater(tools_instance):
    data = pd.DataFrame({"high": [50, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False


def test_find52WeekHighBreakout_previousWeekHigh_greater(tools_instance):
    data = pd.DataFrame({"high": [50, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False


def test_find52WeekHighBreakout_full52WeekHigh_greater(tools_instance):
    data = pd.DataFrame({"high": [50, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False


# Positive test case for find52WeekLowBreakout function
def test_find52WeekLowBreakout_positive(tools_instance):
    data = pd.DataFrame({"low": [10, 20, 30, 40, 50]})
    result = tools_instance.find52WeekLowBreakout(data)
    assert result == True


# Negative test case for find52WeekLowBreakout function
def test_find52WeekLowBreakout_negative(tools_instance):
    data = pd.DataFrame({"low": [50, 40, 30, 20, 10]})
    result = tools_instance.find52WeekLowBreakout(data)
    assert result == False


# Edge test case for find52WeekLowBreakout function
def test_find52WeekLowBreakout_edge(tools_instance):
    data = pd.DataFrame(
        {
            "low": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ]
        }
    )
    result = tools_instance.find52WeekLowBreakout(data)
    assert result == True

def test_find52WeekHighLow_positive_case(tools_instance):
    df = pd.DataFrame({
        "high": [100, 60, 70, 80, 90, 100],  # Assuming recent high is 100
        "low": [5, 30, 20, 10, 5, 5]  # Assuming recent low is 40
    })
    saveDict = {}
    screenDict = {}
    tools_instance.find52WeekHighLow(df, saveDict, screenDict)
    assert saveDict["52Wk-H"] == "100.00"
    assert saveDict["52Wk-L"] == "5.00"
    assert screenDict["52Wk-H"] == f"{colorText.GREEN}100.00{colorText.END}"
    assert screenDict["52Wk-L"] == f"{colorText.FAIL}5.00{colorText.END}"

    df = pd.DataFrame({
        "high": [90, 60, 70, 80, 90, 100],  # Assuming recent high is 90
        "low": [110, 130, 120, 110, 115, 100]  # Assuming recent low is 110
    })
    saveDict = {}
    screenDict = {}
    tools_instance.find52WeekHighLow(df, saveDict, screenDict)
    assert saveDict["52Wk-H"] == "100.00"
    assert saveDict["52Wk-L"] == "100.00"
    assert screenDict["52Wk-H"] == f"{colorText.WARN}100.00{colorText.END}"
    assert screenDict["52Wk-L"] == f"{colorText.WARN}100.00{colorText.END}"

    df = pd.DataFrame({
        "high": [50, 60, 70, 80, 90, 100],  # Assuming recent high is 50
        "low": [40, 30, 20, 10, 5, 0]  # Assuming recent low is 40
    })
    saveDict = {}
    screenDict = {}
    tools_instance.find52WeekHighLow(df, saveDict, screenDict)
    assert saveDict["52Wk-H"] == "100.00"
    assert saveDict["52Wk-L"] == "0.00"
    assert screenDict["52Wk-H"] == f"{colorText.FAIL}100.00{colorText.END}"
    assert screenDict["52Wk-L"] == f"{colorText.GREEN}0.00{colorText.END}"

def test_find52WeekHighLow_negative_case(tools_instance):
    df = pd.DataFrame({
        "high": [50, 60, 70, 80, 90, 80],  # Assuming recent high is 80
        "low": [40, 30, 20, 10, 5, 10]  # Assuming recent low is 10
    })
    saveDict = {}
    screenDict = {}

    tools_instance.find52WeekHighLow(df, saveDict, screenDict)

    assert saveDict["52Wk-H"] == "90.00"
    assert saveDict["52Wk-L"] == "5.00"
    assert screenDict["52Wk-H"] == f"{colorText.FAIL}90.00{colorText.END}"
    assert screenDict["52Wk-L"] == f"{colorText.GREEN}5.00{colorText.END}"
    assert tools_instance.find52WeekHighLow(None,saveDict, screenDict) is False
    assert tools_instance.find52WeekHighLow(pd.DataFrame(),saveDict, screenDict) is False

def test_find52WeekLowBreakout_positive_case(tools_instance):
    df = pd.DataFrame({
        "low": [50, 60, 70, 80, 90, 0]  # Assuming recent low is 0
    })
    assert tools_instance.find52WeekLowBreakout(df) == False

def test_find52WeekLowBreakout_negative_case(tools_instance):
    df = pd.DataFrame({
        "low": [50, 60, 70, 80, 90, 10]  # Assuming recent low is 10
    })
    assert tools_instance.find52WeekLowBreakout(df) == False

# Positive test case for find10DaysLowBreakout function
def test_find10DaysLowBreakout_positive(tools_instance):
    data = pd.DataFrame({"low": [10, 20, 30, 40, 50]})
    result = tools_instance.find10DaysLowBreakout(data)
    assert result == True


# Negative test case for find10DaysLowBreakout function
def test_find10DaysLowBreakout_negative(tools_instance):
    data = pd.DataFrame({"low": [50, 40, 30, 20, 10]})
    result = tools_instance.find10DaysLowBreakout(data)
    assert result == False


# Edge test case for find10DaysLowBreakout function
def test_find10DaysLowBreakout_edge(tools_instance):
    data = pd.DataFrame(
        {
            "low": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ]
        }
    )
    result = tools_instance.find10DaysLowBreakout(data)
    assert result == True


# Positive test case for findAroonBullishCrossover function
def test_findAroonBullishCrossover_positive(tools_instance):
    data = pd.DataFrame({"high": [50, 60, 70, 80, 90], "low": [10, 20, 30, 40, 50]})
    result = tools_instance.findAroonBullishCrossover(data)
    assert result == False


# Negative test case for findAroonBullishCrossover function
def test_findAroonBullishCrossover_negative(tools_instance):
    data = pd.DataFrame({"high": [90, 80, 70, 60, 50], "low": [50, 40, 30, 20, 10]})
    result = tools_instance.findAroonBullishCrossover(data)
    assert result == False


# Edge test case for findAroonBullishCrossover function
def test_findAroonBullishCrossover_edge(tools_instance):
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "low": [
                50,
                40,
                30,
                20,
                10,
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
            ],
        }
    )
    result = tools_instance.findAroonBullishCrossover(data)
    assert result == False

def test_positive_case_findBreakingoutNow(tools_instance):
    df = pd.DataFrame({
        "open": [50, 60, 70, 80, 90, 100],
        "close": [55, 65, 75, 85, 95, 105]
    })
    assert tools_instance.findBreakingoutNow(df,df,{},{}) == False

    df = pd.DataFrame({
        "open": [100,100,100,100,100,100,100,100,100,100,100,100],
        "close": [130,110,110,110,110,110,110,110,110,110,110,110,]
    })
    assert tools_instance.findBreakingoutNow(df,df,{},{}) == True

def test_negative_case_findBreakingoutNow(tools_instance):
    df = pd.DataFrame({
        "open": [50, 60, 70, 80, 90, 80],
        "close": [55, 65, 75, 85, 95, 85]
    })
    assert tools_instance.findBreakingoutNow(df,df,{},{}) == False

def test_empty_dataframe_findBreakingoutNow(tools_instance):
    df = pd.DataFrame()
    assert tools_instance.findBreakingoutNow(df,df,{},{}) == False

def test_dataframe_with_nan_findBreakingoutNow(tools_instance):
    df = pd.DataFrame({
        "open": [50, 60, np.nan, 80, 90, 100],
        "close": [55, 65, np.nan, 85, 95, 105]
    })
    assert tools_instance.findBreakingoutNow(df,df,{},{}) == False

def test_dataframe_with_inf_findBreakingoutNow(tools_instance):
    df = pd.DataFrame({
        "open": [50, 60, np.inf, 80, 90, 100],
        "close": [55, 65, np.inf, 85, 95, 105]
    })
    assert tools_instance.findBreakingoutNow(df,df,{},{}) == False


# Positive test case for findBreakoutValue function
def test_findBreakoutValue_positive(tools_instance):
    data = pd.DataFrame({"high": [50, 60, 70, 80, 90], "close": [40, 50, 60, 70, 80]})
    screenDict = {}
    saveDict = {"Stock": "SBIN"}
    daysToLookback = 5
    result = tools_instance.findBreakoutValue(
        data, screenDict, saveDict, daysToLookback
    )
    assert result == True


# Negative test case for findBreakoutValue function
def test_findBreakoutValue_negative(tools_instance):
    data = pd.DataFrame(
        {
            "high": [90, 80, 70, 60, 50],
            "close": [80, 70, 60, 50, 40],
            "open": [80, 70, 60, 50, 40],
        }
    )
    screenDict = {}
    saveDict = {"Stock": "SBIN"}
    daysToLookback = 5
    result = tools_instance.findBreakoutValue(
        data, screenDict, saveDict, daysToLookback
    )
    assert result == False


# Edge test case for findBreakoutValue function
def test_findBreakoutValue_edge(tools_instance):
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    screenDict = {}
    saveDict = {"Stock": "SBIN"}
    daysToLookback = 5
    result = tools_instance.findBreakoutValue(
        data, screenDict, saveDict, daysToLookback
    )
    assert result == False

def test_positive_case_findNR4Day(tools_instance):
    df = pd.DataFrame({
        "volume": [60000, 70000, 80000, 90000, 100000],
        "close": [10, 9, 8, 7, 6],
        "high": [11, 10, 9, 8, 7],
        "low": [9, 8, 7, 6, 5],
        "SMA10": [8, 7, 6, 5, 4],
        "SMA50": [7, 6, 5, 4, 3],
        "SMA200": [6, 5, 4, 3, 2]
    })
    assert tools_instance.findNR4Day(df) == False

def test_negative_case_findNR4Day(tools_instance):
    df = pd.DataFrame({
        "volume": [40000, 50000, 60000, 70000, 80000],
        "close": [10, 9, 8, 7, 6],
        "high": [11, 10, 9, 8, 7],
        "low": [9, 8, 7, 6, 5],
        "SMA10": [8, 7, 6, 5, 4],
        "SMA50": [7, 6, 5, 4, 3],
        "SMA200": [6, 5, 4, 3, 2]
    })
    assert tools_instance.findNR4Day(df) == False

def test_empty_dataframe_findNR4Day(tools_instance):
    df = pd.DataFrame()
    assert tools_instance.findNR4Day(df) == False

def test_dataframe_with_nan_findNR4Day(tools_instance):
    df = pd.DataFrame({
        "volume": [60000, 70000, np.nan, 90000, 100000],
        "close": [10, 9, np.nan, 7, 6],
        "high": [11, 10, np.nan, 8, 7],
        "low": [9, 8, np.nan, 6, 5],
        "SMA10": [8, 7, np.nan, 5, 4],
        "SMA50": [7, 6, np.nan, 4, 3],
        "SMA200": [6, 5, np.nan, 3, 2]
    })
    assert tools_instance.findNR4Day(df) == False

def test_dataframe_with_inf_findNR4Day(tools_instance):
    df = pd.DataFrame({
        "volume": [60000, 70000, np.inf, 90000, 100000],
        "close": [10, 9, np.inf, 7, 6],
        "high": [11, 10, np.inf, 8, 7],
        "low": [9, 8, np.inf, 6, 5],
        "SMA10": [8, 7, np.inf, 5, 4],
        "SMA50": [7, 6, np.inf, 4, 3],
        "SMA200": [6, 5, np.inf, 3, 2]
    })
    assert tools_instance.findNR4Day(df) == False


# Positive test case for findBullishIntradayRSIMACD function
def test_findBullishIntradayRSIMACD_positive():
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    # Create an instance of the tools class
    tool = ScreeningStatistics(None, None)
    # Call the function and assert the result
    assert tool.findBullishIntradayRSIMACD(data) == False
    assert tool.findBullishIntradayRSIMACD(None) == False
    assert tool.findBullishIntradayRSIMACD(pd.DataFrame()) == False


# # Positive test case for findNR4Day function
def test_findNR4Day_positive():
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    # Create an instance of the tools class
    tool = ScreeningStatistics(None, None)
    # Call the function and assert the result
    assert tool.findNR4Day(data) == False


# Positive test case for findReversalMA function
def test_findReversalMA_positive(tools_instance):
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    # Call the function and assert the result
    assert tools_instance.findReversalMA(data, {}, {}, 3) == False


# Positive test case for findTrend function
def test_findTrend_positive(tools_instance):
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    # Call the function and assert the result
    assert tools_instance.findTrend(data, {}, {}, 10) == "Unknown"

def test_findTrend_valid_input(tools_instance):
    # Create a sample DataFrame for testing
    df = pd.DataFrame({"close": [10, 15, 20, 25, 30, 35, 40, 45, 50]})

    # Define the expected trend for the given DataFrame
    expected_trend = 'Unknown'

    # Call the findTrend function with the sample DataFrame and expected trend
    result = tools_instance.findTrend(df, {}, {}, daysToLookback=9, stockName='')

    # Assert that the returned trend matches the expected trend
    assert result == expected_trend

def test_findTrend_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame()

    # Call the findTrend function with the empty DataFrame
    result = tools_instance.findTrend(df, {}, {})

    # Assert that the returned trend is 'Unknown'
    assert result == 'Unknown'

def test_findTrend_insufficient_data(tools_instance):
    # Create a DataFrame with less than the required number of days
    df = pd.DataFrame({"close": [10, 15, 20]})

    # Call the findTrend function with the insufficient DataFrame
    result = tools_instance.findTrend(df, {}, {})

    # Assert that the returned trend is 'Unknown'
    assert result == 'Unknown'

def test_findTrend_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"close": ['a', 'b', 'c']})
    # Call the findTrend function with the invalid DataFrame
    tools_instance.findTrend(df, {}, {}) == 'Unknown'

def test_findTrend_tops_data(tools_instance):
    # Create a DataFrame with less than the required number of days
    df = pd.DataFrame({"close": [10, 15, 20]})
    with patch("numpy.rad2deg",return_value=0):
        assert tools_instance.findTrend(df, {}, {}) == 'Unknown'
    with patch("numpy.rad2deg",return_value=30):
        assert tools_instance.findTrend(df, {}, {}) == 'Sideways'
    with patch("numpy.rad2deg",return_value=-30):
        assert tools_instance.findTrend(df, {}, {}) == 'Sideways'
    with patch("numpy.rad2deg",return_value=10):
        assert tools_instance.findTrend(df, {}, {}) == 'Sideways'
    with patch("numpy.rad2deg",return_value=-20):
        assert tools_instance.findTrend(df, {}, {}) == 'Sideways'
    with patch("numpy.rad2deg",return_value=60):
        assert tools_instance.findTrend(df, {}, {}) == 'Weak Up'
    with patch("numpy.rad2deg",return_value=61):
        assert tools_instance.findTrend(df, {}, {}) == 'Strong Up'
    with patch("numpy.rad2deg",return_value=-40):
        assert tools_instance.findTrend(df, {}, {}) == 'Weak Down'
    with patch("numpy.rad2deg",return_value=-60):
        assert tools_instance.findTrend(df, {}, {}) == 'Weak Down'
    with patch("numpy.rad2deg",return_value=-61):
        assert tools_instance.findTrend(df, {}, {}) == 'Strong Down'
    with patch("pkscreener.classes.Pktalib.pktalib.argrelextrema",side_effect=[np.linalg.LinAlgError]):
        tools_instance.findTrend(df, {}, {}) == 'Unknown'
    with patch("pkscreener.classes.Pktalib.pktalib.argrelextrema",side_effect=[([0,1,2],)]):
        tools_instance.findTrend(df, {}, {}) == 'Unknown'

# Positive test case for findTrendlines function
def test_findTrendlines_positive(tools_instance):
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )

    # Call the function and assert the result
    assert tools_instance.findTrendlines(data, {}, {}) == True


# Positive test case for getCandleType function
def test_getCandleType_positive(tools_instance):
    # Mocking the dailyData
    dailyData = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    # Call the function and assert the result
    assert tools_instance.getCandleType(dailyData) == True


@pytest.mark.skipif(
    "Windows" in platform.system(),
    reason="Exception:UnicodeEncodeError: 'charmap' codec can't encode characters in position 18-37: character maps to <undefined>",
)
# PositiveNiftyPrediction function
def test_getNiftyPrediction_positive(tools_instance):
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    # Mocking the scaler
    scaler = MagicMock()
    pkl = {"columns": scaler}
    # Mocking the model
    model = MagicMock()
    model.predict.return_value = [0.6]
    # Mocking the Utility class
    Utility.tools.getNiftyModel.return_value = (model, pkl)
    # Call the function and assert the result
    assert tools_instance.getNiftyPrediction(data) is not None
    #         == (
    #     ANY,
    #     "Market may Open BULLISH next day! Stay Bullish!",
    #     "Probability/Strength of Prediction = 0.0%",
    # ) or tools_instance.getNiftyPrediction(data) == (
    #     ANY,
    #     "Market may Open BEARISH next day! Hold your Short position!",
    #     "Probability/Strength of Prediction = 100.0%",
    # ))


# # Positive test case for monitorFiveEma function
# def test_monitorFiveEma_positive():
#     # Mocking the fetcher
#     fetcher = MagicMock()
#     fetcher.fetchFiveEmaData.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())

#     # Mocking the result_df
#     result_df = MagicMock()

#     # Mocking the last_signal
#     last_signal = MagicMock()

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.monitorFiveEma(fetcher, result_df, last_signal) == result_df

# # Negative test case for monitorFiveEma function
# def test_monitorFiveEma_negative():
#     # Mocking the fetcher
#     fetcher = MagicMock()
#     fetcher.fetchFiveEmaData.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
#     # Mocking the result_df
#     result_df = MagicMock()
#     # Mocking the last_signal
#     last_signal = MagicMock()
#     # Create an instance of the tools class
#     tool = tools(None, None)
#     # Call the function and assert the result
#     assert tool.monitorFiveEma(fetcher, result_df, last_signal) != result_df


# Positive test case for preprocessData function
def test_preprocessData_positive(tools_instance):
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200.1,
                190.1,
                180.1,
                170.1,
                160.1,
                150.1,
                140.1,
                130.1,
                120.1,
                110.1,
                100.1,
                90.1,
                80.1,
                70.1,
                60.1,
                50.1,
                40.1,
                30.1,
                20.1,
                10.1,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "Other": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )

    # Call the function and assert the result
    assert tools_instance.preprocessData(data, 10) is not None


def test_preprocessData_valid_input(tools_instance):
    # Create a sample DataFrame for testing
    df = pd.DataFrame({"close": [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45, 50],
                       "volume": [100, 200, 300, 400, 500, 600, 700, 800, 900],
                       "high": [12.0, 18, 22, 28, 32, 38, 42, 48, 52],
                       "low": [8.0, 12, 16, 20, 24, 28, 32, 36, 40],
                       "open": [8.0, 12, 16, 20, 24, 28, 32, 36, 40]})
    df = pd.concat([df]*23, ignore_index=True)
    # Call the preprocessData function with the sample DataFrame
    fullData, trimmedData = tools_instance.preprocessData(df, daysToLookback=9)
    # Assert that the returned dataframes have the expected shape and columns
    assert fullData.shape == (207, 15)
    assert trimmedData.shape == (9, 15)
    assert list(fullData.columns) == ["close", "volume", "high", "low", "open", 'SMA', 'LMA', 'SSMA', 'SSMA20', 'Volatility','VolMA', 'RSI', 'CCI', 'FASTK', 'FASTD']

    tools_instance.configManager.useEMA = True
    # Call the preprocessData function with the sample DataFrame
    fullData, trimmedData = tools_instance.preprocessData(df, daysToLookback=9)
    # Assert that the returned dataframes have the expected shape and columns
    assert fullData.shape == (207, 15)
    assert trimmedData.shape == (9, 15)
    assert list(fullData.columns) == ["close", "volume", "high", "low", "open", 'SMA', 'LMA', 'SSMA', 'SSMA20', 'Volatility','VolMA', 'RSI', 'CCI', 'FASTK', 'FASTD']

def test_preprocessData_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame()

    # Call the preprocessData function with the empty DataFrame
    df1,df2 = tools_instance.preprocessData(df)
    assert df1.empty
    assert df2.empty

def test_preprocessData_insufficient_data(tools_instance):
    # Create a DataFrame with less than the required number of days
    df = pd.DataFrame({"close": [10, 15, 20]})

    # Call the preprocessData function with the insufficient DataFrame
    df1,df2 = tools_instance.preprocessData(df)
    assert not df1.empty
    assert not df2.empty

# Positive test case for validate15MinutePriceVolumeBreakout function
def test_validate15MinutePriceVolumeBreakout_positive(tools_instance):
    # Mocking the data
    data = pd.DataFrame(
        {
            "high": [
                10,
                20,
                30,
                40,
                50,
                60,
                70,
                80,
                90,
                100,
                110,
                120,
                130,
                140,
                150,
                160,
                170,
                180,
                190,
                200,
            ],
            "open": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "close": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "low": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
            "volume": [
                200,
                190,
                180,
                170,
                160,
                150,
                140,
                130,
                120,
                110,
                100,
                90,
                80,
                70,
                60,
                50,
                40,
                30,
                20,
                10,
            ],
        }
    )
    # Call the function and assert the result
    assert tools_instance.validate15MinutePriceVolumeBreakout(data) == True


def test_positive_case_findPotentialBreakout(tools_instance):
    df = pd.DataFrame({
        "volume": [100000, 90000, 80000, 70000, 60000],
        "close": [10, 9, 8, 7, 6],
        "high": [11, 10, 9, 8, 7]
    })
    screenDict = {}
    saveDict = {"Breakout": ""}
    daysToLookback = 30
    assert tools_instance.findPotentialBreakout(df, screenDict, saveDict, daysToLookback) == False
    assert saveDict["Breakout"] == ""

    daysToLookback = 30
    df = pd.DataFrame({
        "volume": [100000, 90000, 80000, 70000, 60000],
        "close": [120, 9, 8, 7, 6],
        "high": [110, 10, 9, 8, 7]
    })
    df_lastrow = pd.DataFrame({
        "volume": [80000],
        "close": [120],
        "high": [111]
    })
    df = pd.concat([df]*46, ignore_index=True)
    screenDict = {"Breakout":""}
    saveDict = {"Breakout": ""}
    assert tools_instance.findPotentialBreakout(df, screenDict, saveDict, daysToLookback) == False
    assert saveDict["Breakout"] == ""

    df = pd.concat([df, df_lastrow], axis=0)
    screenDict = {"Breakout":""}
    saveDict = {"Breakout": "125.0"}
    assert tools_instance.findPotentialBreakout(df, screenDict, saveDict, daysToLookback) == True
    assert saveDict["Breakout"] == "125.0(Potential)"
    assert screenDict["Breakout"] == colorText.GREEN + " (Potential)" + colorText.END

def test_negative_case_findPotentialBreakout(tools_instance):
    df = pd.DataFrame({
        "volume": [100000, 90000, 80000, 70000, 60000],
        "close": [6, 7, 8, 9, 10],
        "high": [7, 8, 9, 10, 11]
    })
    screenDict = {}
    saveDict = {"Breakout": ""}
    daysToLookback = 30
    assert tools_instance.findPotentialBreakout(df, screenDict, saveDict, daysToLookback) == False
    assert saveDict["Breakout"] == ""

def test_empty_dataframe_findPotentialBreakout(tools_instance):
    df = pd.DataFrame()
    screenDict = {}
    saveDict = {"Breakout": ""}
    daysToLookback = 30
    assert tools_instance.findPotentialBreakout(df, screenDict, saveDict, daysToLookback) == False
    assert saveDict["Breakout"] == ""

def test_dataframe_with_nan_findPotentialBreakout(tools_instance):
    df = pd.DataFrame({
        "volume": [100000, 90000, np.nan, 70000, 60000],
        "close": [10, 9, np.nan, 7, 6],
        "high": [11, 10, np.nan, 8, 7]
    })
    screenDict = {}
    saveDict = {"Breakout": ""}
    daysToLookback = 30
    assert tools_instance.findPotentialBreakout(df, screenDict, saveDict, daysToLookback) == False
    assert saveDict["Breakout"] == ""

def test_dataframe_with_inf_findPotentialBreakout(tools_instance):
    df = pd.DataFrame({
        "volume": [100000, 90000, np.inf, 70000, 60000],
        "close": [10, 9, np.inf, 7, 6],
        "high": [11, 10, np.inf, 8, 7]
    })
    screenDict = {}
    saveDict = {"Breakout": ""}
    daysToLookback = 30
    assert tools_instance.findPotentialBreakout(df, screenDict, saveDict, daysToLookback) == False
    assert saveDict["Breakout"] == ""

def test_positive_case_validateBullishForTomorrow(tools_instance):
    df = pd.DataFrame({
        "close": [10, 11, 12, 13, 14],
    })
    assert tools_instance.validateBullishForTomorrow(df) == False

def test_negative_case_validateBullishForTomorrow(tools_instance):
    df = pd.DataFrame({
        "close": [14, 13, 12, 11, 10],
    })
    assert tools_instance.validateBullishForTomorrow(df) == False

def test_empty_dataframe_validateBullishForTomorrow(tools_instance):
    df = pd.DataFrame()
    assert tools_instance.validateBullishForTomorrow(df) == False

def test_dataframe_with_nan_validateBullishForTomorrow(tools_instance):
    df = pd.DataFrame({
        "close": [10, 11, np.nan, 13, 14],
    })
    assert tools_instance.validateBullishForTomorrow(df) == False

def test_dataframe_with_inf_validateBullishForTomorrow(tools_instance):
    df = pd.DataFrame({
        "close": [10, 11, np.inf, 13, 14],
    })
    assert tools_instance.validateBullishForTomorrow(df) == False

def test_validateHigherHighsHigherLowsHigherClose_invalid_input(tools_instance):
    # Create a sample DataFrame for testing
    df = pd.DataFrame({"high": [10, 15, 20, 25,10, 15, 20, 25],
                       "low": [5, 10, 15, 20,5, 10, 15, 20],
                       "close": [12, 18, 22, 28,12, 18, 22, 28]})

    # Call the validateHigherHighsHigherLowsHigherClose function with the sample DataFrame
    assert tools_instance.validateHigherHighsHigherLowsHigherClose(df) == False

def test_validateHigherHighsHigherLowsHigherClose_valid_input(tools_instance):
    # Create a sample DataFrame with invalid data
    df = pd.DataFrame({"high": [25, 20, 15, 10,5, 15, 20, 25],
                       "low": [25, 20, 15, 10,5, 10, 15, 20],
                       "close": [25, 20, 15, 10,5, 18, 22, 28]})
    df = pd.concat([df]*20, ignore_index=True)
    # Call the validateHigherHighsHigherLowsHigherClose function with the invalid DataFrame
    assert tools_instance.validateHigherHighsHigherLowsHigherClose(df) == True


def test_validateHigherHighsHigherLowsHigherClose_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame(data=[1,2,3,4],columns=["A"])

    # Call the validateHigherHighsHigherLowsHigherClose function with the empty DataFrame
    with pytest.raises(KeyError):
        tools_instance.validateHigherHighsHigherLowsHigherClose(df)

def test_validateHigherHighsHigherLowsHigherClose_insufficient_data(tools_instance):
    # Create a DataFrame with less than the required number of days
    df = pd.DataFrame({"high": [10, 15],
                       "low": [5, 10],
                       "close": [12, 18]})

    # Call the validateHigherHighsHigherLowsHigherClose function with the insufficient DataFrame
    assert tools_instance.validateHigherHighsHigherLowsHigherClose(df) == False

def test_validateHigherHighsHigherLowsHigherClose_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"high": ['a', 'b', 'c','c'],
                       "low": ['d', 'e', 'f','f'],
                       "close": ['g', 'h', 'i','i']})

    # Call the validateHigherHighsHigherLowsHigherClose function with the invalid DataFrame
    with pytest.raises(Exception):
        tools_instance.validateHigherHighsHigherLowsHigherClose(df)


def test_validateInsideBar_valid_input(tools_instance):
    # Create a sample DataFrame for testing
    df = pd.DataFrame({"high": [10, 15, 20, 25, 50, 35, 40, 45, 50],
                       "low": [45, 40, 35, 30, 25, 30, 35, 40, 45],
                       "open": [12, 18, 22, 28, 32, 44, 42, 43, 44],
                       "close": [32, 38, 32, 28, 32, 38, 42, 48, 52]})
    saveDict = {"Trend":"Weak Up","MA-Signal":"50MA-Support"}
    # Define the expected pattern
    expected_pattern = 'Inside Bar (5)'

    # Call the validateInsideBar function with the sample DataFrame and expected pattern
    result = tools_instance.validateInsideBar(df, {}, saveDict, chartPattern=1, daysToLookback=5)

    # Assert that the returned pattern matches the expected pattern
    assert result == 5
    assert saveDict["Pattern"] == expected_pattern
    result = tools_instance.validateInsideBar(df, {}, saveDict, chartPattern=2, daysToLookback=5)
    assert result == 0
    saveDict = {"Trend":"Weak Up","MA-Signal":"50MA-Resist"}
    result = tools_instance.validateInsideBar(df, {}, saveDict, chartPattern=1, daysToLookback=5)
    assert result == 0
    saveDict = {"Trend":"Weak Down","MA-Signal":"50MA-Resist"}
    result = tools_instance.validateInsideBar(df, {}, saveDict, chartPattern=2, daysToLookback=5)

    # Assert that the returned pattern matches the expected pattern
    assert result == 5
    assert saveDict["Pattern"] == expected_pattern
    
    saveDict = {"Trend":"Weak Down","MA-Signal":"50MA-Support"}
    result = tools_instance.validateInsideBar(df, {}, saveDict, chartPattern=2, daysToLookback=5)
    assert result == 0
    assert tools_instance.validateInsideBar(df, {}, saveDict, chartPattern=2, daysToLookback=-1) == 0

def test_validateInsideBar_invalid_input(tools_instance):
    # Create a sample DataFrame with invalid data
    df = pd.DataFrame({"high": [10, 15, 20, 25, 30, 35, 40, 45, 50],
                       "low": [45, 40, 35, 30, 25, 30, 35, 40, 45],
                       "open": [12, 18, 22, 28, 32, 38, 42, 48, 52],
                       "close": [32, 38, 32, 28, 32, 38, 42, 48, 52]})
    saveDict = {"Trend":"Weak Up","MA-Signal":"50MA-Support"}
    # Call the validateInsideBar function with the invalid DataFrame
    result = tools_instance.validateInsideBar(df, {}, saveDict, chartPattern=1, daysToLookback=5)

    # Assert that the returned pattern is not the expected pattern
    assert result != 5

def test_validateInsideBar_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame(data=[1,2,3,4],columns=["A"])

    # Call the validateInsideBar function with the empty DataFrame
    with pytest.raises(KeyError):
        tools_instance.validateInsideBar(df, {}, {}, chartPattern=1, daysToLookback=5)

def test_validateInsideBar_insufficient_data(tools_instance):
    # Create a DataFrame with less than the required number of days
    df = pd.DataFrame({"high": [10, 15, 20],
                       "low": [5, 10, 15],
                       "open": [12, 18, 22],
                       "close": [12, 18, 22]})

    # Call the validateInsideBar function with the insufficient DataFrame
    with pytest.raises(KeyError):
        tools_instance.validateInsideBar(df, {}, {}, chartPattern=1, daysToLookback=5)

def test_validateInsideBar_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"high": ['a', 'b', 'c'],
                       "low": ['d', 'e', 'f'],
                       "open": ['g', 'h', 'i'],
                       "close": ['j', 'k', 'l']})

    # Call the validateInsideBar function with the invalid DataFrame
    with pytest.raises(Exception):
        tools_instance.validateInsideBar(df, {}, {}, chartPattern=1, daysToLookback=5)

def test_validateIpoBase_valid_input(tools_instance):
    # Create a sample DataFrame for testing
    df = pd.DataFrame({"open": [10, 15, 20, 12],
                       "close": [12, 18, 22, 28],
                       "high": [12, 15, 12, 15]})
    saveDict = {}
    # Call the validateIpoBase function with the sample DataFrame
    result = tools_instance.validateIpoBase('stock', df, {}, saveDict, percentage=0.3)
    # Assert that the function returns True
    assert result == True
    assert saveDict["Pattern"] == 'IPO Base (0.0 %)'
    df = pd.DataFrame({"open": [10, 15, 20, 12],
                       "close": [12.1, 18, 22, 28],
                       "high": [12, 15, 12, 15]})
    result = tools_instance.validateIpoBase('stock', df, {}, saveDict, percentage=0.3)
    # Assert that the function returns True
    assert result == True
    assert saveDict["Pattern"] == 'IPO Base (0.0 %), IPO Base (0.8 %)'

def test_validateIpoBase_invalid_input(tools_instance):
    # Create a sample DataFrame with invalid data
    df = pd.DataFrame({"open": [10, 15, 20, 25],
                       "close": [30, 35, 40, 45],
                       "high": [30, 35, 40, 45]})

    # Call the validateIpoBase function with the invalid DataFrame
    result = tools_instance.validateIpoBase('stock', df, {}, {}, percentage=0.3)

    # Assert that the function returns False
    assert result == False
    df = pd.DataFrame({"open": [13, 15, 20, 13],
                       "close": [8.1, 18, 22, 28],
                       "high": [12, 15, 12, 15]})
    assert tools_instance.validateIpoBase('stock', df, {}, {}, percentage=0.3) == False

def test_validateIpoBase_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame(data=[1,2,3,4],columns=["A"])

    # Call the validateIpoBase function with the empty DataFrame
    with pytest.raises(KeyError):
        tools_instance.validateIpoBase('stock', df, {}, {}, percentage=0.3)

def test_validateIpoBase_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"open": ['a', 'b', 'c'],
                       "close": ['d', 'e', 'f'],
                       "high": ['g', 'h', 'i']})

    # Call the validateIpoBase function with the invalid DataFrame
    with pytest.raises(Exception):
        tools_instance.validateIpoBase('stock', df, {}, {}, percentage=0.3)

def test_validateLorentzian_buy_signal(tools_instance):
    # Create a sample DataFrame with a buy signal
    df = pd.DataFrame({"open": [10, 15, 20, 25]*5,
                       "close": [12, 18, 22, 28]*5,
                       "high": [12, 18, 22, 28]*5,
                       "low": [8, 12, 16, 20]*5,
                       "volume": [100, 200, 300, 400]*5})

    # Call the validateLorentzian function with the sample DataFrame and lookFor=1 (Buy)
    screenDict = {}
    saveDict = {}
    mock_lc = MagicMock()
    with patch("advanced_ta.LorentzianClassification") as mock_lc:
        mock_lc.return_value = mock_lc
        mock_lc.df = pd.DataFrame([{"isNewSellSignal":False,"isNewBuySignal":True}])
        result = tools_instance.validateLorentzian(df, screenDict, saveDict, lookFor=1)
        # Assert that the function returns True and sets the appropriate screenDict and saveDict values
        assert result == True
        assert screenDict["Pattern"] == (colorText.GREEN + "Lorentzian-Buy" + colorText.END)
        assert saveDict["Pattern"] == "Lorentzian-Buy"
        assert tools_instance.validateLorentzian(df, screenDict, saveDict, lookFor=2) == False

def test_validateLorentzian_sell_signal(tools_instance):
    # Create a sample DataFrame with a sell signal
    df = pd.DataFrame({"open": [10, 15, 20, 25]*5,
                       "close": [12, 18, 22, 28]*5,
                       "high": [12, 18, 22, 28]*5,
                       "low": [8, 12, 16, 20]*5,
                       "volume": [100, 200, 300, 400]*5})

    # Call the validateLorentzian function with the sample DataFrame and lookFor=2 (Sell)
    screenDict = {}
    saveDict = {}
    mock_lc = MagicMock()
    with patch("advanced_ta.LorentzianClassification") as mock_lc:
        mock_lc.return_value = mock_lc
        mock_lc.df = pd.DataFrame([{"isNewSellSignal":True,"isNewBuySignal":False}])
        result = tools_instance.validateLorentzian(df, screenDict, saveDict, lookFor=2)
        # Assert that the function returns True and sets the appropriate screenDict and saveDict values
        assert result == True
        assert screenDict["Pattern"] == (colorText.FAIL + "Lorentzian-Sell" + colorText.END)
        assert saveDict["Pattern"] == "Lorentzian-Sell"
        assert tools_instance.validateLorentzian(df, screenDict, saveDict, lookFor=1) == False
        mock_lc.df = pd.DataFrame([{"isNewSellSignal":False,"isNewBuySignal":False}])
        assert tools_instance.validateLorentzian(df, screenDict, saveDict, lookFor=1) == False

def test_validateLorentzian_no_signal(tools_instance):
    # Create a sample DataFrame without any signals
    df = pd.DataFrame({"open": [10, 15, 20, 25]*5,
                       "close": [12, 18, 22, 28]*5,
                       "high": [12, 18, 22, 28]*5,
                       "low": [8, 12, 16, 20]*5,
                       "volume": [100, 200, 300, 400]*5})

    # Call the validateLorentzian function with the sample DataFrame and lookFor=3 (Any)
    screenDict = {}
    saveDict = {}
    result = tools_instance.validateLorentzian(df, screenDict, saveDict, lookFor=3)

    # Assert that the function returns False and does not modify screenDict and saveDict
    assert result == False
    assert screenDict == {}
    assert saveDict == {}

def test_validateLorentzian_exception(tools_instance):
    # Create a sample DataFrame that raises an exception
    df = pd.DataFrame({"open": ['a', 'b', 'c', 'd']*5,
                       "close": ['e', 'f', 'g', 'h']*5,
                       "high": ['i', 'j', 'k', 'l']*5,
                       "low": ['m', 'n', 'o', 'p']*5,
                       "volume": ['q', 'r', 's', 't']*5})

    # Call the validateLorentzian function with the invalid DataFrame
    screenDict = {}
    saveDict = {}
    result = tools_instance.validateLorentzian(df, screenDict, saveDict, lookFor=3)

    # Assert that the function returns False and does not modify screenDict and saveDict
    assert result == False
    assert screenDict == {}
    assert saveDict == {}

def test_validateLowerHighsLowerLows_valid_input(tools_instance):
    # Create a sample DataFrame with lower highs, lower lows, and higher RSI
    df = pd.DataFrame({"high": [7, 8, 9, 10]*5,
                       "low": [2, 3, 4, 5]*5,
                       'RSI': [50, 55, 60, 65]*5})

    # Call the validateLowerHighsLowerLows function with the sample DataFrame
    result = tools_instance.validateLowerHighsLowerLows(df)

    # Assert that the function returns True
    assert result == True

def test_validateLowerHighsLowerLows_invalid_input(tools_instance):
    # Create a sample DataFrame without lower highs or lower lows
    df = pd.DataFrame({"high": [10, 12, 8, 7],
                       "low": [5, 6, 3, 2],
                       'RSI': [60, 55, 50, 45]})

    # Call the validateLowerHighsLowerLows function with the sample DataFrame
    result = tools_instance.validateLowerHighsLowerLows(df)

    # Assert that the function returns False
    assert result == False

def test_validateLowerHighsLowerLows_no_higher_RSI(tools_instance):
    # Create a sample DataFrame without higher RSI
    df = pd.DataFrame({"high": [10, 9, 8, 7],
                       "low": [5, 4, 3, 2],
                       'RSI': [40, 35, 30, 25]})

    # Call the validateLowerHighsLowerLows function with the sample DataFrame
    result = tools_instance.validateLowerHighsLowerLows(df)

    # Assert that the function returns False
    assert result == False

def test_validateLowerHighsLowerLows_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame(data=[1,2,3,4],columns=["A"])

    # Call the validateLowerHighsLowerLows function with the empty DataFrame
    with pytest.raises(KeyError):
        tools_instance.validateLowerHighsLowerLows(df)

def test_validateLowerHighsLowerLows_insufficient_data(tools_instance):
    # Create a DataFrame with less than the required number of days
    df = pd.DataFrame({"high": [10, 9],
                       "low": [5, 4],
                       'RSI': [60, 55]})

    # Call the validateLowerHighsLowerLows function with the insufficient DataFrame
    assert tools_instance.validateLowerHighsLowerLows(df) == False

def test_validateLowerHighsLowerLows_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"high": ['a', 'b', 'c', 'd'],
                       "low": ['e', 'f', 'g', 'h'],
                       'RSI': ['i', 'j', 'k', 'l']})

    # Call the validateLowerHighsLowerLows function with the invalid DataFrame
    with pytest.raises(Exception):
        tools_instance.validateLowerHighsLowerLows(df)

def test_validateLowestVolume_valid_input(tools_instance):
    # Create a sample DataFrame with lowest volume
    df = pd.DataFrame({"volume": [70, 80, 90, 100, 110, 120, 130]})

    # Call the validateLowestVolume function with the sample DataFrame and daysForLowestVolume=7
    result = tools_instance.validateLowestVolume(df, daysForLowestVolume=7)

    # Assert that the function returns True
    assert result == True

def test_validateLowestVolume_invalid_input(tools_instance):
    # Create a sample DataFrame without lowest volume
    df = pd.DataFrame({"volume": [100, 200, 150, 120, 80, 90, 110]})

    # Call the validateLowestVolume function with the sample DataFrame and daysForLowestVolume=7
    result = tools_instance.validateLowestVolume(df, daysForLowestVolume=7)

    # Assert that the function returns False
    assert result == False

def test_validateLowestVolume_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame()

    # Call the validateLowestVolume function with the empty DataFrame
    assert tools_instance.validateLowestVolume(df, daysForLowestVolume=7) == False

def test_validateLowestVolume_insufficient_data(tools_instance):
    # Create a DataFrame with less than the required number of days
    df = pd.DataFrame({"volume": [100, 200]})

    # Call the validateLowestVolume function with the insufficient DataFrame
    assert tools_instance.validateLowestVolume(df, daysForLowestVolume=7) == False

def test_validateLowestVolume_nan_value(tools_instance):
    # Create a sample DataFrame with NaN value in Volume
    df = pd.DataFrame({"volume": [100, 200, np.nan, 120, 80, 90, 70]})

    # Call the validateLowestVolume function with the sample DataFrame and daysForLowestVolume=7
    result = tools_instance.validateLowestVolume(df, daysForLowestVolume=7)

    # Assert that the function returns False
    assert result == False

def test_validateLowestVolume_none_value(tools_instance):
    # Create a sample DataFrame with NaN value in Volume
    df = pd.DataFrame({"volume": [100, 200, np.nan, 120, 80, 90, 70]})

    # Call the validateLowestVolume function with the sample DataFrame and daysForLowestVolume=7
    result = tools_instance.validateLowestVolume(df, daysForLowestVolume=None)

    # Assert that the function returns False
    assert result == False

def test_validateLowestVolume_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"volume": ['a', 'b', 'c', 'd', 'e', 'f', 'g']})

    # Call the validateLowestVolume function with the invalid DataFrame
    with pytest.raises(Exception):
        tools_instance.validateLowestVolume(df, daysForLowestVolume=7)

def test_validateLTP_valid_input(tools_instance):
    # Create a sample DataFrame with a valid LTP
    df = pd.DataFrame({"close": [10, 15, 20, 25]})

    # Call the validateLTP function with the sample DataFrame and minLTP=10, maxLTP=25
    screenDict = {}
    saveDict = {}
    result, verifyStageTwo = tools_instance.validateLTP(df, screenDict, saveDict, minLTP=10, maxLTP=25)

    # Assert that the function returns True for ltpValid and True for verifyStageTwo
    assert result == True
    assert verifyStageTwo == True
    assert saveDict["LTP"] == 10
    assert screenDict["LTP"] == (colorText.GREEN + "10.00" + colorText.END)

def test_validateLTP_invalid_input(tools_instance):
    # Create a sample DataFrame with an invalid LTP
    df = pd.DataFrame({"close": [10, 15, 20, 25]})

    # Call the validateLTP function with the sample DataFrame and minLTP=30, maxLTP=40
    screenDict = {}
    saveDict = {}
    result, verifyStageTwo = tools_instance.validateLTP(df, screenDict, saveDict, minLTP=30, maxLTP=40)

    # Assert that the function returns False for ltpValid and True for verifyStageTwo
    assert result == False
    assert verifyStageTwo == True
    assert saveDict["LTP"] == 10
    assert screenDict["LTP"] == (colorText.FAIL + "10.00" + colorText.END)

def test_validateLTP_verifyStageTwo(tools_instance):
    # Create a sample DataFrame with more than 250 rows and an invalid LTP for verifyStageTwo
    df = pd.DataFrame({"close": [10, 15, 20, 25] * 100})

    # Call the validateLTP function with the sample DataFrame and minLTP=10, maxLTP=25
    screenDict = {}
    saveDict = {"Stock":"SomeStock"}
    result, verifyStageTwo = tools_instance.validateLTP(df, screenDict, saveDict, minLTP=10, maxLTP=25)

    # Assert that the function returns True for ltpValid and False for verifyStageTwo
    assert result == True
    assert verifyStageTwo == False
    assert saveDict["LTP"] == 10
    assert screenDict["LTP"] == (colorText.GREEN + "10.00" + colorText.END)
    assert screenDict["Stock"] == (colorText.FAIL + saveDict["Stock"] + colorText.END)

def test_validateLTP_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame()

    # Call the validateLTP function with the empty DataFrame
    with pytest.raises(KeyError):
        tools_instance.validateLTP(df, {}, {}, minLTP=10, maxLTP=25)

def test_validateLTP_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"close": ['a', 'b', 'c', 'd']})

    # Call the validateLTP function with the invalid DataFrame
    with pytest.raises(Exception):
        tools_instance.validateLTP(df, {}, {}, minLTP=10, maxLTP=25)

def test_findUptrend_valid_input_downtrend(tools_instance):
    # Create a sample DataFrame with an uptrend
    df = pd.DataFrame({"close": [10, 15, 20, 25, 30, 35, 40, 45, 50]*50})
    screenDict = {"Trend":""}
    saveDict = {"Trend":""}
    result = tools_instance.findUptrend(df, screenDict, saveDict, testing=False,stock="SBIN")
    assert result == (False,ANY,0)
    assert f"T:{colorText.DOWNARROW}" in saveDict["Trend"]
    assert f"T:{colorText.DOWNARROW}" in screenDict["Trend"]

def test_findUptrend_uptrend(tools_instance):
    # Create a sample DataFrame with a downtrend
    df = pd.DataFrame({"close": [50, 45, 40, 35, 30, 25, 20, 15, 10]*50})

    # Call the findUptrend function with the sample DataFrame
    screenDict = {"Trend":""}
    saveDict = {"Trend":""}
    result = tools_instance.findUptrend(df, screenDict, saveDict, testing=False,stock="SBIN")

    # Assert that the function returns False and sets the appropriate screenDict and saveDict values
    assert result == (True,ANY,0)
    assert f"T:{colorText.UPARROW}" in saveDict["Trend"]
    assert f"T:{colorText.UPARROW}" in screenDict["Trend"]

def test_findUptrend_empty_input(tools_instance):
    # Create an empty DataFrame for testing
    df = pd.DataFrame()
    # Call the findUptrend function with the empty DataFrame
    result = tools_instance.findUptrend(df, {"Trend":""}, {"Trend":""}, testing=False,stock="SBIN")
    # Assert that the function returns False
    assert result == (False,ANY,0)

def test_findUptrend_insufficient_data(tools_instance):
    # Create a DataFrame with less than 300 rows
    df = pd.DataFrame({"close": [10, 15, 20, 25]})

    # Call the findUptrend function with the insufficient DataFrame
    result = tools_instance.findUptrend(df, {"Trend":""}, {"Trend":""}, testing=False,stock="SBIN")

    # Assert that the function returns False
    assert result == (False,ANY,0)

def test_findUptrend_testing_mode(tools_instance):
    # Create a sample DataFrame
    df = pd.DataFrame({"close": [10, 15, 20, 25, 30, 35, 40, 45, 50]})

    # Call the findUptrend function with testing=True
    result = tools_instance.findUptrend(df, {"Trend":""}, {"Trend":""}, testing=True,stock="SBIN")

    # Assert that the function returns False
    assert result == (False,ANY,0)

def test_findUptrend_exception(tools_instance):
    # Create a DataFrame with invalid data that will raise an exception
    df = pd.DataFrame({"close": ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']})

    # Call the findUptrend function with the invalid DataFrame
    assert tools_instance.findUptrend(df, {"Trend":""}, {"Trend":""}, testing=False,stock="SBIN") == (False,ANY,0)

# # Positive test case for validateBullishForTomorrow function
# def test_validateBullishForTomorrow_positive(tools_instance):
#     # Mocking the data
#     data = pd.DataFrame({"high": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200],
#                          "open": [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
#                          "close": [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
#                          "low": [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
#                          "volume": [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10],})

#     # Call the function and assert the result
#     assert tools_instance.validateBullishForTomorrow(data) == True

def test_validateCCI():
    tool = ScreeningStatistics(None, None)
    # Test case 1: CCI within specified range and trend is Up
    df = pd.DataFrame({'CCI': [50]})
    screenDict = {}
    saveDict = {}
    minCCI = 40
    maxCCI = 60
    assert tool.validateCCI(df, screenDict, saveDict, minCCI, maxCCI) == False
    assert screenDict['CCI'] == colorText.FAIL + '50' + colorText.END

    # Test case 2: CCI below minCCI and trend is Up
    df = pd.DataFrame({'CCI': [30]})
    screenDict = {}
    saveDict = {"Trend":"Weak Up"}
    minCCI = 20
    maxCCI = 60
    assert tool.validateCCI(df, screenDict, saveDict, minCCI, maxCCI) == True
    assert screenDict['CCI'] == colorText.GREEN + '30' + colorText.END

    # Test case 3: CCI above maxCCI and trend is Up
    df = pd.DataFrame({'CCI': [70]})
    screenDict = {}
    saveDict = {"Trend":"Weak Up"}
    minCCI = 20
    maxCCI = 60
    assert tool.validateCCI(df, screenDict, saveDict, minCCI, maxCCI) == False
    assert screenDict['CCI'] == colorText.FAIL + '70' + colorText.END

    # Test case 4: CCI within specified range and trend is not Up
    df = pd.DataFrame({'CCI': [50]})
    screenDict = {}
    saveDict = {}
    minCCI = 40
    maxCCI = 60
    saveDict['Trend'] = 'Down'
    assert tool.validateCCI(df, screenDict, saveDict, minCCI, maxCCI) == True
    assert screenDict['CCI'] == colorText.FAIL + '50' + colorText.END

    df = pd.DataFrame({'CCI': [70]})
    screenDict = {}
    saveDict = {"Trend":"Weak Down"}
    minCCI = 40
    maxCCI = 60
    assert tool.validateCCI(df, screenDict, saveDict, minCCI, maxCCI) == False
    assert screenDict['CCI'] == colorText.FAIL + '70' + colorText.END

def test_validateConfluence():
    tool = ScreeningStatistics(None, None)
    # Test case 1: SMA and LMA are within specified percentage and SMA is greater than LMA
    df = pd.DataFrame({'SMA': [50], 'LMA': [45], "close": [100]})
    screenDict = {}
    saveDict = {}
    percentage = 0.1
    assert tool.validateConfluence(None, df, screenDict, saveDict, percentage) == False

    # Test case 2: SMA and LMA are within specified percentage and SMA is less than LMA
    df = pd.DataFrame({'SMA': [50], 'LMA': [45], "close": [100]})
    screenDict = {}
    saveDict = {}
    percentage = 0.1
    assert tool.validateConfluence(None, df, screenDict, saveDict, percentage) == False
    # assert screenDict['MA-Signal'] == colorText.GREEN + 'Confluence (5.0%)' + colorText.END

    # Test case 3: SMA and LMA are not within specified percentage
    df = pd.DataFrame({'SMA': [50], 'LMA': [60], "close": [100]})
    screenDict = {}
    saveDict = {}
    percentage = 0.1
    assert tool.validateConfluence(None, df, screenDict, saveDict, percentage) == False

    # Test case 4: SMA and LMA are equal
    df = pd.DataFrame({'SMA': [50], 'LMA': [50], "close": [100]})
    screenDict = {}
    saveDict = {}
    percentage = 0.1
    assert tool.validateConfluence(None, df, screenDict, saveDict, percentage) == False
    # assert screenDict['MA-Signal'] == colorText.GREEN + 'Confluence (0.0%)' + colorText.END

    df = pd.DataFrame({'SMA': [45], 'LMA': [49], "close": [100]})
    screenDict = {}
    saveDict = {}
    percentage = 0.1
    assert tool.validateConfluence(None, df, screenDict, saveDict, percentage) == False
    # assert screenDict['MA-Signal'] == colorText.FAIL + 'Confluence (4.0%)' + colorText.END

def test_validateConsolidation():
    tool = ScreeningStatistics(None, None)
    # Test case 1: High and low close prices within specified percentage
    df = pd.DataFrame({"close": [100, 95]})
    screenDict = {}
    saveDict = {}
    percentage = 10
    assert tool.validateConsolidation(df, screenDict, saveDict, percentage) == 5.0
    assert screenDict['Consol.'] == colorText.GREEN + 'Range:5.0%' + colorText.END

    # Test case 2: High and low close prices not within specified percentage
    df = pd.DataFrame({"close": [100, 80]})
    screenDict = {}
    saveDict = {}
    percentage = 10
    assert tool.validateConsolidation(df, screenDict, saveDict, percentage) == 20.0
    assert screenDict['Consol.'] == colorText.FAIL + 'Range:20.0%' + colorText.END

    # Test case 3: High and low close prices are equal
    df = pd.DataFrame({"close": [100, 100]})
    screenDict = {}
    saveDict = {}
    percentage = 10
    assert tool.validateConsolidation(df, screenDict, saveDict, percentage) == 0.0
    assert screenDict['Consol.'] == colorText.FAIL + 'Range:0.0%' + colorText.END

# # Positive test case for validateInsideBar function
# def test_validateInsideBar_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.tail().iloc[0].return_value = 100
#     data.tail().iloc[1].return_value = 90
#     data.tail().iloc[2].return_value = 80
#     data.tail().iloc[3].return_value = 70
#     data.tail().iloc[4].return_value = 60
#     data.tail().iloc[5].return_value = 50
#     data.tail().iloc[6].return_value = 40
#     data.tail().iloc[7].return_value = 30
#     data.tail().iloc[8].return_value = 20
#     data.tail().iloc[9].return_value = 10

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateInsideBar(data, {}, {}, 1, 10) == 1

# # Negative test case for validateInsideBar function
# def test_validateInsideBar_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.tail().iloc[0].return_value = 100
#     data.tail().iloc[1].return_value = 90
#     data.tail().iloc[2].return_value = 80
#     data.tail().iloc[3].return_value = 70
#     data.tail().iloc[4].return_value = 60
#     data.tail().iloc[5].return_value = 50
#     data.tail().iloc[6].return_value = 40
#     data.tail().iloc[7].return_value = 30
#     data.tail().iloc[8].return_value = 20
#     data.tail().iloc[9].return_value = 5

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateInsideBar(data, {}, {}, 1, 10) == 0

# # Positive test case for validateIpoBase function
# def test_validateIpoBase_positive():
#     # Mocking the data
#     data = MagicMock()
#     data[::-1].head.return_value =()
#     data[::-1].min()["close"].return_value = 100
#     data[::-1].max()["close"].return_value = 200
#     data.head().iloc[0].return_value = 150

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateIpoBase(None, data, {}, {}, 0.3) == True

# # Negative test case for validateIpoBase function
# def test_validateIpoBase_negative():
#     # Mocking the data
#     data = MagicMock()
#     data[::-1].head.return_value = MagicMock()
#     data[::-1].min()["close"].return_value = 100
#     data[::-1].max()["close"].return_value = 200
#     data.head().iloc[0].return_value = 250

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateIpoBase(None, data, {}, {}, 0.3) == False

# # Positive test case for validateLowestVolume function
# def test_validateLowestVolume_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.describe()["volume"]["min"].return_value = 100
#     data.head().iloc[0].return_value = 100

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateLowestVolume(data, 10) == True

# # Negative test case for validateLowestVolume function
# def test_validateLowestVolume_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.describe()["volume"]["min"].return_value = 100
#     data.head().iloc[0].return_value = 200

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateLowestVolume(data, 10) == False


# Positive test case for validateLTP function
def test_validateLTP_positive(tools_instance):
    data = pd.DataFrame({"close": [100, 110, 120]})
    screenDict = {}
    saveDict = {}
    result, verifyStageTwo = tools_instance.validateLTP(
        data, screenDict, saveDict, minLTP=100, maxLTP=120
    )
    assert result == True
    assert verifyStageTwo == True
    assert screenDict["LTP"] == "\x1b[32m100.00\x1b[0m"
    assert saveDict["LTP"] == 100


# Negative test case for validateLTP function
def test_validateLTP_negative(tools_instance):
    data = pd.DataFrame({"close": [90, 95, 100]})
    screenDict = {}
    saveDict = {}
    result, verifyStageTwo = tools_instance.validateLTP(
        data, screenDict, saveDict, minLTP=100, maxLTP=120
    )
    assert result == False
    assert verifyStageTwo == True
    assert screenDict["LTP"] == "\x1b[31m90.00\x1b[0m"
    assert saveDict["LTP"] == 90


# Positive test case for validateMACDHistogramBelow0 function
def test_validateMACDHistogramBelow0_positive(tools_instance):
    data = pd.DataFrame({"close": [100, 110, 120]})
    result = tools_instance.validateMACDHistogramBelow0(data)
    assert result == False


# # Negative test case for validateMACDHistogramBelow0 function
# def test_validateMACDHistogramBelow0_negative(tools_instance):
#     data = pd.DataFrame({"close": [100, 90, 80]})
#     result = tools.validateMACDHistogramBelow0(data)
#     assert result == True

# # Positive test case for validateMomentum function
# def test_validateMomentum_positive(tools_instance):
#     data = pd.DataFrame({"close": [100, 110, 120], "open": [90, 100, 110]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateMomentum(data, screenDict, saveDict)
#     assert result == True
#     assert screenDict['Pattern'] == '\x1b[1m\x1b[92mMomentum Gainer\x1b[0m'
#     assert saveDict['Pattern'] == 'Momentum Gainer'


# Negative test case for validateMomentum function
def test_validateMomentum_negative(tools_instance):
    data = pd.DataFrame({"close": [100, 90, 80], "open": [110, 100, 90]})
    screenDict = {}
    saveDict = {}
    result = tools_instance.validateMomentum(data, screenDict, saveDict)
    assert result == False


# # Positive test case for validateMovingAverages function
# def test_validateMovingAverages_positive(tools_instance):
#     data = pd.DataFrame({"close": [100, 110, 120], 'SMA': [90, 100, 110], 'LMA': [80, 90, 100]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateMovingAverages(data, screenDict, saveDict)
#     assert result == 1
#     assert screenDict['MA-Signal'] == '\x1b[1m\x1b[92mBullish\x1b[0m'

# # Negative test case for validateMovingAverages function
# def test_validateMovingAverages_negative(tools_instance):
#     data = pd.DataFrame({"close": [100, 90, 80], 'SMA': [110, 100, 90], 'LMA': [120, 110, 100]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateMovingAverages(data, screenDict, saveDict)
#     assert result == -1
#     assert screenDict['MA-Signal'] == '\x1b[1m\x1b[91mBearish\x1b[0m'
#     assert saveDict['MA-Signal'] == 'Bearish'

# # Positive test case for validateNarrowRange function
# def test_validateNarrowRange_positive(tools_instance):
#     data = pd.DataFrame({"close": [100, 110, 120, 130]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateNarrowRange(data, screenDict, saveDict, nr=3)
#     assert result == True
#     assert screenDict['Pattern'] == '\x1b[1m\x1b[92mBuy-NR3\x1b[0m'
#     assert saveDict['Pattern'] == 'Buy-NR3'

# # Negative test case for validateNarrowRange function
# def test_validateNarrowRange_negative(tools_instance):
#     data = pd.DataFrame({"close": [100, 110, 120, 130]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateNarrowRange(data, screenDict, saveDict, nr=2)
#     assert result == False


# Positiveed function
def test_validateNewlyListed_positive(tools_instance):
    data = pd.DataFrame({"close": [100, 110, 120]})
    result = tools_instance.validateNewlyListed(data, daysToLookback="2d")
    assert result == False


# Negative test case for validateNewlyListed function
def test_validateNewlyListed_negative(tools_instance):
    data = pd.DataFrame({"close": [100]})
    result = tools_instance.validateNewlyListed(data, daysToLookback="2d")
    assert result == True


@pytest.fixture
def mock_data():
    return pd.DataFrame(
        {
            "close": [100, 105, 110, 115],
            "RSI": [60, 65, 70, 75],
            "FASTK": [30, 40, 50, 60],
            "open": [95, 100, 105, 110],
            "high": [105, 110, 115, 120],
            "low": [95, 100, 105, 110],
            "volume": [1000, 2000, 3000, 4000],
            "VolMA": [1500, 2000, 2500, 3000],
        }
    )


@pytest.fixture
def mock_screen_dict():
    return {}


@pytest.fixture
def mock_save_dict():
    return {}

def test_validatePriceRisingByAtLeast2Percent_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data["close"] = [115, 110, 105, 100]
    assert tools_instance.validatePriceRisingByAtLeast2Percent(mock_data, mock_screen_dict, mock_save_dict) == True
    assert mock_screen_dict["%Chng"] == '\x1b[32m4.5% (4.8%, 5.0%)\x1b[0m'
    assert mock_save_dict["%Chng"] == '4.5% (4.8%, 5.0%)'



def test_validatePriceRisingByAtLeast2Percent_negative(
    mock_data, mock_screen_dict, mock_save_dict, tools_instance
):
    mock_data["close"] = [100, 105, 110, 112]
    assert (
        tools_instance.validatePriceRisingByAtLeast2Percent(
            mock_data, mock_screen_dict, mock_save_dict
        )
        == False
    )
    assert mock_screen_dict.get("LTP") is None
    assert mock_save_dict.get("LTP") is None


def test_validateRSI_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    assert tools_instance.validateRSI(mock_data, mock_screen_dict, mock_save_dict, 60, 80) == True
    assert mock_screen_dict["RSI"] == '\x1b[32m60\x1b[0m' 
    assert mock_save_dict["RSI"] == 60

def test_validateRSI_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    assert tools_instance.validateRSI(mock_data, mock_screen_dict, mock_save_dict, 80, 90) == False
    assert mock_screen_dict["RSI"] == '\x1b[31m60\x1b[0m' 
    assert mock_save_dict["RSI"] == 60

# def test_validateShortTermBullish_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validateShortTermBullish(mock_data, mock_screen_dict, mock_save_dict) == True
#     assert mock_screen_dict["MA-Signal"] == "\033[32mBullish\033[0m"
#     assert mock_save_dict["MA-Signal"] == "Bullish"


def test_validateShortTermBullish_negative(
    mock_data, mock_screen_dict, mock_save_dict, tools_instance
):
    mock_data["FASTK"] = [70, 60, 50, 40]
    assert (
        tools_instance.validateShortTermBullish(
            mock_data, mock_screen_dict, mock_save_dict
        )
        == False
    )
    assert mock_screen_dict.get("MA-Signal") is None
    assert mock_save_dict.get("MA-Signal") is None

def test_validateMomentum(tools_instance):
    # Mock the required functions and classes
    patch('pandas.DataFrame.copy')
    patch('pandas.DataFrame.head')
    patch('pandas.DataFrame.iterrows')
    patch('pandas.DataFrame.sort_values')
    patch('pandas.DataFrame.equals')
    patch('pandas.DataFrame.iloc')
    patch('pandas.concat')
    patch('pandas.DataFrame.rename')
    patch('pandas.DataFrame.debug')

    # Create a test case
    df = pd.DataFrame({"open": [1.1, 2, 3], "high": [4.1, 5, 6], "low": [7.1, 8, 9], "close": [10.1, 11, 12], "volume": [13, 14, 15]})
    df = pd.concat([df]*150, ignore_index=True)
    screenDict = {}
    saveDict = {}

    # Call the function under test
    result = tools_instance.validateMomentum(df, screenDict, saveDict)

    # Assert the expected behavior
    assert result == False
    # assert screenDict['Pattern'] == '\033[32mMomentum Gainer\033[0m'
    # assert saveDict['Pattern'] == 'Momentum Gainer'

def test_validateLTPForPortfolioCalc(tools_instance):
    # Mock the required functions and classes
    patch('pandas.DataFrame.copy')
    patch('pandas.DataFrame.head')
    patch('pandas.DataFrame.reset_index')
    patch('pandas.DataFrame.iloc')
    patch('pandas.concat')
    patch('pandas.DataFrame.rename')
    patch('pandas.DataFrame.debug')

    # Create a test case
    df = pd.DataFrame({"open": [1, 2, 3], "high": [4, 5, 6], "low": [7, 8, 9], "close": [10, 11, 12], "volume": [13, 14, 15]})
    df = pd.concat([df]*150, ignore_index=True)
    screenDict = {}
    saveDict = {}

    # Call the function under test
    result = tools_instance.validateLTPForPortfolioCalc(df, screenDict, saveDict)

    # Assert the expected behavior
    assert result == None
    assert screenDict['LTP1'] == '\033[32m11.00\033[0m'
    assert saveDict['LTP1'] == 11.0

def test_validateNarrowRange(tools_instance):
    # Mock the required functions and classes
    patch('pandas.DataFrame.copy')
    patch('PKDevTools.PKDateUtilities.PKDateUtilities.isTradingTime')
    patch('pandas.DataFrame.head')
    patch('pandas.DataFrame.describe')
    patch('pandas.DataFrame.iloc')
    patch('pandas.concat')
    patch('pandas.DataFrame.rename')
    patch('pandas.DataFrame.debug')

    # Create a test case
    isTrading = PKDateUtilities.isTradingTime()
    closeValue = 10.1 if isTrading else 11
    df = pd.DataFrame({"open": [1.1, 2, 3], "high": [4.1, 5, 6], "low": [7.1, 8, 9], "close": [10.1, closeValue , 12], "volume": [13, 14, 15]})
    df = pd.concat([df]*150, ignore_index=True)
    screenDict = {}
    saveDict = {}

    # Call the function under test
    result = tools_instance.validateNarrowRange(df, screenDict, saveDict)

    # Assert the expected behavior
    assert result == True
    assert screenDict['Pattern'] == '\033[32mNR4\033[0m' if not isTrading else "\033[32mBuy-NR4\033[0m"
    assert saveDict['Pattern'] == 'NR4' if not isTrading else "Buy-NR4"

# def test_validateVCP_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     # mock_data["high"] = [205, 210, 215, 220]
#     assert tools_instance.validateVCP(mock_data, mock_screen_dict, mock_save_dict, "Stock A", 3, 3) == False
#     assert mock_screen_dict["Pattern"] == "\033[32mVCP (BO: 115.0)\033[0m"
#     assert mock_save_dict["Pattern"] == "VCP (BO: 115.0)"


def test_validateVCP_negative(
    mock_data, mock_screen_dict, mock_save_dict, tools_instance
):
    mock_data["high"] = [105, 110, 115, 120]
    assert (
        tools_instance.validateVCP(
            mock_data, mock_screen_dict, mock_save_dict, "Stock A", 3, 3
        )
        == False
    )
    assert mock_screen_dict.get("Pattern") is None
    assert mock_save_dict.get("Pattern") is None


def test_validateVolume_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    assert tools_instance.validateVolume(mock_data, mock_screen_dict, mock_save_dict, 2.5) == (False,True)
    assert mock_screen_dict["volume"] == 0.67
    assert mock_save_dict["volume"] == 0.67
    mock_data.loc[0, "VolMA"] = 1000
    mock_data.loc[0, "volume"] = 2500
    assert tools_instance.validateVolume(mock_data, mock_screen_dict, mock_save_dict, 2.5,1000) == (True, True)
    assert mock_screen_dict["volume"] == 2.5
    assert mock_save_dict["volume"] == 2.5

def test_validateVolume_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data["volume"] = [1000, 2000, 3000, 3500]
    assert tools_instance.validateVolume(mock_data, mock_screen_dict, mock_save_dict, 2.5) == (False, True)
    assert mock_screen_dict["volume"] == 0.67
    assert mock_save_dict["volume"] == 0.67
    mock_data.loc[0, "VolMA"] = 0
    assert tools_instance.validateVolume(mock_data, mock_screen_dict, mock_save_dict, 2.5,10000) == (False, False)

def test_SpreadAnalysis_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data["open"] = [140, 135, 150, 155]
    assert tools_instance.validateVolumeSpreadAnalysis(mock_data, mock_screen_dict, mock_save_dict) == True
    assert mock_screen_dict["Pattern"] == "\033[32mSupply Drought\033[0m"
    assert mock_save_dict["Pattern"] == "Supply Drought"

def test_validateVolumeSpreadAnalysis_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data["open"] = [100, 105, 110,120]
    assert tools_instance.validateVolumeSpreadAnalysis(mock_data, mock_screen_dict, mock_save_dict) == False
    assert mock_screen_dict.get("Pattern") == None
    assert mock_save_dict.get("Pattern") == None

def test_validateVolumeSpreadAnalysis_datalength_lessthan2(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    assert tools_instance.validateVolumeSpreadAnalysis(mock_data.head(1), mock_screen_dict, mock_save_dict) == False
    assert mock_screen_dict.get("Pattern") == None
    assert mock_save_dict.get("Pattern") == None

def test_validateVolumeSpreadAnalysis_open_less_than_close(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data.loc[1, "open"] = 100
    mock_data.loc[1, "close"] = 110
    assert tools_instance.validateVolumeSpreadAnalysis(mock_data, mock_screen_dict, mock_save_dict) == False
    assert mock_screen_dict.get("Pattern") == None
    assert mock_save_dict.get("Pattern") == None

def test_validateVolumeSpreadAnalysis_spread0_lessthan_spread1(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data.loc[1, "open"] = 120
    mock_data.loc[1, "close"] = 100
    mock_data.loc[0, "open"] = 110
    mock_data.loc[0, "close"] = 100
    mock_data.loc[0, "volume"] = mock_data.iloc[0]["VolMA"] + 1000
    mock_data.loc[1, "volume"] = mock_data["volume"].iloc[0] -1000
    assert tools_instance.validateVolumeSpreadAnalysis(mock_data, mock_screen_dict, mock_save_dict) == True
    assert mock_screen_dict.get("Pattern") == colorText.GREEN + "Demand Rise" + colorText.END 
    assert mock_save_dict.get("Pattern") == 'Demand Rise'


class TestScreeningStatistics_calc_relative_strength(unittest.TestCase):

    def setUp(self):
        """Initialize the ScreeningStatistics instance."""
        self.stats = ScreeningStatistics(ConfigManager.tools(),None)

    def test_calc_relative_strength_none_dataframe(self):
        """Test when the input DataFrame is None."""
        result = self.stats.calc_relative_strength(None)
        self.assertEqual(result, -1)

    def test_calc_relative_strength_empty_dataframe(self):
        """Test when the input DataFrame is empty."""
        df = pd.DataFrame()
        result = self.stats.calc_relative_strength(df)
        self.assertEqual(result, -1)

    def test_calc_relative_strength_insufficient_data(self):
        """Test when the input DataFrame has only one row."""
        df = pd.DataFrame({"Adj Close": [100]})
        result = self.stats.calc_relative_strength(df)
        self.assertEqual(result, -1)

    def test_calc_relative_strength_fallback_to_close(self):
        """Test when 'Adj Close' is missing and function falls back to "close"."""
        df = pd.DataFrame({"close": [100, 105, 102, 107, 110]})
        result = self.stats.calc_relative_strength(df)
        self.assertGreater(result, 0)  # Ensure RS is calculated

    def test_calc_relative_strength_calculation(self):
        """Test correct RS calculation."""
        df = pd.DataFrame({"Adj Close": [100, 102, 101, 104, 107]})
        result = self.stats.calc_relative_strength(df)
        self.assertGreater(result, 0)  # RS should be > 0 since there are more gains

    def test_calc_relative_strength_all_gains(self):
        """Test when all price movements are gains (RS should be high)."""
        df = pd.DataFrame({"Adj Close": [100, 105, 110, 115, 120]})
        result = self.stats.calc_relative_strength(df)
        self.assertGreater(result, 1)  # RS should be > 1 since there are no losses

    def test_calc_relative_strength_all_losses(self):
        """Test when all price movements are losses (RS should be 0 or very low)."""
        df = pd.DataFrame({"Adj Close": [100, 95, 90, 85, 80]})
        result = self.stats.calc_relative_strength(df)
        self.assertEqual(result, 0)  # RS should be 0 because there are no gains

    def test_calc_relative_strength_constant_prices(self):
        """Test when all prices are the same (RS should be NaN or raise an exception)."""
        df = pd.DataFrame({"Adj Close": [100, 100, 100, 100, 100]})
        result = self.stats.calc_relative_strength(df)
        self.assertTrue(pd.isna(result) or result == 1)  # Expect NaN or zero division handling


class TestScreeningStatistics_computeBuySellSignals(unittest.TestCase):

    def setUp(self):
        """Initialize the ScreeningStatistics instance."""
        self.stats = ScreeningStatistics(ConfigManager.tools(),None)

    def test_computeBuySellSignals_none_dataframe(self):
        """Test when input DataFrame is None."""
        result = self.stats.computeBuySellSignals(None)
        self.assertIsNone(result)

    def test_computeBuySellSignals_empty_dataframe(self):
        """Test when input DataFrame is empty."""
        df = pd.DataFrame()
        with pytest.raises(KeyError):
            result = self.stats.computeBuySellSignals(df)
        self.assertTrue(df.empty)

    @pytest.mark.skipif(
        "Windows" not in platform.system(),
        reason="Cannot simulate the disabling of print func on Linux/Mac",
    )
    @patch.dict("pkscreener.Imports", {"vectorbt": True})
    @patch("vectorbt.indicators.MA.run")
    @patch("PKDevTools.classes.OutputControls.OutputControls.printOutput")
    def test_computeBuySellSignals_with_vectorbt(self, mock_print,mock_vbt_run):
        """Test Buy/Sell signals calculation when `vectorbt` is available."""
        mock_ema = MagicMock()
        mock_ema.ma_crossed_above.return_value = [True, False, True]
        mock_ema.ma_crossed_below.return_value = [False, True, False]
        mock_vbt_run.return_value = mock_ema

        df = pd.DataFrame({
            "close": [100, 102, 101],
            "ATRTrailingStop": [99, 100, 101]
        })

        result = self.stats.computeBuySellSignals(df)
        
        self.assertIn("Buy", result.columns)
        self.assertIn("Sell", result.columns)
        self.assertTrue(result["Buy"].iloc[0])  # Check Buy signal is generated
        self.assertFalse(result["Sell"].iloc[0])  # Ensure no Sell signal

    @patch.dict("pkscreener.Imports", {"vectorbt": False})
    @patch("PKDevTools.classes.OutputControls.OutputControls.printOutput")
    @patch("pkscreener.classes.Pktalib.pktalib.EMA", return_value=pd.Series([101, 103, 104]))
    def test_computeBuySellSignals_without_vectorbt(self, mock_ema, mock_printOutput):
        """Test Buy/Sell signals calculation when `vectorbt` is missing (fallback to `pktalib`)."""
        df = pd.DataFrame({
            "close": [100, 102, 101],
            "ATRTrailingStop": [99, 100, 101]
        })

        result = self.stats.computeBuySellSignals(df)
        
        self.assertIn("Buy", result.columns)
        self.assertIn("Sell", result.columns)
        self.assertTrue(result["Buy"].iloc[0])  # Check Buy signal is generated
        self.assertFalse(result["Sell"].iloc[0])  # Ensure no Sell signal
        mock_printOutput.assert_called()

    def test_computeBuySellSignals_missing_columns(self):
        """Test when `Close` or `ATRTrailingStop` columns are missing."""
        df = pd.DataFrame({"close": [100, 102, 101]})  # Missing `ATRTrailingStop`

        with self.assertRaises(KeyError):
            self.stats.computeBuySellSignals(df)

    @pytest.mark.skipif(
        "Windows" not in platform.system(),
        reason="Cannot simulate the disabling of print func on Linux/Mac",
    )
    @patch("PKDevTools.classes.OutputControls.OutputControls.printOutput")
    @patch("pkscreener.classes.ScreeningStatistics.ScreeningStatistics.downloadSaveTemplateJsons")
    def test_computeBuySellSignals_oserror_retry(self, mock_download, mock_printOutput):
        """Test that computeBuySellSignals retries after an OSError and downloads necessary files."""
        df = pd.DataFrame({"close": [100, 102, 101], "ATRTrailingStop": [99, 100, 101]})

        with patch("vectorbt.indicators.MA.run", side_effect=[OSError("File missing"), df]) as mock_compute:
            result = self.stats.computeBuySellSignals(df,retry=False)
        
        mock_download.assert_called()
        self.assertIsNone(result)

    @patch("PKDevTools.classes.OutputControls.OutputControls.printOutput")
    def test_computeBuySellSignals_importerror(self, mock_printOutput):
        """Test ImportError handling when `vectorbt` is missing."""
        df = pd.DataFrame({
            "close": [100, 102, 101],
            "ATRTrailingStop": [99, 100, 101]
        })

        with patch.dict("pkscreener.Imports", {"vectorbt": False}):
            result = self.stats.computeBuySellSignals(df)

        self.assertIn("Buy", result.columns)
        self.assertIn("Sell", result.columns)
        mock_printOutput.assert_called()

    @patch('requests.get')  # Mock the 'requests.get' method
    @patch('builtins.open', new_callable=mock_open)  # Mock the "open" function
    @patch('os.makedirs')  # Mock 'os.makedirs' to prevent actual directory creation
    def test_download_save_template_jsons_success(self, mock_makedirs, mock_open, mock_requests_get):
        # Set up the mock response object with desired behavior
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_requests_get.return_value = mock_response

        # Create an instance of ScreeningStatistics
        stats = ScreeningStatistics()

        # Call the method under test
        stats.downloadSaveTemplateJsons('/fake/directory')

        # Assert that the necessary methods were called with expected arguments
        mock_makedirs.assert_called_once_with('/fake/directory/', exist_ok=True)
        mock_open.assert_called_with('/fake/directory/seaborn.json', 'w')
        mock_open().write.assert_called()

    @patch('requests.get')
    def test_download_save_template_jsons_network_failure(self, mock_requests_get):
        # Simulate a network failure by setting side effect
        mock_requests_get.side_effect = Exception('Network error')

        stats = ScreeningStatistics()

        # Call the method and assert that it handles the exception gracefully
        with self.assertRaises(Exception):
            stats.downloadSaveTemplateJsons('/fake/directory')

    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_save_template_jsons_file_write_error(self, mock_open, mock_requests_get):
        # Set up the mock response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key': 'value'}
        mock_requests_get.return_value = mock_response

        # Simulate a file write error
        mock_open.side_effect = IOError('File write error')

        stats = ScreeningStatistics()

        # Call the method and assert that it handles the exception gracefully
        with self.assertRaises(IOError):
            stats.downloadSaveTemplateJsons('/fake/directory')

    # def test_findATRCross_valid_data(self):
    #     # Create a DataFrame with known "close" prices and expected ATR crossovers
    #     data = {
    #         "close": [100, 105, 102, 108, 107],
    #         # Add other necessary columns if required by the method
    #     }
    #     df = pd.DataFrame(data)
    #     result = self.stats.findATRCross(df,{},{})
    #     # Assert that the result contains expected buy/sell signals
    #     # This will depend on the actual implementation details

    # def test_findATRCross_no_crossovers(self):
    #     # Create a DataFrame where "close" prices do not cross the ATR threshold
    #     data = {
    #         "close": [100, 101, 102, 103, 104],
    #         # Add other necessary columns if required by the method
    #     }
    #     df = pd.DataFrame(data)
    #     result = self.stats.findATRCross(df)
    #     # Assert that no buy/sell signals are generated
    #     # This will depend on the actual implementation details

    # def test_findATRCross_edge_case_single_row(self):
    #     # Test with a single row DataFrame
    #     data = {"close": [100]}
    #     df = pd.DataFrame(data)
    #     result = self.stats.findATRCross(df)
    #     # Assert the method's behavior with minimal data
    #     # This will depend on the actual implementation details

    # def test_findATRCross_invalid_data(self):
    #     # Test with a DataFrame missing necessary columns
    #     data = {"open": [100, 105, 102, 108, 107]}  # Missing "close" column
    #     df = pd.DataFrame(data)
    #     with self.assertRaises(KeyError):
    #         self.stats.findATRCross(df)

# def test_validateShortTermBullish(tools_instance):
#     # Mock the required functions and classes
#     patch('pandas.DataFrame.copy')
#     patch('numpy.round')
#     patch('pandas.DataFrame.fillna')
#     patch('pandas.DataFrame.replace')
#     patch('pandas.DataFrame.head')
#     patch('pandas.concat')
#     patch('pandas.DataFrame.rename')
#     patch('pandas.DataFrame.debug')

#     # Create a test case
#     df = pd.DataFrame({"open": [1.0, 2.0, 3.0], "high": [4.1, 5.1, 6.1], "low": [7.1, 8.1, 9.1], "close": [10.1, 11.1, 120.1], "volume": [13.1, 14.1, 15.1]})
#     df = pd.concat([df]*150, ignore_index=True)
#     ichi = pd.DataFrame({"ISA_9":[100,100,100],"ISB_26":[90,90,90],"IKS_26":[110,110,110],"ITS_9":[111,111,111]})
#     ichi = pd.concat([ichi]*150, ignore_index=True)
#     screenDict = {}
#     saveDict = {}
#     df,_ = tools_instance.preprocessData(df,30)
#     df["FASTK"].iloc[2] = 21
#     df["SSMA"].iloc[0] = 48
#     df["FASTD"].iloc[100] = 100
#     df["FASTK"].iloc[100] = 110
#     df["FASTD"].iloc[101] = 110
#     df["FASTK"].iloc[101] = 100
#     # Call the function under test
#     with patch('pkscreener.classes.Pktalib.pktalib.ichimoku',return_value=ichi):
#         result = tools_instance.validateShortTermBullish(df, screenDict, saveDict)

#         # Assert the expected behavior
#         assert result == False
#         assert screenDict['MA-Signal'] == '\033[32mBullish\033[0m'
#         assert saveDict['MA-Signal'] == 'Bullish'
#     ichi = pd.DataFrame({"ISB_26":[100,100,100],"ISA_9":[90,90,90],"IKS_26":[110,110,110],"ITS_9":[111,111,111]})
#     ichi = pd.concat([ichi]*150, ignore_index=True)
#     with patch('pkscreener.classes.Pktalib.pktalib.ichimoku',return_value=ichi):
#         result = tools_instance.validateShortTermBullish(df, screenDict, saveDict)

#         # Assert the expected behavior
#         assert result == True
#         assert screenDict['MA-Signal'] == '\033[32mBullish\033[0m, \033[32mBullish\033[0m'
#         assert saveDict['MA-Signal'] == 'Bullish, Bullish'

import unittest
from pkscreener.classes.ScreeningStatistics import ScreeningStatistics

class TestCupAndHandleDetection(unittest.TestCase):

    def setUp(self):
        """Create sample stock data for testing."""
        dates = pd.date_range(start="2023-01-01", periods=80, freq='D')
        
        # Generate a synthetic cup and handle pattern
        close_prices = np.concatenate([
            np.linspace(100, 85, 20),  # Left cup side (down)
            np.linspace(85, 90, 20),  # Cup bottom (stabilizing)
            np.linspace(90, 100, 20),  # Right cup side (up)
            np.linspace(100, 98, 5),  # Handle downtrend
            np.linspace(98, 102, 10),  # Handle recovery
            np.linspace(102, 110, 5)   # Breakout
        ])
        
        volume = np.concatenate([
            np.linspace(2000, 1500, 20),  # Decreasing volume in cup
            np.linspace(1500, 1400, 20),  # Stabilized low volume
            np.linspace(1400, 1800, 20),  # Increasing volume in recovery
            np.linspace(1800, 1750, 5),   # Stable volume in handle
            np.linspace(1750, 2200, 10),  # Volume picking up
            np.linspace(2200, 3000, 5)    # Breakout volume spike
        ])

        self.df = pd.DataFrame({'Date': dates, "close": close_prices, "volume": volume})
        self.df['Volatility'] = self.df["close"].rolling(window=20).std()
        self.df.set_index('Date', inplace=True)
        self.screener = ScreeningStatistics(ConfigManager.tools(),None)

    def test_valid_cup_and_handle(self):
        """Test if a valid Cup and Handle pattern is detected."""
        points = self.screener.find_cup_and_handle(self.df)
        self.assertIsNotNone(points, "Cup and Handle pattern should be detected.")

    def test_dynamic_order_calculation(self):
        """Test if the order parameter adjusts based on volatility."""
        high_vol_df = self.df.copy()
        high_vol_df["close"] += np.random.normal(0, 15, len(high_vol_df))  # Add artificial volatility
        high_order = self.screener.get_dynamic_order(high_vol_df)
        
        low_vol_df = self.df.copy()
        low_vol_df["close"] += np.random.normal(0, 1, len(low_vol_df))  # Reduce volatility
        low_order = self.screener.get_dynamic_order(low_vol_df)

        self.assertGreaterEqual(high_order, low_order, "Higher volatility should increase order parameter.")
    
    def test_reject_v_shaped_cup(self):
        """Ensure sharp V-bottoms are not detected as valid cups."""
        v_shaped_df = self.df.copy()
        v_shaped_df.iloc[10:30, v_shaped_df.columns.get_loc("close")] = 85  # Sharp bottom
        _,points = self.screener.find_cup_and_handle(v_shaped_df)
        self.assertIsNone(points, "V-bottom shape should be rejected.")

    def test_handle_depth_constraint(self):
        """Ensure the handle does not drop too much (more than 50% of cup depth)."""
        deep_handle_df = self.df.copy()
        deep_handle_df.iloc[60:65, deep_handle_df.columns.get_loc("close")] -= 5  # Excessive handle drop
        _,points = self.screener.find_cup_and_handle(deep_handle_df)
        self.assertIsNone(points, "Pattern should be rejected due to a deep handle.")

    def test_no_breakout_rejection(self):
        """Ensure patterns without a breakout are rejected."""
        no_breakout_df = self.df.copy()
        no_breakout_df.iloc[-5:, no_breakout_df.columns.get_loc("close")] = 100  # No breakout
        _,points = self.screener.find_cup_and_handle(no_breakout_df)
        self.assertIsNone(points, "Pattern should be rejected without a breakout.")

    def test_no_cup_no_detection(self):
        """Ensure detection doesn't falsely identify a pattern when there's no cup formation."""
        random_df = pd.DataFrame({
            'Date': pd.date_range(start="2023-01-01", periods=100, freq='D'),
            "close": np.random.uniform(90, 110, 100),
            "volume": np.random.uniform(1500, 2500, 100)
        })
        random_df['Volatility'] = random_df["close"].rolling(window=20).std()
        random_df.set_index('Date', inplace=True)
        _,points = self.screener.find_cup_and_handle(random_df)
        self.assertIsNone(points, "No cup pattern exists, should return None.")


class TestScreeningStatistics1(unittest.TestCase):
    
    def setUp(self):
        self.screening_stats = ScreeningStatistics()

    def test_calc_relative_strength_valid_data(self):
        df = pd.DataFrame({
            'Adj Close': [100, 102, 101, 103, 105]
        })
        result = self.screening_stats.calc_relative_strength(df)
        self.assertGreater(result, 0)
    
    def test_calc_relative_strength_no_data(self):
        df = pd.DataFrame()
        result = self.screening_stats.calc_relative_strength(df)
        self.assertEqual(result, -1)
    
    def test_calc_relative_strength_missing_close_column(self):
        df = pd.DataFrame({
            "close": [100, 102, 101, 103, 105]
        })
        result = self.screening_stats.calc_relative_strength(df)
        self.assertGreater(result, 0)

    def test_computeBuySellSignals_valid_data(self):
        df = pd.DataFrame({
            "close": [100, 102, 104, 106, 108],
            'ATRTrailingStop': [99, 101, 103, 105, 107]
        })
        result = self.screening_stats.computeBuySellSignals(df)
        self.assertIn("Buy", result.columns)
        self.assertIn("Sell", result.columns)
    
    def test_computeBuySellSignals_missing_columns(self):
        df = pd.DataFrame({
            "close": [100, 102, 104, 106, 108],
            'ATRTrailingStop': [99, 101, 103, 105, 107]
        })
        result = self.screening_stats.computeBuySellSignals(df)
        self.assertIsNotNone(result)
    
    @patch("pkscreener.classes.Pktalib.pktalib.EMA", return_value=np.array([100, 101, 102, 103, 104]))
    def test_computeBuySellSignals_with_mocked_ema(self, mock_ema):
        df = pd.DataFrame({
            "close": [100, 102, 104, 106, 108],
            'ATRTrailingStop': [99, 101, 103, 105, 107]
        })
        result = self.screening_stats.computeBuySellSignals(df)
        self.assertIn("Buy", result.columns)
        self.assertIn("Sell", result.columns)

    @patch("pkscreener.classes.Pktalib.pktalib.ATR", return_value=pd.Series([1.5, 2.0, 2.5, 3.0, 3.5]))
    def test_findATRCross(self, mock_atr):
        df = pd.DataFrame({
            "high": [105, 106, 107, 108, 109],
            "low": [95, 96, 97, 98, 99],
            "close": [100, 102, 104, 106, 108],
            "open": [105, 106, 107, 108, 109],
            'RSI': [56, 54, 53, 52, 51],
            'RSIi': [50, 52, 54, 56, 58],
            "volume": [1000, 1200, 1300, 1400, 1500]
        })
        saveDict = {}
        screenDict = {}
        result = self.screening_stats.findATRCross(df, saveDict, screenDict)
        self.assertTrue(result.dtype == bool)
        self.assertIn("ATR", saveDict)
        self.assertIn("ATR", screenDict)

    @patch("pkscreener.classes.Pktalib.pktalib.ATR", return_value=pd.Series([1.5, 2.0, 2.5, 3.0, 3.5]))
    def test_findATRTrailingStops(self, mock_atr):
        df = pd.DataFrame({
            "high": [105, 106, 107, 108, 109],
            "low": [95, 96, 97, 98, 99],
            "close": [100, 102, 104, 106, 108],
            "volume": [1000, 1200, 1300, 1400, 1500]
        })
        saveDict = {}
        screenDict = {}
        result = self.screening_stats.findATRTrailingStops(df, saveDict=saveDict, screenDict=screenDict)
        self.assertTrue(result.dtype == bool)
        self.assertIn("B/S", saveDict)
        self.assertIn("B/S", screenDict)

    @patch("pkscreener.classes.Pktalib.pktalib.BBANDS", return_value=(pd.Series([110] * 30), pd.Series([105] * 30), pd.Series([100] * 30)))
    @patch("pkscreener.classes.Pktalib.pktalib.KeltnersChannel", return_value=(pd.Series([99] * 30), pd.Series([113] * 30)))
    def test_findBbandsSqueeze(self, mock_bbands, mock_keltners):
        df = pd.DataFrame({
            "high": [108] * 30,
            "low": [98] * 30,
            "close": [103] * 30
        })
        saveDict = {}
        screenDict = {}
        result = self.screening_stats.findBbandsSqueeze(df, screenDict, saveDict)
        self.assertIsInstance(result, bool)
        self.assertIn("Pattern", saveDict)
        self.assertIn("Pattern", screenDict)

    @patch("pkscreener.classes.Pktalib.pktalib.AVWAP", return_value=pd.Series([102] * 30))
    @patch("pkscreener.classes.ConfigManager.tools")
    def test_findBullishAVWAP(self, mock_config,mock_avwap):
        df = pd.DataFrame({
            "high": [108] * 30,
            "low": [98] * 30,
            "close": [103] * 30,
            "open": [98] * 30,
            "volume": [1000] * 30
        })
        saveDict = {}
        screenDict = {}
        self.screening_stats.configManager = mock_config
        self.screening_stats.configManager.volumeRatio = 0.5
        self.screening_stats.configManager.anchoredAVWAPPercentage = 1
        result = self.screening_stats.findBullishAVWAP(df, screenDict, saveDict)
        self.assertTrue(result.dtype == bool)
        self.assertIn("AVWAP", saveDict)
        self.assertIn("AVWAP", screenDict)
        self.assertIn("Anchor", saveDict)
        self.assertIn("Anchor", screenDict)

