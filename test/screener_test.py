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
import math
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

import pkscreener.classes.ConfigManager as ConfigManager
import pkscreener.classes.Utility as Utility
from pkscreener.classes.log import default_logger as dl
from pkscreener.classes.Pktalib import pktalib
from pkscreener.classes.Screener import tools


@pytest.fixture
def configManager():
    return ConfigManager.tools()

@pytest.fixture
def default_logger():
    return dl()

@pytest.fixture
def tools_instance(configManager, default_logger):
    return tools(configManager, default_logger)

def test_find52WeekHighBreakout_positive(tools_instance):
    data = pd.DataFrame({'High': [110, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == True

def test_find52WeekHighBreakout_negative(tools_instance):
    data = pd.DataFrame({'High': [50, 60, 80, 60, 60, 40,100,110,120,50,170]})
    assert tools_instance.find52WeekHighBreakout(data) == False

def test_find52WeekHighBreakout_edge(tools_instance):
    data = pd.DataFrame({'High': [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]})
    assert tools_instance.find52WeekHighBreakout(data) == False

def test_find52WeekHighBreakout_nan_values(tools_instance):
    data = pd.DataFrame({'High': [50, 60, np.nan, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False

def test_find52WeekHighBreakout_inf_values(tools_instance):
    data = pd.DataFrame({'High': [50, 60, np.inf, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False

def test_find52WeekHighBreakout_negative_inf_values(tools_instance):
    data = pd.DataFrame({'High': [50, 60, -np.inf, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False

def test_find52WeekHighBreakout_last1WeekHigh_greater(tools_instance):
    data = pd.DataFrame({'High': [50, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False

def test_find52WeekHighBreakout_previousWeekHigh_greater(tools_instance):
    data = pd.DataFrame({'High': [50, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False

def test_find52WeekHighBreakout_full52WeekHigh_greater(tools_instance):
    data = pd.DataFrame({'High': [50, 60, 70, 80, 90, 100]})
    assert tools_instance.find52WeekHighBreakout(data) == False

# Positive test case for find52WeekLowBreakout function
def test_find52WeekLowBreakout_positive(tools_instance):
    data = pd.DataFrame({'Low': [10, 20, 30, 40, 50]})
    result = tools_instance.find52WeekLowBreakout(data)
    assert result == True

# Negative test case for find52WeekLowBreakout function
def test_find52WeekLowBreakout_negative(tools_instance):
    data = pd.DataFrame({'Low': [50, 40, 30, 20, 10]})
    result = tools_instance.find52WeekLowBreakout(data)
    assert result == True

# Edge test case for find52WeekLowBreakout function
def test_find52WeekLowBreakout_edge(tools_instance):
    data = pd.DataFrame({'Low': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]})
    result = tools_instance.find52WeekLowBreakout(data)
    assert result == True

# Positive test case for find10DaysLowBreakout function
def test_find10DaysLowBreakout_positive(tools_instance):
    data = pd.DataFrame({'Low': [10, 20, 30, 40, 50]})
    result = tools_instance.find10DaysLowBreakout(data)
    assert result == True

# Negative test case for find10DaysLowBreakout function
def test_find10DaysLowBreakout_negative(tools_instance):
    data = pd.DataFrame({'Low': [50, 40, 30, 20, 10]})
    result = tools_instance.find10DaysLowBreakout(data)
    assert result == False

# Edge test case for find10DaysLowBreakout function
def test_find10DaysLowBreakout_edge(tools_instance):
    data = pd.DataFrame({'Low': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200]})
    result = tools_instance.find10DaysLowBreakout(data)
    assert result == True

# Positive test case for findAroonBullishCrossover function
def test_findAroonBullishCrossover_positive(tools_instance):
    data = pd.DataFrame({'High': [50, 60, 70, 80, 90], 'Low': [10, 20, 30, 40, 50]})
    result = tools_instance.findAroonBullishCrossover(data)
    assert result == False

# Negative test case for findAroonBullishCrossover function
def test_findAroonBullishCrossover_negative(tools_instance):
    data = pd.DataFrame({'High': [90, 80, 70, 60, 50], 'Low': [50, 40, 30, 20, 10]})
    result = tools_instance.findAroonBullishCrossover(data)
    assert result == False

# Edge test case for findAroonBullishCrossover function
def test_findAroonBullishCrossover_edge(tools_instance):
    data = pd.DataFrame({'High': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200], 'Low': [50, 40, 30, 20, 10, 200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60]})
    result = tools_instance.findAroonBullishCrossover(data)
    assert result == False

# Positive test case for findBreakout function
def test_findBreakout_positive(tools_instance):
    data = pd.DataFrame({'High': [50, 60, 70, 80, 90], 'Close': [40, 50, 60, 70, 80]})
    screenDict = {}
    saveDict = {"Stock":"SBIN"}
    daysToLookback = 5
    result = tools_instance.findBreakout(data, screenDict, saveDict, daysToLookback)
    assert result == False

# Negative test case for findBreakout function
def test_findBreakout_negative(tools_instance):
    data = pd.DataFrame({'High': [90, 80, 70, 60, 50], 'Close': [80, 70, 60, 50, 40], 'Open': [80, 70, 60, 50, 40]})
    screenDict = {}
    saveDict = {"Stock":"SBIN"}
    daysToLookback = 5
    result = tools_instance.findBreakout(data, screenDict, saveDict, daysToLookback)
    assert result == True

# Edge test case for findBreakout function
def test_findBreakout_edge(tools_instance):
    data = pd.DataFrame({'High': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200], 'Open': [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10], 'Close': [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10]})
    screenDict = {}
    saveDict = {"Stock":"SBIN"}
    daysToLookback = 5
    result = tools_instance.findBreakout(data, screenDict, saveDict, daysToLookback)
    assert result == True

# # Mocking the necessary functions or dependencies
# @pytest.fixture(autouse=True)
# def mock_dependencies(monkeypatch):
#     monkeypatch.setattr(pd, 'DataFrame', MagicMock())
#     monkeypatch.setattr(np, 'nan', MagicMock())
#     monkeypatch.setattr(np, 'inf', MagicMock())
#     monkeypatch.setattr(math, 'isnan', MagicMock())
#     monkeypatch.setattr(math, 'isinf', MagicMock())
#     monkeypatch.setattr(pktalib, 'Aroon', MagicMock())
#     monkeypatch.setattr(tools, 'getCandleType', MagicMock())

# Positive test case for findBullishIntradayRSIMACD function
# def test_findBullishIntradayRSIMACD_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
#     data.tail().iloc[0].return_value = 60
#     data.tail().iloc[1].return_value = 50
#     data.tail().iloc[2].return_value = 40
#     data.tail().iloc[3].return_value = 30
#     data.tail().iloc[4].return_value = 20
#     data.tail().iloc[5].return_value = 10
#     data.tail().iloc[6].return_value = 0
#     data.tail().iloc[7].return_value = -10
#     data.tail().iloc[8].return_value = -20
#     data.tail().iloc[9].return_value = -30

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findBullishIntradayRSIMACD(data) == True

# # Negative test case for findBullishIntradayRSIMACD function
# def test_findBullishIntradayRSIMACD_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
#     data.tail().iloc[0].return_value = 60
#     data.tail().iloc[1].return_value = 50
#     data.tail().iloc[2].return_value = 40
#     data.tail().iloc[3].return_value = 30
#     data.tail().iloc[4].return_value = 20
#     data.tail().iloc[5].return_value = 10
#     data.tail().iloc[6].return_value = 0
#     data.tail().iloc[7].return_value = -10
#     data.tail().iloc[8].return_value = -20
#     data.tail().iloc[9].return_value = -40

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findBullishIntradayRSIMACD(data) == False

# # Positive test case for findNR4Day function
# def test_findNR4Day_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.tail().iloc[0].return_value = 50001
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
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
#     assert tool.findNR4Day(data) == True

# # Negative test case for findNR4Day function
# def test_findNR4Day_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.tail().iloc[0].return_value = 50000
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
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
#     # Call the function 
#     assert tool.findNR4Day(data) == False

# # Positive test case for findReversalMA function
# def test_findReversalMA_positive():
#     # Mocking the data
#     data = MagicMock()
#     data[::-1].head.return_value = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().ilociloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 10

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findReversalMA(data, {}, {}, 10) == True

# # Negative test case for findReversalMA function
# def test_findReversalMA_negative():
#     # Mocking the data
#     data = MagicMock()
#     data[::-1].head.return_value = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 5

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findReversalMA(data, {}, {}, 10) == False

# # Positive test case for findTrend function
# def test_findTrend_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 10

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findTrend(data, {}, {}, 10) == "Strong Up"

# # Negative test case for findTrend function
# def test_findTrend_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.head.return_value = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 5

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findTrend(data, {}, {}, 10) == "Strong Down"

# # Positive test case for findTrendlines function
# def test_findTrendlines_positive():
#     # Mocking the data
#     data = MagicMock()
#     data[::-1].head.return_value = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 10

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findTrendlines(data, {}, {}) == True

# # Negative test case for findTrendlines function
# def test_findTrendlines_negative():
#     # Mocking the data
#     data = MagicMock()
#     data[::-1].head.return_value = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 5

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.findTrendlines(data, {}, {}) == False

# # Positive test case for getCandleType function
# def test_getCandleType_positive():
#     # Mocking the dailyData
#     dailyData = MagicMock()
#     dailyData["Close"].iloc[0].return_value = 100
#     dailyData["Open"].iloc[0].return_value = 90

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.getCandleType(dailyData) == True

# # Negative test case for getCandleType function
# def test_getCandleType_negative():
#     # Mocking the dailyData
#     dailyData = MagicMock()
#     dailyData["Close"].iloc[0].return_value = 90
#     dailyData["Open"].iloc[0].return_value = 100

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.getCandleType(dailyData) == False

# # PositiveNiftyPrediction function
# def test_getNiftyPrediction_positive():
#     # Mocking the data
#     data = MagicMock()
#     # Mocking the scaler
#     scaler = MagicMock()
#     pkl = {"columns": scaler}
#     data[pkl["columns"]].return_value = data
#     data["High"].pct_change.return_value = data
#     data["Low"].pct_change.return_value = data
#     data["Open"].pct_change.return_value = data
#     data["Close"].pct_change.return_value = data
#     data.iloc[-1].return_value = 0.1

#     # Mocking the model
#     model = MagicMock()
#     model.predict.return_value = [0.6]

    
#     # Mocking the Utility class
#     Utility.tools.getNiftyModel.return_value = (model, pkl)

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.getNiftyPrediction(data) == (0.6, "BEARISH", "Probability/Strength of Prediction = 75.0%")

# # Negative test case for getNiftyPrediction function
# def test_getNiftyPrediction_negative():
#     # Mocking the data
#     data = MagicMock()

#     # Mocking the model
#     model = MagicMock()
#     model.predict.return_value = [0.4]

#     # Mocking the scaler
#     scaler = MagicMock()
#     pkl = {"columns": scaler}
#     # Mocking the Utility class
#     Utility.tools.getNiftyModel.return_value = (model, pkl)
#     data[pkl["columns"]].return_value = data
#     data["High"].pct_change.return_value = data
#     data["Low"].pct_change.return_value = data
#     data["Open"].pct_change.return_value = data
#     data["Close"].pct_change.return_value = data
#     data.iloc[-1].return_value = 0.1
#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.getNiftyPrediction(data) == (0.4, "BULLISH", "Probability/Strength of Prediction = 60.0%")

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

# # Positive test case for preprocessData function
# def test_preprocessData_positive():
#     # Mocking the data
#     data = MagicMock()
#     data["Close"].return_value = data
#     data["Volume"].return_value = data
#     data["Close"].rolling.return_value = MagicMock()
#     data["Volume"].rolling.return_value = MagicMock()
#     data[::-1].head.return_value = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 10

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.preprocessData(data, 10) == (data, data.head(10))

# # Negative test case for preprocessData function
# def test_preprocessData_negative():
#     # Mocking the data
#     data = MagicMock()
#     data["Close"].return_value = data
#     data["Volume"].return_value = data
#     data["Close"].rolling.return_value = MagicMock()
#     data["Volume"].rolling.return_value = MagicMock()
#     data[::-1].head.return_value = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 5

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.preprocessData(data, 10) == (data, data.head(5))

# # Positive test case for validate15MinutePriceVolumeBreakout function
# def test_validate15MinutePriceVolumeBreakout_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
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
#     assert tool.validate15MinutePriceVolumeBreakout(data) == True

# # Negative test case for validate15MinutePriceVolumeBreakout function
# def test_validate15MinutePriceVolumeBreakout_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
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
#     assert tool.validate15MinutePriceVolumeBreakout(data) == False

# # Positive test case for validateBullishForTomorrow function
# def test_validateBullishForTomorrow_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
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
#     assert tool.validateBullishForTomorrow(data) == True

# # Negative test case for validateBullishForTomorrow function
# def test_validateBullishForTomorrow_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data[::-1].tail.return_value = MagicMock()
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
#     assert tool.validateBullishForTomorrow(data) == False

# # Positive test case for validateCCI function
# def test_validateCCI_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data.head().iloc[0].return_value = 100

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateCCI(data, {}, {}, 0, 100) == True

# # Negative test case for validateCCI function
# def test_validateCCI_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.fillna.return_value = data
#     data.replace.return_value = data
#     data.head().iloc[0].return_value = 100

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateCCI(data, {}, {}, 200, 300) == False

# # Positive test case for validateConfluence function
# def test_validateConfluence_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 10

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateConfluence(None, data, {}, {}, 0.1) == True

# # Negative test case for validateConfluence function
# def test_validateConfluence_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.head().iloc[0].return_value = 100
#     data.head().iloc[1].return_value = 90
#     data.head().iloc[2].return_value = 80
#     data.head().iloc[3].return_value = 70
#     data.head().iloc[4].return_value = 60
#     data.head().iloc[5].return_value = 50
#     data.head().iloc[6].return_value = 40
#     data.head().iloc[7].return_value = 30
#     data.head().iloc[8].return_value = 20
#     data.head().iloc[9].return_value = 5

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateConfluence(None, data, {}, {}, 0.1) == False

# # Positive test case for validateConsolidation function
# def test_validateConsolidation_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.describe()["Close"]["max"].return_value = 100
#     data.describe()["Close"]["min"].return_value = 90

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateConsolidation(data, {}, {}, 10) == 10.0

# # Negative test case for validateConsolidation function
# def test_validateConsolidation_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.describe()["Close"]["max"].return_value = 100
#     data.describe()["Close"]["min"].return_value = 80

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateConsolidation(data, {}, {}, 10) == 20.0

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
#     data[::-1].min()["Close"].return_value = 100
#     data[::-1].max()["Close"].return_value = 200
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
#     data[::-1].min()["Close"].return_value = 100
#     data[::-1].max()["Close"].return_value = 200
#     data.head().iloc[0].return_value = 250

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateIpoBase(None, data, {}, {}, 0.3) == False

# # Positive test case for validateLowestVolume function
# def test_validateLowestVolume_positive():
#     # Mocking the data
#     data = MagicMock()
#     data.describe()["Volume"]["min"].return_value = 100
#     data.head().iloc[0].return_value = 100

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateLowestVolume(data, 10) == True

# # Negative test case for validateLowestVolume function
# def test_validateLowestVolume_negative():
#     # Mocking the data
#     data = MagicMock()
#     data.describe()["Volume"]["min"].return_value = 100
#     data.head().iloc[0].return_value = 200

#     # Create an instance of the tools class
#     tool = tools(None, None)

#     # Call the function and assert the result
#     assert tool.validateLowestVolume(data, 10) == False

# Positive test case for validateLTP function
def test_validateLTP_positive(tools_instance):
    data = pd.DataFrame({'Close': [100, 110, 120]})
    screenDict = {}
    saveDict = {}
    result, verifyStageTwo = tools_instance.validateLTP(data, screenDict, saveDict, minLTP=100, maxLTP=120)
    assert result == True
    assert verifyStageTwo == True
    assert screenDict['LTP'] == '\x1b[92m100.00\x1b[0m'
    assert saveDict['LTP'] == ' 100.00'

# Negative test case for validateLTP function
def test_validateLTP_negative(tools_instance):
    data = pd.DataFrame({'Close': [90, 95, 100]})
    screenDict = {}
    saveDict = {}
    result, verifyStageTwo = tools_instance.validateLTP(data, screenDict, saveDict, minLTP=100, maxLTP=120)
    assert result == False
    assert verifyStageTwo == True
    assert screenDict['LTP'] == '\x1b[91m90.00\x1b[0m'
    assert saveDict['LTP'] == ' 90.00'

# Positive test case for validateMACDHistogramBelow0 function
def test_validateMACDHistogramBelow0_positive(tools_instance):
    data = pd.DataFrame({'Close': [100, 110, 120]})
    result = tools_instance.validateMACDHistogramBelow0(data)
    assert result == False

# # Negative test case for validateMACDHistogramBelow0 function
# def test_validateMACDHistogramBelow0_negative(tools_instance):
#     data = pd.DataFrame({'Close': [100, 90, 80]})
#     result = tools.validateMACDHistogramBelow0(data)
#     assert result == True

# # Positive test case for validateMomentum function
# def test_validateMomentum_positive(tools_instance):
#     data = pd.DataFrame({'Close': [100, 110, 120], 'Open': [90, 100, 110]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateMomentum(data, screenDict, saveDict)
#     assert result == True
#     assert screenDict['Pattern'] == '\x1b[1m\x1b[92mMomentum Gainer\x1b[0m'
#     assert saveDict['Pattern'] == 'Momentum Gainer'

# Negative test case for validateMomentum function
def test_validateMomentum_negative(tools_instance):
    data = pd.DataFrame({'Close': [100, 90, 80], 'Open': [110, 100, 90]})
    screenDict = {}
    saveDict = {}
    result = tools_instance.validateMomentum(data, screenDict, saveDict)
    assert result == False

# # Positive test case for validateMovingAverages function
# def test_validateMovingAverages_positive(tools_instance):
#     data = pd.DataFrame({'Close': [100, 110, 120], 'SMA': [90, 100, 110], 'LMA': [80, 90, 100]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateMovingAverages(data, screenDict, saveDict)
#     assert result == 1
#     assert screenDict['MA-Signal'] == '\x1b[1m\x1b[92mBullish\x1b[0m'

# # Negative test case for validateMovingAverages function
# def test_validateMovingAverages_negative(tools_instance):
#     data = pd.DataFrame({'Close': [100, 90, 80], 'SMA': [110, 100, 90], 'LMA': [120, 110, 100]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateMovingAverages(data, screenDict, saveDict)
#     assert result == -1
#     assert screenDict['MA-Signal'] == '\x1b[1m\x1b[91mBearish\x1b[0m'
#     assert saveDict['MA-Signal'] == 'Bearish'

# # Positive test case for validateNarrowRange function
# def test_validateNarrowRange_positive(tools_instance):
#     data = pd.DataFrame({'Close': [100, 110, 120, 130]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateNarrowRange(data, screenDict, saveDict, nr=3)
#     assert result == True
#     assert screenDict['Pattern'] == '\x1b[1m\x1b[92mBuy-NR3\x1b[0m'
#     assert saveDict['Pattern'] == 'Buy-NR3'

# # Negative test case for validateNarrowRange function
# def test_validateNarrowRange_negative(tools_instance):
#     data = pd.DataFrame({'Close': [100, 110, 120, 130]})
#     screenDict = {}
#     saveDict = {}
#     result = tools_instance.validateNarrowRange(data, screenDict, saveDict, nr=2)
#     assert result == False

# Positiveed function
def test_validateNewlyListed_positive(tools_instance):
    data = pd.DataFrame({'Close': [100, 110, 120]})
    result = tools_instance.validateNewlyListed(data, daysToLookback='2d')
    assert result == False

# Negative test case for validateNewlyListed function
def test_validateNewlyListed_negative(tools_instance):
    data = pd.DataFrame({'Close': [100]})
    result = tools_instance.validateNewlyListed(data, daysToLookback='2d')
    assert result == True

@pytest.fixture
def mock_data():
    return pd.DataFrame({
        'Close': [100, 105, 110, 115],
        'RSI': [60, 65, 70, 75],
        'FASTK': [30, 40, 50, 60],
        'Open': [95, 100, 105, 110],
        'High': [105, 110, 115, 120],
        'Low': [95, 100, 105, 110],
        'Volume': [1000, 2000, 3000, 4000],
        'VolMA': [1500, 2000, 2500, 3000]
    })

@pytest.fixture
def mock_screen_dict():
    return {}

@pytest.fixture
def mock_save_dict():
    return {}

# def test_validatePriceRisingByAtLeast2Percent_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validatePriceRisingByAtLeast2Percent(mock_data, mock_screen_dict, mock_save_dict) == True
#     assert mock_screen_dict["LTP"] == "\033[92m115.00 (5.0%, 4.8%, 4.3%)\033[0m"
#     assert mock_save_dict["LTP"] == "115.00 (5.0%, 4.8%, 4.3%)"

def test_validatePriceRisingByAtLeast2Percent_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data["Close"] = [100, 105, 110, 112]
    assert tools_instance.validatePriceRisingByAtLeast2Percent(mock_data, mock_screen_dict, mock_save_dict) == False
    assert mock_screen_dict.get("LTP") == None
    assert mock_save_dict.get("LTP") == None

# def test_validateRSI_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validateRSI(mock_data, mock_screen_dict, mock_save_dict, 60, 80) == True
#     assert mock_screen_dict["RSI"] == "\033[1m\033[92m75\033[0m"
#     assert mock_save_dict["RSI"] == 75

# def test_validateRSI_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validateRSI(mock_data, mock_screen_dict, mock_save_dict, 80, 90) == False
#     assert mock_screen_dict["RSI"] == "\033[1m\033[91m75\033[0m"
#     assert mock_save_dict["RSI"] == 75

# def test_validateShortTermBullish_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validateShortTermBullish(mock_data, mock_screen_dict, mock_save_dict) == True
#     assert mock_screen_dict["MA-Signal"] == "\033[1m\033[92mBullish\033[0m"
#     assert mock_save_dict["MA-Signal"] == "Bullish"

def test_validateShortTermBullish_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data["FASTK"] = [70, 60, 50, 40]
    assert tools_instance.validateShortTermBullish(mock_data, mock_screen_dict, mock_save_dict) == False
    assert mock_screen_dict.get("MA-Signal") == None
    assert mock_save_dict.get("MA-Signal") == None

# def test_validateVCP_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validateVCP(mock_data, mock_screen_dict, mock_save_dict, "Stock A", 3, 3) == True
#     assert mock_screen_dict["Pattern"] == "\033[1m\033[92mVCP (BO: 115.0)\033[0m"
#     assert mock_save_dict["Pattern"] == "VCP (BO: 115.0)"

def test_validateVCP_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
    mock_data["High"] = [105, 110, 115, 120]
    assert tools_instance.validateVCP(mock_data, mock_screen_dict, mock_save_dict, "Stock A", 3, 3) == False
    assert mock_screen_dict.get("Pattern") == None
    assert mock_save_dict.get("Pattern") == None

# def test_validateVolume_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validateVolume(mock_data, mock_screen_dict, mock_save_dict, 2.5) == True
#     assert mock_screen_dict["Volume"] == 2.67
#     assert mock_save_dict["Volume"] == 2.67

# def test_validateVolume_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     mock_data["Volume"] = [1000, 2000, 3000, 3500]
#     assert tools_instance.validateVolume(mock_data, mock_screen_dict, mock_save_dict, 2.5) == False
#     assert mock_screen_dict["Volume"] == 3.5
#     assert mock_save_dict["Volume"] == 3.5

# def test_SpreadAnalysis_positive(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     assert tools_instance.validateVolumeSpreadAnalysis(mock_data, mock_screen_dict, mock_save_dict) == True
#     assert mock_screen_dict["Pattern"] == "\033[1m\033[92mSupply Drought\033[0m"
#     assert mock_save_dict["Pattern"] == "Supply Drought"

# def test_validateVolumeSpreadAnalysis_negative(mock_data, mock_screen_dict, mock_save_dict, tools_instance):
#     mock_data["Open"] = [100, 105, 110,]    
#     assert tools_instance.validateVolumeSpreadAnalysis(mock_data, mock_screen_dict, mock_save_dict) == False
#     assert mock_screen_dict.get("Pattern") == None
#     assert mock_save_dict.get("Pattern") == None
