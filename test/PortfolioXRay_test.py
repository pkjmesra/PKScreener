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
import platform
import pytest 
import argparse
import pandas as pd
from  pkscreener.classes.PortfolioXRay import * 
from configparser import ConfigParser
from unittest.mock import patch
from pkscreener.classes.ConfigManager import tools

import numpy as np
from PKDevTools.classes.ColorText import colorText
from PKDevTools.classes.PKDateUtilities import PKDateUtilities
from pkscreener.classes import Utility
from RequestsMocker import RequestsMocker as PRM
import unittest
from unittest.mock import patch, MagicMock

@pytest.fixture
def args():
    return None

def test_summariseAllStrategies_returns_dataframe():
    with patch("pandas.read_html",new=PRM().patched_readhtml):
        result = summariseAllStrategies(testing=True)
        assert df is not None


@pytest.mark.skip(reason="API has changed")
@pytest.mark.parametrize('reportName', ['PKScreener_B_12_1_Insights_DateSorted.html'])
def test_bestStrategiesFromSummaryForReport_returns_dataframe(reportName):
    with patch("pandas.read_html",new=PRM().patched_readhtml):
        df = bestStrategiesFromSummaryForReport(reportName)
        assert df is None


@pytest.mark.parametrize('df_CCIAbove200, expected_CCIAbove200', [
    (pd.DataFrame({'CCI': [100, 150, 200, 250]}), pd.DataFrame({'CCI': [250]})),
    (pd.DataFrame({'CCI': [100, 150, 200, 250, 300]}), pd.DataFrame({'CCI': [250, 300]})),
    (pd.DataFrame({'CCI': [100, 150, 200]}), pd.DataFrame({'CCI':[]}).astype(int)),
    (pd.DataFrame({'CCI': []}), pd.DataFrame({'CCI':[]}))
])
def test_filterCCIAbove200(df_CCIAbove200, expected_CCIAbove200):
    result = filterCCIAbove200(df_CCIAbove200)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_CCIAbove200,check_dtype=False)
    assert filterCCIAbove200(None) is None

@pytest.mark.parametrize('df_CCI100To200, expected_CCI100To200', [
    (pd.DataFrame({'CCI': [100, 120, 150, 250]}), pd.DataFrame({'CCI': [120,150]})),
    (pd.DataFrame({'CCI': [100, 120, 150, 200, 300]}), pd.DataFrame({'CCI': [120,150, 200]})),
    (pd.DataFrame({'CCI': [100, 201]}), pd.DataFrame({'CCI':[]}).astype(int)),
    (pd.DataFrame({'CCI': []}), pd.DataFrame({'CCI':[]}))
])
def test_filterCCI100To200(df_CCI100To200, expected_CCI100To200):
    result = filterCCI100To200(df_CCI100To200)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_CCI100To200,check_dtype=False)
    assert filterCCI100To200(None) is None

@pytest.mark.parametrize('df_CCI0To100, expected_CCI0To100', [
    (pd.DataFrame({'CCI': [0, 20, 50, 150]}), pd.DataFrame({'CCI': [0,20,50]})),
    (pd.DataFrame({'CCI': [0, 20, 50, 100, 200]}), pd.DataFrame({'CCI': [0,20,50,100]})),
    (pd.DataFrame({'CCI': [101, 201]}), pd.DataFrame({'CCI':[]}).astype(int)),
    (pd.DataFrame({'CCI': []}), pd.DataFrame({'CCI':[]}))
])
def test_filterCCIoTo100(df_CCI0To100, expected_CCI0To100):
    result = filterCCI0To100(df_CCI0To100)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_CCI0To100,check_dtype=False)
    assert filterCCI0To100(None) is None

@pytest.mark.parametrize('df_CCIBelow0, expected_CCIBelow0', [
    (pd.DataFrame({'CCI': [-100, -90, -50, 0]}), pd.DataFrame({'CCI': [-90,-50]})),
    (pd.DataFrame({'CCI': [-99, -1, 0, -100, 50, 100, 200]}), pd.DataFrame({'CCI': [-99,-1]})),
    (pd.DataFrame({'CCI': [101, 201]}), pd.DataFrame({'CCI':[]}).astype(int)),
    (pd.DataFrame({'CCI': []}), pd.DataFrame({'CCI':[]}))
])
def test_filterCCIBelow0(df_CCIBelow0, expected_CCIBelow0):
    result = filterCCIBelow0(df_CCIBelow0)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_CCIBelow0,check_dtype=False)
    assert filterCCIBelow0(None) is None

@pytest.mark.parametrize('df_CCIBelowMinus100, expected_CCIBelowMinus100', [
    (pd.DataFrame({'CCI': [-100, -190, -50, 0]}), pd.DataFrame({'CCI': [-100,-190]})),
    (pd.DataFrame({'CCI': [-490, -100, 0, -90, 50, 100, 200]}), pd.DataFrame({'CCI': [-490,-100]})),
    (pd.DataFrame({'CCI': [101, 201]}), pd.DataFrame({'CCI':[]}).astype(int)),
    (pd.DataFrame({'CCI': []}), pd.DataFrame({'CCI':[]}))
])
def test_filterCCIBElowMinus100(df_CCIBelowMinus100, expected_CCIBelowMinus100):
    result = filterCCIBelowMinus100(df_CCIBelowMinus100)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_CCIBelowMinus100,check_dtype=False)
    assert filterCCIBelowMinus100(None) is None

# def test_performXRay_with_savedResults(args):
#     savedResults = [1, 2, 3, 4, 5]
#     with patch('pkscreener.classes.PortfolioXRay.getbacktestPeriod') as mock_getbacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.cleanupData') as mock_cleanupData, \
#          patch('pkscreener.classes.PortfolioXRay.getUpdatedBacktestPeriod') as mock_getUpdatedBacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.getBacktestDataFromCleanedData') as mock_getBacktestDataFromCleanedData, \
#          patch('pkscreener.classes.PortfolioXRay.cleanFormattingForStatsData') as mock_cleanFormattingForStatsData:
        
#         mock_getbacktestPeriod.return_value = 10
#         mock_cleanupData.return_value = savedResults
#         mock_getUpdatedBacktestPeriod.return_value = 10
#         mock_getBacktestDataFromCleanedData.return_value = pd.DataFrame(savedResults)
#         mock_cleanFormattingForStatsData.return_value = pd.DataFrame(savedResults)
        
#         result = performXRay(savedResults=savedResults, args=args, calcForDate=None)
        
#         assert isinstance(result, pd.DataFrame)
#         assert len(result) == len(savedResults)

# def test_performXRay_with_savedResults_no_backtestPeriods(args):
#     savedResults = [1, 2, 3, 4, 5]
#     with patch('pkscreener.classes.PortfolioXRay.getbacktestPeriod') as mock_getbacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.cleanupData') as mock_cleanupData, \
#          patch('pkscreener.classes.PortfolioXRay.getUpdatedBacktestPeriod') as mock_getUpdatedBacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.getBacktestDataFromCleanedData') as mock_getBacktestDataFromCleanedData, \
#          patch('pkscreener.classes.PortfolioXRay.cleanFormattingForStatsData') as mock_cleanFormattingForStatsData:
        
#         mock_getbacktestPeriod.return_value = 0
#         mock_getUpdatedBacktestPeriod.return_value = 0
#         mock_cleanupData.return_value = savedResults
        
#         result = performXRay(savedResults=savedResults, args=args, calcForDate=None)
        
#         assert result is None

# def test_performXRay_with_savedResults_no_df(args):
#     savedResults = [1, 2, 3, 4, 5]
#     with patch('pkscreener.classes.PortfolioXRay.getbacktestPeriod') as mock_getbacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.cleanupData') as mock_cleanupData, \
#          patch('pkscreener.classes.PortfolioXRay.getUpdatedBacktestPeriod') as mock_getUpdatedBacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.getBacktestDataFromCleanedData') as mock_getBacktestDataFromCleanedData, \
#          patch('pkscreener.classes.PortfolioXRay.cleanFormattingForStatsData') as mock_cleanFormattingForStatsData:
        
#         mock_getbacktestPeriod.return_value = 10
#         mock_cleanupData.return_value = savedResults
#         mock_getUpdatedBacktestPeriod.return_value = 10
#         mock_getBacktestDataFromCleanedData.return_value = None
        
#         result = performXRay(savedResults=savedResults, args=args, calcForDate=None)
        
#         assert result is None

# def test_performXRay_with_savedResults_no_calcForDate(args):
#     savedResults = [1, 2, 3, 4, 5]
#     with patch('pkscreener.classes.PortfolioXRay.getbacktestPeriod') as mock_getbacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.cleanupData') as mock_cleanupData, \
#          patch('pkscreener.classes.PortfolioXRay.getUpdatedBacktestPeriod') as mock_getUpdatedBacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.getBacktestDataFromCleanedData') as mock_getBacktestDataFromCleanedData, \
#          patch('pkscreener.classes.PortfolioXRay.cleanFormattingForStatsData') as mock_cleanFormattingForStatsData:
        
#         mock_getbacktestPeriod.return_value = 10
#         mock_cleanupData.return_value = savedResults
#         mock_getUpdatedBacktestPeriod.return_value = 10
#         mock_getBacktestDataFromCleanedData.return_value = pd.DataFrame(savedResults)
#         mock_cleanFormattingForStatsData.return_value = pd.DataFrame(savedResults)
        
#         result = performXRay(savedResults=savedResults, args=args, calcForDate=None)
        
#         assert isinstance(result, pd.DataFrame)
#         assert len(result) == len(savedResults)

# def test_performXRay_with_savedResults_no_days(args):
#     savedResults = [1, 2, 3, 4, 5]
#     with patch('pkscreener.classes.PortfolioXRay.getbacktestPeriod') as mock_getbacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.cleanupData') as mock_cleanupData, \
#          patch('pkscreener.classes.PortfolioXRay.getUpdatedBacktestPeriod') as mock_getUpdatedBacktestPeriod, \
#          patch('pkscreener.classes.PortfolioXRay.getBacktestDataFromCleanedData') as mock_getBacktestDataFromCleanedData, \
#          patch('pkscreener.classes.PortfolioXRay.cleanFormattingForStatsData') as mock_cleanFormattingForStatsData:
        
#         mock_getbacktestPeriod.return_value = 10
#         mock_cleanupData.return_value = savedResults
#         mock_getUpdatedBacktestPeriod.return_value = 0
        
#         result = performXRay(savedResults=savedResults, args=args, calcForDate=None)
        
#         assert result is None


def test_getUpdatedBacktestPeriod_with_calcForDate():
    calcForDate = "2022-01-01"
    backtestPeriods = 10
    saveResults = pd.DataFrame({"Date": ["2021-12-31", "2022-01-01", "2022-01-02"]})
    with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.currentDateTime', return_value=PKDateUtilities.dateFromYmdString(saveResults["Date"].iloc[0])):
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.holidayList', return_value=("",[])):
            result = getUpdatedBacktestPeriod(calcForDate, backtestPeriods, saveResults)
            assert result == 10

def test_getUpdatedBacktestPeriod_without_calcForDate():
    calcForDate = None
    backtestPeriods = 10
    saveResults = pd.DataFrame({"Date": ["2021-12-20", "2022-01-01", "2022-01-02"]})
    with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.currentDateTime', return_value=PKDateUtilities.dateFromYmdString("2022-01-04")):
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.holidayList', return_value=("",[])):
            result = getUpdatedBacktestPeriod(calcForDate, backtestPeriods, saveResults)
            assert result == 11

def test_getUpdatedBacktestPeriod_gap_greater_than_backtestPeriods():
    calcForDate = "2022-01-01"
    backtestPeriods = 2
    saveResults = pd.DataFrame({"Date": ["2021-12-31", "2022-01-01", "2022-01-02"]})
    with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.currentDateTime', return_value=PKDateUtilities.dateFromYmdString("2022-01-06")):
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.holidayList', return_value=("",[])):
            result = getUpdatedBacktestPeriod(calcForDate, backtestPeriods, saveResults)
            assert result == 3

def test_getUpdatedBacktestPeriod_gap_less_than_backtestPeriods():
    calcForDate = "2022-01-01"
    backtestPeriods = 10
    saveResults = pd.DataFrame({"Date": ["2022-01-01", "2022-01-02", "2022-01-03"]})
    with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.currentDateTime', return_value=PKDateUtilities.dateFromYmdString("2022-01-06")):
        with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.holidayList', return_value=("",[])):
            result = getUpdatedBacktestPeriod(calcForDate, backtestPeriods, saveResults)
            assert result == 10

def test_xRaySummary_no_savedResults():
    result = xRaySummary(savedResults=None)
    assert result is None

def test_xRaySummary_empty_savedResults():
    savedResults = pd.DataFrame()
    result = xRaySummary(savedResults=savedResults)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0

def test_xRaySummary_with_savedResults(args):
    savedResults = pd.DataFrame({"ScanType": ["Scan A", "Scan B"], "Date": ["2022-01-01", "2022-01-02"],"1Pd-%":["1","2"],"1Pd-10k":["10000","20000"]})
    with patch('PKDevTools.classes.PKDateUtilities.PKDateUtilities.currentDateTime') as mock_currentDateTime, \
         patch('pkscreener.classes.ImageUtility.PKImageTools.removeAllColorStyles') as mock_removeAllColorStyles:
        mock_currentDateTime.return_value.strftime.return_value = "2022-01-03"
        mock_removeAllColorStyles.return_value = "10.0"
        result = xRaySummary(savedResults=savedResults)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(savedResults) + 2
        assert result["ScanType"].tolist() == ["Scan A", "Scan B", "[SUM]Scan A  (1)", "[SUM]Scan B  (1)"]
        assert result["Date"].tolist() == ["2022-01-01", "2022-01-02", "2022-01-03", "2022-01-03"]


def test_cleanFormattingForStatsData_with_calcForDate():
    calcForDate = "2022-01-01"
    saveResults = pd.DataFrame({"Date": ["2021-12-31", "2022-01-01", "2022-01-02"]})
    df = pd.DataFrame({"ScanType": ["Scan A", "Scan B"], "Pd-%": [0.5, 0.6], "Pd-10k": [10000, 20000]})
    
    result = cleanFormattingForStatsData(calcForDate, saveResults, df)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(df)
    assert "ScanType" in result.columns
    assert "Pd-%" in result.columns
    assert "Pd-10k" in result.columns
    assert "Date" in result.columns
    assert result["Date"].tolist() == ["2022-01-01", "2022-01-01"]

def test_cleanFormattingForStatsData_without_calcForDate():
    calcForDate = None
    saveResults = pd.DataFrame({"Date": ["2021-12-31", "2022-01-01", "2022-01-02"]})
    df = pd.DataFrame({"ScanType": ["Scan A", "Scan B"], "Pd-%": [0.5, 0.6], "Pd-10k": [10000, 20000]})
    
    result = cleanFormattingForStatsData(calcForDate, saveResults, df)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(df)
    assert "ScanType" in result.columns
    assert "Pd-%" in result.columns
    assert "Pd-10k" in result.columns
    assert "Date" in result.columns
    assert result["Date"].tolist() == ["2021-12-31", "2021-12-31"]

def test_cleanFormattingForStatsData_empty_df():
    calcForDate = "2022-01-01"
    saveResults = pd.DataFrame({"Date": ["2021-12-31", "2022-01-01", "2022-01-02"]})
    df = pd.DataFrame()
    
    result = cleanFormattingForStatsData(calcForDate, saveResults, df)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0

def test_cleanFormattingForStatsData_no_df():
    calcForDate = "2022-01-01"
    saveResults = pd.DataFrame({"Date": ["2021-12-31", "2022-01-01", "2022-01-02"]})
    df = None
    
    result = cleanFormattingForStatsData(calcForDate, saveResults, df)
    
    assert result is None

@pytest.mark.skipif("Darwin" in platform.system(),reason="Cannot simulate the environment on MacOS",)
def test_getBacktestDataFromCleanedData_no_df(args):
    saveResults = pd.DataFrame({"LTP": [11, 22, 33], "LTP1": [10, 20, 30], "Growth1": [0.1, 0.2, 0.3], "Pattern": ["A", "B", "C"]})
    period = 1
    
    with patch('pkscreener.classes.PortfolioXRay.statScanCalculationForRSI') as mock_statScanCalculationForRSI, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForTrend') as mock_statScanCalculationForTrend, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForMA') as mock_statScanCalculationForMA, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForVol') as mock_statScanCalculationForVol, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForConsol') as mock_statScanCalculationForConsol, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForBO') as mock_statScanCalculationForBO, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationFor52Wk') as mock_statScanCalculationFor52Wk, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForCCI') as mock_statScanCalculationForCCI:

        result = getBacktestDataFromCleanedData(args, saveResults, df=None, periods=[period])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5*len(saveResults)+1
        assert f"LTP{period}" not in result.columns
        assert f"Growth{period}" not in result.columns
        assert f"{period}Pd-%" in result.columns
        assert f"{period}Pd-10k" in result.columns
        assert "Pattern" not in result.columns
        assert "ScanType" in result.columns
        assert result["ScanType"].tolist()[:4] == ["[P]A", "[P]B", "[P]C", "NoFilter"]

@pytest.mark.skipif("Darwin" in platform.system(),reason="Cannot simulate the environment on MacOS",)
def test_getBacktestDataFromCleanedData_with_df(args):
    saveResults = pd.DataFrame({"LTP": [11, 22, 33], "LTP1": [10, 20, 30], "Growth1": [0.1, 0.2, 0.3], "Pattern": ["A", "B", "C"]})
    period = 1
    df = pd.DataFrame({"Pattern": ["D", "E", "F"]})
    with patch('pkscreener.classes.PortfolioXRay.statScanCalculationForRSI') as mock_statScanCalculationForRSI, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForTrend') as mock_statScanCalculationForTrend, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForMA') as mock_statScanCalculationForMA, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForVol') as mock_statScanCalculationForVol, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForConsol') as mock_statScanCalculationForConsol, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForBO') as mock_statScanCalculationForBO, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationFor52Wk') as mock_statScanCalculationFor52Wk, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForCCI') as mock_statScanCalculationForCCI:

        result = getBacktestDataFromCleanedData(args, saveResults, df=df, periods=[period])
    
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5*len(saveResults)+1
        assert f"LTP{period}" not in result.columns
        assert f"Growth{period}" not in result.columns
        assert f"{period}Pd-%" in result.columns
        assert f"{period}Pd-10k" in result.columns
        assert "Pattern" in result.columns
        assert "ScanType" not in result.columns
        assert result["Pattern"].tolist()[:3] == ["D", "E", "F"]

@pytest.mark.skipif("Darwin" in platform.system(),reason="Cannot simulate the environment on MacOS",)
def test_getBacktestDataFromCleanedData_no_pattern(args):
    saveResults = pd.DataFrame({"LTP": [11, 22, 33], "LTP1": [10, 20, 30], "Growth1": [0.1, 0.2, 0.3], "Pattern": [None, "", "C"]})
    period = 1
    
    with patch('pkscreener.classes.PortfolioXRay.statScanCalculationForRSI') as mock_statScanCalculationForRSI, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForTrend') as mock_statScanCalculationForTrend, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForMA') as mock_statScanCalculationForMA, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForVol') as mock_statScanCalculationForVol, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForConsol') as mock_statScanCalculationForConsol, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForBO') as mock_statScanCalculationForBO, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationFor52Wk') as mock_statScanCalculationFor52Wk, \
        patch('pkscreener.classes.PortfolioXRay.statScanCalculationForCCI') as mock_statScanCalculationForCCI:

        result = getBacktestDataFromCleanedData(args, saveResults, df=None, periods=[period])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4*len(saveResults)
        assert f"LTP{period}" not in result.columns
        assert f"Growth{period}" not in result.columns
        assert f"{period}Pd-%" in result.columns
        assert f"{period}Pd-10k" in result.columns
        assert "Pattern" not in result.columns
        assert "ScanType" in result.columns
        assert result["ScanType"].tolist()[:3] == ["[P]No Pattern", "[P]C", "NoFilter"]

@pytest.fixture
def savedResults():
    return None

def test_cleanupData(savedResults):
    savedResults = pd.DataFrame({
        "LTP": ["10.0", "20.0", "30.0"],
        "RSI": ["50.0", "60.0", "70.0"],
        "volume": ["100x", "200x", "300x"],
        "Consol.": ["Range: 10%", "Range: 20%", "Range: 30%"],
        f"Breakout({configManager.daysToLookback}Prds)": ["BO: 1.0 R: 2.0 (Potential)", "BO: 3.0 R: 4.0 (Potential)", "BO: 5.0 R: 6.0 (Potential)"],
        "52Wk-H": ["100.0", "200.0", "300.0"],
        "52Wk-L": ["50.0", "100.0", "150.0"],
        "CCI": ["80.0", "90.0", "100.0"]
    })

    result = cleanupData(savedResults)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(savedResults)
    assert "LTP" in result.columns
    assert "RSI" in result.columns
    assert "volume" in result.columns
    assert "Consol." in result.columns
    assert "Breakout" in result.columns
    assert "Resistance" in result.columns
    assert "52Wk-H" in result.columns
    assert "52Wk-L" in result.columns
    assert "CCI" in result.columns
    assert result["LTP"].tolist() == [10.0, 20.0, 30.0]
    assert result["RSI"].tolist() == [50.0, 60.0, 70.0]
    assert result["volume"].tolist() == [100.0, 200.0, 300.0]
    assert result["Consol."].tolist() == [10.0, 20.0, 30.0]
    assert result["Breakout"].tolist() == [1.0, 3.0, 5.0]
    assert result["Resistance"].tolist() == [2.0, 4.0, 6.0]
    assert result["52Wk-H"].tolist() == [100.0, 200.0, 300.0]
    assert result["52Wk-L"].tolist() == [50.0, 100.0, 150.0]
    assert result["CCI"].tolist() == [80.0, 90.0, 100.0]

def test_getbacktestPeriod_no_args():
    args = None
    
    result = getbacktestPeriod(args)
    
    assert result == 30

def test_getbacktestPeriod_with_args():
    args = argparse.Namespace(backtestdaysago=10)
    
    result = getbacktestPeriod(args)
    
    assert result == 10

def test_getbacktestPeriod_with_invalid_args():
    args = argparse.Namespace(backtestdaysago="abc")
    
    result = getbacktestPeriod(args)
    
    assert result == 30

@pytest.fixture
def saveResults():
    return None

# def test_statScanCalculations(args, saveResults):
#     period = 30
#     scanResults = []
    
#     with patch('pkscreener.classes.PortfolioXRay.statScanCalculationForRSI') as mock_statScanCalculationForRSI, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForTrend') as mock_statScanCalculationForTrend, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForMA') as mock_statScanCalculationForMA, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForVol') as mock_statScanCalculationForVol, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForConsol') as mock_statScanCalculationForConsol, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForBO') as mock_statScanCalculationForBO, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationFor52Wk') as mock_statScanCalculationFor52Wk, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForCCI') as mock_statScanCalculationForCCI, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForPatterns') as mock_statScanCalculationForPatterns, \
#         patch('pkscreener.classes.PortfolioXRay.statScanCalculationForNoFilter') as mock_statScanCalculationForNoFilter:
        
#         result = statScanCalculations(args, saveResults, period)
        
#         assert result == scanResults
#         mock_statScanCalculationForRSI.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForTrend.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForMA.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForVol.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForConsol.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForBO.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationFor52Wk.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForCCI.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForPatterns.assert_called_once_with(args, saveResults, period, scanResults)
#         mock_statScanCalculationForNoFilter.assert_called_once_with(args, saveResults, period, scanResults)


def test_statScanCalculationForCCI(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterCCIBelowMinus100') as mock_filterCCIBelowMinus100, \
         patch('pkscreener.classes.PortfolioXRay.filterCCIBelow0') as mock_filterCCIBelow0, \
         patch('pkscreener.classes.PortfolioXRay.filterCCI0To100') as mock_filterCCI0To100, \
         patch('pkscreener.classes.PortfolioXRay.filterCCI100To200') as mock_filterCCI100To200, \
         patch('pkscreener.classes.PortfolioXRay.filterCCIAbove200') as mock_filterCCIAbove200, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationForCCI(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterCCIBelowMinus100.assert_called_once_with(saveResults)
        mock_filterCCIBelow0.assert_called_once_with(saveResults)
        mock_filterCCI0To100.assert_called_once_with(saveResults)
        mock_filterCCI100To200.assert_called_once_with(saveResults)
        mock_filterCCIAbove200.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 5


def test_statScanCalculationFor52Wk(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterLTPMoreOREqual52WkH') as mock_filterLTPMoreOREqual52WkH, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPWithin90Percent52WkH') as mock_filterLTPWithin90Percent52WkH, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPLess90Percent52WkH') as mock_filterLTPLess90Percent52WkH, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPMore52WkL') as mock_filterLTPMore52WkL, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPWithin90Percent52WkL') as mock_filterLTPWithin90Percent52WkL, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPLess52WkL') as mock_filterLTPLess52WkL, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationFor52Wk(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterLTPMoreOREqual52WkH.assert_called_once_with(saveResults)
        mock_filterLTPWithin90Percent52WkH.assert_called_once_with(saveResults)
        mock_filterLTPLess90Percent52WkH.assert_called_once_with(saveResults)
        mock_filterLTPMore52WkL.assert_called_once_with(saveResults)
        mock_filterLTPWithin90Percent52WkL.assert_called_once_with(saveResults)
        mock_filterLTPLess52WkL.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 6


def test_statScanCalculationForBO(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterLTPLessThanBreakout') as mock_filterLTPLessThanBreakout, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPMoreOREqualBreakout') as mock_filterLTPMoreOREqualBreakout, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPLessThanResistance') as mock_filterLTPLessThanResistance, \
         patch('pkscreener.classes.PortfolioXRay.filterLTPMoreOREqualResistance') as mock_filterLTPMoreOREqualResistance, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationForBO(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterLTPLessThanBreakout.assert_called_once_with(saveResults)
        mock_filterLTPMoreOREqualBreakout.assert_called_once_with(saveResults)
        mock_filterLTPLessThanResistance.assert_called_once_with(saveResults)
        mock_filterLTPMoreOREqualResistance.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 4


def test_statScanCalculationForConsol(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterConsolidating10Percent') as mock_filterConsolidating10Percent, \
         patch('pkscreener.classes.PortfolioXRay.filterConsolidatingMore10Percent') as mock_filterConsolidatingMore10Percent, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationForConsol(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterConsolidating10Percent.assert_called_once_with(saveResults)
        mock_filterConsolidatingMore10Percent.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 2


def test_statScanCalculationForVol(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterVolumeLessThan25') as mock_filterVolumeLessThan25, \
         patch('pkscreener.classes.PortfolioXRay.filterVolumeMoreThan25') as mock_filterVolumeMoreThan25, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationForVol(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterVolumeLessThan25.assert_called_once_with(saveResults)
        mock_filterVolumeMoreThan25.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 2


def test_statScanCalculationForMA(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterMASignalBullish') as mock_filterMASignalBullish, \
         patch('pkscreener.classes.PortfolioXRay.filterMASignalBearish') as mock_filterMASignalBearish, \
         patch('pkscreener.classes.PortfolioXRay.filterMASignalNeutral') as mock_filterMASignalNeutral, \
         patch('pkscreener.classes.PortfolioXRay.filterMASignalBullCross') as mock_filterMASignalBullCross, \
         patch('pkscreener.classes.PortfolioXRay.filterMASignalBearCross') as mock_filterMASignalBearCross, \
         patch('pkscreener.classes.PortfolioXRay.filterMASignalSupport') as mock_filterMASignalSupport, \
         patch('pkscreener.classes.PortfolioXRay.filterMASignalResist') as mock_filterMASignalResist, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationForMA(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterMASignalBullish.assert_called_once_with(saveResults)
        mock_filterMASignalBearish.assert_called_once_with(saveResults)
        mock_filterMASignalNeutral.assert_called_once_with(saveResults)
        mock_filterMASignalBullCross.assert_called_once_with(saveResults)
        mock_filterMASignalBearCross.assert_called_once_with(saveResults)
        mock_filterMASignalSupport.assert_called_once_with(saveResults)
        mock_filterMASignalResist.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 7


def test_statScanCalculationForTrend(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterTrendStrongUp') as mock_filterTrendStrongUp, \
         patch('pkscreener.classes.PortfolioXRay.filterTrendWeakUp') as mock_filterTrendWeakUp, \
         patch('pkscreener.classes.PortfolioXRay.filterTrendUp') as mock_filterTrendUp, \
         patch('pkscreener.classes.PortfolioXRay.filterTrendStrongDown') as mock_filterTrendStrongDown, \
         patch('pkscreener.classes.PortfolioXRay.filterTrendWeakDown') as mock_filterTrendWeakDown, \
         patch('pkscreener.classes.PortfolioXRay.filterTrendSideways') as mock_filterTrendSideways, \
         patch('pkscreener.classes.PortfolioXRay.filterTrendDown') as mock_filterTrendDown, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationForTrend(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterTrendStrongUp.assert_called_once_with(saveResults)
        mock_filterTrendWeakUp.assert_called_once_with(saveResults)
        mock_filterTrendUp.assert_called_once_with(saveResults)
        mock_filterTrendStrongDown.assert_called_once_with(saveResults)
        mock_filterTrendWeakDown.assert_called_once_with(saveResults)
        mock_filterTrendSideways.assert_called_once_with(saveResults)
        mock_filterTrendDown.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 7


def test_statScanCalculationForRSI(args, saveResults):
    period = 30
    scanResults = []
    
    with patch('pkscreener.classes.PortfolioXRay.filterRSIAbove50') as mock_filterRSIAbove50, \
         patch('pkscreener.classes.PortfolioXRay.filterRSI50To67') as mock_filterRSI50To67, \
         patch('pkscreener.classes.PortfolioXRay.filterRSI68OrAbove') as mock_filterRSI68OrAbove, \
         patch('pkscreener.classes.PortfolioXRay.getCalculatedValues') as mock_getCalculatedValues:
        
        result = statScanCalculationForRSI(args, saveResults, period, scanResults)
        
        assert result == scanResults
        mock_filterRSIAbove50.assert_called_once_with(saveResults)
        mock_filterRSI50To67.assert_called_once_with(saveResults)
        mock_filterRSI68OrAbove.assert_called_once_with(saveResults)
        assert mock_getCalculatedValues.call_count == 3


def test_formatGridOutput():
    df = pd.DataFrame({
        "Col1": [np.nan, 10, 20, 30],
        "Col2": [np.nan, 5000, 15000, 1000],
        "Col3": [5000, -5, 0, 10]
    })

    result = formatGridOutput(df)

    assert isinstance(result, pd.DataFrame)
    assert result["Col1"].tolist() == ["-", 10.0, 20.0, 30.0]
    assert result["Col2"].tolist() == ['-', 5000.0, 15000.0, 1000.0]
    assert result["Col3"].tolist() == [5000.0, -5.0, 0.0, 10.0]


def test_filterRSIAbove50(df):
    df = pd.DataFrame({"RSI": [60, 40, 70, 30]})
    result = filterRSIAbove50(df)
    expected_result = pd.DataFrame({"RSI": [60, 70]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True),check_dtype=False)
    assert filterRSIAbove50(None) is None

def test_filterRSI50To67(df):
    df = pd.DataFrame({"RSI": [60, 40, 70, 30]})
    result = filterRSI50To67(df)
    expected_result = pd.DataFrame({"RSI": [60]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterRSI50To67(None) is None

def test_filterRSI68OrAbove(df):
    df = pd.DataFrame({"RSI": [60, 40, 70, 30]})
    result = filterRSI68OrAbove(df)
    expected_result = pd.DataFrame({"RSI": [70]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterRSI68OrAbove(None) is None

def test_filterTrendStrongUp(df):
    df = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Up", "Weak Up", "Strong Up", "Weak Down"]})
    result = filterTrendStrongUp(df)
    expected_result = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Up", "Strong Up"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterTrendStrongUp(None) is None

def test_filterTrendWeakUp(df):
    df = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Weak Up", "Strong Up", "Weak Up", "Weak Down"]})
    result = filterTrendWeakUp(df)
    expected_result = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Weak Up", "Weak Up"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterTrendWeakUp(None) is None

def test_filterTrendWeakDown(df):
    df = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Weak Down", "Strong Down", "Weak Down", "Weak Up"]})
    result = filterTrendWeakDown(df)
    expected_result = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Weak Down", "Weak Down"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterTrendWeakDown(None) is None

def test_filterTrendStrongDown(df):
    df = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Down", "Weak Down", "Strong Down", "Weak Up"]})
    result = filterTrendStrongDown(df)
    expected_result = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Down", "Strong Down"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterTrendStrongDown(None) is None

def test_filterTrendUp(df):
    df = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Down", "Weak Down", "Strong Down", "Weak Up"]})
    result = filterTrendUp(df)
    expected_result = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Weak Up"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterTrendUp(None) is None

def test_filterSideways(df):
    df = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Down", "Weak Down", "Sideways", "Weak Up"]})
    result = filterTrendSideways(df)
    expected_result = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Sideways"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterTrendSideways(None) is None

def test_filterTrendDown(df):
    df = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Down", "Weak Down", "Strong Down", "Weak Up"]})
    result = filterTrendDown(df)
    expected_result = pd.DataFrame({f"Trend({configManager.daysToLookback}Prds)": ["Strong Down", "Weak Down", "Strong Down"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterTrendDown(None) is None

def test_filterMASignalBullish(df):
    df = pd.DataFrame({"MA-Signal": ["Bullish", "Bearish", "Bearish", "Bullish"]})
    result = filterMASignalBullish(df)
    expected_result = pd.DataFrame({"MA-Signal": ["Bullish", "Bullish"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterMASignalBullish(None) is None

def test_filterMASignalBearish(df):
    df = pd.DataFrame({"MA-Signal": ["Bullish", "Bearish", "Bearish", "Bullish"]})
    result = filterMASignalBearish(df)
    expected_result = pd.DataFrame({"MA-Signal": ["Bearish", "Bearish"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterMASignalBearish(None) is None

def test_filterMASignalNeutral(df):
    df = pd.DataFrame({"MA-Signal": ["Bullish", "Bearish", "Neutral", "Bullish"]})
    result = filterMASignalNeutral(df)
    expected_result = pd.DataFrame({"MA-Signal": ["Neutral"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterMASignalNeutral(None) is None

def test_filterMASignalBullCross(df):
    df = pd.DataFrame({"MA-Signal": ["BullCross-50MA", "Bearish", "Neutral", "BearCross-10MA"]})
    result = filterMASignalBullCross(df)
    expected_result = pd.DataFrame({"MA-Signal": ["BullCross-50MA"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterMASignalBullCross(None) is None

def test_filterMASignalBearCross(df):
    df = pd.DataFrame({"MA-Signal": ["BullCross-50MA", "Bearish", "Neutral", "BearCross-10MA"]})
    result = filterMASignalBearCross(df)
    expected_result = pd.DataFrame({"MA-Signal": ["BearCross-10MA"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterMASignalBearCross(None) is None

def test_filterMASignalSupport(df):
    df = pd.DataFrame({"MA-Signal": ["BullCross-50MA", "50MA-Support", "10MA-Resist", "BearCross-10MA"]})
    result = filterMASignalSupport(df)
    expected_result = pd.DataFrame({"MA-Signal": ["50MA-Support"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterMASignalSupport(None) is None

def test_filterMASignalResist(df):
    df = pd.DataFrame({"MA-Signal": ["BullCross-50MA", "50MA-Support", "10MA-Resist", "BearCross-10MA"]})
    result = filterMASignalResist(df)
    expected_result = pd.DataFrame({"MA-Signal": ["10MA-Resist"]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterMASignalResist(None) is None

def test_filterVolumeLessThan25(df):
    df = pd.DataFrame({"volume": [1,0.3,1.5,2.5,3,4]})
    result = filterVolumeLessThan25(df)
    expected_result = pd.DataFrame({"volume": [1,0.3,1.5]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterVolumeLessThan25(None) is None

def test_filterVolumeMoreThan25(df):
    df = pd.DataFrame({"volume": [1,0.3,1.5,2.5,3,4]})
    result = filterVolumeMoreThan25(df)
    expected_result = pd.DataFrame({"volume": [2.5,3,4]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterVolumeMoreThan25(None) is None

def test_filterConsolidating10Percent(df):
    df = pd.DataFrame({"Consol.": [1,0.3,1.5,2.5,3,4,10,11,19,18]})
    result = filterConsolidating10Percent(df)
    expected_result = pd.DataFrame({"Consol.": [1,0.3,1.5,2.5,3,4,10]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterConsolidating10Percent(None) is None

def test_filterConsolidatingMore10Percent(df):
    df = pd.DataFrame({"Consol.": [1,0.3,1.5,2.5,3,4,10,11.5,19,18]})
    result = filterConsolidatingMore10Percent(df)
    expected_result = pd.DataFrame({"Consol.": [11.5,19,18]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterConsolidatingMore10Percent(None) is None

def test_filterLTPLessThanBreakout(df):
    df = pd.DataFrame({"LTP": [1000,2000,3000,4000,5000],"Breakout":[990,1900,3050,4100,5400]})
    result = filterLTPLessThanBreakout(df)
    expected_result = pd.DataFrame({"LTP": [3000,4000,5000],"Breakout":[3050,4100,5400]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPLessThanBreakout(None) is None

def test_filterLTPMoreOREqualBreakout(df):
    df = pd.DataFrame({"LTP": [1000,2000,3052,4100,5400],"Breakout":[990,2000,3050,4100,5500]})
    result = filterLTPMoreOREqualBreakout(df)
    expected_result = pd.DataFrame({"LTP": [1000,2000,3052,4100],"Breakout":[990,2000,3050,4100]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPMoreOREqualBreakout(None) is None

def test_filterLTPLessThanResistance(df):
    df = pd.DataFrame({"LTP": [1000,2000,3000,4000,5000],"Resistance":[990,1900,3050,4100,5400]})
    result = filterLTPLessThanResistance(df)
    expected_result = pd.DataFrame({"LTP": [3000,4000,5000],"Resistance":[3050,4100,5400]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPLessThanResistance(None) is None

def test_filterLTPMoreOREqualResistance(df):
    df = pd.DataFrame({"LTP": [1000,2000,3052,4100,5400],"Resistance":[990,2000,3050,4100,5500]})
    result = filterLTPMoreOREqualResistance(df)
    expected_result = pd.DataFrame({"LTP": [1000,2000,3052,4100],"Resistance":[990,2000,3050,4100]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPMoreOREqualResistance(None) is None

def test_filterLTPMoreOREqual52WkH(df):
    df = pd.DataFrame({"LTP": [1000,2000,3052,4100,5400],"52Wk-H":[990,2000,3050,4100,5500]})
    result = filterLTPMoreOREqual52WkH(df)
    expected_result = pd.DataFrame({"LTP": [1000,2000,3052,4100],"52Wk-H":[990,2000,3050,4100]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPMoreOREqual52WkH(None) is None

def test_filterLTPWithin90Percent52WkH(df):
    df = pd.DataFrame({"LTP": [1000,2000,3052,4100,4951],"52Wk-H":[990,2000,3050,4100,5500]})
    result = filterLTPWithin90Percent52WkH(df)
    expected_result = pd.DataFrame({"LTP": [4951],"52Wk-H":[5500]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPWithin90Percent52WkH(None) is None

def test_filterLTPLess90Percent52WkH(df):
    df = pd.DataFrame({"LTP": [1000,2000,3052,3500,5400],"52Wk-H":[990,2000,3050,4000,5500]})
    result = filterLTPLess90Percent52WkH(df)
    expected_result = pd.DataFrame({"LTP": [3500],"52Wk-H":[4000]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPLess90Percent52WkH(None) is None

def test_filterLTPWithin90Percent52WkL(df):
    df = pd.DataFrame({"LTP": [110.2,220.4,310.4,410.0,452.1],"52Wk-L":[100.1,200.2,300.3,400.0,500.4]})
    result = filterLTPWithin90Percent52WkL(df)
    expected_result = pd.DataFrame({"LTP": [110.2,220.4],"52Wk-L":[100.1,200.2]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPWithin90Percent52WkL(None) is None

def test_filterLTPLess52WkL(df):
    df = pd.DataFrame({"LTP": [100.1,200.2,300.3,400.0,500.4],"52Wk-L":[110.2,220.4,310.4,410.0,452.1]})
    result = filterLTPLess52WkL(df)
    expected_result = pd.DataFrame({"LTP": [100.1,200.2,300.3,400.0],"52Wk-L":[110.2,220.4,310.4,410.0]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPLess52WkL(None) is None

def test_filterLTPMore52WkL(df):
    df = pd.DataFrame({"52Wk-L": [100.1,200.2,300.3,400.0,500.4],"LTP":[110.2,220.4,310.4,410.0,452.1]})
    result = filterLTPMore52WkL(df)
    expected_result = pd.DataFrame({"52Wk-L": [300.3,400.0],"LTP":[310.4,410.0]})
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))
    assert filterLTPMore52WkL(None) is None

@pytest.fixture
def df():
    return None

# class TestStatScanCalculations(unittest.TestCase):

#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForRSI')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForTrend')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForMA')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForVol')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForConsol')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForBO')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationFor52Wk')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForCCI')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForPatterns')
#     @patch('pkscreener.classes.PortfolioXRay.statScanCalculationForNoFilter')
#     @patch('pkscreener.classes.PKScheduler.PKScheduler')
#     def test_statScanCalculations_positive(self, mock_scheduler, *mock_functions):
#         # Arrange
#         userArgs = {'arg1': 'value1'}
#         saveResults = ['result1', 'result2']
#         periods = 10
#         expected_results = ['RSI result', 'Trend result', 'MA result']

#         for mock_function in mock_functions:
#             mock_function.return_value = expected_results
#             task = PKTask("taskname","long_running_func")
#             task.result = expected_results
#             mock_function.call_args = (task)
#             mock_function.call_args_list.append(task)

#         # Act
#         results = statScanCalculations(userArgs, saveResults, periods)

#         # Assert
#         self.assertEqual(len(results), len(mock_functions) * len(expected_results))
#         for result in results:
#             self.assertIn(result, expected_results)

#     def test_statScanCalculations_no_save_results(self):
#         # Arrange
#         userArgs = {'arg1': 'value1'}
#         saveResults = None
#         periods = 10

#         # Act
#         results = statScanCalculations(userArgs, saveResults, periods)

#         # Assert
#         self.assertEqual(results, [])

#     def test_statScanCalculations_empty_save_results(self):
#         # Arrange
#         userArgs = {'arg1': 'value1'}
#         saveResults = []
#         periods = 10

#         # Act
#         results = statScanCalculations(userArgs, saveResults, periods)

#         # Assert
#         self.assertEqual(results, [])

#     @patch('pkscreener.classes.PKScheduler.PKScheduler')
#     def test_statScanCalculations_with_invalid_input(self, mock_scheduler):
#         # Arrange
#         userArgs = None  # Invalid input
#         saveResults = ['result1', 'result2']
#         periods = 10

#         # Act & Assert
#         with self.assertRaises(TypeError):
#             statScanCalculations(userArgs, saveResults, periods)

#     @patch('pkscreener.classes.PKScheduler.PKScheduler')
#     def test_statScanCalculations_with_large_results(self, mock_scheduler,*mock_functions):
#         # Arrange
#         userArgs = {'arg1': 'value1'}
#         saveResults = ['result' for _ in range(1000)]  # Large input
#         periods = 10
#         expected_results = ['Large result'] * 10

#         # Mocking all functions to return a large result
#         for mock_function in mock_functions:
#             mock_function.return_value = expected_results

#         # Act
#         results = statScanCalculations(userArgs, saveResults, periods)

#         # Assert
#         self.assertEqual(len(results), len(mock_functions) * len(expected_results))
